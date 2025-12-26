# Dockerfile для Railway треугольного арбитража
FROM python:3.11-slim

# Создаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir \
    ccxt==4.1.64 \
    python-telegram-bot==20.7 \
    python-dotenv==1.0.0 \
    psutil==5.9.6

# Копируем файлы
COPY railway_bot.py .
COPY main.py .
COPY .env .

# Переменные окружения для Railway
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

# Команда запуска для Railway
CMD ["python", "main.py"]