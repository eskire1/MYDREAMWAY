"""
scripts/run_backtest.py
Скрипт для запуска бэктеста Apex V5 Global на исторических данных.
"""

import argparse
import yaml
import pandas as pd
from pathlib import Path
from dataclasses import asdict

from src.backtest.engine import BacktestEngine
from src.data.indicators import CompositeOscillator, LiquidityZones
from src.agents.hunter import HunterModel, HunterInference
from src.agents.strategist import StrategistModel, StrategistInference
from src.utils.logger import setup_logger, get_logger


def main():
    parser = argparse.ArgumentParser(description="Run backtest for Apex V5 Global")
    parser.add_argument('--config', default='config/settings.yaml', help='Path to config file')
    parser.add_argument('--data', default='data/historical.csv', help='Path to historical OHLCV CSV')
    args = parser.parse_args()

    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    setup_logger(log_level='INFO')
    logger = get_logger(__name__)

    # Загрузка данных
    logger.info("Loading historical data...")
    df = pd.read_csv(args.data, parse_dates=['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    logger.info(f"Loaded {len(df)} bars")

    # Загрузка моделей
    logger.info("Loading models...")
    hunter_model = HunterModel()
    hunter_model.load(config['paths']['models']['hunter_model'])
    hunter_inference = HunterInference(hunter_model)

    strategist_model = StrategistModel()
    strategist_model.load(config['paths']['models']['strategist_model'])
    strategist_inference = StrategistInference(strategist_model)

    # Запуск бэктеста
    logger.info("Starting backtest...")
    engine = BacktestEngine(config, df, hunter_inference, strategist_inference)
    metrics, _equity = engine.run(show_chart=True)
    metrics_dict = asdict(metrics)

    # Вывод результатов
    logger.info("=== Backtest Results ===")
    for key, value in metrics_dict.items():
        if isinstance(value, float):
            logger.info(f"{key}: {value:.4f}")
        else:
            logger.info(f"{key}: {value}")


if __name__ == "__main__":
    main()