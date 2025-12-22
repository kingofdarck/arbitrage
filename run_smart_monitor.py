#!/usr/bin/env python3
"""
Запуск умного арбитражного монитора
"""

import asyncio
import logging
from smart_arbitrage_monitor import SmartArbitrageMonitor

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def main():
    """Запуск умного монитора"""
    monitor = SmartArbitrageMonitor()
    
    try:
        print("🧠 Запуск умного арбитражного монитора...")
        print("📱 Раздельные уведомления для каждого типа арбитража")
        print("📊 Минимальная прибыль: 0.75% для всех типов")
        print("🔍 Межбиржевой и треугольный арбитраж")
        print("⏹️ Нажмите Ctrl+C для остановки")
        
        await monitor.run(check_interval=10)
        
    except KeyboardInterrupt:
        print("\n⏹️ Остановка мониторинга...")
    except Exception as e:
        print(f"💥 Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())