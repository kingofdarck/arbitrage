#!/usr/bin/env python3
"""
Запуск упрощенного треугольного арбитражного бота
Работает с публичными API без необходимости в ключах
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем путь к модулям
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def print_banner():
    """Красивый баннер"""
    print("=" * 60)
    print("🔺 ТРЕУГОЛЬНЫЙ АРБИТРАЖНЫЙ БОТ")
    print("=" * 60)
    print("✨ Только треугольный арбитраж")
    print("⚡ Максимальная скорость исполнения")
    print("🔓 Работает с публичными API")
    print("=" * 60)

def check_dependencies():
    """Проверка зависимостей"""
    print("🔍 Проверка зависимостей...")
    
    try:
        import ccxt
        print("✅ ccxt установлен")
    except ImportError:
        print("❌ ccxt не установлен. Установите: pip install ccxt")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv установлен")
    except ImportError:
        print("⚠️ python-dotenv не установлен (необязательно)")
    
    return True

def test_connection():
    """Тест подключения к биржам"""
    print("\n🔌 Тестирование подключений...")
    
    import ccxt
    
    # Тестируем Binance (публичный API)
    try:
        exchange = ccxt.binance({'enableRateLimit': True})
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"✅ Binance: BTC/USDT = ${ticker['last']:.2f}")
        return 'binance'
    except Exception as e:
        print(f"❌ Binance: {e}")
    
    # Тестируем Bybit (публичный API)
    try:
        exchange = ccxt.bybit({'enableRateLimit': True})
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"✅ Bybit: BTC/USDT = ${ticker['last']:.2f}")
        return 'bybit'
    except Exception as e:
        print(f"❌ Bybit: {e}")
    
    # Тестируем KuCoin (публичный API)
    try:
        exchange = ccxt.kucoin({'enableRateLimit': True})
        ticker = exchange.fetch_ticker('BTC-USDT')
        print(f"✅ KuCoin: BTC-USDT = ${ticker['last']:.2f}")
        return 'kucoin'
    except Exception as e:
        print(f"❌ KuCoin: {e}")
    
    print("❌ Не удалось подключиться ни к одной бирже")
    return None

async def main():
    """Главная функция"""
    print_banner()
    
    # Проверяем зависимости
    if not check_dependencies():
        return
    
    # Тестируем подключение
    working_exchange = test_connection()
    if not working_exchange:
        print("\n❌ Не удалось подключиться к биржам")
        print("🔧 Проверьте интернет-соединение")
        return
    
    print(f"\n🎯 Используем биржу: {working_exchange}")
    
    # Запускаем ультра-быстрый бот
    try:
        print("\n🚀 Запуск треугольного арбитражного бота...")
        from ultra_fast_triangular import UltraFastTriangularBot
        
        bot = UltraFastTriangularBot()
        
        if await bot.initialize():
            await bot.run_ultra_fast()
        else:
            print("❌ Не удалось инициализировать бота")
            
    except KeyboardInterrupt:
        print("\n⏹️ Остановка по запросу пользователя...")
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("🔧 Убедитесь что все файлы на месте")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
    except Exception as e:
        print(f"❌ Фатальная ошибка: {e}")