"""
src/data/preprocessing.py
Предобработка данных для Apex V5 Global:
- Нормализация признаков (Z‑Score по скользящему окну).
- Формирование окон (20 баров, 4 канала) для Hunter.
- Формирование плоских векторов (80 признаков) для Strategist.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional, List, Dict, Any
from src.utils.helpers import RollingZScoreScaler, flatten_window
from src.data.indicators import CompositeOscillatorResult
from tqdm import tqdm

class FeaturePreprocessor:
    """
    Управляет нормализацией признаков и построением окон для моделей.
    Соответствует документации Apex V5 Global:
    - Глобальная Z‑Score нормализация с окном 1000 баров.
    - Входной тензор (window=20, channels=4).
    """

    def __init__(self, window_size: int = 20, scaling_window: int = 1000):
        self.window_size = window_size
        self.scaling_window = scaling_window

        # Отдельные скейлеры для каждого из 4 каналов
        self.scaler_long = RollingZScoreScaler(window=scaling_window)
        self.scaler_neutral = RollingZScoreScaler(window=scaling_window)
        self.scaler_short = RollingZScoreScaler(window=scaling_window)
        self.scaler_liq = RollingZScoreScaler(window=scaling_window)

        # История последних значений для восстановления состояния скейлеров
        self.history_long: List[float] = []
        self.history_neutral: List[float] = []
        self.history_short: List[float] = []
        self.history_liq: List[float] = []

    def partial_fit(self, long_vals: np.ndarray, neutral_vals: np.ndarray,
                    short_vals: np.ndarray, liq_vals: np.ndarray) -> None:
        """
        Обучает скейлеры на исторических данных (заполняет историю).
        Вызывается один раз перед началом работы для прогрева нормализации.
        """
        for v in long_vals:
            self.scaler_long.update(v)
        for v in neutral_vals:
            self.scaler_neutral.update(v)
        for v in short_vals:
            self.scaler_short.update(v)
        for v in liq_vals:
            self.scaler_liq.update(v)

    def transform_single(
            self,
            long_val: float,
            neutral_val: float,
            short_val: float,
            liq_val: float
    ) -> Tuple[float, float, float, float]:
        """
        Нормализует одно наблюдение (текущий бар) с обновлением истории скейлеров.
        Используется в потоковом режиме (live trading).
        """
        n_long = self.scaler_long.update(long_val)
        n_neutral = self.scaler_neutral.update(neutral_val)
        n_short = self.scaler_short.update(short_val)
        n_liq = self.scaler_liq.update(liq_val)
        return n_long, n_neutral, n_short, n_liq

    def build_window_3d(
            self,
            buffer_long: List[float],
            buffer_neutral: List[float],
            buffer_short: List[float],
            buffer_liq: List[float]
    ) -> np.ndarray:
        """
        Формирует трёхмерное окно (window_size, 4) из буферов нормализованных значений.
        Если длина буферов меньше window_size, дополняет нулями слева.
        """

        # Берём последние window_size элементов из каждого буфера
        def get_last(arr, n):
            if len(arr) >= n:
                return arr[-n:]
            else:
                return [0.0] * (n - len(arr)) + arr

        w_long = get_last(buffer_long, self.window_size)
        w_neutral = get_last(buffer_neutral, self.window_size)
        w_short = get_last(buffer_short, self.window_size)
        w_liq = get_last(buffer_liq, self.window_size)

        window = np.stack([w_long, w_neutral, w_short, w_liq], axis=1)
        return window.astype(np.float32)

    def build_flat_features(self, window_3d: np.ndarray) -> np.ndarray:
        """
        Преобразует окно (20,4) в плоский вектор (80,) для CatBoost Strategist.
        """
        return flatten_window(window_3d)

    def prepare_live_input(
            self,
            current_long: float,
            current_neutral: float,
            current_short: float,
            current_liq: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Основной метод для live-торговли.
        Принимает текущие значения индикаторов, нормализует их, обновляет буферы
        и возвращает:
            - window_3d: np.ndarray (20,4) для Hunter
            - flat_features: np.ndarray (80,) для Strategist
        """
        # Нормализуем и сохраняем в историю
        n_long, n_neutral, n_short, n_liq = self.transform_single(
            current_long, current_neutral, current_short, current_liq
        )
        self.history_long.append(n_long)
        self.history_neutral.append(n_neutral)
        self.history_short.append(n_short)
        self.history_liq.append(n_liq)

        # Ограничиваем длину истории, чтобы не росла бесконечно (храним последние window_size + запас)
        max_history = self.window_size + 100
        if len(self.history_long) > max_history:
            self.history_long = self.history_long[-max_history:]
            self.history_neutral = self.history_neutral[-max_history:]
            self.history_short = self.history_short[-max_history:]
            self.history_liq = self.history_liq[-max_history:]

        # Строим окно
        window_3d = self.build_window_3d(
            self.history_long, self.history_neutral,
            self.history_short, self.history_liq
        )
        flat = self.build_flat_features(window_3d)
        return window_3d, flat


def prepare_training_data(
        df: pd.DataFrame,
        composite: CompositeOscillatorResult,
        liq_distance: np.ndarray,
        window_size: int = 20,
        scaling_window: int = 1000
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Готовит обучающую выборку для Hunter (X, y) из исторических данных.

    Args:
        df: DataFrame с OHLCV и, возможно, уже рассчитанными метками.
        composite: Результат композитного осциллятора.
        liq_distance: Массив расстояний до ликвидности (нормализованных).
        window_size: Размер окна.
        scaling_window: Окно для Z‑Score нормализации.

    Returns:
        X: np.ndarray формы (N, window_size, 4)
        y: np.ndarray формы (N,) с метками (0=HOLD, 1=LONG, 2=SHORT)
           Предполагается, что метки уже есть в df['label'].
    """
    preprocessor = FeaturePreprocessor(window_size, scaling_window)

    # Прогреваем скейлеры на всех данных
    preprocessor.partial_fit(
        composite.long, composite.neutral,
        composite.short, liq_distance
    )

    X_list = []
    y_list = []

    #for i in range(window_size, len(df)):
    for i in tqdm(range(window_size, len(df)), desc='Preparing Tensors'):
        # Нормализованные значения для текущего окна (через историю скейлеров)
        # Но для оффлайн обучения лучше нормализовать всё сразу и строить окна.
        # Здесь упрощённо: берём уже нормализованные значения, предполагая,
        # что preprocessor.transform_single вызывался последовательно.
        # В реальности нужно нормализовать весь массив с учётом expanding window.
        n_long = np.array([preprocessor.scaler_long.update(v) for v in composite.long[:i]])
        n_neutral = np.array([preprocessor.scaler_neutral.update(v) for v in composite.neutral[:i]])
        n_short = np.array([preprocessor.scaler_short.update(v) for v in composite.short[:i]])
        n_liq = np.array([preprocessor.scaler_liq.update(v) for v in liq_distance[:i]])

        # Строим окно для индекса i
        start = i - window_size
        w_long = n_long[start:i]
        w_neutral = n_neutral[start:i]
        w_short = n_short[start:i]
        w_liq = n_liq[start:i]

        window = np.stack([w_long, w_neutral, w_short, w_liq], axis=1)
        X_list.append(window)
        y_list.append(df.iloc[i]['label'])  # предполагается наличие колонки label

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int64)
    return X, y