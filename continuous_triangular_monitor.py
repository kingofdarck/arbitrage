#!/usr/bin/env python3
"""
Непрерывный мониторинг треугольного арбитража
Работает 24/7, ловит возможности когда они появляются
"""

import ccxt
import time
import itertools
import asyncio
from datetime import datetime
import json

class ContinuousTriangularMonitor:
    """Непрерывный монитор треугольного арбитража"""
    
    def __init__(self):
        self.exchange = None
        self.currencies = [
            'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'AVAX', 
            'MATIC', 'LINK', 'UNI', 'LTC', 'BCH', 'ETC', 'ATOM',
            'NEAR', 'FTM', 'ALGO', 'VET', 'ICP'
        ]
        self.quote = 'USDT'
        self.min_profit = 0.1  # Очень низкий порог для поиска любых возможностей
        self.min_volume = 1000  # Минимальный объем
        
        # Статистика
        self.stats = {
            'cycles': 0,
            'opportunities_found': 0,
            'total_profit_potential': 0.0,
            'best_opportunity': None,
            'start_time': time.time(),
            'last_opportunity_time': None
        }
        
        self.is_running = False
    
    def initialize(self):
        """Инициализация"""
        try:
            self.exchange = ccxt.binance({
                'enableRateLimit': False,  # Максимальная скорость
                'timeout': 5000,
                'rateLimit': 100
            })
            print("✅ Подключен к Binance")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    def scan_triangular_opportunities(self):
        """Быстрое сканирование треугольных возможностей"""
        try:
            # Получаем тикеры
            start_time = time.time()
            all_tickers = self.exchange.fetch_tickers()
            fetch_time = time.time() - start_time
            
            # Анализируем треугольники
            opportunities = []
            triangles_checked = 0
            
            for base1, base2 in itertools.combinations(self.currencies, 2):
                # Треугольник: USDT -> base1 -> base2 -> USDT
                pair1 = f"{base1}/{self.quote}"
                pair2 = f"{base1}/{base2}"
                pair3 = f"{base2}/{self.quote}"
                pair2_alt = f"{base2}/{base1}"
                
                # Проверяем существование пар
                triangles_to_check = []
                if all(pair in all_tickers for pair in [pair1, pair2, pair3]):
                    triangles_to_check.append((pair1, pair2, pair3, 'direct'))
                if all(pair in all_tickers for pair in [pair1, pair2_alt, pair3]):
                    triangles_to_check.append((pair1, pair2_alt, pair3, 'reverse'))
                
                for triangle in triangles_to_check:
                    triangles_checked += 1
                    opportunity = self.analyze_triangle(triangle, all_tickers)
                    if opportunity:
                        opportunities.append(opportunity)
            
            total_time = time.time() - start_time
            
            return {
                'opportunities': opportunities,
                'triangles_checked': triangles_checked,
                'fetch_time': fetch_time,
                'total_time': total_time
            }
            
        except Exception as e:
            print(f"❌ Ошибка сканирования: {e}")
            return {
                'opportunities': [],
                'triangles_checked': 0,
                'fetch_time': 0,
                'total_time': 0
            }
    
    def analyze_triangle(self, triangle_data, tickers):
        """Анализ треугольной возможности"""
        try:
            pair1, pair2, pair3, direction = triangle_data
            
            t1, t2, t3 = tickers[pair1], tickers[pair2], tickers[pair3]
            
            # Проверяем наличие цен
            if not all(t['bid'] and t['ask'] for t in [t1, t2, t3]):
                return None
            
            # Расчет треугольного арбитража
            initial_amount = 1000.0
            
            # Шаг 1: USDT -> base1
            base1_amount = initial_amount / t1['ask']
            base1_currency = pair1.split('/')[0]
            
            # Шаг 2: base1 -> base2
            base2_currency = pair3.split('/')[0]
            
            if direction == 'direct':
                base2_amount = base1_amount * t2['bid']
            else:
                base2_amount = base1_amount / t2['ask']
            
            # Шаг 3: base2 -> USDT
            final_amount = base2_amount * t3['bid']
            
            # Расчет прибыли
            profit_amount = final_amount - initial_amount
            profit_percent = (profit_amount / initial_amount) * 100
            
            # Проверяем минимальную прибыль
            if profit_percent < self.min_profit:
                return None
            
            # Проверяем объемы
            volumes = [t1.get('quoteVolume', 0), t2.get('quoteVolume', 0), t3.get('quoteVolume', 0)]
            min_volume = min(volumes)
            if min_volume < self.min_volume:
                return None
            
            return {
                'triangle': triangle_data[:3],
                'path': f"USDT → {base1_currency} → {base2_currency} → USDT",
                'profit_percent': profit_percent,
                'profit_usd': profit_amount,
                'min_volume': min_volume,
                'timestamp': datetime.now(),
                'prices': {
                    pair1: {'ask': t1['ask'], 'bid': t1['bid']},
                    pair2: {'ask': t2['ask'], 'bid': t2['bid']},
                    pair3: {'ask': t3['ask'], 'bid': t3['bid']}
                }
            }
            
        except Exception:
            return None
    
    def print_opportunities(self, opportunities):
        """Вывод найденных возможностей"""
        if not opportunities:
            return
        
        print(f"\n🎯 НАЙДЕНО {len(opportunities)} ВОЗМОЖНОСТЕЙ!")
        print("=" * 70)
        
        # Сортируем по прибыльности
        opportunities.sort(key=lambda x: x['profit_percent'], reverse=True)
        
        for i, opp in enumerate(opportunities[:10], 1):
            print(f"{i}. {opp['path']}")
            print(f"   💰 Прибыль: {opp['profit_percent']:.4f}% (${opp['profit_usd']:.4f})")
            print(f"   📊 Мин. объем: ${opp['min_volume']:,.0f}")
            print(f"   ⏰ Время: {opp['timestamp'].strftime('%H:%M:%S')}")
            print()
        
        # Обновляем статистику
        self.stats['opportunities_found'] += len(opportunities)
        self.stats['total_profit_potential'] += sum(opp['profit_usd'] for opp in opportunities)
        self.stats['last_opportunity_time'] = time.time()
        
        # Сохраняем лучшую возможность
        best = opportunities[0]
        if (self.stats['best_opportunity'] is None or 
            best['profit_percent'] > self.stats['best_opportunity']['profit_percent']):
            self.stats['best_opportunity'] = best
    
    def print_stats(self):
        """Вывод статистики"""
        uptime = time.time() - self.stats['start_time']
        cycles_per_min = (self.stats['cycles'] / uptime) * 60 if uptime > 0 else 0
        
        print(f"\n📊 СТАТИСТИКА (цикл {self.stats['cycles']}):")
        print(f"   ⏰ Время работы: {uptime/60:.1f} мин")
        print(f"   🔄 Циклов/мин: {cycles_per_min:.1f}")
        print(f"   💡 Найдено возможностей: {self.stats['opportunities_found']}")
        print(f"   💰 Потенциальная прибыль: ${self.stats['total_profit_potential']:.2f}")
        
        if self.stats['best_opportunity']:
            best = self.stats['best_opportunity']
            print(f"   🏆 Лучшая возможность: {best['profit_percent']:.4f}% ({best['path']})")
        
        if self.stats['last_opportunity_time']:
            time_since_last = time.time() - self.stats['last_opportunity_time']
            print(f"   🕐 Последняя возможность: {time_since_last/60:.1f} мин назад")
        else:
            print(f"   🕐 Возможностей пока не было")
    
    def run_continuous(self):
        """Непрерывный мониторинг"""
        print("🚀 ЗАПУСК НЕПРЕРЫВНОГО МОНИТОРИНГА ТРЕУГОЛЬНОГО АРБИТРАЖА")
        print("=" * 70)
        print(f"💰 Минимальная прибыль: {self.min_profit}%")
        print(f"📊 Минимальный объем: ${self.min_volume:,}")
        print(f"🔍 Валют для анализа: {len(self.currencies)}")
        print(f"⏰ Интервал: каждые 5 секунд")
        print("=" * 70)
        
        self.is_running = True
        
        try:
            while self.is_running:
                self.stats['cycles'] += 1
                cycle_start = time.time()
                
                # Сканируем возможности
                result = self.scan_triangular_opportunities()
                opportunities = result['opportunities']
                
                # Выводим результаты
                current_time = datetime.now().strftime('%H:%M:%S')
                if opportunities:
                    print(f"\n🔄 Цикл {self.stats['cycles']} - {current_time}")
                    self.print_opportunities(opportunities)
                else:
                    # Краткий вывод если нет возможностей
                    if self.stats['cycles'] % 10 == 0:  # Каждые 10 циклов
                        print(f"🔄 Цикл {self.stats['cycles']} - {current_time} - Возможностей нет")
                
                # Статистика каждые 50 циклов
                if self.stats['cycles'] % 50 == 0:
                    self.print_stats()
                
                cycle_time = time.time() - cycle_start
                
                # Пауза между циклами (5 секунд минус время выполнения)
                sleep_time = max(0, 5 - cycle_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print("\n⏹️ Остановка мониторинга...")
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
        finally:
            self.is_running = False
            self.print_stats()
            print("✅ Мониторинг остановлен")

def main():
    """Главная функция"""
    monitor = ContinuousTriangularMonitor()
    
    if monitor.initialize():
        monitor.run_continuous()
    else:
        print("❌ Не удалось инициализировать монитор")

if __name__ == "__main__":
    main()