#!/usr/bin/env python3
"""
Расширенный криптовалютный арбитражный монитор
Поддержка множества бирж и всех торговых пар
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
import logging
from config import EXCHANGES, TRIANGULAR_SETS, PAIR_FILTERS, BASE_CURRENCIES, TRIANGULAR_BASE_CURRENCIES, generate_all_triangular_sets

logger = logging.getLogger(__name__)

@dataclass
class TradingPair:
    """Информация о торговой паре"""
    symbol: str
    base_asset: str
    quote_asset: str
    price: float
    volume_24h: float
    exchange: str

@dataclass
class ArbitrageOpportunity:
    """Структура для хранения арбитражной возможности"""
    type: str  # 'cross_exchange' или 'triangular'
    profit_percent: float
    details: Dict
    timestamp: datetime
    confidence: float  # Уровень уверенности (0-1)

class EnhancedArbitrageMonitor:
    def __init__(self):
        self.session = None
        self.all_pairs = {}  # {exchange: {symbol: TradingPair}}
        self.normalized_pairs = {}  # {normalized_symbol: {exchange: TradingPair}}
        self.min_profit_threshold = 0.75  # Остается 0.75%
        self.last_update = {}  # Время последнего обновления для каждой биржи
        self.available_currencies = set()  # Все доступные валюты
        self.triangular_sets = []  # Будет генерироваться автоматически
        
        # Активные биржи
        self.active_exchanges = {
            name: config for name, config in EXCHANGES.items() 
            if config['enabled']
        }
        
        logger.info(f"🚀 Инициализирован АГРЕССИВНЫЙ монитор с {len(self.active_exchanges)} биржами")
        logger.info(f"📊 Мониторинг ВСЕХ доступных торговых пар (без белого списка)")
        logger.info(f"🔺 Треугольный арбитраж: ВСЕ возможные комбинации валют")

    async def start_session(self):
        """Инициализация HTTP сессии с таймаутами"""
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
    async def close_session(self):
        """Закрытие HTTP сессии"""
        if self.session:
            await self.session.close()

    def normalize_symbol(self, symbol: str) -> str:
        """Нормализация символа торговой пары"""
        # Убираем разделители и приводим к верхнему регистру
        return symbol.replace('-', '').replace('_', '').replace('/', '').upper()

    def parse_symbol(self, symbol: str) -> Tuple[str, str]:
        """Разбор символа на базовую и котируемую валюту"""
        normalized = self.normalize_symbol(symbol)
        
        # Проверяем стейблкоины в конце
        for quote in ['USDT', 'USDC', 'BUSD', 'DAI', 'TUSD']:
            if normalized.endswith(quote):
                base = normalized[:-len(quote)]
                return base, quote
        
        # Проверяем основные криптовалюты
        for quote in ['BTC', 'ETH', 'BNB']:
            if normalized.endswith(quote) and len(normalized) > len(quote):
                base = normalized[:-len(quote)]
                return base, quote
        
        # Если не удалось разобрать, возвращаем как есть
        return normalized, 'UNKNOWN'

    async def fetch_binance_data(self) -> Dict[str, TradingPair]:
        """Получение данных с Binance"""
        try:
            # Получаем цены
            price_url = 'https://api.binance.com/api/v3/ticker/price'
            stats_url = 'https://api.binance.com/api/v3/ticker/24hr'
            
            async with self.session.get(price_url) as price_response:
                price_data = await price_response.json()
            
            async with self.session.get(stats_url) as stats_response:
                stats_data = await stats_response.json()
            
            # Создаем словарь статистики
            stats_dict = {item['symbol']: item for item in stats_data}
            
            pairs = {}
            for price_item in price_data:
                symbol = price_item['symbol']
                
                if symbol in stats_dict:
                    stats = stats_dict[symbol]
                    base, quote = self.parse_symbol(symbol)
                    
                    # Фильтруем по объему и цене
                    volume_24h = float(stats.get('quoteVolume', 0))
                    price = float(price_item['price'])
                    
                    if (volume_24h >= PAIR_FILTERS['min_volume_24h'] and
                        PAIR_FILTERS['min_price'] <= price <= PAIR_FILTERS['max_price'] and
                        not any(pattern in symbol for pattern in PAIR_FILTERS['exclude_patterns'])):
                        
                        pairs[symbol] = TradingPair(
                            symbol=symbol,
                            base_asset=base,
                            quote_asset=quote,
                            price=price,
                            volume_24h=volume_24h,
                            exchange='binance'
                        )
            
            logger.info(f"Binance: получено {len(pairs)} торговых пар")
            return pairs
            
        except Exception as e:
            logger.error(f"Ошибка получения данных с Binance: {e}")
            return {}

    async def fetch_bybit_data(self) -> Dict[str, TradingPair]:
        """Получение данных с Bybit"""
        try:
            url = 'https://api.bybit.com/v5/market/tickers?category=spot'
            
            async with self.session.get(url) as response:
                data = await response.json()
                
            pairs = {}
            if data.get('retCode') == 0:
                for item in data['result']['list']:
                    symbol = item['symbol']
                    base, quote = self.parse_symbol(symbol)
                    
                    volume_24h = float(item.get('turnover24h', 0))
                    price = float(item.get('lastPrice', 0))
                    
                    if (volume_24h >= PAIR_FILTERS['min_volume_24h'] and
                        PAIR_FILTERS['min_price'] <= price <= PAIR_FILTERS['max_price'] and
                        not any(pattern in symbol for pattern in PAIR_FILTERS['exclude_patterns'])):
                        
                        pairs[symbol] = TradingPair(
                            symbol=symbol,
                            base_asset=base,
                            quote_asset=quote,
                            price=price,
                            volume_24h=volume_24h,
                            exchange='bybit'
                        )
            
            logger.info(f"Bybit: получено {len(pairs)} торговых пар")
            return pairs
            
        except Exception as e:
            logger.error(f"Ошибка получения данных с Bybit: {e}")
            return {}

    async def fetch_okx_data(self) -> Dict[str, TradingPair]:
        """Получение данных с OKX"""
        try:
            url = 'https://www.okx.com/api/v5/market/tickers?instType=SPOT'
            
            async with self.session.get(url) as response:
                data = await response.json()
                
            pairs = {}
            if data.get('code') == '0':
                for item in data['data']:
                    symbol = item['instId'].replace('-', '')
                    base, quote = self.parse_symbol(symbol)
                    
                    volume_24h = float(item.get('volCcy24h', 0))
                    price = float(item.get('last', 0))
                    
                    if (volume_24h >= PAIR_FILTERS['min_volume_24h'] and
                        PAIR_FILTERS['min_price'] <= price <= PAIR_FILTERS['max_price'] and
                        not any(pattern in symbol for pattern in PAIR_FILTERS['exclude_patterns'])):
                        
                        pairs[symbol] = TradingPair(
                            symbol=symbol,
                            base_asset=base,
                            quote_asset=quote,
                            price=price,
                            volume_24h=volume_24h,
                            exchange='okx'
                        )
            
            logger.info(f"OKX: получено {len(pairs)} торговых пар")
            return pairs
            
        except Exception as e:
            logger.error(f"Ошибка получения данных с OKX: {e}")
            return {}

    async def fetch_kucoin_data(self) -> Dict[str, TradingPair]:
        """Получение данных с KuCoin"""
        try:
            url = 'https://api.kucoin.com/api/v1/market/allTickers'
            
            async with self.session.get(url) as response:
                data = await response.json()
                
            pairs = {}
            if data.get('code') == '200000':
                for item in data['data']['ticker']:
                    symbol = item['symbol'].replace('-', '')
                    base, quote = self.parse_symbol(symbol)
                    
                    volume_24h = float(item.get('volValue', 0))
                    price = float(item.get('last', 0))
                    
                    if (volume_24h >= PAIR_FILTERS['min_volume_24h'] and
                        PAIR_FILTERS['min_price'] <= price <= PAIR_FILTERS['max_price'] and
                        not any(pattern in symbol for pattern in PAIR_FILTERS['exclude_patterns'])):
                        
                        pairs[symbol] = TradingPair(
                            symbol=symbol,
                            base_asset=base,
                            quote_asset=quote,
                            price=price,
                            volume_24h=volume_24h,
                            exchange='kucoin'
                        )
            
            logger.info(f"KuCoin: получено {len(pairs)} торговых пар")
            return pairs
            
        except Exception as e:
            logger.error(f"Ошибка получения данных с KuCoin: {e}")
            return {}
    async def fetch_gate_data(self) -> Dict[str, TradingPair]:
        """Получение данных с Gate.io"""
        try:
            url = 'https://api.gateio.ws/api/v4/spot/tickers'
            
            async with self.session.get(url) as response:
                data = await response.json()
                
            pairs = {}
            for item in data:
                symbol = item['currency_pair'].replace('_', '')
                base, quote = self.parse_symbol(symbol)
                
                volume_24h = float(item.get('quote_volume', 0))
                price = float(item.get('last', 0))
                
                if (volume_24h >= PAIR_FILTERS['min_volume_24h'] and
                    PAIR_FILTERS['min_price'] <= price <= PAIR_FILTERS['max_price'] and
                    not any(pattern in symbol for pattern in PAIR_FILTERS['exclude_patterns'])):
                    
                    pairs[symbol] = TradingPair(
                        symbol=symbol,
                        base_asset=base,
                        quote_asset=quote,
                        price=price,
                        volume_24h=volume_24h,
                        exchange='gate'
                    )
            
            logger.info(f"Gate.io: получено {len(pairs)} торговых пар")
            return pairs
            
        except Exception as e:
            logger.error(f"Ошибка получения данных с Gate.io: {e}")
            return {}

    async def fetch_huobi_data(self) -> Dict[str, TradingPair]:
        """Получение данных с Huobi"""
        try:
            url = 'https://api.huobi.pro/market/tickers'
            
            async with self.session.get(url) as response:
                data = await response.json()
                
            pairs = {}
            if data.get('status') == 'ok':
                for item in data['data']:
                    symbol = item['symbol'].upper()
                    base, quote = self.parse_symbol(symbol)
                    
                    volume_24h = float(item.get('vol', 0)) * float(item.get('close', 0))
                    price = float(item.get('close', 0))
                    
                    if (volume_24h >= PAIR_FILTERS['min_volume_24h'] and
                        PAIR_FILTERS['min_price'] <= price <= PAIR_FILTERS['max_price'] and
                        not any(pattern in symbol for pattern in PAIR_FILTERS['exclude_patterns'])):
                        
                        pairs[symbol] = TradingPair(
                            symbol=symbol,
                            base_asset=base,
                            quote_asset=quote,
                            price=price,
                            volume_24h=volume_24h,
                            exchange='huobi'
                        )
            
            logger.info(f"Huobi: получено {len(pairs)} торговых пар")
            return pairs
            
        except Exception as e:
            logger.error(f"Ошибка получения данных с Huobi: {e}")
            return {}

    async def fetch_mexc_data(self) -> Dict[str, TradingPair]:
        """Получение данных с MEXC"""
        try:
            url = 'https://api.mexc.com/api/v3/ticker/24hr'
            
            async with self.session.get(url) as response:
                data = await response.json()
                
            pairs = {}
            for item in data:
                symbol = item['symbol']
                base, quote = self.parse_symbol(symbol)
                
                volume_24h = float(item.get('quoteVolume', 0))
                price = float(item.get('lastPrice', 0))
                
                if (volume_24h >= PAIR_FILTERS['min_volume_24h'] and
                    PAIR_FILTERS['min_price'] <= price <= PAIR_FILTERS['max_price'] and
                    not any(pattern in symbol for pattern in PAIR_FILTERS['exclude_patterns'])):
                    
                    pairs[symbol] = TradingPair(
                        symbol=symbol,
                        base_asset=base,
                        quote_asset=quote,
                        price=price,
                        volume_24h=volume_24h,
                        exchange='mexc'
                    )
            
            logger.info(f"MEXC: получено {len(pairs)} торговых пар")
            return pairs
            
        except Exception as e:
            logger.error(f"Ошибка получения данных с MEXC: {e}")
            return {}

    async def fetch_bitget_data(self) -> Dict[str, TradingPair]:
        """Получение данных с Bitget"""
        try:
            url = 'https://api.bitget.com/api/spot/v1/market/tickers'
            
            async with self.session.get(url) as response:
                data = await response.json()
                
            pairs = {}
            if data.get('code') == '00000':
                for item in data['data']:
                    symbol = item['symbol']
                    base, quote = self.parse_symbol(symbol)
                    
                    volume_24h = float(item.get('quoteVol', 0))
                    price = float(item.get('close', 0))
                    
                    if (volume_24h >= PAIR_FILTERS['min_volume_24h'] and
                        PAIR_FILTERS['min_price'] <= price <= PAIR_FILTERS['max_price'] and
                        not any(pattern in symbol for pattern in PAIR_FILTERS['exclude_patterns'])):
                        
                        pairs[symbol] = TradingPair(
                            symbol=symbol,
                            base_asset=base,
                            quote_asset=quote,
                            price=price,
                            volume_24h=volume_24h,
                            exchange='bitget'
                        )
            
            logger.info(f"Bitget: получено {len(pairs)} торговых пар")
            return pairs
            
        except Exception as e:
            logger.error(f"Ошибка получения данных с Bitget: {e}")
            return {}

    async def fetch_all_exchange_data(self):
        """Получение данных со всех активных бирж параллельно"""
        fetch_functions = {
            'binance': self.fetch_binance_data,
            'bybit': self.fetch_bybit_data,
            'okx': self.fetch_okx_data,
            'kucoin': self.fetch_kucoin_data,
            'mexc': self.fetch_mexc_data,
            'bitget': self.fetch_bitget_data,
        }
        
        # Запускаем только активные биржи
        tasks = []
        exchange_names = []
        for exchange_name in self.active_exchanges.keys():
            if exchange_name in fetch_functions:
                tasks.append(fetch_functions[exchange_name]())
                exchange_names.append(exchange_name)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обновляем данные
        self.all_pairs = {}
        
        for i, result in enumerate(results):
            if i < len(exchange_names):
                exchange_name = exchange_names[i]
                if not isinstance(result, Exception) and result:
                    self.all_pairs[exchange_name] = result
                    self.last_update[exchange_name] = datetime.now()
                else:
                    logger.warning(f"Не удалось получить данные с {exchange_name}")
        
        # Нормализуем символы для поиска арбитража
        self.normalize_all_pairs()
        
        total_pairs = sum(len(pairs) for pairs in self.all_pairs.values())
        logger.info(f"Всего получено {total_pairs} торговых пар с {len(self.all_pairs)} бирж")

    def normalize_all_pairs(self):
        """Нормализация всех пар для поиска арбитража - АГРЕССИВНАЯ версия"""
        from config import WHITELIST_PAIRS, PAIR_FILTERS
        
        self.normalized_pairs = {}
        self.available_currencies = set()
        
        for exchange, pairs in self.all_pairs.items():
            for symbol, pair_data in pairs.items():
                normalized_symbol = self.normalize_symbol(symbol)
                
                # УБИРАЕМ фильтрацию по белому списку - мониторим ВСЕ пары
                # if normalized_symbol not in WHITELIST_PAIRS:
                #     continue
                
                # Более мягкая фильтрация - только критические исключения
                if (pair_data.volume_24h < PAIR_FILTERS['min_volume_24h'] or
                    pair_data.price < PAIR_FILTERS['min_price'] or
                    pair_data.price > PAIR_FILTERS['max_price']):
                    continue
                
                # Исключаем только явно левереджные токены
                if any(pattern in symbol.upper() for pattern in PAIR_FILTERS['exclude_patterns']):
                    continue
                
                if normalized_symbol not in self.normalized_pairs:
                    self.normalized_pairs[normalized_symbol] = {}
                
                self.normalized_pairs[normalized_symbol][exchange] = pair_data
                
                # Добавляем валюты в список для треугольного арбитража
                base, quote = self.parse_symbol(symbol)
                self.available_currencies.add(base)
                self.available_currencies.add(quote)
        
        # Генерируем ВСЕ возможные треугольные комбинации
        self.generate_triangular_combinations()
        
        logger.info(f"📊 Нормализовано {len(self.normalized_pairs)} торговых пар")
        logger.info(f"💱 Найдено {len(self.available_currencies)} уникальных валют")
        logger.info(f"🔺 Сгенерировано {len(self.triangular_sets)} треугольных комбинаций")

    def generate_triangular_combinations(self):
        """Генерация ВСЕХ возможных треугольных комбинаций"""
        # Используем основные валюты + все найденные валюты
        all_currencies = TRIANGULAR_BASE_CURRENCIES.copy()
        
        # Добавляем все найденные валюты (ограничиваем топ-100 по объему)
        currency_volumes = {}
        for symbol, exchanges in self.normalized_pairs.items():
            base, quote = self.parse_symbol(symbol)
            for exchange, pair_data in exchanges.items():
                if base not in currency_volumes:
                    currency_volumes[base] = 0
                if quote not in currency_volumes:
                    currency_volumes[quote] = 0
                currency_volumes[base] += pair_data.volume_24h
                currency_volumes[quote] += pair_data.volume_24h
        
        # Берем топ-50 валют по объему
        top_currencies = sorted(currency_volumes.items(), key=lambda x: x[1], reverse=True)[:50]
        for currency, _ in top_currencies:
            if currency not in all_currencies:
                all_currencies.append(currency)
        
        # Генерируем треугольные комбинации
        self.triangular_sets = []
        currencies = list(set(all_currencies))
        
        # Генерируем комбинации из 3 валют
        for i in range(len(currencies)):
            for j in range(i + 1, len(currencies)):
                for k in range(j + 1, len(currencies)):
                    # Добавляем основные перестановки
                    self.triangular_sets.extend([
                        (currencies[i], currencies[j], currencies[k]),
                        (currencies[i], currencies[k], currencies[j]),
                        (currencies[j], currencies[i], currencies[k])
                    ])
        
        # Убираем дубликаты
        self.triangular_sets = list(set(self.triangular_sets))

    def find_cross_exchange_arbitrage(self) -> List[ArbitrageOpportunity]:
        """Поиск межбиржевого арбитража для всех пар с фильтрацией"""
        from config import PAIR_FILTERS
        
        opportunities = []
        
        for normalized_symbol, exchange_data in self.normalized_pairs.items():
            if len(exchange_data) < 2:
                continue
            
            # Находим минимальную и максимальную цены
            prices = {exchange: pair.price for exchange, pair in exchange_data.items()}
            volumes = {exchange: pair.volume_24h for exchange, pair in exchange_data.items()}
            
            min_exchange = min(prices, key=prices.get)
            max_exchange = max(prices, key=prices.get)
            
            min_price = prices[min_exchange]
            max_price = prices[max_exchange]
            
            # Учитываем комиссии обеих бирж
            min_fee = self.active_exchanges[min_exchange]['fee']
            max_fee = self.active_exchanges[max_exchange]['fee']
            total_fees = min_fee + max_fee
            
            # Рассчитываем прибыль
            profit_percent = ((max_price - min_price) / min_price * 100) - total_fees
            
            # Фильтруем нереалистичные возможности
            if profit_percent > PAIR_FILTERS.get('max_profit_threshold', 50.0):
                continue
            
            # Рассчитываем уровень уверенности на основе объемов
            min_volume = min(volumes[min_exchange], volumes[max_exchange])
            confidence = min(1.0, min_volume / 100000)  # Максимальная уверенность при объеме 100k+
            
            if profit_percent > self.min_profit_threshold:
                opportunity = ArbitrageOpportunity(
                    type='cross_exchange',
                    profit_percent=profit_percent,
                    confidence=confidence,
                    details={
                        'symbol': normalized_symbol,
                        'buy_exchange': min_exchange,
                        'sell_exchange': max_exchange,
                        'buy_price': min_price,
                        'sell_price': max_price,
                        'buy_volume_24h': volumes[min_exchange],
                        'sell_volume_24h': volumes[max_exchange],
                        'all_prices': prices,
                        'all_volumes': volumes,
                        'fees': {'buy': min_fee, 'sell': max_fee, 'total': total_fees}
                    },
                    timestamp=datetime.now()
                )
                opportunities.append(opportunity)
        
        return sorted(opportunities, key=lambda x: x.profit_percent, reverse=True)

    def find_triangular_arbitrage(self, exchange: str) -> List[ArbitrageOpportunity]:
        """Поиск треугольного арбитража на одной бирже - АГРЕССИВНАЯ версия"""
        opportunities = []
        
        if exchange not in self.all_pairs:
            return opportunities
        
        pairs = self.all_pairs[exchange]
        
        # Создаем индекс пар по базовой и котируемой валюте
        pair_index = {}
        for symbol, pair_data in pairs.items():
            key = f"{pair_data.base_asset}{pair_data.quote_asset}"
            pair_index[key] = pair_data
        
        # Используем СГЕНЕРИРОВАННЫЕ треугольные комбинации вместо статичного списка
        for base, intermediate, quote in self.triangular_sets:
            # Формируем ключи для поиска пар
            pair1_key = f"{base}{quote}"      # BTC/USDT
            pair2_key = f"{intermediate}{quote}"  # ETH/USDT  
            pair3_key = f"{base}{intermediate}"   # BTC/ETH
            
            # Также проверяем обратные пары
            pair1_rev = f"{quote}{base}"
            pair2_rev = f"{quote}{intermediate}"
            pair3_rev = f"{intermediate}{base}"
            
            # Ищем доступные пары (прямые или обратные)
            p1 = pair_index.get(pair1_key) or pair_index.get(pair1_rev)
            p2 = pair_index.get(pair2_key) or pair_index.get(pair2_rev)
            p3 = pair_index.get(pair3_key) or pair_index.get(pair3_rev)
            
            if not (p1 and p2 and p3):
                continue
            
            # Проверяем минимальные объемы (СНИЖЕНО)
            min_volume = min(p1.volume_24h, p2.volume_24h, p3.volume_24h)
            if min_volume < PAIR_FILTERS['min_volume_24h']:
                continue
            
            # Комиссия биржи
            fee = self.active_exchanges[exchange]['fee'] / 100
            
            try:
                # Получаем правильные цены (учитываем обратные пары)
                price1 = p1.price if pair1_key in pair_index else (1 / p1.price)
                price2 = p2.price if pair2_key in pair_index else (1 / p2.price)
                price3 = p3.price if pair3_key in pair_index else (1 / p3.price)
                
                # Прямой треугольный арбитраж: quote -> base -> intermediate -> quote
                forward_result = (1 / price1) * price3 * price2
                forward_profit = (forward_result - 1) * 100 - (fee * 3 * 100)  # 3 сделки
                
                # Обратный треугольный арбитраж: quote -> intermediate -> base -> quote
                reverse_result = (1 / price2) * (1 / price3) * price1
                reverse_profit = (reverse_result - 1) * 100 - (fee * 3 * 100)
                
                # Уровень уверенности на основе объемов (СНИЖЕН порог)
                confidence = min(min_volume / 10000, 1.0)  # Снижено с 50000 до 10000
                
                # Проверяем прибыльность (остается 0.75%)
                if forward_profit >= self.min_profit_threshold:
                    opportunities.append(ArbitrageOpportunity(
                        type='triangular',
                        profit_percent=forward_profit,
                        details={
                            'exchange': exchange,
                            'path': f"{quote} -> {base} -> {intermediate} -> {quote}",
                            'pairs': [p1.symbol, p3.symbol, p2.symbol],
                            'prices': [price1, price3, price2],
                            'volume': min_volume,
                            'direction': 'forward'
                        },
                        timestamp=datetime.now(),
                        confidence=confidence
                    ))
                
                if reverse_profit >= self.min_profit_threshold:
                    opportunities.append(ArbitrageOpportunity(
                        type='triangular',
                        profit_percent=reverse_profit,
                        details={
                            'exchange': exchange,
                            'path': f"{quote} -> {intermediate} -> {base} -> {quote}",
                            'pairs': [p2.symbol, p3.symbol, p1.symbol],
                            'prices': [price2, 1/price3, price1],
                            'volume': min_volume,
                            'direction': 'reverse'
                        },
                        timestamp=datetime.now(),
                        confidence=confidence
                    ))
                    
            except (ZeroDivisionError, ValueError) as e:
                # Пропускаем пары с некорректными ценами
                continue
        
        return sorted(opportunities, key=lambda x: x.profit_percent, reverse=True)
                confidence = min(1.0, min_volume / 50000)
                
                # Проверяем прибыльность прямого направления
                if forward_profit > self.min_profit_threshold:
                    opportunity = ArbitrageOpportunity(
                        type='triangular',
                        profit_percent=forward_profit,
                        confidence=confidence,
                        details={
                            'exchange': exchange,
                            'direction': 'forward',
                            'path': f"{quote} -> {base} -> {intermediate} -> {quote}",
                            'pairs': [pair1_key, pair3_key, pair2_key],
                            'prices': [pair1.price, pair3.price, pair2.price],
                            'volumes': [pair1.volume_24h, pair3.volume_24h, pair2.volume_24h],
                            'calculation': f"1 / {pair1.price:.6f} * {pair3.price:.6f} * {pair2.price:.6f} = {forward_result:.6f}",
                            'fee_per_trade': fee * 100,
                            'total_fees': fee * 3 * 100
                        },
                        timestamp=datetime.now()
                    )
                    opportunities.append(opportunity)
                
                # Проверяем прибыльность обратного направления
                if reverse_profit > self.min_profit_threshold:
                    opportunity = ArbitrageOpportunity(
                        type='triangular',
                        profit_percent=reverse_profit,
                        confidence=confidence,
                        details={
                            'exchange': exchange,
                            'direction': 'reverse',
                            'path': f"{quote} -> {intermediate} -> {base} -> {quote}",
                            'pairs': [pair2_key, pair3_key, pair1_key],
                            'prices': [pair2.price, pair3.price, pair1.price],
                            'volumes': [pair2.volume_24h, pair3.volume_24h, pair1.volume_24h],
                            'calculation': f"1 / {pair2.price:.6f} * (1 / {pair3.price:.6f}) * {pair1.price:.6f} = {reverse_result:.6f}",
                            'fee_per_trade': fee * 100,
                            'total_fees': fee * 3 * 100
                        },
                        timestamp=datetime.now()
                    )
                    opportunities.append(opportunity)
        
        return sorted(opportunities, key=lambda x: x.profit_percent, reverse=True)

    async def monitor_loop(self, check_interval: int = 30):
        """Основной цикл мониторинга"""
        logger.info("🚀 Запуск расширенного мониторинга арбитражных возможностей...")
        
        while True:
            try:
                start_time = time.time()
                
                # Получаем данные со всех бирж
                await self.fetch_all_exchange_data()
                
                # Ищем межбиржевой арбитраж
                cross_opportunities = self.find_cross_exchange_arbitrage()
                
                # Ищем треугольный арбитраж на каждой бирже
                triangular_opportunities = []
                for exchange in self.all_pairs.keys():
                    exchange_triangular = self.find_triangular_arbitrage(exchange)
                    triangular_opportunities.extend(exchange_triangular)
                
                # Объединяем и сортируем все возможности
                all_opportunities = cross_opportunities + triangular_opportunities
                all_opportunities.sort(key=lambda x: (x.confidence * x.profit_percent), reverse=True)
                
                # Статистика
                fetch_time = time.time() - start_time
                total_pairs = sum(len(pairs) for pairs in self.all_pairs.values())
                
                logger.info(f"📊 Цикл завершен за {fetch_time:.1f}с | "
                          f"Пар: {total_pairs} | "
                          f"Возможностей: {len(all_opportunities)} | "
                          f"Топ прибыль: {all_opportunities[0].profit_percent:.2f}%" if all_opportunities else "Возможностей: 0")
                
                # Показываем топ возможности
                if all_opportunities:
                    for i, opp in enumerate(all_opportunities[:5]):  # Топ 5
                        confidence_emoji = "🟢" if opp.confidence > 0.7 else "🟡" if opp.confidence > 0.4 else "🔴"
                        logger.info(f"  {i+1}. {confidence_emoji} {opp.type}: {opp.profit_percent:.2f}% "
                                  f"(уверенность: {opp.confidence:.2f})")
                
                # Пауза перед следующей проверкой
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле мониторинга: {e}")
                await asyncio.sleep(10)

    async def run(self, check_interval: int = 30):
        """Запуск монитора"""
        await self.start_session()
        try:
            await self.monitor_loop(check_interval)
        finally:
            await self.close_session()

async def main():
    """Главная функция"""
    monitor = EnhancedArbitrageMonitor()
    await monitor.run()

if __name__ == "__main__":
    asyncio.run(main())