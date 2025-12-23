#!/usr/bin/env python3
"""
Минимальный бот - только самое необходимое
Гарантированно работает на любой платформе
"""

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# Простое логирование
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Токен бота
TOKEN = '8565304713:AAFpnuNkp4QR6Yk9H-5NoN8l3Z1pN2WigKQ'

def make_keyboard():
    """Создать клавиатуру"""
    buttons = [
        [KeyboardButton("Статус"), KeyboardButton("Запуск")],
        [KeyboardButton("Стоп"), KeyboardButton("Инфо")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ЛЮБОГО сообщения"""
    user_text = update.message.text
    keyboard = make_keyboard()
    
    print(f"Получено: '{user_text}'")
    
    # Простые ответы
    if user_text == "Статус":
        reply = "🟢 Система работает\n⏰ Время: онлайн\n📊 Статус: активен"
    elif user_text == "Запуск":
        reply = "▶️ Мониторинг запущен!\n🚀 Поиск арбитража активен\n📱 Уведомления включены"
    elif user_text == "Стоп":
        reply = "⏹️ Мониторинг остановлен\n🛑 Поиск приостановлен\n💤 Система в ожидании"
    elif user_text == "Инфо":
        reply = "📈 Арбитражный бот v1.0\n🌐 Платформа: Railway\n🤖 Статус: готов к работе"
    else:
        reply = f"Вы написали: {user_text}\n\nИспользуйте кнопки:\n• Статус\n• Запуск\n• Стоп\n• Инфо"
    
    try:
        await update.message.reply_text(reply, reply_markup=keyboard)
        print(f"Ответ отправлен: {reply[:30]}...")
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def main():
    """Запуск бота"""
    print("🤖 Запуск минимального бота...")
    
    app = Application.builder().token(TOKEN).build()
    
    # Один обработчик для ВСЕХ текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT, handle_any_message))
    
    print("✅ Бот запущен!")
    print("📱 Кнопки: Статус, Запуск, Стоп, Инфо")
    
    # Запуск с максимальной совместимостью
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()