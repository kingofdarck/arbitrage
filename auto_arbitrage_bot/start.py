#!/usr/bin/env python3
"""
Простой скрипт запуска арбитражного бота
"""

import os
import sys
import asyncio
from pathlib import Path

# Добавляем текущую директорию в путь Python
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def check_requirements():
    """Проверка требований"""
    try:
        import ccxt
        import aiohttp
        import pandas
        import numpy
        print("✅ Все зависимости установлены")
        return True
    except ImportError as e:
        print(f"❌ Отсутствует зависимость: {e}")
        print("Установите зависимости: pip install -r requirements.txt")
        return False

def check_configuration():
    """Проверка конфигурации"""
    try:
        from config import config
        
        print(f"⚙️ Режим торговли: {config.trading_mode.value}")
        print(f"💰 Минимальная прибыль: {config.arbitrage.min_profit_threshold}%")
        
        # Проверка API ключей
        enabled_exchanges = config.get_enabled_exchanges()
        if enabled_exchanges:
            print(f"🏛️ Включенные биржи: {', '.join(enabled_exchanges)}")
        else:
            print("⚠️ Нет включенных бирж (нормально для тестового режима)")
        
        # Проверка Telegram
        if config.telegram['enabled']:
            if config.telegram['bot_token'] and config.telegram['chat_id']:
                print("📱 Telegram уведомления: включены")
            else:
                print("⚠️ Telegram включен, но не настроен")
        else:
            print("📱 Telegram уведомления: отключены")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False

async def main():
    """Главная функция"""
    print("🚀 Запуск автоматического арбитражного бота...")
    print("=" * 50)
    
    # Проверка требований
    if not check_requirements():
        return 1
    
    # Проверка конфигурации
    if not check_configuration():
        return 1
    
    print("=" * 50)
    
    try:
        # Импорт и запуск основного приложения
        from main import ArbitrageBot
        
        bot = ArbitrageBot()
        
        print("🎯 Запуск арбитражного движка...")
        success = await bot.start()
        
        if success:
            print("✅ Бот успешно запущен")
            
            # Ожидание завершения
            try:
                while bot.is_running:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n⏹️ Получен сигнал остановки...")
        
        await bot.stop()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⏹️ Принудительная остановка")
        return 0
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Остановка")
        sys.exit(0)