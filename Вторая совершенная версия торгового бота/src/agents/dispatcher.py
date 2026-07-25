"""
src/agents/dispatcher.py
Агент Dispatcher: управление капиталом, риском и жизненным циклом ордера.
Соответствует документации:
- Fixed Fractional с волатильностной адаптацией
- Paranoia Mode (High Water Mark)
- Конечный автомат состояний сделки (State Machine)
- Heartbeat таймаут
"""

from enum import Enum
from typing import Optional, Tuple, Callable
import time
import threading
from datetime import datetime
from src.utils.helpers import HighWaterMarkTracker, calculate_fixed_fractional_risk
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TradingState(Enum):
    """Состояния жизненного цикла сделки."""
    IDLE = 0  # Нет активной позиции, ожидание сигнала
    SIGNAL_RECEIVED = 1  # Получен сигнал от Hunter, проверен Critic
    ORDER_SENT = 2  # Ордер отправлен на биржу
    AWAIT_FILL = 3  # Ожидание исполнения ордера
    IN_POSITION = 4  # Позиция открыта, отслеживаются TP/SL


class Dispatcher:
    """
    Управляет размером позиции, риском и состоянием сделки.
    """

    def __init__(
            self,
            initial_equity: float,
            base_risk: float = 0.005,
            target_volatility: float = 0.20,
            max_leverage_normal: float = 3.0,
            max_leverage_paranoia: float = 1.5,
            atr_period: int = 50,
            sl_multiplier: float = 1.5,
            hwm_threshold: float = 0.95,
            heartbeat_timeout: float = 5.0,
            send_order_callback: Optional[Callable] = None,
            cancel_order_callback: Optional[Callable] = None
    ):
        """
        Args:
            initial_equity: начальный капитал
            base_risk: базовая доля риска на сделку (0.5%)
            target_volatility: целевая волатильность (20% годовых)
            max_leverage_normal: максимальное плечо в обычном режиме
            max_leverage_paranoia: максимальное плечо в режиме паранойи
            atr_period: период ATR для расчёта волатильности
            sl_multiplier: множитель ATR для стоп-лосса
            hwm_threshold: порог High Water Mark для активации паранойи
            heartbeat_timeout: таймаут ожидания исполнения ордера (сек)
            send_order_callback: функция для отправки ордера (принимает параметры)
            cancel_order_callback: функция для отмены ордера (принимает order_id)
        """
        # Риск-менеджмент
        self.base_risk = base_risk
        self.target_volatility = target_volatility
        self.max_leverage_normal = max_leverage_normal
        self.max_leverage_paranoia = max_leverage_paranoia
        self.atr_period = atr_period
        self.sl_multiplier = sl_multiplier

        # High Water Mark трекер
        self.hwm_tracker = HighWaterMarkTracker(initial_equity)
        self.hwm_threshold = hwm_threshold

        # Управление состоянием
        self.state = TradingState.IDLE
        self.heartbeat_timeout = heartbeat_timeout
        self._heartbeat_timer: Optional[threading.Timer] = None
        self._current_order_id: Optional[str] = None

        # Колбэки для взаимодействия с биржей
        self.send_order_callback = send_order_callback
        self.cancel_order_callback = cancel_order_callback

        # Текущая открытая позиция (для отслеживания)
        self.current_position: Optional[dict] = None

    @property
    def equity(self) -> float:
        """Текущий баланс капитала."""
        return self.hwm_tracker.current

    @property
    def paranoia_mode(self) -> bool:
        """Активен ли режим паранойи."""
        return self.hwm_tracker.is_paranoia(self.hwm_threshold)

    @property
    def max_leverage(self) -> float:
        """Текущее максимальное разрешённое плечо."""
        return self.max_leverage_paranoia if self.paranoia_mode else self.max_leverage_normal

    def update_equity(self, new_equity: float) -> None:
        """Обновляет текущий баланс и HWM."""
        self.hwm_tracker.update(new_equity)
        logger.info(f"Equity updated: {new_equity:.2f}, HWM: {self.hwm_tracker.hwm:.2f}, "
                    f"Paranoia: {self.paranoia_mode}")

    def calculate_position(
            self,
            entry_price: float,
            sl_price: float,
            current_volatility: float
    ) -> Tuple[float, float, float]:
        """
        Рассчитывает размер позиции и плечо.

        Args:
            entry_price: цена входа
            sl_price: цена стоп-лосса
            current_volatility: текущая волатильность (например, ATR(50)/Price)

        Returns:
            (leverage, position_size, risk_per_trade)
        """
        stop_loss_pct = abs(entry_price - sl_price) / entry_price
        risk_per_trade, leverage, position_size = calculate_fixed_fractional_risk(
            equity=self.equity,
            base_risk=self.base_risk,
            target_volatility=self.target_volatility,
            current_volatility=current_volatility,
            stop_loss_pct=stop_loss_pct,
            max_leverage=self.max_leverage
        )
        logger.debug(f"Position calc: risk={risk_per_trade:.4%}, lev={leverage:.2f}, "
                     f"size={position_size:.2f}, vol={current_volatility:.4%}, sl_pct={stop_loss_pct:.4%}")
        return leverage, position_size, risk_per_trade

    def receive_signal(
            self,
            signal: str,
            entry_price: float,
            tp_price: float,
            sl_price: float,
            current_volatility: float
    ) -> bool:
        """
        Обрабатывает торговый сигнал: рассчитывает размер, отправляет ордер,
        переводит автомат в состояние ORDER_SENT.

        Returns:
            True, если ордер успешно отправлен, иначе False.
        """
        if self.state != TradingState.IDLE:
            logger.warning(f"Cannot receive signal in state {self.state}")
            return False

        # Расчёт размера
        leverage, position_size, _ = self.calculate_position(
            entry_price, sl_price, current_volatility
        )
        if position_size <= 0:
            logger.warning("Position size is zero, signal rejected")
            return False

        # Отправка ордера через колбэк
        if self.send_order_callback is None:
            logger.error("No send_order_callback provided")
            return False

        try:
            order_id = self.send_order_callback(
                signal=signal,
                entry_price=entry_price,
                position_size=position_size,
                leverage=leverage,
                tp_price=tp_price,
                sl_price=sl_price
            )
            self._current_order_id = order_id
            self.current_position = {
                'signal': signal,
                'entry_price': entry_price,
                'tp_price': tp_price,
                'sl_price': sl_price,
                'size': position_size,
                'leverage': leverage
            }
            self.state = TradingState.ORDER_SENT
            self._start_heartbeat()
            logger.info(f"Order sent: {order_id}, signal={signal}, size={position_size:.2f}, lev={leverage:.2f}")
            return True
        except Exception as e:
            logger.exception(f"Failed to send order: {e}")
            return False

    def on_order_accepted(self) -> None:
        """Вызывается, когда биржа подтвердила принятие ордера."""
        if self.state == TradingState.ORDER_SENT:
            self.state = TradingState.AWAIT_FILL
            logger.debug("Order accepted, awaiting fill")

    def on_order_filled(self, execution_price: float) -> None:
        """
        Вызывается при исполнении ордера.
        Переводит автомат в IN_POSITION и отключает heartbeat.
        """
        if self.state in (TradingState.ORDER_SENT, TradingState.AWAIT_FILL):
            self.state = TradingState.IN_POSITION
            self._cancel_heartbeat()
            if self.current_position:
                self.current_position['entry_price'] = execution_price
            logger.info(f"Order filled at {execution_price}")
        else:
            logger.warning(f"Unexpected fill in state {self.state}")

    def on_position_closed(self, pnl: float) -> None:
        """
        Вызывается при закрытии позиции (TP/SL или ручное).
        Обновляет эквити и сбрасывает состояние в IDLE.
        """
        new_equity = self.equity + pnl
        self.update_equity(new_equity)
        self._reset_state()
        logger.info(f"Position closed, PnL: {pnl:.2f}, new equity: {self.equity:.2f}")

    def _reset_state(self) -> None:
        """Сбрасывает состояние в IDLE и очищает данные текущей сделки."""
        self.state = TradingState.IDLE
        self._current_order_id = None
        self.current_position = None
        self._cancel_heartbeat()

    def _start_heartbeat(self) -> None:
        """Запускает таймер heartbeat для контроля зависания ордера."""
        self._cancel_heartbeat()  # на всякий случай
        self._heartbeat_timer = threading.Timer(
            self.heartbeat_timeout,
            self._heartbeat_timeout_handler
        )
        self._heartbeat_timer.start()

    def _cancel_heartbeat(self) -> None:
        """Отменяет таймер heartbeat."""
        if self._heartbeat_timer is not None:
            self._heartbeat_timer.cancel()
            self._heartbeat_timer = None

    def _heartbeat_timeout_handler(self) -> None:
        """Обработчик таймаута ожидания исполнения."""
        if self.state == TradingState.AWAIT_FILL:
            logger.warning(f"Heartbeat timeout ({self.heartbeat_timeout}s) for order {self._current_order_id}")
            if self.cancel_order_callback and self._current_order_id:
                try:
                    self.cancel_order_callback(self._current_order_id)
                except Exception as e:
                    logger.exception(f"Failed to cancel order: {e}")
            self._reset_state()
        else:
            logger.debug(f"Heartbeat fired but state is {self.state}, ignoring")

    def cancel_order(self) -> bool:
        """Ручная отмена ордера (например, по сигналу извне)."""
        if self.state in (TradingState.ORDER_SENT, TradingState.AWAIT_FILL):
            if self.cancel_order_callback and self._current_order_id:
                try:
                    self.cancel_order_callback(self._current_order_id)
                    logger.info(f"Order {self._current_order_id} cancelled manually")
                except Exception as e:
                    logger.exception(f"Cancel order failed: {e}")
                    return False
            self._reset_state()
            return True
        return False

    def is_ready_for_signal(self) -> bool:
        """Можно ли принимать новый сигнал."""
        return self.state == TradingState.IDLE