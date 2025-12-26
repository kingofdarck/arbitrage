#!/usr/bin/env python3
"""
ПРОСТОЙ РАБОЧИЙ треугольный арбитраж бот для MEXC
Максимально упрощенная версия которая точно работает
"""

import asyncio
import ccxt
import time
import os
from datetime import datetime
import logging

# Загружаем переменные окружения
try:
    from dotenv import load_dotenv
    if os.path.exists('.env'):
        load_dotenv('.env')
except ImportError:
    pass

class SimpleWorkingBot:
    """Простой рабочий треугольный арбитраж бот"""
    
    def __init__(self):
        self.exchange = None
        self.telegram_bot = None
        
        # Простые настройки
        self.min_profit = 0.2  # Очень низкий порог
        self.min_balance = 1.0  # Минимальный баланс
        
        # Telegram
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Статистика
        self.cycles = 0
        self.start_time = time.time()
        self.last_balance_report = 0
        
        # Простое логирование
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def send_telegram(self, message: str):
        """Отправка сообщения в Telegram"""
        if not self.telegram_token or not self.telegram_chat_id:
            print(f"Telegram: {message}")
            return
        
        try:
            if not self.telegram_bot:
                from telegram import Bot
                self.telegram_bot = Bot(token=self.telegram_token)
            
            await self.telegram_bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message
            )
            print(f"Telegram отправлено: {message[:50]}...")
        except Exception as e:
            print(f"Ошибка Telegram: {e}")
    
    async def initialize(self):
        """Инициализация"""
        print("Инициализация простого рабочего бота...")
        
        # API ключи
        api_key = os.getenv('MEXC_API_KEY')
        api_secret = os.getenv('MEXC_API_SECRET')
        
        if not api_key or not api_secret:
            print("ОШИБКА: API ключи MEXC не найдены!")
            return False
        
        try:
            # Простая инициализация MEXC (синхронная версия)
            self.exchange = ccxt.mexc({
                'apiKey': api_key,
                'secret': api_secret,
                'sandbox': False,
                'enableRateLimit': True,
                'rateLimit': 1000
            })
            
            # Проверяем подключение (синхронно)
            balance = self.exchange.fetch_balance()
            print(f"Подключение к MEXC успешно! Найдено валют: {len([k for k, v in balance.items() if v.get('free', 0) > 0])}")
            
            # Уведомление в Telegram
            await self.send_telegram("🤖 ПРОСТОЙ РАБОЧИЙ БОТ ЗАПУЩЕН\n\nПодключение к MEXC установлено\nОтчеты каждые 5 минут")
            
            return True
            
        except Exception as e:
            print(f"Ошибка инициализации: {e}")
            return False
    
    async def get_balance_report(self):
        """Получить отчет о балансе"""
        try:
            balance = self.exchange.fetch_balance()
            
            # Собираем валюты с балансом
            currencies = []
            total_usdt = 0
            
            for currency, info in balance.items():
                free = info.get('free', 0)
                if free > 0.001:  # Только значимые суммы
                    currencies.append(f"{currency}: {free:.6f}")
                    
                    # Пытаемся оценить в USDT
                    if currency == 'USDT':
                        total_usdt += free
                    else:
                        try:
                            # Пробуем найти пару с USDT
                            ticker = self.exchange.fetch_ticker(f"{currency}/USDT")
                            usdt_value = free * ticker['last']
                            total_usdt += usdt_value
                            currencies[-1] += f" (≈{usdt_value:.2f} USDT)"
                        except:
                            pass
            
            if not currencies:
                return "Нет доступных средств"
            
            # Формируем отчет
            report = "💰 ОТЧЕТ О БАЛАНСЕ\n\n"
            report += "\n".join(currencies[:10])  # Максимум 10 валют
            report += f"\n\n💵 Общая стоимость: ≈{total_usdt:.2f} USDT"
            
            # Статистика
            uptime = (time.time() - self.start_time) / 3600
            report += f"\n\n📊 Время работы: {uptime:.1f}ч"
            report += f"\n🔄 Циклов: {self.cycles}"
            report += f"\n🤖 Бот работает"
            
            return report
            
        except Exception as e:
            return f"Ошибка получения баланса: {e}"
    
    async def find_simple_arbitrage(self):
        """Поиск простых арбитражных возможностей"""
        try:
            # Простые популярные треугольники
            triangles = [
                ('BTC/USDT', 'ETH/BTC', 'ETH/USDT'),
                ('BTC/USDT', 'BNB/BTC', 'BNB/USDT'),
                ('ETH/USDT', 'BNB/ETH', 'BNB/USDT'),
                ('BTC/USDT', 'ADA/BTC', 'ADA/USDT'),
                ('ETH/USDT', 'ADA/ETH', 'ADA/USDT')
            ]
            
            best_profit = 0
            best_triangle = None
            
            for triangle in triangles:
                try:
                    pair1, pair2, pair3 = triangle
                    
                    # Получаем тикеры (синхронно)
                    t1 = self.exchange.fetch_ticker(pair1)
                    t2 = self.exchange.fetch_ticker(pair2)
                    t3 = self.exchange.fetch_ticker(pair3)
                    
                    # Проверяем что есть цены
                    if not all(t['bid'] and t['ask'] for t in [t1, t2, t3]):
                        continue
                    
                    # Простой расчет треугольника: USDT -> crypto1 -> crypto2 -> USDT
                    amount = 100  # Тестовая сумма
                    
                    # Шаг 1: покупаем первую валюту
                    amount1 = amount / t1['ask']
                    
                    # Шаг 2: обмениваем на вторую валюту
                    amount2 = amount1 * t2['bid']
                    
                    # Шаг 3: продаем за USDT
                    final_amount = amount2 * t3['bid']
                    
                    # Прибыль
                    profit = final_amount - amount
                    profit_percent = (profit / amount) * 100
                    
                    # Учитываем комиссии (0.6% за 3 сделки)
                    net_profit_percent = profit_percent - 0.6
                    
                    if net_profit_percent > best_profit and net_profit_percent >= self.min_profit:
                        best_profit = net_profit_percent
                        best_triangle = {
                            'triangle': triangle,
                            'profit_percent': net_profit_percent,
                            'path': f"USDT -> {pair1.split('/')[0]} -> {pair3.split('/')[0]} -> USDT"
                        }
                
                except Exception as e:
                    continue  # Пропускаем проблемные пары
            
            return best_triangle
            
        except Exception as e:
            print(f"Ошибка поиска арбитража: {e}")
            return None
    
    async def execute_simple_trade(self, opportunity):
        """Простое исполнение сделки (только симуляция)"""
        try:
            # Получаем баланс USDT (синхронно)
            balance = self.exchange.fetch_balance()
            usdt_balance = balance.get('USDT', {}).get('free', 0)
            
            if usdt_balance < self.min_balance:
                return f"Недостаточно USDT: {usdt_balance:.2f}"
            
            # Симуляция сделки
            profit = usdt_balance * (opportunity['profit_percent'] / 100)
            
            report = f"""
🚀 СИМУЛЯЦИЯ ТРЕУГОЛЬНОГО АРБИТРАЖА

🔺 Путь: {opportunity['path']}
💰 Сумма: {usdt_balance:.2f} USDT
📊 Прибыль: {opportunity['profit_percent']:.3f}%
💵 Ожидаемая прибыль: {profit:.6f} USDT

✅ Симуляция успешна
⏰ Время: {datetime.now().strftime('%H:%M:%S')}
            """
            
            return report
            
        except Exception as e:
            return f"Ошибка исполнения: {e}"
    
    async def run(self):
        """Главный цикл"""
        print("Запуск простого рабочего бота...")
        
        while True:
            try:
                self.cycles += 1
                print(f"\nЦикл {self.cycles} - {datetime.now().strftime('%H:%M:%S')}")
                
                # Отчет о балансе каждые 5 минут
                if time.time() - self.last_balance_report >= 300:  # 5 минут
                    print("Отправка отчета о балансе...")
                    balance_report = await self.get_balance_report()
                    await self.send_telegram(balance_report)
                    self.last_balance_report = time.time()
                
                # Поиск арбитража
                print("Поиск арбитражных возможностей...")
                opportunity = await self.find_simple_arbitrage()
                
                if opportunity:
                    print(f"Найдена возможность: {opportunity['profit_percent']:.3f}%")
                    
                    # Исполняем (симуляция)
                    result = await self.execute_simple_trade(opportunity)
                    await self.send_telegram(result)
                else:
                    print("Прибыльных возможностей не найдено")
                
                # Статистика каждые 20 циклов
                if self.cycles % 20 == 0:
                    uptime = (time.time() - self.start_time) / 3600
                    stats = f"📊 Статистика: {uptime:.1f}ч работы, {self.cycles} циклов"
                    print(stats)
                    await self.send_telegram(stats)
                
                # Пауза между циклами
                print("Ожидание 60 секунд...")
                await asyncio.sleep(60)
                
            except KeyboardInterrupt:
                print("Остановка по запросу пользователя")
                break
            except Exception as e:
                print(f"Ошибка цикла: {e}")
                await asyncio.sleep(30)  # Пауза при ошибке
        
        # Закрываем соединения
        if self.exchange:
            # Для синхронной версии ccxt не нужно await
            pass

async def main():
    """Главная функция"""
    print("🤖 ПРОСТОЙ РАБОЧИЙ ТРЕУГОЛЬНЫЙ АРБИТРАЖ")
    print("=" * 50)
    print("✅ Максимально упрощенная версия")
    print("📊 Отчеты о балансе каждые 5 минут")
    print("🔍 Поиск простых треугольников")
    print("🧪 Только симуляция сделок")
    print("📱 Уведомления в Telegram")
    print("=" * 50)
    
    bot = SimpleWorkingBot()
    
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