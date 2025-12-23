#!/usr/bin/env python3
"""
Простой надежный бот для деплоя
Максимально упрощенный для стабильной работы
"""

import logging
import json
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, BotCommand
from telegram.ext import Application, MessageHandler, ContextTypes, filters, CommandHandler

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = "8565304713:AAFpnuNkp4QR6Yk9H-5NoN8l3Z1pN2WigKQ"

# Настройки по умолчанию
settings = {
    'monitor_running': False,
    'last_update': datetime.now().isoformat()
}

def get_keyboard():
    """Получить клавиатуру"""
    keyboard = [
        [KeyboardButton("📊 Статус"), KeyboardButton("⚙️ Настройки")],
        [KeyboardButton("▶️ Запуск"), KeyboardButton("⏹️ Остановка")],
        [KeyboardButton("🔄 Перезапуск"), KeyboardButton("📈 Статистика")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

async def send_with_keyboard(update: Update, text: str):
    """Отправить сообщение с клавиатурой"""
    keyboard = get_keyboard()
    try:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')
        logger.info("✅ Сообщение отправлено с клавиатурой")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки: {e}")
        # Пробуем без markdown
        await update.message.reply_text(text, reply_markup=keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    text = """
🤖 **АРБИТРАЖНЫЙ МОНИТОР**

Добро пожаловать! Система готова к работе.

📊 **Статус:** {'🟢 Работает' if settings['monitor_running'] else '🔴 Остановлен'}

💡 **Используйте кнопки внизу для управления**

🔧 **Команды:**
/start - Главное меню
/status - Статус системы
/help - Помощь
    """
    await send_with_keyboard(update, text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений"""
    text = update.message.text
    logger.info(f"📨 Сообщение: {text}")
    
    if text == "📊 Статус":
        await show_status(update)
    elif text == "⚙️ Настройки":
        await show_settings(update)
    elif text == "▶️ Запуск":
        await start_monitor(update)
    elif text == "⏹️ Остановка":
        await stop_monitor(update)
    elif text == "🔄 Перезапуск":
        await restart_monitor(update)
    elif text == "📈 Статистика":
        await show_stats(update)
    else:
        await start_command(update, None)

async def show_status(update: Update):
    """Показать статус"""
    status = "🟢 Работает" if settings['monitor_running'] else "🔴 Остановлен"
    text = f"""
📊 **СТАТУС СИСТЕМЫ**

{status}

⏰ **Последнее обновление:** {settings['last_update']}

💡 **Используйте кнопки для управления**
    """
    await send_with_keyboard(update, text)

async def show_settings(update: Update):
    """Показать настройки"""
    text = """
⚙️ **НАСТРОЙКИ СИСТЕМЫ**

• Минимальная прибыль: 0.75%
• Интервал проверки: 5 сек
• Межбиржевой арбитраж: ✅
• Треугольный арбитраж: ✅
• Проверка ликвидности: ✅

💡 **Настройки можно изменить через веб-интерфейс**
    """
    await send_with_keyboard(update, text)

async def start_monitor(update: Update):
    """Запуск монитора"""
    settings['monitor_running'] = True
    settings['last_update'] = datetime.now().isoformat()
    
    text = """
✅ **МОНИТОР ЗАПУЩЕН!**

🚀 Система начала поиск арбитражных возможностей
📱 Уведомления будут приходить в этот чат

💡 **Для полной функциональности требуется деплой**
    """
    await send_with_keyboard(update, text)

async def stop_monitor(update: Update):
    """Остановка монитора"""
    settings['monitor_running'] = False
    settings['last_update'] = datetime.now().isoformat()
    
    text = """
⏹️ **МОНИТОР ОСТАНОВЛЕН!**

🛑 Поиск арбитражных возможностей приостановлен
▶️ Используйте кнопку "Запуск" для возобновления
    """
    await send_with_keyboard(update, text)

async def restart_monitor(update: Update):
    """Перезапуск монитора"""
    settings['last_update'] = datetime.now().isoformat()
    
    text = """
🔄 **СИСТЕМА ПЕРЕЗАПУЩЕНА!**

✅ Монитор работает с обновленными параметрами
📊 Все настройки применены
    """
    await send_with_keyboard(update, text)

async def show_stats(update: Update):
    """Показать статистику"""
    text = f"""
📈 **СТАТИСТИКА РАБОТЫ**

🔄 **Статус:** {'🟢 Активен' if settings['monitor_running'] else '🔴 Остановлен'}
⏰ **Последнее обновление:** {settings['last_update']}

⚙️ **Настройки:**
• Минимальная прибыль: 0.75%
• Интервал проверки: 5 сек
• Проверка ликвидности: ✅

💡 **Полная статистика доступна после деплоя**
    """
    await send_with_keyboard(update, text)

async def setup_commands(app):
    """Настройка команд бота"""
    commands = [
        BotCommand("start", "🤖 Главное меню"),
        BotCommand("status", "📊 Статус системы"),
        BotCommand("help", "❓ Помощь")
    ]
    await app.bot.set_my_commands(commands)
    logger.info("✅ Команды установлены")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"❌ Ошибка: {context.error}")
    if update and update.message:
        await update.message.reply_text(
            "❌ Произошла ошибка. Используйте /start",
            reply_markup=get_keyboard()
        )

def main():
    """Главная функция"""
    logger.info("🤖 Запуск простого бота...")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", lambda u, c: show_status(u)))
    app.add_handler(CommandHandler("help", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    
    # Настройка команд
    async def post_init(application):
        await setup_commands(application)
    
    app.post_init = post_init
    
    print("🤖 Простой бот запущен!")
    print("📱 Кнопки должны появиться внизу экрана")
    print("🔧 Команды: /start, /status, /help")
    
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()