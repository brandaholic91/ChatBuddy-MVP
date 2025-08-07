"""
Tests for SMS service module
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import os
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from integrations.marketing.sms_service import TwilioSMSService


class TestTwilioSMSService:
    """Tests for TwilioSMSService"""
    
    @pytest.fixture
    def mock_template_engine(self):
        """Mock template engine"""
        with patch('integrations.marketing.sms_service.MarketingTemplateEngine') as mock_engine:
            mock_instance = Mock()
            mock_instance.render_sms_template.return_value = "Mock SMS content"
            mock_engine.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def mock_twilio_client(self):
        """Mock Twilio client"""
        with patch('integrations.marketing.sms_service.Client') as mock_client_class:
            mock_client = Mock()
            mock_message = Mock()
            mock_message.sid = "test_sid_12345"
            mock_client.messages.create.return_value = mock_message
            mock_client_class.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def sms_service_with_credentials(self, mock_template_engine, mock_twilio_client):
        """Create SMS service with Twilio credentials"""
        with patch.dict(os.environ, {
            'TWILIO_ACCOUNT_SID': 'test_account_sid',
            'TWILIO_AUTH_TOKEN': 'test_auth_token',
            'TWILIO_PHONE_NUMBER': '+1234567890',
            'TESTING': 'false'
        }):
            service = TwilioSMSService()
            return service
    
    @pytest.fixture
    def sms_service_testing_mode(self, mock_template_engine):
        """Create SMS service in testing mode"""
        with patch.dict(os.environ, {'TESTING': 'true'}, clear=True):
            service = TwilioSMSService()
            return service
    
    @pytest.fixture
    def sms_service_no_credentials(self, mock_template_engine):
        """Create SMS service without credentials (should raise ValueError)"""
        with patch.dict(os.environ, {}, clear=True):
            return TwilioSMSService

    # Initialization tests
    def test_init_with_credentials(self, sms_service_with_credentials):
        """Test SMS service initialization with credentials"""
        assert sms_service_with_credentials.account_sid == 'test_account_sid'
        assert sms_service_with_credentials.auth_token == 'test_auth_token'
        assert sms_service_with_credentials.from_number == '+1234567890'
        assert sms_service_with_credentials.client is not None
        assert sms_service_with_credentials.template_engine is not None

    def test_init_testing_mode(self, sms_service_testing_mode):
        """Test SMS service initialization in testing mode"""
        assert sms_service_testing_mode.client is None
        assert sms_service_testing_mode.template_engine is not None

    def test_init_without_credentials_non_testing(self, mock_template_engine):
        """Test SMS service initialization without credentials (should raise ValueError)"""
        with patch.dict(os.environ, {'TESTING': 'false'}, clear=True):
            with pytest.raises(ValueError, match="Twilio environment variables hiányoznak"):
                TwilioSMSService()

    def test_init_missing_partial_credentials(self, mock_template_engine):
        """Test SMS service initialization with partial credentials"""
        with patch.dict(os.environ, {
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TESTING': 'false'
            # Missing TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER
        }, clear=True):
            with pytest.raises(ValueError, match="Twilio environment variables hiányoznak"):
                TwilioSMSService()

    # Abandoned cart SMS tests
    @pytest.mark.asyncio
    async def test_send_abandoned_cart_sms_success(self, sms_service_with_credentials):
        """Test successful abandoned cart SMS sending"""
        to_phone = "+1234567890"
        template_data = {
            'customer_name': 'John Doe',
            'cart_items': [{'name': 'Test Product', 'price': 1000}],
            'discount_code': 'CART123456'
        }
        
        # Mock successful message
        mock_message = Mock()
        mock_message.sid = "test_sid_12345"
        
        with patch.object(sms_service_with_credentials, '_send_sms_async', return_value=mock_message) as mock_send:
            result = await sms_service_with_credentials.send_abandoned_cart_sms(to_phone, template_data)
            
            assert result is True
            mock_send.assert_called_once()
            sms_service_with_credentials.template_engine.render_sms_template.assert_called_with('abandoned_cart', template_data)

    @pytest.mark.asyncio
    async def test_send_abandoned_cart_sms_failure(self, sms_service_with_credentials):
        """Test failed abandoned cart SMS sending"""
        to_phone = "+1234567890"
        template_data = {'customer_name': 'John Doe'}
        
        # Mock failed message (no sid)
        mock_message = Mock()
        mock_message.sid = None
        
        with patch.object(sms_service_with_credentials, '_send_sms_async', return_value=mock_message):
            result = await sms_service_with_credentials.send_abandoned_cart_sms(to_phone, template_data)
            
            assert result is False

    @pytest.mark.asyncio
    async def test_send_abandoned_cart_sms_no_message(self, sms_service_with_credentials):
        """Test abandoned cart SMS sending with no message returned"""
        to_phone = "+1234567890"
        template_data = {'customer_name': 'John Doe'}
        
        with patch.object(sms_service_with_credentials, '_send_sms_async', return_value=None):
            result = await sms_service_with_credentials.send_abandoned_cart_sms(to_phone, template_data)
            
            assert result is False

    @pytest.mark.asyncio
    async def test_send_abandoned_cart_sms_exception(self, sms_service_with_credentials):
        """Test abandoned cart SMS sending with exception"""
        to_phone = "+1234567890"
        template_data = {'customer_name': 'John Doe'}
        
        with patch.object(sms_service_with_credentials, '_send_sms_async', side_effect=Exception("Network error")):
            result = await sms_service_with_credentials.send_abandoned_cart_sms(to_phone, template_data)
            
            assert result is False

    # Welcome SMS tests
    @pytest.mark.asyncio
    async def test_send_welcome_sms_success(self, sms_service_with_credentials):
        """Test successful welcome SMS sending"""
        to_phone = "+1234567890"
        template_data = {
            'customer_name': 'John Doe',
            'welcome_discount': 'WELCOME10'
        }
        
        # Mock successful message
        mock_message = Mock()
        mock_message.sid = "welcome_sid_12345"
        
        with patch.object(sms_service_with_credentials, '_send_sms_async', return_value=mock_message):
            result = await sms_service_with_credentials.send_welcome_sms(to_phone, template_data)
            
            assert result is True
            sms_service_with_credentials.template_engine.render_sms_template.assert_called_with('welcome', template_data)

    @pytest.mark.asyncio
    async def test_send_welcome_sms_failure(self, sms_service_with_credentials):
        """Test failed welcome SMS sending"""
        to_phone = "+1234567890"
        template_data = {'customer_name': 'John Doe'}
        
        with patch.object(sms_service_with_credentials, '_send_sms_async', return_value=None):
            result = await sms_service_with_credentials.send_welcome_sms(to_phone, template_data)
            
            assert result is False

    @pytest.mark.asyncio
    async def test_send_welcome_sms_exception(self, sms_service_with_credentials):
        """Test welcome SMS sending with exception"""
        to_phone = "+1234567890"
        template_data = {'customer_name': 'John Doe'}
        
        with patch.object(sms_service_with_credentials, '_send_sms_async', side_effect=Exception("Template error")):
            result = await sms_service_with_credentials.send_welcome_sms(to_phone, template_data)
            
            assert result is False

    # Discount reminder SMS tests
    @pytest.mark.asyncio
    async def test_send_discount_reminder_sms_success(self, sms_service_with_credentials):
        """Test successful discount reminder SMS sending"""
        to_phone = "+1234567890"
        template_data = {
            'customer_name': 'John Doe',
            'discount_code': 'DISCOUNT123',
            'valid_until': '2024-12-31'
        }
        
        # Mock successful message
        mock_message = Mock()
        mock_message.sid = "reminder_sid_12345"
        
        with patch.object(sms_service_with_credentials, '_send_sms_async', return_value=mock_message):
            result = await sms_service_with_credentials.send_discount_reminder_sms(to_phone, template_data)
            
            assert result is True
            sms_service_with_credentials.template_engine.render_sms_template.assert_called_with('discount_reminder', template_data)

    @pytest.mark.asyncio
    async def test_send_discount_reminder_sms_failure(self, sms_service_with_credentials):
        """Test failed discount reminder SMS sending"""
        to_phone = "+1234567890"
        template_data = {'discount_code': 'DISCOUNT123'}
        
        with patch.object(sms_service_with_credentials, '_send_sms_async', return_value=None):
            result = await sms_service_with_credentials.send_discount_reminder_sms(to_phone, template_data)
            
            assert result is False

    @pytest.mark.asyncio
    async def test_send_discount_reminder_sms_exception(self, sms_service_with_credentials):
        """Test discount reminder SMS sending with exception"""
        to_phone = "+1234567890"
        template_data = {'discount_code': 'DISCOUNT123'}
        
        with patch.object(sms_service_with_credentials, '_send_sms_async', side_effect=Exception("Twilio API error")):
            result = await sms_service_with_credentials.send_discount_reminder_sms(to_phone, template_data)
            
            assert result is False

    # Bulk SMS tests
    @pytest.mark.asyncio
    async def test_send_bulk_sms_all_success(self, sms_service_with_credentials):
        """Test bulk SMS sending with all successes"""
        recipients = [
            {'phone': '+1234567890', 'data': {'name': 'User 1'}},
            {'phone': '+1234567891', 'data': {'name': 'User 2'}}
        ]
        template_name = 'newsletter'
        
        # Mock successful messages
        mock_message = Mock()
        mock_message.sid = "bulk_sid_12345"
        
        with patch.object(sms_service_with_credentials, '_send_sms_async', return_value=mock_message):
            result = await sms_service_with_credentials.send_bulk_sms(recipients, template_name)
            
            assert result['success_count'] == 2
            assert result['failure_count'] == 0
            assert result['total_count'] == 2
            assert len(result['errors']) == 0

    @pytest.mark.asyncio
    async def test_send_bulk_sms_mixed_results(self, sms_service_with_credentials):
        """Test bulk SMS sending with mixed results"""
        recipients = [
            {'phone': '+1234567890', 'data': {'name': 'User 1'}},
            {'phone': '+1234567891', 'data': {'name': 'User 2'}},
            {'phone': '+1234567892', 'data': {'name': 'User 3'}}
        ]
        template_name = 'newsletter'
        
        # Mock mixed responses (success, failure, success)
        call_count = 0
        def mock_send_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # Second call fails
                return None
            else:
                mock_message = Mock()
                mock_message.sid = f"bulk_sid_{call_count}"
                return mock_message
        
        with patch.object(sms_service_with_credentials, '_send_sms_async', side_effect=mock_send_side_effect):
            result = await sms_service_with_credentials.send_bulk_sms(recipients, template_name)
            
            assert result['success_count'] == 2
            assert result['failure_count'] == 1
            assert result['total_count'] == 3
            assert len(result['errors']) == 1

    @pytest.mark.asyncio
    async def test_send_bulk_sms_with_exceptions(self, sms_service_with_credentials):
        """Test bulk SMS sending with exceptions"""
        recipients = [
            {'phone': '+1234567890', 'data': {'name': 'User 1'}},
            {'phone': '+1234567891', 'data': {'name': 'User 2'}}
        ]
        template_name = 'newsletter'
        
        # Mock one success, one exception
        call_count = 0
        def mock_send_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                mock_message = Mock()
                mock_message.sid = "success_sid"
                return mock_message
            else:
                raise Exception("Network timeout")
        
        with patch.object(sms_service_with_credentials, '_send_sms_async', side_effect=mock_send_side_effect):
            result = await sms_service_with_credentials.send_bulk_sms(recipients, template_name)
            
            assert result['success_count'] == 1
            assert result['failure_count'] == 1
            assert result['total_count'] == 2
            assert len(result['errors']) == 1

    @pytest.mark.asyncio
    async def test_send_bulk_sms_general_exception(self, sms_service_with_credentials):
        """Test bulk SMS sending with general exception"""
        recipients = [
            {'phone': '+1234567890', 'data': {'name': 'User 1'}}
        ]
        template_name = 'newsletter'
        
        # Mock template engine exception
        sms_service_with_credentials.template_engine.render_sms_template.side_effect = Exception("Template not found")
        
        result = await sms_service_with_credentials.send_bulk_sms(recipients, template_name)
        
        assert result['success_count'] == 0
        assert result['failure_count'] == 1
        assert result['total_count'] == 1
        assert len(result['errors']) == 1

    # Send SMS async tests
    @pytest.mark.asyncio
    async def test_send_sms_async_success(self, sms_service_with_credentials, mock_twilio_client):
        """Test successful async SMS sending"""
        to_phone = "+1234567890"
        body = "Test SMS content"
        
        mock_message = Mock()
        mock_message.sid = "async_test_sid"
        mock_twilio_client.messages.create.return_value = mock_message
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_executor = AsyncMock()
            mock_executor.return_value = mock_message
            mock_loop.return_value.run_in_executor = mock_executor
            
            result = await sms_service_with_credentials._send_sms_async(to_phone, body)
            
            assert result == mock_message
            mock_executor.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_sms_async_twilio_exception(self, sms_service_with_credentials, mock_twilio_client):
        """Test async SMS sending with Twilio exception"""
        from twilio.base.exceptions import TwilioException
        
        to_phone = "+1234567890"
        body = "Test SMS content"
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_executor = AsyncMock()
            mock_executor.side_effect = TwilioException("Invalid phone number")
            mock_loop.return_value.run_in_executor = mock_executor
            
            result = await sms_service_with_credentials._send_sms_async(to_phone, body)
            
            assert result is None

    @pytest.mark.asyncio
    async def test_send_sms_async_general_exception(self, sms_service_with_credentials, mock_twilio_client):
        """Test async SMS sending with general exception"""
        to_phone = "+1234567890"
        body = "Test SMS content"
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_executor = AsyncMock()
            mock_executor.side_effect = Exception("Executor error")
            mock_loop.return_value.run_in_executor = mock_executor
            
            result = await sms_service_with_credentials._send_sms_async(to_phone, body)
            
            assert result is None

    # Phone number validation tests
    @pytest.mark.parametrize("phone,expected", [
        ("+1234567890", True),
        ("+36301234567", True),
        ("+4401234567890", True),
        ("+12345", True),  # Minimum length (5 digits)
        ("+123456789012345", True),  # Maximum length (15 digits)
        ("1234567890", True),  # No + sign
        ("+0123456789", False),  # Starts with 0
        ("+123456789012345678", False),  # Too long (18 digits)
        ("+123", False),  # Too short (3 digits)
        ("+1234", False),  # Too short (4 digits)
        ("abc123", False),  # Contains letters
        ("", False),  # Empty
        ("+", False),  # Just + sign
        ("123", False),  # Too short without + (3 digits)
        ("1234", False)  # Too short without + (4 digits)
    ])
    def test_validate_phone_number(self, sms_service_with_credentials, phone, expected):
        """Test phone number validation with various inputs"""
        result = sms_service_with_credentials.validate_phone_number(phone)
        assert result == expected

    # Phone number formatting tests
    @pytest.mark.parametrize("phone,expected", [
        ("06301234567", "+36301234567"),  # Hungarian mobile with 06
        ("6301234567", "+36301234567"),   # Hungarian mobile with 6
        ("36301234567", "+36301234567"),  # Hungarian mobile with 36
        ("+36301234567", "+36301234567"), # Already formatted Hungarian
        ("1234567890", "+1234567890"),    # International without +
        ("+1234567890", "+1234567890"),   # Already formatted international
        ("123-456-7890", "+1234567890"),  # With dashes
        ("123 456 7890", "+1234567890"),  # With spaces
        ("(123) 456-7890", "+1234567890") # With parentheses
    ])
    def test_format_phone_number(self, sms_service_with_credentials, phone, expected):
        """Test phone number formatting"""
        result = sms_service_with_credentials.format_phone_number(phone)
        assert result == expected

    # Delivery stats tests
    def test_get_delivery_stats(self, sms_service_with_credentials):
        """Test getting delivery statistics"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        result = sms_service_with_credentials.get_delivery_stats(start_date, end_date)
        
        assert isinstance(result, dict)
        assert 'sent_count' in result
        assert 'delivered_count' in result
        assert 'failed_count' in result
        assert 'undelivered_count' in result
        
        # All counts should be 0 in the mock implementation
        assert all(count == 0 for count in result.values())

    def test_get_delivery_stats_exception(self, sms_service_with_credentials):
        """Test getting delivery statistics with exception"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        # Force an exception by patching something that will be accessed
        with patch.object(sms_service_with_credentials, 'client', side_effect=Exception("API error")):
            result = sms_service_with_credentials.get_delivery_stats(start_date, end_date)
            
            # Should return the default stats even with the exception
            assert isinstance(result, dict)
            assert 'sent_count' in result

    # Message status tests
    def test_get_message_status_success(self, sms_service_with_credentials, mock_twilio_client):
        """Test getting message status successfully"""
        message_sid = "test_sid_12345"
        
        # Mock message with status
        mock_message = Mock()
        mock_message.status = "delivered"
        
        mock_twilio_client.messages.return_value.fetch.return_value = mock_message
        
        result = sms_service_with_credentials.get_message_status(message_sid)
        
        assert result == "delivered"
        mock_twilio_client.messages.assert_called_with(message_sid)

    def test_get_message_status_twilio_exception(self, sms_service_with_credentials, mock_twilio_client):
        """Test getting message status with Twilio exception"""
        from twilio.base.exceptions import TwilioException
        
        message_sid = "invalid_sid"
        
        mock_twilio_client.messages.return_value.fetch.side_effect = TwilioException("Message not found")
        
        result = sms_service_with_credentials.get_message_status(message_sid)
        
        assert result is None

    def test_get_message_status_general_exception(self, sms_service_with_credentials, mock_twilio_client):
        """Test getting message status with general exception"""
        message_sid = "test_sid_12345"
        
        mock_twilio_client.messages.side_effect = Exception("Client error")
        
        result = sms_service_with_credentials.get_message_status(message_sid)
        
        assert result is None

    # Testing mode tests
    @pytest.mark.asyncio
    async def test_send_sms_testing_mode(self, sms_service_testing_mode):
        """Test SMS sending in testing mode (no client available)"""
        to_phone = "+1234567890"
        template_data = {'customer_name': 'John Doe'}
        
        # Since client is None, this should handle the error gracefully
        result = await sms_service_testing_mode.send_abandoned_cart_sms(to_phone, template_data)
        
        # Should return False due to no Twilio client
        assert result is False

    # Integration tests with template engine
    @pytest.mark.asyncio
    async def test_sms_with_template_engine_integration(self, sms_service_with_credentials):
        """Test SMS sending with template engine integration"""
        to_phone = "+1234567890"
        template_data = {'customer_name': 'John Doe', 'product': 'Test Product'}
        
        # Mock successful message
        mock_message = Mock()
        mock_message.sid = "integration_test_sid"
        
        # Verify template engine is called correctly
        sms_service_with_credentials.template_engine.render_sms_template.return_value = "Rendered SMS content"
        
        with patch.object(sms_service_with_credentials, '_send_sms_async', return_value=mock_message):
            result = await sms_service_with_credentials.send_abandoned_cart_sms(to_phone, template_data)
            
            assert result is True
            sms_service_with_credentials.template_engine.render_sms_template.assert_called_with('abandoned_cart', template_data)