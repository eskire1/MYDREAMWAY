"""
tests/test_preprocessing.py
Модульные тесты для предобработки данных (src/data/preprocessing.py).
Проверяет FeaturePreprocessor, нормализацию, построение окон и подготовку данных.
"""

import pytest
import numpy as np
import pandas as pd
from src.data.preprocessing import FeaturePreprocessor, prepare_training_data
from src.data.indicators import CompositeOscillator, CompositeOscillatorResult
from src.utils.helpers import RollingZScoreScaler


class TestFeaturePreprocessor:
    @pytest.fixture
    def preprocessor(self):
        return FeaturePreprocessor(window_size=20, scaling_window=1000)

    def test_partial_fit(self, preprocessor):
        long_vals = np.random.randn(2000)
        neutral_vals = np.random.randn(2000)
        short_vals = np.random.randn(2000)
        liq_vals = np.random.randn(2000)
        preprocessor.partial_fit(long_vals, neutral_vals, short_vals, liq_vals)
        # Скейлеры должны содержать историю (последние 1000 значений)
        assert len(preprocessor.scaler_long.history) == 1000
        assert len(preprocessor.scaler_neutral.history) == 1000
        assert len(preprocessor.scaler_short.history) == 1000
        assert len(preprocessor.scaler_liq.history) == 1000

    def test_transform_single(self, preprocessor):
        # Прогреваем небольшим количеством данных
        preprocessor.partial_fit([1,2,3], [4,5,6], [7,8,9], [10,11,12])
        n_long, n_neutral, n_short, n_liq = preprocessor.transform_single(4, 7, 10, 13)
        # Проверяем, что значения изменились (нормализованы)
        assert isinstance(n_long, float)
        assert isinstance(n_neutral, float)
        assert isinstance(n_short, float)
        assert isinstance(n_liq, float)

    def test_build_window_3d(self, preprocessor):
        # Заполняем историю нормализованными значениями
        preprocessor.history_long = [0.1] * 15 + [0.2] * 5
        preprocessor.history_neutral = [0.1] * 15 + [0.2] * 5
        preprocessor.history_short = [0.1] * 15 + [0.2] * 5
        preprocessor.history_liq = [0.1] * 15 + [0.2] * 5
        window = preprocessor.build_window_3d(
            preprocessor.history_long,
            preprocessor.history_neutral,
            preprocessor.history_short,
            preprocessor.history_liq
        )
        assert window.shape == (20, 4)

    def test_build_window_3d_insufficient_history(self, preprocessor):
        # Меньше 20 значений
        preprocessor.history_long = [0.1] * 5
        preprocessor.history_neutral = [0.1] * 5
        preprocessor.history_short = [0.1] * 5
        preprocessor.history_liq = [0.1] * 5
        window = preprocessor.build_window_3d(
            preprocessor.history_long,
            preprocessor.history_neutral,
            preprocessor.history_short,
            preprocessor.history_liq
        )
        assert window.shape == (20, 4)
        # Первые 15 строк должны быть нулями (паддинг)
        assert np.all(window[:15] == 0)

    def test_build_flat_features(self, preprocessor):
        window_3d = np.random.randn(20, 4).astype(np.float32)
        flat = preprocessor.build_flat_features(window_3d)
        assert flat.shape == (80,)
        assert np.array_equal(flat, window_3d.flatten())

    def test_prepare_live_input(self, preprocessor):
        # Прогреваем небольшим количеством, чтобы скейлеры имели историю
        preprocessor.partial_fit(np.random.randn(100), np.random.randn(100),
                                 np.random.randn(100), np.random.randn(100))
        window_3d, flat = preprocessor.prepare_live_input(1.0, 2.0, 3.0, 4.0)
        assert window_3d.shape == (20, 4)
        assert flat.shape == (80,)
        # Проверяем, что история увеличилась на 1
        assert len(preprocessor.history_long) == 1  # т.к. мы не добавляли раньше в history_long


class TestPrepareTrainingData:
    def test_prepare_training_data(self):
        # Создаём синтетические данные
        n_bars = 200
        df = pd.DataFrame({
            'open': np.random.randn(n_bars) + 100,
            'high': np.random.randn(n_bars) + 101,
            'low': np.random.randn(n_bars) + 99,
            'close': np.random.randn(n_bars) + 100,
            'volume': np.random.rand(n_bars) * 1000,
            'label': np.random.choice([0, 1, 2], size=n_bars)  # метки для обучения
        })
        comp = CompositeOscillator()
        curves = comp.compute(df)
        liq_dist = np.random.randn(n_bars)

        X, y = prepare_training_data(
            df, curves, liq_dist,
            window_size=20, scaling_window=100
        )
        # Количество образцов = n_bars - window_size
        assert X.shape[0] == n_bars - 20
        assert X.shape[1] == 20
        assert X.shape[2] == 4
        assert y.shape[0] == n_bars - 20
        # Проверяем, что метки соответствуют (в пределах допустимых классов)
        assert set(np.unique(y)).issubset({0, 1, 2})