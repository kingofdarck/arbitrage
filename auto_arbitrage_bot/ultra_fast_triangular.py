#!/usr/bin/env python3
"""
Ультра-быстрый треугольный арбитражный бот
Максимальная скорость исполнения, только треугольный арбитраж
"""

import asyncio
import ccxt.pro as ccxt
import time
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json
import itertools

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

class UltraFastTriangularBot:
    """Ультра-быстрый бот для треугольного арбитража"""
    
    def __init__(self):
        self.exchange = None
        self.markets = {}
        self.tickers = {}
        self.triangles = []
        
        # Настройки
        self.min_profit = float(os.getenv('MIN_PROFIT_THRESHOLD', '0.75'))
        self.max_position = float(os.getenv('MAX_POSITION_SIZE', '50.0'))
        self.trading_mode = os.getenv('TRADING_MODE', 'test')
        
        # Оптимизированный список валют для треугольного арбитража
        self.currencies = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'AVAX', 'MATIC', 'LINK', 'UNI', 'LTC']
        self.quote = 'USDT'
        
        # Статистика
        self.stats = {
            'cycles': 0,
            'opportunities_found': 0,
            'trades_executed': 0,
            'total_profit': 0.0,
            'avg_cycle_time': 0.0,
            'fastest_execution': float('inf'),
            'start_time': time.time()
        }
        
        self.is_running = False
    
    async def initialize(self):
        """Быстрая инициализация"""
        print("⚡ Инициализация ультра-быстрого треугольного бота...")
        
        # Определяем лучшую биржу для треугольного арбитража
        exchanges_to_try = [
            ('binance', self._init_binance),
            ('bybit', self._init_bybit),
            ('kucoin', self._init_kucoin)
        ]
        
        for exchange_name, init_func in exchanges_to_try:
            try:
                print(f"🔌 Пробуем {exchange_name}...")
                if await init_func():
                    print(f"✅ Подключен к {exchange_name}")
                    break
            except Exception as e:
                print(f"❌ {exchange_name}: {e}")
                continue
        else:
            print("❌ Не удалось подключиться ни к одной бирже")
            return False
        
        # Предварительная генерация треугольников
        await self._generate_triangles()
        print(f"🔺 Сгенерировано {len(self.triangles)} треугольников")
        
        return True
    
    async def _init_binance(self):
        """Инициализация Binance (публичный API)"""
        self.exchange = ccxt.binance({
            'enableRateLimit': False,  # Максимальная скорость
            'options': {'defaultType': 'spot'}
        })
        
        markets = await self.exchange.load_markets()
        self.markets = markets
        return True
    
    async def _init_bybit(self):
        """Инициализация Bybit"""
        api_key = os.getenv('BYBIT_API_KEY')
        api_secret = os.getenv('BYBIT_API_SECRET')
        
        if not api_key or not api_secret:
            # Используем публичный API
            self.exchange = ccxt.bybit({
                'enableRateLimit': False,
                'options': {'defaultType': 'spot'}
            })
        else:
            self.exchange = ccxt.bybit({
                'apiKey': api_key,
                'secret': api_secret,
                'sandbox': os.getenv('BYBIT_SANDBOX', 'true').lower() == 'true',
                'enableRateLimit': False,
                'options': {'defaultType': 'spot'}
            })
        
        markets = await self.exchange.load_markets()
        self.markets = markets
        return True
    
    async def _init_kucoin(self):
        """Инициализация KuCoin"""
        api_key = os.getenv('KUCOIN_API_KEY')
        api_secret = os.getenv('KUCOIN_API_SECRET')
        passphrase = os.getenv('KUCOIN_PASSPHRASE')
        
        if not all([api_key, api_secret, passphrase]):
            # Используем публичный API
            self.exchange = ccxt.kucoin({
                'enableRateLimit': False
            })
        else:
            self.exchange = ccxt.kucoin({
                'apiKey': api_key,
                'secret': api_secret,
                'password': passphrase,
                'sandbox': os.getenv('KUCOIN_SANDBOX', 'false').lower() == 'true',
                'enableRateLimit': False
            })
        
        markets = await self.exchange.load_markets()
        self.markets = markets
        return True
    
    async def _generate_triangles(self):
        """Предварительная генерация всех возможных треугольников"""
        self.triangles = []
        
        for base1, base2 in itertools.combinations(self.currencies, 2):
            # Треугольник: USDT -> base1 -> base2 -> USDT
            pair1 = f"{base1}/{self.quote}"  # BTC/USDT
            pair2 = f"{base1}/{base2}"       # BTC/ETH
            pair3 = f"{base2}/{self.quote}"  # ETH/USDT
            
            # Альтернативный порядок для pair2
            pair2_alt = f"{base2}/{base1}"   # ETH/BTC
            
            # Проверяем какие пары существуют
            if (pair1 in self.markets and pair3 in self.markets):
                if pair2 in self.markets:
                    self.triangles.append((pair1, pair2, pair3, 'direct'))
                elif pair2_alt in self.markets:
                    self.triangles.append((pair1, pair2_alt, pair3, 'reverse'))
        
        print(f"🔺 Найдено {len(self.triangles)} валидных треугольников")
    
    async def scan_opportunities(self):
        """Быстрое сканирование возможностей"""
        start_time = time.time()
        
        # Получаем все нужные тикеры одним запросом
        symbols_needed = set()
        for triangle in self.triangles:
            symbols_needed.update(triangle[:3])
        
        try:
            # Получаем тикеры максимально быстро
            if hasattr(self.exchange, 'fetch_tickers'):
                tickers = await self.exchange.fetch_tickers(list(symbols_needed))
            else:
                # Fallback для бирж без batch API
                tickers = {}
                tasks = [self.exchange.fetch_ticker(symbol) for symbol in symbols_needed]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for symbol, result in zip(symbols_needed, results):
                    if not isinstance(result, Exception):
                        tickers[symbol] = result
            
            fetch_time = time.time() - start_time
            
            # Быстрый анализ треугольников
            opportunities = []
            for triangle in self.triangles[:100]:  # Ограничиваем для скорости
                opp = self._analyze_triangle_fast(triangle, tickers)
                if opp:
                    opportunities.append(opp)
            
            analysis_time = time.time() - start_time - fetch_time
            total_time = time.time() - start_time
            
            self.stats['cycles'] += 1
            self.stats['avg_cycle_time'] = (self.stats['avg_cycle_time'] * (self.stats['cycles'] - 1) + total_time) / self.stats['cycles']
            
            if opportunities:
                self.stats['opportunities_found'] += len(opportunities)
                print(f"⚡ Найдено {len(opportunities)} возможностей за {total_time:.3f}с (fetch: {fetch_time:.3f}с, анализ: {analysis_time:.3f}с)")
                
                # Сортируем по прибыльности
                opportunities.sort(key=lambda x: x['profit_percent'], reverse=True)
                
                # Показываем топ-3
                for i, opp in enumerate(opportunities[:3], 1):
                    print(f"   {i}. {opp['path']}: {opp['profit_percent']:.3f}% (${opp['profit_usd']:.2f})")
                
                # Исполняем лучшую возможность
                await self._execute_fast(opportunities[0])
            
            return opportunities
            
        except Exception as e:
            print(f"❌ Ошибка сканирования: {e}")
            return []
    
    def _analyze_triangle_fast(self, triangle, tickers):
        """Быстрый анализ треугольника"""
        try:
            pair1, pair2, pair3, direction = triangle
            
            # Проверяем наличие тикеров
            if not all(pair in tickers for pair in [pair1, pair2, pair3]):
                return None
            
            t1, t2, t3 = tickers[pair1], tickers[pair2], tickers[pair3]
            
            # Проверяем наличие цен
            if not all(t['bid'] and t['ask'] for t in [t1, t2, t3]):
                return None
            
            # Быстрый расчет прибыли
            amount = 1000.0  # USDT
            
            # Шаг 1: USDT -> base1
            base1_amount = amount / t1['ask']
            
            # Шаг 2: base1 -> base2
            if direction == 'direct':
                base2_amount = base1_amount * t2['bid']
            else:  # reverse
                base2_amount = base1_amount / t2['ask']
            
            # Шаг 3: base2 -> USDT
            final_amount = base2_amount * t3['bid']
            
            profit_percent = ((final_amount - amount) / amount) * 100
            
            if profit_percent < self.min_profit:
                return None
            
            return {
                'triangle': triangle,
                'profit_percent': profit_percent,
                'profit_usd': final_amount - amount,
                'path': f"{self.quote} → {pair1.split('/')[0]} → {pair3.split('/')[0]} → {self.quote}",
                'final_amount': final_amount,
                'timestamp': datetime.now()
            }
            
        except Exception:
            return None
    
    async def _execute_fast(self, opportunity):
        """Быстрое исполнение"""
        exec_start = time.time()
        
        try:
            if self.trading_mode == 'test':
                # Симуляция
                await asyncio.sleep(0.01)  # Минимальная задержка
                profit = opportunity['profit_usd']
                self.stats['trades_executed'] += 1
                self.stats['total_profit'] += profit
                
                exec_time = time.time() - exec_start
                if exec_time < self.stats['fastest_execution']:
                    self.stats['fastest_execution'] = exec_time
                
                print(f"   ✅ СИМУЛЯЦИЯ: +${profit:.2f} за {exec_time:.3f}с")
                return True
            
            else:
                # Реальное исполнение (если есть API ключи)
                print(f"   🚀 РЕАЛЬНОЕ ИСПОЛНЕНИЕ: {opportunity['path']}")
                # Здесь будет код реального исполнения
                return False
                
        except Exception as e:
            print(f"   ❌ Ошибка исполнения: {e}")
            return False
    
    async def run_ultra_fast(self):
        """Ультра-быстрый основной цикл"""
        print("🚀 Запуск ультра-быстрого треугольного арбитража...")
        print(f"⚙️ Режим: {self.trading_mode}")
        print(f"💰 Минимальная прибыль: {self.min_profit}%")
        print(f"📊 Треугольников: {len(self.triangles)}")
        
        self.is_running = True
        
        while self.is_running:
            try:
                await self.scan_opportunities()
                
                # Показываем статистику каждые 50 циклов
                if self.stats['cycles'] % 50 == 0:
                    self._print_stats()
                
                # Минимальная пауза для максимальной скорости
                await asyncio.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\n⏹️ Остановка...")
                break
            except Exception as e:
                print(f"❌ Ошибка цикла: {e}")
                await asyncio.sleep(1)
    
    def _print_stats(self):
        """Быстрая статистика"""
        uptime = time.time() - self.stats['start_time']
        cycles_per_sec = self.stats['cycles'] / uptime if uptime > 0 else 0
        
        print(f"\n⚡ СТАТИСТИКА (цикл {self.stats['cycles']}):")
        print(f"   Время работы: {uptime:.1f}с")
        print(f"   Циклов/сек: {cycles_per_sec:.2f}")
        print(f"   Средний цикл: {self.stats['avg_cycle_time']:.3f}с")
        print(f"   Найдено возможностей: {self.stats['opportunities_found']}")
        print(f"   Исполнено сделок: {self.stats['trades_executed']}")
        print(f"   Общая прибыль: ${self.stats['total_profit']:.2f}")
        if self.stats['fastest_execution'] != float('inf'):
            print(f"   Быстрейшее исполнение: {self.stats['fastest_execution']:.3f}с")
    
    async def stop(self):
        """Остановка"""
        self.is_running = False
        if self.exchange:
            await self.exchange.close()
        print("✅ Бот остановлен")

async def main():
    """Главная функция"""
    bot = UltraFastTriangularBot()
    
    try:
        if not await bot.initialize():
            return
        
        await bot.run_ultra_fast()
        
    except KeyboardInterrupt:
        print("\n⏹️ Принудительная остановка...")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())