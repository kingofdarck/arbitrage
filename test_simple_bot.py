#!/usr/bin/env python3
"""
Тест простого рабочего бота
"""

import asyncio
from simple_working_bot import SimpleWorkingBot

async def test_simple_bot():
    """Тест простого бота"""
    print("🤖 ТЕСТ ПРОСТОГО РАБОЧЕГО БОТА")
    print("=" * 40)
    
    bot = SimpleWorkingBot()
    
    try:
        print("🔄 Инициализация...")
        if await bot.initialize():
            print("✅ Инициализация успешна")
            
            print("📊 Тест отчета о балансе...")
            balance_report = await bot.get_balance_report()
            print(f"Отчет: {balance_report[:100]}...")
            
            print("🔍 Тест поиска арбитража...")
            opportunity = await bot.find_simple_arbitrage()
            
            if opportunity:
                print(f"✅ Найдена возможность: {opportunity['profit_percent']:.3f}%")
                print(f"   Путь: {opportunity['path']}")
                
                print("🚀 Тест исполнения...")
                result = await bot.execute_simple_trade(opportunity)
                print(f"Результат: {result[:100]}...")
            else:
                print("❌ Возможности не найдены (это нормально)")
            
            print("📱 Тест Telegram...")
            await bot.send_telegram("🧪 Тестовое сообщение от простого бота")
            
        else:
            print("❌ Ошибка инициализации")
            
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if bot.exchange:
            # Для синхронной версии ccxt не нужно await
            pass
    
    print("🔺 Тест завершен")

if __name__ == "__main__":
    asyncio.run(test_simple_bot())