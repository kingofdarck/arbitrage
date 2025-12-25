#!/usr/bin/env python3
"""
Исправление и проверка API ключей
Помогает пользователю правильно настроить ключи
"""

import os
import sys
from pathlib import Path

# Добавляем путь к модулям
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def check_env_file():
    """Проверка .env файла"""
    env_path = current_dir / '.env'
    
    print("🔍 ПРОВЕРКА .ENV ФАЙЛА")
    print("=" * 50)
    
    if not env_path.exists():
        print("❌ .env файл не найден!")
        return False
    
    print(f"✅ .env файл найден: {env_path}")
    
    # Читаем содержимое
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем ключи
    lines = content.split('\n')
    api_keys = {}
    
    for line in lines:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            if 'API_KEY' in key or 'SECRET' in key or 'PASSPHRASE' in key:
                api_keys[key] = value
    
    print(f"\n📋 НАЙДЕННЫЕ API КЛЮЧИ:")
    for key, value in api_keys.items():
        if value and value != 'your_' + key.lower():
            print(f"✅ {key}: {value[:10]}... (длина: {len(value)})")
        else:
            print(f"❌ {key}: не настроен")
    
    return True

def analyze_bybit_keys():
    """Анализ ключей Bybit"""
    print("\n🔵 АНАЛИЗ КЛЮЧЕЙ BYBIT")
    print("=" * 50)
    
    # Загружаем переменные окружения
    try:
        from dotenv import load_dotenv
        env_path = current_dir / '.env'
        if env_path.exists():
            load_dotenv(env_path)
    except ImportError:
        pass
    
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    
    print(f"API Key: '{api_key}'")
    print(f"Secret: '{api_secret}'")
    
    if not api_key or not api_secret:
        print("❌ Ключи не найдены в переменных окружения")
        return False
    
    # Анализ формата
    print(f"\n📏 АНАЛИЗ ФОРМАТА:")
    print(f"API Key длина: {len(api_key)} (должно быть 20-30)")
    print(f"Secret длина: {len(api_secret)} (должно быть 40-50)")
    
    # Проверка символов
    print(f"API Key содержит только буквы/цифры: {api_key.isalnum()}")
    print(f"Secret содержит только буквы/цифры: {api_secret.isalnum()}")
    
    # Рекомендации
    issues = []
    if len(api_key) < 20:
        issues.append("API Key слишком короткий")
    if len(api_secret) < 30:
        issues.append("Secret слишком короткий")
    if not api_key.isalnum():
        issues.append("API Key содержит недопустимые символы")
    if not api_secret.isalnum():
        issues.append("Secret содержит недопустимые символы")
    
    if issues:
        print(f"\n⚠️ ОБНАРУЖЕННЫЕ ПРОБЛЕМЫ:")
        for issue in issues:
            print(f"   - {issue}")
        
        print(f"\n🔧 РЕКОМЕНДАЦИИ:")
        print("1. Зайдите на https://www.bybit.com/app/user/api-management")
        print("2. Создайте новый API ключ")
        print("3. Убедитесь что выбраны права: 'Spot Trading'")
        print("4. Скопируйте ключи ТОЧНО как показано")
        print("5. Обновите .env файл")
        
        return False
    else:
        print("✅ Формат ключей выглядит корректно")
        return True

def create_new_env_template():
    """Создание шаблона .env с правильными ключами"""
    print("\n📝 СОЗДАНИЕ ШАБЛОНА .ENV")
    print("=" * 50)
    
    template = """# Режим торговли: test, paper, live
TRADING_MODE=test

# Отладка
DEBUG=true

# Настройки арбитража
MIN_PROFIT_THRESHOLD=0.75
MAX_POSITION_SIZE=50.0

# Telegram уведомления
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=8512825754:AAFfsMd5T2vrNeR9vCCzkCJSp9FhMe_7wHU
TELEGRAM_CHAT_ID=884434550

# Bybit API (ОСНОВНАЯ БИРЖА)
BYBIT_ENABLED=true
BYBIT_API_KEY=ВСТАВЬТЕ_ВАШ_BYBIT_API_KEY_ЗДЕСЬ
BYBIT_API_SECRET=ВСТАВЬТЕ_ВАШ_BYBIT_SECRET_ЗДЕСЬ
BYBIT_SANDBOX=true

# KuCoin API (ДОПОЛНИТЕЛЬНАЯ)
KUCOIN_ENABLED=false
KUCOIN_API_KEY=ВСТАВЬТЕ_ВАШ_KUCOIN_API_KEY_ЗДЕСЬ
KUCOIN_API_SECRET=ВСТАВЬТЕ_ВАШ_KUCOIN_SECRET_ЗДЕСЬ
KUCOIN_PASSPHRASE=ВСТАВЬТЕ_ВАШ_KUCOIN_PASSPHRASE_ЗДЕСЬ
KUCOIN_SANDBOX=false

# MEXC API (ДОПОЛНИТЕЛЬНАЯ)
MEXC_ENABLED=false
MEXC_API_KEY=ВСТАВЬТЕ_ВАШ_MEXC_API_KEY_ЗДЕСЬ
MEXC_API_SECRET=ВСТАВЬТЕ_ВАШ_MEXC_SECRET_ЗДЕСЬ
MEXC_SANDBOX=false
"""
    
    env_path = current_dir / '.env.new'
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(template)
    
    print(f"✅ Создан шаблон: {env_path}")
    print("\n📋 ИНСТРУКЦИИ:")
    print("1. Откройте файл .env.new")
    print("2. Замените ВСТАВЬТЕ_ВАШ_... на реальные ключи")
    print("3. Переименуйте .env.new в .env")
    print("4. Запустите тест снова")

def main():
    """Главная функция"""
    print("🔧 ИСПРАВЛЕНИЕ API КЛЮЧЕЙ")
    print("=" * 60)
    
    # Проверяем .env файл
    if not check_env_file():
        create_new_env_template()
        return
    
    # Анализируем ключи Bybit
    if not analyze_bybit_keys():
        print("\n💡 СОВЕТ: Попробуйте использовать публичный API без ключей")
        print("Установите BYBIT_API_KEY= (пустое значение) для публичного доступа")
    
    print("\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Исправьте API ключи если нужно")
    print("2. Запустите: python debug_api_keys.py")
    print("3. Если ключи работают, запустите: python ultra_fast_triangular.py")

if __name__ == "__main__":
    main()