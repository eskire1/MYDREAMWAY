"""
tests/test_strategist.py
Модульные тесты для агента Strategist (src/agents/strategist.py).
Проверяет модель CatBoost, инференс, расчёт TP/SL, сохранение/загрузку.
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path

from src.agents.strategist import StrategistModel, StrategistInference


class TestStrategistModel:
    def test_init_default(self):
        model = StrategistModel()
        assert model.loss_function == 'Quantile:alpha=0.8'
        assert model.iterations == 500
        assert model.learning_rate == 0.03
        assert model.depth == 6

    def test_fit_and_predict(self):
        model = StrategistModel(iterations=10)  # мало итераций для теста
        X = np.random.randn(100, 80).astype(np.float32)
        y = np.abs(np.random.randn(100)).astype(np.float32) * 0.05
        model.fit(X, y)
        preds = model.predict(X[:10])
        assert preds.shape == (10,)
        assert np.all(preds >= 0)  # экскурсия положительная

    def test_partial_fit(self):
        model = StrategistModel(iterations=10)
        X = np.random.randn(100, 80).astype(np.float32)
        y = np.abs(np.random.randn(100)).astype(np.float32) * 0.05
        model.fit(X[:50], y[:50])
        model.partial_fit(X[50:], y[50:], epochs=5)
        preds = model.predict(X)
        assert preds.shape == (100,)

    def test_save_load(self):
        model = StrategistModel(iterations=10)
        X = np.random.randn(100, 80).astype(np.float32)
        y = np.abs(np.random.randn(100)).astype(np.float32) * 0.05
        model.fit(X, y)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "strat.cbm"
            model.save(str(path))
            assert path.exists()

            loaded = StrategistModel()
            loaded.load(str(path))
            preds_orig = model.predict(X)
            preds_loaded = loaded.predict(X)
            np.testing.assert_array_almost_equal(preds_orig, preds_loaded)

    def test_predict_single(self):
        model = StrategistModel(iterations=10)
        X = np.random.randn(100, 80).astype(np.float32)
        y = np.abs(np.random.randn(100)).astype(np.float32) * 0.05
        model.fit(X, y)
        single = X[0]
        pred = model.predict_single(single)
        assert isinstance(pred, float)
        assert pred >= 0


class TestStrategistInference:
    def setup_method(self):
        model = StrategistModel(iterations=10)
        X = np.random.randn(100, 80).astype(np.float32)
        y = np.abs(np.random.randn(100)).astype(np.float32) * 0.05
        model.fit(X, y)
        self.inference = StrategistInference(model)

    def test_predict_tp_move(self):
        features = np.random.randn(80).astype(np.float32)
        tp = self.inference.predict_tp_move(features)
        assert isinstance(tp, float)
        assert tp >= 0

    def test_calculate_tp_sl_long(self):
        features = np.random.randn(80).astype(np.float32)
        entry = 50000.0
        atr = 500.0
        tp_move = self.inference.predict_tp_move(features)
        tp, sl = self.inference.calculate_tp_sl(features, entry, atr, 'LONG', sl_multiplier=1.5)
        assert tp > entry
        assert sl < entry
        expected_tp = entry * (1 + tp_move)
        expected_sl = entry - atr * 1.5
        assert np.isclose(tp, expected_tp)
        assert np.isclose(sl, expected_sl)

    def test_calculate_tp_sl_short(self):
        features = np.random.randn(80).astype(np.float32)
        entry = 50000.0
        atr = 500.0
        tp_move = self.inference.predict_tp_move(features)
        tp, sl = self.inference.calculate_tp_sl(features, entry, atr, 'SHORT', sl_multiplier=1.5)
        assert tp < entry
        assert sl > entry
        expected_tp = entry * (1 - tp_move)
        expected_sl = entry + atr * 1.5
        assert np.isclose(tp, expected_tp)
        assert np.isclose(sl, expected_sl)