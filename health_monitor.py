#!/usr/bin/env python3
"""
Health Monitor для умного арбитражного монитора
Проверяет работоспособность системы и отправляет уведомления о проблемах
"""

import asyncio
import aiohttp
import os
import time
from datetime import datetime, timedelta
from aiohttp import web
import logging
from notifications import NotificationService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HealthMonitor:
    """Монитор здоровья умной системы арбитража"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.last_check = datetime.now()
        self.last_log_update = None
        self.last_notification_sent = None
        self.notification_cooldown = timedelta(hours=1)  # Не чаще раза в час
        self.log_file = '/app/smart_arbitrage.log'
        self.total_cycles = 0
        self.total_opportunities = 0
        self.errors_count = 0
        
    def update_stats(self, cycles, opportunities, errors=0):
        """Обновление статистики"""
        self.last_check = datetime.now()
        self.total_cycles = cycles
        self.total_opportunities = opportunities
        self.errors_count = errors
        
    async def check_log_file(self):
        """Проверка обновления лог файла"""
        try:
            if os.path.exists(self.log_file):
                stat = os.stat(self.log_file)
                file_modified = datetime.fromtimestamp(stat.st_mtime)
                
                # Если файл не обновлялся более 5 минут - проблема
                if datetime.now() - file_modified > timedelta(minutes=5):
                    return False, f"Лог файл не обновлялся {datetime.now() - file_modified}"
                
                self.last_log_update = file_modified
                return True, "Лог файл обновляется"
            else:
                return False, "Лог файл не найден"
        except Exception as e:
            return False, f"Ошибка проверки лог файла: {e}"
    
    async def check_system_resources(self):
        """Проверка системных ресурсов"""
        try:
            # Проверяем использование памяти
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            mem_total = None
            mem_available = None
            
            for line in meminfo.split('\n'):
                if line.startswith('MemTotal:'):
                    mem_total = int(line.split()[1])
                elif line.startswith('MemAvailable:'):
                    mem_available = int(line.split()[1])
            
            if mem_total and mem_available:
                mem_usage = (mem_total - mem_available) / mem_total * 100
                
                if mem_usage > 90:
                    return False, f"Высокое использование памяти: {mem_usage:.1f}%"
                
                return True, f"Использование памяти: {mem_usage:.1f}%"
            
            return True, "Память в норме"
            
        except Exception as e:
            return True, f"Не удалось проверить память: {e}"
    
    async def send_alert(self, message):
        """Отправка уведомления о проблеме"""
        now = datetime.now()
        
        # Проверяем cooldown
        if (self.last_notification_sent and 
            now - self.last_notification_sent < self.notification_cooldown):
            return
        
        try:
            alert_message = f"""
🚨 ПРОБЛЕМА С УМНЫМ МОНИТОРОМ

⏰ Время: {now.strftime('%H:%M:%S %d.%m.%Y')}
❌ Проблема: {message}

🔧 Рекомендации:
1. Проверьте логи: docker-compose logs smart-arbitrage-monitor
2. Перезапустите: docker-compose restart smart-arbitrage-monitor
3. Проверьте интернет соединение

🌐 Health check: http://localhost:8000
            """
            
            await NotificationService.send_telegram(alert_message.strip())
            self.last_notification_sent = now
            logger.warning(f"Отправлено уведомление о проблеме: {message}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
    
    async def health_check_internal(self):
        """Внутренняя проверка здоровья системы"""
        issues = []
        
        # Проверяем лог файл
        log_ok, log_msg = await self.check_log_file()
        if not log_ok:
            issues.append(log_msg)
        
        # Проверяем системные ресурсы
        resources_ok, resources_msg = await self.check_system_resources()
        if not resources_ok:
            issues.append(resources_msg)
        
        # Если есть проблемы - отправляем уведомление
        if issues:
            await self.send_alert("; ".join(issues))
            return False, issues
        
        return True, ["Все системы работают нормально"]

    async def health_check(self, request):
        """HTTP endpoint для проверки здоровья"""
        uptime = datetime.now() - self.start_time
        
        # Выполняем внутреннюю проверку
        is_healthy, messages = await self.health_check_internal()
        
        status_data = {
            "status": "healthy" if is_healthy else "unhealthy",
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_human": str(uptime),
            "start_time": self.start_time.isoformat(),
            "last_check": self.last_check.isoformat(),
            "last_log_update": self.last_log_update.isoformat() if self.last_log_update else None,
            "total_cycles": self.total_cycles,
            "total_opportunities": self.total_opportunities,
            "errors_count": self.errors_count,
            "messages": messages,
            "timestamp": datetime.now().isoformat()
        }
        
        # Определяем HTTP статус
        http_status = 200 if is_healthy else 503
        
        return web.json_response(status_data, status=http_status)
    
    async def monitor_loop(self):
        """Основной цикл мониторинга"""
        logger.info("🏥 Запуск Health Monitor для умного арбитражного монитора")
        
        while True:
            try:
                # Выполняем проверку здоровья
                is_healthy, messages = await self.health_check_internal()
                
                status = "✅ ЗДОРОВ" if is_healthy else "❌ ПРОБЛЕМЫ"
                logger.info(f"{status}: {'; '.join(messages)}")
                
                # Ждем 2 минуты до следующей проверки
                await asyncio.sleep(120)
                
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга: {e}")
                await asyncio.sleep(60)

    async def start_server(self, port=8000):
        """Запуск HTTP сервера"""
        app = web.Application()
        app.router.add_get('/health', self.health_check)
        app.router.add_get('/', self.health_check)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        logger.info(f"🌐 Health check сервер запущен на порту {port}")
        return runner

async def main():
    """Главная функция"""
    # Создаем монитор
    monitor = HealthMonitor()
    
    # Запускаем web сервер
    await monitor.start_server(8000)
    
    # Запускаем цикл мониторинга
    await monitor.monitor_loop()

# Глобальный экземпляр для использования в основном мониторе
health_monitor = HealthMonitor()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Health Monitor остановлен")
    except Exception as e:
        logger.error(f"Критическая ошибка Health Monitor: {e}")