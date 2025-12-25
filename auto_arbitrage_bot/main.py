#!/usr/bin/env python3
"""
Главный файл автоматического арбитражного бота
"""

import asyncio
import signal
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Добавляем путь к модулям
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from config import config
from models import TradingMode
from core.arbitrage_engine import ArbitrageEngine
from utils.logger import get_logger
from utils.notifications import NotificationManager

class ArbitrageBot:
    """Главный класс арбитражного бота"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.engine = ArbitrageEngine()
        self.notification_manager = NotificationManager()
        self.is_running = False
        
    async def start(self):
        """Запуск бота"""
        self.logger.info("🚀 Запуск автоматического арбитражного бота...")
        
        try:
            # Валидация конфигурации
            errors = config.validate()
            if errors:
                for error in errors:
                    self.logger.error(f"❌ Ошибка конфигурации: {error}")
                return False
            
            # Вывод информации о конфигурации
            self._log_configuration()
            
            # Запуск движка арбитража
            self.is_running = True
            await self.engine.start()
            
            return True
            
        except KeyboardInterrupt:
            self.logger.info("⏹️ Получен сигнал остановки...")
            await self.stop()
            return True
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка: {e}")
            await self.notification_manager.send_message(f"❌ Критическая ошибка бота: {e}")
            return False
    
    async def stop(self):
        """Остановка бота"""
        if not self.is_running:
            return
        
        self.logger.info("🛑 Остановка арбитражного бота...")
        self.is_running = False
        
        try:
            # Остановка движка
            await self.engine.stop()
            
            # Уведомление об остановке
            await self.notification_manager.send_message(
                f"🛑 Арбитражный бот остановлен\n"
                f"Время работы: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            self.logger.info("✅ Бот успешно остановлен")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка при остановке: {e}")
    
    def _log_configuration(self):
        """Вывод информации о конфигурации"""
        self.logger.info("⚙️ Конфигурация системы:")
        self.logger.info(f"   Режим торговли: {config.trading_mode.value}")
        self.logger.info(f"   Минимальная прибыль: {config.arbitrage.min_profit_threshold}%")
        self.logger.info(f"   Максимальная позиция: ${config.arbitrage.max_position_size}")
        self.logger.info(f"   Максимальное проскальзывание: {config.arbitrage.max_slippage}%")
        self.logger.info(f"   Таймаут исполнения: {config.arbitrage.timeout_seconds}с")
        
        enabled_exchanges = config.get_enabled_exchanges()
        self.logger.info(f"   Включенные биржи: {', '.join(enabled_exchanges) if enabled_exchanges else 'Нет'}")
        
        self.logger.info(f"   Telegram уведомления: {'Включены' if config.telegram['enabled'] else 'Отключены'}")
        self.logger.info(f"   Веб-интерфейс: {'Включен' if config.web['enabled'] else 'Отключен'}")

def setup_signal_handlers(bot):
    """Настройка обработчиков сигналов"""
    def signal_handler(signum, frame):
        print(f"\n🛑 Получен сигнал {signum}, остановка бота...")
        asyncio.create_task(bot.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(description='Автоматический арбитражный бот')
    
    parser.add_argument(
        '--mode',
        choices=['test', 'paper', 'live'],
        default='test',
        help='Режим торговли (по умолчанию: test)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Путь к файлу конфигурации'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Уровень логирования (по умолчанию: INFO)'
    )
    
    parser.add_argument(
        '--exchanges',
        nargs='+',
        help='Список бирж для использования'
    )
    
    return parser.parse_args()

async def main():
    """Главная функция"""
    # Парсинг аргументов
    args = parse_arguments()
    
    # Применение аргументов к конфигурации
    if args.mode:
        config.trading_mode = TradingMode(args.mode)
    
    # Создание и запуск бота
    bot = ArbitrageBot()
    
    # Настройка обработчиков сигналов
    setup_signal_handlers(bot)
    
    # Запуск бота
    success = await bot.start()
    
    if success:
        # Ожидание завершения
        try:
            while bot.is_running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
    
    # Финальная остановка
    await bot.stop()
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Принудительная остановка")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)