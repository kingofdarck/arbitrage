#!/usr/bin/env python3
"""
Тест исправленного автономного треугольного арбитража
"""

import asyncio
import os
from fixed_auto_bot import FixedAutoBot

async def test_fixed_bot():
    """Тест исправленного бота"""
    print("🤖 ТЕСТ ИСПРАВЛЕННОГО АВТОНОМНОГО АРБИТРАЖА")
    print("=" * 50)
    
    # Устанавливаем тестовый режим
    os.environ['TRADING_MODE'] = 'test'
    os.environ['MIN_PROFIT_THRESHOLD'] = '0.1'  # Очень низкий порог для теста
    os.environ['MIN_BALANCE_USDT'] = '1.0'  # Низкий минимум
    
    bot = FixedAutoBot()
    
    try:
        print("🔄 Инициализация...")
        if await bot.initialize():
            print("✅ Инициализация успешна")
            print(f"   Сгенерировано треугольников: {len(bot.valid_triangles)}")
            
            if bot.valid_triangles:
                print("✅ Треугольники найдены!")
                for i, triangle in enumerate(bot.valid_triangles[:3]):
                    pair1, pair2, pair3, direction, base = triangle
                    crypto1 = pair1.split('/')[0]
                    crypto2 = pair3.split('/')[0]
                    path = f"{base} -> {crypto1} -> {crypto2} -> {base}"
                    print(f"   {i+1}. {path} ({direction})")
                
                print("📊 Отчет о балансе...")
                await bot.send_balance_report()
                
                print("🔍 Поиск треугольников...")
                opportunity = await bot.find_best_triangle()
                
                if opportunity:
                    print(f"✅ Найден треугольник:")
                    triangle = opportunity['triangle']
                    print(f"   🔺 Путь: {triangle[4]} -> {triangle[0].split('/')[0]} -> {triangle[2].split('/')[0]} -> {triangle[4]}")
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
                    print("❌ Прибыльные треугольники не найдены")
                    print("💡 Попробуйте снизить MIN_PROFIT_THRESHOLD")
            else:
                print("❌ Треугольники не сгенерированы")
                print("💡 Проверьте доступность торговых пар")
                
        else:
            print("❌ Ошибка инициализации")
            
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if bot.exchange:
            await bot.exchange.close()
    
    print("🔺 Тест завершен")

if __name__ == "__main__":
    asyncio.run(test_fixed_bot())