#!/usr/bin/env python3
"""
Менеджер бирж - управление подключениями и данными
"""

import asyncio
import ccxt.pro as ccxt
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

# Добавляем путь к модулям
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from config import config
from utils.logger import get_logger

class ExchangeManager:
    """Менеджер для работы с биржами"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.exchanges = {}
        self.market_data = {}
        self.last_update = {}
        self.websocket_connections = {}
        
    async def initialize(self):
        """Инициализация подключений к биржам"""
        self.logger.info("🔌 Инициализация подключений к биржам...")
        
        for exchange_name, exchange_config in config.exchanges.items():
            if not exchange_config.enabled:
                continue
                
            try:
                # Создание экземпляра биржи
                exchange_class = getattr(ccxt, exchange_name)
                exchange = exchange_class({
                    'apiKey': exchange_config.api_key,
                    'secret': exchange_config.api_secret,
                    'password': exchange_config.passphrase,
                    'sandbox': exchange_config.sandbox,
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'spot',  # Спотовая торговля
                    }
                })
                
                # Тест подключения
                await exchange.load_markets()
                balance = await exchange.fetch_balance()
                
                self.exchanges[exchange_name] = exchange
                self.logger.info(f"✅ {exchange_name}: подключено")
                
            except Exception as e:
                self.logger.error(f"❌ {exchange_name}: ошибка подключения - {e}")
                continue
        
        if not self.exchanges:
            raise ConnectionError("Не удалось подключиться ни к одной бирже")
        
        # Запуск WebSocket подключений для реального времени
        await self._start_websocket_feeds()
    
    async def test_connections(self) -> List[str]:
        """Тестирование подключений к биржам"""
        connected = []
        
        for name, exchange in self.exchanges.items():
            try:
                await exchange.fetch_ticker('BTC/USDT')
                connected.append(name)
            except Exception as e:
                self.logger.warning(f"⚠️ {name}: проблема с подключением - {e}")
        
        return connected
    
    async def get_market_data(self) -> Dict[str, Dict]:
        """Получение рыночных данных со всех бирж"""
        market_data = {}
        
        for exchange_name, exchange in self.exchanges.items():
            try:
                # Получение тикеров для основных пар
                tickers = await exchange.fetch_tickers()
                
                # Фильтрация только нужных пар
                filtered_tickers = {}
                for symbol, ticker in tickers.items():
                    if self._is_valid_symbol(symbol):
                        filtered_tickers[symbol] = {
                            'bid': ticker['bid'],
                            'ask': ticker['ask'],
                            'last': ticker['last'],
                            'volume': ticker['baseVolume'],
                            'timestamp': ticker['timestamp']
                        }
                
                market_data[exchange_name] = filtered_tickers
                self.last_update[exchange_name] = datetime.now()
                
            except Exception as e:
                self.logger.error(f"❌ Ошибка получения данных с {exchange_name}: {e}")
        
        self.market_data = market_data
        return market_data
    
    async def get_orderbook(self, exchange_name: str, symbol: str, limit: int = 20) -> Optional[Dict]:
        """Получение стакана заявок"""
        if exchange_name not in self.exchanges:
            return None
        
        try:
            exchange = self.exchanges[exchange_name]
            orderbook = await exchange.fetch_order_book(symbol, limit)
            return orderbook
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения стакана {symbol} с {exchange_name}: {e}")
            return None
    
    async def check_liquidity(self, opportunity) -> bool:
        """Проверка ликвидности для арбитражной возможности"""
        try:
            min_volume = config.arbitrage.max_position_size
            
            for exchange_name in opportunity.exchanges:
                if exchange_name not in self.exchanges:
                    return False
                
                # Проверка объема в стакане
                orderbook = await self.get_orderbook(exchange_name, opportunity.symbol)
                if not orderbook:
                    return False
                
                # Проверка достаточности объема на покупку/продажу
                bid_volume = sum([order[1] for order in orderbook['bids'][:5]])
                ask_volume = sum([order[1] for order in orderbook['asks'][:5]])
                
                if bid_volume < min_volume or ask_volume < min_volume:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки ликвидности: {e}")
            return False
    
    async def get_balance(self, exchange_name: str) -> Optional[Dict]:
        """Получение баланса на бирже"""
        if exchange_name not in self.exchanges:
            return None
        
        try:
            exchange = self.exchanges[exchange_name]
            balance = await exchange.fetch_balance()
            return balance
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения баланса с {exchange_name}: {e}")
            return None
    
    async def get_trading_fees(self, exchange_name: str, symbol: str) -> Optional[Dict]:
        """Получение торговых комиссий"""
        if exchange_name not in self.exchanges:
            return None
        
        try:
            exchange = self.exchanges[exchange_name]
            fees = await exchange.fetch_trading_fees()
            
            if symbol in fees:
                return fees[symbol]
            else:
                # Возвращаем стандартные комиссии
                return {
                    'maker': exchange.fees['trading']['maker'],
                    'taker': exchange.fees['trading']['taker']
                }
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения комиссий с {exchange_name}: {e}")
            return None
    
    async def check_deposit_withdrawal(self, exchange_name: str, currency: str) -> Dict[str, bool]:
        """Проверка возможности депозита и вывода"""
        if exchange_name not in self.exchanges:
            return {'deposit': False, 'withdrawal': False}
        
        try:
            exchange = self.exchanges[exchange_name]
            currencies = await exchange.fetch_currencies()
            
            if currency in currencies:
                currency_info = currencies[currency]
                return {
                    'deposit': currency_info.get('deposit', True),
                    'withdrawal': currency_info.get('withdraw', True)
                }
            else:
                return {'deposit': False, 'withdrawal': False}
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки депозита/вывода {currency} на {exchange_name}: {e}")
            return {'deposit': False, 'withdrawal': False}
    
    async def _start_websocket_feeds(self):
        """Запуск WebSocket подключений для реального времени"""
        self.logger.info("🔌 Запуск WebSocket подключений...")
        
        for exchange_name, exchange in self.exchanges.items():
            try:
                if hasattr(exchange, 'watch_tickers'):
                    # Запуск в фоновом режиме
                    asyncio.create_task(self._websocket_feed(exchange_name, exchange))
                    self.logger.info(f"📡 WebSocket запущен для {exchange_name}")
            except Exception as e:
                self.logger.warning(f"⚠️ WebSocket недоступен для {exchange_name}: {e}")
    
    async def _websocket_feed(self, exchange_name: str, exchange):
        """WebSocket поток данных"""
        symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']
        
        while True:
            try:
                tickers = await exchange.watch_tickers(symbols)
                
                # Обновление данных
                if exchange_name not in self.market_data:
                    self.market_data[exchange_name] = {}
                
                for symbol, ticker in tickers.items():
                    self.market_data[exchange_name][symbol] = {
                        'bid': ticker['bid'],
                        'ask': ticker['ask'],
                        'last': ticker['last'],
                        'volume': ticker['baseVolume'],
                        'timestamp': ticker['timestamp']
                    }
                
            except Exception as e:
                self.logger.error(f"❌ WebSocket ошибка {exchange_name}: {e}")
                await asyncio.sleep(5)
    
    def _is_valid_symbol(self, symbol: str) -> bool:
        """Проверка валидности торговой пары"""
        # Основные валютные пары
        major_pairs = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
            'XRP/USDT', 'DOT/USDT', 'AVAX/USDT', 'MATIC/USDT', 'LINK/USDT',
            'UNI/USDT', 'LTC/USDT', 'BCH/USDT', 'ATOM/USDT', 'FIL/USDT'
        ]
        
        # Проверка на основные пары
        if symbol in major_pairs:
            return True
        
        # Проверка на USDT пары топ-100 монет
        if symbol.endswith('/USDT'):
            base = symbol.split('/')[0]
            if len(base) <= 10 and base.isalpha():  # Простая проверка
                return True
        
        return False
    
    async def disconnect(self):
        """Отключение от всех бирж"""
        self.logger.info("🔌 Отключение от бирж...")
        
        for exchange_name, exchange in self.exchanges.items():
            try:
                await exchange.close()
                self.logger.info(f"✅ {exchange_name}: отключено")
            except Exception as e:
                self.logger.error(f"❌ Ошибка отключения {exchange_name}: {e}")
        
        self.exchanges.clear()
        self.market_data.clear()
    
    def get_connected_exchanges(self) -> List[str]:
        """Получение списка подключенных бирж"""
        return list(self.exchanges.keys())
    
    def get_exchange(self, exchange_name: str):
        """Получение экземпляра биржи"""
        return self.exchanges.get(exchange_name)
    
    def is_data_fresh(self, exchange_name: str, max_age_seconds: int = 30) -> bool:
        """Проверка свежести данных"""
        if exchange_name not in self.last_update:
            return False
        
        age = datetime.now() - self.last_update[exchange_name]
        return age.total_seconds() <= max_age_seconds