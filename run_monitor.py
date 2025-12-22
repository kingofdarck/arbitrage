#!/usr/bin/env python3
"""
Запуск арбитражного монитора с улучшенной конфигурацией
"""

import asyncio
import sys
import signal
from crypto_arbitrage_monitor import CryptoArbitrageMonitor
from config import MONITORING_CONFIG, EXCHANGES, TRADING_PAIRS, TRIANGULAR_SETS
from notifications import NotificationService
import logging

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('arbitrage_monitor.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class EnhancedArbitrageMonitor(CryptoArbitrageMonitor):
    """Улучшенная версия арбитражного монитора с конфигурацией"""
    
    def __init__(self):
        super().__init__()
        
        # Применяем настройки из конфига
        self.min_profit_threshold = MONITORING_CONFIG['min_profit_threshold']
        self.check_interval = MONITORING_CONFIG['check_interval']
        self.main_pairs = TRADING_PAIRS
        self.triangular_sets = TRIANGULAR_SETS
        
        # Фильтруем активные биржи
        self.exchanges = {
            name: config['api_url'] 
            for name, config in EXCHANGES.items() 
            if config['enabled']
        }
        
        self.running = True
        logger.info(f"Монитор инициализирован с {len(self.exchanges)} биржами")
        logger.info(f"Отслеживаемые пары: {len(self.main_pairs)}")
        logger.info(f"Треугольные наборы: {len(self.triangular_sets)}")
    
    async def send_notification(self, opportunity):
        """Отправка уведомления через все каналы"""
        message = self.format_opportunity_message(opportunity)
        
        # Логируем в консоль и файл
        logger.info(f"🚨 НАЙДЕНА ВОЗМОЖНОСТЬ: {opportunity.profit_percent:.2f}%")
        
        # Отправляем через все настроенные каналы
        await NotificationService.send_all(message)
        
        # Сохраняем в файл истории
        with open('opportunities_history.log', 'a', encoding='utf-8') as f:
            f.write(f"{opportunity.timestamp.isoformat()},{opportunity.type},{opportunity.profit_percent:.2f}%,{opportunity.details}\n")
    
    def format_opportunity_message(self, opportunity) -> str:
        """Форматирование сообщения о возможности"""
        if opportunity.type == 'cross_exchange':
            return f"""
🚨 МЕЖБИРЖЕВОЙ АРБИТРАЖ 🚨

💰 Прибыль: {opportunity.profit_percent:.2f}%
🪙 Пара: {opportunity.details['symbol']}
📈 Купить на {opportunity.details['buy_exchange']}: ${opportunity.details['buy_price']:.4f}
📉 Продать на {opportunity.details['sell_exchange']}: ${opportunity.details['sell_price']:.4f}
⏰ Время: {opportunity.timestamp.strftime('%H:%M:%S')}

Все цены:
{chr(10).join([f"  {ex}: ${price:.4f}" for ex, price in opportunity.details['all_prices'].items()])}
            """
        else:  # triangular
            return f"""
🔺 ТРЕУГОЛЬНЫЙ АРБИТРАЖ 🔺

💰 Прибыль: {opportunity.profit_percent:.2f}%
🏢 Биржа: {opportunity.details['exchange']}
🔄 Путь: {opportunity.details['path']}
📊 Расчет: {opportunity.details['calculation']}
⏰ Время: {opportunity.timestamp.strftime('%H:%M:%S')}
            """
    
    async def monitor_loop(self):
        """Основной цикл мониторинга с обработкой сигналов"""
        logger.info("🚀 Запуск мониторинга арбитражных возможностей...")
        
        while self.running:
            try:
                # Получаем актуальные цены
                await self.fetch_all_prices()
                
                # Ищем возможности
                opportunities = []
                
                # Межбиржевой арбитраж
                cross_opportunities = self.find_cross_exchange_arbitrage()
                opportunities.extend(cross_opportunities)
                
                # Треугольный арбитраж
                for exchange in self.prices.keys():
                    triangular_opportunities = self.find_triangular_arbitrage(exchange)
                    opportunities.extend(triangular_opportunities)
                
                # Сортируем по прибыльности
                opportunities.sort(key=lambda x: x.profit_percent, reverse=True)
                
                # Ограничиваем количество уведомлений
                max_notifications = MONITORING_CONFIG['max_opportunities_per_notification']
                top_opportunities = opportunities[:max_notifications]
                
                if top_opportunities:
                    logger.info(f"📊 Найдено {len(opportunities)} возможностей, отправляем топ {len(top_opportunities)}")
                    for opportunity in top_opportunities:
                        await self.send_notification(opportunity)
                else:
                    logger.info("✅ Мониторинг активен, возможностей не найдено")
                
                # Пауза перед следующей проверкой
                await asyncio.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Получен сигнал остановки")
                self.running = False
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле мониторинга: {e}")
                await asyncio.sleep(10)
    
    def stop(self):
        """Остановка мониторинга"""
        self.running = False
        logger.info("Остановка мониторинга...")

async def main():
    """Главная функция с обработкой сигналов"""
    monitor = EnhancedArbitrageMonitor()
    
    # Обработка сигналов для корректного завершения
    def signal_handler(signum, frame):
        logger.info(f"Получен сигнал {signum}")
        monitor.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await monitor.run()
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        logger.info("Мониторинг завершен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nПрограмма остановлена")
    except Exception as e:
        print(f"Ошибка запуска: {e}")