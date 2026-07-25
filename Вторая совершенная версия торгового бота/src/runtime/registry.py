"""
Индексация исторических датасетов и моделей Hunter по паре и порядковому номеру.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

REGISTRY_PATH = Path("data/registry.json")
HISTORICAL_ROOT = Path("data/historical")
MODELS_ROOT = Path("models/hunter")


@dataclass
class DatasetEntry:
    id: str
    symbol: str
    seq: int
    path: str
    start: str
    end: str
    bars: int
    created_at: str

    @property
    def label(self) -> str:
        return f"{self.symbol} #{self.seq:03d} ({self.start} … {self.end}, {self.bars} баров)"


@dataclass
class ModelEntry:
    id: str
    symbol: str
    seq: int
    path: str
    dataset_id: str
    created_at: str
    val_accuracy: Optional[float] = None

    @property
    def label(self) -> str:
        acc = f", acc={self.val_accuracy:.3f}" if self.val_accuracy is not None else ""
        return f"{self.symbol} #{self.seq:03d}{acc}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_raw() -> Dict[str, List[Dict[str, Any]]]:
    if not REGISTRY_PATH.exists():
        return {"datasets": [], "models": []}
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"datasets": data.get("datasets", []), "models": data.get("models", [])}


def _save_raw(data: Dict[str, List[Dict[str, Any]]]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _next_seq(items: List[Dict[str, Any]], symbol: str) -> int:
    seqs = [int(x["seq"]) for x in items if x.get("symbol") == symbol]
    return (max(seqs) if seqs else 0) + 1


def list_datasets(symbol: Optional[str] = None) -> List[DatasetEntry]:
    raw = _load_raw()["datasets"]
    entries = [DatasetEntry(**x) for x in raw]
    if symbol:
        entries = [e for e in entries if e.symbol == symbol]
    return sorted(entries, key=lambda e: (e.symbol, e.seq))


def list_models(symbol: Optional[str] = None) -> List[ModelEntry]:
    raw = _load_raw()["models"]
    entries = [ModelEntry(**x) for x in raw]
    if symbol:
        entries = [e for e in entries if e.symbol == symbol]
    return sorted(entries, key=lambda e: (e.symbol, e.seq))


def get_dataset(entry_id: str) -> Optional[DatasetEntry]:
    for e in list_datasets():
        if e.id == entry_id:
            return e
    return None


def get_model(entry_id: str) -> Optional[ModelEntry]:
    for e in list_models():
        if e.id == entry_id:
            return e
    return None


def register_dataset(
    symbol: str,
    csv_path: Path,
    start: str,
    end: str,
    seq: Optional[int] = None,
) -> DatasetEntry:
    data = _load_raw()
    if seq is None:
        seq = _next_seq(data["datasets"], symbol)
    entry_id = f"{symbol}_{seq:03d}"
    rel_path = str(csv_path).replace("\\", "/")
    bars = len(pd.read_csv(csv_path))
    entry = DatasetEntry(
        id=entry_id,
        symbol=symbol,
        seq=seq,
        path=rel_path,
        start=start,
        end=end,
        bars=bars,
        created_at=_now_iso(),
    )
    data["datasets"].append(asdict(entry))
    _save_raw(data)
    return entry


def register_model(
    symbol: str,
    model_path: Path,
    dataset_id: str,
    val_accuracy: Optional[float] = None,
) -> ModelEntry:
    data = _load_raw()
    seq = _next_seq(data["models"], symbol)
    entry_id = f"{symbol}_{seq:03d}"
    entry = ModelEntry(
        id=entry_id,
        symbol=symbol,
        seq=seq,
        path=str(model_path).replace("\\", "/"),
        dataset_id=dataset_id,
        created_at=_now_iso(),
        val_accuracy=val_accuracy,
    )
    data["models"].append(asdict(entry))
    _save_raw(data)
    return entry


def dataset_output_path(symbol: str, seq: int, start: str, end: str) -> Path:
    """Путь для нового CSV: data/historical/ETH-USDT/ETH-USDT_001_20220101_20231231.csv"""
    folder = HISTORICAL_ROOT / symbol
    folder.mkdir(parents=True, exist_ok=True)
    s = start.replace("-", "")
    e = end.replace("-", "")
    return folder / f"{symbol}_{seq:03d}_{s}_{e}.csv"


def model_output_path(symbol: str, seq: int) -> Path:
    folder = MODELS_ROOT / symbol
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{symbol}_{seq:03d}.cbm"


def dropdown_options_datasets(symbol: Optional[str] = None) -> Dict[str, str]:
    """value=id -> label"""
    return {e.id: e.label for e in list_datasets(symbol)}


def dropdown_options_models(symbol: Optional[str] = None) -> Dict[str, str]:
    return {e.id: e.label for e in list_models(symbol)}


def scan_legacy_files() -> None:
    """Подхватывает старые CSV/CBM в реестр, если их ещё нет."""
    data = _load_raw()
    known_paths = {x["path"] for x in data["datasets"]}
    for csv in Path("data").glob("*.csv"):
        if str(csv).replace("\\", "/") in known_paths:
            continue
        try:
            df = pd.read_csv(csv, nrows=5)
            if "timestamp" not in df.columns:
                continue
        except Exception:
            continue
        symbol = "ETH-USDT" if "eth" in csv.name.lower() else "BTC-USDT"
        seq = _next_seq(data["datasets"], symbol)
        entry = DatasetEntry(
            id=f"{symbol}_{seq:03d}",
            symbol=symbol,
            seq=seq,
            path=str(csv).replace("\\", "/"),
            start="",
            end="",
            bars=len(pd.read_csv(csv)),
            created_at=_now_iso(),
        )
        data["datasets"].append(asdict(entry))

    known_models = {x["path"] for x in data["models"]}
    for cbm in Path("models").rglob("*.cbm"):
        p = str(cbm).replace("\\", "/")
        if p in known_models:
            continue
        symbol = "ETH-USDT" if "eth" in cbm.name.lower() else "BTC-USDT"
        seq = _next_seq(data["models"], symbol)
        entry = ModelEntry(
            id=f"{symbol}_{seq:03d}",
            symbol=symbol,
            seq=seq,
            path=p,
            dataset_id="",
            created_at=_now_iso(),
        )
        data["models"].append(asdict(entry))

    _save_raw(data)
