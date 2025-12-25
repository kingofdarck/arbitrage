FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование и установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание директорий для логов и данных
RUN mkdir -p logs data

# Установка переменных окружения по умолчанию
ENV PYTHONUNBUFFERED=1
ENV TRADING_MODE=test
ENV MIN_PROFIT_THRESHOLD=0.5
ENV MAX_POSITION_SIZE=50.0

# Открытие порта для мониторинга (если нужно)
EXPOSE 8080

# Команда запуска
CMD ["python", "bybit_live_triangular.py"]