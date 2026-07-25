"""
scripts/initial_train_hunter.py
Скрипт обучения Hunter'а на исторических данных с диагностикой распределения меток
и балансировкой классов для предотвращения вырождения в HOLD.
"""

import argparse
import yaml
import numpy as np
import pandas as pd
from pathlib import Path

from catboost import CatBoostClassifier

from src.data.indicators import CompositeOscillator, LiquidityZones
from src.agents.spotter import Spotter
from src.agents.hunter import build_hunter_features, label_hunter_targets
from src.utils.helpers import calculate_atr
from src.utils.logger import setup_logger, get_logger


def load_historical_data(data_path: str) -> pd.DataFrame:
    df = pd.read_csv(data_path, parse_dates=['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    return df


def main():
    parser = argparse.ArgumentParser(description="Initial training of Hunter model")
    parser.add_argument('--config', default='config/settings.yaml', help='Path to config file')
    parser.add_argument('--data', default='data/historical.csv', help='Path to historical OHLCV CSV')
    parser.add_argument('--output', default='models/hunter/hunter_v1.cbm', help='Output model path')
    args = parser.parse_args()

    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    setup_logger(log_level='INFO')
    logger = get_logger(__name__)

    logger.info("Loading historical data...")
    df = load_historical_data(args.data)
    logger.info(f"Loaded {len(df)} bars")

    logger.info("Computing composite oscillator...")
    comp = CompositeOscillator()
    curves = comp.compute(df)

    logger.info("Computing liquidity zones...")
    atr = calculate_atr(df['high'].values, df['low'].values, df['close'].values, period=50)
    liq = LiquidityZones(pivot_lookback=14, volume_percentile=90)
    liq_upper, liq_lower = liq.compute_series(df, atr)

    logger.info("Detecting Spotter timestamps...")
    spotter = Spotter(window=50, order=5, max_lag=2)
    spotter_ts_list = spotter.get_signals(curves.long, curves.neutral, curves.short)
    spotter_timestamps = set(spotter_ts_list)

    logger.info("Building Hunter features...")
    X, indices = build_hunter_features(
        df,
        curves.long, curves.neutral, curves.short,
        liq_upper, liq_lower,
        atr,
        spotter_timestamps,
        max_lag=config.get('hunter', {}).get('max_lag', 10)
    )
    logger.info(f"Training samples: {len(indices)}")

    if len(indices) == 0:
        logger.error("No training samples generated. Check parameters or data.")
        return

    logger.info("Labeling targets...")
    y = label_hunter_targets(df, indices, spotter_timestamps,
                             horizon=config.get('hunter', {}).get('target_horizon', 50))

    # Диагностика распределения меток
    unique, counts = np.unique(y, return_counts=True)
    logger.info(f"Label distribution: {dict(zip(unique, counts))}")
    if len(unique) < 3:
        logger.warning("Not all classes present in training data. Model may have poor generalization.")

    # Балансировка классов
    # (опционально можно использовать sample_weight или class_weights)
    # CatBoost поддерживает параметр auto_class_weights
    logger.info("Training CatBoost model with class balancing...")
    model = CatBoostClassifier(
        iterations=500,
        learning_rate=0.1,
        depth=7,
        loss_function='MultiClass',
        verbose=100,
        allow_writing_files=False,
        auto_class_weights='Balanced',   # автоматическая балансировка
        eval_metric = "MultiClass"
    )

    # Разделение train/val по дате (последние 20% для валидации)
    if 'timestamp' in df.columns and len(indices) > 0:
        df_indices = df.iloc[indices]
        last_ts = df_indices['timestamp'].max() if 'timestamp' in df_indices.columns else None
        if last_ts is not None and 'timestamp' in df.columns:
            cutoff = pd.Timestamp(last_ts) - pd.Timedelta(days=config.get('hunter', {}).get('online_learning', {}).get('validation_last_days', 7))
            train_mask = df_indices['timestamp'] < cutoff
            val_mask = ~train_mask
        else:
            split = int(len(X) * 0.8)
            train_mask = np.arange(len(X)) < split
            val_mask = ~train_mask
    else:
        split = int(len(X) * 0.8)
        train_mask = np.arange(len(X)) < split
        val_mask = ~train_mask

    X_train, y_train = X[train_mask], y[train_mask]
    X_val, y_val = X[val_mask], y[val_mask]

    model.fit(
        X_train, y_train,
        eval_set=(X_val, y_val),
        plot=False
    )

    # Оценка на валидации
    from sklearn.metrics import accuracy_score, f1_score, classification_report
    y_pred = model.predict(X_val)
    acc = accuracy_score(y_val, y_pred)
    y_train_pred = model.predict(X_train)  # обязательно X_train, не X_val
    train_acc = accuracy_score(y_train, y_train_pred)
    train_f1 = f1_score(y_train, y_train_pred, average='macro')
    logger.info(f"Validation accuracy: {acc:.4f}, Train accuracy: {train_acc:.4f}, Train macro F1: {train_f1:.4f}")
    logger.info(f"Classification report:\n{classification_report(y_val, y_pred, zero_division=0)}")

    import matplotlib.pyplot as plt

    # Получаем историю обучения
    history = model.evals_result_

    # Строим график
    plt.figure(figsize=(10, 6))
    plt.plot(history['learn']['MultiClass'], label='Train Loss')
    plt.plot(history['validation']['MultiClass'], label='Validation Loss')
    plt.xlabel('Итерация')
    plt.ylabel('MultiClass Loss')
    plt.title('Кривая обучения CatBoost')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(output_path))
    logger.info(f"Model saved to {output_path}")


if __name__ == "__main__":
    main()