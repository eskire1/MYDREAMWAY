"""
src/agents/learner.py
Агент Learner: онлайн-дообучение CatBoost-моделей Hunter и Strategist.
Реализовано полностью, включая Replay Buffer для Hunter.
"""

import os
import random
import numpy as np
import pandas as pd
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from catboost import CatBoostClassifier, CatBoostRegressor

from src.data.storage import WindowStorage, HunterLogStorage, StrategistLogStorage
from src.utils.logger import get_logger

logger = get_logger(__name__)


class HunterLearner:
    """
    Дообучение CatBoost-классификатора Hunter с Replay Buffer.
    """

    def __init__(
        self,
        hunter_model_path: str,
        hunter_log: HunterLogStorage,
        config: Dict[str, Any]
    ):
        self.model_path = Path(hunter_model_path)
        self.hunter_log = hunter_log

        hunter_cfg = config['hunter']['online_learning']
        self.min_buffer_size = hunter_cfg['min_buffer_size']
        self.min_new_examples = hunter_cfg['min_new_examples']
        self.max_days_since_update = hunter_cfg['max_days_since_update']
        self.replay_sample_size = hunter_cfg['replay_sample_size']
        self.validation_last_days = hunter_cfg['validation_last_days']

        self.model = CatBoostClassifier()
        if self.model_path.exists():
            self.model.load_model(str(self.model_path))
        else:
            logger.warning(f"Hunter model not found at {self.model_path}, will train from scratch on first update.")

        self.last_update_time: Optional[datetime] = None

    def _load_hunter_data(self) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
        """Загружает все размеченные данные из логов Hunter."""
        df = self.hunter_log._load()
        # Ожидаем колонки: 'features' (список), 'label' (0/1/2)
        # Если колонок нет, вернём пустые массивы
        if 'features' not in df.columns or 'label' not in df.columns:
            return df, np.empty((0,)), np.empty((0,))
        labeled = df.dropna(subset=['label'])
        if labeled.empty:
            return df, np.empty((0,)), np.empty((0,))
        X = np.array(labeled['features'].tolist(), dtype=np.float32)
        y = labeled['label'].values.astype(int)
        return labeled, X, y

    def check_and_update(self) -> bool:
        labeled_df, X, y = self._load_hunter_data()
        if len(X) < self.min_buffer_size:
            logger.info(f"Hunter buffer size {len(X)} < {self.min_buffer_size}, skipping.")
            return False

        # Новые примеры после последнего обновления
        new_mask = labeled_df['timestamp'] >= self.last_update_time if self.last_update_time else pd.Series(True, index=labeled_df.index)
        new_X = X[new_mask.values]
        new_y = y[new_mask.values]

        days_since = (datetime.now() - self.last_update_time).days if self.last_update_time else 999
        if len(new_X) < self.min_new_examples and days_since < self.max_days_since_update:
            logger.info(f"Hunter: {len(new_X)} new examples, {days_since} days since update. Not enough for retraining.")
            return False

        logger.info(f"Starting Hunter retraining with total {len(X)} examples, {len(new_X)} new.")

        # Разделение на train/val по дате
        if 'timestamp' in labeled_df.columns:
            last_ts = labeled_df['timestamp'].max()
            cutoff = last_ts - timedelta(days=self.validation_last_days)
            train_idx = labeled_df['timestamp'] < cutoff
            val_idx = ~train_idx
        else:
            split = int(len(X) * 0.9)
            train_idx = np.arange(len(X)) < split
            val_idx = ~train_idx

        X_train, y_train = X[train_idx], y[train_idx]
        X_val, y_val = X[val_idx], y[val_idx]

        # Replay Buffer: добавляем случайные старые примеры к обучающей выборке
        if len(new_X) > 0:
            old_mask = ~new_mask.values if self.last_update_time else pd.Series(False, index=labeled_df.index)
            old_X = X[old_mask]
            old_y = y[old_mask]
            if len(old_X) > 0:
                replay_size = min(self.replay_sample_size, len(old_X))
                replay_idx = np.random.choice(len(old_X), size=replay_size, replace=False)
                X_train = np.vstack([X_train, old_X[replay_idx]])
                y_train = np.concatenate([y_train, old_y[replay_idx]])

        # Дообучение
        self.model.fit(X_train, y_train, eval_set=(X_val, y_val), verbose=False)
        self.model.save_model(str(self.model_path))

        self.last_update_time = datetime.now()
        logger.info(f"Hunter retraining completed, model saved to {self.model_path}")
        return True


class StrategistLearner:
    """
    Дообучение CatBoost-регрессора Strategist.
    """

    def __init__(
        self,
        strategist_model_path: str,
        strategist_log: StrategistLogStorage,
        config: Dict[str, Any]
    ):
        self.model_path = Path(strategist_model_path)
        self.strategist_log = strategist_log

        strat_cfg = config['strategist']['online_learning']
        self.min_new_examples = strat_cfg['min_new_examples']
        self.update_frequency_days = strat_cfg['update_frequency_days']
        self.epochs = strat_cfg['epochs']

        self.model = CatBoostRegressor()
        if self.model_path.exists():
            self.model.load_model(str(self.model_path))
        else:
            logger.warning(f"Strategist model not found at {self.model_path}, will train from scratch on first update.")

        self.last_update_time: Optional[datetime] = None

    def _load_strategist_data(self) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
        """Загружает данные из логов Strategist."""
        df = self.strategist_log._load()
        if 'features_flat' not in df.columns or 'actual_max_excursion_pct' not in df.columns:
            return df, np.empty((0,)), np.empty((0,))
        labeled = df.dropna(subset=['actual_max_excursion_pct'])
        if labeled.empty:
            return df, np.empty((0,)), np.empty((0,))
        X = np.array(labeled['features_flat'].tolist(), dtype=np.float32)
        y = labeled['actual_max_excursion_pct'].values.astype(float)
        return labeled, X, y

    def check_and_update(self) -> bool:
        labeled_df, X, y = self._load_strategist_data()
        if len(X) < self.min_new_examples:
            logger.info(f"Strategist: only {len(X)} labeled examples, need {self.min_new_examples}")
            return False

        new_mask = labeled_df['timestamp'] >= self.last_update_time if self.last_update_time else pd.Series(True, index=labeled_df.index)
        new_X = X[new_mask.values]
        new_y = y[new_mask.values]

        if len(new_X) < self.min_new_examples:
            logger.info(f"Strategist: {len(new_X)} new examples, not enough.")
            return False

        logger.info(f"Strategist retraining on {len(new_X)} new examples.")
        self.model.fit(new_X, new_y, init_model=self.model, epochs=self.epochs, verbose=False)
        self.model.save_model(str(self.model_path))
        self.last_update_time = datetime.now()
        logger.info(f"Strategist retraining completed, model saved to {self.model_path}")
        return True


class Learner:
    """
    Оркестратор дообучения.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        window_storage: WindowStorage,
        hunter_log: HunterLogStorage,
        strategist_log: StrategistLogStorage
    ):
        self.config = config
        self.hunter_learner = HunterLearner(
            hunter_model_path=config['paths']['models']['hunter_model'],
            hunter_log=hunter_log,
            config=config
        )
        self.strategist_learner = StrategistLearner(
            strategist_model_path=config['paths']['models']['strategist_model'],
            strategist_log=strategist_log,
            config=config
        )

        self.last_check_time: Dict[str, datetime] = {
            'hunter': datetime.min,
            'strategist': datetime.min
        }

    def run(self) -> None:
        now = datetime.now()
        if (now - self.last_check_time['strategist']).days >= self.strategist_learner.update_frequency_days:
            logger.info("Running Strategist learner check...")
            try:
                updated = self.strategist_learner.check_and_update()
                if updated:
                    self.last_check_time['strategist'] = now
            except Exception as e:
                logger.exception(f"Strategist learner failed: {e}")

        if (now - self.last_check_time['hunter']).days >= 1:
            logger.info("Running Hunter learner check...")
            try:
                updated = self.hunter_learner.check_and_update()
                if updated:
                    self.last_check_time['hunter'] = now
            except Exception as e:
                logger.exception(f"Hunter learner failed: {e}")