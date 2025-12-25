#!/usr/bin/env python3
"""
Базовые тесты системы
"""

import pytest
import asyncio
from datetime import datetime

# Добавляем путь к модулям
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config, TradingMode, ArbitrageType
from core.arbitrage_engine import ArbitrageEngine, ArbitrageOpportunity
from core.exchange_manager import ExchangeManager
from core.risk_manager import RiskManager
from core.order_executor import OrderExecutor

class TestConfiguration:
    """Тесты конфигурации"""
    
    def test_config_loading(self):
        """Тест загрузки конфигурации"""
        assert config is not None
        assert isinstance(config.trading_mode, TradingMode)
        assert config.arbitrage.min_profit_threshold > 0
        assert config.arbitrage.max_position_size > 0
    
    def test_config_validation(self):
        """Тест валидации конфигурации"""
        # В тестовом режиме без API ключей должны быть ошибки
        errors = config.validate()
        assert isinstance(errors, list)
        # В тестовом режиме ошибки допустимы

class TestArbitrageEngine:
    """Тесты движка арбитража"""
    
    @pytest.fixture
    def engine(self):
        """Фикстура движка"""
        return ArbitrageEngine()
    
    def test_engine_creation(self, engine):
        """Тест создания движка"""
        assert engine is not None
        assert not engine.is_running
        assert engine.total_trades == 0
        assert engine.successful_trades == 0
    
    def test_engine_status(self, engine):
        """Тест получения статуса"""
        status = engine.get_status()
        assert isinstance(status, dict)
        assert 'is_running' in status
        assert 'trading_mode' in status
        assert 'total_trades' in status

class TestArbitrageOpportunity:
    """Тесты арбитражных возможностей"""
    
    def test_opportunity_creation(self):
        """Тест создания возможности"""
        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.CROSS_EXCHANGE,
            symbol='BTC/USDT',
            profit_percent=1.5,
            profit_usd=150.0,
            exchanges=['binance', 'bybit'],
            prices={'binance': 45000, 'bybit': 45675},
            volumes={'binance': 10000, 'bybit': 8000},
            timestamp=datetime.now(),
            confidence=0.8,
            risk_score=0.3
        )
        
        assert opportunity.type == ArbitrageType.CROSS_EXCHANGE
        assert opportunity.symbol == 'BTC/USDT'
        assert opportunity.profit_percent == 1.5
        assert len(opportunity.exchanges) == 2
    
    def test_opportunity_string_representation(self):
        """Тест строкового представления"""
        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.TRIANGULAR,
            symbol='BTC/USDT->ETH/BTC->ETH/USDT',
            profit_percent=0.8,
            profit_usd=80.0,
            exchanges=['binance'],
            prices={},
            volumes={},
            timestamp=datetime.now(),
            confidence=0.7,
            risk_score=0.4
        )
        
        str_repr = str(opportunity)
        assert 'triangular' in str_repr
        assert 'BTC/USDT->ETH/BTC->ETH/USDT' in str_repr
        assert '0.80%' in str_repr

class TestExchangeManager:
    """Тесты менеджера бирж"""
    
    @pytest.fixture
    def exchange_manager(self):
        """Фикстура менеджера бирж"""
        return ExchangeManager()
    
    def test_exchange_manager_creation(self, exchange_manager):
        """Тест создания менеджера"""
        assert exchange_manager is not None
        assert isinstance(exchange_manager.exchanges, dict)
        assert isinstance(exchange_manager.market_data, dict)
    
    def test_symbol_validation(self, exchange_manager):
        """Тест валидации символов"""
        # Валидные символы
        assert exchange_manager._is_valid_symbol('BTC/USDT')
        assert exchange_manager._is_valid_symbol('ETH/USDT')
        assert exchange_manager._is_valid_symbol('BNB/USDT')
        
        # Невалидные символы
        assert not exchange_manager._is_valid_symbol('SCAM/USDT')
        assert not exchange_manager._is_valid_symbol('BTC/EUR')
        assert not exchange_manager._is_valid_symbol('INVALID')

class TestRiskManager:
    """Тесты риск-менеджера"""
    
    @pytest.fixture
    def risk_manager(self):
        """Фикстура риск-менеджера"""
        return RiskManager()
    
    def test_risk_manager_creation(self, risk_manager):
        """Тест создания риск-менеджера"""
        assert risk_manager is not None
        assert risk_manager.trading_enabled
        assert not risk_manager.emergency_stop
        assert risk_manager.daily_pnl == 0.0
    
    @pytest.mark.asyncio
    async def test_can_trade(self, risk_manager):
        """Тест проверки возможности торговли"""
        # Изначально торговля разрешена
        can_trade = await risk_manager.can_trade()
        assert can_trade
        
        # После экстренной остановки торговля запрещена
        await risk_manager.emergency_stop_all("Test stop")
        can_trade = await risk_manager.can_trade()
        assert not can_trade
    
    def test_risk_metrics(self, risk_manager):
        """Тест метрик рисков"""
        metrics = risk_manager.get_risk_metrics()
        assert hasattr(metrics, 'daily_pnl')
        assert hasattr(metrics, 'max_drawdown')
        assert hasattr(metrics, 'active_positions')
        assert hasattr(metrics, 'risk_score')

class TestOrderExecutor:
    """Тесты исполнителя ордеров"""
    
    @pytest.fixture
    def order_executor(self):
        """Фикстура исполнителя"""
        return OrderExecutor()
    
    def test_order_executor_creation(self, order_executor):
        """Тест создания исполнителя"""
        assert order_executor is not None
        assert isinstance(order_executor.active_orders, dict)
        assert isinstance(order_executor.completed_orders, dict)
    
    def test_trade_amount_calculation(self, order_executor):
        """Тест расчета размера сделки"""
        # Создаем тестовую возможность
        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.CROSS_EXCHANGE,
            symbol='BTC/USDT',
            profit_percent=1.0,
            profit_usd=100.0,
            exchanges=['binance', 'bybit'],
            prices={},
            volumes={},
            timestamp=datetime.now(),
            confidence=0.8,
            risk_score=0.2
        )
        
        amount = order_executor._calculate_trade_amount(opportunity)
        assert amount > 0
        assert amount <= config.arbitrage.max_position_size

@pytest.mark.asyncio
async def test_integration_basic():
    """Базовый интеграционный тест"""
    # Создание компонентов
    engine = ArbitrageEngine()
    
    # Проверка статуса
    status = engine.get_status()
    assert status['is_running'] == False
    assert status['trading_mode'] == config.trading_mode.value

if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"])