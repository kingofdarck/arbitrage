#!/bin/bash

# Скрипт быстрого деплоя треугольного арбитража
# Поддерживает Railway, Render, VPS, Docker

set -e

echo "🚀 ДЕПЛОЙ ТРЕУГОЛЬНОГО АРБИТРАЖА"
echo "================================="

# Проверка наличия .env файла
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден!"
    echo "📝 Создайте .env файл с вашими API ключами"
    echo "💡 Используйте .env.example как шаблон"
    exit 1
fi

# Проверка API ключей в .env
if ! grep -q "BYBIT_API_KEY=" .env || ! grep -q "BYBIT_API_SECRET=" .env; then
    echo "❌ API ключи не настроены в .env файле!"
    echo "📝 Добавьте BYBIT_API_KEY и BYBIT_API_SECRET"
    exit 1
fi

# Проверка что ключи не являются заглушками
if grep -q "ВСТАВЬТЕ" .env; then
    echo "❌ Замените заглушки в .env файле на реальные API ключи!"
    exit 1
fi

echo "✅ Конфигурация проверена"

# Меню выбора платформы деплоя
echo ""
echo "Выберите платформу для деплоя:"
echo "1) Railway (рекомендуется, бесплатно)"
echo "2) Render (бесплатно)"
echo "3) Docker (локально)"
echo "4) VPS (ручная настройка)"
echo "5) Heroku"
echo ""
read -p "Введите номер (1-5): " choice

case $choice in
    1)
        echo "🚂 Деплой на Railway"
        echo "1. Загрузите код на GitHub"
        echo "2. Зайдите на https://railway.app"
        echo "3. Подключите GitHub репозиторий"
        echo "4. Добавьте переменные окружения из .env файла"
        echo "5. Railway автоматически запустит бота"
        echo ""
        echo "📋 Переменные для Railway:"
        echo "=========================="
        grep -E "^[A-Z_]+=.+" .env | sed 's/=.*/=***/' | head -10
        ;;
    
    2)
        echo "🎨 Деплой на Render"
        echo "1. Загрузите код на GitHub"
        echo "2. Зайдите на https://render.com"
        echo "3. Создайте новый Web Service из GitHub"
        echo "4. Используйте файл render.yaml для настройки"
        echo "5. Добавьте переменные окружения"
        ;;
    
    3)
        echo "🐳 Деплой через Docker"
        
        # Проверка Docker
        if ! command -v docker &> /dev/null; then
            echo "❌ Docker не установлен!"
            echo "📥 Установите Docker: https://docs.docker.com/get-docker/"
            exit 1
        fi
        
        echo "🔨 Сборка Docker образа..."
        docker build -t triangular-arbitrage .
        
        echo "🚀 Запуск контейнера..."
        docker run -d \
            --name triangular-arbitrage-bot \
            --env-file .env \
            --restart unless-stopped \
            -v $(pwd)/logs:/app/logs \
            triangular-arbitrage
        
        echo "✅ Бот запущен в Docker контейнере!"
        echo "📊 Просмотр логов: docker logs -f triangular-arbitrage-bot"
        echo "⏹️ Остановка: docker stop triangular-arbitrage-bot"
        ;;
    
    4)
        echo "🖥️ Настройка VPS"
        echo "Выполните следующие команды на вашем VPS:"
        echo ""
        echo "# Обновление системы"
        echo "sudo apt update && sudo apt upgrade -y"
        echo ""
        echo "# Установка зависимостей"
        echo "sudo apt install python3 python3-pip git screen -y"
        echo ""
        echo "# Клонирование репозитория"
        echo "git clone https://github.com/ваш-username/arbitrage-bot.git"
        echo "cd arbitrage-bot/auto_arbitrage_bot"
        echo ""
        echo "# Установка Python зависимостей"
        echo "pip3 install -r requirements.txt"
        echo ""
        echo "# Копирование .env файла на сервер"
        echo "# Затем запуск:"
        echo "screen -S arbitrage"
        echo "python3 bybit_live_triangular.py"
        ;;
    
    5)
        echo "🟣 Деплой на Heroku"
        echo "1. Установите Heroku CLI"
        echo "2. Выполните команды:"
        echo ""
        echo "heroku create ваше-имя-бота"
        echo "heroku config:set BYBIT_API_KEY=ваш_ключ"
        echo "heroku config:set BYBIT_API_SECRET=ваш_секрет"
        echo "heroku config:set TRADING_MODE=live"
        echo "git push heroku main"
        ;;
    
    *)
        echo "❌ Неверный выбор"
        exit 1
        ;;
esac

echo ""
echo "🎯 ВАЖНЫЕ НАПОМИНАНИЯ:"
echo "====================="
echo "1. 🔑 Убедитесь что API ключи правильные и активные"
echo "2. 💰 Проверьте баланс на Bybit перед запуском"
echo "3. 📊 Мониторьте логи первые дни работы"
echo "4. ⚠️ Начните с малых сумм для тестирования"
echo "5. 🛡️ Установите лимиты убытков"
echo ""
echo "✅ Деплой готов! Удачной торговли! 🚀"