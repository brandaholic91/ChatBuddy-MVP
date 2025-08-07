"""
UNAS API integration for Chatbuddy MVP.

This module provides integration with UNAS webshop platform.
Includes both real API integration and mock implementation for development.
"""

import httpx
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from .base import BaseWebshopAPI, Product, Order, Customer, OrderStatus, ProductCategory, OrderItem

logger = logging.getLogger(__name__)


class UNASAPI(BaseWebshopAPI):
    """Éles UNAS API integráció"""
    
    def __init__(self, api_key: str, base_url: str):
        super().__init__(api_key, base_url)
        self.client = httpx.AsyncClient(
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def get_products(self, limit: int = 50, offset: int = 0) -> List[Product]:
        """Termékek lekérése UNAS API-ból"""
        try:
            params = {
                "limit": limit,
                "offset": offset
            }
                
            response = await self.client.get(f"{self.base_url}/api/products", params=params)
            response.raise_for_status()
            
            data = response.json()
            products = []
            
            for item in data.get("data", []):
                product = Product(
                    id=item["product_id"],
                    name=item["name"],
                    description=item.get("description"),
                    price=float(item["price"]),
                    original_price=float(item.get("original_price", 0)),
                    stock=int(item.get("stock", 0)),
                    category=ProductCategory(item.get("category", "other")),
                    brand=item.get("brand"),
                    images=item.get("images", []),
                    tags=item.get("tags", []),
                    is_active=item.get("active", True),
                    created_at=datetime.fromisoformat(item["created_at"]),
                    updated_at=datetime.fromisoformat(item["updated_at"])
                )
                products.append(product)
                
            return products
            
        except Exception as e:
            logger.error(f"UNAS API hiba: {e}")
            return []
    
    async def get_product(self, product_id: str) -> Optional[Product]:
        """Egy termék lekérése"""
        try:
            response = await self.client.get(f"{self.base_url}/api/products/{product_id}")
            response.raise_for_status()
            
            item = response.json()
            return Product(
                id=item["product_id"],
                name=item["name"],
                description=item.get("description"),
                price=float(item["price"]),
                original_price=float(item.get("original_price", 0)),
                stock=int(item.get("stock", 0)),
                category=ProductCategory(item.get("category", "other")),
                brand=item.get("brand"),
                images=item.get("images", []),
                tags=item.get("tags", []),
                is_active=item.get("active", True),
                created_at=datetime.fromisoformat(item["created_at"]),
                updated_at=datetime.fromisoformat(item["updated_at"])
            )
            
        except Exception as e:
            logger.error(f"UNAS API hiba: {e}")
            return None
    
    async def search_products(self, query: str, limit: int = 20) -> List[Product]:
        """Termék keresés"""
        try:
            params = {
                "search": query,
                "limit": limit
            }
            
            response = await self.client.get(f"{self.base_url}/api/products/search", params=params)
            response.raise_for_status()
            
            data = response.json()
            products = []
            
            for item in data.get("data", []):
                product = Product(
                    id=item["product_id"],
                    name=item["name"],
                    description=item.get("description"),
                    price=float(item["price"]),
                    original_price=float(item.get("original_price", 0)),
                    stock=int(item.get("stock", 0)),
                    category=ProductCategory(item.get("category", "other")),
                    brand=item.get("brand"),
                    images=item.get("images", []),
                    tags=item.get("tags", []),
                    is_active=item.get("active", True),
                    created_at=datetime.fromisoformat(item["created_at"]),
                    updated_at=datetime.fromisoformat(item["updated_at"])
                )
                products.append(product)
                
            return products
            
        except Exception as e:
            logger.error(f"UNAS API hiba: {e}")
            return []
    
    async def get_orders(self, user_id: str, limit: int = 20) -> List[Order]:
        """Felhasználó rendelései"""
        try:
            params = {
                "user_id": user_id,
                "limit": limit
            }
            
            response = await self.client.get(f"{self.base_url}/api/orders", params=params)
            response.raise_for_status()
            
            data = response.json()
            orders = []
            
            for item in data.get("data", []):
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
                    id=item["order_id"],
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
            logger.error(f"UNAS API hiba: {e}")
            return []
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Egy rendelés lekérése"""
        try:
            response = await self.client.get(f"{self.base_url}/api/orders/{order_id}")
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
                id=item["order_id"],
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
            logger.error(f"UNAS API hiba: {e}")
            return None
    
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Ügyfél adatok lekérése"""
        try:
            response = await self.client.get(f"{self.base_url}/api/customers/{customer_id}")
            response.raise_for_status()
            
            item = response.json()
            return Customer(
                id=item["customer_id"],
                email=item["email"],
                first_name=item.get("first_name"),
                last_name=item.get("last_name"),
                phone=item.get("phone"),
                address=item.get("address"),
                created_at=datetime.fromisoformat(item["created_at"]),
                updated_at=datetime.fromisoformat(item["updated_at"])
            )
            
        except Exception as e:
            logger.error(f"UNAS API hiba: {e}")
            return None
    
    async def update_order_status(self, order_id: str, status: OrderStatus) -> bool:
        """Rendelési státusz frissítése"""
        try:
            response = await self.client.patch(
                f"{self.base_url}/api/orders/{order_id}",
                json={"status": status.value}
            )
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error(f"UNAS API hiba: {e}")
            return False
    
    async def close(self):
        """HTTP kliens lezárása"""
        await self.client.aclose()


class MockUNASAPI(BaseWebshopAPI):
    """Mock UNAS API fejlesztéshez"""
    
    def __init__(self, api_key: str = "mock_key", base_url: str = "https://mock.unas.hu"):
        super().__init__(api_key, base_url)
        
        # Mock termék adatok
        self.mock_products = [
            Product(
                id="unas_prod_1",
                name="Asus ROG Strix G15",
                description="Asus ROG Strix G15 gaming laptop RTX 4060-tel",
                price=899999.0,
                original_price=999999.0,
                stock=5,
                category=ProductCategory.ELECTRONICS,
                brand="Asus",
                images=["https://example.com/asus-rog.jpg"],
                tags=["laptop", "gaming", "asus", "rtx"],
                is_active=True,
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 15)
            ),
            Product(
                id="unas_prod_2",
                name="Adidas Ultraboost 22",
                description="Adidas Ultraboost 22 futócipő fehér színben",
                price=129999.0,
                original_price=149999.0,
                stock=12,
                category=ProductCategory.SPORTS,
                brand="Adidas",
                images=["https://example.com/adidas-ultraboost.jpg"],
                tags=["cipő", "adidas", "futás", "sport"],
                is_active=True,
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 15)
            ),
            Product(
                id="unas_prod_3",
                name="Sony WH-1000XM5",
                description="Sony WH-1000XM5 vezetéknélküli zajszűrős fejhallgató",
                price=299999.0,
                original_price=349999.0,
                stock=8,
                category=ProductCategory.ELECTRONICS,
                brand="Sony",
                images=["https://example.com/sony-wh1000xm5.jpg"],
                tags=["fejhallgató", "sony", "zajszűrős", "bluetooth"],
                is_active=True,
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 15)
            )
        ]
        
        # Mock rendelés adatok
        self.mock_orders = [
            Order(
                id="unas_order_1",
                user_id="unas_user_123",
                status=OrderStatus.DELIVERED,
                total=899999.0,
                items=[
                    OrderItem(
                        product_id="unas_prod_1",
                        product_name="Asus ROG Strix G15",
                        quantity=1,
                        unit_price=899999.0,
                        total_price=899999.0
                    )
                ],
                shipping_address={
                    "street": "Debrecen, 5678 utca 3.",
                    "city": "Debrecen",
                    "postal_code": "5678",
                    "country": "Hungary"
                },
                tracking_number="UNAS123456789",
                created_at=datetime(2024, 1, 5),
                updated_at=datetime(2024, 1, 8)
            ),
            Order(
                id="unas_order_2",
                user_id="unas_user_123",
                status=OrderStatus.PROCESSING,
                total=129999.0,
                items=[
                    OrderItem(
                        product_id="unas_prod_2",
                        product_name="Adidas Ultraboost 22",
                        quantity=1,
                        unit_price=129999.0,
                        total_price=129999.0
                    )
                ],
                shipping_address={
                    "street": "Debrecen, 9012 utca 4.",
                    "city": "Debrecen",
                    "postal_code": "9012",
                    "country": "Hungary"
                },
                created_at=datetime(2024, 1, 18),
                updated_at=datetime(2024, 1, 18)
            )
        ]
        
        # Mock ügyfél adatok
        self.mock_customers = [
            Customer(
                id="unas_user_123",
                email="unas_user@example.com",
                first_name="Mária",
                last_name="Nagy",
                phone="+36 30 987 6543",
                address={
                    "street": "Debrecen, 5678 utca 3.",
                    "city": "Debrecen",
                    "postal_code": "5678",
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