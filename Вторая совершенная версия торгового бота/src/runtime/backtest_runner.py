"""Запуск бэктеста в отдельном потоке."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from src.runtime.progress import ProgressCallback

import pandas as pd
from dataclasses import asdict

from src.agents.hunter import HunterInference, HunterModel
from src.agents.strategist import StrategistInference, StrategistModel
from src.backtest.engine import BacktestEngine
from src.runtime.params import RuntimeParams, build_config
from src.utils.logger import setup_logger


@dataclass
class BacktestResult:
    metrics: Dict[str, Any]
    equity_timestamps: List[str]
    equity_values: List[float]
    trades_count: int
    data_bars: int


class BacktestRunner:
    def __init__(self) -> None:
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.last_result: Optional[BacktestResult] = None
        self.last_error: Optional[str] = None
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def run_async(
        self,
        params: RuntimeParams,
        on_done: Callable[[Optional[BacktestResult], Optional[str]], None],
        on_progress: Optional[ProgressCallback] = None,
    ) -> None:
        with self._lock:
            if self._running:
                raise RuntimeError("Бэктест уже выполняется.")

            def worker() -> None:
                self._running = True
                self.last_error = None
                try:
                    result = self._execute(params, on_progress)
                    self.last_result = result
                    on_done(result, None)
                except Exception as exc:
                    self.last_error = str(exc)
                    on_done(None, str(exc))
                finally:
                    self._running = False

            self._thread = threading.Thread(target=worker, name="apex-backtest", daemon=True)
            self._thread.start()

    @staticmethod
    def _execute(params: RuntimeParams, progress: Optional[ProgressCallback]) -> BacktestResult:
        def report(msg: str, pct: Optional[float] = None) -> None:
            if progress:
                progress(msg, pct)

        setup_logger(log_level="INFO", log_file="logs/apex_v5.log")
        config = build_config(params)

        data_path = params.data_csv
        report(f"Загрузка {data_path}…", 5)
        df = pd.read_csv(data_path, parse_dates=["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)

        report("Загрузка модели Hunter…", 15)
        hunter_model = HunterModel()
        hunter_model.load(config["paths"]["models"]["hunter_model"])
        hunter_inference = HunterInference(hunter_model)

        strategist_model = StrategistModel()
        strat_path = config["paths"]["models"].get("strategist_model", "")
        if strat_path:
            try:
                from pathlib import Path
                if Path(strat_path).exists():
                    strategist_model.load(strat_path)
            except Exception:
                pass
        strategist_inference = StrategistInference(strategist_model)

        report("Симуляция (это может занять несколько минут)…", 30)
        engine = BacktestEngine(config, df, hunter_inference, strategist_inference)
        metrics, equity = engine.run(show_chart=False)
        report("Расчёт метрик…", 95)
        report("Готово", 100)

        return BacktestResult(
            metrics=asdict(metrics),
            equity_timestamps=equity["timestamps"],
            equity_values=equity["equity"],
            trades_count=int(metrics.total_trades),
            data_bars=len(df),
        )

    def run_sync(
        self,
        params: RuntimeParams,
        on_progress: Optional[ProgressCallback] = None,
    ) -> BacktestResult:
        """Синхронный запуск (удобно для async UI через to_thread)."""
        self._running = True
        self.last_error = None
        try:
            result = self._execute(params, on_progress)
            self.last_result = result
            return result
        except Exception as exc:
            self.last_error = str(exc)
            raise
        finally:
            self._running = False
