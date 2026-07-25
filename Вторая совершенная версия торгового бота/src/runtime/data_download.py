"""Загрузка OHLCV с биржи через CCXT + регистрация в реестре."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

from src.runtime.progress import ProgressCallback
from src.runtime.registry import (
    DatasetEntry,
    _load_raw,
    _next_seq,
    dataset_output_path,
    register_dataset,
)
from src.runtime.symbols import normalize_symbol


def download_ohlcv(
    symbol: str,
    timeframe: str = "15m",
    start: str = "2022-01-01",
    end: str = "2023-01-01",
    output_path: Optional[Path] = None,
    exchange_id: str = "binance",
    progress: Optional[ProgressCallback] = None,
) -> Tuple[Path, DatasetEntry]:
    import ccxt

    symbol = normalize_symbol(symbol)

    def report(msg: str, pct: Optional[float] = None) -> None:
        if progress:
            progress(msg, pct)

    pair = symbol.replace("-", "/")
    exchange = getattr(ccxt, exchange_id)({"enableRateLimit": True})
    since = exchange.parse8601(f"{start}T00:00:00Z")
    end_ms = exchange.parse8601(f"{end}T23:59:59Z")
    since_start = since
    span = max(end_ms - since_start, 1)

    data = _load_raw()
    seq = _next_seq(data["datasets"], symbol)
    out = output_path or dataset_output_path(symbol, seq, start, end)

    report(f"Подключение к {exchange_id}: {pair} {timeframe} → #{seq:03d}", 0)
    all_klines = []
    while since < end_ms:
        batch = exchange.fetch_ohlcv(pair, timeframe, since=since, limit=1000)
        if not batch:
            break
        all_klines.extend(batch)
        since = batch[-1][0] + 1
        pct = min(95.0, (since - since_start) / span * 100.0)
        report(f"Загружено {len(all_klines)} свечей…", pct)

    if not all_klines:
        raise RuntimeError("Биржа не вернула данных за указанный период.")

    report("Формирование CSV…", 96)
    df = pd.DataFrame(
        all_klines, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp")

    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)

    report("Регистрация в индексе…", 98)
    entry = register_dataset(symbol=symbol, csv_path=out, start=start, end=end, seq=seq)
    report(f"Готово: {entry.bars} баров · {entry.id}", 100)
    return out, entry
