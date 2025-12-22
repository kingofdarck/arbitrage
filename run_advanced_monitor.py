#!/usr/bin/env python3
"""
Запуск продвинутого арбитражного монитора со всеми видами арбитража
"""

import asyncio
import sys
import signal
import argparse
from datetime import datetime
from typing import List
from enhanced_arbitrage_monitor import EnhancedArbitrageMonitor
from advanced_arbitrage_monitor import AdvancedArbitrageMonitor, ArbitrageOpportunity
from config import MONITORING_CONFIG, EXCHANGES, ARBITRAGE_CONFIG
from notifications import NotificationService
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('advanced_arbitrage.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class UnifiedArbitrageMonitor(EnhancedArbitrageMonitor, AdvancedArbitrageMonitor):
    """Объединенный монитор всех видов арбитража"""
    
    def __init__(self, enabled_types=None, **kwargs):
        # Инициализируем оба родительских класса
        EnhancedArbitrageMonitor.__init__(self)
        AdvancedArbitrageMonitor.__init__(self)
        
        # Настройки
        self.enabled_arbitrage_types = enabled_types or list(ARBITRAGE_CONFIG.keys())
        self.min_profit_threshold = kwargs.get('min_profit', 0.3)
        self.min_confidence = kwargs.get('min_confidence', 0.5)
        self.max_notifications_per_cycle = kwargs.get('max_notifications', 5)
        self.running = True
        
        # Статистика
        self.stats = {
            'total_cycles': 0,
            'opportunities_by_type': {t: 0 for t in self.enabled_arbitrage_types},
            'best_profit_by_type': {t: 0 for t in self.enabled_arbitrage_types},
            'start_time': datetime.now()
        }
        
        logger.info(f"🎯 Инициализирован объединенный монитор")
        logger.info(f"📊 Активные типы арбитража: {', '.join(self.enabled_arbitrage_types)}")
        logger.info(f"⚙️ Настройки: мин. прибыль {self.min_profit_threshold}%, "
                   f"мин. уверенность {self.min_confidence}")

    async def find_all_opportunities(self) -> List[ArbitrageOpportunity]:
        """Поиск всех видов арбитражных возможностей"""
        all_opportunities = []
        
        try:
            # 1. Межбиржевой арбитраж (из EnhancedArbitrageMonitor)
            if 'cross_exchange' in self.enabled_arbitrage_types:
                cross_opps = self.find_cross_exchange_arbitrage()
                # Конвертируем в новый формат
                for opp in cross_opps:
                    new_opp = ArbitrageOpportunity(
                        type='cross_exchange',
                        subtype='price_difference',
                        profit_percent=opp.profit_percent,
                        confidence=opp.confidence,
                        risk_level='low',
                        details=opp.details,
                        timestamp=opp.timestamp
                    )
                    all_opportunities.append(new_opp)
                
                logger.debug(f"Межбиржевой: {len(cross_opps)} возможностей")
            
            # 2. Треугольный арбитраж (из EnhancedArbitrageMonitor)
            if 'triangular' in self.enabled_arbitrage_types:
                triangular_opps = []
                for exchange in self.all_pairs.keys():
                    exchange_triangular = self.find_triangular_arbitrage(exchange)
                    for opp in exchange_triangular:
                        new_opp = ArbitrageOpportunity(
                            type='triangular',
                            subtype=opp.details.get('direction', 'unknown'),
                            profit_percent=opp.profit_percent,
                            confidence=opp.confidence,
                            risk_level='medium',
                            details=opp.details,
                            timestamp=opp.timestamp
                        )
                        triangular_opps.append(new_opp)
                
                all_opportunities.extend(triangular_opps)
                logger.debug(f"Треугольный: {len(triangular_opps)} возможностей")
            
            # 3-9. Продвинутые виды арбитража (из AdvancedArbitrageMonitor)
            advanced_methods = {
                'statistical': self.find_statistical_arbitrage,
                'temporal': self.find_temporal_arbitrage,
                'spread': self.find_spread_arbitrage,
                'liquidity': self.find_liquidity_arbitrage,
                'index': self.find_index_arbitrage,
                'staking': self.find_staking_arbitrage,
                'funding': self.find_funding_rate_arbitrage
            }
            
            for arb_type, method in advanced_methods.items():
                if arb_type in self.enabled_arbitrage_types:
                    try:
                        opps = method()
                        all_opportunities.extend(opps)
                        logger.debug(f"{arb_type.capitalize()}: {len(opps)} возможностей")
                    except Exception as e:
                        logger.error(f"Ошибка в {arb_type} арбитраже: {e}")
            
        except Exception as e:
            logger.error(f"Ошибка при поиске возможностей: {e}")
        
        # Фильтруем по настройкам
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
        
        return filtered_opportunities

    async def send_notification(self, opportunity: ArbitrageOpportunity):
        """Отправка уведомления о возможности"""
        message = self.format_opportunity_message(opportunity)
        
        # Логируем
        risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(opportunity.risk_level, "⚪")
        logger.info(f"🚨 {risk_emoji} {opportunity.type.upper()}: {opportunity.profit_percent:.2f}% "
                   f"(уверенность: {opportunity.confidence:.1%})")
        
        # Отправляем уведомления
        try:
            await NotificationService.send_all(message)
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
        
        # Сохраняем в историю
        with open('advanced_opportunities.log', 'a', encoding='utf-8') as f:
            f.write(f"{opportunity.timestamp.isoformat()},{opportunity.type},"
                   f"{opportunity.subtype},{opportunity.profit_percent:.4f},"
                   f"{opportunity.confidence:.4f},{opportunity.risk_level},"
                   f"{opportunity.details}\n")

    def format_opportunity_message(self, opportunity: ArbitrageOpportunity) -> str:
        """Форматирование сообщения для разных типов арбитража"""
        risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(opportunity.risk_level, "⚪")
        type_emoji = {
            'cross_exchange': '🔄',
            'triangular': '🔺', 
            'statistical': '📊',
            'temporal': '⏰',
            'spread': '📈',
            'liquidity': '💧',
            'index': '📦',
            'staking': '🔒',
            'funding': '💰'
        }.get(opportunity.type, '🎯')
        
        header = f"""
{type_emoji} {opportunity.type.upper().replace('_', ' ')} АРБИТРАЖ {risk_emoji}

💰 Прибыль: {opportunity.profit_percent:.2f}%
🎯 Уверенность: {opportunity.confidence:.1%}
⚠️ Риск: {opportunity.risk_level.upper()}
⏰ Время: {opportunity.timestamp.strftime('%H:%M:%S')}
        """
        
        # Специфичные детали для каждого типа
        if opportunity.type == 'cross_exchange':
            details = opportunity.details
            return header + f"""
🪙 Пара: {details['symbol']}
📈 Купить на {details['buy_exchange'].upper()}: ${details['buy_price']:.6f}
📉 Продать на {details['sell_exchange'].upper()}: ${details['sell_price']:.6f}
💸 Комиссии: {details['fees']['total']:.2f}%
            """
        
        elif opportunity.type == 'triangular':
            details = opportunity.details
            return header + f"""
🏢 Биржа: {details['exchange'].upper()}
🔄 Путь: {details['path']}
🧮 Расчет: {details['calculation']}
💸 Комиссии: {details['total_fees']:.2f}%
            """
        
        elif opportunity.type == 'statistical':
            details = opportunity.details
            return header + f"""
📊 Пары: {details['symbol1']} / {details['symbol2']}
🔗 Корреляция: {details['correlation']:.2f}
📈 Z-Score: {details['z_score']:.2f}
🎯 Действие: {details['action'].upper()} {details['target_symbol']}
            """
        
        elif opportunity.type == 'temporal':
            details = opportunity.details
            return header + f"""
🪙 Пара: {details['symbol']}
⏰ Задержка: {details['time_lag']:.0f} сек
🐌 Медленная биржа: {details['slow_exchange'].upper()} (${details['slow_price']:.6f})
🚀 Быстрая биржа: {details['fast_exchange'].upper()} (${details['fast_price']:.6f})
            """
        
        elif opportunity.type == 'liquidity':
            details = opportunity.details
            return header + f"""
🪙 Пара: {details['symbol']}
📈 Купить на {details['buy_exchange'].upper()}: ${details['buy_price']:.6f}
📉 Продать на {details['sell_exchange'].upper()}: ${details['sell_price']:.6f}
💧 Доступный объем: {details['available_volume']:.2f}
            """
        
        elif opportunity.type == 'staking':
            details = opportunity.details
            return header + f"""
🔒 Токены: {details['staked_token']} / {details['base_token']}
💰 Дисконт: {details['discount_percent']:.2f}%
📈 Годовая ставка: {details['annual_staking_rate']:.1f}%
🏢 Биржа: {details['exchange'].upper()}
            """
        
        else:
            return header + f"\n📋 Детали: {opportunity.details}"

    async def monitor_loop(self, check_interval: int = 30):
        """Основной цикл мониторинга всех видов арбитража"""
        logger.info("🚀 Запуск объединенного мониторинга всех видов арбитража...")
        
        while self.running:
            try:
                cycle_start = datetime.now()
                
                # Получаем данные (из обоих родительских классов)
                await self.fetch_all_exchange_data()  # EnhancedArbitrageMonitor
                await self.fetch_all_data()  # AdvancedArbitrageMonitor
                
                # Ищем все возможности
                opportunities = await self.find_all_opportunities()
                
                # Обновляем статистику
                self.stats['total_cycles'] += 1
                
                type_counts = {}
                for opp in opportunities:
                    opp_type = opp.type
                    type_counts[opp_type] = type_counts.get(opp_type, 0) + 1
                    self.stats['opportunities_by_type'][opp_type] += 1
                    
                    current_best = self.stats['best_profit_by_type'][opp_type]
                    if opp.profit_percent > current_best:
                        self.stats['best_profit_by_type'][opp_type] = opp.profit_percent
                
                # Отправляем уведомления о лучших возможностях
                top_opportunities = opportunities[:self.max_notifications_per_cycle]
                
                cycle_time = (datetime.now() - cycle_start).total_seconds()
                total_pairs = sum(len(pairs) for pairs in self.all_pairs.values()) if hasattr(self, 'all_pairs') else 0
                
                # Логируем статистику цикла
                logger.info(f"📊 Цикл #{self.stats['total_cycles']} за {cycle_time:.1f}с | "
                          f"Биржи: {len(self.all_pairs) if hasattr(self, 'all_pairs') else 0} | "
                          f"Пары: {total_pairs:,} | "
                          f"Возможности: {len(opportunities)}")
                
                if type_counts:
                    type_stats = " | ".join([f"{t}: {c}" for t, c in type_counts.items()])
                    logger.info(f"   По типам: {type_stats}")
                
                if top_opportunities:
                    logger.info(f"🎯 Отправляем {len(top_opportunities)} лучших возможностей:")
                    
                    for i, opportunity in enumerate(top_opportunities):
                        await self.send_notification(opportunity)
                        
                        # Краткий лог
                        risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(opportunity.risk_level, "⚪")
                        logger.info(f"  {i+1}. {risk_emoji} {opportunity.type}/{opportunity.subtype}: "
                                  f"{opportunity.profit_percent:.2f}% (уверенность: {opportunity.confidence:.1%})")
                        
                        # Пауза между уведомлениями
                        if i < len(top_opportunities) - 1:
                            await asyncio.sleep(2)
                
                # Показываем общую статистику каждые 10 циклов
                if self.stats['total_cycles'] % 10 == 0:
                    uptime = datetime.now() - self.stats['start_time']
                    total_opportunities = sum(self.stats['opportunities_by_type'].values())
                    
                    logger.info(f"📈 СТАТИСТИКА (uptime: {uptime}):")
                    logger.info(f"   Циклов: {self.stats['total_cycles']}")
                    logger.info(f"   Всего возможностей: {total_opportunities}")
                    
                    for arb_type, count in self.stats['opportunities_by_type'].items():
                        if count > 0:
                            best = self.stats['best_profit_by_type'][arb_type]
                            logger.info(f"   {arb_type}: {count} (лучшая: {best:.2f}%)")
                
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
        logger.info("🛑 Остановка объединенного мониторинга...")

def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(description='Продвинутый арбитражный монитор')
    
    parser.add_argument('--types', nargs='+', 
                       choices=list(ARBITRAGE_CONFIG.keys()),
                       default=list(ARBITRAGE_CONFIG.keys()),
                       help='Типы арбитража для мониторинга')
    parser.add_argument('--min-profit', type=float, default=0.3,
                       help='Минимальная прибыль (%)')
    parser.add_argument('--min-confidence', type=float, default=0.5,
                       help='Минимальная уверенность (0-1)')
    parser.add_argument('--interval', type=int, default=30,
                       help='Интервал проверки (секунды)')
    parser.add_argument('--max-notifications', type=int, default=5,
                       help='Максимум уведомлений за цикл')
    parser.add_argument('--test-mode', action='store_true',
                       help='Тестовый режим')
    
    return parser.parse_args()

async def main():
    """Главная функция"""
    args = parse_arguments()
    
    logger.info(f"🚀 Запуск продвинутого арбитражного монитора")
    logger.info(f"📊 Типы арбитража: {', '.join(args.types)}")
    logger.info(f"⚙️ Параметры: прибыль≥{args.min_profit}%, уверенность≥{args.min_confidence}, "
               f"интервал={args.interval}с")
    
    if args.test_mode:
        logger.info("🧪 ТЕСТОВЫЙ РЕЖИМ")
    
    monitor = UnifiedArbitrageMonitor(
        enabled_types=args.types,
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
        total_opportunities = sum(monitor.stats['opportunities_by_type'].values())
        
        logger.info(f"📊 ФИНАЛЬНАЯ СТАТИСТИКА:")
        logger.info(f"   Время работы: {uptime}")
        logger.info(f"   Циклов: {monitor.stats['total_cycles']}")
        logger.info(f"   Всего возможностей: {total_opportunities}")
        
        for arb_type, count in monitor.stats['opportunities_by_type'].items():
            if count > 0:
                best = monitor.stats['best_profit_by_type'][arb_type]
                logger.info(f"   {arb_type}: {count} (лучшая: {best:.2f}%)")
        
        logger.info("👋 Мониторинг завершен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Программа остановлена")
    except Exception as e:
        print(f"💥 Ошибка запуска: {e}")