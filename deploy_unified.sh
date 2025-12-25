#!/bin/bash

# Скрипт деплоя объединенной системы арбитража
# Поддерживает Railway, Render, Docker, VPS

set -e

echo "🚀 ДЕПЛОЙ ОБЪЕДИНЕННОЙ СИСТЕМЫ АРБИТРАЖА"
echo "=========================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода цветного текста
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Проверка зависимостей
check_dependencies() {
    print_info "Проверка зависимостей..."
    
    # Проверяем Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 не найден!"
        exit 1
    fi
    print_status "Python3 найден: $(python3 --version)"
    
    # Проверяем pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 не найден!"
        exit 1
    fi
    print_status "pip3 найден"
    
    # Проверяем Git
    if ! command -v git &> /dev/null; then
        print_warning "Git не найден - некоторые функции могут быть недоступны"
    else
        print_status "Git найден"
    fi
}

# Проверка конфигурации
check_config() {
    print_info "Проверка конфигурации..."
    
    # Проверяем .env файл
    if [ -f "auto_arbitrage_bot/.env" ]; then
        print_status "Найден .env файл"
        
        # Проверяем критические переменные
        if grep -q "BYBIT_API_KEY=ВСТАВЬТЕ" auto_arbitrage_bot/.env; then
            print_warning "API ключи Bybit не настроены!"
            echo "Отредактируйте auto_arbitrage_bot/.env и укажите реальные ключи"
        else
            print_status "API ключи Bybit настроены"
        fi
        
        if grep -q "TELEGRAM_BOT_TOKEN=" auto_arbitrage_bot/.env; then
            print_status "Telegram токен найден"
        else
            print_warning "Telegram токен не найден"
        fi
    else
        print_warning ".env файл не найден"
        echo "Создайте auto_arbitrage_bot/.env на основе .env.example"
    fi
    
    # Проверяем основные файлы
    required_files=(
        "unified_system.py"
        "smart_arbitrage_monitor.py"
        "persistent_bot.py"
        "config.py"
        "notifications.py"
        "requirements.txt"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            print_status "Найден $file"
        else
            print_error "Отсутствует $file"
            exit 1
        fi
    done
}

# Локальная установка зависимостей
install_local() {
    print_info "Установка зависимостей локально..."
    
    # Создаем виртуальное окружение если его нет
    if [ ! -d "venv" ]; then
        print_info "Создание виртуального окружения..."
        python3 -m venv venv
    fi
    
    # Активируем виртуальное окружение
    source venv/bin/activate
    
    # Обновляем pip
    pip install --upgrade pip
    
    # Устанавливаем зависимости
    print_info "Установка основных зависимостей..."
    pip install -r requirements.txt
    
    # Устанавливаем дополнительные зависимости
    if [ -f "auto_arbitrage_bot/requirements.txt" ]; then
        print_info "Установка дополнительных зависимостей..."
        pip install -r auto_arbitrage_bot/requirements.txt || true
    fi
    
    # Устанавливаем пакеты для объединенной системы
    print_info "Установка пакетов для объединенной системы..."
    pip install aiohttp python-telegram-bot ccxt python-dotenv
    
    print_status "Зависимости установлены"
}

# Тестовый запуск
test_run() {
    print_info "Тестовый запуск системы..."
    
    # Активируем виртуальное окружение
    source venv/bin/activate
    
    # Запускаем систему в тестовом режиме на 30 секунд
    timeout 30s python unified_system.py || true
    
    print_status "Тестовый запуск завершен"
}

# Docker деплой
deploy_docker() {
    print_info "Деплой через Docker..."
    
    # Проверяем Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker не найден!"
        return 1
    fi
    
    # Строим образ
    print_info "Сборка Docker образа..."
    docker build -f Dockerfile.unified -t unified-arbitrage-system .
    
    # Запускаем контейнер
    print_info "Запуск Docker контейнера..."
    docker run -d \
        --name unified-arbitrage \
        --restart unless-stopped \
        -p 8080:8080 \
        -v $(pwd)/logs:/app/logs \
        -v $(pwd)/data:/app/data \
        --env-file auto_arbitrage_bot/.env \
        unified-arbitrage-system
    
    print_status "Docker контейнер запущен"
    print_info "Проверьте статус: docker logs unified-arbitrage"
    print_info "Health check: http://localhost:8080/health"
}

# Docker Compose деплой
deploy_docker_compose() {
    print_info "Деплой через Docker Compose..."
    
    # Проверяем Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose не найден!"
        return 1
    fi
    
    # Копируем переменные окружения
    if [ -f "auto_arbitrage_bot/.env" ]; then
        cp auto_arbitrage_bot/.env .env
        print_status "Переменные окружения скопированы"
    fi
    
    # Запускаем через Docker Compose
    print_info "Запуск через Docker Compose..."
    if command -v docker-compose &> /dev/null; then
        docker-compose -f docker-compose.unified.yml up -d
    else
        docker compose -f docker-compose.unified.yml up -d
    fi
    
    print_status "Docker Compose запущен"
    print_info "Проверьте статус: docker-compose -f docker-compose.unified.yml logs"
    print_info "Health check: http://localhost:8080/health"
}

# Railway деплой
deploy_railway() {
    print_info "Подготовка к деплою на Railway..."
    
    # Проверяем Railway CLI
    if ! command -v railway &> /dev/null; then
        print_warning "Railway CLI не найден"
        print_info "Установите: npm install -g @railway/cli"
        print_info "Или используйте веб-интерфейс Railway"
        return 1
    fi
    
    # Копируем конфигурацию
    cp railway.unified.json railway.json
    cp Dockerfile.unified Dockerfile
    
    print_info "Инициализация Railway проекта..."
    railway login
    railway init
    
    # Устанавливаем переменные окружения
    if [ -f "auto_arbitrage_bot/.env" ]; then
        print_info "Установка переменных окружения..."
        while IFS='=' read -r key value; do
            if [[ ! $key =~ ^#.*$ ]] && [[ $key != "" ]]; then
                railway variables set "$key=$value"
            fi
        done < auto_arbitrage_bot/.env
    fi
    
    print_info "Деплой на Railway..."
    railway up
    
    print_status "Деплой на Railway завершен"
    print_info "Проверьте статус в Railway Dashboard"
}

# Render деплой
deploy_render() {
    print_info "Подготовка к деплою на Render..."
    
    # Копируем конфигурацию
    cp render.unified.yaml render.yaml
    
    print_status "Конфигурация Render подготовлена"
    print_info "Следующие шаги:"
    echo "1. Загрузите код в GitHub репозиторий"
    echo "2. Подключите репозиторий в Render Dashboard"
    echo "3. Добавьте переменные окружения в Render"
    echo "4. Запустите деплой"
    
    # Показываем переменные окружения
    if [ -f "auto_arbitrage_bot/.env" ]; then
        print_info "Переменные окружения для Render:"
        grep -v '^#' auto_arbitrage_bot/.env | grep -v '^$'
    fi
}

# Heroku деплой
deploy_heroku() {
    print_info "Подготовка к деплою на Heroku..."
    
    # Проверяем Heroku CLI
    if ! command -v heroku &> /dev/null; then
        print_warning "Heroku CLI не найден"
        print_info "Установите: https://devcenter.heroku.com/articles/heroku-cli"
        return 1
    fi
    
    # Копируем конфигурацию
    cp Procfile.unified Procfile
    cp app.unified.json app.json
    
    print_info "Создание Heroku приложения..."
    heroku create unified-arbitrage-$(date +%s)
    
    # Устанавливаем переменные окружения
    if [ -f "auto_arbitrage_bot/.env" ]; then
        print_info "Установка переменных окружения..."
        while IFS='=' read -r key value; do
            if [[ ! $key =~ ^#.*$ ]] && [[ $key != "" ]]; then
                heroku config:set "$key=$value"
            fi
        done < auto_arbitrage_bot/.env
    fi
    
    print_info "Деплой на Heroku..."
    git add .
    git commit -m "Deploy unified arbitrage system" || true
    git push heroku main
    
    print_status "Деплой на Heroku завершен"
    print_info "Проверьте статус: heroku logs --tail"
}

# Главное меню
show_menu() {
    echo ""
    echo "Выберите способ деплоя:"
    echo "1) Локальная установка и тест"
    echo "2) Docker"
    echo "3) Docker Compose"
    echo "4) Railway (рекомендуется)"
    echo "5) Render"
    echo "6) Heroku"
    echo "7) Проверка конфигурации"
    echo "8) Выход"
    echo ""
}

# Основная логика
main() {
    check_dependencies
    
    while true; do
        show_menu
        read -p "Ваш выбор (1-8): " choice
        
        case $choice in
            1)
                check_config
                install_local
                test_run
                ;;
            2)
                check_config
                deploy_docker
                ;;
            3)
                check_config
                deploy_docker_compose
                ;;
            4)
                check_config
                deploy_railway
                ;;
            5)
                check_config
                deploy_render
                ;;
            6)
                check_config
                deploy_heroku
                ;;
            7)
                check_config
                ;;
            8)
                print_info "До свидания!"
                exit 0
                ;;
            *)
                print_error "Неверный выбор. Попробуйте снова."
                ;;
        esac
        
        echo ""
        read -p "Нажмите Enter для продолжения..."
    done
}

# Запуск
main "$@"