#!/usr/bin/env python3
"""
Оптимизированный мониторинг треугольного арбитража
Учитывает лимиты API, работает стабильно
"""

import ccxt
import time
import itertools
from datetime import datetime
import json

class OptimizedTriangularMonitor:
    """Оптимизированный монитор треугольного арбитража"""
    
    def __init__(self):
        self.exchange = None
        # Сокращенный список валют для снижения нагрузки на API
        self.currencies = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'AVAX']
        self.quote = 'USDT'
        self.min_profit = 0.2  # Повышаем порог для качественных возможностей
        self.min_volume = 5000  # Повышаем минимальный объем
        
        # Статистика
        self.stats = {
            'cycles': 0,
            'opportunities_found': 0,
            'api_calls': 0,
            'errors': 0,
            'best_opportunity': None,
            'start_time': time.time()
        }
        
        self.is_running = False
    
    def initialize(self):
        """Инициализация с правильными лимитами"""
        try:
            self.exchange = ccxt.binance({
                'enableRateLimit': True,  # Включаем rate limiting
                'timeout': 10000,
                'rateLimit': 1200,  # Увеличиваем интервал между запросами
                'options': {
                    'adjustForTimeDifference': True
                }
            })
            print("✅ Подключен к Binance с rate limiting")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    def get_specific_tickers(self):
        """Получение только нужных тикеров для экономии API calls"""
        try:
            # Формируем список только нужных пар
            needed_pairs = []
            
            # Добавляем базовые пары (валюта/USDT)
            for currency in self.currencies:
                needed_pairs.append(f"{currency}{self.quote}")
            
            # Добавляем кросс-пары для треугольников
            for base1, base2 in itertools.combinations(self.currencies, 2):
                needed_pairs.extend([f"{base1}{base2}", f"{base2}{base1}"])
            
            # Убираем дубликаты
            needed_pairs = list(set(needed_pairs))
            
            print(f"📊 Запрашиваем {len(needed_pairs)} специфичных тикеров...")
            
            # Получаем все тикеры одним запросом
            all_tickers = self.exchange.fetch_tickers()
            self.stats['api_calls'] += 1
            
            # Фильтруем только нужные
            filtered_tickers = {}
            for pair in needed_pairs:
                # Преобразуем формат BTCUSDT -> BTC/USDT
                if pair.endswith('USDT'):
                    base = pair[:-4]
                    formatted_pair = f"{base}/USDT"
                    if formatted_pair in all_tickers:
                        filtered_tickers[formatted_pair] = all_tickers[formatted_pair]
                else:
                    # Для кросс-пар пробуем разные форматы
                    for currency in self.currencies:
                        if pair.startswith(currency) and len(pair) > len(currency):
                            base = currency
                            quote = pair[len(currency):]
                            if quote in self.currencies:
                                formatted_pair = f"{base}/{quote}"
                                if formatted_pair in all_tickers:
                                    filtered_tickers[formatted_pair] = all_tickers[formatted_pair]
                                break
            
            print(f"✅ Получено {len(filtered_tickers)} релевантных тикеров")
            return filtered_tickers
            
        except Exception as e:
            print(f"❌ Ошибка получения тикеров: {e}")
            self.stats['errors'] += 1
            return {}
    
    def scan_triangular_opportunities(self):
        """Сканирование треугольных возможностей"""
        try:
            start_time = time.time()
            
            # Получаем тикеры
            tickers = self.get_specific_tickers()
            if not tickers:
                return {'opportunities': [], 'scan_time': 0}
            
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
                if all(pair in tickers for pair in [pair1, pair2, pair3]):
                    triangles_to_check.append((pair1, pair2, pair3, 'direct'))
                if all(pair in tickers for pair in [pair1, pair2_alt, pair3]):
                    triangles_to_check.append((pair1, pair2_alt, pair3, 'reverse'))
                
                for triangle in triangles_to_check:
                    triangles_checked += 1
                    opportunity = self.analyze_triangle(triangle, tickers)
                    if opportunity:
                        opportunities.append(opportunity)
            
            scan_time = time.time() - start_time
            
            return {
                'opportunities': opportunities,
                'triangles_checked': triangles_checked,
                'fetch_time': fetch_time,
                'scan_time': scan_time
            }
            
        except Exception as e:
            print(f"❌ Ошибка сканирования: {e}")
            self.stats['errors'] += 1
            return {'opportunities': [], 'scan_time': 0}
    
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
            
            # Учитываем комиссии биржи (0.1% за сделку)
            total_fees = initial_amount * 0.003  # 3 сделки по 0.1%
            net_profit = profit_amount - total_fees
            net_profit_percent = (net_profit / initial_amount) * 100
            
            # Проверяем чистую прибыль после комиссий
            if net_profit_percent < 0.1:
                return None
            
            return {
                'triangle': triangle_data[:3],
                'path': f"USDT → {base1_currency} → {base2_currency} → USDT",
                'profit_percent': profit_percent,
                'net_profit_percent': net_profit_percent,
                'profit_usd': profit_amount,
                'net_profit_usd': net_profit,
                'fees_usd': total_fees,
                'min_volume': min_volume,
                'timestamp': datetime.now(),
                'execution_steps': [
                    f"1. Купить {base1_amount:.6f} {base1_currency} за ${initial_amount:.2f}",
                    f"2. Обменять на {base2_amount:.6f} {base2_currency} ({direction})",
                    f"3. Продать за ${final_amount:.2f} USDT"
                ]
            }
            
        except Exception:
            return None
    
    def print_opportunities(self, opportunities):
        """Вывод найденных возможностей"""
        if not opportunities:
            return
        
        print(f"\n🎯 НАЙДЕНО {len(opportunities)} КАЧЕСТВЕННЫХ ВОЗМОЖНОСТЕЙ!")
        print("=" * 80)
        
        # Сортируем по чистой прибыли
        opportunities.sort(key=lambda x: x['net_profit_percent'], reverse=True)
        
        for i, opp in enumerate(opportunities[:5], 1):
            print(f"{i}. {opp['path']}")
            print(f"   💰 Валовая прибыль: {opp['profit_percent']:.3f}% (${opp['profit_usd']:.2f})")
            print(f"   💵 Чистая прибыль: {opp['net_profit_percent']:.3f}% (${opp['net_profit_usd']:.2f})")
            print(f"   💸 Комиссии: ${opp['fees_usd']:.2f}")
            print(f"   📊 Мин. объем: ${opp['min_volume']:,.0f}")
            print(f"   ⏰ Время: {opp['timestamp'].strftime('%H:%M:%S')}")
            print(f"   📋 Исполнение:")
            for step in opp['execution_steps']:
                print(f"      {step}")
            print()
        
        # Обновляем статистику
        self.stats['opportunities_found'] += len(opportunities)
        
        # Сохраняем лучшую возможность
        best = opportunities[0]
        if (self.stats['best_opportunity'] is None or 
            best['net_profit_percent'] > self.stats['best_opportunity']['net_profit_percent']):
            self.stats['best_opportunity'] = best
            print(f"🏆 НОВЫЙ РЕКОРД! Лучшая возможность: {best['net_profit_percent']:.3f}%")
    
    def print_stats(self):
        """Вывод статистики"""
        uptime = time.time() - self.stats['start_time']
        
        print(f"\n📊 СТАТИСТИКА:")
        print(f"   ⏰ Время работы: {uptime/60:.1f} мин")
        print(f"   🔄 Циклов: {self.stats['cycles']}")
        print(f"   📡 API вызовов: {self.stats['api_calls']}")
        print(f"   ❌ Ошибок: {self.stats['errors']}")
        print(f"   💡 Найдено возможностей: {self.stats['opportunities_found']}")
        
        if self.stats['best_opportunity']:
            best = self.stats['best_opportunity']
            print(f"   🏆 Лучшая возможность: {best['net_profit_percent']:.3f}% ({best['path']})")
        
        success_rate = ((self.stats['cycles'] - self.stats['errors']) / self.stats['cycles'] * 100) if self.stats['cycles'] > 0 else 0
        print(f"   ✅ Успешность: {success_rate:.1f}%")
    
    def run_optimized(self):
        """Оптимизированный мониторинг"""
        print("🚀 ЗАПУСК ОПТИМИЗИРОВАННОГО МОНИТОРИНГА")
        print("=" * 60)
        print(f"💰 Минимальная прибыль: {self.min_profit}%")
        print(f"📊 Минимальный объем: ${self.min_volume:,}")
        print(f"🔍 Валют: {len(self.currencies)} ({', '.join(self.currencies)})")
        print(f"⏰ Интервал: 30 секунд (с учетом лимитов API)")
        print(f"💸 Учет комиссий: 0.1% за сделку")
        print("=" * 60)
        
        self.is_running = True
        
        try:
            while self.is_running:
                self.stats['cycles'] += 1
                cycle_start = time.time()
                
                print(f"\n🔄 Цикл {self.stats['cycles']} - {datetime.now().strftime('%H:%M:%S')}")
                
                # Сканируем возможности
                result = self.scan_triangular_opportunities()
                opportunities = result['opportunities']
                
                if opportunities:
                    self.print_opportunities(opportunities)
                else:
                    print("   ℹ️ Качественных возможностей не найдено")
                
                # Статистика каждые 10 циклов
                if self.stats['cycles'] % 10 == 0:
                    self.print_stats()
                
                cycle_time = time.time() - cycle_start
                print(f"   ⏱️ Время цикла: {cycle_time:.2f}с")
                
                # Пауза 30 секунд для соблюдения лимитов API
                print("   ⏳ Ожидание 30 секунд...")
                time.sleep(30)
                
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
    monitor = OptimizedTriangularMonitor()
    
    if monitor.initialize():
        monitor.run_optimized()
    else:
        print("❌ Не удалось инициализировать монитор")

if __name__ == "__main__":
    main()