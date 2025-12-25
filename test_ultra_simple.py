#!/usr/bin/env python3
"""
Тест ультра простого бота
"""

import os
import asyncio
from telegram import Bot

# Загружаем переменные окружения
try:
    from dotenv import load_dotenv
    if os.path.exists('.env'):
        load_dotenv('.env')
except ImportError:
    pass

async def test_ultra_simple():
    """Тест ультра простого бота"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ Токен или chat_id не найдены")
        return
    
    try:
        bot = Bot(token=bot_token)
        
        print("🔺 ТЕСТ УЛЬТРА ПРОСТОГО БОТА")
        print("=" * 40)
        
        # Тест 1: start
        print("1️⃣ Отправка 'start'...")
        await bot.send_message(chat_id=chat_id, text="start")
        await asyncio.sleep(2)
        
        # Тест 2: status
        print("2️⃣ Отправка 'status'...")
        await bot.send_message(chat_id=chat_id, text="status")
        await asyncio.sleep(2)
        
        # Тест 3: help
        print("3️⃣ Отправка 'help'...")
        await bot.send_message(chat_id=chat_id, text="help")
        await asyncio.sleep(2)
        
        # Тест 4: run
        print("4️⃣ Отправка 'run'...")
        await bot.send_message(chat_id=chat_id, text="run")
        await asyncio.sleep(2)
        
        print("\n✅ Все команды отправлены!")
        print("📱 Проверьте Telegram - бот должен ответить на каждую")
        print("🔺 Если отвечает - ультра простая версия работает!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_ultra_simple())