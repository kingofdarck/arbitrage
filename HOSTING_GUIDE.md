# Руководство по размещению на хостинге

## 🚀 Варианты хостинга для 24/7 работы

### 1. **VPS/VDS серверы (Рекомендуется)**

#### **DigitalOcean**
```bash
# 1. Создайте дроплет Ubuntu 22.04 (минимум $6/месяц)
# 2. Подключитесь по SSH
ssh root@your-server-ip

# 3. Клонируйте репозиторий
git clone https://github.com/yourusername/crypto-arbitrage-monitor.git
cd crypto-arbitrage-monitor

# 4. Запустите деплой
chmod +x deploy.sh
./deploy.sh
```

#### **Vultr**
```bash
# Аналогично DigitalOcean
# Минимальный план: $6/месяц
# Выберите Ubuntu 22.04
```

#### **Linode**
```bash
# Минимальный план: $5/месяц
# Процедура аналогична
```

### 2. **Облачные платформы**

#### **Google Cloud Platform (GCP)**
```bash
# 1. Создайте проект в GCP
# 2. Включите Compute Engine API
# 3. Создайте VM instance

# На VM:
sudo apt update
sudo apt install git docker.io docker-compose
git clone your-repo
cd crypto-arbitrage-monitor
sudo ./deploy.sh
```

#### **Amazon AWS EC2**
```bash
# 1. Запустите EC2 instance (t3.micro для начала)
# 2. Настройте Security Group (порт 8000 для мониторинга)

# На instance:
sudo yum update
sudo yum install git docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Перелогиньтесь и:
git clone your-repo
cd crypto-arbitrage-monitor
./deploy.sh
```

### 3. **Специализированные платформы**

#### **Railway**
```yaml
# railway.toml
[build]
builder = "dockerfile"

[deploy]
startCommand = "python production_monitor.py"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "always"
```

#### **Render**
```yaml
# render.yaml
services:
  - type: web
    name: arbitrage-monitor
    env: docker
    dockerfilePath: ./Dockerfile
    healthCheckPath: /health
    envVars:
      - key: PYTHONUNBUFFERED
        value: "1"
```

#### **Heroku**
```bash
# 1. Установите Heroku CLI
# 2. Создайте приложение
heroku create your-arbitrage-monitor

# 3. Добавьте переменные окружения
heroku config:set PYTHONUNBUFFERED=1

# 4. Деплой
git push heroku main
```

## ⚙️ Настройка перед деплоем

### 1. **Настройте Telegram бота**
```python
# В config.py
NOTIFICATION_CONFIG = {
    'telegram': {
        'enabled': True,
        'bot_token': 'YOUR_BOT_TOKEN',  # Получите у @BotFather
        'chat_id': 'YOUR_CHAT_ID',      # Ваш ID или ID группы
    }
}
```

### 2. **Получите токен Telegram бота**
```
1. Напишите @BotFather в Telegram
2. Отправьте /newbot
3. Выберите имя и username для бота
4. Скопируйте токен
5. Для получения chat_id:
   - Напишите боту любое сообщение
   - Перейдите: https://api.telegram.org/bot<TOKEN>/getUpdates
   - Найдите "chat":{"id": YOUR_CHAT_ID}
```

### 3. **Настройте переменные окружения**
```bash
# Для безопасности вынесите токены в переменные окружения
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

## 🔧 Мониторинг и обслуживание

### **Проверка статуса**
```bash
# Статус контейнера
docker-compose ps

# Логи в реальном времени
docker-compose logs -f

# Статистика ресурсов
docker stats
```

### **Обновление системы**
```bash
# Остановка
docker-compose stop

# Обновление кода
git pull

# Пересборка и запуск
docker-compose up -d --build
```

### **Мониторинг здоровья**
```bash
# HTTP endpoint для проверки
curl http://your-server:8000/health

# Ответ:
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "total_cycles": 120,
  "total_opportunities": 1500,
  "last_cycle": "2024-01-01T12:00:00"
}
```

## 💰 Стоимость хостинга

| Платформа | Минимальная стоимость | Рекомендуемый план |
|-----------|----------------------|-------------------|
| DigitalOcean | $6/месяц | $12/месяц (2GB RAM) |
| Vultr | $6/месяц | $12/месяц |
| Linode | $5/месяц | $10/месяц |
| AWS EC2 | $8/месяц | $15/месяц |
| Google Cloud | $7/месяц | $14/месяц |
| Railway | $5/месяц | $10/месяц |
| Render | $7/месяц | $25/месяц |
| Heroku | $7/месяц | $25/месяц |

## 🛡️ Безопасность

### **Настройка файрвола**
```bash
# Ubuntu/Debian
sudo ufw allow ssh
sudo ufw allow 8000  # Для мониторинга
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

### **Автоматические обновления**
```bash
# Ubuntu
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Настройка автоперезапуска
echo "0 4 * * 1 cd /path/to/arbitrage && docker-compose restart" | sudo crontab -
```

### **Резервное копирование логов**
```bash
# Настройка ротации логов
sudo nano /etc/logrotate.d/arbitrage

# Содержимое:
/path/to/arbitrage/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
```

## 📊 Мониторинг производительности

### **Системные ресурсы**
```bash
# Использование CPU и памяти
htop

# Использование диска
df -h

# Сетевая активность
iftop
```

### **Мониторинг приложения**
```bash
# Количество запросов к API
grep "INFO" production_arbitrage.log | grep "Цикл" | tail -10

# Ошибки Telegram
grep "ERROR" production_arbitrage.log | grep "Telegram"

# Статистика возможностей
grep "возможностей" production_arbitrage.log | tail -5
```

## 🚨 Алерты и уведомления

### **Настройка алертов о сбоях**
```bash
# Скрипт проверки здоровья
#!/bin/bash
# health_check.sh

HEALTH_URL="http://localhost:8000/health"
TELEGRAM_BOT_TOKEN="your_token"
TELEGRAM_CHAT_ID="your_chat_id"

if ! curl -f $HEALTH_URL > /dev/null 2>&1; then
    MESSAGE="🚨 Арбитражный монитор не отвечает!"
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
         -d chat_id=$TELEGRAM_CHAT_ID \
         -d text="$MESSAGE"
fi

# Добавьте в crontab:
# */5 * * * * /path/to/health_check.sh
```

## 🎯 Рекомендации по выбору хостинга

### **Для начинающих:**
- **DigitalOcean** - простота настройки, хорошая документация
- **Vultr** - низкие цены, быстрое развертывание

### **Для продвинутых:**
- **AWS EC2** - максимальная гибкость, интеграция с другими сервисами
- **Google Cloud** - хорошая производительность, кредиты для новых пользователей

### **Для минимальных затрат:**
- **Railway** - простой деплой, бесплатный tier
- **Render** - автоматический деплой из Git

## 📋 Чеклист деплоя

- [ ] Создан и настроен Telegram бот
- [ ] Получен chat_id для уведомлений
- [ ] Настроен config.py с правильными токенами
- [ ] Выбран и настроен хостинг
- [ ] Установлен Docker и Docker Compose
- [ ] Склонирован репозиторий на сервер
- [ ] Запущен deploy.sh
- [ ] Проверен статус контейнера
- [ ] Настроен мониторинг здоровья
- [ ] Настроены алерты о сбоях
- [ ] Проверена работа уведомлений в Telegram

**Готово! Ваш арбитражный монитор работает 24/7 и отправляет топ-15 возможностей в Telegram каждые 30 секунд! 🚀**