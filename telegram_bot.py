#!/usr/bin/env python3
"""
Telegram бот для управления арбитражным монитором
Меню управления, настройки, перезапуск
"""

import asyncio
import logging
import json
import os
import signal
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from config import NOTIFICATION_CONFIG, MONITORING_CONFIG, ARBITRAGE_CONFIG
from smart_arbitrage_monitor import SmartArbitrageMonitor

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ArbitrageBot:
    def __init__(self):
        self.monitor: Optional[SmartArbitrageMonitor] = None
        self.monitor_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Настройки по умолчанию
        self.settings = {
            'min_profit': 0.75,
            'check_interval': 5,
            'cross_exchange_enabled': True,
            'triangular_enabled': True,
            'max_notifications': 25,
            'confidence_threshold': 0.1,
            'opportunity_expiry': 1
        }
        
        # Загружаем сохраненные настройки
        self.load_settings()
        
        # Токен бота
        self.bot_token = NOTIFICATION_CONFIG['telegram']['bot_token']
        self.chat_id = NOTIFICATION_CONFIG['telegram']['chat_id']
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        welcome_text = """
🤖 **АРБИТРАЖНЫЙ МОНИТОР**

Добро пожаловать в систему управления арбитражным мониторингом!

📊 **Текущие настройки:**
• Минимальная прибыль: {min_profit}%
• Интервал проверки: {check_interval} сек
• Межбиржевой арбитраж: {'✅' if self.settings['cross_exchange_enabled'] else '❌'}
• Треугольный арбитраж: {'✅' if self.settings['triangular_enabled'] else '❌'}

Выберите действие:
        """.format(**self.settings)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий кнопок"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "status":
            await self.show_status(query)
        elif query.data == "settings":
            await self.show_settings(query)
        elif query.data == "start_monitor":
            await self.start_monitor(query)
        elif query.data == "stop_monitor":
            await self.stop_monitor(query)
        elif query.data == "restart_monitor":
            await self.restart_monitor(query)
        elif query.data == "stats":
            await self.show_stats(query)
        elif query.data.startswith("set_"):
            await self.handle_setting(query)
        elif query.data == "toggle_cross":
            self.settings['cross_exchange_enabled'] = not self.settings['cross_exchange_enabled']
            await self.show_settings(query)
        elif query.data == "toggle_triangular":
            self.settings['triangular_enabled'] = not self.settings['triangular_enabled']
            await self.show_settings(query)
        elif query.data == "save_settings":
            await self.save_settings(query)
        elif query.data == "back_main":
            await self.show_main_menu(query)

    async def show_status(self, query):
        """Показать статус системы"""
        status_icon = "🟢" if self.is_running else "🔴"
        status_text = "Работает" if self.is_running else "Остановлен"
        
        uptime = ""
        if self.monitor and hasattr(self.monitor, 'stats'):
            start_time = self.monitor.stats.get('start_time')
            if start_time:
                uptime = str(datetime.now() - start_time)
        
        text = f"""
📊 **СТАТУС СИСТЕМЫ**

{status_icon} **Состояние:** {status_text}
⏱️ **Время работы:** {uptime}

🔧 **Настройки:**
• Минимальная прибыль: {self.settings['min_profit']}%
• Интервал проверки: {self.settings['check_interval']} сек
• Межбиржевой арбитраж: {'✅' if self.settings['cross_exchange_enabled'] else '❌'}
• Треугольный арбитраж: {'✅' if self.settings['triangular_enabled'] else '❌'}
• Макс. уведомлений: {self.settings['max_notifications']}
• Порог уверенности: {self.settings['confidence_threshold']}
        """
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_settings(self, query):
        """Показать меню настроек"""
        keyboard = [
            [
                InlineKeyboardButton(f"💰 Прибыль: {self.settings['min_profit']}%", callback_data="set_profit"),
                InlineKeyboardButton(f"⏱️ Интервал: {self.settings['check_interval']}с", callback_data="set_interval")
            ],
            [
                InlineKeyboardButton(
                    f"🔄 Межбиржевой: {'✅' if self.settings['cross_exchange_enabled'] else '❌'}", 
                    callback_data="toggle_cross"
                ),
                InlineKeyboardButton(
                    f"🔺 Треугольный: {'✅' if self.settings['triangular_enabled'] else '❌'}", 
                    callback_data="toggle_triangular"
                )
            ],
            [
                InlineKeyboardButton(f"📱 Уведомлений: {self.settings['max_notifications']}", callback_data="set_notifications"),
                InlineKeyboardButton(f"🎯 Уверенность: {self.settings['confidence_threshold']}", callback_data="set_confidence")
            ],
            [
                InlineKeyboardButton(f"⏰ Срок: {self.settings['opportunity_expiry']}ч", callback_data="set_expiry"),
                InlineKeyboardButton("💾 Сохранить", callback_data="save_settings")
            ],
            [
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
⏰ **Срок возможности** - время жизни сигнала
        """
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_setting(self, query):
        """Обработка изменения настроек"""
        setting = query.data.replace("set_", "")
        
        if setting == "profit":
            # Циклическое изменение прибыли: 0.5% -> 0.75% -> 1.0% -> 1.5% -> 2.0%
            profits = [0.5, 0.75, 1.0, 1.5, 2.0]
            current_idx = profits.index(self.settings['min_profit']) if self.settings['min_profit'] in profits else 1
            self.settings['min_profit'] = profits[(current_idx + 1) % len(profits)]
            
        elif setting == "interval":
            # Циклическое изменение интервала: 3 -> 5 -> 10 -> 15 -> 30
            intervals = [3, 5, 10, 15, 30]
            current_idx = intervals.index(self.settings['check_interval']) if self.settings['check_interval'] in intervals else 1
            self.settings['check_interval'] = intervals[(current_idx + 1) % len(intervals)]
            
        elif setting == "notifications":
            # Циклическое изменение уведомлений: 10 -> 15 -> 25 -> 50
            notifications = [10, 15, 25, 50]
            current_idx = notifications.index(self.settings['max_notifications']) if self.settings['max_notifications'] in notifications else 2
            self.settings['max_notifications'] = notifications[(current_idx + 1) % len(notifications)]
            
        elif setting == "confidence":
            # Циклическое изменение уверенности: 0.05 -> 0.1 -> 0.2 -> 0.3
            confidences = [0.05, 0.1, 0.2, 0.3]
            current_idx = confidences.index(self.settings['confidence_threshold']) if self.settings['confidence_threshold'] in confidences else 1
            self.settings['confidence_threshold'] = confidences[(current_idx + 1) % len(confidences)]
            
        elif setting == "expiry":
            # Циклическое изменение срока: 0.5 -> 1 -> 2 -> 4
            expiries = [0.5, 1, 2, 4]
            current_idx = expiries.index(self.settings['opportunity_expiry']) if self.settings['opportunity_expiry'] in expiries else 1
            self.settings['opportunity_expiry'] = expiries[(current_idx + 1) % len(expiries)]
        
        # Обновляем меню настроек
        await self.show_settings(query)

    async def save_settings(self, query):
        """Сохранить настройки в файл"""
        try:
            # Сохраняем настройки в JSON файл
            settings_file = 'bot_settings.json'
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            
            await query.edit_message_text(
                "💾 **Настройки сохранены!**\n\nИзменения будут применены при следующем запуске монитора.",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ **Ошибка сохранения:**\n{str(e)}",
                parse_mode='Markdown'
            )

    def load_settings(self):
        """Загрузить настройки из файла"""
        try:
            settings_file = 'bot_settings.json'
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
                logger.info("✅ Настройки загружены из файла")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось загрузить настройки: {e}")

    async def start_monitor(self, query):
        """Запуск монитора"""
        if self.is_running:
            await query.edit_message_text("⚠️ Монитор уже запущен!")
            return
        
        try:
            # Применяем настройки
            await self.apply_settings()
            
            # Создаем и запускаем монитор
            self.monitor = SmartArbitrageMonitor()
            self.monitor_task = asyncio.create_task(
                self.monitor.run(check_interval=self.settings['check_interval'])
            )
            self.is_running = True
            
            await query.edit_message_text("✅ **Монитор запущен!**\n\nСистема начала поиск арбитражных возможностей.", parse_mode='Markdown')
            
        except Exception as e:
            await query.edit_message_text(f"❌ **Ошибка запуска:**\n{str(e)}", parse_mode='Markdown')

    async def stop_monitor(self, query):
        """Остановка монитора"""
        if not self.is_running:
            await query.edit_message_text("⚠️ Монитор уже остановлен!")
            return
        
        try:
            if self.monitor_task:
                self.monitor_task.cancel()
            if self.monitor:
                self.monitor.stop()
            
            self.is_running = False
            await query.edit_message_text("⏹️ **Монитор остановлен!**", parse_mode='Markdown')
            
        except Exception as e:
            await query.edit_message_text(f"❌ **Ошибка остановки:**\n{str(e)}", parse_mode='Markdown')

    async def restart_monitor(self, query):
        """Перезапуск монитора"""
        await query.edit_message_text("🔄 **Перезапуск системы...**", parse_mode='Markdown')
        
        # Останавливаем
        if self.is_running:
            if self.monitor_task:
                self.monitor_task.cancel()
            if self.monitor:
                self.monitor.stop()
            self.is_running = False
            
            # Ждем немного
            await asyncio.sleep(2)
        
        # Запускаем заново
        try:
            await self.apply_settings()
            self.monitor = SmartArbitrageMonitor()
            self.monitor_task = asyncio.create_task(
                self.monitor.run(check_interval=self.settings['check_interval'])
            )
            self.is_running = True
            
            await query.edit_message_text("✅ **Система перезапущена!**\n\nМонитор работает с новыми настройками.", parse_mode='Markdown')
            
        except Exception as e:
            await query.edit_message_text(f"❌ **Ошибка перезапуска:**\n{str(e)}", parse_mode='Markdown')

    async def show_stats(self, query):
        """Показать статистику"""
        if not self.monitor or not hasattr(self.monitor, 'stats'):
            await query.edit_message_text("📊 **Статистика недоступна**\n\nМонитор не запущен или нет данных.", parse_mode='Markdown')
            return
        
        stats = self.monitor.stats
        uptime = datetime.now() - stats['start_time']
        
        text = f"""
📈 **СТАТИСТИКА РАБОТЫ**

⏱️ **Время работы:** {uptime}
🔄 **Циклов выполнено:** {stats['total_cycles']}
🎯 **Всего возможностей:** {stats['total_opportunities_found']}
🆕 **Новых возможностей:** {stats['new_opportunities_found']}
📱 **Уведомлений отправлено:** {stats['notifications_sent']}
🔍 **Отслеживается:** {len(self.monitor.tracked_opportunities)}
🧹 **Очищено устаревших:** {stats['expired_opportunities_cleaned']}
❌ **Дубликатов отфильтровано:** {stats['duplicate_opportunities_filtered']}

📊 **Эффективность:**
• Новых/Всего: {(stats['new_opportunities_found'] / max(stats['total_opportunities_found'], 1) * 100):.1f}%
• Уведомлений/Циклов: {(stats['notifications_sent'] / max(stats['total_cycles'], 1)):.2f}
        """
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_main_menu(self, query):
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
• Минимальная прибыль: {self.settings['min_profit']}%
• Интервал проверки: {self.settings['check_interval']} сек
• Межбиржевой арбитраж: {'✅' if self.settings['cross_exchange_enabled'] else '❌'}
• Треугольный арбитраж: {'✅' if self.settings['triangular_enabled'] else '❌'}

Выберите действие:
        """
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def apply_settings(self):
        """Применить настройки к конфигурации"""
        # Обновляем глобальные настройки
        MONITORING_CONFIG['min_profit_threshold'] = self.settings['min_profit']
        MONITORING_CONFIG['check_interval'] = self.settings['check_interval']
        MONITORING_CONFIG['max_opportunities_per_notification'] = self.settings['max_notifications']
        
        # Обновляем настройки арбитража
        ARBITRAGE_CONFIG['cross_exchange']['enabled'] = self.settings['cross_exchange_enabled']
        ARBITRAGE_CONFIG['triangular']['enabled'] = self.settings['triangular_enabled']
        ARBITRAGE_CONFIG['cross_exchange']['min_confidence'] = self.settings['confidence_threshold']
        ARBITRAGE_CONFIG['triangular']['min_confidence'] = self.settings['confidence_threshold']

def main():
    """Главная функция бота"""
    bot = ArbitrageBot()
    
    # Создаем приложение
    application = Application.builder().token(bot.bot_token).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CallbackQueryHandler(bot.button_handler))
    
    # Запускаем бота
    logger.info("🤖 Запуск Telegram бота управления арбитражем...")
    application.run_polling()

if __name__ == "__main__":
    main()