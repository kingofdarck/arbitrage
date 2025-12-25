#!/usr/bin/env python3
"""
Health Check сервис для мониторинга состояния арбитражного бота
Предоставляет HTTP endpoint для проверки работоспособности
"""

import asyncio
import time
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from aiohttp import web
import logging

class HealthCheckService:
    """Сервис проверки здоровья системы"""
    
    def __init__(self, port=8080):
        self.port = port
        self.start_time = time.time()
        self.last_heartbeat = time.time()
        self.stats = {
            'status': 'starting',
            'uptime': 0,
            'last_activity': None,
            'total_opportunities': 0,
            'total_trades': 0,
            'total_profit': 0.0,
            'errors_count': 0,
            'last_error': None
        }
        
        # Настройка логирования
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Путь к файлу статистики
        self.stats_file = Path(__file__).parent / 'data' / 'health_stats.json'
        self.stats_file.parent.mkdir(exist_ok=True)
        
        # Загружаем сохраненную статистику
        self.load_stats()
    
    def load_stats(self):
        """Загрузка сохраненной статистики"""
        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r') as f:
                    saved_stats = json.load(f)
                    self.stats.update(saved_stats)
                    self.logger.info("📊 Статистика загружена из файла")
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки статистики: {e}")
    
    def save_stats(self):
        """Сохранение статистики"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения статистики: {e}")
    
    def update_heartbeat(self):
        """Обновление heartbeat"""
        self.last_heartbeat = time.time()
        self.stats['last_activity'] = datetime.now().isoformat()
        self.stats['uptime'] = time.time() - self.start_time
        self.stats['status'] = 'running'
    
    def record_opportunity(self, profit_percent=0.0):
        """Запись найденной возможности"""
        self.stats['total_opportunities'] += 1
        self.update_heartbeat()
        self.save_stats()
    
    def record_trade(self, profit_usd=0.0, success=True):
        """Запись исполненной сделки"""
        self.stats['total_trades'] += 1
        if success:
            self.stats['total_profit'] += profit_usd
        self.update_heartbeat()
        self.save_stats()
    
    def record_error(self, error_message):
        """Запись ошибки"""
        self.stats['errors_count'] += 1
        self.stats['last_error'] = {
            'message': str(error_message),
            'timestamp': datetime.now().isoformat()
        }
        self.save_stats()
    
    async def health_handler(self, request):
        """HTTP handler для проверки здоровья"""
        current_time = time.time()
        uptime = current_time - self.start_time
        time_since_heartbeat = current_time - self.last_heartbeat
        
        # Определяем статус
        if time_since_heartbeat > 300:  # 5 минут без активности
            status = 'unhealthy'
            status_code = 503
        elif time_since_heartbeat > 120:  # 2 минуты без активности
            status = 'degraded'
            status_code = 200
        else:
            status = 'healthy'
            status_code = 200
        
        response_data = {
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': uptime,
            'uptime_human': self.format_uptime(uptime),
            'last_heartbeat': datetime.fromtimestamp(self.last_heartbeat).isoformat(),
            'time_since_heartbeat': time_since_heartbeat,
            'statistics': self.stats,
            'system_info': {
                'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                'platform': os.name,
                'pid': os.getpid()
            }
        }
        
        return web.json_response(response_data, status=status_code)
    
    async def stats_handler(self, request):
        """HTTP handler для получения статистики"""
        return web.json_response(self.stats)
    
    async def metrics_handler(self, request):
        """HTTP handler для метрик в формате Prometheus"""
        current_time = time.time()
        uptime = current_time - self.start_time
        
        metrics = f"""# HELP arbitrage_uptime_seconds Uptime in seconds
# TYPE arbitrage_uptime_seconds counter
arbitrage_uptime_seconds {uptime}

# HELP arbitrage_opportunities_total Total opportunities found
# TYPE arbitrage_opportunities_total counter
arbitrage_opportunities_total {self.stats['total_opportunities']}

# HELP arbitrage_trades_total Total trades executed
# TYPE arbitrage_trades_total counter
arbitrage_trades_total {self.stats['total_trades']}

# HELP arbitrage_profit_usd_total Total profit in USD
# TYPE arbitrage_profit_usd_total counter
arbitrage_profit_usd_total {self.stats['total_profit']}

# HELP arbitrage_errors_total Total errors count
# TYPE arbitrage_errors_total counter
arbitrage_errors_total {self.stats['errors_count']}

# HELP arbitrage_last_heartbeat_seconds Timestamp of last heartbeat
# TYPE arbitrage_last_heartbeat_seconds gauge
arbitrage_last_heartbeat_seconds {self.last_heartbeat}
"""
        
        return web.Response(text=metrics, content_type='text/plain')
    
    def format_uptime(self, seconds):
        """Форматирование времени работы"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    async def start_server(self):
        """Запуск HTTP сервера"""
        app = web.Application()
        
        # Маршруты
        app.router.add_get('/health', self.health_handler)
        app.router.add_get('/stats', self.stats_handler)
        app.router.add_get('/metrics', self.metrics_handler)
        app.router.add_get('/', self.health_handler)  # Корневой маршрут
        
        # Запуск сервера
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        self.logger.info(f"🏥 Health Check сервер запущен на порту {self.port}")
        self.logger.info(f"📊 Endpoints:")
        self.logger.info(f"   GET /health - проверка здоровья")
        self.logger.info(f"   GET /stats - статистика")
        self.logger.info(f"   GET /metrics - метрики Prometheus")
        
        return runner

# Глобальный экземпляр для использования в других модулях
health_service = HealthCheckService()

async def main():
    """Запуск health check сервера как отдельного сервиса"""
    try:
        runner = await health_service.start_server()
        
        # Симуляция работы для тестирования
        while True:
            await asyncio.sleep(30)
            health_service.update_heartbeat()
            
            # Симуляция активности каждые 2 минуты
            if int(time.time()) % 120 == 0:
                health_service.record_opportunity(1.5)
                print(f"💓 Heartbeat: {datetime.now().strftime('%H:%M:%S')}")
            
    except KeyboardInterrupt:
        print("\n⏹️ Остановка Health Check сервера...")
    except Exception as e:
        print(f"❌ Ошибка Health Check сервера: {e}")
    finally:
        if 'runner' in locals():
            await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())