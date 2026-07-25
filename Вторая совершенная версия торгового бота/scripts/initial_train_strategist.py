"""
scripts/initial_train_strategist.py
Скрипт обучения модели Strategist на исторических данных.
Использует все 19 индикаторов CompositeOscillator, ATR, объём и полные данные ликвидности.
Целевая переменная: максимальная процентная экскурсия цены до следующей метки Spotter
(или до горизонта 50 баров, если меток нет). Модель: CatBoostRegressor с Quantile:alpha=0.8.
"""

import argparse
import yaml
import numpy as np
import pandas as pd
from pathlib import Path

from catboost import CatBoostRegressor

from src.data.indicators import CompositeOscillator, LiquidityZones
from src.agents.spotter import Spotter
from src.agents.strategist import build_strategist_features
from src.utils.helpers import calculate_atr
from src.utils.logger import setup_logger, get_logger


def load_historical_data(data_path: str) -> pd.DataFrame:
    """Загружает исторические OHLCV данные."""
    df = pd.read_csv(data_path, parse_dates=['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    return df


def main():
    parser = argparse.ArgumentParser(description="Initial training of Strategist model")
    parser.add_argument('--config', default='config/settings.yaml', help='Path to config file')
    parser.add_argument('--data', default='data/historical.csv', help='Path to historical OHLCV CSV')
    parser.add_argument('--output', default='models/strategist/strategist_v1.cbm', help='Output model path')
    args = parser.parse_args()

    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    setup_logger(log_level='INFO')
    logger = get_logger(__name__)

    logger.info("Loading historical data...")
    df = load_historical_data(args.data)
    logger.info(f"Loaded {len(df)} bars")

    logger.info("Computing composite oscillator (all 19 indicators)...")
    comp = CompositeOscillator()
    curves_all = comp.get_all_indicators(df)  # словарь с массивами

    logger.info("Computing liquidity zones...")
    atr = calculate_atr(df['high'].values, df['low'].values, df['close'].values, period=50)
    liq = LiquidityZones(pivot_lookback=14, volume_percentile=90)
    liq_upper, liq_lower = liq.compute_series(df, atr)

    logger.info("Detecting Spotter timestamps...")
    # Spotter нужны три кривые, они есть в CompositeOscillatorResult
    curves = comp.compute(df)  # получаем CompositeOscillatorResult для Spotter
    spotter = Spotter(window=50, order=5, max_lag=2)
    spotter_ts = set(spotter.get_signals(curves.long, curves.neutral, curves.short))
    sorted_spotter = sorted(spotter_ts)

    horizon = config.get('hunter', {}).get('target_horizon', 50)  # используем тот же горизонт, что и для Hunter

    logger.info("Building features and targets...")
    X_list = []
    y_list = []
    n = len(df)
    volume = df['volume'].values
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values

    min_bars = 50  # минимальное количество баров для индикаторов

    for i in range(min_bars, n - 1):
        # Формируем признаки для i-го бара
        feats = build_strategist_features(
            curves=curves_all,
            atr=atr,
            volume=volume,
            liq_upper=liq_upper,
            liq_lower=liq_lower,
            index=i
        )

        # Определяем индекс окончания периода (следующая метка Spotter или горизонт)
        # Ищем следующий отсортированный Spotter после i
        next_idx = None
        for s in sorted_spotter:
            if s > i:
                next_idx = s
                break
        if next_idx is None:
            next_idx = min(i + horizon, n - 1)
        else:
            next_idx = min(next_idx, i + horizon)  # ограничиваем горизонтом

        # Максимальная экскурсия (процент от цены закрытия)
        segment_high = high[i+1 : next_idx+1]
        segment_low = low[i+1 : next_idx+1]
        if len(segment_high) == 0:
            continue
        max_up = (segment_high.max() - close[i]) / close[i]
        max_down = (close[i] - segment_low.min()) / close[i]
        target = max(max_up, max_down)  # абсолютная экскурсия

        X_list.append(feats)
        y_list.append(target)

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.float32)
    logger.info(f"Training samples: {len(X)}")

    # Разделение на train/val (последние 20% для валидации)
    split_idx = int(len(X) * 0.8)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]

    strat_cfg = config.get('strategist', {}).get('model', {})
    model = CatBoostRegressor(
        loss_function='Quantile:alpha=0.8',
        iterations=strat_cfg.get('iterations', 500),
        learning_rate=strat_cfg.get('learning_rate', 0.03),
        depth=strat_cfg.get('depth', 6),
        verbose=100,
        allow_writing_files=False
    )

    logger.info("Training Strategist...")
    model.fit(
        X_train, y_train,
        eval_set=(X_val, y_val),
        plot=False
    )

    # Сохранение модели
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(output_path))
    logger.info(f"Model saved to {output_path}")

    # Метрики
    train_r2 = model.score(X_train, y_train)
    val_r2 = model.score(X_val, y_val)
    logger.info(f"Train R²: {train_r2:.4f}, Val R²: {val_r2:.4f}")


if __name__ == "__main__":
    main()