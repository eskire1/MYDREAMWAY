"""
src/agents/hunter.py
Агент Hunter: обучаемый CatBoost-классификатор, который принимает решение
в момент, когда одновременно выполняются два условия:
1) есть временная метка Spotter (выпуклости кривых),
2) цена коснулась зоны ликвидности (верхней или нижней).
Порядок событий не важен – как только оба условия выполнены в пределах
max_lag баров, генерируется сигнал, признаки собираются на баре последнего
из этих двух событий, включая лаг между ними и полную информацию о зоне
ликвидности (цена, объём, ширина, число касаний, перекрытие в пунктах и %).
"""

import os
import numpy as np
from typing import Tuple, List, Set
from catboost import CatBoostClassifier
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ------------------------------------------------------------------------------
# Извлечение признаков (на момент завершения комбинации)
# ------------------------------------------------------------------------------

def build_hunter_features(
    df,
    curves_long: np.ndarray,
    curves_neutral: np.ndarray,
    curves_short: np.ndarray,
    liq_upper_data: dict,   # словарь с массивами: 'price', 'volume', 'width', 'count', 'overlap_pts', 'overlap_pct'
    liq_lower_data: dict,   # аналогично для нижнего уровня
    atr: np.ndarray,
    spotter_timestamps: Set[int],
    max_lag: int = 10
) -> Tuple[np.ndarray, List[int]]:
    n = len(df)
    if n < 20:
        return np.empty((0, 18)), []

    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    open_ = df['open'].values
    volume = df['volume'].values

    from src.data.indicators import CompositeOscillator
    adx = CompositeOscillator._adx(high, low, close, 14)

    avg_volume = np.zeros(n)
    for i in range(n):
        start_idx = max(0, i - 19)
        avg_volume[i] = volume[start_idx:i+1].mean()

    last_spotter = -1
    last_upper_touch = -1
    last_lower_touch = -1

    X_list = []
    indices_list = []

    for i in range(n):
        if i in spotter_timestamps:
            last_spotter = i
        if not np.isnan(liq_upper_data['price'][i]) and high[i] >= liq_upper_data['price'][i]:
            last_upper_touch = i
        if not np.isnan(liq_lower_data['price'][i]) and low[i] <= liq_lower_data['price'][i]:
            last_lower_touch = i

        # Комбинация с верхней зоной
        if last_spotter != -1 and last_upper_touch != -1:
            dist = abs(last_spotter - last_upper_touch)
            if dist <= max_lag and max(last_spotter, last_upper_touch) == i:
                feats = _collect_features(i, last_spotter, last_upper_touch,
                                          volume, avg_volume, close, high, low, open_,
                                          liq_upper_data, liq_lower_data, adx, atr)
                X_list.append(feats)
                indices_list.append(i)

        # Комбинация с нижней зоной
        if last_spotter != -1 and last_lower_touch != -1:
            dist = abs(last_spotter - last_lower_touch)
            if dist <= max_lag and max(last_spotter, last_lower_touch) == i:
                feats = _collect_features(i, last_spotter, last_lower_touch,
                                          volume, avg_volume, close, high, low, open_,
                                          liq_upper_data, liq_lower_data, adx, atr)
                X_list.append(feats)
                indices_list.append(i)

    if not X_list:
        return np.empty((0, 0)), []
    return np.array(X_list, dtype=np.float32), indices_list


def _collect_features(idx, spotter_idx, touch_idx,
                      volume, avg_volume, close, high, low, open_,
                      liq_upper, liq_lower, adx, atr):
    i = idx
    lag = abs(spotter_idx - touch_idx)

    # Векторы объёма (5 последних значений + 5 отношений к среднему)
    vol_raw = []
    vol_ratio = []
    for offset in range(5):
        j = max(0, i - offset)
        vol_raw.append(volume[j])
        vol_ratio.append(volume[j] / (avg_volume[j] + 1e-10))
    while len(vol_raw) < 5:
        vol_raw.insert(0, vol_raw[0] if vol_raw else 0.0)
        vol_ratio.insert(0, vol_ratio[0] if vol_ratio else 0.0)

    # Расстояния до уровней в пунктах и ATR
    dist_upper = (liq_upper['price'][i] - close[i]) if not np.isnan(liq_upper['price'][i]) else 0.0
    dist_lower = (close[i] - liq_lower['price'][i]) if not np.isnan(liq_lower['price'][i]) else 0.0

    # Полные данные ликвидности
    liq_feat = [
        liq_upper['volume'][i] if not np.isnan(liq_upper['volume'][i]) else 0.0,
        liq_upper['width'][i] if not np.isnan(liq_upper['width'][i]) else 0.0,
        liq_upper['count'][i] if not np.isnan(liq_upper['count'][i]) else 0.0,
        liq_upper['overlap_pts'][i] if not np.isnan(liq_upper['overlap_pts'][i]) else 0.0,
        liq_upper['overlap_pct'][i] if not np.isnan(liq_upper['overlap_pct'][i]) else 0.0,
        liq_lower['volume'][i] if not np.isnan(liq_lower['volume'][i]) else 0.0,
        liq_lower['width'][i] if not np.isnan(liq_lower['width'][i]) else 0.0,
        liq_lower['count'][i] if not np.isnan(liq_lower['count'][i]) else 0.0,
        liq_lower['overlap_pts'][i] if not np.isnan(liq_lower['overlap_pts'][i]) else 0.0,
        liq_lower['overlap_pct'][i] if not np.isnan(liq_lower['overlap_pct'][i]) else 0.0,
    ]

    # Соотношения свечей и интенсивности
    body = abs(close[i] - open_[i])
    total_range = high[i] - low[i] + 1e-10
    if body == 0:
        rel = [0, 0, 0, 0]
    else:
        if close[i] >= open_[i]:
            rel = [
                (high[i] - close[i]) / body,
                (open_[i] - low[i]) / body,
                (high[i] - close[i]) / total_range,
                (open_[i] - low[i]) / total_range
            ]
        else:
            rel = [
                (high[i] - open_[i]) / body,
                (close[i] - low[i]) / body,
                (high[i] - open_[i]) / total_range,
                (close[i] - low[i]) / total_range
            ]
    int1 = np.mean(np.abs(np.diff(high[max(0,i-2):i+1]))) if i >= 2 else 0
    int2 = np.mean(np.abs(np.diff(low[max(0,i-2):i+1]))) if i >= 2 else 0
    int3, int4 = int1, int2

    # Тени, коснувшиеся уровня
    upper_shadow = max(0, high[i] - max(open_[i], close[i]))
    lower_shadow = max(0, min(open_[i], close[i]) - low[i])

    # Прочие индикаторы
    spread = high[i] - low[i]
    momentum = close[i] - close[i-3] if i >= 3 else 0
    adx_val = adx[i] if not np.isnan(adx[i]) else 0.0
    trend = np.sign(close[i] - close[i-10]) if i >= 10 else 0

    features = [
        lag,
        *vol_raw,
        *vol_ratio,
        dist_upper, dist_lower,
        dist_upper / atr[i] if atr[i] > 0 else 0,
        dist_lower / atr[i] if atr[i] > 0 else 0,
        *liq_feat,
        *rel,
        int1, int2, int3, int4,
        upper_shadow, lower_shadow,
        spread,
        momentum,
        adx_val,
        trend
    ]
    return features


# ------------------------------------------------------------------------------
# Разметка целей (по движению цены после завершения комбинации)
# ------------------------------------------------------------------------------
def label_hunter_targets(
    df,
    indices: List[int],
    spotter_timestamps: Set[int],
    horizon: int = 50
) -> np.ndarray:
    close = df['close'].values
    n = len(df)
    targets = np.zeros(len(indices), dtype=int)
    sorted_spotter = sorted(spotter_timestamps)

    for idx_pos, bar_idx in enumerate(indices):
        if bar_idx + horizon >= n:
            continue
        max_idx = bar_idx + horizon
        for s in sorted_spotter:
            if s > bar_idx and s < bar_idx + horizon:
                max_idx = s
                break
        future = close[max_idx] if max_idx < n else close[-1]
        current = close[bar_idx]
        if future > current * 1.005:
            targets[idx_pos] = 1
        elif future < current * 0.995:
            targets[idx_pos] = 2
    return targets


# ------------------------------------------------------------------------------
# Модель Hunter (CatBoost)
# ------------------------------------------------------------------------------
class HunterModel:
    def __init__(
        self,
        iterations: int = 200,
        learning_rate: float = 0.1,
        depth: int = 5,
    ):
        self.model = CatBoostClassifier(
            iterations=iterations,
            learning_rate=learning_rate,
            depth=depth,
            loss_function='MultiClass',
            verbose=False,
            allow_writing_files=False,
            class_weights=[0.5, 5, 5]
        )
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.model.fit(X, y)
        self._fitted = True

    def partial_fit(self, X: np.ndarray, y: np.ndarray, epochs: int = 5):
        if not self._fitted:
            self.fit(X, y)
        else:
            self.model.fit(X, y, init_model=self.model)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.model.save_model(path)

    def load(self, path: str):
        self.model.load_model(path)
        self._fitted = True


# ------------------------------------------------------------------------------
# Интерфейс для live-торговли
# ------------------------------------------------------------------------------
class HunterInference:
    def __init__(self, model: HunterModel):
        self.model = model

    def decide(self, features: List[float]) -> Tuple[str, np.ndarray]:
        """Принимает готовый вектор признаков, возвращает ('LONG'/'SHORT'/'HOLD', вероятности)."""
        if not self.model._fitted:
            return "HOLD", np.zeros(3)
        X = np.array([features], dtype=np.float32)
        probs = self.model.predict_proba(X)[0]
        pred = np.argmax(probs)
        if pred == 0:
            return "HOLD", probs
        elif pred == 1:
            return "LONG", probs
        else:
            return "SHORT", probs
