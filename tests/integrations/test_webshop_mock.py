# tests/integrations/test_webshop_mock.py

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.integrations.webshop.unified import UnifiedWebshopAPI, WebshopPlatform
from tests.mocks import MockWebShopAPI

@pytest.mark.unit
@pytest.mark.integrations
@pytest.mark.fast
class TestUnifiedWebshopAPIMock:
    """UnifiedWebshopAPI mock tesztek."""
    
    @pytest.fixture(autouse=True)
    def mock_internal_api_client(self):
        """Mockolja a UnifiedWebshopAPI belső API kliensét."""
        mock_instance = MockWebShopAPI()

        with patch('src.integrations.webshop.unified.ShoprenterAPI') as mock_shoprenter:
            mock_shoprenter.return_value = mock_instance
        with patch('src.integrations.webshop.unified.UNASAPI') as mock_unas:
            mock_unas.return_value = mock_instance
        with patch('src.integrations.webshop.unified.WooCommerceAPI') as mock_woocommerce:
            mock_woocommerce.return_value = mock_instance
        with patch('src.integrations.webshop.unified.ShopifyAPI') as mock_shopify:
            mock_shopify.return_value = mock_instance
        with patch('src.integrations.webshop.unified.MockShoprenterAPI') as mock_mock_shoprenter:
            mock_mock_shoprenter.return_value = mock_instance
        with patch('src.integrations.webshop.unified.MockUNASAPI') as mock_mock_unas:
            mock_mock_unas.return_value = mock_instance
        with patch('src.integrations.webshop.unified.MockWooCommerceAPI') as mock_mock_woocommerce:
            mock_mock_woocommerce.return_value = mock_instance
        with patch('src.integrations.webshop.unified.MockShopifyAPI') as mock_mock_shopify:
            mock_mock_shopify.return_value = mock_instance
            
        yield mock_instance

    async def test_get_products(self, mock_internal_api_client):
        """Termékek lekérdezésének tesztje."""
        api = UnifiedWebshopAPI(WebshopPlatform.SHOPRENTER, "mock_key", "http://test.url")
        products = await api.get_products()
        
        assert len(products) == 1
        assert products[0].name == "Test Product"
        mock_internal_api_client.get_products.assert_awaited_once()

    async def test_get_orders(self, mock_internal_api_client):
        """Rendelések lekérdezésének tesztje."""
        api = UnifiedWebshopAPI(WebshopPlatform.UNAS, "mock_key", "http://test.url")
        orders = await api.get_orders()
        
        assert len(orders) == 1
        assert orders[0].status == "completed"
        mock_internal_api_client.get_orders.assert_awaited_once()

    async def test_search_products(self, mock_internal_api_client):
        """Termék keresésének tesztje."""
        mock_internal_api_client.search_products.return_value = [
            MagicMock(name="Searched Product", price=100.0)
        ]
        api = UnifiedWebshopAPI(WebshopPlatform.WOOCOMMERCE, "mock_key", "http://test.url")
        products = await api.search_products("test query")
        
        assert len(products) == 1
        assert products[0].name == "Searched Product"
        mock_internal_api_client.search_products.assert_awaited_once_with("test query", 20)

    async def test_get_product(self, mock_internal_api_client):
        """Egy termék lekérdezésének tesztje."""
        mock_internal_api_client.get_product.return_value = MagicMock(name="Single Product", price=50.0)
        api = UnifiedWebshopAPI(WebshopPlatform.SHOPIFY, "mock_key", "http://test.url")
        product = await api.get_product("prod123")
        
        assert product.name == "Single Product"
        mock_internal_api_client.get_product.assert_awaited_once_with("prod123")

    async def test_update_order_status(self, mock_internal_api_client):
        """Rendelési státusz frissítésének tesztje."""
        mock_internal_api_client.update_order_status.return_value = True
        api = UnifiedWebshopAPI(WebshopPlatform.MOCK, "mock_key", "http://test.url")
        success = await api.update_order_status("order123", "shipped")
        
        assert success is True
        mock_internal_api_client.update_order_status.assert_awaited_once_with("order123", "shipped")

    async def test_platform_info(self):
        """Platform információk lekérdezésének tesztje."""
        api = UnifiedWebshopAPI(WebshopPlatform.SHOPRENTER, "real_key", "http://real.url")
        info = api.get_platform_info()
        
        assert info["platform"] == "shoprenter"
        assert info["base_url"] == "http://real.url"
        assert info["api_key_configured"] is True

        api_mock = UnifiedWebshopAPI(WebshopPlatform.MOCK, "mock_key", "http://test.url")
        info_mock = api_mock.get_platform_info()
        assert info_mock["api_key_configured"] is False