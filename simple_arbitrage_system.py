#!/usr/bin/env python3
"""
Простая система треугольного арбитража
Только Bybit + Telegram уведомления о сделках
"""

import asyncio
import ccxt.pro as ccxt
import time
import itertools
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from telegram import Bot
from telegram.error import TelegramError

# Загружаем переменные окружения
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / 'auto_arbitrage_bot' / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

@dataclass
class Trade:
    """Информация о сделке"""
    symbol: str
    side: str  # buy/sell
    amount: float
    price: float
    timestamp: datetime
    order_id: str

@dataclass
class TriangularTrade:
    """Треугольная сделка"""
    path: str
    trades: List[Trade]
    expected_profit: float
    actual_profit: float
    execution_time: float
    success: bool

class SimpleArbitrageBot:
    """Простой бот треугольного арбитража"""
    
    def __init__(self):
        self.exchange = None
        self.telegram_bot = None
        self.markets = {}
        self.valid_triangles = []
        
        # Настройки
        self.min_profit = float(os.getenv('MIN_PROFIT_THRESHOLD', '0.75'))
        self.max_position = float(os.getenv('MAX_POSITION_SIZE', '50.0'))
        self.trading_mode = os.getenv('TRADING_MODE', 'live')
        
        # Telegram
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Статистика
        self.stats = {
            'start_time': time.time(),
            'total_trades': 0,
            'successful_trades': 0,
            'total_profit': 0.0,
            'opportunities_found': 0
        }
        
        self.setup_logging()
        self.is_running = False
    
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('arbitrage.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Инициализация"""
        self.logger.info("🚀 Инициализация простого арбитражного бота...")
        
        # Инициализация Bybit
        api_key = os.getenv('BYBIT_API_KEY')
        api_secret = os.getenv('BYBIT_API_SECRET')
        sandbox = os.getenv('BYBIT_SANDBOX', 'false').lower() == 'true'
        
        if not api_key or not api_secret:
            self.logger.error("❌ API ключи Bybit не найдены!")
            return False
        
        try:
            self.exchange = ccxt.bybit({
                'apiKey': api_key,
                'secret': api_secret,
                'sandbox': sandbox,
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })
            
            # Загружаем рынки
            self.markets = await self.exchange.load_markets()
            self.logger.info(f"✅ Загружено {len(self.markets)} торговых пар")
            
            # Инициализация Telegram
            if self.telegram_token and self.telegram_chat_id:
                self.telegram_bot = Bot(token=self.telegram_token)
                await self.send_telegram("🤖 Арбитражный бот запущен!")
                self.logger.info("✅ Telegram бот инициализирован")
            
            # Генерируем треугольники
            await self.generate_triangles()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации: {e}")
            return False
    
    async def generate_triangles(self):
        """Генерация треугольников"""
        self.logger.info("🔺 Генерация треугольников...")
        
        # Основные валюты для треугольников
        base_currencies = ['USDT', 'BTC', 'ETH']
        
        # Популярные криптовалюты
        crypto_currencies = [
            'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'AVAX',
            'MATIC', 'LINK', 'UNI', 'LTC', 'BCH', 'ATOM', 'FTM', 'NEAR'
        ]
        
        self.valid_triangles = []
        
        for base in base_currencies:
            # Находим пары с этой базовой валютой
            base_pairs = []
            for symbol in self.markets.keys():
                if '/' in symbol and symbol.endswith(f'/{base}'):
                    crypto = symbol.split('/')[0]
                    if crypto in crypto_currencies:
                        base_pairs.append(crypto)
            
            # Генерируем треугольники
            for crypto1, crypto2 in itertools.combinations(base_pairs, 2):
                # Проверяем существование всех пар
                pair1 = f"{crypto1}/{base}"
                pair2 = f"{crypto1}/{crypto2}"
                pair3 = f"{crypto2}/{base}"
                pair2_alt = f"{crypto2}/{crypto1}"
                
                if all(pair in self.markets for pair in [pair1, pair2, pair3]):
                    self.valid_triangles.append((pair1, pair2, pair3, 'direct'))
                
                if all(pair in self.markets for pair in [pair1, pair2_alt, pair3]):
                    self.valid_triangles.append((pair1, pair2_alt, pair3, 'reverse'))
        
        self.logger.info(f"✅ Сгенерировано {len(self.valid_triangles)} треугольников")
    
    async def send_telegram(self, message: str):
        """Отправка сообщения в Telegram"""
        if not self.telegram_bot or not self.telegram_chat_id:
            return
        
        try:
            await self.telegram_bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message,
                parse_mode='Markdown'
            )
        except TelegramError as e:
            self.logger.error(f"❌ Ошибка Telegram: {e}")
    
    async def find_opportunities(self):
        """Поиск арбитражных возможностей"""
        try:
            # Получаем тикеры
            tickers = await self.exchange.fetch_tickers()
            opportunities = []
            
            for triangle in self.valid_triangles:
                pair1, pair2, pair3, direction = triangle
                
                if not all(pair in tickers for pair in [pair1, pair2, pair3]):
                    continue
                
                t1, t2, t3 = tickers[pair1], tickers[pair2], tickers[pair3]
                
                if not all(t['bid'] and t['ask'] for t in [t1, t2, t3]):
                    continue
                
                # Расчет прибыли
                initial_amount = self.max_position
                
                # Шаг 1: покупаем первую валюту
                amount1 = initial_amount / t1['ask']
                
                # Шаг 2: обмениваем на вторую валюту
                if direction == 'direct':
                    amount2 = amount1 * t2['bid']
                else:
                    amount2 = amount1 / t2['ask']
                
                # Шаг 3: продаем за базовую валюту
                final_amount = amount2 * t3['bid']
                
                # Прибыль
                profit = final_amount - initial_amount
                profit_percent = (profit / initial_amount) * 100
                
                # Учитываем комиссии (0.1% за сделку)
                fees = initial_amount * 0.003  # 3 сделки
                net_profit = profit - fees
                net_profit_percent = (net_profit / initial_amount) * 100
                
                if net_profit_percent >= self.min_profit:
                    opportunities.append({
                        'triangle': triangle,
                        'path': f"{pair1.split('/')[1]} → {pair1.split('/')[0]} → {pair3.split('/')[0]} → {pair1.split('/')[1]}",
                        'profit_percent': net_profit_percent,
                        'profit_usd': net_profit,
                        'prices': {pair1: t1, pair2: t2, pair3: t3}
                    })
            
            # Сортируем по прибыли
            opportunities.sort(key=lambda x: x['profit_percent'], reverse=True)
            self.stats['opportunities_found'] += len(opportunities)
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка поиска возможностей: {e}")
            return []
    
    async def execute_triangular_trade(self, opportunity):
        """Исполнение треугольной сделки"""
        triangle = opportunity['triangle']
        pair1, pair2, pair3, direction = triangle
        
        self.logger.info(f"🚀 Исполнение: {opportunity['path']}")
        self.logger.info(f"💰 Ожидаемая прибыль: {opportunity['profit_percent']:.3f}%")
        
        if self.trading_mode == 'test':
            # Симуляция
            await self.send_telegram(f"""
🧪 **СИМУЛЯЦИЯ СДЕЛКИ**

🔺 Путь: `{opportunity['path']}`
💰 Прибыль: {opportunity['profit_percent']:.3f}% (${opportunity['profit_usd']:.2f})
⏰ Время: {datetime.now().strftime('%H:%M:%S')}
            """)
            
            self.stats['total_trades'] += 1
            self.stats['successful_trades'] += 1
            self.stats['total_profit'] += opportunity['profit_usd']
            return True
        
        # Реальная торговля
        trades = []
        start_time = time.time()
        
        try:
            initial_amount = self.max_position
            
            # Сделка 1
            self.logger.info(f"1️⃣ Покупка {pair1}")
            order1 = await self.exchange.create_market_buy_order(
                pair1, initial_amount / opportunity['prices'][pair1]['ask']
            )
            
            if order1['status'] != 'closed':
                raise Exception("Первая сделка не исполнена")
            
            trades.append(Trade(
                symbol=pair1,
                side='buy',
                amount=order1['filled'],
                price=order1['average'],
                timestamp=datetime.now(),
                order_id=order1['id']
            ))
            
            amount1 = order1['filled']
            
            # Сделка 2
            self.logger.info(f"2️⃣ Обмен {pair2}")
            if direction == 'direct':
                order2 = await self.exchange.create_market_sell_order(pair2, amount1)
            else:
                order2 = await self.exchange.create_market_buy_order(pair2, amount1)
            
            if order2['status'] != 'closed':
                raise Exception("Вторая сделка не исполнена")
            
            trades.append(Trade(
                symbol=pair2,
                side='sell' if direction == 'direct' else 'buy',
                amount=order2['filled'],
                price=order2['average'],
                timestamp=datetime.now(),
                order_id=order2['id']
            ))
            
            amount2 = order2['filled']
            
            # Сделка 3
            self.logger.info(f"3️⃣ Продажа {pair3}")
            order3 = await self.exchange.create_market_sell_order(pair3, amount2)
            
            if order3['status'] != 'closed':
                raise Exception("Третья сделка не исполнена")
            
            trades.append(Trade(
                symbol=pair3,
                side='sell',
                amount=order3['filled'],
                price=order3['average'],
                timestamp=datetime.now(),
                order_id=order3['id']
            ))
            
            # Расчет фактической прибыли
            final_amount = order3['filled'] * order3['average']
            actual_profit = final_amount - initial_amount
            execution_time = time.time() - start_time
            
            # Создаем объект сделки
            triangular_trade = TriangularTrade(
                path=opportunity['path'],
                trades=trades,
                expected_profit=opportunity['profit_usd'],
                actual_profit=actual_profit,
                execution_time=execution_time,
                success=True
            )
            
            # Отправляем уведомление
            await self.send_trade_notification(triangular_trade)
            
            # Обновляем статистику
            self.stats['total_trades'] += 1
            self.stats['successful_trades'] += 1
            self.stats['total_profit'] += actual_profit
            
            self.logger.info(f"✅ Сделка успешна! Прибыль: ${actual_profit:.2f}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка исполнения: {e}")
            
            # Уведомление об ошибке
            await self.send_telegram(f"""
❌ **ОШИБКА СДЕЛКИ**

🔺 Путь: `{opportunity['path']}`
❌ Ошибка: {str(e)}
⏰ Время: {datetime.now().strftime('%H:%M:%S')}
            """)
            
            self.stats['total_trades'] += 1
            return False
    
    async def send_trade_notification(self, trade: TriangularTrade):
        """Отправка уведомления о сделке"""
        profit_emoji = "💰" if trade.actual_profit > 0 else "💸"
        
        message = f"""
✅ **ТРЕУГОЛЬНАЯ СДЕЛКА ИСПОЛНЕНА**

🔺 Путь: `{trade.path}`
{profit_emoji} Прибыль: ${trade.actual_profit:.2f}
📊 Ожидалось: ${trade.expected_profit:.2f}
⏱️ Время исполнения: {trade.execution_time:.2f}с

📋 **Детали сделок:**
"""
        
        for i, t in enumerate(trade.trades, 1):
            side_emoji = "🟢" if t.side == 'buy' else "🔴"
            message += f"""
{i}. {side_emoji} {t.side.upper()} {t.symbol}
   💱 Количество: {t.amount:.8f}
   💲 Цена: ${t.price:.6f}
   🆔 ID: `{t.order_id}`
"""
        
        message += f"""
📊 **Общая статистика:**
• Всего сделок: {self.stats['total_trades']}
• Успешных: {self.stats['successful_trades']}
• Общая прибыль: ${self.stats['total_profit']:.2f}
        """
        
        await self.send_telegram(message.strip())
    
    async def run(self):
        """Главный цикл"""
        self.logger.info("🚀 Запуск треугольного арбитража...")
        self.is_running = True
        
        cycle = 0
        
        while self.is_running:
            try:
                cycle += 1
                self.logger.info(f"🔄 Цикл {cycle} - {datetime.now().strftime('%H:%M:%S')}")
                
                # Ищем возможности
                opportunities = await self.find_opportunities()
                
                if opportunities:
                    self.logger.info(f"💡 Найдено {len(opportunities)} возможностей")
                    
                    # Исполняем лучшую возможность
                    best = opportunities[0]
                    await self.execute_triangular_trade(best)
                else:
                    self.logger.info("📊 Прибыльных возможностей не найдено")
                
                # Статистика каждые 20 циклов
                if cycle % 20 == 0:
                    uptime = time.time() - self.stats['start_time']
                    success_rate = (self.stats['successful_trades'] / max(1, self.stats['total_trades'])) * 100
                    
                    self.logger.info(f"📊 Статистика: время работы {uptime/3600:.1f}ч, "
                                   f"сделок {self.stats['total_trades']}, "
                                   f"успешность {success_rate:.1f}%, "
                                   f"прибыль ${self.stats['total_profit']:.2f}")
                
                # Пауза между циклами
                await asyncio.sleep(60)  # 1 минута
                
            except KeyboardInterrupt:
                self.logger.info("⏹️ Остановка по запросу пользователя")
                break
            except Exception as e:
                self.logger.error(f"❌ Ошибка цикла: {e}")
                await asyncio.sleep(30)
        
        self.is_running = False
        
        # Финальная статистика
        await self.send_telegram(f"""
🛑 **БОТ ОСТАНОВЛЕН**

📊 **Финальная статистика:**
• Время работы: {(time.time() - self.stats['start_time'])/3600:.1f} часов
• Всего сделок: {self.stats['total_trades']}
• Успешных: {self.stats['successful_trades']}
• Общая прибыль: ${self.stats['total_profit']:.2f}
• Найдено возможностей: {self.stats['opportunities_found']}
        """)
        
        if self.exchange:
            await self.exchange.close()

async def main():
    """Главная функция"""
    print("🔺 ПРОСТАЯ СИСТЕМА ТРЕУГОЛЬНОГО АРБИТРАЖА")
    print("=" * 50)
    print("🤖 Только Bybit + Telegram уведомления")
    print("=" * 50)
    
    bot = SimpleArbitrageBot()
    
    try:
        if await bot.initialize():
            await bot.run()
        else:
            print("❌ Не удалось инициализировать бота")
    except KeyboardInterrupt:
        print("\n⏹️ Остановка...")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())