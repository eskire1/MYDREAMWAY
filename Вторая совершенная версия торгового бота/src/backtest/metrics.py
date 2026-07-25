"""
src/backtest/metrics.py
Расчёт метрик эффективности по результатам бэктеста Apex V5 Global.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class MetricsResult:
    """Контейнер для результатов расчёта метрик."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    final_equity: float
    initial_equity: float
    total_return: float


def calculate_metrics(
    trades: List[Dict[str, Any]],
    initial_equity: float,
    final_equity: float,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 365 * 24 * 4  # 15-минутные бары
) -> MetricsResult:
    """
    Рассчитывает основные метрики торговой стратегии.

    Args:
        trades: список словарей с информацией о сделках (ключи: 'pnl', 'return')
        initial_equity: начальный капитал
        final_equity: конечный капитал
        risk_free_rate: безрисковая ставка (по умолчанию 0)
        periods_per_year: количество торговых периодов в году (для 15m = 35040)

    Returns:
        MetricsResult с вычисленными метриками
    """
    if not trades:
        return MetricsResult(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            total_pnl=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            profit_factor=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            final_equity=final_equity,
            initial_equity=initial_equity,
            total_return=0.0
        )

    pnls = [t['pnl'] for t in trades]
    returns = [t['return'] for t in trades]

    total_trades = len(pnls)
    winning_trades = sum(1 for p in pnls if p > 0)
    losing_trades = sum(1 for p in pnls if p <= 0)

    win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
    total_pnl = sum(pnls)

    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    avg_win = np.mean(wins) if wins else 0.0
    avg_loss = np.mean(losses) if losses else 0.0

    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')

    # Расчёт кривой эквити для максимальной просадки
    equity_curve = [initial_equity]
    for pnl in pnls:
        equity_curve.append(equity_curve[-1] + pnl)
    equity_curve = np.array(equity_curve)

    peak = np.maximum.accumulate(equity_curve)
    drawdown = (peak - equity_curve) / peak
    max_drawdown = np.max(drawdown)

    # Коэффициент Шарпа
    if len(returns) > 1:
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        sharpe_ratio = (mean_return - risk_free_rate) / std_return * np.sqrt(periods_per_year) if std_return > 0 else 0.0
    else:
        sharpe_ratio = 0.0

    total_return = (final_equity / initial_equity - 1) if initial_equity > 0 else 0.0

    return MetricsResult(
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate=win_rate,
        total_pnl=total_pnl,
        avg_win=avg_win,
        avg_loss=avg_loss,
        profit_factor=profit_factor,
        sharpe_ratio=sharpe_ratio,
        max_drawdown=max_drawdown,
        final_equity=final_equity,
        initial_equity=initial_equity,
        total_return=total_return
    )