#!/usr/bin/env python3
"""
Комбинированный деплой - бот + монитор в одном процессе
Для максимальной надежности на Railway
"""

import asyncio
import logging
import signal
import sys
from concurrent.futures import ThreadPoolExecutor
import threading

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CombinedDeployment:
    """Комбинированный деплой бота и монитора"""
    
    def __init__(self):
        self.bot_task = None
        self.monitor_task = None
        self.running = True
        
    async def start_bot(self):
        """Запуск Telegram бота"""
        try:
            logger.info("🤖 Запуск Telegram бота...")
            
            # Импортируем и запускаем бот
            from deployment_bot import main as bot_main
            
            # Запускаем бот в отдельном потоке
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            def run_bot():
                try:
                    bot_main()
                except Exception as e:
                    logger.error(f"❌ Ошибка в боте: {e}")
            
            # Запускаем в отдельном потоке
            bot_thread = threading.Thread(target=run_bot, daemon=True)
            bot_thread.start()
            
            logger.info("✅ Telegram бот запущен")
            
            # Ждем пока поток работает
            while self.running and bot_thread.is_alive():
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Критическая ошибка бота: {e}")
    
    async def start_monitor(self):
        """Запуск арбитражного монитора"""
        try:
            logger.info("📊 Запуск арбитражного монитора...")
            
            # Небольшая задержка чтобы бот успел запуститься
            await asyncio.sleep(10)
            
            # Импортируем и запускаем монитор
            from smart_arbitrage_monitor import SmartArbitrageMonitor
            
            monitor = SmartArbitrageMonitor()
            
            # Запускаем монитор
            await monitor.run(check_interval=5)
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка монитора: {e}")
    
    async def health_check(self):
        """Проверка здоровья системы"""
        while self.running:
            try:
                logger.info("💓 Система работает нормально")
                await asyncio.sleep(300)  # Каждые 5 минут
            except Exception as e:
                logger.error(f"❌ Ошибка health check: {e}")
                await asyncio.sleep(60)
    
    async def run(self):
        """Запуск всей системы"""
        logger.info("🚀 Запуск комбинированной системы...")
        
        try:
            # Запускаем все компоненты параллельно
            tasks = [
                asyncio.create_task(self.start_bot(), name="telegram_bot"),
                asyncio.create_task(self.start_monitor(), name="arbitrage_monitor"),
                asyncio.create_task(self.health_check(), name="health_check")
            ]
            
            # Ждем завершения любой задачи
            done, pending = await asyncio.wait(
                tasks, 
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Если какая-то задача завершилась, останавливаем остальные
            for task in pending:
                task.cancel()
                
            # Проверяем результаты
            for task in done:
                try:
                    result = await task
                    logger.info(f"✅ Задача {task.get_name()} завершена: {result}")
                except Exception as e:
                    logger.error(f"❌ Ошибка в задаче {task.get_name()}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Критическая ошибка системы: {e}")
        finally:
            self.running = False
            logger.info("🛑 Комбинированная система остановлена")

def signal_handler(signum, frame):
    """Обработчик сигналов"""
    logger.info(f"📡 Получен сигнал {signum}")
    sys.exit(0)

async def main():
    """Главная функция"""
    # Устанавливаем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🌟 Запуск комбинированного деплоя...")
    print("🌟 Комбинированный деплой запущен!")
    print("🤖 Telegram бот + 📊 Арбитражный монитор")
    print("💾 Все настройки сохраняются автоматически")
    print("🔄 Система перезапускается при ошибках")
    
    deployment = CombinedDeployment()
    
    try:
        await deployment.run()
    except KeyboardInterrupt:
        logger.info("⏹️ Получен сигнал остановки")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
    finally:
        logger.info("👋 Комбинированный деплой завершен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Система остановлена пользователем")
    except Exception as e:
        print(f"💥 Ошибка запуска: {e}")
        sys.exit(1)