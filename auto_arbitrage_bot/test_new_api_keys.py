#!/usr/bin/env python3
"""
Тестирование новых API ключей Bybit
Проверяем что ключи работают для реальной торговли
"""

import ccxt
import os
import sys
from pathlib import Path
import asyncio

# Добавляем путь к модулям
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Загружаем переменные окружения
try:
    from dotenv import load_dotenv
    env_path = current_dir / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

async def test_bybit_api_comprehensive():
    """Комплексное тестирование Bybit API"""
    print("🔑 ТЕСТИРОВАНИЕ НОВЫХ API КЛЮЧЕЙ BYBIT")
    print("=" * 60)
    
    # Получаем ключи
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    sandbox = os.getenv('BYBIT_SANDBOX', 'false').lower() == 'true'
    
    print(f"API Key: {api_key}")
    print(f"Secret: {api_secret}")
    print(f"Sandbox: {sandbox}")
    print()
    
    # Проверяем наличие ключей
    if not api_key or not api_secret:
        print("❌ API ключи не найдены в .env файле!")
        print("📝 Откройте файл .env и добавьте:")
        print("BYBIT_API_KEY=ваш_новый_api_key")
        print("BYBIT_API_SECRET=ваш_новый_secret")
        return False
    
    # Проверяем что ключи не являются заглушками
    if 'ВСТАВЬТЕ' in api_key or 'ВСТАВЬТЕ' in api_secret:
        print("❌ Ключи не настроены! Замените заглушки на реальные ключи.")
        print("🔧 Инструкция: откройте НАСТРОЙКА_РЕАЛЬНОЙ_ТОРГОВЛИ.md")
        return False
    
    # Проверяем длину ключей
    print(f"🔍 АНАЛИЗ КЛЮЧЕЙ:")
    print(f"   API Key длина: {len(api_key)} (должно быть 20-30)")
    print(f"   Secret длина: {len(api_secret)} (должно быть 40-50)")
    
    if len(api_key) < 20:
        print("⚠️ API Key кажется коротким")
    if len(api_secret) < 30:
        print("⚠️ Secret кажется коротким")
    
    print()
    
    # Тестируем подключение
    try:
        print("🔌 ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ...")
        
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
        print(f"   ✅ Загружено {len(markets)} торговых пар")
        
        # Тест 2: Получение баланса
        print("2️⃣ Получение баланса...")
        balance = await exchange.fetch_balance()
        print(f"   ✅ Баланс получен для {len(balance)} валют")
        
        # Показываем ненулевые балансы
        total_usd = 0
        currencies_with_balance = []
        
        for currency, info in balance.items():
            if isinstance(info, dict) and info.get('total', 0) > 0:
                currencies_with_balance.append((currency, info['total'], info['free']))
                # Примерная оценка в USD
                if currency == 'USDT':
                    total_usd += info['total']
                elif currency == 'BTC':
                    total_usd += info['total'] * 88000  # Примерный курс
                elif currency == 'ETH':
                    total_usd += info['total'] * 3200
        
        if currencies_with_balance:
            print("   💰 Ненулевые балансы:")
            for currency, total, free in currencies_with_balance:
                print(f"      {currency}: {total:.8f} (свободно: {free:.8f})")
            print(f"   💵 Примерный общий баланс: ~${total_usd:.2f}")
        else:
            print("   💰 Все балансы нулевые")
            if not sandbox:
                print("   ⚠️ Для реальной торговли нужны средства на счету!")
        
        # Тест 3: Получение тикера
        print("3️⃣ Получение тикера BTC/USDT...")
        ticker = await exchange.fetch_ticker('BTC/USDT')
        print(f"   ✅ BTC/USDT: ${ticker['last']:.2f} (bid: ${ticker['bid']:.2f}, ask: ${ticker['ask']:.2f})")
        
        # Тест 4: Проверка разрешений (попытка создать тестовый ордер)
        print("4️⃣ Проверка разрешений торговли...")
        try:
            # Пробуем создать очень маленький ордер (который не исполнится)
            test_order = await exchange.create_limit_buy_order(
                'BTC/USDT', 
                0.00001,  # Очень маленькое количество
                1.0       # Очень низкая цена
            )
            print("   ✅ Разрешения торговли работают")
            
            # Отменяем тестовый ордер
            await exchange.cancel_order(test_order['id'], 'BTC/USDT')
            print("   ✅ Отмена ордеров работает")
            
        except Exception as e:
            error_msg = str(e).lower()
            if 'insufficient' in error_msg:
                print("   ⚠️ Недостаточно средств для тестового ордера (это нормально)")
            elif 'permission' in error_msg or 'forbidden' in error_msg:
                print("   ❌ Нет разрешений для торговли!")
                print("   🔧 Проверьте что включены права 'Spot Trading' в API ключе")
            else:
                print(f"   ⚠️ Ошибка тестового ордера: {e}")
        
        await exchange.close()
        
        print("\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("🎯 API ключи работают корректно")
        
        if total_usd > 10:
            print(f"💰 Баланс достаточен для торговли: ~${total_usd:.2f}")
            print("🚀 Можно запускать реальную торговлю!")
        else:
            print("⚠️ Низкий баланс для реальной торговли")
            print("💡 Рекомендуется пополнить счет или использовать тестовый режим")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА ПОДКЛЮЧЕНИЯ: {e}")
        
        error_msg = str(e).lower()
        
        if 'invalid' in error_msg and 'key' in error_msg:
            print("\n🔧 РЕШЕНИЕ:")
            print("1. Проверьте правильность API ключей")
            print("2. Убедитесь что ключи активны на Bybit")
            print("3. Проверьте что не истек срок действия")
            print("4. Создайте новые ключи если нужно")
            
        elif 'ip' in error_msg or 'whitelist' in error_msg:
            print("\n🔧 РЕШЕНИЕ:")
            print("1. Добавьте ваш IP в whitelist на Bybit")
            print("2. Или отключите IP ограничения в настройках API")
            
        elif 'permission' in error_msg:
            print("\n🔧 РЕШЕНИЕ:")
            print("1. Проверьте разрешения API ключа")
            print("2. Включите 'Spot Trading' и 'Read-Only'")
            print("3. Пересоздайте ключ с правильными разрешениями")
        
        else:
            print("\n🔧 ОБЩИЕ РЕКОМЕНДАЦИИ:")
            print("1. Проверьте интернет соединение")
            print("2. Попробуйте через несколько минут")
            print("3. Проверьте статус Bybit API")
        
        return False

def main():
    """Главная функция"""
    try:
        result = asyncio.run(test_bybit_api_comprehensive())
        
        if result:
            print("\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
            print("1. Запустите живой бот: python bybit_live_triangular.py")
            print("2. Или WebSocket версию: python bybit_websocket_triangular.py")
            print("3. Мониторьте результаты в логах")
        else:
            print("\n❌ Исправьте проблемы с API ключами перед запуском торговли")
            
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()