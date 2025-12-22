#!/usr/bin/env python3
"""
Продвинутый криптовалютный арбитражный монитор
Поддержка всех видов арбитража
"""

import asyncio
import aiohttp
import json
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging
from config import EXCHANGES, TRIANGULAR_SETS, PAIR_FILTERS, BASE_CURRENCIES

logger = logging.getLogger(__name__)

@dataclass
class PriceData:
    """Расширенная информация о цене"""
    symbol: str
    price: float
    bid: float
    ask: float
    volume_24h: float
    spread_percent: float
    timestamp: datetime
    exchange: str
    order_book_depth: Dict[str, float] = field(default_factory=dict)

@dataclass
class ArbitrageOpportunity:
    """Расширенная структура арбитражной возможности"""
    type: str  # Тип арбитража
    subtype: str  # Подтип (например, 'forward', 'reverse' для треугольного)
    profit_percent: float
    confidence: float
    risk_level: str  # 'low', 'medium', 'high'
    details: Dict
    timestamp: datetime
    estimated_volume: float = 0  # Оценочный объем для исполнения
    execution_time: float = 0  # Оценочное время исполнения

class AdvancedArbitrageMonitor:
    def __init__(self):
        self.session = None
        self.price_history = defaultdict(lambda: deque(maxlen=100))  # История цен
        self.correlation_matrix = {}  # Матрица корреляций
        self.current_prices = {}  # Текущие цены с расширенной информацией
        self.futures_prices = {}  # Цены фьючерсов
        self.staking_rates = {}  # Ставки стейкинга
        
        # Настройки
        self.min_profit_threshold = 0.3
        self.correlation_window = 50  # Окно для расчета корреляций
        self.price_update_interval = 5  # Интервал обновления для временного арбитража
        
        # Активные биржи
        self.active_exchanges = {
            name: config for name, config in EXCHANGES.items() 
            if config['enabled']
        }
        
        logger.info(f"Инициализирован продвинутый монитор с {len(self.active_exchanges)} биржами")

    async def start_session(self):
        """Инициализация HTTP сессии"""
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
    async def close_session(self):
        """Закрытие HTTP сессии"""
        if self.session:
            await self.session.close()

    async def fetch_order_book(self, exchange: str, symbol: str, limit: int = 20) -> Dict:
        """Получение стакана заявок для анализа ликвидности"""
        try:
            if exchange == 'binance':
                url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit={limit}"
            elif exchange == 'bybit':
                url = f"https://api.bybit.com/v5/market/orderbook?category=spot&symbol={symbol}&limit={limit}"
            elif exchange == 'okx':
                url = f"https://www.okx.com/api/v5/market/books?instId={symbol}&sz={limit}"
            else:
                return {}
            
            async with self.session.get(url) as response:
                data = await response.json()
                
            # Нормализуем формат стакана
            if exchange == 'binance':
                return {
                    'bids': [[float(price), float(qty)] for price, qty in data.get('bids', [])],
                    'asks': [[float(price), float(qty)] for price, qty in data.get('asks', [])]
                }
            elif exchange == 'bybit' and data.get('retCode') == 0:
                result = data['result']
                return {
                    'bids': [[float(item[0]), float(item[1])] for item in result.get('b', [])],
                    'asks': [[float(item[0]), float(item[1])] for item in result.get('a', [])]
                }
            elif exchange == 'okx' and data.get('code') == '0':
                book_data = data['data'][0] if data['data'] else {}
                return {
                    'bids': [[float(item[0]), float(item[1])] for item in book_data.get('bids', [])],
                    'asks': [[float(item[0]), float(item[1])] for item in book_data.get('asks', [])]
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения стакана {symbol} с {exchange}: {e}")
            
        return {}

    async def fetch_futures_prices(self, exchange: str) -> Dict[str, float]:
        """Получение цен фьючерсов для арбитража спот-фьючерс"""
        try:
            if exchange == 'binance':
                url = "https://fapi.binance.com/fapi/v1/ticker/price"
            elif exchange == 'bybit':
                url = "https://api.bybit.com/v5/market/tickers?category=linear"
            elif exchange == 'okx':
                url = "https://www.okx.com/api/v5/market/tickers?instType=SWAP"
            else:
                return {}
            
            async with self.session.get(url) as response:
                data = await response.json()
            
            futures_prices = {}
            
            if exchange == 'binance':
                for item in data:
                    symbol = item['symbol']
                    if symbol.endswith('USDT'):
                        futures_prices[symbol] = float(item['price'])
                        
            elif exchange == 'bybit' and data.get('retCode') == 0:
                for item in data['result']['list']:
                    symbol = item['symbol']
                    if symbol.endswith('USDT'):
                        futures_prices[symbol] = float(item['lastPrice'])
                        
            elif exchange == 'okx' and data.get('code') == '0':
                for item in data['data']:
                    symbol = item['instId'].replace('-', '')
                    if 'SWAP' in item['instId']:
                        futures_prices[symbol] = float(item['last'])
            
            return futures_prices
            
        except Exception as e:
            logger.error(f"Ошибка получения фьючерсов с {exchange}: {e}")
            return {}

    def calculate_correlation(self, symbol1: str, symbol2: str) -> float:
        """Расчет корреляции между двумя торговыми парами"""
        if symbol1 not in self.price_history or symbol2 not in self.price_history:
            return 0.0
        
        prices1 = [p.price for p in list(self.price_history[symbol1])]
        prices2 = [p.price for p in list(self.price_history[symbol2])]
        
        if len(prices1) < 10 or len(prices2) < 10:
            return 0.0
        
        # Выравниваем длины массивов
        min_len = min(len(prices1), len(prices2))
        prices1 = prices1[-min_len:]
        prices2 = prices2[-min_len:]
        
        try:
            correlation = np.corrcoef(prices1, prices2)[0, 1]
            return correlation if not np.isnan(correlation) else 0.0
        except:
            return 0.0

    def find_statistical_arbitrage(self) -> List[ArbitrageOpportunity]:
        """Поиск статистического арбитража на основе корреляций"""
        opportunities = []
        
        # Находим пары с высокой корреляцией
        symbols = list(self.current_prices.keys())
        
        for i, symbol1 in enumerate(symbols):
            for symbol2 in symbols[i+1:]:
                correlation = self.calculate_correlation(symbol1, symbol2)
                
                if abs(correlation) > 0.8:  # Высокая корреляция
                    # Проверяем текущее отклонение от исторической корреляции
                    current_ratio = self.current_prices[symbol1].price / self.current_prices[symbol2].price
                    
                    # Рассчитываем историческое среднее соотношение
                    historical_ratios = []
                    for p1, p2 in zip(list(self.price_history[symbol1]), list(self.price_history[symbol2])):
                        if p2.price > 0:
                            historical_ratios.append(p1.price / p2.price)
                    
                    if len(historical_ratios) >= 20:
                        mean_ratio = np.mean(historical_ratios)
                        std_ratio = np.std(historical_ratios)
                        
                        # Z-score отклонения
                        z_score = (current_ratio - mean_ratio) / std_ratio if std_ratio > 0 else 0
                        
                        if abs(z_score) > 2:  # Значительное отклонение
                            profit_estimate = abs(z_score) * std_ratio / mean_ratio * 100
                            
                            if profit_estimate > self.min_profit_threshold:
                                opportunity = ArbitrageOpportunity(
                                    type='statistical',
                                    subtype='mean_reversion',
                                    profit_percent=profit_estimate,
                                    confidence=min(abs(correlation), 0.95),
                                    risk_level='medium',
                                    details={
                                        'symbol1': symbol1,
                                        'symbol2': symbol2,
                                        'correlation': correlation,
                                        'current_ratio': current_ratio,
                                        'mean_ratio': mean_ratio,
                                        'z_score': z_score,
                                        'action': 'buy' if z_score < -2 else 'sell',
                                        'target_symbol': symbol1 if z_score < -2 else symbol2
                                    },
                                    timestamp=datetime.now()
                                )
                                opportunities.append(opportunity)
        
        return opportunities

    def find_temporal_arbitrage(self) -> List[ArbitrageOpportunity]:
        """Поиск временного арбитража (задержки в обновлении цен)"""
        opportunities = []
        
        # Группируем цены по символам
        symbol_prices = defaultdict(list)
        for exchange, price_data in self.current_prices.items():
            for symbol, data in price_data.items():
                symbol_prices[symbol].append((exchange, data))
        
        for symbol, exchange_data in symbol_prices.items():
            if len(exchange_data) < 2:
                continue
            
            # Сортируем по времени обновления
            exchange_data.sort(key=lambda x: x[1].timestamp)
            
            # Проверяем разницу во времени обновления
            latest = exchange_data[-1]
            for exchange, data in exchange_data[:-1]:
                time_diff = (latest[1].timestamp - data.timestamp).total_seconds()
                
                if time_diff > 10:  # Задержка более 10 секунд
                    price_diff = abs(latest[1].price - data.price) / data.price * 100
                    
                    if price_diff > self.min_profit_threshold:
                        opportunity = ArbitrageOpportunity(
                            type='temporal',
                            subtype='price_lag',
                            profit_percent=price_diff,
                            confidence=max(0.3, 1.0 - time_diff/60),  # Уверенность падает со временем
                            risk_level='high',
                            details={
                                'symbol': symbol,
                                'slow_exchange': exchange,
                                'fast_exchange': latest[0],
                                'slow_price': data.price,
                                'fast_price': latest[1].price,
                                'time_lag': time_diff,
                                'action': 'buy_slow_sell_fast' if data.price < latest[1].price else 'sell_slow_buy_fast'
                            },
                            timestamp=datetime.now(),
                            execution_time=time_diff
                        )
                        opportunities.append(opportunity)
        
        return opportunities

    def find_spread_arbitrage(self) -> List[ArbitrageOpportunity]:
        """Поиск арбитража спот-фьючерс"""
        opportunities = []
        
        for exchange in self.active_exchanges.keys():
            if exchange not in self.current_prices or exchange not in self.futures_prices:
                continue
            
            spot_prices = self.current_prices[exchange]
            futures_prices = self.futures_prices[exchange]
            
            for symbol in spot_prices.keys():
                if symbol in futures_prices:
                    spot_price = spot_prices[symbol].price
                    futures_price = futures_prices[symbol]
                    
                    # Рассчитываем спред
                    spread_percent = (futures_price - spot_price) / spot_price * 100
                    
                    if abs(spread_percent) > self.min_profit_threshold:
                        opportunity = ArbitrageOpportunity(
                            type='spread',
                            subtype='spot_futures',
                            profit_percent=abs(spread_percent),
                            confidence=0.7,  # Средняя уверенность из-за рисков фьючерсов
                            risk_level='medium',
                            details={
                                'symbol': symbol,
                                'exchange': exchange,
                                'spot_price': spot_price,
                                'futures_price': futures_price,
                                'spread_percent': spread_percent,
                                'action': 'buy_spot_sell_futures' if spread_percent > 0 else 'sell_spot_buy_futures'
                            },
                            timestamp=datetime.now()
                        )
                        opportunities.append(opportunity)
        
        return opportunities

    def find_liquidity_arbitrage(self) -> List[ArbitrageOpportunity]:
        """Поиск арбитража ликвидности (использование разной глубины стаканов)"""
        opportunities = []
        
        # Группируем стаканы по символам
        symbol_books = defaultdict(list)
        for exchange, books in getattr(self, 'order_books', {}).items():
            for symbol, book in books.items():
                if book and 'bids' in book and 'asks' in book:
                    symbol_books[symbol].append((exchange, book))
        
        for symbol, exchange_books in symbol_books.items():
            if len(exchange_books) < 2:
                continue
            
            for i, (exchange1, book1) in enumerate(exchange_books):
                for exchange2, book2 in exchange_books[i+1:]:
                    # Анализируем возможность арбитража с учетом глубины
                    if not book1['bids'] or not book1['asks'] or not book2['bids'] or not book2['asks']:
                        continue
                    
                    # Лучшие цены
                    best_bid1 = book1['bids'][0][0] if book1['bids'] else 0
                    best_ask1 = book1['asks'][0][0] if book1['asks'] else float('inf')
                    best_bid2 = book2['bids'][0][0] if book2['bids'] else 0
                    best_ask2 = book2['asks'][0][0] if book2['asks'] else float('inf')
                    
                    # Проверяем арбитраж: покупаем на одной бирже, продаем на другой
                    if best_ask1 < best_bid2:  # Покупаем на exchange1, продаем на exchange2
                        profit_percent = (best_bid2 - best_ask1) / best_ask1 * 100
                        
                        # Рассчитываем доступный объем
                        ask_volume1 = sum([qty for price, qty in book1['asks'] if price <= best_bid2])
                        bid_volume2 = sum([qty for price, qty in book2['bids'] if price >= best_ask1])
                        available_volume = min(ask_volume1, bid_volume2)
                        
                        if profit_percent > self.min_profit_threshold and available_volume > 0:
                            opportunity = ArbitrageOpportunity(
                                type='liquidity',
                                subtype='order_book_imbalance',
                                profit_percent=profit_percent,
                                confidence=min(0.9, available_volume / 10),  # Уверенность зависит от объема
                                risk_level='low',
                                details={
                                    'symbol': symbol,
                                    'buy_exchange': exchange1,
                                    'sell_exchange': exchange2,
                                    'buy_price': best_ask1,
                                    'sell_price': best_bid2,
                                    'available_volume': available_volume,
                                    'execution_steps': f"Buy {available_volume} on {exchange1} at {best_ask1}, sell on {exchange2} at {best_bid2}"
                                },
                                timestamp=datetime.now(),
                                estimated_volume=available_volume
                            )
                            opportunities.append(opportunity)
                    
                    # Проверяем обратное направление
                    if best_ask2 < best_bid1:
                        profit_percent = (best_bid1 - best_ask2) / best_ask2 * 100
                        
                        ask_volume2 = sum([qty for price, qty in book2['asks'] if price <= best_bid1])
                        bid_volume1 = sum([qty for price, qty in book1['bids'] if price >= best_ask2])
                        available_volume = min(ask_volume2, bid_volume1)
                        
                        if profit_percent > self.min_profit_threshold and available_volume > 0:
                            opportunity = ArbitrageOpportunity(
                                type='liquidity',
                                subtype='order_book_imbalance',
                                profit_percent=profit_percent,
                                confidence=min(0.9, available_volume / 10),
                                risk_level='low',
                                details={
                                    'symbol': symbol,
                                    'buy_exchange': exchange2,
                                    'sell_exchange': exchange1,
                                    'buy_price': best_ask2,
                                    'sell_price': best_bid1,
                                    'available_volume': available_volume,
                                    'execution_steps': f"Buy {available_volume} on {exchange2} at {best_ask2}, sell on {exchange1} at {best_bid1}"
                                },
                                timestamp=datetime.now(),
                                estimated_volume=available_volume
                            )
                            opportunities.append(opportunity)
        
        return opportunities
    def find_index_arbitrage(self) -> List[ArbitrageOpportunity]:
        """Поиск арбитража индексных токенов"""
        opportunities = []
        
        # Определяем индексные токены и их составляющие
        index_compositions = {
            'DPI': ['UNI', 'AAVE', 'SNX', 'MKR', 'COMP', 'BAL', 'YFI', 'REN', 'KNC', 'LRC'],
            'BTC2X-FLI': ['BTC'],  # Левереджный индекс
            'ETH2X-FLI': ['ETH'],  # Левереджный индекс
            # Можно добавить больше индексов
        }
        
        for index_symbol, components in index_compositions.items():
            # Ищем цену индексного токена
            index_prices = {}
            for exchange, prices in self.current_prices.items():
                for symbol, data in prices.items():
                    if symbol.startswith(index_symbol):
                        index_prices[exchange] = data.price
            
            if not index_prices:
                continue
            
            # Рассчитываем теоретическую стоимость корзины
            basket_value = 0
            missing_components = 0
            
            for component in components:
                component_found = False
                for exchange, prices in self.current_prices.items():
                    component_symbol = f"{component}USDT"
                    if component_symbol in prices:
                        # Здесь нужны веса компонентов в индексе (упрощенно берем равные веса)
                        weight = 1.0 / len(components)
                        basket_value += prices[component_symbol].price * weight
                        component_found = True
                        break
                
                if not component_found:
                    missing_components += 1
            
            # Если слишком много отсутствующих компонентов, пропускаем
            if missing_components > len(components) * 0.3:
                continue
            
            # Сравниваем с ценой индексного токена
            for exchange, index_price in index_prices.items():
                if basket_value > 0:
                    price_diff_percent = abs(index_price - basket_value) / basket_value * 100
                    
                    if price_diff_percent > self.min_profit_threshold:
                        opportunity = ArbitrageOpportunity(
                            type='index',
                            subtype='basket_deviation',
                            profit_percent=price_diff_percent,
                            confidence=0.6,  # Средняя уверенность из-за сложности исполнения
                            risk_level='high',
                            details={
                                'index_symbol': index_symbol,
                                'exchange': exchange,
                                'index_price': index_price,
                                'basket_value': basket_value,
                                'components': components,
                                'missing_components': missing_components,
                                'action': 'buy_index_sell_basket' if index_price < basket_value else 'sell_index_buy_basket'
                            },
                            timestamp=datetime.now()
                        )
                        opportunities.append(opportunity)
        
        return opportunities

    def find_staking_arbitrage(self) -> List[ArbitrageOpportunity]:
        """Поиск арбитража стейкинга (между стейкнутыми и обычными токенами)"""
        opportunities = []
        
        # Пары стейкнутых токенов
        staking_pairs = {
            'STETH': 'ETH',    # Lido Staked ETH
            'RETH': 'ETH',     # Rocket Pool ETH
            'BETH': 'ETH',     # Binance Staked ETH
            'STMATIC': 'MATIC', # Staked MATIC
            'STBNB': 'BNB',    # Staked BNB
            'STSOL': 'SOL',    # Staked SOL
        }
        
        for staked_token, base_token in staking_pairs.items():
            staked_prices = {}
            base_prices = {}
            
            # Собираем цены стейкнутого токена
            for exchange, prices in self.current_prices.items():
                staked_symbol = f"{staked_token}USDT"
                base_symbol = f"{base_token}USDT"
                
                if staked_symbol in prices:
                    staked_prices[exchange] = prices[staked_symbol].price
                if base_symbol in prices:
                    base_prices[exchange] = prices[base_symbol].price
            
            # Ищем арбитражные возможности
            for exchange in staked_prices.keys():
                if exchange in base_prices:
                    staked_price = staked_prices[exchange]
                    base_price = base_prices[exchange]
                    
                    # Обычно стейкнутые токены торгуются с дисконтом
                    discount_percent = (base_price - staked_price) / base_price * 100
                    
                    # Получаем текущую ставку стейкинга (упрощенно используем фиксированные значения)
                    staking_rates = {
                        'ETH': 4.0,    # ~4% годовых
                        'MATIC': 8.0,  # ~8% годовых
                        'BNB': 6.0,    # ~6% годовых
                        'SOL': 7.0,    # ~7% годовых
                    }
                    
                    annual_rate = staking_rates.get(base_token, 5.0)
                    
                    # Если дисконт больше ожидаемой доходности, это возможность
                    if discount_percent > annual_rate / 12:  # Месячная доходность
                        opportunity = ArbitrageOpportunity(
                            type='staking',
                            subtype='discount_arbitrage',
                            profit_percent=discount_percent - annual_rate / 12,
                            confidence=0.8,
                            risk_level='low',
                            details={
                                'staked_token': staked_token,
                                'base_token': base_token,
                                'exchange': exchange,
                                'staked_price': staked_price,
                                'base_price': base_price,
                                'discount_percent': discount_percent,
                                'annual_staking_rate': annual_rate,
                                'action': f'buy_{staked_token}_stake_for_{base_token}',
                                'expected_monthly_yield': annual_rate / 12
                            },
                            timestamp=datetime.now()
                        )
                        opportunities.append(opportunity)
        
        return opportunities

    def find_funding_rate_arbitrage(self) -> List[ArbitrageOpportunity]:
        """Поиск арбитража ставок фондирования"""
        opportunities = []
        
        # Здесь нужно получать ставки фондирования с бирж
        # Упрощенная реализация
        funding_rates = {
            'BTCUSDT': 0.01,   # 1% в день
            'ETHUSDT': 0.008,  # 0.8% в день
            'BNBUSDT': 0.005,  # 0.5% в день
        }
        
        for symbol, funding_rate in funding_rates.items():
            daily_rate_percent = funding_rate * 100
            
            if daily_rate_percent > 0.1:  # Если ставка больше 0.1% в день
                opportunity = ArbitrageOpportunity(
                    type='funding',
                    subtype='rate_arbitrage',
                    profit_percent=daily_rate_percent,
                    confidence=0.9,
                    risk_level='low',
                    details={
                        'symbol': symbol,
                        'funding_rate_daily': daily_rate_percent,
                        'action': 'long_perpetual_short_spot',
                        'strategy': 'Hold long perpetual position to collect funding'
                    },
                    timestamp=datetime.now()
                )
                opportunities.append(opportunity)
        
        return opportunities

    async def update_price_history(self):
        """Обновление истории цен для статистического анализа"""
        current_time = datetime.now()
        
        for exchange, prices in self.current_prices.items():
            for symbol, price_data in prices.items():
                self.price_history[f"{exchange}:{symbol}"].append(price_data)

    async def fetch_all_data(self):
        """Получение всех необходимых данных"""
        # Получаем основные цены (используем метод из базового класса)
        # Здесь должен быть вызов метода получения цен
        
        # Получаем фьючерсные цены
        futures_tasks = []
        for exchange in ['binance', 'bybit', 'okx']:
            if exchange in self.active_exchanges:
                futures_tasks.append(self.fetch_futures_prices(exchange))
        
        futures_results = await asyncio.gather(*futures_tasks, return_exceptions=True)
        
        for i, result in enumerate(futures_results):
            if not isinstance(result, Exception) and result:
                exchange_name = ['binance', 'bybit', 'okx'][i]
                self.futures_prices[exchange_name] = result
        
        # Получаем стаканы заявок для ликвидного арбитража
        self.order_books = {}
        for exchange in ['binance', 'bybit', 'okx']:
            if exchange in self.active_exchanges:
                self.order_books[exchange] = {}
                # Получаем стаканы для топ-пар
                top_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
                for symbol in top_symbols:
                    book = await self.fetch_order_book(exchange, symbol)
                    if book:
                        self.order_books[exchange][symbol] = book
        
        # Обновляем историю цен
        await self.update_price_history()

    def find_all_arbitrage_opportunities(self) -> List[ArbitrageOpportunity]:
        """Поиск всех видов арбитражных возможностей"""
        all_opportunities = []
        
        try:
            # 1. Статистический арбитраж
            statistical_opps = self.find_statistical_arbitrage()
            all_opportunities.extend(statistical_opps)
            logger.info(f"Найдено {len(statistical_opps)} статистических возможностей")
            
            # 2. Временной арбитраж
            temporal_opps = self.find_temporal_arbitrage()
            all_opportunities.extend(temporal_opps)
            logger.info(f"Найдено {len(temporal_opps)} временных возможностей")
            
            # 3. Арбитраж спредов
            spread_opps = self.find_spread_arbitrage()
            all_opportunities.extend(spread_opps)
            logger.info(f"Найдено {len(spread_opps)} спред-возможностей")
            
            # 4. Арбитраж ликвидности
            liquidity_opps = self.find_liquidity_arbitrage()
            all_opportunities.extend(liquidity_opps)
            logger.info(f"Найдено {len(liquidity_opps)} ликвидных возможностей")
            
            # 5. Арбитраж индексов
            index_opps = self.find_index_arbitrage()
            all_opportunities.extend(index_opps)
            logger.info(f"Найдено {len(index_opps)} индексных возможностей")
            
            # 6. Арбитраж стейкинга
            staking_opps = self.find_staking_arbitrage()
            all_opportunities.extend(staking_opps)
            logger.info(f"Найдено {len(staking_opps)} стейкинг-возможностей")
            
            # 7. Арбитраж ставок фондирования
            funding_opps = self.find_funding_rate_arbitrage()
            all_opportunities.extend(funding_opps)
            logger.info(f"Найдено {len(funding_opps)} фондинг-возможностей")
            
        except Exception as e:
            logger.error(f"Ошибка при поиске арбитража: {e}")
        
        # Сортируем по взвешенной прибыли
        all_opportunities.sort(
            key=lambda x: x.profit_percent * x.confidence, 
            reverse=True
        )
        
        return all_opportunities

    async def monitor_loop(self, check_interval: int = 30):
        """Основной цикл мониторинга всех видов арбитража"""
        logger.info("🚀 Запуск продвинутого мониторинга всех видов арбитража...")
        
        cycle_count = 0
        
        while True:
            try:
                cycle_start = datetime.now()
                cycle_count += 1
                
                # Получаем все данные
                await self.fetch_all_data()
                
                # Ищем все виды арбитража
                all_opportunities = self.find_all_arbitrage_opportunities()
                
                # Статистика по типам
                type_stats = defaultdict(int)
                for opp in all_opportunities:
                    type_stats[opp.type] += 1
                
                cycle_time = (datetime.now() - cycle_start).total_seconds()
                
                logger.info(f"📊 Цикл #{cycle_count} за {cycle_time:.1f}с | "
                          f"Всего возможностей: {len(all_opportunities)}")
                
                # Показываем статистику по типам
                if type_stats:
                    stats_str = " | ".join([f"{t}: {c}" for t, c in type_stats.items()])
                    logger.info(f"   По типам: {stats_str}")
                
                # Показываем топ возможности
                if all_opportunities:
                    logger.info("🎯 Топ-5 возможностей:")
                    for i, opp in enumerate(all_opportunities[:5]):
                        risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(opp.risk_level, "⚪")
                        logger.info(f"  {i+1}. {risk_emoji} {opp.type}/{opp.subtype}: "
                                  f"{opp.profit_percent:.2f}% (уверенность: {opp.confidence:.1%})")
                
                # Пауза перед следующим циклом
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле мониторинга: {e}")
                await asyncio.sleep(10)

    async def run(self, check_interval: int = 30):
        """Запуск продвинутого монитора"""
        await self.start_session()
        try:
            await self.monitor_loop(check_interval)
        finally:
            await self.close_session()

async def main():
    """Главная функция"""
    monitor = AdvancedArbitrageMonitor()
    await monitor.run()

if __name__ == "__main__":
    asyncio.run(main())