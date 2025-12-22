#!/usr/bin/env python3
"""
Тест умного арбитражного монитора
"""

import asyncio
import logging
from smart_arbitrage_monitor import SmartArbitrageMonitor

# Настройка логирования для тестирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def test_smart_monitor():
    """Тестирование умного монитора"""
    print("🧪 Тестирование умного арбитражного монитора...")
    
    monitor = SmartArbitrageMonitor()
    
    try:
        # Инициализируем сессию
        await monitor.start_session()
        
        print("📡 Получение данных с бирж...")
        await monitor.fetch_all_exchange_data()
        
        if not monitor.all_pairs:
            print("❌ Не удалось получить данные с бирж")
            return
        
        total_pairs = sum(len(pairs) for pairs in monitor.all_pairs.values())
        print(f"✅ Получено {total_pairs} торговых пар с {len(monitor.all_pairs)} бирж")
        
        # Тестируем поиск возможностей
        print("🔍 Поиск межбиржевых возможностей...")
        cross_opportunities = monitor.find_cross_exchange_arbitrage()
        print(f"📊 Найдено {len(cross_opportunities)} межбиржевых возможностей")
        
        # Показываем топ-5
        if cross_opportunities:
            print("\n🏆 Топ-5 межбиржевых возможностей:")
            for i, opp in enumerate(cross_opportunities[:5], 1):
                details = opp.details
                print(f"  {i}. {details['symbol']}: {opp.profit_percent:.2f}% "
                      f"({details['buy_exchange']} → {details['sell_exchange']})")
        
        # Тестируем треугольный арбитраж
        print("\n🔺 Поиск треугольных возможностей...")
        triangular_opportunities = []
        for exchange in list(monitor.all_pairs.keys())[:2]:  # Тестируем только 2 биржи
            exchange_triangular = monitor.find_triangular_arbitrage(exchange)
            triangular_opportunities.extend(exchange_triangular)
            print(f"📊 {exchange}: найдено {len(exchange_triangular)} треугольных возможностей")
        
        # Показываем топ треугольных
        if triangular_opportunities:
            print("\n🏆 Топ-3 треугольных возможности:")
            for i, opp in enumerate(triangular_opportunities[:3], 1):
                details = opp.details
                print(f"  {i}. {details['exchange']}: {opp.profit_percent:.2f}% "
                      f"({details['path']})")
        
        # Тестируем систему отслеживания
        print("\n🧠 Тестирование системы отслеживания...")
        all_opportunities = cross_opportunities + triangular_opportunities
        
        # Фильтруем качественные возможности
        quality_opportunities = [
            opp for opp in all_opportunities 
            if opp.profit_percent >= 0.5 and opp.confidence >= 0.3
        ]
        
        print(f"📈 Качественных возможностей: {len(quality_opportunities)}")
        
        # Тестируем определение новых возможностей
        new_count = 0
        for opp in quality_opportunities[:10]:  # Тестируем первые 10
            is_new = monitor.is_opportunity_new(opp)
            if is_new:
                new_count += 1
                monitor.update_tracked_opportunity(opp, True)
        
        print(f"🆕 Новых возможностей: {new_count}")
        print(f"🔍 Отслеживается: {len(monitor.tracked_opportunities)} возможностей")
        
        # Тестируем генерацию хешей
        if quality_opportunities:
            test_opp = quality_opportunities[0]
            opp_hash = monitor.generate_opportunity_hash(test_opp)
            print(f"🔑 Пример хеша возможности: {opp_hash}")
        
        print("\n✅ Тестирование завершено успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await monitor.close_session()

async def main():
    """Главная функция тестирования"""
    await test_smart_monitor()

if __name__ == "__main__":
    asyncio.run(main())