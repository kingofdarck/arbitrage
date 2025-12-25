#!/usr/bin/env python3
"""
Простой Telegram бот управления треугольным арбитражем
Работает только через текстовые команды - без кнопок
"""

import asyncio
import logging
import json
import os
import time
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters, CommandHandler

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

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    text = f"""
🔺 **ТРЕУГОЛЬНЫЙ АРБИТРАЖ НА MEXC**

Добро пожаловать! Бот работает через команды.

📊 **Доступные команды:**
/status - статус системы
/start_trading - запустить арбитраж
/stop_trading - остановить арбитраж
/restart_trading - перезапустить арбитраж
/settings - показать настройки
/stats - статистика
/help - помощь

📋 **Текущие настройки:**
• Минимальная прибыль: {settings['min_profit']}%
• Максимальная позиция: ${settings['max_position']}
• Режим торговли: {settings['trading_mode']}
• Статус: {'🟢 Работает' if settings['bot_running'] else '🔴 Остановлен'}

💡 **Просто отправьте команду для управления системой**
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status"""
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
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def start_trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start_trading"""
    settings['bot_running'] = True
    save_settings(settings)
    
    text = f"""
✅ **ТРЕУГОЛЬНЫЙ АРБИТРАЖ ЗАПУЩЕН!**

🔺 Система начала поиск треугольных возможностей на MEXC
📱 Уведомления о сделках будут приходить в этот чат

📊 **Настройки:**
• Минимальная прибыль: {settings['min_profit']}%
• Максимальная позиция: ${settings['max_position']}
• Режим: {settings['trading_mode']}

💡 Используйте /stop_trading для остановки
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def stop_trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stop_trading"""
    settings['bot_running'] = False
    save_settings(settings)
    
    text = """
⏹️ **ТРЕУГОЛЬНЫЙ АРБИТРАЖ ОСТАНОВЛЕН!**

🛑 Поиск треугольных возможностей приостановлен
📊 Статистика сохранена

💡 Используйте /start_trading для возобновления
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def restart_trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /restart_trading"""
    settings['bot_running'] = True
    save_settings(settings)
    
    text = f"""
🔄 **ТРЕУГОЛЬНЫЙ АРБИТРАЖ ПЕРЕЗАПУЩЕН!**

✅ Система работает с обновленными параметрами

⚙️ **Текущие настройки:**
• Минимальная прибыль: {settings['min_profit']}%
• Максимальная позиция: ${settings['max_position']}
• Режим: {settings['trading_mode']}

💡 Настройки автоматически сохранены
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /settings"""
    text = f"""
⚙️ **НАСТРОЙКИ ТРЕУГОЛЬНОГО АРБИТРАЖА**

📊 **Текущие параметры:**
• 💰 Минимальная прибыль: {settings['min_profit']}%
• 💵 Максимальная позиция: ${settings['max_position']}
• 🎯 Режим торговли: {settings['trading_mode']}
• 🧪 Sandbox: {'✅' if settings['mexc_sandbox'] else '❌'}

🔧 **Команды для изменения:**
/set_profit 1.0 - установить прибыль 1.0%
/set_position 100 - установить позицию $100
/set_mode test - установить тестовый режим
/set_mode live - установить реальный режим

🔺 **Система ищет только треугольные возможности**
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats"""
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

🔺 **Только треугольные возможности на MEXC**
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    text = """
🆘 **ПОМОЩЬ - КОМАНДЫ УПРАВЛЕНИЯ**

🔺 **Основные команды:**
/start - приветствие и список команд
/status - текущий статус системы
/start_trading - запустить арбитраж
/stop_trading - остановить арбитраж
/restart_trading - перезапустить систему

📊 **Информация:**
/settings - показать настройки
/stats - статистика работы
/help - эта справка

⚙️ **Настройки:**
/set_profit [число] - установить минимальную прибыль (%)
/set_position [число] - установить размер позиции ($)
/set_mode [test/live] - установить режим торговли

📝 **Примеры:**
/set_profit 1.0
/set_position 100
/set_mode test

🔺 **Треугольный арбитраж на MEXC работает 24/7!**
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def set_profit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /set_profit"""
    try:
        if context.args and len(context.args) > 0:
            profit = float(context.args[0])
            if 0.1 <= profit <= 5.0:
                settings['min_profit'] = profit
                save_settings(settings)
                await update.message.reply_text(f"✅ Минимальная прибыль установлена: {profit}%")
            else:
                await update.message.reply_text("❌ Прибыль должна быть от 0.1% до 5.0%")
        else:
            await update.message.reply_text("💡 Использование: /set_profit 1.0")
    except ValueError:
        await update.message.reply_text("❌ Неверный формат числа. Пример: /set_profit 1.0")

async def set_position_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /set_position"""
    try:
        if context.args and len(context.args) > 0:
            position = float(context.args[0])
            if 10 <= position <= 1000:
                settings['max_position'] = position
                save_settings(settings)
                await update.message.reply_text(f"✅ Максимальная позиция установлена: ${position}")
            else:
                await update.message.reply_text("❌ Позиция должна быть от $10 до $1000")
        else:
            await update.message.reply_text("💡 Использование: /set_position 100")
    except ValueError:
        await update.message.reply_text("❌ Неверный формат числа. Пример: /set_position 100")

async def set_mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /set_mode"""
    if context.args and len(context.args) > 0:
        mode = context.args[0].lower()
        if mode in ['test', 'live']:
            settings['trading_mode'] = mode
            save_settings(settings)
            await update.message.reply_text(f"✅ Режим торговли установлен: {mode}")
        else:
            await update.message.reply_text("❌ Режим должен быть 'test' или 'live'")
    else:
        await update.message.reply_text("💡 Использование: /set_mode test или /set_mode live")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    text = update.message.text.lower()
    
    # Простые текстовые команды
    if 'статус' in text or 'status' in text:
        await status_command(update, context)
    elif 'запуск' in text or 'start' in text:
        await start_trading_command(update, context)
    elif 'остановка' in text or 'stop' in text:
        await stop_trading_command(update, context)
    elif 'перезапуск' in text or 'restart' in text:
        await restart_trading_command(update, context)
    elif 'настройки' in text or 'settings' in text:
        await settings_command(update, context)
    elif 'статистика' in text or 'stats' in text:
        await stats_command(update, context)
    elif 'помощь' in text or 'help' in text:
        await help_command(update, context)
    else:
        # Показываем помощь для неизвестных команд
        await update.message.reply_text(
            "❓ Неизвестная команда. Используйте /help для списка команд или /start для начала."
        )

def main():
    """Главная функция"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не найден в .env")
        return
    
    # Создаем приложение
    application = Application.builder().token(bot_token).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("start_trading", start_trading_command))
    application.add_handler(CommandHandler("stop_trading", stop_trading_command))
    application.add_handler(CommandHandler("restart_trading", restart_trading_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("set_profit", set_profit_command))
    application.add_handler(CommandHandler("set_position", set_position_command))
    application.add_handler(CommandHandler("set_mode", set_mode_command))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Запускаем бота
    logger.info("🤖 Запуск простого Telegram бота управления...")
    print("🔺 ПРОСТОЙ TELEGRAM БОТ УПРАВЛЕНИЯ")
    print("📱 Работает только через команды")
    print("💾 Настройки сохраняются в triangular_settings.json")
    print("🔺 Только треугольный арбитраж на MEXC")
    print("🚫 БЕЗ КНОПОК - только команды!")
    
    try:
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")

if __name__ == "__main__":
    main()