# Dockerfile для автономного треугольного арбитража
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости с фиксированными версиями
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    ccxt==4.1.64 \
    python-telegram-bot==20.7 \
    python-dotenv==1.0.0 \
    psutil==5.9.6 \
    aiohttp==3.9.1

# Копируем файлы
COPY autonomous_arbitrage_bot.py .
COPY main.py .
COPY .env .

# Переменные окружения для Railway
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONIOENCODING=utf-8
ENV PORT=8080

# Добавляем health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# Команда запуска для Railway
CMD ["python", "main.py"]