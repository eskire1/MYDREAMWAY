"""
tests/test_learner.py
Модульные тесты для агента Learner (src/agents/learner.py).
Проверяет условия запуска дообучения Hunter и Strategist, работу с хранилищами.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile

from src.agents.learner import HunterLearner, StrategistLearner, Learner
from src.data.storage import WindowStorage, HunterLogStorage, StrategistLogStorage


class TestHunterLearner:
    @pytest.fixture
    def config(self):
        return {
            'hunter': {
                'online_learning': {
                    'min_buffer_size': 2000,
                    'min_new_examples': 500,
                    'max_days_since_update': 30,
                    'replay_sample_size': 500,
                    'validation_last_days': 7,
                    'checkpoint_frequency_days': 14
                },
                'training': {
                    'batch_size': 32,
                    'max_epochs': 3,
                    'learning_rate': 0.001
                }
            },
            'paths': {'models': {'hunter_ckpt': 'dummy.ckpt'}}
        }

    @pytest.fixture
    def mock_storage(self):
        window_storage = Mock(spec=WindowStorage)
        hunter_log = Mock(spec=HunterLogStorage)
        return window_storage, hunter_log

    def test_not_enough_buffer(self, config, mock_storage):
        window_storage, hunter_log = mock_storage
        labeled_df = pd.DataFrame({'window_id': ['w1']*1500, 'outcome_15bars': [1]*1500})
        hunter_log._load.return_value = labeled_df
        learner = HunterLearner('dummy.ckpt', window_storage, hunter_log, config)
        updated = learner.check_and_update()
        assert updated is False

    def test_buffer_ok_but_not_enough_new(self, config, mock_storage):
        window_storage, hunter_log = mock_storage
        dates = [datetime.now() - timedelta(days=i) for i in range(2500)]
        labeled_df = pd.DataFrame({
            'window_id': [f'w{i}' for i in range(2500)],
            'outcome_15bars': [1]*2500,
            'timestamp': dates
        })
        hunter_log._load.return_value = labeled_df
        learner = HunterLearner('dummy.ckpt', window_storage, hunter_log, config)
        learner.last_update_time = datetime.now() - timedelta(days=2)
        updated = learner.check_and_update()
        assert updated is False

    @patch('src.agents.learner.HunterLightning')
    @patch('src.agents.learner.load_hunter_from_checkpoint')
    @patch('src.agents.learner.pl.Trainer')
    def test_retraining_triggers(self, mock_trainer, mock_load, mock_lightning, config, mock_storage, tmp_path):
        window_storage, hunter_log = mock_storage
        ckpt_path = tmp_path / "hunter.ckpt"
        ckpt_path.touch()
        base_time = datetime.now()
        dates = [base_time - timedelta(days=i) for i in range(2500)]
        labeled_df = pd.DataFrame({
            'window_id': [f'w{i}' for i in range(2500)],
            'outcome_15bars': [1]*2500,
            'timestamp': dates
        })
        hunter_log._load.return_value = labeled_df
        window_storage.get_window_by_id.return_value = np.random.randn(20, 4).astype(np.float32)

        learner = HunterLearner(str(ckpt_path), window_storage, hunter_log, config)
        learner.last_update_time = base_time - timedelta(days=20)
        mock_model = Mock()
        mock_lightning_module = Mock()
        mock_load.return_value = (mock_model, mock_lightning_module)

        updated = learner.check_and_update()
        assert updated is True
        mock_trainer.return_value.fit.assert_called_once()


class TestStrategistLearner:
    @pytest.fixture
    def config(self):
        return {
            'strategist': {
                'online_learning': {
                    'min_new_examples': 100,
                    'update_frequency_days': 1,
                    'epochs': 5
                },
                'model': {
                    'loss_function': 'Quantile:alpha=0.8',
                    'iterations': 500,
                    'learning_rate': 0.03,
                    'depth': 6
                }
            }
        }

    @pytest.fixture
    def mock_log(self):
        return Mock(spec=StrategistLogStorage)

    def test_not_enough_new_examples(self, config, mock_log):
        labeled_df = pd.DataFrame({
            'features_flat': ['[]']*80,
            'actual_max_excursion_pct': [0.02]*80,
            'timestamp': [datetime.now()]*80
        })
        mock_log._load.return_value = labeled_df
        learner = StrategistLearner('dummy.cbm', mock_log, config)
        updated = learner.check_and_update()
        assert updated is False

    @patch('src.agents.learner.StrategistModel')
    def test_retraining_triggers(self, mock_model_class, config, mock_log, tmp_path):
        model_path = tmp_path / "strat.cbm"
        model_path.touch()
        dates = [datetime.now() - timedelta(days=i) for i in range(150)]
        labeled_df = pd.DataFrame({
            'features_flat': ['[1,2,3]']*150,
            'actual_max_excursion_pct': [0.02]*150,
            'timestamp': dates
        })
        mock_log._load.return_value = labeled_df

        mock_model = Mock()
        mock_model_class.return_value = mock_model

        learner = StrategistLearner(str(model_path), mock_log, config)
        learner.last_update_time = datetime.now() - timedelta(days=2)
        updated = learner.check_and_update()
        assert updated is True
        mock_model.partial_fit.assert_called_once()


class TestLearnerOrchestrator:
    @pytest.fixture
    def config(self):
        return {
            'hunter': {
                'online_learning': {
                    'min_buffer_size': 2000,
                    'min_new_examples': 500,
                    'max_days_since_update': 30,
                    'replay_sample_size': 500,
                    'validation_last_days': 7
                },
                'training': {'batch_size': 32, 'max_epochs': 3, 'learning_rate': 0.001}
            },
            'strategist': {
                'online_learning': {'min_new_examples': 100, 'update_frequency_days': 1, 'epochs': 5},
                'model': {'loss_function': 'Quantile:alpha=0.8', 'iterations': 500, 'learning_rate': 0.03, 'depth': 6}
            },
            'paths': {
                'models': {'hunter_ckpt': 'h.ckpt', 'strategist_model': 's.cbm'}
            }
        }

    @patch('src.agents.learner.HunterLearner')
    @patch('src.agents.learner.StrategistLearner')
    def test_run_calls_both_learners(self, mock_strat_learner, mock_hunter_learner, config):
        window_storage = Mock(spec=WindowStorage)
        hunter_log = Mock(spec=HunterLogStorage)
        strategist_log = Mock(spec=StrategistLogStorage)

        # Создаём экземпляры моков
        mock_hunter_instance = Mock()
        mock_strat_instance = Mock()
        mock_hunter_learner.return_value = mock_hunter_instance
        mock_strat_learner.return_value = mock_strat_instance

        learner = Learner(config, window_storage, hunter_log, strategist_log)
        learner.run()

        # Проверяем, что у каждого внутреннего learner был вызван check_and_update
        mock_hunter_instance.check_and_update.assert_called_once()
        mock_strat_instance.check_and_update.assert_called_once()