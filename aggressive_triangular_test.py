#!/usr/bin/env python3
"""
Агрессивный тест треугольного арбитража
Низкий порог прибыли для поиска большего количества возможностей
"""

import ccxt
import time
import itertools
from datetime import datetime

def aggressive_triangular_test():
    """Агрессивный тест с низким порогом прибыли"""
    print("🔺 АГРЕССИВНЫЙ ТЕСТ ТРЕУГОЛЬНОГО АРБИТРАЖА")
    print("=" * 60)
    
    # Инициализация Binance
    try:
        exchange = ccxt.binance({'enableRateLimit': True})
        print("✅ Подключен к Binance")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return
    
    # Расширенный список валют
    currencies = [
        'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'AVAX', 
        'MATIC', 'LINK', 'UNI', 'LTC', 'BCH', 'ETC', 'ATOM'
    ]
    quote = 'USDT'
    
    print(f"🔍 Анализируем {len(currencies)} валют")
    print(f"💰 Минимальная прибыль: 0.1% (агрессивно)")
    print(f"📊 Минимальный объем: $1,000 (низкий)")
    
    try:
        # Получаем все тикеры
        print("\n📊 Получение тикеров...")
        start_time = time.time()
        all_tickers = exchange.fetch_tickers()
        fetch_time = time.time() - start_time
        print(f"✅ Получено {len(all_tickers)} тикеров за {fetch_time:.3f}с")
        
        # Анализируем треугольники
        opportunities = []
        triangles_checked = 0
        
        print("🔺 Анализ треугольников...")
        analysis_start = time.time()
        
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
                opportunity = analyze_triangle_aggressive(triangle, all_tickers)
                if opportunity:
                    opportunities.append(opportunity)
        
        analysis_time = time.time() - analysis_start
        total_time = time.time() - start_time
        
        print(f"✅ Проверено {triangles_checked} треугольников за {analysis_time:.3f}с")
        print(f"⏱️ Общее время: {total_time:.3f}с")
        
        if opportunities:
            # Сортируем по прибыльности
            opportunities.sort(key=lambda x: x['profit_percent'], reverse=True)
            
            print(f"\n🎯 НАЙДЕНО {len(opportunities)} ВОЗМОЖНОСТЕЙ!")
            print("=" * 70)
            
            for i, opp in enumerate(opportunities[:15], 1):
                print(f"{i}. {opp['path']}")
                print(f"   💰 Прибыль: {opp['profit_percent']:.4f}% (${opp['profit_usd']:.4f})")
                print(f"   📊 Объемы: {opp['min_volume']:,.0f} USD")
                print(f"   ⚡ Исполнение: {opp['execution_complexity']}")
                print()
                
                # Показываем детали для топ-3
                if i <= 3:
                    print(f"   📋 Детальные шаги:")
                    for step in opp['steps']:
                        print(f"      {step}")
                    print()
        else:
            print("\n❌ Даже с агрессивными настройками возможностей не найдено")
            print("💡 Возможные причины:")
            print("   - Рынок очень эффективен в данный момент")
            print("   - Высокая конкуренция арбитражных ботов")
            print("   - Комиссии биржи съедают прибыль")
            print("   - Нужно проверить другие биржи или время")
        
        # Статистика
        print(f"\n📊 СТАТИСТИКА:")
        print(f"   Время получения данных: {fetch_time:.3f}с")
        print(f"   Время анализа: {analysis_time:.3f}с")
        print(f"   Треугольников проверено: {triangles_checked}")
        print(f"   Возможностей найдено: {len(opportunities)}")
        if opportunities:
            avg_profit = sum(opp['profit_percent'] for opp in opportunities) / len(opportunities)
            print(f"   Средняя прибыль: {avg_profit:.4f}%")
            print(f"   Лучшая прибыль: {opportunities[0]['profit_percent']:.4f}%")
        
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n✅ Агрессивный тест завершен в {datetime.now().strftime('%H:%M:%S')}")

def analyze_triangle_aggressive(triangle_data, tickers):
    """Агрессивный анализ треугольной возможности"""
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
        
        # АГРЕССИВНЫЙ порог прибыли: 0.1% (вместо 0.75%)
        if profit_percent < 0.1:
            return None
        
        # АГРЕССИВНЫЕ требования к объему: $1k (вместо $10k)
        volumes = [t1.get('quoteVolume', 0), t2.get('quoteVolume', 0), t3.get('quoteVolume', 0)]
        min_volume = min(volumes)
        if min_volume < 1000:
            return None
        
        # Оценка сложности исполнения
        execution_complexity = "Простая"
        if profit_percent < 0.3:
            execution_complexity = "Сложная (низкая прибыль)"
        elif min_volume < 5000:
            execution_complexity = "Средняя (низкий объем)"
        
        return {
            'triangle': triangle_data[:3],
            'path': f"USDT → {base1_currency} → {base2_currency} → USDT",
            'profit_percent': profit_percent,
            'profit_usd': profit_amount,
            'initial_amount': initial_amount,
            'final_amount': final_amount,
            'min_volume': min_volume,
            'execution_complexity': execution_complexity,
            'steps': [
                f"1. Купить {base1_amount:.8f} {base1_currency} за {initial_amount:.2f} USDT по цене {t1['ask']:.8f}",
                f"2. Обменять {base1_amount:.8f} {base1_currency} на {base2_amount:.8f} {base2_currency} ({direction})",
                f"3. Продать {base2_amount:.8f} {base2_currency} за {final_amount:.2f} USDT по цене {t3['bid']:.8f}"
            ]
        }
        
    except Exception as e:
        return None

if __name__ == "__main__":
    aggressive_triangular_test()