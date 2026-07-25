"""
tests/test_utils.py
Модульные тесты для вспомогательных функций src/utils/helpers.py.
Проверяет корректность расчётов ATR, нормализации, HighWaterMark и риск-менеджмента.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timezone

from src.utils.helpers import (
    calculate_atr,
    RollingZScoreScaler,
    is_blocked_time,
    HighWaterMarkTracker,
    calculate_fixed_fractional_risk,
    flatten_window,
    reconstruct_window,
)


class TestCalculateATR:
    def test_basic_calculation(self):
        high = np.array([10, 11, 12, 13, 14])
        low = np.array([9, 10, 11, 12, 13])
        close = np.array([9.5, 10.5, 11.5, 12.5, 13.5])
        atr = calculate_atr(high, low, close, period=3)
        # Ожидаем, что длина совпадает и значения неотрицательны
        assert len(atr) == 5
        assert np.all(atr >= 0)

    def test_period_50_default(self):
        # Проверяем, что функция работает с period=50 (как в документации)
        np.random.seed(42)
        n = 100
        price = 100 + np.cumsum(np.random.randn(n))
        high = price + np.abs(np.random.randn(n) * 0.5)
        low = price - np.abs(np.random.randn(n) * 0.5)
        close = price
        atr = calculate_atr(high, low, close, period=50)
        assert len(atr) == n
        # ATR должен быть сглаженным и положительным
        assert np.all(atr > 0)


class TestRollingZScoreScaler:
    def test_update_and_normalize(self):
        scaler = RollingZScoreScaler(window=5)
        values = [1, 2, 3, 4, 5, 6, 7]
        normalized = []
        for v in values:
            normalized.append(scaler.update(v))
        # После накопления достаточной истории значения должны быть около 0 с std=1
        assert len(scaler.history) == 5
        last_five = values[-5:]
        mean = np.mean(last_five)
        std = np.std(last_five)
        expected_last = (7 - mean) / std if std > 0 else 0.0
        assert np.isclose(normalized[-1], expected_last)

    def test_normalize_array(self):
        scaler = RollingZScoreScaler(window=3)
        for v in [1, 2, 3]:
            scaler.update(v)
        arr = np.array([2, 3, 4])
        norm = scaler.normalize_array(arr)
        mean = np.mean([1, 2, 3])
        std = np.std([1, 2, 3])
        expected = (arr - mean) / std if std > 0 else arr
        np.testing.assert_array_almost_equal(norm, expected)


class TestIsBlockedTime:
    def test_blocked_hours_utc(self):
        # 00:00-01:00 UTC должно быть заблокировано
        dt_blocked = datetime(2024, 1, 1, 0, 30, tzinfo=timezone.utc)
        assert is_blocked_time(dt_blocked, [(0, 1)]) is True
        dt_allowed = datetime(2024, 1, 1, 1, 30, tzinfo=timezone.utc)
        assert is_blocked_time(dt_allowed, [(0, 1)]) is False

    def test_no_blocked_hours(self):
        dt = datetime.now(timezone.utc)
        assert is_blocked_time(dt, []) is False


class TestHighWaterMarkTracker:
    def test_initialization(self):
        tracker = HighWaterMarkTracker(10000)
        assert tracker.current == 10000
        assert tracker.hwm == 10000

    def test_update_hwm(self):
        tracker = HighWaterMarkTracker(10000)
        tracker.update(10500)
        assert tracker.hwm == 10500
        tracker.update(10200)
        assert tracker.hwm == 10500
        assert tracker.current == 10200

    def test_paranoia_threshold(self):
        tracker = HighWaterMarkTracker(10000)
        tracker.update(10500)  # HWM = 10500
        tracker.update(10000)  # current = 10000, что < 10500*0.95 = 9975? нет
        assert tracker.is_paranoia(0.95) is False
        tracker.update(9900)   # 9900 < 9975 -> True
        assert tracker.is_paranoia(0.95) is True


class TestCalculateFixedFractionalRisk:
    def test_basic_calculation(self):
        equity = 10000
        base_risk = 0.005
        target_vol = 0.20
        current_vol = 0.25
        stop_loss_pct = 0.02
        max_lev = 3.0
        risk, lev, pos_size = calculate_fixed_fractional_risk(
            equity, base_risk, target_vol, current_vol, stop_loss_pct, max_lev
        )
        expected_risk = base_risk * (target_vol / current_vol)  # 0.005 * 0.8 = 0.004
        expected_lev = min(max_lev, expected_risk / stop_loss_pct)  # 0.004 / 0.02 = 0.2, min(3,0.2)=0.2
        expected_pos = equity * expected_lev
        assert np.isclose(risk, expected_risk)
        assert np.isclose(lev, expected_lev)
        assert np.isclose(pos_size, expected_pos)

    def test_leverage_cap(self):
        # При очень маленьком стоп-лоссе плечо ограничивается max_leverage
        risk, lev, pos_size = calculate_fixed_fractional_risk(
            10000, 0.005, 0.2, 0.2, 0.001, 3.0
        )
        # risk_per_trade = 0.005, stop_loss=0.001 -> leverage = 5.0, но max=3.0
        assert lev == 3.0
        assert pos_size == 30000.0

    def test_zero_volatility_protection(self):
        # Если current_volatility=0, должно использоваться target_volatility
        risk, lev, pos_size = calculate_fixed_fractional_risk(
            10000, 0.005, 0.2, 0.0, 0.01, 3.0
        )
        assert risk == 0.005  # base_risk * (0.2 / 0.2)
        assert lev == min(3.0, 0.005 / 0.01)  # 0.5
        assert pos_size == 5000.0


class TestWindowFlatten:
    def test_flatten_reconstruct(self):
        window = np.random.randn(20, 4).astype(np.float32)
        flat = flatten_window(window)
        assert flat.shape == (80,)
        reconstructed = reconstruct_window(flat, (20, 4))
        np.testing.assert_array_almost_equal(window, reconstructed)