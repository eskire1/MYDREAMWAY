"""
src/backtest/__init__.py
Пакет backtest содержит модули для симуляции торговли на исторических данных.
"""

from .engine import BacktestEngine
from .slippage import apply_slippage, SlippageModel
from .metrics import calculate_metrics, MetricsResult

__all__ = [
    "BacktestEngine",
    "apply_slippage",
    "SlippageModel",
    "calculate_metrics",
    "MetricsResult",
]