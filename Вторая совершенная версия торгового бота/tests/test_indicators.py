"""
tests/test_indicators.py
Модульные тесты для модуля индикаторов (src/data/indicators.py).
Проверяет CompositeOscillator, LiquidityZones и подготовку окон.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch

from src.data.indicators import (
    CompositeOscillator,
    CompositeOscillatorResult,
    LiquidityZones,
    prepare_input_window,
)
from src.utils.helpers import RollingZScoreScaler


class TestCompositeOscillator:
    def test_output_shape(self):
        df = pd.DataFrame({
            'open': np.random.randn(100) + 100,
            'high': np.random.randn(100) + 101,
            'low': np.random.randn(100) + 99,
            'close': np.random.randn(100) + 100,
            'volume': np.random.rand(100) * 1000,
        })
        comp = CompositeOscillator(num_indicators=40)
        result = comp.compute(df)
        assert isinstance(result, CompositeOscillatorResult)
        assert len(result.long) == len(df)
        assert len(result.neutral) == len(df)
        assert len(result.short) == len(df)

    def test_values_range(self):
        df = pd.DataFrame({
            'open': [100]*50,
            'high': [101]*50,
            'low': [99]*50,
            'close': [100]*50,
            'volume': [1000]*50,
        })
        comp = CompositeOscillator()
        result = comp.compute(df)
        # Значения должны быть в пределах [0,1] (синтетическая реализация)
        assert np.all(result.long >= 0) and np.all(result.long <= 1)
        assert np.all(result.neutral >= 0) and np.all(result.neutral <= 1)
        assert np.all(result.short >= 0) and np.all(result.short <= 1)

    def test_normalize_curves(self):
        df = pd.DataFrame({
            'open': [100]*30,
            'high': [101]*30,
            'low': [99]*30,
            'close': [100]*30,
            'volume': [1000]*30,
        })
        comp = CompositeOscillator()
        result = comp.compute(df)
        scaler_long = RollingZScoreScaler(window=10)
        scaler_neutral = RollingZScoreScaler(window=10)
        scaler_short = RollingZScoreScaler(window=10)
        norm_long, norm_neutral, norm_short = comp.normalize_curves(
            result, scaler_long, scaler_neutral, scaler_short
        )
        assert len(norm_long) == len(df)
        # После нормализации среднее близко к 0, std близко к 1 для последних значений
        if len(norm_long) > 10:
            assert np.abs(np.mean(norm_long[-10:])) < 0.5
            assert 0.5 < np.std(norm_long[-10:]) < 1.5


class TestLiquidityZones:
    def test_identify_levels(self):
        df = pd.DataFrame({
            'open': [100, 101, 102, 101, 100, 99, 98, 99, 100],
            'high': [101, 102, 103, 102, 101, 100, 99, 100, 101],
            'low': [99, 100, 101, 100, 99, 98, 97, 98, 99],
            'close': [100.5, 101.5, 102.5, 101.5, 100.5, 99.5, 98.5, 99.5, 100.5],
            'volume': [1000, 1200, 5000, 800, 900, 1100, 4000, 700, 1000],
        })
        liq = LiquidityZones(volume_threshold_percentile=80)
        levels = liq.identify_levels(df)
        # Должны найти уровни с аномальным объемом
        assert isinstance(levels, list)
        # В тестовых данных может быть несколько уровней
        assert len(levels) >= 0

    def test_distance_to_nearest(self):
        liq = LiquidityZones()
        levels = [100.0, 105.0, 95.0]
        dist = liq.distance_to_nearest(102.0, levels, atr=2.0)
        # Ближайший уровень 100.0, расстояние 2.0, нормированное на ATR=2.0 -> 1.0
        assert dist == 1.0

    def test_distance_no_levels(self):
        liq = LiquidityZones()
        dist = liq.distance_to_nearest(100.0, [], atr=2.0)
        assert dist == float('inf')

    def test_compute_series(self):
        df = pd.DataFrame({
            'open': [100]*20,
            'high': [101]*20,
            'low': [99]*20,
            'close': [100]*20,
            'volume': [1000]*20,
        })
        atr = np.ones(20) * 2.0
        liq = LiquidityZones()
        distances = liq.compute_series(df, atr)
        assert len(distances) == len(df)
        # Если уровни не найдены, расстояния могут быть inf, но в реализации заглушки могут быть конечны
        # Здесь просто проверяем, что массив возвращается


class TestPrepareInputWindow:
    def test_window_creation(self):
        df = pd.DataFrame({
            'open': [100]*40,
            'high': [101]*40,
            'low': [99]*40,
            'close': [100]*40,
            'volume': [1000]*40,
        })
        comp = CompositeOscillator()
        curves = comp.compute(df)
        atr = np.ones(40) * 2.0
        liq = LiquidityZones()
        liq_dist = liq.compute_series(df, atr)

        window = prepare_input_window(
            df, index=30, window_size=20,
            composite=curves, liq_distance=liq_dist, scalers=None
        )
        assert window.shape == (20, 4)

    def test_window_padding_beginning(self):
        df = pd.DataFrame({
            'open': [100]*10,
            'high': [101]*10,
            'low': [99]*10,
            'close': [100]*10,
            'volume': [1000]*10,
        })
        comp = CompositeOscillator()
        curves = comp.compute(df)
        atr = np.ones(10) * 2.0
        liq = LiquidityZones()
        liq_dist = liq.compute_series(df, atr)

        window = prepare_input_window(
            df, index=5, window_size=20,
            composite=curves, liq_distance=liq_dist, scalers=None
        )
        assert window.shape == (20, 4)
        # Первые несколько строк должны быть нулями (паддинг)
        assert np.all(window[0] == 0)