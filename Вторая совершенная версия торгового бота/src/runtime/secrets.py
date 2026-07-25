"""Сохранение API-ключей в .env для live-торговли."""

import os
from pathlib import Path

from dotenv import load_dotenv, set_key

ENV_PATH = Path(".env")


def apply_connection(api_key: str, api_secret: str, testnet: bool) -> None:
    os.environ["BINGX_API_KEY"] = api_key or ""
    os.environ["BINGX_API_SECRET"] = api_secret or ""
    os.environ["BINGX_TESTNET"] = "true" if testnet else "false"


def persist_connection(api_key: str, api_secret: str, testnet: bool) -> None:
    apply_connection(api_key, api_secret, testnet)
    if not ENV_PATH.exists():
        ENV_PATH.write_text("", encoding="utf-8")
    set_key(str(ENV_PATH), "BINGX_API_KEY", api_key or "")
    set_key(str(ENV_PATH), "BINGX_API_SECRET", api_secret or "")
    set_key(str(ENV_PATH), "BINGX_TESTNET", "true" if testnet else "false")


def load_connection_from_env() -> tuple[str, str, bool]:
    load_dotenv(ENV_PATH)
    return (
        os.getenv("BINGX_API_KEY", ""),
        os.getenv("BINGX_API_SECRET", ""),
        os.getenv("BINGX_TESTNET", "true").lower() == "true",
    )
