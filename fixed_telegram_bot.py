#!/usr/bin/env python3
"""
Исправленный Telegram бот управления треугольным арбитражем на MEXC
Устойчивый к проблемам деплоя
"""

import asyncio
import logging
import json
import os
import time
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, ContextTypes, filters, CommandHandler
from telegram.error import Conflict, NetworkError, TimedOut

# Загружаем переменные окружения
try:
    from dotenv import load_dotenv
    if os.path.exists('.env'):
        load_dotenv('.env')
except ImportError:
    pass

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Глобальные настройки с сохранением в файл
SETTINGS_FILE = 'triangular_settings.json'

default_settings = {
    'min_profit': 0.75,
    'max_position': 50.0,
    'trading_mode': 'live',
    'bot_running': False,
    'mexc_sandbox': False,
    'last_update': datetime.now().isoformat(),
    'total_trades': 0,
    'successful_trades': 0,
    'total_profit': 0.0
}

def load_settings():
    """Загрузка настроек из файла"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                logger.info("✅ Настройки загружены из файла")
                return settings
    except Exception as e:
        logger.warning(f"⚠️ Ошибка загрузки настроек: {e}")
    
    return default_settings.copy()

def save_settings(settings):
    """Сохранение настроек в файл"""
    try:
        settings['last_update'] = datetime.now().isoformat()
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        logger.info("💾 Настройки сохранены")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения настроек: {e}")

# Загружаем настройки при запуске
settings = load_settings()

# Основные кнопки меню (постоянные внизу экрана)
def get_main_keyboard():
    """Получить основную клавиатуру"""
    keyboard = [
        [KeyboardButton("📊 Статус"), KeyboardButton("⚙️ Настройки")],
        [KeyboardButton("▶️ Запуск"), KeyboardButton("⏹️ Остановка")],
        [KeyboardButton("🔄 Перезапуск"), KeyboardButton("📈 Статистика")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    # Игнорируем конфликты (другой бот уже запущен)
    if isinstance(context.error, Conflict):
        logger.info("🔄 Конфликт с другим экземпляром бота - это нормально для Railway")
        return
    
    # Игнорируем сетевые ошибки
    if isinstance(context.error, (NetworkError, TimedOut)):
        logger.warning("🌐 Сетевая ошибка - переподключение...")
        return

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    try:
        await show_welcome(update, context)
    except Exception as e:
        logger.error(f"Ошибка в start_command: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех сообщений"""
    try:
        if not update.message or not update.message.text:
            return
            
        message_text = update.message.text
        logger.info(f"📨 Получено сообщение: {message_text}")
        
        # Отправляем клавиатуру при любом сообщении
        keyboard = get_main_keyboard()
        
        if message_text == "📊 Статус":
            await show_status(update, context)
        elif message_text == "⚙️ Настройки":
            await show_settings(update, context)
        elif message_text == "▶️ Запуск":
            await start_arbitrage(update, context)
        elif message_text == "⏹️ Остановка":
            await stop_arbitrage(update, context)
        elif message_text == "🔄 Перезапуск":
            await restart_arbitrage(update, context)
        elif message_text == "📈 Статистика":
            await show_stats(update, context)
        else:
            # Приветственное сообщение для любого другого текста
            await show_welcome(update, context)
            
    except Exception as e:
        logger.error(f"Ошибка в handle_message: {e}")
        try:
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте еще раз.")
        except:
            pass

async def show_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать приветственное сообщение"""
    try:
        keyboard = get_main_keyboard()
        
        text = f"""
🔺 **ТРЕУГОЛЬНЫЙ АРБИТРАЖ НА MEXC**

Добро пожаловать в систему управления!

📊 **Текущие настройки:**
• Минимальная прибыль: {settings['min_profit']}%
• Максимальная позиция: ${settings['max_position']}
• Режим торговли: {settings['trading_mode']}
• Тестовая среда: {'✅' if settings['mexc_sandbox'] else '❌'}
• Статус бота: {'🟢 Работает' if settings['bot_running'] else '🔴 Остановлен'}

🔺 **Только треугольный арбитраж:**
• Поиск треугольных возможностей на MEXC
• Автоматическое исполнение прибыльных сделок
• Детальные уведомления о каждой сделке

💡 **Используйте кнопки внизу для управления**
        """
        
        await update.message.reply_text(
            text, 
            reply_markup=keyboard, 
            parse_mode='Markdown'
        )
        logger.info("✅ Приветственное сообщение отправлено")
        
    except Exception as e:
        logger.error(f"Ошибка в show_welcome: {e}")

async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статус системы"""
    try:
        keyboard = get_main_keyboard()
        status_icon = "🟢" if settings['bot_running'] else "🔴"
        status_text = "Работает" if settings['bot_running'] else "Остановлен"
        
        text = f"""
📊 **СТАТУС ТРЕУГОЛЬНОГО АРБИТРАЖА**

{status_icon} **Состояние:** {status_text}
⏰ **Последнее обновление:** {settings.get('last_update', 'Неизвестно')}

🔧 **Настройки:**
• Минимальная прибыль: {settings['min_profit']}%
• Максимальная позиция: ${settings['max_position']}
• Режим торговли: {settings['trading_mode']}
• Тестовая среда MEXC: {'✅' if settings['mexc_sandbox'] else '❌'}

📈 **Статистика:**
• Всего сделок: {settings['total_trades']}
• Успешных: {settings['successful_trades']}
• Общая прибыль: ${settings['total_profit']:.2f}

🔺 **Только треугольные возможности на MEXC**

💡 **Используйте кнопки внизу для управления**
        """
        
        await update.message.reply_text(
            text, 
            reply_markup=keyboard, 
            parse_mode='Markdown'
        )
        logger.info("✅ Статус отправлен")
        
    except Exception as e:
        logger.error(f"Ошибка в show_status: {e}")

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать настройки (упрощенная версия)"""
    try:
        keyboard = get_main_keyboard()
        
        text = f"""
⚙️ **НАСТРОЙКИ ТРЕУГОЛЬНОГО АРБИТРАЖА**

📊 **Текущие параметры:**
• 💰 Минимальная прибыль: {settings['min_profit']}%
• 💵 Максимальная позиция: ${settings['max_position']}
• 🎯 Режим торговли: {settings['trading_mode']}
• 🧪 Sandbox: {'✅' if settings['mexc_sandbox'] else '❌'}

🔺 **Система ищет только треугольные возможности**

💡 **Для изменения настроек используйте команды:**
/profit - изменить минимальную прибыль
/position - изменить размер позиции
/mode - переключить режим торговли

💡 **Кнопки управления всегда внизу экрана**
        """
        
        await update.message.reply_text(
            text, 
            reply_markup=keyboard, 
            parse_mode='Markdown'
        )
        logger.info("✅ Настройки отправлены")
        
    except Exception as e:
        logger.error(f"Ошибка в show_settings: {e}")

async def start_arbitrage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запуск треугольного арбитража"""
    try:
        keyboard = get_main_keyboard()
        settings['bot_running'] = True
        save_settings(settings)
        
        text = f"""
✅ **ТРЕУГОЛЬНЫЙ АРБИТРАЖ ЗАПУЩЕН!**

🔺 Система начала поиск треугольных возможностей на MEXC
📱 Уведомления о сделках будут приходить в этот чат
⚙️ Используйте кнопки для управления

📊 **Настройки:**
• Минимальная прибыль: {settings['min_profit']}%
• Максимальная позиция: ${settings['max_position']}
• Режим: {settings['trading_mode']}

💡 **Примечание:** В режиме '{settings['trading_mode']}'. Для реального запуска убедитесь что режим 'live'.
        """
        
        await update.message.reply_text(
            text, 
            reply_markup=keyboard, 
            parse_mode='Markdown'
        )
        logger.info("✅ Арбитраж запущен")
        
    except Exception as e:
        logger.error(f"Ошибка в start_arbitrage: {e}")

async def stop_arbitrage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Остановка треугольного арбитража"""
    try:
        keyboard = get_main_keyboard()
        settings['bot_running'] = False
        save_settings(settings)
        
        text = """
⏹️ **ТРЕУГОЛЬНЫЙ АРБИТРАЖ ОСТАНОВЛЕН!**

🛑 Поиск треугольных возможностей приостановлен
📊 Статистика сохранена
▶️ Используйте кнопку "Запуск" для возобновления

🔺 Система готова к повторному запуску
        """
        
        await update.message.reply_text(
            text, 
            reply_markup=keyboard, 
            parse_mode='Markdown'
        )
        logger.info("✅ Арбитраж остановлен")
        
    except Exception as e:
        logger.error(f"Ошибка в stop_arbitrage: {e}")

async def restart_arbitrage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапуск треугольного арбитража"""
    try:
        keyboard = get_main_keyboard()
        settings['bot_running'] = True
        save_settings(settings)
        
        text = f"""
🔄 **ТРЕУГОЛЬНЫЙ АРБИТРАЖ ПЕРЕЗАПУЩЕН!**

✅ Новые настройки применены
🚀 Система работает с обновленными параметрами
📊 Статистика продолжается

⚙️ **Текущие настройки:**
• Минимальная прибыль: {settings['min_profit']}%
• Максимальная позиция: ${settings['max_position']}
• Режим: {settings['trading_mode']}

💡 **Настройки автоматически сохранены**
        """
        
        await update.message.reply_text(
            text, 
            reply_markup=keyboard, 
            parse_mode='Markdown'
        )
        logger.info("✅ Арбитраж перезапущен")
        
    except Exception as e:
        logger.error(f"Ошибка в restart_arbitrage: {e}")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику"""
    try:
        keyboard = get_main_keyboard()
        
        uptime = "Система управления"
        if settings.get('last_update'):
            try:
                last_update = datetime.fromisoformat(settings['last_update'])
                uptime = str(datetime.now() - last_update)
            except:
                pass
        
        success_rate = 0
        if settings['total_trades'] > 0:
            success_rate = (settings['successful_trades'] / settings['total_trades']) * 100
        
        text = f"""
📈 **СТАТИСТИКА ТРЕУГОЛЬНОГО АРБИТРАЖА**

⏱️ **Время с последнего обновления:** {uptime}
🔄 **Статус:** {'🟢 Активен' if settings['bot_running'] else '🔴 Остановлен'}

📊 **Торговая статистика:**
• Всего сделок: {settings['total_trades']}
• Успешных: {settings['successful_trades']}
• Процент успеха: {success_rate:.1f}%
• Общая прибыль: ${settings['total_profit']:.2f}

⚙️ **Текущие настройки:**
• Минимальная прибыль: {settings['min_profit']}%
• Максимальная позиция: ${settings['max_position']}
• Режим торговли: {settings['trading_mode']}
• Тестовая среда: {'✅' if settings['mexc_sandbox'] else '❌'}

🔺 **Только треугольные возможности на MEXC**

💡 **Для реальной статистики запустите систему**
        """
        
        await update.message.reply_text(
            text, 
            reply_markup=keyboard, 
            parse_mode='Markdown'
        )
        logger.info("✅ Статистика отправлена")
        
    except Exception as e:
        logger.error(f"Ошибка в show_stats: {e}")

def main():
    """Главная функция"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не найден в .env")
        return
    
    # Создаем приложение с обработкой ошибок
    application = Application.builder().token(bot_token).build()
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота с обработкой конфликтов
    logger.info("🤖 Запуск исправленного Telegram бота управления...")
    print("🔺 ИСПРАВЛЕННЫЙ TELEGRAM БОТ УПРАВЛЕНИЯ")
    print("📱 Кнопки управления внизу экрана")
    print("💾 Настройки сохраняются в triangular_settings.json")
    print("🔺 Только треугольный арбитраж на MEXC")
    print("🔧 Устойчив к проблемам деплоя")
    
    try:
        application.run_polling(
            drop_pending_updates=True,  # Игнорируем старые обновления
            allowed_updates=Update.ALL_TYPES
        )
    except Conflict as e:
        logger.info(f"🔄 Конфликт с другим экземпляром: {e}")
        print("✅ Другой экземпляр бота уже работает на Railway")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")

if __name__ == "__main__":
    main()