"""
src/utils/logger.py
Настройка логирования для Apex V5 Global с использованием loguru.
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional


def setup_logger(
        log_level: str = "INFO",
        log_file: Optional[str] = "logs/apex_v5.log",
        rotation: str = "10 MB",
        retention: str = "1 week",
        compression: str = "zip",
        backtrace: bool = True,
        diagnose: bool = False,
) -> None:
    """
    Конфигурирует глобальный логгер loguru.

    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR).
        log_file: Путь к файлу лога. Если None, запись в файл отключена.
        rotation: Максимальный размер файла перед ротацией.
        retention: Срок хранения старых логов.
        compression: Сжатие ротированных файлов.
        backtrace: Добавлять ли трассировку для ошибок.
        diagnose: Включать ли детальную диагностику переменных.
    """
    # Удаляем стандартный обработчик (если был)
    logger.remove()

    # Добавляем вывод в консоль с цветным форматированием
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
        backtrace=backtrace,
        diagnose=diagnose,
    )

    # Добавляем запись в файл, если указан путь
    if log_file:
        # Убедимся, что директория существует
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            str(log_path),
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level,
            rotation=rotation,
            retention=retention,
            compression=compression,
            backtrace=backtrace,
            diagnose=diagnose,
            enqueue=True,  # Асинхронная запись для производительности
        )


def get_logger(name: Optional[str] = None):
    """
    Возвращает настроенный логгер. Для совместимости с модульным импортом.
    """
    return logger.bind(name=name) if name else logger