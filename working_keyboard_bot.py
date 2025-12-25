#!/usr/bin/env python3
"""
Telegram бот управления треугольным арбитражем на MEXC
РАБОЧИЕ КНОПКИ - как до переключения на MEXC
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, ContextTypes, filters, CommandHandler

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
    """Загрузка настроек из файла - ПРОСТАЯ И НАДЕЖНАЯ"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
                logger.info("✅ Настройки загружены из файла")
                return loaded_settings
    except Exception as e:
        logger.warning(f"⚠️ Ошибка загрузки настроек: {e}")
    
    # Возвращаем копию настроек по умолчанию
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

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await show_welcome(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех сообщений - РАБОЧИЙ КАК ДО MEXC"""
    message_text = update.message.text
    
    # ВСЕГДА отправляем клавиатуру
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

async def show_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать приветственное сообщение"""
    keyboard = get_main_keyboard()
    
    text = f"""
🔺 **ТРЕУГОЛЬНЫЙ АРБИТРАЖ НА MEXC**

Добро пожаловать в систему управления!

📊 **Текущие настройки:**
• Минимальная прибыль: {settings.get('min_profit', 0.75)}%
• Максимальная позиция: ${settings.get('max_position', 50.0)}
• Режим торговли: {settings.get('trading_mode', 'live')}
• Тестовая среда: {'✅' if settings.get('mexc_sandbox', False) else '❌'}
• Статус бота: {'🟢 Работает' if settings.get('bot_running', False) else '🔴 Остановлен'}

🔺 **Только треугольный арбитраж:**
• Поиск треугольных возможностей на MEXC
• Автоматическое исполнение прибыльных сделок
• Детальные уведомления о каждой сделке

⚠️ **АРБИТРАЖ ПО УМОЛЧАНИЮ ВЫКЛЮЧЕН**
Нажмите "▶️ Запуск" для начала работы

💡 **Используйте кнопки внизу для управления**
    """
    
    await update.message.reply_text(
        text, 
        reply_markup=keyboard, 
        parse_mode='Markdown'
    )

async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статус системы - РЕАЛЬНАЯ ПРОВЕРКА"""
    keyboard = get_main_keyboard()
    
    # РЕАЛЬНАЯ ПРОВЕРКА ПРОЦЕССОВ
    arbitrage_running = False
    process_count = 0
    process_info = []
    
    try:
        import psutil
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'memory_info']):
            try:
                if proc.info['cmdline'] and any('triangular_arbitrage_bot.py' in cmd for cmd in proc.info['cmdline']):
                    arbitrage_running = True
                    process_count += 1
                    
                    # Информация о процессе
                    create_time = datetime.fromtimestamp(proc.info['create_time'])
                    uptime = datetime.now() - create_time
                    memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                    
                    process_info.append({
                        'pid': proc.info['pid'],
                        'uptime': str(uptime).split('.')[0],  # Убираем микросекунды
                        'memory': f"{memory_mb:.1f} MB"
                    })
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
    except ImportError:
        # Если psutil не установлен, используем настройки
        arbitrage_running = settings.get('bot_running', False)
    
    # Определяем реальный статус
    if arbitrage_running and settings.get('bot_running', False):
        status_icon = "🟢"
        status_text = "Работает"
        status_detail = f"Найдено {process_count} активных процессов"
    elif arbitrage_running and not settings.get('bot_running', False):
        status_icon = "🟡"
        status_text = "Работает (не управляется)"
        status_detail = "Процесс запущен вне системы управления"
    elif not arbitrage_running and settings.get('bot_running', False):
        status_icon = "🔴"
        status_text = "Ошибка (должен работать)"
        status_detail = "Флаг запуска установлен, но процесс не найден"
    else:
        status_icon = "🔴"
        status_text = "Остановлен"
        status_detail = "Система не активна"
    
    # Формируем сообщение
    text = f"""
📊 **СТАТУС ТРЕУГОЛЬНОГО АРБИТРАЖА**

{status_icon} **Состояние:** {status_text}
📋 **Детали:** {status_detail}
⏰ **Последнее обновление:** {settings.get('last_update', 'Неизвестно')}

🔧 **Настройки:**
• Минимальная прибыль: {settings.get('min_profit', 0.75)}%
• Максимальная позиция: ${settings.get('max_position', 50.0)}
• Режим торговли: {settings.get('trading_mode', 'live')}
• Тестовая среда MEXC: {'✅' if settings.get('mexc_sandbox', False) else '❌'}

📈 **Статистика:**
• Всего сделок: {settings.get('total_trades', 0)}
• Успешных: {settings.get('successful_trades', 0)}
• Общая прибыль: ${settings.get('total_profit', 0.0):.2f}
    """
    
    # Добавляем информацию о процессах если есть
    if process_info:
        text += "\n🔄 **Активные процессы:**\n"
        for proc in process_info:
            text += f"• PID {proc['pid']}: работает {proc['uptime']}, память {proc['memory']}\n"
    
    text += """
🔺 **Только треугольные возможности на MEXC**

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
            InlineKeyboardButton(f"💰 Прибыль: {settings.get('min_profit', 0.75)}%", callback_data="set_profit"),
            InlineKeyboardButton(f"💵 Позиция: ${settings.get('max_position', 50.0)}", callback_data="set_position")
        ],
        [
            InlineKeyboardButton(f"🎯 Режим: {settings.get('trading_mode', 'live')}", callback_data="toggle_mode"),
            InlineKeyboardButton(f"🧪 Sandbox: {'✅' if settings.get('mexc_sandbox', False) else '❌'}", callback_data="toggle_sandbox")
        ],
        [
            InlineKeyboardButton("💾 Сохранить настройки", callback_data="save_settings")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
⚙️ **НАСТРОЙКИ ТРЕУГОЛЬНОГО АРБИТРАЖА**

Нажмите на параметр для изменения:

💰 **Минимальная прибыль** - порог прибыльности для сделок
💵 **Максимальная позиция** - размер позиции в USD
🎯 **Режим торговли** - live (реальная) / test (симуляция)
🧪 **Sandbox** - тестовая среда MEXC

🔺 **Система ищет только треугольные возможности**

💡 **Кнопки управления всегда внизу экрана**
    """
    
    # ВСЕГДА отправляем основную клавиатуру
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

async def start_arbitrage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запуск треугольного арбитража - РЕАЛЬНОЕ ДЕЙСТВИЕ"""
    keyboard = get_main_keyboard()
    
    # Проверяем что арбитраж не запущен
    if settings.get('bot_running', False):
        text = """
⚠️ **АРБИТРАЖ УЖЕ ЗАПУЩЕН!**

🔺 Система уже работает и ищет треугольные возможности
📊 Используйте кнопку "Статус" для проверки состояния
⏹️ Используйте кнопку "Остановка" для остановки
        """
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')
        return
    
    # РЕАЛЬНЫЙ ЗАПУСК АРБИТРАЖА
    settings['bot_running'] = True
    settings['start_time'] = datetime.now().isoformat()
    save_settings(settings)
    
    # Запускаем арбитражный процесс
    try:
        import subprocess
        import sys
        
        # Запускаем треугольный арбитраж в фоне
        subprocess.Popen([
            sys.executable, 'triangular_arbitrage_bot.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        logger.info("🚀 Треугольный арбитраж запущен в фоне")
        
        text = f"""
✅ **ТРЕУГОЛЬНЫЙ АРБИТРАЖ ЗАПУЩЕН!**

🔺 Система начала поиск треугольных возможностей на MEXC
📱 Уведомления о сделках будут приходить в этот чат
⚙️ Используйте кнопки для управления

📊 **Настройки:**
• Минимальная прибыль: {settings.get('min_profit', 0.75)}%
• Максимальная позиция: ${settings.get('max_position', 50.0)}
• Режим: {settings.get('trading_mode', 'live')}

🚀 **Арбитражный процесс запущен в фоне**
⏰ Время запуска: {datetime.now().strftime('%H:%M:%S')}

💡 **Примечание:** В режиме '{settings.get('trading_mode', 'live')}'. Для реального запуска убедитесь что режим 'live'.
        """
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска арбитража: {e}")
        settings['bot_running'] = False
        save_settings(settings)
        
        text = f"""
❌ **ОШИБКА ЗАПУСКА АРБИТРАЖА!**

🚫 Не удалось запустить треугольный арбитраж
📝 Ошибка: {str(e)}
🔄 Попробуйте еще раз или проверьте логи

💡 Убедитесь что все зависимости установлены
        """
    
    await update.message.reply_text(
        text, 
        reply_markup=keyboard, 
        parse_mode='Markdown'
    )

async def stop_arbitrage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Остановка треугольного арбитража - РЕАЛЬНОЕ ДЕЙСТВИЕ"""
    keyboard = get_main_keyboard()
    
    # Проверяем что арбитраж запущен
    if not settings.get('bot_running', False):
        text = """
⚠️ **АРБИТРАЖ УЖЕ ОСТАНОВЛЕН!**

🔴 Система не работает
📊 Используйте кнопку "Статус" для проверки состояния
▶️ Используйте кнопку "Запуск" для запуска
        """
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')
        return
    
    # РЕАЛЬНАЯ ОСТАНОВКА АРБИТРАЖА
    settings['bot_running'] = False
    settings['stop_time'] = datetime.now().isoformat()
    save_settings(settings)
    
    try:
        import psutil
        import os
        
        # Находим и останавливаем процессы арбитража
        stopped_processes = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline'] and any('triangular_arbitrage_bot.py' in cmd for cmd in proc.info['cmdline']):
                    proc.terminate()
                    stopped_processes += 1
                    logger.info(f"🛑 Остановлен процесс арбитража PID: {proc.info['pid']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        text = f"""
⏹️ **ТРЕУГОЛЬНЫЙ АРБИТРАЖ ОСТАНОВЛЕН!**

🛑 Поиск треугольных возможностей приостановлен
📊 Статистика сохранена
▶️ Используйте кнопку "Запуск" для возобновления

🔺 Система готова к повторному запуску
⏰ Время остановки: {datetime.now().strftime('%H:%M:%S')}
🔄 Остановлено процессов: {stopped_processes}

💾 Все настройки и статистика сохранены
        """
        
    except ImportError:
        # Если psutil не установлен, просто меняем флаг
        text = """
⏹️ **ТРЕУГОЛЬНЫЙ АРБИТРАЖ ОСТАНОВЛЕН!**

🛑 Поиск треугольных возможностей приостановлен
📊 Статистика сохранена
▶️ Используйте кнопку "Запуск" для возобновления

🔺 Система готова к повторному запуску
⏰ Время остановки: {datetime.now().strftime('%H:%M:%S')}

💡 Для полной остановки перезапустите систему
        """
    except Exception as e:
        logger.error(f"❌ Ошибка остановки: {e}")
        text = f"""
⚠️ **АРБИТРАЖ ОСТАНОВЛЕН С ПРЕДУПРЕЖДЕНИЕМ**

🛑 Флаг остановки установлен
📝 Предупреждение: {str(e)}
🔄 Процессы могут продолжать работать

💡 Для полной остановки перезапустите систему
        """
    
    await update.message.reply_text(
        text, 
        reply_markup=keyboard, 
        parse_mode='Markdown'
    )

async def restart_arbitrage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапуск треугольного арбитража - РЕАЛЬНОЕ ДЕЙСТВИЕ"""
    keyboard = get_main_keyboard()
    
    try:
        # Сначала останавливаем
        settings['bot_running'] = False
        save_settings(settings)
        
        import psutil
        import subprocess
        import sys
        import time
        
        # Останавливаем старые процессы
        stopped_processes = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline'] and any('triangular_arbitrage_bot.py' in cmd for cmd in proc.info['cmdline']):
                    proc.terminate()
                    stopped_processes += 1
                    logger.info(f"🛑 Остановлен процесс арбитража PID: {proc.info['pid']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Ждем завершения процессов
        time.sleep(2)
        
        # Запускаем новый процесс
        settings['bot_running'] = True
        settings['restart_time'] = datetime.now().isoformat()
        save_settings(settings)
        
        subprocess.Popen([
            sys.executable, 'triangular_arbitrage_bot.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        logger.info("🔄 Треугольный арбитраж перезапущен")
        
        text = f"""
🔄 **ТРЕУГОЛЬНЫЙ АРБИТРАЖ ПЕРЕЗАПУЩЕН!**

✅ Новые настройки применены
🚀 Система работает с обновленными параметрами
📊 Статистика продолжается

⚙️ **Текущие настройки:**
• Минимальная прибыль: {settings.get('min_profit', 0.75)}%
• Максимальная позиция: ${settings.get('max_position', 50.0)}
• Режим: {settings.get('trading_mode', 'live')}

🔄 **Процесс перезапуска:**
• Остановлено процессов: {stopped_processes}
• Новый процесс запущен
• Время перезапуска: {datetime.now().strftime('%H:%M:%S')}

💡 **Настройки автоматически сохранены**
        """
        
    except ImportError:
        # Если psutil не установлен, просто меняем настройки
        settings['bot_running'] = True
        settings['restart_time'] = datetime.now().isoformat()
        save_settings(settings)
        
        text = f"""
🔄 **НАСТРОЙКИ ПЕРЕЗАПУЩЕНЫ!**

✅ Новые настройки применены и сохранены
📊 Статистика продолжается

⚙️ **Текущие настройки:**
• Минимальная прибыль: {settings.get('min_profit', 0.75)}%
• Максимальная позиция: ${settings.get('max_position', 50.0)}
• Режим: {settings.get('trading_mode', 'live')}

💡 Для полного перезапуска используйте кнопки "Остановка" → "Запуск"
        """
        
    except Exception as e:
        logger.error(f"❌ Ошибка перезапуска: {e}")
        settings['bot_running'] = False
        save_settings(settings)
        
        text = f"""
❌ **ОШИБКА ПЕРЕЗАПУСКА!**

🚫 Не удалось перезапустить арбитраж
📝 Ошибка: {str(e)}
🔄 Попробуйте использовать кнопки "Остановка" → "Запуск"

💡 Настройки сохранены, но процесс не запущен
        """
    
    await update.message.reply_text(
        text, 
        reply_markup=keyboard, 
        parse_mode='Markdown'
    )

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику"""
    keyboard = get_main_keyboard()
    
    uptime = "Система управления"
    if settings.get('last_update'):
        try:
            last_update = datetime.fromisoformat(settings['last_update'])
            uptime = str(datetime.now() - last_update)
        except:
            pass
    
    total_trades = settings.get('total_trades', 0)
    successful_trades = settings.get('successful_trades', 0)
    success_rate = 0
    if total_trades > 0:
        success_rate = (successful_trades / total_trades) * 100
    
    text = f"""
📈 **СТАТИСТИКА ТРЕУГОЛЬНОГО АРБИТРАЖА**

⏱️ **Время с последнего обновления:** {uptime}
🔄 **Статус:** {'🟢 Активен' if settings.get('bot_running', False) else '🔴 Остановлен'}

📊 **Торговая статистика:**
• Всего сделок: {total_trades}
• Успешных: {successful_trades}
• Процент успеха: {success_rate:.1f}%
• Общая прибыль: ${settings.get('total_profit', 0.0):.2f}

⚙️ **Текущие настройки:**
• Минимальная прибыль: {settings.get('min_profit', 0.75)}%
• Максимальная позиция: ${settings.get('max_position', 50.0)}
• Режим торговли: {settings.get('trading_mode', 'live')}
• Тестовая среда: {'✅' if settings.get('mexc_sandbox', False) else '❌'}

🔺 **Только треугольные возможности на MEXC**

💡 **Для реальной статистики запустите систему**
    """
    
    await update.message.reply_text(
        text, 
        reply_markup=keyboard, 
        parse_mode='Markdown'
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик inline кнопок - РЕАЛЬНЫЕ ИЗМЕНЕНИЯ НАСТРОЕК"""
    query = update.callback_query
    await query.answer()
    
    old_settings = settings.copy()  # Сохраняем старые настройки для сравнения
    
    if query.data == "set_profit":
        profits = [0.5, 0.75, 1.0, 1.5, 2.0]
        current_profit = settings.get('min_profit', 0.75)
        current_idx = profits.index(current_profit) if current_profit in profits else 1
        settings['min_profit'] = profits[(current_idx + 1) % len(profits)]
        
    elif query.data == "set_position":
        positions = [25.0, 50.0, 100.0, 200.0, 500.0]
        current_position = settings.get('max_position', 50.0)
        current_idx = positions.index(current_position) if current_position in positions else 1
        settings['max_position'] = positions[(current_idx + 1) % len(positions)]
        
    elif query.data == "toggle_mode":
        current_mode = settings.get('trading_mode', 'live')
        settings['trading_mode'] = 'test' if current_mode == 'live' else 'live'
        
    elif query.data == "toggle_sandbox":
        settings['mexc_sandbox'] = not settings.get('mexc_sandbox', False)
        
    elif query.data == "save_settings":
        # РЕАЛЬНОЕ СОХРАНЕНИЕ И ПРИМЕНЕНИЕ НАСТРОЕК
        save_settings(settings)
        
        # Проверяем изменились ли настройки
        changes = []
        if old_settings.get('min_profit') != settings.get('min_profit'):
            changes.append(f"Прибыль: {settings.get('min_profit')}%")
        if old_settings.get('max_position') != settings.get('max_position'):
            changes.append(f"Позиция: ${settings.get('max_position')}")
        if old_settings.get('trading_mode') != settings.get('trading_mode'):
            changes.append(f"Режим: {settings.get('trading_mode')}")
        if old_settings.get('mexc_sandbox') != settings.get('mexc_sandbox'):
            changes.append(f"Sandbox: {'✅' if settings.get('mexc_sandbox') else '❌'}")
        
        # Уведомляем работающий арбитраж о изменениях
        arbitrage_notified = False
        if settings.get('bot_running', False) and changes:
            try:
                # Создаем файл-сигнал для арбитража
                with open('settings_updated.signal', 'w') as f:
                    f.write(datetime.now().isoformat())
                arbitrage_notified = True
                logger.info("📡 Сигнал об обновлении настроек отправлен арбитражу")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось уведомить арбитраж: {e}")
        
        # Формируем сообщение о сохранении
        message = "💾 **Настройки сохранены!**\n\n✅ Все изменения применены и сохранены в файл.\n🔺 Треугольный арбитраж будет использовать новые настройки."
        
        if changes:
            message += f"\n\n🔄 **Изменения:**\n• " + "\n• ".join(changes)
            
        if arbitrage_notified:
            message += "\n\n📡 **Работающий арбитраж уведомлен об изменениях**"
        elif settings.get('bot_running', False):
            message += "\n\n⚠️ **Для применения изменений рекомендуется перезапуск**"
        
        await query.edit_message_text(message, parse_mode='Markdown')
        return
    
    # АВТОМАТИЧЕСКОЕ СОХРАНЕНИЕ при каждом изменении
    save_settings(settings)
    
    # Обновляем меню настроек
    await update_settings_menu(query)

async def update_settings_menu(query):
    """Обновить меню настроек"""
    keyboard = [
        [
            InlineKeyboardButton(f"💰 Прибыль: {settings.get('min_profit', 0.75)}%", callback_data="set_profit"),
            InlineKeyboardButton(f"💵 Позиция: ${settings.get('max_position', 50.0)}", callback_data="set_position")
        ],
        [
            InlineKeyboardButton(f"🎯 Режим: {settings.get('trading_mode', 'live')}", callback_data="toggle_mode"),
            InlineKeyboardButton(f"🧪 Sandbox: {'✅' if settings.get('mexc_sandbox', False) else '❌'}", callback_data="toggle_sandbox")
        ],
        [
            InlineKeyboardButton("💾 Сохранить настройки", callback_data="save_settings")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
🎛️ **Панель настроек:**

💰 Прибыль: {settings.get('min_profit', 0.75)}%
💵 Позиция: ${settings.get('max_position', 50.0)}
🎯 Режим: {settings.get('trading_mode', 'live')}
🧪 Sandbox: {'✅' if settings.get('mexc_sandbox', False) else '❌'}

🔺 Только треугольный арбитраж на MEXC
    """
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

def main():
    """Главная функция"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не найден в .env")
        return
    
    # Создаем приложение
    application = Application.builder().token(bot_token).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Запускаем бота
    logger.info("🤖 Запуск РАБОЧЕГО Telegram бота управления...")
    print("🔺 РАБОЧИЙ TELEGRAM БОТ УПРАВЛЕНИЯ")
    print("✅ Кнопки работают как до переключения на MEXC")
    print("📱 Клавиатура постоянная внизу экрана")
    print("💾 Настройки сохраняются в triangular_settings.json")
    print("🔺 Только треугольный арбитраж на MEXC")
    print("⚠️ Арбитраж по умолчанию ВЫКЛЮЧЕН")
    
    application.run_polling()

if __name__ == "__main__":
    main()