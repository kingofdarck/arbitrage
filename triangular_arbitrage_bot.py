#!/usr/bin/env python3
"""
Чистый треугольный арбитраж бот для MEXC
Только треугольный арбитраж + Telegram уведомления о сделках
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

# Загружаем переменные окружения
try:
    from dotenv import load_dotenv
    if os.path.exists('.env'):
        load_dotenv('.env')
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
class TriangularOpportunity:
    """Треугольная возможность"""
    path: str
    triangle: Tuple[str, str, str, str]  # pair1, pair2, pair3, direction
    profit_percent: float
    profit_usd: float
    net_profit_percent: float
    net_profit_usd: float
    fees_usd: float
    prices: Dict[str, Dict[str, float]]

class TriangularArbitrageBot:
    """Бот треугольного арбитража"""
    
    def __init__(self):
        self.exchange = None
        self.telegram_bot = None
        self.markets = {}
        self.valid_triangles = []
        
        # Загружаем настройки из файла управления
        self.load_control_settings()
        
        # Проверяем что арбитраж не запущен по умолчанию
        if not hasattr(self, 'min_profit'):
            self.min_profit = float(os.getenv('MIN_PROFIT_THRESHOLD', '0.75'))
            self.max_position = float(os.getenv('MAX_POSITION_SIZE', '50.0'))
            self.trading_mode = os.getenv('TRADING_MODE', 'live')
            
        # Арбитраж по умолчанию ВЫКЛЮЧЕН
        self.auto_start = False
        
        # Telegram
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Статистика
        self.stats = {
            'start_time': time.time(),
            'total_trades': 0,
            'successful_trades': 0,
            'total_profit': 0.0,
            'opportunities_found': 0,
            'cycles': 0
        }
        
        self.setup_logging()
        self.is_running = False
        
        # Добавляем логгер для методов
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger(__name__)
    
    def load_control_settings(self):
        """Загрузка настроек из файла управления"""
        try:
            import json
            if os.path.exists('triangular_settings.json'):
                with open('triangular_settings.json', 'r', encoding='utf-8') as f:
                    control_settings = json.load(f)
                
                # Применяем настройки из файла управления
                self.min_profit = control_settings.get('min_profit', 0.75)
                self.max_position = control_settings.get('max_position', 50.0)
                self.trading_mode = control_settings.get('trading_mode', 'live')
                
                # Проверяем команду запуска
                bot_running = control_settings.get('bot_running', False)
                if bot_running and not self.is_running:
                    self.should_run = True
                    self.logger.info("✅ Получена команда запуска из Telegram")
                elif not bot_running and self.is_running:
                    self.is_running = False
                    self.logger.info("⏹️ Получена команда остановки из Telegram")
                
                if hasattr(self, 'logger'):
                    self.logger.info(f"✅ Настройки загружены: прибыль {self.min_profit}%, позиция ${self.max_position}, режим {self.trading_mode}")
            else:
                # Настройки по умолчанию из .env
                self.min_profit = float(os.getenv('MIN_PROFIT_THRESHOLD', '0.75'))
                self.max_position = float(os.getenv('MAX_POSITION_SIZE', '50.0'))
                self.trading_mode = os.getenv('TRADING_MODE', 'live')
                
                if hasattr(self, 'logger'):
                    self.logger.info("📋 Используются настройки по умолчанию из .env")
        except Exception as e:
            # Fallback к .env настройкам
            self.min_profit = float(os.getenv('MIN_PROFIT_THRESHOLD', '0.75'))
            self.max_position = float(os.getenv('MAX_POSITION_SIZE', '50.0'))
            self.trading_mode = os.getenv('TRADING_MODE', 'live')
            
            if hasattr(self, 'logger'):
                self.logger.warning(f"⚠️ Ошибка загрузки настроек управления: {e}")
    
    def update_stats_to_control(self):
        """Обновление статистики в файле управления"""
        try:
            import json
            if os.path.exists('triangular_settings.json'):
                with open('triangular_settings.json', 'r', encoding='utf-8') as f:
                    control_settings = json.load(f)
                
                # Обновляем статистику
                control_settings['total_trades'] = self.stats['total_trades']
                control_settings['successful_trades'] = self.stats['successful_trades']
                control_settings['total_profit'] = self.stats['total_profit']
                control_settings['bot_running'] = self.is_running
                
                with open('triangular_settings.json', 'w', encoding='utf-8') as f:
                    json.dump(control_settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.warning(f"⚠️ Ошибка обновления статистики: {e}")
    
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('triangular_arbitrage.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Инициализация"""
        self.logger.info("🔺 Инициализация треугольного арбитража на MEXC...")
        
        # Инициализация MEXC
        api_key = os.getenv('MEXC_API_KEY')
        api_secret = os.getenv('MEXC_API_SECRET')
        sandbox = os.getenv('MEXC_SANDBOX', 'false').lower() == 'true'
        
        if not api_key or not api_secret:
            self.logger.error("❌ API ключи MEXC не найдены!")
            return False
        
        if len(api_key) < 20 or len(api_secret) < 30:
            self.logger.warning("⚠️ API ключи кажутся короткими")
        
        try:
            self.exchange = ccxt.mexc({
                'apiKey': api_key,
                'secret': api_secret,
                'sandbox': sandbox,
                'enableRateLimit': True,
                'rateLimit': 1000,
                'options': {'defaultType': 'spot'}
            })
            
            # Загружаем рынки
            self.markets = await self.exchange.load_markets()
            self.logger.info(f"✅ Загружено {len(self.markets)} торговых пар MEXC")
            
            # Инициализация Telegram
            if self.telegram_token and self.telegram_chat_id:
                self.logger.info("🤖 Инициализация Telegram бота...")
                await self.send_telegram("🔺 **ТРЕУГОЛЬНЫЙ АРБИТРАЖ ЗАПУЩЕН**\n\n✅ Подключение к MEXC установлено\n📊 Поиск только треугольных возможностей")
                self.logger.info("✅ Telegram бот инициализирован")
            else:
                self.logger.warning("⚠️ Telegram не настроен - токен или chat_id отсутствуют")
            
            # Генерируем треугольники
            await self.generate_triangles()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации MEXC: {e}")
            return False
    
    async def generate_triangles(self):
        """Генерация треугольников"""
        self.logger.info("🔺 Генерация треугольных возможностей...")
        
        # Основные валюты для треугольников
        base_currencies = ['USDT', 'BTC', 'ETH']
        
        # Популярные криптовалюты
        crypto_currencies = [
            'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'AVAX',
            'MATIC', 'LINK', 'UNI', 'LTC', 'BCH', 'ATOM', 'FTM', 'NEAR',
            'ALGO', 'VET', 'ICP', 'SAND', 'MANA', 'CRV', 'AAVE', 'COMP'
        ]
        
        self.valid_triangles = []
        
        for base in base_currencies:
            # Находим пары с этой базовой валютой
            base_pairs = []
            for symbol in self.markets.keys():
                if '/' in symbol and symbol.endswith(f'/{base}'):
                    crypto = symbol.split('/')[0]
                    if crypto in crypto_currencies and crypto != base:
                        base_pairs.append(crypto)
            
            self.logger.info(f"📊 Для {base}: найдено {len(base_pairs)} валют")
            
            # Генерируем треугольники
            for crypto1, crypto2 in itertools.combinations(base_pairs, 2):
                # Треугольник: base -> crypto1 -> crypto2 -> base
                pair1 = f"{crypto1}/{base}"  # BTC/USDT
                pair2 = f"{crypto1}/{crypto2}"  # BTC/ETH
                pair3 = f"{crypto2}/{base}"  # ETH/USDT
                pair2_alt = f"{crypto2}/{crypto1}"  # ETH/BTC
                
                # Проверяем существование всех пар
                if all(pair in self.markets for pair in [pair1, pair2, pair3]):
                    self.valid_triangles.append((pair1, pair2, pair3, 'direct'))
                
                if all(pair in self.markets for pair in [pair1, pair2_alt, pair3]):
                    self.valid_triangles.append((pair1, pair2_alt, pair3, 'reverse'))
        
        self.logger.info(f"✅ Сгенерировано {len(self.valid_triangles)} треугольных возможностей")
        
        # Показываем примеры
        for i, triangle in enumerate(self.valid_triangles[:5]):
            pair1, pair2, pair3, direction = triangle
            base = pair1.split('/')[1]
            crypto1 = pair1.split('/')[0]
            crypto2 = pair3.split('/')[0]
            path = f"{base} → {crypto1} → {crypto2} → {base}"
            self.logger.info(f"   {i+1}. {path} ({direction})")
    
    async def send_telegram(self, message: str):
        """Отправка сообщения в Telegram"""
        if not self.telegram_token or not self.telegram_chat_id:
            self.logger.warning("⚠️ Telegram токен или chat_id не настроены")
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
            self.logger.info("📱 Telegram сообщение отправлено")
        except Exception as e:
            self.logger.error(f"❌ Ошибка Telegram: {e}")
            # Попробуем без Markdown
            try:
                await self.telegram_bot.send_message(
                    chat_id=self.telegram_chat_id,
                    text=message
                )
                self.logger.info("📱 Telegram сообщение отправлено (без Markdown)")
            except Exception as e2:
                self.logger.error(f"❌ Критическая ошибка Telegram: {e2}")
    
    async def find_triangular_opportunities(self):
        """Поиск треугольных возможностей"""
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
                
                # Расчет треугольного арбитража
                initial_amount = self.max_position
                
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
                
                if net_profit_percent >= self.min_profit:
                    base_currency = pair1.split('/')[1]
                    crypto1 = pair1.split('/')[0]
                    crypto2 = pair3.split('/')[0]
                    path = f"{base_currency} → {crypto1} → {crypto2} → {base_currency}"
                    
                    opportunity = TriangularOpportunity(
                        path=path,
                        triangle=triangle,
                        profit_percent=profit_percent,
                        profit_usd=profit,
                        net_profit_percent=net_profit_percent,
                        net_profit_usd=net_profit,
                        fees_usd=fees,
                        prices={pair1: t1, pair2: t2, pair3: t3}
                    )
                    opportunities.append(opportunity)
            
            # Сортируем по чистой прибыли
            opportunities.sort(key=lambda x: x.net_profit_percent, reverse=True)
            self.stats['opportunities_found'] += len(opportunities)
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка поиска возможностей: {e}")
            return []
    
    async def execute_triangular_trade(self, opportunity: TriangularOpportunity):
        """Исполнение треугольной сделки"""
        pair1, pair2, pair3, direction = opportunity.triangle
        
        self.logger.info(f"🚀 Исполнение треугольного арбитража:")
        self.logger.info(f"   🔺 Путь: {opportunity.path}")
        self.logger.info(f"   💰 Ожидаемая прибыль: {opportunity.net_profit_percent:.3f}%")
        
        if self.trading_mode == 'test':
            # Симуляция
            await self.send_telegram(f"""
🧪 **СИМУЛЯЦИЯ ТРЕУГОЛЬНОЙ СДЕЛКИ**

🔺 **Путь:** `{opportunity.path}`
💰 **Прибыль:** {opportunity.net_profit_percent:.3f}% (${opportunity.net_profit_usd:.2f})
📊 **Валовая прибыль:** {opportunity.profit_percent:.3f}%
💸 **Комиссии:** ${opportunity.fees_usd:.2f}
⏰ **Время:** {datetime.now().strftime('%H:%M:%S')}

📋 **План сделок:**
1. 🟢 BUY {pair1} по ${opportunity.prices[pair1]['ask']:.6f}
2. {'🔴 SELL' if direction == 'direct' else '🟢 BUY'} {pair2} по ${opportunity.prices[pair2]['bid' if direction == 'direct' else 'ask']:.6f}
3. 🔴 SELL {pair3} по ${opportunity.prices[pair3]['bid']:.6f}
            """)
            
            self.stats['total_trades'] += 1
            self.stats['successful_trades'] += 1
            self.stats['total_profit'] += opportunity.net_profit_usd
            return True
        
        # Реальная торговля
        trades = []
        start_time = time.time()
        
        try:
            initial_amount = self.max_position
            
            # Сделка 1: Покупаем первую валюту
            self.logger.info(f"1️⃣ Покупка {pair1}")
            order1 = await self.exchange.create_market_buy_order(
                pair1, initial_amount / opportunity.prices[pair1]['ask']
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
            await asyncio.sleep(0.1)  # Небольшая пауза
            
            # Сделка 2: Обмениваем на вторую валюту
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
            await asyncio.sleep(0.1)  # Небольшая пауза
            
            # Сделка 3: Продаем за базовую валюту
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
            
            # Отправляем уведомление о успешной сделке
            await self.send_trade_notification(opportunity, trades, actual_profit, execution_time, True)
            
            # Обновляем статистику
            self.stats['total_trades'] += 1
            self.stats['successful_trades'] += 1
            self.stats['total_profit'] += actual_profit
            
            # Обновляем статистику в файле управления
            self.update_stats_to_control()
            
            self.logger.info(f"✅ Треугольная сделка успешна! Прибыль: ${actual_profit:.2f}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка исполнения треугольной сделки: {e}")
            
            # Уведомление об ошибке
            await self.send_telegram(f"""
❌ **ОШИБКА ТРЕУГОЛЬНОЙ СДЕЛКИ**

🔺 **Путь:** `{opportunity.path}`
❌ **Ошибка:** {str(e)}
⏰ **Время:** {datetime.now().strftime('%H:%M:%S')}

💡 Сделка была прервана для минимизации потерь
            """)
            
            self.stats['total_trades'] += 1
            # Обновляем статистику в файле управления
            self.update_stats_to_control()
            return False
    
    async def send_trade_notification(self, opportunity: TriangularOpportunity, trades: List[Trade], actual_profit: float, execution_time: float, success: bool):
        """Отправка уведомления о треугольной сделке"""
        profit_emoji = "💰" if actual_profit > 0 else "💸"
        status_emoji = "✅" if success else "❌"
        
        message = f"""
{status_emoji} **ТРЕУГОЛЬНАЯ СДЕЛКА ИСПОЛНЕНА**

🔺 **Путь:** `{opportunity.path}`
{profit_emoji} **Фактическая прибыль:** ${actual_profit:.2f}
📊 **Ожидалось:** ${opportunity.net_profit_usd:.2f}
⏱️ **Время исполнения:** {execution_time:.2f}с

📋 **Детали сделок:**
"""
        
        for i, trade in enumerate(trades, 1):
            side_emoji = "🟢" if trade.side == 'buy' else "🔴"
            message += f"""
{i}. {side_emoji} **{trade.side.upper()}** `{trade.symbol}`
   💱 Количество: `{trade.amount:.8f}`
   💲 Цена: `${trade.price:.6f}`
   🆔 Order ID: `{trade.order_id}`
   ⏰ Время: `{trade.timestamp.strftime('%H:%M:%S')}`
"""
        
        message += f"""
📊 **Общая статистика:**
• Всего сделок: {self.stats['total_trades']}
• Успешных: {self.stats['successful_trades']}
• Общая прибыль: ${self.stats['total_profit']:.2f}
• Время работы: {(time.time() - self.stats['start_time'])/3600:.1f}ч
        """
        
        await self.send_telegram(message.strip())
    
    async def run(self):
        """Главный цикл треугольного арбитража"""
        self.logger.info("🔺 Система треугольного арбитража готова...")
        self.logger.info("⚠️ Арбитраж по умолчанию ВЫКЛЮЧЕН")
        self.logger.info("💡 Используйте Telegram бот для запуска")
        
        # Ждем команды запуска через Telegram
        while True:
            try:
                # Перезагружаем настройки каждые 10 секунд
                self.load_control_settings()
                
                # Проверяем нужно ли запускать арбитраж
                if not self.is_running and hasattr(self, 'should_run') and self.should_run:
                    self.logger.info("🚀 Получена команда запуска через Telegram")
                    self.is_running = True
                    break
                elif not self.is_running:
                    # Ждем команды запуска
                    await asyncio.sleep(10)
                    continue
                else:
                    # Арбитраж уже запущен, выходим из ожидания
                    break
                    
            except KeyboardInterrupt:
                self.logger.info("⏹️ Остановка по запросу пользователя")
                return
            except Exception as e:
                self.logger.error(f"❌ Ошибка ожидания: {e}")
                await asyncio.sleep(10)
        
        # Основной цикл арбитража (запускается только после команды)
        self.logger.info("🔺 Запуск треугольного арбитража...")
        
        while self.is_running:
            try:
                self.stats['cycles'] += 1
                cycle_start = time.time()
                
                self.logger.info(f"🔄 Цикл {self.stats['cycles']} - {datetime.now().strftime('%H:%M:%S')}")
                
                # Ищем треугольные возможности
                opportunities = await self.find_triangular_opportunities()
                
                if opportunities:
                    self.logger.info(f"🔺 Найдено {len(opportunities)} треугольных возможностей")
                    
                    # Исполняем лучшую возможность
                    best = opportunities[0]
                    self.logger.info(f"💎 Лучшая возможность: {best.path} ({best.net_profit_percent:.3f}%)")
                    
                    await self.execute_triangular_trade(best)
                else:
                    self.logger.info("📊 Треугольных возможностей не найдено")
                
                # Статистика каждые 20 циклов
                if self.stats['cycles'] % 20 == 0:
                    uptime = time.time() - self.stats['start_time']
                    success_rate = (self.stats['successful_trades'] / max(1, self.stats['total_trades'])) * 100
                    
                    self.logger.info(f"📊 Статистика: время работы {uptime/3600:.1f}ч, "
                                   f"циклов {self.stats['cycles']}, "
                                   f"сделок {self.stats['total_trades']}, "
                                   f"успешность {success_rate:.1f}%, "
                                   f"прибыль ${self.stats['total_profit']:.2f}")
                    
                    # Обновляем статистику в файле управления
                    self.update_stats_to_control()
                
                # Проверяем настройки каждые 10 циклов
                if self.stats['cycles'] % 10 == 0:
                    old_settings = (self.min_profit, self.max_position, self.trading_mode)
                    self.load_control_settings()
                    new_settings = (self.min_profit, self.max_position, self.trading_mode)
                    
                    if old_settings != new_settings:
                        self.logger.info("🔄 Настройки обновлены из управления")
                        await self.send_telegram(f"""
🔄 **НАСТРОЙКИ ОБНОВЛЕНЫ**

⚙️ **Новые параметры:**
• Минимальная прибыль: {self.min_profit}%
• Максимальная позиция: ${self.max_position}
• Режим торговли: {self.trading_mode}

🔺 Треугольный арбитраж продолжает работу
                        """)
                
                cycle_time = time.time() - cycle_start
                
                # Пауза между циклами (2 минуты)
                sleep_time = 120
                self.logger.info(f"⏳ Ожидание {sleep_time} секунд...")
                await asyncio.sleep(sleep_time)
                
            except KeyboardInterrupt:
                self.logger.info("⏹️ Остановка по запросу пользователя")
                break
            except Exception as e:
                self.logger.error(f"❌ Ошибка цикла: {e}")
                await asyncio.sleep(30)
        
        self.is_running = False
        
        # Финальная статистика
        uptime = time.time() - self.stats['start_time']
        success_rate = (self.stats['successful_trades'] / max(1, self.stats['total_trades'])) * 100
        
        await self.send_telegram(f"""
🛑 **ТРЕУГОЛЬНЫЙ АРБИТРАЖ ОСТАНОВЛЕН**

📊 **Финальная статистика:**
• Время работы: {uptime/3600:.1f} часов
• Циклов: {self.stats['cycles']}
• Всего сделок: {self.stats['total_trades']}
• Успешных: {self.stats['successful_trades']} ({success_rate:.1f}%)
• Общая прибыль: ${self.stats['total_profit']:.2f}
• Найдено возможностей: {self.stats['opportunities_found']}

🔺 Только треугольный арбитраж на MEXC
        """)
        
        if self.exchange:
            await self.exchange.close()

async def main():
    """Главная функция"""
    print("🔺 ТРЕУГОЛЬНЫЙ АРБИТРАЖ НА MEXC")
    print("=" * 50)
    print("🎯 Только треугольные возможности")
    print("📱 Telegram уведомления о сделках")
    print("💰 Реальная торговля на MEXC")
    print("=" * 50)
    
    bot = TriangularArbitrageBot()
    
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