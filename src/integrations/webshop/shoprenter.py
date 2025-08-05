"""
Shoprenter API integration for Chatbuddy MVP.

This module provides integration with Shoprenter webshop platform.
Includes both real API integration and mock implementation for development.
"""

import httpx
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from .base import BaseWebshopAPI, Product, Order, Customer, OrderStatus, ProductCategory, OrderItem

logger = logging.getLogger(__name__)


class ShoprenterAPI(BaseWebshopAPI):
    """Éles Shoprenter API integráció"""
    
    def __init__(self, api_key: str, base_url: str):
        super().__init__(api_key, base_url)
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def get_products(self, limit: int = 50, offset: int = 0) -> List[Product]:
        """Termékek lekérése Shoprenter API-ból"""
        try:
            params = {
                "limit": limit,
                "offset": offset
            }
                
            response = await self.client.get(f"{self.base_url}/products", params=params)
            response.raise_for_status()
            
            data = response.json()
            products = []
            
            for item in data.get("products", []):
                product = Product(
                    id=item["id"],
                    name=item["name"],
                    description=item.get("description"),
                    price=float(item["price"]),
                    original_price=float(item.get("original_price", 0)),
                    stock=int(item.get("stock", 0)),
                    category=ProductCategory(item.get("category", "other")),
                    brand=item.get("brand"),
                    images=item.get("images", []),
                    tags=item.get("tags", []),
                    is_active=item.get("is_active", True),
                    created_at=datetime.fromisoformat(item["created_at"]),
                    updated_at=datetime.fromisoformat(item["updated_at"])
                )
                products.append(product)
                
            return products
            
        except Exception as e:
            logger.error(f"Shoprenter API hiba: {e}")
            return []
    
    async def get_product(self, product_id: str) -> Optional[Product]:
        """Egy termék lekérése"""
        try:
            response = await self.client.get(f"{self.base_url}/products/{product_id}")
            response.raise_for_status()
            
            item = response.json()
            return Product(
                id=item["id"],
                name=item["name"],
                description=item.get("description"),
                price=float(item["price"]),
                original_price=float(item.get("original_price", 0)),
                stock=int(item.get("stock", 0)),
                category=ProductCategory(item.get("category", "other")),
                brand=item.get("brand"),
                images=item.get("images", []),
                tags=item.get("tags", []),
                is_active=item.get("is_active", True),
                created_at=datetime.fromisoformat(item["created_at"]),
                updated_at=datetime.fromisoformat(item["updated_at"])
            )
            
        except Exception as e:
            logger.error(f"Shoprenter API hiba: {e}")
            return None
    
    async def search_products(self, query: str, limit: int = 20) -> List[Product]:
        """Termék keresés"""
        try:
            params = {
                "q": query,
                "limit": limit
            }
            
            response = await self.client.get(f"{self.base_url}/products/search", params=params)
            response.raise_for_status()
            
            data = response.json()
            products = []
            
            for item in data.get("products", []):
                product = Product(
                    id=item["id"],
                    name=item["name"],
                    description=item.get("description"),
                    price=float(item["price"]),
                    original_price=float(item.get("original_price", 0)),
                    stock=int(item.get("stock", 0)),
                    category=ProductCategory(item.get("category", "other")),
                    brand=item.get("brand"),
                    images=item.get("images", []),
                    tags=item.get("tags", []),
                    is_active=item.get("is_active", True),
                    created_at=datetime.fromisoformat(item["created_at"]),
                    updated_at=datetime.fromisoformat(item["updated_at"])
                )
                products.append(product)
                
            return products
            
        except Exception as e:
            logger.error(f"Shoprenter API hiba: {e}")
            return []
    
    async def get_orders(self, user_id: str, limit: int = 20) -> List[Order]:
        """Felhasználó rendelései"""
        try:
            params = {
                "user_id": user_id,
                "limit": limit
            }
            
            response = await self.client.get(f"{self.base_url}/orders", params=params)
            response.raise_for_status()
            
            data = response.json()
            orders = []
            
            for item in data.get("orders", []):
                order_items = [
                    OrderItem(
                        product_id=order_item["product_id"],
                        product_name=order_item["product_name"],
                        quantity=order_item["quantity"],
                        unit_price=float(order_item["unit_price"]),
                        total_price=float(order_item["total_price"])
                    )
                    for order_item in item.get("items", [])
                ]
                
                order = Order(
                    id=item["id"],
                    user_id=item["user_id"],
                    status=OrderStatus(item["status"]),
                    total=float(item["total"]),
                    items=order_items,
                    shipping_address=item.get("shipping_address"),
                    billing_address=item.get("billing_address"),
                    tracking_number=item.get("tracking_number"),
                    notes=item.get("notes"),
                    created_at=datetime.fromisoformat(item["created_at"]),
                    updated_at=datetime.fromisoformat(item["updated_at"])
                )
                orders.append(order)
                
            return orders
            
        except Exception as e:
            logger.error(f"Shoprenter API hiba: {e}")
            return []
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Egy rendelés lekérése"""
        try:
            response = await self.client.get(f"{self.base_url}/orders/{order_id}")
            response.raise_for_status()
            
            item = response.json()
            order_items = [
                OrderItem(
                    product_id=order_item["product_id"],
                    product_name=order_item["product_name"],
                    quantity=order_item["quantity"],
                    unit_price=float(order_item["unit_price"]),
                    total_price=float(order_item["total_price"])
                )
                for order_item in item.get("items", [])
            ]
            
            return Order(
                id=item["id"],
                user_id=item["user_id"],
                status=OrderStatus(item["status"]),
                total=float(item["total"]),
                items=order_items,
                shipping_address=item.get("shipping_address"),
                billing_address=item.get("billing_address"),
                tracking_number=item.get("tracking_number"),
                notes=item.get("notes"),
                created_at=datetime.fromisoformat(item["created_at"]),
                updated_at=datetime.fromisoformat(item["updated_at"])
            )
            
        except Exception as e:
            logger.error(f"Shoprenter API hiba: {e}")
            return None
    
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Ügyfél adatok lekérése"""
        try:
            response = await self.client.get(f"{self.base_url}/customers/{customer_id}")
            response.raise_for_status()
            
            item = response.json()
            return Customer(
                id=item["id"],
                email=item["email"],
                first_name=item.get("first_name"),
                last_name=item.get("last_name"),
                phone=item.get("phone"),
                address=item.get("address"),
                created_at=datetime.fromisoformat(item["created_at"]),
                updated_at=datetime.fromisoformat(item["updated_at"])
            )
            
        except Exception as e:
            logger.error(f"Shoprenter API hiba: {e}")
            return None
    
    async def update_order_status(self, order_id: str, status: OrderStatus) -> bool:
        """Rendelési státusz frissítése"""
        try:
            response = await self.client.patch(
                f"{self.base_url}/orders/{order_id}",
                json={"status": status.value}
            )
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error(f"Shoprenter API hiba: {e}")
            return False
    
    async def close(self):
        """HTTP kliens lezárása"""
        await self.client.aclose()


class MockShoprenterAPI(BaseWebshopAPI):
    """Mock Shoprenter API fejlesztéshez"""
    
    def __init__(self, api_key: str = "mock_key", base_url: str = "https://mock.shoprenter.com"):
        super().__init__(api_key, base_url)
        
        # Mock termék adatok
        self.mock_products = [
            Product(
                id="prod_1",
                name="iPhone 15 Pro",
                description="Apple iPhone 15 Pro 128GB Titanium",
                price=499999.0,
                original_price=549999.0,
                stock=15,
                category=ProductCategory.ELECTRONICS,
                brand="Apple",
                images=["https://example.com/iphone15pro.jpg"],
                tags=["telefon", "apple", "iphone", "5g"],
                is_active=True,
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 15)
            ),
            Product(
                id="prod_2", 
                name="Samsung Galaxy S24",
                description="Samsung Galaxy S24 256GB Phantom Black",
                price=399999.0,
                original_price=449999.0,
                stock=8,
                category=ProductCategory.ELECTRONICS,
                brand="Samsung",
                images=["https://example.com/galaxys24.jpg"],
                tags=["telefon", "samsung", "android", "5g"],
                is_active=True,
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 15)
            ),
            Product(
                id="prod_3",
                name="Nike Air Max 270",
                description="Nike Air Max 270 cipő fekete színben",
                price=89999.0,
                original_price=99999.0,
                stock=25,
                category=ProductCategory.SPORTS,
                brand="Nike",
                images=["https://example.com/nikeairmax.jpg"],
                tags=["cipő", "nike", "sport", "futás"],
                is_active=True,
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 15)
            )
        ]
        
        # Mock rendelés adatok
        self.mock_orders = [
            Order(
                id="order_1",
                user_id="user_123",
                status=OrderStatus.SHIPPED,
                total=499999.0,
                items=[
                    OrderItem(
                        product_id="prod_1",
                        product_name="iPhone 15 Pro",
                        quantity=1,
                        unit_price=499999.0,
                        total_price=499999.0
                    )
                ],
                shipping_address={
                    "street": "Budapest, 1234 utca 1.",
                    "city": "Budapest",
                    "postal_code": "1234",
                    "country": "Hungary"
                },
                tracking_number="TRK123456789",
                created_at=datetime(2024, 1, 10),
                updated_at=datetime(2024, 1, 12)
            ),
            Order(
                id="order_2",
                user_id="user_123", 
                status=OrderStatus.PROCESSING,
                total=89999.0,
                items=[
                    OrderItem(
                        product_id="prod_3",
                        product_name="Nike Air Max 270",
                        quantity=1,
                        unit_price=89999.0,
                        total_price=89999.0
                    )
                ],
                shipping_address={
                    "street": "Budapest, 5678 utca 2.",
                    "city": "Budapest", 
                    "postal_code": "5678",
                    "country": "Hungary"
                },
                created_at=datetime(2024, 1, 15),
                updated_at=datetime(2024, 1, 15)
            )
        ]
        
        # Mock ügyfél adatok
        self.mock_customers = [
            Customer(
                id="user_123",
                email="user@example.com",
                first_name="János",
                last_name="Kovács",
                phone="+36 20 123 4567",
                address={
                    "street": "Budapest, 1234 utca 1.",
                    "city": "Budapest",
                    "postal_code": "1234",
                    "country": "Hungary"
                },
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 15)
            )
        ]
    
    async def get_products(self, limit: int = 50, offset: int = 0, category: Optional[str] = None) -> List[Product]:
        """Mock termékek lekérése"""
        await asyncio.sleep(0.1)  # Simulate API delay
        
        products = self.mock_products[offset:offset + limit]
        
        if category:
            products = [p for p in products if p.category.value == category]
            
        return products
    
    async def get_product(self, product_id: str) -> Optional[Product]:
        """Mock egy termék lekérése"""
        await asyncio.sleep(0.1)  # Simulate API delay
        
        for product in self.mock_products:
            if product.id == product_id:
                return product
        return None
    
    async def search_products(self, query: str, limit: int = 20) -> List[Product]:
        """Mock termék keresés"""
        await asyncio.sleep(0.1)  # Simulate API delay
        
        query_lower = query.lower()
        results = []
        
        for product in self.mock_products:
            if (query_lower in product.name.lower() or 
                query_lower in product.description.lower() or
                any(query_lower in tag.lower() for tag in product.tags)):
                results.append(product)
                if len(results) >= limit:
                    break
                    
        return results
    
    async def get_orders(self, user_id: str, limit: int = 20) -> List[Order]:
        """Mock felhasználó rendelései"""
        await asyncio.sleep(0.1)  # Simulate API delay
        
        user_orders = [order for order in self.mock_orders if order.user_id == user_id]
        return user_orders[:limit]
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Mock egy rendelés lekérése"""
        await asyncio.sleep(0.1)  # Simulate API delay
        
        for order in self.mock_orders:
            if order.id == order_id:
                return order
        return None
    
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Mock ügyfél adatok lekérése"""
        await asyncio.sleep(0.1)  # Simulate API delay
        
        for customer in self.mock_customers:
            if customer.id == customer_id:
                return customer
        return None
    
    async def update_order_status(self, order_id: str, status: OrderStatus) -> bool:
        """Mock rendelési státusz frissítése"""
        await asyncio.sleep(0.1)  # Simulate API delay
        
        for order in self.mock_orders:
            if order.id == order_id:
                order.status = status
                order.updated_at = datetime.now()
                return True
        return False 