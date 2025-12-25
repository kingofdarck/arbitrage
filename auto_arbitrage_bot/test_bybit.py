#!/usr/bin/env python3
"""
Тест подключения к Bybit
"""

import sys
import asyncio
from pathlib import Path

# Добавляем путь к модулям
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

async def test_bybit_connection():
    """Тест подключения к Bybit"""
    try:
        print("🧪 Тестирование подключения к Bybit...")
        
        # Загружаем конфигурацию
        from config import config
        print(f"✅ Конфигурация загружена")
        
        # Проверяем настройки Bybit
        if 'bybit' not in config.exchanges:
            print("❌ Bybit не найден в конфигурации")
            return False
        
        bybit_config = config.exchanges['bybit']
        print(f"✅ Bybit настройки найдены:")
        print(f"   Включен: {bybit_config.enabled}")
        print(f"   API Key: {bybit_config.api_key[:10]}...")
        print(f"   Secret: {bybit_config.api_secret[:10]}...")
        print(f"   Sandbox: {bybit_config.sandbox}")
        
        if not bybit_config.enabled:
            print("❌ Bybit отключен в настройках")
            return False
        
        # Тестируем подключение через ccxt
        import ccxt
        
        exchange = ccxt.bybit({
            'apiKey': bybit_config.api_key,
            'secret': bybit_config.api_secret,
            'sandbox': bybit_config.sandbox,
            'enableRateLimit': True,
        })
        
        print("🔌 Попытка подключения к Bybit...")
        
        # Загружаем рынки
        markets = await exchange.load_markets()
        print(f"✅ Рынки загружены: {len(markets)} пар")
        
        # Проверяем баланс
        try:
            balance = await exchange.fetch_balance()
            print(f"✅ Баланс получен: {len(balance)} валют")
        except Exception as e:
            print(f"⚠️ Ошибка получения баланса: {e}")
        
        # Проверяем тикер
        try:
            ticker = await exchange.fetch_ticker('BTC/USDT')
            print(f"✅ Тикер BTC/USDT: ${ticker['last']}")
        except Exception as e:
            print(f"⚠️ Ошибка получения тикера: {e}")
        
        await exchange.close()
        print("✅ Подключение к Bybit успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к Bybit: {e}")
        return False

async def test_exchange_manager():
    """Тест через ExchangeManager"""
    try:
        print("\n🔧 Тестирование через ExchangeManager...")
        
        from core.exchange_manager import ExchangeManager
        
        em = ExchangeManager()
        await em.initialize()
        
        connected = await em.test_connections()
        print(f"✅ Подключенные биржи: {connected}")
        
        if 'bybit' in connected:
            print("✅ Bybit подключен через ExchangeManager!")
            return True
        else:
            print("❌ Bybit не подключен через ExchangeManager")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка ExchangeManager: {e}")
        return False

async def main():
    """Главная функция"""
    print("🚀 ДИАГНОСТИКА ПОДКЛЮЧЕНИЯ К BYBIT")
    print("=" * 50)
    
    success1 = await test_bybit_connection()
    success2 = await test_exchange_manager()
    
    print("\n" + "=" * 50)
    
    if success1 and success2:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ! Bybit работает корректно!")
        print("\n📋 Можете запускать основную систему:")
        print("python start.py")
    elif success1:
        print("⚠️ Прямое подключение работает, но есть проблемы с ExchangeManager")
        print("Проверьте логи для деталей")
    else:
        print("❌ ПРОБЛЕМЫ С ПОДКЛЮЧЕНИЕМ К BYBIT")
        print("\n🔧 Возможные причины:")
        print("1. Неправильные API ключи")
        print("2. API ключ не активирован")
        print("3. Нет разрешений для API")
        print("4. IP адрес не в whitelist")
        print("5. Проблемы с интернетом")
        
        print("\n📋 Что проверить:")
        print("1. Зайдите на bybit.com → API Management")
        print("2. Убедитесь что API ключ активен")
        print("3. Проверьте разрешения (Spot Trading)")
        print("4. Добавьте IP в whitelist")

if __name__ == "__main__":
    asyncio.run(main())