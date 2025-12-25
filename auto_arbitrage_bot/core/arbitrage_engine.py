#!/usr/bin/env python3
"""
Основной движок арбитража
Координирует поиск возможностей и исполнение сделок
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

# Добавляем путь к модулям
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from config import config
from models import ArbitrageType, ArbitrageOpportunity
from core.exchange_manager import ExchangeManager
from core.risk_manager import RiskManager
from core.order_executor import OrderExecutor
from strategies.cross_exchange import CrossExchangeStrategy
from strategies.triangular import TriangularStrategy
from utils.logger import get_logger
from utils.notifications import NotificationManager

class ArbitrageEngine:
    """Главный движок арбитража"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.exchange_manager = ExchangeManager()
        self.risk_manager = RiskManager()
        self.order_executor = OrderExecutor()
        self.notification_manager = NotificationManager()
        
        # Стратегии арбитража
        self.strategies = {
            ArbitrageType.CROSS_EXCHANGE: CrossExchangeStrategy(),
            ArbitrageType.TRIANGULAR: TriangularStrategy()
        }
        
        # Состояние системы
        self.is_running = False
        self.active_positions = {}
        self.daily_pnl = 0.0
        self.total_trades = 0
        self.successful_trades = 0
        
        # Статистика
        self.stats = {
            'opportunities_found': 0,
            'opportunities_executed': 0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'avg_profit_percent': 0.0,
            'success_rate': 0.0
        }
    
    async def start(self):
        """Запуск движка арбитража"""
        self.logger.info("🚀 Запуск арбитражного движка...")
        
        try:
            # Инициализация компонентов
            await self.exchange_manager.initialize()
            await self.risk_manager.initialize()
            await self.order_executor.initialize()
            
            # Проверка конфигурации
            errors = config.validate()
            if errors:
                for error in errors:
                    self.logger.error(f"❌ Ошибка конфигурации: {error}")
                raise ValueError("Некорректная конфигурация")
            
            # Проверка подключения к биржам
            connected_exchanges = await self.exchange_manager.test_connections()
            if not connected_exchanges:
                raise ConnectionError("Не удалось подключиться ни к одной бирже")
            
            self.logger.info(f"✅ Подключено к биржам: {', '.join(connected_exchanges)}")
            
            # Уведомление о запуске
            await self.notification_manager.send_message(
                f"🚀 Арбитражный бот запущен\n"
                f"Режим: {config.trading_mode.value}\n"
                f"Биржи: {', '.join(connected_exchanges)}\n"
                f"Минимальная прибыль: {config.arbitrage.min_profit_threshold}%"
            )
            
            self.is_running = True
            
            # Запуск основного цикла
            await self._main_loop()
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка запуска: {e}")
            await self.notification_manager.send_message(f"❌ Ошибка запуска бота: {e}")
            raise
    
    async def stop(self):
        """Остановка движка"""
        self.logger.info("🛑 Остановка арбитражного движка...")
        self.is_running = False
        
        # Закрытие всех позиций
        await self._close_all_positions()
        
        # Отключение от бирж
        await self.exchange_manager.disconnect()
        
        # Финальная статистика
        await self._send_daily_report()
        
        self.logger.info("✅ Арбитражный движок остановлен")
    
    async def _main_loop(self):
        """Основной цикл поиска и исполнения арбитража"""
        self.logger.info("🔄 Запуск основного цикла арбитража...")
        
        while self.is_running:
            try:
                # Проверка рисков
                if not await self.risk_manager.can_trade():
                    self.logger.warning("⚠️ Торговля приостановлена из-за рисков")
                    await asyncio.sleep(60)
                    continue
                
                # Поиск возможностей арбитража
                opportunities = await self._find_opportunities()
                
                if opportunities:
                    self.logger.info(f"💡 Найдено {len(opportunities)} возможностей")
                    
                    # Фильтрация и ранжирование
                    filtered_opportunities = await self._filter_opportunities(opportunities)
                    
                    # Исполнение лучших возможностей
                    for opportunity in filtered_opportunities[:3]:  # Топ-3
                        if await self._execute_opportunity(opportunity):
                            self.stats['opportunities_executed'] += 1
                
                # Мониторинг активных позиций
                await self._monitor_positions()
                
                # Пауза между циклами
                await asyncio.sleep(5)
                
            except Exception as e:
                self.logger.error(f"❌ Ошибка в основном цикле: {e}")
                await asyncio.sleep(10)
    
    async def _find_opportunities(self) -> List[ArbitrageOpportunity]:
        """Поиск арбитражных возможностей"""
        opportunities = []
        
        # Получение данных с бирж
        market_data = await self.exchange_manager.get_market_data()
        
        # Поиск по каждой стратегии
        for arbitrage_type, strategy in self.strategies.items():
            if arbitrage_type in config.arbitrage.enabled_types:
                try:
                    strategy_opportunities = await strategy.find_opportunities(market_data)
                    opportunities.extend(strategy_opportunities)
                    self.stats['opportunities_found'] += len(strategy_opportunities)
                except Exception as e:
                    self.logger.error(f"❌ Ошибка в стратегии {arbitrage_type.value}: {e}")
        
        return opportunities
    
    async def _filter_opportunities(self, opportunities: List[ArbitrageOpportunity]) -> List[ArbitrageOpportunity]:
        """Фильтрация и ранжирование возможностей"""
        filtered = []
        
        for opp in opportunities:
            # Проверка минимальной прибыли
            if opp.profit_percent < config.arbitrage.min_profit_threshold:
                continue
            
            # Проверка рисков
            if not await self.risk_manager.assess_opportunity(opp):
                continue
            
            # Проверка ликвидности
            if not await self.exchange_manager.check_liquidity(opp):
                continue
            
            filtered.append(opp)
        
        # Сортировка по прибыльности и уверенности
        filtered.sort(key=lambda x: (x.profit_percent * x.confidence), reverse=True)
        
        return filtered
    
    async def _execute_opportunity(self, opportunity: ArbitrageOpportunity) -> bool:
        """Исполнение арбитражной возможности"""
        self.logger.info(f"🎯 Исполнение: {opportunity}")
        
        try:
            # Проверка перед исполнением
            if not await self.risk_manager.pre_trade_check(opportunity):
                self.logger.warning(f"⚠️ Отклонено риск-менеджером: {opportunity}")
                return False
            
            # Исполнение через стратегию
            strategy = self.strategies[opportunity.type]
            result = await strategy.execute(opportunity, self.order_executor)
            
            if result.success:
                self.successful_trades += 1
                self.daily_pnl += result.profit_usd
                self.stats['total_profit'] += result.profit_usd
                
                # Уведомление об успешной сделке
                await self.notification_manager.send_message(
                    f"✅ Успешный арбитраж!\n"
                    f"Тип: {opportunity.type.value}\n"
                    f"Символ: {opportunity.symbol}\n"
                    f"Прибыль: {result.profit_percent:.2f}% (${result.profit_usd:.2f})\n"
                    f"Биржи: {', '.join(opportunity.exchanges)}"
                )
                
                self.logger.info(f"✅ Успешно исполнено: {result.profit_usd:.2f} USD")
                return True
            else:
                self.stats['total_loss'] += abs(result.profit_usd)
                self.logger.warning(f"❌ Неудачное исполнение: {result.error}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка исполнения {opportunity}: {e}")
            return False
        finally:
            self.total_trades += 1
            self._update_stats()
    
    async def _monitor_positions(self):
        """Мониторинг активных позиций"""
        if not self.active_positions:
            return
        
        for position_id, position in list(self.active_positions.items()):
            try:
                # Проверка статуса позиции
                status = await self.order_executor.get_position_status(position_id)
                
                # Обновление позиции
                if status.is_closed:
                    del self.active_positions[position_id]
                    self.logger.info(f"📊 Позиция закрыта: {position_id}")
                
            except Exception as e:
                self.logger.error(f"❌ Ошибка мониторинга позиции {position_id}: {e}")
    
    async def _close_all_positions(self):
        """Закрытие всех активных позиций"""
        if not self.active_positions:
            return
        
        self.logger.info(f"🔒 Закрытие {len(self.active_positions)} активных позиций...")
        
        for position_id in list(self.active_positions.keys()):
            try:
                await self.order_executor.close_position(position_id)
                self.logger.info(f"✅ Позиция {position_id} закрыта")
            except Exception as e:
                self.logger.error(f"❌ Ошибка закрытия позиции {position_id}: {e}")
        
        self.active_positions.clear()
    
    def _update_stats(self):
        """Обновление статистики"""
        if self.total_trades > 0:
            self.stats['success_rate'] = (self.successful_trades / self.total_trades) * 100
            self.stats['avg_profit_percent'] = (
                self.stats['total_profit'] / self.total_trades 
                if self.total_trades > 0 else 0
            )
    
    async def _send_daily_report(self):
        """Отправка дневного отчета"""
        report = (
            f"📊 Дневной отчет арбитража\n"
            f"Всего сделок: {self.total_trades}\n"
            f"Успешных: {self.successful_trades}\n"
            f"Успешность: {self.stats['success_rate']:.1f}%\n"
            f"Прибыль: ${self.stats['total_profit']:.2f}\n"
            f"Убытки: ${self.stats['total_loss']:.2f}\n"
            f"Чистая прибыль: ${self.daily_pnl:.2f}\n"
            f"Найдено возможностей: {self.stats['opportunities_found']}\n"
            f"Исполнено: {self.stats['opportunities_executed']}"
        )
        
        await self.notification_manager.send_message(report)
        self.logger.info("📊 Дневной отчет отправлен")
    
    def get_status(self) -> Dict:
        """Получение текущего статуса системы"""
        return {
            'is_running': self.is_running,
            'trading_mode': config.trading_mode.value,
            'active_positions': len(self.active_positions),
            'daily_pnl': self.daily_pnl,
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'stats': self.stats,
            'connected_exchanges': self.exchange_manager.get_connected_exchanges()
        }