"""
Unit tests for integration components.
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.integrations.database.supabase_client import SupabaseClient
from src.integrations.database.vector_operations import VectorOperations
from src.integrations.database.rls_policies import RLSPolicies
from src.integrations.marketing import MarketingIntegration
from src.integrations.social_media import SocialMediaIntegration
from src.integrations.webshop import WebshopIntegration


class TestSupabaseClient:
    """Unit tests for SupabaseClient."""
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_supabase_client_initialization(self, mock_supabase_client):
        """Test SupabaseClient initialization."""
        client = SupabaseClient(client=mock_supabase_client)
        assert client is not None
        assert client.client == mock_supabase_client
    
    @pytest.mark.unit
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_supabase_client_query(self, mock_supabase_client):
        """Test SupabaseClient query execution."""
        client = SupabaseClient(client=mock_supabase_client)
        result = await client.query("test_table", {"id": "test"})
        assert result is not None
    
    @pytest.mark.unit
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_supabase_client_insert(self, mock_supabase_client, sample_user_data):
        """Test SupabaseClient insert operation."""
        client = SupabaseClient(client=mock_supabase_client)
        result = await client.insert("users", sample_user_data)
        assert result is not None


class TestVectorOperations:
    """Unit tests for VectorOperations."""
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_vector_operations_initialization(self, mock_supabase_client):
        """Test VectorOperations initialization."""
        vector_ops = VectorOperations(client=mock_supabase_client)
        assert vector_ops is not None
        assert vector_ops.client == mock_supabase_client
    
    @pytest.mark.unit
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_vector_operations_create_embedding(self, mock_supabase_client):
        """Test VectorOperations embedding creation."""
        vector_ops = VectorOperations(client=mock_supabase_client)
        embedding = await vector_ops.create_embedding("test text")
        assert embedding is not None
        assert isinstance(embedding, list)
    
    @pytest.mark.unit
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_vector_operations_search(self, mock_supabase_client):
        """Test VectorOperations similarity search."""
        vector_ops = VectorOperations(client=mock_supabase_client)
        results = await vector_ops.search("test_table", [0.1, 0.2, 0.3], limit=5)
        assert results is not None
        assert isinstance(results, list)


class TestRLSPolicies:
    """Unit tests for RLSPolicies."""
    
    @pytest.mark.unit
    @pytest.mark.database
    @pytest.mark.security
    def test_rls_policies_initialization(self, mock_supabase_client):
        """Test RLSPolicies initialization."""
        rls = RLSPolicies(client=mock_supabase_client)
        assert rls is not None
        assert rls.client == mock_supabase_client
    
    @pytest.mark.unit
    @pytest.mark.database
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_rls_policies_create_policy(self, mock_supabase_client):
        """Test RLSPolicies policy creation."""
        rls = RLSPolicies(client=mock_supabase_client)
        result = await rls.create_policy("test_table", "test_policy", "SELECT")
        assert result is not None
    
    @pytest.mark.unit
    @pytest.mark.database
    @pytest.mark.security
    def test_rls_policies_validate_policy(self, mock_supabase_client):
        """Test RLSPolicies policy validation."""
        rls = RLSPolicies(client=mock_supabase_client)
        is_valid = rls.validate_policy("SELECT * FROM users WHERE user_id = auth.uid()")
        assert is_valid is True


class TestMarketingIntegration:
    """Unit tests for MarketingIntegration."""
    
    @pytest.mark.unit
    @pytest.mark.marketing
    def test_marketing_integration_initialization(self, mock_sendgrid_client, mock_twilio_client):
        """Test MarketingIntegration initialization."""
        marketing = MarketingIntegration(
            email_client=mock_sendgrid_client,
            sms_client=mock_twilio_client
        )
        assert marketing is not None
        assert marketing.email_client == mock_sendgrid_client
        assert marketing.sms_client == mock_twilio_client
    
    @pytest.mark.unit
    @pytest.mark.marketing
    @pytest.mark.asyncio
    async def test_marketing_integration_send_email(self, mock_sendgrid_client, mock_twilio_client):
        """Test MarketingIntegration email sending."""
        marketing = MarketingIntegration(
            email_client=mock_sendgrid_client,
            sms_client=mock_twilio_client
        )
        result = await marketing.send_email("test@example.com", "Test Subject", "Test Content")
        assert result is not None
    
    @pytest.mark.unit
    @pytest.mark.marketing
    @pytest.mark.asyncio
    async def test_marketing_integration_send_sms(self, mock_sendgrid_client, mock_twilio_client):
        """Test MarketingIntegration SMS sending."""
        marketing = MarketingIntegration(
            email_client=mock_sendgrid_client,
            sms_client=mock_twilio_client
        )
        result = await marketing.send_sms("+1234567890", "Test SMS")
        assert result is not None


class TestSocialMediaIntegration:
    """Unit tests for SocialMediaIntegration."""
    
    @pytest.mark.unit
    @pytest.mark.marketing
    def test_social_media_integration_initialization(self):
        """Test SocialMediaIntegration initialization."""
        social = SocialMediaIntegration()
        assert social is not None
    
    @pytest.mark.unit
    @pytest.mark.marketing
    @pytest.mark.asyncio
    async def test_social_media_integration_post_message(self):
        """Test SocialMediaIntegration message posting."""
        social = SocialMediaIntegration()
        result = await social.post_message("Test message", "facebook")
        assert result is not None
    
    @pytest.mark.unit
    @pytest.mark.marketing
    def test_social_media_integration_get_platforms(self):
        """Test SocialMediaIntegration platform listing."""
        social = SocialMediaIntegration()
        platforms = social.get_platforms()
        assert isinstance(platforms, list)
        assert len(platforms) > 0


class TestWebshopIntegration:
    """Unit tests for WebshopIntegration."""
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_webshop_integration_initialization(self, mock_webshop_client):
        """Test WebshopIntegration initialization."""
        webshop = WebshopIntegration(client=mock_webshop_client)
        assert webshop is not None
        assert webshop.client == mock_webshop_client
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_webshop_integration_search_products(self, mock_webshop_client):
        """Test WebshopIntegration product search."""
        webshop = WebshopIntegration(client=mock_webshop_client)
        results = await webshop.search_products("laptop")
        assert results is not None
        assert isinstance(results, list)
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_webshop_integration_get_product(self, mock_webshop_client):
        """Test WebshopIntegration product retrieval."""
        webshop = WebshopIntegration(client=mock_webshop_client)
        product = await webshop.get_product("prod_123")
        assert product is not None
        assert "id" in product
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_webshop_integration_get_order(self, mock_webshop_client):
        """Test WebshopIntegration order retrieval."""
        webshop = WebshopIntegration(client=mock_webshop_client)
        order = await webshop.get_order("order_123")
        assert order is not None
        assert "id" in order 