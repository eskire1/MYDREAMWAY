"""Фоновый запуск live-торговли (может работать параллельно с бэктестом)."""

from __future__ import annotations

import threading
from typing import Callable, Optional

from src.main import ApexV5Live
from src.runtime.params import RuntimeParams, build_config
from src.runtime.secrets import apply_connection


class LiveRunner:
    def __init__(self) -> None:
        self._thread: Optional[threading.Thread] = None
        self._app: Optional[ApexV5Live] = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(
        self,
        params: RuntimeParams,
        on_status: Optional[Callable[[str], None]] = None,
    ) -> None:
        with self._lock:
            if self.is_running:
                raise RuntimeError("Live-торговля уже запущена.")

            apply_connection(params.api_key, params.api_secret, params.testnet)
            config = build_config(params)

            self._app = ApexV5Live(config=config, register_signals=False)
            self._thread = threading.Thread(
                target=self._run_loop,
                name="apex-live",
                daemon=True,
            )
            self._thread.start()
        if on_status:
            on_status("Live запущен")

    def _run_loop(self) -> None:
        assert self._app is not None
        try:
            self._app.run()
        except Exception:
            self._app.logger.exception("Live loop crashed")

    def stop(self, on_status: Optional[Callable[[str], None]] = None) -> None:
        with self._lock:
            if self._app:
                self._app.stop()
            if self._thread:
                self._thread.join(timeout=15.0)
            self._thread = None
            self._app = None
        if on_status:
            on_status("Live остановлен")
