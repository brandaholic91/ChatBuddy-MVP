"""
Twilio SMS service a marketing automation-hoz
"""
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from .template_engine import MarketingTemplateEngine

logger = logging.getLogger(__name__)

class TwilioSMSService:
    """
    Twilio alapú SMS service a marketing automation-hoz
    """
    
    def __init__(self):
        """Twilio SMS service inicializálása"""
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([self.account_sid, self.auth_token, self.from_number]):
            if os.getenv('TESTING') == 'true':
                logger.warning("Twilio environment variables hiányoznak - mock módban működik")
                self.client = None
            else:
                raise ValueError("Twilio environment variables hiányoznak: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER")
        else:
            self.client = Client(self.account_sid, self.auth_token)
        self.template_engine = MarketingTemplateEngine()
        
        logger.info("Twilio SMS service inicializálva")
    
    async def send_abandoned_cart_sms(self, to_phone: str, template_data: Dict[str, Any]) -> bool:
        """
        Kosárelhagyás follow-up SMS küldése
        
        Args:
            to_phone: Címzett telefonszáma
            template_data: Template adatok (cart_items, customer_name, discount_code, stb.)
            
        Returns:
            bool: Sikeres küldés esetén True, egyébként False
        """
        try:
            logger.info(f"Abandoned cart SMS küldése: {to_phone}")
            
            # SMS template renderelés
            sms_content = self.template_engine.render_sms_template('abandoned_cart', template_data)
            
            # SMS küldés
            message = await self._send_sms_async(to_phone, sms_content)
            
            if message and message.sid:
                logger.info(f"Abandoned cart SMS sikeresen elküldve: {to_phone}, SID: {message.sid}")
                return True
            else:
                logger.error(f"Abandoned cart SMS küldés sikertelen: {to_phone}")
                return False
                
        except Exception as e:
            logger.error(f"Hiba az abandoned cart SMS küldésben: {to_phone}, hiba: {e}")
            return False
    
    async def send_welcome_sms(self, to_phone: str, template_data: Dict[str, Any]) -> bool:
        """
        Üdvözlő SMS küldése új regisztráció után
        
        Args:
            to_phone: Címzett telefonszáma
            template_data: Template adatok (customer_name, welcome_discount, stb.)
            
        Returns:
            bool: Sikeres küldés esetén True, egyébként False
        """
        try:
            logger.info(f"Welcome SMS küldése: {to_phone}")
            
            # SMS template renderelés
            sms_content = self.template_engine.render_sms_template('welcome', template_data)
            
            # SMS küldés
            message = await self._send_sms_async(to_phone, sms_content)
            
            if message and message.sid:
                logger.info(f"Welcome SMS sikeresen elküldve: {to_phone}, SID: {message.sid}")
                return True
            else:
                logger.error(f"Welcome SMS küldés sikertelen: {to_phone}")
                return False
                
        except Exception as e:
            logger.error(f"Hiba a welcome SMS küldésben: {to_phone}, hiba: {e}")
            return False
    
    async def send_discount_reminder_sms(self, to_phone: str, template_data: Dict[str, Any]) -> bool:
        """
        Kedvezmény emlékeztető SMS küldése
        
        Args:
            to_phone: Címzett telefonszáma
            template_data: Template adatok (discount_code, valid_until, stb.)
            
        Returns:
            bool: Sikeres küldés esetén True, egyébként False
        """
        try:
            logger.info(f"Discount reminder SMS küldése: {to_phone}")
            
            # SMS template renderelés
            sms_content = self.template_engine.render_sms_template('discount_reminder', template_data)
            
            # SMS küldés
            message = await self._send_sms_async(to_phone, sms_content)
            
            if message and message.sid:
                logger.info(f"Discount reminder SMS sikeresen elküldve: {to_phone}, SID: {message.sid}")
                return True
            else:
                logger.error(f"Discount reminder SMS küldés sikertelen: {to_phone}")
                return False
                
        except Exception as e:
            logger.error(f"Hiba a discount reminder SMS küldésben: {to_phone}, hiba: {e}")
            return False
    
    async def send_bulk_sms(self, recipients: List[Dict[str, Any]], template_name: str) -> Dict[str, Any]:
        """
        Bulk SMS küldés több címzettnek
        
        Args:
            recipients: Címzettek listája [{'phone': '...', 'data': {...}}]
            template_name: Template neve
            
        Returns:
            Dict: Eredmények (success_count, failure_count, errors)
        """
        try:
            logger.info(f"Bulk SMS küldés indítása: {len(recipients)} címzett")
            
            success_count = 0
            failure_count = 0
            errors = []
            
            for recipient in recipients:
                try:
                    # SMS template renderelés
                    sms_content = self.template_engine.render_sms_template(template_name, recipient['data'])
                    
                    # SMS küldés
                    message = await self._send_sms_async(recipient['phone'], sms_content)
                    
                    if message and message.sid:
                        success_count += 1
                    else:
                        failure_count += 1
                        errors.append(f"SMS küldés sikertelen: {recipient['phone']}")
                        
                except Exception as e:
                    failure_count += 1
                    errors.append(f"Hiba az SMS küldésben: {recipient['phone']}, hiba: {e}")
            
            logger.info(f"Bulk SMS küldés befejezve: {success_count} sikeres, {failure_count} sikertelen")
            
            return {
                'success_count': success_count,
                'failure_count': failure_count,
                'total_count': len(recipients),
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Hiba a bulk SMS küldésben: {e}")
            return {
                'success_count': 0,
                'failure_count': len(recipients),
                'total_count': len(recipients),
                'errors': [str(e)]
            }
    
    async def _send_sms_async(self, to_phone: str, body: str):
        """
        Async SMS küldés Twilio API-val
        
        Args:
            to_phone: Címzett telefonszáma
            body: SMS szövege
            
        Returns:
            Message objektum vagy None hiba esetén
        """
        try:
            # Twilio API hívás async wrapper-ben
            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None, 
                lambda: self.client.messages.create(
                    to=to_phone,
                    from_=self.from_number,
                    body=body
                )
            )
            return message
            
        except TwilioException as e:
            logger.error(f"Twilio hiba az SMS küldésben: {e}")
            return None
        except Exception as e:
            logger.error(f"Hiba az async SMS küldésben: {e}")
            return None
    
    def validate_phone_number(self, phone: str) -> bool:
        """
        Telefonszám validálása
        
        Args:
            phone: Telefonszám
            
        Returns:
            bool: True ha valid, False ha nem
        """
        import re
        
        # Telefonszám regex pattern - minimum 5 karakteres szám (nemzetközi formátum)
        # +? optional + jel, [1-9] nem kezdődhet 0-val, \d{4,14} még 4-14 számjegy
        pattern = r'^\+?[1-9]\d{4,14}$'
        return bool(re.match(pattern, phone))
    
    def format_phone_number(self, phone: str) -> str:
        """
        Telefonszám formázása nemzetközi formátumra
        
        Args:
            phone: Telefonszám
            
        Returns:
            str: Formázott telefonszám
        """
        # Eltávolítjuk a nem numerikus karaktereket
        digits_only = ''.join(filter(str.isdigit, phone))
        
        # Ha nincs + jel és magyar szám (36), akkor hozzáadjuk
        if digits_only.startswith('36') and not phone.startswith('+'):
            return f"+{digits_only}"
        elif digits_only.startswith('06') and not phone.startswith('+'):
            # Magyar mobil szám 06-ral kezdődik
            return f"+36{digits_only[2:]}"
        elif digits_only.startswith('6') and not phone.startswith('+'):
            # Magyar mobil szám 6-ral kezdődik (nem 06)
            return f"+36{digits_only[1:]}"
        elif not phone.startswith('+'):
            return f"+{digits_only}"
        else:
            return phone
    
    def get_delivery_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        SMS delivery statisztikák lekérése
        
        Args:
            start_date: Kezdő dátum
            end_date: Záró dátum
            
        Returns:
            Dict: Delivery statisztikák
        """
        try:
            # Twilio API statisztikák lekérése
            # Ez egy egyszerűsített implementáció, a valóságban a Twilio API-t kellene használni
            return {
                'sent_count': 0,
                'delivered_count': 0,
                'failed_count': 0,
                'undelivered_count': 0
            }
            
        except Exception as e:
            logger.error(f"Hiba a delivery statisztikák lekérésében: {e}")
            return {}
    
    def get_message_status(self, message_sid: str) -> Optional[str]:
        """
        SMS üzenet státuszának lekérése
        
        Args:
            message_sid: Twilio message SID
            
        Returns:
            Optional[str]: Üzenet státusza vagy None hiba esetén
        """
        try:
            message = self.client.messages(message_sid).fetch()
            return message.status
            
        except TwilioException as e:
            logger.error(f"Twilio hiba az üzenet státusz lekérésében: {e}")
            return None
        except Exception as e:
            logger.error(f"Hiba az üzenet státusz lekérésében: {e}")
            return None
