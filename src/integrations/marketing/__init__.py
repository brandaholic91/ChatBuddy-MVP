"""
Marketing automation modul a ChatBuddy MVP-hez
"""

from .celery_app import celery_app, detect_abandoned_carts, send_follow_up_email, send_follow_up_sms
from .email_service import SendGridEmailService
from .sms_service import TwilioSMSService
from .template_engine import MarketingTemplateEngine
from .discount_service import DiscountService
from .abandoned_cart_detector import AbandonedCartDetector
from .analytics import MarketingAnalytics

__all__ = [
    'celery_app',
    'detect_abandoned_carts',
    'send_follow_up_email', 
    'send_follow_up_sms',
    'SendGridEmailService',
    'TwilioSMSService',
    'MarketingTemplateEngine',
    'DiscountService',
    'AbandonedCartDetector',
    'MarketingAnalytics'
]