#!/usr/bin/env python3
"""
Тестовый бот для проверки работы кнопок
Выводит подробную информацию в консоль
"""

import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, BotCommand
from telegram.ext import Application, MessageHandler, ContextTypes, filters, CommandHandler

# Настройка подробного логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = "8565304713:AAFpnuNkp4QR6Yk9H-5NoN8l3Z1pN2WigKQ"

def get_keyboard():
    """Получить клавиатуру"""
    keyboard = [
        [KeyboardButton("📊 Статус"), KeyboardButton("⚙️ Настройки")],
        [KeyboardButton("▶️ Запуск"), KeyboardButton("⏹️ Остановка")],
        [KeyboardButton("🔄 Перезапуск"), KeyboardButton("📈 Статистика")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

async def send_message(update: Update, text: str):
    """Отправить сообщение с клавиатурой и логированием"""
    keyboard = get_keyboard()
    
    print(f"📤 ОТПРАВКА СООБЩЕНИЯ:")
    print(f"   Текст: {text[:50]}...")
    print(f"   Клавиатура: {len(keyboard.keyboard)} рядов кнопок")
    
    try:
        message = await update.message.reply_text(text, reply_markup=keyboard)
        print(f"✅ Сообщение отправлено успешно (ID: {message.message_id})")
        logger.info(f"✅ Сообщение отправлено с клавиатурой")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки сообщения: {e}")
        logger.error(f"❌ Ошибка отправки: {e}")
        return False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    print(f"\n🚀 КОМАНДА /start")
    print(f"   Пользователь: {update.effective_user.first_name}")
    print(f"   Chat ID: {update.effective_chat.id}")
    
    text = f"""🤖 ТЕСТОВЫЙ БОТ ЗАПУЩЕН

Время: {datetime.now().strftime('%H:%M:%S')}
Пользователь: {update.effective_user.first_name}
Chat ID: {update.effective_chat.id}

📱 Кнопки должны появиться внизу экрана
🔧 Команды: /start, /test, /keyboard"""
    
    success = await send_message(update, text)
    print(f"   Результат: {'✅ Успех' if success else '❌ Ошибка'}")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /test"""
    print(f"\n🧪 КОМАНДА /test")
    
    text = f"""🧪 ТЕСТ КЛАВИАТУРЫ

Время: {datetime.now().strftime('%H:%M:%S')}

Если вы видите это сообщение, бот работает!
Проверьте кнопки внизу экрана."""
    
    await send_message(update, text)

async def keyboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /keyboard - принудительная установка клавиатуры"""
    print(f"\n⌨️ КОМАНДА /keyboard - ПРИНУДИТЕЛЬНАЯ УСТАНОВКА")
    
    text = f"""⌨️ ПРИНУДИТЕЛЬНАЯ УСТАНОВКА КЛАВИАТУРЫ

Время: {datetime.now().strftime('%H:%M:%S')}

Клавиатура установлена принудительно!
Кнопки должны появиться внизу экрана."""
    
    await send_message(update, text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений"""
    text = update.message.text
    user = update.effective_user.first_name
    
    print(f"\n📨 ПОЛУЧЕНО СООБЩЕНИЕ:")
    print(f"   От: {user}")
    print(f"   Текст: '{text}'")
    print(f"   Время: {datetime.now().strftime('%H:%M:%S')}")
    
    # Определяем ответ
    if text == "📊 Статус":
        print(f"   🎯 Обработка: Статус")
        response = f"📊 СТАТУС СИСТЕМЫ\n\nВремя: {datetime.now().strftime('%H:%M:%S')}\nСтатус: 🟢 Работает\nПользователь: {user}"
        
    elif text == "⚙️ Настройки":
        print(f"   🎯 Обработка: Настройки")
        response = f"⚙️ НАСТРОЙКИ\n\nВремя: {datetime.now().strftime('%H:%M:%S')}\nВсе настройки активны\nПользователь: {user}"
        
    elif text == "▶️ Запуск":
        print(f"   🎯 Обработка: Запуск")
        response = f"▶️ СИСТЕМА ЗАПУЩЕНА\n\nВремя: {datetime.now().strftime('%H:%M:%S')}\nМонитор активирован\nПользователь: {user}"
        
    elif text == "⏹️ Остановка":
        print(f"   🎯 Обработка: Остановка")
        response = f"⏹️ СИСТЕМА ОСТАНОВЛЕНА\n\nВремя: {datetime.now().strftime('%H:%M:%S')}\nМонитор деактивирован\nПользователь: {user}"
        
    elif text == "🔄 Перезапуск":
        print(f"   🎯 Обработка: Перезапуск")
        response = f"🔄 СИСТЕМА ПЕРЕЗАПУЩЕНА\n\nВремя: {datetime.now().strftime('%H:%M:%S')}\nВсе процессы обновлены\nПользователь: {user}"
        
    elif text == "📈 Статистика":
        print(f"   🎯 Обработка: Статистика")
        response = f"📈 СТАТИСТИКА\n\nВремя: {datetime.now().strftime('%H:%M:%S')}\nВсе системы работают\nПользователь: {user}"
        
    else:
        print(f"   🎯 Обработка: Неизвестная команда")
        response = f"❓ НЕИЗВЕСТНАЯ КОМАНДА\n\nВы написали: '{text}'\nВремя: {datetime.now().strftime('%H:%M:%S')}\n\nИспользуйте кнопки внизу или команды:\n/start, /test, /keyboard"
    
    # Отправляем ответ
    success = await send_message(update, response)
    print(f"   📤 Ответ отправлен: {'✅ Успех' if success else '❌ Ошибка'}")

async def setup_commands(app):
    """Настройка команд бота"""
    print(f"\n🔧 НАСТРОЙКА КОМАНД БОТА...")
    
    commands = [
        BotCommand("start", "🤖 Запуск бота"),
        BotCommand("test", "🧪 Тест клавиатуры"),
        BotCommand("keyboard", "⌨️ Принудительная установка клавиатуры")
    ]
    
    try:
        await app.bot.set_my_commands(commands)
        print(f"✅ Команды установлены: {len(commands)} шт.")
        logger.info("✅ Команды бота установлены")
    except Exception as e:
        print(f"❌ Ошибка установки команд: {e}")
        logger.error(f"❌ Ошибка установки команд: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    error_msg = str(context.error)
    print(f"\n❌ ОШИБКА В БОТЕ:")
    print(f"   Описание: {error_msg}")
    print(f"   Время: {datetime.now().strftime('%H:%M:%S')}")
    
    logger.error(f"❌ Ошибка в боте: {context.error}")
    
    if update and update.message:
        try:
            await update.message.reply_text(
                f"❌ Произошла ошибка: {error_msg}\n\nИспользуйте /start для перезапуска",
                reply_markup=get_keyboard()
            )
            print(f"   📤 Сообщение об ошибке отправлено")
        except Exception as e:
            print(f"   ❌ Не удалось отправить сообщение об ошибке: {e}")

def main():
    """Главная функция"""
    print("=" * 60)
    print("🤖 ЗАПУСК ТЕСТОВОГО БОТА")
    print("=" * 60)
    print(f"⏰ Время запуска: {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}")
    print(f"🔑 Токен: {BOT_TOKEN[:20]}...")
    print(f"📱 Ожидаемые кнопки: 6 штук в 3 ряда")
    print("=" * 60)
    
    logger.info("🤖 Запуск тестового бота...")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CommandHandler("keyboard", keyboard_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    
    # Настройка команд
    async def post_init(application):
        await setup_commands(application)
        print("🚀 Бот полностью инициализирован и готов к работе!")
        print("📱 Отправьте любое сообщение боту для проверки кнопок")
    
    app.post_init = post_init
    
    try:
        print("\n🔄 Запуск polling...")
        app.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        print("\n⏹️ Бот остановлен пользователем")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")

if __name__ == "__main__":
    main()