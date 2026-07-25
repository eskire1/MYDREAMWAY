"""
src/data/storage.py
Управление хранилищем данных Apex V5 Global.
- HDF5 для трёхмерных окон (20,4) с уникальными ID.
- Parquet для логов Hunter и Strategist.
Обновлено: колонки features (Hunter) и features_flat (Strategist) теперь сохраняют признаки
в формате JSON, необходимые для дообучения.
"""

import h5py
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import uuid
import json

# ------------------------------------------------------------------------------
# Хранилище окон (HDF5)
# ------------------------------------------------------------------------------

class WindowStorage:
    """
    Управляет HDF5 файлом с трёхмерными окнами (N, 20, 4).
    Каждое окно имеет уникальный строковый идентификатор (window_id).
    """

    def __init__(self, filepath: str, mode: str = 'a'):
        self.filepath = Path(filepath)
        self.mode = mode
        self._file: Optional[h5py.File] = None

    def open(self) -> None:
        if self._file is None:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            self._file = h5py.File(self.filepath, self.mode)
            self._ensure_datasets()

    def _ensure_datasets(self) -> None:
        if 'windows' not in self._file:
            self._file.create_dataset(
                'windows',
                shape=(0, 20, 4),
                maxshape=(None, 20, 4),
                dtype=np.float32,
                chunks=(1000, 20, 4),
                compression='gzip',
                compression_opts=4
            )
        if 'ids' not in self._file:
            dt = h5py.special_dtype(vlen=str)
            self._file.create_dataset('ids', shape=(0,), maxshape=(None,), dtype=dt)
        if 'timestamps' not in self._file:
            dt = h5py.special_dtype(vlen=str)
            self._file.create_dataset('timestamps', shape=(0,), maxshape=(None,), dtype=dt)

    def add_window(
        self,
        window: np.ndarray,
        timestamp: Optional[datetime] = None,
        window_id: Optional[str] = None
    ) -> str:
        if self._file is None:
            self.open()
        if window.ndim == 2:
            window = window[np.newaxis, ...]
        if window_id is None:
            window_id = str(uuid.uuid4())
        ts_str = (timestamp or datetime.utcnow()).isoformat()
        n = self._file['windows'].shape[0]
        self._file['windows'].resize(n + 1, axis=0)
        self._file['ids'].resize(n + 1, axis=0)
        self._file['timestamps'].resize(n + 1, axis=0)
        self._file['windows'][-1] = window[0]
        self._file['ids'][-1] = window_id
        self._file['timestamps'][-1] = ts_str
        self._file.flush()
        return window_id

    def get_window_by_id(self, window_id: str) -> Optional[np.ndarray]:
        if self._file is None:
            self.open()
        ids = self._file['ids'][:].astype(str)
        matches = np.where(ids == window_id)[0]
        if len(matches) == 0:
            return None
        idx = matches[0]
        return self._file['windows'][idx]

    def get_batch(self, start: int = 0, end: Optional[int] = None) -> np.ndarray:
        if self._file is None:
            self.open()
        if end is None:
            end = self._file['windows'].shape[0]
        return self._file['windows'][start:end]

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ------------------------------------------------------------------------------
# Логирование в Parquet
# ------------------------------------------------------------------------------

class LogStorage:
    """Базовый класс для работы с логами в формате Parquet."""

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self._df: Optional[pd.DataFrame] = None

    def _load(self) -> pd.DataFrame:
        if self.filepath.exists():
            return pd.read_parquet(self.filepath)
        return pd.DataFrame()

    def _save(self, df: pd.DataFrame) -> None:
        df.to_parquet(self.filepath, compression='snappy', index=False)


class HunterLogStorage(LogStorage):
    """
    Лог Hunter.
    Колонки: timestamp, window_id, hunter_probs (JSON строка), outcome_15bars,
             features (JSON список признаков), label (класс 0/1/2).
    """

    def add_record(
        self,
        timestamp: datetime,
        window_id: str,
        hunter_probs: List[float],
        features: Optional[List[float]] = None,
        outcome_15bars: Optional[int] = None,
        label: Optional[int] = None
    ) -> None:
        df = self._load()
        new_row = pd.DataFrame([{
            'timestamp': timestamp,
            'window_id': window_id,
            'hunter_probs': json.dumps(hunter_probs),
            'features': json.dumps(features) if features else None,
            'outcome_15bars': outcome_15bars,
            'label': label
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        self._save(df)

    def update_outcome(self, window_id: str, outcome: int) -> None:
        df = self._load()
        mask = df['window_id'] == window_id
        if mask.any():
            df.loc[mask, 'outcome_15bars'] = outcome
            # Также можно автоматически проставлять label на основе outcome, если нужно
            self._save(df)

    def get_unlabeled(self, limit: Optional[int] = None) -> pd.DataFrame:
        df = self._load()
        unlabeled = df[df['label'].isna()]
        if limit:
            unlabeled = unlabeled.head(limit)
        return unlabeled


class StrategistLogStorage(LogStorage):
    """
    Лог Strategist.
    Колонки: timestamp, features_flat (JSON список признаков),
             predicted_tp_pct, actual_max_excursion_pct.
    """

    def add_record(
        self,
        timestamp: datetime,
        features_flat: np.ndarray,
        predicted_tp_pct: float,
        actual_max_excursion_pct: Optional[float] = None
    ) -> None:
        df = self._load()
        new_row = pd.DataFrame([{
            'timestamp': timestamp,
            'features_flat': json.dumps(features_flat.tolist()),
            'predicted_tp_pct': predicted_tp_pct,
            'actual_max_excursion_pct': actual_max_excursion_pct
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        self._save(df)

    def update_actual(self, index: int, actual: float) -> None:
        df = self._load()
        if index < len(df):
            df.at[index, 'actual_max_excursion_pct'] = actual
            self._save(df)

    def get_unlabeled(self, limit: Optional[int] = None) -> pd.DataFrame:
        df = self._load()
        unlabeled = df[df['actual_max_excursion_pct'].isna()]
        if limit:
            unlabeled = unlabeled.head(limit)
        return unlabeled


# ------------------------------------------------------------------------------
# Утилита для связки хранилищ
# ------------------------------------------------------------------------------

class DataStorageManager:
    """
    Центральный менеджер для работы со всеми хранилищами данных.
    """

    def __init__(self, config: Dict[str, Any]):
        paths = config['paths']
        self.window_storage = WindowStorage(paths['windows_h5'])
        self.hunter_log = HunterLogStorage(paths['logs']['hunter_log'])
        self.strategist_log = StrategistLogStorage(paths['logs']['strategist_log'])

    def log_hunter_signal(
        self,
        timestamp: datetime,
        window_3d: np.ndarray,
        hunter_probs: List[float],
        features: Optional[List[float]] = None,
        label: Optional[int] = None
    ) -> str:
        window_id = self.window_storage.add_window(window_3d, timestamp)
        self.hunter_log.add_record(
            timestamp, window_id, hunter_probs,
            features=features, label=label
        )
        return window_id

    def log_strategist_signal(
        self,
        timestamp: datetime,
        features_flat: np.ndarray,
        predicted_tp_pct: float
    ) -> None:
        self.strategist_log.add_record(timestamp, features_flat, predicted_tp_pct)

    def close(self) -> None:
        self.window_storage.close()