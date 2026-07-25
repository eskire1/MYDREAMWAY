"""
src/agents/spotter.py
Агент Spotter: обнаружение временных точек, где на любых двух из трёх кривых
композитного осциллятора одновременно формируются локальные экстремумы
противоположной направленности (максимум на одной и минимум на другой).
Возвращает список индексов баров (временных меток). Направление не определяет.
"""

import numpy as np
from typing import List
from scipy.signal import argrelextrema
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Spotter:
    """Обнаруживает моменты одновременных разнонаправленных экстремумов на двух кривых."""

    def __init__(self, window: int = 50, order: int = 5, max_lag: int = 2):
        """
        Args:
            window: глубина окна анализа (число баров)
            order: порядок для argrelextrema (сколько соседей слева/справа должны быть меньше/больше)
            max_lag: допустимое смещение индексов экстремумов на разных кривых (баров)
        """
        self.window = window
        self.order = order
        self.max_lag = max_lag

    def get_signals(
        self,
        c_long: np.ndarray,
        c_neutral: np.ndarray,
        c_short: np.ndarray
    ) -> List[int]:
        """
        Сканирует всю историю кривых и возвращает индексы баров, на которых
        обнаружен паттерн одновременных разнонаправленных экстремумов.
        """
        n = len(c_long)
        if n < self.window:
            return []

        signals = []
        for i in range(self.window, n):
            if self._detect_at(c_long, c_neutral, c_short, i):
                signals.append(i)
        return signals

    def _detect_at(
        self,
        c_long: np.ndarray,
        c_neutral: np.ndarray,
        c_short: np.ndarray,
        current_index: int
    ) -> bool:
        """
        Проверяет, сформировался ли паттерн на окне, заканчивающемся в current_index.
        """
        start = current_index - self.window + 1
        end = current_index + 1

        long_win = c_long[start:end]
        neutral_win = c_neutral[start:end]
        short_win = c_short[start:end]

        def extrema_sets(series: np.ndarray):
            max_idx = set(argrelextrema(series, np.greater, order=self.order)[0])
            min_idx = set(argrelextrema(series, np.less, order=self.order)[0])
            return max_idx, min_idx

        l_max, l_min = extrema_sets(long_win)
        n_max, n_min = extrema_sets(neutral_win)
        s_max, s_min = extrema_sets(short_win)

        # Проверяем все пары кривых: Long-Short, Long-Neutral, Short-Neutral
        pairs = [
            (l_max, l_min, s_max, s_min),
            (l_max, l_min, n_max, n_min),
            (s_max, s_min, n_max, n_min),
        ]

        for max_a, min_a, max_b, min_b in pairs:
            # Ищем пересечение: максимум на одной и минимум на другой с учётом лага
            for idx_a in max_a:
                for idx_b in min_b:
                    if abs(idx_a - idx_b) <= self.max_lag:
                        return True
            # И симметрично: максимум на второй и минимум на первой
            for idx_a in max_b:
                for idx_b in min_a:
                    if abs(idx_a - idx_b) <= self.max_lag:
                        return True
        return False