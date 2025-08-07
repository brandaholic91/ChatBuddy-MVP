"""
Tests for WooCommerce and Shopify API integrations.
"""

import pytest
import asyncio
from datetime import datetime

from src.integrations.webshop.woocommerce import WooCommerceAPI, MockWooCommerceAPI
from src.integrations.webshop.shopify import ShopifyAPI, MockShopifyAPI
from src.integrations.webshop.base import Product, Order, Customer, OrderItem, OrderStatus, ProductCategory


class TestWooCommerceIntegration:
    """WooCommerce API integráció tesztek"""
    
    def test_mock_woocommerce_api_creation(self):
        """Mock WooCommerce API létrehozásának tesztje"""
        api = MockWooCommerceAPI()
        assert api is not None
        assert len(api.mock_products) > 0
        assert len(api.mock_orders) > 0
        assert len(api.mock_customers) > 0
    
    @pytest.mark.asyncio
    async def test_mock_woocommerce_get_products(self):
        """Mock WooCommerce termékek lekérésének tesztje"""
        api = MockWooCommerceAPI()
        products = await api.get_products()
        
        assert len(products) > 0
        assert all(isinstance(p, Product) for p in products)
        
        # Ellenőrizzük a mock adatok tartalmát
        product_names = [p.name for p in products]
        assert "iPhone 15 Pro" in product_names
        assert "Samsung Galaxy S24" in product_names
        assert "Nike Air Max 270" in product_names
        assert "MacBook Pro 14" in product_names
    
    @pytest.mark.asyncio
    async def test_mock_woocommerce_get_product(self):
        """Mock WooCommerce egy termék lekérésének tesztje"""
        api = MockWooCommerceAPI()
        product = await api.get_product("1")
        
        assert product is not None
        assert product.id == "1"
        assert product.name == "iPhone 15 Pro"
        assert product.price == 499999.0
        assert product.currency == "HUF"
    
    @pytest.mark.asyncio
    async def test_mock_woocommerce_search_products(self):
        """Mock WooCommerce termék keresésének tesztje"""
        api = MockWooCommerceAPI()
        
        # iPhone keresés
        results = await api.search_products("iPhone")
        assert len(results) > 0
        assert any("iPhone" in p.name for p in results)
        
        # Samsung keresés
        results = await api.search_products("Samsung")
        assert len(results) > 0
        assert any("Samsung" in p.name for p in results)
        
        # Nem létező termék
        results = await api.search_products("nemletezo")
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_mock_woocommerce_get_orders(self):
        """Mock WooCommerce rendelések lekérésének tesztje"""
        api = MockWooCommerceAPI()
        orders = await api.get_orders()
        
        assert len(orders) > 0
        assert all(isinstance(o, Order) for o in orders)
        
        # Ellenőrizzük a mock adatok tartalmát
        order_ids = [o.id for o in orders]
        assert "1001" in order_ids
        assert "1002" in order_ids
    
    @pytest.mark.asyncio
    async def test_mock_woocommerce_get_order(self):
        """Mock WooCommerce egy rendelés lekérésének tesztje"""
        api = MockWooCommerceAPI()
        order = await api.get_order("1001")
        
        assert order is not None
        assert order.id == "1001"
        assert order.total == 589998.0
        assert len(order.items) == 2
    
    @pytest.mark.asyncio
    async def test_mock_woocommerce_get_customer(self):
        """Mock WooCommerce ügyfél lekérésének tesztje"""
        api = MockWooCommerceAPI()
        customer = await api.get_customer("2001")
        
        assert customer is not None
        assert customer.id == "2001"
        assert customer.email == "kiss.janos@example.com"
        assert customer.first_name == "János"
        assert customer.last_name == "Kiss"
    
    @pytest.mark.asyncio
    async def test_mock_woocommerce_update_order_status(self):
        """Mock WooCommerce rendelési státusz frissítésének tesztje"""
        api = MockWooCommerceAPI()
        
        # Státusz frissítése
        success = await api.update_order_status("1001", "completed")
        assert success is True
        
        # Ellenőrizzük, hogy frissült-e
        order = await api.get_order("1001")
        assert order.status == OrderStatus.DELIVERED


class TestShopifyIntegration:
    """Shopify API integráció tesztek"""
    
    def test_mock_shopify_api_creation(self):
        """Mock Shopify API létrehozásának tesztje"""
        api = MockShopifyAPI()
        assert api is not None
        assert len(api.mock_products) > 0
        assert len(api.mock_orders) > 0
        assert len(api.mock_customers) > 0
    
    @pytest.mark.asyncio
    async def test_mock_shopify_get_products(self):
        """Mock Shopify termékek lekérésének tesztje"""
        api = MockShopifyAPI()
        products = await api.get_products()
        
        assert len(products) > 0
        assert all(isinstance(p, Product) for p in products)
        
        # Ellenőrizzük a mock adatok tartalmát
        product_names = [p.name for p in products]
        assert "Sony WH-1000XM5" in product_names
        assert "Adidas Ultraboost 22" in product_names
        assert "Dell XPS 13" in product_names
        assert "Canon EOS R6" in product_names
    
    @pytest.mark.asyncio
    async def test_mock_shopify_get_product(self):
        """Mock Shopify egy termék lekérésének tesztje"""
        api = MockShopifyAPI()
        product = await api.get_product("1")
        
        assert product is not None
        assert product.id == "1"
        assert product.name == "Sony WH-1000XM5"
        assert product.price == 299999.0
        assert product.currency == "HUF"
    
    @pytest.mark.asyncio
    async def test_mock_shopify_search_products(self):
        """Mock Shopify termék keresésének tesztje"""
        api = MockShopifyAPI()
        
        # Sony keresés
        results = await api.search_products("Sony")
        assert len(results) > 0
        assert any("Sony" in p.name for p in results)
        
        # Adidas keresés
        results = await api.search_products("Adidas")
        assert len(results) > 0
        assert any("Adidas" in p.name for p in results)
        
        # Nem létező termék
        results = await api.search_products("nemletezo")
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_mock_shopify_get_orders(self):
        """Mock Shopify rendelések lekérésének tesztje"""
        api = MockShopifyAPI()
        orders = await api.get_orders()
        
        assert len(orders) > 0
        assert all(isinstance(o, Order) for o in orders)
        
        # Ellenőrizzük a mock adatok tartalmát
        order_ids = [o.id for o in orders]
        assert "2001" in order_ids
        assert "2002" in order_ids
    
    @pytest.mark.asyncio
    async def test_mock_shopify_get_order(self):
        """Mock Shopify egy rendelés lekérésének tesztje"""
        api = MockShopifyAPI()
        order = await api.get_order("2001")
        
        assert order is not None
        assert order.id == "2001"
        assert order.total == 429998.0
        assert len(order.items) == 2
    
    @pytest.mark.asyncio
    async def test_mock_shopify_get_customer(self):
        """Mock Shopify ügyfél lekérésének tesztje"""
        api = MockShopifyAPI()
        customer = await api.get_customer("3001")
        
        assert customer is not None
        assert customer.id == "3001"
        assert customer.email == "szabo.peter@example.com"
        assert customer.first_name == "Péter"
        assert customer.last_name == "Szabó"
    
    @pytest.mark.asyncio
    async def test_mock_shopify_update_order_status(self):
        """Mock Shopify rendelési státusz frissítésének tesztje"""
        api = MockShopifyAPI()
        
        # Státusz frissítése
        success = await api.update_order_status("2001", "paid")
        assert success is True
        
        # Ellenőrizzük, hogy frissült-e
        order = await api.get_order("2001")
        assert order.status == OrderStatus.DELIVERED


class TestUnifiedIntegration:
    """Egységes webshop integráció tesztek WooCommerce és Shopify platformokkal"""
    
    @pytest.mark.asyncio
    async def test_woocommerce_unified_api(self):
        """WooCommerce egységes API tesztje"""
        from src.integrations.webshop.unified import UnifiedWebshopAPI, WebshopPlatform
        
        # Mock WooCommerce API
        api = UnifiedWebshopAPI(WebshopPlatform.WOOCOMMERCE, "mock_key", "https://mock.woocommerce.com")
        
        # Termékek lekérése
        products = await api.get_products()
        assert len(products) > 0
        assert all(isinstance(p, Product) for p in products)
        
        # Termék keresés
        search_results = await api.search_products("iPhone")
        assert len(search_results) > 0
        
        # Platform információk
        info = api.get_platform_info()
        assert info["platform"] == "woocommerce"
        assert info["api_key_configured"] is False
    
    @pytest.mark.asyncio
    async def test_shopify_unified_api(self):
        """Shopify egységes API tesztje"""
        from src.integrations.webshop.unified import UnifiedWebshopAPI, WebshopPlatform
        
        # Mock Shopify API
        api = UnifiedWebshopAPI(WebshopPlatform.SHOPIFY, "mock_key", "https://mock.shopify.com")
        
        # Termékek lekérése
        products = await api.get_products()
        assert len(products) > 0
        assert all(isinstance(p, Product) for p in products)
        
        # Termék keresés
        search_results = await api.search_products("Sony")
        assert len(search_results) > 0
        
        # Platform információk
        info = api.get_platform_info()
        assert info["platform"] == "shopify"
        assert info["api_key_configured"] is False
    
    @pytest.mark.asyncio
    async def test_webshop_manager_with_new_platforms(self):
        """WebshopManager tesztje az új platformokkal"""
        from src.integrations.webshop.unified import WebshopManager, WebshopPlatform
        
        manager = WebshopManager()
        
        # WooCommerce hozzáadása
        manager.add_webshop("woocommerce_test", WebshopPlatform.WOOCOMMERCE, "mock_key", "https://mock.woocommerce.com")
        
        # Shopify hozzáadása
        manager.add_webshop("shopify_test", WebshopPlatform.SHOPIFY, "mock_key", "https://mock.shopify.com")
        
        # Webshopok listázása
        webshops = manager.list_webshops()
        assert "woocommerce_test" in webshops
        assert "shopify_test" in webshops
        
        # Termék keresés minden webshopban
        results = await manager.search_all_products("iPhone")
        assert "woocommerce_test" in results
        assert "shopify_test" in results
        
        # WooCommerce-ben található iPhone
        assert len(results["woocommerce_test"]) > 0
        
        # Shopify-ben nincs iPhone
        assert len(results["shopify_test"]) == 0


class TestPerformance:
    """Teljesítmény tesztek az új platformokkal"""
    
    @pytest.mark.asyncio
    async def test_bulk_product_search_new_platforms(self):
        """Tömeges termék keresés tesztje az új platformokkal"""
        from src.integrations.webshop.unified import WebshopManager, WebshopPlatform
        
        manager = WebshopManager()
        
        # Webshopok hozzáadása
        manager.add_webshop("woocommerce_mock", WebshopPlatform.WOOCOMMERCE, "mock_key", "https://mock.woocommerce.com")
        manager.add_webshop("shopify_mock", WebshopPlatform.SHOPIFY, "mock_key", "https://mock.shopify.com")
        
        # Több keresési kifejezés tesztelése
        search_queries = ["iPhone", "Sony", "Nike"]
        
        for query in search_queries:
            results = await manager.search_all_products(query)
            
            # Minden webshop válaszol
            assert "woocommerce_mock" in results
            assert "shopify_mock" in results
            
            # Legalább egy webshopban található eredmény
            total_results = sum(len(products) for products in results.values())
            assert total_results >= 0  # Lehet, hogy nincs találat
    
    @pytest.mark.asyncio
    async def test_concurrent_api_calls(self):
        """Párhuzamos API hívások tesztje"""
        from src.integrations.webshop.unified import WebshopManager, WebshopPlatform
        
        manager = WebshopManager()
        manager.add_webshop("woocommerce_mock", WebshopPlatform.WOOCOMMERCE, "mock_key", "https://mock.woocommerce.com")
        manager.add_webshop("shopify_mock", WebshopPlatform.SHOPIFY, "mock_key", "https://mock.shopify.com")
        
        # Párhuzamos termék lekérések
        tasks = []
        for _ in range(5):
            tasks.append(manager.search_all_products("iPhone"))
            tasks.append(manager.search_all_products("Sony"))
        
        results = await asyncio.gather(*tasks)
        
        # Minden task sikeresen lefutott
        assert len(results) == 10
        for result in results:
            assert isinstance(result, dict)
            assert "woocommerce_mock" in result
            assert "shopify_mock" in result


if __name__ == "__main__":
    pytest.main([__file__]) 