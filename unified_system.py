#!/usr/bin/env python3
"""
Объединенная система: Telegram бот + Треугольный арбитраж
Запускает оба компонента одновременно в одном процессе
"""

import asyncio
import signal
import sys
import os
import time
import logging
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

# Добавляем пути к модулям
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / 'auto_arbitrage_bot'))

# Загружаем переменные окружения
try:
    from dotenv import load_dotenv
    env_path = current_dir / 'auto_arbitrage_bot' / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Загружен .env файл: {env_path}")
    else:
        print(f"⚠️ .env файл не найден: {env_path}")
except ImportError:
    print("⚠️ python-dotenv не установлен")

class UnifiedArbitrageSystem:
    """Объединенная система арбитража и Telegram бота"""
    
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Компоненты системы
        self.arbitrage_bot = None
        self.telegram_bot = None
        self.smart_monitor = None
        self.health_service = None
        
        # Состояние системы
        self.is_running = False
        self.shutdown_requested = False
        
        # Статистика
        self.system_stats = {
            'start_time': time.time(),
            'arbitrage_cycles': 0,
            'telegram_messages': 0,
            'opportunities_found': 0,
            'trades_executed': 0,
            'total_profit': 0.0
        }
        
        # Настройка обработчиков сигналов
        self.setup_signal_handlers()
    
    def setup_logging(self):
        """Настройка логирования"""
        log_dir = current_dir / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'unified_system.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def setup_signal_handlers(self):
        """Настройка обработчиков сигналов"""
        def signal_handler(signum, frame):
            signal_name = signal.Signals(signum).name
            self.logger.info(f"📡 Получен сигнал {signal_name}")
            self.shutdown_requested = True
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def start_telegram_bot(self):
        """Запуск Telegram бота"""
        try:
            self.logger.info("🤖 Запуск Telegram бота...")
            
            # Проверяем наличие токена
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '8565304713:AAFpnuNkp4QR6Yk9H-5NoN8l3Z1pN2WigKQ')
            chat_id = os.getenv('TELEGRAM_CHAT_ID', '884434550')
            
            if not bot_token or bot_token == 'your_telegram_bot_token':
                self.logger.warning("⚠️ Telegram токен не настроен, бот не будет запущен")
                return None
            
            # Импортируем и создаем бота
            try:
                # Пробуем импортировать персистентный бот
                sys.path.insert(0, str(current_dir))
                
                # Создаем простую версию бота для объединенной системы
                from telegram.ext import Application
                
                application = Application.builder().token(bot_token).build()
                
                # Простой обработчик сообщений
                async def handle_message(update, context):
                    message = f"""
🤖 ОБЪЕДИНЕННАЯ СИСТЕМА АРБИТРАЖА

📊 Статус: {'🟢 Работает' if self.is_running else '🔴 Остановлена'}
⏰ Время работы: {(time.time() - self.system_stats['start_time'])/3600:.1f} часов

📈 Статистика:
• Циклов арбитража: {self.system_stats['arbitrage_cycles']}
• Найдено возможностей: {self.system_stats['opportunities_found']}
• Исполнено сделок: {self.system_stats['trades_executed']}
• Общая прибыль: ${self.system_stats['total_profit']:.2f}

🔧 Компоненты:
• Telegram бот: {'✅' if self.telegram_bot else '❌'}
• Умный монитор: {'✅' if self.smart_monitor else '❌'}
• Треугольный арбитраж: {'✅' if self.arbitrage_bot else '❌'}
• Health сервис: {'✅' if self.health_service else '❌'}

💡 Система работает автоматически 24/7
                    """
                    await update.message.reply_text(message.strip())
                    self.system_stats['telegram_messages'] += 1
                
                from telegram.ext import MessageHandler, filters
                application.add_handler(MessageHandler(filters.TEXT, handle_message))
                
                # Запускаем бота в отдельной задаче
                async def run_bot():
                    await application.initialize()
                    await application.start()
                    await application.updater.start_polling()
                    
                    # Отправляем уведомление о запуске
                    try:
                        await application.bot.send_message(
                            chat_id=chat_id,
                            text="🚀 Объединенная система арбитража запущена!\n\n"
                                 "📊 Мониторинг возможностей активен\n"
                                 "🔺 Треугольный арбитраж готов\n"
                                 "💬 Отправьте любое сообщение для статуса"
                        )
                    except Exception as e:
                        self.logger.warning(f"Не удалось отправить уведомление о запуске: {e}")
                    
                    # Держим бота активным
                    while self.is_running:
                        await asyncio.sleep(60)
                    
                    await application.updater.stop()
                    await application.stop()
                    await application.shutdown()
                
                telegram_task = asyncio.create_task(run_bot())
                self.telegram_bot = application
                
                self.logger.info("✅ Telegram бот запущен")
                return telegram_task
                
            except ImportError as e:
                self.logger.warning(f"⚠️ Не удалось импортировать Telegram бота: {e}")
                return None
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка запуска Telegram бота: {e}")
            return None
    
    async def start_arbitrage_monitor(self):
        """Запуск монитора арбитража"""
        try:
            self.logger.info("🔺 Запуск монитора треугольного арбитража...")
            
            # Импортируем и запускаем smart monitor
            from smart_arbitrage_monitor import SmartArbitrageMonitor
            
            self.smart_monitor = SmartArbitrageMonitor()
            
            # Запускаем монитор в отдельной задаче
            monitor_task = asyncio.create_task(self.smart_monitor.run())
            
            self.logger.info("✅ Монитор арбитража запущен")
            return monitor_task
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка запуска монитора арбитража: {e}")
            return None
    
    async def start_triangular_arbitrage(self):
        """Запуск треугольного арбитража"""
        try:
            self.logger.info("🔺 Запуск треугольного арбитража...")
            
            # Импортируем треугольный арбитраж
            from auto_arbitrage_bot.bybit_live_triangular import BybitLiveTriangularBot
            
            self.arbitrage_bot = BybitLiveTriangularBot()
            
            if await self.arbitrage_bot.initialize():
                # Запускаем арбитраж в отдельной задаче
                arbitrage_task = asyncio.create_task(self.arbitrage_bot.run_24_7_monitoring())
                
                self.logger.info("✅ Треугольный арбитраж запущен")
                return arbitrage_task
            else:
                self.logger.error("❌ Не удалось инициализировать треугольный арбитраж")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка запуска треугольного арбитража: {e}")
            return None
    
    async def start_health_service(self):
        """Запуск health check сервиса"""
        try:
            self.logger.info("🏥 Запуск Health Check сервиса...")
            
            # Импортируем health service
            try:
                from auto_arbitrage_bot.health_check import HealthService
                self.health_service = HealthService()
                
                # Запускаем health service
                health_task = asyncio.create_task(self.health_service.start_server())
                
                self.logger.info("✅ Health Check сервис запущен на порту 8080")
                return health_task
            except ImportError:
                self.logger.warning("⚠️ Health Check сервис не найден, создаем простой веб-сервер...")
                return await self.start_simple_health_server()
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка запуска Health Check: {e}")
            return None
    
    async def start_simple_health_server(self):
        """Запуск простого health check сервера"""
        try:
            from aiohttp import web
            
            async def health_check(request):
                uptime = time.time() - self.system_stats['start_time']
                status = {
                    'status': 'healthy' if self.is_running else 'stopped',
                    'uptime_seconds': uptime,
                    'components': {
                        'telegram_bot': self.telegram_bot is not None,
                        'smart_monitor': self.smart_monitor is not None,
                        'arbitrage_bot': self.arbitrage_bot is not None
                    },
                    'stats': self.system_stats,
                    'timestamp': datetime.now().isoformat()
                }
                return web.json_response(status)
            
            app = web.Application()
            app.router.add_get('/', health_check)
            app.router.add_get('/health', health_check)
            app.router.add_get('/status', health_check)
            
            # Получаем порт из переменной окружения или используем 8080
            port = int(os.getenv('PORT', '8080'))
            
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', port)
            await site.start()
            
            self.logger.info(f"✅ Простой health сервер запущен на порту {port}")
            
            # Возвращаем задачу, которая будет работать бесконечно
            async def keep_running():
                while self.is_running:
                    await asyncio.sleep(60)
            
            return asyncio.create_task(keep_running())
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка запуска простого health сервера: {e}")
            return None
    
    async def system_monitor(self):
        """Системный монитор - отслеживает состояние всех компонентов"""
        self.logger.info("📊 Запуск системного монитора...")
        
        while self.is_running and not self.shutdown_requested:
            try:
                # Обновляем статистику
                uptime = time.time() - self.system_stats['start_time']
                
                # Логируем статистику каждые 10 минут
                if int(uptime) % 600 == 0:
                    self.logger.info("📊 СИСТЕМНАЯ СТАТИСТИКА:")
                    self.logger.info(f"   ⏰ Время работы: {uptime/3600:.1f} часов")
                    self.logger.info(f"   🔄 Циклов арбитража: {self.system_stats['arbitrage_cycles']}")
                    self.logger.info(f"   💬 Telegram сообщений: {self.system_stats['telegram_messages']}")
                    self.logger.info(f"   💡 Найдено возможностей: {self.system_stats['opportunities_found']}")
                    self.logger.info(f"   📈 Исполнено сделок: {self.system_stats['trades_executed']}")
                    self.logger.info(f"   💰 Общая прибыль: ${self.system_stats['total_profit']:.2f}")
                
                await asyncio.sleep(60)  # Проверка каждую минуту
                
            except Exception as e:
                self.logger.error(f"❌ Ошибка системного монитора: {e}")
                await asyncio.sleep(60)
    
    async def run_unified_system(self):
        """Запуск объединенной системы"""
        self.logger.info("🚀 ЗАПУСК ОБЪЕДИНЕННОЙ СИСТЕМЫ АРБИТРАЖА")
        self.logger.info("=" * 70)
        self.logger.info("🤖 Telegram бот для управления")
        self.logger.info("🔺 Треугольный арбитраж на Bybit")
        self.logger.info("📊 Мониторинг возможностей")
        self.logger.info("🏥 Health Check сервис")
        self.logger.info("=" * 70)
        
        self.is_running = True
        tasks = []
        
        try:
            # 1. Запуск Health Check сервиса
            health_task = await self.start_health_service()
            if health_task:
                tasks.append(health_task)
            
            # 2. Запуск Telegram бота
            telegram_task = await self.start_telegram_bot()
            if telegram_task:
                tasks.append(telegram_task)
            
            # 3. Запуск монитора арбитража (основной)
            monitor_task = await self.start_arbitrage_monitor()
            if monitor_task:
                tasks.append(monitor_task)
            
            # 4. Запуск треугольного арбитража (дополнительный)
            arbitrage_task = await self.start_triangular_arbitrage()
            if arbitrage_task:
                tasks.append(arbitrage_task)
            
            # 5. Запуск системного монитора
            system_task = asyncio.create_task(self.system_monitor())
            tasks.append(system_task)
            
            if not tasks:
                self.logger.error("❌ Не удалось запустить ни одного компонента!")
                return
            
            self.logger.info(f"✅ Запущено {len(tasks)} компонентов системы")
            self.logger.info("🔄 Система работает в штатном режиме...")
            
            # Ожидаем завершения всех задач
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка системы: {e}")
        finally:
            await self.shutdown_system()
    
    async def shutdown_system(self):
        """Корректное завершение системы"""
        self.logger.info("🛑 Начало процедуры остановки системы...")
        
        self.is_running = False
        
        try:
            # Остановка компонентов
            if self.arbitrage_bot:
                self.logger.info("🔺 Остановка треугольного арбитража...")
                await self.arbitrage_bot.stop()
            
            if self.smart_monitor:
                self.logger.info("📊 Остановка монитора...")
                # smart_monitor не имеет метода stop, просто прерываем
            
            # Финальная статистика
            uptime = time.time() - self.system_stats['start_time']
            self.logger.info("📊 ФИНАЛЬНАЯ СТАТИСТИКА:")
            self.logger.info(f"   ⏰ Общее время работы: {uptime/3600:.1f} часов")
            self.logger.info(f"   🔄 Всего циклов: {self.system_stats['arbitrage_cycles']}")
            self.logger.info(f"   💰 Общая прибыль: ${self.system_stats['total_profit']:.2f}")
            
            self.logger.info("✅ Система остановлена корректно")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка при остановке: {e}")

async def main():
    """Главная функция"""
    print("🚀 ОБЪЕДИНЕННАЯ СИСТЕМА АРБИТРАЖА")
    print("=" * 50)
    print("🤖 Telegram бот + 🔺 Треугольный арбитраж")
    print("=" * 50)
    
    # Создание и запуск объединенной системы
    system = UnifiedArbitrageSystem()
    
    try:
        await system.run_unified_system()
    except KeyboardInterrupt:
        print("\n⏹️ Получен сигнал остановки...")
    except Exception as e:
        print(f"❌ Фатальная ошибка: {e}")
    
    print("👋 Система остановлена")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        sys.exit(1)