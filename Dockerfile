FROM python:3.11-slim

WORKDIR /app

# Устанавливаем зависимости
RUN pip install ccxt==4.1.64 python-telegram-bot==20.7 python-dotenv==1.0.0

# Копируем файлы
COPY simple_railway_bot.py main.py .env ./

# Переменные окружения
ENV PYTHONUNBUFFERED=1

# Запуск
CMD ["python", "main.py"]