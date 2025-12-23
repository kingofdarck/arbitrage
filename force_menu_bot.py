#!/usr/bin/env python3
"""
Принудительный бот с меню - отправляет меню на любое сообщение
"""

import asyncio
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from config import NOTIFICATION_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройки
settings = {
    'min_profit': 0.75,
    'check_interval': 5,
    'cross_exchange_enabled': True,
    'triangular_enabled': True,
    'max_notifications': 25,
    'confidence_threshold': 0.1,
    'monitor_running': False
}

async def any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет меню на любое сообщение"""
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

Система управления арбитражным мониторингом

📊 **Текущие настройки:**
• Минимальная прибыль: {settings['min_profit']}%
• Интервал проверки: {settings['check_interval']} сек
• Межбиржевой арбитраж: {'✅' if settings['cross_exchange_enabled'] else '❌'}
• Треугольный арбитраж: {'✅' if settings['triangular_enabled'] else '❌'}
• Статус: {'🟢 Работает' if settings['monitor_running'] else '🔴 Остановлен'}

Выберите действие:
    """
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "status":
        text = f"""
📊 **СТАТУС СИСТЕМЫ**

{'🟢' if settings['monitor_running'] else '🔴'} **Состояние:** {'Работает' if settings['monitor_running'] else 'Остановлен'}

🔧 **Настройки:**
• Минимальная прибыль: {settings['min_profit']}%
• Интервал проверки: {settings['check_interval']} сек
• Межбиржевой арбитраж: {'✅' if settings['cross_exchange_enabled'] else '❌'}
• Треугольный арбитраж: {'✅' if settings['triangular_enabled'] else '❌'}
• Макс. уведомлений: {settings['max_notifications']}
• Порог уверенности: {settings['confidence_threshold']}

💡 Отправьте любое сообщение для возврата в главное меню
        """
        await query.edit_message_text(text, parse_mode='Markdown')
        
    elif query.data == "settings":
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

💡 Отправьте любое сообщение для возврата в главное меню
        """
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
    elif query.data == "start_monitor":
        settings['monitor_running'] = True
        await query.edit_message_text("✅ **Монитор запущен!**\n\n💡 Отправьте любое сообщение для главного меню", parse_mode='Markdown')
        
    elif query.data == "stop_monitor":
        settings['monitor_running'] = False
        await query.edit_message_text("⏹️ **Монитор остановлен!**\n\n💡 Отправьте любое сообщение для главного меню", parse_mode='Markdown')
        
    elif query.data == "restart_monitor":
        await query.edit_message_text("🔄 **Система перезапущена!**\n\nНовые настройки применены.\n\n💡 Отправьте любое сообщение для главного меню", parse_mode='Markdown')
        
    elif query.data == "stats":
        text = """
📈 **СТАТИСТИКА РАБОТЫ**

⏱️ **Время работы:** Демо-режим
🔄 **Циклов выполнено:** 0
🎯 **Всего возможностей:** 0
📱 **Уведомлений отправлено:** 0

💡 **Для реальной статистики запустите combined_monitor.py**

💡 Отправьте любое сообщение для главного меню
        """
        await query.edit_message_text(text, parse_mode='Markdown')
        
    elif query.data.startswith("set_"):
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
        
        # Возвращаемся в настройки
        await button_handler(update, context)  # Рекурсивно вызываем с settings
        
    elif query.data == "toggle_cross":
        settings['cross_exchange_enabled'] = not settings['cross_exchange_enabled']
        # Имитируем нажатие кнопки настроек
        query.data = "settings"
        await button_handler(update, context)
        
    elif query.data == "toggle_triangular":
        settings['triangular_enabled'] = not settings['triangular_enabled']
        # Имитируем нажатие кнопки настроек
        query.data = "settings"
        await button_handler(update, context)

def main():
    """Главная функция"""
    bot_token = NOTIFICATION_CONFIG['telegram']['bot_token']
    
    application = Application.builder().token(bot_token).build()
    
    # Обрабатываем ВСЕ текстовые сообщения
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, any_message))
    application.add_handler(MessageHandler(filters.COMMAND, any_message))  # И команды тоже
    application.add_handler(CallbackQueryHandler(button_handler))
    
    logger.info("🤖 Запуск принудительного бота с меню...")
    print("🤖 Принудительный бот запущен!")
    print("📱 Отправьте ЛЮБОЕ сообщение боту для получения меню")
    application.run_polling()

if __name__ == "__main__":
    main()