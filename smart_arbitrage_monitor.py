#!/usr/bin/env python3
"""
Умный арбитражный монитор с дедупликацией возможностей
Отправляет уведомления только при обнаружении новых возможностей
Поддержка переменных окружения для бесплатного хостинга
"""

import asyncio
import sys
import signal
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enhanced_arbitrage_monitor import EnhancedArbitrageMonitor, ArbitrageOpportunity
from config import MONITORING_CONFIG, NOTIFICATION_CONFIG
from notifications import NotificationService
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_arbitrage.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Переопределяем настройки из переменных окружения для бесплатного хостинга
if os.getenv('TELEGRAM_BOT_TOKEN'):
    NOTIFICATION_CONFIG['telegram']['bot_token'] = os.getenv('TELEGRAM_BOT_TOKEN')
    logger.info("🔑 Используется токен бота из переменной окружения")

if os.getenv('TELEGRAM_CHAT_ID'):
    NOTIFICATION_CONFIG['telegram']['chat_id'] = os.getenv('TELEGRAM_CHAT_ID')
    logger.info("💬 Используется chat_id из переменной окружения")

@dataclass
class TrackedOpportunity:
    """Отслеживаемая арбитражная возможность"""
    opportunity_hash: str
    first_seen: datetime
    last_seen: datetime
    max_profit: float
    times_seen: int
    sent_notification: bool

class SmartArbitrageMonitor(EnhancedArbitrageMonitor):
    """Умный арбитражный монитор с дедупликацией"""
    
    def __init__(self):
        super().__init__()
        
        # Настройки из конфига
        self.min_profit_threshold = MONITORING_CONFIG['min_profit_threshold']  # 0.75%
        self.max_notifications_per_cycle = MONITORING_CONFIG['max_opportunities_per_notification']  # 15
        
        # Устанавливаем единый порог 0.75% для поиска и уведомлений
        self.search_min_profit = 0.75  # Ищем и уведомляем от 0.75%
        self.min_confidence = 0.3      # Минимальная уверенность
        
        # Отслеживание возможностей
        self.tracked_opportunities: Dict[str, TrackedOpportunity] = {}
        self.opportunity_expiry_hours = 2  # Возможности "устаревают" через 2 часа
        
        # Статистика
        self.stats = {
            'total_cycles': 0,
            'total_opportunities_found': 0,
            'new_opportunities_found': 0,
            'notifications_sent': 0,
            'duplicate_opportunities_filtered': 0,
            'expired_opportunities_cleaned': 0,
            'start_time': datetime.now(),
            'last_notification_time': None
        }
        
        self.running = True
        
        logger.info("🧠 Умный арбитражный монитор инициализирован")
        logger.info(f"📊 Настройки: мин. прибыль {self.min_profit_threshold}%")
        logger.info(f"🔍 Поиск и уведомления от {self.search_min_profit}%")
        logger.info(f"📱 Раздельные уведомления для каждого типа арбитража")

    def generate_opportunity_hash(self, opportunity: ArbitrageOpportunity) -> str:
        """Генерация хеша для идентификации возможности"""
        details = opportunity.details
        
        if opportunity.type == 'cross_exchange':
            # Для межбиржевого арбитража: символ + биржи
            hash_string = f"{details['symbol']}_{details['buy_exchange']}_{details['sell_exchange']}"
        else:
            # Для треугольного арбитража: биржа + путь
            hash_string = f"{details['exchange']}_{details['path']}"
        
        return hashlib.md5(hash_string.encode()).hexdigest()[:12]

    def is_opportunity_new(self, opportunity: ArbitrageOpportunity) -> bool:
        """Проверка, является ли возможность новой"""
        opp_hash = self.generate_opportunity_hash(opportunity)
        
        if opp_hash not in self.tracked_opportunities:
            return True
        
        tracked = self.tracked_opportunities[opp_hash]
        
        # Проверяем, не истекла ли возможность
        if datetime.now() - tracked.last_seen > timedelta(hours=self.opportunity_expiry_hours):
            return True
        
        # Проверяем, значительно ли выросла прибыль (более чем на 0.3%)
        profit_increase = opportunity.profit_percent - tracked.max_profit
        if profit_increase > 0.3:
            return True
        
        return False

    def update_tracked_opportunity(self, opportunity: ArbitrageOpportunity, is_new: bool):
        """Обновление информации об отслеживаемой возможности"""
        opp_hash = self.generate_opportunity_hash(opportunity)
        now = datetime.now()
        
        if opp_hash in self.tracked_opportunities:
            tracked = self.tracked_opportunities[opp_hash]
            tracked.last_seen = now
            tracked.times_seen += 1
            
            # Обновляем максимальную прибыль
            if opportunity.profit_percent > tracked.max_profit:
                tracked.max_profit = opportunity.profit_percent
            
            # Отмечаем, что отправили уведомление
            if is_new:
                tracked.sent_notification = True
        else:
            # Создаем новую запись
            self.tracked_opportunities[opp_hash] = TrackedOpportunity(
                opportunity_hash=opp_hash,
                first_seen=now,
                last_seen=now,
                max_profit=opportunity.profit_percent,
                times_seen=1,
                sent_notification=is_new
            )

    def cleanup_expired_opportunities(self):
        """Очистка устаревших возможностей"""
        now = datetime.now()
        expired_hashes = []
        
        for opp_hash, tracked in self.tracked_opportunities.items():
            if now - tracked.last_seen > timedelta(hours=self.opportunity_expiry_hours):
                expired_hashes.append(opp_hash)
        
        for opp_hash in expired_hashes:
            del self.tracked_opportunities[opp_hash]
            self.stats['expired_opportunities_cleaned'] += 1
        
        if expired_hashes:
            logger.debug(f"🧹 Очищено {len(expired_hashes)} устаревших возможностей")

    def format_cross_exchange_message(self, opportunities: List[ArbitrageOpportunity]) -> str:
        """Форматирование сообщения для межбиржевого арбитража"""
        if not opportunities:
            return ""
        
        message = f"""
🚨 МЕЖБИРЖЕВОЙ АРБИТРАЖ
⏰ {datetime.now().strftime('%H:%M:%S')} | Найдено: {len(opportunities)}

"""
        
        for i, opp in enumerate(opportunities, 1):
            details = opp.details
            confidence_emoji = "🟢" if opp.confidence > 0.7 else "🟡" if opp.confidence > 0.4 else "🔴"
            
            # Определяем эмодзи для криптовалюты
            symbol = details['symbol']
            crypto_emoji = "₿" if symbol.startswith('BTC') else "Ξ" if symbol.startswith('ETH') else "🪙"
            
            message += f"""
{i}. {confidence_emoji} {crypto_emoji} {symbol}
   💰 Прибыль: {opp.profit_percent:.2f}% | 🎯 {opp.confidence:.0%}
   📈 КУПИТЬ: {details['buy_exchange'].upper()} ${details['buy_price']:.6f}
   📉 ПРОДАТЬ: {details['sell_exchange'].upper()} ${details['sell_price']:.6f}
   📊 Объемы: ${details['buy_volume_24h']:,.0f} / ${details['sell_volume_24h']:,.0f}
   💸 Комиссии: {details['fees']['total']:.2f}%
"""
        
        return message.strip()

    def format_triangular_message(self, opportunities: List[ArbitrageOpportunity]) -> str:
        """Форматирование сообщения для треугольного арбитража"""
        if not opportunities:
            return ""
        
        message = f"""
🔺 ТРЕУГОЛЬНЫЙ АРБИТРАЖ
⏰ {datetime.now().strftime('%H:%M:%S')} | Найдено: {len(opportunities)}

"""
        
        for i, opp in enumerate(opportunities, 1):
            details = opp.details
            confidence_emoji = "🟢" if opp.confidence > 0.7 else "🟡" if opp.confidence > 0.4 else "🔴"
            
            message += f"""
{i}. {confidence_emoji} 🔺 {details['exchange'].upper()}
   💰 Прибыль: {opp.profit_percent:.2f}% | 🎯 {opp.confidence:.0%}
   🔄 Путь: {details['path']}
   📊 Мин. объем: ${min(details['volumes']):,.0f}
   💸 Комиссии: {details['total_fees']:.2f}%
   🧮 Расчет: {details['calculation']}
"""
        
        return message.strip()

    def format_telegram_message(self, opportunities: List[ArbitrageOpportunity]) -> str:
        """Форматирование общего сообщения для Telegram (устаревший метод)"""
        # Этот метод больше не используется, но оставляем для совместимости
        return self.format_cross_exchange_message(opportunities)

    async def start_health_server(self):
        """Запуск HTTP сервера для health check (для бесплатного хостинга)"""
        try:
            from aiohttp import web
            
            async def health_check(request):
                """Health check endpoint"""
                uptime = datetime.now() - self.stats['start_time']
                
                status_data = {
                    "status": "healthy",
                    "uptime_seconds": int(uptime.total_seconds()),
                    "uptime_human": str(uptime),
                    "total_cycles": self.stats['total_cycles'],
                    "new_opportunities": self.stats['new_opportunities_found'],
                    "notifications_sent": self.stats['notifications_sent'],
                    "tracked_opportunities": len(self.tracked_opportunities),
                    "timestamp": datetime.now().isoformat()
                }
                
                return web.json_response(status_data)
            
            app = web.Application()
            app.router.add_get('/health', health_check)
            app.router.add_get('/', health_check)
            
            runner = web.AppRunner(app)
            await runner.setup()
            
            # Используем порт из переменной окружения (для Heroku/Railway)
            port = int(os.getenv('PORT', 8000))
            site = web.TCPSite(runner, '0.0.0.0', port)
            await site.start()
            
            logger.info(f"🌐 Health check сервер запущен на порту {port}")
            
        except ImportError:
            logger.warning("⚠️ aiohttp не установлен, health check сервер недоступен")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска health check сервера: {e}")

    async def send_startup_notification(self):
        """Отправка уведомления о запуске системы"""
        try:
            startup_message = f"""
🧠 УМНЫЙ АРБИТРАЖНЫЙ МОНИТОР ЗАПУЩЕН

⏰ Время запуска: {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}
🌐 Платформа: {os.getenv('RAILWAY_ENVIRONMENT', os.getenv('RENDER', 'Локальная'))}
📊 Настройки:
   • Минимальная прибыль: {self.min_profit_threshold}%
   • Проверка каждые: 10 секунд
   • Раздельные уведомления по типам

🎯 Система готова к поиску арбитражных возможностей!
            """
            
            await NotificationService.send_telegram(startup_message.strip())
            logger.info("📱 Отправлено уведомление о запуске")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления о запуске: {e}")
        """Отправка раздельных уведомлений о новых возможностях по типам"""
        if not new_opportunities or not NOTIFICATION_CONFIG['telegram']['enabled']:
            return
        
        try:
            # Разделяем возможности по типам
            cross_exchange_opps = [opp for opp in new_opportunities if opp.type == 'cross_exchange']
            triangular_opps = [opp for opp in new_opportunities if opp.type == 'triangular']
            
            messages_sent = 0
            
            # Отправляем межбиржевые возможности
            if cross_exchange_opps:
                # Ограничиваем до 10 возможностей на сообщение
                limited_cross = cross_exchange_opps[:10]
                message = self.format_cross_exchange_message(limited_cross)
                
                # Добавляем статистику в конец сообщения
                message += f"""

📊 СТАТИСТИКА:
   🔄 Циклов: {self.stats['total_cycles']}
   🆕 Новых возможностей: {self.stats['new_opportunities_found']}
   📱 Уведомлений: {self.stats['notifications_sent']}
   🔍 Отслеживается: {len(self.tracked_opportunities)}
"""
                
                await NotificationService.send_telegram(message)
                messages_sent += 1
                logger.info(f"📱 Отправлено уведомление о {len(limited_cross)} межбиржевых возможностях")
            
            # Отправляем треугольные возможности
            if triangular_opps:
                # Ограничиваем до 8 возможностей на сообщение (они длиннее)
                limited_triangular = triangular_opps[:8]
                message = self.format_triangular_message(limited_triangular)
                
                # Добавляем статистику в конец сообщения
                message += f"""

📊 СТАТИСТИКА:
   🔄 Циклов: {self.stats['total_cycles']}
   🆕 Новых возможностей: {self.stats['new_opportunities_found']}
   📱 Уведомлений: {self.stats['notifications_sent']}
   🔍 Отслеживается: {len(self.tracked_opportunities)}
"""
                
                await NotificationService.send_telegram(message)
                messages_sent += 1
                logger.info(f"📱 Отправлено уведомление о {len(limited_triangular)} треугольных возможностях")
            
            self.stats['notifications_sent'] += messages_sent
            self.stats['last_notification_time'] = datetime.now()
            
    async def send_new_opportunities_notification(self, new_opportunities: List[ArbitrageOpportunity]):
        """Отправка раздельных уведомлений о новых возможностях по типам"""
        if not new_opportunities or not NOTIFICATION_CONFIG['telegram']['enabled']:
            return
        
        try:
            # Разделяем возможности по типам
            cross_exchange_opps = [opp for opp in new_opportunities if opp.type == 'cross_exchange']
            triangular_opps = [opp for opp in new_opportunities if opp.type == 'triangular']
            
            messages_sent = 0
            
            # Отправляем межбиржевые возможности
            if cross_exchange_opps:
                # Ограничиваем до 10 возможностей на сообщение
                limited_cross = cross_exchange_opps[:10]
                message = self.format_cross_exchange_message(limited_cross)
                
                # Добавляем статистику в конец сообщения
                message += f"""

📊 СТАТИСТИКА:
   🔄 Циклов: {self.stats['total_cycles']}
   🆕 Новых возможностей: {self.stats['new_opportunities_found']}
   📱 Уведомлений: {self.stats['notifications_sent']}
   🔍 Отслеживается: {len(self.tracked_opportunities)}
"""
                
                await NotificationService.send_telegram(message)
                messages_sent += 1
                logger.info(f"📱 Отправлено уведомление о {len(limited_cross)} межбиржевых возможностях")
            
            # Отправляем треугольные возможности
            if triangular_opps:
                # Ограничиваем до 8 возможностей на сообщение (они длиннее)
                limited_triangular = triangular_opps[:8]
                message = self.format_triangular_message(limited_triangular)
                
                # Добавляем статистику в конец сообщения
                message += f"""

📊 СТАТИСТИКА:
   🔄 Циклов: {self.stats['total_cycles']}
   🆕 Новых возможностей: {self.stats['new_opportunities_found']}
   📱 Уведомлений: {self.stats['notifications_sent']}
   🔍 Отслеживается: {len(self.tracked_opportunities)}
"""
                
                await NotificationService.send_telegram(message)
                messages_sent += 1
                logger.info(f"📱 Отправлено уведомление о {len(limited_triangular)} треугольных возможностях")
            
            self.stats['notifications_sent'] += messages_sent
            self.stats['last_notification_time'] = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления: {e}")

    async def run(self, check_interval: int = 10):
        """Запуск монитора с поддержкой бесплатного хостинга"""
        await self.start_session()
        
        # Запускаем health check сервер для бесплатного хостинга
        await self.start_health_server()
        
        # Отправляем уведомление о запуске
        await self.send_startup_notification()
        
        try:
            await self.monitor_loop(check_interval)
        finally:
            await self.close_session()

    async def monitor_loop(self, check_interval: int = 10):
        """Основной цикл умного мониторинга"""
        logger.info("🚀 Запуск умного мониторинга арбитражных возможностей...")
        
        while self.running:
            try:
                cycle_start = datetime.now()
                
                # Получаем данные со всех бирж
                await self.fetch_all_exchange_data()
                
                if not self.all_pairs:
                    logger.warning("⚠️ Не получены данные ни с одной биржи")
                    await asyncio.sleep(check_interval)
                    continue
                
                # Временно снижаем порог для поиска
                original_threshold = self.min_profit_threshold
                self.min_profit_threshold = self.search_min_profit
                
                # Ищем межбиржевые возможности
                cross_opportunities = self.find_cross_exchange_arbitrage()
                
                # Ищем треугольные возможности
                triangular_opportunities = []
                for exchange in self.all_pairs.keys():
                    exchange_triangular = self.find_triangular_arbitrage(exchange)
                    triangular_opportunities.extend(exchange_triangular)
                
                # Восстанавливаем порог
                self.min_profit_threshold = original_threshold
                
                # Объединяем все возможности
                all_opportunities = cross_opportunities + triangular_opportunities
                
                # Фильтруем по минимальной уверенности
                filtered_opportunities = [
                    opp for opp in all_opportunities 
                    if opp.confidence >= self.min_confidence
                ]
                
                # Сортируем по взвешенной прибыли
                filtered_opportunities.sort(
                    key=lambda x: x.profit_percent * x.confidence, 
                    reverse=True
                )
                
                # Обновляем статистику
                self.stats['total_cycles'] += 1
                self.stats['total_opportunities_found'] += len(filtered_opportunities)
                
                # Определяем новые возможности
                new_opportunities = []
                
                for opp in filtered_opportunities:
                    # Проверяем только возможности с прибылью выше порога
                    if opp.profit_percent >= self.min_profit_threshold:
                        is_new = self.is_opportunity_new(opp)
                        
                        if is_new:
                            new_opportunities.append(opp)
                            self.stats['new_opportunities_found'] += 1
                        else:
                            self.stats['duplicate_opportunities_filtered'] += 1
                        
                        # Обновляем информацию об отслеживании
                        self.update_tracked_opportunity(opp, is_new)
                
                # Ограничиваем общее количество уведомлений
                new_opportunities = new_opportunities[:self.max_notifications_per_cycle]
                
                # Очищаем устаревшие возможности
                self.cleanup_expired_opportunities()
                
                cycle_time = (datetime.now() - cycle_start).total_seconds()
                total_pairs = sum(len(pairs) for pairs in self.all_pairs.values())
                
                # Логируем статистику цикла
                logger.info(f"🧠 Цикл #{self.stats['total_cycles']} за {cycle_time:.1f}с | "
                          f"Пары: {total_pairs:,} | "
                          f"Найдено: {len(filtered_opportunities)} | "
                          f"Новых: {len(new_opportunities)} | "
                          f"Отслеживается: {len(self.tracked_opportunities)}")
                
                # Отправляем уведомления только о новых возможностях
                if new_opportunities:
                    await self.send_new_opportunities_notification(new_opportunities)
                    
                    # Показываем детали новых возможностей
                    cross_count = len([opp for opp in new_opportunities if opp.type == 'cross_exchange'])
                    triangular_count = len([opp for opp in new_opportunities if opp.type == 'triangular'])
                    
                    logger.info(f"📱 Отправлены уведомления: межбиржевых {cross_count}, треугольных {triangular_count}")
                    
                    for i, opp in enumerate(new_opportunities):
                        details = opp.details
                        if opp.type == 'cross_exchange':
                            logger.info(f"  🆕 {i+1}. {details['symbol']}: {opp.profit_percent:.2f}% "
                                      f"({details['buy_exchange']} → {details['sell_exchange']})")
                        else:
                            logger.info(f"  🆕 {i+1}. Треугольный {details['exchange']}: {opp.profit_percent:.2f}% "
                                      f"({details['path']})")
                else:
                    logger.info("📊 Новых качественных возможностей не найдено")
                
                # Показываем общую статистику каждые 20 циклов
                if self.stats['total_cycles'] % 20 == 0:
                    uptime = datetime.now() - self.stats['start_time']
                    avg_opportunities = self.stats['total_opportunities_found'] / self.stats['total_cycles']
                    
                    logger.info(f"📈 СТАТИСТИКА (uptime: {uptime}):")
                    logger.info(f"   Циклов: {self.stats['total_cycles']}")
                    logger.info(f"   Всего возможностей: {self.stats['total_opportunities_found']}")
                    logger.info(f"   Новых возможностей: {self.stats['new_opportunities_found']}")
                    logger.info(f"   Дубликатов отфильтровано: {self.stats['duplicate_opportunities_filtered']}")
                    logger.info(f"   Уведомлений отправлено: {self.stats['notifications_sent']}")
                    logger.info(f"   Среднее за цикл: {avg_opportunities:.1f}")
                    logger.info(f"   Отслеживается возможностей: {len(self.tracked_opportunities)}")
                
                # Пауза перед следующим циклом
                await asyncio.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("Получен сигнал остановки")
                self.running = False
                break
            except Exception as e:
                logger.error(f"❌ Критическая ошибка в цикле мониторинга: {e}")
                await asyncio.sleep(10)

    def stop(self):
        """Остановка мониторинга"""
        self.running = False
        logger.info("🛑 Остановка умного мониторинга...")

async def main():
    """Главная функция"""
    logger.info("🧠 Запуск умного арбитражного монитора")
    logger.info("📱 Уведомления отправляются только о НОВЫХ возможностях")
    
    monitor = SmartArbitrageMonitor()
    
    # Обработка сигналов для корректного завершения
    def signal_handler(signum, frame):
        logger.info(f"Получен сигнал {signum}")
        monitor.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await monitor.run(check_interval=10)
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
        logger.info(f"   Всего возможностей: {monitor.stats['total_opportunities_found']}")
        logger.info(f"   Новых возможностей: {monitor.stats['new_opportunities_found']}")
        logger.info(f"   Дубликатов отфильтровано: {monitor.stats['duplicate_opportunities_filtered']}")
        logger.info(f"   Уведомлений отправлено: {monitor.stats['notifications_sent']}")
        logger.info(f"   Очищено устаревших: {monitor.stats['expired_opportunities_cleaned']}")
        logger.info("👋 Умный мониторинг завершен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Программа остановлена")
    except Exception as e:
        print(f"💥 Ошибка запуска: {e}")
        sys.exit(1)