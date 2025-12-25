#!/usr/bin/env python3
"""
Рабочий Telegram бот с кнопками для MEXC треугольного арбитража
Арбитраж выключен по умолчанию
"""

import asyncio
import logging
import json
import os
import time
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, ContextTypes, filters, CommandHandler
from telegram.error import NetworkError, TimedOut

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
    'bot_running': False,  # По умолчанию ВЫКЛЮЧЕН
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
    return ReplyKeyboardMarkup(
        keyboard, 
        resize_keyboard=True, 
        is_persistent=True,
        one_time_keyboard=False
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.error(f"Exception while handling an update: {context.error}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    try:
        keyboard = get_main_keyboard()
        
        text = f"""
🔺 **ТРЕУГОЛЬНЫЙ АРБИТРАЖ НА MEXC**

Добро пожаловать в систему управления!

📊 **Текущие настройки:**
• Минимальная прибыль: {settings['min_profit']}%
• Максимальная позиция: ${settings['max_position']}
• Режим торговли: {settings['trading_mode']}
• Статус бота: {'🟢 Работает' if settings['bot_running'] else '🔴 Остановлен'}

🔺 **Только треугольный арбитраж:**
• Поиск треугольных возможностей на MEXC
• Автоматическое исполнение прибыльных сделок
• Детальные уведомления о каждой сделке

💡 **Используйте кнопки внизу для управления**

⚠️ **Арбитраж по умолчанию ВЫКЛЮЧЕН**
Нажмите "▶️ Запуск" для начала работы
        """
        
        await update.message.reply_text(
            text, 
            reply_markup=keyboard, 
            parse_mode='Markdown'
        )
        logger.info("✅ Команда /start выполнена")
        
    except Exception as e:
        logger.error(f"Ошибка в start_command: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех сообщений"""
    try:
        if not update.message or not update.message.text:
            return
            
        message_text = update.message.text
        logger.info(f"📨 Получено сообщение: {message_text}")
        
        # Всегда отправляем клавиатуру
        keyboard = get_main_keyboard()
        
        if message_text == "📊 Статус":
            await show_status(update, context, keyboard)
        elif message_text == "⚙️ Настройки":
            await show_settings(update, context, keyboard)
        elif message_text == "▶️ Запуск":
            await start_arbitrage(update, context, keyboard)
        elif message_text == "⏹️ Остановка":
            await stop_arbitrage(update, context, keyboard)
        elif message_text == "🔄 Перезапуск":
            await restart_arbitrage(update, context, keyboard)
        elif message_text == "📈 Статистика":
            await show_stats(update, context, keyboard)
        else:
            # Для любого другого текста показываем помощь
            await show_help(update, context, keyboard)
            
    except Exception as e:
        logger.error(f"Ошибка в handle_message: {e}")
        try:
            keyboard = get_main_keyboard()
            await update.message.reply_text(
                "❌ Произошла ошибка. Попробуйте еще раз.",
                reply_markup=keyboard
            )
        except:
            pass

async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE, keyboard):
    """Показать статус системы"""
    try:
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

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE, keyboard):
    """Показать настройки"""
    try:
        text = f"""
⚙️ **НАСТРОЙКИ ТРЕУГОЛЬНОГО АРБИТРАЖА**

📊 **Текущие параметры:**
• 💰 Минимальная прибыль: {settings['min_profit']}%
• 💵 Максимальная позиция: ${settings['max_position']}
• 🎯 Режим торговли: {settings['trading_mode']}
• 🧪 Sandbox: {'✅' if settings['mexc_sandbox'] else '❌'}

🔺 **Система ищет только треугольные возможности на MEXC**

🔧 **Для изменения настроек используйте команды:**
/profit 1.0 - установить прибыль 1.0%
/position 100 - установить позицию $100
/mode test - тестовый режим
/mode live - реальный режим

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

async def start_arbitrage(update: Update, context: ContextTypes.DEFAULT_TYPE, keyboard):
    """Запуск треугольного арбитража"""
    try:
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

💡 **Примечание:** В режиме '{settings['trading_mode']}'. 
Для реального запуска убедитесь что режим 'live'.

🔺 **Поиск среди 3361 торговой пары MEXC**
        """
        
        await update.message.reply_text(
            text, 
            reply_markup=keyboard, 
            parse_mode='Markdown'
        )
        logger.info("✅ Арбитраж запущен")
        
    except Exception as e:
        logger.error(f"Ошибка в start_arbitrage: {e}")

async def stop_arbitrage(update: Update, context: ContextTypes.DEFAULT_TYPE, keyboard):
    """Остановка треугольного арбитража"""
    try:
        settings['bot_running'] = False
        save_settings(settings)
        
        text = """
⏹️ **ТРЕУГОЛЬНЫЙ АРБИТРАЖ ОСТАНОВЛЕН!**

🛑 Поиск треугольных возможностей приостановлен
📊 Статистика сохранена
▶️ Используйте кнопку "▶️ Запуск" для возобновления

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

async def restart_arbitrage(update: Update, context: ContextTypes.DEFAULT_TYPE, keyboard):
    """Перезапуск треугольного арбитража"""
    try:
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
🔺 **Поиск на MEXC возобновлен**
        """
        
        await update.message.reply_text(
            text, 
            reply_markup=keyboard, 
            parse_mode='Markdown'
        )
        logger.info("✅ Арбитраж перезапущен")
        
    except Exception as e:
        logger.error(f"Ошибка в restart_arbitrage: {e}")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, keyboard):
    """Показать статистику"""
    try:
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

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE, keyboard):
    """Показать помощь"""
    try:
        text = """
🆘 **ПОМОЩЬ - УПРАВЛЕНИЕ СИСТЕМОЙ**

🔺 **Кнопки управления:**
📊 **Статус** - текущее состояние системы
⚙️ **Настройки** - параметры торговли
▶️ **Запуск** - запустить арбитраж на MEXC
⏹️ **Остановка** - остановить арбитраж
🔄 **Перезапуск** - перезапустить с новыми настройками
📈 **Статистика** - детальная статистика

⚙️ **Команды настроек:**
/profit [число] - установить минимальную прибыль (%)
/position [число] - установить размер позиции ($)
/mode [test/live] - установить режим торговли

📝 **Примеры:**
/profit 1.0
/position 100
/mode live

🔺 **Треугольный арбитраж на MEXC работает 24/7!**

⚠️ **По умолчанию арбитраж ВЫКЛЮЧЕН**
Нажмите "▶️ Запуск" для начала работы
        """
        
        await update.message.reply_text(
            text, 
            reply_markup=keyboard, 
            parse_mode='Markdown'
        )
        logger.info("✅ Помощь отправлена")
        
    except Exception as e:
        logger.error(f"Ошибка в show_help: {e}")

# Команды настроек
async def set_profit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /profit"""
    try:
        keyboard = get_main_keyboard()
        if context.args and len(context.args) > 0:
            profit = float(context.args[0])
            if 0.1 <= profit <= 5.0:
                settings['min_profit'] = profit
                save_settings(settings)
                await update.message.reply_text(
                    f"✅ Минимальная прибыль установлена: {profit}%",
                    reply_markup=keyboard
                )
            else:
                await update.message.reply_text(
                    "❌ Прибыль должна быть от 0.1% до 5.0%",
                    reply_markup=keyboard
                )
        else:
            await update.message.reply_text(
                "💡 Использование: /profit 1.0",
                reply_markup=keyboard
            )
    except ValueError:
        keyboard = get_main_keyboard()
        await update.message.reply_text(
            "❌ Неверный формат числа. Пример: /profit 1.0",
            reply_markup=keyboard
        )

async def set_position_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /position"""
    try:
        keyboard = get_main_keyboard()
        if context.args and len(context.args) > 0:
            position = float(context.args[0])
            if 10 <= position <= 1000:
                settings['max_position'] = position
                save_settings(settings)
                await update.message.reply_text(
                    f"✅ Максимальная позиция установлена: ${position}",
                    reply_markup=keyboard
                )
            else:
                await update.message.reply_text(
                    "❌ Позиция должна быть от $10 до $1000",
                    reply_markup=keyboard
                )
        else:
            await update.message.reply_text(
                "💡 Использование: /position 100",
                reply_markup=keyboard
            )
    except ValueError:
        keyboard = get_main_keyboard()
        await update.message.reply_text(
            "❌ Неверный формат числа. Пример: /position 100",
            reply_markup=keyboard
        )

async def set_mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /mode"""
    keyboard = get_main_keyboard()
    if context.args and len(context.args) > 0:
        mode = context.args[0].lower()
        if mode in ['test', 'live']:
            settings['trading_mode'] = mode
            save_settings(settings)
            await update.message.reply_text(
                f"✅ Режим торговли установлен: {mode}",
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                "❌ Режим должен быть 'test' или 'live'",
                reply_markup=keyboard
            )
    else:
        await update.message.reply_text(
            "💡 Использование: /mode test или /mode live",
            reply_markup=keyboard
        )

def main():
    """Главная функция"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не найден в .env")
        return
    
    # Создаем приложение
    application = Application.builder().token(bot_token).build()
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("profit", set_profit_command))
    application.add_handler(CommandHandler("position", set_position_command))
    application.add_handler(CommandHandler("mode", set_mode_command))
    
    # Обработчик текстовых сообщений (кнопки)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    logger.info("🤖 Запуск рабочего Telegram бота с кнопками...")
    print("🔺 РАБОЧИЙ TELEGRAM БОТ С КНОПКАМИ")
    print("📱 Кнопки управления внизу экрана")
    print("💾 Настройки сохраняются в triangular_settings.json")
    print("🔺 Треугольный арбитраж на MEXC")
    print("⚠️ Арбитраж по умолчанию ВЫКЛЮЧЕН")
    
    try:
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            timeout=30,
            pool_timeout=30
        )
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")

if __name__ == "__main__":
    main()