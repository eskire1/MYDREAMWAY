"""
src/backtest/slippage.py
Моделирование проскальзывания для бэктеста Apex V5 Global.
Соответствует документации:
- BTC/ETH: slippage = 0.05% (0.0005)
- Альткойны: slippage = 0.2% (0.002)
- Для BUY цена умножается на (1 + slippage), для SELL — на (1 - slippage)
"""


class SlippageModel:
    """
    Класс для применения проскальзывания к цене исполнения.
    """

    def __init__(self, slippage_rate: float):
        self.slippage_rate = slippage_rate

    def apply(self, price: float, side: str) -> float:
        """
        Применяет проскальзывание к цене в зависимости от стороны сделки.

        Args:
            price: базовая цена (обычно open бара)
            side: 'BUY' или 'SELL'

        Returns:
            Цена с учётом проскальзывания
        """
        if side.upper() == 'BUY':
            return price * (1 + self.slippage_rate)
        elif side.upper() == 'SELL':
            return price * (1 - self.slippage_rate)
        else:
            raise ValueError(f"Invalid side: {side}, expected 'BUY' or 'SELL'")


def apply_slippage(price: float, side: str, slippage_rate: float) -> float:
    """
    Функциональная версия применения проскальзывания.
    """
    model = SlippageModel(slippage_rate)
    return model.apply(price, side)