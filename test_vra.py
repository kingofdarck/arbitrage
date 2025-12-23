#!/usr/bin/env python3
import asyncio
from liquidity_checker import LiquidityChecker

async def test_vra():
    checker = LiquidityChecker()
    await checker.start_session()
    
    liquidity = await checker.check_arbitrage_liquidity('VRAUSDT', 'binance', 'kucoin')
    
    print(f'VRA результат: {checker.format_liquidity_info(liquidity)}')
    print(f'Доступно для арбитража: {liquidity.is_viable}')
    
    if liquidity.buy_liquidity:
        print(f'Депозит на Binance: {"✅" if liquidity.buy_liquidity.deposit_enabled else "❌"}')
    
    if liquidity.sell_liquidity:
        print(f'Вывод с KuCoin: {"✅" if liquidity.sell_liquidity.withdraw_enabled else "❌"}')
    
    await checker.close_session()

asyncio.run(test_vra())