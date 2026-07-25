"""
tests/test_dispatcher.py
Модульные тесты для агента Dispatcher (src/agents/dispatcher.py).
Проверяет расчёт риска, управление состоянием, Paranoia Mode и колбэки.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch

from src.agents.dispatcher import Dispatcher, TradingState


class TestDispatcherRisk:
    def test_calculate_position_normal(self):
        disp = Dispatcher(initial_equity=10000.0)
        lev, size, risk = disp.calculate_position(
            entry_price=50000.0,
            sl_price=49000.0,
            current_volatility=0.02
        )
        # stop_loss_pct = 1000/50000 = 0.02 (2%)
        # risk_per_trade = 0.005 * (0.2 / 0.02) = 0.005 * 10 = 0.05 (5%)
        # leverage = min(3.0, 0.05 / 0.02) = min(3.0, 2.5) = 2.5
        # position_size = 10000 * 2.5 = 25000
        assert lev == 2.5
        assert size == 25000.0
        assert risk == 0.05

    def test_leverage_cap(self):
        disp = Dispatcher(initial_equity=10000.0, max_leverage_normal=3.0)
        lev, size, risk = disp.calculate_position(
            entry_price=50000.0,
            sl_price=49900.0,  # sl_pct = 0.2%
            current_volatility=0.02
        )
        # risk_per_trade = 0.005 * (0.2/0.02) = 0.05
        # leverage без кэпа = 0.05 / 0.002 = 25.0, но max=3.0
        assert lev == 3.0
        assert size == 30000.0

    def test_paranoia_mode_reduces_leverage(self):
        disp = Dispatcher(initial_equity=10000.0, max_leverage_paranoia=1.5)
        # Вручную включаем паранойю через HWM трекер
        disp.hwm_tracker.update(9500)  # current < HWM*0.95 (изначально HWM=10000)
        assert disp.paranoia_mode is True
        lev, size, risk = disp.calculate_position(50000.0, 49000.0, 0.02)
        # risk_per_trade = 0.05, stop_loss_pct=0.02, lev = min(1.5, 2.5) = 1.5
        assert lev == 1.5
        assert size == 15000.0


class TestDispatcherStateMachine:
    def setup_method(self):
        self.send_mock = Mock(return_value="order_123")
        self.cancel_mock = Mock(return_value=True)
        self.disp = Dispatcher(
            initial_equity=10000.0,
            send_order_callback=self.send_mock,
            cancel_order_callback=self.cancel_mock
        )

    def test_initial_state(self):
        assert self.disp.state == TradingState.IDLE
        assert self.disp.is_ready_for_signal() is True

    def test_receive_signal_transitions(self):
        success = self.disp.receive_signal(
            signal='LONG',
            entry_price=50000.0,
            tp_price=51000.0,
            sl_price=49000.0,
            current_volatility=0.02
        )
        assert success is True
        assert self.disp.state == TradingState.ORDER_SENT
        self.send_mock.assert_called_once()
        assert self.disp._current_order_id == "order_123"

    def test_order_accepted_to_await_fill(self):
        self.disp.receive_signal('LONG', 50000.0, 51000.0, 49000.0, 0.02)
        self.disp.on_order_accepted()
        assert self.disp.state == TradingState.AWAIT_FILL

    def test_order_filled_to_in_position(self):
        self.disp.receive_signal('LONG', 50000.0, 51000.0, 49000.0, 0.02)
        self.disp.on_order_accepted()
        self.disp.on_order_filled(50010.0)
        assert self.disp.state == TradingState.IN_POSITION
        assert self.disp.current_position['entry_price'] == 50010.0

    def test_position_closed_resets_state(self):
        self.disp.receive_signal('LONG', 50000.0, 51000.0, 49000.0, 0.02)
        self.disp.on_order_accepted()
        self.disp.on_order_filled(50010.0)
        initial_equity = self.disp.equity
        self.disp.on_position_closed(pnl=100.0)
        assert self.disp.state == TradingState.IDLE
        assert self.disp.equity == initial_equity + 100.0

    def test_cannot_receive_signal_when_not_idle(self):
        self.disp.receive_signal('LONG', 50000.0, 51000.0, 49000.0, 0.02)
        assert self.disp.state != TradingState.IDLE
        success = self.disp.receive_signal('LONG', 50000.0, 51000.0, 49000.0, 0.02)
        assert success is False


class TestHeartbeat:
    def setup_method(self):
        self.send_mock = Mock(return_value="order_123")
        self.cancel_mock = Mock(return_value=True)
        self.disp = Dispatcher(
            initial_equity=10000.0,
            send_order_callback=self.send_mock,
            cancel_order_callback=self.cancel_mock,
            heartbeat_timeout=0.2  # короткий таймаут для теста
        )

    def test_heartbeat_cancels_order(self):
        self.disp.receive_signal('LONG', 50000.0, 51000.0, 49000.0, 0.02)
        self.disp.on_order_accepted()
        assert self.disp.state == TradingState.AWAIT_FILL
        # Ждём срабатывания таймера
        time.sleep(0.3)
        # Таймер должен был вызвать cancel_order_callback и сбросить состояние
        self.cancel_mock.assert_called_with("order_123")
        assert self.disp.state == TradingState.IDLE


class TestHighWaterMarkIntegration:
    def test_paranoia_activation(self):
        disp = Dispatcher(initial_equity=10000.0, hwm_threshold=0.95)
        # Изначально не паранойя
        assert disp.paranoia_mode is False
        # Обновляем эквити ниже порога
        disp.update_equity(9400.0)  # 9400 < 10000*0.95 = 9500
        assert disp.paranoia_mode is True

    def test_paranoia_deactivation_after_recovery(self):
        disp = Dispatcher(initial_equity=10000.0, hwm_threshold=0.95)
        disp.update_equity(9400.0)
        assert disp.paranoia_mode is True
        disp.update_equity(9800.0)
        # HWM остался 10000, 9800 > 9500 -> паранойя выключается
        assert disp.paranoia_mode is False

    def test_hwm_updates(self):
        disp = Dispatcher(initial_equity=10000.0)
        disp.update_equity(11000.0)
        assert disp.hwm_tracker.hwm == 11000.0
        disp.update_equity(10500.0)
        assert disp.hwm_tracker.hwm == 11000.0