#!/usr/bin/env python3
"""
Упрощенный бот только для треугольного арбитража
Максимальная скорость исполнения
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

class TriangularArbitrageBot:
    """Упрощенный бот для треугольного арбитража"""
    
    def __init__(self):
        self.exchange = None
        self.markets = {}
        self.tickers = {}
        self.min_profit = float(os.getenv('MIN_PROFIT_THRESHOLD', '0.75'))
        self.max_position = float(os.getenv('MAX_POSITION_SIZE', '100.0'))
        self.is_running = False
        
        # Основные валюты для треугольного арбитража
        self.base_currencies = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'AVAX', 'MATIC', 'LINK']
        self.quote_currency = 'USDT'
        
        # Статистика
        self.stats = {
            'opportunities_found': 0,
            'trades_executed': 0,
            'total_profit': 0.0,
            'successful_trades': 0
        }
    
    async def initialize(self):
        """Инициализация бота"""
        print("🔺 Инициализация треугольного арбитражного бота...")
        
        # Настройка биржи
        api_key = os.getenv('BYBIT_API_KEY')
        api_secret = os.getenv('BYBIT_API_SECRET')
        sandbox = os.getenv('BYBIT_SANDBOX', 'true').lower() == 'true'
        
        if not api_key or not api_secret:
            print("❌ API ключи не найдены в переменных окружения")
            return False
        
        print(f"🔑 API Key: {api_key[:10]}... (длина: {len(api_key)})")
        print(f"🔐 Secret: {api_secret[:10]}... (длина: {len(api_secret)})")
        print(f"🧪 Sandbox режим: {sandbox}")
        
        try:
            self.exchange = ccxt.bybit({
                'apiKey': api_key,
                'secret': api_secret,
                'sandbox': sandbox,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                }
            })
            
            # Тест подключения
            print("🔌 Тестирование подключения...")
            self.markets = await self.exchange.load_markets()
            print(f"✅ Загружено {len(self.markets)} торговых пар")
            
            # Проверка баланса
            balance = await self.exchange.fetch_balance()
            print(f"✅ Баланс получен: {len(balance)} валют")
            
            # Показываем основные балансы
            for currency in ['USDT', 'BTC', 'ETH']:
                if currency in balance and balance[currency]['total'] > 0:
                    print(f"   {currency}: {balance[currency]['total']:.6f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка инициализации: {e}")
            return False
    
    async def find_triangular_opportunities(self) -> List[Dict]:
        """Поиск треугольных возможностей"""
        opportunities = []
        
        try:
            # Получаем свежие тикеры
            symbols_to_fetch = []
            triangles = []
            
            # Генерируем треугольники
            for base1 in self.base_currencies:
                for base2 in self.base_currencies:
                    if base1 == base2:
                        continue
                    
                    pair1 = f"{base1}/{self.quote_currency}"  # BTC/USDT
                    pair2 = f"{base1}/{base2}"                # BTC/ETH
                    pair3 = f"{base2}/{self.quote_currency}"  # ETH/USDT
                    
                    # Альтернативный порядок для pair2
                    pair2_alt = f"{base2}/{base1}"            # ETH/BTC
                    
                    if (pair1 in self.markets and 
                        (pair2 in self.markets or pair2_alt in self.markets) and
                        pair3 in self.markets):
                        
                        actual_pair2 = pair2 if pair2 in self.markets else pair2_alt
                        triangle = (pair1, actual_pair2, pair3)
                        triangles.append(triangle)
                        
                        symbols_to_fetch.extend([pair1, actual_pair2, pair3])
            
            # Убираем дубликаты
            symbols_to_fetch = list(set(symbols_to_fetch))
            
            # Получаем тикеры одним запросом для скорости
            print(f"📊 Получение тикеров для {len(symbols_to_fetch)} пар...")
            start_time = time.time()
            
            tickers = await self.exchange.fetch_tickers(symbols_to_fetch)
            
            fetch_time = time.time() - start_time
            print(f"⚡ Тикеры получены за {fetch_time:.3f}с")
            
            # Анализируем треугольники
            for triangle in triangles[:50]:  # Ограничиваем для скорости
                opportunity = await self._analyze_triangle(triangle, tickers)
                if opportunity:
                    opportunities.append(opportunity)
                    self.stats['opportunities_found'] += 1
            
            return opportunities
            
        except Exception as e:
            print(f"❌ Ошибка поиска возможностей: {e}")
            return []
    
    async def _analyze_triangle(self, triangle: Tuple[str, str, str], tickers: Dict) -> Optional[Dict]:
        """Анализ треугольной возможности"""
        try:
            pair1, pair2, pair3 = triangle
            
            # Проверяем наличие тикеров
            if not all(pair in tickers for pair in triangle):
                return None
            
            ticker1 = tickers[pair1]
            ticker2 = tickers[pair2]
            ticker3 = tickers[pair3]
            
            # Проверяем наличие цен
            if not all(ticker['bid'] and ticker['ask'] for ticker in [ticker1, ticker2, ticker3]):
                return None
            
            # Расчет прибыли
            initial_amount = 1000.0  # USDT
            
            # Путь: USDT -> BTC -> ETH -> USDT
            # Шаг 1: Покупаем BTC за USDT
            btc_amount = initial_amount / ticker1['ask']
            
            # Шаг 2: Обмениваем BTC на ETH
            if pair1.split('/')[0] == pair2.split('/')[0]:  # BTC/USDT и BTC/ETH
                eth_amount = btc_amount * ticker2['bid']
            else:  # BTC/USDT и ETH/BTC
                eth_amount = btc_amount / ticker2['ask']
            
            # Шаг 3: Продаем ETH за USDT
            final_amount = eth_amount * ticker3['bid']
            
            profit_percent = ((final_amount - initial_amount) / initial_amount) * 100
            
            # Проверяем минимальную прибыль
            if profit_percent < self.min_profit:
                return None
            
            # Проверяем объемы
            min_volume = min(ticker1['baseVolume'] or 0, ticker2['baseVolume'] or 0, ticker3['baseVolume'] or 0)
            if min_volume < 1000:  # Минимальный объем
                return None
            
            return {
                'type': 'triangular',
                'triangle': triangle,
                'profit_percent': profit_percent,
                'profit_usd': final_amount - initial_amount,
                'initial_amount': initial_amount,
                'final_amount': final_amount,
                'path': f"{self.quote_currency} → {pair1.split('/')[0]} → {pair3.split('/')[0]} → {self.quote_currency}",
                'tickers': {pair1: ticker1, pair2: ticker2, pair3: ticker3},
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Ошибка анализа треугольника {triangle}: {e}")
            return None
    
    async def execute_opportunity(self, opportunity: Dict) -> bool:
        """Быстрое исполнение треугольной возможности"""
        try:
            print(f"⚡ ИСПОЛНЕНИЕ: {opportunity['path']}")
            print(f"   Прибыль: {opportunity['profit_percent']:.3f}% (${opportunity['profit_usd']:.2f})")
            
            triangle = opportunity['triangle']
            pair1, pair2, pair3 = triangle
            
            # Определяем размер позиции
            position_size = min(self.max_position, opportunity['initial_amount'])
            
            start_time = time.time()
            
            # В тестовом режиме - симуляция
            trading_mode = os.getenv('TRADING_MODE', 'test')
            if trading_mode == 'test':
                await asyncio.sleep(0.1)  # Имитация времени исполнения
                print(f"   ✅ СИМУЛЯЦИЯ: Прибыль ${opportunity['profit_usd']:.2f}")
                self.stats['trades_executed'] += 1
                self.stats['successful_trades'] += 1
                self.stats['total_profit'] += opportunity['profit_usd']
                return True
            
            # Реальное исполнение (последовательно для треугольного арбитража)
            try:
                # Шаг 1: Покупаем первую валюту
                amount1 = position_size
                order1 = await self.exchange.create_market_buy_order(pair1, amount1 / opportunity['tickers'][pair1]['ask'])
                print(f"   1️⃣ {pair1}: Куплено {order1['filled']} за ${amount1:.2f}")
                
                # Шаг 2: Обмениваем на вторую валюту
                amount2 = order1['filled']
                if pair1.split('/')[0] == pair2.split('/')[0]:
                    order2 = await self.exchange.create_market_sell_order(pair2, amount2)
                else:
                    order2 = await self.exchange.create_market_buy_order(pair2, amount2)
                print(f"   2️⃣ {pair2}: Получено {order2['filled']}")
                
                # Шаг 3: Продаем за базовую валюту
                amount3 = order2['filled']
                order3 = await self.exchange.create_market_sell_order(pair3, amount3)
                final_amount = order3['filled'] * order3['average']
                print(f"   3️⃣ {pair3}: Продано за ${final_amount:.2f}")
                
                actual_profit = final_amount - position_size
                execution_time = time.time() - start_time
                
                print(f"   ✅ УСПЕХ: Прибыль ${actual_profit:.2f} за {execution_time:.3f}с")
                
                self.stats['trades_executed'] += 1
                self.stats['successful_trades'] += 1
                self.stats['total_profit'] += actual_profit
                
                return True
                
            except Exception as e:
                execution_time = time.time() - start_time
                print(f"   ❌ ОШИБКА ИСПОЛНЕНИЯ: {e} (за {execution_time:.3f}с)")
                self.stats['trades_executed'] += 1
                return False
                
        except Exception as e:
            print(f"❌ Критическая ошибка исполнения: {e}")
            return False
    
    async def run(self):
        """Основной цикл бота"""
        print("🚀 Запуск треугольного арбитражного бота...")
        self.is_running = True
        
        cycle_count = 0
        
        while self.is_running:
            try:
                cycle_count += 1
                cycle_start = time.time()
                
                print(f"\n🔄 Цикл {cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                # Поиск возможностей
                opportunities = await self.find_triangular_opportunities()
                
                if opportunities:
                    # Сортируем по прибыльности
                    opportunities.sort(key=lambda x: x['profit_percent'], reverse=True)
                    
                    print(f"💡 Найдено {len(opportunities)} возможностей:")
                    for i, opp in enumerate(opportunities[:5], 1):
                        print(f"   {i}. {opp['path']}: {opp['profit_percent']:.3f}% (${opp['profit_usd']:.2f})")
                    
                    # Исполняем лучшую возможность
                    best_opportunity = opportunities[0]
                    await self.execute_opportunity(best_opportunity)
                    
                else:
                    print("   ℹ️ Прибыльных возможностей не найдено")
                
                cycle_time = time.time() - cycle_start
                print(f"⏱️ Цикл завершен за {cycle_time:.3f}с")
                
                # Показываем статистику каждые 10 циклов
                if cycle_count % 10 == 0:
                    self._print_stats()
                
                # Пауза между циклами (минимальная для максимальной скорости)
                await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                print("\n⏹️ Остановка по запросу пользователя...")
                break
            except Exception as e:
                print(f"❌ Ошибка в цикле: {e}")
                await asyncio.sleep(5)
    
    def _print_stats(self):
        """Вывод статистики"""
        print(f"\n📊 СТАТИСТИКА:")
        print(f"   Найдено возможностей: {self.stats['opportunities_found']}")
        print(f"   Исполнено сделок: {self.stats['trades_executed']}")
        print(f"   Успешных сделок: {self.stats['successful_trades']}")
        print(f"   Общая прибыль: ${self.stats['total_profit']:.2f}")
        if self.stats['trades_executed'] > 0:
            success_rate = (self.stats['successful_trades'] / self.stats['trades_executed']) * 100
            avg_profit = self.stats['total_profit'] / self.stats['trades_executed']
            print(f"   Успешность: {success_rate:.1f}%")
            print(f"   Средняя прибыль: ${avg_profit:.2f}")
    
    async def stop(self):
        """Остановка бота"""
        self.is_running = False
        if self.exchange:
            await self.exchange.close()
        print("✅ Бот остановлен")

async def main():
    """Главная функция"""
    bot = TriangularArbitrageBot()
    
    try:
        # Инициализация
        if not await bot.initialize():
            print("❌ Не удалось инициализировать бота")
            return
        
        # Запуск
        await bot.run()
        
    except KeyboardInterrupt:
        print("\n⏹️ Принудительная остановка...")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())