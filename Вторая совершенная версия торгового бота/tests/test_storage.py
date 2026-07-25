"""
tests/test_storage.py
Модульные тесты для хранилищ данных (src/data/storage.py).
Проверяет WindowStorage (HDF5), HunterLogStorage, StrategistLogStorage (Parquet) и DataStorageManager.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
import tempfile
import json

from src.data.storage import (
    WindowStorage,
    HunterLogStorage,
    StrategistLogStorage,
    DataStorageManager,
)


class TestWindowStorage:
    @pytest.fixture
    def temp_h5(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "windows.h5"

    def test_add_and_get_window(self, temp_h5):
        with WindowStorage(str(temp_h5), mode='w') as storage:
            window = np.random.randn(20, 4).astype(np.float32)
            ts = datetime.now()
            window_id = storage.add_window(window, timestamp=ts)

            retrieved = storage.get_window_by_id(window_id)
            assert retrieved.shape == (20, 4)
            np.testing.assert_array_almost_equal(window, retrieved)

    def test_add_multiple_windows(self, temp_h5):
        with WindowStorage(str(temp_h5), mode='w') as storage:
            ids = []
            for i in range(5):
                window = np.ones((20, 4)) * i
                wid = storage.add_window(window)
                ids.append(wid)

            assert len(ids) == 5
            batch = storage.get_batch(0, 5)
            assert batch.shape == (5, 20, 4)
            for i in range(5):
                assert batch[i, 0, 0] == i

    def test_get_nonexistent_window(self, temp_h5):
        with WindowStorage(str(temp_h5), mode='w') as storage:
            assert storage.get_window_by_id("nonexistent") is None


class TestHunterLogStorage:
    @pytest.fixture
    def temp_parquet(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "hunter_log.parquet"

    def test_add_and_retrieve(self, temp_parquet):
        log = HunterLogStorage(str(temp_parquet))
        ts = datetime.now()
        log.add_record(
            timestamp=ts,
            window_id="test_win_1",
            hunter_probs=[0.7, 0.2, 0.1],
            outcome_15bars=None
        )

        df = log._load()
        assert len(df) == 1
        assert df.iloc[0]['window_id'] == "test_win_1"
        assert df.iloc[0]['outcome_15bars'] is None

    def test_update_outcome(self, temp_parquet):
        log = HunterLogStorage(str(temp_parquet))
        log.add_record(datetime.now(), "win1", [0.6, 0.3, 0.1], None)
        log.update_outcome("win1", 1)

        df = log._load()
        assert df.iloc[0]['outcome_15bars'] == 1

    def test_get_unlabeled(self, temp_parquet):
        log = HunterLogStorage(str(temp_parquet))
        log.add_record(datetime.now(), "win1", [0.5, 0.3, 0.2], None)
        log.add_record(datetime.now(), "win2", [0.6, 0.2, 0.2], 1)

        unlabeled = log.get_unlabeled()
        assert len(unlabeled) == 1
        assert unlabeled.iloc[0]['window_id'] == "win1"


class TestStrategistLogStorage:
    @pytest.fixture
    def temp_parquet(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "strategist_log.parquet"

    def test_add_and_retrieve(self, temp_parquet):
        log = StrategistLogStorage(str(temp_parquet))
        features = np.random.randn(80).astype(np.float32)
        log.add_record(
            timestamp=datetime.now(),
            features_flat=features,
            predicted_tp_pct=0.025,
            actual_max_excursion_pct=None
        )

        df = log._load()
        assert len(df) == 1
        assert df.iloc[0]['predicted_tp_pct'] == 0.025
        assert df.iloc[0]['actual_max_excursion_pct'] is None

    def test_update_actual(self, temp_parquet):
        log = StrategistLogStorage(str(temp_parquet))
        log.add_record(datetime.now(), np.random.randn(80), 0.03, None)
        log.update_actual(0, 0.028)

        df = log._load()
        assert df.iloc[0]['actual_max_excursion_pct'] == 0.028

    def test_get_unlabeled(self, temp_parquet):
        log = StrategistLogStorage(str(temp_parquet))
        log.add_record(datetime.now(), np.random.randn(80), 0.01, None)
        log.add_record(datetime.now(), np.random.randn(80), 0.02, 0.015)

        unlabeled = log.get_unlabeled()
        assert len(unlabeled) == 1


class TestDataStorageManager:
    @pytest.fixture
    def config(self, tmp_path):
        windows_h5 = tmp_path / "windows.h5"
        hunter_log = tmp_path / "hunter.parquet"
        strat_log = tmp_path / "strategist.parquet"
        return {
            'paths': {
                'windows_h5': str(windows_h5),
                'logs': {
                    'hunter_log': str(hunter_log),
                    'strategist_log': str(strat_log)
                }
            }
        }

    def test_log_hunter_signal(self, config):
        mgr = DataStorageManager(config)
        ts = datetime.now()
        window = np.random.randn(20, 4).astype(np.float32)
        probs = [0.8, 0.15, 0.05]
        window_id = mgr.log_hunter_signal(ts, window, probs)

        # Проверяем, что окно сохранено
        retrieved = mgr.window_storage.get_window_by_id(window_id)
        np.testing.assert_array_almost_equal(window, retrieved)

        # Проверяем лог
        df = mgr.hunter_log._load()
        assert len(df) == 1
        assert df.iloc[0]['window_id'] == window_id
        assert json.loads(df.iloc[0]['hunter_probs']) == probs

    def test_log_strategist_signal(self, config):
        mgr = DataStorageManager(config)
        ts = datetime.now()
        features = np.random.randn(80).astype(np.float32)
        mgr.log_strategist_signal(ts, features, 0.035)

        df = mgr.strategist_log._load()
        assert len(df) == 1
        assert df.iloc[0]['predicted_tp_pct'] == 0.035

    def test_close(self, config):
        mgr = DataStorageManager(config)
        mgr.close()
        # Проверяем, что файл HDF5 закрыт (повторный вызов не должен падать)
        mgr.close()