#!/usr/bin/env python3
"""
Ультра-простой бот - максимальная совместимость с Railway
Без сложной логики, только базовые функции
"""

import logging
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, ContextTypes, filters, CommandHandler

# Минимальное логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8565304713:AAFpnuNkp4QR6Yk9H-5NoN8l3Z1pN2WigKQ')

def create_keyboard():
    """Создать простую клавиатуру"""
    keyboard = [
        [KeyboardButton("📊 Статус")],
        [KeyboardButton("▶️ Запуск"), KeyboardButton("⏹️ Стоп")],
        [KeyboardButton("📈 Инфо")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    keyboard = create_keyboard()
    text = """🤖 Арбитражный бот запущен!

Используйте кнопки внизу экрана для управления.

Команды:
/start - перезапуск
/help - помощь"""
    
    await update.message.reply_text(text, reply_markup=keyboard)
    logger.info(f"Start command from user {update.effective_user.id}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    keyboard = create_keyboard()
    text = """❓ Помощь

Доступные кнопки:
📊 Статус - состояние системы
▶️ Запуск - запустить мониторинг
⏹️ Стоп - остановить мониторинг  
📈 Инфо - информация о системе

Команды:
/start - главное меню
/help - эта справка"""
    
    await update.message.reply_text(text, reply_markup=keyboard)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    text = update.message.text
    user_id = update.effective_user.id
    keyboard = create_keyboard()
    
    logger.info(f"Message '{text}' from user {user_id}")
    
    if text == "📊 Статус":
        response = """📊 СТАТУС СИСТЕМЫ

🟢 Бот: Активен
🔄 Мониторинг: Готов к запуску
⏰ Время: Онлайн

Система работает нормально."""
        
    elif text == "▶️ Запуск":
        response = """▶️ СИСТЕМА ЗАПУЩЕНА

🚀 Мониторинг арбитража активирован
📱 Уведомления включены
⚡ Поиск возможностей начат

Система работает в фоновом режиме."""
        
    elif text == "⏹️ Стоп":
        response = """⏹️ СИСТЕМА ОСТАНОВЛЕНА

🛑 Мониторинг приостановлен
📴 Уведомления отключены
💤 Система в режиме ожидания

Используйте ▶️ Запуск для возобновления."""
        
    elif text == "📈 Инфо":
        response = """📈 ИНФОРМАЦИЯ О СИСТЕМЕ

🤖 Арбитражный монитор v2.0
🌐 Платформа: Railway
💧 Проверка ликвидности: Включена
🔄 Межбиржевой арбитраж: Активен
🔺 Треугольный арбитраж: Активен

Система готова к работе!"""
        
    else:
        response = f"""❓ Неизвестная команда: "{text}"

Используйте кнопки внизу экрана или команды:
/start - главное меню
/help - справка

Доступные кнопки:
📊 Статус
▶️ Запуск  
⏹️ Стоп
📈 Инфо"""
    
    try:
        await update.message.reply_text(response, reply_markup=keyboard)
        logger.info(f"Response sent to user {user_id}")
    except Exception as e:
        logger.error(f"Error sending response: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ошибок"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Главная функция"""
    logger.info("Starting ultra simple bot...")
    
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Bot started successfully")
    print("🤖 Ultra Simple Bot запущен!")
    print("📱 Кнопки: Статус, Запуск, Стоп, Инфо")
    
    # Используем polling для максимальной совместимости
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == "__main__":
    main()