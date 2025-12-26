#!/usr/bin/env python3
"""
Тест Railway бота
"""

import asyncio
from railway_bot import RailwayBot

async def test_railway_bot():
    """Тест Railway бота"""
    print("🚀 ТЕСТ RAILWAY БОТА")
    print("=" * 40)
    
    bot = RailwayBot()
    
    try:
        print("📱 Тест Telegram...")
        success = await bot.send_telegram("🧪 Тестовое сообщение от Railway бота")
        print(f"Telegram: {'✅' if success else '❌'}")
        
        print("📊 Тест получения баланса...")
        balance = await bot.get_mexc_balance()
        print(f"Баланс: {balance[:100]}...")
        
        print("🔍 Тест поиска возможностей...")
        opportunities = await bot.find_opportunities()
        if opportunities:
            print(f"Возможности: {opportunities[:100]}...")
        else:
            print("Возможности: Не найдены (это нормально)")
        
        print("💓 Тест heartbeat...")
        await bot.send_heartbeat()
        
        print("⚠️ Тест обработки ошибок...")
        await bot.handle_error(Exception("Тестовая ошибка"), "Тест")
        
        print("✅ Все тесты пройдены")
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()
    
    print("🔺 Тест завершен")

if __name__ == "__main__":
    asyncio.run(test_railway_bot())