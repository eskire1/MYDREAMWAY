"""
tests/test_critic.py
Модульные тесты для агента Critic (src/agents/critic.py).
Проверяет статистические фильтры, пороги и Paranoia Mode.
"""

import pytest
import numpy as np
from datetime import datetime, timezone

from src.agents.critic import CriticRules


class TestCriticRules:
    def setup_method(self):
        self.critic = CriticRules(
            adx_threshold=20.0,
            adx_threshold_paranoia=25.0,
            spread_multiplier=1.5,
            liquidity_distance_threshold=2.0,
            min_tick_multiplier=3.0,
            blocked_hours=[(0, 1)],
            avg_spread_window=100,
            atr_period=50
        )

    def test_passes_all_conditions(self):
        # Заполняем историю спреда
        for _ in range(100):
            self.critic.update_spread(10.0)
        passed, reason = self.critic.passes(
            adx=25.0,
            spread=12.0,
            liq_distance=1.5,
            atr=100.0,
            target_price=1050.0,
            entry_price=1000.0,
            current_time=datetime(2024, 1, 1, 2, 0, tzinfo=timezone.utc)
        )
        assert passed is True
        assert reason == "Passed"

    def test_blocks_low_adx_high_spread(self):
        for _ in range(100):
            self.critic.update_spread(10.0)
        passed, reason = self.critic.passes(
            adx=15.0,           # < 20
            spread=20.0,        # > 1.5 * 10 = 15
            liq_distance=1.0,
            atr=100.0,
            target_price=1050.0,
            entry_price=1000.0,
            current_time=datetime(2024, 1, 1, 2, 0, tzinfo=timezone.utc)
        )
        assert passed is False
        assert "Low ADX" in reason

    def test_blocks_liquidity_distance(self):
        for _ in range(100):
            self.critic.update_spread(10.0)
        passed, reason = self.critic.passes(
            adx=25.0,
            spread=12.0,
            liq_distance=3.0,   # > 2.0 * ATR = 200 (atr=100) -> |liq_distance|=3.0 сравнивается с threshold=2.0, но в коде сравнивается abs(liq_distance) > threshold * atr? В реализации Critic.passes() сравнивается abs(liq_distance) > self.liquidity_distance_threshold * atr. Здесь liq_distance уже в единицах ATR? По документации liq_distance подаётся в ATR. Тогда порог 2.0 означает 2.0*ATR. Проверим: liq_distance=3.0, порог=2.0 -> 3.0 > 2.0 -> True блокировка.
            atr=100.0,
            target_price=1050.0,
            entry_price=1000.0,
            current_time=datetime(2024, 1, 1, 2, 0, tzinfo=timezone.utc)
        )
        assert passed is False
        assert "liquidity" in reason.lower()

    def test_blocks_minimum_tick(self):
        for _ in range(100):
            self.critic.update_spread(10.0)
        passed, reason = self.critic.passes(
            adx=25.0,
            spread=12.0,
            liq_distance=1.0,
            atr=100.0,
            target_price=1005.0,   # движение 5
            entry_price=1000.0,
            current_time=datetime(2024, 1, 1, 2, 0, tzinfo=timezone.utc)
        )
        # avg_spread=10, min_tick_multiplier=3 -> 30
        assert passed is False
        assert "Expected move" in reason

    def test_blocks_time_of_day(self):
        for _ in range(100):
            self.critic.update_spread(10.0)
        passed, reason = self.critic.passes(
            adx=25.0,
            spread=12.0,
            liq_distance=1.0,
            atr=100.0,
            target_price=1050.0,
            entry_price=1000.0,
            current_time=datetime(2024, 1, 1, 0, 30, tzinfo=timezone.utc)  # 00:30 UTC
        )
        assert passed is False
        assert "Blocked trading hours" in reason

    def test_paranoia_mode(self):
        self.critic.set_paranoia_mode(True)
        for _ in range(100):
            self.critic.update_spread(10.0)
        # ADX=22, в обычном режиме проходит (>=20), в паранойе должно быть >=25
        passed, reason = self.critic.passes(
            adx=22.0,
            spread=12.0,
            liq_distance=1.0,
            atr=100.0,
            target_price=1050.0,
            entry_price=1000.0,
            current_time=datetime(2024, 1, 1, 2, 0, tzinfo=timezone.utc)
        )
        assert passed is False
        assert "Low ADX" in reason

        # Увеличиваем ADX до 26
        passed, reason = self.critic.passes(
            adx=26.0,
            spread=12.0,
            liq_distance=1.0,
            atr=100.0,
            target_price=1050.0,
            entry_price=1000.0,
            current_time=datetime(2024, 1, 1, 2, 0, tzinfo=timezone.utc)
        )
        assert passed is True

    def test_passes_signal_wrapper(self):
        for _ in range(100):
            self.critic.update_spread(10.0)
        passed, reason = self.critic.passes_signal(
            adx=25.0,
            spread=12.0,
            liq_distance=1.0,
            atr=100.0,
            signal='LONG',
            entry_price=1000.0,
            tp_move_pct=0.05,
            current_time=datetime(2024, 1, 1, 2, 0, tzinfo=timezone.utc)
        )
        assert passed is True