#!/usr/bin/env python3
"""
Тестирование проблемных токенов для проверки точности модуля ликвидности
"""

import asyncio
import sys
from liquidity_checker import LiquidityChecker

async def test_problematic_tokens():
    """Тестирование проблемных токенов"""
    print("🔍 Тестирование проблемных токенов...")
    
    checker = LiquidityChecker()
    await checker.start_session()
    
    try:
        # Тестируем известные проблемные токены
        problematic_cases = [
            ('VRAUSDT', 'binance', 'kucoin'),  # VRA - известные проблемы с депозитами
            ('LUNCUSDT', 'binance', 'bybit'),  # LUNC - проблемы после коллапса Terra
            ('FTTUSDT', 'binance', 'okx'),     # FTT - проблемы после краха FTX
            ('SHIBUSDT', 'binance', 'mexc'),   # SHIB - иногда проблемы с сетями
            ('BTTCUSDT', 'binance', 'kucoin')  # BTTC - часто проблемы с депозитами
        ]
        
        # Тестируем надежные токены для сравнения
        reliable_cases = [
            ('BTCUSDT', 'binance', 'bybit'),   # BTC - всегда надежен
            ('ETHUSDT', 'okx', 'kucoin'),      # ETH - всегда надежен
            ('ADAUSDT', 'binance', 'mexc'),    # ADA - обычно надежен
        ]
        
        print(f"\n🔴 ПРОБЛЕМНЫЕ ТОКЕНЫ:\n")
        
        for i, (symbol, buy_exchange, sell_exchange) in enumerate(problematic_cases, 1):
            print(f"{i}. 🔍 {symbol}: {buy_exchange.upper()} → {sell_exchange.upper()}")
            
            try:
                liquidity = await checker.check_arbitrage_liquidity(symbol, buy_exchange, sell_exchange)
                
                status_info = checker.format_liquidity_info(liquidity)
                print(f"   Результат: {status_info}")
                
                if liquidity.is_viable:
                    print(f"   ⚠️ ВНИМАНИЕ: Система считает доступным, но может быть ошибка!")
                else:
                    print(f"   ✅ ПРАВИЛЬНО: Система корректно определила как недоступный")
                
                # Детали
                if liquidity.buy_liquidity:
                    dep_status = "✅" if liquidity.buy_liquidity.deposit_enabled else "❌"
                    print(f"   📥 Депозит на {buy_exchange}: {dep_status} (уверенность: {liquidity.buy_liquidity.confidence:.2f})")
                
                if liquidity.sell_liquidity:
                    with_status = "✅" if liquidity.sell_liquidity.withdraw_enabled else "❌"
                    print(f"   📤 Вывод с {sell_exchange}: {with_status} (уверенность: {liquidity.sell_liquidity.confidence:.2f})")
                
            except Exception as e:
                print(f"   ❌ Ошибка проверки: {e}")
            
            print()
        
        print(f"\n🟢 НАДЕЖНЫЕ ТОКЕНЫ:\n")
        
        for i, (symbol, buy_exchange, sell_exchange) in enumerate(reliable_cases, 1):
            print(f"{i}. 🔍 {symbol}: {buy_exchange.upper()} → {sell_exchange.upper()}")
            
            try:
                liquidity = await checker.check_arbitrage_liquidity(symbol, buy_exchange, sell_exchange)
                
                status_info = checker.format_liquidity_info(liquidity)
                print(f"   Результат: {status_info}")
                
                if liquidity.is_viable:
                    print(f"   ✅ ПРАВИЛЬНО: Надежный токен определен как доступный")
                else:
                    print(f"   ⚠️ ВНИМАНИЕ: Надежный токен определен как недоступный - возможна ошибка")
                
                # Детали
                if liquidity.buy_liquidity:
                    dep_status = "✅" if liquidity.buy_liquidity.deposit_enabled else "❌"
                    print(f"   📥 Депозит на {buy_exchange}: {dep_status} (уверенность: {liquidity.buy_liquidity.confidence:.2f})")
                
                if liquidity.sell_liquidity:
                    with_status = "✅" if liquidity.sell_liquidity.withdraw_enabled else "❌"
                    print(f"   📤 Вывод с {sell_exchange}: {with_status} (уверенность: {liquidity.sell_liquidity.confidence:.2f})")
                
            except Exception as e:
                print(f"   ❌ Ошибка проверки: {e}")
            
            print()
        
        # Итоговая статистика
        summary = await checker.get_liquidity_summary()
        print("=" * 60)
        print(f"📊 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"   Записей в кеше: {summary['total_checked']}")
        print(f"   Доступных пар: {summary['viable_pairs']}")
        print(f"   Низкий риск: {summary['low_risk']}")
        print(f"   Средний риск: {summary['medium_risk']}")
        print(f"   Высокий риск: {summary['high_risk']}")
        
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        print(f"   • Проблемные токены должны показывать ❌ или 🔴 HIGH риск")
        print(f"   • Надежные токены должны показывать ✅ или 🟢 LOW риск")
        print(f"   • При низкой уверенности (<0.5) лучше избегать арбитража")
        
        print(f"\n✅ Тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False
    
    finally:
        await checker.close_session()
    
    return True

async def main():
    """Главная функция"""
    success = await test_problematic_tokens()
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())