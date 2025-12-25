#!/usr/bin/env python3
"""
Демо режим - запуск без реальных бирж
"""

import sys
import asyncio
from pathlib import Path

# Добавляем путь к модулям
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

async def demo_arbitrage():
    """Демонстрация арбитража без реальных бирж"""
    print("🎮 ДЕМО РЕЖИМ АРБИТРАЖА")
    print("=" * 50)
    print("Симуляция работы без подключения к биржам")
    print("=" * 50)
    
    # Импортируем компоненты
    from models import ArbitrageType, ArbitrageOpportunity
    from datetime import datetime
    
    # Создаем фиктивные возможности арбитража
    opportunities = [
        ArbitrageOpportunity(
            type=ArbitrageType.CROSS_EXCHANGE,
            symbol='BTC/USDT',
            profit_percent=1.25,
            profit_usd=125.0,
            exchanges=['binance', 'bybit'],
            prices={'binance': 95000, 'bybit': 96187.5},
            volumes={'binance': 10000, 'bybit': 8500},
            timestamp=datetime.now(),
            confidence=0.85,
            risk_score=0.2
        ),
        ArbitrageOpportunity(
            type=ArbitrageType.TRIANGULAR,
            symbol='BTC/USDT->ETH/BTC->ETH/USDT',
            profit_percent=0.95,
            profit_usd=95.0,
            exchanges=['binance'],
            prices={'BTC/USDT': 95000, 'ETH/BTC': 0.035, 'ETH/USDT': 3325},
            volumes={'BTC/USDT': 5000, 'ETH/BTC': 2000, 'ETH/USDT': 7500},
            timestamp=datetime.now(),
            confidence=0.78,
            risk_score=0.35
        ),
        ArbitrageOpportunity(
            type=ArbitrageType.CROSS_EXCHANGE,
            symbol='ETH/USDT',
            profit_percent=0.87,
            profit_usd=87.0,
            exchanges=['okx', 'kucoin'],
            prices={'okx': 3320, 'kucoin': 3349},
            volumes={'okx': 15000, 'kucoin': 12000},
            timestamp=datetime.now(),
            confidence=0.92,
            risk_score=0.15
        )
    ]
    
    print("💡 Найденные возможности арбитража:")
    print()
    
    for i, opp in enumerate(opportunities, 1):
        emoji = "🔄" if opp.type == ArbitrageType.CROSS_EXCHANGE else "🔺"
        print(f"{emoji} Возможность {i}:")
        print(f"   Тип: {opp.type.value}")
        print(f"   Символ: {opp.symbol}")
        print(f"   Прибыль: {opp.profit_percent:.2f}% (${opp.profit_usd:.2f})")
        print(f"   Биржи: {', '.join(opp.exchanges)}")
        print(f"   Уверенность: {opp.confidence:.2f}")
        print(f"   Риск: {opp.risk_score:.2f}")
        print()
    
    print("⚡ Симуляция исполнения...")
    await asyncio.sleep(2)
    
    for i, opp in enumerate(opportunities, 1):
        print(f"🎯 Исполнение возможности {i}...")
        await asyncio.sleep(1)
        
        # Симуляция успешного исполнения
        success_rate = 0.8  # 80% успешности
        import random
        
        if random.random() < success_rate:
            actual_profit = opp.profit_usd * random.uniform(0.85, 0.95)  # Небольшое проскальзывание
            print(f"   ✅ Успешно! Прибыль: ${actual_profit:.2f}")
        else:
            print(f"   ❌ Неудачно (проскальзывание или изменение цены)")
        
        print()
    
    print("📊 Итоговая статистика:")
    total_profit = sum(opp.profit_usd for opp in opportunities) * 0.8 * 0.9  # 80% успешность * 90% от ожидаемой прибыли
    print(f"   Найдено возможностей: {len(opportunities)}")
    print(f"   Ожидаемая прибыль: ${sum(opp.profit_usd for opp in opportunities):.2f}")
    print(f"   Реальная прибыль: ${total_profit:.2f}")
    print(f"   Успешность: 80%")
    
    print("\n" + "=" * 50)
    print("🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!")
    print("\n📋 Для реальной работы:")
    print("1. Получите правильные API ключи бирж")
    print("2. Обновите .env файл")
    print("3. Запустите: python start.py")

async def main():
    """Главная функция"""
    try:
        await demo_arbitrage()
    except KeyboardInterrupt:
        print("\n⏹️ Демо остановлено пользователем")
    except Exception as e:
        print(f"❌ Ошибка в демо режиме: {e}")

if __name__ == "__main__":
    asyncio.run(main())