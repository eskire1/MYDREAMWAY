"""
src/agents/learner.py
Агент Learner: онлайн-дообучение CatBoost-моделей Hunter и Strategist.
Реализовано полностью, включая Replay Buffer для Hunter.
"""

import os
import random
import json
import numpy as np
import pandas as pd
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from catboost import CatBoostClassifier, CatBoostRegressor

from src.data.storage import WindowStorage, HunterLogStorage, StrategistLogStorage
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _decode_feature_matrix(values: pd.Series) -> np.ndarray:
    decoded = []
    for value in values:
        if isinstance(value, str):
            decoded.append(json.loads(value))
        else:
            decoded.append(value)
    return np.array(decoded, dtype=np.float32)


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
        X = _decode_feature_matrix(labeled['features'])
        y = labeled['label'].values.astype(int)
        return labeled, X, y

    def check_and_update(self) -> bool:
        labeled_df, X, y = self._load_hunter_data()
        if len(X) < self.min_buffer_size:
            logger.info(f"Hunter buffer size {len(X)} < {self.min_buffer_size}, skipping.")
            return False

        new_mask = labeled_df['timestamp'] >= self.last_update_time if self.last_update_time else pd.Series(True,
                                                                                                            index=labeled_df.index)
        new_X = X[new_mask.values]
        new_y = y[new_mask.values]

        days_since = (datetime.now() - self.last_update_time).days if self.last_update_time else 999
        if len(new_X) < self.min_new_examples and days_since < self.max_days_since_update:
            logger.info(
                f"Hunter: {len(new_X)} new examples, {days_since} days since update. Not enough for retraining.")
            return False

        logger.info(f"Starting Hunter retraining with total {len(X)} examples, {len(new_X)} new.")

        # Разделение на train/val (по дате)
        if 'timestamp' in labeled_df.columns:
            last_ts = labeled_df['timestamp'].max()
            cutoff = last_ts - timedelta(days=self.validation_last_days)
            train_idx = labeled_df['timestamp'] < cutoff
            val_idx = ~train_idx
        else:
            split = int(len(X) * 0.9)
            train_idx = np.arange(len(X)) < split
            val_idx = ~train_idx

        X_train_base, y_train_base = X[train_idx], y[train_idx]
        X_val, y_val = X[val_idx], y[val_idx]

        # --------------- Replay Buffer с пропорциональным отбором ---------------
        if len(new_X) > 0 and self.last_update_time is not None:
            old_mask = ~new_mask.values
            old_X = X[old_mask]
            old_y = y[old_mask]

            if len(old_X) > 0:
                total_needed = min(self.replay_sample_size, len(old_X))

                # Вычисляем ошибки для каждого старого примера (если модель обучена)
                if self.model.is_fitted():
                    probs = self.model.predict_proba(old_X)
                    # ошибка = 1 - вероятность правильного класса
                    errors = 1.0 - probs[np.arange(len(old_y)), old_y]
                    # Устойчивость — это обратная величина ошибки (или просто низкая ошибка)
                    stability = -errors  # чтобы сортировка по возрастанию дала самые стабильные
                else:
                    # Если модель не обучена, используем случайный порядок (равномерно)
                    errors = np.random.rand(len(old_X))
                    stability = -errors

                # Индексы для трёх групп
                # 10% наибольших ошибок (top_errors)
                n_errors = max(1, int(total_needed * 0.10))
                # 15% наименьших ошибок (top_stable)
                n_stable = max(1, int(total_needed * 0.15))
                # Остаток (75%) добираем случайно из оставшихся
                n_random = total_needed - n_errors - n_stable

                # Индексы, отсортированные по ошибке (от большей к меньшей)
                sorted_error_idx = np.argsort(errors)[::-1]  # убывание ошибки
                # Индексы по устойчивости (от самой стабильной к менее стабильной = возрастание ошибки)
                sorted_stable_idx = np.argsort(errors)  # возрастание ошибки (самые стабильные в начале)

                # Берём top_errors (первые n_errors из sorted_error_idx)
                selected_error = sorted_error_idx[:n_errors]
                # Берём top_stable (первые n_stable из sorted_stable_idx)
                selected_stable = sorted_stable_idx[:n_stable]

                # Исключаем уже отобранные индексы из пула для случайной выборки
                used_idx = set(selected_error) | set(selected_stable)
                remaining_idx = [idx for idx in range(len(old_X)) if idx not in used_idx]
                if len(remaining_idx) >= n_random:
                    selected_random = np.random.choice(remaining_idx, size=n_random, replace=False)
                else:
                    # Если оставшихся недостаточно, добираем из использованных (но это маловероятно)
                    selected_random = np.random.choice(range(len(old_X)), size=n_random, replace=False)

                # Собираем финальный набор старых примеров
                final_old_indices = np.concatenate([selected_error, selected_stable, selected_random])
                X_old_selected = old_X[final_old_indices]
                y_old_selected = old_y[final_old_indices]

                # Добавляем к новым примерам
                X_train = np.vstack([new_X, X_old_selected])
                y_train = np.concatenate([new_y, y_old_selected])
            else:
                X_train, y_train = new_X, new_y
        else:
            # Если новых примеров нет или last_update_time None, просто используем то, что есть
            X_train, y_train = X_train_base, y_train_base
        # ----------------------------------------------------------------------------

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
        X = _decode_feature_matrix(labeled['features_flat'])
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
        fit_kwargs = {"verbose": False}
        if self.model.is_fitted():
            fit_kwargs["init_model"] = self.model
        self.model.fit(new_X, new_y, **fit_kwargs)
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
