#!/bin/bash

# Скрипт для деплоя умного арбитражного монитора на VPS

echo "🧠 Деплой умного арбитражного монитора"
echo "======================================"

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Устанавливаем..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "✅ Docker установлен"
fi

# Проверяем наличие Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Устанавливаем..."
    sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose установлен"
fi

# Проверяем настройки Telegram
echo "🔍 Проверка настроек Telegram..."
if ! grep -q "1373836655:AAGjxf5N0j2J4zFrafpHAxVg9s5PWGDHVh0" config.py; then
    echo "⚠️  ВНИМАНИЕ: Проверьте настройки Telegram в config.py:"
    echo "   - bot_token: токен вашего бота"
    echo "   - chat_id: ID чата для уведомлений"
    echo ""
    read -p "Продолжить деплой? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Деплой отменен"
        exit 1
    fi
fi

# Создаем директории
echo "📁 Создание директорий..."
mkdir -p logs
chmod 755 logs

# Останавливаем старые контейнеры
echo "🛑 Остановка старых контейнеров..."
docker-compose down 2>/dev/null || true

echo "📦 Сборка Docker образа для умного монитора..."
docker-compose build --no-cache

echo "🚀 Запуск умного арбитражного монитора..."
docker-compose up -d

# Ждем запуска
echo "⏳ Ожидание запуска (30 секунд)..."
sleep 30

echo "📊 Проверка статуса контейнеров..."
docker-compose ps

echo ""
echo "📋 Последние логи умного монитора:"
echo "=================================="
docker-compose logs --tail=20 smart-arbitrage-monitor

echo ""
echo "✅ Деплой умного монитора завершен!"
echo ""
echo "🎯 Особенности умного монитора:"
echo "   📱 Раздельные уведомления по типам арбитража"
echo "   🧠 Только новые возможности (без дубликатов)"
echo "   📊 Минимальная прибыль: 0.75%"
echo "   ⏰ Проверка каждые 10 секунд"
echo ""
echo "📋 Команды для управления:"
echo "   Просмотр логов:     docker-compose logs -f smart-arbitrage-monitor"
echo "   Остановка:          docker-compose stop"
echo "   Перезапуск:         docker-compose restart smart-arbitrage-monitor"
echo "   Обновление:         git pull && docker-compose up -d --build"
echo "   Удаление:           docker-compose down"
echo ""
echo "🌐 Health check: http://localhost:8000"
echo "📱 Уведомления будут приходить в Telegram 24/7!"