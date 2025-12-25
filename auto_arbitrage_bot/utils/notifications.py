#!/usr/bin/env python3
"""
Система уведомлений
"""

import asyncio
import aiohttp
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

# Добавляем путь к модулям
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from config import config
from utils.logger import get_logger

class NotificationManager:
    """Менеджер уведомлений"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.telegram_enabled = config.telegram['enabled']
        self.bot_token = config.telegram['bot_token']
        self.chat_id = config.telegram['chat_id']
        
    async def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """Отправка сообщения"""
        if not self.telegram_enabled:
            self.logger.info(f"📢 Уведомление: {message}")
            return True
        
        try:
            await self._send_telegram_message(message, parse_mode)
            return True
        except Exception as e:
            self.logger.error(f"❌ Ошибка отправки уведомления: {e}")
            return False
    
    async def _send_telegram_message(self, message: str, parse_mode: str = 'HTML'):
        """Отправка сообщения в Telegram"""
        if not self.bot_token or not self.chat_id:
            return
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                if response.status != 200:
                    raise Exception(f"Telegram API error: {response.status}")
    
    async def send_startup_notification(self, connected_exchanges: list):
        """Уведомление о запуске"""
        message = (
            f"🚀 <b>Арбитражный бот запущен</b>\n\n"
            f"⚙️ Режим: <code>{config.trading_mode.value}</code>\n"
            f"🏛️ Биржи: <code>{', '.join(connected_exchanges)}</code>\n"
            f"💰 Мин. прибыль: <code>{config.arbitrage.min_profit_threshold}%</code>\n"
            f"📊 Макс. позиция: <code>${config.arbitrage.max_position_size}</code>\n"
            f"🕐 Время: <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>"
        )
        await self.send_message(message)
    
    async def send_opportunity_notification(self, opportunity):
        """Уведомление о найденной возможности"""
        emoji = "🔄" if opportunity.type.value == "cross_exchange" else "🔺"
        type_name = "Межбиржевой" if opportunity.type.value == "cross_exchange" else "Треугольный"
        
        message = (
            f"{emoji} <b>{type_name} арбитраж</b>\n\n"
            f"💎 Символ: <code>{opportunity.symbol}</code>\n"
            f"💰 Прибыль: <code>{opportunity.profit_percent:.2f}%</code> "
            f"(<code>${opportunity.profit_usd:.2f}</code>)\n"
            f"🏛️ Биржи: <code>{', '.join(opportunity.exchanges)}</code>\n"
            f"📊 Уверенность: <code>{opportunity.confidence:.2f}</code>\n"
            f"⚠️ Риск: <code>{opportunity.risk_score:.2f}</code>\n"
            f"🕐 Время: <code>{opportunity.timestamp.strftime('%H:%M:%S')}</code>"
        )
        await self.send_message(message)
    
    async def send_trade_result_notification(self, trade_result):
        """Уведомление о результате сделки"""
        if trade_result.success:
            emoji = "✅"
            status = "УСПЕШНО"
            color = "🟢"
        else:
            emoji = "❌"
            status = "НЕУДАЧНО"
            color = "🔴"
        
        type_name = "Межбиржевой" if trade_result.arbitrage_type == "cross_exchange" else "Треугольный"
        
        message = (
            f"{emoji} <b>{status}</b> {color}\n\n"
            f"📈 Тип: <code>{type_name}</code>\n"
            f"💎 Символ: <code>{trade_result.symbol}</code>\n"
        )
        
        if trade_result.success:
            message += (
                f"💰 Прибыль: <code>${trade_result.profit_usd:.2f}</code> "
                f"(<code>{trade_result.profit_percent:.2f}%</code>)\n"
                f"⚡ Время: <code>{trade_result.execution_time:.2f}с</code>\n"
                f"📋 Ордеров: <code>{len(trade_result.orders)}</code>"
            )
        else:
            message += f"❌ Ошибка: <code>{trade_result.error}</code>"
        
        message += f"\n🕐 Время: <code>{datetime.now().strftime('%H:%M:%S')}</code>"
        
        await self.send_message(message)
    
    async def send_daily_report(self, stats: dict):
        """Отправка дневного отчета"""
        message = (
            f"📊 <b>Дневной отчет</b>\n\n"
            f"📈 Всего сделок: <code>{stats.get('total_trades', 0)}</code>\n"
            f"✅ Успешных: <code>{stats.get('successful_trades', 0)}</code>\n"
            f"📊 Успешность: <code>{stats.get('success_rate', 0):.1f}%</code>\n"
            f"💰 Прибыль: <code>${stats.get('total_profit', 0):.2f}</code>\n"
            f"📉 Убытки: <code>${stats.get('total_loss', 0):.2f}</code>\n"
            f"💵 Чистая прибыль: <code>${stats.get('daily_pnl', 0):.2f}</code>\n"
            f"💡 Найдено возможностей: <code>{stats.get('opportunities_found', 0)}</code>\n"
            f"⚡ Исполнено: <code>{stats.get('opportunities_executed', 0)}</code>\n"
            f"🕐 Время: <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>"
        )
        await self.send_message(message)
    
    async def send_risk_alert(self, alert_type: str, message: str):
        """Уведомление о рисках"""
        emoji_map = {
            'daily_loss': '📉',
            'max_drawdown': '⬇️',
            'emergency_stop': '🚨',
            'high_risk': '⚠️'
        }
        
        emoji = emoji_map.get(alert_type, '⚠️')
        
        alert_message = (
            f"{emoji} <b>ПРЕДУПРЕЖДЕНИЕ О РИСКАХ</b>\n\n"
            f"🔔 Тип: <code>{alert_type}</code>\n"
            f"📝 Сообщение: <code>{message}</code>\n"
            f"🕐 Время: <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>"
        )
        await self.send_message(alert_message)
    
    async def send_system_status(self, status: dict):
        """Уведомление о статусе системы"""
        status_emoji = "🟢" if status.get('is_running') else "🔴"
        
        message = (
            f"{status_emoji} <b>Статус системы</b>\n\n"
            f"🔄 Работает: <code>{'Да' if status.get('is_running') else 'Нет'}</code>\n"
            f"⚙️ Режим: <code>{status.get('trading_mode', 'unknown')}</code>\n"
            f"📊 Активных позиций: <code>{status.get('active_positions', 0)}</code>\n"
            f"💰 Дневная прибыль: <code>${status.get('daily_pnl', 0):.2f}</code>\n"
            f"📈 Всего сделок: <code>{status.get('total_trades', 0)}</code>\n"
            f"✅ Успешных: <code>{status.get('successful_trades', 0)}</code>\n"
            f"🏛️ Подключенные биржи: <code>{', '.join(status.get('connected_exchanges', []))}</code>\n"
            f"🕐 Время: <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>"
        )
        await self.send_message(message)