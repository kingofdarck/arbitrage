#!/usr/bin/env python3
"""
Криптовалютный арбитражный монитор
Поиск межбиржевых и треугольных арбитражных возможностей
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('arbitrage.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ArbitrageOpportunity:
    """Структура для хранения арбитражной возможности"""
    type: str  # 'cross_exchange' или 'triangular'
    profit_percent: float
    details: Dict
    timestamp: datetime

class CryptoArbitrageMonitor:
    def __init__(self):
        self.session = None
        self.exchanges = {
            'binance': 'https://api.binance.com/api/v3/ticker/price',
            'kucoin': 'https://api.kucoin.com/api/v1/market/allTickers',
            'gate': 'https://api.gateio.ws/api/v4/spot/tickers'
        }
        
        # Основные торговые пары для мониторинга
        self.main_pairs = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 
            'DOTUSDT', 'LINKUSDT', 'LTCUSDT', 'XRPUSDT'
        ]
        
        # Треугольные пары для арбитража
        self.triangular_sets = [
            ('BTC', 'ETH', 'USDT'),
            ('BTC', 'BNB', 'USDT'),
            ('ETH', 'BNB', 'USDT'),
            ('BTC', 'ADA', 'USDT'),
            ('ETH', 'LINK', 'USDT')
        ]
        
        self.prices = {}
        self.min_profit_threshold = 0.5  # Минимальная прибыль в %
        
    async def start_session(self):
        """Инициализация HTTP сессии"""
        self.session = aiohttp.ClientSession()
        
    async def close_session(self):
        """Закрытие HTTP сессии"""
        if self.session:
            await self.session.close()
    async def fetch_binance_prices(self) -> Dict[str, float]:
        """Получение цен с Binance"""
        try:
            async with self.session.get(self.exchanges['binance']) as response:
                data = await response.json()
                prices = {}
                for item in data:
                    symbol = item['symbol']
                    if symbol in self.main_pairs or any(symbol.startswith(base) for base in ['BTC', 'ETH', 'BNB']):
                        prices[symbol] = float(item['price'])
                return prices
        except Exception as e:
            logger.error(f"Ошибка получения данных с Binance: {e}")
            return {}

    async def fetch_kucoin_prices(self) -> Dict[str, float]:
        """Получение цен с KuCoin"""
        try:
            async with self.session.get(self.exchanges['kucoin']) as response:
                data = await response.json()
                prices = {}
                if data.get('code') == '200000':
                    for item in data['data']['ticker']:
                        symbol = item['symbol'].replace('-', '')
                        if symbol in self.main_pairs or any(symbol.startswith(base) for base in ['BTC', 'ETH', 'BNB']):
                            prices[symbol] = float(item['last'])
                return prices
        except Exception as e:
            logger.error(f"Ошибка получения данных с KuCoin: {e}")
            return {}

    async def fetch_gate_prices(self) -> Dict[str, float]:
        """Получение цен с Gate.io"""
        try:
            async with self.session.get(self.exchanges['gate']) as response:
                data = await response.json()
                prices = {}
                for item in data:
                    symbol = item['currency_pair'].replace('_', '')
                    if symbol in self.main_pairs or any(symbol.startswith(base) for base in ['BTC', 'ETH', 'BNB']):
                        prices[symbol] = float(item['last'])
                return prices
        except Exception as e:
            logger.error(f"Ошибка получения данных с Gate.io: {e}")
            return {}

    async def fetch_all_prices(self):
        """Получение цен со всех бирж"""
        tasks = [
            self.fetch_binance_prices(),
            self.fetch_kucoin_prices(),
            self.fetch_gate_prices()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        self.prices = {
            'binance': results[0] if not isinstance(results[0], Exception) else {},
            'kucoin': results[1] if not isinstance(results[1], Exception) else {},
            'gate': results[2] if not isinstance(results[2], Exception) else {}
        }
        
        logger.info(f"Получены цены с {len([p for p in self.prices.values() if p])} бирж")

    def find_cross_exchange_arbitrage(self) -> List[ArbitrageOpportunity]:
        """Поиск межбиржевого арбитража"""
        opportunities = []
        
        for symbol in self.main_pairs:
            exchange_prices = {}
            
            # Собираем цены по биржам для данного символа
            for exchange, prices in self.prices.items():
                if symbol in prices:
                    exchange_prices[exchange] = prices[symbol]
            
            if len(exchange_prices) >= 2:
                # Находим минимальную и максимальную цены
                min_exchange = min(exchange_prices, key=exchange_prices.get)
                max_exchange = max(exchange_prices, key=exchange_prices.get)
                
                min_price = exchange_prices[min_exchange]
                max_price = exchange_prices[max_exchange]
                
                # Рассчитываем потенциальную прибыль (учитываем комиссии ~0.2%)
                profit_percent = ((max_price - min_price) / min_price * 100) - 0.4
                
                if profit_percent > self.min_profit_threshold:
                    opportunity = ArbitrageOpportunity(
                        type='cross_exchange',
                        profit_percent=profit_percent,
                        details={
                            'symbol': symbol,
                            'buy_exchange': min_exchange,
                            'sell_exchange': max_exchange,
                            'buy_price': min_price,
                            'sell_price': max_price,
                            'all_prices': exchange_prices
                        },
                        timestamp=datetime.now()
                    )
                    opportunities.append(opportunity)
        
        return opportunities
    def find_triangular_arbitrage(self, exchange: str) -> List[ArbitrageOpportunity]:
        """Поиск треугольного арбитража на одной бирже"""
        opportunities = []
        
        if exchange not in self.prices or not self.prices[exchange]:
            return opportunities
        
        prices = self.prices[exchange]
        
        for base, intermediate, quote in self.triangular_sets:
            # Формируем названия пар
            pair1 = f"{base}{quote}"      # BTC/USDT
            pair2 = f"{intermediate}{quote}"  # ETH/USDT  
            pair3 = f"{base}{intermediate}"   # BTC/ETH
            
            # Проверяем наличие всех необходимых пар
            if all(pair in prices for pair in [pair1, pair2, pair3]):
                price1 = prices[pair1]  # BTC/USDT
                price2 = prices[pair2]  # ETH/USDT
                price3 = prices[pair3]  # BTC/ETH
                
                # Прямой треугольный арбитраж: USDT -> BTC -> ETH -> USDT
                forward_result = (1 / price1) * price3 * price2
                forward_profit = (forward_result - 1) * 100 - 0.3  # Учитываем комиссии
                
                # Обратный треугольный арбитраж: USDT -> ETH -> BTC -> USDT
                reverse_result = (1 / price2) * (1 / price3) * price1
                reverse_profit = (reverse_result - 1) * 100 - 0.3
                
                # Проверяем прибыльность
                if forward_profit > self.min_profit_threshold:
                    opportunity = ArbitrageOpportunity(
                        type='triangular',
                        profit_percent=forward_profit,
                        details={
                            'exchange': exchange,
                            'direction': 'forward',
                            'path': f"{quote} -> {base} -> {intermediate} -> {quote}",
                            'pairs': [pair1, pair3, pair2],
                            'prices': [price1, price3, price2],
                            'calculation': f"1 / {price1} * {price3} * {price2} = {forward_result}"
                        },
                        timestamp=datetime.now()
                    )
                    opportunities.append(opportunity)
                
                if reverse_profit > self.min_profit_threshold:
                    opportunity = ArbitrageOpportunity(
                        type='triangular',
                        profit_percent=reverse_profit,
                        details={
                            'exchange': exchange,
                            'direction': 'reverse',
                            'path': f"{quote} -> {intermediate} -> {base} -> {quote}",
                            'pairs': [pair2, pair3, pair1],
                            'prices': [price2, price3, price1],
                            'calculation': f"1 / {price2} * (1 / {price3}) * {price1} = {reverse_result}"
                        },
                        timestamp=datetime.now()
                    )
                    opportunities.append(opportunity)
        
        return opportunities

    def send_notification(self, opportunity: ArbitrageOpportunity):
        """Отправка уведомления о найденной возможности"""
        message = f"""
🚨 АРБИТРАЖНАЯ ВОЗМОЖНОСТЬ НАЙДЕНА! 🚨

Тип: {opportunity.type.upper()}
Прибыль: {opportunity.profit_percent:.2f}%
Время: {opportunity.timestamp.strftime('%H:%M:%S')}

Детали: {json.dumps(opportunity.details, indent=2, ensure_ascii=False)}
        """
        
        logger.info(message)
        
        # Здесь можно добавить отправку в Telegram, Discord, email и т.д.
        # Пример для Telegram (нужно настроить bot_token и chat_id):
        # await self.send_telegram_message(message)
        
        # Сохраняем в файл для истории
        with open('arbitrage_opportunities.log', 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().isoformat()} - {message}\n")

    async def monitor_loop(self):
        """Основной цикл мониторинга"""
        logger.info("Запуск мониторинга арбитражных возможностей...")
        
        while True:
            try:
                # Получаем актуальные цены
                await self.fetch_all_prices()
                
                # Ищем межбиржевой арбитраж
                cross_opportunities = self.find_cross_exchange_arbitrage()
                
                # Ищем треугольный арбитраж на каждой бирже
                triangular_opportunities = []
                for exchange in self.prices.keys():
                    triangular_opportunities.extend(
                        self.find_triangular_arbitrage(exchange)
                    )
                
                # Отправляем уведомления о найденных возможностях
                all_opportunities = cross_opportunities + triangular_opportunities
                
                if all_opportunities:
                    logger.info(f"Найдено {len(all_opportunities)} арбитражных возможностей!")
                    for opportunity in all_opportunities:
                        self.send_notification(opportunity)
                else:
                    logger.info("Арбитражных возможностей не найдено")
                
                # Пауза перед следующей проверкой (30 секунд)
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга: {e}")
                await asyncio.sleep(10)

    async def run(self):
        """Запуск монитора"""
        await self.start_session()
        try:
            await self.monitor_loop()
        finally:
            await self.close_session()

async def main():
    """Главная функция"""
    monitor = CryptoArbitrageMonitor()
    await monitor.run()

if __name__ == "__main__":
    asyncio.run(main())