#!/usr/bin/env python3
"""
Менеджер рисков - контроль и ограничение торговых рисков
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

# Добавляем путь к модулям
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from config import config
from utils.logger import get_logger

@dataclass
class RiskMetrics:
    """Метрики рисков"""
    daily_pnl: float
    max_drawdown: float
    active_positions: int
    total_exposure: float
    risk_score: float
    
class RiskManager:
    """Менеджер рисков"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Состояние рисков
        self.daily_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_balance = 0.0
        self.active_positions = {}
        self.total_exposure = 0.0
        
        # Лимиты и ограничения
        self.daily_loss_limit = config.risk.max_daily_loss
        self.max_positions = config.risk.max_position_count
        self.max_drawdown_limit = config.risk.max_drawdown_percent
        
        # История сделок
        self.trade_history = []
        self.risk_events = []
        
        # Флаги состояния
        self.trading_enabled = True
        self.emergency_stop = False
        
    async def initialize(self):
        """Инициализация риск-менеджера"""
        self.logger.info("🛡️ Инициализация риск-менеджера...")
        
        # Загрузка истории рисков
        await self._load_risk_data()
        
        # Сброс дневных метрик если новый день
        await self._reset_daily_metrics_if_needed()
        
        self.logger.info("✅ Риск-менеджер инициализирован")
    
    async def can_trade(self) -> bool:
        """Проверка возможности торговли"""
        if self.emergency_stop:
            return False
        
        if not self.trading_enabled:
            return False
        
        # Проверка дневных убытков
        if self.daily_pnl <= -self.daily_loss_limit:
            self.logger.warning(f"⚠️ Достигнут лимит дневных убытков: ${abs(self.daily_pnl):.2f}")
            self.trading_enabled = False
            return False
        
        # Проверка максимальной просадки
        if self.max_drawdown >= self.max_drawdown_limit:
            self.logger.warning(f"⚠️ Достигнут лимит просадки: {self.max_drawdown:.2f}%")
            self.trading_enabled = False
            return False
        
        # Проверка количества позиций
        if len(self.active_positions) >= self.max_positions:
            self.logger.warning(f"⚠️ Достигнут лимит позиций: {len(self.active_positions)}")
            return False
        
        return True
    
    async def assess_opportunity(self, opportunity) -> bool:
        """Оценка арбитражной возможности"""
        try:
            # Базовые проверки
            if opportunity.profit_percent < config.arbitrage.min_profit_threshold:
                return False
            
            # Проверка размера позиции
            position_size = min(
                config.arbitrage.max_position_size,
                opportunity.profit_usd * 10  # Максимум 10x от ожидаемой прибыли
            )
            
            if position_size < 10:  # Минимальный размер $10
                return False
            
            # Проверка общей экспозиции
            if self.total_exposure + position_size > config.arbitrage.max_position_size * 5:
                return False
            
            # Оценка риска по символу
            risk_score = await self._calculate_symbol_risk(opportunity.symbol)
            if risk_score > 0.7:  # Высокий риск
                return False
            
            # Проверка корреляции с активными позициями
            if await self._check_correlation_risk(opportunity):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка оценки возможности: {e}")
            return False
    
    async def pre_trade_check(self, opportunity) -> bool:
        """Проверка перед исполнением сделки"""
        # Финальная проверка возможности торговли
        if not await self.can_trade():
            return False
        
        # Проверка свежести данных
        if not self._is_opportunity_fresh(opportunity):
            return False
        
        # Проверка волатильности
        if await self._is_high_volatility(opportunity.symbol):
            self.logger.warning(f"⚠️ Высокая волатильность для {opportunity.symbol}")
            return False
        
        return True
    
    async def post_trade_update(self, trade_result):
        """Обновление после исполнения сделки"""
        try:
            # Обновление P&L
            self.daily_pnl += trade_result.profit_usd
            
            # Обновление просадки
            if trade_result.profit_usd > 0:
                self.peak_balance = max(self.peak_balance, self.daily_pnl)
            else:
                current_drawdown = ((self.peak_balance - self.daily_pnl) / self.peak_balance) * 100
                self.max_drawdown = max(self.max_drawdown, current_drawdown)
            
            # Добавление в историю
            self.trade_history.append({
                'timestamp': datetime.now(),
                'symbol': trade_result.symbol,
                'profit_usd': trade_result.profit_usd,
                'profit_percent': trade_result.profit_percent,
                'type': trade_result.arbitrage_type
            })
            
            # Сохранение данных
            await self._save_risk_data()
            
            # Проверка на критические события
            await self._check_risk_events()
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка обновления после сделки: {e}")
    
    async def add_position(self, position_id: str, position_data: Dict):
        """Добавление активной позиции"""
        self.active_positions[position_id] = {
            'timestamp': datetime.now(),
            'symbol': position_data['symbol'],
            'size': position_data['size'],
            'exchanges': position_data['exchanges'],
            'entry_price': position_data.get('entry_price', 0),
            'stop_loss': position_data.get('stop_loss'),
            'take_profit': position_data.get('take_profit')
        }
        
        self.total_exposure += position_data['size']
        self.logger.info(f"📊 Добавлена позиция {position_id}: {position_data['symbol']}")
    
    async def remove_position(self, position_id: str):
        """Удаление активной позиции"""
        if position_id in self.active_positions:
            position = self.active_positions[position_id]
            self.total_exposure -= position['size']
            del self.active_positions[position_id]
            self.logger.info(f"📊 Удалена позиция {position_id}")
    
    async def emergency_stop_all(self, reason: str):
        """Экстренная остановка всех операций"""
        self.logger.critical(f"🚨 ЭКСТРЕННАЯ ОСТАНОВКА: {reason}")
        
        self.emergency_stop = True
        self.trading_enabled = False
        
        # Запись события
        self.risk_events.append({
            'timestamp': datetime.now(),
            'type': 'emergency_stop',
            'reason': reason,
            'daily_pnl': self.daily_pnl,
            'max_drawdown': self.max_drawdown
        })
        
        await self._save_risk_data()
    
    async def _calculate_symbol_risk(self, symbol: str) -> float:
        """Расчет риска по символу"""
        try:
            # Базовый риск по типу актива
            base_currency = symbol.split('/')[0]
            
            # Низкий риск для топ-10 монет
            low_risk_coins = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'AVAX', 'MATIC', 'LINK']
            if base_currency in low_risk_coins:
                return 0.2
            
            # Средний риск для топ-50
            medium_risk_coins = ['UNI', 'LTC', 'BCH', 'ATOM', 'FIL', 'ALGO', 'VET', 'ICP', 'THETA', 'TRX']
            if base_currency in medium_risk_coins:
                return 0.4
            
            # Высокий риск для остальных
            return 0.8
            
        except Exception:
            return 0.9  # Максимальный риск при ошибке
    
    async def _check_correlation_risk(self, opportunity) -> bool:
        """Проверка корреляционного риска"""
        symbol = opportunity.symbol
        base_currency = symbol.split('/')[0]
        
        # Подсчет позиций с тем же базовым активом
        same_base_count = 0
        for pos in self.active_positions.values():
            if pos['symbol'].startswith(base_currency):
                same_base_count += 1
        
        # Ограничение на 2 позиции с одним базовым активом
        return same_base_count >= 2
    
    def _is_opportunity_fresh(self, opportunity, max_age_seconds: int = 10) -> bool:
        """Проверка свежести возможности"""
        age = datetime.now() - opportunity.timestamp
        return age.total_seconds() <= max_age_seconds
    
    async def _is_high_volatility(self, symbol: str) -> bool:
        """Проверка высокой волатильности"""
        # Простая проверка - можно расширить анализом исторических данных
        volatile_symbols = ['DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT']
        return symbol in volatile_symbols
    
    async def _check_risk_events(self):
        """Проверка критических событий"""
        # Проверка серии убыточных сделок
        recent_trades = [t for t in self.trade_history if 
                        datetime.now() - t['timestamp'] <= timedelta(hours=1)]
        
        if len(recent_trades) >= 5:
            losing_trades = [t for t in recent_trades if t['profit_usd'] < 0]
            if len(losing_trades) >= 4:  # 4 из 5 убыточных
                await self.emergency_stop_all("Серия убыточных сделок")
    
    async def _reset_daily_metrics_if_needed(self):
        """Сброс дневных метрик если новый день"""
        # Простая проверка - можно улучшить
        # В реальной системе нужно учитывать часовой пояс
        pass
    
    async def _load_risk_data(self):
        """Загрузка данных рисков"""
        try:
            # В реальной системе загрузка из базы данных
            pass
        except Exception as e:
            self.logger.warning(f"⚠️ Не удалось загрузить данные рисков: {e}")
    
    async def _save_risk_data(self):
        """Сохранение данных рисков"""
        try:
            # В реальной системе сохранение в базу данных
            pass
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения данных рисков: {e}")
    
    def get_risk_metrics(self) -> RiskMetrics:
        """Получение текущих метрик рисков"""
        risk_score = 0.0
        
        # Расчет общего риска
        if self.daily_pnl < 0:
            risk_score += abs(self.daily_pnl) / self.daily_loss_limit * 0.4
        
        risk_score += self.max_drawdown / self.max_drawdown_limit * 0.3
        risk_score += len(self.active_positions) / self.max_positions * 0.3
        
        return RiskMetrics(
            daily_pnl=self.daily_pnl,
            max_drawdown=self.max_drawdown,
            active_positions=len(self.active_positions),
            total_exposure=self.total_exposure,
            risk_score=min(risk_score, 1.0)
        )
    
    def get_status(self) -> Dict:
        """Получение статуса риск-менеджера"""
        return {
            'trading_enabled': self.trading_enabled,
            'emergency_stop': self.emergency_stop,
            'daily_pnl': self.daily_pnl,
            'max_drawdown': self.max_drawdown,
            'active_positions': len(self.active_positions),
            'total_exposure': self.total_exposure,
            'risk_metrics': self.get_risk_metrics().__dict__
        }