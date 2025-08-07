"""
Tests for email service module
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import os
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from integrations.marketing.email_service import SendGridEmailService


class TestSendGridEmailService:
    """Tests for SendGridEmailService"""
    
    @pytest.fixture
    def mock_template_engine(self):
        """Mock template engine"""
        with patch('integrations.marketing.email_service.MarketingTemplateEngine') as mock_engine:
            mock_instance = Mock()
            mock_instance.render_email_template.return_value = "<html>Mock HTML content</html>"
            mock_instance.render_text_template.return_value = "Mock text content"
            mock_engine.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def mock_sendgrid(self):
        """Mock SendGrid client"""
        with patch('integrations.marketing.email_service.sendgrid.SendGridAPIClient') as mock_sg:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.status_code = 202
            mock_client.send.return_value = mock_response
            mock_sg.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def email_service_with_api_key(self, mock_template_engine, mock_sendgrid):
        """Create email service with API key"""
        with patch.dict(os.environ, {
            'SENDGRID_API_KEY': 'test_api_key',
            'EMAIL_FROM_ADDRESS': 'test@example.com',
            'EMAIL_FROM_NAME': 'Test Sender'
        }):
            service = SendGridEmailService()
            return service
    
    @pytest.fixture
    def email_service_without_api_key(self, mock_template_engine):
        """Create email service without API key"""
        with patch.dict(os.environ, {}, clear=True):
            service = SendGridEmailService()
            return service

    # Initialization tests
    def test_init_with_api_key(self, email_service_with_api_key):
        """Test email service initialization with API key"""
        assert email_service_with_api_key.api_key == 'test_api_key'
        assert email_service_with_api_key.from_email == 'test@example.com'
        assert email_service_with_api_key.from_name == 'Test Sender'
        assert email_service_with_api_key.sg is not None
        assert email_service_with_api_key.template_engine is not None

    def test_init_without_api_key(self, email_service_without_api_key):
        """Test email service initialization without API key"""
        assert email_service_without_api_key.api_key is None
        assert email_service_without_api_key.sg is None
        assert email_service_without_api_key.from_email == 'no-reply@chatbuddy.com'
        assert email_service_without_api_key.from_name == 'ChatBuddy'
        assert email_service_without_api_key.template_engine is not None

    # Abandoned cart email tests
    @pytest.mark.asyncio
    async def test_send_abandoned_cart_email_success(self, email_service_with_api_key, mock_sendgrid):
        """Test successful abandoned cart email sending"""
        to_email = "test@example.com"
        template_data = {
            'customer_name': 'John Doe',
            'cart_items': [{'name': 'Test Product', 'price': 1000}],
            'discount_code': 'CART123456'
        }
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 202
        
        with patch.object(email_service_with_api_key, '_send_email_async', return_value=mock_response) as mock_send:
            result = await email_service_with_api_key.send_abandoned_cart_email(to_email, template_data)
            
            assert result is True
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_abandoned_cart_email_failure(self, email_service_with_api_key):
        """Test failed abandoned cart email sending"""
        to_email = "test@example.com"
        template_data = {'customer_name': 'John Doe'}
        
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 400
        
        with patch.object(email_service_with_api_key, '_send_email_async', return_value=mock_response):
            result = await email_service_with_api_key.send_abandoned_cart_email(to_email, template_data)
            
            assert result is False

    @pytest.mark.asyncio
    async def test_send_abandoned_cart_email_no_response(self, email_service_with_api_key):
        """Test abandoned cart email sending with no response"""
        to_email = "test@example.com"
        template_data = {'customer_name': 'John Doe'}
        
        with patch.object(email_service_with_api_key, '_send_email_async', return_value=None):
            result = await email_service_with_api_key.send_abandoned_cart_email(to_email, template_data)
            
            assert result is False

    @pytest.mark.asyncio
    async def test_send_abandoned_cart_email_exception(self, email_service_with_api_key):
        """Test abandoned cart email sending with exception"""
        to_email = "test@example.com"
        template_data = {'customer_name': 'John Doe'}
        
        with patch.object(email_service_with_api_key, '_send_email_async', side_effect=Exception("Network error")):
            result = await email_service_with_api_key.send_abandoned_cart_email(to_email, template_data)
            
            assert result is False

    # Welcome email tests
    @pytest.mark.asyncio
    async def test_send_welcome_email_success(self, email_service_with_api_key):
        """Test successful welcome email sending"""
        to_email = "test@example.com"
        template_data = {
            'customer_name': 'John Doe',
            'welcome_discount': 'WELCOME10'
        }
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 202
        
        with patch.object(email_service_with_api_key, '_send_email_async', return_value=mock_response):
            result = await email_service_with_api_key.send_welcome_email(to_email, template_data)
            
            assert result is True

    @pytest.mark.asyncio
    async def test_send_welcome_email_failure(self, email_service_with_api_key):
        """Test failed welcome email sending"""
        to_email = "test@example.com"
        template_data = {'customer_name': 'John Doe'}
        
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 400
        
        with patch.object(email_service_with_api_key, '_send_email_async', return_value=mock_response):
            result = await email_service_with_api_key.send_welcome_email(to_email, template_data)
            
            assert result is False

    @pytest.mark.asyncio
    async def test_send_welcome_email_exception(self, email_service_with_api_key):
        """Test welcome email sending with exception"""
        to_email = "test@example.com"
        template_data = {'customer_name': 'John Doe'}
        
        with patch.object(email_service_with_api_key, '_send_email_async', side_effect=Exception("Template error")):
            result = await email_service_with_api_key.send_welcome_email(to_email, template_data)
            
            assert result is False

    # Discount reminder email tests
    @pytest.mark.asyncio
    async def test_send_discount_reminder_email_success(self, email_service_with_api_key):
        """Test successful discount reminder email sending"""
        to_email = "test@example.com"
        template_data = {
            'customer_name': 'John Doe',
            'discount_code': 'DISCOUNT123',
            'valid_until': '2024-12-31'
        }
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 202
        
        with patch.object(email_service_with_api_key, '_send_email_async', return_value=mock_response):
            result = await email_service_with_api_key.send_discount_reminder_email(to_email, template_data)
            
            assert result is True

    @pytest.mark.asyncio
    async def test_send_discount_reminder_email_failure(self, email_service_with_api_key):
        """Test failed discount reminder email sending"""
        to_email = "test@example.com"
        template_data = {'discount_code': 'DISCOUNT123'}
        
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch.object(email_service_with_api_key, '_send_email_async', return_value=mock_response):
            result = await email_service_with_api_key.send_discount_reminder_email(to_email, template_data)
            
            assert result is False

    @pytest.mark.asyncio
    async def test_send_discount_reminder_email_exception(self, email_service_with_api_key):
        """Test discount reminder email sending with exception"""
        to_email = "test@example.com"
        template_data = {'discount_code': 'DISCOUNT123'}
        
        with patch.object(email_service_with_api_key, '_send_email_async', side_effect=Exception("SendGrid API error")):
            result = await email_service_with_api_key.send_discount_reminder_email(to_email, template_data)
            
            assert result is False

    # Bulk email tests
    @pytest.mark.asyncio
    async def test_send_bulk_email_all_success(self, email_service_with_api_key):
        """Test bulk email sending with all successes"""
        recipients = [
            {'email': 'test1@example.com', 'data': {'name': 'User 1'}},
            {'email': 'test2@example.com', 'data': {'name': 'User 2'}}
        ]
        template_name = 'newsletter'
        subject = 'Test Newsletter'
        
        # Mock successful responses
        mock_response = Mock()
        mock_response.status_code = 202
        
        with patch.object(email_service_with_api_key, '_send_email_async', return_value=mock_response):
            result = await email_service_with_api_key.send_bulk_email(recipients, template_name, subject)
            
            assert result['success_count'] == 2
            assert result['failure_count'] == 0
            assert result['total_count'] == 2
            assert len(result['errors']) == 0

    @pytest.mark.asyncio
    async def test_send_bulk_email_mixed_results(self, email_service_with_api_key):
        """Test bulk email sending with mixed results"""
        recipients = [
            {'email': 'test1@example.com', 'data': {'name': 'User 1'}},
            {'email': 'test2@example.com', 'data': {'name': 'User 2'}},
            {'email': 'test3@example.com', 'data': {'name': 'User 3'}}
        ]
        template_name = 'newsletter'
        subject = 'Test Newsletter'
        
        # Mock mixed responses (success, failure, success)
        responses = [
            Mock(status_code=202),  # Success
            Mock(status_code=400),  # Failure
            Mock(status_code=202)   # Success
        ]
        
        call_count = 0
        def mock_send_side_effect(*args, **kwargs):
            nonlocal call_count
            response = responses[call_count]
            call_count += 1
            return response
        
        with patch.object(email_service_with_api_key, '_send_email_async', side_effect=mock_send_side_effect):
            result = await email_service_with_api_key.send_bulk_email(recipients, template_name, subject)
            
            assert result['success_count'] == 2
            assert result['failure_count'] == 1
            assert result['total_count'] == 3
            assert len(result['errors']) == 1

    @pytest.mark.asyncio
    async def test_send_bulk_email_with_exceptions(self, email_service_with_api_key):
        """Test bulk email sending with exceptions"""
        recipients = [
            {'email': 'test1@example.com', 'data': {'name': 'User 1'}},
            {'email': 'test2@example.com', 'data': {'name': 'User 2'}}
        ]
        template_name = 'newsletter'
        subject = 'Test Newsletter'
        
        # Mock one success, one exception
        call_count = 0
        def mock_send_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return Mock(status_code=202)
            else:
                raise Exception("Network timeout")
        
        with patch.object(email_service_with_api_key, '_send_email_async', side_effect=mock_send_side_effect):
            result = await email_service_with_api_key.send_bulk_email(recipients, template_name, subject)
            
            assert result['success_count'] == 1
            assert result['failure_count'] == 1
            assert result['total_count'] == 2
            assert len(result['errors']) == 1

    @pytest.mark.asyncio
    async def test_send_bulk_email_general_exception(self, email_service_with_api_key):
        """Test bulk email sending with general exception"""
        recipients = [
            {'email': 'test1@example.com', 'data': {'name': 'User 1'}}
        ]
        template_name = 'newsletter'
        subject = 'Test Newsletter'
        
        # Mock template engine exception
        email_service_with_api_key.template_engine.render_email_template.side_effect = Exception("Template not found")
        
        result = await email_service_with_api_key.send_bulk_email(recipients, template_name, subject)
        
        assert result['success_count'] == 0
        assert result['failure_count'] == 1
        assert result['total_count'] == 1
        assert len(result['errors']) == 1

    # Send email async tests
    @pytest.mark.asyncio
    async def test_send_email_async_success(self, email_service_with_api_key, mock_sendgrid):
        """Test successful async email sending"""
        from sendgrid.helpers.mail import Mail, From, To, Subject, HtmlContent
        
        message = Mail(
            from_email=From("test@example.com", "Test"),
            to_emails=To("recipient@example.com"),
            subject=Subject("Test"),
            html_content=HtmlContent("<html>Test</html>")
        )
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 202
        mock_sendgrid.send.return_value = mock_response
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_executor = AsyncMock()
            mock_executor.return_value = mock_response
            mock_loop.return_value.run_in_executor = mock_executor
            
            result = await email_service_with_api_key._send_email_async(message)
            
            assert result == mock_response
            mock_executor.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_async_exception(self, email_service_with_api_key, mock_sendgrid):
        """Test async email sending with exception"""
        from sendgrid.helpers.mail import Mail, From, To, Subject, HtmlContent
        
        message = Mail(
            from_email=From("test@example.com", "Test"),
            to_emails=To("recipient@example.com"),
            subject=Subject("Test"),
            html_content=HtmlContent("<html>Test</html>")
        )
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_executor = AsyncMock()
            mock_executor.side_effect = Exception("Executor error")
            mock_loop.return_value.run_in_executor = mock_executor
            
            result = await email_service_with_api_key._send_email_async(message)
            
            assert result is None

    # Email validation tests
    @pytest.mark.parametrize("email,expected", [
        ("test@example.com", True),
        ("user.name@domain.co.uk", True),
        ("user+tag@example.org", True),
        ("user123@test-domain.com", True),
        ("invalid-email", False),
        ("@example.com", False),
        ("test@", False),
        ("test.example.com", False),
        ("test@.com", False),
        ("test@example.", False),
        ("", False),
        ("test@exam ple.com", False)
    ])
    def test_validate_email(self, email_service_with_api_key, email, expected):
        """Test email validation with various inputs"""
        result = email_service_with_api_key.validate_email(email)
        assert result == expected

    # Delivery stats tests
    def test_get_delivery_stats(self, email_service_with_api_key):
        """Test getting delivery statistics"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        result = email_service_with_api_key.get_delivery_stats(start_date, end_date)
        
        assert isinstance(result, dict)
        assert 'sent_count' in result
        assert 'delivered_count' in result
        assert 'bounced_count' in result
        assert 'opened_count' in result
        assert 'clicked_count' in result
        assert 'unsubscribed_count' in result
        
        # All counts should be 0 in the mock implementation
        assert all(count == 0 for count in result.values())

    def test_get_delivery_stats_exception(self, email_service_with_api_key):
        """Test getting delivery statistics with exception"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        # Force an exception by patching something that will be accessed
        with patch.object(email_service_with_api_key, 'sg', side_effect=Exception("API error")):
            result = email_service_with_api_key.get_delivery_stats(start_date, end_date)
            
            # Should return the default stats even with the exception
            assert isinstance(result, dict)
            assert 'sent_count' in result

    # Integration tests with template engine
    @pytest.mark.asyncio
    async def test_email_with_template_engine_integration(self, email_service_with_api_key):
        """Test email sending with template engine integration"""
        to_email = "test@example.com"
        template_data = {'customer_name': 'John Doe', 'product': 'Test Product'}
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 202
        
        # Verify template engine is called correctly
        email_service_with_api_key.template_engine.render_email_template.return_value = "<html>Rendered HTML</html>"
        email_service_with_api_key.template_engine.render_text_template.return_value = "Rendered text"
        
        with patch.object(email_service_with_api_key, '_send_email_async', return_value=mock_response):
            result = await email_service_with_api_key.send_abandoned_cart_email(to_email, template_data)
            
            assert result is True
            email_service_with_api_key.template_engine.render_email_template.assert_called_with('abandoned_cart', template_data)
            email_service_with_api_key.template_engine.render_text_template.assert_called_with('abandoned_cart', template_data)

    # Test with no SendGrid client (no API key scenario)
    @pytest.mark.asyncio
    async def test_send_email_without_client(self, email_service_without_api_key):
        """Test email sending when SendGrid client is not available"""
        to_email = "test@example.com"
        template_data = {'customer_name': 'John Doe'}
        
        # Since sg is None, this should handle the error gracefully
        result = await email_service_without_api_key.send_abandoned_cart_email(to_email, template_data)
        
        # Should return False due to no SendGrid client
        assert result is False