#!/usr/bin/env python3
"""
Тестирование модуля проверки ликвидности
"""

import asyncio
import sys
from liquidity_checker import LiquidityChecker

async def test_liquidity_checker():
    """Тестирование проверки ликвидности"""
    print("🔍 Тестирование модуля проверки ликвидности...")
    
    checker = LiquidityChecker()
    await checker.start_session()
    
    try:
        # Тестируем популярные пары
        test_cases = [
            ('BTCUSDT', 'binance', 'bybit'),
            ('ETHUSDT', 'okx', 'kucoin'),
            ('ADAUSDT', 'binance', 'mexc'),
            ('BNBUSDT', 'binance', 'okx'),
            ('SOLUSDT', 'bybit', 'kucoin')
        ]
        
        print(f"\n📊 Тестирование {len(test_cases)} арбитражных возможностей:\n")
        
        viable_count = 0
        total_count = len(test_cases)
        
        for i, (symbol, buy_exchange, sell_exchange) in enumerate(test_cases, 1):
            print(f"{i}. 🔍 {symbol}: {buy_exchange.upper()} → {sell_exchange.upper()}")
            
            try:
                # Проверяем ликвидность
                liquidity = await checker.check_arbitrage_liquidity(symbol, buy_exchange, sell_exchange)
                
                # Форматируем результат
                status_info = checker.format_liquidity_info(liquidity)
                print(f"   Результат: {status_info}")
                
                if liquidity.is_viable:
                    viable_count += 1
                    print(f"   ✅ ДОСТУПНО для арбитража")
                    
                    if liquidity.buy_liquidity:
                        dep_status = "✅" if liquidity.buy_liquidity.deposit_enabled else "❌"
                        print(f"   📥 Депозит на {buy_exchange}: {dep_status}")
                        if liquidity.buy_liquidity.deposit_min > 0:
                            print(f"      Мин. депозит: {liquidity.buy_liquidity.deposit_min}")
                    
                    if liquidity.sell_liquidity:
                        with_status = "✅" if liquidity.sell_liquidity.withdraw_enabled else "❌"
                        print(f"   📤 Вывод с {sell_exchange}: {with_status}")
                        if liquidity.sell_liquidity.withdraw_min > 0:
                            print(f"      Мин. вывод: {liquidity.sell_liquidity.withdraw_min}")
                        if liquidity.sell_liquidity.withdraw_fee > 0:
                            print(f"      Комиссия вывода: {liquidity.sell_liquidity.withdraw_fee}")
                    
                    print(f"   ⏱️ Ожидаемое время: ~{liquidity.estimated_time} мин")
                    print(f"   🎯 Уровень риска: {liquidity.risk_level.upper()}")
                else:
                    print(f"   ❌ НЕДОСТУПНО для арбитража")
                    
                    if liquidity.buy_liquidity and not liquidity.buy_liquidity.deposit_enabled:
                        print(f"      Проблема: депозиты отключены на {buy_exchange}")
                    
                    if liquidity.sell_liquidity and not liquidity.sell_liquidity.withdraw_enabled:
                        print(f"      Проблема: выводы отключены на {sell_exchange}")
                
            except Exception as e:
                print(f"   ❌ Ошибка проверки: {e}")
            
            print()  # Пустая строка для разделения
        
        # Итоговая статистика
        print("=" * 60)
        print(f"📈 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"   Всего проверено: {total_count}")
        print(f"   Доступно для арбитража: {viable_count}")
        print(f"   Процент доступности: {(viable_count/total_count)*100:.1f}%")
        
        # Статистика кеша
        summary = await checker.get_liquidity_summary()
        print(f"\n💾 СТАТИСТИКА КЕША:")
        print(f"   Записей в кеше: {summary['total_checked']}")
        print(f"   Доступных пар: {summary['viable_pairs']}")
        print(f"   Низкий риск: {summary['low_risk']}")
        print(f"   Средний риск: {summary['medium_risk']}")
        print(f"   Высокий риск: {summary['high_risk']}")
        
        print(f"\n✅ Тестирование завершено успешно!")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False
    
    finally:
        await checker.close_session()
    
    return True

async def main():
    """Главная функция"""
    success = await test_liquidity_checker()
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())