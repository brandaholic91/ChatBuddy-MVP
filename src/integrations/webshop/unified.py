"""
Unified webshop API interface for Chatbuddy MVP.

This module provides a unified interface for multiple webshop platforms,
allowing the chatbot to work with different e-commerce systems seamlessly.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import logging
from enum import Enum

from .base import BaseWebshopAPI, Product, Order, Customer, OrderStatus, ProductCategory, OrderItem
from .shoprenter import ShoprenterAPI, MockShoprenterAPI
from .unas import UNASAPI, MockUNASAPI
from .woocommerce import WooCommerceAPI, MockWooCommerceAPI
from .shopify import ShopifyAPI, MockShopifyAPI

logger = logging.getLogger(__name__)


class WebshopPlatform(str, Enum):
    """Webshop platform típusok"""
    SHOPRENTER = "shoprenter"
    UNAS = "unas"
    WOOCOMMERCE = "woocommerce"
    SHOPIFY = "shopify"
    MOCK = "mock"


class UnifiedWebshopAPI:
    """Egységes webshop API interfész több platformhoz"""
    
    def __init__(self, platform: WebshopPlatform, api_key: str, base_url: str):
        self.platform = platform
        self.api_key = api_key
        self.base_url = base_url
        self.api_client = self._create_api_client()
    
    def _create_api_client(self) -> BaseWebshopAPI:
        """API kliens létrehozása a platform alapján"""
        if self.platform == WebshopPlatform.SHOPRENTER:
            if self.api_key == "mock_key":
                return MockShoprenterAPI()
            else:
                return ShoprenterAPI(self.api_key, self.base_url)
        elif self.platform == WebshopPlatform.UNAS:
            if self.api_key == "mock_key":
                return MockUNASAPI()
            else:
                return UNASAPI(self.api_key, self.base_url)
        elif self.platform == WebshopPlatform.WOOCOMMERCE:
            if self.api_key == "mock_key":
                return MockWooCommerceAPI()
            else:
                return WooCommerceAPI(self.api_key, self.base_url)
        elif self.platform == WebshopPlatform.SHOPIFY:
            if self.api_key == "mock_key":
                return MockShopifyAPI()
            else:
                return ShopifyAPI(self.api_key, self.base_url)
        elif self.platform == WebshopPlatform.MOCK:
            # Default mock Shoprenter API
            return MockShoprenterAPI()
        else:
            raise ValueError(f"Unsupported platform: {self.platform}")
    
    async def get_products(self, limit: int = 50, offset: int = 0, 
                          category: Optional[str] = None) -> List[Product]:
        """Termékek lekérése egységes interfészen keresztül"""
        try:
            return await self.api_client.get_products(limit, offset, category)
        except Exception as e:
            logger.error(f"Unified API hiba - get_products: {e}")
            return []
    
    async def get_product(self, product_id: str) -> Optional[Product]:
        """Egy termék lekérése egységes interfészen keresztül"""
        try:
            return await self.api_client.get_product(product_id)
        except Exception as e:
            logger.error(f"Unified API hiba - get_product: {e}")
            return None
    
    async def search_products(self, query: str, limit: int = 20) -> List[Product]:
        """Termék keresés egységes interfészen keresztül"""
        try:
            return await self.api_client.search_products(query, limit)
        except Exception as e:
            logger.error(f"Unified API hiba - search_products: {e}")
            return []
    
    async def get_orders(self, limit: int = 50, offset: int = 0) -> List[Order]:
        """Rendelések lekérése egységes interfészen keresztül"""
        try:
            return await self.api_client.get_orders(limit, offset)
        except Exception as e:
            logger.error(f"Unified API hiba - get_orders: {e}")
            return []
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Egy rendelés lekérése egységes interfészen keresztül"""
        try:
            return await self.api_client.get_order(order_id)
        except Exception as e:
            logger.error(f"Unified API hiba - get_order: {e}")
            return None
    
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Ügyfél adatok lekérése egységes interfészen keresztül"""
        try:
            return await self.api_client.get_customer(customer_id)
        except Exception as e:
            logger.error(f"Unified API hiba - get_customer: {e}")
            return None
    
    async def update_order_status(self, order_id: str, status: str) -> bool:
        """Rendelési státusz frissítése egységes interfészen keresztül"""
        try:
            return await self.api_client.update_order_status(order_id, status)
        except Exception as e:
            logger.error(f"Unified API hiba - update_order_status: {e}")
            return False
    
    async def close(self):
        """API kliens lezárása"""
        if hasattr(self.api_client, 'close'):
            await self.api_client.close()
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Platform információk lekérése"""
        return {
            "platform": self.platform.value,
            "base_url": self.base_url,
            "api_key_configured": self.api_key != "mock_key"
        }


class WebshopManager:
    """Több webshop kezelése egyszerre"""
    
    def __init__(self):
        self.webshops: Dict[str, UnifiedWebshopAPI] = {}
    
    def add_webshop(self, name: str, platform: WebshopPlatform, 
                    api_key: str, base_url: str) -> None:
        """Webshop hozzáadása a kezelőhöz"""
        self.webshops[name] = UnifiedWebshopAPI(platform, api_key, base_url)
        logger.info(f"Webshop hozzáadva: {name} ({platform.value})")
    
    def get_webshop(self, name: str) -> Optional[UnifiedWebshopAPI]:
        """Webshop lekérése név alapján"""
        return self.webshops.get(name)
    
    def list_webshops(self) -> List[str]:
        """Elérhető webshopok listája"""
        return list(self.webshops.keys())
    
    async def search_all_products(self, query: str, limit: int = 20) -> Dict[str, List[Product]]:
        """Termék keresés minden webshopban"""
        results = {}
        
        for name, webshop in self.webshops.items():
            try:
                products = await webshop.search_products(query, limit)
                results[name] = products
            except Exception as e:
                logger.error(f"Hiba a {name} webshop keresésében: {e}")
                results[name] = []
        
        return results
    
    async def get_product_from_all(self, product_id: str) -> Dict[str, Optional[Product]]:
        """Termék lekérése minden webshopból"""
        results = {}
        
        for name, webshop in self.webshops.items():
            try:
                product = await webshop.get_product(product_id)
                results[name] = product
            except Exception as e:
                logger.error(f"Hiba a {name} webshop termék lekérésében: {e}")
                results[name] = None
        
        return results
    
    async def close_all(self):
        """Minden webshop kapcsolat lezárása"""
        for webshop in self.webshops.values():
            await webshop.close()


# Factory függvények a könnyebb használathoz
def create_shoprenter_api(api_key: str, base_url: str, use_mock: bool = False) -> UnifiedWebshopAPI:
    """Shoprenter API létrehozása"""
    if use_mock:
        return UnifiedWebshopAPI(WebshopPlatform.MOCK, "mock_key", base_url)
    else:
        return UnifiedWebshopAPI(WebshopPlatform.SHOPRENTER, api_key, base_url)


def create_unas_api(api_key: str, base_url: str, use_mock: bool = False) -> UnifiedWebshopAPI:
    """UNAS API létrehozása"""
    if use_mock:
        return UnifiedWebshopAPI(WebshopPlatform.MOCK, "mock_key", base_url)
    else:
        return UnifiedWebshopAPI(WebshopPlatform.UNAS, api_key, base_url)


def create_woocommerce_api(api_key: str, base_url: str, use_mock: bool = False) -> UnifiedWebshopAPI:
    """WooCommerce API létrehozása"""
    if use_mock:
        return UnifiedWebshopAPI(WebshopPlatform.WOOCOMMERCE, "mock_key", base_url)
    else:
        return UnifiedWebshopAPI(WebshopPlatform.WOOCOMMERCE, api_key, base_url)


def create_shopify_api(api_key: str, base_url: str, use_mock: bool = False) -> UnifiedWebshopAPI:
    """Shopify API létrehozása"""
    if use_mock:
        return UnifiedWebshopAPI(WebshopPlatform.SHOPIFY, "mock_key", base_url)
    else:
        return UnifiedWebshopAPI(WebshopPlatform.SHOPIFY, api_key, base_url)


def create_mock_api() -> UnifiedWebshopAPI:
    """Mock API létrehozása fejlesztéshez"""
    return UnifiedWebshopAPI(WebshopPlatform.MOCK, "mock_key", "https://mock.webshop.com") 