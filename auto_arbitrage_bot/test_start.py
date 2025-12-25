#!/usr/bin/env python3
"""
Тестовый запуск без бирж
"""

import sys
from pathlib import Path

# Добавляем путь к модулям
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_imports():
    """Тест импортов"""
    try:
        print("🧪 Тестирование импортов...")
        
        from config import config
        print("✅ config импортирован")
        
        from models import TradingMode, ArbitrageType, ArbitrageOpportunity
        print("✅ models импортированы")
        
        from core.arbitrage_engine import ArbitrageEngine
        print("✅ ArbitrageEngine импортирован")
        
        from core.exchange_manager import ExchangeManager
        print("✅ ExchangeManager импортирован")
        
        from core.risk_manager import RiskManager
        print("✅ RiskManager импортирован")
        
        from core.order_executor import OrderExecutor
        print("✅ OrderExecutor импортирован")
        
        from strategies.cross_exchange import CrossExchangeStrategy
        print("✅ CrossExchangeStrategy импортирован")
        
        from strategies.triangular import TriangularStrategy
        print("✅ TriangularStrategy импортирован")
        
        from utils.logger import get_logger
        print("✅ logger импортирован")
        
        from utils.notifications import NotificationManager
        print("✅ NotificationManager импортирован")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_configuration():
    """Тест конфигурации"""
    try:
        print("\n⚙️ Тестирование конфигурации...")
        
        from config import config
        
        print(f"Режим торговли: {config.trading_mode.value}")
        print(f"Минимальная прибыль: {config.arbitrage.min_profit_threshold}%")
        print(f"Максимальная позиция: ${config.arbitrage.max_position_size}")
        
        # Проверка валидации (ожидаем предупреждения в тестовом режиме)
        errors = config.validate()
        if errors:
            print(f"⚠️ Предупреждения конфигурации: {len(errors)}")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✅ Конфигурация корректна")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False

def test_components():
    """Тест компонентов"""
    try:
        print("\n🔧 Тестирование компонентов...")
        
        from core.arbitrage_engine import ArbitrageEngine
        from core.exchange_manager import ExchangeManager
        from core.risk_manager import RiskManager
        from core.order_executor import OrderExecutor
        
        # Создание компонентов
        engine = ArbitrageEngine()
        print("✅ ArbitrageEngine создан")
        
        exchange_manager = ExchangeManager()
        print("✅ ExchangeManager создан")
        
        risk_manager = RiskManager()
        print("✅ RiskManager создан")
        
        order_executor = OrderExecutor()
        print("✅ OrderExecutor создан")
        
        # Проверка статуса
        status = engine.get_status()
        print(f"✅ Статус движка: {status['is_running']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка компонентов: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("🚀 ТЕСТОВЫЙ ЗАПУСК АРБИТРАЖНОГО БОТА")
    print("=" * 50)
    
    success = True
    
    # Тест импортов
    if not test_imports():
        success = False
    
    # Тест конфигурации
    if not test_configuration():
        success = False
    
    # Тест компонентов
    if not test_components():
        success = False
    
    print("\n" + "=" * 50)
    
    if success:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("\n📋 Что дальше:")
        print("1. Добавьте API ключи бирж в .env файл")
        print("2. Запустите: python start.py")
        print("3. Или используйте: python main.py --mode=test")
        return 0
    else:
        print("❌ ЕСТЬ ОШИБКИ В СИСТЕМЕ")
        print("Проверьте сообщения выше и исправьте проблемы")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)