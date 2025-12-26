#!/usr/bin/env python3
"""
УЛЬТРА ПРОСТОЙ бот который точно работает
Только отчеты о балансе каждые 5 минут + поиск возможностей
"""

import asyncio
import time
import os
from datetime import datetime

# Загружаем переменные окружения
try:
    from dotenv import load_dotenv
    if os.path.exists('.env'):
        load_dotenv('.env')
except ImportError:
    pass

class UltraSimpleBot:
    """Ультра простой бот"""
    
    def __init__(self):
        self.telegram_bot = None
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        self.cycles = 0
        self.start_time = time.time()
        self.last_balance_report = 0
        
        print("Ультра простой бот инициализирован")
    
    async def send_telegram(self, message: str):
        """Отправка сообщения в Telegram"""
        if not self.telegram_token or not self.telegram_chat_id:
            print(f"[Telegram] {message}")
            return
        
        try:
            if not self.telegram_bot:
                from telegram import Bot
                self.telegram_bot = Bot(token=self.telegram_token)
            
            await self.telegram_bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message
            )
            print(f"[Telegram] Отправлено: {message[:50]}...")
        except Exception as e:
            print(f"[Telegram] Ошибка: {e}")
    
    async def get_mexc_balance(self):
        """Получить баланс с MEXC"""
        try:
            import ccxt
            
            api_key = os.getenv('MEXC_API_KEY')
            api_secret = os.getenv('MEXC_API_SECRET')
            
            if not api_key or not api_secret:
                return "Нет API ключей MEXC"
            
            # Простое подключение к MEXC
            exchange = ccxt.mexc({
                'apiKey': api_key,
                'secret': api_secret,
                'sandbox': False,
                'enableRateLimit': True
            })
            
            # Получаем баланс
            balance = exchange.fetch_balance()
            
            # Собираем валюты с балансом
            currencies = []
            total_usdt = 0
            
            for currency, info in balance.items():
                free = info.get('free', 0)
                if free > 0.001:
                    currencies.append(f"{currency}: {free:.6f}")
                    
                    if currency == 'USDT':
                        total_usdt += free
                    else:
                        # Пробуем оценить в USDT
                        try:
                            ticker = exchange.fetch_ticker(f"{currency}/USDT")
                            usdt_value = free * ticker['last']
                            total_usdt += usdt_value
                            currencies[-1] += f" (≈{usdt_value:.2f} USDT)"
                        except:
                            pass
            
            if not currencies:
                return "Нет доступных средств на MEXC"
            
            # Формируем отчет
            report = "💰 ОТЧЕТ О БАЛАНСЕ MEXC\n\n"
            report += "\n".join(currencies[:10])
            report += f"\n\n💵 Общая стоимость: ≈{total_usdt:.2f} USDT"
            
            return report
            
        except Exception as e:
            return f"Ошибка получения баланса MEXC: {e}"
    
    async def find_opportunities(self):
        """Поиск простых возможностей"""
        try:
            import ccxt
            
            api_key = os.getenv('MEXC_API_KEY')
            api_secret = os.getenv('MEXC_API_SECRET')
            
            if not api_key or not api_secret:
                return "Нет API ключей для поиска"
            
            exchange = ccxt.mexc({
                'apiKey': api_key,
                'secret': api_secret,
                'sandbox': False,
                'enableRateLimit': True
            })
            
            # Простые пары для проверки
            pairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
            opportunities = []
            
            for pair in pairs:
                try:
                    ticker = exchange.fetch_ticker(pair)
                    
                    # Простая проверка спреда
                    bid = ticker['bid']
                    ask = ticker['ask']
                    spread = ((ask - bid) / bid) * 100
                    
                    if spread < 0.5:  # Хороший спред
                        opportunities.append(f"{pair}: спред {spread:.3f}%")
                        
                except Exception as e:
                    continue
            
            if opportunities:
                return "🔍 НАЙДЕННЫЕ ВОЗМОЖНОСТИ:\n\n" + "\n".join(opportunities)
            else:
                return "🔍 Возможности не найдены (спреды слишком большие)"
                
        except Exception as e:
            return f"Ошибка поиска возможностей: {e}"
    
    async def run(self):
        """Главный цикл"""
        print("🤖 Запуск ультра простого бота...")
        
        # Стартовое сообщение
        await self.send_telegram("🤖 УЛЬТРА ПРОСТОЙ БОТ ЗАПУЩЕН\n\nОтчеты каждые 5 минут\nПоиск возможностей каждую минуту")
        
        while True:
            try:
                self.cycles += 1
                current_time = datetime.now().strftime('%H:%M:%S')
                print(f"\n[{current_time}] Цикл {self.cycles}")
                
                # Отчет о балансе каждые 5 минут
                if time.time() - self.last_balance_report >= 300:  # 5 минут
                    print("[Баланс] Получение отчета о балансе...")
                    balance_report = await self.get_mexc_balance()
                    
                    # Добавляем статистику
                    uptime = (time.time() - self.start_time) / 3600
                    full_report = balance_report + f"\n\n📊 Время работы: {uptime:.1f}ч\n🔄 Циклов: {self.cycles}\n⏰ Время: {current_time}"
                    
                    await self.send_telegram(full_report)
                    self.last_balance_report = time.time()
                    print("[Баланс] Отчет отправлен")
                
                # Поиск возможностей каждый цикл
                print("[Поиск] Поиск возможностей...")
                opportunities = await self.find_opportunities()
                
                # Отправляем только если найдены хорошие возможности
                if "спред" in opportunities and "0.1" in opportunities:
                    await self.send_telegram(opportunities + f"\n\n⏰ Время: {current_time}")
                    print("[Поиск] Возможности найдены и отправлены")
                else:
                    print("[Поиск] Хороших возможностей не найдено")
                
                # Краткая статистика каждые 10 циклов
                if self.cycles % 10 == 0:
                    uptime = (time.time() - self.start_time) / 3600
                    stats = f"📊 Статистика: {uptime:.1f}ч работы, {self.cycles} циклов, время {current_time}"
                    await self.send_telegram(stats)
                    print("[Статистика] Отправлена")
                
                # Пауза между циклами (1 минута)
                print("[Ожидание] 60 секунд до следующего цикла...")
                await asyncio.sleep(60)
                
            except KeyboardInterrupt:
                print("\n[Остановка] По запросу пользователя")
                await self.send_telegram("⏹️ Ультра простой бот остановлен")
                break
            except Exception as e:
                print(f"[Ошибка] Цикл: {e}")
                await self.send_telegram(f"⚠️ Ошибка в цикле: {e}")
                await asyncio.sleep(30)  # Пауза при ошибке

async def main():
    """Главная функция"""
    print("🤖 УЛЬТРА ПРОСТОЙ ТРЕУГОЛЬНЫЙ АРБИТРАЖ")
    print("=" * 50)
    print("✅ Максимально упрощенная версия")
    print("📊 Отчеты о балансе каждые 5 минут")
    print("🔍 Поиск возможностей каждую минуту")
    print("📱 Все уведомления в Telegram")
    print("🛡️ Безопасно - только мониторинг")
    print("=" * 50)
    
    bot = UltraSimpleBot()
    
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\n⏹️ Остановка...")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())