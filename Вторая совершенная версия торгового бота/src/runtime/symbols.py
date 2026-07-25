"""Список и нормализация торговых пар."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

import yaml

PRESET_SYMBOLS = [
    "BTC-USDT",
    "ETH-USDT",
    "SOL-USDT",
    "BNB-USDT",
    "XRP-USDT",
    "DOGE-USDT",
    "ADA-USDT",
    "AVAX-USDT",
    "LINK-USDT",
    "DOT-USDT",
]

CUSTOM_SYMBOLS_PATH = Path("config/custom_symbols.yaml")


def normalize_symbol(raw: str) -> str:
    """BTCUSDT / btc-usdt / BTC/USDT → BTC-USDT."""
    s = raw.strip().upper().replace("/", "-").replace("_", "-")
    s = re.sub(r"\s+", "", s)
    if not s:
        raise ValueError("Пустая торговая пара")
    if "-" not in s:
        if s.endswith("USDT"):
            return f"{s[:-4]}-USDT"
        if s.endswith("USD"):
            return f"{s[:-3]}-USD"
        return f"{s}-USDT"
    parts = s.split("-")
    if len(parts) == 2:
        return f"{parts[0]}-{parts[1]}"
    return s


def load_custom_symbols() -> List[str]:
    if not CUSTOM_SYMBOLS_PATH.exists():
        return []
    with open(CUSTOM_SYMBOLS_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    items = data.get("symbols", [])
    return [normalize_symbol(x) for x in items if x]


def save_custom_symbol(symbol: str) -> None:
    symbol = normalize_symbol(symbol)
    custom = load_custom_symbols()
    if symbol not in custom:
        custom.append(symbol)
    all_syms = sorted(set(PRESET_SYMBOLS + custom))
    CUSTOM_SYMBOLS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CUSTOM_SYMBOLS_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump({"symbols": [s for s in all_syms if s not in PRESET_SYMBOLS]}, f)


def all_symbol_options() -> List[str]:
    return sorted(set(PRESET_SYMBOLS + load_custom_symbols()))
