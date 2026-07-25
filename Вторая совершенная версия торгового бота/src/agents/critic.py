"""
src/agents/critic.py
Агент Critic: статистический фильтр сигналов для Apex V5 Global.
Реализует набор детерминированных правил для блокировки сделок
в неблагоприятных рыночных условиях.
"""

from typing import Optional, Tuple, List
from datetime import datetime, timezone
import numpy as np
from src.utils.helpers import is_blocked_time


class CriticRules:
    """
    Набор пороговых фильтров, блокирующих сигналы Hunter.
    Соответствует документации:
    - ADX < порога И спред > порога → блокировка
    - Цена далеко от зон ликвидности → блокировка
    - Целевое движение < минимального тика → блокировка
    - Time-of-Day фильтр
    """

    def __init__(
            self,
            adx_threshold: float = 20.0,
            adx_threshold_paranoia: float = 25.0,
            spread_multiplier: float = 1.5,
            liquidity_distance_threshold: float = 2.0,
            min_tick_multiplier: float = 3.0,
            blocked_hours: List[Tuple[int, int]] = [(0, 1)],
            avg_spread_window: int = 100,
            atr_period: int = 50
    ):
        self.adx_threshold = adx_threshold
        self.adx_threshold_paranoia = adx_threshold_paranoia
        self.spread_multiplier = spread_multiplier
        self.liquidity_distance_threshold = liquidity_distance_threshold
        self.min_tick_multiplier = min_tick_multiplier
        self.blocked_hours = blocked_hours
        self.avg_spread_window = avg_spread_window
        self.atr_period = atr_period

        # История спредов для расчёта среднего
        self.spread_history: List[float] = []
        self._paranoia_mode: bool = False

    def set_paranoia_mode(self, enabled: bool) -> None:
        """Включает/выключает режим повышенной осторожности."""
        self._paranoia_mode = enabled

    def update_spread(self, spread: float) -> None:
        """Добавляет текущий спред в историю для расчёта среднего."""
        self.spread_history.append(spread)
        if len(self.spread_history) > self.avg_spread_window:
            self.spread_history.pop(0)

    def get_avg_spread(self) -> float:
        """Возвращает средний спред за последние бары."""
        if not self.spread_history:
            return 0.0
        return np.mean(self.spread_history)

    def passes(
            self,
            adx: float,
            spread: float,
            liq_distance: float,
            atr: float,
            target_price: float,
            entry_price: float,
            current_time: Optional[datetime] = None
    ) -> Tuple[bool, str]:
        """
        Проверяет, проходит ли сигнал все фильтры.

        Args:
            adx: значение ADX(14) на текущем баре.
            spread: текущий bid-ask спред в абсолютных единицах.
            liq_distance: расстояние до ближайшей зоны ликвидности (в ATR).
            atr: текущее значение ATR(50).
            target_price: прогнозируемый тейк-профит.
            entry_price: цена входа.
            current_time: UTC время для Time-of-Day фильтра.

        Returns:
            (passed, reason) — True, если все проверки пройдены,
            иначе False с описанием причины блокировки.
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        # 1. Time-of-Day фильтр
        if is_blocked_time(current_time, self.blocked_hours):
            return False, "Blocked trading hours"

        # 2. Проверка ADX и спреда
        avg_spread = self.get_avg_spread()
        adx_thresh = self.adx_threshold_paranoia if self._paranoia_mode else self.adx_threshold

        if self._paranoia_mode and adx < adx_thresh:
            return False, f"Low ADX ({adx:.2f} < {adx_thresh}) in paranoia mode"

        if adx < adx_thresh and avg_spread > 0 and spread > self.spread_multiplier * avg_spread:
            return False, f"Low ADX ({adx:.2f} < {adx_thresh}) and high spread ({spread:.5f} > {self.spread_multiplier}*avg)"

        # 3. Расстояние до ликвидности
        if abs(liq_distance) > self.liquidity_distance_threshold:
            return False, f"Price too far from liquidity zones (|{liq_distance:.2f}| > {self.liquidity_distance_threshold} ATR)"

        # 4. Минимальное движение
        movement = abs(target_price - entry_price)
        if movement < self.min_tick_multiplier * avg_spread and avg_spread > 0:
            return False, f"Expected move ({movement:.5f}) < {self.min_tick_multiplier}*avg_spread ({avg_spread:.5f})"

        return True, "Passed"

    def passes_signal(
            self,
            adx: float,
            spread: float,
            liq_distance: float,
            atr: float,
            signal: str,
            entry_price: float,
            tp_move_pct: float,
            current_time: Optional[datetime] = None
    ) -> Tuple[bool, str]:
        """
        Упрощённый интерфейс, принимающий сигнал и прогноз движения в процентах.
        """
        if signal == 'LONG':
            target_price = entry_price * (1 + tp_move_pct)
        elif signal == 'SHORT':
            target_price = entry_price * (1 - tp_move_pct)
        else:
            return False, "No signal"

        return self.passes(
            adx=adx,
            spread=spread,
            liq_distance=liq_distance,
            atr=atr,
            target_price=target_price,
            entry_price=entry_price,
            current_time=current_time
        )
