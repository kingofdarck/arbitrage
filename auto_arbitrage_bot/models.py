#!/usr/bin/env python3
"""
Модели данных для арбитражной системы
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List
from enum import Enum

class TradingMode(Enum):
    """Режимы торговли"""
    TEST = "test"           # Тестовый режим (без реальных сделок)
    PAPER = "paper"         # Бумажная торговля
    LIVE = "live"           # Реальная торговля

class ArbitrageType(Enum):
    """Типы арбитража"""
    CROSS_EXCHANGE = "cross_exchange"    # Межбиржевой
    TRIANGULAR = "triangular"            # Треугольный
    STATISTICAL = "statistical"          # Статистический

@dataclass
class ArbitrageOpportunity:
    """Арбитражная возможность"""
    type: ArbitrageType
    symbol: str
    profit_percent: float
    profit_usd: float
    exchanges: List[str]
    prices: Dict[str, float]
    volumes: Dict[str, float]
    timestamp: datetime
    confidence: float
    risk_score: float
    
    def __str__(self):
        return f"{self.type.value}: {self.symbol} - {self.profit_percent:.2f}% (${self.profit_usd:.2f})"