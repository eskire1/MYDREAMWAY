"""
tests/test_hunter.py
Модульные тесты для агента Hunter (src/agents/hunter.py).
Проверяет архитектуру модели, инференс, загрузку/сохранение чекпоинтов.
"""

import pytest
import torch
import numpy as np
from pathlib import Path
import tempfile

from src.agents.hunter import (
    HunterModel,
    HunterLightning,
    HunterInference,
    load_hunter_from_checkpoint,
    save_hunter_checkpoint,
    prepare_hunter_dataloader,
)


class TestHunterModel:
    def test_architecture(self):
        model = HunterModel(
            input_size=4,
            hidden_size=64,
            num_layers=2,
            num_heads=4,
            num_classes=3,
        )
        # Проверка параметров согласно документации
        assert model.input_size == 4
        assert model.hidden_size == 64
        assert model.num_layers == 2
        assert model.num_classes == 3

    def test_forward_shape(self):
        model = HunterModel()
        batch_size = 32
        seq_len = 20
        features = 4
        x = torch.randn(batch_size, seq_len, features)
        logits = model(x)
        assert logits.shape == (batch_size, 3)

    def test_predict_proba(self):
        model = HunterModel()
        x = torch.randn(1, 20, 4)
        probs = model.predict_proba(x)
        assert probs.shape == (1, 3)
        assert np.allclose(probs.sum(axis=1), 1.0)


class TestHunterLightning:
    def test_training_step(self):
        model = HunterModel()
        lightning = HunterLightning(model=model, learning_rate=1e-3)
        x = torch.randn(8, 20, 4)
        y = torch.randint(0, 3, (8,))
        batch = (x, y)
        loss = lightning.training_step(batch, 0)
        assert loss is not None
        assert loss.item() > 0


class TestHunterInference:
    def test_predict_signal(self):
        model = HunterModel()
        model.eval()
        inference = HunterInference(model)
        window = np.random.randn(20, 4).astype(np.float32)
        signal, probs = inference.predict(window)
        assert signal in ['LONG', 'SHORT', 'HOLD']
        assert len(probs) == 3
        assert np.isclose(probs.sum(), 1.0)

    def test_batch_input(self):
        model = HunterModel()
        inference = HunterInference(model)
        batch_window = np.random.randn(4, 20, 4).astype(np.float32)
        # predict ожидает (N,20,4) или (20,4)
        signal, probs = inference.predict(batch_window[0])  # тестируем один экземпляр
        assert signal in ['LONG', 'SHORT', 'HOLD']


class TestCheckpoint:
    def test_save_load(self):
        model = HunterModel()
        lightning = HunterLightning(model=model)
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt_path = Path(tmpdir) / "hunter.ckpt"
            save_hunter_checkpoint(lightning, str(ckpt_path))
            assert ckpt_path.exists()

            loaded_model, loaded_lightning = load_hunter_from_checkpoint(str(ckpt_path))
            assert isinstance(loaded_model, HunterModel)
            # Проверяем, что веса совпадают
            for p1, p2 in zip(model.parameters(), loaded_model.parameters()):
                assert torch.allclose(p1, p2)


class TestDataloader:
    def test_prepare_dataloader(self):
        windows = np.random.randn(100, 20, 4).astype(np.float32)
        labels = np.random.randint(0, 3, size=100)
        loader = prepare_hunter_dataloader(windows, labels, batch_size=16)
        batch = next(iter(loader))
        x, y = batch
        assert x.shape == (16, 20, 4)
        assert y.shape == (16,)