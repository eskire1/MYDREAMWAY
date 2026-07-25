"""
src/utils/helpers.py
Вспомогательные функции для Apex V5 Global.
"""

import numpy as np
import pandas as pd
from typing import Optional, Union, List, Tuple
from datetime import datetime, timezone
from pathlib import Path


# ------------------------------------------------------------------------------
# Расчёт индикаторов
# ------------------------------------------------------------------------------

def calculate_atr(
        high: Union[pd.Series, np.ndarray],
        low: Union[pd.Series, np.ndarray],
        close: Union[pd.Series, np.ndarray],
        period: int = 50,
) -> np.ndarray:
    """
    Расчёт Average True Range (ATR) с заданным периодом.
    Соответствует документации: ATR(50) для Dispatcher и Critic.
    """
    high = np.asarray(high)
    low = np.asarray(low)
    close = np.asarray(close)

    prev_close = np.roll(close, 1)
    prev_close[0] = close[0]

    tr1 = high - low
    tr2 = np.abs(high - prev_close)
    tr3 = np.abs(low - prev_close)
    tr = np.maximum.reduce([tr1, tr2, tr3])

    atr = np.zeros_like(tr)
    atr[0] = tr[0]
    alpha = 1.0 / period

    for i in range(1, len(tr)):
        atr[i] = alpha * tr[i] + (1 - alpha) * atr[i - 1]

    return atr


# ------------------------------------------------------------------------------
# Нормализация
# ------------------------------------------------------------------------------

class RollingZScoreScaler:
    """
    Глобальный Z‑Score нормализатор на скользящем окне.
    Используется для приведения признаков к единому масштабу.
    Соответствует документации: rolling_window = 1000.
    """

    def __init__(self, window: int = 1000):
        self.window = window
        self.history: List[float] = []

    def update(self, value: float) -> float:
        """Добавляет новое значение и возвращает нормализованное."""
        self.history.append(value)
        if len(self.history) > self.window:
            self.history.pop(0)

        if len(self.history) < 2:
            return 0.0

        mean = np.mean(self.history)
        std = np.std(self.history)
        if std == 0:
            return 0.0
        return (value - mean) / std

    def normalize_array(self, values: np.ndarray) -> np.ndarray:
        """Нормализует массив значений на основе текущей истории."""
        if len(self.history) < 2:
            return np.zeros_like(values)
        mean = np.mean(self.history)
        std = np.std(self.history)
        if std == 0:
            return np.zeros_like(values)
        return (values - mean) / std


# ------------------------------------------------------------------------------
# Работа со временем и датами
# ------------------------------------------------------------------------------

def is_blocked_time(
        dt: Optional[datetime] = None,
        blocked_hours: List[Tuple[int, int]] = [(0, 1)]
) -> bool:
    """
    Проверяет, попадает ли текущее UTC время в запрещённый интервал.
    Соответствует документации: Time-of-Day Filter (00:00–01:00 UTC).
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    hour = dt.hour
    for start, end in blocked_hours:
        if start <= hour < end:
            return True
    return False


def get_current_utc() -> datetime:
    """Возвращает текущее UTC время."""
    return datetime.now(timezone.utc)


def bars_to_days(bars: int, timeframe_minutes: int = 15) -> float:
    """Конвертирует количество баров в дни (для оценки сроков)."""
    minutes_per_day = 24 * 60
    return (bars * timeframe_minutes) / minutes_per_day


# ------------------------------------------------------------------------------
# Управление капиталом и Paranoia Mode
# ------------------------------------------------------------------------------

class HighWaterMarkTracker:
    """
    Отслеживает исторический максимум эквити (High Water Mark).
    Используется для Paranoia Mode.
    Соответствует документации: HWM с порогом 0.95.
    """

    def __init__(self, initial_equity: float):
        self.initial = initial_equity
        self.hwm = initial_equity
        self.current = initial_equity

    def update(self, new_equity: float) -> None:
        self.current = new_equity
        if new_equity > self.hwm:
            self.hwm = new_equity

    def is_paranoia(self, threshold: float = 0.95) -> bool:
        """Возвращает True, если текущий баланс < HWM * threshold."""
        return self.current <= self.hwm * threshold


def calculate_fixed_fractional_risk(
        equity: float,
        base_risk: float,
        target_volatility: float,
        current_volatility: float,
        stop_loss_pct: float,
        max_leverage: float,
) -> Tuple[float, float]:
    """
    Расчёт риска на сделку и плеча по методу Fixed Fractional с волатильностной адаптацией.
    Соответствует документации Dispatcher:
    Риск_на_сделку = База_Риска * (Целевая_Волатильность / Текущая_Волатильность)
    Leverage = min(max_leverage, Риск_на_сделку / stop_loss_pct)
    """
    if current_volatility <= 0:
        current_volatility = target_volatility  # защита от деления на ноль
    risk_per_trade = base_risk * (target_volatility / current_volatility)
    if stop_loss_pct <= 0:
        return 0.0, 0.0
    leverage = min(max_leverage, risk_per_trade / stop_loss_pct)
    position_size = (equity * leverage)
    return risk_per_trade, leverage, position_size


# ------------------------------------------------------------------------------
# Работа с файловой системой
# ------------------------------------------------------------------------------

def ensure_directory(path: Union[str, Path]) -> Path:
    """Создаёт директорию, если её нет, и возвращает Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


# ------------------------------------------------------------------------------
# Конвертация данных
# ------------------------------------------------------------------------------

def flatten_window(window_3d: np.ndarray) -> np.ndarray:
    """
    Преобразует окно (20,4) в плоский вектор (80,).
    Используется для подачи в Strategist (CatBoost).
    """
    return window_3d.flatten()


def reconstruct_window(flat_array: np.ndarray, shape: Tuple[int, int] = (20, 4)) -> np.ndarray:
    """Обратное преобразование плоского вектора в окно (для тестов)."""
    return flat_array.reshape(shape)
