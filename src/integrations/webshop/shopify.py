"""
Shopify API integration for Chatbuddy MVP.

This module provides both real and mock implementations for Shopify API.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
from pydantic import BaseModel

from .base import BaseWebshopAPI, Product, Order, Customer, OrderItem, OrderStatus, ProductCategory


class ShopifyAPI(BaseWebshopAPI):
    """Real Shopify API implementation."""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(
            headers={
                "X-Shopify-Access-Token": api_key,
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def get_products(self, limit: int = 50, offset: int = 0, category: Optional[str] = None) -> List[Product]:
        """Get products from Shopify."""
        try:
            params = {"limit": limit, "offset": offset}
            if category:
                params["collection_id"] = category
            response = await self.client.get(
                f"{self.base_url}/admin/api/2023-10/products.json",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            products = []
            for item in data.get("products", []):
                # Shopify product variants
                variants = item.get("variants", [])
                if variants:
                    variant = variants[0]  # Első variáns
                    product = Product(
                        id=str(item["id"]),
                        name=item["title"],
                        description=item.get("body_html", ""),
                        price=float(variant.get("price", 0)),
                        currency="HUF",
                        category=ProductCategory.ELECTRONICS,  # Default kategória
                        stock=int(variant.get("inventory_quantity", 0)),
                        images=[img.get("src", "") for img in item.get("images", [])],
                        tags=[str(option) for option in item.get("options", [])],
                        is_active=item.get("status") == "active"
                    )
                    products.append(product)
            
            return products
        except Exception as e:
            raise Exception(f"Shopify API hiba: {str(e)}")
    
    async def get_product(self, product_id: str) -> Optional[Product]:
        """Get a specific product by ID."""
        try:
            response = await self.client.get(
                f"{self.base_url}/admin/api/2023-10/products/{product_id}.json"
            )
            response.raise_for_status()
            data = response.json()
            item = data.get("product", {})
            
            variants = item.get("variants", [])
            if not variants:
                return None
                
            variant = variants[0]
            return Product(
                id=str(item["id"]),
                name=item["title"],
                description=item.get("body_html", ""),
                price=float(variant.get("price", 0)),
                currency="HUF",
                category=ProductCategory.ELECTRONICS,  # Default kategória
                stock=int(variant.get("inventory_quantity", 0)),
                images=[img.get("src", "") for img in item.get("images", [])],
                tags=[str(option) for option in item.get("options", [])],
                is_active=item.get("status") == "active"
            )
        except Exception as e:
            raise Exception(f"Shopify API hiba: {str(e)}")
    
    async def search_products(self, query: str, limit: int = 20) -> List[Product]:
        """Search products by query."""
        try:
            response = await self.client.get(
                f"{self.base_url}/admin/api/2023-10/products.json",
                params={"limit": limit, "query": query}
            )
            response.raise_for_status()
            data = response.json()
            
            products = []
            for item in data.get("products", []):
                variants = item.get("variants", [])
                if variants:
                    variant = variants[0]
                    product = Product(
                        id=str(item["id"]),
                        name=item["title"],
                        description=item.get("body_html", ""),
                        price=float(variant.get("price", 0)),
                        currency="HUF",
                        category=ProductCategory.ELECTRONICS,  # Default kategória
                        stock=int(variant.get("inventory_quantity", 0)),
                        images=[img.get("src", "") for img in item.get("images", [])],
                        tags=[str(option) for option in item.get("options", [])],
                        is_active=item.get("status") == "active"
                    )
                    products.append(product)
            
            return products
        except Exception as e:
            raise Exception(f"Shopify API hiba: {str(e)}")
    
    async def get_orders(self, limit: int = 50, offset: int = 0) -> List[Order]:
        """Get orders from Shopify."""
        try:
            response = await self.client.get(
                f"{self.base_url}/admin/api/2023-10/orders.json",
                params={"limit": limit, "offset": offset}
            )
            response.raise_for_status()
            data = response.json()
            
            orders = []
            for item in data.get("orders", []):
                order_items = []
                for line_item in item.get("line_items", []):
                    order_item = OrderItem(
                        product_id=str(line_item["product_id"]),
                        product_name=line_item["title"],
                        quantity=line_item["quantity"],
                        unit_price=float(line_item["price"]),
                        total_price=float(line_item["price"]) * line_item["quantity"]
                    )
                    order_items.append(order_item)
                
                order = Order(
                    id=str(item["id"]),
                    user_id=str(item.get("customer", {}).get("id", 0)),
                    status=OrderStatus.PROCESSING,  # Default státusz
                    total=float(item["total_price"]),
                    currency=item["currency"],
                    items=order_items,
                    shipping_address=item.get("shipping_address", {}),
                    billing_address=item.get("billing_address", {}),
                    notes=item.get("note", "")
                )
                orders.append(order)
            
            return orders
        except Exception as e:
            raise Exception(f"Shopify API hiba: {str(e)}")
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get a specific order by ID."""
        try:
            response = await self.client.get(
                f"{self.base_url}/admin/api/2023-10/orders/{order_id}.json"
            )
            response.raise_for_status()
            data = response.json()
            item = data.get("order", {})
            
            order_items = []
            for line_item in item.get("line_items", []):
                order_item = OrderItem(
                    product_id=str(line_item["product_id"]),
                    product_name=line_item["title"],
                    quantity=line_item["quantity"],
                    unit_price=float(line_item["price"]),
                    total_price=float(line_item["price"]) * line_item["quantity"]
                )
                order_items.append(order_item)
            
            return Order(
                id=str(item["id"]),
                user_id=str(item.get("customer", {}).get("id", 0)),
                status=OrderStatus.PROCESSING,  # Default státusz
                total=float(item["total_price"]),
                currency=item["currency"],
                items=order_items,
                shipping_address=item.get("shipping_address", {}),
                billing_address=item.get("billing_address", {}),
                notes=item.get("note", "")
            )
        except Exception as e:
            raise Exception(f"Shopify API hiba: {str(e)}")
    
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer information."""
        try:
            response = await self.client.get(
                f"{self.base_url}/admin/api/2023-10/customers/{customer_id}.json"
            )
            response.raise_for_status()
            data = response.json()
            item = data.get("customer", {})
            
            return Customer(
                id=str(item["id"]),
                email=item["email"],
                first_name=item.get("first_name", ""),
                last_name=item.get("last_name", ""),
                phone=item.get("phone", ""),
                address=item.get("default_address", {})
            )
        except Exception as e:
            raise Exception(f"Shopify API hiba: {str(e)}")
    
    async def update_order_status(self, order_id: str, status: str) -> bool:
        """Update order status."""
        try:
            response = await self.client.put(
                f"{self.base_url}/admin/api/2023-10/orders/{order_id}.json",
                json={"order": {"financial_status": status}}
            )
            response.raise_for_status()
            return True
        except Exception as e:
            raise Exception(f"Shopify API hiba: {str(e)}")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class MockShopifyAPI(BaseWebshopAPI):
    """Mock Shopify API for development and testing."""
    
    def __init__(self):
        # Mock adatok Shopify webshophoz
        self.mock_products = [
            Product(
                id="1",
                name="Sony WH-1000XM5",
                description="Sony WH-1000XM5 vezetéknélküli zajszűrős fejhallgató",
                price=299999.0,
                currency="HUF",
                category=ProductCategory.ELECTRONICS,
                stock=12,
                images=["https://example.com/sony-wh1000xm5.jpg"],
                tags=["Fekete", "Sony", "Fejhallgató"],
                is_active=True
            ),
            Product(
                id="2", 
                name="Adidas Ultraboost 22",
                description="Adidas Ultraboost 22 futócipő",
                price=129999.0,
                currency="HUF",
                category=ProductCategory.SPORTS,
                stock=30,
                images=["https://example.com/adidas-ultraboost.jpg"],
                tags=["Adidas", "Sport", "Cipő"],
                is_active=True
            ),
            Product(
                id="3",
                name="Dell XPS 13",
                description="Dell XPS 13 laptop 13.4 inch",
                price=699999.0,
                currency="HUF",
                category=ProductCategory.ELECTRONICS,
                stock=7,
                images=["https://example.com/dell-xps13.jpg"],
                tags=["Ezüst", "Dell", "Laptop"],
                is_active=True
            ),
            Product(
                id="4",
                name="Canon EOS R6",
                description="Canon EOS R6 tükörreflexes kamera",
                price=899999.0,
                currency="HUF",
                category=ProductCategory.ELECTRONICS,
                stock=3,
                images=["https://example.com/canon-eos-r6.jpg"],
                tags=["Canon", "Kamera", "Fényképező"],
                is_active=True
            )
        ]
        
        self.mock_orders = [
            Order(
                id="2001",
                user_id="3001",
                status=OrderStatus.DELIVERED,
                total=429998.0,
                currency="HUF",
                items=[
                    OrderItem(
                        product_id="1",
                        product_name="Sony WH-1000XM5",
                        quantity=1,
                        unit_price=299999.0,
                        total_price=299999.0
                    ),
                    OrderItem(
                        product_id="2",
                        product_name="Adidas Ultraboost 22",
                        quantity=1,
                        unit_price=129999.0,
                        total_price=129999.0
                    )
                ],
                shipping_address={"city": "Szeged", "postcode": "6720"},
                billing_address={"city": "Szeged", "postcode": "6720"},
                notes="Csomagolás figyelmesen"
            ),
            Order(
                id="2002",
                user_id="3002", 
                status=OrderStatus.PENDING,
                total=899999.0,
                currency="HUF",
                items=[
                    OrderItem(
                        product_id="4",
                        product_name="Canon EOS R6",
                        quantity=1,
                        unit_price=899999.0,
                        total_price=899999.0
                    )
                ],
                shipping_address={"city": "Miskolc", "postcode": "3530"},
                billing_address={"city": "Miskolc", "postcode": "3530"},
                notes=""
            )
        ]
        
        self.mock_customers = [
            Customer(
                id="3001",
                email="szabo.peter@example.com",
                first_name="Péter",
                last_name="Szabó",
                phone="+36701234567",
                address={"city": "Szeged", "postcode": "6720"}
            ),
            Customer(
                id="3002",
                email="kovacs.anna@example.com", 
                first_name="Anna",
                last_name="Kovács",
                phone="+36801234567",
                address={"city": "Miskolc", "postcode": "3530"}
            )
        ]
    
    async def get_products(self, limit: int = 50, offset: int = 0, category: Optional[str] = None) -> List[Product]:
        """Get mock products."""
        await asyncio.sleep(0.1)  # Szimuláljuk a hálózati késleltetést
        products = self.mock_products[offset:offset + limit]
        
        if category:
            products = [p for p in products if p.category.value == category]
            
        return products
    
    async def get_product(self, product_id: str) -> Optional[Product]:
        """Get a specific mock product by ID."""
        await asyncio.sleep(0.1)
        for product in self.mock_products:
            if product.id == product_id:
                return product
        return None
    
    async def search_products(self, query: str, limit: int = 20) -> List[Product]:
        """Search mock products by query."""
        await asyncio.sleep(0.1)
        query_lower = query.lower()
        results = []
        
        for product in self.mock_products:
            if (query_lower in product.name.lower() or 
                query_lower in product.description.lower()):
                results.append(product)
                if len(results) >= limit:
                    break
        
        return results
    
    async def get_orders(self, limit: int = 50, offset: int = 0) -> List[Order]:
        """Get mock orders."""
        await asyncio.sleep(0.1)
        return self.mock_orders[offset:offset + limit]
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get a specific mock order by ID."""
        await asyncio.sleep(0.1)
        for order in self.mock_orders:
            if order.id == order_id:
                return order
        return None
    
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get mock customer information."""
        await asyncio.sleep(0.1)
        for customer in self.mock_customers:
            if customer.id == customer_id:
                return customer
        return None
    
    async def update_order_status(self, order_id: str, status: str) -> bool:
        """Update mock order status."""
        await asyncio.sleep(0.1)
        for order in self.mock_orders:
            if order.id == order_id:
                # Státusz konvertálása
                status_map = {
                    "paid": OrderStatus.DELIVERED,
                    "pending": OrderStatus.PENDING,
                    "processing": OrderStatus.PROCESSING
                }
                order.status = status_map.get(status, OrderStatus.PROCESSING)
                return True
        return False
    
    async def close(self):
        """Mock close method."""
        pass 