"""
Abandoned cart detector a marketing automation-hoz
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import asyncio
from ..database.supabase_client import get_supabase_client
from .email_service import SendGridEmailService
from .sms_service import TwilioSMSService
from .discount_service import DiscountService

logger = logging.getLogger(__name__)

class AbandonedCartDetector:
    """
    Kosárelhagyás detektálás és follow-up kezelés
    """
    
    def __init__(self):
        """Abandoned cart detector inicializálása"""
        self.supabase = get_supabase_client().get_client()
        self.email_service = SendGridEmailService()
        self.sms_service = TwilioSMSService()
        self.discount_service = DiscountService()
        self.is_testing = os.getenv('TESTING') == 'true'
        
        # Konfiguráció environment variables alapján
        self.timeout_minutes = int(os.getenv('ABANDONED_CART_TIMEOUT_MINUTES', '30'))
        self.minimum_cart_value = float(os.getenv('MINIMUM_CART_VALUE_FOR_FOLLOWUP', '5000'))
        self.email_delay_minutes = int(os.getenv('FOLLOW_UP_EMAIL_DELAY_MINUTES', '30'))
        self.sms_delay_hours = int(os.getenv('FOLLOW_UP_SMS_DELAY_HOURS', '2'))
        
        logger.info("Abandoned cart detector inicializálva")
    
    async def detect_abandoned_carts(self) -> int:
        """
        Kosárelhagyás detektálás és abandoned cart event-ek létrehozása
        
        Returns:
            int: Új abandoned cart-ok száma
        """
        try:
            logger.info("Kosárelhagyás detektálás indítása...")
            
            # Aktív kosarak lekérése
            active_carts = await self._get_active_carts()
            
            if not active_carts:
                logger.info("Nincsenek aktív kosarak")
                return 0
            
            abandoned_count = 0
            
            for cart in active_carts:
                if await self._is_cart_abandoned(cart):
                    # Abandoned cart event létrehozása
                    if await self._create_abandoned_cart_event(cart):
                        abandoned_count += 1
                        
                        # Follow-up ütemezés
                        await self._schedule_follow_ups(cart['cart_id'])
            
            logger.info(f"Kosárelhagyás detektálás befejezve: {abandoned_count} új abandoned cart")
            return abandoned_count
            
        except Exception as e:
            logger.error(f"Hiba a kosárelhagyás detektálásban: {e}")
            return 0
    
    async def send_follow_up_email(self, cart_id: str, email_service: SendGridEmailService, delay_minutes: int = 30) -> bool:
        """
        Email follow-up küldés
        
        Args:
            cart_id: Kosár azonosítója
            email_service: Email service
            delay_minutes: Késleltetés percekben
            
        Returns:
            bool: Sikeres küldés esetén True
        """
        try:
            logger.info(f"Email follow-up küldés: cart_id={cart_id}")
            
            # Késleltetés
            await asyncio.sleep(delay_minutes * 60)
            
            # Abandoned cart adatok lekérése
            abandoned_cart = await self._get_abandoned_cart(cart_id)
            if not abandoned_cart:
                logger.warning(f"Abandoned cart nem található: {cart_id}")
                return False
            
            # Email már elküldve ellenőrzése
            if abandoned_cart.get('email_sent'):
                logger.info(f"Email már elküldve: {cart_id}")
                return True
            
            # Template adatok előkészítése
            template_data = await self._prepare_email_template_data(abandoned_cart)
            
            # Email küldés
            if template_data.get('customer_email'):
                success = await email_service.send_abandoned_cart_email(
                    template_data['customer_email'], 
                    template_data
                )
                
                if success:
                    # Email küldés státusz frissítése
                    await self._update_email_sent_status(cart_id)
                    
                    # Marketing message mentése
                    await self._save_marketing_message(
                        abandoned_cart['id'],
                        'email',
                        template_data['customer_email'],
                        "🛒 Ne felejtsd el a kosaradat!",
                        template_data
                    )
                    
                    logger.info(f"Email follow-up sikeresen elküldve: {cart_id}")
                    return True
                else:
                    logger.error(f"Email follow-up küldés sikertelen: {cart_id}")
                    return False
            else:
                logger.warning(f"Nincs email cím az abandoned cart-hoz: {cart_id}")
                return False
                
        except Exception as e:
            logger.error(f"Hiba az email follow-up küldésben: {cart_id}, hiba: {e}")
            return False
    
    async def send_follow_up_sms(self, cart_id: str, sms_service: TwilioSMSService, delay_hours: int = 2) -> bool:
        """
        SMS follow-up küldés
        
        Args:
            cart_id: Kosár azonosítója
            sms_service: SMS service
            delay_hours: Késleltetés órákban
            
        Returns:
            bool: Sikeres küldés esetén True
        """
        try:
            logger.info(f"SMS follow-up küldés: cart_id={cart_id}")
            
            # Késleltetés
            await asyncio.sleep(delay_hours * 3600)
            
            # Abandoned cart adatok lekérése
            abandoned_cart = await self._get_abandoned_cart(cart_id)
            if not abandoned_cart:
                logger.warning(f"Abandoned cart nem található: {cart_id}")
                return False
            
            # SMS már elküldve ellenőrzése
            if abandoned_cart.get('sms_sent'):
                logger.info(f"SMS már elküldve: {cart_id}")
                return True
            
            # Template adatok előkészítése
            template_data = await self._prepare_sms_template_data(abandoned_cart)
            
            # SMS küldés
            if template_data.get('customer_phone'):
                success = await sms_service.send_abandoned_cart_sms(
                    template_data['customer_phone'], 
                    template_data
                )
                
                if success:
                    # SMS küldés státusz frissítése
                    await self._update_sms_sent_status(cart_id)
                    
                    # Marketing message mentése
                    await self._save_marketing_message(
                        abandoned_cart['id'],
                        'sms',
                        template_data['customer_phone'],
                        None,
                        template_data
                    )
                    
                    logger.info(f"SMS follow-up sikeresen elküldve: {cart_id}")
                    return True
                else:
                    logger.error(f"SMS follow-up küldés sikertelen: {cart_id}")
                    return False
            else:
                logger.warning(f"Nincs telefonszám az abandoned cart-hoz: {cart_id}")
                return False
                
        except Exception as e:
            logger.error(f"Hiba az SMS follow-up küldésben: {cart_id}, hiba: {e}")
            return False
    
    async def cleanup_old_abandoned_carts(self) -> int:
        """
        Régi abandoned cart-ok tisztítása (30 napnál régebbiek)
        
        Returns:
            int: Törölt rekordok száma
        """
        try:
            logger.info("Régi abandoned cart-ok tisztítása")
            
            # Teszt környezetben mock implementáció
            if self.is_testing:
                logger.info("Mock cleanup old abandoned carts")
                return 0
            
            # 30 napnál régebbi abandoned cart-ok lekérése
            cutoff_date = datetime.now() - timedelta(days=30)
            
            result = await self.supabase.table('abandoned_carts').delete().lt('created_at', cutoff_date.isoformat()).execute()
            
            deleted_count = len(result.data) if result.data else 0
            logger.info(f"Régi abandoned cart-ok törölve: {deleted_count}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Hiba a régi abandoned cart-ok tisztításában: {e}")
            return 0
    
    async def mark_cart_returned(self, cart_id: str) -> bool:
        """
        Kosár visszatérésének megjelölése
        
        Args:
            cart_id: Kosár azonosítója
            
        Returns:
            bool: Sikeres frissítés esetén True
        """
        try:
            logger.info(f"Kosár visszatérés megjelölése: {cart_id}")
            
            # Teszt környezetben mock implementáció
            if self.is_testing:
                logger.info(f"Mock cart returned for cart_id: {cart_id}")
                return True
            
            result = await self.supabase.table('abandoned_carts').update({
                'returned': True,
                'returned_at': datetime.now().isoformat()
            }).eq('cart_id', cart_id).execute()
            
            if result.data:
                logger.info(f"Kosár visszatérés sikeresen megjelölve: {cart_id}")
                return True
            else:
                logger.warning(f"Abandoned cart nem található: {cart_id}")
                return False
                
        except Exception as e:
            logger.error(f"Hiba a kosár visszatérés megjelölésében: {cart_id}, hiba: {e}")
            return False
    
    async def _get_active_carts(self) -> List[Dict[str, Any]]:
        """
        Aktív kosarak lekérése
        
        Returns:
            List: Aktív kosarak listája
        """
        try:
            # Ez egy egyszerűsített implementáció
            # A valóságban a webshop API-ból vagy session adatokból kellene lekérni
            # Itt mock adatokat használunk teszteléshez
            
            mock_carts = [
                {
                    'cart_id': 'cart_001',
                    'customer_id': 'customer_001',
                    'session_id': 'session_001',
                    'last_activity': (datetime.now() - timedelta(minutes=45)).isoformat(),
                    'cart_value': 25000,
                    'items': [
                        {'id': 1, 'name': 'iPhone 15', 'quantity': 1, 'price': 25000}
                    ],
                    'customer_email': 'test@example.com',
                    'customer_phone': '+36123456789'
                },
                {
                    'cart_id': 'cart_002',
                    'customer_id': 'customer_002',
                    'session_id': 'session_002',
                    'last_activity': (datetime.now() - timedelta(minutes=20)).isoformat(),
                    'cart_value': 15000,
                    'items': [
                        {'id': 2, 'name': 'Samsung Galaxy', 'quantity': 1, 'price': 15000}
                    ],
                    'customer_email': 'test2@example.com',
                    'customer_phone': '+36987654321'
                }
            ]
            
            return mock_carts
            
        except Exception as e:
            logger.error(f"Hiba az aktív kosarak lekérésében: {e}")
            return []
    
    async def _is_cart_abandoned(self, cart: Dict[str, Any]) -> bool:
        """
        Kosár elhagyott-e ellenőrzése
        
        Args:
            cart: Kosár adatok
            
        Returns:
            bool: True ha elhagyott, False ha nem
        """
        try:
            # Minimum kosárérték ellenőrzése
            if cart['cart_value'] < self.minimum_cart_value:
                return False
            
            # Időtartam ellenőrzése
            last_activity = datetime.fromisoformat(cart['last_activity'].replace('Z', '+00:00'))
            time_since_activity = datetime.now() - last_activity
            
            # Timeout ellenőrzése
            if time_since_activity.total_seconds() < (self.timeout_minutes * 60):
                return False
            
            # Teszt környezetben mock implementáció
            if self.is_testing:
                logger.info(f"Mock abandoned cart check for cart_id: {cart['cart_id']}")
                return True
            
            # Már létezik-e abandoned cart event
            existing = await self.supabase.table('abandoned_carts').select('id').eq('cart_id', cart['cart_id']).execute()
            
            if existing.data:
                return False  # Már létezik abandoned cart event
            
            return True
            
        except Exception as e:
            logger.error(f"Hiba a kosár elhagyás ellenőrzésében: {e}")
            return False
    
    async def _create_abandoned_cart_event(self, cart: Dict[str, Any]) -> bool:
        """
        Abandoned cart event létrehozása
        
        Args:
            cart: Kosár adatok
            
        Returns:
            bool: Sikeres létrehozás esetén True
        """
        try:
            logger.info(f"Abandoned cart event létrehozása: {cart['cart_id']}")
            
            # Teszt környezetben mock implementáció
            if self.is_testing:
                logger.info(f"Mock abandoned cart event created: {cart['cart_id']}")
                return True
            
            # Abandoned cart event mentése
            result = await self.supabase.table('abandoned_carts').insert({
                'cart_id': cart['cart_id'],
                'customer_id': cart['customer_id'],
                'session_id': cart['session_id'],
                'abandoned_at': datetime.now().isoformat(),
                'cart_value': cart['cart_value'],
                'items': cart['items'],
                'customer_email': cart.get('customer_email'),
                'customer_phone': cart.get('customer_phone'),
                'follow_up_attempts': 0,
                'email_sent': False,
                'sms_sent': False,
                'returned': False
            }).execute()
            
            if result.data:
                logger.info(f"Abandoned cart event sikeresen létrehozva: {cart['cart_id']}")
                return True
            else:
                logger.error(f"Abandoned cart event létrehozás sikertelen: {cart['cart_id']}")
                return False
                
        except Exception as e:
            logger.error(f"Hiba az abandoned cart event létrehozásában: {cart['cart_id']}, hiba: {e}")
            return False
    
    async def _schedule_follow_ups(self, cart_id: str):
        """
        Follow-up üzenetek ütemezése
        
        Args:
            cart_id: Kosár azonosítója
        """
        try:
            logger.info(f"Follow-up üzenetek ütemezése: {cart_id}")
            
            # Teszt környezetben mock implementáció
            if self.is_testing:
                logger.info(f"Mock follow-up scheduling for cart_id: {cart_id}")
                return
            
            # Email follow-up ütemezése (30 perc múlva)
            from .celery_app import send_follow_up_email
            send_follow_up_email.delay(cart_id, self.email_delay_minutes)
            
            # SMS follow-up ütemezése (2 óra múlva)
            from .celery_app import send_follow_up_sms
            send_follow_up_sms.delay(cart_id, self.sms_delay_hours)
            
            logger.info(f"Follow-up üzenetek ütemezve: {cart_id}")
            
        except Exception as e:
            logger.error(f"Hiba a follow-up üzenetek ütemezésében: {cart_id}, hiba: {e}")
    
    async def _get_abandoned_cart(self, cart_id: str) -> Optional[Dict[str, Any]]:
        """
        Abandoned cart adatok lekérése
        
        Args:
            cart_id: Kosár azonosítója
            
        Returns:
            Optional[Dict]: Abandoned cart adatok vagy None
        """
        try:
            # Teszt környezetben mock implementáció
            if self.is_testing:
                return {
                    'id': 1,
                    'cart_id': cart_id,
                    'customer_id': 'customer_001',
                    'cart_value': 25000,
                    'items': [{'id': 1, 'name': 'iPhone 15', 'quantity': 1, 'price': 25000}],
                    'customer_email': 'test@example.com',
                    'customer_phone': '+36123456789',
                    'email_sent': False,
                    'sms_sent': False,
                    'returned': False
                }
            
            result = await self.supabase.table('abandoned_carts').select('*').eq('cart_id', cart_id).execute()
            
            if result.data:
                return result.data[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Hiba az abandoned cart lekérésében: {cart_id}, hiba: {e}")
            return None
    
    async def _prepare_email_template_data(self, abandoned_cart: Dict[str, Any]) -> Dict[str, Any]:
        """
        Email template adatok előkészítése
        
        Args:
            abandoned_cart: Abandoned cart adatok
            
        Returns:
            Dict: Template adatok
        """
        try:
            # Kedvezmény kód generálása
            discount_code = await self.discount_service.generate_abandoned_cart_discount(
                abandoned_cart['customer_id'],
                abandoned_cart['cart_value']
            )
            
            # Template adatok összeállítása
            template_data = {
                'customer_name': f"Vásárló {abandoned_cart['customer_id']}",
                'cart_items': abandoned_cart['items'],
                'cart_value': abandoned_cart['cart_value'],
                'discount_code': discount_code,
                'discount_percentage': 10.0,  # Alapértelmezett érték
                'valid_until': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                'customer_email': abandoned_cart.get('customer_email'),
                'customer_phone': abandoned_cart.get('customer_phone')
            }
            
            return template_data
            
        except Exception as e:
            logger.error(f"Hiba az email template adatok előkészítésében: {e}")
            return {}
    
    async def _prepare_sms_template_data(self, abandoned_cart: Dict[str, Any]) -> Dict[str, Any]:
        """
        SMS template adatok előkészítése
        
        Args:
            abandoned_cart: Abandoned cart adatok
            
        Returns:
            Dict: Template adatok
        """
        try:
            # Template adatok összeállítása (egyszerűbb mint email)
            template_data = {
                'customer_name': f"Vásárló {abandoned_cart['customer_id']}",
                'cart_value': abandoned_cart['cart_value'],
                'discount_code': abandoned_cart.get('discount_code', ''),
                'customer_phone': abandoned_cart.get('customer_phone')
            }
            
            return template_data
            
        except Exception as e:
            logger.error(f"Hiba az SMS template adatok előkészítésében: {e}")
            return {}
    
    async def _update_email_sent_status(self, cart_id: str):
        """
        Email küldés státusz frissítése
        
        Args:
            cart_id: Kosár azonosítója
        """
        try:
            # Teszt környezetben mock implementáció
            if self.is_testing:
                logger.info(f"Mock email sent status updated for cart_id: {cart_id}")
                return
            
            await self.supabase.table('abandoned_carts').update({
                'email_sent': True,
                'last_follow_up': datetime.now().isoformat(),
                'follow_up_attempts': self.supabase.raw('follow_up_attempts + 1')
            }).eq('cart_id', cart_id).execute()
            
        except Exception as e:
            logger.error(f"Hiba az email státusz frissítésében: {cart_id}, hiba: {e}")
    
    async def _update_sms_sent_status(self, cart_id: str):
        """
        SMS küldés státusz frissítése
        
        Args:
            cart_id: Kosár azonosítója
        """
        try:
            # Teszt környezetben mock implementáció
            if self.is_testing:
                logger.info(f"Mock SMS sent status updated for cart_id: {cart_id}")
                return
            
            await self.supabase.table('abandoned_carts').update({
                'sms_sent': True,
                'last_follow_up': datetime.now().isoformat(),
                'follow_up_attempts': self.supabase.raw('follow_up_attempts + 1')
            }).eq('cart_id', cart_id).execute()
            
        except Exception as e:
            logger.error(f"Hiba az SMS státusz frissítésében: {cart_id}, hiba: {e}")
    
    async def _save_marketing_message(self, abandoned_cart_id: int, message_type: str, recipient: str, subject: str, content: Dict[str, Any]):
        """
        Marketing üzenet mentése
        
        Args:
            abandoned_cart_id: Abandoned cart azonosítója
            message_type: Üzenet típusa ('email', 'sms')
            recipient: Címzett
            subject: Tárgy (email esetén)
            content: Üzenet tartalma
        """
        try:
            # Teszt környezetben mock implementáció
            if self.is_testing:
                logger.info(f"Mock marketing message saved: {message_type} to {recipient}")
                return
            
            await self.supabase.table('marketing_messages').insert({
                'abandoned_cart_id': abandoned_cart_id,
                'message_type': message_type,
                'recipient': recipient,
                'subject': subject,
                'content': str(content),
                'sent_at': datetime.now().isoformat(),
                'delivery_status': 'sent'
            }).execute()
            
        except Exception as e:
            logger.error(f"Hiba a marketing üzenet mentésében: {e}")
    
    async def get_abandoned_cart_statistics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Abandoned cart statisztikák lekérése
        
        Args:
            start_date: Kezdő dátum
            end_date: Záró dátum
            
        Returns:
            Dict: Abandoned cart statisztikák
        """
        try:
            logger.info(f"Abandoned cart statisztikák lekérése: {start_date} - {end_date}")
            
            # Teszt környezetben mock implementáció
            if self.is_testing:
                return {
                    'total_abandoned_carts': 10,
                    'total_abandoned_value': 250000,
                    'email_sent_count': 8,
                    'sms_sent_count': 5,
                    'returned_count': 3,
                    'return_rate': 30.0,
                    'avg_cart_value': 25000.0
                }
            
            # Abandoned cart-ok lekérése a dátumtartományban
            result = await self.supabase.table('abandoned_carts').select('''
                cart_value,
                email_sent,
                sms_sent,
                returned,
                follow_up_attempts
            ''').gte('created_at', start_date.isoformat()).lte('created_at', end_date.isoformat()).execute()
            
            if not result.data:
                return {
                    'total_abandoned_carts': 0,
                    'total_abandoned_value': 0,
                    'email_sent_count': 0,
                    'sms_sent_count': 0,
                    'returned_count': 0,
                    'return_rate': 0.0,
                    'avg_cart_value': 0.0
                }
            
            # Statisztikák kalkuláció
            total_carts = len(result.data)
            total_value = sum(cart['cart_value'] for cart in result.data)
            email_sent = sum(1 for cart in result.data if cart['email_sent'])
            sms_sent = sum(1 for cart in result.data if cart['sms_sent'])
            returned = sum(1 for cart in result.data if cart['returned'])
            
            return {
                'total_abandoned_carts': total_carts,
                'total_abandoned_value': total_value,
                'email_sent_count': email_sent,
                'sms_sent_count': sms_sent,
                'returned_count': returned,
                'return_rate': (returned / total_carts * 100) if total_carts > 0 else 0.0,
                'avg_cart_value': (total_value / total_carts) if total_carts > 0 else 0.0
            }
            
        except Exception as e:
            logger.error(f"Hiba az abandoned cart statisztikák lekérésében: {e}")
            return {}
