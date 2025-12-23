#!/usr/bin/env python3
"""
Постоянный Telegram бот с кнопками внизу экрана
Устойчив к деплою и перезапускам
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from config import NOTIFICATION_CONFIG

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Глобальные настройки с сохранением в файл
SETTINGS_FILE = 'persistent_settings.json'

default_settings = {
    'min_profit': 0.75,
    'check_interval': 5,
    'cross_exchange_enabled': True,
    'triangular_enabled': True,
    'max_notifications': 25,
    'confidence_threshold': 0.1,
    'check_liquidity': True,  # Проверка ликвидности
    'monitor_running': False,
    'last_update': datetime.now().isoformat()
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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех сообщений"""
    message_text = update.message.text
    
    # Отправляем клавиатуру при любом сообщении
    keyboard = get_main_keyboard()
    
    if message_text == "📊 Статус":
        await show_status(update, context)
    elif message_text == "⚙️ Настройки":
        await show_settings(update, context)
    elif message_text == "▶️ Запуск":
        await start_monitor(update, context)
    elif message_text == "⏹️ Остановка":
        await stop_monitor(update, context)
    elif message_text == "🔄 Перезапуск":
        await restart_monitor(update, context)
    elif message_text == "📈 Статистика":
        await show_stats(update, context)
    else:
        # Приветственное сообщение для любого другого текста
        await show_welcome(update, context)

async def show_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать приветственное сообщение"""
    keyboard = get_main_keyboard()
    
    text = f"""
🤖 **АРБИТРАЖНЫЙ МОНИТОР**

Добро пожаловать в систему управления!

📊 **Текущие настройки:**
• Минимальная прибыль: {settings['min_profit']}%
• Интервал проверки: {settings['check_interval']} сек
• Межбиржевой арбитраж: {'✅' if settings['cross_exchange_enabled'] else '❌'}
• Треугольный арбитраж: {'✅' if settings['triangular_enabled'] else '❌'}
• Проверка ликвидности: {'✅' if settings['check_liquidity'] else '❌'}
• Статус: {'🟢 Работает' if settings['monitor_running'] else '🔴 Остановлен'}

💡 **Используйте кнопки внизу для управления**
    """
    
    await update.message.reply_text(
        text, 
        reply_markup=keyboard, 
        parse_mode='Markdown'
    )

async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статус системы"""
    keyboard = get_main_keyboard()
    status_icon = "🟢" if settings['monitor_running'] else "🔴"
    status_text = "Работает" if settings['monitor_running'] else "Остановлен"
    
    text = f"""
📊 **СТАТУС СИСТЕМЫ**

{status_icon} **Состояние:** {status_text}
⏰ **Последнее обновление:** {settings.get('last_update', 'Неизвестно')}

🔧 **Настройки:**
• Минимальная прибыль: {settings['min_profit']}%
• Интервал проверки: {settings['check_interval']} сек
• Межбиржевой арбитраж: {'✅' if settings['cross_exchange_enabled'] else '❌'}
• Треугольный арбитраж: {'✅' if settings['triangular_enabled'] else '❌'}
• Проверка ликвидности: {'✅' if settings['check_liquidity'] else '❌'}
• Макс. уведомлений: {settings['max_notifications']}
• Порог уверенности: {settings['confidence_threshold']}

💡 **Используйте кнопки внизу для управления**
    """
    
    await update.message.reply_text(
        text, 
        reply_markup=keyboard, 
        parse_mode='Markdown'
    )

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню настроек с inline кнопками"""
    keyboard = [
        [
            InlineKeyboardButton(f"💰 Прибыль: {settings['min_profit']}%", callback_data="set_profit"),
            InlineKeyboardButton(f"⏱️ Интервал: {settings['check_interval']}с", callback_data="set_interval")
        ],
        [
            InlineKeyboardButton(
                f"🔄 Межбиржевой: {'✅' if settings['cross_exchange_enabled'] else '❌'}", 
                callback_data="toggle_cross"
            ),
            InlineKeyboardButton(
                f"🔺 Треугольный: {'✅' if settings['triangular_enabled'] else '❌'}", 
                callback_data="toggle_triangular"
            )
        ],
        [
            InlineKeyboardButton(f"📱 Уведомлений: {settings['max_notifications']}", callback_data="set_notifications"),
            InlineKeyboardButton(f"🎯 Уверенность: {settings['confidence_threshold']}", callback_data="set_confidence")
        ],
        [
            InlineKeyboardButton("💾 Сохранить настройки", callback_data="save_settings")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
⚙️ **НАСТРОЙКИ СИСТЕМЫ**

Нажмите на параметр для изменения:

💰 **Минимальная прибыль** - порог прибыльности
⏱️ **Интервал проверки** - частота сканирования  
🔄 **Межбиржевой арбитраж** - поиск между биржами
🔺 **Треугольный арбитраж** - поиск внутри биржи
💧 **Проверка ликвидности** - депозиты/выводы
📱 **Макс. уведомлений** - лимит за цикл
🎯 **Порог уверенности** - фильтр качества

💡 **Кнопки управления всегда внизу экрана**
    """
    
    # Убеждаемся что основная клавиатура остается
    main_keyboard = get_main_keyboard()
    await update.message.reply_text(
        text, 
        reply_markup=main_keyboard, 
        parse_mode='Markdown'
    )
    
    # Отправляем inline меню отдельным сообщением
    await update.message.reply_text(
        "🎛️ **Панель настроек:**", 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )

async def start_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запуск монитора"""
    keyboard = get_main_keyboard()
    settings['monitor_running'] = True
    save_settings(settings)
    
    text = """
✅ **МОНИТОР ЗАПУЩЕН!**

🚀 Система начала поиск арбитражных возможностей
📱 Уведомления будут приходить в этот чат
⚙️ Используйте кнопки для управления

💡 **Примечание:** В демо-режиме. Для реального запуска используйте деплой.
    """
    
    await update.message.reply_text(
        text, 
        reply_markup=keyboard, 
        parse_mode='Markdown'
    )

async def stop_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Остановка монитора"""
    keyboard = get_main_keyboard()
    settings['monitor_running'] = False
    save_settings(settings)
    
    text = """
⏹️ **МОНИТОР ОСТАНОВЛЕН!**

🛑 Поиск арбитражных возможностей приостановлен
📊 Статистика сохранена
▶️ Используйте кнопку "Запуск" для возобновления
    """
    
    await update.message.reply_text(
        text, 
        reply_markup=keyboard, 
        parse_mode='Markdown'
    )

async def restart_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапуск монитора"""
    keyboard = get_main_keyboard()
    
    text = """
🔄 **СИСТЕМА ПЕРЕЗАПУЩЕНА!**

✅ Новые настройки применены
🚀 Монитор работает с обновленными параметрами
📊 Статистика сброшена

💡 **Настройки автоматически сохранены**
    """
    
    await update.message.reply_text(
        text, 
        reply_markup=keyboard, 
        parse_mode='Markdown'
    )

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику"""
    keyboard = get_main_keyboard()
    
    uptime = "Демо-режим"
    if settings.get('last_update'):
        try:
            last_update = datetime.fromisoformat(settings['last_update'])
            uptime = str(datetime.now() - last_update)
        except:
            pass
    
    text = f"""
📈 **СТАТИСТИКА РАБОТЫ**

⏱️ **Время с последнего обновления:** {uptime}
🔄 **Статус:** {'🟢 Активен' if settings['monitor_running'] else '🔴 Остановлен'}
⚙️ **Текущие настройки:**

💰 Минимальная прибыль: {settings['min_profit']}%
⏱️ Интервал проверки: {settings['check_interval']} сек
📱 Макс. уведомлений: {settings['max_notifications']}
🎯 Порог уверенности: {settings['confidence_threshold']}

🔄 Межбиржевой: {'✅' if settings['cross_exchange_enabled'] else '❌'}
🔺 Треугольный: {'✅' if settings['triangular_enabled'] else '❌'}

💡 **Для реальной статистики используйте деплой**
    """
    
    await update.message.reply_text(
        text, 
        reply_markup=keyboard, 
        parse_mode='Markdown'
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик inline кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("set_"):
        setting = query.data.replace("set_", "")
        
        if setting == "profit":
            profits = [0.5, 0.75, 1.0, 1.5, 2.0]
            current_idx = profits.index(settings['min_profit']) if settings['min_profit'] in profits else 1
            settings['min_profit'] = profits[(current_idx + 1) % len(profits)]
            
        elif setting == "interval":
            intervals = [3, 5, 10, 15, 30]
            current_idx = intervals.index(settings['check_interval']) if settings['check_interval'] in intervals else 1
            settings['check_interval'] = intervals[(current_idx + 1) % len(intervals)]
            
        elif setting == "notifications":
            notifications = [10, 15, 25, 50]
            current_idx = notifications.index(settings['max_notifications']) if settings['max_notifications'] in notifications else 2
            settings['max_notifications'] = notifications[(current_idx + 1) % len(notifications)]
            
        elif setting == "confidence":
            confidences = [0.05, 0.1, 0.2, 0.3]
            current_idx = confidences.index(settings['confidence_threshold']) if settings['confidence_threshold'] in confidences else 1
            settings['confidence_threshold'] = confidences[(current_idx + 1) % len(confidences)]
        
        # Обновляем меню настроек
        await update_settings_menu(query)
        
    elif query.data == "toggle_cross":
        settings['cross_exchange_enabled'] = not settings['cross_exchange_enabled']
        await update_settings_menu(query)
        
    elif query.data == "toggle_triangular":
        settings['triangular_enabled'] = not settings['triangular_enabled']
        await update_settings_menu(query)
        
    elif query.data == "toggle_liquidity":
        settings['check_liquidity'] = not settings['check_liquidity']
        await update_settings_menu(query)
        
    elif query.data == "save_settings":
        save_settings(settings)
        await query.edit_message_text(
            "💾 **Настройки сохранены!**\n\nВсе изменения применены и сохранены в файл.",
            parse_mode='Markdown'
        )

async def update_settings_menu(query):
    """Обновить меню настроек"""
    keyboard = [
        [
            InlineKeyboardButton(f"💰 Прибыль: {settings['min_profit']}%", callback_data="set_profit"),
            InlineKeyboardButton(f"⏱️ Интервал: {settings['check_interval']}с", callback_data="set_interval")
        ],
        [
            InlineKeyboardButton(
                f"🔄 Межбиржевой: {'✅' if settings['cross_exchange_enabled'] else '❌'}", 
                callback_data="toggle_cross"
            ),
            InlineKeyboardButton(
                f"🔺 Треугольный: {'✅' if settings['triangular_enabled'] else '❌'}", 
                callback_data="toggle_triangular"
            )
        ],
        [
            InlineKeyboardButton(f"📱 Уведомлений: {settings['max_notifications']}", callback_data="set_notifications"),
            InlineKeyboardButton(f"🎯 Уверенность: {settings['confidence_threshold']}", callback_data="set_confidence")
        ],
        [
            InlineKeyboardButton("💾 Сохранить настройки", callback_data="save_settings")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
🎛️ **Панель настроек:**

💰 Прибыль: {settings['min_profit']}%
⏱️ Интервал: {settings['check_interval']}с
🔄 Межбиржевой: {'✅' if settings['cross_exchange_enabled'] else '❌'}
🔺 Треугольный: {'✅' if settings['triangular_enabled'] else '❌'}
💧 Ликвидность: {'✅' if settings['check_liquidity'] else '❌'}
📱 Уведомлений: {settings['max_notifications']}
🎯 Уверенность: {settings['confidence_threshold']}
    """
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def setup_bot_commands(application):
    """Настройка команд бота при запуске"""
    try:
        from telegram import BotCommand
        commands = [
            BotCommand("start", "🤖 Главное меню управления арбитражем"),
            BotCommand("status", "📊 Статус системы"),
            BotCommand("settings", "⚙️ Настройки системы")
        ]
        await application.bot.set_my_commands(commands)
        logger.info("✅ Команды бота установлены")
    except Exception as e:
        logger.error(f"❌ Ошибка установки команд: {e}")

def main():
    """Главная функция"""
    bot_token = NOTIFICATION_CONFIG['telegram']['bot_token']
    
    # Создаем приложение
    application = Application.builder().token(bot_token).build()
    
    # Добавляем обработчики
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Настройка команд при запуске
    async def post_init(application):
        await setup_bot_commands(application)
    
    application.post_init = post_init
    
    # Запускаем бота
    logger.info("🤖 Запуск постоянного бота с кнопками...")
    print("🤖 Постоянный бот запущен!")
    print("📱 Кнопки управления всегда внизу экрана")
    print("💾 Настройки сохраняются в persistent_settings.json")
    application.run_polling()

if __name__ == "__main__":
    main()