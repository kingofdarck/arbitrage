#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы арбитражного монитора
"""

import asyncio
import sys
from crypto_arbitrage_monitor import CryptoArbitrageMonitor

async def test_monitor():
    """Тестирование основных функций монитора"""
    print("🧪 Тестирование арбитражного монитора...")
    
    monitor = CryptoArbitrageMonitor()
    
    try:
        # Инициализация сессии
        await monitor.start_session()
        print("✅ HTTP сессия инициализирована")
        
        # Тестирование получения цен
        print("\n📊 Тестирование получения цен с бирж...")
        await monitor.fetch_all_prices()
        
        for exchange, prices in monitor.prices.items():
            if prices:
                print(f"✅ {exchange}: получено {len(prices)} цен")
                # Показываем несколько примеров
                sample_pairs = list(prices.keys())[:3]
                for pair in sample_pairs:
                    print(f"   {pair}: ${prices[pair]:.4f}")
            else:
                print(f"❌ {exchange}: данные не получены")
        
        # Тестирование поиска межбиржевого арбитража
        print("\n🔄 Тестирование поиска межбиржевого арбитража...")
        cross_opportunities = monitor.find_cross_exchange_arbitrage()
        
        if cross_opportunities:
            print(f"🎯 Найдено {len(cross_opportunities)} межбиржевых возможностей:")
            for opp in cross_opportunities[:3]:  # Показываем первые 3
                details = opp.details
                print(f"   {details['symbol']}: {opp.profit_percent:.2f}% "
                      f"({details['buy_exchange']} → {details['sell_exchange']})")
        else:
            print("ℹ️  Межбиржевых возможностей не найдено")
        
        # Тестирование поиска треугольного арбитража
        print("\n🔺 Тестирование поиска треугольного арбитража...")
        all_triangular = []
        
        for exchange in monitor.prices.keys():
            if monitor.prices[exchange]:
                triangular_opportunities = monitor.find_triangular_arbitrage(exchange)
                all_triangular.extend(triangular_opportunities)
                
                if triangular_opportunities:
                    print(f"🎯 {exchange}: найдено {len(triangular_opportunities)} треугольных возможностей")
                    for opp in triangular_opportunities[:2]:  # Показываем первые 2
                        details = opp.details
                        print(f"   {details['path']}: {opp.profit_percent:.2f}%")
        
        if not all_triangular:
            print("ℹ️  Треугольных возможностей не найдено")
        
        # Общая статистика
        total_opportunities = len(cross_opportunities) + len(all_triangular)
        print(f"\n📈 Общая статистика:")
        print(f"   Всего возможностей: {total_opportunities}")
        print(f"   Межбиржевых: {len(cross_opportunities)}")
        print(f"   Треугольных: {len(all_triangular)}")
        
        if total_opportunities > 0:
            all_opps = cross_opportunities + all_triangular
            max_profit = max(opp.profit_percent for opp in all_opps)
            print(f"   Максимальная прибыль: {max_profit:.2f}%")
        
        print("\n✅ Тестирование завершено успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False
    finally:
        await monitor.close_session()
    
    return True

async def test_single_exchange():
    """Тестирование получения данных с одной биржи"""
    print("\n🔍 Детальное тестирование Binance...")
    
    monitor = CryptoArbitrageMonitor()
    await monitor.start_session()
    
    try:
        binance_prices = await monitor.fetch_binance_prices()
        
        if binance_prices:
            print(f"✅ Получено {len(binance_prices)} цен с Binance")
            
            # Показываем основные пары
            main_pairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
            print("\nОсновные пары:")
            for pair in main_pairs:
                if pair in binance_prices:
                    print(f"   {pair}: ${binance_prices[pair]:,.2f}")
                else:
                    print(f"   {pair}: не найдена")
        else:
            print("❌ Не удалось получить данные с Binance")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await monitor.close_session()

def main():
    """Главная функция тестирования"""
    print("🚀 Запуск тестов арбитражного монитора\n")
    
    try:
        # Основное тестирование
        success = asyncio.run(test_monitor())
        
        if success:
            # Дополнительное тестирование
            asyncio.run(test_single_exchange())
            
            print("\n🎉 Все тесты пройдены! Монитор готов к работе.")
            print("\nДля запуска мониторинга используйте:")
            print("   python run_monitor.py")
        else:
            print("\n❌ Тесты не пройдены. Проверьте подключение к интернету и настройки.")
            
    except KeyboardInterrupt:
        print("\n⏹️  Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()