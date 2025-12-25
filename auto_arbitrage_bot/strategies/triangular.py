#!/usr/bin/env python3
"""
Стратегия треугольного арбитража
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from itertools import permutations

# Добавляем путь к модулям
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from config import config
from models import ArbitrageType, ArbitrageOpportunity
from utils.logger import get_logger

class TriangularStrategy:
    """Стратегия треугольного арбитража"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.min_profit_threshold = config.arbitrage.min_profit_threshold
        
        # Основные валюты для треугольного арбитража
        self.base_currencies = [
            'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'AVAX', 
            'MATIC', 'LINK', 'UNI', 'LTC', 'BCH', 'ATOM', 'FIL'
        ]
        self.quote_currencies = ['USDT', 'BUSD', 'USDC']
    
    async def find_opportunities(self, market_data: Dict[str, Dict]) -> List[ArbitrageOpportunity]:
        """Поиск возможностей треугольного арбитража"""
        opportunities = []
        
        try:
            # Поиск на каждой бирже отдельно
            for exchange_name, exchange_data in market_data.items():
                exchange_opportunities = await self._find_exchange_opportunities(
                    exchange_name, exchange_data
                )
                opportunities.extend(exchange_opportunities)
            
            self.logger.info(f"🔺 Найдено {len(opportunities)} треугольных возможностей")
            return opportunities
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка поиска треугольного арбитража: {e}")
            return []
    
    async def _find_exchange_opportunities(self, exchange_name: str, exchange_data: Dict) -> List[ArbitrageOpportunity]:
        """Поиск треугольных возможностей на одной бирже"""
        opportunities = []
        
        # Создание треугольных комбинаций
        triangles = await self._generate_triangles(exchange_data)
        
        for triangle in triangles:
            opportunity = await self._calculate_triangular_arbitrage(
                exchange_name, triangle, exchange_data
            )
            if opportunity:
                opportunities.append(opportunity)
        
        return opportunities
    
    async def _generate_triangles(self, exchange_data: Dict) -> List[Tuple[str, str, str]]:
        """Генерация треугольных комбинаций"""
        triangles = []
        available_symbols = set(exchange_data.keys())
        
        # Генерация всех возможных треугольников
        for base1 in self.base_currencies:
            for base2 in self.base_currencies:
                if base1 == base2:
                    continue
                    
                for quote in self.quote_currencies:
                    # Треугольник: base1/quote -> base1/base2 -> base2/quote
                    pair1 = f"{base1}/{quote}"
                    pair2 = f"{base1}/{base2}"
                    pair3 = f"{base2}/{quote}"
                    
                    # Альтернативный порядок для pair2
                    pair2_alt = f"{base2}/{base1}"
                    
                    if (pair1 in available_symbols and 
                        (pair2 in available_symbols or pair2_alt in available_symbols) and
                        pair3 in available_symbols):
                        
                        actual_pair2 = pair2 if pair2 in available_symbols else pair2_alt
                        triangles.append((pair1, actual_pair2, pair3))
        
        return triangles[:100]  # Ограничиваем количество для производительности
    
    async def _calculate_triangular_arbitrage(self, exchange_name: str, triangle: Tuple[str, str, str], 
                                            exchange_data: Dict) -> Optional[ArbitrageOpportunity]:
        """Расчет треугольного арбитража"""
        try:
            pair1, pair2, pair3 = triangle
            
            # Получение данных по парам
            data1 = exchange_data.get(pair1)
            data2 = exchange_data.get(pair2)
            data3 = exchange_data.get(pair3)
            
            if not all([data1, data2, data3]):
                return None
            
            # Проверка наличия цен
            if not all([data1.get('bid'), data1.get('ask'), 
                       data2.get('bid'), data2.get('ask'),
                       data3.get('bid'), data3.get('ask')]):
                return None
            
            # Расчет прибыли для прямого направления
            profit_percent = await self._calculate_triangle_profit(
                data1, data2, data3, pair1, pair2, pair3
            )
            
            if profit_percent < self.min_profit_threshold:
                return None
            
            # Проверка объемов
            min_volume = min(data1['volume'], data2['volume'], data3['volume'])
            if min_volume < 500:  # Минимальный объем
                return None
            
            # Расчет ожидаемой прибыли в USD
            trade_amount = min(config.arbitrage.max_position_size, min_volume * 0.05)
            profit_usd = trade_amount * (profit_percent / 100)
            
            # Оценка уверенности и риска
            confidence = await self._calculate_triangle_confidence(data1, data2, data3)
            risk_score = await self._calculate_triangle_risk(pair1, pair2, pair3, profit_percent)
            
            return ArbitrageOpportunity(
                type=ArbitrageType.TRIANGULAR,
                symbol=f"{pair1}->{pair2}->{pair3}",
                profit_percent=profit_percent,
                profit_usd=profit_usd,
                exchanges=[exchange_name],
                prices={
                    pair1: data1['ask'],
                    pair2: data2['bid'] if self._is_sell_order(pair1, pair2) else data2['ask'],
                    pair3: data3['bid']
                },
                volumes={
                    pair1: data1['volume'],
                    pair2: data2['volume'],
                    pair3: data3['volume']
                },
                timestamp=datetime.now(),
                confidence=confidence,
                risk_score=risk_score
            )
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка расчета треугольного арбитража: {e}")
            return None
    
    async def _calculate_triangle_profit(self, data1: Dict, data2: Dict, data3: Dict,
                                       pair1: str, pair2: str, pair3: str) -> float:
        """Расчет прибыли треугольного арбитража"""
        try:
            # Начальная сумма в базовой валюте
            initial_amount = 1000.0  # USDT
            
            # Шаг 1: Покупка первой валюты (например, BTC за USDT)
            price1 = data1['ask']  # Цена покупки
            amount_after_step1 = initial_amount / price1
            
            # Шаг 2: Обмен на вторую валюту (например, BTC на ETH)
            if self._is_sell_order(pair1, pair2):
                price2 = data2['bid']  # Продаем BTC за ETH
                amount_after_step2 = amount_after_step1 * price2
            else:
                price2 = data2['ask']  # Покупаем ETH за BTC
                amount_after_step2 = amount_after_step1 / price2
            
            # Шаг 3: Продажа за базовую валюту (например, ETH за USDT)
            price3 = data3['bid']  # Цена продажи
            final_amount = amount_after_step2 * price3
            
            # Расчет прибыли
            profit_percent = ((final_amount - initial_amount) / initial_amount) * 100
            
            return profit_percent
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка расчета прибыли треугольника: {e}")
            return 0.0
    
    def _is_sell_order(self, pair1: str, pair2: str) -> bool:
        """Определение направления ордера"""
        # Логика определения нужно ли продавать или покупать
        base1 = pair1.split('/')[0]
        base2_pair = pair2.split('/')
        
        return base1 in base2_pair
    
    async def _calculate_triangle_confidence(self, data1: Dict, data2: Dict, data3: Dict) -> float:
        """Расчет уверенности для треугольного арбитража"""
        confidence = 1.0
        
        # Проверка свежести данных
        now = datetime.now().timestamp() * 1000
        for data in [data1, data2, data3]:
            if data.get('timestamp'):
                age = (now - data['timestamp']) / 1000
                if age > 30:
                    confidence *= 0.5
                elif age > 10:
                    confidence *= 0.8
        
        # Проверка объемов
        min_volume = min(data1['volume'], data2['volume'], data3['volume'])
        if min_volume < 1000:
            confidence *= 0.6
        elif min_volume < 5000:
            confidence *= 0.8
        
        return max(confidence, 0.1)
    
    async def _calculate_triangle_risk(self, pair1: str, pair2: str, pair3: str, profit_percent: float) -> float:
        """Расчет риска треугольного арбитража"""
        risk_score = 0.0
        
        # Базовый риск треугольного арбитража (выше чем межбиржевого)
        risk_score += 0.3
        
        # Риск по валютам
        all_currencies = set()
        for pair in [pair1, pair2, pair3]:
            base, quote = pair.split('/')
            all_currencies.update([base, quote])
        
        risky_currencies = set(all_currencies) - {'BTC', 'ETH', 'BNB', 'USDT', 'BUSD', 'USDC'}
        risk_score += len(risky_currencies) * 0.1
        
        # Риск по размеру прибыли
        if profit_percent > 5.0:
            risk_score += 0.4
        elif profit_percent > 2.0:
            risk_score += 0.2
        
        return min(risk_score, 1.0)
    
    async def execute(self, opportunity: ArbitrageOpportunity, order_executor):
        """Исполнение треугольного арбитража"""
        self.logger.info(f"🔺 Исполнение треугольного арбитража: {opportunity}")
        
        try:
            result = await order_executor.execute_triangular_arbitrage(opportunity)
            
            if result.success:
                self.logger.info(f"✅ Успешный треугольный арбитраж: ${result.profit_usd:.2f}")
            else:
                self.logger.warning(f"❌ Неудачный треугольный арбитраж: {result.error}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка исполнения треугольного арбитража: {e}")
            from core.order_executor import TradeResult
            return TradeResult(
                success=False,
                profit_usd=0.0,
                profit_percent=0.0,
                symbol=opportunity.symbol,
                arbitrage_type="triangular",
                orders=[],
                execution_time=0.0,
                error=str(e)
            )
    
    def get_strategy_info(self) -> Dict:
        """Информация о стратегии"""
        return {
            'name': 'Triangular Arbitrage',
            'description': 'Треугольный арбитраж внутри одной биржи',
            'min_profit_threshold': self.min_profit_threshold,
            'base_currencies': self.base_currencies,
            'quote_currencies': self.quote_currencies
        }