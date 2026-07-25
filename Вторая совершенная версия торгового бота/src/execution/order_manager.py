"""
src/execution/order_manager.py
Управление ордерами для Apex V5 Global.
Обеспечивает:
- Отправку ордеров с учётом Immediate-or-Cancel (IOC)
- Обработку подтверждений и исполнений
- Интеграцию с Dispatcher через колбэки
- Логирование всех действий
"""

from typing import Optional, Dict, Any, Callable
from datetime import datetime
from enum import Enum

from src.execution.broker import BingXBroker, OrderRequest, OrderResponse
from src.utils.logger import get_logger

logger = get_logger(__name__)


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderManager:
    """
    Управляет жизненным циклом ордеров.
    Предоставляет высокоуровневый интерфейс для отправки и отмены ордеров,
    скрывая детали работы с брокером.
    """

    def __init__(self, broker: BingXBroker, default_symbol: str = "BTCUSDT"):
        self.broker = broker
        self.default_symbol = default_symbol

        # Колбэки, вызываемые при событиях с ордерами
        self.on_order_filled: Optional[Callable[[str, float], None]] = None  # (order_id, execution_price)
        self.on_order_cancelled: Optional[Callable[[str], None]] = None      # (order_id)
        self.on_order_rejected: Optional[Callable[[str, str], None]] = None  # (order_id, reason)

        # Активные ордера (для отслеживания статусов)
        self.active_orders: Dict[str, Dict[str, Any]] = {}

    def set_callbacks(
        self,
        on_filled: Optional[Callable[[str, float], None]] = None,
        on_cancelled: Optional[Callable[[str], None]] = None,
        on_rejected: Optional[Callable[[str, str], None]] = None
    ) -> None:
        """Устанавливает колбэки для интеграции с Dispatcher."""
        self.on_order_filled = on_filled
        self.on_order_cancelled = on_cancelled
        self.on_order_rejected = on_rejected

    def send_ioc_order(
        self,
        side: str,
        quantity: float,
        price: float,
        tp_price: Optional[float] = None,
        sl_price: Optional[float] = None,
        leverage: int = 1,
        symbol: Optional[str] = None
    ) -> Optional[str]:
        """
        Отправляет ордер Immediate-or-Cancel (IOC).
        Если ордер не исполняется немедленно, он отменяется.
        Возвращает order_id или None в случае ошибки.
        """
        symbol = symbol or self.default_symbol

        # Устанавливаем плечо
        self.broker.set_leverage(symbol, leverage)

        # Создаём запрос
        request = OrderRequest(
            symbol=symbol,
            side=side.upper(),
            order_type="IMMEDIATE_OR_CANCEL",
            quantity=quantity,
            price=price,
            leverage=leverage,
            stop_loss=sl_price,
            take_profit=tp_price
        )

        try:
            response = self.broker.send_order(request)
            self.active_orders[response.order_id] = {
                'request': request,
                'response': response,
                'status': response.status,
                'created_at': datetime.now()
            }
            logger.info(f"IOC order sent: {response.order_id}, side={side}, qty={quantity}, price={price}")

            # Если ордер исполнился сразу (FILLED), вызываем колбэк
            if response.status == 'FILLED' and response.price:
                self._handle_fill(response.order_id, response.price)
            elif response.status == 'REJECTED':
                self._handle_rejection(response.order_id, "Order rejected by exchange")

            return response.order_id

        except Exception as e:
            logger.exception(f"Failed to send order: {e}")
            return None

    def cancel_order(self, order_id: str) -> bool:
        """
        Отменяет активный ордер.
        Возвращает True, если отмена успешна.
        """
        if order_id not in self.active_orders:
            logger.warning(f"Attempt to cancel unknown order {order_id}")
            return False

        try:
            success = self.broker.cancel_order(order_id, symbol=self.default_symbol)
            if success:
                self.active_orders[order_id]['status'] = 'CANCELED'
                logger.info(f"Order {order_id} cancelled successfully")
                if self.on_order_cancelled:
                    self.on_order_cancelled(order_id)
            return success
        except Exception as e:
            logger.exception(f"Failed to cancel order {order_id}: {e}")
            return False

    def get_order_status(self, order_id: str) -> Optional[str]:
        """Возвращает статус ордера по его ID."""
        if order_id in self.active_orders:
            return self.active_orders[order_id]['status']
        return None

    def _handle_fill(self, order_id: str, execution_price: float) -> None:
        """Обрабатывает исполнение ордера."""
        if order_id in self.active_orders:
            self.active_orders[order_id]['status'] = 'FILLED'
            self.active_orders[order_id]['execution_price'] = execution_price
        if self.on_order_filled:
            self.on_order_filled(order_id, execution_price)

    def _handle_rejection(self, order_id: str, reason: str) -> None:
        """Обрабатывает отклонение ордера биржей."""
        if order_id in self.active_orders:
            self.active_orders[order_id]['status'] = 'REJECTED'
        if self.on_order_rejected:
            self.on_order_rejected(order_id, reason)

    # --------------------------------------------------------------------------
    # Методы для симуляции (в реальной торговле заменяются WebSocket событиями)
    # --------------------------------------------------------------------------

    def simulate_fill(self, order_id: str, execution_price: Optional[float] = None) -> None:
        """
        Имитирует исполнение ордера (только для бэктеста/тестирования).
        В production исполнение приходит через WebSocket.
        """
        if order_id not in self.active_orders:
            logger.warning(f"Cannot simulate fill for unknown order {order_id}")
            return

        order_info = self.active_orders[order_id]
        if execution_price is None:
            execution_price = order_info['response'].price or order_info['request'].price

        self._handle_fill(order_id, execution_price)

    def simulate_cancel(self, order_id: str) -> None:
        """Имитирует отмену ордера (для тестирования)."""
        if order_id not in self.active_orders:
            logger.warning(f"Cannot simulate cancel for unknown order {order_id}")
            return
        self.active_orders[order_id]['status'] = 'CANCELED'
        if self.on_order_cancelled:
            self.on_order_cancelled(order_id)