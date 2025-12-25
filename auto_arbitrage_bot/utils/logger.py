#!/usr/bin/env python3
"""
Система логирования
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
import colorlog

# Добавляем путь к модулям
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from config import config

def get_logger(name: str) -> logging.Logger:
    """Получение настроенного логгера"""
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    # Уровень логирования
    level = getattr(logging, config.logging['level'].upper(), logging.INFO)
    logger.setLevel(level)
    
    # Создание директории для логов
    log_dir = os.path.dirname(config.logging['file'])
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Форматтер для файлов
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Форматтер для консоли с цветами
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    # Файловый хендлер с ротацией
    file_handler = logging.handlers.RotatingFileHandler(
        config.logging['file'],
        maxBytes=config.logging['max_size'],
        backupCount=config.logging['backup_count'],
        encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)
    
    # Консольный хендлер
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)
    
    # Добавление хендлеров
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Предотвращение дублирования
    logger.propagate = False
    
    return logger

def log_trade_result(trade_result):
    """Специальное логирование результатов сделок"""
    logger = get_logger('trade_results')
    
    if trade_result.success:
        logger.info(
            f"✅ УСПЕШНАЯ СДЕЛКА | "
            f"Тип: {trade_result.arbitrage_type} | "
            f"Символ: {trade_result.symbol} | "
            f"Прибыль: ${trade_result.profit_usd:.2f} ({trade_result.profit_percent:.2f}%) | "
            f"Время: {trade_result.execution_time:.2f}с | "
            f"Ордеров: {len(trade_result.orders)}"
        )
    else:
        logger.error(
            f"❌ НЕУДАЧНАЯ СДЕЛКА | "
            f"Тип: {trade_result.arbitrage_type} | "
            f"Символ: {trade_result.symbol} | "
            f"Ошибка: {trade_result.error} | "
            f"Время: {trade_result.execution_time:.2f}с"
        )

def log_opportunity(opportunity):
    """Логирование найденной возможности"""
    logger = get_logger('opportunities')
    
    logger.info(
        f"💡 ВОЗМОЖНОСТЬ | "
        f"Тип: {opportunity.type.value} | "
        f"Символ: {opportunity.symbol} | "
        f"Прибыль: {opportunity.profit_percent:.2f}% (${opportunity.profit_usd:.2f}) | "
        f"Биржи: {', '.join(opportunity.exchanges)} | "
        f"Уверенность: {opportunity.confidence:.2f} | "
        f"Риск: {opportunity.risk_score:.2f}"
    )