"""
Tests for marketing template engine module
"""
import pytest
import os
import shutil
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from integrations.marketing.template_engine import MarketingTemplateEngine


class TestMarketingTemplateEngine:
    """Tests for MarketingTemplateEngine"""
    
    @pytest.fixture
    def temp_template_dir(self):
        """Create temporary template directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def template_engine_with_temp_dir(self, temp_template_dir):
        """Create template engine with temporary directory"""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            with patch('integrations.marketing.template_engine.FileSystemLoader') as mock_loader:
                with patch('integrations.marketing.template_engine.Environment') as mock_env:
                    mock_environment = Mock()
                    # Create a proper dict for filters that supports item assignment
                    mock_environment.filters = {}
                    mock_env.return_value = mock_environment
                    
                    engine = MarketingTemplateEngine()
                    engine.env = mock_environment
                    return engine
    
    @pytest.fixture
    def template_engine_no_existing_dirs(self):
        """Create template engine when no template directories exist"""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            with patch('os.makedirs') as mock_makedirs:
                with patch.object(MarketingTemplateEngine, '_create_default_templates') as mock_create:
                    with patch('integrations.marketing.template_engine.FileSystemLoader') as mock_loader:
                        with patch('integrations.marketing.template_engine.Environment') as mock_env:
                            mock_environment = Mock()
                            # Create a proper dict for filters that supports item assignment
                            mock_environment.filters = {}
                            mock_env.return_value = mock_environment
                            
                            engine = MarketingTemplateEngine()
                            engine.env = mock_environment
                            return engine

    # Initialization tests
    def test_init_with_existing_dirs(self):
        """Test template engine initialization with existing directories"""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            with patch('integrations.marketing.template_engine.FileSystemLoader') as mock_loader:
                with patch('integrations.marketing.template_engine.Environment') as mock_env:
                    mock_environment = Mock()
                    # Create a proper dict for filters that supports item assignment
                    mock_environment.filters = {}
                    mock_env.return_value = mock_environment
                    
                    engine = MarketingTemplateEngine()
                    
                    assert engine.env == mock_environment
                    mock_loader.assert_called_once()
                    mock_env.assert_called_once()

    def test_init_no_existing_dirs(self):
        """Test template engine initialization without existing directories"""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            with patch('os.makedirs') as mock_makedirs:
                with patch.object(MarketingTemplateEngine, '_create_default_templates') as mock_create:
                    with patch('integrations.marketing.template_engine.FileSystemLoader') as mock_loader:
                        with patch('integrations.marketing.template_engine.Environment') as mock_env:
                            mock_environment = Mock()
                            # Create a proper dict for filters that supports item assignment
                            mock_environment.filters = {}
                            mock_env.return_value = mock_environment
                            
                            engine = MarketingTemplateEngine()
                            
                            mock_makedirs.assert_called_once()
                            mock_create.assert_called_once()

    # Email template rendering tests
    def test_render_email_template_success(self, template_engine_with_temp_dir):
        """Test successful email template rendering"""
        template_name = "abandoned_cart"
        data = {"customer_name": "John Doe", "cart_value": 25000.0}
        
        # Mock template
        mock_template = Mock()
        mock_template.render.return_value = "<html>Rendered email content</html>"
        template_engine_with_temp_dir.env.get_template.return_value = mock_template
        
        # Mock prepare_template_data
        with patch.object(template_engine_with_temp_dir, '_prepare_template_data') as mock_prepare:
            mock_prepare.return_value = data
            
            result = template_engine_with_temp_dir.render_email_template(template_name, data)
            
            assert result == "<html>Rendered email content</html>"
            template_engine_with_temp_dir.env.get_template.assert_called_with("abandoned_cart.html")
            mock_template.render.assert_called_with(**data)

    def test_render_email_template_exception(self, template_engine_with_temp_dir):
        """Test email template rendering with exception"""
        template_name = "nonexistent_template"
        data = {"customer_name": "John Doe"}
        
        # Mock template exception
        template_engine_with_temp_dir.env.get_template.side_effect = Exception("Template not found")
        
        # Mock fallback template
        with patch.object(template_engine_with_temp_dir, '_get_fallback_email_template') as mock_fallback:
            mock_fallback.return_value = "<html>Fallback content</html>"
            
            result = template_engine_with_temp_dir.render_email_template(template_name, data)
            
            assert result == "<html>Fallback content</html>"
            mock_fallback.assert_called_with(template_name, data)

    # Text template rendering tests
    def test_render_text_template_success(self, template_engine_with_temp_dir):
        """Test successful text template rendering"""
        template_name = "welcome"
        data = {"customer_name": "Jane Smith", "welcome_discount": "WELCOME10"}
        
        # Mock template
        mock_template = Mock()
        mock_template.render.return_value = "Welcome text content"
        template_engine_with_temp_dir.env.get_template.return_value = mock_template
        
        # Mock prepare_template_data
        with patch.object(template_engine_with_temp_dir, '_prepare_template_data') as mock_prepare:
            mock_prepare.return_value = data
            
            result = template_engine_with_temp_dir.render_text_template(template_name, data)
            
            assert result == "Welcome text content"
            template_engine_with_temp_dir.env.get_template.assert_called_with("welcome.txt")
            mock_template.render.assert_called_with(**data)

    def test_render_text_template_exception(self, template_engine_with_temp_dir):
        """Test text template rendering with exception"""
        template_name = "invalid_template"
        data = {"customer_name": "Jane Smith"}
        
        # Mock template exception
        template_engine_with_temp_dir.env.get_template.side_effect = Exception("Template error")
        
        # Mock fallback template
        with patch.object(template_engine_with_temp_dir, '_get_fallback_text_template') as mock_fallback:
            mock_fallback.return_value = "Fallback text content"
            
            result = template_engine_with_temp_dir.render_text_template(template_name, data)
            
            assert result == "Fallback text content"
            mock_fallback.assert_called_with(template_name, data)

    # SMS template rendering tests
    def test_render_sms_template_success(self, template_engine_with_temp_dir):
        """Test successful SMS template rendering"""
        template_name = "discount_reminder"
        data = {"customer_name": "Bob Wilson", "discount_code": "SAVE20"}
        
        # Mock template
        mock_template = Mock()
        mock_template.render.return_value = "SMS reminder content"
        template_engine_with_temp_dir.env.get_template.return_value = mock_template
        
        # Mock prepare_template_data
        with patch.object(template_engine_with_temp_dir, '_prepare_template_data') as mock_prepare:
            mock_prepare.return_value = data
            
            result = template_engine_with_temp_dir.render_sms_template(template_name, data)
            
            assert result == "SMS reminder content"
            template_engine_with_temp_dir.env.get_template.assert_called_with("discount_reminder.txt")
            mock_template.render.assert_called_with(**data)

    def test_render_sms_template_exception(self, template_engine_with_temp_dir):
        """Test SMS template rendering with exception"""
        template_name = "broken_template"
        data = {"customer_name": "Bob Wilson"}
        
        # Mock template exception
        template_engine_with_temp_dir.env.get_template.side_effect = Exception("SMS template error")
        
        # Mock fallback template
        with patch.object(template_engine_with_temp_dir, '_get_fallback_sms_template') as mock_fallback:
            mock_fallback.return_value = "Fallback SMS content"
            
            result = template_engine_with_temp_dir.render_sms_template(template_name, data)
            
            assert result == "Fallback SMS content"
            mock_fallback.assert_called_with(template_name, data)

    # Template data preparation tests
    def test_prepare_template_data(self, template_engine_with_temp_dir):
        """Test template data preparation"""
        input_data = {
            'customer_name': 'John Doe',
            'cart_value': 25000.0,
            'discount_code': 'SAVE15'
        }
        
        with patch.object(template_engine_with_temp_dir, '_format_cart_items') as mock_format_items:
            mock_format_items.return_value = []
            with patch.dict(os.environ, {'COMPANY_NAME': 'Test Company'}):
                
                result = template_engine_with_temp_dir._prepare_template_data(input_data)
                
                # Check original data is preserved
                assert result['customer_name'] == 'John Doe'
                assert result['cart_value'] == 25000.0
                assert result['discount_code'] == 'SAVE15'
                
                # Check default values are added
                assert result['company_name'] == 'Test Company'
                assert result['website_url'] == 'https://chatbuddy.com'  # Default value
                assert 'current_date' in result
                assert 'current_time' in result
                assert 'year' in result

    def test_prepare_template_data_with_cart_items(self, template_engine_with_temp_dir):
        """Test template data preparation with cart items"""
        cart_items = [
            {'name': 'Product 1', 'price': 1000.0, 'quantity': 2},
            {'name': 'Product 2', 'price': 1500.0, 'quantity': 1}
        ]
        
        input_data = {
            'customer_name': 'Jane Smith',
            'cart_items': cart_items,
            'cart_value': 3500.0
        }
        
        formatted_cart_items = [
            {'name': 'Product 1', 'price': 1000.0, 'quantity': 2, 'formatted_price': '1,000 Ft'},
            {'name': 'Product 2', 'price': 1500.0, 'quantity': 1, 'formatted_price': '1,500 Ft'}
        ]
        
        with patch.object(template_engine_with_temp_dir, '_format_cart_items') as mock_format_items:
            mock_format_items.return_value = formatted_cart_items
            with patch.object(template_engine_with_temp_dir, '_format_price') as mock_format_price:
                mock_format_price.return_value = '3,500 Ft'
                
                result = template_engine_with_temp_dir._prepare_template_data(input_data)
                
                assert result['cart_items'] == formatted_cart_items
                assert result['formatted_cart_value'] == '3,500 Ft'
                mock_format_items.assert_called_with(cart_items)

    def test_prepare_template_data_with_discount_amount(self, template_engine_with_temp_dir):
        """Test template data preparation with discount amount"""
        input_data = {
            'customer_name': 'Bob Wilson',
            'discount_amount': 2500.0
        }
        
        with patch.object(template_engine_with_temp_dir, '_format_price') as mock_format_price:
            mock_format_price.return_value = '2,500 Ft'
            
            result = template_engine_with_temp_dir._prepare_template_data(input_data)
            
            assert result['formatted_discount_amount'] == '2,500 Ft'

    # Cart items formatting tests
    def test_format_cart_items(self, template_engine_with_temp_dir):
        """Test cart items formatting"""
        cart_items = [
            {'name': 'Product A', 'price': 1200.0, 'quantity': 2, 'total_price': 2400.0},
            {'name': 'Product B', 'price': 850.0, 'quantity': 1}
        ]
        
        with patch.object(template_engine_with_temp_dir, '_format_price') as mock_format_price:
            mock_format_price.side_effect = lambda x: f"{x:,.0f} Ft"
            
            result = template_engine_with_temp_dir._format_cart_items(cart_items)
            
            assert len(result) == 2
            assert result[0]['name'] == 'Product A'
            assert result[0]['formatted_price'] == '1,200 Ft'
            assert result[0]['formatted_total_price'] == '2,400 Ft'
            assert result[1]['name'] == 'Product B'
            assert result[1]['formatted_price'] == '850 Ft'
            assert 'formatted_total_price' not in result[1]  # No total_price in input

    # Price formatting tests
    @pytest.mark.parametrize("price,expected", [
        (1000.0, "1,000 Ft"),
        (1234.56, "1,235 Ft"),  # Rounded
        (0.0, "0 Ft"),
        (999999.99, "1,000,000 Ft")
    ])
    def test_format_price_valid(self, template_engine_with_temp_dir, price, expected):
        """Test price formatting with valid inputs"""
        result = template_engine_with_temp_dir._format_price(price)
        assert result == expected

    @pytest.mark.parametrize("price,expected", [
        ("invalid", "invalid"),
        (None, "None"),
        ("", "")
    ])
    def test_format_price_invalid(self, template_engine_with_temp_dir, price, expected):
        """Test price formatting with invalid inputs"""
        result = template_engine_with_temp_dir._format_price(price)
        assert result == expected

    # Custom filters tests
    def test_add_custom_filters(self, template_engine_with_temp_dir):
        """Test adding custom Jinja2 filters"""
        # Mock the filters dict
        template_engine_with_temp_dir.env.filters = {}
        
        template_engine_with_temp_dir._add_custom_filters()
        
        # Check that filters were added
        assert 'format_price' in template_engine_with_temp_dir.env.filters
        assert 'format_date' in template_engine_with_temp_dir.env.filters
        assert 'format_percentage' in template_engine_with_temp_dir.env.filters

    def test_format_price_filter(self, template_engine_with_temp_dir):
        """Test price formatting filter"""
        template_engine_with_temp_dir.env.filters = {}
        template_engine_with_temp_dir._add_custom_filters()
        
        filter_func = template_engine_with_temp_dir.env.filters['format_price']
        result = filter_func(1500.0)
        
        assert result == "1,500 Ft"

    def test_format_date_filter(self, template_engine_with_temp_dir):
        """Test date formatting filter"""
        template_engine_with_temp_dir.env.filters = {}
        template_engine_with_temp_dir._add_custom_filters()
        
        filter_func = template_engine_with_temp_dir.env.filters['format_date']
        
        # Test with datetime object
        test_date = datetime(2024, 1, 15, 10, 30)
        result = filter_func(test_date, '%Y-%m-%d %H:%M')
        assert result == '2024-01-15 10:30'
        
        # Test with ISO string
        result = filter_func('2024-01-15T10:30:00', '%Y-%m-%d')
        assert result == '2024-01-15'
        
        # Test with invalid string
        result = filter_func('invalid-date', '%Y-%m-%d')
        assert result == 'invalid-date'

    def test_format_percentage_filter(self, template_engine_with_temp_dir):
        """Test percentage formatting filter"""
        template_engine_with_temp_dir.env.filters = {}
        template_engine_with_temp_dir._add_custom_filters()
        
        filter_func = template_engine_with_temp_dir.env.filters['format_percentage']
        
        # Test with valid number
        result = filter_func(15.0)
        assert result == '15.0%'
        
        # Test with string number
        result = filter_func('12.5')
        assert result == '12.5%'
        
        # Test with invalid input
        result = filter_func('invalid')
        assert result == 'invalid'

    # Default template creation tests
    def test_create_default_templates(self, template_engine_with_temp_dir, temp_template_dir):
        """Test creation of default templates"""
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            template_engine_with_temp_dir._create_default_templates(temp_template_dir)
            
            # Should create multiple template files
            assert mock_open.call_count == 6  # 3 email + 3 text templates
            mock_file.write.assert_called()

    # Default template content tests
    def test_get_default_abandoned_cart_email_template(self, template_engine_with_temp_dir):
        """Test default abandoned cart email template"""
        result = template_engine_with_temp_dir._get_default_abandoned_cart_email_template()
        
        assert '<!DOCTYPE html>' in result
        assert 'Ne felejtsd el a kosaradat!' in result
        assert '{{ customer_name or \'Vásárló\' }}' in result
        assert '{{ cart_items|length }}' in result

    def test_get_default_welcome_email_template(self, template_engine_with_temp_dir):
        """Test default welcome email template"""
        result = template_engine_with_temp_dir._get_default_welcome_email_template()
        
        assert '<!DOCTYPE html>' in result
        assert 'Üdvözöljük a ChatBuddy-ban!' in result
        assert '{{ customer_name or \'Vásárló\' }}' in result

    def test_get_default_discount_reminder_email_template(self, template_engine_with_temp_dir):
        """Test default discount reminder email template"""
        result = template_engine_with_temp_dir._get_default_discount_reminder_email_template()
        
        assert '<!DOCTYPE html>' in result
        assert 'Kedvezményed hamarosan lejár!' in result
        assert '{{ discount_code }}' in result

    def test_get_default_abandoned_cart_text_template(self, template_engine_with_temp_dir):
        """Test default abandoned cart text template"""
        result = template_engine_with_temp_dir._get_default_abandoned_cart_text_template()
        
        assert result.startswith('Kedves {{ customer_name or \'Vásárló\' }}!')
        assert '{{ cart_items|length }}' in result
        assert '{{ website_url }}/cart' in result

    def test_get_default_welcome_text_template(self, template_engine_with_temp_dir):
        """Test default welcome text template"""
        result = template_engine_with_temp_dir._get_default_welcome_text_template()
        
        assert result.startswith('Kedves {{ customer_name or \'Vásárló\' }}!')
        assert 'ChatBuddy közösségéhez' in result
        assert '{{ welcome_discount }}' in result

    def test_get_default_discount_reminder_text_template(self, template_engine_with_temp_dir):
        """Test default discount reminder text template"""
        result = template_engine_with_temp_dir._get_default_discount_reminder_text_template()
        
        assert result.startswith('Kedves {{ customer_name or \'Vásárló\' }}!')
        assert '{{ discount_code }}' in result
        assert '{{ hours_left }}' in result

    # Fallback template tests
    def test_get_fallback_email_template(self, template_engine_with_temp_dir):
        """Test fallback email template"""
        template_name = "test_template"
        data = {
            'company_name': 'Test Company',
            'customer_name': 'John Doe',
            'website_url': 'https://test.com'
        }
        
        result = template_engine_with_temp_dir._get_fallback_email_template(template_name, data)
        
        assert '<html>' in result
        assert 'Test Company' in result
        assert 'John Doe' in result
        assert 'https://test.com' in result

    def test_get_fallback_text_template(self, template_engine_with_temp_dir):
        """Test fallback text template"""
        template_name = "test_template"
        data = {
            'company_name': 'Test Company',
            'customer_name': 'Jane Smith',
            'website_url': 'https://test.com'
        }
        
        result = template_engine_with_temp_dir._get_fallback_text_template(template_name, data)
        
        assert result.startswith('Kedves Jane Smith!')
        assert 'Test Company' in result
        assert 'https://test.com' in result

    def test_get_fallback_sms_template(self, template_engine_with_temp_dir):
        """Test fallback SMS template"""
        template_name = "test_template"
        data = {
            'company_name': 'Test Company',
            'customer_name': 'Bob Wilson',
            'website_url': 'https://test.com'
        }
        
        result = template_engine_with_temp_dir._get_fallback_sms_template(template_name, data)
        
        assert result.startswith('Kedves Bob Wilson!')
        assert 'Test Company' in result
        assert 'https://test.com' in result

    # Environment variable handling tests
    def test_template_data_with_env_vars(self, template_engine_with_temp_dir):
        """Test template data preparation with environment variables"""
        input_data = {'customer_name': 'Test User'}
        
        with patch.dict(os.environ, {
            'COMPANY_NAME': 'Custom Company',
            'WEBSITE_URL': 'https://custom.com',
            'SUPPORT_EMAIL': 'help@custom.com',
            'SUPPORT_PHONE': '+1-555-0123'
        }):
            result = template_engine_with_temp_dir._prepare_template_data(input_data)
            
            assert result['company_name'] == 'Custom Company'
            assert result['website_url'] == 'https://custom.com'
            assert result['support_email'] == 'help@custom.com'
            assert result['support_phone'] == '+1-555-0123'

    def test_template_data_default_values(self, template_engine_with_temp_dir):
        """Test template data preparation with default values"""
        input_data = {'customer_name': 'Test User'}
        
        with patch.dict(os.environ, {}, clear=True):
            result = template_engine_with_temp_dir._prepare_template_data(input_data)
            
            assert result['company_name'] == 'ChatBuddy'
            assert result['website_url'] == 'https://chatbuddy.com'
            assert result['support_email'] == 'support@chatbuddy.com'
            assert result['support_phone'] == '+36 1 234 5678'