"""
src/execution/__init__.py
Пакет execution содержит модули для взаимодействия с биржей,
управления ордерами и конечным автоматом состояний.
"""

from .broker import BingXBroker, OrderRequest, OrderResponse
from .order_manager import OrderManager, OrderSide
from .state_machine import TradingStateMachine, TradingState

__all__ = [
    "BingXBroker",
    "OrderRequest",
    "OrderResponse",
    "OrderManager",
    "OrderSide",
    "TradingStateMachine",
    "TradingState",
]