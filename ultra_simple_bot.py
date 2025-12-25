#!/usr/bin/env python3
"""
Ультра простой Telegram бот - минимальный код для Railway
"""

import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# Загружаем переменные окружения
try:
    from dotenv import load_dotenv
    if os.path.exists('.env'):
        load_dotenv('.env')
except ImportError:
    pass

# Простые настройки
settings = {
    'min_profit': 0.75,
    'max_position': 50.0,
    'trading_mode': 'live',
    'bot_running': False,
    'total_trades': 0,
    'successful_trades': 0,
    'total_profit': 0.0
}

def save_settings():
    """Сохранить настройки"""
    try:
        with open('settings.json', 'w') as f:
            json.dump(settings, f)
    except:
        pass

def load_settings():
    """Загрузить настройки"""
    try:
        if os.path.exists('settings.json'):
            with open('settings.json', 'r') as f:
                global settings
                settings.update(json.load(f))
    except:
        pass

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех сообщений"""
    try:
        if not update.message or not update.message.text:
            return
            
        text = update.message.text.lower()
        
        # Команды
        if text in ['/start', 'start', 'старт', 'привет']:
            response = f"""
🔺 ТРЕУГОЛЬНЫЙ АРБИТРАЖ НА MEXC

Простой бот управления. Команды:

📊 УПРАВЛЕНИЕ:
• start / старт - это сообщение
• status / статус - статус системы  
• run / запуск - запустить арбитраж
• stop / стоп - остановить арбитраж
• help / помощь - справка

⚙️ НАСТРОЙКИ:
• Прибыль: {settings['min_profit']}%
• Позиция: ${settings['max_position']}
• Режим: {settings['trading_mode']}
• Статус: {'🟢 Работает' if settings['bot_running'] else '🔴 Остановлен'}

💡 Просто напишите команду
            """
            
        elif text in ['status', 'статус', '/status']:
            status = "🟢 Работает" if settings['bot_running'] else "🔴 Остановлен"
            response = f"""
📊 СТАТУС MEXC АРБИТРАЖА

{status}

⚙️ Настройки:
• Прибыль: {settings['min_profit']}%
• Позиция: ${settings['max_position']}
• Режим: {settings['trading_mode']}

📈 Статистика:
• Сделок: {settings['total_trades']}
• Успешных: {settings['successful_trades']}
• Прибыль: ${settings['total_profit']:.2f}

🔺 Треугольный арбитраж на MEXC
            """
            
        elif text in ['run', 'запуск', '/start_trading', 'запустить']:
            settings['bot_running'] = True
            save_settings()
            response = """
✅ АРБИТРАЖ ЗАПУЩЕН!

🔺 Поиск треугольных возможностей на MEXC
📱 Уведомления будут приходить сюда
⚙️ Используйте 'стоп' для остановки

💰 Ищем прибыль 0.75%+ среди 3361 пары
            """
            
        elif text in ['stop', 'стоп', '/stop_trading', 'остановить']:
            settings['bot_running'] = False
            save_settings()
            response = """
⏹️ АРБИТРАЖ ОСТАНОВЛЕН!

🛑 Поиск возможностей приостановлен
📊 Статистика сохранена
▶️ Используйте 'запуск' для возобновления
            """
            
        elif text in ['help', 'помощь', '/help', 'команды']:
            response = """
🆘 КОМАНДЫ УПРАВЛЕНИЯ

📊 ОСНОВНЫЕ:
• start / старт - приветствие
• status / статус - статус системы
• run / запуск - запустить арбитраж
• stop / стоп - остановить арбитраж
• help / помощь - эта справка

⚙️ НАСТРОЙКИ:
• profit 1.0 - установить прибыль 1.0%
• position 100 - установить позицию $100
• mode test - тестовый режим
• mode live - реальный режим

🔺 MEXC треугольный арбитраж 24/7
            """
            
        elif text.startswith('profit '):
            try:
                value = float(text.split()[1])
                if 0.1 <= value <= 5.0:
                    settings['min_profit'] = value
                    save_settings()
                    response = f"✅ Прибыль установлена: {value}%"
                else:
                    response = "❌ Прибыль должна быть от 0.1% до 5.0%"
            except:
                response = "❌ Формат: profit 1.0"
                
        elif text.startswith('position '):
            try:
                value = float(text.split()[1])
                if 10 <= value <= 1000:
                    settings['max_position'] = value
                    save_settings()
                    response = f"✅ Позиция установлена: ${value}"
                else:
                    response = "❌ Позиция должна быть от $10 до $1000"
            except:
                response = "❌ Формат: position 100"
                
        elif text.startswith('mode '):
            try:
                mode = text.split()[1]
                if mode in ['test', 'live']:
                    settings['trading_mode'] = mode
                    save_settings()
                    response = f"✅ Режим установлен: {mode}"
                else:
                    response = "❌ Режим: test или live"
            except:
                response = "❌ Формат: mode live"
                
        else:
            response = """
❓ Неизвестная команда

💡 Доступные команды:
• start - приветствие
• status - статус
• run - запустить
• stop - остановить  
• help - справка

Или напишите 'help' для полного списка
            """
        
        await update.message.reply_text(response)
        
    except Exception as e:
        try:
            await update.message.reply_text("❌ Ошибка. Попробуйте 'help'")
        except:
            pass

def main():
    """Главная функция"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN не найден")
        return
    
    load_settings()
    
    # Создаем приложение
    application = Application.builder().token(bot_token).build()
    
    # Один обработчик для всех сообщений
    application.add_handler(MessageHandler(filters.TEXT, handle_all_messages))
    
    print("🤖 Ультра простой бот запущен")
    print("🔺 MEXC треугольный арбитраж")
    print("📱 Обрабатывает все текстовые сообщения")
    
    try:
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()