#!/usr/bin/env python3
"""
Запуск Telegram бота управления арбитражным монитором
"""

import sys
import logging
from telegram_bot import main

if __name__ == "__main__":
    try:
        print("🤖 Запуск Telegram бота управления...")
        main()
    except KeyboardInterrupt:
        print("\n⏹️ Бот остановлен")
    except Exception as e:
        print(f"💥 Ошибка запуска бота: {e}")
        sys.exit(1)