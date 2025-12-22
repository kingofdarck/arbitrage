#!/usr/bin/env python3
"""
Live арбитражный монитор с редактированием сообщений
Обновление каждые 5 секунд, редактирование одного сообщения в Telegram
"""

import asyncio
import sys
import signal
import os
from datetime import datetime, timedelta
from enhanced_arbitrage_monitor import EnhancedArbitrageMonitor
from config import MONITORING_CONFIG, EXCHANGES, NOTIFICATION_CONFIG
from notifications import NotificationService
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('live_arbitrage.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class LiveArbitrageMonitor(EnhancedArbitrageMonitor):
    """Live монитор с редактированием сообщений в Telegram"""
    
    def __init__(self):
        super().__init__()
        self.min_profit_threshold = 0.1
        self.min_confidence = 0.3
        self.max_opportunities_display = 10  # Показываем топ-10 в сообщении
        self.running = True
        
        # Статистика
        self.stats = {
            'total_cycles': 0,
            'total_opportunities': 0,
            'best_profit': 0,
            'start_time': datetime.now(),
            'last_update': None,
            'message_updates': 0,
            'current_opportunities': []
        }
        
        logger.info(f"🔴 Live монитор инициализирован")
        logger.info(f"⚡ Обновление каждые 5 секунд с редактированием сообщения")
        logger.info(f"📱 Telegram: {'✅ Включен' if NOTIFICATION_CONFIG['telegram']['enabled'] else '❌ Отключен'}")

    def format_live_message(self, opportunities) -> str:
        """Форматирование live сообщения для Telegram"""
        current_time = datetime.now()
        uptime = current_time - self.stats['start_time']
        
        # Заголовок с live индикатором
        header = f"""
🔴 <b>LIVE АРБИТРАЖ МОНИТОР</b>

⏰ {current_time.strftime('%H:%M:%S')} | 🔄 Цикл #{self.stats['total_cycles']}
⚡ Обновлено: {self.stats['message_updates']} раз
🕐 Работает: {str(uptime).split('.')[0]}

"""
        
        if not opportunities:
            content = """
📊 <b>СТАТУС:</b> Поиск возможностей...
🔍 Мониторинг 5 бирж
📈 Анализ топ криптовалют
⏳ Ожидание арбитража...

💡 <i>Система активно ищет прибыльные возможности</i>
            """
        else:
            # Показываем топ возможности
            content = f"🎯 <b>ТОП-{min(len(opportunities), self.max_opportunities_display)} ВОЗМОЖНОСТЕЙ:</b>\n\n"
            
            for i, opp in enumerate(opportunities[:self.max_opportunities_display], 1):
                details = opp.details
                confidence_emoji = "🟢" if opp.confidence > 0.7 else "🟡" if opp.confidence > 0.4 else "🔴"
                profit_display = min(opp.profit_percent, 50.0)
                
                # Определяем эмодзи для криптовалюты
                symbol = details['symbol']
                crypto_emoji = "₿" if symbol.startswith('BTC') else "Ξ" if symbol.startswith('ETH') else "🪙"
                
                content += f"""
<b>{i}.</b> {confidence_emoji} {crypto_emoji} <b>{symbol}</b>
💰 <b>{profit_display:.2f}%</b> | 🎯 {opp.confidence:.0%}
📈 {details['buy_exchange'].upper()} <code>${details['buy_price']:.6f}</code>
📉 {details['sell_exchange'].upper()} <code>${details['sell_price']:.6f}</code>
"""
        
        # Статистика внизу
        footer = f"""

📊 <b>СТАТИСТИКА:</b>
🔄 Циклов: <b>{self.stats['total_cycles']}</b>
🎯 Возможностей: <b>{self.stats['total_opportunities']}</b>
🏆 Лучшая: <b>{self.stats['best_profit']:.2f}%</b>
🏢 Биржи: <b>{len(self.all_pairs) if hasattr(self, 'all_pairs') else 0}</b>

<i>🤖 Автообновление каждые 5 сек</i>
        """
        
        return (header + content + footer).strip()

    async def update_telegram_message(self, opportunities):
        """Обновление сообщения в Telegram"""
        try:
            message = self.format_live_message(opportunities)
            
            if NOTIFICATION_CONFIG['telegram']['enabled']:
                message_id = await NotificationService.edit_telegram_message(message)
                if message_id:
                    self.stats['message_updates'] += 1
                    self.stats['last_update'] = datetime.now()
                    logger.debug(f"📱 Сообщение обновлено (#{self.stats['message_updates']})")
                
        except Exception as e:
            logger.error(f"❌ Ошибка обновления Telegram: {e}")

    async def monitor_loop(self, check_interval: int = 5):
        """Основной цикл live мониторинга"""
        logger.info("🔴 Запуск LIVE арбитражного мониторинга...")
        logger.info("⚡ Обновления каждые 5 секунд с редактированием сообщения")
        
        # Отправляем первое сообщение
        if NOTIFICATION_CONFIG['telegram']['enabled']:
            initial_message = self.format_live_message([])
            await NotificationService.send_telegram(initial_message)
            logger.info("📱 Отправлено начальное сообщение в Telegram")
        
        while self.running:
            try:
                cycle_start = datetime.now()
                
                # Получаем данные со всех бирж
                await self.fetch_all_exchange_data()
                
                opportunities = []
                
                if self.all_pairs:
                    # Ищем межбиржевые возможности
                    cross_opportunities = self.find_cross_exchange_arbitrage()
                    
                    # Ищем треугольные возможности
                    triangular_opportunities = []
                    for exchange in self.all_pairs.keys():
                        exchange_triangular = self.find_triangular_arbitrage(exchange)
                        triangular_opportunities.extend(exchange_triangular)
                    
                    # Объединяем и фильтруем
                    all_opportunities = cross_opportunities + triangular_opportunities
                    opportunities = [
                        opp for opp in all_opportunities 
                        if (opp.profit_percent >= self.min_profit_threshold and
                            opp.confidence >= self.min_confidence)
                    ]
                    
                    # Сортируем по взвешенной прибыли
                    opportunities.sort(
                        key=lambda x: x.profit_percent * x.confidence, 
                        reverse=True
                    )
                
                # Обновляем статистику
                self.stats['total_cycles'] += 1
                self.stats['total_opportunities'] += len(opportunities)
                self.stats['current_opportunities'] = opportunities
                
                if opportunities:
                    best_profit = opportunities[0].profit_percent
                    if best_profit > self.stats['best_profit']:
                        self.stats['best_profit'] = best_profit
                
                cycle_time = (datetime.now() - cycle_start).total_seconds()
                total_pairs = sum(len(pairs) for pairs in self.all_pairs.values()) if hasattr(self, 'all_pairs') else 0
                
                # Обновляем сообщение в Telegram
                await self.update_telegram_message(opportunities)
                
                # Логируем статистику (реже, чтобы не спамить)
                if self.stats['total_cycles'] % 12 == 0:  # Каждую минуту (12 * 5 сек)
                    logger.info(f"🔴 Live #{self.stats['total_cycles']} за {cycle_time:.1f}с | "
                              f"Биржи: {len(self.all_pairs) if hasattr(self, 'all_pairs') else 0} | "
                              f"Пары: {total_pairs:,} | "
                              f"Возможности: {len(opportunities)} | "
                              f"Обновлений: {self.stats['message_updates']}")
                
                # Показываем общую статистику каждые 5 минут
                if self.stats['total_cycles'] % 60 == 0:  # 60 * 5 сек = 5 минут
                    uptime = datetime.now() - self.stats['start_time']
                    avg_opportunities = self.stats['total_opportunities'] / self.stats['total_cycles']
                    
                    logger.info(f"📈 СТАТИСТИКА (uptime: {uptime}):")
                    logger.info(f"   Циклов: {self.stats['total_cycles']}")
                    logger.info(f"   Всего возможностей: {self.stats['total_opportunities']}")
                    logger.info(f"   Среднее за цикл: {avg_opportunities:.1f}")
                    logger.info(f"   Лучшая прибыль: {self.stats['best_profit']:.2f}%")
                    logger.info(f"   Обновлений сообщения: {self.stats['message_updates']}")
                
                # Пауза перед следующим циклом
                await asyncio.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("Получен сигнал остановки")
                self.running = False
                break
            except Exception as e:
                logger.error(f"❌ Критическая ошибка в цикле мониторинга: {e}")
                # Не останавливаемся при ошибках, продолжаем работу
                await asyncio.sleep(check_interval)

    def stop(self):
        """Остановка мониторинга"""
        self.running = False
        logger.info("🛑 Остановка live мониторинга...")

async def main():
    """Главная функция для live мониторинга"""
    logger.info("🔴 Запуск LIVE арбитражного монитора")
    logger.info("⚡ Обновление каждые 5 секунд с редактированием одного сообщения")
    
    monitor = LiveArbitrageMonitor()
    
    # Обработка сигналов для корректного завершения
    def signal_handler(signum, frame):
        logger.info(f"Получен сигнал {signum}")
        monitor.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await monitor.run(check_interval=5)
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
        logger.info(f"   Обновлений: {monitor.stats['message_updates']}")
        logger.info(f"   Лучшая прибыль: {monitor.stats['best_profit']:.2f}%")
        
        # Отправляем финальное сообщение
        if NOTIFICATION_CONFIG['telegram']['enabled']:
            final_message = f"""
🔴 <b>LIVE МОНИТОР ОСТАНОВЛЕН</b>

⏰ {datetime.now().strftime('%H:%M:%S')}
🕐 Работал: {str(uptime).split('.')[0]}
🔄 Циклов: {monitor.stats['total_cycles']}
🎯 Возможностей: {monitor.stats['total_opportunities']}
🏆 Лучшая прибыль: {monitor.stats['best_profit']:.2f}%

<i>Мониторинг завершен</i>
            """
            await NotificationService.edit_telegram_message(final_message)
        
        logger.info("👋 Live мониторинг завершен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Программа остановлена")
    except Exception as e:
        print(f"💥 Ошибка запуска: {e}")
        sys.exit(1)