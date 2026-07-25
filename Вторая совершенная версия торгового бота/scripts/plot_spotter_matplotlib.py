import argparse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.indicators import CompositeOscillator
from src.agents.spotter import Spotter


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default='data/eth_historical.csv')
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--end', type=int, default=None)
    args = parser.parse_args()

    # Загрузка данных
    df = pd.read_csv(args.data, parse_dates=['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    if args.end is not None:
        df = df.iloc[args.start:args.end]
    else:
        df = df.iloc[args.start:]

    # Индикаторы
    comp = CompositeOscillator()
    curves = comp.compute(df)

    # Spotter
    spotter = Spotter(window=50, order=5, max_lag=2)
    spotter_ts = spotter.get_signals(curves.long, curves.neutral, curves.short)
    spotter_times = [df['timestamp'].iloc[i] for i in spotter_ts if i < len(df)]

    # Создаём два графика
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    fig.suptitle('Spotter Signals', fontsize=16)

    # Свечной график (заменяем на обычный линейный, так как свечной сложнее, но можно и свечной при желании)
    ax1.plot(df['timestamp'], df['close'], color='black', linewidth=0.8, label='Close')
    ax1.set_ylabel('Price')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')

    # Кривые осциллятора
    ax2.plot(df['timestamp'], curves.long, color='green', linewidth=0.8, label='Long')
    ax2.plot(df['timestamp'], curves.neutral, color='yellow', linewidth=0.8, label='Neutral')
    ax2.plot(df['timestamp'], curves.short, color='red', linewidth=0.8, label='Short')
    ax2.set_ylabel('Oscillator %')
    ax2.set_xlabel('Time')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left')

    # Вертикальные линии Spotter
    for ts in spotter_times:
        ax1.axvline(x=ts, color='blue', alpha=0.3, linewidth=0.8)
        ax2.axvline(x=ts, color='blue', alpha=0.3, linewidth=0.8)

    # Форматирование дат
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.xticks(rotation=45)
    plt.tight_layout()

    print(f"Found {len(spotter_ts)} Spotter signals")
    plt.show()


if __name__ == "__main__":
    main()