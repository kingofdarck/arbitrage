#!/usr/bin/env python3
"""
Тест ультра простого бота
"""

import asyncio
from ultra_simple_bot import UltraSimpleBot

async def test_ultra_simple():
    """Тест ультра простого бота"""
    print("🤖 ТЕСТ УЛЬТРА ПРОСТОГО БОТА")
    print("=" * 40)
    
    bot = UltraSimpleBot()
    
    try:
        print("📱 Тест Telegram...")
        await bot.send_telegram("🧪 Тестовое сообщение от ультра простого бота")
        
        print("📊 Тест получения баланса...")
        balance = await bot.get_mexc_balance()
        print(f"Баланс: {balance[:100]}...")
        
        print("🔍 Тест поиска возможностей...")
        opportunities = await bot.find_opportunities()
        print(f"Возможности: {opportunities[:100]}...")
        
        print("✅ Все тесты пройдены")
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()
    
    print("🔺 Тест завершен")

if __name__ == "__main__":
    asyncio.run(test_ultra_simple())