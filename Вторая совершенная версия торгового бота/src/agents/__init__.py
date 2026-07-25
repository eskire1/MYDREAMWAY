"""
src/agents/__init__.py
Пакет agents содержит реализации всех агентов системы Apex V5 Global.
"""

from .spotter import Spotter
from .hunter import HunterModel, HunterInference, build_hunter_features, label_hunter_targets
from .critic import CriticRules
from .strategist import StrategistModel, StrategistInference
from .dispatcher import Dispatcher, TradingState
from .learner import Learner, HunterLearner, StrategistLearner

__all__ = [
    # Spotter
    "Spotter",
    # Hunter (CatBoost)
    "HunterModel",
    "HunterInference",
    "build_hunter_features",
    "label_hunter_targets",
    # Critic
    "CriticRules",
    # Strategist (пока старая версия)
    "StrategistModel",
    "StrategistInference",
    # Dispatcher
    "Dispatcher",
    "TradingState",
    # Learner
    "Learner",
    "HunterLearner",
    "StrategistLearner",
]