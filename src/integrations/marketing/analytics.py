"""
Marketing analytics és teljesítmény követés
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from ..database.supabase_client import get_supabase_client
from .abandoned_cart_detector import AbandonedCartDetector
from .discount_service import DiscountService

logger = logging.getLogger(__name__)

class MarketingAnalytics:
    """
    Marketing metrikák és teljesítmény követés
    """
    
    def __init__(self):
        """Marketing analytics inicializálása"""
        self.supabase = get_supabase_client().get_client()
        self.abandoned_cart_detector = AbandonedCartDetector()
        self.discount_service = DiscountService()
        
        logger.info("Marketing analytics inicializálva")
    
    async def get_abandoned_cart_stats(self, date_range: tuple) -> Dict[str, Any]:
        """
        Kosárelhagyás statisztikák
        
        Args:
            date_range: (start_date, end_date) tuple
            
        Returns:
            Dict: Kosárelhagyás statisztikák
        """
        try:
            start_date, end_date = date_range
            logger.info(f"Kosárelhagyás statisztikák lekérése: {start_date} - {end_date}")
            
            # Abandoned cart statisztikák
            abandoned_stats = await self.abandoned_cart_detector.get_abandoned_cart_statistics(start_date, end_date)
            
            # Marketing üzenetek statisztikái
            message_stats = await self._get_marketing_message_stats(start_date, end_date)
            
            # Összesített statisztikák
            stats = {
                'total_abandoned_carts': abandoned_stats.get('total_abandoned_carts', 0),
                'total_abandoned_value': abandoned_stats.get('total_abandoned_value', 0),
                'follow_up_sent': message_stats.get('total_sent', 0),
                'return_rate': abandoned_stats.get('return_rate', 0.0),
                'conversion_rate': self._calculate_conversion_rate(abandoned_stats),
                'recovered_revenue': self._calculate_recovered_revenue(abandoned_stats),
                'email_performance': message_stats.get('email_performance', {}),
                'sms_performance': message_stats.get('sms_performance', {}),
                'daily_trends': await self._get_daily_trends(start_date, end_date)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Hiba a kosárelhagyás statisztikák lekérésében: {e}")
            return {}
    
    async def get_email_campaign_performance(self, campaign_id: int = None, date_range: tuple = None) -> Dict[str, Any]:
        """
        Email kampány teljesítmény
        
        Args:
            campaign_id: Kampány azonosítója (opcionális)
            date_range: Dátumtartomány (opcionális)
            
        Returns:
            Dict: Email kampány teljesítmény
        """
        try:
            logger.info(f"Email kampány teljesítmény lekérése: campaign_id={campaign_id}")
            
            # Marketing üzenetek lekérése
            query = self.supabase.table('marketing_messages').select('''
                COUNT(*) as sent_count,
                COUNT(opened_at) as opened_count,
                COUNT(clicked_at) as clicked_count,
                COUNT(CASE WHEN converted = true THEN 1 END) as converted_count
            ''').eq('message_type', 'email')
            
            if campaign_id:
                query = query.eq('campaign_id', campaign_id)
            
            if date_range:
                start_date, end_date = date_range
                query = query.gte('sent_at', start_date.isoformat()).lte('sent_at', end_date.isoformat())
            
            result = await query.execute()
            
            if not result.data:
                return {
                    'sent_count': 0,
                    'open_rate': 0.0,
                    'click_rate': 0.0,
                    'conversion_rate': 0.0,
                    'bounce_rate': 0.0,
                    'unsubscribe_rate': 0.0
                }
            
            data = result.data[0]
            sent_count = data['sent_count']
            
            # Ráták kalkuláció
            open_rate = (data['opened_count'] / sent_count * 100) if sent_count > 0 else 0.0
            click_rate = (data['clicked_count'] / sent_count * 100) if sent_count > 0 else 0.0
            conversion_rate = (data['converted_count'] / sent_count * 100) if sent_count > 0 else 0.0
            
            return {
                'sent_count': sent_count,
                'open_rate': round(open_rate, 2),
                'click_rate': round(click_rate, 2),
                'conversion_rate': round(conversion_rate, 2),
                'bounce_rate': 0.0,  # Ezt a SendGrid API-ból kellene lekérni
                'unsubscribe_rate': 0.0  # Ezt a SendGrid API-ból kellene lekérni
            }
            
        except Exception as e:
            logger.error(f"Hiba az email kampány teljesítmény lekérésében: {e}")
            return {}
    
    async def get_sms_campaign_performance(self, campaign_id: int = None, date_range: tuple = None) -> Dict[str, Any]:
        """
        SMS kampány teljesítmény
        
        Args:
            campaign_id: Kampány azonosítója (opcionális)
            date_range: Dátumtartomány (opcionális)
            
        Returns:
            Dict: SMS kampány teljesítmény
        """
        try:
            logger.info(f"SMS kampány teljesítmény lekérése: campaign_id={campaign_id}")
            
            # Marketing üzenetek lekérése
            query = self.supabase.table('marketing_messages').select('''
                COUNT(*) as sent_count,
                COUNT(CASE WHEN delivery_status = 'delivered' THEN 1 END) as delivered_count,
                COUNT(CASE WHEN delivery_status = 'failed' THEN 1 END) as failed_count,
                COUNT(CASE WHEN converted = true THEN 1 END) as converted_count
            ''').eq('message_type', 'sms')
            
            if campaign_id:
                query = query.eq('campaign_id', campaign_id)
            
            if date_range:
                start_date, end_date = date_range
                query = query.gte('sent_at', start_date.isoformat()).lte('sent_at', end_date.isoformat())
            
            result = await query.execute()
            
            if not result.data:
                return {
                    'sent_count': 0,
                    'delivery_rate': 0.0,
                    'failure_rate': 0.0,
                    'conversion_rate': 0.0
                }
            
            data = result.data[0]
            sent_count = data['sent_count']
            
            # Ráták kalkuláció
            delivery_rate = (data['delivered_count'] / sent_count * 100) if sent_count > 0 else 0.0
            failure_rate = (data['failed_count'] / sent_count * 100) if sent_count > 0 else 0.0
            conversion_rate = (data['converted_count'] / sent_count * 100) if sent_count > 0 else 0.0
            
            return {
                'sent_count': sent_count,
                'delivery_rate': round(delivery_rate, 2),
                'failure_rate': round(failure_rate, 2),
                'conversion_rate': round(conversion_rate, 2)
            }
            
        except Exception as e:
            logger.error(f"Hiba az SMS kampány teljesítmény lekérésében: {e}")
            return {}
    
    async def get_discount_performance(self, date_range: tuple) -> Dict[str, Any]:
        """
        Kedvezmény teljesítmény
        
        Args:
            date_range: (start_date, end_date) tuple
            
        Returns:
            Dict: Kedvezmény teljesítmény
        """
        try:
            start_date, end_date = date_range
            logger.info(f"Kedvezmény teljesítmény lekérése: {start_date} - {end_date}")
            
            # Kedvezmény statisztikák
            discount_stats = await self.discount_service.get_discount_statistics(start_date, end_date)
            
            return {
                'total_discounts': discount_stats.get('total_discounts', 0),
                'total_used': discount_stats.get('total_used', 0),
                'usage_rate': self._calculate_usage_rate(discount_stats),
                'total_revenue_saved': discount_stats.get('total_revenue_saved', 0),
                'by_type': discount_stats.get('by_type', {}),
                'avg_discount_percentage': self._calculate_avg_discount_percentage(discount_stats)
            }
            
        except Exception as e:
            logger.error(f"Hiba a kedvezmény teljesítmény lekérésében: {e}")
            return {}
    
    async def get_customer_lifetime_value(self, customer_id: str) -> Dict[str, Any]:
        """
        Vásárló életciklus érték (CLV)
        
        Args:
            customer_id: Vásárló azonosítója
            
        Returns:
            Dict: CLV adatok
        """
        try:
            logger.info(f"Vásárló CLV lekérése: {customer_id}")
            
            # Vásárló adatok lekérése (egyszerűsített implementáció)
            # A valóságban a rendelések és tranzakciók alapján kellene kalkulálni
            
            clv_data = {
                'customer_id': customer_id,
                'total_orders': 0,
                'total_spent': 0.0,
                'avg_order_value': 0.0,
                'first_order_date': None,
                'last_order_date': None,
                'abandoned_carts': 0,
                'recovered_carts': 0,
                'discounts_used': 0,
                'loyalty_level': 'bronze',
                'predicted_clv': 0.0
            }
            
            # Abandoned cart-ok száma
            abandoned_carts = await self.supabase.table('abandoned_carts').select('id, returned').eq('customer_id', customer_id).execute()
            
            if abandoned_carts.data:
                clv_data['abandoned_carts'] = len(abandoned_carts.data)
                clv_data['recovered_carts'] = sum(1 for cart in abandoned_carts.data if cart['returned'])
            
            # Kedvezmények használata
            discounts = await self.discount_service.get_customer_discounts(customer_id)
            clv_data['discounts_used'] = sum(discount['times_used'] for discount in discounts)
            
            # Prediktált CLV kalkuláció (egyszerűsített)
            clv_data['predicted_clv'] = self._calculate_predicted_clv(clv_data)
            
            return clv_data
            
        except Exception as e:
            logger.error(f"Hiba a vásárló CLV lekérésében: {customer_id}, hiba: {e}")
            return {}
    
    async def get_marketing_roi(self, date_range: tuple) -> Dict[str, Any]:
        """
        Marketing ROI (Return on Investment)
        
        Args:
            date_range: (start_date, end_date) tuple
            
        Returns:
            Dict: Marketing ROI adatok
        """
        try:
            start_date, end_date = date_range
            logger.info(f"Marketing ROI lekérése: {start_date} - {end_date}")
            
            # Marketing költségek (egyszerűsített)
            marketing_costs = {
                'email_costs': 0.0,  # SendGrid költségek
                'sms_costs': 0.0,    # Twilio költségek
                'discount_costs': 0.0,  # Kedvezmények költsége
                'total_costs': 0.0
            }
            
            # Marketing bevétel (egyszerűsített)
            marketing_revenue = {
                'recovered_revenue': 0.0,
                'conversion_revenue': 0.0,
                'total_revenue': 0.0
            }
            
            # ROI kalkuláció
            total_costs = marketing_costs['total_costs']
            total_revenue = marketing_revenue['total_revenue']
            
            roi = ((total_revenue - total_costs) / total_costs * 100) if total_costs > 0 else 0.0
            
            return {
                'total_costs': total_costs,
                'total_revenue': total_revenue,
                'roi_percentage': round(roi, 2),
                'cost_breakdown': marketing_costs,
                'revenue_breakdown': marketing_revenue
            }
            
        except Exception as e:
            logger.error(f"Hiba a marketing ROI lekérésében: {e}")
            return {}
    
    async def get_ab_test_results(self, test_id: str) -> Dict[str, Any]:
        """
        A/B teszt eredmények
        
        Args:
            test_id: Teszt azonosítója
            
        Returns:
            Dict: A/B teszt eredmények
        """
        try:
            logger.info(f"A/B teszt eredmények lekérése: {test_id}")
            
            # A/B teszt adatok lekérése (egyszerűsített implementáció)
            # A valóságban a teszt adatokból kellene kalkulálni
            
            test_results = {
                'test_id': test_id,
                'variant_a': {
                    'name': 'Kontrol csoport',
                    'sent_count': 0,
                    'open_rate': 0.0,
                    'click_rate': 0.0,
                    'conversion_rate': 0.0
                },
                'variant_b': {
                    'name': 'Teszt csoport',
                    'sent_count': 0,
                    'open_rate': 0.0,
                    'click_rate': 0.0,
                    'conversion_rate': 0.0
                },
                'statistical_significance': 0.0,
                'winner': None
            }
            
            return test_results
            
        except Exception as e:
            logger.error(f"Hiba az A/B teszt eredmények lekérésében: {test_id}, hiba: {e}")
            return {}
    
    async def _get_marketing_message_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Marketing üzenetek statisztikái
        
        Args:
            start_date: Kezdő dátum
            end_date: Záró dátum
            
        Returns:
            Dict: Marketing üzenetek statisztikái
        """
        try:
            # Email üzenetek
            email_result = await self.supabase.table('marketing_messages').select('''
                COUNT(*) as sent_count,
                COUNT(opened_at) as opened_count,
                COUNT(clicked_at) as clicked_count,
                COUNT(CASE WHEN converted = true THEN 1 END) as converted_count
            ''').eq('message_type', 'email').gte('sent_at', start_date.isoformat()).lte('sent_at', end_date.isoformat()).execute()
            
            # SMS üzenetek
            sms_result = await self.supabase.table('marketing_messages').select('''
                COUNT(*) as sent_count,
                COUNT(CASE WHEN delivery_status = 'delivered' THEN 1 END) as delivered_count,
                COUNT(CASE WHEN delivery_status = 'failed' THEN 1 END) as failed_count,
                COUNT(CASE WHEN converted = true THEN 1 END) as converted_count
            ''').eq('message_type', 'sms').gte('sent_at', start_date.isoformat()).lte('sent_at', end_date.isoformat()).execute()
            
            email_data = email_result.data[0] if email_result.data else {}
            sms_data = sms_result.data[0] if sms_result.data else {}
            
            total_sent = (email_data.get('sent_count', 0) + sms_data.get('sent_count', 0))
            
            return {
                'total_sent': total_sent,
                'email_performance': {
                    'sent_count': email_data.get('sent_count', 0),
                    'open_rate': self._calculate_rate(email_data.get('opened_count', 0), email_data.get('sent_count', 0)),
                    'click_rate': self._calculate_rate(email_data.get('clicked_count', 0), email_data.get('sent_count', 0)),
                    'conversion_rate': self._calculate_rate(email_data.get('converted_count', 0), email_data.get('sent_count', 0))
                },
                'sms_performance': {
                    'sent_count': sms_data.get('sent_count', 0),
                    'delivery_rate': self._calculate_rate(sms_data.get('delivered_count', 0), sms_data.get('sent_count', 0)),
                    'failure_rate': self._calculate_rate(sms_data.get('failed_count', 0), sms_data.get('sent_count', 0)),
                    'conversion_rate': self._calculate_rate(sms_data.get('converted_count', 0), sms_data.get('sent_count', 0))
                }
            }
            
        except Exception as e:
            logger.error(f"Hiba a marketing üzenetek statisztikáinak lekérésében: {e}")
            return {}
    
    async def _get_daily_trends(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Napi trendek lekérése
        
        Args:
            start_date: Kezdő dátum
            end_date: Záró dátum
            
        Returns:
            List: Napi trendek
        """
        try:
            trends = []
            current_date = start_date
            
            while current_date <= end_date:
                day_start = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
                
                # Napi abandoned cart-ok
                daily_abandoned = await self.supabase.table('abandoned_carts').select('cart_value').gte('created_at', day_start.isoformat()).lt('created_at', day_end.isoformat()).execute()
                
                # Napi marketing üzenetek
                daily_messages = await self.supabase.table('marketing_messages').select('message_type, converted').gte('sent_at', day_start.isoformat()).lt('sent_at', day_end.isoformat()).execute()
                
                trends.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'abandoned_carts': len(daily_abandoned.data),
                    'abandoned_value': sum(cart['cart_value'] for cart in daily_abandoned.data),
                    'emails_sent': sum(1 for msg in daily_messages.data if msg['message_type'] == 'email'),
                    'sms_sent': sum(1 for msg in daily_messages.data if msg['message_type'] == 'sms'),
                    'conversions': sum(1 for msg in daily_messages.data if msg['converted'])
                })
                
                current_date += timedelta(days=1)
            
            return trends
            
        except Exception as e:
            logger.error(f"Hiba a napi trendek lekérésében: {e}")
            return []
    
    def _calculate_conversion_rate(self, abandoned_stats: Dict[str, Any]) -> float:
        """Konverziós ráta kalkuláció"""
        total_carts = abandoned_stats.get('total_abandoned_carts', 0)
        returned_carts = abandoned_stats.get('returned_count', 0)
        
        return (returned_carts / total_carts * 100) if total_carts > 0 else 0.0
    
    def _calculate_recovered_revenue(self, abandoned_stats: Dict[str, Any]) -> float:
        """Visszanyert bevétel kalkuláció"""
        total_value = abandoned_stats.get('total_abandoned_value', 0)
        return_rate = abandoned_stats.get('return_rate', 0.0)
        
        return total_value * (return_rate / 100)
    
    def _calculate_usage_rate(self, discount_stats: Dict[str, Any]) -> float:
        """Kedvezmény használati ráta kalkuláció"""
        total_discounts = discount_stats.get('total_discounts', 0)
        total_used = discount_stats.get('total_used', 0)
        
        return (total_used / total_discounts * 100) if total_discounts > 0 else 0.0
    
    def _calculate_avg_discount_percentage(self, discount_stats: Dict[str, Any]) -> float:
        """Átlagos kedvezmény százalék kalkuláció"""
        by_type = discount_stats.get('by_type', {})
        
        if not by_type:
            return 0.0
        
        total_percentage = sum(type_stats.get('avg_discount_percentage', 0) for type_stats in by_type.values())
        return total_percentage / len(by_type)
    
    def _calculate_predicted_clv(self, clv_data: Dict[str, Any]) -> float:
        """Prediktált CLV kalkuláció (egyszerűsített)"""
        avg_order_value = clv_data.get('avg_order_value', 0)
        total_orders = clv_data.get('total_orders', 0)
        loyalty_multiplier = {
            'bronze': 1.0,
            'silver': 1.5,
            'gold': 2.0,
            'platinum': 3.0
        }.get(clv_data.get('loyalty_level', 'bronze'), 1.0)
        
        return avg_order_value * total_orders * loyalty_multiplier
    
    def _calculate_rate(self, numerator: int, denominator: int) -> float:
        """Ráta kalkuláció"""
        return (numerator / denominator * 100) if denominator > 0 else 0.0
