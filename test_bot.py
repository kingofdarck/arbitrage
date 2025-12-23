#!/usr/bin/env python3
"""
Тест Telegram бота
"""

import asyncio
import logging
from telegram import Bot
from config import NOTIFICATION_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_bot():
    """Тест подключения к боту"""
    try:
        bot_token = NOTIFICATION_CONFIG['telegram']['bot_token']
        chat_id = NOTIFICATION_CONFIG['telegram']['chat_id']
        
        print(f"🤖 Тестируем бот...")
        print(f"📋 Токен: {bot_token[:10]}...")
        print(f"💬 Chat ID: {chat_id}")
        
        bot = Bot(token=bot_token)
        
        # Получаем информацию о боте
        me = await bot.get_me()
        print(f"✅ Бот найден: @{me.username} ({me.first_name})")
        
        # Отправляем тестовое сообщение
        message = await bot.send_message(
            chat_id=chat_id,
            text="🧪 **ТЕСТ БОТА**\n\nЕсли вы видите это сообщение, бот работает!\n\nОтправьте /start для меню управления.",
            parse_mode='Markdown'
        )
        print(f"✅ Сообщение отправлено: {message.message_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования бота: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_bot())
    if result:
        print("\n🎉 Бот работает! Теперь отправьте /start в Telegram")
    else:
        print("\n💥 Проблемы с ботом. Проверьте токен и chat_id в config.py")