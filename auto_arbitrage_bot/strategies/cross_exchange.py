#!/usr/bin/env python3
"""
Стратегия межбиржевого арбитража
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from itertools import combinations

# Добавляем путь к модулям
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from config import config
from models import ArbitrageType, ArbitrageOpportunity
from utils.logger import get_logger

class CrossExchangeStrategy:
    """Стратегия межбиржевого арбитража"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.min_profit_threshold = config.arbitrage.min_profit_threshold
        self.max_slippage = config.arbitrage.max_slippage
    
    async def find_opportunities(self, market_data: Dict[str, Dict]) -> List[ArbitrageOpportunity]:
        """Поиск возможностей межбиржевого арбитража"""
        opportunities = []
        
        try:
            # Получение всех уникальных символов
            all_symbols = set()
            for exchange_data in market_data.values():
                all_symbols.update(exchange_data.keys())
            
            # Поиск арбитража для каждого символа
            for symbol in all_symbols:
                symbol_opportunities = await self._find_symbol_opportunities(symbol, market_data)
                opportunities.extend(symbol_opportunities)
            
            self.logger.info(f"💡 Найдено {len(opportunities)} межбиржевых возможностей")
            return opportunities
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка поиска межбиржевого арбитража: {e}")
            return []
    
    async def _find_symbol_opportunities(self, symbol: str, market_data: Dict[str, Dict]) -> List[ArbitrageOpportunity]:
        """Поиск возможностей для конкретного символа"""
        opportunities = []
        
        # Сбор данных по символу со всех бирж
        exchange_prices = {}
        for exchange_name, exchange_data in market_data.items():
            if symbol in exchange_data:
                ticker = exchange_data[symbol]
                if ticker['bid'] and ticker['ask'] and ticker['volume']:
                    exchange_prices[exchange_name] = {
                        'bid': ticker['bid'],
                        'ask': ticker['ask'],
                        'volume': ticker['volume'],
                        'timestamp': ticker['timestamp']
                    }
        
        # Нужно минимум 2 биржи для арбитража
        if len(exchange_prices) < 2:
            return opportunities
        
        # Поиск арбитража между всеми парами бирж
        for buy_exchange, sell_exchange in combinations(exchange_prices.keys(), 2):
            # Проверяем оба направления
            opp1 = await self._calculate_arbitrage(
                symbol, buy_exchange, sell_exchange, exchange_prices
            )
            if opp1:
                opportunities.append(opp1)
            
            opp2 = await self._calculate_arbitrage(
                symbol, sell_exchange, buy_exchange, exchange_prices
            )
            if opp2:
                opportunities.append(opp2)
        
        return opportunities
    
    async def _calculate_arbitrage(self, symbol: str, buy_exchange: str, sell_exchange: str, 
                                 exchange_prices: Dict) -> Optional[ArbitrageOpportunity]:
        """Расчет арбитража между двумя биржами"""
        try:
            buy_data = exchange_prices[buy_exchange]
            sell_data = exchange_prices[sell_exchange]
            
            # Цена покупки (ask на бирже покупки)
            buy_price = buy_data['ask']
            # Цена продажи (bid на бирже продажи)
            sell_price = sell_data['bid']
            
            if not buy_price or not sell_price or buy_price <= 0 or sell_price <= 0:
                return None
            
            # Расчет прибыли
            profit_percent = ((sell_price - buy_price) / buy_price) * 100
            
            # Проверка минимального порога прибыли
            if profit_percent < self.min_profit_threshold:
                return None
            
            # Расчет объемов
            buy_volume = buy_data['volume']
            sell_volume = sell_data['volume']
            min_volume = min(buy_volume, sell_volume)
            
            # Проверка минимального объема
            if min_volume < 1000:  # Минимум $1000 объема
                return None
            
            # Расчет ожидаемой прибыли в USD
            trade_amount = min(config.arbitrage.max_position_size, min_volume * 0.1)  # 10% от объема
            profit_usd = trade_amount * (profit_percent / 100)
            
            # Оценка уверенности
            confidence = await self._calculate_confidence(
                buy_data, sell_data, profit_percent
            )
            
            # Оценка риска
            risk_score = await self._calculate_risk_score(
                symbol, buy_exchange, sell_exchange, profit_percent
            )
            
            return ArbitrageOpportunity(
                type=ArbitrageType.CROSS_EXCHANGE,
                symbol=symbol,
                profit_percent=profit_percent,
                profit_usd=profit_usd,
                exchanges=[buy_exchange, sell_exchange],
                prices={
                    buy_exchange: buy_price,
                    sell_exchange: sell_price
                },
                volumes={
                    buy_exchange: buy_volume,
                    sell_exchange: sell_volume
                },
                timestamp=datetime.now(),
                confidence=confidence,
                risk_score=risk_score
            )
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка расчета арбитража {symbol}: {e}")
            return None
    
    async def _calculate_confidence(self, buy_data: Dict, sell_data: Dict, profit_percent: float) -> float:
        """Расчет уверенности в возможности"""
        confidence = 1.0
        
        # Снижение уверенности при высокой прибыли (может быть ошибка данных)
        if profit_percent > 5.0:
            confidence *= 0.7
        elif profit_percent > 2.0:
            confidence *= 0.9
        
        # Проверка свежести данных
        now = datetime.now()
        buy_age = (now.timestamp() - buy_data['timestamp'] / 1000) if buy_data['timestamp'] else 60
        sell_age = (now.timestamp() - sell_data['timestamp'] / 1000) if sell_data['timestamp'] else 60
        
        max_age = max(buy_age, sell_age)
        if max_age > 30:  # Данные старше 30 секунд
            confidence *= 0.5
        elif max_age > 10:  # Данные старше 10 секунд
            confidence *= 0.8
        
        # Проверка объемов
        min_volume = min(buy_data['volume'], sell_data['volume'])
        if min_volume < 5000:  # Низкий объем
            confidence *= 0.6
        elif min_volume < 10000:
            confidence *= 0.8
        
        return max(confidence, 0.1)  # Минимальная уверенность 10%
    
    async def _calculate_risk_score(self, symbol: str, buy_exchange: str, 
                                  sell_exchange: str, profit_percent: float) -> float:
        """Расчет оценки риска"""
        risk_score = 0.0
        
        # Базовый риск по символу
        base_currency = symbol.split('/')[0]
        if base_currency in ['BTC', 'ETH', 'BNB']:
            risk_score += 0.1  # Низкий риск для топ-монет
        elif base_currency in ['ADA', 'SOL', 'XRP', 'DOT']:
            risk_score += 0.2  # Средний риск
        else:
            risk_score += 0.4  # Высокий риск для остальных
        
        # Риск по биржам
        reliable_exchanges = ['binance', 'bybit', 'okx']
        if buy_exchange not in reliable_exchanges:
            risk_score += 0.2
        if sell_exchange not in reliable_exchanges:
            risk_score += 0.2
        
        # Риск по размеру прибыли (слишком высокая прибыль подозрительна)
        if profit_percent > 10.0:
            risk_score += 0.5
        elif profit_percent > 5.0:
            risk_score += 0.3
        elif profit_percent > 2.0:
            risk_score += 0.1
        
        return min(risk_score, 1.0)  # Максимальный риск 100%
    
    async def execute(self, opportunity: ArbitrageOpportunity, order_executor):
        """Исполнение межбиржевого арбитража"""
        self.logger.info(f"🎯 Исполнение межбиржевого арбитража: {opportunity}")
        
        try:
            # Делегирование исполнения order_executor
            result = await order_executor.execute_cross_exchange_arbitrage(opportunity)
            
            if result.success:
                self.logger.info(f"✅ Успешный межбиржевой арбитраж: ${result.profit_usd:.2f}")
            else:
                self.logger.warning(f"❌ Неудачный межбиржевой арбитраж: {result.error}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка исполнения межбиржевого арбитража: {e}")
            from core.order_executor import TradeResult
            return TradeResult(
                success=False,
                profit_usd=0.0,
                profit_percent=0.0,
                symbol=opportunity.symbol,
                arbitrage_type="cross_exchange",
                orders=[],
                execution_time=0.0,
                error=str(e)
            )
    
    def get_strategy_info(self) -> Dict:
        """Информация о стратегии"""
        return {
            'name': 'Cross-Exchange Arbitrage',
            'description': 'Арбитраж между различными биржами',
            'min_profit_threshold': self.min_profit_threshold,
            'max_slippage': self.max_slippage,
            'supported_exchanges': list(config.exchanges.keys())
        }