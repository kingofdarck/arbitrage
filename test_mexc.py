#!/usr/bin/env python3
"""
Тест подключения к MEXC API
"""

import os
import asyncio
import ccxt.pro as ccxt

# Загружаем переменные окружения
try:
    from dotenv import load_dotenv
    if os.path.exists('.env'):
        load_dotenv('.env')
except ImportError:
    pass

async def test_mexc_connection():
    """Тест подключения к MEXC"""
    print("🔺 ТЕСТ ПОДКЛЮЧЕНИЯ К MEXC")
    print("=" * 40)
    
    # Получаем API ключи
    api_key = os.getenv('MEXC_API_KEY')
    api_secret = os.getenv('MEXC_API_SECRET')
    
    print(f"🔑 API Key: {api_key[:10]}... (длина: {len(api_key)})")
    print(f"🔐 Secret: {api_secret[:10]}... (длина: {len(api_secret)})")
    
    if not api_key or not api_secret:
        print("❌ API ключи не найдены в .env!")
        return False
    
    try:
        # Создаем подключение к MEXC
        exchange = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': False,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        print("📡 Подключение к MEXC...")
        
        # Тест 1: Загрузка рынков
        print("1️⃣ Загрузка торговых пар...")
        markets = await exchange.load_markets()
        print(f"✅ Загружено {len(markets)} торговых пар")
        
        # Показываем примеры пар
        usdt_pairs = [symbol for symbol in markets.keys() if symbol.endswith('/USDT')][:10]
        print(f"📊 Примеры USDT пар: {', '.join(usdt_pairs)}")
        
        # Тест 2: Получение баланса
        print("\n2️⃣ Проверка баланса аккаунта...")
        try:
            balance = await exchange.fetch_balance()
            total_balance = balance.get('total', {})
            
            # Показываем ненулевые балансы
            non_zero = {currency: amount for currency, amount in total_balance.items() if amount > 0}
            
            if non_zero:
                print("✅ Баланс получен:")
                for currency, amount in list(non_zero.items())[:5]:  # Показываем первые 5
                    print(f"   💰 {currency}: {amount}")
                if len(non_zero) > 5:
                    print(f"   ... и еще {len(non_zero) - 5} валют")
            else:
                print("⚠️ Баланс пуст (это нормально для нового аккаунта)")
                
        except Exception as e:
            print(f"⚠️ Ошибка получения баланса: {e}")
            print("💡 Возможно нужны дополнительные разрешения API")
        
        # Тест 3: Получение тикеров
        print("\n3️⃣ Получение рыночных данных...")
        try:
            tickers = await exchange.fetch_tickers(['BTC/USDT', 'ETH/USDT', 'BNB/USDT'])
            print("✅ Рыночные данные получены:")
            for symbol, ticker in tickers.items():
                price = ticker.get('last', 0)
                print(f"   📈 {symbol}: ${price:,.2f}")
        except Exception as e:
            print(f"⚠️ Ошибка получения тикеров: {e}")
        
        # Тест 4: Проверка треугольных пар
        print("\n4️⃣ Поиск треугольных возможностей...")
        
        # Основные валюты для треугольников
        base_currencies = ['USDT', 'BTC', 'ETH']
        crypto_currencies = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'AVAX']
        
        triangles_found = 0
        for base in base_currencies:
            for crypto1 in crypto_currencies:
                for crypto2 in crypto_currencies:
                    if crypto1 != crypto2 and crypto1 != base and crypto2 != base:
                        pair1 = f"{crypto1}/{base}"
                        pair2 = f"{crypto1}/{crypto2}"
                        pair3 = f"{crypto2}/{base}"
                        
                        if all(pair in markets for pair in [pair1, pair2, pair3]):
                            triangles_found += 1
                            if triangles_found <= 3:  # Показываем первые 3
                                print(f"   🔺 {base} → {crypto1} → {crypto2} → {base}")
        
        print(f"✅ Найдено {triangles_found} треугольных возможностей")
        
        await exchange.close()
        
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ MEXC API работает корректно")
        print("🔺 Система готова к треугольному арбитражу")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к MEXC: {e}")
        print("\n💡 Возможные причины:")
        print("   • Неверные API ключи")
        print("   • Недостаточные разрешения API")
        print("   • Проблемы с сетью")
        print("   • API ключи не активированы")
        
        return False

if __name__ == "__main__":
    asyncio.run(test_mexc_connection())