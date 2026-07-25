"""Тип колбэка прогресса: сообщение + процент 0–100 (None = неопределённый)."""

from __future__ import annotations

from typing import Callable, Optional

ProgressCallback = Callable[[str, Optional[float]], None]


def noop_progress(message: str, percent: Optional[float] = None) -> None:
    pass
