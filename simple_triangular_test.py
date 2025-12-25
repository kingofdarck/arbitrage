#!/usr/bin/env python3
"""
Простой тест треугольного арбитража
Работает с публичными API Binance
"""

import ccxt
import time
import itertools
from datetime import datetime

def test_triangular_arbitrage():
    """Тест треугольного арбитража на Binance"""
    print("🔺 ТЕСТ ТРЕУГОЛЬНОГО АРБИТРАЖА")
    print("=" * 50)
    
    # Инициализация Binance
    try:
        exchange = ccxt.binance({'enableRateLimit': True})
        print("✅ Подключен к Binance")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return
    
    # Основные валюты для треугольного арбитража
    currencies = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP']
    quote = 'USDT'
    
    print(f"🔍 Анализируем валюты: {', '.join(currencies)}")
    
    try:
        # Получаем все тикеры
        print("📊 Получение тикеров...")
        start_time = time.time()
        all_tickers = exchange.fetch_tickers()
        fetch_time = time.time() - start_time
        print(f"✅ Получено {len(all_tickers)} тикеров за {fetch_time:.3f}с")
        
        # Анализируем треугольники
        opportunities = []
        triangles_checked = 0
        
        for base1, base2 in itertools.combinations(currencies, 2):
            # Треугольник: USDT -> base1 -> base2 -> USDT
            pair1 = f"{base1}/{quote}"  # BTC/USDT
            pair2 = f"{base1}/{base2}"  # BTC/ETH
            pair3 = f"{base2}/{quote}"  # ETH/USDT
            
            # Альтернативный порядок для pair2
            pair2_alt = f"{base2}/{base1}"  # ETH/BTC
            
            # Проверяем какие пары существуют
            triangles_to_check = []
            if all(pair in all_tickers for pair in [pair1, pair2, pair3]):
                triangles_to_check.append((pair1, pair2, pair3, 'direct'))
            if all(pair in all_tickers for pair in [pair1, pair2_alt, pair3]):
                triangles_to_check.append((pair1, pair2_alt, pair3, 'reverse'))
            
            for triangle in triangles_to_check:
                triangles_checked += 1
                opportunity = analyze_triangle(triangle, all_tickers)
                if opportunity:
                    opportunities.append(opportunity)
        
        print(f"🔺 Проверено {triangles_checked} треугольников")
        
        if opportunities:
            # Сортируем по прибыльности
            opportunities.sort(key=lambda x: x['profit_percent'], reverse=True)
            
            print(f"\n💡 НАЙДЕНО {len(opportunities)} ВОЗМОЖНОСТЕЙ:")
            print("=" * 60)
            
            for i, opp in enumerate(opportunities[:10], 1):
                print(f"{i}. {opp['path']}")
                print(f"   💰 Прибыль: {opp['profit_percent']:.3f}% (${opp['profit_usd']:.2f})")
                print(f"   📊 Шаги:")
                for step in opp['steps']:
                    print(f"      {step}")
                print()
        else:
            print("\n❌ Прибыльных треугольных возможностей не найдено")
            print("💡 Это нормально - рынок не всегда предоставляет возможности")
            print("🔧 Попробуйте снизить минимальную прибыль или проверить позже")
        
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")
    
    print(f"\n✅ Тест завершен в {datetime.now().strftime('%H:%M:%S')}")

def analyze_triangle(triangle_data, tickers):
    """Анализ треугольной возможности"""
    try:
        pair1, pair2, pair3, direction = triangle_data
        
        t1, t2, t3 = tickers[pair1], tickers[pair2], tickers[pair3]
        
        # Проверяем наличие цен
        if not all(t['bid'] and t['ask'] for t in [t1, t2, t3]):
            return None
        
        # Расчет треугольного арбитража
        initial_amount = 1000.0  # USDT
        
        # Шаг 1: USDT -> base1
        base1_amount = initial_amount / t1['ask']
        base1_currency = pair1.split('/')[0]
        
        # Шаг 2: base1 -> base2
        base2_currency = pair3.split('/')[0]
        
        if direction == 'direct':
            # Прямой порядок: BTC/ETH
            base2_amount = base1_amount * t2['bid']
        else:
            # Обратный порядок: ETH/BTC
            base2_amount = base1_amount / t2['ask']
        
        # Шаг 3: base2 -> USDT
        final_amount = base2_amount * t3['bid']
        
        # Расчет прибыли
        profit_amount = final_amount - initial_amount
        profit_percent = (profit_amount / initial_amount) * 100
        
        # Минимальная прибыль 0.75%
        if profit_percent < 0.75:
            return None
        
        # Проверяем объемы (минимум $10k)
        volumes = [t1.get('quoteVolume', 0), t2.get('quoteVolume', 0), t3.get('quoteVolume', 0)]
        if min(volumes) < 10000:
            return None
        
        return {
            'triangle': triangle_data[:3],
            'path': f"USDT → {base1_currency} → {base2_currency} → USDT",
            'profit_percent': profit_percent,
            'profit_usd': profit_amount,
            'initial_amount': initial_amount,
            'final_amount': final_amount,
            'steps': [
                f"1. Купить {base1_amount:.8f} {base1_currency} за {initial_amount:.2f} USDT по цене {t1['ask']:.8f}",
                f"2. Обменять {base1_amount:.8f} {base1_currency} на {base2_amount:.8f} {base2_currency}",
                f"3. Продать {base2_amount:.8f} {base2_currency} за {final_amount:.2f} USDT по цене {t3['bid']:.8f}"
            ]
        }
        
    except Exception as e:
        return None

if __name__ == "__main__":
    test_triangular_arbitrage()