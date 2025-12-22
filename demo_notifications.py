#!/usr/bin/env python3
"""
Демонстрация раздельных уведомлений для разных типов арбитража
"""

from datetime import datetime
from smart_arbitrage_monitor import SmartArbitrageMonitor, ArbitrageOpportunity

def create_demo_cross_exchange_opportunity():
    """Создание демо межбиржевой возможности"""
    return ArbitrageOpportunity(
        type='cross_exchange',
        profit_percent=1.25,
        confidence=0.85,
        details={
            'symbol': 'BTCUSDT',
            'buy_exchange': 'kucoin',
            'sell_exchange': 'binance',
            'buy_price': 43250.50,
            'sell_price': 43895.20,
            'buy_volume_24h': 2450000,
            'sell_volume_24h': 15200000,
            'fees': {'buy': 0.1, 'sell': 0.1, 'total': 0.2}
        },
        timestamp=datetime.now()
    )

def create_demo_triangular_opportunity():
    """Создание демо треугольной возможности"""
    return ArbitrageOpportunity(
        type='triangular',
        profit_percent=0.95,
        confidence=0.78,
        details={
            'exchange': 'binance',
            'direction': 'forward',
            'path': 'USDT->BTC->ETH->USDT',
            'pairs': ['BTCUSDT', 'ETHBTC', 'ETHUSDT'],
            'prices': [43250.50, 0.0578, 2495.30],
            'volumes': [15200000, 8500000, 12300000],
            'calculation': '1 / 43250.50 * 0.0578 * 2495.30 = 1.0095',
            'fee_per_trade': 0.1,
            'total_fees': 0.3
        },
        timestamp=datetime.now()
    )

async def demo_notifications():
    """Демонстрация раздельных уведомлений"""
    print("📱 Демонстрация раздельных уведомлений")
    print("=" * 50)
    
    monitor = SmartArbitrageMonitor()
    
    # Создаем демо возможности
    cross_opp = create_demo_cross_exchange_opportunity()
    triangular_opp = create_demo_triangular_opportunity()
    
    # Демонстрируем межбиржевое уведомление
    print("\n🚨 ПРИМЕР: Межбиржевой арбитраж")
    print("-" * 40)
    cross_message = monitor.format_cross_exchange_message([cross_opp])
    print(cross_message)
    
    # Демонстрируем треугольное уведомление
    print("\n\n🔺 ПРИМЕР: Треугольный арбитраж")
    print("-" * 40)
    triangular_message = monitor.format_triangular_message([triangular_opp])
    print(triangular_message)
    
    print("\n" + "=" * 50)
    print("✅ Теперь каждый тип арбитража отправляется отдельным сообщением!")
    print("📊 Минимальная прибыль для всех типов: 0.75%")

if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_notifications())