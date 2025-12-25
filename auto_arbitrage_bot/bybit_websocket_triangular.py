#!/usr/bin/env python3
"""
WebSocket треугольный арбитраж на Bybit
Максимальная скорость, без блокировок API, реальное время
"""

import ccxt.pro as ccxt
import asyncio
import time
import itertools
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
import logging
from collections import defaultdict

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

class BybitWebSocketTriangularBot:
    """WebSocket треугольный арбитражный бот для максимальной скорости"""
    
    def __init__(self):
        self.exchange = None
        self.markets = {}
        self.tickers = {}
        self.all_currencies = set()
        self.valid_triangles = []
        self.websocket_symbols = set()
        
        # Настройки торговли
        self.min_profit = float(os.getenv('MIN_PROFIT_THRESHOLD', '0.5'))
        self.max_position = float(os.getenv('MAX_POSITION_SIZE', '50.0'))
        self.trading_mode = os.getenv('TRADING_MODE', 'test')
        
        # Настройки WebSocket
        self.max_symbols_per_stream = 200  # Лимит Bybit
        self.update_frequency = 0.1  # Анализ каждые 100мс
        
        # Статистика
        self.stats = {
            'start_time': time.time(),
            'updates_received': 0,
            'opportunities_found': 0,
            'trades_executed': 0,
            'successful_trades': 0,
            'total_profit': 0.0,
            'best_opportunity': None,
            'last_opportunity_time': None
        }
        
        # Настройка логирования
        self.setup_logging()
        
        self.is_running = False
    
    def setup_logging(self):
        """Настройка логирования"""
        log_dir = current_dir / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'bybit_websocket_triangular.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Инициализация WebSocket подключения"""
        self.logger.info("🚀 Инициализация WebSocket треугольного арбитража...")
        
        # Получаем API ключи
        api_key = os.getenv('BYBIT_API_KEY')
        api_secret = os.getenv('BYBIT_API_SECRET')
        sandbox = os.getenv('BYBIT_SANDBOX', 'false').lower() == 'true'
        
        try:
            # Инициализируем exchange с WebSocket поддержкой
            self.exchange = ccxt.bybit({
                'apiKey': api_key,
                'secret': api_secret,
                'sandbox': sandbox,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                    'adjustForTimeDifference': True
                }
            })
            
            self.logger.info(f"🔑 API настроен (sandbox: {sandbox})")
            
            # Загружаем рынки
            self.markets = await self.exchange.load_markets()
            self.logger.info(f"✅ Загружено {len(self.markets)} торговых пар")
            
            # Генерируем все треугольники
            await self.generate_all_triangles()
            
            # Подготавливаем символы для WebSocket
            await self.prepare_websocket_symbols()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации: {e}")
            return False
    
    async def generate_all_triangles(self):
        """Генерация всех возможных треугольников"""
        self.logger.info("🔺 Генерация всех треугольников из всех валют...")
        
        # Извлекаем все валюты
        self.all_currencies = set()
        quote_currencies = {'USDT', 'USDC', 'BTC', 'ETH'}
        
        for symbol in self.markets.keys():
            if '/' in symbol and self.markets[symbol]['active']:
                base, quote = symbol.split('/')
                self.all_currencies.add(base)
                self.all_currencies.add(quote)
        
        # Фильтруем служебные токены
        excluded_patterns = [
            'UP', 'DOWN', 'BEAR', 'BULL', '3L', '3S', '5L', '5S',
            'LEVERAGED', 'INVERSE', 'PERP', 'SWAP', 'TEST'
        ]
        
        self.all_currencies = {
            curr for curr in self.all_currencies 
            if not any(pattern in curr for pattern in excluded_patterns) 
            and len(curr) <= 10
        }
        
        self.logger.info(f"💎 Найдено {len(self.all_currencies)} уникальных валют")
        
        # Генерируем треугольники
        self.valid_triangles = []
        
        for quote in quote_currencies:
            if quote not in self.all_currencies:
                continue
            
            # Валюты, торгующиеся против базовой
            quote_pairs = [
                curr for curr in self.all_currencies 
                if f"{curr}/{quote}" in self.markets and curr != quote
            ]
            
            # Ограничиваем количество для производительности
            quote_pairs = quote_pairs[:50]  # Топ-50 валют для каждой базовой
            
            for base1, base2 in itertools.combinations(quote_pairs, 2):
                pair1 = f"{base1}/{quote}"
                pair2 = f"{base1}/{base2}"
                pair3 = f"{base2}/{quote}"
                pair2_alt = f"{base2}/{base1}"
                
                # Проверяем существование и активность пар
                if all(pair in self.markets and self.markets[pair]['active'] 
                       for pair in [pair1, pair2, pair3]):
                    self.valid_triangles.append((pair1, pair2, pair3, 'direct', quote))
                
                if all(pair in self.markets and self.markets[pair]['active'] 
                       for pair in [pair1, pair2_alt, pair3]):
                    self.valid_triangles.append((pair1, pair2_alt, pair3, 'reverse', quote))
        
        self.logger.info(f"🔺 Сгенерировано {len(self.valid_triangles)} валидных треугольников")
        
        # Показываем примеры
        for i, triangle in enumerate(self.valid_triangles[:10]):
            pair1, pair2, pair3, direction, quote = triangle
            base1 = pair1.split('/')[0]
            base2 = pair3.split('/')[0]
            path = f"{quote} → {base1} → {base2} → {quote}"
            self.logger.info(f"   {i+1}. {path}")
    
    async def prepare_websocket_symbols(self):
        """Подготовка символов для WebSocket подписки"""
        # Собираем все уникальные символы из треугольников
        self.websocket_symbols = set()
        
        for triangle in self.valid_triangles:
            pair1, pair2, pair3, _, _ = triangle
            self.websocket_symbols.update([pair1, pair2, pair3])
        
        # Ограничиваем количество символов лимитом Bybit
        if len(self.websocket_symbols) > self.max_symbols_per_stream:
            # Приоритизируем по объему торгов
            symbol_volumes = {}
            try:
                tickers = await self.exchange.fetch_tickers()
                for symbol in self.websocket_symbols:
                    if symbol in tickers:
                        symbol_volumes[symbol] = tickers[symbol].get('quoteVolume', 0)
            except:
                pass
            
            # Берем топ символы по объему
            sorted_symbols = sorted(
                self.websocket_symbols, 
                key=lambda s: symbol_volumes.get(s, 0), 
                reverse=True
            )
            self.websocket_symbols = set(sorted_symbols[:self.max_symbols_per_stream])
        
        self.logger.info(f"📡 Подготовлено {len(self.websocket_symbols)} символов для WebSocket")
    
    async def start_websocket_streams(self):
        """Запуск WebSocket потоков для получения тикеров в реальном времени"""
        self.logger.info("📡 Запуск WebSocket потоков...")
        
        try:
            # Подписываемся на тикеры всех нужных символов
            tasks = []
            for symbol in self.websocket_symbols:
                task = asyncio.create_task(self.watch_ticker(symbol))
                tasks.append(task)
            
            # Запускаем анализ в отдельной задаче
            analysis_task = asyncio.create_task(self.continuous_analysis())
            tasks.append(analysis_task)
            
            # Ждем завершения всех задач
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка WebSocket потоков: {e}")
    
    async def watch_ticker(self, symbol: str):
        """Отслеживание тикера через WebSocket"""
        try:
            while self.is_running:
                ticker = await self.exchange.watch_ticker(symbol)
                self.tickers[symbol] = ticker
                self.stats['updates_received'] += 1
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка отслеживания {symbol}: {e}")
    
    async def continuous_analysis(self):
        """Непрерывный анализ возможностей"""
        self.logger.info("🔍 Запуск непрерывного анализа...")
        
        while self.is_running:
            try:
                # Анализируем возможности с текущими данными
                opportunities = await self.analyze_all_triangles()
                
                if opportunities:
                    await self.handle_opportunities(opportunities)
                
                # Короткая пауза для оптимальной производительности
                await asyncio.sleep(self.update_frequency)
                
            except Exception as e:
                self.logger.error(f"❌ Ошибка анализа: {e}")
                await asyncio.sleep(1)
    
    async def analyze_all_triangles(self) -> List[Dict]:
        """Анализ всех треугольников с текущими данными"""
        opportunities = []
        
        if len(self.tickers) < 10:  # Ждем достаточно данных
            return opportunities
        
        for triangle in self.valid_triangles:
            opportunity = await self.analyze_triangle_fast(triangle)
            if opportunity:
                opportunities.append(opportunity)
        
        # Сортируем по прибыльности
        opportunities.sort(key=lambda x: x['net_profit_percent'], reverse=True)
        
        return opportunities
    
    async def analyze_triangle_fast(self, triangle_data: Tuple) -> Optional[Dict]:
        """Быстрый анализ треугольника"""
        try:
            pair1, pair2, pair3, direction, quote_currency = triangle_data
            
            # Проверяем наличие свежих данных
            if not all(pair in self.tickers for pair in [pair1, pair2, pair3]):
                return None
            
            t1, t2, t3 = self.tickers[pair1], self.tickers[pair2], self.tickers[pair3]
            
            # Проверяем актуальность данных (не старше 5 секунд)
            current_time = time.time() * 1000
            for ticker in [t1, t2, t3]:
                if current_time - ticker.get('timestamp', 0) > 5000:
                    return None
            
            # Проверяем наличие цен
            if not all(t['bid'] and t['ask'] for t in [t1, t2, t3]):
                return None
            
            # Быстрый расчет прибыли
            initial_amount = 100.0
            
            # Шаг 1: quote -> base1
            base1_amount = initial_amount / t1['ask']
            base1_currency = pair1.split('/')[0]
            
            # Шаг 2: base1 -> base2
            base2_currency = pair3.split('/')[0]
            
            if direction == 'direct':
                base2_amount = base1_amount * t2['bid']
            else:
                base2_amount = base1_amount / t2['ask']
            
            # Шаг 3: base2 -> quote
            final_amount = base2_amount * t3['bid']
            
            # Расчет прибыли
            profit_amount = final_amount - initial_amount
            profit_percent = (profit_amount / initial_amount) * 100
            
            # Быстрая фильтрация
            if profit_percent < self.min_profit:
                return None
            
            # Расчет комиссий
            total_fees = initial_amount * 0.003  # 0.1% × 3 сделки
            net_profit = profit_amount - total_fees
            net_profit_percent = (net_profit / initial_amount) * 100
            
            if net_profit_percent < 0.2:
                return None
            
            # Проверяем объемы
            volumes = [
                t1.get('quoteVolume', 0),
                t2.get('quoteVolume', 0) or t2.get('baseVolume', 0),
                t3.get('quoteVolume', 0)
            ]
            min_volume = min(volumes)
            
            if min_volume < 5000:
                return None
            
            path = f"{quote_currency} → {base1_currency} → {base2_currency} → {quote_currency}"
            
            return {
                'path': path,
                'triangle': (pair1, pair2, pair3),
                'profit_percent': profit_percent,
                'net_profit_percent': net_profit_percent,
                'profit_usd': profit_amount,
                'net_profit_usd': net_profit,
                'fees_usd': total_fees,
                'min_volume': min_volume,
                'timestamp': datetime.now(),
                'data_age': max(current_time - t['timestamp'] for t in [t1, t2, t3]) / 1000,
                'prices': {
                    pair1: {'ask': t1['ask'], 'bid': t1['bid']},
                    pair2: {'ask': t2['ask'], 'bid': t2['bid']},
                    pair3: {'ask': t3['ask'], 'bid': t3['bid']}
                }
            }
            
        except Exception:
            return None
    
    async def handle_opportunities(self, opportunities: List[Dict]):
        """Обработка найденных возможностей"""
        if not opportunities:
            return
        
        # Обновляем статистику
        self.stats['opportunities_found'] += len(opportunities)
        self.stats['last_opportunity_time'] = time.time()
        
        # Сохраняем лучшую возможность
        best = opportunities[0]
        if (self.stats['best_opportunity'] is None or 
            best['net_profit_percent'] > self.stats['best_opportunity']['net_profit_percent']):
            self.stats['best_opportunity'] = best
        
        # Логируем только значимые возможности
        significant_opportunities = [opp for opp in opportunities if opp['net_profit_percent'] > 1.0]
        
        if significant_opportunities:
            self.logger.info(f"🎯 НАЙДЕНО {len(opportunities)} ВОЗМОЖНОСТЕЙ! (значимых: {len(significant_opportunities)})")
            
            for i, opp in enumerate(significant_opportunities[:5], 1):
                data_age = opp.get('data_age', 0)
                self.logger.info(f"{i}. {opp['path']}")
                self.logger.info(f"   💰 Чистая прибыль: {opp['net_profit_percent']:.3f}% (${opp['net_profit_usd']:.2f})")
                self.logger.info(f"   📊 Объем: ${opp['min_volume']:,.0f}")
                self.logger.info(f"   ⏱️ Возраст данных: {data_age:.1f}с")
            
            # Исполняем лучшую возможность если она очень хорошая
            if best['net_profit_percent'] > 2.0 and best.get('data_age', 0) < 1.0:
                await self.execute_opportunity(best)
    
    async def execute_opportunity(self, opportunity: Dict):
        """Исполнение возможности"""
        if self.trading_mode == 'test':
            self.logger.info(f"🧪 СИМУЛЯЦИЯ: {opportunity['path']}")
            self.logger.info(f"   💰 Прибыль: {opportunity['net_profit_percent']:.3f}% (${opportunity['net_profit_usd']:.2f})")
            
            self.stats['trades_executed'] += 1
            self.stats['successful_trades'] += 1
            self.stats['total_profit'] += opportunity['net_profit_usd']
            
            return True
        
        # Реальное исполнение
        self.logger.info(f"🚀 ИСПОЛНЕНИЕ: {opportunity['path']}")
        
        try:
            # Здесь будет код реального исполнения
            # Пока что симуляция
            await asyncio.sleep(0.1)
            
            self.stats['trades_executed'] += 1
            self.stats['successful_trades'] += 1
            self.stats['total_profit'] += opportunity['net_profit_usd']
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка исполнения: {e}")
            return False
    
    def print_stats(self):
        """Вывод статистики"""
        uptime = time.time() - self.stats['start_time']
        updates_per_sec = self.stats['updates_received'] / uptime if uptime > 0 else 0
        
        self.logger.info("📊 WEBSOCKET СТАТИСТИКА:")
        self.logger.info(f"   ⏰ Время работы: {uptime/60:.1f} мин")
        self.logger.info(f"   📡 Обновлений получено: {self.stats['updates_received']}")
        self.logger.info(f"   📈 Обновлений/сек: {updates_per_sec:.1f}")
        self.logger.info(f"   💡 Найдено возможностей: {self.stats['opportunities_found']}")
        self.logger.info(f"   📈 Исполнено сделок: {self.stats['trades_executed']}")
        self.logger.info(f"   ✅ Успешных: {self.stats['successful_trades']}")
        self.logger.info(f"   💰 Общая прибыль: ${self.stats['total_profit']:.2f}")
        
        if self.stats['best_opportunity']:
            best = self.stats['best_opportunity']
            self.logger.info(f"   🏆 Лучшая возможность: {best['net_profit_percent']:.3f}% ({best['path']})")
        
        if self.stats['last_opportunity_time']:
            time_since_last = time.time() - self.stats['last_opportunity_time']
            self.logger.info(f"   🕐 Последняя возможность: {time_since_last:.1f}с назад")
    
    async def run_websocket_arbitrage(self):
        """Запуск WebSocket арбитража"""
        self.logger.info("🚀 ЗАПУСК WEBSOCKET ТРЕУГОЛЬНОГО АРБИТРАЖА")
        self.logger.info("=" * 70)
        self.logger.info(f"💰 Минимальная прибыль: {self.min_profit}%")
        self.logger.info(f"🔺 Треугольников: {len(self.valid_triangles)}")
        self.logger.info(f"📡 WebSocket символов: {len(self.websocket_symbols)}")
        self.logger.info(f"⚡ Частота анализа: {1/self.update_frequency:.0f} раз/сек")
        self.logger.info(f"⚙️ Режим: {self.trading_mode}")
        self.logger.info("=" * 70)
        
        self.is_running = True
        
        try:
            # Запускаем WebSocket потоки
            await self.start_websocket_streams()
            
        except KeyboardInterrupt:
            self.logger.info("\n⏹️ Остановка WebSocket арбитража...")
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка: {e}")
        finally:
            self.is_running = False
            self.print_stats()
            if self.exchange:
                await self.exchange.close()
            self.logger.info("✅ WebSocket арбитраж остановлен")

async def main():
    """Главная функция"""
    bot = BybitWebSocketTriangularBot()
    
    try:
        if await bot.initialize():
            # Запускаем статистику в отдельной задаче
            stats_task = asyncio.create_task(periodic_stats(bot))
            
            # Запускаем основной цикл
            await bot.run_websocket_arbitrage()
            
        else:
            print("❌ Не удалось инициализировать WebSocket бота")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

async def periodic_stats(bot):
    """Периодический вывод статистики"""
    while bot.is_running:
        await asyncio.sleep(60)  # Каждую минуту
        bot.print_stats()

if __name__ == "__main__":
    asyncio.run(main())