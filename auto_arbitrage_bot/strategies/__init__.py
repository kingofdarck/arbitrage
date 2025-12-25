"""
Стратегии арбитража
"""

from .cross_exchange import CrossExchangeStrategy
from .triangular import TriangularStrategy

__all__ = [
    'CrossExchangeStrategy',
    'TriangularStrategy'
]