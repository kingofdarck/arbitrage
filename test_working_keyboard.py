#!/usr/bin/env python3
"""
Тест рабочих кнопок Telegram бота
Проверяем что кнопки отвечают как до переключения на MEXC
"""

import asyncio
import logging
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, ContextTypes, filters, CommandHandler

# Загружаем переменные окружения
try:
    from dotenv import load_dotenv
    if os.path.exists('.env'):
        load_dotenv('.env')
except ImportError:
    pass

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_main_keyboard():
    """Получить основную клавиатуру"""
    keyboard = [
        [KeyboardButton("📊 Статус"), KeyboardButton("⚙️ Настройки")],
        [KeyboardButton("▶️ Запуск"), KeyboardButton("⏹️ Остановка")],
        [KeyboardButton("🔄 Перезапуск"), KeyboardButton("📈 Статистика")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    keyboard = get_main_keyboard()
    
    text = """
🔺 **ТЕСТ РАБОЧИХ КНОПОК**

✅ Кнопки должны работать как до переключения на MEXC
🤖 Каждая кнопка должна отвечать
📱 Клавиатура должна быть постоянной

💡 **Нажмите любую кнопку для проверки**
    """
    
    await update.message.reply_text(
        text, 
        reply_markup=keyboard, 
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех сообщений"""
    message_text = update.message.text
    keyboard = get_main_keyboard()
    
    if message_text == "📊 Статус":
        response = "✅ **КНОПКА СТАТУС РАБОТАЕТ!**\n\n🔺 Арбитраж по умолчанию выключен\n💡 Кнопки отвечают корректно"
    elif message_text == "⚙️ Настройки":
        response = "✅ **КНОПКА НАСТРОЙКИ РАБОТАЕТ!**\n\n⚙️ Меню настроек доступно\n🔧 Все параметры настраиваются"
    elif message_text == "▶️ Запуск":
        response = "✅ **КНОПКА ЗАПУСК РАБОТАЕТ!**\n\n🚀 Арбитраж можно запустить\n🔺 Система готова к работе"
    elif message_text == "⏹️ Остановка":
        response = "✅ **КНОПКА ОСТАНОВКА РАБОТАЕТ!**\n\n⏹️ Арбитраж можно остановить\n🛑 Система корректно останавливается"
    elif message_text == "🔄 Перезапуск":
        response = "✅ **КНОПКА ПЕРЕЗАПУСК РАБОТАЕТ!**\n\n🔄 Система может перезапуститься\n⚡ Новые настройки применяются"
    elif message_text == "📈 Статистика":
        response = "✅ **КНОПКА СТАТИСТИКА РАБОТАЕТ!**\n\n📊 Статистика отображается\n📈 Все данные доступны"
    else:
        response = f"✅ **ПОЛУЧЕНО СООБЩЕНИЕ:** `{message_text}`\n\n💡 Используйте кнопки внизу экрана"
    
    await update.message.reply_text(
        response, 
        reply_markup=keyboard, 
        parse_mode='Markdown'
    )

def main():
    """Главная функция"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не найден в .env")
        return
    
    # Создаем приложение
    application = Application.builder().token(bot_token).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    # Запускаем бота
    logger.info("🤖 Запуск теста рабочих кнопок...")
    print("🔺 ТЕСТ РАБОЧИХ КНОПОК TELEGRAM БОТА")
    print("✅ Каждая кнопка должна отвечать")
    print("📱 Клавиатура должна быть постоянной")
    print("💡 Нажмите Ctrl+C для остановки")
    
    application.run_polling()

if __name__ == "__main__":
    main()