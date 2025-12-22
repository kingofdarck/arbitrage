"""
Конфигурационный файл для арбитражного монитора
"""

# Настройки мониторинга
MONITORING_CONFIG = {
    'check_interval': 10,  # Интервал проверки в секундах
    'min_profit_threshold': 0.75,  # Минимальная прибыль в % (повышено до 0.75%)
    'max_opportunities_per_notification': 15,  # Максимум возможностей в одном уведомлении
}

# Настройки бирж
EXCHANGES = {
    'binance': {
        'name': 'Binance',
        'api_url': 'https://api.binance.com/api/v3/ticker/price',
        'fee': 0.1,  # Комиссия в %
        'enabled': True,
        'min_volume': 100000  # Минимальный объем торгов за 24ч в USDT
    },
    'bybit': {
        'name': 'Bybit',
        'api_url': 'https://api.bybit.com/v5/market/tickers',
        'fee': 0.1,
        'enabled': True,
        'min_volume': 50000
    },
    'okx': {
        'name': 'OKX',
        'api_url': 'https://www.okx.com/api/v5/market/tickers',
        'fee': 0.1,
        'enabled': True,
        'min_volume': 50000
    },
    'kucoin': {
        'name': 'KuCoin', 
        'api_url': 'https://api.kucoin.com/api/v1/market/allTickers',
        'fee': 0.1,
        'enabled': True,
        'min_volume': 30000
    },
    'mexc': {
        'name': 'MEXC',
        'api_url': 'https://api.mexc.com/api/v3/ticker/24hr',
        'fee': 0.2,
        'enabled': True,
        'min_volume': 20000
    },
    'bitget': {
        'name': 'Bitget',
        'api_url': 'https://api.bitget.com/api/spot/v1/market/tickers',
        'fee': 0.1,
        'enabled': True,
        'min_volume': 20000
    },
    'coinbase': {
        'name': 'Coinbase Pro',
        'api_url': 'https://api.exchange.coinbase.com/products/stats',
        'fee': 0.5,
        'enabled': False,  # Отключаем пока
        'min_volume': 100000
    },
    'kraken': {
        'name': 'Kraken',
        'api_url': 'https://api.kraken.com/0/public/Ticker',
        'fee': 0.26,
        'enabled': False,  # Отключаем пока
        'min_volume': 50000
    }
}

# Торговые пары для мониторинга - теперь динамически получаем все доступные
TRADING_PAIRS = []  # Будет заполняться автоматически

# Базовые валюты для фильтрации (основные стейблкоины и топ криптовалюты)
BASE_CURRENCIES = ['USDT', 'USDC', 'BUSD', 'DAI', 'BTC', 'ETH', 'BNB']

# Минимальные требования для включения пары в мониторинг
PAIR_FILTERS = {
    'min_volume_24h': 50000,       # Минимальный объем торгов за 24ч в USD (снижено до $50k)
    'min_price': 0.00001,          # Минимальная цена (исключаем токены по $0.000001)
    'max_price': 1000000,          # Максимальная цена
    'exclude_patterns': ['UP', 'DOWN', 'BEAR', 'BULL', '3L', '3S', 'HEDGE'],  # Исключаем левереджные токены
    'max_profit_threshold': 50.0,  # Максимальная прибыль для фильтрации скамов (50%)
}

# Белый список - только проверенные топ криптовалюты
WHITELIST_PAIRS = [
    # Топ-20 по капитализации
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'SOLUSDT',
    'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'TRXUSDT', 'LINKUSDT',
    'DOTUSDT', 'MATICUSDT', 'LTCUSDT', 'SHIBUSDT', 'UNIUSDT',
    'ATOMUSDT', 'ETCUSDT', 'XLMUSDT', 'BCHUSDT', 'FILUSDT',
    
    # Популярные DeFi токены
    'AAVEUSDT', 'MKRUSDT', 'COMPUSDT', 'YFIUSDT', 'SUSHIUSDT',
    'CRVUSDT', 'BALUSDT', 'SNXUSDT', 'RENUSDT', 'KNCUSDT',
    
    # Стейблкоины
    'USDCUSDT', 'BUSDUSDT', 'DAIUSDT', 'TUSDUSDT',
    
    # Кросс-пары с BTC
    'ETHBTC', 'BNBBTC', 'ADABTC', 'DOTBTC', 'LINKBTC',
    'LTCBTC', 'XRPBTC', 'SOLBTC', 'AVAXBTC', 'MATICBTC',
    
    # Кросс-пары с ETH  
    'BNBETH', 'ADAETH', 'DOTETH', 'LINKETH', 'LTCETH',
    'XRPETH', 'SOLETH', 'AVAXETH', 'MATICETH', 'UNIETH',
]

# Настройки арбитража
ARBITRAGE_CONFIG = {
    'cross_exchange': {
        'enabled': True,
        'min_profit': 0.75,  # Повышено до 0.75%
        'min_confidence': 0.3
    },
    'triangular': {
        'enabled': True,
        'min_profit': 0.75,  # Повышено до 0.75%
        'min_confidence': 0.3
    },
    'statistical': {
        'enabled': True,
        'min_profit': 0.75,  # Повышено до 0.75%
        'min_confidence': 0.5,
        'correlation_threshold': 0.8,
        'z_score_threshold': 2.0
    },
    'temporal': {
        'enabled': True,
        'min_profit': 0.75,  # Повышено до 0.75%
        'min_confidence': 0.2,
        'max_time_lag': 60  # секунды
    },
    'spread': {
        'enabled': True,
        'min_profit': 0.75,  # Повышено до 0.75%
        'min_confidence': 0.4
    },
    'liquidity': {
        'enabled': True,
        'min_profit': 0.75,  # Повышено до 0.75%
        'min_confidence': 0.6,
        'min_volume': 1000  # USD
    },
    'index': {
        'enabled': True,
        'min_profit': 0.75,  # Повышено до 0.75%
        'min_confidence': 0.4
    },
    'staking': {
        'enabled': True,
        'min_profit': 0.75,  # Повышено до 0.75%
        'min_confidence': 0.6
    },
    'funding': {
        'enabled': True,
        'min_profit': 0.75,  # Повышено до 0.75%
        'min_confidence': 0.7
    }
}

# Треугольные наборы - расширенный список для всех основных валют
TRIANGULAR_SETS = [
    # Основные с USDT
    ('BTC', 'ETH', 'USDT'), ('BTC', 'BNB', 'USDT'), ('ETH', 'BNB', 'USDT'),
    ('BTC', 'ADA', 'USDT'), ('ETH', 'ADA', 'USDT'), ('BNB', 'ADA', 'USDT'),
    ('BTC', 'SOL', 'USDT'), ('ETH', 'SOL', 'USDT'), ('BNB', 'SOL', 'USDT'),
    ('BTC', 'MATIC', 'USDT'), ('ETH', 'MATIC', 'USDT'), ('BNB', 'MATIC', 'USDT'),
    ('BTC', 'DOT', 'USDT'), ('ETH', 'DOT', 'USDT'), ('BNB', 'DOT', 'USDT'),
    ('BTC', 'LINK', 'USDT'), ('ETH', 'LINK', 'USDT'), ('BNB', 'LINK', 'USDT'),
    ('BTC', 'AVAX', 'USDT'), ('ETH', 'AVAX', 'USDT'), ('BNB', 'AVAX', 'USDT'),
    ('BTC', 'UNI', 'USDT'), ('ETH', 'UNI', 'USDT'), ('BNB', 'UNI', 'USDT'),
    
    # С USDC
    ('BTC', 'ETH', 'USDC'), ('BTC', 'BNB', 'USDC'), ('ETH', 'BNB', 'USDC'),
    ('BTC', 'SOL', 'USDC'), ('ETH', 'SOL', 'USDC'), ('BNB', 'SOL', 'USDC'),
    
    # Между топ криптовалютами
    ('BTC', 'ETH', 'BNB'), ('SOL', 'ADA', 'BTC'), ('ETH', 'SOL', 'BNB'),
    ('MATIC', 'DOT', 'ETH'), ('LINK', 'UNI', 'BTC'), ('AVAX', 'SOL', 'ETH'),
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
        'bot_token': '1373836655:AAGjxf5N0j2J4zFrafpHAxVg9s5PWGDHVh0',  # Ваш токен бота
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