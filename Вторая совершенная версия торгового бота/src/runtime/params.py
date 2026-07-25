"""
Параметры, управляемые из UI (live + бэктест).
Сохраняются в config/ui_state.yaml и накладываются на config/settings.yaml.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, asdict, fields
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

UI_STATE_PATH = Path("config/ui_state.yaml")
BASE_CONFIG_PATH = Path("config/settings.yaml")


@dataclass
class RuntimeParams:
    """Параметры, реально влияющие на live и бэктест."""

    # Биржа
    api_key: str = ""
    api_secret: str = ""
    testnet: bool = True

    # Торговля
    symbol: str = "ETH-USDT"
    prob_threshold: float = 0.5
    tp_atr_mult: float = 4.0
    sl_atr_mult: float = 0.8
    max_lag: int = 10
    target_horizon: int = 50

    # Spotter
    spotter_window: int = 50
    spotter_order: int = 5
    spotter_max_lag: int = 2

    # Hunter (обучение / путь модели)
    hunter_model_path: str = "models/hunter/hunter_eth_2.cbm"
    hunter_iterations: int = 200
    hunter_learning_rate: float = 0.1
    hunter_depth: int = 5

    # Реестр данных и моделей
    dataset_id: str = ""
    model_id: str = ""

    # Бэктест / загрузка
    data_csv: str = "data/eth_historical.csv"
    data_start: str = "2022-01-01"
    data_end: str = "2023-01-01"
    use_critic: bool = False
    enable_learner: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuntimeParams":
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


def _deep_merge(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def build_config(params: RuntimeParams, base_path: Path = BASE_CONFIG_PATH) -> Dict[str, Any]:
    """Собирает итоговый config dict для ApexV5Live / BacktestEngine."""
    with open(base_path, "r", encoding="utf-8") as f:
        base = yaml.safe_load(f)

    overlay = {
        "general": {
            "symbols": [params.symbol],
        },
        "trading": {
            "prob_threshold": params.prob_threshold,
            "tp_atr_mult": params.tp_atr_mult,
            "sl_atr_mult": params.sl_atr_mult,
            "use_critic": params.use_critic,
            "enable_learner": params.enable_learner,
        },
        "spotter": {
            "window": params.spotter_window,
            "order": params.spotter_order,
            "max_lag": params.spotter_max_lag,
        },
        "hunter": {
            "max_lag": params.max_lag,
            "target_horizon": params.target_horizon,
            "model": {
                "iterations": params.hunter_iterations,
                "learning_rate": params.hunter_learning_rate,
                "depth": params.hunter_depth,
            },
        },
        "dispatcher": {
            "risk": {
                "sl_multiplier": params.sl_atr_mult,
            },
        },
        "paths": {
            "models": {
                "hunter_model": params.hunter_model_path,
            },
        },
        "backtest": {
            "use_critic": params.use_critic,
        },
    }
    return _deep_merge(base, overlay)


def load_runtime_params(path: Path = UI_STATE_PATH) -> RuntimeParams:
    if not path.exists():
        return RuntimeParams()
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return RuntimeParams.from_dict(data)


def save_runtime_params(params: RuntimeParams, path: Path = UI_STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(params.to_dict(), f, allow_unicode=True, default_flow_style=False)
