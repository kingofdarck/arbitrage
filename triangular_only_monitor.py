#!/usr/bin/env python3
"""
Упрощенный монитор ТОЛЬКО треугольного арбитража
Максимальная скорость, минимум кода
"""

import asyncio
import aiohttp
import time
import itertools
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json

# Импорт конфигурации и уведомлений
from config import *
from notifications import send_notification

class TriangularOnlyMonitor:
    """Монитор только треугольного арбитража"""
    
    def __init__(self):
        self.session = None
        self.triangular_opportunities = []
        self.last_notification_time = 0
        self.notification_interval = 30  # секунд
        
        # Основные валюты для треугольного арбитража
        self.currencies = [
            'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'AVAX', 
            'MATIC', 'LINK', 'UNI', 'LTC', 'BCH', 'ETC', 'ATOM'
        ]
        self.quote_currency = 'USDT'
        
        # Статистика
        self.stats = {
            'cycles': 0,
            'opportunities_found': 0,
            'notifications_sent': 0,
            'start_time': time.time()
        }
    
    async def initialize(self):
        """Инициализация"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            connector=aiohttp.TCPConnector(limit=100)
        )
        print("✅ Треугольный монитор инициализирован")
    
    async def get_binance_tickers(self) -> Dict[str, Dict]:
        """Получение тикеров с Binance"""
        try:
            url = "https://api.binance.com/api/v3/ticker/24hr"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    tickers = {}
                    
                    for ticker in data:
                        symbol = ticker['symbol']
                        # Преобразуем в формат BASE/QUOTE
                        if symbol.endswith('USDT'):
                            base = symbol[:-4]
                            formatted_symbol = f"{base}/USDT"
                            tickers[formatted_symbol] = {
                                'bid': float(ticker['bidPrice']),
                                'ask': float(ticker['askPrice']),
                                'volume': float(ticker['volume']),
                                'quoteVolume': float(ticker['quoteVolume'])
                            }
                    
                    return tickers
        except Exception as e:
            print(f"❌ Ошибка получения тикеров Binance: {e}")
        
        return {}
    
    def generate_triangular_combinations(self) -> List[Tuple[str, str, str]]:
        """Генерация треугольных комбинаций"""
        triangles = []
        
        for base1, base2 in itertools.combinations(self.currencies, 2):
            # Проверяем существование пар
            pair1 = f"{base1}/{self.quote_currency}"  # BTC/USDT
            pair2 = f"{base1}/{base2}"                # BTC/ETH  
            pair3 = f"{base2}/{self.quote_currency}"  # ETH/USDT
            
            # Альтернативный порядок для pair2
            pair2_alt = f"{base2}/{base1}"            # ETH/BTC
            
            triangles.append((pair1, pair2, pair3))
            triangles.append((pair1, pair2_alt, pair3))
        
        return triangles
    
    def analyze_triangular_opportunity(self, triangle: Tuple[str, str, str], tickers: Dict) -> Optional[Dict]:
        """Анализ треугольной возможности"""
        try:
            pair1, pair2, pair3 = triangle
            
            # Проверяем наличие всех тикеров
            if not all(pair in tickers for pair in triangle):
                return None
            
            ticker1 = tickers[pair1]
            ticker2 = tickers[pair2]
            ticker3 = tickers[pair3]
            
            # Проверяем наличие цен
            if not all(ticker['bid'] > 0 and ticker['ask'] > 0 for ticker in [ticker1, ticker2, ticker3]):
                return None
            
            # Расчет треугольного арбитража
            initial_amount = 1000.0  # USDT
            
            # Путь: USDT -> base1 -> base2 -> USDT
            # Шаг 1: Покупаем base1 за USDT
            base1_amount = initial_amount / ticker1['ask']
            
            # Шаг 2: Обмениваем base1 на base2
            base1_currency = pair1.split('/')[0]
            base2_currency = pair3.split('/')[0]
            
            if pair2 == f"{base1_currency}/{base2_currency}":
                # Прямой порядок: BTC/ETH
                base2_amount = base1_amount * ticker2['bid']
            else:
                # Обратный порядок: ETH/BTC
                base2_amount = base1_amount / ticker2['ask']
            
            # Шаг 3: Продаем base2 за USDT
            final_amount = base2_amount * ticker3['bid']
            
            # Расчет прибыли
            profit_amount = final_amount - initial_amount
            profit_percent = (profit_amount / initial_amount) * 100
            
            # Проверяем минимальную прибыль
            min_profit = ARBITRAGE_CONFIG['triangular']['min_profit']
            if profit_percent < min_profit:
                return None
            
            # Проверяем объемы
            min_volume = 10000  # USD
            volumes = [ticker1['quoteVolume'], ticker2.get('quoteVolume', 0), ticker3['quoteVolume']]
            if min(volumes) < min_volume:
                return None
            
            return {
                'type': 'triangular',
                'triangle': triangle,
                'path': f"{self.quote_currency} → {base1_currency} → {base2_currency} → {self.quote_currency}",
                'profit_percent': profit_percent,
                'profit_usd': profit_amount,
                'initial_amount': initial_amount,
                'final_amount': final_amount,
                'exchange': 'Binance',
                'timestamp': datetime.now(),
                'confidence': 0.8,
                'steps': [
                    f"1. Купить {base1_currency} за {initial_amount:.2f} USDT по цене {ticker1['ask']:.8f}",
                    f"2. Обменять {base1_amount:.8f} {base1_currency} на {base2_amount:.8f} {base2_currency}",
                    f"3. Продать {base2_amount:.8f} {base2_currency} за {final_amount:.2f} USDT по цене {ticker3['bid']:.8f}"
                ]
            }
            
        except Exception as e:
            print(f"❌ Ошибка анализа треугольника {triangle}: {e}")
            return None
    
    async def scan_triangular_arbitrage(self) -> List[Dict]:
        """Сканирование треугольного арбитража"""
        opportunities = []
        
        try:
            # Получаем тикеры
            print("📊 Получение тикеров с Binance...")
            start_time = time.time()
            tickers = await self.get_binance_tickers()
            fetch_time = time.time() - start_time
            
            if not tickers:
                print("❌ Не удалось получить тикеры")
                return []
            
            print(f"✅ Получено {len(tickers)} тикеров за {fetch_time:.3f}с")
            
            # Генерируем треугольники
            triangles = self.generate_triangular_combinations()
            print(f"🔺 Анализируем {len(triangles)} треугольников...")
            
            # Анализируем каждый треугольник
            analysis_start = time.time()
            for triangle in triangles:
                opportunity = self.analyze_triangular_opportunity(triangle, tickers)
                if opportunity:
                    opportunities.append(opportunity)
            
            analysis_time = time.time() - analysis_start
            total_time = time.time() - start_time
            
            print(f"⚡ Анализ завершен за {analysis_time:.3f}с (общее время: {total_time:.3f}с)")
            
            if opportunities:
                # Сортируем по прибыльности
                opportunities.sort(key=lambda x: x['profit_percent'], reverse=True)
                print(f"💡 Найдено {len(opportunities)} треугольных возможностей!")
                
                # Показываем топ-5
                for i, opp in enumerate(opportunities[:5], 1):
                    print(f"   {i}. {opp['path']}: {opp['profit_percent']:.3f}% (${opp['profit_usd']:.2f})")
            else:
                print("   ℹ️ Треугольных возможностей не найдено")
            
            return opportunities
            
        except Exception as e:
            print(f"❌ Ошибка сканирования: {e}")
            return []
    
    async def send_opportunities_notification(self, opportunities: List[Dict]):
        """Отправка уведомлений о возможностях"""
        try:
            if not opportunities:
                return
            
            # Проверяем интервал уведомлений
            current_time = time.time()
            if current_time - self.last_notification_time < self.notification_interval:
                return
            
            # Формируем сообщение
            message = "🔺 ТРЕУГОЛЬНЫЙ АРБИТРАЖ\n"
            message += f"⏰ {datetime.now().strftime('%H:%M:%S')}\n\n"
            
            # Добавляем топ возможности
            for i, opp in enumerate(opportunities[:10], 1):
                message += f"{i}. {opp['path']}\n"
                message += f"   💰 Прибыль: {opp['profit_percent']:.3f}% (${opp['profit_usd']:.2f})\n"
                message += f"   🏛️ Биржа: {opp['exchange']}\n\n"
            
            # Добавляем статистику
            uptime = current_time - self.stats['start_time']
            message += f"📊 Статистика:\n"
            message += f"   Циклов: {self.stats['cycles']}\n"
            message += f"   Найдено: {self.stats['opportunities_found']}\n"
            message += f"   Время работы: {uptime/60:.1f} мин\n"
            
            # Отправляем уведомление
            await send_notification(message, notification_type='triangular')
            self.last_notification_time = current_time
            self.stats['notifications_sent'] += 1
            
            print(f"📱 Уведомление отправлено ({len(opportunities)} возможностей)")
            
        except Exception as e:
            print(f"❌ Ошибка отправки уведомления: {e}")
    
    async def run_monitoring_cycle(self):
        """Один цикл мониторинга"""
        try:
            self.stats['cycles'] += 1
            cycle_start = time.time()
            
            print(f"\n🔄 Цикл {self.stats['cycles']} - {datetime.now().strftime('%H:%M:%S')}")
            
            # Сканируем треугольный арбитраж
            opportunities = await self.scan_triangular_arbitrage()
            
            if opportunities:
                self.stats['opportunities_found'] += len(opportunities)
                self.triangular_opportunities = opportunities
                
                # Отправляем уведомления
                await self.send_opportunities_notification(opportunities)
            
            cycle_time = time.time() - cycle_start
            print(f"⏱️ Цикл завершен за {cycle_time:.3f}с")
            
        except Exception as e:
            print(f"❌ Ошибка цикла мониторинга: {e}")
    
    async def run(self):
        """Основной цикл мониторинга"""
        print("🚀 Запуск треугольного арбитражного монитора...")
        print(f"⚙️ Минимальная прибыль: {ARBITRAGE_CONFIG['triangular']['min_profit']}%")
        print(f"🔺 Валют для анализа: {len(self.currencies)}")
        print(f"📱 Уведомления: {'включены' if NOTIFICATION_CONFIG['telegram']['enabled'] else 'отключены'}")
        
        try:
            while True:
                await self.run_monitoring_cycle()
                
                # Пауза между циклами
                await asyncio.sleep(MONITORING_CONFIG['check_interval'])
                
        except KeyboardInterrupt:
            print("\n⏹️ Остановка мониторинга...")
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
        finally:
            if self.session:
                await self.session.close()
            print("✅ Монитор остановлен")

async def main():
    """Главная функция"""
    monitor = TriangularOnlyMonitor()
    
    try:
        await monitor.initialize()
        await monitor.run()
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")

if __name__ == "__main__":
    asyncio.run(main())