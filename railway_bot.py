#!/usr/bin/env python3
"""
БОТ ДЛЯ RAILWAY - стабильная работа на сервере
Исправлены все проблемы с деплоем
"""

import asyncio
import time
import os
import sys
import traceback
from datetime import datetime

# Загружаем переменные окружения
try:
    from dotenv import load_dotenv
    if os.path.exists('.env'):
        load_dotenv('.env')
except ImportError:
    pass

class RailwayBot:
    """Бот для стабильной работы на Railway"""
    
    def __init__(self):
        self.telegram_bot = None
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        self.cycles = 0
        self.start_time = time.time()
        self.last_balance_report = 0
        self.last_heartbeat = 0
        self.errors_count = 0
        
        print(f"[{self.get_time()}] Railway бот инициализирован")
        print(f"[{self.get_time()}] Telegram токен: {'✅' if self.telegram_token else '❌'}")
        print(f"[{self.get_time()}] Chat ID: {'✅' if self.telegram_chat_id else '❌'}")
    
    def get_time(self):
        """Получить текущее время"""
        return datetime.now().strftime('%H:%M:%S')
    
    async def send_telegram(self, message: str, retry_count=3):
        """Отправка сообщения в Telegram с повторными попытками"""
        if not self.telegram_token or not self.telegram_chat_id:
            print(f"[{self.get_time()}] [Telegram] {message}")
            return False
        
        for attempt in range(retry_count):
            try:
                if not self.telegram_bot:
                    from telegram import Bot
                    self.telegram_bot = Bot(token=self.telegram_token)
                
                await self.telegram_bot.send_message(
                    chat_id=self.telegram_chat_id,
                    text=message
                )
                print(f"[{self.get_time()}] [Telegram] Отправлено: {message[:50]}...")
                return True
                
            except Exception as e:
                print(f"[{self.get_time()}] [Telegram] Ошибка попытка {attempt+1}: {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2)  # Пауза перед повтором
                
        return False
    
    async def get_mexc_balance(self):
        """Получить баланс с MEXC с обработкой ошибок"""
        try:
            import ccxt
            
            api_key = os.getenv('MEXC_API_KEY')
            api_secret = os.getenv('MEXC_API_SECRET')
            
            if not api_key or not api_secret:
                return "❌ Нет API ключей MEXC"
            
            # Создаем новое подключение каждый раз для стабильности
            exchange = ccxt.mexc({
                'apiKey': api_key,
                'secret': api_secret,
                'sandbox': False,
                'enableRateLimit': True,
                'rateLimit': 2000,  # Увеличиваем задержку для Railway
                'timeout': 30000,   # Увеличиваем таймаут
            })
            
            # Получаем баланс
            balance = exchange.fetch_balance()
            
            # Собираем валюты с балансом
            currencies = []
            total_usdt = 0
            
            for currency, info in balance.items():
                free = info.get('free', 0)
                if free > 0.001:
                    currencies.append(f"• {currency}: {free:.6f}")
                    
                    if currency == 'USDT':
                        total_usdt += free
                    else:
                        # Пробуем оценить в USDT с обработкой ошибок
                        try:
                            ticker = exchange.fetch_ticker(f"{currency}/USDT")
                            usdt_value = free * ticker['last']
                            total_usdt += usdt_value
                            currencies[-1] += f" (≈{usdt_value:.2f} USDT)"
                        except:
                            pass  # Игнорируем ошибки оценки
            
            if not currencies:
                return "💰 **ОТЧЕТ О БАЛАНСЕ**\n\n❌ Нет доступных средств на MEXC"
            
            # Формируем отчет
            report = "💰 **ОТЧЕТ О БАЛАНСЕ MEXC**\n\n"
            report += "\n".join(currencies[:15])  # Максимум 15 валют
            report += f"\n\n💵 **Общая стоимость:** ≈{total_usdt:.2f} USDT"
            
            return report
            
        except Exception as e:
            error_msg = f"❌ Ошибка получения баланса: {str(e)[:100]}"
            print(f"[{self.get_time()}] {error_msg}")
            return error_msg
    
    async def find_opportunities(self):
        """Поиск возможностей с обработкой ошибок"""
        try:
            import ccxt
            
            api_key = os.getenv('MEXC_API_KEY')
            api_secret = os.getenv('MEXC_API_SECRET')
            
            if not api_key or not api_secret:
                return None
            
            exchange = ccxt.mexc({
                'apiKey': api_key,
                'secret': api_secret,
                'sandbox': False,
                'enableRateLimit': True,
                'rateLimit': 2000,
                'timeout': 30000,
            })
            
            # Простые пары для проверки
            pairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']
            opportunities = []
            
            for pair in pairs:
                try:
                    ticker = exchange.fetch_ticker(pair)
                    
                    # Простая проверка спреда
                    bid = ticker['bid']
                    ask = ticker['ask']
                    if bid and ask and bid > 0:
                        spread = ((ask - bid) / bid) * 100
                        
                        if spread < 0.3:  # Хороший спред
                            opportunities.append(f"• {pair}: спред {spread:.3f}%")
                            
                except Exception as e:
                    continue  # Пропускаем проблемные пары
            
            if opportunities:
                return "🔍 **НАЙДЕННЫЕ ВОЗМОЖНОСТИ:**\n\n" + "\n".join(opportunities)
            else:
                return None  # Не отправляем если нет хороших возможностей
                
        except Exception as e:
            print(f"[{self.get_time()}] Ошибка поиска возможностей: {e}")
            return None
    
    async def send_heartbeat(self):
        """Отправка heartbeat для проверки что бот жив"""
        try:
            uptime = (time.time() - self.start_time) / 3600
            heartbeat = f"💓 **HEARTBEAT**\n\n🤖 Бот работает\n⏰ Время работы: {uptime:.1f}ч\n🔄 Циклов: {self.cycles}\n❌ Ошибок: {self.errors_count}\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            await self.send_telegram(heartbeat)
            self.last_heartbeat = time.time()
            print(f"[{self.get_time()}] Heartbeat отправлен")
            
        except Exception as e:
            print(f"[{self.get_time()}] Ошибка heartbeat: {e}")
    
    async def handle_error(self, error, context=""):
        """Обработка ошибок с уведомлением"""
        self.errors_count += 1
        error_msg = f"⚠️ **ОШИБКА В БОТЕ**\n\n📍 Контекст: {context}\n❌ Ошибка: {str(error)[:200]}\n🔄 Цикл: {self.cycles}\n⏰ Время: {self.get_time()}"
        
        print(f"[{self.get_time()}] [ОШИБКА] {context}: {error}")
        await self.send_telegram(error_msg)
    
    async def run(self):
        """Главный цикл для Railway"""
        print(f"[{self.get_time()}] 🚀 Запуск Railway бота...")
        
        # Стартовое сообщение
        startup_msg = f"🚀 **RAILWAY БОТ ЗАПУЩЕН**\n\n✅ Сервер: Railway\n📊 Отчеты каждые 5 минут\n🔍 Поиск возможностей каждые 2 минуты\n💓 Heartbeat каждые 30 минут\n⏰ Запуск: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        await self.send_telegram(startup_msg)
        
        while True:
            try:
                self.cycles += 1
                current_time = self.get_time()
                print(f"\n[{current_time}] === ЦИКЛ {self.cycles} ===")
                
                # Heartbeat каждые 30 минут (1800 секунд)
                if time.time() - self.last_heartbeat >= 1800:
                    print(f"[{current_time}] Отправка heartbeat...")
                    await self.send_heartbeat()
                
                # Отчет о балансе каждые 5 минут (300 секунд)
                if time.time() - self.last_balance_report >= 300:
                    print(f"[{current_time}] Получение баланса...")
                    
                    try:
                        balance_report = await self.get_mexc_balance()
                        
                        # Добавляем статистику к отчету
                        uptime = (time.time() - self.start_time) / 3600
                        full_report = balance_report + f"\n\n📊 **Статистика:**\n• Время работы: {uptime:.1f}ч\n• Циклов: {self.cycles}\n• Ошибок: {self.errors_count}\n⏰ {current_time}"
                        
                        success = await self.send_telegram(full_report)
                        if success:
                            self.last_balance_report = time.time()
                            print(f"[{current_time}] Баланс отправлен успешно")
                        else:
                            print(f"[{current_time}] Ошибка отправки баланса")
                            
                    except Exception as e:
                        await self.handle_error(e, "Получение баланса")
                
                # Поиск возможностей каждые 2 минуты (120 секунд)
                if self.cycles % 2 == 0:  # Каждый второй цикл
                    print(f"[{current_time}] Поиск возможностей...")
                    
                    try:
                        opportunities = await self.find_opportunities()
                        
                        if opportunities:
                            opp_msg = opportunities + f"\n\n⏰ Время: {current_time}"
                            await self.send_telegram(opp_msg)
                            print(f"[{current_time}] Возможности найдены и отправлены")
                        else:
                            print(f"[{current_time}] Хороших возможностей не найдено")
                            
                    except Exception as e:
                        await self.handle_error(e, "Поиск возможностей")
                
                # Статистика каждые 20 циклов
                if self.cycles % 20 == 0:
                    uptime = (time.time() - self.start_time) / 3600
                    stats = f"📊 **СТАТИСТИКА РАБОТЫ**\n\n⏰ Время работы: {uptime:.1f} часов\n🔄 Циклов выполнено: {self.cycles}\n❌ Ошибок: {self.errors_count}\n💓 Последний heartbeat: {(time.time() - self.last_heartbeat)/60:.1f} мин назад\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    
                    await self.send_telegram(stats)
                    print(f"[{current_time}] Статистика отправлена")
                
                # Пауза между циклами (1 минута)
                print(f"[{current_time}] Ожидание 60 секунд...")
                await asyncio.sleep(60)
                
            except KeyboardInterrupt:
                print(f"\n[{self.get_time()}] Остановка по запросу пользователя")
                await self.send_telegram("⏹️ **Railway бот остановлен по запросу пользователя**")
                break
                
            except Exception as e:
                await self.handle_error(e, "Главный цикл")
                print(f"[{self.get_time()}] Пауза 60 секунд после ошибки...")
                await asyncio.sleep(60)  # Пауза при критической ошибке

async def main():
    """Главная функция для Railway"""
    print("🚀 RAILWAY ТРЕУГОЛЬНЫЙ АРБИТРАЖ БОТ")
    print("=" * 50)
    print("✅ Оптимизирован для Railway")
    print("📊 Отчеты о балансе каждые 5 минут")
    print("🔍 Поиск возможностей каждые 2 минуты")
    print("💓 Heartbeat каждые 30 минут")
    print("⚠️ Обработка всех ошибок")
    print("🛡️ Безопасно - только мониторинг")
    print("=" * 50)
    
    bot = RailwayBot()
    
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\n⏹️ Остановка...")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        traceback.print_exc()
        
        # Попытка отправить уведомление о критической ошибке
        try:
            await bot.send_telegram(f"💥 **КРИТИЧЕСКАЯ ОШИБКА БОТА**\n\n❌ {str(e)[:300]}\n\n🔄 Попытка перезапуска...")
        except:
            pass

if __name__ == "__main__":
    # Для Railway важно правильно обрабатывать сигналы
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Остановка...")
    except Exception as e:
        print(f"Фатальная ошибка: {e}")
        sys.exit(1)