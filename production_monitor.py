#!/usr/bin/env python3
"""
Продакшн версия арбитражного монитора для хостинга
Топ-15 возможностей в Telegram каждые 30 секунд
"""

import asyncio
import sys
import signal
import os
from datetime import datetime
from enhanced_arbitrage_monitor import EnhancedArbitrageMonitor
from config import MONITORING_CONFIG, EXCHANGES, NOTIFICATION_CONFIG
from notifications import NotificationService
import logging

# Настройка логирования для продакшн
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_arbitrage.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ProductionArbitrageMonitor(EnhancedArbitrageMonitor):
    """Продакшн версия арбитражного монитора"""
    
    def __init__(self):
        super().__init__()
        self.min_profit_threshold = 0.1  # Снижено до 0.1% для реальных пар
        self.min_confidence = 0.3        # Снижено до 30% для большего количества возможностей
        self.max_notifications_per_cycle = 15  # Топ-15 возможностей
        self.running = True
        
        # Статистика для продакшн
        self.stats = {
            'total_cycles': 0,
            'total_opportunities': 0,
            'total_notifications_sent': 0,
            'best_profit': 0,
            'start_time': datetime.now(),
            'last_telegram_success': None,
            'telegram_errors': 0
        }
        
        logger.info(f"🚀 Продакшн монитор инициализирован")
        logger.info(f"📊 Настройки: топ-{self.max_notifications_per_cycle} возможностей")
        logger.info(f"📱 Telegram: {'✅ Включен' if NOTIFICATION_CONFIG['telegram']['enabled'] else '❌ Отключен'}")

    async def send_telegram_notification(self, opportunity):
        """Отправка уведомления в Telegram с обработкой ошибок"""
        try:
            message = self.format_telegram_message(opportunity)
            await NotificationService.send_telegram(message)
            
            self.stats['last_telegram_success'] = datetime.now()
            self.stats['total_notifications_sent'] += 1
            
            logger.debug(f"📱 Telegram: отправлено уведомление о {opportunity.profit_percent:.2f}%")
            
        except Exception as e:
            self.stats['telegram_errors'] += 1
            logger.error(f"❌ Ошибка отправки в Telegram: {e}")

    def format_telegram_message(self, opportunity) -> str:
        """Форматирование сообщения для Telegram с проверенными парами"""
        details = opportunity.details
        confidence_emoji = "🟢" if opportunity.confidence > 0.7 else "🟡" if opportunity.confidence > 0.4 else "🔴"
        
        # Ограничиваем прибыль для читаемости (максимум 50%)
        profit_display = min(opportunity.profit_percent, 50.0)
        
        # Определяем тип криптовалюты для эмодзи
        symbol = details['symbol']
        crypto_emoji = "₿" if symbol.startswith('BTC') else "Ξ" if symbol.startswith('ETH') else "🪙"
        
        message = f"""
🚨 АРБИТРАЖ {confidence_emoji}

{crypto_emoji} {symbol}
💰 Прибыль: {profit_display:.2f}%
🎯 Уверенность: {opportunity.confidence:.1%}

📈 КУПИТЬ на {details['buy_exchange'].upper()}
💵 ${details['buy_price']:.8f}
📊 Объем: ${details['buy_volume_24h']:,.0f}

📉 ПРОДАТЬ на {details['sell_exchange'].upper()}  
💵 ${details['sell_price']:.8f}
📊 Объем: ${details['sell_volume_24h']:,.0f}

💸 Комиссии: {details['fees']['total']:.2f}%
⏰ {opportunity.timestamp.strftime('%H:%M:%S')}
        """
        
        return message.strip()

    async def send_batch_telegram_summary(self, opportunities):
        """Отправка сводки топ возможностей с проверенными парами"""
        if not opportunities:
            return
            
        try:
            # Заголовок сводки
            summary = f"""
🎯 ТОП-{len(opportunities)} АРБИТРАЖНЫХ ВОЗМОЖНОСТЕЙ
⏰ {datetime.now().strftime('%H:%M:%S')} | Цикл #{self.stats['total_cycles']}

"""
            
            # Добавляем каждую возможность
            for i, opp in enumerate(opportunities, 1):
                details = opp.details
                confidence_emoji = "🟢" if opp.confidence > 0.7 else "🟡" if opp.confidence > 0.4 else "🔴"
                profit_display = min(opp.profit_percent, 50.0)  # Ограничиваем до 50%
                
                # Определяем эмодзи для криптовалюты
                symbol = details['symbol']
                crypto_emoji = "₿" if symbol.startswith('BTC') else "Ξ" if symbol.startswith('ETH') else "🪙"
                
                summary += f"""
{i}. {confidence_emoji} {crypto_emoji} {symbol}
   💰 {profit_display:.2f}% | 🎯 {opp.confidence:.0%}
   📈 {details['buy_exchange']} ${details['buy_price']:.6f}
   📉 {details['sell_exchange']} ${details['sell_price']:.6f}
"""
            
            # Добавляем статистику
            uptime = datetime.now() - self.stats['start_time']
            summary += f"""
📊 СТАТИСТИКА:
   ⏱️ Работает: {str(uptime).split('.')[0]}
   🔄 Циклов: {self.stats['total_cycles']}
   📱 Уведомлений: {self.stats['total_notifications_sent']}
   🏆 Лучшая прибыль: {self.stats['best_profit']:.2f}%
   ❌ Ошибок: {self.stats['telegram_errors']}
            """
            
            await NotificationService.send_telegram(summary.strip())
            self.stats['last_telegram_success'] = datetime.now()
            self.stats['total_notifications_sent'] += 1
            
            logger.info(f"📱 Отправлена сводка с {len(opportunities)} возможностями")
            
        except Exception as e:
            self.stats['telegram_errors'] += 1
            logger.error(f"❌ Ошибка отправки сводки в Telegram: {e}")

    async def monitor_loop(self, check_interval: int = 30):
        """Основной цикл продакшн мониторинга"""
        logger.info("🚀 Запуск продакшн мониторинга арбитражных возможностей...")
        
        while self.running:
            try:
                cycle_start = datetime.now()
                
                # Получаем данные со всех бирж
                await self.fetch_all_exchange_data()
                
                if not self.all_pairs:
                    logger.warning("⚠️ Не получены данные ни с одной биржи")
                    await asyncio.sleep(check_interval)
                    continue
                
                # Ищем межбиржевые возможности
                cross_opportunities = self.find_cross_exchange_arbitrage()
                
                # Ищем треугольные возможности
                triangular_opportunities = []
                for exchange in self.all_pairs.keys():
                    exchange_triangular = self.find_triangular_arbitrage(exchange)
                    triangular_opportunities.extend(exchange_triangular)
                
                # Объединяем и фильтруем
                all_opportunities = cross_opportunities + triangular_opportunities
                filtered_opportunities = [
                    opp for opp in all_opportunities 
                    if (opp.profit_percent >= self.min_profit_threshold and
                        opp.confidence >= self.min_confidence)
                ]
                
                # Сортируем по взвешенной прибыли
                filtered_opportunities.sort(
                    key=lambda x: x.profit_percent * x.confidence, 
                    reverse=True
                )
                
                # Обновляем статистику
                self.stats['total_cycles'] += 1
                self.stats['total_opportunities'] += len(filtered_opportunities)
                
                if filtered_opportunities:
                    best_profit = filtered_opportunities[0].profit_percent
                    if best_profit > self.stats['best_profit']:
                        self.stats['best_profit'] = best_profit
                
                # Берем топ возможности
                top_opportunities = filtered_opportunities[:self.max_notifications_per_cycle]
                
                cycle_time = (datetime.now() - cycle_start).total_seconds()
                total_pairs = sum(len(pairs) for pairs in self.all_pairs.values())
                
                # Логируем статистику цикла
                logger.info(f"📊 Цикл #{self.stats['total_cycles']} за {cycle_time:.1f}с | "
                          f"Биржи: {len(self.all_pairs)} | "
                          f"Пары: {total_pairs:,} | "
                          f"Возможности: {len(all_opportunities)} | "
                          f"Качественные: {len(filtered_opportunities)} | "
                          f"Топ: {len(top_opportunities)}")
                
                # Отправляем уведомления в Telegram
                if top_opportunities and NOTIFICATION_CONFIG['telegram']['enabled']:
                    # Отправляем сводку одним сообщением
                    await self.send_batch_telegram_summary(top_opportunities)
                    
                    logger.info(f"📱 Отправлена сводка топ-{len(top_opportunities)} возможностей")
                else:
                    logger.info("📊 Качественных возможностей не найдено")
                
                # Показываем общую статистику каждые 10 циклов
                if self.stats['total_cycles'] % 10 == 0:
                    uptime = datetime.now() - self.stats['start_time']
                    avg_opportunities = self.stats['total_opportunities'] / self.stats['total_cycles']
                    
                    logger.info(f"📈 СТАТИСТИКА (uptime: {uptime}):")
                    logger.info(f"   Циклов: {self.stats['total_cycles']}")
                    logger.info(f"   Всего возможностей: {self.stats['total_opportunities']}")
                    logger.info(f"   Среднее за цикл: {avg_opportunities:.1f}")
                    logger.info(f"   Лучшая прибыль: {self.stats['best_profit']:.2f}%")
                    logger.info(f"   Уведомлений отправлено: {self.stats['total_notifications_sent']}")
                    logger.info(f"   Ошибок Telegram: {self.stats['telegram_errors']}")
                
                # Пауза перед следующим циклом
                await asyncio.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("Получен сигнал остановки")
                self.running = False
                break
            except Exception as e:
                logger.error(f"❌ Критическая ошибка в цикле мониторинга: {e}")
                # Не останавливаемся при ошибках, продолжаем работу
                await asyncio.sleep(10)

    def stop(self):
        """Остановка мониторинга"""
        self.running = False
        logger.info("🛑 Остановка продакшн мониторинга...")

async def main():
    """Главная функция для продакшн"""
    logger.info("🚀 Запуск продакшн арбитражного монитора")
    logger.info("📱 Топ-15 возможностей будут отправляться в Telegram каждые 30 секунд")
    
    monitor = ProductionArbitrageMonitor()
    
    # Обработка сигналов для корректного завершения
    def signal_handler(signum, frame):
        logger.info(f"Получен сигнал {signum}")
        monitor.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await monitor.run(check_interval=30)
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        # Финальная статистика
        uptime = datetime.now() - monitor.stats['start_time']
        logger.info(f"📊 ФИНАЛЬНАЯ СТАТИСТИКА:")
        logger.info(f"   Время работы: {uptime}")
        logger.info(f"   Циклов: {monitor.stats['total_cycles']}")
        logger.info(f"   Возможностей: {monitor.stats['total_opportunities']}")
        logger.info(f"   Уведомлений: {monitor.stats['total_notifications_sent']}")
        logger.info(f"   Лучшая прибыль: {monitor.stats['best_profit']:.2f}%")
        logger.info("👋 Продакшн мониторинг завершен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Программа остановлена")
    except Exception as e:
        print(f"💥 Ошибка запуска: {e}")
        sys.exit(1)