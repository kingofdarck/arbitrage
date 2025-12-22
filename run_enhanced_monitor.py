#!/usr/bin/env python3
"""
Запуск расширенного арбитражного монитора
Поддержка множества бирж и всех торговых пар
"""

import asyncio
import sys
import signal
import argparse
from datetime import datetime
from enhanced_arbitrage_monitor import EnhancedArbitrageMonitor, ArbitrageOpportunity
from config import MONITORING_CONFIG, EXCHANGES
from notifications import NotificationService
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_arbitrage.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ProductionArbitrageMonitor(EnhancedArbitrageMonitor):
    """Продакшн версия арбитражного монитора с уведомлениями"""
    
    def __init__(self, min_profit=0.3, min_confidence=0.5, max_notifications=3):
        super().__init__()
        self.min_profit_threshold = min_profit
        self.min_confidence = min_confidence
        self.max_notifications_per_cycle = max_notifications
        self.running = True
        self.stats = {
            'total_cycles': 0,
            'total_opportunities': 0,
            'best_profit': 0,
            'start_time': datetime.now()
        }
        
        logger.info(f"🎯 Настройки: мин. прибыль {min_profit}%, мин. уверенность {min_confidence}")
    
    async def send_notification(self, opportunity: ArbitrageOpportunity):
        """Отправка уведомления о возможности"""
        message = self.format_opportunity_message(opportunity)
        
        # Логируем
        confidence_emoji = "🟢" if opportunity.confidence > 0.7 else "🟡" if opportunity.confidence > 0.4 else "🔴"
        logger.info(f"🚨 {confidence_emoji} ВОЗМОЖНОСТЬ: {opportunity.profit_percent:.2f}% "
                   f"(уверенность: {opportunity.confidence:.2f})")
        
        # Отправляем уведомления
        try:
            await NotificationService.send_all(message)
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
        
        # Сохраняем в историю
        with open('opportunities_detailed.log', 'a', encoding='utf-8') as f:
            f.write(f"{opportunity.timestamp.isoformat()},{opportunity.type},"
                   f"{opportunity.profit_percent:.4f},{opportunity.confidence:.4f},"
                   f"{opportunity.details}\n")
    
    def format_opportunity_message(self, opportunity: ArbitrageOpportunity) -> str:
        """Форматирование сообщения с подробностями"""
        confidence_emoji = "🟢" if opportunity.confidence > 0.7 else "🟡" if opportunity.confidence > 0.4 else "🔴"
        
        if opportunity.type == 'cross_exchange':
            details = opportunity.details
            return f"""
🚨 МЕЖБИРЖЕВОЙ АРБИТРАЖ {confidence_emoji}

💰 Прибыль: {opportunity.profit_percent:.2f}%
🎯 Уверенность: {opportunity.confidence:.1%}
🪙 Пара: {details['symbol']}

📈 КУПИТЬ на {details['buy_exchange'].upper()}
   💵 Цена: ${details['buy_price']:.6f}
   📊 Объем 24ч: ${details['buy_volume_24h']:,.0f}

📉 ПРОДАТЬ на {details['sell_exchange'].upper()}
   💵 Цена: ${details['sell_price']:.6f}
   📊 Объем 24ч: ${details['sell_volume_24h']:,.0f}

💸 Комиссии: {details['fees']['total']:.2f}%
⏰ Время: {opportunity.timestamp.strftime('%H:%M:%S')}

🏢 Все биржи:
{chr(10).join([f"   {ex.upper()}: ${price:.6f} (${vol:,.0f})" 
               for ex, price, vol in zip(details['all_prices'].keys(), 
                                       details['all_prices'].values(),
                                       details['all_volumes'].values())])}
            """
        else:  # triangular
            details = opportunity.details
            return f"""
🔺 ТРЕУГОЛЬНЫЙ АРБИТРАЖ {confidence_emoji}

💰 Прибыль: {opportunity.profit_percent:.2f}%
🎯 Уверенность: {opportunity.confidence:.1%}
🏢 Биржа: {details['exchange'].upper()}
🔄 Направление: {details['direction']}

📈 Путь торговли:
   {details['path']}

📊 Пары и цены:
{chr(10).join([f"   {pair}: ${price:.6f} (${vol:,.0f})" 
               for pair, price, vol in zip(details['pairs'], 
                                         details['prices'],
                                         details['volumes'])])}

🧮 Расчет: {details['calculation']}
💸 Комиссии: {details['total_fees']:.2f}%
⏰ Время: {opportunity.timestamp.strftime('%H:%M:%S')}
            """
    
    async def monitor_loop(self, check_interval: int = 30):
        """Расширенный цикл мониторинга с уведомлениями"""
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
                
                # Ищем возможности
                cross_opportunities = self.find_cross_exchange_arbitrage()
                
                triangular_opportunities = []
                for exchange in self.all_pairs.keys():
                    exchange_triangular = self.find_triangular_arbitrage(exchange)
                    triangular_opportunities.extend(exchange_triangular)
                
                # Фильтруем по уверенности и сортируем
                all_opportunities = cross_opportunities + triangular_opportunities
                filtered_opportunities = [
                    opp for opp in all_opportunities 
                    if opp.confidence >= self.min_confidence
                ]
                
                # Сортируем по взвешенной прибыли (прибыль * уверенность)
                filtered_opportunities.sort(
                    key=lambda x: x.profit_percent * x.confidence, 
                    reverse=True
                )
                
                # Обновляем статистику
                self.stats['total_cycles'] += 1
                self.stats['total_opportunities'] += len(filtered_opportunities)
                if filtered_opportunities:
                    self.stats['best_profit'] = max(
                        self.stats['best_profit'], 
                        filtered_opportunities[0].profit_percent
                    )
                
                # Отправляем уведомления о лучших возможностях
                top_opportunities = filtered_opportunities[:self.max_notifications_per_cycle]
                
                cycle_time = (datetime.now() - cycle_start).total_seconds()
                total_pairs = sum(len(pairs) for pairs in self.all_pairs.values())
                
                # Логируем статистику цикла
                logger.info(f"📊 Цикл #{self.stats['total_cycles']} за {cycle_time:.1f}с | "
                          f"Биржи: {len(self.all_pairs)} | "
                          f"Пары: {total_pairs:,} | "
                          f"Возможности: {len(all_opportunities)} | "
                          f"Качественные: {len(filtered_opportunities)}")
                
                if top_opportunities:
                    logger.info(f"🎯 Отправляем {len(top_opportunities)} лучших возможностей:")
                    
                    for i, opportunity in enumerate(top_opportunities):
                        await self.send_notification(opportunity)
                        
                        # Краткий лог
                        logger.info(f"  {i+1}. {opportunity.type}: {opportunity.profit_percent:.2f}% "
                                  f"(уверенность: {opportunity.confidence:.1%})")
                        
                        # Небольшая пауза между уведомлениями
                        if i < len(top_opportunities) - 1:
                            await asyncio.sleep(2)
                
                # Показываем общую статистику каждые 10 циклов
                if self.stats['total_cycles'] % 10 == 0:
                    uptime = datetime.now() - self.stats['start_time']
                    avg_opportunities = self.stats['total_opportunities'] / self.stats['total_cycles']
                    
                    logger.info(f"📈 СТАТИСТИКА (uptime: {uptime}):")
                    logger.info(f"   Циклов: {self.stats['total_cycles']}")
                    logger.info(f"   Всего возможностей: {self.stats['total_opportunities']}")
                    logger.info(f"   Среднее за цикл: {avg_opportunities:.1f}")
                    logger.info(f"   Лучшая прибыль: {self.stats['best_profit']:.2f}%")
                
                # Пауза перед следующим циклом
                await asyncio.sleep(check_interval)
                
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
        logger.info("🛑 Остановка мониторинга...")

def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(description='Расширенный арбитражный монитор')
    
    parser.add_argument('--min-profit', type=float, default=0.3,
                       help='Минимальная прибыль для уведомления (%)')
    parser.add_argument('--min-confidence', type=float, default=0.5,
                       help='Минимальная уверенность (0-1)')
    parser.add_argument('--interval', type=int, default=30,
                       help='Интервал проверки (секунды)')
    parser.add_argument('--max-notifications', type=int, default=3,
                       help='Максимум уведомлений за цикл')
    parser.add_argument('--test-mode', action='store_true',
                       help='Тестовый режим (без уведомлений)')
    
    return parser.parse_args()

async def main():
    """Главная функция с обработкой аргументов"""
    args = parse_arguments()
    
    logger.info(f"🚀 Запуск расширенного арбитражного монитора")
    logger.info(f"⚙️ Параметры: прибыль≥{args.min_profit}%, уверенность≥{args.min_confidence}, "
               f"интервал={args.interval}с, уведомления≤{args.max_notifications}")
    
    if args.test_mode:
        logger.info("🧪 ТЕСТОВЫЙ РЕЖИМ - уведомления отключены")
    
    monitor = ProductionArbitrageMonitor(
        min_profit=args.min_profit,
        min_confidence=args.min_confidence,
        max_notifications=args.max_notifications if not args.test_mode else 0
    )
    
    # Обработка сигналов
    def signal_handler(signum, frame):
        logger.info(f"Получен сигнал {signum}")
        monitor.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await monitor.run(check_interval=args.interval)
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
        logger.info(f"   Лучшая прибыль: {monitor.stats['best_profit']:.2f}%")
        logger.info("👋 Мониторинг завершен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Программа остановлена")
    except Exception as e:
        print(f"💥 Ошибка запуска: {e}")