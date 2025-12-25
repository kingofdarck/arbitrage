@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo 🚀 ДЕПЛОЙ ОБЪЕДИНЕННОЙ СИСТЕМЫ АРБИТРАЖА
echo ==========================================

:: Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python 3.8+
    pause
    exit /b 1
)
echo ✅ Python найден

:: Проверка pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip не найден!
    pause
    exit /b 1
)
echo ✅ pip найден

:: Проверка основных файлов
if not exist "unified_system.py" (
    echo ❌ unified_system.py не найден!
    pause
    exit /b 1
)
echo ✅ unified_system.py найден

if not exist "requirements.txt" (
    echo ❌ requirements.txt не найден!
    pause
    exit /b 1
)
echo ✅ requirements.txt найден

:: Меню выбора
:menu
echo.
echo Выберите способ деплоя:
echo 1) Локальная установка и тест
echo 2) Docker (требует Docker Desktop)
echo 3) Railway (рекомендуется)
echo 4) Render
echo 5) Проверка конфигурации
echo 6) Выход
echo.
set /p choice="Ваш выбор (1-6): "

if "%choice%"=="1" goto local_install
if "%choice%"=="2" goto docker_deploy
if "%choice%"=="3" goto railway_deploy
if "%choice%"=="4" goto render_deploy
if "%choice%"=="5" goto check_config
if "%choice%"=="6" goto exit
echo ❌ Неверный выбор
goto menu

:local_install
echo.
echo 📦 ЛОКАЛЬНАЯ УСТАНОВКА
echo =====================

:: Создание виртуального окружения
if not exist "venv" (
    echo 🔧 Создание виртуального окружения...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Ошибка создания виртуального окружения
        pause
        goto menu
    )
)

:: Активация виртуального окружения
echo 🔧 Активация виртуального окружения...
call venv\Scripts\activate.bat

:: Обновление pip
echo 🔧 Обновление pip...
python -m pip install --upgrade pip

:: Установка зависимостей
echo 📦 Установка основных зависимостей...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Ошибка установки основных зависимостей
    pause
    goto menu
)

:: Установка дополнительных зависимостей
if exist "auto_arbitrage_bot\requirements.txt" (
    echo 📦 Установка дополнительных зависимостей...
    pip install -r auto_arbitrage_bot\requirements.txt
)

:: Установка пакетов для объединенной системы
echo 📦 Установка пакетов для объединенной системы...
pip install aiohttp python-telegram-bot ccxt python-dotenv

echo ✅ Зависимости установлены

:: Проверка конфигурации
call :check_env_file

:: Тестовый запуск
echo 🧪 Тестовый запуск (30 секунд)...
timeout /t 30 /nobreak python unified_system.py >nul 2>&1

echo ✅ Локальная установка завершена
echo 💡 Для запуска используйте: venv\Scripts\activate.bat && python unified_system.py
pause
goto menu

:docker_deploy
echo.
echo 🐳 DOCKER ДЕПЛОЙ
echo ===============

:: Проверка Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker не найден! Установите Docker Desktop
    pause
    goto menu
)
echo ✅ Docker найден

:: Проверка конфигурации
call :check_env_file

:: Сборка образа
echo 🔧 Сборка Docker образа...
docker build -f Dockerfile.unified -t unified-arbitrage-system .
if errorlevel 1 (
    echo ❌ Ошибка сборки образа
    pause
    goto menu
)

:: Остановка существующего контейнера
docker stop unified-arbitrage >nul 2>&1
docker rm unified-arbitrage >nul 2>&1

:: Запуск контейнера
echo 🚀 Запуск Docker контейнера...
docker run -d ^
    --name unified-arbitrage ^
    --restart unless-stopped ^
    -p 8080:8080 ^
    -v "%cd%\logs:/app/logs" ^
    -v "%cd%\data:/app/data" ^
    --env-file auto_arbitrage_bot\.env ^
    unified-arbitrage-system

if errorlevel 1 (
    echo ❌ Ошибка запуска контейнера
    pause
    goto menu
)

echo ✅ Docker контейнер запущен
echo 💡 Проверьте статус: docker logs unified-arbitrage
echo 💡 Health check: http://localhost:8080/health
pause
goto menu

:railway_deploy
echo.
echo 🚂 RAILWAY ДЕПЛОЙ
echo =================

:: Проверка Railway CLI
railway --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Railway CLI не найден!
    echo 💡 Установите: npm install -g @railway/cli
    echo 💡 Или используйте веб-интерфейс Railway
    pause
    goto menu
)
echo ✅ Railway CLI найден

:: Проверка конфигурации
call :check_env_file

:: Копирование конфигурации
echo 🔧 Подготовка конфигурации...
copy railway.unified.json railway.json >nul
copy Dockerfile.unified Dockerfile >nul

echo 🔑 Войдите в Railway...
railway login

echo 🔧 Инициализация проекта...
railway init

echo 🔧 Установка переменных окружения...
echo ⚠️ Установите переменные окружения вручную в Railway Dashboard
echo 💡 Или используйте: railway variables set KEY=VALUE

echo 🚀 Деплой на Railway...
railway up

echo ✅ Деплой на Railway завершен
echo 💡 Проверьте статус в Railway Dashboard
pause
goto menu

:render_deploy
echo.
echo 🎨 RENDER ДЕПЛОЙ
echo ================

:: Копирование конфигурации
echo 🔧 Подготовка конфигурации...
copy render.unified.yaml render.yaml >nul

echo ✅ Конфигурация Render подготовлена
echo.
echo 📋 СЛЕДУЮЩИЕ ШАГИ:
echo 1. Загрузите код в GitHub репозиторий
echo 2. Подключите репозиторий в Render Dashboard
echo 3. Выберите render.yaml как конфигурацию
echo 4. Добавьте переменные окружения в Render:

call :show_env_vars

pause
goto menu

:check_config
echo.
echo 🔍 ПРОВЕРКА КОНФИГУРАЦИИ
echo ========================

call :check_env_file

:: Проверка основных файлов
set files=unified_system.py smart_arbitrage_monitor.py persistent_bot.py config.py notifications.py
for %%f in (%files%) do (
    if exist "%%f" (
        echo ✅ %%f найден
    ) else (
        echo ❌ %%f отсутствует
    )
)

echo.
echo 📊 СТРУКТУРА ПРОЕКТА:
dir /b *.py | findstr /v __pycache__

pause
goto menu

:check_env_file
echo 🔍 Проверка .env файла...
if exist "auto_arbitrage_bot\.env" (
    echo ✅ .env файл найден
    
    :: Проверка критических переменных
    findstr /c:"BYBIT_API_KEY=ВСТАВЬТЕ" auto_arbitrage_bot\.env >nul
    if not errorlevel 1 (
        echo ⚠️ API ключи Bybit не настроены!
        echo 💡 Отредактируйте auto_arbitrage_bot\.env
    ) else (
        echo ✅ API ключи Bybit настроены
    )
    
    findstr /c:"TELEGRAM_BOT_TOKEN=" auto_arbitrage_bot\.env >nul
    if not errorlevel 1 (
        echo ✅ Telegram токен найден
    ) else (
        echo ⚠️ Telegram токен не найден
    )
) else (
    echo ❌ .env файл не найден
    echo 💡 Создайте auto_arbitrage_bot\.env на основе .env.example
)
goto :eof

:show_env_vars
if exist "auto_arbitrage_bot\.env" (
    echo.
    echo 🔑 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:
    type auto_arbitrage_bot\.env | findstr /v "^#" | findstr /v "^$"
)
goto :eof

:exit
echo 👋 До свидания!
pause
exit /b 0