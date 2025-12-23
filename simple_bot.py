#!/usr/bin/env python3
"""
Простой Telegram бот для управления арбитражным монитором
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from config import NOTIFICATION_CONFIG

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Глобальные настройки
settings = {
    'min_profit': 0.75,
    'check_interval': 5,
    'cross_exchange_enabled': True,
    'triangular_enabled': True,
    'max_notifications': 25,
    'confidence_threshold': 0.1,
    'opportunity_expiry': 1,
    'monitor_running': False
}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - показывает главное меню"""
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
    
    welcome_text = f"""
🤖 **АРБИТРАЖНЫЙ МОНИТОР**

Добро пожаловать в систему управления!

📊 **Текущие настройки:**
• Минимальная прибыль: {settings['min_profit']}%
• Интервал проверки: {settings['check_interval']} сек
• Межбиржевой арбитраж: {'✅' if settings['cross_exchange_enabled'] else '❌'}
• Треугольный арбитраж: {'✅' if settings['triangular_enabled'] else '❌'}

Выберите действие:
    """
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "status":
        await show_status(query)
    elif query.data == "settings":
        await show_settings(query)
    elif query.data == "start_monitor":
        await start_monitor(query)
    elif query.data == "stop_monitor":
        await stop_monitor(query)
    elif query.data == "restart_monitor":
        await restart_monitor(query)
    elif query.data == "stats":
        await show_stats(query)
    elif query.data.startswith("set_"):
        await handle_setting(query)
    elif query.data == "toggle_cross":
        settings['cross_exchange_enabled'] = not settings['cross_exchange_enabled']
        await show_settings(query)
    elif query.data == "toggle_triangular":
        settings['triangular_enabled'] = not settings['triangular_enabled']
        await show_settings(query)
    elif query.data == "save_settings":
        await save_settings(query)
    elif query.data == "back_main":
        await show_main_menu(query)

async def show_status(query):
    """Показать статус системы"""
    status_icon = "🟢" if settings['monitor_running'] else "🔴"
    status_text = "Работает" if settings['monitor_running'] else "Остановлен"
    
    text = f"""
📊 **СТАТУС СИСТЕМЫ**

{status_icon} **Состояние:** {status_text}

🔧 **Настройки:**
• Минимальная прибыль: {settings['min_profit']}%
• Интервал проверки: {settings['check_interval']} сек
• Межбиржевой арбитраж: {'✅' if settings['cross_exchange_enabled'] else '❌'}
• Треугольный арбитраж: {'✅' if settings['triangular_enabled'] else '❌'}
• Макс. уведомлений: {settings['max_notifications']}
• Порог уверенности: {settings['confidence_threshold']}
    """
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_settings(query):
    """Показать меню настроек"""
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
            InlineKeyboardButton("💾 Сохранить", callback_data="save_settings"),
            InlineKeyboardButton("🔙 Назад", callback_data="back_main")
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
📱 **Макс. уведомлений** - лимит за цикл
🎯 **Порог уверенности** - фильтр качества
    """
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_setting(query):
    """Обработка изменения настроек"""
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
    
    await show_settings(query)

async def start_monitor(query):
    """Запуск монитора"""
    settings['monitor_running'] = True
    await query.edit_message_text("✅ **Монитор запущен!**\n\n(Примечание: это демо-режим. Для реального запуска используйте combined_monitor.py)", parse_mode='Markdown')

async def stop_monitor(query):
    """Остановка монитора"""
    settings['monitor_running'] = False
    await query.edit_message_text("⏹️ **Монитор остановлен!**", parse_mode='Markdown')

async def restart_monitor(query):
    """Перезапуск монитора"""
    await query.edit_message_text("🔄 **Система перезапущена!**\n\nНовые настройки применены.", parse_mode='Markdown')

async def show_stats(query):
    """Показать статистику"""
    text = """
📈 **СТАТИСТИКА РАБОТЫ**

⏱️ **Время работы:** Демо-режим
🔄 **Циклов выполнено:** 0
🎯 **Всего возможностей:** 0
📱 **Уведомлений отправлено:** 0

💡 **Для реальной статистики запустите combined_monitor.py**
    """
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_main_menu(query):
    """Показать главное меню"""
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
    
    text = f"""
🤖 **АРБИТРАЖНЫЙ МОНИТОР**

📊 **Текущие настройки:**
• Минимальная прибыль: {settings['min_profit']}%
• Интервал проверки: {settings['check_interval']} сек
• Межбиржевой арбитраж: {'✅' if settings['cross_exchange_enabled'] else '❌'}
• Треугольный арбитраж: {'✅' if settings['triangular_enabled'] else '❌'}

Выберите действие:
    """
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def save_settings(query):
    """Сохранить настройки"""
    try:
        with open('bot_settings.json', 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        
        await query.edit_message_text(
            "💾 **Настройки сохранены!**\n\nИзменения применены.",
            parse_mode='Markdown'
        )
    except Exception as e:
        await query.edit_message_text(f"❌ **Ошибка сохранения:**\n{str(e)}", parse_mode='Markdown')

def main():
    """Главная функция"""
    bot_token = NOTIFICATION_CONFIG['telegram']['bot_token']
    
    # Создаем приложение
    application = Application.builder().token(bot_token).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Устанавливаем команды бота при запуске
    async def post_init(application):
        """Инициализация после запуска"""
        try:
            from telegram import BotCommand
            commands = [
                BotCommand("start", "🤖 Главное меню управления арбитражем")
            ]
            await application.bot.set_my_commands(commands)
            logger.info("✅ Команды бота установлены")
        except Exception as e:
            logger.error(f"❌ Ошибка установки команд: {e}")
    
    application.post_init = post_init
    
    # Запускаем бота
    logger.info("🤖 Запуск простого Telegram бота...")
    print("🤖 Бот запущен! Отправьте /start в Telegram")
    application.run_polling()

if __name__ == "__main__":
    main()