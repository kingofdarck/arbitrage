# 📦 Установка и настройка

## Системные требования

- **Python 3.9+** - основной язык программирования
- **pip** - менеджер пакетов Python
- **Git** - для клонирования репозитория
- **4GB RAM** - минимальные требования к памяти
- **Стабильное интернет-соединение** - для работы с биржами

## Быстрая установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/your-repo/auto-arbitrage-bot.git
cd auto-arbitrage-bot
```

### 2. Создание виртуального окружения
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Настройка конфигурации
```bash
# Создание файла переменных окружения
cp .env.example .env

# Редактирование конфигурации
nano .env
```

## Настройка переменных окружения

Создайте файл `.env` в корневой директории:

```env
# Режим торговли
TRADING_MODE=test  # test, paper, live

# Настройки арбитража
MIN_PROFIT_THRESHOLD=0.75
MAX_POSITION_SIZE=1000.0
MAX_SLIPPAGE=0.1
TIMEOUT_SECONDS=30

# Настройки рисков
MAX_DAILY_LOSS=100.0
MAX_POSITION_COUNT=5
STOP_LOSS_PERCENT=2.0
TAKE_PROFIT_PERCENT=5.0
MAX_DRAWDOWN_PERCENT=10.0

# Telegram уведомления
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# API ключи бирж (см. следующий раздел)
```

## Настройка API ключей бирж

### Binance
```env
BINANCE_ENABLED=true
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
BINANCE_SANDBOX=true  # false для боевого режима
```

### Bybit
```env
BYBIT_ENABLED=true
BYBIT_API_KEY=your_api_key
BYBIT_API_SECRET=your_api_secret
BYBIT_SANDBOX=true
```

### KuCoin
```env
KUCOIN_ENABLED=true
KUCOIN_API_KEY=your_api_key
KUCOIN_API_SECRET=your_api_secret
KUCOIN_PASSPHRASE=your_passphrase
KUCOIN_SANDBOX=true
```

### MEXC
```env
MEXC_ENABLED=true
MEXC_API_KEY=your_api_key
MEXC_API_SECRET=your_api_secret
MEXC_SANDBOX=true
```

### OKX
```env
OKX_ENABLED=true
OKX_API_KEY=your_api_key
OKX_API_SECRET=your_api_secret
OKX_PASSPHRASE=your_passphrase
OKX_SANDBOX=true
```

### Coinbase
```env
COINBASE_ENABLED=true
COINBASE_API_KEY=your_api_key
COINBASE_API_SECRET=your_api_secret
COINBASE_PASSPHRASE=your_passphrase
COINBASE_SANDBOX=true
```

## Получение API ключей

### 🔐 Важные правила безопасности:
1. **Никогда не делитесь API ключами**
2. **Используйте только необходимые разрешения**
3. **Начинайте с sandbox/testnet режима**
4. **Регулярно обновляйте ключи**

### Binance
1. Войдите в [Binance](https://www.binance.com)
2. Перейдите в API Management
3. Создайте новый API ключ
4. Включите только "Enable Spot & Margin Trading"
5. Добавьте IP-адрес сервера (рекомендуется)

### Bybit
1. Войдите в [Bybit](https://www.bybit.com)
2. Перейдите в API Management
3. Создайте новый API ключ
4. Выберите "Spot Trading" разрешения

### KuCoin
1. Войдите в [KuCoin](https://www.kucoin.com)
2. Перейдите в API Management
3. Создайте новый API ключ
4. Установите passphrase
5. Включите "Trade" разрешения

## Первый запуск

### Тестовый режим
```bash
python main.py --mode=test
```

### Проверка конфигурации
```bash
python -c "from config import config; print('Конфигурация корректна' if not config.validate() else 'Ошибки в конфигурации')"
```

### Проверка подключения к биржам
```bash
python -c "
import asyncio
from core.exchange_manager import ExchangeManager

async def test():
    em = ExchangeManager()
    await em.initialize()
    exchanges = await em.test_connections()
    print(f'Подключенные биржи: {exchanges}')

asyncio.run(test())
"
```

## Структура проекта после установки

```
auto_arbitrage_bot/
├── core/                   # Основная логика
├── exchanges/              # Адаптеры бирж
├── strategies/             # Стратегии арбитража
├── utils/                  # Утилиты
├── tests/                  # Тесты
├── docs/                   # Документация
├── data/                   # База данных
├── logs/                   # Логи
├── main.py                 # Точка входа
├── config.py               # Конфигурация
├── requirements.txt        # Зависимости
└── .env                    # Переменные окружения
```

## Устранение проблем

### Ошибка импорта модулей
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Ошибки подключения к биржам
1. Проверьте API ключи
2. Убедитесь что IP разрешен
3. Проверьте интернет-соединение
4. Используйте sandbox режим для тестов

### Ошибки разрешений
```bash
chmod +x main.py
```

## Следующие шаги

1. [Настройка бирж](exchanges.md)
2. [Конфигурация стратегий](strategies.md)
3. [Управление рисками](risk_management.md)
4. [Запуск в продакшене](deployment.md)