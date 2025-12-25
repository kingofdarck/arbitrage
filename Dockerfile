# Dockerfile для треугольного арбитража
FROM python:3.11-slim

# Создаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir \
    ccxt==4.1.64 \
    python-telegram-bot==20.7 \
    python-dotenv==1.0.0

# Копируем файлы
COPY triangular_arbitrage_bot.py .
COPY main.py .
COPY .env .

# Переменные окружения
ENV PYTHONUNBUFFERED=1

# Команда запуска
CMD ["python", "main.py"]