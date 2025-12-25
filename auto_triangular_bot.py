#!/usr/bin/env python3
"""
Полностью автономный треугольный арбитраж бот для MEXC
- Сам находит треугольники
- Конвертирует в нужную валюту
- Исполняет на весь баланс
- Блокирует другие операции во время исполнения
- Отправляет отчеты в Telegram
"""

import asyncio
import ccxt.pro as ccxt
import time
import itertools
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
import json

# Загружаем переменные окружения
try:
    from dotenv import load_dotenv
    if os.path.exists('.env'):
        load_dotenv('.env')
except ImportError:
    pass

@dataclass
class TriangleResult:
    """Результат треугольного арбитража"""
    path: str
    initial_balance: float
    final_balance: float
    profit: float
    profit_percent: float
    trades: List[Dict]
    execution_time: float
    success: bool
    error: Optional[str] = None

class AutoTriangularBot:
    """Полностью автономный треугольный арбитраж бот"""
    
    def __init__(self):
        self.exchange = None
        self.telegram_bot = None
        self.markets = {}
        self.valid_triangles = []
        self.is_executing = False  # Флаг блокировки операций
        
        # Настройки
        self.min_profit = float(os.getenv('MIN_PROFIT_THRESHOLD', '0.5'))  # Снижаем порог
        self.min_balance_usdt = float(os.getenv('MIN_BALANCE_USDT', '10.0'))  # Минимальный баланс
        self.trading_mode = os.getenv('TRADING_MODE', 'live')
        
        # Telegram
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Статистика
        self.stats = {
            'start_time': time.time(),
            'total_triangles': 0,
            'successful_triangles': 0,
            'total_profit': 0.0,
            'cycles': 0,
            'last_execution': None
        }
        
        self.setup_logging()
        
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('auto_triangular.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Инициализация"""
        self.logger.info("🔺 Инициализация автономного треугольного арбитража...")
        
        # Инициализация MEXC
        api_key = os.getenv('MEXC_API_KEY')
        api_secret = os.getenv('MEXC_API_SECRET')
        sandbox = os.getenv('MEXC_SANDBOX', 'false').lower() == 'true'
        
        if not api_key or not api_secret:
            self.logger.error("❌ API ключи MEXC не найдены!")
            return False
        
        try:
            self.exchange = ccxt.mexc({
                'apiKey': api_key,
                'secret': api_secret,
                'sandbox': sandbox,
                'enableRateLimit': True,
                'rateLimit': 500,  # Быстрее для арбитража
                'options': {'defaultType': 'spot'}
            })
            
            # Загружаем рынки
            self.markets = await self.exchange.load_markets()
            self.logger.info(f"✅ Загружено {len(self.markets)} торговых пар MEXC")
            
            # Инициализация Telegram
            if self.telegram_token and self.telegram_chat_id:
                await self.send_telegram("🔺 **АВТОНОМНЫЙ ТРЕУГОЛЬНЫЙ АРБИТРАЖ ЗАПУЩЕН**\n\n✅ Подключение к MEXC установлено\n🤖 Полностью автономный режим\n💰 Операции на весь баланс")
                self.logger.info("✅ Telegram бот инициализирован")
            
            # Генерируем треугольники
            await self.generate_triangles()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации MEXC: {e}")
            return False
    
    async def send_telegram(self, message: str):
        """Отправка сообщения в Telegram"""
        if not self.telegram_token or not self.telegram_chat_id:
            return
        
        try:
            if not self.telegram_bot:
                from telegram import Bot
                self.telegram_bot = Bot(token=self.telegram_token)
            
            await self.telegram_bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            self.logger.error(f"❌ Ошибка Telegram: {e}")
    
    async def generate_triangles(self):
        """Генерация треугольных возможностей"""
        self.logger.info("🔺 Генерация треугольных возможностей...")
        
        # Основные валюты для треугольников
        base_currencies = ['USDT', 'BTC', 'ETH']
        
        # Популярные криптовалюты с хорошей ликвидностью
        crypto_currencies = [
            'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'AVAX',
            'MATIC', 'LINK', 'UNI', 'LTC', 'BCH', 'ATOM', 'FTM', 'NEAR',
            'ALGO', 'VET', 'ICP', 'SAND', 'MANA', 'CRV', 'AAVE', 'COMP',
            'DOGE', 'SHIB', 'TRX', 'ETC', 'FIL', 'XLM', 'HBAR', 'THETA'
        ]
        
        self.valid_triangles = []
        
        for base in base_currencies:
            # Находим пары с этой базовой валютой
            base_pairs = []
            for symbol in self.markets.keys():
                if '/' in symbol and symbol.endswith(f'/{base}'):
                    crypto = symbol.split('/')[0]
                    if crypto in crypto_currencies and crypto != base:
                        # Проверяем что пара активна
                        market = self.markets[symbol]
                        if market.get('active', True):
                            base_pairs.append(crypto)
            
            self.logger.info(f"📊 Для {base}: найдено {len(base_pairs)} активных валют")
            
            # Генерируем треугольники
            for crypto1, crypto2 in itertools.combinations(base_pairs, 2):
                # Треугольник: base -> crypto1 -> crypto2 -> base
                pair1 = f"{crypto1}/{base}"  # BTC/USDT
                pair2 = f"{crypto1}/{crypto2}"  # BTC/ETH
                pair3 = f"{crypto2}/{base}"  # ETH/USDT
                pair2_alt = f"{crypto2}/{crypto1}"  # ETH/BTC
                
                # Проверяем существование и активность всех пар
                if all(pair in self.markets and self.markets[pair].get('active', True) for pair in [pair1, pair2, pair3]):
                    self.valid_triangles.append((pair1, pair2, pair3, 'direct', base))
                
                if all(pair in self.markets and self.markets[pair].get('active', True) for pair in [pair1, pair2_alt, pair3]):
                    self.valid_triangles.append((pair1, pair2_alt, pair3, 'reverse', base))
        
        self.logger.info(f"✅ Сгенерировано {len(self.valid_triangles)} треугольных возможностей")
    
    async def get_balance(self, currency: str) -> float:
        """Получить баланс валюты"""
        try:
            balance = await self.exchange.fetch_balance()
            return balance.get(currency, {}).get('free', 0.0)
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения баланса {currency}: {e}")
            return 0.0
    
    async def convert_to_base_currency(self, base_currency: str) -> float:
        """Конвертировать весь баланс в базовую валюту"""
        try:
            balance = await self.exchange.fetch_balance()
            total_base = 0.0
            conversions = []
            
            for currency, info in balance.items():
                free_amount = info.get('free', 0.0)
                if free_amount > 0 and currency != base_currency:
                    # Пытаемся найти прямую пару
                    pair = f"{currency}/{base_currency}"
                    if pair in self.markets:
                        try:
                            ticker = await self.exchange.fetch_ticker(pair)
                            if ticker['bid'] > 0:
                                # Продаем валюту за базовую
                                order = await self.exchange.create_market_sell_order(pair, free_amount)
                                if order['status'] == 'closed':
                                    converted = order['filled'] * order['average']
                                    total_base += converted
                                    conversions.append(f"{currency}: {free_amount:.6f} → {converted:.6f} {base_currency}")
                                    self.logger.info(f"✅ Конвертировано {currency}: {free_amount:.6f} → {converted:.6f} {base_currency}")
                        except Exception as e:
                            self.logger.warning(f"⚠️ Не удалось конвертировать {currency}: {e}")
                    else:
                        # Пытаемся через обратную пару
                        reverse_pair = f"{base_currency}/{currency}"
                        if reverse_pair in self.markets:
                            try:
                                ticker = await self.exchange.fetch_ticker(reverse_pair)
                                if ticker['ask'] > 0:
                                    # Покупаем базовую валюту
                                    base_amount = free_amount / ticker['ask']
                                    order = await self.exchange.create_market_buy_order(reverse_pair, base_amount)
                                    if order['status'] == 'closed':
                                        converted = order['filled']
                                        total_base += converted
                                        conversions.append(f"{currency}: {free_amount:.6f} → {converted:.6f} {base_currency}")
                                        self.logger.info(f"✅ Конвертировано {currency}: {free_amount:.6f} → {converted:.6f} {base_currency}")
                            except Exception as e:
                                self.logger.warning(f"⚠️ Не удалось конвертировать {currency} через обратную пару: {e}")
            
            # Добавляем уже имеющуюся базовую валюту
            existing_base = balance.get(base_currency, {}).get('free', 0.0)
            total_base += existing_base
            
            if conversions:
                await self.send_telegram(f"""
💱 **КОНВЕРТАЦИЯ В {base_currency}**

🔄 **Конвертировано:**
{chr(10).join(conversions)}

💰 **Итого {base_currency}:** {total_base:.6f}
                """)
            
            return total_base
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка конвертации в {base_currency}: {e}")
            return 0.0
    
    async def find_best_triangle(self) -> Optional[Tuple]:
        """Найти лучший треугольник"""
        try:
            best_opportunity = None
            best_profit = 0
            
            # Получаем тикеры всех пар
            tickers = await self.exchange.fetch_tickers()
            
            for triangle in self.valid_triangles:
                pair1, pair2, pair3, direction, base_currency = triangle
                
                if not all(pair in tickers for pair in [pair1, pair2, pair3]):
                    continue
                
                t1, t2, t3 = tickers[pair1], tickers[pair2], tickers[pair3]
                
                if not all(t['bid'] and t['ask'] for t in [t1, t2, t3]):
                    continue
                
                # Получаем баланс базовой валюты
                balance = await self.get_balance(base_currency)
                if balance < self.min_balance_usdt:
                    continue
                
                # Расчет треугольного арбитража на весь баланс
                initial_amount = balance
                
                # Шаг 1: покупаем первую валюту (base -> crypto1)
                amount1 = initial_amount / t1['ask']
                
                # Шаг 2: обмениваем на вторую валюту (crypto1 -> crypto2)
                if direction == 'direct':
                    amount2 = amount1 * t2['bid']
                else:
                    amount2 = amount1 / t2['ask']
                
                # Шаг 3: продаем за базовую валюту (crypto2 -> base)
                final_amount = amount2 * t3['bid']
                
                # Прибыль
                profit = final_amount - initial_amount
                profit_percent = (profit / initial_amount) * 100
                
                # Учитываем комиссии MEXC (0.2% за сделку)
                fees = initial_amount * 0.006  # 3 сделки по 0.2%
                net_profit = profit - fees
                net_profit_percent = (net_profit / initial_amount) * 100
                
                if net_profit_percent >= self.min_profit and net_profit_percent > best_profit:
                    best_profit = net_profit_percent
                    best_opportunity = {
                        'triangle': triangle,
                        'initial_amount': initial_amount,
                        'final_amount': final_amount,
                        'profit': net_profit,
                        'profit_percent': net_profit_percent,
                        'prices': {pair1: t1, pair2: t2, pair3: t3}
                    }
            
            return best_opportunity
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка поиска треугольника: {e}")
            return None
    
    async def execute_triangle(self, opportunity: Dict) -> TriangleResult:
        """Исполнить треугольный арбитраж"""
        triangle = opportunity['triangle']
        pair1, pair2, pair3, direction, base_currency = triangle
        
        self.logger.info(f"🚀 Исполнение треугольного арбитража:")
        self.logger.info(f"   🔺 Путь: {base_currency} → {pair1.split('/')[0]} → {pair3.split('/')[0]} → {base_currency}")
        self.logger.info(f"   💰 Ожидаемая прибыль: {opportunity['profit_percent']:.3f}%")
        
        trades = []
        start_time = time.time()
        initial_balance = opportunity['initial_amount']
        
        try:
            # БЛОКИРУЕМ ДРУГИЕ ОПЕРАЦИИ
            self.is_executing = True
            
            await self.send_telegram(f"""
🚀 **НАЧАЛО ТРЕУГОЛЬНОГО АРБИТРАЖА**

🔺 **Путь:** {base_currency} → {pair1.split('/')[0]} → {pair3.split('/')[0]} → {base_currency}
💰 **Сумма:** {initial_balance:.6f} {base_currency}
📊 **Ожидаемая прибыль:** {opportunity['profit_percent']:.3f}%

⏳ Исполнение...
            """)
            
            if self.trading_mode == 'test':
                # Симуляция
                await asyncio.sleep(2)  # Имитация времени исполнения
                execution_time = time.time() - start_time
                
                return TriangleResult(
                    path=f"{base_currency} → {pair1.split('/')[0]} → {pair3.split('/')[0]} → {base_currency}",
                    initial_balance=initial_balance,
                    final_balance=opportunity['final_amount'],
                    profit=opportunity['profit'],
                    profit_percent=opportunity['profit_percent'],
                    trades=[],
                    execution_time=execution_time,
                    success=True
                )
            
            # РЕАЛЬНОЕ ИСПОЛНЕНИЕ
            
            # Сделка 1: Покупаем первую валюту
            self.logger.info(f"1️⃣ Покупка {pair1}")
            order1 = await self.exchange.create_market_buy_order(
                pair1, initial_balance / opportunity['prices'][pair1]['ask']
            )
            
            if order1['status'] != 'closed':
                raise Exception("Первая сделка не исполнена")
            
            trades.append({
                'step': 1,
                'pair': pair1,
                'side': 'buy',
                'amount': order1['filled'],
                'price': order1['average'],
                'timestamp': datetime.now().isoformat()
            })
            
            amount1 = order1['filled']
            await asyncio.sleep(0.1)
            
            # Сделка 2: Обмениваем на вторую валюту
            self.logger.info(f"2️⃣ Обмен {pair2}")
            if direction == 'direct':
                order2 = await self.exchange.create_market_sell_order(pair2, amount1)
            else:
                order2 = await self.exchange.create_market_buy_order(pair2, amount1)
            
            if order2['status'] != 'closed':
                raise Exception("Вторая сделка не исполнена")
            
            trades.append({
                'step': 2,
                'pair': pair2,
                'side': 'sell' if direction == 'direct' else 'buy',
                'amount': order2['filled'],
                'price': order2['average'],
                'timestamp': datetime.now().isoformat()
            })
            
            amount2 = order2['filled']
            await asyncio.sleep(0.1)
            
            # Сделка 3: Продаем за базовую валюту
            self.logger.info(f"3️⃣ Продажа {pair3}")
            order3 = await self.exchange.create_market_sell_order(pair3, amount2)
            
            if order3['status'] != 'closed':
                raise Exception("Третья сделка не исполнена")
            
            trades.append({
                'step': 3,
                'pair': pair3,
                'side': 'sell',
                'amount': order3['filled'],
                'price': order3['average'],
                'timestamp': datetime.now().isoformat()
            })
            
            # Расчет фактической прибыли
            final_balance = order3['filled'] * order3['average']
            actual_profit = final_balance - initial_balance
            actual_profit_percent = (actual_profit / initial_balance) * 100
            execution_time = time.time() - start_time
            
            self.logger.info(f"✅ Треугольник успешен! Прибыль: {actual_profit:.6f} {base_currency} ({actual_profit_percent:.3f}%)")
            
            return TriangleResult(
                path=f"{base_currency} → {pair1.split('/')[0]} → {pair3.split('/')[0]} → {base_currency}",
                initial_balance=initial_balance,
                final_balance=final_balance,
                profit=actual_profit,
                profit_percent=actual_profit_percent,
                trades=trades,
                execution_time=execution_time,
                success=True
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"❌ Ошибка исполнения треугольника: {e}")
            
            return TriangleResult(
                path=f"{base_currency} → {pair1.split('/')[0]} → {pair3.split('/')[0]} → {base_currency}",
                initial_balance=initial_balance,
                final_balance=initial_balance,
                profit=0.0,
                profit_percent=0.0,
                trades=trades,
                execution_time=execution_time,
                success=False,
                error=str(e)
            )
        
        finally:
            # РАЗБЛОКИРУЕМ ОПЕРАЦИИ
            self.is_executing = False
    
    async def send_triangle_report(self, result: TriangleResult):
        """Отправить отчет о треугольнике"""
        status_emoji = "✅" if result.success else "❌"
        profit_emoji = "💰" if result.profit > 0 else "💸"
        
        message = f"""
{status_emoji} **ТРЕУГОЛЬНЫЙ АРБИТРАЖ ЗАВЕРШЕН**

🔺 **Путь:** `{result.path}`
{profit_emoji} **Прибыль:** {result.profit:.6f} ({result.profit_percent:.3f}%)
💰 **Начальный баланс:** {result.initial_balance:.6f}
💰 **Конечный баланс:** {result.final_balance:.6f}
⏱️ **Время исполнения:** {result.execution_time:.2f}с
        """
        
        if result.error:
            message += f"\n❌ **Ошибка:** {result.error}"
        
        if result.trades:
            message += "\n\n📋 **Сделки:**"
            for trade in result.trades:
                side_emoji = "🟢" if trade['side'] == 'buy' else "🔴"
                message += f"""
{trade['step']}. {side_emoji} **{trade['side'].upper()}** `{trade['pair']}`
   💱 Количество: `{trade['amount']:.8f}`
   💲 Цена: `{trade['price']:.8f}`
"""
        
        # Обновляем статистику
        self.stats['total_triangles'] += 1
        if result.success:
            self.stats['successful_triangles'] += 1
            self.stats['total_profit'] += result.profit
        self.stats['last_execution'] = datetime.now().isoformat()
        
        success_rate = (self.stats['successful_triangles'] / self.stats['total_triangles']) * 100
        
        message += f"""

📊 **Общая статистика:**
• Всего треугольников: {self.stats['total_triangles']}
• Успешных: {self.stats['successful_triangles']} ({success_rate:.1f}%)
• Общая прибыль: {self.stats['total_profit']:.6f}
• Время работы: {(time.time() - self.stats['start_time'])/3600:.1f}ч
        """
        
        await self.send_telegram(message.strip())
    
    async def run(self):
        """Главный цикл автономного арбитража"""
        self.logger.info("🔺 Запуск автономного треугольного арбитража...")
        
        while True:
            try:
                # Пропускаем если уже исполняем треугольник
                if self.is_executing:
                    await asyncio.sleep(1)
                    continue
                
                self.stats['cycles'] += 1
                cycle_start = time.time()
                
                self.logger.info(f"🔄 Цикл {self.stats['cycles']} - {datetime.now().strftime('%H:%M:%S')}")
                
                # Ищем лучший треугольник
                opportunity = await self.find_best_triangle()
                
                if opportunity:
                    base_currency = opportunity['triangle'][4]
                    
                    # Конвертируем весь баланс в базовую валюту
                    total_balance = await self.convert_to_base_currency(base_currency)
                    
                    if total_balance >= self.min_balance_usdt:
                        # Обновляем сумму в возможности
                        opportunity['initial_amount'] = total_balance
                        
                        # Исполняем треугольник
                        result = await self.execute_triangle(opportunity)
                        
                        # Отправляем отчет
                        await self.send_triangle_report(result)
                    else:
                        self.logger.info(f"💸 Недостаточно средств: {total_balance:.6f} {base_currency}")
                else:
                    self.logger.info("📊 Прибыльных треугольников не найдено")
                
                # Статистика каждые 50 циклов
                if self.stats['cycles'] % 50 == 0:
                    uptime = time.time() - self.stats['start_time']
                    success_rate = (self.stats['successful_triangles'] / max(1, self.stats['total_triangles'])) * 100
                    
                    await self.send_telegram(f"""
📊 **СТАТИСТИКА АВТОНОМНОГО АРБИТРАЖА**

⏱️ **Время работы:** {uptime/3600:.1f} часов
🔄 **Циклов:** {self.stats['cycles']}
🔺 **Треугольников:** {self.stats['total_triangles']}
✅ **Успешных:** {self.stats['successful_triangles']} ({success_rate:.1f}%)
💰 **Общая прибыль:** {self.stats['total_profit']:.6f}

🤖 Автономный режим продолжается...
                    """)
                
                # Пауза между циклами (30 секунд)
                sleep_time = 30
                await asyncio.sleep(sleep_time)
                
            except KeyboardInterrupt:
                self.logger.info("⏹️ Остановка по запросу пользователя")
                break
            except Exception as e:
                self.logger.error(f"❌ Ошибка цикла: {e}")
                await asyncio.sleep(60)  # Пауза при ошибке
        
        if self.exchange:
            await self.exchange.close()

async def main():
    """Главная функция"""
    print("🔺 АВТОНОМНЫЙ ТРЕУГОЛЬНЫЙ АРБИТРАЖ")
    print("=" * 50)
    print("🤖 Полностью автономный режим")
    print("🔍 Автоматический поиск треугольников")
    print("💱 Конвертация в нужную валюту")
    print("💰 Операции на весь баланс")
    print("🚫 Блокировка других операций во время исполнения")
    print("📱 Отчеты в Telegram")
    print("=" * 50)
    
    bot = AutoTriangularBot()
    
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