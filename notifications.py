"""
Модуль для отправки уведомлений
"""

import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from config import NOTIFICATION_CONFIG

logger = logging.getLogger(__name__)

class NotificationService:
    """Сервис для отправки уведомлений через различные каналы"""
    
    @staticmethod
    async def send_telegram(message: str):
        """Отправка уведомления в Telegram"""
        if not NOTIFICATION_CONFIG['telegram']['enabled']:
            return None
        
        bot_token = NOTIFICATION_CONFIG['telegram']['bot_token']
        chat_id = NOTIFICATION_CONFIG['telegram']['chat_id']
        
        if not bot_token or not chat_id:
            logger.warning("Telegram не настроен")
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    'chat_id': chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }
                
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            message_id = result['result']['message_id']
                            logger.info("Уведомление отправлено в Telegram")
                            return message_id
                        else:
                            logger.error(f"Ошибка Telegram API: {result.get('description')}")
                            return None
                    else:
                        logger.error(f"Ошибка отправки в Telegram: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Ошибка при отправке в Telegram: {e}")
            return None
    
    @staticmethod
    async def send_discord(message: str):
        """Отправка уведомления в Discord"""
        if not NOTIFICATION_CONFIG['discord']['enabled']:
            return
        
        webhook_url = NOTIFICATION_CONFIG['discord']['webhook_url']
        
        if not webhook_url:
            logger.warning("Discord не настроен")
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json={
                    'content': message
                }) as response:
                    if response.status == 204:
                        logger.info("Уведомление отправлено в Discord")
                    else:
                        logger.error(f"Ошибка отправки в Discord: {response.status}")
        except Exception as e:
            logger.error(f"Ошибка при отправке в Discord: {e}")
    
    @staticmethod
    def send_email(subject: str, message: str):
        """Отправка уведомления по email"""
        if not NOTIFICATION_CONFIG['email']['enabled']:
            return
        
        config = NOTIFICATION_CONFIG['email']
        
        if not all([config['username'], config['password'], config['to_email']]):
            logger.warning("Email не настроен")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = config['username']
            msg['To'] = config['to_email']
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
            server.login(config['username'], config['password'])
            server.send_message(msg)
            server.quit()
            
            logger.info("Уведомление отправлено по email")
        except Exception as e:
            logger.error(f"Ошибка при отправке email: {e}")
    
    @staticmethod
    async def send_all(message: str):
        """Отправка уведомления через все настроенные каналы"""
        await NotificationService.send_telegram(message)
        await NotificationService.send_discord(message)
        # Email отправляется синхронно
        try:
            NotificationService.send_email("Арбитражная возможность", message)
        except Exception as e:
            logger.error(f"Ошибка отправки email: {e}")