"""
src/main.py
Главная точка входа для live-торговли Apex V5 Global (v4.0 – Spotter + CatBoost Hunter + CatBoost Strategist).

Загружает конфигурацию, инициализирует индикаторы (CompositeOscillator, LiquidityZones),
агентов (Spotter, Hunter, Strategist, Critic, Dispatcher, Learner) и запускает основной цикл
обработки новых 15m баров.

Логика:
1. На каждом баре получаем кривые и полные данные ликвидности.
2. Spotter обновляет метки.
3. Отслеживаем последние касания зон ликвидности.
4. Как только комбинация «метка Spotter + касание» завершается (в пределах max_lag),
   формируем признаки и передаём в CatBoost-Hunter.
5. Hunter возвращает сигнал (LONG/SHORT/HOLD) и вероятности.
6. При сигнале расчёт TP через CatBoost-Strategist и SL через ATR.
7. Фильтр уверенности модели (порог 0.5).
8. Проверка Critic (обязательная) и Dispatcher.receive_signal.
9. Логирование признаков и меток для дообучения через Learner.
10. Learner запускается периодически (раз в час).
"""

import os
import sys
import signal
import time
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Set

from dotenv import load_dotenv
load_dotenv()

from src.utils.logger import setup_logger, get_logger
from src.utils.helpers import calculate_atr, HighWaterMarkTracker
from src.data.indicators import CompositeOscillator, LiquidityZones, CompositeOscillatorResult
from src.agents.spotter import Spotter
from src.agents.hunter import HunterModel, HunterInference, _collect_features
from src.agents.strategist import StrategistModel, StrategistInference, build_strategist_features
from src.agents.critic import CriticRules
from src.agents.dispatcher import Dispatcher
from src.agents.learner import Learner
from src.execution.broker import BingXBroker
from src.execution.order_manager import OrderManager
from src.data.storage import DataStorageManager

class ApexV5Live:
    """Основной класс торговой системы."""

    def __init__(
        self,
        config_path: str = "config/settings.yaml",
        config: Optional[Dict[str, Any]] = None,
        register_signals: bool = True,
    ):
        self.config = config if config is not None else self._load_config(config_path)
        self._running = True
        self._setup_logging()
        self.logger = get_logger(__name__)

        trading = self.config.get("trading", {})
        self.prob_threshold = float(trading.get("prob_threshold", 0.5))
        self.tp_atr_mult = float(trading.get("tp_atr_mult", 4.0))
        self.sl_atr_mult = float(
            trading.get(
                "sl_atr_mult",
                self.config["dispatcher"]["risk"].get("sl_multiplier", 0.8),
            )
        )
        self.use_critic = bool(trading.get("use_critic", False))
        self.enable_learner = bool(trading.get("enable_learner", False))

        self.symbol = self.config['general']['symbols'][0]
        self.timeframe = self.config['general']['timeframe']

        if register_signals:
            def _stop_handler(sig, frame):
                self.stop()

            signal.signal(signal.SIGINT, _stop_handler)
            signal.signal(signal.SIGTERM, _stop_handler)

        # Компоненты
        self._init_broker()
        self._init_storage()
        self._init_indicators()
        self._init_models()
        self._init_agents()

        # Состояние отслеживания событий
        self.last_spotter = -1
        self.last_upper_touch = -1
        self.last_lower_touch = -1

        # Временные буферы
        self.last_bar_time: Optional[datetime] = None
        self.last_learner_run = datetime.min

        # Кэш свечей для индикаторов (накапливаем до 200 баров)
        self.klines_buffer: List[Dict] = []

    # --------------------------------------------------------------------------
    # Инициализация
    # --------------------------------------------------------------------------
    def _load_config(self, path: str) -> Dict[str, Any]:
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_logging(self):
        log_cfg = self.config.get('general', {})
        setup_logger(
            log_level=log_cfg.get('log_level', 'INFO'),
            log_file="logs/apex_v5.log"
        )

    def _init_broker(self):
        testnet = os.getenv("BINGX_TESTNET", "true").lower() == "true"
        self.broker = BingXBroker(
            api_key=os.getenv("BINGX_API_KEY"),
            api_secret=os.getenv("BINGX_API_SECRET"),
            testnet=testnet,
        )
        self.order_manager = OrderManager(self.broker, default_symbol=self.symbol)

    def _init_storage(self):
        self.storage = DataStorageManager(self.config)

    def _init_indicators(self):
        self.composite = CompositeOscillator()
        self.liquidity = LiquidityZones(
            pivot_lookback=14,
            volume_percentile=90
        )
        spotter_cfg = self.config.get('spotter', {})
        self.spotter = Spotter(
            window=spotter_cfg.get('window', 50),
            order=spotter_cfg.get('order', 5),
            max_lag=spotter_cfg.get('max_lag', 2)
        )

    def _init_models(self):
        # Hunter (CatBoost)
        hunter_model_path = self.config['paths']['models']['hunter_model']
        h_cfg = self.config.get("hunter", {}).get("model", {})
        self.hunter_model = HunterModel(
            iterations=h_cfg.get("iterations", 200),
            learning_rate=h_cfg.get("learning_rate", 0.1),
            depth=h_cfg.get("depth", 5),
        )
        if Path(hunter_model_path).exists():
            self.hunter_model.load(hunter_model_path)
        else:
            self.logger.warning(f"Hunter model not found at {hunter_model_path}, trading will be disabled.")
        self.hunter_inference = HunterInference(self.hunter_model)

        self.strategist_model = None
        self.strategist_inference = None
        if self.enable_learner:
            strat_path = self.config['paths']['models']['strategist_model']
            self.strategist_model = StrategistModel()
            if Path(strat_path).exists():
                self.strategist_model.load(strat_path)
            self.strategist_inference = StrategistInference(self.strategist_model)

    def _init_agents(self):
        self.critic = None
        if self.use_critic:
            critic_cfg = self.config['critic']
            self.critic = CriticRules(
                adx_threshold=critic_cfg['adx_threshold'],
                adx_threshold_paranoia=critic_cfg.get('adx_threshold_paranoia', 25),
                spread_multiplier=critic_cfg['spread_multiplier'],
                liquidity_distance_threshold=critic_cfg['liquidity_distance_threshold'],
                min_tick_multiplier=critic_cfg['min_tick_multiplier'],
                blocked_hours=[tuple(h) for h in critic_cfg['blocked_hours']],
                avg_spread_window=critic_cfg['avg_spread_window']
            )

        # Dispatcher
        disp_cfg = self.config['dispatcher']
        risk_cfg = disp_cfg['risk']
        paranoia_cfg = disp_cfg['paranoia_mode']
        self.dispatcher = Dispatcher(
            initial_equity=10000.0,
            base_risk=risk_cfg['base_risk'],
            target_volatility=risk_cfg['target_volatility'],
            max_leverage_normal=risk_cfg['max_leverage_normal'],
            max_leverage_paranoia=risk_cfg['max_leverage_paranoia'],
            atr_period=risk_cfg['atr_period'],
            sl_multiplier=risk_cfg['sl_multiplier'],
            hwm_threshold=paranoia_cfg.get('hwm_threshold', 0.95),
            heartbeat_timeout=disp_cfg['state_machine']['heartbeat_timeout_seconds'],
            send_order_callback=self._send_order_callback,
            cancel_order_callback=self._cancel_order_callback
        )
        self.order_manager.set_callbacks(
            on_filled=lambda _order_id, execution_price: self.dispatcher.on_order_filled(execution_price),
            on_cancelled=lambda oid: self.logger.info(f"Order {oid} cancelled"),
            on_rejected=lambda oid, reason: self.logger.error(f"Order {oid} rejected: {reason}")
        )

        self.learner = None
        if self.enable_learner:
            self.learner = Learner(
                config=self.config,
                window_storage=self.storage.window_storage,
                hunter_log=self.storage.hunter_log,
                strategist_log=self.storage.strategist_log
            )

    def stop(self) -> None:
        """Остановка цикла (из UI или API)."""
        self._running = False

    # --------------------------------------------------------------------------
    # Колбэки для Dispatcher
    # --------------------------------------------------------------------------
    def _send_order_callback(self, signal, entry_price, position_size, leverage, tp_price, sl_price):
        side = 'BUY' if signal == 'LONG' else 'SELL'
        order_id = self.order_manager.send_ioc_order(
            side=side,
            quantity=position_size / entry_price,
            price=entry_price,
            tp_price=tp_price,
            sl_price=sl_price,
            leverage=int(leverage),
            symbol=self.symbol
        )
        if order_id:
            self.dispatcher.on_order_accepted()
        return order_id

    def _cancel_order_callback(self, order_id):
        return self.order_manager.cancel_order(order_id)

    # --------------------------------------------------------------------------
    # Обновление буфера свечей и расчёт индикаторов
    # --------------------------------------------------------------------------
    '''
    def _update_klines_buffer(self):
        symbol = self.symbol
        # Если буфер пуст, загружаем сразу много свечей для старта
        if not self.klines_buffer:
            klines = self.broker.get_klines(symbol, interval=self.timeframe, limit=100)
        else:
            klines = self.broker.get_klines(symbol, interval=self.timeframe, limit=2)
        #klines = self.broker.get_klines(symbol, interval=self.timeframe, limit=2)
        self.logger.info(f"Fetched {len(klines)} klines")
        if not klines:
            self.logger.warning("No klines returned – buffer not updated")
            return
        self.logger.debug(f"Buffer updated, last bar: {klines[-1]['timestamp']}")
        latest_closed = klines[-2] if len(klines) >= 2 else klines[-1]
        if self.klines_buffer and self.klines_buffer[-1]['timestamp'] == latest_closed['timestamp']:
            return
        self.klines_buffer.append(latest_closed)
        self.logger.info(f"Buffer updated: size={len(self.klines_buffer)}")
        if len(self.klines_buffer) > 200:
            self.klines_buffer.pop(0)
    '''

    def _update_klines_buffer(self):
        try:
            symbol = self.symbol
            if not self.klines_buffer:
                limit = 100
            else:
                limit = 2
            klines = self.broker.get_klines(symbol, interval=self.timeframe, limit=limit)
            self.logger.info(
                f"Received {len(klines)} klines, first timestamp: {klines[0]['timestamp'] if klines else 'none'}")
            if not klines:
                return

            # Сортируем по времени (на случай, если API отдаёт в обратном порядке)
            klines.sort(key=lambda x: x['timestamp'])

            if not self.klines_buffer:
                # Первичное заполнение: берём все свечи, кроме последней (если она ещё не закрыта)
                # Последняя свеча может быть незавершённой, оставим её для следующего обновления
                self.klines_buffer.extend(klines[:-1])
            else:
                # Инкрементальное обновление: берём предпоследнюю закрытую свечу
                if len(klines) >= 2:
                    latest_closed = klines[-2]
                else:
                    latest_closed = klines[-1]
                if not self.klines_buffer or self.klines_buffer[-1]['timestamp'] != latest_closed['timestamp']:
                    self.klines_buffer.append(latest_closed)

            # Ограничим буфер 200 свечами
            if len(self.klines_buffer) > 200:
                self.klines_buffer = self.klines_buffer[-200:]

            self.logger.info(f"Buffer size after update: {len(self.klines_buffer)}")
        except Exception as e:
            self.logger.exception("Error in _update_klines_buffer: ", e)

    def _get_indicators_from_buffer(self) -> Optional[Dict[str, Any]]:
        if len(self.klines_buffer) < 50:
            self.logger.info(f"Buffer size {len(self.klines_buffer)} < 50, waiting...")
            return None

        df = pd.DataFrame(self.klines_buffer)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)

        n = len(df)
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        open_ = df['open'].values
        volume = df['volume'].values

        atr = calculate_atr(high, low, close, period=50)

        avg_volume = np.zeros(n)
        for i in range(n):
            start_idx = max(0, i - 19)
            avg_volume[i] = volume[start_idx:i+1].mean()

        from src.data.indicators import CompositeOscillator
        adx = CompositeOscillator._adx(high, low, close, 14)

        curves = self.composite.compute(df)
        # Реальные данные всех 19 индикаторов для Strategist
        strategist_curves = self.composite.get_all_indicators(df)

        liq_upper, liq_lower = self.liquidity.compute_series(df, atr)

        spotter_ts = set(self.spotter.get_signals(curves.long, curves.neutral, curves.short))

        return {
            'df': df,
            'n': n,
            'close': close,
            'high': high,
            'low': low,
            'open': open_,
            'volume': volume,
            'atr': atr,
            'avg_volume': avg_volume,
            'adx': adx,
            'curves': curves,
            'liq_upper': liq_upper,
            'liq_lower': liq_lower,
            'spotter_ts': spotter_ts,
            'price': close[-1],
            'current_high': high[-1],
            'current_low': low[-1],
            'spread': high[-1] - low[-1],
            'strategist_curves': strategist_curves,
        }

    # --------------------------------------------------------------------------
    # Обработка нового бара
    # --------------------------------------------------------------------------
    def process_new_bar(self):
        self._update_klines_buffer()
        ind = self._get_indicators_from_buffer()
        if ind is None:
            self.logger.debug("Buffer not ready")
            return

        i = ind['n'] - 1
        if i in ind['spotter_ts']:
            self.last_spotter = i
        if not np.isnan(ind['liq_upper']['price'][i]) and ind['current_high'] >= ind['liq_upper']['price'][i]:
            self.last_upper_touch = i
        if not np.isnan(ind['liq_lower']['price'][i]) and ind['current_low'] <= ind['liq_lower']['price'][i]:
            self.last_lower_touch = i

        max_lag = self.config['hunter']['max_lag']
        signal = None
        probs = None
        features = None
        direction = None

        # Проверяем комбинацию с верхней зоной (SHORT)
        if self.last_spotter != -1 and self.last_upper_touch != -1:
            dist = abs(self.last_spotter - self.last_upper_touch)
            self.logger.info(
                f"Spotter+upper combo possible: spotter={self.last_spotter}, upper_touch={self.last_upper_touch}, dist={dist}")
            if dist <= max_lag and max(self.last_spotter, self.last_upper_touch) == i:
                features = _collect_features(
                    i, self.last_spotter, self.last_upper_touch,
                    ind['volume'], ind['avg_volume'], ind['close'], ind['high'],
                    ind['low'], ind['open'],
                    ind['liq_upper'], ind['liq_lower'],
                    ind['adx'], ind['atr']
                )
                signal, probs = self.hunter_inference.decide(features)
                self.logger.info(f"Hunter raw signal: {signal}, probs={probs}")
                direction = 'upper'
                self.logger.info(
                   f"Loop tick: now={datetime.utcnow().strftime('%H:%M:%S')}, last_bar={self.last_bar_time.strftime('%H:%M:%S') if self.last_bar_time else 'None'}")

        # Комбинация с нижней зоной (LONG)
        if signal is None and self.last_spotter != -1 and self.last_lower_touch != -1:
            dist = abs(self.last_spotter - self.last_lower_touch)
            self.logger.info(
                f"Spotter+lower combo possible: spotter={self.last_spotter}, lower_touch={self.last_lower_touch}, dist={dist}")
            if dist <= max_lag and max(self.last_spotter, self.last_lower_touch) == i:
                features = _collect_features(
                    i, self.last_spotter, self.last_lower_touch,
                    ind['volume'], ind['avg_volume'], ind['close'], ind['high'],
                    ind['low'], ind['open'],
                    ind['liq_upper'], ind['liq_lower'],
                    ind['adx'], ind['atr']
                )
                signal, probs = self.hunter_inference.decide(features)
                self.logger.info(f"Hunter raw signal: {signal}, probs={probs}")
                direction = 'lower'
                self.logger.info(
                   f"Loop tick: now={datetime.utcnow().strftime('%H:%M:%S')}, last_bar={self.last_bar_time.strftime('%H:%M:%S') if self.last_bar_time else 'None'}")

        if signal is None or signal == "HOLD":
            return

        # Фильтр по уверенности модели (как в engine.py)
        if probs is not None and np.max(probs) < self.prob_threshold:
            self.logger.info(
                f"Signal rejected by confidence filter, max prob = {np.max(probs):.3f} "
                f"(threshold {self.prob_threshold})"
            )
            return

        self.logger.info(f"Hunter signal: {signal} with probs {probs}")

        # Расчёт TP/SL – теперь фиксированные коэффициенты, как в engine.py (TP=4.0, SL=0.8)
        entry_price = ind['price']
        atr_val = ind['atr'][-1]
        sl_mult = self.sl_atr_mult
        tp_mult = self.tp_atr_mult
        strat_features = None
        if self.enable_learner:
            strat_features = build_strategist_features(
                curves=ind['strategist_curves'],
                atr=ind['atr'],
                volume=ind['volume'],
                liq_upper=ind['liq_upper'],
                liq_lower=ind['liq_lower'],
                index=i
            )
        # tp_price, sl_price = self.strategist_inference.calculate_tp_sl(
        #    features=strat_features,
        #    entry_price=entry_price,
        #    atr=atr_val,
        #    signal=signal,
        #    sl_multiplier=sl_mult
        # )
        if signal == 'LONG':
            tp_price = entry_price + tp_mult * atr_val
            sl_price = entry_price - sl_mult * atr_val
        else:
            tp_price = entry_price - tp_mult * atr_val
            sl_price = entry_price + sl_mult * atr_val

        if self.use_critic and self.critic is not None:
            self.critic.update_spread(ind['spread'])
            passed, reason = self.critic.passes_signal(
                adx=ind['adx'][-1],
                spread=ind['spread'],
                liq_distance=0.0,
                atr=atr_val,
                signal=signal,
                entry_price=entry_price,
                tp_move_pct=abs(tp_price - entry_price) / entry_price,
                current_time=datetime.utcnow()
            )
            if not passed:
                self.logger.info(f"Critic blocked signal: {reason}")
                return

        # Dispatcher
        if not self.dispatcher.is_ready_for_signal():
            self.logger.info("Dispatcher not ready")
            return

        current_volatility = atr_val / entry_price
        success = self.dispatcher.receive_signal(
            signal=signal,
            entry_price=entry_price,
            tp_price=tp_price,
            sl_price=sl_price,
            current_volatility=current_volatility
        )
        if success:
            self.logger.info(f"Order sent: {signal}")
            if self.enable_learner and self.learner is not None:
                timestamp = datetime.utcnow()
                self.storage.log_hunter_signal(
                    timestamp=timestamp,
                    window_3d=np.random.randn(20, 4),
                    hunter_probs=probs,
                    features=features,
                    label=None
                )
                if strat_features is not None:
                    self.storage.log_strategist_signal(
                        timestamp=timestamp,
                        features_flat=strat_features,
                        predicted_tp_pct=abs(tp_price - entry_price) / entry_price
                    )

    # --------------------------------------------------------------------------
    # Главный цикл
    # --------------------------------------------------------------------------
    def run(self):
        self.logger.info("Apex V5 Global started (Spotter + CatBoost Hunter + CatBoost Strategist)")
        self.logger.info(f"Symbol: {self.symbol}, Timeframe: {self.timeframe}")

        while self._running:
            #self.logger.info(
            #    f"Loop tick: now={datetime.utcnow().strftime('%H:%M:%S')}, last_bar={self.last_bar_time.strftime('%H:%M:%S') if self.last_bar_time else 'None'}")
            now = datetime.utcnow()

            # Всегда пытаемся обновить буфер (наполнение первыми 100 свечами уже произошло, дальше будет по 1)
            #self._update_klines_buffer()

            # Вычисляем время окончания последнего завершённого 15-минутного бара
            current_minute = now.minute
            completed_minute = (current_minute // 15) * 15  # начало последнего завершённого бара
            bar_end = now.replace(minute=completed_minute, second=0,
                                  microsecond=0)  # это и есть время окончания последнего бара
            bar_start = bar_end - timedelta(minutes=15)

            #self.logger.info(
            #    f"Check: now={now.strftime('%H:%M:%S')}, bar_end={bar_end.strftime('%H:%M:%S')}, last_bar={self.last_bar_time.strftime('%H:%M:%S') if self.last_bar_time else 'None'}, condition={now >= bar_end}")

            # Если этот завершённый бар ещё не обработан – обрабатываем
            if self.last_bar_time is None or bar_end > self.last_bar_time:
                self.logger.info(f"Processing completed bar: start={bar_start}, end={bar_end}")
                try:
                    self.process_new_bar()
                    self.last_bar_time = bar_end  # запоминаем время окончания обработанного бара
                except Exception as e:
                    self.logger.exception(f"Error in process_new_bar: {e}")

            # Запуск Learner раз в час
            if self.enable_learner and self.learner is not None:
                if (now - self.last_learner_run).total_seconds() >= 3600:
                    try:
                        self.learner.run()
                        self.last_learner_run = now
                    except Exception as e:
                        self.logger.exception(f"Learner error: {e}")

            time.sleep(30)

        self.logger.info("Shutdown complete")
        self.storage.close()


def main() -> None:
    app = ApexV5Live(register_signals=False)

    def _cli_stop(sig, frame):
        app.stop()

    signal.signal(signal.SIGINT, _cli_stop)
    signal.signal(signal.SIGTERM, _cli_stop)
    app.run()


if __name__ == "__main__":
    main()
