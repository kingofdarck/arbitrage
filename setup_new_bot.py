#!/usr/bin/env python3
"""
Настройка нового бота - автоматическое обновление config.py
"""

import re

def setup_new_bot():
    """Интерактивная настройка нового бота"""
    print("🤖 НАСТРОЙКА НОВОГО БОТА")
    print("=" * 50)
    
    print("\n📋 Сначала создайте нового бота:")
    print("1. Откройте @BotFather в Telegram")
    print("2. Отправьте /newbot")
    print("3. Следуйте инструкциям")
    print("4. Получите токен бота")
    print("\n📱 Затем получите ваш Chat ID:")
    print("1. Откройте @userinfobot в Telegram")
    print("2. Отправьте любое сообщение")
    print("3. Скопируйте ваш Chat ID")
    
    print("\n" + "=" * 50)
    
    # Получаем данные от пользователя
    bot_token = input("🔑 Введите токен нового бота: ").strip()
    chat_id = input("💬 Введите ваш Chat ID: ").strip()
    
    # Валидация токена
    if not re.match(r'^\d+:[A-Za-z0-9_-]+$', bot_token):
        print("❌ Неправильный формат токена!")
        return False
    
    # Валидация chat_id
    if not chat_id.isdigit() and not (chat_id.startswith('-') and chat_id[1:].isdigit()):
        print("❌ Неправильный формат Chat ID!")
        return False
    
    # Читаем текущий config.py
    try:
        with open('config.py', 'r', encoding='utf-8') as f:
            config_content = f.read()
    except FileNotFoundError:
        print("❌ Файл config.py не найден!")
        return False
    
    # Обновляем токен и chat_id
    config_content = re.sub(
        r"'bot_token': '[^']*'",
        f"'bot_token': '{bot_token}'",
        config_content
    )
    
    config_content = re.sub(
        r"'chat_id': '[^']*'",
        f"'chat_id': '{chat_id}'",
        config_content
    )
    
    # Сохраняем обновленный config.py
    try:
        with open('config.py', 'w', encoding='utf-8') as f:
            f.write(config_content)
        print("✅ Файл config.py обновлен!")
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return False
    
    # Создаем файл с данными нового бота
    bot_info = f"""# ДАННЫЕ НОВОГО БОТА

Токен бота: {bot_token}
Chat ID: {chat_id}
Дата создания: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Для тестирования:
python test_bot.py
python force_menu_bot.py

# Отправьте любое сообщение новому боту для получения меню!
"""
    
    with open('new_bot_info.txt', 'w', encoding='utf-8') as f:
        f.write(bot_info)
    
    print("\n🎉 НАСТРОЙКА ЗАВЕРШЕНА!")
    print("📄 Данные сохранены в new_bot_info.txt")
    print("\n🧪 Тестирование:")
    print("python test_bot.py")
    print("\n🤖 Запуск бота:")
    print("python force_menu_bot.py")
    print("\n📱 Отправьте любое сообщение новому боту!")
    
    return True

if __name__ == "__main__":
    setup_new_bot()