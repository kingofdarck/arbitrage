#!/usr/bin/env python3
"""
Комбинированный запуск: арбитражный монитор + Telegram бот управления
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Optional

from smart_arbitrage_monitor import SmartArbitrageMonitor
from telegram_bot import ArbitrageBot
from config import NOTIFICATION_CONFIG

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('combined_monitor.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class CombinedSystem:
    def __init__(self):
        self.monitor: Optional[SmartArbitrageMonitor] = None
        self.bot: Optional[ArbitrageBot] = None
        self.monitor_task: Optional[asyncio.Task] = None
        self.bot_task: Optional[asyncio.Task] = None
        self.running = True

    async def start_monitor(self):
        """Запуск арбитражного монитора"""
        try:
            self.monitor = SmartArbitrageMonitor()
            logger.info("🚀 Запуск арбитражного монитора...")
            await self.monitor.run(check_interval=5)
        except Exception as e:
            logger.error(f"❌ Ошибка монитора: {e}")

    async def start_bot(self):
        """Запуск Telegram бота"""
        try:
            from telegram.ext import Application, CommandHandler, CallbackQueryHandler
            
            self.bot = ArbitrageBot()
            
            # Создаем приложение
            application = Application.builder().token(self.bot.bot_token).build()
            
            # Добавляем обработчики
            application.add_handler(CommandHandler("start", self.bot.start_command))
            application.add_handler(CallbackQueryHandler(self.bot.button_handler))
            
            logger.info("🤖 Запуск Telegram бота...")
            
            # Запускаем бот
            async with application:
                await application.start()
                await application.updater.start_polling()
                
                # Ждем пока не остановят
                while self.running:
                    await asyncio.sleep(1)
                    
                await application.updater.stop()
                await application.stop()
                
        except Exception as e:
            logger.error(f"❌ Ошибка бота: {e}")
            import traceback
            traceback.print_exc()

    async def run(self):
        """Запуск обеих систем"""
        logger.info("🎯 Запуск комбинированной системы: Монитор + Бот")
        
        # Запускаем обе системы параллельно
        self.monitor_task = asyncio.create_task(self.start_monitor())
        self.bot_task = asyncio.create_task(self.start_bot())
        
        # Ждем завершения любой из задач
        try:
            await asyncio.gather(self.monitor_task, self.bot_task)
        except asyncio.CancelledError:
            logger.info("🛑 Система остановлена")

    def stop(self):
        """Остановка системы"""
        self.running = False
        if self.monitor:
            self.monitor.stop()
        if self.monitor_task:
            self.monitor_task.cancel()
        if self.bot_task:
            self.bot_task.cancel()

async def main():
    """Главная функция"""
    system = CombinedSystem()
    
    # Обработка сигналов для корректного завершения
    def signal_handler(signum, frame):
        logger.info(f"Получен сигнал {signum}")
        system.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await system.run()
    except KeyboardInterrupt:
        logger.info("Система остановлена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        logger.info("👋 Комбинированная система завершена")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Система остановлена")
    except Exception as e:
        print(f"💥 Ошибка запуска: {e}")
        sys.exit(1)