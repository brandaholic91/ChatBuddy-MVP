"""
Webshop API integrations for Chatbuddy MVP.

This module provides unified interfaces for different webshop platforms:
- Shoprenter API integration
- UNAS API integration
- WooCommerce API integration
- Shopify API integration
- Mock APIs for development
- Common product and order models
"""

from .base import BaseWebshopAPI, Product, Order, Customer
from .shoprenter import ShoprenterAPI, MockShoprenterAPI
from .unas import UNASAPI, MockUNASAPI
from .woocommerce import WooCommerceAPI, MockWooCommerceAPI
from .shopify import ShopifyAPI, MockShopifyAPI
from .unified import UnifiedWebshopAPI

__all__ = [
    "BaseWebshopAPI",
    "Product", 
    "Order",
    "Customer",
    "ShoprenterAPI",
    "MockShoprenterAPI", 
    "UNASAPI",
    "MockUNASAPI",
    "WooCommerceAPI",
    "MockWooCommerceAPI",
    "ShopifyAPI",
    "MockShopifyAPI",
    "UnifiedWebshopAPI"
]
