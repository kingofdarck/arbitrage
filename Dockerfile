# Dockerfile для автономного треугольного арбитража
FROM python:3.11-slim

# Создаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости Python
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

# Команда запуска для Railway
CMD ["python", "main.py"]