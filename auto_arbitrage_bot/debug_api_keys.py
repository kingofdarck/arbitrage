#!/usr/bin/env python3
"""
Отладка API ключей для всех бирж
Проверяем правильность ключей и их формат
"""

import asyncio
import ccxt.pro as ccxt
import os
import sys
from pathlib import Path

# Добавляем путь к модулям
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Загружаем переменные окружения
try:
    from dotenv import load_dotenv
    env_path = current_dir / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Загружен .env файл: {env_path}")
    else:
        print(f"❌ .env файл не найден: {env_path}")
except ImportError:
    print("⚠️ python-dotenv не установлен")

async def test_bybit_api():
    """Тестирование Bybit API"""
    print("\n🔵 ТЕСТИРОВАНИЕ BYBIT API")
    print("=" * 50)
    
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    sandbox = os.getenv('BYBIT_SANDBOX', 'true').lower() == 'true'
    
    print(f"API Key: {api_key}")
    print(f"API Key длина: {len(api_key) if api_key else 0}")
    print(f"Secret: {api_secret}")
    print(f"Secret длина: {len(api_secret) if api_secret else 0}")
    print(f"Sandbox: {sandbox}")
    
    if not api_key or not api_secret:
        print("❌ API ключи не найдены")
        return False
    
    # Проверяем формат ключей
    print(f"\n🔍 АНАЛИЗ ФОРМАТА КЛЮЧЕЙ:")
    print(f"API Key содержит только буквы и цифры: {api_key.isalnum()}")
    print(f"Secret содержит только буквы и цифры: {api_secret.isalnum()}")
    
    # Типичные длины ключей Bybit
    print(f"\n📏 ПРОВЕРКА ДЛИНЫ:")
    print(f"API Key: {len(api_key)} символов (обычно 20-30)")
    print(f"Secret: {len(api_secret)} символов (обычно 40-50)")
    
    if len(api_key) < 20:
        print("⚠️ API Key кажется слишком коротким")
    if len(api_secret) < 30:
        print("⚠️ Secret кажется слишком коротким")
    
    # Тестируем подключение
    try:
        print(f"\n🔌 ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ...")
        
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': sandbox,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
            }
        })
        
        # Тест 1: Загрузка рынков
        print("1️⃣ Загрузка рынков...")
        markets = await exchange.load_markets()
        print(f"✅ Загружено {len(markets)} рынков")
        
        # Тест 2: Получение баланса
        print("2️⃣ Получение баланса...")
        balance = await exchange.fetch_balance()
        print(f"✅ Баланс получен: {len(balance)} валют")
        
        # Показываем ненулевые балансы
        non_zero_balances = {k: v for k, v in balance.items() 
                           if isinstance(v, dict) and v.get('total', 0) > 0}
        if non_zero_balances:
            print("💰 Ненулевые балансы:")
            for currency, info in non_zero_balances.items():
                print(f"   {currency}: {info['total']:.8f}")
        else:
            print("💰 Все балансы нулевые (нормально для тестового режима)")
        
        # Тест 3: Получение тикера
        print("3️⃣ Получение тикера BTC/USDT...")
        ticker = await exchange.fetch_ticker('BTC/USDT')
        print(f"✅ BTC/USDT: ${ticker['last']:.2f}")
        
        await exchange.close()
        print("✅ Bybit API работает корректно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка Bybit API: {e}")
        if exchange:
            await exchange.close()
        return False

async def test_kucoin_api():
    """Тестирование KuCoin API"""
    print("\n🟢 ТЕСТИРОВАНИЕ KUCOIN API")
    print("=" * 50)
    
    api_key = os.getenv('KUCOIN_API_KEY')
    api_secret = os.getenv('KUCOIN_API_SECRET')
    passphrase = os.getenv('KUCOIN_PASSPHRASE')
    sandbox = os.getenv('KUCOIN_SANDBOX', 'false').lower() == 'true'
    
    print(f"API Key: {api_key}")
    print(f"Secret: {api_secret}")
    print(f"Passphrase: {passphrase}")
    print(f"Sandbox: {sandbox}")
    
    if not all([api_key, api_secret, passphrase]):
        print("❌ Не все ключи KuCoin найдены")
        return False
    
    try:
        exchange = ccxt.kucoin({
            'apiKey': api_key,
            'secret': api_secret,
            'password': passphrase,
            'sandbox': sandbox,
            'enableRateLimit': True,
        })
        
        print("🔌 Тестирование подключения...")
        markets = await exchange.load_markets()
        print(f"✅ KuCoin: Загружено {len(markets)} рынков")
        
        balance = await exchange.fetch_balance()
        print(f"✅ KuCoin: Баланс получен")
        
        await exchange.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка KuCoin API: {e}")
        return False

async def test_mexc_api():
    """Тестирование MEXC API"""
    print("\n🔴 ТЕСТИРОВАНИЕ MEXC API")
    print("=" * 50)
    
    api_key = os.getenv('MEXC_API_KEY')
    api_secret = os.getenv('MEXC_API_SECRET')
    sandbox = os.getenv('MEXC_SANDBOX', 'false').lower() == 'true'
    
    print(f"API Key: {api_key}")
    print(f"Secret: {api_secret}")
    print(f"Sandbox: {sandbox}")
    
    if not all([api_key, api_secret]):
        print("❌ Ключи MEXC не найдены")
        return False
    
    try:
        exchange = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': sandbox,
            'enableRateLimit': True,
        })
        
        print("🔌 Тестирование подключения...")
        markets = await exchange.load_markets()
        print(f"✅ MEXC: Загружено {len(markets)} рынков")
        
        await exchange.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка MEXC API: {e}")
        return False

async def main():
    """Главная функция тестирования"""
    print("🔍 ДИАГНОСТИКА API КЛЮЧЕЙ")
    print("=" * 60)
    
    results = {}
    
    # Тестируем все биржи
    results['bybit'] = await test_bybit_api()
    results['kucoin'] = await test_kucoin_api()
    results['mexc'] = await test_mexc_api()
    
    # Итоговый отчет
    print("\n📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    
    working_exchanges = []
    for exchange, status in results.items():
        status_text = "✅ Работает" if status else "❌ Не работает"
        print(f"{exchange.upper()}: {status_text}")
        if status:
            working_exchanges.append(exchange)
    
    print(f"\n🎯 Рабочих бирж: {len(working_exchanges)}")
    if working_exchanges:
        print(f"Доступные биржи: {', '.join(working_exchanges)}")
    else:
        print("❌ Ни одна биржа не работает!")
        print("\n🔧 РЕКОМЕНДАЦИИ:")
        print("1. Проверьте правильность API ключей")
        print("2. Убедитесь что ключи активны")
        print("3. Проверьте разрешения ключей (spot trading)")
        print("4. Проверьте IP whitelist если настроен")
        print("5. Для Bybit: ключи должны быть длиннее")

if __name__ == "__main__":
    asyncio.run(main())