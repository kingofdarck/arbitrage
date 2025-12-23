#!/usr/bin/env python3
"""
Сброс команд бота и установка новых
"""

import asyncio
from telegram import Bot, BotCommand
from config import NOTIFICATION_CONFIG

async def reset_bot_commands():
    """Сброс и установка команд бота"""
    try:
        bot_token = NOTIFICATION_CONFIG['telegram']['bot_token']
        bot = Bot(token=bot_token)
        
        print("🤖 Подключение к боту...")
        me = await bot.get_me()
        print(f"✅ Подключен к боту: @{me.username}")
        
        # Удаляем все старые команды
        print("🗑️ Удаление старых команд...")
        await bot.delete_my_commands()
        
        # Устанавливаем новые команды
        print("📝 Установка новых команд...")
        commands = [
            BotCommand("start", "🤖 Главное меню управления арбитражем")
        ]
        await bot.set_my_commands(commands)
        
        # Отправляем тестовое сообщение с новым меню
        chat_id = NOTIFICATION_CONFIG['telegram']['chat_id']
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Статус", callback_data="status"),
                InlineKeyboardButton("⚙️ Настройки", callback_data="settings")
            ],
            [
                InlineKeyboardButton("▶️ Запуск", callback_data="start_monitor"),
                InlineKeyboardButton("⏹️ Остановка", callback_data="stop_monitor")
            ],
            [
                InlineKeyboardButton("🔄 Перезапуск", callback_data="restart_monitor"),
                InlineKeyboardButton("📈 Статистика", callback_data="stats")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = """
🔄 **БОТ ОБНОВЛЕН!**

Команды сброшены и установлены заново.

🤖 **АРБИТРАЖНЫЙ МОНИТОР**

Теперь доступно новое меню управления:
        """
        
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        print("✅ Команды обновлены!")
        print("📱 Новое меню отправлено в чат")
        print("\n🎯 Теперь отправьте /start для нового меню")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(reset_bot_commands())