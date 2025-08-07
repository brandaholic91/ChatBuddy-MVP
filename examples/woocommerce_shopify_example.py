"""
WooCommerce és Shopify API integráció példa használat.

Ez a példa bemutatja, hogyan lehet használni az új WooCommerce és Shopify
integrációkat a Chatbuddy MVP rendszerben.
"""

import asyncio
import os
import sys
from typing import Dict, List

# Hozzáadjuk a projekt gyökérkönyvtárát a Python path-hoz
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Webshop integrációk importálása
from src.integrations.webshop.woocommerce import WooCommerceAPI, MockWooCommerceAPI
from src.integrations.webshop.shopify import ShopifyAPI, MockShopifyAPI
from src.integrations.webshop.unified import (
    UnifiedWebshopAPI, 
    WebshopManager, 
    WebshopPlatform,
    create_woocommerce_api,
    create_shopify_api
)
from src.integrations.webshop.base import Product, Order, Customer


async def example_woocommerce_mock_usage():
    """WooCommerce mock API használat példa"""
    print("=== WooCommerce Mock API Példa ===")
    
    # Mock WooCommerce API létrehozása
    api = MockWooCommerceAPI()
    
    # Termékek lekérése
    products = await api.get_products()
    print(f"WooCommerce termékek száma: {len(products)}")
    
    # Első termék részletei
    if products:
        first_product = products[0]
        print(f"Első termék: {first_product.name} - {first_product.price} {first_product.currency}")
    
    # Termék keresés
    search_results = await api.search_products("iPhone")
    print(f"iPhone keresési eredmények: {len(search_results)}")
    
    # Rendelések lekérése
    orders = await api.get_orders()
    print(f"WooCommerce rendelések száma: {len(orders)}")
    
    # Ügyfél adatok
    if orders:
        user_id = orders[0].user_id
        customer = await api.get_customer(user_id)
        if customer:
            print(f"Ügyfél: {customer.first_name} {customer.last_name} ({customer.email})")


async def example_shopify_mock_usage():
    """Shopify mock API használat példa"""
    print("\n=== Shopify Mock API Példa ===")
    
    # Mock Shopify API létrehozása
    api = MockShopifyAPI()
    
    # Termékek lekérése
    products = await api.get_products()
    print(f"Shopify termékek száma: {len(products)}")
    
    # Első termék részletei
    if products:
        first_product = products[0]
        print(f"Első termék: {first_product.name} - {first_product.price} {first_product.currency}")
    
    # Termék keresés
    search_results = await api.search_products("Sony")
    print(f"Sony keresési eredmények: {len(search_results)}")
    
    # Rendelések lekérése
    orders = await api.get_orders()
    print(f"Shopify rendelések száma: {len(orders)}")
    
    # Ügyfél adatok
    if orders:
        user_id = orders[0].user_id
        customer = await api.get_customer(user_id)
        if customer:
            print(f"Ügyfél: {customer.first_name} {customer.last_name} ({customer.email})")


async def example_unified_api_usage():
    """Egységes API használat példa"""
    print("\n=== Egységes API Példa ===")
    
    # WooCommerce egységes API
    woocommerce_api = create_woocommerce_api("mock_key", "https://mock.woocommerce.com", use_mock=True)
    
    # Shopify egységes API
    shopify_api = create_shopify_api("mock_key", "https://mock.shopify.com", use_mock=True)
    
    # Termékek lekérése mindkét platformról
    wc_products = await woocommerce_api.get_products()
    sf_products = await shopify_api.get_products()
    
    print(f"WooCommerce termékek: {len(wc_products)}")
    print(f"Shopify termékek: {len(sf_products)}")
    
    # Platform információk
    wc_info = woocommerce_api.get_platform_info()
    sf_info = shopify_api.get_platform_info()
    
    print(f"WooCommerce platform: {wc_info['platform']}")
    print(f"Shopify platform: {sf_info['platform']}")


async def example_webshop_manager_usage():
    """WebshopManager használat példa"""
    print("\n=== WebshopManager Példa ===")
    
    # WebshopManager létrehozása
    manager = WebshopManager()
    
    # Webshopok hozzáadása
    manager.add_webshop(
        "woocommerce_store", 
        WebshopPlatform.WOOCOMMERCE, 
        "mock_key", 
        "https://mock.woocommerce.com"
    )
    
    manager.add_webshop(
        "shopify_store", 
        WebshopPlatform.SHOPIFY, 
        "mock_key", 
        "https://mock.shopify.com"
    )
    
    # Webshopok listázása
    webshops = manager.list_webshops()
    print(f"Elérhető webshopok: {webshops}")
    
    # Termék keresés minden webshopban
    search_results = await manager.search_all_products("iPhone")
    
    print("Keresési eredmények:")
    for webshop_name, products in search_results.items():
        print(f"  {webshop_name}: {len(products)} termék")
        for product in products[:2]:  # Csak az első 2 terméket mutatjuk
            print(f"    - {product.name} ({product.price} {product.currency})")


async def example_real_api_setup():
    """Valós API beállítás példa"""
    print("\n=== Valós API Beállítás Példa ===")
    
    # WooCommerce valós API (ha vannak környezeti változók)
    wc_api_key = os.getenv("WOOCOMMERCE_API_KEY")
    wc_base_url = os.getenv("WOOCOMMERCE_BASE_URL")
    
    if wc_api_key and wc_base_url:
        print("WooCommerce valós API konfigurálva")
        woocommerce_api = create_woocommerce_api(wc_api_key, wc_base_url, use_mock=False)
        print("WooCommerce API létrehozva")
    else:
        print("WooCommerce környezeti változók nincsenek beállítva")
    
    # Shopify valós API (ha vannak környezeti változók)
    sf_api_key = os.getenv("SHOPIFY_API_KEY")
    sf_base_url = os.getenv("SHOPIFY_BASE_URL")
    
    if sf_api_key and sf_base_url:
        print("Shopify valós API konfigurálva")
        shopify_api = create_shopify_api(sf_api_key, sf_base_url, use_mock=False)
        print("Shopify API létrehozva")
    else:
        print("Shopify környezeti változók nincsenek beállítva")


async def example_order_status_update():
    """Rendelési státusz frissítés példa"""
    print("\n=== Rendelési Státusz Frissítés Példa ===")
    
    # WooCommerce mock API
    wc_api = MockWooCommerceAPI()
    
    # Rendelés státuszának frissítése
    order_id = "1001"
    success = await wc_api.update_order_status(order_id, "completed")
    
    if success:
        # Ellenőrizzük a frissítést
        order = await wc_api.get_order(order_id)
        print(f"WooCommerce rendelés {order_id} státusza: {order.status.name}")
    
    # Shopify mock API
    sf_api = MockShopifyAPI()
    
    # Rendelés státuszának frissítése
    order_id = "2001"
    success = await sf_api.update_order_status(order_id, "paid")
    
    if success:
        # Ellenőrizzük a frissítést
        order = await sf_api.get_order(order_id)
        print(f"Shopify rendelés {order_id} státusza: {order.status.name}")


async def main():
    """Fő függvény az összes példa futtatásához"""
    print("WooCommerce és Shopify API Integráció Példák")
    print("=" * 50)
    
    try:
        # Mock API használat példák
        await example_woocommerce_mock_usage()
        await example_shopify_mock_usage()
        
        # Egységes API példák
        await example_unified_api_usage()
        
        # WebshopManager példák
        await example_webshop_manager_usage()
        
        # Valós API beállítás példák
        await example_real_api_setup()
        
        # Rendelési státusz frissítés példák
        await example_order_status_update()
        
        print("\n" + "=" * 50)
        print("Minden példa sikeresen lefutott!")
        
    except Exception as e:
        print(f"Hiba történt: {e}")
        raise


if __name__ == "__main__":
    # Aszinkron fő függvény futtatása
    asyncio.run(main()) 