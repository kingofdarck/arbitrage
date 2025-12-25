#!/usr/bin/env python3
"""
Тест Telegram бота
"""

import asyncio
import os
from telegram import Bot

async def test_telegram():
    """Тест отправки сообщения в Telegram"""
    
    # Загружаем переменные окружения
    try:
        from dotenv import load_dotenv
        if os.path.exists('.env'):
            load_dotenv('.env')
    except ImportError:
        pass
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    print(f"🔑 Токен: {token[:20]}... (длина: {len(token) if token else 0})")
    print(f"💬 Chat ID: {chat_id}")
    
    if not token or not chat_id:
        print("❌ Токен или chat_id не найдены в .env")
        return
    
    try:
        bot = Bot(token=token)
        
        # Тест отправки сообщения
        print("📱 Отправка тестового сообщения...")
        await bot.send_message(
            chat_id=chat_id,
            text="🧪 **ТЕСТ TELEGRAM БОТА**\n\n✅ Бот работает корректно!\n🔺 Треугольный арбитраж готов к работе",
            parse_mode='Markdown'
        )
        print("✅ Сообщение отправлено успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        
        # Попробуем без Markdown
        try:
            print("🔄 Попытка без Markdown...")
            await bot.send_message(
                chat_id=chat_id,
                text="🧪 ТЕСТ TELEGRAM БОТА\n\nБот работает корректно!\nТреугольный арбитраж готов к работе"
            )
            print("✅ Сообщение отправлено без Markdown!")
        except Exception as e2:
            print(f"❌ Критическая ошибка: {e2}")

if __name__ == "__main__":
    asyncio.run(test_telegram())