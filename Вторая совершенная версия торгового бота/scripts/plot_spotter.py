"""
scripts/plot_spotter.py
Визуализация работы Spotter:
- свечной график цены (верхний)
- три кривые композитного осциллятора (нижний)
- вертикальные линии на обоих графиках в точках, найденных Spotter
"""

import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.indicators import CompositeOscillator, LiquidityZones
from src.agents.spotter import Spotter
from src.utils.helpers import calculate_atr

def main():
    parser = argparse.ArgumentParser(description="Plot Spotter signals")
    parser.add_argument('--data', default='data/eth_historical.csv', help='Path to historical CSV')
    parser.add_argument('--start', type=int, default=0, help='Start bar index')
    parser.add_argument('--end', type=int, default=None, help='End bar index (default: all)')
    args = parser.parse_args()

    # Загрузка данных
    df = pd.read_csv(args.data, parse_dates=['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    if args.end is not None:
        df = df.iloc[args.start:args.end]
    else:
        df = df.iloc[args.start:]

    print(f"Loaded {len(df)} bars from {df['timestamp'].min()} to {df['timestamp'].max()}")

    # Индикаторы
    comp = CompositeOscillator()
    curves = comp.compute(df)
    atr = calculate_atr(df['high'].values, df['low'].values, df['close'].values, period=50)
    liq = LiquidityZones(pivot_lookback=14, volume_percentile=90)
    liq_upper, liq_lower = liq.compute_series(df, atr)

    # Spotter
    spotter = Spotter(window=50, order=5, max_lag=2)
    spotter_timestamps = set(spotter.get_signals(curves.long, curves.neutral, curves.short))
    print(f"Spotter found {len(spotter_timestamps)} signals")

    # Создаём два подграфика
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    # 1. Свечной график цены
    ax1.plot(df['timestamp'], df['close'], color='black', linewidth=0.8, label='Close')
    ax1.set_ylabel('Price')
    ax1.set_title('Price and Spotter signals')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')

    # 2. Три кривые осциллятора
    ax2.plot(df['timestamp'], curves.long, color='green', linewidth=0.8, label='Long')
    ax2.plot(df['timestamp'], curves.neutral, color='yellow', linewidth=0.8, label='Neutral')
    ax2.plot(df['timestamp'], curves.short, color='red', linewidth=0.8, label='Short')
    ax2.set_ylabel('Oscillator %')
    ax2.set_xlabel('Time')
    ax2.set_title('Composite Oscillator and Spotter signals')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left')

    # Вертикальные линии на обоих графиках
    for ts_idx in spotter_timestamps:
        if ts_idx < len(df):
            ts = df['timestamp'].iloc[ts_idx]
            ax1.axvline(x=ts, color='blue', alpha=0.3, linewidth=0.8)
            ax2.axvline(x=ts, color='blue', alpha=0.3, linewidth=0.8)

    # Форматирование оси времени
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show(block=True)

if __name__ == "__main__":
    main()