"""
Apex V5 — минималистичный UI для live-торговли и бэктеста.

Запуск из корня проекта:
    python -m src.ui.app
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from nicegui import app, ui

from src.execution.broker import BingXBroker
from src.runtime.backtest_runner import BacktestRunner
from src.runtime.data_download import download_ohlcv
from src.runtime.live_runner import LiveRunner
from src.runtime.params import RuntimeParams, load_runtime_params, save_runtime_params
from src.runtime.registry import (
    dropdown_options_datasets,
    dropdown_options_models,
    get_dataset,
    get_model,
    scan_legacy_files,
)
from src.runtime.secrets import apply_connection, load_connection_from_env, persist_connection
from src.runtime.symbols import all_symbol_options, normalize_symbol, save_custom_symbol
from src.runtime.train_hunter import train_hunter
from src.ui.process_log import ProcessLog

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CUSTOM_CSS = """
:root {
    --apex-bg: #0c0e14;
    --apex-surface: #151922;
    --apex-border: #252a36;
    --apex-accent: #3d8bfd;
    --apex-accent-dim: #2a5a9e;
    --apex-text: #e8eaef;
    --apex-muted: #8b92a5;
    --apex-success: #3ecf8e;
    --apex-danger: #f07178;
}
body {
    background: var(--apex-bg) !important;
    color: var(--apex-text);
    font-family: 'Segoe UI', system-ui, sans-serif;
}
.apex-header {
    letter-spacing: 0.12em;
    font-weight: 300;
    font-size: 1.75rem;
    color: var(--apex-text);
}
.apex-sub {
    color: var(--apex-muted);
    font-size: 0.85rem;
}
.apex-card {
    background: var(--apex-surface) !important;
    border: 1px solid var(--apex-border) !important;
    border-radius: 12px !important;
}
.apex-tabs .q-tab {
    color: var(--apex-muted);
    text-transform: none;
    font-weight: 500;
}
.apex-tabs .q-tab--active {
    color: var(--apex-accent) !important;
}
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.8rem;
    border: 1px solid var(--apex-border);
}
.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}
.status-idle .status-dot { background: var(--apex-muted); }
.status-run .status-dot { background: var(--apex-success); box-shadow: 0 0 8px var(--apex-success); }
.status-idle { color: var(--apex-muted); }
.status-run { color: var(--apex-success); border-color: #2a4a3a; }
"""


class ApexUI:
    def __init__(self) -> None:
        self.params = load_runtime_params()
        key, secret, testnet = load_connection_from_env()
        if key and not self.params.api_key:
            self.params.api_key = key
        if secret and not self.params.api_secret:
            self.params.api_secret = secret
        self.params.testnet = testnet

        scan_legacy_files()

        self.live_runner = LiveRunner()
        self.backtest_runner = BacktestRunner()
        self._download_running = False
        self._train_running = False
        self.process_log = ProcessLog()
        self._log_dialog: Optional[ui.dialog] = None

        self.widgets: dict = {}

    def _ui_thread(self, fn) -> None:
        """Безопасное обновление UI из фонового потока."""
        try:
            ui.run(fn)
        except Exception:
            fn()

    def _log_process(self, message: str, level: str = "INFO") -> None:
        self.process_log.log(message, level=level)

    def _set_progress(self, message: str, percent: Optional[float] = None) -> None:
        if "progress_label" not in self.widgets:
            return
        self.widgets["progress_label"].set_text(message)
        bar = self.widgets["progress_bar"]
        if percent is None:
            bar.value = 0
            bar.props("indeterminate")
        else:
            bar.props(remove="indeterminate")
            bar.value = max(0.0, min(1.0, percent / 100.0))

    def _reset_progress(self) -> None:
        self._set_progress("Готов к работе", 0)

    def _make_progress_callback(self):
        def cb(message: str, percent: Optional[float] = None) -> None:
            def update() -> None:
                self._set_progress(message, percent)
                self._log_process(message)
            self._ui_thread(update)
        return cb

    def _get_symbol(self) -> str:
        custom = ""
        if "symbol_custom" in self.widgets:
            custom = (self.widgets["symbol_custom"].value or "").strip()
        if custom:
            return normalize_symbol(custom)
        return normalize_symbol(self.widgets["symbol"].value)

    def _add_custom_symbol(self) -> None:
        try:
            sym = self._get_symbol()
            save_custom_symbol(sym)
            self.widgets["symbol_custom"].value = ""
            self._refresh_symbol_dropdown(sym)
            self._refresh_registry_dropdowns()
            ui.notify(f"Пара {sym} добавлена", type="positive")
            self._log_process(f"Добавлена пара {sym}")
        except Exception as exc:
            ui.notify(str(exc), type="negative")

    def _open_process_log_dialog(self) -> None:
        if self._log_dialog is not None:
            self.widgets["process_log_dialog_text"].value = self.process_log.text
            self._log_dialog.open()

    def _resolve_paths(self, p: RuntimeParams) -> RuntimeParams:
        if p.dataset_id:
            ds = get_dataset(p.dataset_id)
            if ds:
                p.data_csv = ds.path
        if p.model_id:
            m = get_model(p.model_id)
            if m:
                p.hunter_model_path = m.path
        return p

    def _apply_select_options(
        self,
        widget,
        options: dict[str, str],
        preferred_value: Optional[str] = None,
        empty_label: str = "— нет данных —",
    ) -> None:
        """Обновляет ui.select после изменения реестра (NiceGUI требует set_options)."""
        if widget is None:
            return
        if not options:
            options = {"": empty_label}
            value = preferred_value if preferred_value in options else ""
        else:
            if preferred_value and preferred_value in options:
                value = preferred_value
            elif preferred_value and preferred_value not in options:
                value = next(iter(options))
            else:
                value = next(iter(options))

        if hasattr(widget, "set_options"):
            widget.set_options(options, value=value)
        else:
            widget.options = options
            widget.value = value
            widget.update()

    def _refresh_symbol_dropdown(self, symbol: Optional[str] = None) -> None:
        widget = self.widgets.get("symbol")
        if widget is None:
            return
        opts = all_symbol_options()
        value = normalize_symbol(symbol) if symbol else self._get_symbol()
        if value not in opts:
            opts = sorted(set(opts) | {value})
        if hasattr(widget, "set_options"):
            widget.set_options(opts, value=value)
        else:
            widget.options = opts
            widget.value = value
            widget.update()

    def _refresh_registry_dropdowns(
        self,
        dataset_id: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> None:
        symbol = self._get_symbol()
        ds_opts = dropdown_options_datasets(symbol)
        m_opts = dropdown_options_models(symbol)
        did = dataset_id or self.params.dataset_id
        mid = model_id or self.params.model_id

        for key in ("dataset_select", "dataset_select_bt"):
            self._apply_select_options(
                self.widgets.get(key),
                ds_opts,
                did,
                empty_label="— нет данных —",
            )
        self._apply_select_options(
            self.widgets.get("model_select"),
            m_opts,
            mid,
            empty_label="— нет моделей —",
        )

    def _collect_params(self) -> RuntimeParams:
        p = self.params
        p.api_key = self.widgets["api_key"].value or ""
        p.api_secret = self.widgets["api_secret"].value or ""
        p.testnet = self.widgets["testnet"].value
        p.symbol = self._get_symbol()
        p.prob_threshold = float(self.widgets["prob_threshold"].value)
        p.tp_atr_mult = float(self.widgets["tp_atr_mult"].value)
        p.sl_atr_mult = float(self.widgets["sl_atr_mult"].value)
        p.max_lag = int(self.widgets["max_lag"].value)
        p.target_horizon = int(self.widgets["target_horizon"].value)
        p.spotter_window = int(self.widgets["spotter_window"].value)
        p.spotter_order = int(self.widgets["spotter_order"].value)
        p.spotter_max_lag = int(self.widgets["spotter_max_lag"].value)
        p.hunter_iterations = int(self.widgets["hunter_iterations"].value)
        p.hunter_learning_rate = float(self.widgets["hunter_learning_rate"].value)
        p.hunter_depth = int(self.widgets["hunter_depth"].value)
        p.data_start = self.widgets["data_start"].value
        p.data_end = self.widgets["data_end"].value
        p.use_critic = self.widgets["use_critic"].value
        for key in ("dataset_select", "dataset_select_bt"):
            if key in self.widgets and self.widgets[key].value:
                p.dataset_id = self.widgets[key].value
                break
        if "model_select" in self.widgets and self.widgets["model_select"].value:
            p.model_id = self.widgets["model_select"].value
        return self._resolve_paths(p)

    def _save_params(self) -> None:
        self.params = self._collect_params()
        save_runtime_params(self.params)
        ui.notify("Параметры сохранены", type="positive")

    def _save_connection(self) -> None:
        p = self._collect_params()
        persist_connection(p.api_key, p.api_secret, p.testnet)
        ui.notify("Подключение к BingX сохранено", type="positive")

    async def _test_connection(self) -> None:
        p = self._collect_params()
        if not p.api_key or not p.api_secret:
            ui.notify("Укажите API Key и Secret", type="negative")
            return
        persist_connection(p.api_key, p.api_secret, p.testnet)
        self._set_progress("Проверка BingX…", None)
        self._log_process(f"Проверка BingX для {p.symbol}…")

        def check() -> tuple[bool, str]:
            broker = BingXBroker(p.api_key, p.api_secret, p.testnet)
            ok = broker.test_connection(p.symbol)
            mode = "VST/testnet" if p.testnet else "production"
            return ok, mode

        try:
            ok, mode = await asyncio.to_thread(check)
            if ok:
                self._set_progress(f"BingX OK ({mode})", 100)
                self._log_process(f"BingX OK ({mode})")
                ui.notify(f"BingX OK ({mode})", type="positive")
            else:
                self._set_progress("Ошибка BingX", 0)
                self._log_process(f"BingX ошибка ({mode})", level="ERROR")
                ui.notify(
                    f"Ошибка BingX ({mode}). Выключите Testnet или проверьте сеть.",
                    type="negative",
                )
        finally:
            ui.timer(2.0, self._reset_progress, once=True)

    def _refresh_live_status(self) -> None:
        running = self.live_runner.is_running
        bt_running = self.backtest_runner.is_running
        pill = self.widgets["live_status"]
        bt_pill = self.widgets.get("bt_status")
        if running:
            pill.classes(remove="status-idle", add="status-run")
            self.widgets["live_status_text"].set_text("Live · активен")
        else:
            pill.classes(remove="status-run", add="status-idle")
            self.widgets["live_status_text"].set_text("Live · остановлен")
        if bt_pill is not None:
            if bt_running:
                bt_pill.classes(remove="status-idle", add="status-run")
                self.widgets["bt_status_text"].set_text("Бэктест · идёт")
            else:
                bt_pill.classes(remove="status-run", add="status-idle")
                self.widgets["bt_status_text"].set_text("Бэктест · готов")

    def _append_log(self, target: str, message: str) -> None:
        log = self.widgets[target]
        prev = log.value or ""
        log.value = (prev + message + "\n")[-8000:]

    def _start_live(self) -> None:
        if self.live_runner.is_running:
            ui.notify("Live уже запущен", type="warning")
            return
        p = self._collect_params()
        if not p.api_key or not p.api_secret:
            ui.notify("Укажите API Key и Secret", type="negative")
            return
        if not Path(p.hunter_model_path).exists():
            ui.notify(f"Модель не найдена: {p.hunter_model_path}", type="negative")
            return
        save_runtime_params(p)
        persist_connection(p.api_key, p.api_secret, p.testnet)
        try:
            self._log_process(f"Старт live: {p.symbol}, порог {p.prob_threshold}")
            self.live_runner.start(p, on_status=lambda m: self._append_log("live_log", m))
            self._append_log("live_log", f"Старт live: {p.symbol}, порог {p.prob_threshold}")
            ui.notify("Live-торговля запущена", type="positive")
        except Exception as exc:
            ui.notify(str(exc), type="negative")
        self._refresh_live_status()

    def _stop_live(self) -> None:
        self.live_runner.stop(on_status=lambda m: self._append_log("live_log", m))
        self._refresh_live_status()
        ui.notify("Live остановлен", type="info")

    async def _download_data(self) -> None:
        if self._download_running:
            return
        p = self._collect_params()
        self._download_running = True
        self._set_progress("Старт загрузки…", 0)
        self._log_process(f"Загрузка OHLCV {p.symbol} {p.data_start}…{p.data_end}")
        cb = self._make_progress_callback()
        try:
            out, entry = await asyncio.to_thread(
                download_ohlcv,
                symbol=p.symbol,
                start=p.data_start,
                end=p.data_end,
                progress=cb,
            )
            self.params.dataset_id = entry.id
            self._refresh_registry_dropdowns(dataset_id=entry.id)
            save_runtime_params(self._collect_params())
            self._append_log("data_log", f"{entry.label} → {out.name}")
            ui.notify(f"Датасет {entry.id}", type="positive")
        except Exception as exc:
            self._set_progress("Ошибка загрузки", 0)
            self._log_process(f"ERROR: {exc}", level="ERROR")
            ui.notify(f"Ошибка: {exc}", type="negative")
            self._append_log("data_log", f"ERROR: {exc}")
        finally:
            self._download_running = False
            ui.timer(3.0, self._reset_progress, once=True)

    async def _train_model(self) -> None:
        if self._train_running:
            return
        p = self._collect_params()
        if not p.dataset_id:
            ui.notify("Выберите датасет", type="negative")
            return
        self._train_running = True
        self._set_progress("Обучение Hunter…", 0)
        self._log_process(f"Обучение Hunter на {p.dataset_id}")
        self._append_log("data_log", "Обучение Hunter…")
        cb = self._make_progress_callback()
        try:
            result = await asyncio.to_thread(train_hunter, p, p.dataset_id, cb)
            self.params.model_id = result.model_id
            self.params.hunter_model_path = result.model_path
            self._refresh_registry_dropdowns(model_id=result.model_id)
            save_runtime_params(self._collect_params())
            msg = (
                f"Модель {result.model_id}, acc={result.val_accuracy:.3f}, "
                f"примеров={result.n_samples}"
            )
            self._append_log("data_log", msg)
            ui.notify("Обучение завершено", type="positive")
        except Exception as exc:
            self._set_progress("Ошибка обучения", 0)
            self._log_process(f"ERROR: {exc}", level="ERROR")
            ui.notify(str(exc), type="negative")
            self._append_log("data_log", f"ERROR: {exc}")
        finally:
            self._train_running = False
            ui.timer(3.0, self._reset_progress, once=True)

    async def _run_backtest(self) -> None:
        if self.backtest_runner.is_running:
            ui.notify("Бэктест уже идёт", type="warning")
            return
        p = self._collect_params()
        if not Path(p.data_csv).exists():
            ui.notify(f"Файл данных не найден: {p.data_csv}", type="negative")
            return
        if not Path(p.hunter_model_path).exists():
            ui.notify(f"Модель не найдена: {p.hunter_model_path}", type="negative")
            return
        save_runtime_params(p)
        self._set_progress("Бэктест…", 0)
        self._log_process(f"Бэктест {p.symbol}, датасет {p.dataset_id}")
        self._append_log("bt_log", "Запуск бэктеста…")
        self.widgets["bt_metrics"].content = "*Выполняется…*"
        self._refresh_live_status()
        cb = self._make_progress_callback()
        try:
            result = await asyncio.to_thread(self.backtest_runner.run_sync, p, cb)
            m = result.metrics
            self.widgets["bt_metrics"].content = (
                f"**Сделок** {m.get('total_trades', 0)}  \n"
                f"**Win rate** {m.get('win_rate', 0) * 100:.1f}%  \n"
                f"**PnL** {m.get('total_pnl', 0):.2f} USDT  \n"
                f"**Return** {m.get('total_return', 0) * 100:.2f}%  \n"
                f"**Sharpe** {m.get('sharpe_ratio', 0):.2f}  \n"
                f"**Max DD** {m.get('max_drawdown', 0) * 100:.2f}%  \n"
                f"**Баров** {result.data_bars}"
            )
            chart = self.widgets["equity_chart"]
            chart.options["xAxis"]["data"] = result.equity_timestamps
            chart.options["series"][0]["data"] = result.equity_values
            chart.update()
            ui.notify("Бэктест завершён", type="positive")
            self._append_log("bt_log", "Готово.")
        except Exception as exc:
            self._set_progress("Ошибка бэктеста", 0)
            self._log_process(f"ERROR: {exc}", level="ERROR")
            self.widgets["bt_metrics"].content = f"**Ошибка:** {exc}"
            ui.notify(str(exc), type="negative")
            self._append_log("bt_log", f"ERROR: {exc}")
        finally:
            self._refresh_live_status()
            ui.timer(3.0, self._reset_progress, once=True)

    def _build_strategy_fields(self, container) -> None:
        p = self.params
        with container:
            with ui.row().classes("w-full gap-4 flex-wrap"):
                self.widgets["prob_threshold"] = ui.number(
                    "Порог вероятности", value=p.prob_threshold, min=0.1, max=0.99, step=0.01
                ).classes("min-w-[160px]")
                self.widgets["tp_atr_mult"] = ui.number(
                    "TP (× ATR)", value=p.tp_atr_mult, min=0.1, max=20, step=0.1
                ).classes("min-w-[120px]")
                self.widgets["sl_atr_mult"] = ui.number(
                    "SL (× ATR)", value=p.sl_atr_mult, min=0.1, max=10, step=0.1
                ).classes("min-w-[120px]")
                self.widgets["max_lag"] = ui.number(
                    "max_lag", value=p.max_lag, min=1, max=50, step=1, format="%.0f"
                ).classes("min-w-[100px]")
                self.widgets["target_horizon"] = ui.number(
                    "target_horizon", value=p.target_horizon, min=5, max=200, step=1, format="%.0f"
                ).classes("min-w-[130px]")

            with ui.expansion("Spotter", icon="timeline").classes("w-full text-grey-4"):
                with ui.row().classes("gap-4 flex-wrap"):
                    self.widgets["spotter_window"] = ui.number(
                        "window", value=p.spotter_window, min=10, max=200, format="%.0f"
                    )
                    self.widgets["spotter_order"] = ui.number(
                        "order", value=p.spotter_order, min=2, max=20, format="%.0f"
                    )
                    self.widgets["spotter_max_lag"] = ui.number(
                        "max_lag", value=p.spotter_max_lag, min=1, max=10, format="%.0f"
                    )

            m_opts = dropdown_options_models(p.symbol) or {"": "— нет моделей —"}
            self.widgets["model_select"] = ui.select(
                m_opts,
                value=p.model_id if p.model_id in m_opts else (next(iter(m_opts)) if m_opts else ""),
                label="Модель Hunter",
            ).classes("min-w-[320px] flex-grow")

            with ui.expansion("Параметры обучения CatBoost", icon="psychology").classes("w-full text-grey-4"):
                with ui.row().classes("gap-4 flex-wrap w-full"):
                    self.widgets["hunter_iterations"] = ui.number(
                        "iterations", value=p.hunter_iterations, min=50, max=2000, format="%.0f"
                    )
                    self.widgets["hunter_learning_rate"] = ui.number(
                        "learning_rate", value=p.hunter_learning_rate, min=0.001, max=0.5, step=0.01
                    )
                    self.widgets["hunter_depth"] = ui.number(
                        "depth", value=p.hunter_depth, min=2, max=12, format="%.0f"
                    )
                ui.label(
                    "Модель для live/бэктеста выбирается выше. Параметры ниже — для вкладки «Данные и обучение»."
                ).classes("apex-sub")

            self.widgets["use_critic"] = ui.checkbox(
                "Critic (фильтр сигналов) — по умолчанию выкл. для live",
                value=p.use_critic,
            )

    def build(self) -> None:
        ui.add_head_html(f"<style>{CUSTOM_CSS}</style>")

        with ui.column().classes("w-full max-w-6xl mx-auto p-6 gap-5"):
            with ui.row().classes("w-full items-end justify-between"):
                with ui.column().classes("gap-0"):
                    ui.html('<div class="apex-header">APEX <span style="color:#3d8bfd">V5</span></div>')
                    ui.label("Live и бэктест могут работать одновременно").classes("apex-sub")
                with ui.row().classes("gap-2"):
                    ui.button("Сохранить параметры", on_click=self._save_params).props(
                        "outline color=grey-6"
                    )
                    ui.button("Сохранить API", on_click=self._save_connection).props(
                        "outline color=primary"
                    )
                    ui.button("Журнал процессов", on_click=self._open_process_log_dialog).props(
                        "outline"
                    )

            # --- Прогресс ---
            with ui.card().classes("apex-card w-full p-4"):
                self.widgets["progress_label"] = ui.label("Готов к работе").classes("apex-sub")
                self.widgets["progress_bar"] = ui.linear_progress(value=0, show_value=True).classes(
                    "w-full"
                )

            # --- Торговая пара ---
            sym_opts = all_symbol_options()
            if self.params.symbol not in sym_opts:
                sym_opts.append(self.params.symbol)
            with ui.card().classes("apex-card w-full p-5"):
                ui.label("Торговая пара").classes("text-lg mb-3")
                with ui.row().classes("w-full gap-4 flex-wrap items-end"):
                    self.widgets["symbol"] = ui.select(
                        sym_opts,
                        value=self.params.symbol,
                        label="Пара из списка",
                        on_change=lambda _: self._refresh_registry_dropdowns(),
                    ).classes("min-w-[180px]")
                    self.widgets["symbol_custom"] = ui.input(
                        "Своя пара",
                        placeholder="например DOGE-USDT или BTCUSDT",
                    ).classes("min-w-[200px] flex-grow")
                    ui.button("Применить пару", on_click=self._add_custom_symbol).props("outline")

            # --- Подключение ---
            with ui.card().classes("apex-card w-full p-5"):
                ui.label("Подключение BingX").classes("text-lg mb-3")
                with ui.row().classes("w-full gap-4 flex-wrap"):
                    self.widgets["api_key"] = ui.input(
                        "API Key", value=self.params.api_key, password_toggle_button=True
                    ).classes("flex-grow min-w-[200px]")
                    self.widgets["api_secret"] = ui.input(
                        "API Secret", value=self.params.api_secret, password=True
                    ).classes("flex-grow min-w-[200px]")
                    self.widgets["testnet"] = ui.switch(
                        "Testnet / VST", value=self.params.testnet
                    )
                    ui.button("Проверить BingX", on_click=self._test_connection).props(
                        "outline color=primary"
                    )

            # --- Общие параметры стратегии ---
            with ui.card().classes("apex-card w-full p-5"):
                ui.label("Параметры стратегии").classes("text-lg mb-2")
                self._build_strategy_fields(ui.column().classes("w-full gap-3"))

            # --- Вкладки ---
            with ui.card().classes("apex-card w-full p-0"):
                with ui.tabs().classes("apex-tabs w-full px-4 pt-2") as tabs:
                    tab_data = ui.tab("Данные и обучение")
                    tab_live = ui.tab("Live")
                    tab_bt = ui.tab("Бэктест")

                with ui.tab_panels(tabs, value=tab_data).classes("w-full p-5"):
                    with ui.tab_panel(tab_data):
                        ui.label(
                            "Скачивание и обучение. Файлы индексируются: ПАРА_№ (например ETH-USDT_001)."
                        ).classes("apex-sub mb-3")
                        with ui.row().classes("w-full gap-4 flex-wrap mb-3"):
                            self.widgets["data_start"] = ui.input(
                                "Дата начала", value=self.params.data_start
                            )
                            self.widgets["data_end"] = ui.input(
                                "Дата конца", value=self.params.data_end
                            )
                        with ui.row().classes("gap-2 mb-4"):
                            ui.button("Скачать OHLCV", on_click=self._download_data).props(
                                "outline"
                            )
                            ui.button("Обучить Hunter", on_click=self._train_model).props(
                                "unelevated color=primary"
                            )
                        ds_opts = dropdown_options_datasets(self.params.symbol) or {
                            "": "— нет данных —"
                        }
                        self.widgets["dataset_select"] = ui.select(
                            ds_opts,
                            value=self.params.dataset_id if self.params.dataset_id in ds_opts else (
                                next(iter(ds_opts)) if ds_opts else ""
                            ),
                            label="Исторические данные",
                        ).classes("w-full")
                        self.widgets["data_log"] = ui.textarea(
                            label="Журнал вкладки", value=""
                        ).classes("w-full").props("readonly outlined rows=4")
                        self.widgets["process_log_inline"] = ui.textarea(
                            label="Процессы (дублируется в консоль PyCharm)",
                            value="",
                        ).classes("w-full").props("readonly outlined rows=5")

                    with ui.tab_panel(tab_live):
                        with ui.row().classes("w-full items-center justify-between mb-4"):
                            with ui.row().classes("items-center gap-3"):
                                with ui.element("div").classes("status-pill status-idle") as pill:
                                    self.widgets["live_status"] = pill
                                    ui.element("span").classes("status-dot")
                                    self.widgets["live_status_text"] = ui.label(
                                        "Live · остановлен"
                                    ).classes("!p-0")
                            with ui.row().classes("gap-2"):
                                ui.button("Запустить live", on_click=self._start_live).props(
                                    "unelevated color=primary"
                                )
                                ui.button("Остановить", on_click=self._stop_live).props(
                                    "outline color=negative"
                                )

                        ui.label(
                            "В live: Spotter + Hunter + Dispatcher. "
                            "Strategist, Learner и Critic по умолчанию отключены."
                        ).classes("apex-sub mb-2")
                        self.widgets["live_log"] = ui.textarea(
                            label="Журнал", value=""
                        ).classes("w-full").props("readonly outlined rows=8")

                    # ===== BACKTEST =====
                    with ui.tab_panel(tab_bt):
                        with ui.row().classes("w-full items-center mb-3"):
                            with ui.element("div").classes("status-pill status-idle") as bt_pill:
                                self.widgets["bt_status"] = bt_pill
                                ui.element("span").classes("status-dot")
                                self.widgets["bt_status_text"] = ui.label(
                                    "Бэктест · готов"
                                ).classes("!p-0")
                        ds_opts_bt = dropdown_options_datasets(self.params.symbol) or {
                            "": "— сначала скачайте данные —"
                        }
                        self.widgets["dataset_select_bt"] = ui.select(
                            ds_opts_bt,
                            value=self.params.dataset_id if self.params.dataset_id in ds_opts_bt else (
                                next(iter(ds_opts_bt)) if ds_opts_bt else ""
                            ),
                            label="Датасет для бэктеста",
                        ).classes("w-full mb-3")
                        ui.button("Запустить бэктест", on_click=self._run_backtest).props(
                            "unelevated color=primary"
                        ).classes("mb-4")

                        with ui.row().classes("w-full gap-4 flex-wrap"):
                            with ui.column().classes("min-w-[200px]"):
                                ui.label("Метрики").classes("text-grey-5 mb-1")
                                self.widgets["bt_metrics"] = ui.markdown(
                                    "_Ожидание запуска…_"
                                )
                            with ui.column().classes("flex-grow min-w-[320px]"):
                                self.widgets["equity_chart"] = ui.echart({
                                    "backgroundColor": "transparent",
                                    "grid": {"left": 48, "right": 24, "top": 24, "bottom": 48},
                                    "tooltip": {"trigger": "axis"},
                                    "xAxis": {
                                        "type": "category",
                                        "data": [],
                                        "axisLabel": {"color": "#8b92a5", "rotate": 30},
                                    },
                                    "yAxis": {
                                        "type": "value",
                                        "axisLabel": {"color": "#8b92a5"},
                                        "splitLine": {"lineStyle": {"color": "#252a36"}},
                                    },
                                    "series": [{
                                        "type": "line",
                                        "data": [],
                                        "smooth": True,
                                        "showSymbol": False,
                                        "lineStyle": {"color": "#3d8bfd", "width": 2},
                                        "areaStyle": {
                                            "color": {
                                                "type": "linear",
                                                "x": 0, "y": 0, "x2": 0, "y2": 1,
                                                "colorStops": [
                                                    {"offset": 0, "color": "rgba(61,139,253,0.25)"},
                                                    {"offset": 1, "color": "rgba(61,139,253,0)"},
                                                ],
                                            }
                                        },
                                    }],
                                }).classes("w-full h-72")

                        self.widgets["bt_log"] = ui.textarea(
                            label="Журнал бэктеста", value=""
                        ).classes("w-full mt-2").props("readonly outlined rows=5")

        with ui.dialog() as self._log_dialog, ui.card().classes("w-[min(900px,95vw)] p-4"):
            ui.label("Журнал процессов").classes("text-lg mb-2")
            self.widgets["process_log_dialog_text"] = ui.textarea(
                value="",
            ).classes("w-full").props("readonly outlined rows=22")
            with ui.row().classes("justify-end gap-2 mt-2"):
                ui.button("Очистить", on_click=lambda: self.process_log.clear()).props("flat")
                ui.button("Закрыть", on_click=self._log_dialog.close)

        def _sync_inline_log(text: str) -> None:
            if "process_log_inline" in self.widgets:
                self.widgets["process_log_inline"].value = text[-6000:]
            if "process_log_dialog_text" in self.widgets:
                self.widgets["process_log_dialog_text"].value = text

        self.process_log.subscribe(_sync_inline_log)
        self._log_process("Интерфейс Apex V5 запущен")

        self._refresh_symbol_dropdown()
        self._refresh_registry_dropdowns()
        ui.timer(2.0, self._refresh_live_status)

    def on_shutdown(self) -> None:
        if self.live_runner.is_running:
            self.live_runner.stop()


def main() -> None:
    import os
    os.chdir(PROJECT_ROOT)
    apex = ApexUI()
    apex.build()
    app.on_shutdown(apex.on_shutdown)
    ui.run(
        title="Apex V5",
        dark=True,
        reload=False,
        port=8080,
        show=True,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
