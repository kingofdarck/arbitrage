#!/usr/bin/env python3
"""
Исполнитель ордеров - выполнение торговых операций
"""

import asyncio
import uuid
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Добавляем путь к модулям
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from config import config
from models import TradingMode
from utils.logger import get_logger

class OrderStatus(Enum):
    """Статусы ордеров"""
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    FAILED = "failed"

class OrderSide(Enum):
    """Стороны ордера"""
    BUY = "buy"
    SELL = "sell"

@dataclass
class Order:
    """Торговый ордер"""
    id: str
    exchange: str
    symbol: str
    side: OrderSide
    amount: float
    price: float
    status: OrderStatus
    filled_amount: float = 0.0
    filled_price: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class TradeResult:
    """Результат торговой операции"""
    success: bool
    profit_usd: float
    profit_percent: float
    symbol: str
    arbitrage_type: str
    orders: List[Order]
    execution_time: float
    error: Optional[str] = None

class OrderExecutor:
    """Исполнитель торговых ордеров"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.active_orders = {}
        self.completed_orders = {}
        self.exchange_manager = None  # Будет установлен при инициализации
        
    async def initialize(self):
        """Инициализация исполнителя"""
        self.logger.info("⚡ Инициализация исполнителя ордеров...")
        
        # Импорт здесь чтобы избежать циклических импортов
        from core.exchange_manager import ExchangeManager
        
        self.logger.info("✅ Исполнитель ордеров инициализирован")
    
    async def execute_cross_exchange_arbitrage(self, opportunity) -> TradeResult:
        """Исполнение межбиржевого арбитража"""
        start_time = datetime.now()
        orders = []
        
        try:
            self.logger.info(f"🔄 Исполнение межбиржевого арбитража: {opportunity}")
            
            # Определение бирж для покупки и продажи
            buy_exchange = opportunity.exchanges[0]  # Дешевая биржа
            sell_exchange = opportunity.exchanges[1]  # Дорогая биржа
            
            symbol = opportunity.symbol
            amount = self._calculate_trade_amount(opportunity)
            
            # Проверка балансов
            if not await self._check_balances(buy_exchange, sell_exchange, symbol, amount):
                return TradeResult(
                    success=False,
                    profit_usd=0.0,
                    profit_percent=0.0,
                    symbol=symbol,
                    arbitrage_type="cross_exchange",
                    orders=[],
                    execution_time=0.0,
                    error="Недостаточно средств"
                )
            
            if config.trading_mode == TradingMode.TEST:
                # Симуляция в тестовом режиме
                return await self._simulate_cross_exchange_trade(opportunity, amount)
            
            # Одновременное исполнение ордеров
            buy_task = asyncio.create_task(
                self._place_market_order(buy_exchange, symbol, OrderSide.BUY, amount)
            )
            sell_task = asyncio.create_task(
                self._place_market_order(sell_exchange, symbol, OrderSide.SELL, amount)
            )
            
            # Ожидание исполнения с таймаутом
            try:
                buy_order, sell_order = await asyncio.wait_for(
                    asyncio.gather(buy_task, sell_task),
                    timeout=config.arbitrage.timeout_seconds
                )
                orders = [buy_order, sell_order]
                
            except asyncio.TimeoutError:
                self.logger.error("⏰ Таймаут исполнения ордеров")
                # Отмена незавершенных ордеров
                await self._cancel_pending_orders([buy_task, sell_task])
                return TradeResult(
                    success=False,
                    profit_usd=0.0,
                    profit_percent=0.0,
                    symbol=symbol,
                    arbitrage_type="cross_exchange",
                    orders=orders,
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    error="Таймаут исполнения"
                )
            
            # Проверка успешности исполнения
            if buy_order.status == OrderStatus.FILLED and sell_order.status == OrderStatus.FILLED:
                # Расчет прибыли
                profit_usd = (sell_order.filled_price - buy_order.filled_price) * buy_order.filled_amount
                profit_percent = (profit_usd / (buy_order.filled_price * buy_order.filled_amount)) * 100
                
                # Вычет комиссий
                profit_usd = await self._subtract_fees(profit_usd, orders)
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return TradeResult(
                    success=True,
                    profit_usd=profit_usd,
                    profit_percent=profit_percent,
                    symbol=symbol,
                    arbitrage_type="cross_exchange",
                    orders=orders,
                    execution_time=execution_time
                )
            else:
                return TradeResult(
                    success=False,
                    profit_usd=0.0,
                    profit_percent=0.0,
                    symbol=symbol,
                    arbitrage_type="cross_exchange",
                    orders=orders,
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    error="Ордеры не исполнены полностью"
                )
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка исполнения межбиржевого арбитража: {e}")
            return TradeResult(
                success=False,
                profit_usd=0.0,
                profit_percent=0.0,
                symbol=opportunity.symbol,
                arbitrage_type="cross_exchange",
                orders=orders,
                execution_time=(datetime.now() - start_time).total_seconds(),
                error=str(e)
            )
    
    async def execute_triangular_arbitrage(self, opportunity) -> TradeResult:
        """Исполнение треугольного арбитража"""
        start_time = datetime.now()
        orders = []
        
        try:
            self.logger.info(f"🔺 Исполнение треугольного арбитража: {opportunity}")
            
            exchange_name = opportunity.exchanges[0]
            symbols = opportunity.symbol.split('->')  # Например: BTC/USDT->ETH/BTC->ETH/USDT
            amount = self._calculate_trade_amount(opportunity)
            
            if config.trading_mode == TradingMode.TEST:
                return await self._simulate_triangular_trade(opportunity, amount)
            
            # Последовательное исполнение треугольного арбитража
            current_amount = amount
            
            for i, symbol in enumerate(symbols):
                side = OrderSide.BUY if i % 2 == 0 else OrderSide.SELL
                
                order = await self._place_market_order(exchange_name, symbol, side, current_amount)
                orders.append(order)
                
                if order.status != OrderStatus.FILLED:
                    # Откат предыдущих операций
                    await self._rollback_triangular_orders(orders[:-1])
                    return TradeResult(
                        success=False,
                        profit_usd=0.0,
                        profit_percent=0.0,
                        symbol=opportunity.symbol,
                        arbitrage_type="triangular",
                        orders=orders,
                        execution_time=(datetime.now() - start_time).total_seconds(),
                        error=f"Ордер {i+1} не исполнен"
                    )
                
                # Обновление количества для следующего ордера
                current_amount = order.filled_amount
            
            # Расчет итоговой прибыли
            initial_value = amount
            final_value = orders[-1].filled_amount * orders[-1].filled_price
            profit_usd = final_value - initial_value
            profit_percent = (profit_usd / initial_value) * 100
            
            # Вычет комиссий
            profit_usd = await self._subtract_fees(profit_usd, orders)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return TradeResult(
                success=True,
                profit_usd=profit_usd,
                profit_percent=profit_percent,
                symbol=opportunity.symbol,
                arbitrage_type="triangular",
                orders=orders,
                execution_time=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка исполнения треугольного арбитража: {e}")
            return TradeResult(
                success=False,
                profit_usd=0.0,
                profit_percent=0.0,
                symbol=opportunity.symbol,
                arbitrage_type="triangular",
                orders=orders,
                execution_time=(datetime.now() - start_time).total_seconds(),
                error=str(e)
            )
    
    async def _place_market_order(self, exchange_name: str, symbol: str, side: OrderSide, amount: float) -> Order:
        """Размещение рыночного ордера"""
        order_id = str(uuid.uuid4())
        
        order = Order(
            id=order_id,
            exchange=exchange_name,
            symbol=symbol,
            side=side,
            amount=amount,
            price=0.0,  # Рыночная цена
            status=OrderStatus.PENDING
        )
        
        try:
            if config.trading_mode == TradingMode.LIVE:
                # Реальное исполнение через биржу
                from core.exchange_manager import ExchangeManager
                exchange_manager = ExchangeManager()
                exchange = exchange_manager.get_exchange(exchange_name)
                
                if not exchange:
                    order.status = OrderStatus.FAILED
                    return order
                
                # Размещение ордера
                result = await exchange.create_market_order(
                    symbol=symbol,
                    side=side.value,
                    amount=amount
                )
                
                order.status = OrderStatus.FILLED if result['status'] == 'closed' else OrderStatus.PARTIAL
                order.filled_amount = result.get('filled', 0)
                order.filled_price = result.get('average', 0)
                
            else:
                # Симуляция для тестового режима
                await asyncio.sleep(0.1)  # Имитация задержки
                order.status = OrderStatus.FILLED
                order.filled_amount = amount
                order.filled_price = 50000.0  # Примерная цена
            
            self.active_orders[order_id] = order
            return order
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка размещения ордера: {e}")
            order.status = OrderStatus.FAILED
            return order
    
    def _calculate_trade_amount(self, opportunity) -> float:
        """Расчет размера сделки"""
        # Базовый размер из конфигурации
        base_amount = config.arbitrage.max_position_size
        
        # Корректировка на основе ожидаемой прибыли
        profit_multiplier = min(opportunity.profit_percent / 1.0, 2.0)  # Максимум 2x
        
        # Корректировка на основе уверенности
        confidence_multiplier = opportunity.confidence
        
        amount = base_amount * profit_multiplier * confidence_multiplier
        
        # Ограничения
        amount = max(amount, 10.0)  # Минимум $10
        amount = min(amount, config.arbitrage.max_position_size)  # Максимум из конфига
        
        return amount
    
    async def _check_balances(self, buy_exchange: str, sell_exchange: str, symbol: str, amount: float) -> bool:
        """Проверка достаточности балансов"""
        try:
            # В реальной системе проверка через exchange_manager
            # Пока возвращаем True для тестирования
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки балансов: {e}")
            return False
    
    async def _subtract_fees(self, profit_usd: float, orders: List[Order]) -> float:
        """Вычет торговых комиссий"""
        total_fees = 0.0
        
        for order in orders:
            # Примерная комиссия 0.1%
            fee = order.filled_amount * order.filled_price * 0.001
            total_fees += fee
        
        return profit_usd - total_fees
    
    async def _simulate_cross_exchange_trade(self, opportunity, amount: float) -> TradeResult:
        """Симуляция межбиржевого арбитража"""
        await asyncio.sleep(0.5)  # Имитация времени исполнения
        
        # Симуляция успешной сделки
        profit_usd = amount * (opportunity.profit_percent / 100)
        
        return TradeResult(
            success=True,
            profit_usd=profit_usd,
            profit_percent=opportunity.profit_percent,
            symbol=opportunity.symbol,
            arbitrage_type="cross_exchange",
            orders=[],
            execution_time=0.5
        )
    
    async def _simulate_triangular_trade(self, opportunity, amount: float) -> TradeResult:
        """Симуляция треугольного арбитража"""
        await asyncio.sleep(1.0)  # Имитация времени исполнения
        
        # Симуляция успешной сделки
        profit_usd = amount * (opportunity.profit_percent / 100)
        
        return TradeResult(
            success=True,
            profit_usd=profit_usd,
            profit_percent=opportunity.profit_percent,
            symbol=opportunity.symbol,
            arbitrage_type="triangular",
            orders=[],
            execution_time=1.0
        )
    
    async def _cancel_pending_orders(self, tasks: List):
        """Отмена незавершенных ордеров"""
        for task in tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    
    async def _rollback_triangular_orders(self, orders: List[Order]):
        """Откат треугольных ордеров"""
        # В реальной системе нужно выполнить обратные операции
        self.logger.warning(f"⚠️ Откат {len(orders)} ордеров треугольного арбитража")
    
    async def get_position_status(self, position_id: str):
        """Получение статуса позиции"""
        # Заглушка для интерфейса
        class PositionStatus:
            def __init__(self):
                self.is_closed = True
        
        return PositionStatus()
    
    async def close_position(self, position_id: str):
        """Закрытие позиции"""
        self.logger.info(f"🔒 Закрытие позиции {position_id}")
        # В реальной системе закрытие через биржи
    
    def get_active_orders(self) -> Dict[str, Order]:
        """Получение активных ордеров"""
        return {oid: order for oid, order in self.active_orders.items() 
                if order.status in [OrderStatus.PENDING, OrderStatus.PARTIAL]}
    
    def get_order_history(self) -> List[Order]:
        """Получение истории ордеров"""
        return list(self.completed_orders.values())