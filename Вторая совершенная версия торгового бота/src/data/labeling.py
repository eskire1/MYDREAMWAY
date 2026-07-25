"""
src/data/labeling.py
Разметка данных методом Triple-Barrier для обучения Hunter.
Соответствует документации Apex V5 Global:
- Верхний барьер: +2.0 * ATR (фиксированный множитель для начальной разметки)
- Нижний барьер: -1.5 * ATR
- Временной барьер: horizon_bars = 16
- Метки: 0 = HOLD, 1 = LONG, 2 = SHORT
"""

import numpy as np
import pandas as pd


def triple_barrier_labels(
    df: pd.DataFrame,
    atr: np.ndarray,
    horizon_bars: int = 16,
    sl_multiplier: float = 1.5,
    tp_multiplier: float = 2.0,
) -> np.ndarray:
    """
    Возвращает метки для каждого бара на основе метода Triple-Barrier.

    Args:
        df: DataFrame с колонками 'high', 'low', 'close'.
        atr: массив значений ATR(50) для каждого бара.
        horizon_bars: количество баров до временного барьера.
        sl_multiplier: множитель ATR для стоп-лосса.
        tp_multiplier: множитель ATR для тейк-профита (временная заглушка).

    Returns:
        np.ndarray[int]: метки классов:
            0 — HOLD (временной барьер сработал первым или движение не достигло порогов)
            1 — LONG (верхний барьер достигнут раньше нижнего)
            2 — SHORT (нижний барьер достигнут раньше верхнего)
    """
    n = len(df)
    labels = np.full(n, 0, dtype=int)  # по умолчанию HOLD

    close = df['close'].values
    high = df['high'].values
    low = df['low'].values

    for i in range(n - horizon_bars):
        entry_price = close[i]
        upper_barrier = entry_price + tp_multiplier * atr[i]
        lower_barrier = entry_price - sl_multiplier * atr[i]

        # Ищем первое касание барьера в пределах горизонта
        hit_upper = False
        hit_lower = False
        for j in range(1, horizon_bars + 1):
            idx = i + j
            if high[idx] >= upper_barrier:
                hit_upper = True
                break
            if low[idx] <= lower_barrier:
                hit_lower = True
                break

        if hit_upper and not hit_lower:
            labels[i] = 1  # LONG
        elif hit_lower and not hit_upper:
            labels[i] = 2  # SHORT
        # Если оба или ни один не достигнуты, остаётся 0 (HOLD)

    return labels