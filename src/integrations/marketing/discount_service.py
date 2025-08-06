"""
Discount service a marketing automation-hoz
"""
import uuid
import hashlib
import random
import string
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging
from ..database.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

class DiscountService:
    """
    Kedvezmény kód generálás és kezelés a marketing automation-hoz
    """
    
    def __init__(self):
        """Discount service inicializálása"""
        self.supabase = get_supabase_client().get_client()
        self.is_testing = os.getenv('TESTING') == 'true'
        logger.info("Discount service inicializálva")
    
    async def generate_abandoned_cart_discount(self, customer_id: str, cart_value: float) -> str:
        """
        Kosárelhagyás kedvezmény kód generálása
        
        Args:
            customer_id: Vásárló azonosítója
            cart_value: Kosár értéke
            
        Returns:
            str: Generált kedvezmény kód
        """
        try:
            logger.info(f"Abandoned cart kedvezmény generálása: customer_id={customer_id}, cart_value={cart_value}")
            
            # Kedvezmény kód generálása
            discount_code = self._generate_discount_code('CART')
            
            # Kedvezmény százalék kalkuláció
            discount_percentage = self._calculate_discount_percentage(cart_value)
            
            # Kedvezmény érvényességi idő
            valid_until = datetime.now() + timedelta(days=7)  # 7 nap
            
            # Teszt környezetben mock implementáció
            if self.is_testing:
                logger.info(f"Mock discount code created: {discount_code}")
                return discount_code
            
            # Kedvezmény kód mentése
            await self.supabase.table('discount_codes').insert({
                'code': discount_code,
                'customer_id': customer_id,
                'discount_percentage': discount_percentage,
                'minimum_order_value': cart_value * 0.5,  # 50% minimum
                'valid_from': datetime.now().isoformat(),
                'valid_until': valid_until.isoformat(),
                'usage_limit': 1,
                'times_used': 0,
                'created_for': 'abandoned_cart',
                'active': True
            }).execute()
            
            logger.info(f"Abandoned cart kedvezmény sikeresen létrehozva: {discount_code}")
            return discount_code
            
        except Exception as e:
            logger.error(f"Hiba az abandoned cart kedvezmény generálásában: {e}")
            raise
    
    async def generate_welcome_discount(self, customer_id: str) -> str:
        """
        Üdvözlő kedvezmény kód generálása új regisztráció után
        
        Args:
            customer_id: Vásárló azonosítója
            
        Returns:
            str: Generált kedvezmény kód
        """
        try:
            logger.info(f"Welcome kedvezmény generálása: customer_id={customer_id}")
            
            # Kedvezmény kód generálása
            discount_code = self._generate_discount_code('WELCOME')
            
            # Teszt környezetben mock implementáció
            if self.is_testing:
                logger.info(f"Mock welcome discount created: {discount_code}")
                return discount_code
            
            # Kedvezmény kód mentése
            await self.supabase.table('discount_codes').insert({
                'code': discount_code,
                'customer_id': customer_id,
                'discount_percentage': 10.0,  # 10% üdvözlő kedvezmény
                'minimum_order_value': 10000,  # 10.000 Ft minimum
                'valid_from': datetime.now().isoformat(),
                'valid_until': (datetime.now() + timedelta(days=30)).isoformat(),  # 30 nap
                'usage_limit': 1,
                'times_used': 0,
                'created_for': 'welcome',
                'active': True
            }).execute()
            
            logger.info(f"Welcome kedvezmény sikeresen létrehozva: {discount_code}")
            return discount_code
            
        except Exception as e:
            logger.error(f"Hiba a welcome kedvezmény generálásában: {e}")
            raise
    
    async def generate_loyalty_discount(self, customer_id: str, loyalty_level: str) -> str:
        """
        Hűségi kedvezmény kód generálása
        
        Args:
            customer_id: Vásárló azonosítója
            loyalty_level: Hűségi szint ('bronze', 'silver', 'gold', 'platinum')
            
        Returns:
            str: Generált kedvezmény kód
        """
        try:
            logger.info(f"Loyalty kedvezmény generálása: customer_id={customer_id}, level={loyalty_level}")
            
            # Kedvezmény kód generálása
            discount_code = self._generate_discount_code('LOYALTY')
            
            # Kedvezmény százalék a hűségi szint alapján
            discount_percentage = self._get_loyalty_discount_percentage(loyalty_level)
            
            # Teszt környezetben mock implementáció
            if self.is_testing:
                logger.info(f"Mock loyalty discount created: {discount_code}")
                return discount_code
            
            # Kedvezmény kód mentése
            await self.supabase.table('discount_codes').insert({
                'code': discount_code,
                'customer_id': customer_id,
                'discount_percentage': discount_percentage,
                'minimum_order_value': 5000,  # 5.000 Ft minimum
                'valid_from': datetime.now().isoformat(),
                'valid_until': (datetime.now() + timedelta(days=14)).isoformat(),  # 14 nap
                'usage_limit': 1,
                'times_used': 0,
                'created_for': 'loyalty',
                'active': True
            }).execute()
            
            logger.info(f"Loyalty kedvezmény sikeresen létrehozva: {discount_code}")
            return discount_code
            
        except Exception as e:
            logger.error(f"Hiba a loyalty kedvezmény generálásában: {e}")
            raise
    
    async def validate_discount_code(self, code: str, customer_id: str, order_value: float) -> Dict[str, Any]:
        """
        Kedvezmény kód validálása
        
        Args:
            code: Kedvezmény kód
            customer_id: Vásárló azonosítója
            order_value: Rendelés értéke
            
        Returns:
            Dict: Validálási eredmény
        """
        try:
            logger.info(f"Kedvezmény kód validálása: {code}")
            
            # Teszt környezetben mock implementáció
            if self.is_testing:
                # Mock discount objektum
                discount = {
                    'id': 1,
                    'code': code,
                    'discount_percentage': 15.0,
                    'minimum_order_value': 10000,
                    'valid_from': datetime.now().isoformat(),
                    'valid_until': (datetime.now() + timedelta(days=7)).isoformat(),
                    'usage_limit': 1,
                    'times_used': 0,
                    'customer_id': customer_id,
                    'active': True
                }
            else:
                # Kedvezmény kód lekérése
                result = await self.supabase.table('discount_codes').select('*').eq('code', code).eq('active', True).execute()
                
                if not result.data:
                    return {
                        'valid': False,
                        'error': 'Kedvezmény kód nem található'
                    }
                
                discount = result.data[0]
            
            # Ellenőrzések
            checks = [
                ('Érvényesség', self._check_validity(discount)),
                ('Használati limit', self._check_usage_limit(discount)),
                ('Minimum rendelési érték', self._check_minimum_order_value(discount, order_value)),
                ('Vásárló specifikus', self._check_customer_specific(discount, customer_id))
            ]
            
            # Hibák összegyűjtése
            errors = [error for check_name, (valid, error) in checks if not valid]
            
            if errors:
                return {
                    'valid': False,
                    'error': '; '.join(errors)
                }
            
            # Kedvezmény összeg kalkuláció
            discount_amount = (order_value * discount['discount_percentage']) / 100
            
            return {
                'valid': True,
                'discount_percentage': discount['discount_percentage'],
                'discount_amount': discount_amount,
                'discount_id': discount['id']
            }
            
        except Exception as e:
            logger.error(f"Hiba a kedvezmény kód validálásában: {e}")
            return {
                'valid': False,
                'error': 'Hiba a kedvezmény kód ellenőrzésében'
            }
    
    async def use_discount_code(self, discount_id: int) -> bool:
        """
        Kedvezmény kód használata
        
        Args:
            discount_id: Kedvezmény azonosítója
            
        Returns:
            bool: Sikeres használat esetén True
        """
        try:
            logger.info(f"Kedvezmény kód használata: {discount_id}")
            
            # Teszt környezetben mock implementáció
            if self.is_testing:
                logger.info(f"Mock discount code used: {discount_id}")
                return True
            
            # Használat növelése
            result = await self.supabase.table('discount_codes').update({
                'times_used': self.supabase.raw('times_used + 1')
            }).eq('id', discount_id).execute()
            
            if result.data:
                logger.info(f"Kedvezmény kód sikeresen használva: {discount_id}")
                return True
            else:
                logger.error(f"Kedvezmény kód használata sikertelen: {discount_id}")
                return False
                
        except Exception as e:
            logger.error(f"Hiba a kedvezmény kód használatában: {e}")
            return False
    
    async def get_customer_discounts(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Vásárló kedvezményeinek lekérése
        
        Args:
            customer_id: Vásárló azonosítója
            
        Returns:
            List: Kedvezmények listája
        """
        try:
            logger.info(f"Vásárló kedvezményeinek lekérése: {customer_id}")
            
            # Teszt környezetben mock implementáció
            if self.is_testing:
                return [
                    {
                        'id': 1,
                        'code': 'TEST123',
                        'discount_percentage': 10.0,
                        'minimum_order_value': 10000,
                        'valid_from': datetime.now().isoformat(),
                        'valid_until': (datetime.now() + timedelta(days=7)).isoformat(),
                        'usage_limit': 1,
                        'times_used': 0,
                        'active': True
                    }
                ]
            
            result = await self.supabase.table('discount_codes').select('*').eq('customer_id', customer_id).eq('active', True).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Hiba a vásárló kedvezményeinek lekérésében: {e}")
            return []
    
    async def cleanup_expired_discounts(self) -> int:
        """
        Lejárt kedvezmény kódok tisztítása
        
        Returns:
            int: Törölt kedvezmények száma
        """
        try:
            logger.info("Lejárt kedvezmény kódok tisztítása")
            
            # Teszt környezetben mock implementáció
            if self.is_testing:
                logger.info("Mock cleanup expired discounts")
                return 0
            
            # Lejárt kedvezmények lekérése
            expired_discounts = await self.supabase.table('discount_codes').select('id').lt('valid_until', datetime.now().isoformat()).eq('active', True).execute()
            
            if not expired_discounts.data:
                return 0
            
            # Kedvezmények deaktiválása
            discount_ids = [discount['id'] for discount in expired_discounts.data]
            
            result = await self.supabase.table('discount_codes').update({
                'active': False
            }).in_('id', discount_ids).execute()
            
            deleted_count = len(discount_ids)
            logger.info(f"Lejárt kedvezmény kódok törölve: {deleted_count}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Hiba a lejárt kedvezmény kódok tisztításában: {e}")
            return 0
    
    def _generate_discount_code(self, prefix: str) -> str:
        """
        Kedvezmény kód generálása
        
        Args:
            prefix: Kód előtagja
            
        Returns:
            str: Generált kedvezmény kód
        """
        # Véletlenszerű karakterek generálása
        random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # Kód összeállítása
        discount_code = f"{prefix}{random_chars}"
        
        return discount_code
    
    def _calculate_discount_percentage(self, cart_value: float) -> float:
        """
        Kedvezmény százalék kalkuláció kosár érték alapján
        
        Args:
            cart_value: Kosár értéke
            
        Returns:
            float: Kedvezmény százalék
        """
        if cart_value >= 50000:
            return 15.0
        elif cart_value >= 25000:
            return 10.0
        elif cart_value >= 10000:
            return 5.0
        else:
            return 3.0
    
    def _get_loyalty_discount_percentage(self, loyalty_level: str) -> float:
        """
        Hűségi kedvezmény százalék lekérése
        
        Args:
            loyalty_level: Hűségi szint
            
        Returns:
            float: Kedvezmény százalék
        """
        loyalty_discounts = {
            'bronze': 5.0,
            'silver': 10.0,
            'gold': 15.0,
            'platinum': 20.0
        }
        
        return loyalty_discounts.get(loyalty_level.lower(), 5.0)
    
    def _check_validity(self, discount: Dict[str, Any]) -> tuple:
        """
        Kedvezmény érvényesség ellenőrzése
        
        Args:
            discount: Kedvezmény adatok
            
        Returns:
            tuple: (valid, error_message)
        """
        now = datetime.now()
        valid_from = datetime.fromisoformat(discount['valid_from'].replace('Z', '+00:00'))
        valid_until = datetime.fromisoformat(discount['valid_until'].replace('Z', '+00:00'))
        
        if now < valid_from:
            return False, f"Kedvezmény még nem érvényes (érvényes: {valid_from.strftime('%Y.%m.%d')}-tól)"
        
        if now > valid_until:
            return False, f"Kedvezmény lejárt (érvényes volt: {valid_until.strftime('%Y.%m.%d')}-ig)"
        
        return True, None
    
    def _check_usage_limit(self, discount: Dict[str, Any]) -> tuple:
        """
        Használati limit ellenőrzése
        
        Args:
            discount: Kedvezmény adatok
            
        Returns:
            tuple: (valid, error_message)
        """
        if discount['times_used'] >= discount['usage_limit']:
            return False, "Kedvezmény kód már felhasznált"
        
        return True, None
    
    def _check_minimum_order_value(self, discount: Dict[str, Any], order_value: float) -> tuple:
        """
        Minimum rendelési érték ellenőrzése
        
        Args:
            discount: Kedvezmény adatok
            order_value: Rendelés értéke
            
        Returns:
            tuple: (valid, error_message)
        """
        if order_value < discount['minimum_order_value']:
            return False, f"Minimum rendelési érték: {discount['minimum_order_value']:,.0f} Ft"
        
        return True, None
    
    def _check_customer_specific(self, discount: Dict[str, Any], customer_id: str) -> tuple:
        """
        Vásárló specifikus ellenőrzés
        
        Args:
            discount: Kedvezmény adatok
            customer_id: Vásárló azonosítója
            
        Returns:
            tuple: (valid, error_message)
        """
        if discount['customer_id'] and discount['customer_id'] != customer_id:
            return False, "Kedvezmény kód nem ehhez a vásárlóhoz tartozik"
        
        return True, None
    
    async def get_discount_statistics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Kedvezmény statisztikák lekérése
        
        Args:
            start_date: Kezdő dátum
            end_date: Záró dátum
            
        Returns:
            Dict: Kedvezmény statisztikák
        """
        try:
            logger.info(f"Kedvezmény statisztikák lekérése: {start_date} - {end_date}")
            
            # Teszt környezetben mock implementáció
            if self.is_testing:
                return {
                    'total_discounts': 5,
                    'total_used': 2,
                    'total_revenue_saved': 5000,
                    'by_type': {
                        'abandoned_cart': {
                            'count': 3,
                            'used': 1,
                            'avg_discount_percentage': 10.0
                        },
                        'welcome': {
                            'count': 2,
                            'used': 1,
                            'avg_discount_percentage': 10.0
                        }
                    }
                }
            
            # Kedvezmények lekérése a dátumtartományban
            result = await self.supabase.table('discount_codes').select('''
                created_for,
                discount_percentage,
                times_used,
                active
            ''').gte('created_at', start_date.isoformat()).lte('created_at', end_date.isoformat()).execute()
            
            if not result.data:
                return {
                    'total_discounts': 0,
                    'total_used': 0,
                    'total_revenue_saved': 0,
                    'by_type': {}
                }
            
            # Statisztikák kalkuláció
            stats = {
                'total_discounts': len(result.data),
                'total_used': sum(discount['times_used'] for discount in result.data),
                'total_revenue_saved': 0,  # Ezt a rendelések alapján kellene kalkulálni
                'by_type': {}
            }
            
            # Típus szerinti statisztikák
            for discount in result.data:
                discount_type = discount['created_for']
                if discount_type not in stats['by_type']:
                    stats['by_type'][discount_type] = {
                        'count': 0,
                        'used': 0,
                        'avg_discount_percentage': 0
                    }
                
                stats['by_type'][discount_type]['count'] += 1
                stats['by_type'][discount_type]['used'] += discount['times_used']
            
            # Átlagos kedvezmény százalék kalkuláció
            for discount_type in stats['by_type']:
                type_discounts = [d for d in result.data if d['created_for'] == discount_type]
                if type_discounts:
                    avg_percentage = sum(d['discount_percentage'] for d in type_discounts) / len(type_discounts)
                    stats['by_type'][discount_type]['avg_discount_percentage'] = round(avg_percentage, 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Hiba a kedvezmény statisztikák lekérésében: {e}")
            return {}
