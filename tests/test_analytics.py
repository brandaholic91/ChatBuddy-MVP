"""
Tests for marketing analytics module
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import os
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from integrations.marketing.analytics import MarketingAnalytics


class TestMarketingAnalytics:
    """Tests for MarketingAnalytics"""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client"""
        with patch('integrations.marketing.analytics.get_supabase_client') as mock_client:
            mock_supabase = Mock()
            mock_client.return_value.get_client.return_value = mock_supabase
            yield mock_supabase
    
    @pytest.fixture
    def mock_abandoned_cart_detector(self):
        """Mock abandoned cart detector"""
        with patch('integrations.marketing.analytics.AbandonedCartDetector') as mock_detector:
            mock_instance = Mock()
            mock_detector.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def mock_discount_service(self):
        """Mock discount service"""
        with patch('integrations.marketing.analytics.DiscountService') as mock_service:
            mock_instance = Mock()
            mock_service.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def analytics(self, mock_supabase_client, mock_abandoned_cart_detector, mock_discount_service):
        """Create MarketingAnalytics instance"""
        analytics = MarketingAnalytics()
        return analytics

    # Initialization tests
    def test_init(self, analytics):
        """Test analytics initialization"""
        assert analytics.supabase is not None
        assert analytics.abandoned_cart_detector is not None
        assert analytics.discount_service is not None

    # Abandoned cart stats tests
    @pytest.mark.asyncio
    async def test_get_abandoned_cart_stats_success(self, analytics, mock_abandoned_cart_detector):
        """Test successful abandoned cart stats retrieval"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        date_range = (start_date, end_date)
        
        # Mock abandoned cart stats
        mock_abandoned_cart_detector.get_abandoned_cart_statistics = AsyncMock(return_value={
            'total_abandoned_carts': 10,
            'total_abandoned_value': 50000.0,
            'return_rate': 20.0,
            'returned_count': 2
        })
        
        # Mock marketing message stats
        analytics._get_marketing_message_stats = AsyncMock(return_value={
            'total_sent': 5,
            'email_performance': {'sent_count': 3, 'open_rate': 25.0},
            'sms_performance': {'sent_count': 2, 'delivery_rate': 90.0}
        })
        
        # Mock daily trends
        analytics._get_daily_trends = AsyncMock(return_value=[
            {'date': '2024-01-01', 'abandoned_carts': 1, 'abandoned_value': 5000.0}
        ])
        
        result = await analytics.get_abandoned_cart_stats(date_range)
        
        assert result['total_abandoned_carts'] == 10
        assert result['total_abandoned_value'] == 50000.0
        assert result['follow_up_sent'] == 5
        assert result['return_rate'] == 20.0
        assert 'conversion_rate' in result
        assert 'recovered_revenue' in result
        assert 'email_performance' in result
        assert 'sms_performance' in result
        assert 'daily_trends' in result

    @pytest.mark.asyncio
    async def test_get_abandoned_cart_stats_exception(self, analytics, mock_abandoned_cart_detector):
        """Test abandoned cart stats with exception"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        date_range = (start_date, end_date)
        
        # Mock exception
        mock_abandoned_cart_detector.get_abandoned_cart_statistics.side_effect = Exception("Database error")
        
        result = await analytics.get_abandoned_cart_stats(date_range)
        
        assert result == {}

    # Email campaign performance tests
    @pytest.mark.asyncio
    async def test_get_email_campaign_performance_success(self, analytics, mock_supabase_client):
        """Test successful email campaign performance retrieval"""
        campaign_id = 123
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        date_range = (start_date, end_date)
        
        # Mock Supabase query chain
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_gte = Mock()
        mock_lte = Mock()
        mock_execute = AsyncMock()
        mock_execute.return_value = Mock(data=[{
            'sent_count': 100,
            'opened_count': 30,
            'clicked_count': 10,
            'converted_count': 5
        }])
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.gte.return_value = mock_gte
        mock_gte.lte.return_value = mock_lte
        mock_lte.execute = mock_execute
        mock_supabase_client.table.return_value = mock_table
        
        result = await analytics.get_email_campaign_performance(campaign_id, date_range)
        
        assert result['sent_count'] == 100
        assert result['open_rate'] == 30.0  # 30/100 * 100
        assert result['click_rate'] == 10.0  # 10/100 * 100
        assert result['conversion_rate'] == 5.0  # 5/100 * 100
        assert result['bounce_rate'] == 0.0
        assert result['unsubscribe_rate'] == 0.0

    @pytest.mark.asyncio
    async def test_get_email_campaign_performance_no_data(self, analytics, mock_supabase_client):
        """Test email campaign performance with no data"""
        # Mock empty result
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = AsyncMock()
        mock_execute.return_value = Mock(data=[])
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute = mock_execute
        mock_supabase_client.table.return_value = mock_table
        
        result = await analytics.get_email_campaign_performance()
        
        assert result['sent_count'] == 0
        assert result['open_rate'] == 0.0
        assert result['click_rate'] == 0.0
        assert result['conversion_rate'] == 0.0

    @pytest.mark.asyncio
    async def test_get_email_campaign_performance_exception(self, analytics, mock_supabase_client):
        """Test email campaign performance with exception"""
        # Mock exception
        mock_supabase_client.table.side_effect = Exception("Database error")
        
        result = await analytics.get_email_campaign_performance()
        
        assert result == {}

    # SMS campaign performance tests
    @pytest.mark.asyncio
    async def test_get_sms_campaign_performance_success(self, analytics, mock_supabase_client):
        """Test successful SMS campaign performance retrieval"""
        campaign_id = 456
        
        # Mock Supabase query chain
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_execute = AsyncMock()
        mock_execute.return_value = Mock(data=[{
            'sent_count': 50,
            'delivered_count': 45,
            'failed_count': 3,
            'converted_count': 8
        }])
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.execute = mock_execute
        mock_supabase_client.table.return_value = mock_table
        
        result = await analytics.get_sms_campaign_performance(campaign_id)
        
        assert result['sent_count'] == 50
        assert result['delivery_rate'] == 90.0  # 45/50 * 100
        assert result['failure_rate'] == 6.0    # 3/50 * 100
        assert result['conversion_rate'] == 16.0  # 8/50 * 100

    @pytest.mark.asyncio
    async def test_get_sms_campaign_performance_no_data(self, analytics, mock_supabase_client):
        """Test SMS campaign performance with no data"""
        # Mock empty result
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = AsyncMock()
        mock_execute.return_value = Mock(data=[])
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute = mock_execute
        mock_supabase_client.table.return_value = mock_table
        
        result = await analytics.get_sms_campaign_performance()
        
        assert result['sent_count'] == 0
        assert result['delivery_rate'] == 0.0
        assert result['failure_rate'] == 0.0
        assert result['conversion_rate'] == 0.0

    @pytest.mark.asyncio
    async def test_get_sms_campaign_performance_exception(self, analytics, mock_supabase_client):
        """Test SMS campaign performance with exception"""
        # Mock exception
        mock_supabase_client.table.side_effect = Exception("Database error")
        
        result = await analytics.get_sms_campaign_performance()
        
        assert result == {}

    # Discount performance tests
    @pytest.mark.asyncio
    async def test_get_discount_performance_success(self, analytics, mock_discount_service):
        """Test successful discount performance retrieval"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        date_range = (start_date, end_date)
        
        # Mock discount service stats
        mock_discount_service.get_discount_statistics = AsyncMock(return_value={
            'total_discounts': 20,
            'total_used': 8,
            'total_revenue_saved': 15000.0,
            'by_type': {
                'abandoned_cart': {'avg_discount_percentage': 10.0},
                'welcome': {'avg_discount_percentage': 15.0}
            }
        })
        
        result = await analytics.get_discount_performance(date_range)
        
        assert result['total_discounts'] == 20
        assert result['total_used'] == 8
        assert result['usage_rate'] == 40.0  # 8/20 * 100
        assert result['total_revenue_saved'] == 15000.0
        assert 'by_type' in result
        assert result['avg_discount_percentage'] == 12.5  # (10.0 + 15.0) / 2

    @pytest.mark.asyncio
    async def test_get_discount_performance_exception(self, analytics, mock_discount_service):
        """Test discount performance with exception"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        date_range = (start_date, end_date)
        
        # Mock exception
        mock_discount_service.get_discount_statistics.side_effect = Exception("Service error")
        
        result = await analytics.get_discount_performance(date_range)
        
        assert result == {}

    # Customer lifetime value tests
    @pytest.mark.asyncio
    async def test_get_customer_lifetime_value_success(self, analytics, mock_supabase_client, mock_discount_service):
        """Test successful customer lifetime value retrieval"""
        customer_id = "customer_123"
        
        # Mock abandoned carts query
        mock_table1 = Mock()
        mock_select1 = Mock()
        mock_eq1 = Mock()
        mock_execute1 = AsyncMock()
        mock_execute1.return_value = Mock(data=[
            {'id': 1, 'returned': True},
            {'id': 2, 'returned': False},
            {'id': 3, 'returned': True}
        ])
        
        mock_table1.select.return_value = mock_select1
        mock_select1.eq.return_value = mock_eq1
        mock_eq1.execute = mock_execute1
        
        mock_supabase_client.table.return_value = mock_table1
        
        # Mock discount service
        mock_discount_service.get_customer_discounts = AsyncMock(return_value=[
            {'times_used': 1},
            {'times_used': 0},
            {'times_used': 2}
        ])
        
        result = await analytics.get_customer_lifetime_value(customer_id)
        
        assert result['customer_id'] == customer_id
        assert result['abandoned_carts'] == 3
        assert result['recovered_carts'] == 2
        assert result['discounts_used'] == 3  # 1 + 0 + 2
        assert result['loyalty_level'] == 'bronze'
        assert 'predicted_clv' in result

    @pytest.mark.asyncio
    async def test_get_customer_lifetime_value_no_data(self, analytics, mock_supabase_client, mock_discount_service):
        """Test customer lifetime value with no data"""
        customer_id = "customer_456"
        
        # Mock empty results
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = AsyncMock()
        mock_execute.return_value = Mock(data=[])
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute = mock_execute
        mock_supabase_client.table.return_value = mock_table
        
        mock_discount_service.get_customer_discounts = AsyncMock(return_value=[])
        
        result = await analytics.get_customer_lifetime_value(customer_id)
        
        assert result['customer_id'] == customer_id
        assert result['abandoned_carts'] == 0
        assert result['recovered_carts'] == 0
        assert result['discounts_used'] == 0

    @pytest.mark.asyncio
    async def test_get_customer_lifetime_value_exception(self, analytics, mock_supabase_client):
        """Test customer lifetime value with exception"""
        customer_id = "customer_789"
        
        # Mock exception
        mock_supabase_client.table.side_effect = Exception("Database error")
        
        result = await analytics.get_customer_lifetime_value(customer_id)
        
        assert result == {}

    # Marketing ROI tests
    @pytest.mark.asyncio
    async def test_get_marketing_roi_success(self, analytics):
        """Test successful marketing ROI calculation"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        date_range = (start_date, end_date)
        
        result = await analytics.get_marketing_roi(date_range)
        
        assert 'total_costs' in result
        assert 'total_revenue' in result
        assert 'roi_percentage' in result
        assert 'cost_breakdown' in result
        assert 'revenue_breakdown' in result
        assert result['roi_percentage'] == 0.0  # Since both costs and revenue are 0

    @pytest.mark.asyncio
    async def test_get_marketing_roi_exception(self, analytics):
        """Test marketing ROI with exception"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        date_range = (start_date, end_date)
        
        # Force exception by mocking logger
        with patch('integrations.marketing.analytics.logger') as mock_logger:
            mock_logger.info.side_effect = Exception("Logger error")
            
            result = await analytics.get_marketing_roi(date_range)
            
            assert result == {}

    # A/B test results tests
    @pytest.mark.asyncio
    async def test_get_ab_test_results_success(self, analytics):
        """Test successful A/B test results retrieval"""
        test_id = "test_123"
        
        result = await analytics.get_ab_test_results(test_id)
        
        assert result['test_id'] == test_id
        assert 'variant_a' in result
        assert 'variant_b' in result
        assert 'statistical_significance' in result
        assert 'winner' in result
        assert result['variant_a']['name'] == 'Kontrol csoport'
        assert result['variant_b']['name'] == 'Teszt csoport'

    @pytest.mark.asyncio
    async def test_get_ab_test_results_exception(self, analytics):
        """Test A/B test results with exception"""
        test_id = "test_456"
        
        # Force exception by mocking logger
        with patch('integrations.marketing.analytics.logger') as mock_logger:
            mock_logger.info.side_effect = Exception("Logger error")
            
            result = await analytics.get_ab_test_results(test_id)
            
            assert result == {}

    # Marketing message stats tests
    @pytest.mark.asyncio
    async def test_get_marketing_message_stats_success(self, analytics, mock_supabase_client):
        """Test successful marketing message stats retrieval"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        # Mock multiple table calls (email and SMS)
        call_count = 0
        def table_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            
            mock_table = Mock()
            mock_select = Mock()
            mock_eq = Mock()
            mock_gte = Mock()
            mock_lte = Mock()
            mock_execute = AsyncMock()
            
            if call_count == 1:  # Email stats
                mock_execute.return_value = Mock(data=[{
                    'sent_count': 100,
                    'opened_count': 30,
                    'clicked_count': 10,
                    'converted_count': 5
                }])
            else:  # SMS stats
                mock_execute.return_value = Mock(data=[{
                    'sent_count': 50,
                    'delivered_count': 45,
                    'failed_count': 3,
                    'converted_count': 8
                }])
            
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.gte.return_value = mock_gte
            mock_gte.lte.return_value = mock_lte
            mock_lte.execute = mock_execute
            
            return mock_table
        
        mock_supabase_client.table.side_effect = table_side_effect
        
        result = await analytics._get_marketing_message_stats(start_date, end_date)
        
        assert result['total_sent'] == 150  # 100 + 50
        assert result['email_performance']['sent_count'] == 100
        assert result['email_performance']['open_rate'] == 30.0
        assert result['email_performance']['click_rate'] == 10.0
        assert result['email_performance']['conversion_rate'] == 5.0
        assert result['sms_performance']['sent_count'] == 50
        assert result['sms_performance']['delivery_rate'] == 90.0
        assert result['sms_performance']['failure_rate'] == 6.0
        assert result['sms_performance']['conversion_rate'] == 16.0

    @pytest.mark.asyncio
    async def test_get_marketing_message_stats_no_data(self, analytics, mock_supabase_client):
        """Test marketing message stats with no data"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        # Mock empty results
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_gte = Mock()
        mock_lte = Mock()
        mock_execute = AsyncMock()
        mock_execute.return_value = Mock(data=[])
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.gte.return_value = mock_gte
        mock_gte.lte.return_value = mock_lte
        mock_lte.execute = mock_execute
        mock_supabase_client.table.return_value = mock_table
        
        result = await analytics._get_marketing_message_stats(start_date, end_date)
        
        assert result['total_sent'] == 0
        assert result['email_performance']['sent_count'] == 0
        assert result['sms_performance']['sent_count'] == 0

    @pytest.mark.asyncio
    async def test_get_marketing_message_stats_exception(self, analytics, mock_supabase_client):
        """Test marketing message stats with exception"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        # Mock exception
        mock_supabase_client.table.side_effect = Exception("Database error")
        
        result = await analytics._get_marketing_message_stats(start_date, end_date)
        
        assert result == {}

    # Daily trends tests
    @pytest.mark.asyncio
    async def test_get_daily_trends_success(self, analytics, mock_supabase_client):
        """Test successful daily trends retrieval"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)  # 2 days
        
        # Mock multiple table calls for different queries
        call_count = 0
        def table_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            
            mock_table = Mock()
            mock_select = Mock()
            mock_gte = Mock()
            mock_lt = Mock()
            mock_execute = AsyncMock()
            
            if 'abandoned_carts' in table_name or call_count % 2 == 1:  # Abandoned carts
                mock_execute.return_value = Mock(data=[
                    {'cart_value': 5000.0},
                    {'cart_value': 3000.0}
                ])
            else:  # Marketing messages
                mock_execute.return_value = Mock(data=[
                    {'message_type': 'email', 'converted': True},
                    {'message_type': 'sms', 'converted': False},
                    {'message_type': 'email', 'converted': True}
                ])
            
            mock_table.select.return_value = mock_select
            mock_select.gte.return_value = mock_gte
            mock_gte.lt.return_value = mock_lt
            mock_lt.execute = mock_execute
            
            return mock_table
        
        mock_supabase_client.table.side_effect = table_side_effect
        
        result = await analytics._get_daily_trends(start_date, end_date)
        
        assert len(result) == 2  # 2 days
        assert result[0]['date'] == '2024-01-01'
        assert result[0]['abandoned_carts'] == 2
        assert result[0]['abandoned_value'] == 8000.0  # 5000 + 3000
        assert result[0]['emails_sent'] == 2
        assert result[0]['sms_sent'] == 1
        assert result[0]['conversions'] == 2
        
        assert result[1]['date'] == '2024-01-02'

    @pytest.mark.asyncio
    async def test_get_daily_trends_exception(self, analytics, mock_supabase_client):
        """Test daily trends with exception"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)
        
        # Mock exception
        mock_supabase_client.table.side_effect = Exception("Database error")
        
        result = await analytics._get_daily_trends(start_date, end_date)
        
        assert result == []

    # Private method tests
    def test_calculate_conversion_rate(self, analytics):
        """Test conversion rate calculation"""
        abandoned_stats = {
            'total_abandoned_carts': 100,
            'returned_count': 25
        }
        
        result = analytics._calculate_conversion_rate(abandoned_stats)
        assert result == 25.0  # 25/100 * 100

    def test_calculate_conversion_rate_zero_carts(self, analytics):
        """Test conversion rate calculation with zero carts"""
        abandoned_stats = {
            'total_abandoned_carts': 0,
            'returned_count': 0
        }
        
        result = analytics._calculate_conversion_rate(abandoned_stats)
        assert result == 0.0

    def test_calculate_recovered_revenue(self, analytics):
        """Test recovered revenue calculation"""
        abandoned_stats = {
            'total_abandoned_value': 10000.0,
            'return_rate': 20.0
        }
        
        result = analytics._calculate_recovered_revenue(abandoned_stats)
        assert result == 2000.0  # 10000 * (20/100)

    def test_calculate_usage_rate(self, analytics):
        """Test usage rate calculation"""
        discount_stats = {
            'total_discounts': 50,
            'total_used': 15
        }
        
        result = analytics._calculate_usage_rate(discount_stats)
        assert result == 30.0  # 15/50 * 100

    def test_calculate_usage_rate_zero_discounts(self, analytics):
        """Test usage rate calculation with zero discounts"""
        discount_stats = {
            'total_discounts': 0,
            'total_used': 0
        }
        
        result = analytics._calculate_usage_rate(discount_stats)
        assert result == 0.0

    def test_calculate_avg_discount_percentage(self, analytics):
        """Test average discount percentage calculation"""
        discount_stats = {
            'by_type': {
                'abandoned_cart': {'avg_discount_percentage': 10.0},
                'welcome': {'avg_discount_percentage': 15.0},
                'loyalty': {'avg_discount_percentage': 12.0}
            }
        }
        
        result = analytics._calculate_avg_discount_percentage(discount_stats)
        assert result == 12.333333333333334  # (10.0 + 15.0 + 12.0) / 3

    def test_calculate_avg_discount_percentage_empty(self, analytics):
        """Test average discount percentage calculation with empty data"""
        discount_stats = {'by_type': {}}
        
        result = analytics._calculate_avg_discount_percentage(discount_stats)
        assert result == 0.0

    def test_calculate_predicted_clv(self, analytics):
        """Test predicted CLV calculation"""
        clv_data = {
            'avg_order_value': 5000.0,
            'total_orders': 10,
            'loyalty_level': 'gold'
        }
        
        result = analytics._calculate_predicted_clv(clv_data)
        assert result == 100000.0  # 5000 * 10 * 2.0

    @pytest.mark.parametrize("loyalty_level,expected_multiplier", [
        ('bronze', 1.0),
        ('silver', 1.5),
        ('gold', 2.0),
        ('platinum', 3.0),
        ('unknown', 1.0)  # Default
    ])
    def test_calculate_predicted_clv_loyalty_levels(self, analytics, loyalty_level, expected_multiplier):
        """Test predicted CLV calculation with different loyalty levels"""
        clv_data = {
            'avg_order_value': 1000.0,
            'total_orders': 5,
            'loyalty_level': loyalty_level
        }
        
        result = analytics._calculate_predicted_clv(clv_data)
        assert result == 1000.0 * 5 * expected_multiplier

    def test_calculate_rate(self, analytics):
        """Test rate calculation"""
        result = analytics._calculate_rate(25, 100)
        assert result == 25.0  # 25/100 * 100

    def test_calculate_rate_zero_denominator(self, analytics):
        """Test rate calculation with zero denominator"""
        result = analytics._calculate_rate(25, 0)
        assert result == 0.0