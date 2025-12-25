# 📈 Стратегии арбитража

## Обзор стратегий

Система поддерживает два основных типа арбитража:

1. **Межбиржевой арбитраж** - использование ценовых различий между биржами
2. **Треугольный арбитраж** - использование несоответствий курсов внутри одной биржи

## 🔄 Межбиржевой арбитраж

### Принцип работы
1. Мониторинг цен одного актива на разных биржах
2. Покупка на бирже с низкой ценой
3. Продажа на бирже с высокой ценой
4. Получение прибыли от разности цен

### Пример
```
BTC/USDT на Binance: $45,000 (покупка)
BTC/USDT на Bybit: $45,500 (продажа)
Потенциальная прибыль: $500 (1.11%)
```

### Алгоритм поиска
```python
for symbol in all_symbols:
    for buy_exchange, sell_exchange in exchange_pairs:
        buy_price = get_ask_price(buy_exchange, symbol)
        sell_price = get_bid_price(sell_exchange, symbol)
        
        profit_percent = (sell_price - buy_price) / buy_price * 100
        
        if profit_percent > min_threshold:
            create_opportunity(symbol, buy_exchange, sell_exchange, profit_percent)
```

### Факторы риска
- **Время исполнения** - цены могут измениться
- **Комиссии** - снижают прибыль
- **Ликвидность** - недостаток объема
- **Переводы** - время и комиссии за переводы между биржами

### Настройки
```python
# В config.py
CROSS_EXCHANGE_CONFIG = {
    'min_profit_threshold': 0.75,  # Минимальная прибыль %
    'max_slippage': 0.1,           # Максимальное проскальзывание %
    'min_volume': 1000,            # Минимальный объем USD
    'timeout_seconds': 30          # Таймаут исполнения
}
```

## 🔺 Треугольный арбитраж

### Принцип работы
1. Поиск несоответствий в курсах трех валют
2. Выполнение цепочки из 3 сделок
3. Возврат к исходной валюте с прибылью

### Пример
```
Начальная сумма: 1000 USDT

1. USDT → BTC: 1000 USDT / 45000 = 0.0222 BTC
2. BTC → ETH: 0.0222 BTC * 15 = 0.333 ETH  
3. ETH → USDT: 0.333 ETH * 3050 = 1015.65 USDT

Прибыль: 15.65 USDT (1.565%)
```

### Алгоритм поиска
```python
def find_triangular_opportunities():
    for base1 in base_currencies:
        for base2 in base_currencies:
            for quote in quote_currencies:
                if base1 != base2:
                    # Проверяем треугольник: base1/quote -> base1/base2 -> base2/quote
                    profit = calculate_triangle_profit(base1, base2, quote)
                    if profit > min_threshold:
                        create_triangle_opportunity(base1, base2, quote, profit)
```

### Типы треугольников
1. **Прямой треугольник**: A/C → A/B → B/C
2. **Обратный треугольник**: A/C → B/A → B/C
3. **Смешанный треугольник**: различные комбинации

### Поддерживаемые валюты
```python
BASE_CURRENCIES = [
    'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 
    'AVAX', 'MATIC', 'LINK', 'UNI', 'LTC', 'BCH'
]

QUOTE_CURRENCIES = ['USDT', 'BUSD', 'USDC']
```

### Настройки
```python
TRIANGULAR_CONFIG = {
    'min_profit_threshold': 0.75,  # Минимальная прибыль %
    'max_execution_time': 10,      # Максимальное время исполнения
    'min_volume_per_pair': 500,    # Минимальный объем на пару
    'max_triangles_per_scan': 100  # Максимум треугольников за сканирование
}
```

## 📊 Оценка возможностей

### Система скоринга
Каждая возможность оценивается по нескольким критериям:

```python
def calculate_opportunity_score(opportunity):
    score = 0
    
    # Прибыльность (40%)
    profit_score = min(opportunity.profit_percent / 2.0, 1.0) * 0.4
    
    # Уверенность (30%)
    confidence_score = opportunity.confidence * 0.3
    
    # Ликвидность (20%)
    liquidity_score = min(opportunity.min_volume / 10000, 1.0) * 0.2
    
    # Скорость исполнения (10%)
    speed_score = (1.0 - opportunity.estimated_execution_time / 30) * 0.1
    
    return profit_score + confidence_score + liquidity_score + speed_score
```

### Фильтрация возможностей
```python
def filter_opportunities(opportunities):
    filtered = []
    
    for opp in opportunities:
        # Минимальная прибыль
        if opp.profit_percent < config.min_profit_threshold:
            continue
            
        # Максимальный риск
        if opp.risk_score > 0.7:
            continue
            
        # Минимальная уверенность
        if opp.confidence < 0.5:
            continue
            
        # Проверка ликвидности
        if not check_liquidity(opp):
            continue
            
        filtered.append(opp)
    
    # Сортировка по скорингу
    return sorted(filtered, key=lambda x: x.score, reverse=True)
```

## ⚡ Исполнение стратегий

### Межбиржевой арбитраж
```python
async def execute_cross_exchange(opportunity):
    buy_exchange = opportunity.exchanges[0]
    sell_exchange = opportunity.exchanges[1]
    
    # Одновременное исполнение
    buy_task = place_buy_order(buy_exchange, opportunity.symbol, amount)
    sell_task = place_sell_order(sell_exchange, opportunity.symbol, amount)
    
    buy_result, sell_result = await asyncio.gather(buy_task, sell_task)
    
    return calculate_final_profit(buy_result, sell_result)
```

### Треугольный арбитраж
```python
async def execute_triangular(opportunity):
    exchange = opportunity.exchanges[0]
    pairs = opportunity.symbol.split('->')
    
    current_amount = initial_amount
    
    # Последовательное исполнение
    for i, pair in enumerate(pairs):
        side = determine_order_side(i, pair)
        result = await place_order(exchange, pair, side, current_amount)
        current_amount = result.filled_amount
    
    return calculate_triangle_profit(initial_amount, current_amount)
```

## 🎯 Оптимизация стратегий

### Параллельное исполнение
- Одновременные ордеры для межбиржевого арбитража
- Предварительная подготовка ордеров
- Использование WebSocket для быстрых данных

### Управление ликвидностью
- Проверка глубины стакана
- Разбиение крупных ордеров
- Мониторинг проскальзывания

### Адаптивные пороги
```python
def adaptive_threshold(market_volatility, success_rate):
    base_threshold = 0.75
    
    # Увеличиваем порог при высокой волатильности
    volatility_adjustment = market_volatility * 0.5
    
    # Уменьшаем порог при высокой успешности
    success_adjustment = (success_rate - 0.8) * 0.2
    
    return base_threshold + volatility_adjustment - success_adjustment
```

## 📈 Мониторинг производительности

### Ключевые метрики
- **Успешность исполнения** - % успешных сделок
- **Средняя прибыль** - средняя прибыль на сделку
- **Время исполнения** - среднее время исполнения
- **Проскальзывание** - отклонение от ожидаемых цен

### Логирование
```python
def log_strategy_performance(strategy_name, result):
    logger.info(f"Strategy: {strategy_name}")
    logger.info(f"Success: {result.success}")
    logger.info(f"Profit: ${result.profit_usd:.2f} ({result.profit_percent:.2f}%)")
    logger.info(f"Execution time: {result.execution_time:.2f}s")
    logger.info(f"Slippage: {result.slippage:.3f}%")
```

## 🔧 Настройка и тюнинг

### Файл конфигурации стратегий
```python
# strategies_config.py
STRATEGY_CONFIG = {
    'cross_exchange': {
        'enabled': True,
        'min_profit_threshold': 0.75,
        'max_position_size': 1000,
        'timeout_seconds': 30,
        'max_slippage': 0.1
    },
    'triangular': {
        'enabled': True,
        'min_profit_threshold': 0.75,
        'max_execution_time': 10,
        'max_triangles_per_scan': 100,
        'base_currencies': ['BTC', 'ETH', 'BNB'],
        'quote_currencies': ['USDT']
    }
}
```

### A/B тестирование
- Тестирование разных параметров
- Сравнение производительности
- Постепенное внедрение изменений

## 🚨 Предупреждения

1. **Рыночные риски** - цены могут измениться во время исполнения
2. **Технические риски** - сбои API, проблемы с сетью
3. **Ликвидные риски** - недостаток объема для исполнения
4. **Регуляторные риски** - изменения в правилах бирж

## 📚 Дополнительные ресурсы

- [Управление рисками](risk_management.md)
- [API документация](api.md)
- [Примеры использования](examples.md)
- [Часто задаваемые вопросы](faq.md)