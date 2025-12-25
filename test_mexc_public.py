#!/usr/bin/env python3
"""
Тест публичного API MEXC (без авторизации)
"""

import asyncio
import ccxt.pro as ccxt

async def test_mexc_public():
    """Тест публичного API MEXC"""
    print("🔺 ТЕСТ ПУБЛИЧНОГО API MEXC")
    print("=" * 40)
    
    try:
        # Создаем подключение без API ключей
        exchange = ccxt.mexc({
            'sandbox': False,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        print("📡 Подключение к MEXC (публичное API)...")
        
        # Тест 1: Загрузка рынков
        print("1️⃣ Загрузка торговых пар...")
        markets = await exchange.load_markets()
        print(f"✅ Загружено {len(markets)} торговых пар")
        
        # Показываем примеры пар
        usdt_pairs = [symbol for symbol in markets.keys() if symbol.endswith('/USDT')][:10]
        print(f"📊 Примеры USDT пар: {', '.join(usdt_pairs)}")
        
        # Тест 2: Получение тикеров
        print("\n2️⃣ Получение рыночных данных...")
        tickers = await exchange.fetch_tickers(['BTC/USDT', 'ETH/USDT', 'BNB/USDT'])
        print("✅ Рыночные данные получены:")
        for symbol, ticker in tickers.items():
            price = ticker.get('last', 0)
            volume = ticker.get('quoteVolume', 0)
            print(f"   📈 {symbol}: ${price:,.2f} (объем: ${volume:,.0f})")
        
        # Тест 3: Проверка треугольных пар
        print("\n3️⃣ Поиск треугольных возможностей...")
        
        # Основные валюты для треугольников
        base_currencies = ['USDT', 'BTC', 'ETH']
        crypto_currencies = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'AVAX', 'MATIC', 'LINK']
        
        triangles_found = 0
        examples = []
        
        for base in base_currencies:
            for crypto1 in crypto_currencies:
                for crypto2 in crypto_currencies:
                    if crypto1 != crypto2 and crypto1 != base and crypto2 != base:
                        pair1 = f"{crypto1}/{base}"
                        pair2 = f"{crypto1}/{crypto2}"
                        pair3 = f"{crypto2}/{base}"
                        pair2_alt = f"{crypto2}/{crypto1}"
                        
                        if all(pair in markets for pair in [pair1, pair2, pair3]):
                            triangles_found += 1
                            if len(examples) < 5:
                                examples.append(f"{base} → {crypto1} → {crypto2} → {base}")
                        
                        if all(pair in markets for pair in [pair1, pair2_alt, pair3]):
                            triangles_found += 1
                            if len(examples) < 5:
                                examples.append(f"{base} → {crypto1} → {crypto2} → {base} (reverse)")
        
        print(f"✅ Найдено {triangles_found} треугольных возможностей")
        print("🔺 Примеры треугольников:")
        for example in examples:
            print(f"   • {example}")
        
        # Тест 4: Симуляция треугольного арбитража
        print("\n4️⃣ Симуляция треугольного арбитража...")
        
        try:
            # Получаем цены для треугольника BTC/USDT -> BTC/ETH -> ETH/USDT
            triangle_pairs = ['BTC/USDT', 'BTC/ETH', 'ETH/USDT']
            triangle_tickers = await exchange.fetch_tickers(triangle_pairs)
            
            # Симулируем арбитраж с $100
            initial_amount = 100.0
            
            # Шаг 1: USDT -> BTC
            btc_price = triangle_tickers['BTC/USDT']['ask']
            btc_amount = initial_amount / btc_price
            
            # Шаг 2: BTC -> ETH
            btc_eth_price = triangle_tickers['BTC/ETH']['bid']
            eth_amount = btc_amount * btc_eth_price
            
            # Шаг 3: ETH -> USDT
            eth_price = triangle_tickers['ETH/USDT']['bid']
            final_amount = eth_amount * eth_price
            
            # Расчет прибыли
            profit = final_amount - initial_amount
            profit_percent = (profit / initial_amount) * 100
            
            # Учитываем комиссии MEXC (0.2% за сделку)
            fees = initial_amount * 0.006  # 3 сделки по 0.2%
            net_profit = profit - fees
            net_profit_percent = (net_profit / initial_amount) * 100
            
            print(f"💰 Симуляция треугольника USDT → BTC → ETH → USDT:")
            print(f"   💵 Начальная сумма: ${initial_amount:.2f}")
            print(f"   📈 Финальная сумма: ${final_amount:.2f}")
            print(f"   💸 Валовая прибыль: ${profit:.2f} ({profit_percent:.3f}%)")
            print(f"   🏦 Комиссии: ${fees:.2f}")
            print(f"   💎 Чистая прибыль: ${net_profit:.2f} ({net_profit_percent:.3f}%)")
            
            if net_profit_percent > 0.75:
                print("   ✅ Прибыльная возможность!")
            else:
                print("   ❌ Недостаточная прибыль")
                
        except Exception as e:
            print(f"   ⚠️ Ошибка симуляции: {e}")
        
        await exchange.close()
        
        print("\n🎉 ПУБЛИЧНОЕ API РАБОТАЕТ!")
        print("✅ MEXC доступен для треугольного арбитража")
        print("🔧 Исправьте проблему с IP белым списком для полного доступа")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к MEXC: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_mexc_public())