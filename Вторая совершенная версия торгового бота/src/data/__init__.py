"""
src/data/__init__.py
Пакет data содержит модули для работы с индикаторами, предобработкой,
разметкой и хранилищами данных Apex V5 Global.
"""

from .indicators import (
    CompositeOscillator,
    CompositeOscillatorResult,
    LiquidityZones,
)
from .preprocessing import FeaturePreprocessor, prepare_training_data
from .labeling import triple_barrier_labels
from .storage import (
    WindowStorage,
    HunterLogStorage,
    StrategistLogStorage,
    DataStorageManager,
)

__all__ = [
    # Индикаторы
    "CompositeOscillator",
    "CompositeOscillatorResult",
    "LiquidityZones",
    # Препроцессинг (оставлено для совместимости, но может не использоваться)
    "FeaturePreprocessor",
    "prepare_training_data",
    # Разметка (старая Triple Barrier, пока не удалена)
    "triple_barrier_labels",
    # Хранилища
    "WindowStorage",
    "HunterLogStorage",
    "StrategistLogStorage",
    "DataStorageManager",
]