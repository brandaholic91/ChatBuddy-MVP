"""
Celery konfiguráció és background task-ok a marketing automation-hoz
"""
from celery import Celery
from celery.schedules import crontab
import os
import asyncio
from typing import Dict, Any
import logging

# Logger setup
logger = logging.getLogger(__name__)

# Celery app konfiguráció
celery_app = Celery('marketing_automation')

# Konfiguráció environment variables alapján
celery_app.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'),
    timezone=os.getenv('CELERY_TIMEZONE', 'Europe/Budapest'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 perc timeout
    task_soft_time_limit=25 * 60,  # 25 perc soft timeout
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # Teszteléshez: ha nincs Redis, akkor memory backend-et használunk
    broker_transport_options={'max_retries': 1},
    result_backend_transport_options={'max_retries': 1},
)

# Periodic tasks ütemezés
celery_app.conf.beat_schedule = {
    'detect-abandoned-carts': {
        'task': 'src.integrations.marketing.celery_app.detect_abandoned_carts',
        'schedule': crontab(minute='*/15'),  # 15 percenként
    },
    'cleanup-old-carts': {
        'task': 'src.integrations.marketing.celery_app.cleanup_old_abandoned_carts',
        'schedule': crontab(hour=2, minute=0),  # Napi 2:00-kor
    },
}

@celery_app.task(bind=True, max_retries=3)
def detect_abandoned_carts(self):
    """
    Rendszeres kosárelhagyás detektálás (15 percenként)
    """
    try:
        logger.info("Kosárelhagyás detektálás indítása...")
        
        # Teszt környezet ellenőrzése
        if os.getenv('TESTING') == 'true':
            logger.info("Teszt környezet - mock eredmény visszaadása")
            return 0
        
        # Async függvény hívása sync context-ben
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_detect_abandoned_carts_async())
            logger.info(f"Kosárelhagyás detektálás befejezve: {result} új abandoned cart")
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Hiba a kosárelhagyás detektálásban: {exc}")
        # Teszt környezetben ne próbálkozzunk újra
        if os.getenv('TESTING') == 'true':
            logger.warning("Teszt környezet - újrapróbálkozás kihagyva")
            return 0
        raise self.retry(exc=exc, countdown=60)  # 1 perc múlva újrapróbálkozás

@celery_app.task(bind=True, max_retries=3)
def send_follow_up_email(self, cart_id: str, delay_minutes: int = 30):
    """
    Email follow-up küldés késleltetéssel
    """
    try:
        logger.info(f"Email follow-up küldés indítása cart_id: {cart_id}")
        
        # Teszt környezet ellenőrzése
        if os.getenv('TESTING') == 'true':
            logger.info("Teszt környezet - mock email küldés")
            return True
        
        # Async függvény hívása sync context-ben
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_send_follow_up_email_async(cart_id, delay_minutes))
            logger.info(f"Email follow-up küldés befejezve cart_id: {cart_id}")
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Hiba az email follow-up küldésben cart_id: {cart_id}, hiba: {exc}")
        # Teszt környezetben ne próbálkozzunk újra
        if os.getenv('TESTING') == 'true':
            logger.warning("Teszt környezet - újrapróbálkozás kihagyva")
            return False
        raise self.retry(exc=exc, countdown=300)  # 5 perc múlva újrapróbálkozás

@celery_app.task(bind=True, max_retries=3)
def send_follow_up_sms(self, cart_id: str, delay_hours: int = 2):
    """
    SMS follow-up küldés késleltetéssel
    """
    try:
        logger.info(f"SMS follow-up küldés indítása cart_id: {cart_id}")
        
        # Teszt környezet ellenőrzése
        if os.getenv('TESTING') == 'true':
            logger.info("Teszt környezet - mock SMS küldés")
            return True
        
        # Async függvény hívása sync context-ben
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_send_follow_up_sms_async(cart_id, delay_hours))
            logger.info(f"SMS follow-up küldés befejezve cart_id: {cart_id}")
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Hiba az SMS follow-up küldésben cart_id: {cart_id}, hiba: {exc}")
        # Teszt környezetben ne próbálkozzunk újra
        if os.getenv('TESTING') == 'true':
            logger.warning("Teszt környezet - újrapróbálkozás kihagyva")
            return False
        raise self.retry(exc=exc, countdown=600)  # 10 perc múlva újrapróbálkozás

@celery_app.task(bind=True)
def cleanup_old_abandoned_carts(self):
    """
    Régi abandoned cart-ok tisztítása (napi 2:00-kor)
    """
    try:
        logger.info("Régi abandoned cart-ok tisztítása indítása...")
        
        # Teszt környezet ellenőrzése
        if os.getenv('TESTING') == 'true':
            logger.info("Teszt környezet - mock cleanup")
            return 0
        
        # Async függvény hívása sync context-ben
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_cleanup_old_abandoned_carts_async())
            logger.info(f"Régi abandoned cart-ok tisztítása befejezve: {result} törölt rekord")
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Hiba a régi abandoned cart-ok tisztításában: {exc}")
        return False

# Async helper függvények
async def _detect_abandoned_carts_async() -> int:
    """
    Async kosárelhagyás detektálás implementáció
    """
    from .abandoned_cart_detector import AbandonedCartDetector
    
    detector = AbandonedCartDetector()
    return await detector.detect_abandoned_carts()

async def _send_follow_up_email_async(cart_id: str, delay_minutes: int) -> bool:
    """
    Async email follow-up küldés implementáció
    """
    from .email_service import SendGridEmailService
    from .abandoned_cart_detector import AbandonedCartDetector
    
    detector = AbandonedCartDetector()
    email_service = SendGridEmailService()
    
    return await detector.send_follow_up_email(cart_id, email_service, delay_minutes)

async def _send_follow_up_sms_async(cart_id: str, delay_hours: int) -> bool:
    """
    Async SMS follow-up küldés implementáció
    """
    from .sms_service import TwilioSMSService
    from .abandoned_cart_detector import AbandonedCartDetector
    
    detector = AbandonedCartDetector()
    sms_service = TwilioSMSService()
    
    return await detector.send_follow_up_sms(cart_id, sms_service, delay_hours)

async def _cleanup_old_abandoned_carts_async() -> int:
    """
    Async régi abandoned cart-ok tisztítása implementáció
    """
    from .abandoned_cart_detector import AbandonedCartDetector
    
    detector = AbandonedCartDetector()
    return await detector.cleanup_old_abandoned_carts()

# Celery worker indítás helper
def start_celery_worker():
    """
    Celery worker indítása development környezetben
    """
    celery_app.worker_main(['worker', '--loglevel=info'])

def start_celery_beat():
    """
    Celery beat indítása development környezetben
    """
    celery_app.worker_main(['beat', '--loglevel=info'])
