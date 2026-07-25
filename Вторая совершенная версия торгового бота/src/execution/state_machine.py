"""
src/execution/state_machine.py
Реализация конечного автомата для управления состояниями торговли.
Используется в Dispatcher, но вынесен в отдельный модуль для переиспользования.
"""

from enum import Enum
from typing import Optional, Callable, Dict, Any, List, Tuple
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TradingState(Enum):
    """Состояния жизненного цикла сделки."""
    IDLE = 0               # Нет активной позиции, ожидание сигнала
    SIGNAL_RECEIVED = 1    # Получен сигнал от Hunter, проверен Critic
    ORDER_SENT = 2         # Ордер отправлен на биржу
    AWAIT_FILL = 3         # Ожидание исполнения ордера
    IN_POSITION = 4        # Позиция открыта, отслеживаются TP/SL


class TradingStateMachine:
    """
    Управляет переходами между состояниями с валидацией.
    """

    def __init__(self, initial_state: TradingState = TradingState.IDLE):
        self._state = initial_state
        self._history: List[Tuple[TradingState, TradingState]] = []
        self._callbacks: Dict[TradingState, List[Callable]] = {
            state: [] for state in TradingState
        }

        # Определяем разрешённые переходы
        self._transitions = {
            TradingState.IDLE: [TradingState.SIGNAL_RECEIVED],
            TradingState.SIGNAL_RECEIVED: [TradingState.ORDER_SENT],
            TradingState.ORDER_SENT: [TradingState.AWAIT_FILL],
            TradingState.AWAIT_FILL: [TradingState.IN_POSITION, TradingState.IDLE],  # IDLE при таймауте
            TradingState.IN_POSITION: [TradingState.IDLE],
        }

    @property
    def state(self) -> TradingState:
        return self._state

    def can_transition_to(self, new_state: TradingState) -> bool:
        """Проверяет, разрешён ли переход."""
        return new_state in self._transitions.get(self._state, [])

    def transition_to(self, new_state: TradingState, force: bool = False) -> bool:
        """
        Выполняет переход в новое состояние, если он разрешён.
        При force=True игнорирует правила (для экстренных случаев).
        """
        if not force and not self.can_transition_to(new_state):
            logger.warning(f"Invalid transition from {self._state.name} to {new_state.name}")
            return False

        old_state = self._state
        self._history.append((old_state, new_state))
        self._state = new_state
        logger.debug(f"State transition: {old_state.name} -> {new_state.name}")

        # Вызываем зарегистрированные колбэки для нового состояния
        for callback in self._callbacks.get(new_state, []):
            try:
                callback(old_state, new_state)
            except Exception as e:
                logger.exception(f"Callback error: {e}")

        return True

    def register_callback(self, state: TradingState, callback: Callable) -> None:
        """Регистрирует функцию, вызываемую при входе в состояние."""
        self._callbacks[state].append(callback)

    def reset(self) -> None:
        """Сбрасывает автомат в IDLE."""
        self.transition_to(TradingState.IDLE, force=True)

    def is_idle(self) -> bool:
        return self._state == TradingState.IDLE

    def is_in_position(self) -> bool:
        return self._state == TradingState.IN_POSITION

    def get_history(self) -> List[Tuple[TradingState, TradingState]]:
        """Возвращает историю переходов."""
        return self._history.copy()