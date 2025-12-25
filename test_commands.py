#!/usr/bin/env python3
"""
Тест команд для простого бота
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

async def test_bot_commands():
    """Тест команд бота"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ Токен или chat_id не найдены")
        return
    
    try:
        bot = Bot(token=bot_token)
        
        print("🔺 ТЕСТ ПРОСТОГО БОТА БЕЗ КНОПОК")
        print("=" * 40)
        
        # Тест 1: Отправляем /start
        print("1️⃣ Отправка команды /start...")
        await bot.send_message(
            chat_id=chat_id,
            text="/start"
        )
        
        await asyncio.sleep(2)
        
        # Тест 2: Отправляем /status
        print("2️⃣ Отправка команды /status...")
        await bot.send_message(
            chat_id=chat_id,
            text="/status"
        )
        
        await asyncio.sleep(2)
        
        # Тест 3: Отправляем текстовую команду
        print("3️⃣ Отправка текстовой команды 'статус'...")
        await bot.send_message(
            chat_id=chat_id,
            text="статус"
        )
        
        await asyncio.sleep(2)
        
        # Тест 4: Отправляем /help
        print("4️⃣ Отправка команды /help...")
        await bot.send_message(
            chat_id=chat_id,
            text="/help"
        )
        
        print("\n✅ Все тестовые команды отправлены!")
        print("📱 Проверьте Telegram - бот должен ответить на каждую команду")
        print("\n💡 Если бот отвечает - значит простая версия работает!")
        print("🚫 Кнопки больше не нужны - все через команды")
        
    except Exception as e:
        print(f"❌ Ошибка отправки команд: {e}")

if __name__ == "__main__":
    asyncio.run(test_bot_commands())