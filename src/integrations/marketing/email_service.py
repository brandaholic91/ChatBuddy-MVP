"""
SendGrid email service a marketing automation-hoz
"""
import sendgrid
from sendgrid.helpers.mail import Mail, From, To, Subject, HtmlContent, PlainTextContent
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from .template_engine import MarketingTemplateEngine

logger = logging.getLogger(__name__)

class SendGridEmailService:
    """
    SendGrid alapú email service a marketing automation-hoz
    """
    
    def __init__(self):
        """SendGrid email service inicializálása"""
        self.api_key = os.getenv('SENDGRID_API_KEY')
        if not self.api_key:
            logger.warning("SENDGRID_API_KEY environment variable hiányzik - mock módban működik")
            self.sg = None
        else:
            self.sg = sendgrid.SendGridAPIClient(api_key=self.api_key)
        
        self.from_email = os.getenv('EMAIL_FROM_ADDRESS', 'no-reply@chatbuddy.com')
        self.from_name = os.getenv('EMAIL_FROM_NAME', 'ChatBuddy')
        self.template_engine = MarketingTemplateEngine()
        
        logger.info("SendGrid email service inicializálva")
    
    async def send_abandoned_cart_email(self, to_email: str, template_data: Dict[str, Any]) -> bool:
        """
        Kosárelhagyás follow-up email küldése
        
        Args:
            to_email: Címzett email címe
            template_data: Template adatok (cart_items, customer_name, discount_code, stb.)
            
        Returns:
            bool: Sikeres küldés esetén True, egyébként False
        """
        try:
            logger.info(f"Abandoned cart email küldése: {to_email}")
            
            # Email template renderelés
            html_content = self.template_engine.render_email_template('abandoned_cart', template_data)
            text_content = self.template_engine.render_text_template('abandoned_cart', template_data)
            
            # Email létrehozása
            message = Mail(
                from_email=From(self.from_email, self.from_name),
                to_emails=To(to_email),
                subject=Subject("🛒 Ne felejtsd el a kosaradat!"),
                html_content=HtmlContent(html_content),
                plain_text_content=PlainTextContent(text_content)
            )
            
            # Email küldés
            response = await self._send_email_async(message)
            
            if response and response.status_code == 202:
                logger.info(f"Abandoned cart email sikeresen elküldve: {to_email}")
                return True
            else:
                logger.error(f"Abandoned cart email küldés sikertelen: {to_email}, status: {response.status_code if response else 'No response'}")
                return False
                
        except Exception as e:
            logger.error(f"Hiba az abandoned cart email küldésben: {to_email}, hiba: {e}")
            return False
    
    async def send_welcome_email(self, to_email: str, template_data: Dict[str, Any]) -> bool:
        """
        Üdvözlő email küldése új regisztráció után
        
        Args:
            to_email: Címzett email címe
            template_data: Template adatok (customer_name, welcome_discount, stb.)
            
        Returns:
            bool: Sikeres küldés esetén True, egyébként False
        """
        try:
            logger.info(f"Welcome email küldése: {to_email}")
            
            # Email template renderelés
            html_content = self.template_engine.render_email_template('welcome', template_data)
            text_content = self.template_engine.render_text_template('welcome', template_data)
            
            # Email létrehozása
            message = Mail(
                from_email=From(self.from_email, self.from_name),
                to_emails=To(to_email),
                subject=Subject("🎉 Üdvözöljük a ChatBuddy-ban!"),
                html_content=HtmlContent(html_content),
                plain_text_content=PlainTextContent(text_content)
            )
            
            # Email küldés
            response = await self._send_email_async(message)
            
            if response and response.status_code == 202:
                logger.info(f"Welcome email sikeresen elküldve: {to_email}")
                return True
            else:
                logger.error(f"Welcome email küldés sikertelen: {to_email}, status: {response.status_code if response else 'No response'}")
                return False
                
        except Exception as e:
            logger.error(f"Hiba a welcome email küldésben: {to_email}, hiba: {e}")
            return False
    
    async def send_discount_reminder_email(self, to_email: str, template_data: Dict[str, Any]) -> bool:
        """
        Kedvezmény emlékeztető email küldése
        
        Args:
            to_email: Címzett email címe
            template_data: Template adatok (discount_code, valid_until, stb.)
            
        Returns:
            bool: Sikeres küldés esetén True, egyébként False
        """
        try:
            logger.info(f"Discount reminder email küldése: {to_email}")
            
            # Email template renderelés
            html_content = self.template_engine.render_email_template('discount_reminder', template_data)
            text_content = self.template_engine.render_text_template('discount_reminder', template_data)
            
            # Email létrehozása
            message = Mail(
                from_email=From(self.from_email, self.from_name),
                to_emails=To(to_email),
                subject=Subject("⏰ Kedvezményed hamarosan lejár!"),
                html_content=HtmlContent(html_content),
                plain_text_content=PlainTextContent(text_content)
            )
            
            # Email küldés
            response = await self._send_email_async(message)
            
            if response and response.status_code == 202:
                logger.info(f"Discount reminder email sikeresen elküldve: {to_email}")
                return True
            else:
                logger.error(f"Discount reminder email küldés sikertelen: {to_email}, status: {response.status_code if response else 'No response'}")
                return False
                
        except Exception as e:
            logger.error(f"Hiba a discount reminder email küldésben: {to_email}, hiba: {e}")
            return False
    
    async def send_bulk_email(self, recipients: List[Dict[str, Any]], template_name: str, subject: str) -> Dict[str, Any]:
        """
        Bulk email küldés több címzettnek
        
        Args:
            recipients: Címzettek listája [{'email': '...', 'data': {...}}]
            template_name: Template neve
            subject: Email tárgy
            
        Returns:
            Dict: Eredmények (success_count, failure_count, errors)
        """
        try:
            logger.info(f"Bulk email küldés indítása: {len(recipients)} címzett")
            
            success_count = 0
            failure_count = 0
            errors = []
            
            for recipient in recipients:
                try:
                    # Email template renderelés
                    html_content = self.template_engine.render_email_template(template_name, recipient['data'])
                    text_content = self.template_engine.render_text_template(template_name, recipient['data'])
                    
                    # Email létrehozása
                    message = Mail(
                        from_email=From(self.from_email, self.from_name),
                        to_emails=To(recipient['email']),
                        subject=Subject(subject),
                        html_content=HtmlContent(html_content),
                        plain_text_content=PlainTextContent(text_content)
                    )
                    
                    # Email küldés
                    response = await self._send_email_async(message)
                    
                    if response and response.status_code == 202:
                        success_count += 1
                    else:
                        failure_count += 1
                        errors.append(f"Email küldés sikertelen: {recipient['email']}")
                        
                except Exception as e:
                    failure_count += 1
                    errors.append(f"Hiba az email küldésben: {recipient['email']}, hiba: {e}")
            
            logger.info(f"Bulk email küldés befejezve: {success_count} sikeres, {failure_count} sikertelen")
            
            return {
                'success_count': success_count,
                'failure_count': failure_count,
                'total_count': len(recipients),
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Hiba a bulk email küldésben: {e}")
            return {
                'success_count': 0,
                'failure_count': len(recipients),
                'total_count': len(recipients),
                'errors': [str(e)]
            }
    
    async def _send_email_async(self, message: Mail):
        """
        Async email küldés SendGrid API-val
        
        Args:
            message: SendGrid Mail objektum
            
        Returns:
            Response objektum vagy None hiba esetén
        """
        try:
            # SendGrid API hívás async wrapper-ben
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.sg.send, message)
            return response
            
        except Exception as e:
            logger.error(f"Hiba az async email küldésben: {e}")
            return None
    
    def validate_email(self, email: str) -> bool:
        """
        Email cím validálása
        
        Args:
            email: Email cím
            
        Returns:
            bool: True ha valid, False ha nem
        """
        import re
        
        # Egyszerű email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def get_delivery_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Email delivery statisztikák lekérése
        
        Args:
            start_date: Kezdő dátum
            end_date: Záró dátum
            
        Returns:
            Dict: Delivery statisztikák
        """
        try:
            # SendGrid API statisztikák lekérése
            # Ez egy egyszerűsített implementáció, a valóságban a SendGrid API-t kellene használni
            return {
                'sent_count': 0,
                'delivered_count': 0,
                'bounced_count': 0,
                'opened_count': 0,
                'clicked_count': 0,
                'unsubscribed_count': 0
            }
            
        except Exception as e:
            logger.error(f"Hiba a delivery statisztikák lekérésében: {e}")
            return {}
