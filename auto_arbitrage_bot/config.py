#!/usr/bin/env python3
"""
Конфигурация автоматического арбитражного бота
Содержит все настройки системы
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

# Добавляем путь к модулям
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Загружаем переменные окружения из .env файла
try:
    from dotenv import load_dotenv
    env_path = current_dir / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Загружен .env файл: {env_path}")
    else:
        print(f"⚠️ .env файл не найден: {env_path}")
except ImportError:
    print("⚠️ python-dotenv не установлен, переменные окружения не загружены")

from models import TradingMode, ArbitrageType

@dataclass
class ExchangeConfig:
    """Конфигурация биржи"""
    name: str
    api_key: str
    api_secret: str
    passphrase: Optional[str] = None
    sandbox: bool = True
    enabled: bool = True
    max_position_size: float = 1000.0  # USD
    trading_fee: float = 0.1            # %

@dataclass
class ArbitrageConfig:
    """Конфигурация арбитража"""
    min_profit_threshold: float = 0.5   # Минимальная прибыль %
    max_position_size: float = 1000.0   # Максимальный размер позиции USD
    max_slippage: float = 0.1           # Максимальное проскальзывание %
    timeout_seconds: int = 30           # Таймаут исполнения сделки
    enabled_types: List[ArbitrageType] = None

@dataclass
class RiskConfig:
    """Конфигурация управления рисками"""
    max_daily_loss: float = 100.0       # Максимальная дневная потеря USD
    max_position_count: int = 5          # Максимальное количество позиций
    stop_loss_percent: float = 2.0       # Stop-loss %
    take_profit_percent: float = 5.0     # Take-profit %
    max_drawdown_percent: float = 10.0   # Максимальная просадка %

class Config:
    """Главная конфигурация системы"""
    
    def __init__(self):
        # Основные настройки
        self.trading_mode = TradingMode(os.getenv('TRADING_MODE', 'test'))
        self.debug = os.getenv('DEBUG', 'true').lower() == 'true'
        
        # Настройки арбитража
        self.arbitrage = ArbitrageConfig(
            min_profit_threshold=float(os.getenv('MIN_PROFIT_THRESHOLD', '0.5')),
            max_position_size=float(os.getenv('MAX_POSITION_SIZE', '1000.0')),
            max_slippage=float(os.getenv('MAX_SLIPPAGE', '0.1')),
            timeout_seconds=int(os.getenv('TIMEOUT_SECONDS', '30')),
            enabled_types=[ArbitrageType.CROSS_EXCHANGE, ArbitrageType.TRIANGULAR]
        )
        
        # Настройки управления рисками
        self.risk = RiskConfig(
            max_daily_loss=float(os.getenv('MAX_DAILY_LOSS', '100.0')),
            max_position_count=int(os.getenv('MAX_POSITION_COUNT', '5')),
            stop_loss_percent=float(os.getenv('STOP_LOSS_PERCENT', '2.0')),
            take_profit_percent=float(os.getenv('TAKE_PROFIT_PERCENT', '5.0')),
            max_drawdown_percent=float(os.getenv('MAX_DRAWDOWN_PERCENT', '10.0'))
        )
        
        # Конфигурация бирж
        self.exchanges = self._load_exchange_configs()
        
        # Настройки уведомлений
        self.telegram = {
            'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
            'chat_id': os.getenv('TELEGRAM_CHAT_ID', ''),
            'enabled': os.getenv('TELEGRAM_ENABLED', 'false').lower() == 'true'
        }
        
        # Настройки базы данных
        self.database = {
            'url': os.getenv('DATABASE_URL', 'sqlite:///data/arbitrage.db'),
            'echo': self.debug
        }
        
        # Настройки веб-интерфейса
        self.web = {
            'host': os.getenv('WEB_HOST', '0.0.0.0'),
            'port': int(os.getenv('WEB_PORT', '8080')),
            'enabled': os.getenv('WEB_ENABLED', 'true').lower() == 'true'
        }
        
        # Настройки логирования
        self.logging = {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'file': os.getenv('LOG_FILE', 'logs/arbitrage.log'),
            'max_size': int(os.getenv('LOG_MAX_SIZE', '10485760')),  # 10MB
            'backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5'))
        }

    def _load_exchange_configs(self) -> Dict[str, ExchangeConfig]:
        """Загрузка конфигураций бирж"""
        exchanges = {}
        
        # Binance
        if os.getenv('BINANCE_API_KEY'):
            exchanges['binance'] = ExchangeConfig(
                name='binance',
                api_key=os.getenv('BINANCE_API_KEY', ''),
                api_secret=os.getenv('BINANCE_API_SECRET', ''),
                sandbox=os.getenv('BINANCE_SANDBOX', 'true').lower() == 'true',
                enabled=os.getenv('BINANCE_ENABLED', 'false').lower() == 'true',
                trading_fee=0.1
            )
        
        # Bybit
        if os.getenv('BYBIT_API_KEY'):
            exchanges['bybit'] = ExchangeConfig(
                name='bybit',
                api_key=os.getenv('BYBIT_API_KEY', ''),
                api_secret=os.getenv('BYBIT_API_SECRET', ''),
                sandbox=os.getenv('BYBIT_SANDBOX', 'true').lower() == 'true',
                enabled=os.getenv('BYBIT_ENABLED', 'false').lower() == 'true',
                trading_fee=0.1
            )
        
        # KuCoin
        if os.getenv('KUCOIN_API_KEY'):
            exchanges['kucoin'] = ExchangeConfig(
                name='kucoin',
                api_key=os.getenv('KUCOIN_API_KEY', ''),
                api_secret=os.getenv('KUCOIN_API_SECRET', ''),
                passphrase=os.getenv('KUCOIN_PASSPHRASE', ''),
                sandbox=os.getenv('KUCOIN_SANDBOX', 'true').lower() == 'true',
                enabled=os.getenv('KUCOIN_ENABLED', 'false').lower() == 'true',
                trading_fee=0.1
            )
        
        # MEXC
        if os.getenv('MEXC_API_KEY'):
            exchanges['mexc'] = ExchangeConfig(
                name='mexc',
                api_key=os.getenv('MEXC_API_KEY', ''),
                api_secret=os.getenv('MEXC_API_SECRET', ''),
                sandbox=os.getenv('MEXC_SANDBOX', 'true').lower() == 'true',
                enabled=os.getenv('MEXC_ENABLED', 'false').lower() == 'true',
                trading_fee=0.2
            )
        
        # OKX
        if os.getenv('OKX_API_KEY'):
            exchanges['okx'] = ExchangeConfig(
                name='okx',
                api_key=os.getenv('OKX_API_KEY', ''),
                api_secret=os.getenv('OKX_API_SECRET', ''),
                passphrase=os.getenv('OKX_PASSPHRASE', ''),
                sandbox=os.getenv('OKX_SANDBOX', 'true').lower() == 'true',
                enabled=os.getenv('OKX_ENABLED', 'false').lower() == 'true',
                trading_fee=0.1
            )
        
        # Coinbase
        if os.getenv('COINBASE_API_KEY'):
            exchanges['coinbase'] = ExchangeConfig(
                name='coinbase',
                api_key=os.getenv('COINBASE_API_KEY', ''),
                api_secret=os.getenv('COINBASE_API_SECRET', ''),
                passphrase=os.getenv('COINBASE_PASSPHRASE', ''),
                sandbox=os.getenv('COINBASE_SANDBOX', 'true').lower() == 'true',
                enabled=os.getenv('COINBASE_ENABLED', 'false').lower() == 'true',
                trading_fee=0.5
            )
        
        return exchanges
    
    def get_enabled_exchanges(self) -> List[str]:
        """Получить список включенных бирж"""
        return [name for name, config in self.exchanges.items() if config.enabled]
    
    def is_exchange_enabled(self, exchange_name: str) -> bool:
        """Проверить включена ли биржа"""
        return exchange_name in self.exchanges and self.exchanges[exchange_name].enabled
    
    def validate(self) -> List[str]:
        """Валидация конфигурации"""
        errors = []
        
        # Проверяем что есть хотя бы одна включенная биржа
        if not self.get_enabled_exchanges():
            errors.append("Нет включенных бирж. Добавьте API ключи и включите биржи.")
        
        # Проверяем настройки Telegram если включен
        if self.telegram['enabled']:
            if not self.telegram['bot_token']:
                errors.append("Telegram включен, но не указан bot_token")
            if not self.telegram['chat_id']:
                errors.append("Telegram включен, но не указан chat_id")
        
        # Проверяем настройки арбитража
        if self.arbitrage.min_profit_threshold <= 0:
            errors.append("Минимальная прибыль должна быть больше 0")
        
        if self.arbitrage.max_position_size <= 0:
            errors.append("Максимальный размер позиции должен быть больше 0")
        
        return errors

# Глобальный экземпляр конфигурации
config = Config()