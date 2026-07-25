"""Обучение Hunter на выбранном датасете (для UI и скриптов)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.runtime.progress import ProgressCallback

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier

from src.agents.hunter import build_hunter_features, label_hunter_targets
from src.agents.spotter import Spotter
from src.data.indicators import CompositeOscillator, LiquidityZones
from src.runtime.params import RuntimeParams
from src.runtime.registry import (
    _load_raw,
    _next_seq,
    get_dataset,
    model_output_path,
    register_model,
)
from src.utils.helpers import calculate_atr
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TrainResult:
    model_id: str
    model_path: str
    val_accuracy: float
    n_samples: int
    label_distribution: dict


def train_hunter(
    params: RuntimeParams,
    dataset_id: str,
    progress: Optional[ProgressCallback] = None,
) -> TrainResult:
    def report(msg: str, pct: Optional[float] = None) -> None:
        logger.info(msg)
        if progress:
            progress(msg, pct)

    ds = get_dataset(dataset_id)
    if ds is None:
        raise FileNotFoundError(f"Датасет не найден: {dataset_id}")

    report(f"Загрузка {ds.path}…", 5)
    df = pd.read_csv(ds.path, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    report("Индикаторы и Spotter…", 20)
    comp = CompositeOscillator()
    curves = comp.compute(df)
    atr = calculate_atr(df["high"].values, df["low"].values, df["close"].values, period=50)
    liq = LiquidityZones(pivot_lookback=14, volume_percentile=90)
    liq_upper, liq_lower = liq.compute_series(df, atr)

    spotter = Spotter(
        window=params.spotter_window,
        order=params.spotter_order,
        max_lag=params.spotter_max_lag,
    )
    spotter_ts = set(spotter.get_signals(curves.long, curves.neutral, curves.short))

    report("Признаки Hunter…", 45)
    X, indices = build_hunter_features(
        df,
        curves.long,
        curves.neutral,
        curves.short,
        liq_upper,
        liq_lower,
        atr,
        spotter_ts,
        max_lag=params.max_lag,
    )
    if len(indices) == 0:
        raise RuntimeError("Нет обучающих примеров. Проверьте данные и параметры Spotter/max_lag.")

    y = label_hunter_targets(df, indices, spotter_ts, horizon=params.target_horizon)
    unique, counts = np.unique(y, return_counts=True)
    label_dist = {int(k): int(v) for k, v in zip(unique, counts)}
    report(f"Метки: {label_dist}", 55)

    split = int(len(X) * 0.8)
    X_train, y_train = X[:split], y[:split]
    X_val, y_val = X[split:], y[split:]

    report("Обучение CatBoost…", 65)
    model = CatBoostClassifier(
        iterations=params.hunter_iterations,
        learning_rate=params.hunter_learning_rate,
        depth=params.hunter_depth,
        loss_function="MultiClass",
        verbose=100,
        allow_writing_files=False,
        auto_class_weights="Balanced",
    )
    model.fit(X_train, y_train, eval_set=(X_val, y_val) if len(X_val) else None)

    val_accuracy = 0.0
    if len(X_val):
        from sklearn.metrics import accuracy_score

        y_pred = model.predict(X_val)
        val_accuracy = float(accuracy_score(y_val, y_pred))
        report(f"Validation accuracy: {val_accuracy:.4f}", 90)

    symbol = ds.symbol
    data = _load_raw()
    seq = _next_seq(data["models"], symbol)
    out_path = model_output_path(symbol, seq)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(out_path))

    entry = register_model(
        symbol=symbol,
        model_path=out_path,
        dataset_id=dataset_id,
        val_accuracy=val_accuracy,
    )
    report(f"Модель сохранена: {entry.path} ({entry.id})", 100)

    return TrainResult(
        model_id=entry.id,
        model_path=entry.path,
        val_accuracy=val_accuracy,
        n_samples=len(indices),
        label_distribution=label_dist,
    )
