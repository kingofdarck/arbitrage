#!/usr/bin/env python3
"""
Тест автономного треугольного арбитража
"""

import asyncio
import os
from auto_triangular_bot import AutoTriangularBot

async def test_auto_bot():
    """Тест автономного бота"""
    print("🔺 ТЕСТ АВТОНОМНОГО ТРЕУГОЛЬНОГО АРБИТРАЖА")
    print("=" * 50)
    
    # Устанавливаем тестовый режим
    os.environ['TRADING_MODE'] = 'test'
    os.environ['MIN_PROFIT_THRESHOLD'] = '0.1'  # Низкий порог для теста
    
    bot = AutoTriangularBot()
    
    try:
        print("🔄 Инициализация...")
        if await bot.initialize():
            print("✅ Инициализация успешна")
            
            print("🔍 Поиск треугольников...")
            opportunity = await bot.find_best_triangle()
            
            if opportunity:
                print(f"✅ Найден треугольник:")
                triangle = opportunity['triangle']
                print(f"   🔺 Путь: {triangle[4]} → {triangle[0].split('/')[0]} → {triangle[2].split('/')[0]} → {triangle[4]}")
                print(f"   💰 Прибыль: {opportunity['profit_percent']:.3f}%")
                print(f"   💵 Сумма: {opportunity['initial_amount']:.6f} {triangle[4]}")
                
                print("🚀 Тестовое исполнение...")
                result = await bot.execute_triangle(opportunity)
                
                if result.success:
                    print("✅ Тестовое исполнение успешно")
                    print(f"   💰 Прибыль: {result.profit:.6f} ({result.profit_percent:.3f}%)")
                    print(f"   ⏱️ Время: {result.execution_time:.2f}с")
                else:
                    print(f"❌ Ошибка исполнения: {result.error}")
                
                print("📱 Отправка отчета...")
                await bot.send_triangle_report(result)
                
            else:
                print("❌ Треугольники не найдены")
                
        else:
            print("❌ Ошибка инициализации")
            
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
    
    finally:
        if bot.exchange:
            await bot.exchange.close()
    
    print("🔺 Тест завершен")

if __name__ == "__main__":
    asyncio.run(test_auto_bot())