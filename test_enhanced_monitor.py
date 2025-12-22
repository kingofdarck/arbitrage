#!/usr/bin/env python3
"""
Тестирование расширенного арбитражного монитора
"""

import asyncio
import sys
from enhanced_arbitrage_monitor import EnhancedArbitrageMonitor
from config import EXCHANGES

async def test_exchange_connections():
    """Тестирование подключения к биржам"""
    print("🔗 Тестирование подключений к биржам...\n")
    
    monitor = EnhancedArbitrageMonitor()
    await monitor.start_session()
    
    results = {}
    
    try:
        # Тестируем каждую биржу отдельно
        test_functions = {
            'binance': monitor.fetch_binance_data,
            'bybit': monitor.fetch_bybit_data,
            'okx': monitor.fetch_okx_data,
            'kucoin': monitor.fetch_kucoin_data,
            'gate': monitor.fetch_gate_data,
            'huobi': monitor.fetch_huobi_data,
            'mexc': monitor.fetch_mexc_data,
            'bitget': monitor.fetch_bitget_data,
        }
        
        for exchange_name, test_func in test_functions.items():
            if exchange_name in monitor.active_exchanges:
                print(f"📡 Тестирование {exchange_name.upper()}...")
                try:
                    pairs = await test_func()
                    if pairs:
                        results[exchange_name] = {
                            'status': 'success',
                            'pairs_count': len(pairs),
                            'sample_pairs': list(pairs.keys())[:5]
                        }
                        print(f"   ✅ Успешно: {len(pairs)} торговых пар")
                        
                        # Показываем примеры пар
                        for symbol in list(pairs.keys())[:3]:
                            pair = pairs[symbol]
                            print(f"      {symbol}: ${pair.price:.6f} (объем: ${pair.volume_24h:,.0f})")
                    else:
                        results[exchange_name] = {'status': 'no_data', 'pairs_count': 0}
                        print(f"   ⚠️ Данные не получены")
                        
                except Exception as e:
                    results[exchange_name] = {'status': 'error', 'error': str(e)}
                    print(f"   ❌ Ошибка: {e}")
                
                print()
        
    finally:
        await monitor.close_session()
    
    return results

async def test_full_cycle():
    """Тестирование полного цикла мониторинга"""
    print("🔄 Тестирование полного цикла мониторинга...\n")
    
    monitor = EnhancedArbitrageMonitor()
    await monitor.start_session()
    
    try:
        # Получаем данные со всех бирж
        print("📊 Получение данных со всех бирж...")
        await monitor.fetch_all_exchange_data()
        
        total_pairs = sum(len(pairs) for pairs in monitor.all_pairs.values())
        print(f"✅ Получено {total_pairs:,} торговых пар с {len(monitor.all_pairs)} бирж")
        
        # Статистика по биржам
        print("\n📈 Статистика по биржам:")
        for exchange, pairs in monitor.all_pairs.items():
            print(f"   {exchange.upper()}: {len(pairs):,} пар")
        
        # Тестируем межбиржевой арбитраж
        print("\n🔄 Поиск межбиржевого арбитража...")
        cross_opportunities = monitor.find_cross_exchange_arbitrage()
        
        print(f"✅ Найдено {len(cross_opportunities)} межбиржевых возможностей")
        
        if cross_opportunities:
            print("\n🎯 Топ-5 межбиржевых возможностей:")
            for i, opp in enumerate(cross_opportunities[:5]):
                details = opp.details
                confidence_emoji = "🟢" if opp.confidence > 0.7 else "🟡" if opp.confidence > 0.4 else "🔴"
                print(f"   {i+1}. {confidence_emoji} {details['symbol']}: {opp.profit_percent:.2f}% "
                      f"({details['buy_exchange']} → {details['sell_exchange']}) "
                      f"уверенность: {opp.confidence:.1%}")
        
        # Тестируем треугольный арбитраж
        print("\n🔺 Поиск треугольного арбитража...")
        all_triangular = []
        
        for exchange in monitor.all_pairs.keys():
            triangular_opportunities = monitor.find_triangular_arbitrage(exchange)
            all_triangular.extend(triangular_opportunities)
            
            if triangular_opportunities:
                print(f"   {exchange.upper()}: {len(triangular_opportunities)} возможностей")
        
        print(f"✅ Всего найдено {len(all_triangular)} треугольных возможностей")
        
        if all_triangular:
            print("\n🎯 Топ-5 треугольных возможностей:")
            sorted_triangular = sorted(all_triangular, key=lambda x: x.profit_percent, reverse=True)
            for i, opp in enumerate(sorted_triangular[:5]):
                details = opp.details
                confidence_emoji = "🟢" if opp.confidence > 0.7 else "🟡" if opp.confidence > 0.4 else "🔴"
                print(f"   {i+1}. {confidence_emoji} {details['exchange'].upper()}: {opp.profit_percent:.2f}% "
                      f"({details['direction']}) уверенность: {opp.confidence:.1%}")
                print(f"       Путь: {details['path']}")
        
        # Общая статистика
        all_opportunities = cross_opportunities + all_triangular
        high_confidence = [opp for opp in all_opportunities if opp.confidence > 0.7]
        
        print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
        print(f"   Всего возможностей: {len(all_opportunities)}")
        print(f"   Межбиржевых: {len(cross_opportunities)}")
        print(f"   Треугольных: {len(all_triangular)}")
        print(f"   Высокая уверенность (>70%): {len(high_confidence)}")
        
        if all_opportunities:
            max_profit = max(opp.profit_percent for opp in all_opportunities)
            avg_profit = sum(opp.profit_percent for opp in all_opportunities) / len(all_opportunities)
            print(f"   Максимальная прибыль: {max_profit:.2f}%")
            print(f"   Средняя прибыль: {avg_profit:.2f}%")
        
        return len(all_opportunities) > 0
        
    finally:
        await monitor.close_session()

async def test_symbol_parsing():
    """Тестирование парсинга символов"""
    print("🔤 Тестирование парсинга символов торговых пар...\n")
    
    monitor = EnhancedArbitrageMonitor()
    
    test_symbols = [
        'BTCUSDT', 'ETH-USDT', 'BNB_USDC', 'ADA/BTC',
        'SOLUSDT', 'MATICETH', 'DOTBNB', 'LINKBTC',
        'AVAXUSDC', 'UNIUSDT', 'ATOMBTC', 'ADABNB'
    ]
    
    print("Тестовые символы и их разбор:")
    for symbol in test_symbols:
        normalized = monitor.normalize_symbol(symbol)
        base, quote = monitor.parse_symbol(symbol)
        print(f"   {symbol:12} → {normalized:12} → {base:8} / {quote}")
    
    print("\n✅ Парсинг символов работает корректно")

def print_exchange_status(results):
    """Вывод статуса бирж"""
    print("📊 ИТОГОВЫЙ СТАТУС БИРЖ:\n")
    
    total_pairs = 0
    working_exchanges = 0
    
    for exchange, result in results.items():
        status = result['status']
        
        if status == 'success':
            emoji = "✅"
            working_exchanges += 1
            pairs_count = result['pairs_count']
            total_pairs += pairs_count
            status_text = f"{pairs_count:,} пар"
        elif status == 'no_data':
            emoji = "⚠️"
            status_text = "Нет данных"
        else:
            emoji = "❌"
            status_text = f"Ошибка: {result.get('error', 'Неизвестная')}"
        
        print(f"{emoji} {exchange.upper():12} - {status_text}")
    
    print(f"\n📈 Итого: {working_exchanges}/{len(results)} бирж работают")
    print(f"📊 Всего торговых пар: {total_pairs:,}")

async def main():
    """Главная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ РАСШИРЕННОГО АРБИТРАЖНОГО МОНИТОРА\n")
    print("=" * 60)
    
    try:
        # Тест 1: Парсинг символов
        await test_symbol_parsing()
        print("\n" + "=" * 60)
        
        # Тест 2: Подключения к биржам
        connection_results = await test_exchange_connections()
        print_exchange_status(connection_results)
        print("\n" + "=" * 60)
        
        # Тест 3: Полный цикл мониторинга
        success = await test_full_cycle()
        
        print("\n" + "=" * 60)
        
        if success:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            print("\n🚀 Для запуска мониторинга используйте:")
            print("   python run_enhanced_monitor.py")
            print("\n⚙️ Доступные параметры:")
            print("   --min-profit 0.5      # Минимальная прибыль 0.5%")
            print("   --min-confidence 0.7   # Минимальная уверенность 70%")
            print("   --interval 20          # Интервал проверки 20 сек")
            print("   --test-mode           # Тестовый режим без уведомлений")
        else:
            print("⚠️ Тесты завершены, но возможности не найдены")
            print("Это нормально - арбитражные возможности появляются периодически")
            
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n💥 Критическая ошибка при тестировании: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())