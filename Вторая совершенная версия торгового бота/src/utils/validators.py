"""
src/utils/validators.py
Вспомогательные функции валидации входных данных для Apex V5 Global.
"""

import numpy as np
import pandas as pd
from typing import List, Optional, Union


def validate_ohlcv_dataframe(df: pd.DataFrame) -> bool:
    """
    Проверяет, что DataFrame содержит необходимые колонки OHLCV.
    """
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"DataFrame missing required column: {col}")
    return True


def validate_window_shape(window: np.ndarray, expected_shape: tuple = (20, 4)) -> bool:
    """
    Проверяет форму входного окна для Hunter.
    """
    if window.shape != expected_shape:
        raise ValueError(f"Window shape {window.shape} != expected {expected_shape}")
    return True


def validate_probabilities(probs: Union[List[float], np.ndarray], expected_len: int = 3) -> bool:
    """
    Проверяет, что вероятности суммируются к 1 и имеют правильную длину.
    """
    probs = np.asarray(probs)
    if len(probs) != expected_len:
        raise ValueError(f"Probabilities length {len(probs)} != expected {expected_len}")
    if not np.isclose(probs.sum(), 1.0, atol=1e-5):
        raise ValueError(f"Probabilities sum to {probs.sum()}, expected 1.0")
    if np.any(probs < 0) or np.any(probs > 1):
        raise ValueError("Probabilities must be in [0,1]")
    return True


def validate_signal(signal: str) -> bool:
    """
    Проверяет, что сигнал принадлежит допустимым значениям.
    """
    allowed = {'LONG', 'SHORT', 'HOLD'}
    if signal not in allowed:
        raise ValueError(f"Signal '{signal}' not in {allowed}")
    return True


def validate_positive(value: float, name: str = "value") -> bool:
    """
    Проверяет, что значение положительное.
    """
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return True