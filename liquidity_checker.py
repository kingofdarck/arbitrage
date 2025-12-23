#!/usr/bin/env python3
"""
Модуль проверки ликвидности и доступности депозитов/выводов
Проверяет можно ли реально внести и вывести криптовалюту с бирж
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class LiquidityStatus:
    """Статус ликвидности для криптовалюты на бирже"""
    symbol: str
    exchange: str
    deposit_enabled: bool
    withdraw_enabled: bool
    deposit_min: float
    withdraw_min: float
    withdraw_fee: float
    network_status: str  # 'normal', 'maintenance', 'suspended'
    last_checked: datetime
    confidence: float  # 0-1, уверенность в данных

@dataclass
class ArbitrageLiquidity:
    """Ликвидность для арбитражной возможности"""
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_liquidity: LiquidityStatus
    sell_liquidity: LiquidityStatus
    is_viable: bool  # Можно ли реально выполнить арбитраж
    risk_level: str  # 'low', 'medium', 'high'
    estimated_time: int  # Время выполнения в минутах

class LiquidityChecker:
    """Проверка ликвидности и доступности депозитов/выводов"""
    
    def __init__(self):
        self.session = None
        self.liquidity_cache = {}  # Кеш статусов ликвидности
        self.cache_duration = timedelta(minutes=10)  # Кеш на 10 минут
        
        # Известные сети для популярных токенов
        self.token_networks = {
            'USDT': ['TRC20', 'ERC20', 'BEP20', 'POLYGON'],
            'USDC': ['ERC20', 'BEP20', 'POLYGON', 'ARBITRUM'],
            'BTC': ['BTC'],
            'ETH': ['ERC20'],
            'BNB': ['BEP20'],
            'TRX': ['TRC20'],
            'MATIC': ['POLYGON'],
            'AVAX': ['AVAX-C'],
            'SOL': ['SOL'],
            'ADA': ['ADA'],
            'DOT': ['DOT'],
            'ATOM': ['COSMOS']
        }
        
        # Список токенов с частыми проблемами депозитов/выводов
        self.problematic_tokens = {
            # Коллапсы и скамы
            'VRA', 'LUNC', 'USTC', 'FTT', 'SRM', 'RAY', 'FIDA', 'KIN', 'MAPS',
            'OXY', 'BTTC', 'WIN', 'NFT', 'JST', 'SUN', 'APENFT',
            
            # Мем-токены с проблемами
            'SHIB', 'FLOKI', 'BABYDOGE', 'SAFEMOON', 'ELONGATE', 'HOKK',
            'KISHU', 'ELON', 'AKITA', 'RYOSHI', 'LEASH', 'BONE',
            
            # Токены с техническими проблемами
            'GALA', 'SAND', 'MANA', 'ENJ', 'CHZ', 'BAT', 'ZIL',
            'HOT', 'DENT', 'BTT', 'WRX', 'DOGE', 'XVG', 'NPXS',
            
            # Токены DeFi с проблемами
            'CAKE', 'ALPHA', 'XVS', 'SXP', 'HARD', 'KAVA', 'BNX',
            'TLM', 'ALICE', 'TKO', 'PROS', 'BETA', 'RARE', 'LOKA',
            
            # Старые токены с проблемами
            'XEM', 'WAVES', 'LSK', 'ARDR', 'NXT', 'BURST', 'SC',
            'DGB', 'RDD', 'DOGE', 'LTC', 'DASH', 'ZEC', 'XMR'
        }
        
        # Надежные токены с высокой ликвидностью
        self.reliable_tokens = {
            'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'MATIC', 'DOT', 'LINK', 'AVAX',
            'UNI', 'AAVE', 'COMP', 'MKR', 'SNX', 'CRV', 'YFI', 'SUSHI',
            'ATOM', 'NEAR', 'FTM', 'ALGO', 'VET', 'ICP', 'THETA', 'FIL',
            'XRP', 'LTC', 'BCH', 'ETC', 'XLM', 'TRX', 'EOS'
        }
        
        logger.info("🔍 Инициализирован модуль проверки ликвидности")

    async def start_session(self):
        """Инициализация HTTP сессии"""
        timeout = aiohttp.ClientTimeout(total=15, connect=5)
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def close_session(self):
        """Закрытие HTTP сессии"""
        if self.session:
            await self.session.close()

    def get_cache_key(self, symbol: str, exchange: str) -> str:
        """Генерация ключа для кеша"""
        return f"{exchange}_{symbol}"

    def is_cache_valid(self, cache_key: str) -> bool:
        """Проверка валидности кеша"""
        if cache_key not in self.liquidity_cache:
            return False
        
        cached_data = self.liquidity_cache[cache_key]
        return datetime.now() - cached_data.last_checked < self.cache_duration

    async def get_real_binance_deposit_status(self, base_currency: str) -> Tuple[bool, bool]:
        """Попытка получить реальный статус депозитов/выводов с Binance"""
        try:
            # Пробуем получить информацию о монете (может потребовать API ключ)
            url = 'https://api.binance.com/sapi/v1/capital/config/getall'
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for coin_info in data:
                        if coin_info.get('coin') == base_currency:
                            networks = coin_info.get('networkList', [])
                            
                            # Ищем хотя бы одну рабочую сеть
                            deposit_available = False
                            withdraw_available = False
                            
                            for network in networks:
                                if network.get('depositEnable', False):
                                    deposit_available = True
                                if network.get('withdrawEnable', False):
                                    withdraw_available = True
                            
                            logger.info(f"✅ Получен реальный статус {base_currency}: депозит={deposit_available}, вывод={withdraw_available}")
                            return deposit_available, withdraw_available
                            
        except Exception as e:
            logger.debug(f"Не удалось получить реальный статус для {base_currency}: {e}")
        
        # Возвращаем None если не удалось получить данные
        return None, None

    async def check_binance_liquidity(self, symbol: str) -> Optional[LiquidityStatus]:
        """Проверка ликвидности на Binance с реальной проверкой депозитов/выводов"""
        try:
            # Сначала проверяем что пара торгуется
            ticker_url = f'https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}'
            
            async with self.session.get(ticker_url) as response:
                if response.status != 200:
                    return None
                    
                ticker_data = await response.json()
                if ticker_data.get('symbol') != symbol:
                    return None
                
                volume = float(ticker_data.get('quoteVolume', 0))
                
                # Получаем базовую валюту из символа
                base_currency = symbol.replace('USDT', '').replace('USDC', '').replace('BUSD', '').replace('FDUSD', '')
                
                # Пытаемся получить реальный статус
                real_deposit, real_withdraw = await self.get_real_binance_deposit_status(base_currency)
                
                # Если получили реальные данные, используем их
                if real_deposit is not None and real_withdraw is not None:
                    deposit_enabled = real_deposit
                    withdraw_enabled = real_withdraw
                    network_status = 'normal' if (real_deposit and real_withdraw) else 'limited'
                    confidence = 0.95  # Высокая уверенность в реальных данных
                else:
                    # Иначе используем эвристику
                    deposit_enabled = True
                    withdraw_enabled = True
                    network_status = 'normal'
                    confidence = min(1.0, volume / 1000000)
                    
                    # Проблемные токены - консервативная оценка
                    if base_currency in self.problematic_tokens:
                        deposit_enabled = False
                        withdraw_enabled = False
                        network_status = 'suspended'
                        confidence = 0.1
                        logger.info(f"⚠️ {base_currency} в списке проблемных токенов - депозиты/выводы могут быть недоступны")
                    
                    # Для малоизвестных токенов снижаем уверенность
                    elif volume < 10000:  # Очень низкий объем
                        confidence = 0.3
                        network_status = 'limited'
                        deposit_enabled = False  # Консервативно предполагаем что депозиты могут быть отключены
                        withdraw_enabled = True   # Выводы обычно работают
                    elif volume < 100000:  # Низкий объем
                        confidence = 0.5
                        network_status = 'limited'
                    
                    # Для надежных токенов высокая уверенность
                    elif base_currency in self.reliable_tokens:
                        confidence = 0.9
                        deposit_enabled = True
                        withdraw_enabled = True
                        network_status = 'normal'
                
                return LiquidityStatus(
                    symbol=symbol,
                    exchange='binance',
                    deposit_enabled=deposit_enabled,
                    withdraw_enabled=withdraw_enabled,
                    deposit_min=0.0,
                    withdraw_min=0.0,
                    withdraw_fee=0.0,
                    network_status=network_status,
                    last_checked=datetime.now(),
                    confidence=confidence
                )
                        
        except Exception as e:
            logger.warning(f"Ошибка проверки ликвидности Binance для {symbol}: {e}")
        
        return None

    async def check_bybit_liquidity(self, symbol: str) -> Optional[LiquidityStatus]:
        """Проверка ликвидности на Bybit с учетом проблемных токенов"""
        try:
            # Проверяем что пара торгуется
            url = f'https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}'
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('retCode') == 0:
                        result = data.get('result', {}).get('list', [])
                        if result and result[0].get('symbol') == symbol:
                            volume = float(result[0].get('turnover24h', 0))
                            base_currency = symbol.replace('USDT', '').replace('USDC', '').replace('BUSD', '')
                            
                            # Применяем ту же логику что и для Binance
                            deposit_enabled = True
                            withdraw_enabled = True
                            network_status = 'normal'
                            confidence = min(1.0, volume / 500000)
                            
                            if base_currency in self.problematic_tokens:
                                deposit_enabled = False
                                withdraw_enabled = False
                                network_status = 'suspended'
                                confidence = 0.1
                            elif volume < 5000:
                                confidence = 0.3
                                network_status = 'limited'
                                deposit_enabled = False
                            elif base_currency in self.reliable_tokens:
                                confidence = 0.8
                                deposit_enabled = True
                                withdraw_enabled = True
                                network_status = 'normal'
                            
                            return LiquidityStatus(
                                symbol=symbol,
                                exchange='bybit',
                                deposit_enabled=deposit_enabled,
                                withdraw_enabled=withdraw_enabled,
                                deposit_min=0.0,
                                withdraw_min=0.0,
                                withdraw_fee=0.0,
                                network_status=network_status,
                                last_checked=datetime.now(),
                                confidence=confidence
                            )
                            
        except Exception as e:
            logger.warning(f"Ошибка проверки ликвидности Bybit для {symbol}: {e}")
        
        return None

    async def check_okx_liquidity(self, symbol: str) -> Optional[LiquidityStatus]:
        """Проверка ликвидности на OKX (упрощенная)"""
        try:
            # Проверяем что пара торгуется
            url = f'https://www.okx.com/api/v5/market/ticker?instId={symbol}'
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('code') == '0' and data.get('data'):
                        ticker = data['data'][0]
                        if ticker.get('instId') == symbol:
                            # Если пара торгуется, предполагаем доступность
                            volume = float(ticker.get('volCcy24h', 0))
                            confidence = min(1.0, volume / 300000)
                            
                            return LiquidityStatus(
                                symbol=symbol,
                                exchange='okx',
                                deposit_enabled=True,
                                withdraw_enabled=True,
                                deposit_min=0.0,
                                withdraw_min=0.0,
                                withdraw_fee=0.0,
                                network_status='normal' if volume > 30000 else 'limited',
                                last_checked=datetime.now(),
                                confidence=confidence
                            )
                            
        except Exception as e:
            logger.warning(f"Ошибка проверки ликвидности OKX для {symbol}: {e}")
        
        return None

    async def check_kucoin_liquidity(self, symbol: str) -> Optional[LiquidityStatus]:
        """Проверка ликвидности на KuCoin (упрощенная)"""
        try:
            # Проверяем что пара торгуется
            url = f'https://api.kucoin.com/api/v1/market/stats?symbol={symbol}'
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('code') == '200000' and data.get('data'):
                        ticker = data['data']
                        if ticker.get('symbol') == symbol:
                            # Если пара торгуется, предполагаем доступность
                            volume = float(ticker.get('volValue', 0) or 0)
                            confidence = min(1.0, volume / 200000)
                            
                            return LiquidityStatus(
                                symbol=symbol,
                                exchange='kucoin',
                                deposit_enabled=True,
                                withdraw_enabled=True,
                                deposit_min=0.0,
                                withdraw_min=0.0,
                                withdraw_fee=0.0,
                                network_status='normal' if volume > 20000 else 'limited',
                                last_checked=datetime.now(),
                                confidence=confidence
                            )
                            
        except Exception as e:
            logger.warning(f"Ошибка проверки ликвидности KuCoin для {symbol}: {e}")
        
        return None

    async def check_mexc_liquidity(self, symbol: str) -> Optional[LiquidityStatus]:
        """Проверка ликвидности на MEXC (упрощенная)"""
        try:
            # MEXC не предоставляет подробную информацию через публичное API
            # Делаем базовую проверку через ticker
            url = f'https://api.mexc.com/api/v3/ticker/24hr?symbol={symbol}'
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('symbol') == symbol:
                        # Если пара торгуется, предполагаем что депозиты/выводы доступны
                        return LiquidityStatus(
                            symbol=symbol,
                            exchange='mexc',
                            deposit_enabled=True,  # Предположение
                            withdraw_enabled=True,  # Предположение
                            deposit_min=0.0,
                            withdraw_min=0.0,
                            withdraw_fee=0.0,
                            network_status='unknown',
                            last_checked=datetime.now(),
                            confidence=0.5  # Низкая уверенность из-за отсутствия точных данных
                        )
                        
        except Exception as e:
            logger.warning(f"Ошибка проверки ликвидности MEXC для {symbol}: {e}")
        
        return None

    async def get_liquidity_status(self, symbol: str, exchange: str) -> Optional[LiquidityStatus]:
        """Получение статуса ликвидности для символа на бирже"""
        cache_key = self.get_cache_key(symbol, exchange)
        
        # Проверяем кеш
        if self.is_cache_valid(cache_key):
            return self.liquidity_cache[cache_key]
        
        # Получаем новые данные
        liquidity_status = None
        
        if exchange == 'binance':
            liquidity_status = await self.check_binance_liquidity(symbol)
        elif exchange == 'bybit':
            liquidity_status = await self.check_bybit_liquidity(symbol)
        elif exchange == 'okx':
            liquidity_status = await self.check_okx_liquidity(symbol)
        elif exchange == 'kucoin':
            liquidity_status = await self.check_kucoin_liquidity(symbol)
        elif exchange == 'mexc':
            liquidity_status = await self.check_mexc_liquidity(symbol)
        
        # Сохраняем в кеш
        if liquidity_status:
            self.liquidity_cache[cache_key] = liquidity_status
        
        return liquidity_status

    async def check_arbitrage_liquidity(self, symbol: str, buy_exchange: str, sell_exchange: str) -> ArbitrageLiquidity:
        """Проверка ликвидности для арбитражной возможности"""
        
        # Получаем статусы ликвидности для обеих бирж
        buy_liquidity = await self.get_liquidity_status(symbol, buy_exchange)
        sell_liquidity = await self.get_liquidity_status(symbol, sell_exchange)
        
        # Анализируем возможность выполнения арбитража
        is_viable = False
        risk_level = 'high'
        estimated_time = 120  # По умолчанию 2 часа
        
        if buy_liquidity and sell_liquidity:
            # Для арбитража КРИТИЧЕСКИ важны депозиты на биржу покупки и выводы с биржи продажи
            can_deposit_to_buy = buy_liquidity.deposit_enabled
            can_withdraw_from_sell = sell_liquidity.withdraw_enabled
            
            # Арбитраж возможен только если можно внести на биржу покупки И вывести с биржи продажи
            if can_deposit_to_buy and can_withdraw_from_sell:
                is_viable = True
                
                # Определяем уровень риска на основе статусов и уверенности
                avg_confidence = (buy_liquidity.confidence + sell_liquidity.confidence) / 2
                
                if (buy_liquidity.network_status == 'normal' and 
                    sell_liquidity.network_status == 'normal' and
                    avg_confidence > 0.7):
                    risk_level = 'low'
                    estimated_time = 30  # 30 минут для низкого риска
                elif (buy_liquidity.network_status != 'suspended' and 
                      sell_liquidity.network_status != 'suspended' and
                      avg_confidence > 0.4):
                    risk_level = 'medium'
                    estimated_time = 60  # 1 час для среднего риска
                else:
                    risk_level = 'high'
                    estimated_time = 180  # 3 часа для высокого риска
            else:
                is_viable = False
                risk_level = 'high'
                estimated_time = 999  # Недоступно
                
                # Логируем причину недоступности
                if not can_deposit_to_buy:
                    logger.debug(f"❌ {symbol}: депозиты заблокированы на {buy_exchange}")
                if not can_withdraw_from_sell:
                    logger.debug(f"❌ {symbol}: выводы заблокированы на {sell_exchange}")
        else:
            is_viable = False
            risk_level = 'high'
            estimated_time = 999
        
        return ArbitrageLiquidity(
            symbol=symbol,
            buy_exchange=buy_exchange,
            sell_exchange=sell_exchange,
            buy_liquidity=buy_liquidity,
            sell_liquidity=sell_liquidity,
            is_viable=is_viable,
            risk_level=risk_level,
            estimated_time=estimated_time
        )

    def format_liquidity_info(self, liquidity: ArbitrageLiquidity) -> str:
        """Форматирование информации о ликвидности"""
        if not liquidity.is_viable:
            return "❌ НЕДОСТУПНО"
        
        risk_emoji = {
            'low': '🟢',
            'medium': '🟡', 
            'high': '🔴'
        }
        
        info = f"{risk_emoji.get(liquidity.risk_level, '⚪')} {liquidity.risk_level.upper()}"
        
        if liquidity.buy_liquidity and liquidity.sell_liquidity:
            buy_status = "✅" if liquidity.buy_liquidity.deposit_enabled else "❌"
            sell_status = "✅" if liquidity.sell_liquidity.withdraw_enabled else "❌"
            
            info += f" | Депозит: {buy_status} | Вывод: {sell_status}"
            
            if liquidity.estimated_time < 60:
                info += f" | ~{liquidity.estimated_time}мин"
            else:
                info += f" | ~{liquidity.estimated_time//60}ч"
        
        return info

    async def get_liquidity_summary(self) -> Dict[str, int]:
        """Получение сводки по ликвидности"""
        summary = {
            'total_checked': len(self.liquidity_cache),
            'viable_pairs': 0,
            'low_risk': 0,
            'medium_risk': 0,
            'high_risk': 0,
            'cache_hits': 0
        }
        
        for liquidity_status in self.liquidity_cache.values():
            if liquidity_status.deposit_enabled and liquidity_status.withdraw_enabled:
                summary['viable_pairs'] += 1
                
                if liquidity_status.confidence > 0.8:
                    summary['low_risk'] += 1
                elif liquidity_status.confidence > 0.6:
                    summary['medium_risk'] += 1
                else:
                    summary['high_risk'] += 1
        
        return summary

# Глобальный экземпляр для использования в других модулях
liquidity_checker = LiquidityChecker()

async def main():
    """Тестирование модуля ликвидности"""
    checker = LiquidityChecker()
    await checker.start_session()
    
    try:
        # Тестируем несколько популярных пар
        test_pairs = [
            ('BTCUSDT', 'binance', 'bybit'),
            ('ETHUSDT', 'okx', 'kucoin'),
            ('ADAUSDT', 'binance', 'mexc')
        ]
        
        for symbol, buy_exchange, sell_exchange in test_pairs:
            print(f"\n🔍 Проверка ликвидности для {symbol}: {buy_exchange} → {sell_exchange}")
            
            liquidity = await checker.check_arbitrage_liquidity(symbol, buy_exchange, sell_exchange)
            
            print(f"Результат: {checker.format_liquidity_info(liquidity)}")
            
            if liquidity.buy_liquidity:
                print(f"  Покупка ({buy_exchange}): депозит {'✅' if liquidity.buy_liquidity.deposit_enabled else '❌'}")
            
            if liquidity.sell_liquidity:
                print(f"  Продажа ({sell_exchange}): вывод {'✅' if liquidity.sell_liquidity.withdraw_enabled else '❌'}")
        
        # Показываем сводку
        summary = await checker.get_liquidity_summary()
        print(f"\n📊 Сводка ликвидности:")
        print(f"  Проверено пар: {summary['total_checked']}")
        print(f"  Доступных: {summary['viable_pairs']}")
        print(f"  Низкий риск: {summary['low_risk']}")
        print(f"  Средний риск: {summary['medium_risk']}")
        print(f"  Высокий риск: {summary['high_risk']}")
        
    finally:
        await checker.close_session()

if __name__ == "__main__":
    asyncio.run(main())