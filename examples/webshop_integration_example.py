"""
Webshop API Integration Example for Chatbuddy MVP.

This example demonstrates how to use the webshop API integrations
with both mock and real APIs.
"""

import asyncio
import os
from typing import List

from src.integrations.webshop.unified import (
    UnifiedWebshopAPI, WebshopManager, WebshopPlatform,
    create_shoprenter_api, create_unas_api, create_mock_api
)
from src.integrations.webshop.base import Product, Order, OrderStatus


async def example_mock_api_usage():
    """Példa mock API használatára"""
    print("🔧 Mock API használat példa")
    print("=" * 50)
    
    # Mock API létrehozása
    mock_api = create_mock_api()
    
    # Termékek lekérése
    products = await mock_api.get_products(limit=5)
    print(f"📦 {len(products)} termék található:")
    for product in products:
        print(f"  - {product.name}: {product.price:,} HUF")
    
    # Termék keresés
    search_results = await mock_api.search_products("iPhone")
    print(f"\n🔍 Keresési eredmények 'iPhone' kulcsszóra:")
    for product in search_results:
        print(f"  - {product.name}: {product.price:,} HUF")
    
    # Rendelés lekérése
    order = await mock_api.get_order("order_1")
    if order:
        print(f"\n📋 Rendelés: {order.id}")
        print(f"  Státusz: {order.status.value}")
        print(f"  Összeg: {order.total:,} HUF")
        for item in order.items:
            print(f"  - {item.product_name}: {item.quantity} db")
    
    await mock_api.close()


async def example_multiple_webshops():
    """Példa több webshop kezelésére"""
    print("\n🏪 Több webshop kezelése")
    print("=" * 50)
    
    # Webshop manager létrehozása
    manager = WebshopManager()
    
    # Mock webshopok hozzáadása
    manager.add_webshop(
        "shoprenter_mock",
        WebshopPlatform.SHOPRENTER,
        "mock_key",
        "https://mock.shoprenter.hu"
    )
    manager.add_webshop(
        "unas_mock",
        WebshopPlatform.UNAS,
        "mock_key",
        "https://mock.unas.hu"
    )
    
    print(f"📋 Elérhető webshopok: {manager.list_webshops()}")
    
    # Keresés minden webshopban
    search_results = await manager.search_all_products("telefon")
    
    for shop_name, products in search_results.items():
        print(f"\n🏪 {shop_name}:")
        for product in products:
            print(f"  - {product.name}: {product.price:,} HUF")
    
    await manager.close_all()


async def example_real_api_setup():
    """Példa éles API beállításra"""
    print("\n🚀 Éles API beállítás")
    print("=" * 50)
    
    # Környezeti változók ellenőrzése
    shoprenter_api_key = os.getenv("SHOPRENTER_API_KEY")
    shoprenter_base_url = os.getenv("SHOPRENTER_BASE_URL")
    
    unas_api_key = os.getenv("UNAS_API_KEY")
    unas_base_url = os.getenv("UNAS_BASE_URL")
    
    if shoprenter_api_key and shoprenter_base_url:
        print("✅ Shoprenter API konfigurálva")
        shoprenter_api = create_shoprenter_api(
            shoprenter_api_key, 
            shoprenter_base_url,
            use_mock=False
        )
        
        # Éles API használata
        try:
            products = await shoprenter_api.get_products(limit=3)
            print(f"📦 {len(products)} termék az éles Shoprenter webshopból")
        except Exception as e:
            print(f"❌ Hiba az éles API használatakor: {e}")
        
        await shoprenter_api.close()
    else:
        print("⚠️ Shoprenter API nincs konfigurálva")
    
    if unas_api_key and unas_base_url:
        print("✅ UNAS API konfigurálva")
        unas_api = create_unas_api(
            unas_api_key,
            unas_base_url,
            use_mock=False
        )
        
        # Éles API használata
        try:
            products = await unas_api.get_products(limit=3)
            print(f"📦 {len(products)} termék az éles UNAS webshopból")
        except Exception as e:
            print(f"❌ Hiba az éles API használatakor: {e}")
        
        await unas_api.close()
    else:
        print("⚠️ UNAS API nincs konfigurálva")


async def example_order_status_update():
    """Példa rendelési státusz frissítésre"""
    print("\n📋 Rendelési státusz frissítés")
    print("=" * 50)
    
    mock_api = create_mock_api()
    
    # Eredeti státusz lekérése
    order = await mock_api.get_order("order_1")
    if order:
        print(f"Eredeti státusz: {order.status.value}")
        
        # Státusz frissítése
        success = await mock_api.update_order_status("order_1", OrderStatus.DELIVERED)
        if success:
            print("✅ Státusz frissítve: DELIVERED")
            
            # Ellenőrzés
            updated_order = await mock_api.get_order("order_1")
            print(f"Új státusz: {updated_order.status.value}")
        else:
            print("❌ Státusz frissítés sikertelen")
    
    await mock_api.close()


async def main():
    """Fő függvény"""
    print("🚀 Chatbuddy MVP - Webshop API Integration Examples")
    print("=" * 60)
    
    try:
        # Mock API használat
        await example_mock_api_usage()
        
        # Több webshop kezelése
        await example_multiple_webshops()
        
        # Éles API beállítás
        await example_real_api_setup()
        
        # Rendelési státusz frissítés
        await example_order_status_update()
        
        print("\n✅ Minden példa sikeresen lefutott!")
        
    except Exception as e:
        print(f"❌ Hiba: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 