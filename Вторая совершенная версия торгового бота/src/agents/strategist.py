"""
src/agents/strategist.py
Агент Strategist: прогноз динамического тейк-профита.
Модель: CatBoostRegressor с квантильной функцией потерь (Quantile:alpha=0.8).
Вход: значения всех 19 индикаторов композитного осциллятора + ATR + объём + данные ликвидности.
Выход: прогнозируемое процентное движение цены до следующего разворота.
"""

import os
import numpy as np
from typing import Optional, Tuple, Dict, Any
from catboost import CatBoostRegressor
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StrategistModel:
    """Обёртка над CatBoostRegressor для прогноза экскурсии цены."""

    def __init__(self, iterations: int = 500, learning_rate: float = 0.03, depth: int = 6):
        self.model = CatBoostRegressor(
            loss_function='Quantile:alpha=0.8',
            iterations=iterations,
            learning_rate=learning_rate,
            depth=depth,
            verbose=False,
            allow_writing_files=False
        )
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray, eval_set: Optional[Tuple] = None):
        self.model.fit(X, y, eval_set=eval_set)
        self._fitted = True

    def partial_fit(self, X: np.ndarray, y: np.ndarray, epochs: int = 5):
        if not self._fitted:
            self.fit(X, y)
        else:
            self.model.fit(X, y, init_model=self.model)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.model.save_model(path)

    def load(self, path: str):
        self.model.load_model(path)
        self._fitted = True


def build_strategist_features(
    curves: Dict[str, np.ndarray],      # словарь с массивами всех 19 индикаторов
    atr: np.ndarray,
    volume: np.ndarray,
    liq_upper: Dict[str, np.ndarray],
    liq_lower: Dict[str, np.ndarray],
    index: int
) -> np.ndarray:
    """
    Формирует вектор признаков для одного бара (index) для Strategist.
    curves должен содержать ключи: 'rsi', 'macd', 'stoch_k', 'bb_upper', 'bb_lower',
    'adx', 'vol_osc', 'atr', 'zscore', 'corr', 'cov', 'cci', 'momentum',
    'chande', 'fib', 'quantile', 'ml_signal', 'normal_z', 'sharpe', 'gauss_prob'.
    """
    feats = [
        curves['rsi'][index],
        curves['macd_line'][index],
        curves['stoch_k'][index],
        curves['bb_upper'][index],
        curves['bb_lower'][index],
        curves['adx'][index],
        curves['vol_osc'][index],
        curves['atr'][index],
        curves['zscore'][index],
        curves['corr'][index],
        curves['cov'][index],
        curves['cci'][index],
        curves['momentum'][index],
        curves['chande'][index],
        curves['fib'][index],
        curves['quantile'][index],
        curves['ml_signal'][index],
        curves['normal_z'][index],
        curves['sharpe'][index],
        curves['gauss_prob'][index],
        atr[index] if atr is not None else 0.0,
        volume[index],
        liq_upper['volume'][index] if not np.isnan(liq_upper['volume'][index]) else 0.0,
        liq_upper['width'][index] if not np.isnan(liq_upper['width'][index]) else 0.0,
        liq_upper['count'][index] if not np.isnan(liq_upper['count'][index]) else 0.0,
        liq_upper['overlap_pts'][index] if not np.isnan(liq_upper['overlap_pts'][index]) else 0.0,
        liq_upper['overlap_pct'][index] if not np.isnan(liq_upper['overlap_pct'][index]) else 0.0,
        liq_lower['volume'][index] if not np.isnan(liq_lower['volume'][index]) else 0.0,
        liq_lower['width'][index] if not np.isnan(liq_lower['width'][index]) else 0.0,
        liq_lower['count'][index] if not np.isnan(liq_lower['count'][index]) else 0.0,
        liq_lower['overlap_pts'][index] if not np.isnan(liq_lower['overlap_pts'][index]) else 0.0,
        liq_lower['overlap_pct'][index] if not np.isnan(liq_lower['overlap_pct'][index]) else 0.0,
    ]
    return np.array(feats, dtype=np.float32)


class StrategistInference:
    """Интерфейс для получения прогноза TP."""

    def __init__(self, model: StrategistModel):
        self.model = model

    def predict_tp_move(self, features: np.ndarray) -> float:
        """Возвращает прогноз процентного движения (например, 0.023 для 2.3%)."""
        if not self.model._fitted:
            logger.warning("Strategist model not fitted, returning 0")
            return 0.0
        return float(self.model.predict(features.reshape(1, -1))[0])

    def calculate_tp_sl(
        self,
        features: np.ndarray,
        entry_price: float,
        atr: float,
        signal: str,
        sl_multiplier: float = 1.5
    ) -> Tuple[float, float]:
        """Рассчитывает TP и SL на основе прогноза и ATR."""
        tp_move = self.predict_tp_move(features)
        if signal == 'LONG':
            tp_price = entry_price * (1 + tp_move)
            sl_price = entry_price - atr * sl_multiplier
        else:
            tp_price = entry_price * (1 - tp_move)
            sl_price = entry_price + atr * sl_multiplier
        return tp_price, sl_price
