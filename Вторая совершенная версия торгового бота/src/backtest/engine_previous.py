"""
src/backtest/engine.py
Движок бэктестинга Apex V5 Global (v4.0 – Spotter + CatBoost Hunter + CatBoost Strategist).
Выполняет симуляцию торговли на исторических данных с учётом задержек,
проскальзывания, комиссий и логики всех агентов.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

from src.data.indicators import CompositeOscillator, LiquidityZones
from src.agents.spotter import Spotter
from src.agents.hunter import HunterInference, _collect_features
from src.agents.strategist import StrategistInference, build_strategist_features
from src.agents.critic import CriticRules
from src.agents.dispatcher import Dispatcher
from src.backtest.slippage import apply_slippage
from src.backtest.metrics import calculate_metrics
from src.utils.helpers import calculate_atr, HighWaterMarkTracker
from src.utils.logger import get_logger


class BacktestEngine:
    """
    Симулятор торговли на исторических OHLCV данных.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        data: pd.DataFrame,
        hunter_inference: HunterInference,
        strategist_inference: StrategistInference,
    ):
        self.config = config
        self.df = data.reset_index(drop=True)
        self.hunter = hunter_inference
        self.strategist = strategist_inference

        self.symbol = config['general']['symbols'][0]
        self.timeframe = config['general']['timeframe']

        # Параметры бэктеста
        bt_cfg = config['backtest']
        self.slippage_btc_eth = bt_cfg['slippage']['btc_eth']
        self.slippage_alt = bt_cfg['slippage']['altcoins']
        self.commission_maker = bt_cfg['commission']['maker']
        self.commission_taker = bt_cfg['commission']['taker']
        self.delay_bars = bt_cfg['delay_bars']

        if 'BTC' in self.symbol or 'ETH' in self.symbol:
            self.slippage = self.slippage_btc_eth
        else:
            self.slippage = self.slippage_alt

        # Инициализация индикаторов
        self.composite = CompositeOscillator()
        self.liquidity = LiquidityZones(
            pivot_lookback=14,
            volume_percentile=90
        )
        self.atr = calculate_atr(
            self.df['high'].values,
            self.df['low'].values,
            self.df['close'].values,
            period=config['dispatcher']['risk']['atr_period']
        )
        self.curves = self.composite.compute(self.df)
        self.liq_upper, self.liq_lower = self.liquidity.compute_series(self.df, self.atr)
        self.strategist_curves = self.composite.get_all_indicators(self.df)

        # Spotter
        spotter_cfg = config.get('spotter', {})
        self.spotter = Spotter(
            window=spotter_cfg.get('window', 50),
            order=spotter_cfg.get('order', 5),
            max_lag=spotter_cfg.get('max_lag', 2)
        )
        self.spotter_ts = set(self.spotter.get_signals(
            self.curves.long, self.curves.neutral, self.curves.short
        ))

        # Агенты
        self.critic = CriticRules(
            adx_threshold=config['critic']['adx_threshold'],
            adx_threshold_paranoia=config['critic'].get('adx_threshold_paranoia', 25),
            spread_multiplier=config['critic']['spread_multiplier'],
            liquidity_distance_threshold=config['critic']['liquidity_distance_threshold'],
            min_tick_multiplier=config['critic']['min_tick_multiplier'],
            blocked_hours=[]  # в бэктесте отключаем временной фильтр
        )

        disp_cfg = config['dispatcher']
        risk_cfg = disp_cfg['risk']
        paranoia_cfg = disp_cfg['paranoia_mode']

        self.dispatcher = Dispatcher(
            initial_equity=disp_cfg.get('initial_equity', 10000.0),
            base_risk=risk_cfg['base_risk'],
            target_volatility=risk_cfg['target_volatility'],
            max_leverage_normal=risk_cfg['max_leverage_normal'],
            max_leverage_paranoia=risk_cfg['max_leverage_paranoia'],
            atr_period=risk_cfg['atr_period'],
            sl_multiplier=risk_cfg['sl_multiplier'],
            hwm_threshold=paranoia_cfg.get('hwm_threshold', 0.95),
            heartbeat_timeout=999,
            send_order_callback=self._send_order,
            cancel_order_callback=self._cancel_order
        )

        # Состояние отслеживания событий
        self.last_spotter = -1
        self.last_upper_touch = -1
        self.last_lower_touch = -1

        self.pending_order: Optional[Dict] = None
        self.position: Optional[Dict] = None
        self.trades: List[Dict] = []
        self.equity = disp_cfg.get('initial_equity', 10000.0)
        self.logger = get_logger(__name__)

    def _send_order(self, signal, entry_price, position_size, leverage, tp_price, sl_price):
        self.pending_order = {
            'signal': signal,
            'entry_price': entry_price,
            'size': position_size,
            'leverage': leverage,
            'tp': tp_price,
            'sl': sl_price,
            'timestamp': self.current_time
        }
        self.dispatcher.on_order_accepted()
        return "backtest_order"

    def _cancel_order(self, order_id):
        self.pending_order = None
        return True

    def _apply_slippage(self, price: float, side: str) -> float:
        return apply_slippage(price, side, self.slippage)

    def _apply_commission(self, notional: float) -> float:
        return notional * self.commission_taker

    def _execute_order(self, order: Dict, bar_open: float) -> Tuple[bool, float]:
        side = 'BUY' if order['signal'] == 'LONG' else 'SELL'
        exec_price = self._apply_slippage(bar_open, side)
        return True, exec_price

    def _check_exit(self, position: Dict, bar_high: float, bar_low: float) -> Tuple[bool, float, str]:
        if position['signal'] == 'LONG':
            if bar_high >= position['tp']:
                return True, position['tp'], 'tp'
            elif bar_low <= position['sl']:
                return True, position['sl'], 'sl'
        else:
            if bar_low <= position['tp']:
                return True, position['tp'], 'tp'
            elif bar_high >= position['sl']:
                return True, position['sl'], 'sl'
        return False, 0.0, ''

    def _calculate_pnl(self, pos: Dict, exit_price: float) -> float:
        entry_notional = pos['notional']
        exit_notional = entry_notional * (exit_price / pos['entry_price'])
        if pos['signal'] == 'LONG':
            gross_pnl = exit_notional - entry_notional
        else:
            gross_pnl = entry_notional - exit_notional
        commission_exit = exit_notional * self.commission_taker
        return gross_pnl - commission_exit - pos['commission_paid']

    def run(self) -> Dict[str, Any]:
        window_size = self.config['features']['window_size'] if 'features' in self.config else 20
        start_idx = max(window_size, 50) + self.delay_bars  # минимум 50 баров для индикаторов
        self.equity = self.config['dispatcher'].get('initial_equity', 10000.0)
        self.dispatcher.update_equity(self.equity)
        self.pending_order = None
        self.position = None
        self.trades = []

        n = len(self.df)
        close = self.df['close'].values
        high = self.df['high'].values
        low = self.df['low'].values
        open_ = self.df['open'].values
        volume = self.df['volume'].values

        # Средний объем за 20 баров
        avg_volume = np.zeros(n)
        for i in range(n):
            start_idx_vol = max(0, i - 19)
            avg_volume[i] = volume[start_idx_vol:i+1].mean()

        # ADX
        from src.data.indicators import CompositeOscillator
        adx = CompositeOscillator._adx(high, low, close, 14)

        for i in range(start_idx, n):
            self.current_time = self.df.iloc[i]['timestamp']
            bar_open = open_[i]
            bar_high = high[i]
            bar_low = low[i]

            # Обновляем последние события
            if i in self.spotter_ts:
                self.last_spotter = i
            if not np.isnan(self.liq_upper['price'][i]) and bar_high >= self.liq_upper['price'][i]:
                self.last_upper_touch = i
            if not np.isnan(self.liq_lower['price'][i]) and bar_low <= self.liq_lower['price'][i]:
                self.last_lower_touch = i

            combo_checked = 0
            combo_upper = 0
            combo_lower = 0
            hunter_long = 0
            hunter_short = 0
            critic_blocked = 0
            dispatcher_not_ready = 0
            orders_sent = 0

            # 1. Проверка выхода из позиции
            if self.position is not None:
                exit_triggered, exit_price, reason = self._check_exit(
                    self.position, bar_high, bar_low
                )
                if exit_triggered:
                    pnl = self._calculate_pnl(self.position, exit_price)
                    self.equity += pnl
                    self.dispatcher.on_position_closed(pnl)
                    self.trades.append({
                        'entry_time': self.position['entry_time'],
                        'exit_time': self.current_time,
                        'signal': self.position['signal'],
                        'entry_price': self.position['entry_price'],
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'return': pnl / self.position['notional'],
                        'reason': reason
                    })
                    self.position = None

            # 2. Обработка отложенного ордера
            if self.pending_order is not None:
                executed, exec_price = self._execute_order(self.pending_order, bar_open)
                if executed:
                    notional = self.pending_order['size']
                    commission = self._apply_commission(notional)
                    self.equity -= commission
                    self.dispatcher.update_equity(self.equity)
                    self.position = {
                        'signal': self.pending_order['signal'],
                        'entry_price': exec_price,
                        'tp': self.pending_order['tp'],
                        'sl': self.pending_order['sl'],
                        'size': self.pending_order['size'],
                        'leverage': self.pending_order['leverage'],
                        'notional': notional,
                        'entry_time': self.current_time,
                        'commission_paid': commission
                    }
                    self.dispatcher.on_order_filled(exec_price)
                    self.pending_order = None

            # 3. Генерация сигнала
            if self.position is None and self.pending_order is None and self.dispatcher.is_ready_for_signal():
                max_lag = self.config['hunter']['max_lag']
                signal = None
                probs = None
                features = None
                direction = None

                # Комбинация с верхней зоной (SHORT)
                if self.last_spotter != -1 and self.last_upper_touch != -1:
                    dist = abs(self.last_spotter - self.last_upper_touch)
                    if dist <= max_lag and max(self.last_spotter, self.last_upper_touch) == i:
                        features = _collect_features(
                            i, self.last_spotter, self.last_upper_touch,
                            volume, avg_volume, close, high, low, open_,
                            self.liq_upper, self.liq_lower,
                            adx, self.atr
                        )
                        signal, probs = self.hunter.decide(features)
                        direction = 'upper'

                # Комбинация с нижней зоной (LONG)
                if signal is None and self.last_spotter != -1 and self.last_lower_touch != -1:
                    dist = abs(self.last_spotter - self.last_lower_touch)
                    if dist <= max_lag and max(self.last_spotter, self.last_lower_touch) == i:
                        features = _collect_features(
                            i, self.last_spotter, self.last_lower_touch,
                            volume, avg_volume, close, high, low, open_,
                            self.liq_upper, self.liq_lower,
                            adx, self.atr
                        )
                        signal, probs = self.hunter.decide(features)
                        direction = 'lower'

                if signal is None or signal == "HOLD":
                    continue

                # Расчёт TP через Strategist
                entry_price = bar_open
                atr_val = self.atr[i]
                sl_mult = self.config['dispatcher']['risk']['sl_multiplier']
                strat_features = build_strategist_features(
                    curves=self.strategist_curves,
                    atr=self.atr,
                    volume=volume,
                    liq_upper=self.liq_upper,
                    liq_lower=self.liq_lower,
                    index=i
                )
                #tp_price, sl_price = self.strategist.calculate_tp_sl(
                #    features=strat_features,
                #    entry_price=entry_price,
                #    atr=atr_val,
                #    signal=signal,
                #    sl_multiplier=sl_mult
                #)
                if signal == 'LONG':
                    tp_price = entry_price + 1.5 * atr_val
                    sl_price = entry_price - atr_val * sl_mult
                else:
                    tp_price = entry_price - 1.5 * atr_val
                    sl_price = entry_price + atr_val * sl_mult

                # Critic
                spread = bar_high - bar_low
                self.critic.update_spread(spread)
                passed, _ = self.critic.passes_signal(
                    adx=adx[i],
                    spread=spread,
                    liq_distance=0.0,
                    atr=atr_val,
                    signal=signal,
                    entry_price=entry_price,
                    tp_move_pct=abs(tp_price - entry_price) / entry_price,
                    current_time=self.current_time
                )
                if not passed:
                    continue

                # Dispatcher
                current_volatility = atr_val / entry_price
                self.dispatcher.receive_signal(
                    signal, entry_price, tp_price, sl_price, current_volatility
                )

        # Расчёт метрик
        metrics = calculate_metrics(
            trades=self.trades,
            initial_equity=self.config['dispatcher'].get('initial_equity', 10000.0),
            final_equity=self.equity
        )
        return metrics