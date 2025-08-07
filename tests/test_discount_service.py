"""
Tests for discount service module
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import os
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from integrations.marketing.discount_service import DiscountService


class TestDiscountService:
    """Tests for DiscountService"""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client"""
        with patch('integrations.marketing.discount_service.get_supabase_client') as mock_client:
            mock_supabase = Mock()
            mock_client.return_value.get_client.return_value = mock_supabase
            yield mock_supabase
    
    @pytest.fixture
    def discount_service(self, mock_supabase_client):
        """Create DiscountService instance"""
        with patch.dict(os.environ, {'TESTING': 'true'}):
            service = DiscountService()
            return service
    
    @pytest.fixture
    def non_testing_discount_service(self, mock_supabase_client):
        """Create DiscountService instance without testing flag"""
        with patch.dict(os.environ, {'TESTING': 'false'}):
            service = DiscountService()
            return service

    # Initialization tests
    def test_init(self, discount_service):
        """Test discount service initialization"""
        assert discount_service.is_testing is True
        assert discount_service.supabase is not None
    
    def test_init_non_testing(self, non_testing_discount_service):
        """Test discount service initialization in non-testing mode"""
        assert non_testing_discount_service.is_testing is False
        assert non_testing_discount_service.supabase is not None

    # Abandoned cart discount tests
    @pytest.mark.asyncio
    async def test_generate_abandoned_cart_discount_testing(self, discount_service):
        """Test abandoned cart discount generation in testing mode"""
        customer_id = "test_customer_123"
        cart_value = 25000.0
        
        result = await discount_service.generate_abandoned_cart_discount(customer_id, cart_value)
        
        assert isinstance(result, str)
        assert result.startswith("CART")
        assert len(result) == 10  # CART + 6 random chars

    @pytest.mark.asyncio
    async def test_generate_abandoned_cart_discount_non_testing(self, non_testing_discount_service, mock_supabase_client):
        """Test abandoned cart discount generation in non-testing mode"""
        customer_id = "test_customer_123"
        cart_value = 25000.0
        
        # Mock Supabase table operations
        mock_table = Mock()
        mock_insert = Mock()
        mock_execute = AsyncMock()
        mock_execute.return_value = Mock(data=[{'code': 'CART123456'}])
        
        mock_table.insert.return_value = mock_insert
        mock_insert.execute = mock_execute
        mock_supabase_client.table.return_value = mock_table
        
        result = await non_testing_discount_service.generate_abandoned_cart_discount(customer_id, cart_value)
        
        assert isinstance(result, str)
        assert result.startswith("CART")
        mock_supabase_client.table.assert_called_with('discount_codes')
        mock_table.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_abandoned_cart_discount_exception(self, non_testing_discount_service, mock_supabase_client):
        """Test abandoned cart discount generation exception handling"""
        customer_id = "test_customer_123"
        cart_value = 25000.0
        
        # Mock exception
        mock_supabase_client.table.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            await non_testing_discount_service.generate_abandoned_cart_discount(customer_id, cart_value)

    # Welcome discount tests
    @pytest.mark.asyncio
    async def test_generate_welcome_discount_testing(self, discount_service):
        """Test welcome discount generation in testing mode"""
        customer_id = "test_customer_123"
        
        result = await discount_service.generate_welcome_discount(customer_id)
        
        assert isinstance(result, str)
        assert result.startswith("WELCOME")
        assert len(result) == 13  # WELCOME + 6 random chars

    @pytest.mark.asyncio
    async def test_generate_welcome_discount_non_testing(self, non_testing_discount_service, mock_supabase_client):
        """Test welcome discount generation in non-testing mode"""
        customer_id = "test_customer_123"
        
        # Mock Supabase table operations
        mock_table = Mock()
        mock_insert = Mock()
        mock_execute = AsyncMock()
        mock_execute.return_value = Mock(data=[{'code': 'WELCOME123456'}])
        
        mock_table.insert.return_value = mock_insert
        mock_insert.execute = mock_execute
        mock_supabase_client.table.return_value = mock_table
        
        result = await non_testing_discount_service.generate_welcome_discount(customer_id)
        
        assert isinstance(result, str)
        assert result.startswith("WELCOME")
        mock_supabase_client.table.assert_called_with('discount_codes')

    @pytest.mark.asyncio
    async def test_generate_welcome_discount_exception(self, non_testing_discount_service, mock_supabase_client):
        """Test welcome discount generation exception handling"""
        customer_id = "test_customer_123"
        
        # Mock exception
        mock_supabase_client.table.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            await non_testing_discount_service.generate_welcome_discount(customer_id)

    # Loyalty discount tests
    @pytest.mark.parametrize("loyalty_level,expected_percentage", [
        ("bronze", 5.0),
        ("silver", 10.0),
        ("gold", 15.0),
        ("platinum", 20.0),
        ("unknown", 5.0)  # Default value
    ])
    @pytest.mark.asyncio
    async def test_generate_loyalty_discount_testing(self, discount_service, loyalty_level, expected_percentage):
        """Test loyalty discount generation in testing mode with different levels"""
        customer_id = "test_customer_123"
        
        result = await discount_service.generate_loyalty_discount(customer_id, loyalty_level)
        
        assert isinstance(result, str)
        assert result.startswith("LOYALTY")
        assert len(result) == 13  # LOYALTY + 6 random chars

    @pytest.mark.asyncio
    async def test_generate_loyalty_discount_non_testing(self, non_testing_discount_service, mock_supabase_client):
        """Test loyalty discount generation in non-testing mode"""
        customer_id = "test_customer_123"
        loyalty_level = "gold"
        
        # Mock Supabase table operations
        mock_table = Mock()
        mock_insert = Mock()
        mock_execute = AsyncMock()
        mock_execute.return_value = Mock(data=[{'code': 'LOYALTY123456'}])
        
        mock_table.insert.return_value = mock_insert
        mock_insert.execute = mock_execute
        mock_supabase_client.table.return_value = mock_table
        
        result = await non_testing_discount_service.generate_loyalty_discount(customer_id, loyalty_level)
        
        assert isinstance(result, str)
        assert result.startswith("LOYALTY")
        mock_supabase_client.table.assert_called_with('discount_codes')

    # Discount validation tests
    @pytest.mark.asyncio
    async def test_validate_discount_code_testing(self, discount_service):
        """Test discount code validation in testing mode"""
        code = "TEST123"
        customer_id = "test_customer_123"
        order_value = 15000.0
        
        result = await discount_service.validate_discount_code(code, customer_id, order_value)
        
        assert result['valid'] is True
        assert result['discount_percentage'] == 15.0
        assert result['discount_amount'] == 2250.0  # 15% of 15000
        assert 'discount_id' in result

    @pytest.mark.asyncio
    async def test_validate_discount_code_invalid_testing(self, discount_service):
        """Test discount code validation with invalid order value in testing mode"""
        code = "TEST123"
        customer_id = "test_customer_123"
        order_value = 5000.0  # Below minimum
        
        result = await discount_service.validate_discount_code(code, customer_id, order_value)
        
        assert result['valid'] is False
        assert 'Minimum rendelési érték' in result['error']

    @pytest.mark.asyncio
    async def test_validate_discount_code_non_testing_not_found(self, non_testing_discount_service, mock_supabase_client):
        """Test discount code validation when code not found"""
        code = "NOTFOUND123"
        customer_id = "test_customer_123"
        order_value = 15000.0
        
        # Mock empty result
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = AsyncMock()
        mock_execute.return_value = Mock(data=[])
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.eq.return_value = mock_eq
        mock_eq.execute = mock_execute
        mock_supabase_client.table.return_value = mock_table
        
        result = await non_testing_discount_service.validate_discount_code(code, customer_id, order_value)
        
        assert result['valid'] is False
        assert 'nem található' in result['error']

    @pytest.mark.asyncio
    async def test_validate_discount_code_exception(self, non_testing_discount_service, mock_supabase_client):
        """Test discount code validation exception handling"""
        code = "TEST123"
        customer_id = "test_customer_123"
        order_value = 15000.0
        
        # Mock exception
        mock_supabase_client.table.side_effect = Exception("Database error")
        
        result = await non_testing_discount_service.validate_discount_code(code, customer_id, order_value)
        
        assert result['valid'] is False
        assert 'Hiba a kedvezmény kód ellenőrzésében' in result['error']

    # Use discount code tests
    @pytest.mark.asyncio
    async def test_use_discount_code_testing(self, discount_service):
        """Test using discount code in testing mode"""
        discount_id = 123
        
        result = await discount_service.use_discount_code(discount_id)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_use_discount_code_non_testing_success(self, non_testing_discount_service, mock_supabase_client):
        """Test using discount code in non-testing mode - success"""
        discount_id = 123
        
        # Mock successful update
        mock_table = Mock()
        mock_update = Mock()
        mock_eq = Mock()
        mock_execute = AsyncMock()
        mock_execute.return_value = Mock(data=[{'id': 123}])
        
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.execute = mock_execute
        mock_supabase_client.table.return_value = mock_table
        
        result = await non_testing_discount_service.use_discount_code(discount_id)
        
        assert result is True
        mock_supabase_client.table.assert_called_with('discount_codes')

    @pytest.mark.asyncio
    async def test_use_discount_code_non_testing_failure(self, non_testing_discount_service, mock_supabase_client):
        """Test using discount code in non-testing mode - failure"""
        discount_id = 123
        
        # Mock failed update
        mock_table = Mock()
        mock_update = Mock()
        mock_eq = Mock()
        mock_execute = AsyncMock()
        mock_execute.return_value = Mock(data=[])
        
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.execute = mock_execute
        mock_supabase_client.table.return_value = mock_table
        
        result = await non_testing_discount_service.use_discount_code(discount_id)
        
        assert result is False

    # Get customer discounts tests
    @pytest.mark.asyncio
    async def test_get_customer_discounts_testing(self, discount_service):
        """Test getting customer discounts in testing mode"""
        customer_id = "test_customer_123"
        
        result = await discount_service.get_customer_discounts(customer_id)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['code'] == 'TEST123'
        assert result[0]['discount_percentage'] == 10.0

    @pytest.mark.asyncio
    async def test_get_customer_discounts_non_testing(self, non_testing_discount_service, mock_supabase_client):
        """Test getting customer discounts in non-testing mode"""
        customer_id = "test_customer_123"
        
        # Mock result with discounts
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = AsyncMock()
        mock_execute.return_value = Mock(data=[
            {'id': 1, 'code': 'CART123456', 'discount_percentage': 10.0}
        ])
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.eq.return_value = mock_eq
        mock_eq.execute = mock_execute
        mock_supabase_client.table.return_value = mock_table
        
        result = await non_testing_discount_service.get_customer_discounts(customer_id)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['code'] == 'CART123456'

    @pytest.mark.asyncio
    async def test_get_customer_discounts_exception(self, non_testing_discount_service, mock_supabase_client):
        """Test getting customer discounts exception handling"""
        customer_id = "test_customer_123"
        
        # Mock exception
        mock_supabase_client.table.side_effect = Exception("Database error")
        
        result = await non_testing_discount_service.get_customer_discounts(customer_id)
        
        assert result == []

    # Cleanup expired discounts tests
    @pytest.mark.asyncio
    async def test_cleanup_expired_discounts_testing(self, discount_service):
        """Test cleanup expired discounts in testing mode"""
        result = await discount_service.cleanup_expired_discounts()
        
        assert result == 0

    @pytest.mark.asyncio
    async def test_cleanup_expired_discounts_non_testing_no_expired(self, non_testing_discount_service, mock_supabase_client):
        """Test cleanup expired discounts - no expired discounts"""
        # Mock empty result
        mock_table = Mock()
        mock_select = Mock()
        mock_lt = Mock()
        mock_eq = Mock()
        mock_execute = AsyncMock()
        mock_execute.return_value = Mock(data=[])
        
        mock_table.select.return_value = mock_select
        mock_select.lt.return_value = mock_lt
        mock_lt.eq.return_value = mock_eq
        mock_eq.execute = mock_execute
        mock_supabase_client.table.return_value = mock_table
        
        result = await non_testing_discount_service.cleanup_expired_discounts()
        
        assert result == 0

    @pytest.mark.asyncio
    async def test_cleanup_expired_discounts_non_testing_with_expired(self, non_testing_discount_service, mock_supabase_client):
        """Test cleanup expired discounts - with expired discounts"""
        # Mock select for expired discounts
        mock_select_table = Mock()
        mock_select = Mock()
        mock_lt = Mock()
        mock_eq = Mock()
        mock_select_execute = AsyncMock()
        mock_select_execute.return_value = Mock(data=[
            {'id': 1}, {'id': 2}
        ])
        
        mock_select_table.select.return_value = mock_select
        mock_select.lt.return_value = mock_lt
        mock_lt.eq.return_value = mock_eq
        mock_eq.execute = mock_select_execute
        
        # Mock update for deactivating
        mock_update_table = Mock()
        mock_update = Mock()
        mock_in = Mock()
        mock_update_execute = AsyncMock()
        mock_update_execute.return_value = Mock(data=[{'id': 1}, {'id': 2}])
        
        mock_update_table.update.return_value = mock_update
        mock_update.in_.return_value = mock_in
        mock_in.execute = mock_update_execute
        
        # Mock table method to return appropriate mock based on call
        def table_side_effect(name):
            if mock_supabase_client.table.call_count == 1:
                return mock_select_table
            else:
                return mock_update_table
        
        mock_supabase_client.table.side_effect = table_side_effect
        
        result = await non_testing_discount_service.cleanup_expired_discounts()
        
        assert result == 2

    @pytest.mark.asyncio
    async def test_cleanup_expired_discounts_exception(self, non_testing_discount_service, mock_supabase_client):
        """Test cleanup expired discounts exception handling"""
        # Mock exception
        mock_supabase_client.table.side_effect = Exception("Database error")
        
        result = await non_testing_discount_service.cleanup_expired_discounts()
        
        assert result == 0

    # Private method tests
    def test_generate_discount_code(self, discount_service):
        """Test discount code generation"""
        prefix = "TEST"
        code = discount_service._generate_discount_code(prefix)
        
        assert code.startswith(prefix)
        assert len(code) == len(prefix) + 6
        assert code[len(prefix):].isalnum()

    @pytest.mark.parametrize("cart_value,expected_percentage", [
        (60000.0, 15.0),
        (50000.0, 15.0),
        (30000.0, 10.0),
        (25000.0, 10.0),
        (15000.0, 5.0),
        (10000.0, 5.0),
        (5000.0, 3.0)
    ])
    def test_calculate_discount_percentage(self, discount_service, cart_value, expected_percentage):
        """Test discount percentage calculation"""
        result = discount_service._calculate_discount_percentage(cart_value)
        assert result == expected_percentage

    @pytest.mark.parametrize("loyalty_level,expected_percentage", [
        ("bronze", 5.0),
        ("silver", 10.0),
        ("gold", 15.0),
        ("platinum", 20.0),
        ("PLATINUM", 20.0),  # Case insensitive
        ("unknown", 5.0)  # Default
    ])
    def test_get_loyalty_discount_percentage(self, discount_service, loyalty_level, expected_percentage):
        """Test loyalty discount percentage calculation"""
        result = discount_service._get_loyalty_discount_percentage(loyalty_level)
        assert result == expected_percentage

    def test_check_validity_valid(self, discount_service):
        """Test validity check - valid discount"""
        discount = {
            'valid_from': (datetime.now() - timedelta(days=1)).isoformat(),
            'valid_until': (datetime.now() + timedelta(days=1)).isoformat()
        }
        
        valid, error = discount_service._check_validity(discount)
        
        assert valid is True
        assert error is None

    def test_check_validity_not_yet_valid(self, discount_service):
        """Test validity check - not yet valid"""
        discount = {
            'valid_from': (datetime.now() + timedelta(days=1)).isoformat(),
            'valid_until': (datetime.now() + timedelta(days=2)).isoformat()
        }
        
        valid, error = discount_service._check_validity(discount)
        
        assert valid is False
        assert 'még nem érvényes' in error

    def test_check_validity_expired(self, discount_service):
        """Test validity check - expired"""
        discount = {
            'valid_from': (datetime.now() - timedelta(days=2)).isoformat(),
            'valid_until': (datetime.now() - timedelta(days=1)).isoformat()
        }
        
        valid, error = discount_service._check_validity(discount)
        
        assert valid is False
        assert 'lejárt' in error

    def test_check_usage_limit_valid(self, discount_service):
        """Test usage limit check - valid"""
        discount = {'times_used': 0, 'usage_limit': 1}
        
        valid, error = discount_service._check_usage_limit(discount)
        
        assert valid is True
        assert error is None

    def test_check_usage_limit_exceeded(self, discount_service):
        """Test usage limit check - exceeded"""
        discount = {'times_used': 1, 'usage_limit': 1}
        
        valid, error = discount_service._check_usage_limit(discount)
        
        assert valid is False
        assert 'felhasznált' in error

    def test_check_minimum_order_value_valid(self, discount_service):
        """Test minimum order value check - valid"""
        discount = {'minimum_order_value': 10000}
        order_value = 15000.0
        
        valid, error = discount_service._check_minimum_order_value(discount, order_value)
        
        assert valid is True
        assert error is None

    def test_check_minimum_order_value_below_minimum(self, discount_service):
        """Test minimum order value check - below minimum"""
        discount = {'minimum_order_value': 10000}
        order_value = 5000.0
        
        valid, error = discount_service._check_minimum_order_value(discount, order_value)
        
        assert valid is False
        assert 'Minimum rendelési érték' in error

    def test_check_customer_specific_valid(self, discount_service):
        """Test customer specific check - valid"""
        discount = {'customer_id': 'test_customer_123'}
        customer_id = 'test_customer_123'
        
        valid, error = discount_service._check_customer_specific(discount, customer_id)
        
        assert valid is True
        assert error is None

    def test_check_customer_specific_no_restriction(self, discount_service):
        """Test customer specific check - no restriction"""
        discount = {'customer_id': None}
        customer_id = 'test_customer_123'
        
        valid, error = discount_service._check_customer_specific(discount, customer_id)
        
        assert valid is True
        assert error is None

    def test_check_customer_specific_wrong_customer(self, discount_service):
        """Test customer specific check - wrong customer"""
        discount = {'customer_id': 'other_customer_456'}
        customer_id = 'test_customer_123'
        
        valid, error = discount_service._check_customer_specific(discount, customer_id)
        
        assert valid is False
        assert 'nem ehhez a vásárlóhoz tartozik' in error

    # Statistics tests
    @pytest.mark.asyncio
    async def test_get_discount_statistics_testing(self, discount_service):
        """Test getting discount statistics in testing mode"""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        result = await discount_service.get_discount_statistics(start_date, end_date)
        
        assert result['total_discounts'] == 5
        assert result['total_used'] == 2
        assert result['total_revenue_saved'] == 5000
        assert 'by_type' in result
        assert 'abandoned_cart' in result['by_type']
        assert 'welcome' in result['by_type']

    @pytest.mark.asyncio
    async def test_get_discount_statistics_non_testing_empty(self, non_testing_discount_service, mock_supabase_client):
        """Test getting discount statistics - empty result"""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        # Mock empty result
        mock_table = Mock()
        mock_select = Mock()
        mock_gte = Mock()
        mock_lte = Mock()
        mock_execute = AsyncMock()
        mock_execute.return_value = Mock(data=[])
        
        mock_table.select.return_value = mock_select
        mock_select.gte.return_value = mock_gte
        mock_gte.lte.return_value = mock_lte
        mock_lte.execute = mock_execute
        mock_supabase_client.table.return_value = mock_table
        
        result = await non_testing_discount_service.get_discount_statistics(start_date, end_date)
        
        assert result['total_discounts'] == 0
        assert result['total_used'] == 0
        assert result['total_revenue_saved'] == 0
        assert result['by_type'] == {}

    @pytest.mark.asyncio
    async def test_get_discount_statistics_non_testing_with_data(self, non_testing_discount_service, mock_supabase_client):
        """Test getting discount statistics - with data"""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        # Mock result with data
        mock_table = Mock()
        mock_select = Mock()
        mock_gte = Mock()
        mock_lte = Mock()
        mock_execute = AsyncMock()
        mock_execute.return_value = Mock(data=[
            {
                'created_for': 'abandoned_cart',
                'discount_percentage': 10.0,
                'times_used': 1,
                'active': True
            },
            {
                'created_for': 'welcome',
                'discount_percentage': 10.0,
                'times_used': 0,
                'active': True
            }
        ])
        
        mock_table.select.return_value = mock_select
        mock_select.gte.return_value = mock_gte
        mock_gte.lte.return_value = mock_lte
        mock_lte.execute = mock_execute
        mock_supabase_client.table.return_value = mock_table
        
        result = await non_testing_discount_service.get_discount_statistics(start_date, end_date)
        
        assert result['total_discounts'] == 2
        assert result['total_used'] == 1
        assert 'by_type' in result
        assert 'abandoned_cart' in result['by_type']
        assert 'welcome' in result['by_type']
        assert result['by_type']['abandoned_cart']['count'] == 1
        assert result['by_type']['abandoned_cart']['used'] == 1
        assert result['by_type']['abandoned_cart']['avg_discount_percentage'] == 10.0

    @pytest.mark.asyncio
    async def test_get_discount_statistics_exception(self, non_testing_discount_service, mock_supabase_client):
        """Test getting discount statistics exception handling"""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        # Mock exception
        mock_supabase_client.table.side_effect = Exception("Database error")
        
        result = await non_testing_discount_service.get_discount_statistics(start_date, end_date)
        
        assert result == {}