#!/usr/bin/env python3
"""
Детальная диагностика проблем с Bybit
"""

import sys
import asyncio
import os
from pathlib import Path

# Добавляем путь к модулям
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

async def debug_bybit():
    """Детальная диагностика Bybit"""
    print("🔍 ДЕТАЛЬНАЯ ДИАГНОСТИКА BYBIT")
    print("=" * 60)
    
    # 1. Проверка переменных окружения
    print("1️⃣ Проверка переменных окружения:")
    from config import config
    
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    enabled = os.getenv('BYBIT_ENABLED')
    sandbox = os.getenv('BYBIT_SANDBOX')
    
    print(f"   BYBIT_ENABLED: {enabled}")
    print(f"   BYBIT_API_KEY: {api_key}")
    print(f"   BYBIT_API_SECRET: {api_secret}")
    print(f"   BYBIT_SANDBOX: {sandbox}")
    print()
    
    # 2. Проверка длины ключей
    print("2️⃣ Проверка формата ключей:")
    if api_key:
        print(f"   API Key длина: {len(api_key)} символов")
        print(f"   API Key начинается с: {api_key[:5]}...")
        print(f"   API Key заканчивается на: ...{api_key[-5:]}")
    
    if api_secret:
        print(f"   Secret длина: {len(api_secret)} символов")
        print(f"   Secret начинается с: {api_secret[:5]}...")
        print(f"   Secret заканчивается на: ...{api_secret[-5:]}")
    print()
    
    # 3. Проверка разных режимов
    print("3️⃣ Тестирование разных режимов:")
    
    # Тест 1: Testnet (sandbox)
    print("   🧪 Тест Testnet (sandbox=true):")
    success_testnet = await test_bybit_connection(api_key, api_secret, sandbox=True)
    
    # Тест 2: Mainnet (sandbox)
    print("   🌐 Тест Mainnet (sandbox=false):")
    success_mainnet = await test_bybit_connection(api_key, api_secret, sandbox=False)
    
    # 4. Проверка IP
    print("\n4️⃣ Проверка IP адреса:")
    try:
        import requests
        response = requests.get('https://httpbin.org/ip', timeout=5)
        ip_info = response.json()
        print(f"   Ваш IP: {ip_info.get('origin', 'Неизвестно')}")
    except Exception as e:
        print(f"   ❌ Ошибка получения IP: {e}")
    
    # 5. Рекомендации
    print("\n5️⃣ Рекомендации:")
    
    if not success_testnet and not success_mainnet:
        print("   ❌ Оба режима не работают. Возможные причины:")
        print("      • API ключ создан для другого типа аккаунта")
        print("      • Нет разрешений для Spot Trading")
        print("      • IP адрес не в whitelist")
        print("      • API ключ еще не активирован (подождите 1-2 минуты)")
        print("      • Неправильно скопированы ключи")
    elif success_testnet and not success_mainnet:
        print("   ✅ Testnet работает, Mainnet нет")
        print("      • Оставьте BYBIT_SANDBOX=true")
        print("      • Для реальной торговли нужны другие ключи")
    elif not success_testnet and success_mainnet:
        print("   ✅ Mainnet работает, Testnet нет")
        print("      • Измените BYBIT_SANDBOX=false")
        print("      • Будьте осторожны - это реальные деньги!")
    else:
        print("   ✅ Оба режима работают!")
        print("      • Можете использовать любой режим")

async def test_bybit_connection(api_key, api_secret, sandbox=True):
    """Тест подключения к Bybit"""
    try:
        import ccxt
        
        # Определяем URL
        if sandbox:
            base_url = 'https://api-testnet.bybit.com'
            print(f"      Подключение к: {base_url}")
        else:
            base_url = 'https://api.bybit.com'
            print(f"      Подключение к: {base_url}")
        
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': sandbox,
            'enableRateLimit': True,
            'urls': {
                'api': {
                    'public': base_url,
                    'private': base_url,
                }
            } if not sandbox else {}
        })
        
        # Простой тест - получение информации об аккаунте
        try:
            # Для Bybit v5 API
            balance = await exchange.fetch_balance()
            print(f"      ✅ Успешно! Получен баланс: {len(balance)} валют")
            await exchange.close()
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"      ❌ Ошибка: {error_msg}")
            
            # Анализ ошибки
            if "10003" in error_msg:
                print("         → API ключ недействителен")
            elif "10004" in error_msg:
                print("         → Неправильная подпись")
            elif "10005" in error_msg:
                print("         → Нет разрешений")
            elif "10016" in error_msg:
                print("         → IP не в whitelist")
            elif "10018" in error_msg:
                print("         → API ключ заблокирован")
            
            await exchange.close()
            return False
            
    except Exception as e:
        print(f"      ❌ Критическая ошибка: {e}")
        return False

async def test_manual_request():
    """Ручной тест API запроса"""
    print("\n6️⃣ Ручной тест API:")
    
    try:
        import hmac
        import hashlib
        import time
        import requests
        
        api_key = os.getenv('BYBIT_API_KEY')
        api_secret = os.getenv('BYBIT_API_SECRET')
        
        if not api_key or not api_secret:
            print("   ❌ API ключи не найдены")
            return
        
        # Параметры запроса
        timestamp = str(int(time.time() * 1000))
        
        # Создание подписи
        param_str = f"timestamp={timestamp}"
        signature = hmac.new(
            api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Заголовки
        headers = {
            'X-BAPI-API-KEY': api_key,
            'X-BAPI-TIMESTAMP': timestamp,
            'X-BAPI-SIGN': signature,
            'Content-Type': 'application/json'
        }
        
        # Тест на testnet
        url = f"https://api-testnet.bybit.com/v5/account/wallet-balance?accountType=UNIFIED&timestamp={timestamp}"
        
        print(f"   📡 Запрос к: {url}")
        print(f"   🔑 API Key: {api_key[:10]}...")
        print(f"   ⏰ Timestamp: {timestamp}")
        print(f"   ✍️ Signature: {signature[:20]}...")
        
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"   📊 Статус: {response.status_code}")
        print(f"   📄 Ответ: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("   ✅ Ручной запрос успешен!")
        else:
            print("   ❌ Ручной запрос неудачен")
            
    except Exception as e:
        print(f"   ❌ Ошибка ручного теста: {e}")

async def main():
    """Главная функция"""
    await debug_bybit()
    await test_manual_request()
    
    print("\n" + "=" * 60)
    print("🎯 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Проверьте настройки API на bybit.com")
    print("2. Убедитесь что включен Spot Trading")
    print("3. Добавьте IP в whitelist")
    print("4. Подождите 1-2 минуты после создания ключа")
    print("5. Попробуйте пересоздать API ключ")

if __name__ == "__main__":
    asyncio.run(main())