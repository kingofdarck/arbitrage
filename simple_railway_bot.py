#!/usr/bin/env python3
"""
Простой Railway бот для диагностики
"""

import asyncio
import os
import time
from datetime import datetime

# Загружаем переменные окружения
try:
    from dotenv import load_dotenv
    if os.path.exists('.env'):
        load_dotenv('.env')
except ImportError:
    pass

async def send_telegram_message(message):
    """Отправка сообщения в Telegram"""
    try:
        from telegram import Bot
        
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not token or not chat_id:
            print(f"❌ Нет Telegram токена или chat_id")
            return False
        
        bot = Bot(token=token)
        await bot.send_message(chat_id=chat_id, text=message)
        print(f"✅ Сообщение отправлено: {message[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка Telegram: {e}")
        return False

async def test_mexc_connection():
    """Тест подключения к MEXC"""
    try:
        import ccxt
        
        api_key = os.getenv('MEXC_API_KEY')
        api_secret = os.getenv('MEXC_API_SECRET')
        
        if not api_key or not api_secret:
            return False, "Нет API ключей"
        
        exchange = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': False,
            'enableRateLimit': True,
            'timeout': 30000,
        })
        
        # Простой тест
        balance = exchange.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('free', 0)
        
        return True, f"USDT баланс: {usdt_balance:.2f}"
        
    except Exception as e:
        return False, f"Ошибка MEXC: {str(e)[:100]}"

async def main():
    """Главная функция"""
    print("🚀 ПРОСТОЙ RAILWAY БОТ - ДИАГНОСТИКА")
    print("=" * 50)
    
    # Проверяем переменные окружения
    print("🔧 Проверка переменных окружения...")
    
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    mexc_key = os.getenv('MEXC_API_KEY')
    mexc_secret = os.getenv('MEXC_API_SECRET')
    
    print(f"Telegram токен: {'✅' if telegram_token else '❌'}")
    print(f"Telegram chat_id: {'✅' if telegram_chat_id else '❌'}")
    print(f"MEXC API key: {'✅' if mexc_key else '❌'}")
    print(f"MEXC API secret: {'✅' if mexc_secret else '❌'}")
    
    # Отправляем стартовое сообщение
    startup_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    startup_msg = f"🚀 **RAILWAY БОТ ЗАПУЩЕН**\n\n⏰ Время: {startup_time}\n🌐 Сервер: Railway\n✅ Статус: Активен"
    
    print("📱 Отправка стартового сообщения...")
    telegram_success = await send_telegram_message(startup_msg)
    
    if not telegram_success:
        print("❌ Не удалось отправить стартовое сообщение")
        return
    
    # Тестируем MEXC
    print("🏦 Тестирование MEXC...")
    mexc_success, mexc_msg = await test_mexc_connection()
    
    mexc_report = f"🏦 **ТЕСТ MEXC**\n\n{'✅' if mexc_success else '❌'} {mexc_msg}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
    await send_telegram_message(mexc_report)
    
    # Главный цикл - отправляем heartbeat каждые 5 минут
    cycle = 0
    start_time = time.time()
    
    while True:
        try:
            cycle += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            uptime = (time.time() - start_time) / 60  # в минутах
            
            print(f"\n[{current_time}] === ЦИКЛ {cycle} ===")
            print(f"[{current_time}] Время работы: {uptime:.1f} минут")
            
            # Heartbeat каждые 5 минут (300 секунд)
            if cycle % 5 == 0:  # Каждый 5-й цикл (5 минут)
                heartbeat_msg = f"💓 **HEARTBEAT**\n\n🤖 Бот работает\n⏰ Время работы: {uptime:.1f} мин\n🔄 Циклов: {cycle}\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                print(f"[{current_time}] Отправка heartbeat...")
                await send_telegram_message(heartbeat_msg)
            
            # Пауза 1 минута
            print(f"[{current_time}] Ожидание 60 секунд...")
            await asyncio.sleep(60)
            
        except KeyboardInterrupt:
            print("\n⏹️ Остановка по запросу пользователя")
            await send_telegram_message("⏹️ **Railway бот остановлен**")
            break
            
        except Exception as e:
            error_msg = f"❌ **ОШИБКА БОТА**\n\n{str(e)[:200]}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            print(f"❌ Ошибка: {e}")
            await send_telegram_message(error_msg)
            await asyncio.sleep(60)  # Пауза при ошибке

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")