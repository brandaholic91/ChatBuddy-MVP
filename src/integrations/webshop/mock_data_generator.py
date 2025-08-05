"""
Mock adat generátor a termékadat szinkronizáció teszteléséhez.
Ez lehetővé teszi a valós webshop nélküli fejlesztést.
"""

import asyncio
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from src.models.product import Product, ProductCategory
from src.models.order import Order, OrderStatus


class MockEventType(Enum):
    """Mock esemény típusok"""
    PRODUCT_CREATED = "product_created"
    PRODUCT_UPDATED = "product_updated"
    PRODUCT_DELETED = "product_deleted"
    INVENTORY_CHANGED = "inventory_changed"
    PRICE_CHANGED = "price_changed"
    ORDER_CREATED = "order_created"
    ORDER_STATUS_CHANGED = "order_status_changed"


@dataclass
class MockEvent:
    """Mock esemény adatstruktúra"""
    event_type: MockEventType
    timestamp: datetime
    data: Dict
    source: str = "mock_webshop"


class MockDataGenerator:
    """Mock adat generátor a termékadat szinkronizációhoz"""
    
    def __init__(self):
        self.product_categories = [
            "Elektronika", "Ruházat", "Könyvek", "Otthon", "Sport", 
            "Szépségápolás", "Játékok", "Élelmiszer", "Autó", "Kert"
        ]
        
        self.brand_names = [
            "TechCorp", "FashionStyle", "HomeLife", "SportMax", "BeautyPro",
            "ToyWorld", "FoodFresh", "AutoParts", "GardenCare", "SmartHome"
        ]
        
        self.product_names = [
            "iPhone 15 Pro", "Samsung Galaxy S24", "MacBook Air", "iPad Pro",
            "Nike Air Max", "Adidas Ultraboost", "Puma RS-X", "Under Armour",
            "Sony WH-1000XM5", "Bose QuietComfort", "Apple Watch Series 9",
            "Garmin Fenix 7", "Canon EOS R5", "Sony A7 IV", "DJI Mini 3 Pro"
        ]
        
        self.descriptions = [
            "Prémium minőségű termék kiváló teljesítménnyel",
            "Innovatív technológia a modern élethez",
            "Ergonomikus design kényelmes használatért",
            "Tartós anyagokból készült professzionális minőségben",
            "Környezetbarát megoldás fenntartható jövőért",
            "Kompatibilis minden főbb platformmal",
            "Gyors és hatékony működés garantált",
            "Egyszerű használat kezdőknek és szakértőknek egyaránt"
        ]

    def generate_mock_product(self, product_id: Optional[int] = None) -> Product:
        """Mock termék generálása"""
        if product_id is None:
            product_id = random.randint(1000, 9999)
            
        name = random.choice(self.product_names)
        brand = random.choice(self.brand_names)
        category = random.choice(self.product_categories)
        price = round(random.uniform(10.0, 2000.0), 2)
        stock = random.randint(0, 100)
        description = random.choice(self.descriptions)
        
        # Random változások generálása
        price_change = random.choice([-0.05, 0, 0.05, 0.10, -0.10])
        stock_change = random.choice([-5, -2, 0, 2, 5])
        
        return Product(
            id=str(product_id),
            name=f"{brand} {name}",
            description=description,
            price=price,
            original_price=price * (1 + price_change),
            category_id=category,
            stock_quantity=stock,
            sku=f"SKU-{product_id:04d}",
            images=[f"https://mock-images.com/product-{product_id}.jpg"],
            tags=[brand.lower(), category.lower(), "mock"],
            created_at=datetime.now() - timedelta(days=random.randint(1, 365)),
            updated_at=datetime.now()
        )

    def generate_mock_products(self, count: int = 50) -> List[Product]:
        """Több mock termék generálása"""
        products = []
        for i in range(count):
            product = self.generate_mock_product(1000 + i)
            products.append(product)
        return products

    def generate_mock_order(self, order_id: Optional[int] = None) -> Order:
        """Mock rendelés generálása"""
        if order_id is None:
            order_id = random.randint(10000, 99999)
            
        status = random.choice(list(OrderStatus))
        customer_name = f"Vásárló {random.randint(1, 100)}"
        
        return Order(
            id=str(order_id),
            customer_name=customer_name,
            customer_email=f"vasarlo{random.randint(1, 100)}@example.com",
            status=status,
            total_amount=round(random.uniform(50.0, 500.0), 2),
            items=[],  # Mock termékek lesznek hozzáadva
            created_at=datetime.now() - timedelta(days=random.randint(1, 30)),
            updated_at=datetime.now()
        )

    def generate_mock_events(self, event_count: int = 10) -> List[MockEvent]:
        """Mock események generálása szinkronizáció teszteléséhez"""
        events = []
        event_types = list(MockEventType)
        
        for i in range(event_count):
            event_type = random.choice(event_types)
            timestamp = datetime.now() - timedelta(minutes=random.randint(1, 60))
            
            if event_type in [MockEventType.PRODUCT_CREATED, MockEventType.PRODUCT_UPDATED]:
                data = {
                    "product_id": random.randint(1000, 9999),
                    "product_name": random.choice(self.product_names),
                    "price": round(random.uniform(10.0, 2000.0), 2),
                    "stock": random.randint(0, 100)
                }
            elif event_type == MockEventType.INVENTORY_CHANGED:
                data = {
                    "product_id": random.randint(1000, 9999),
                    "old_stock": random.randint(10, 50),
                    "new_stock": random.randint(0, 100),
                    "change_reason": random.choice(["sale", "restock", "damage", "return"])
                }
            elif event_type == MockEventType.PRICE_CHANGED:
                data = {
                    "product_id": random.randint(1000, 9999),
                    "old_price": round(random.uniform(10.0, 1000.0), 2),
                    "new_price": round(random.uniform(10.0, 1000.0), 2),
                    "change_percentage": round(random.uniform(-0.5, 0.5), 2)
                }
            else:
                data = {"order_id": random.randint(10000, 99999)}
            
            event = MockEvent(
                event_type=event_type,
                timestamp=timestamp,
                data=data,
                source="mock_webshop"
            )
            events.append(event)
        
        return sorted(events, key=lambda x: x.timestamp)

    async def simulate_real_time_updates(self, callback_func, interval: int = 30):
        """Valós idejű frissítések szimulálása"""
        """Valós idejű frissítések szimulálása"""
        while True:
            # Random esemény generálása
            event_type = random.choice(list(MockEventType))
            event = MockEvent(
                event_type=event_type,
                timestamp=datetime.now(),
                data={"product_id": random.randint(1000, 9999)},
                source="mock_webshop"
            )
            
            # Callback hívása az eseménnyel
            await callback_func(event)
            
            # Várakozás a következő frissítésig
            await asyncio.sleep(interval)


class MockSyncManager:
    """Mock szinkronizációs menedzser"""
    
    def __init__(self, data_generator: MockDataGenerator):
        self.data_generator = data_generator
        self.sync_history = []
        self.last_sync = None
        
    async def sync_products(self) -> Dict:
        """Termékek szinkronizálása"""
        products = self.data_generator.generate_mock_products(20)
        
        sync_result = {
            "timestamp": datetime.now(),
            "products_synced": len(products),
            "new_products": random.randint(0, 5),
            "updated_products": random.randint(0, 10),
            "deleted_products": random.randint(0, 2),
            "errors": []
        }
        
        self.sync_history.append(sync_result)
        self.last_sync = datetime.now()
        
        return sync_result
    
    async def sync_inventory(self) -> Dict:
        """Készlet frissítések szinkronizálása"""
        inventory_updates = []
        
        for _ in range(random.randint(5, 15)):
            product_id = random.randint(1000, 9999)
            old_stock = random.randint(10, 50)
            new_stock = random.randint(0, 100)
            
            inventory_updates.append({
                "product_id": product_id,
                "old_stock": old_stock,
                "new_stock": new_stock,
                "change": new_stock - old_stock,
                "timestamp": datetime.now()
            })
        
        return {
            "timestamp": datetime.now(),
            "inventory_updates": inventory_updates,
            "total_updates": len(inventory_updates)
        }
    
    async def sync_prices(self) -> Dict:
        """Ár változások szinkronizálása"""
        price_updates = []
        
        for _ in range(random.randint(3, 10)):
            product_id = random.randint(1000, 9999)
            old_price = round(random.uniform(10.0, 1000.0), 2)
            new_price = round(random.uniform(10.0, 1000.0), 2)
            
            price_updates.append({
                "product_id": product_id,
                "old_price": old_price,
                "new_price": new_price,
                "change_percentage": round((new_price - old_price) / old_price * 100, 2),
                "timestamp": datetime.now()
            })
        
        return {
            "timestamp": datetime.now(),
            "price_updates": price_updates,
            "total_updates": len(price_updates)
        }
    
    def get_sync_statistics(self) -> Dict:
        """Szinkronizációs statisztikák"""
        if not self.sync_history:
            return {"total_syncs": 0, "last_sync": None}
        
        return {
            "total_syncs": len(self.sync_history),
            "last_sync": self.last_sync,
            "average_products_per_sync": sum(s["products_synced"] for s in self.sync_history) / len(self.sync_history),
            "total_errors": sum(len(s["errors"]) for s in self.sync_history)
        }


# Singleton instance
mock_data_generator = MockDataGenerator()
mock_sync_manager = MockSyncManager(mock_data_generator) 