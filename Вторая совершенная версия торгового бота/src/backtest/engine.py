"""
src/backtest/engine.py
Движок бэктестинга Apex V5 Global (v4.0 – Spotter + CatBoost Hunter, фиксированный TP).
Включает детальную диагностику и сбор статистики уверенности модели.
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

import matplotlib.pyplot as plt
import matplotlib.dates as mdates


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

        trading = config.get("trading", {})
        self.prob_threshold = float(trading.get("prob_threshold", 0.5))
        self.tp_atr_mult = float(trading.get("tp_atr_mult", 4.0))
        self.sl_atr_mult = float(
            trading.get(
                "sl_atr_mult",
                config["dispatcher"]["risk"].get("sl_multiplier", 0.8),
            )
        )
        self.use_critic = bool(
            trading.get("use_critic", config.get("backtest", {}).get("use_critic", False))
        )

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

        # Счётчики для диагностики
        self.diag = {
            'combo_checked': 0,
            'combo_upper': 0,
            'combo_lower': 0,
            'hunter_long': 0,
            'hunter_short': 0,
            'hunter_hold': 0,
            'critic_blocked': 0,
            'dispatcher_not_ready': 0,
            'orders_sent': 0,
        }
        self.last_probs = None
        self.critic_reasons = {
            'Low ADX & high spread': 0,
            'Too far from liquidity': 0,
            'Expected move too small': 0,
            'Blocked trading hours': 0,
            'Other': 0
        }
        self.critic_move_samples = []

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

    def run(self, show_chart: bool = False) -> Tuple[Any, Dict[str, List]]:
        start_idx = max(50, self.config['features']['window_size'] if 'features' in self.config else 20) + self.delay_bars
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

        max_lag = self.config['hunter']['max_lag']

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

            # 1. Проверка выхода из позиции
            if self.position is not None:
                exit_triggered, exit_price, reason = self._check_exit(
                    self.position, bar_high, bar_low
                )
                if exit_triggered:
                    pnl = self._calculate_pnl(self.position, exit_price)
                    self.equity += pnl
                    self.dispatcher.on_position_closed(pnl)
                    trade_record = {
                        'entry_time': self.position['entry_time'],
                        'exit_time': self.current_time,
                        'signal': self.position['signal'],
                        'entry_price': self.position['entry_price'],
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'return': pnl / self.position['notional'],
                        'reason': reason,
                        'hunter_probs': self.position['hunter_probs'].tolist() if 'hunter_probs' in self.position and self.position['hunter_probs'] is not None else None,
                        'hunter_signal': self.position.get('hunter_signal', self.position['signal'])
                    }
                    self.trades.append(trade_record)
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
                        'commission_paid': commission,
                        'hunter_probs': self.last_probs if self.last_probs is not None else np.zeros(3),
                        'hunter_signal': self.pending_order['signal']  # сохраняем исходный сигнал
                    }
                    self.dispatcher.on_order_filled(exec_price)
                    self.pending_order = None

            # 3. Генерация сигнала
            if self.position is None and self.pending_order is None and self.dispatcher.is_ready_for_signal():
                signal = None
                probs = None
                features = None
                direction = None

                # Комбинация с верхней зоной
                if self.last_spotter != -1 and self.last_upper_touch != -1:
                    dist = abs(self.last_spotter - self.last_upper_touch)
                    if dist <= max_lag and max(self.last_spotter, self.last_upper_touch) == i:
                        self.diag['combo_checked'] += 1
                        self.diag['combo_upper'] += 1
                        features = _collect_features(
                            i, self.last_spotter, self.last_upper_touch,
                            volume, avg_volume, close, high, low, open_,
                            self.liq_upper, self.liq_lower,
                            adx, self.atr
                        )
                        signal, probs = self.hunter.decide(features)
                        self.last_probs = probs  # запоминаем вероятности
                        direction = 'upper'

                        if signal == 'LONG':
                            self.diag['hunter_long'] += 1
                        elif signal == 'SHORT':
                            self.diag['hunter_short'] += 1
                        else:
                            self.diag['hunter_hold'] += 1

                # Комбинация с нижней зоной
                if signal is None and self.last_spotter != -1 and self.last_lower_touch != -1:
                    dist = abs(self.last_spotter - self.last_lower_touch)
                    if dist <= max_lag and max(self.last_spotter, self.last_lower_touch) == i:
                        self.diag['combo_checked'] += 1
                        self.diag['combo_lower'] += 1
                        features = _collect_features(
                            i, self.last_spotter, self.last_lower_touch,
                            volume, avg_volume, close, high, low, open_,
                            self.liq_upper, self.liq_lower,
                            adx, self.atr
                        )
                        signal, probs = self.hunter.decide(features)
                        self.last_probs = probs  # запоминаем вероятности
                        direction = 'lower'

                        if signal == 'LONG':
                            self.diag['hunter_long'] += 1
                        elif signal == 'SHORT':
                            self.diag['hunter_short'] += 1
                        else:
                            self.diag['hunter_hold'] += 1

                if signal is None or signal == "HOLD":
                    continue

                # Фильтр по уверенности модели
                if probs is not None and np.max(probs) < self.prob_threshold:
                    continue

                entry_price = bar_open
                atr_val = self.atr[i]
                sl_mult = self.sl_atr_mult
                tp_mult = self.tp_atr_mult
                if signal == 'LONG':
                    tp_price = entry_price + tp_mult * atr_val
                    sl_price = entry_price - sl_mult * atr_val
                else:
                    tp_price = entry_price - tp_mult * atr_val
                    sl_price = entry_price + sl_mult * atr_val

                if self.use_critic:
                    spread = bar_high - bar_low
                    self.critic.update_spread(spread)
                    tp_move_pts = abs(tp_price - entry_price)
                    passed, reason = self.critic.passes_signal(
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
                        self.diag['critic_blocked'] += 1
                        if 'Low ADX' in reason:
                            self.critic_reasons['Low ADX & high spread'] += 1
                        elif 'liquidity' in reason.lower():
                            self.critic_reasons['Too far from liquidity'] += 1
                        elif 'Expected move' in reason:
                            self.critic_reasons['Expected move too small'] += 1
                            if len(self.critic_move_samples) < 5:
                                self.critic_move_samples.append({
                                    'bar': i,
                                    'spread': spread,
                                    'avg_spread': self.critic.get_avg_spread(),
                                    'target_move_pts': tp_move_pts,
                                    'min_tick_limit': self.critic.min_tick_multiplier * self.critic.get_avg_spread()
                                })
                        elif 'Blocked' in reason:
                            self.critic_reasons['Blocked trading hours'] += 1
                        else:
                            self.critic_reasons['Other'] += 1
                        continue

                # Dispatcher
                if not self.dispatcher.is_ready_for_signal():
                    self.diag['dispatcher_not_ready'] += 1
                    continue

                current_volatility = atr_val / entry_price
                success = self.dispatcher.receive_signal(
                    signal, entry_price, tp_price, sl_price, current_volatility
                )
                if success:
                    self.diag['orders_sent'] += 1

        # Причины блокировки
        self.logger.info("=== Critic Reasons ===")
        for reason, cnt in self.critic_reasons.items():
            self.logger.info(f"{reason}: {cnt}")

        # Примеры блокировок при маленьком ожидаемом движении
        if self.critic_move_samples:
            self.logger.info("=== Sample Critic 'Expected move too small' rejections ===")
            for s in self.critic_move_samples:
                self.logger.info(f"bar={s['bar']}, spread={s['spread']:.6f}, avg_spread={s['avg_spread']:.6f}, "
                                 f"target_move_pts={s['target_move_pts']:.2f}, min_tick_limit={s['min_tick_limit']:.6f}")

        # Диагностика
        self.logger.info("=== Backtest Diagnostics ===")
        for k, v in self.diag.items():
            self.logger.info(f"{k}: {v}")

        # Статистика уверенности модели
        if self.trades:
            probs_true, probs_false = [], []
            for t in self.trades:
                if t.get('hunter_probs') is not None:
                    # Индексы: 0=HOLD, 1=LONG, 2=SHORT
                    prob = t['hunter_probs'][1] if t.get('hunter_signal') == 'LONG' else t['hunter_probs'][2]
                    if t['pnl'] > 0:
                        probs_true.append(prob)
                    else:
                        probs_false.append(prob)
            if probs_true or probs_false:
                self.logger.info("=== Hunter Confidence Stats ===")
                self.logger.info(f"Avg prob for winning trades: {np.mean(probs_true):.4f} (n={len(probs_true)})")
                self.logger.info(f"Avg prob for losing trades:  {np.mean(probs_false):.4f} (n={len(probs_false)})")

        # Расчёт метрик
        metrics = calculate_metrics(
            trades=self.trades,
            initial_equity=self.config['dispatcher'].get('initial_equity', 10000.0),
            final_equity=self.equity
        )
        initial = self.config['dispatcher'].get('initial_equity', 10000.0)
        equity_values = [initial]
        equity_timestamps = [str(self.df['timestamp'].iloc[0])]
        for t in self.trades:
            equity_values.append(equity_values[-1] + t['pnl'])
            equity_timestamps.append(str(t['exit_time']))

        equity_payload = {"timestamps": equity_timestamps, "equity": equity_values}

        if show_chart and self.trades:
            plt.figure(figsize=(12, 6))
            plt.plot(equity_timestamps, equity_values, label='Equity', color='blue')
            plt.xlabel('Время')
            plt.ylabel('Капитал, USDT')
            plt.title('Кривая эквити')
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.legend()
            plt.tight_layout()
            plt.show()

        return metrics, equity_payload