"""
Конфигурационный файл для арбитражного монитора
"""

# Настройки мониторинга - АГРЕССИВНЫЕ для максимального покрытия
MONITORING_CONFIG = {
    'check_interval': 5,  # Проверка каждые 5 секунд (было 10)
    'min_profit_threshold': 3,  # Минимальная прибыль остается 0.75%
    'max_opportunities_per_notification': 25,  # Больше возможностей в уведомлении (было 15)
    'check_liquidity': True,  # Проверка ликвидности депозитов/выводов
}

# Настройки бирж - СНИЖЕНЫ требования для большего покрытия
EXCHANGES = {
    'binance': {
        'name': 'Binance',
        'api_url': 'https://api.binance.com/api/v3/ticker/price',
        'fee': 0.1,  # Комиссия в %
        'enabled': True,
        'min_volume': 10000  # Снижено с 100k до 10k
    },
    'bybit': {
        'name': 'Bybit',
        'api_url': 'https://api.bybit.com/v5/market/tickers',
        'fee': 0.1,
        'enabled': True,
        'min_volume': 5000  # Снижено с 50k до 5k
    },
    'okx': {
        'name': 'OKX',
        'api_url': 'https://www.okx.com/api/v5/market/tickers',
        'fee': 0.1,
        'enabled': True,
        'min_volume': 5000  # Снижено с 50k до 5k
    },
    'kucoin': {
        'name': 'KuCoin', 
        'api_url': 'https://api.kucoin.com/api/v1/market/allTickers',
        'fee': 0.1,
        'enabled': True,
        'min_volume': 3000  # Снижено с 30k до 3k
    },
    'mexc': {
        'name': 'MEXC',
        'api_url': 'https://api.mexc.com/api/v3/ticker/24hr',
        'fee': 0.2,
        'enabled': True,
        'min_volume': 2000  # Снижено с 20k до 2k
    },
    'bitget': {
        'name': 'Bitget',
        'api_url': 'https://api.bitget.com/api/spot/v1/market/tickers',
        'fee': 0.1,
        'enabled': True,
        'min_volume': 2000  # Снижено с 20k до 2k
    },
    'coinbase': {
        'name': 'Coinbase Pro',
        'api_url': 'https://api.exchange.coinbase.com/products/stats',
        'fee': 0.5,
        'enabled': True,  # ВКЛЮЧАЕМ для большего покрытия
        'min_volume': 10000  # Снижено с 100k до 10k
    },
    'kraken': {
        'name': 'Kraken',
        'api_url': 'https://api.kraken.com/0/public/Ticker',
        'fee': 0.26,
        'enabled': True,  # ВКЛЮЧАЕМ для большего покрытия
        'min_volume': 5000  # Снижено с 50k до 5k
    }
}

# Торговые пары для мониторинга - УБИРАЕМ ОГРАНИЧЕНИЯ, мониторим ВСЕ
TRADING_PAIRS = []  # Будет заполняться автоматически ВСЕМИ доступными парами

# Базовые валюты для фильтрации - РАСШИРЯЕМ список
BASE_CURRENCIES = ['USDT', 'USDC', 'BUSD', 'DAI', 'BTC', 'ETH', 'BNB', 'FDUSD', 'TUSD', 'USDD']

# Минимальные требования для включения пары в мониторинг - СНИЖАЕМ для большего покрытия
PAIR_FILTERS = {
    'min_volume_24h': 1000,        # Снижено с 50k до 1k USD
    'min_price': 0.000001,         # Снижено для включения мелких токенов
    'max_price': 10000000,         # Увеличено
    'exclude_patterns': ['UP', 'DOWN', 'BEAR', 'BULL'],  # Убираем часть исключений
    'max_profit_threshold': 100.0, # Увеличено с 50% до 100% для включения больше возможностей
}

# УБИРАЕМ белый список - мониторим ВСЕ пары, которые проходят фильтры
# Белый список отключен для максимального покрытия
WHITELIST_PAIRS = []  # Пустой список = мониторим все доступные пары

# Настройки арбитража - ТОЛЬКО ТРЕУГОЛЬНЫЙ
ARBITRAGE_CONFIG = {
    'cross_exchange': {
        'enabled': False,  # ОТКЛЮЧЕН - убираем межбиржевой арбитраж
        'min_profit': 0.75,
        'min_confidence': 0.1
    },
    'triangular': {
        'enabled': True,   # ЕДИНСТВЕННЫЙ АКТИВНЫЙ ТИП
        'min_profit': 0.75,  # Остается 0.75%
        'min_confidence': 0.1  # Снижено с 0.3 до 0.1
    },
    # ОТКЛЮЧАЕМ остальные типы арбитража
    'statistical': {
        'enabled': False,
        'min_profit': 0.75,
        'min_confidence': 0.2,
        'correlation_threshold': 0.6,
        'z_score_threshold': 1.5
    },
    'temporal': {
        'enabled': False,
        'min_profit': 0.75,
        'min_confidence': 0.1,
        'max_time_lag': 120
    },
    'spread': {
        'enabled': False,
        'min_profit': 0.75,
        'min_confidence': 0.2
    },
    'liquidity': {
        'enabled': False,
        'min_profit': 0.75,
        'min_confidence': 0.3,
        'min_volume': 500
    },
    'index': {
        'enabled': False,
        'min_profit': 0.75,
        'min_confidence': 0.2
    },
    'staking': {
        'enabled': False,
        'min_profit': 0.75,
        'min_confidence': 0.3
    },
    'funding': {
        'enabled': False,
        'min_profit': 0.75,
        'min_confidence': 0.4
    }
}

# Треугольные наборы - АВТОМАТИЧЕСКАЯ ГЕНЕРАЦИЯ всех возможных комбинаций
# Будет заполняться динамически из всех доступных валют
TRIANGULAR_SETS = []  # Будет генерироваться автоматически

# Функция для генерации всех треугольных комбинаций
def generate_all_triangular_sets(available_currencies):
    """Генерирует все возможные треугольные комбинации из доступных валют"""
    triangular_sets = []
    currencies = list(available_currencies)
    
    # Генерируем все комбинации из 3 валют
    for i in range(len(currencies)):
        for j in range(i + 1, len(currencies)):
            for k in range(j + 1, len(currencies)):
                # Добавляем все возможные перестановки
                triangular_sets.extend([
                    (currencies[i], currencies[j], currencies[k]),
                    (currencies[i], currencies[k], currencies[j]),
                    (currencies[j], currencies[i], currencies[k]),
                    (currencies[j], currencies[k], currencies[i]),
                    (currencies[k], currencies[i], currencies[j]),
                    (currencies[k], currencies[j], currencies[i])
                ])
    
    # Убираем дубликаты
    return list(set(triangular_sets))

# Основные валюты для треугольного арбитража (будет расширяться автоматически)
TRIANGULAR_BASE_CURRENCIES = [
    'BTC', 'ETH', 'BNB', 'USDT', 'USDC', 'BUSD', 'DAI',
    'ADA', 'SOL', 'MATIC', 'DOT', 'LINK', 'AVAX', 'UNI',
    'XRP', 'LTC', 'BCH', 'ETC', 'ATOM', 'NEAR', 'FTM',
    'ALGO', 'VET', 'ICP', 'THETA', 'FIL', 'TRX', 'EOS',
    'XLM', 'AAVE', 'MKR', 'COMP', 'YFI', 'SUSHI', 'CRV',
    'SNX', 'BAL', 'REN', 'KNC', 'LRC', 'ZRX', 'BAND',
    'STORJ', 'BAT', 'ENJ', 'MANA', 'SAND', 'AXS', 'GALA'
]

# Индексные токены и их составляющие
INDEX_COMPOSITIONS = {
    'DPI': {
        'name': 'DeFi Pulse Index',
        'components': {
            'UNI': 0.15, 'AAVE': 0.12, 'SNX': 0.10, 'MKR': 0.10,
            'COMP': 0.08, 'BAL': 0.07, 'YFI': 0.06, 'REN': 0.05,
            'KNC': 0.04, 'LRC': 0.03, 'SUSHI': 0.05, 'CRV': 0.05,
            'BADGER': 0.03, 'FLX': 0.02, 'INDEX': 0.05
        }
    },
    'MVI': {
        'name': 'Metaverse Index',
        'components': {
            'AXS': 0.20, 'MANA': 0.15, 'SAND': 0.12, 'ILV': 0.10,
            'ENJ': 0.08, 'GALA': 0.07, 'ALICE': 0.06, 'BOSON': 0.05,
            'REVV': 0.04, 'STARL': 0.03, 'SUPER': 0.05, 'TVK': 0.05
        }
    }
}

# Стейкинг пары и их параметры
STAKING_PAIRS = {
    'STETH': {
        'base_token': 'ETH',
        'annual_rate': 4.0,
        'risk_level': 'low',
        'liquidity': 'high'
    },
    'RETH': {
        'base_token': 'ETH', 
        'annual_rate': 4.2,
        'risk_level': 'low',
        'liquidity': 'medium'
    },
    'BETH': {
        'base_token': 'ETH',
        'annual_rate': 3.8,
        'risk_level': 'low',
        'liquidity': 'high'
    },
    'STMATIC': {
        'base_token': 'MATIC',
        'annual_rate': 8.0,
        'risk_level': 'medium',
        'liquidity': 'medium'
    },
    'STBNB': {
        'base_token': 'BNB',
        'annual_rate': 6.0,
        'risk_level': 'low',
        'liquidity': 'high'
    },
    'STSOL': {
        'base_token': 'SOL',
        'annual_rate': 7.0,
        'risk_level': 'medium',
        'liquidity': 'medium'
    }
}

# Корреляционные пары для статистического арбитража
CORRELATION_PAIRS = [
    ('BTCUSDT', 'ETHUSDT'),
    ('ETHUSDT', 'BNBUSDT'),
    ('ADAUSDT', 'DOTUSDT'),
    ('LINKUSDT', 'UNIUSDT'),
    ('SOLUSDT', 'AVAXUSDT'),
    ('MATICUSDT', 'FTMUSDT'),
    ('ATOMUSDT', 'LUNAUSDT'),
    ('NEARUSDT', 'ALGOUSDT')
]

# Настройки уведомлений
NOTIFICATION_CONFIG = {
    'telegram': {
        'enabled': True,  # Включаем Telegram
        'bot_token': '8565304713:AAFpnuNkp4QR6Yk9H-5NoN8l3Z1pN2WigKQ',  # Ваш токен бота
        'chat_id': '884434550',    # Ваш chat_id
    },
    'discord': {
        'enabled': False,
        'webhook_url': '',  # Вставьте URL Discord webhook
    },
    'email': {
        'enabled': False,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': '',
        'password': '',
        'to_email': ''
    }
}

# Настройки логирования
LOGGING_CONFIG = {
    'level': 'INFO',
    'file': 'arbitrage.log',
    'max_file_size': 10 * 1024 * 1024,  # 10 MB
    'backup_count': 5
}