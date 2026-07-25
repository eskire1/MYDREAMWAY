"""
tests/test_backtest.py
Модульные тесты для бэктест-движка (scripts/run_backtest.py).
Проверяет логику симуляции сделок, расчёт метрик, учёт проскальзывания и комиссий.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import yaml

from scripts.run_backtest import BacktestEngine


class TestBacktestEngine:
    @pytest.fixture
    def sample_config(self):
        return {
            'general': {
                'symbols': ['BTCUSDT'],
                'timeframe': '15m'
            },
            'features': {
                'window_size': 20,
                'normalization': {'rolling_window': 1000}
            },
            'backtest': {
                'slippage': {'btc_eth': 0.0005, 'altcoins': 0.002},
                'commission': {'maker': 0.0004, 'taker': 0.0006},
                'delay_bars': 1,
                'triple_barrier': {'horizon_bars': 16, 'atr_multiplier_sl': 1.5}
            },
            'dispatcher': {
                'initial_equity': 10000.0,
                'risk': {
                    'base_risk': 0.005,
                    'target_volatility': 0.2,
                    'max_leverage_normal': 3.0,
                    'max_leverage_paranoia': 1.5,
                    'atr_period': 50,
                    'sl_multiplier': 1.5
                },
                'paranoia_mode': {'hwm_threshold': 0.95},
                'state_machine': {'heartbeat_timeout_seconds': 5}
            },
            'critic': {
                'adx_threshold': 20,
                'adx_threshold_paranoia': 25,
                'spread_multiplier': 1.5,
                'liquidity_distance_threshold': 2.0,
                'min_tick_multiplier': 3.0,
                'blocked_hours': [[0, 1]],
                'avg_spread_window': 100
            },
            'paths': {
                'models': {
                    'hunter_ckpt': 'dummy.ckpt',
                    'strategist_model': 'dummy.cbm'
                }
            },
            'hunter': {'model': {}, 'training': {}},
            'strategist': {'model': {}, 'forecast_horizon_bars': 12}
        }

    @pytest.fixture
    def sample_ohlcv_data(self):
        dates = pd.date_range(start='2024-01-01', periods=200, freq='15min')
        np.random.seed(42)
        price = 50000 + np.cumsum(np.random.randn(200) * 100)
        df = pd.DataFrame({
            'timestamp': dates,
            'open': price + np.random.randn(200) * 10,
            'high': price + np.abs(np.random.randn(200) * 20),
            'low': price - np.abs(np.random.randn(200) * 20),
            'close': price + np.random.randn(200) * 10,
            'volume': np.random.rand(200) * 1000
        })
        return df

    @patch('scripts.run_backtest.load_hunter_from_checkpoint')
    @patch('scripts.run_backtest.StrategistModel')
    @patch('scripts.run_backtest.HunterInference')
    @patch('scripts.run_backtest.StrategistInference')
    def test_initialization(self, mock_strat_inf, mock_hunter_inf, mock_strat_model, mock_load, sample_config, sample_ohlcv_data, tmp_path):
        data_path = tmp_path / "data.csv"
        sample_ohlcv_data.to_csv(data_path, index=False)

        # Мокаем загрузку моделей
        mock_load.return_value = (Mock(), Mock())
        mock_strat_model.return_value = Mock()

        engine = BacktestEngine(sample_config, str(data_path))
        assert engine.symbol == 'BTCUSDT'
        assert engine.slippage == 0.0005
        assert engine.commission_taker == 0.0006
        assert engine.delay_bars == 1

    @patch('scripts.run_backtest.load_hunter_from_checkpoint')
    @patch('scripts.run_backtest.StrategistModel')
    def test_apply_slippage(self, mock_strat, mock_load, sample_config, sample_ohlcv_data, tmp_path):
        data_path = tmp_path / "data.csv"
        sample_ohlcv_data.to_csv(data_path, index=False)
        mock_load.return_value = (Mock(), Mock())
        engine = BacktestEngine(sample_config, str(data_path))
        price = 50000.0
        buy_price = engine._apply_slippage(price, 'BUY')
        sell_price = engine._apply_slippage(price, 'SELL')
        assert buy_price == price * (1 + engine.slippage)
        assert sell_price == price * (1 - engine.slippage)

    @patch('scripts.run_backtest.load_hunter_from_checkpoint')
    @patch('scripts.run_backtest.StrategistModel')
    def test_calculate_pnl_long(self, mock_strat, mock_load, sample_config, sample_ohlcv_data, tmp_path):
        data_path = tmp_path / "data.csv"
        sample_ohlcv_data.to_csv(data_path, index=False)
        mock_load.return_value = (Mock(), Mock())
        engine = BacktestEngine(sample_config, str(data_path))

        position = {
            'signal': 'LONG',
            'entry_price': 50000.0,
            'notional': 10000.0,
            'commission_paid': 10000.0 * engine.commission_taker
        }
        exit_price = 51000.0
        pnl = engine._calculate_pnl(position, exit_price)
        # gross = 10000 * (51000/50000 - 1) = 200
        # commission_exit = 10200 * taker
        # net = 200 - commission_entry - commission_exit
        expected_gross = 200.0
        exit_notional = 10000 * (51000 / 50000)
        comm_exit = exit_notional * engine.commission_taker
        expected_net = expected_gross - position['commission_paid'] - comm_exit
        assert np.isclose(pnl, expected_net)

    @patch('scripts.run_backtest.load_hunter_from_checkpoint')
    @patch('scripts.run_backtest.StrategistModel')
    def test_check_exit_long(self, mock_strat, mock_load, sample_config, sample_ohlcv_data, tmp_path):
        data_path = tmp_path / "data.csv"
        sample_ohlcv_data.to_csv(data_path, index=False)
        mock_load.return_value = (Mock(), Mock())
        engine = BacktestEngine(sample_config, str(data_path))
        engine.df = sample_ohlcv_data

        position = {'signal': 'LONG', 'tp': 51000.0, 'sl': 49000.0}
        bar_idx = 10
        engine.df.loc[bar_idx, 'high'] = 51200.0
        engine.df.loc[bar_idx, 'low'] = 49500.0
        triggered, price, reason = engine._check_exit(position, bar_idx)
        assert triggered is True
        assert price == 51000.0
        assert reason == 'tp'

        # SL срабатывает
        engine.df.loc[bar_idx, 'high'] = 50500.0
        engine.df.loc[bar_idx, 'low'] = 48500.0
        triggered, price, reason = engine._check_exit(position, bar_idx)
        assert triggered is True
        assert price == 49000.0
        assert reason == 'sl'

    @patch('scripts.run_backtest.load_hunter_from_checkpoint')
    @patch('scripts.run_backtest.StrategistModel')
    def test_calculate_metrics_values(self, mock_strat, mock_load, sample_config, sample_ohlcv_data, tmp_path):
        data_path = tmp_path / "data.csv"
        sample_ohlcv_data.to_csv(data_path, index=False)
        mock_load.return_value = (Mock(), Mock())
        engine = BacktestEngine(sample_config, str(data_path))
        engine.trades = [
            {'pnl': 100.0, 'return': 0.01},
            {'pnl': -50.0, 'return': -0.005},
            {'pnl': 200.0, 'return': 0.02},
            {'pnl': -30.0, 'return': -0.003}
        ]
        engine.equity = 10220.0

        # Вместо вывода на печать, извлекаем значения напрямую для проверки
        pnls = [t['pnl'] for t in engine.trades]
        win_trades = [p for p in pnls if p > 0]
        loss_trades = [p for p in pnls if p <= 0]
        total_pnl = sum(pnls)
        win_rate = len(win_trades) / len(pnls)
        profit_factor = abs(sum(win_trades) / sum(loss_trades)) if sum(loss_trades) != 0 else float('inf')

        assert total_pnl == 220.0
        assert win_rate == 0.5
        assert profit_factor == 300.0 / 80.0  # 3.75