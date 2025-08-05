"""
WooCommerce API integration for Chatbuddy MVP.

This module provides both real and mock implementations for WooCommerce API.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
from pydantic import BaseModel

from .base import BaseWebshopAPI, Product, Order, Customer, OrderItem, OrderStatus, ProductCategory


class WooCommerceAPI(BaseWebshopAPI):
    """Real WooCommerce API implementation."""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def get_products(self, limit: int = 50, offset: int = 0, category: Optional[str] = None) -> List[Product]:
        """Get products from WooCommerce."""
        try:
            params = {"per_page": limit, "offset": offset}
            if category:
                params["category"] = category
            response = await self.client.get(
                f"{self.base_url}/wp-json/wc/v3/products",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            products = []
            for item in data:
                product = Product(
                    id=str(item["id"]),
                    name=item["name"],
                    description=item.get("description", ""),
                    price=float(item["price"]),
                    currency="HUF",
                    category=ProductCategory.ELECTRONICS,  # Default kategória
                    stock=item.get("stock_quantity", 0),
                    images=item.get("images", []),
                    tags=item.get("attributes", []),
                    is_active=item.get("status", "publish") == "publish"
                )
                products.append(product)
            
            return products
        except Exception as e:
            raise Exception(f"WooCommerce API hiba: {str(e)}")
    
    async def get_product(self, product_id: str) -> Optional[Product]:
        """Get a specific product by ID."""
        try:
            response = await self.client.get(
                f"{self.base_url}/wp-json/wc/v3/products/{product_id}"
            )
            response.raise_for_status()
            item = response.json()
            
            return Product(
                id=str(item["id"]),
                name=item["name"],
                description=item.get("description", ""),
                price=float(item["price"]),
                currency="HUF",
                category=ProductCategory.ELECTRONICS,  # Default kategória
                stock=item.get("stock_quantity", 0),
                images=item.get("images", []),
                tags=item.get("attributes", []),
                is_active=item.get("status", "publish") == "publish"
            )
        except Exception as e:
            raise Exception(f"WooCommerce API hiba: {str(e)}")
    
    async def search_products(self, query: str, limit: int = 20) -> List[Product]:
        """Search products by query."""
        try:
            response = await self.client.get(
                f"{self.base_url}/wp-json/wc/v3/products",
                params={"search": query, "per_page": limit}
            )
            response.raise_for_status()
            data = response.json()
            
            products = []
            for item in data:
                product = Product(
                    id=str(item["id"]),
                    name=item["name"],
                    description=item.get("description", ""),
                    price=float(item["price"]),
                    currency="HUF",
                    category=ProductCategory.ELECTRONICS,  # Default kategória
                    stock=item.get("stock_quantity", 0),
                    images=item.get("images", []),
                    tags=item.get("attributes", []),
                    is_active=item.get("status", "publish") == "publish"
                )
                products.append(product)
            
            return products
        except Exception as e:
            raise Exception(f"WooCommerce API hiba: {str(e)}")
    
    async def get_orders(self, limit: int = 50, offset: int = 0) -> List[Order]:
        """Get orders from WooCommerce."""
        try:
            response = await self.client.get(
                f"{self.base_url}/wp-json/wc/v3/orders",
                params={"per_page": limit, "offset": offset}
            )
            response.raise_for_status()
            data = response.json()
            
            orders = []
            for item in data:
                order_items = []
                for line_item in item.get("line_items", []):
                    order_item = OrderItem(
                        product_id=str(line_item["product_id"]),
                        product_name=line_item["name"],
                        quantity=line_item["quantity"],
                        unit_price=float(line_item["price"]),
                        total_price=float(line_item["total"])
                    )
                    order_items.append(order_item)
                
                order = Order(
                    id=str(item["id"]),
                    user_id=str(item["customer_id"]),
                    status=OrderStatus.PROCESSING,  # Default státusz
                    total=float(item["total"]),
                    currency=item["currency"],
                    items=order_items,
                    shipping_address=item.get("shipping", {}),
                    billing_address=item.get("billing", {}),
                    notes=item.get("customer_note", "")
                )
                orders.append(order)
            
            return orders
        except Exception as e:
            raise Exception(f"WooCommerce API hiba: {str(e)}")
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get a specific order by ID."""
        try:
            response = await self.client.get(
                f"{self.base_url}/wp-json/wc/v3/orders/{order_id}"
            )
            response.raise_for_status()
            item = response.json()
            
            order_items = []
            for line_item in item.get("line_items", []):
                order_item = OrderItem(
                    product_id=str(line_item["product_id"]),
                    product_name=line_item["name"],
                    quantity=line_item["quantity"],
                    unit_price=float(line_item["price"]),
                    total_price=float(line_item["total"])
                )
                order_items.append(order_item)
            
            return Order(
                id=str(item["id"]),
                user_id=str(item["customer_id"]),
                status=OrderStatus.PROCESSING,  # Default státusz
                total=float(item["total"]),
                currency=item["currency"],
                items=order_items,
                shipping_address=item.get("shipping", {}),
                billing_address=item.get("billing", {}),
                notes=item.get("customer_note", "")
            )
        except Exception as e:
            raise Exception(f"WooCommerce API hiba: {str(e)}")
    
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer information."""
        try:
            response = await self.client.get(
                f"{self.base_url}/wp-json/wc/v3/customers/{customer_id}"
            )
            response.raise_for_status()
            item = response.json()
            
            return Customer(
                id=str(item["id"]),
                email=item["email"],
                first_name=item.get("first_name", ""),
                last_name=item.get("last_name", ""),
                phone=item.get("billing", {}).get("phone", ""),
                address=item.get("billing", {})
            )
        except Exception as e:
            raise Exception(f"WooCommerce API hiba: {str(e)}")
    
    async def update_order_status(self, order_id: str, status: str) -> bool:
        """Update order status."""
        try:
            response = await self.client.put(
                f"{self.base_url}/wp-json/wc/v3/orders/{order_id}",
                json={"status": status}
            )
            response.raise_for_status()
            return True
        except Exception as e:
            raise Exception(f"WooCommerce API hiba: {str(e)}")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class MockWooCommerceAPI(BaseWebshopAPI):
    """Mock WooCommerce API for development and testing."""
    
    def __init__(self):
        # Mock adatok WooCommerce webshophoz
        self.mock_products = [
            Product(
                id="1",
                name="iPhone 15 Pro",
                description="Apple iPhone 15 Pro 128GB",
                price=499999.0,
                currency="HUF",
                category=ProductCategory.ELECTRONICS,
                stock=15,
                images=["https://example.com/iphone15pro.jpg"],
                tags=["Titánium", "iPhone", "Apple"],
                is_active=True
            ),
            Product(
                id="2", 
                name="Samsung Galaxy S24",
                description="Samsung Galaxy S24 256GB",
                price=399999.0,
                currency="HUF",
                category=ProductCategory.ELECTRONICS,
                stock=8,
                images=["https://example.com/samsung-s24.jpg"],
                tags=["Fekete", "Samsung", "Android"],
                is_active=True
            ),
            Product(
                id="3",
                name="Nike Air Max 270",
                description="Nike Air Max 270 cipő",
                price=89999.0,
                currency="HUF", 
                category=ProductCategory.SPORTS,
                stock=25,
                images=["https://example.com/nike-airmax.jpg"],
                tags=["Nike", "Sport", "Cipő"],
                is_active=True
            ),
            Product(
                id="4",
                name="MacBook Pro 14",
                description="Apple MacBook Pro 14 inch M3",
                price=899999.0,
                currency="HUF",
                category=ProductCategory.ELECTRONICS,
                stock=5,
                images=["https://example.com/macbook-pro.jpg"],
                tags=["Ezüst", "MacBook", "Laptop"],
                is_active=True
            )
        ]
        
        self.mock_orders = [
            Order(
                id="1001",
                user_id="2001",
                status=OrderStatus.PROCESSING,
                total=589998.0,
                currency="HUF",
                items=[
                    OrderItem(
                        product_id="1",
                        product_name="iPhone 15 Pro",
                        quantity=1,
                        unit_price=499999.0,
                        total_price=499999.0
                    ),
                    OrderItem(
                        product_id="3",
                        product_name="Nike Air Max 270",
                        quantity=1,
                        unit_price=89999.0,
                        total_price=89999.0
                    )
                ],
                shipping_address={"city": "Budapest", "postcode": "1000"},
                billing_address={"city": "Budapest", "postcode": "1000"},
                notes="Sürgős szállítás"
            ),
            Order(
                id="1002",
                user_id="2002", 
                status=OrderStatus.DELIVERED,
                total=899999.0,
                currency="HUF",
                items=[
                    OrderItem(
                        product_id="4",
                        product_name="MacBook Pro 14",
                        quantity=1,
                        unit_price=899999.0,
                        total_price=899999.0
                    )
                ],
                shipping_address={"city": "Debrecen", "postcode": "4000"},
                billing_address={"city": "Debrecen", "postcode": "4000"},
                notes=""
            )
        ]
        
        self.mock_customers = [
            Customer(
                id="2001",
                email="kiss.janos@example.com",
                first_name="János",
                last_name="Kiss",
                phone="+36201234567",
                address={"city": "Budapest", "postcode": "1000"}
            ),
            Customer(
                id="2002",
                email="nagy.maria@example.com", 
                first_name="Mária",
                last_name="Nagy",
                phone="+36301234567",
                address={"city": "Debrecen", "postcode": "4000"}
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
                    "completed": OrderStatus.DELIVERED,
                    "processing": OrderStatus.PROCESSING,
                    "pending": OrderStatus.PENDING
                }
                order.status = status_map.get(status, OrderStatus.PROCESSING)
                return True
        return False
    
    async def close(self):
        """Mock close method."""
        pass 