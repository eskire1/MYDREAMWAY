"""Журнал процессов: UI + stdout (консоль PyCharm)."""

from __future__ import annotations

from datetime import datetime
from typing import Callable, List, Optional


class ProcessLog:
    def __init__(self, max_lines: int = 500) -> None:
        self.max_lines = max_lines
        self._lines: List[str] = []
        self._listeners: List[Callable[[str], None]] = []

    def subscribe(self, callback: Callable[[str], None]) -> None:
        self._listeners.append(callback)
        callback(self.text)

    def log(self, message: str, level: str = "INFO") -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] [{level}] {message}"
        print(line, flush=True)
        self._lines.append(line)
        if len(self._lines) > self.max_lines:
            self._lines = self._lines[-self.max_lines :]
        for cb in self._listeners:
            cb(self.text)

    @property
    def text(self) -> str:
        return "\n".join(self._lines)

    def clear(self) -> None:
        self._lines.clear()
        for cb in self._listeners:
            cb("")
