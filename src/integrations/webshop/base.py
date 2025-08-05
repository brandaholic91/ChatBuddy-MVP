"""
Base webshop API interface and data models.

This module defines the common interface and data models for all webshop integrations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class OrderStatus(str, Enum):
    """Rendelési státuszok"""
    PENDING = "pending"
    CONFIRMED = "confirmed" 
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class ProductCategory(str, Enum):
    """Termék kategóriák"""
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    BOOKS = "books"
    HOME = "home"
    SPORTS = "sports"
    BEAUTY = "beauty"
    FOOD = "food"
    OTHER = "other"


class Product(BaseModel):
    """Egységes termék modell"""
    id: str = Field(..., description="Termék egyedi azonosító")
    name: str = Field(..., description="Termék neve")
    description: Optional[str] = Field(None, description="Termék leírása")
    price: float = Field(..., description="Termék ára (HUF)")
    original_price: Optional[float] = Field(None, description="Eredeti ár (HUF)")
    currency: str = Field(default="HUF", description="Pénznem")
    stock: int = Field(..., description="Készlet mennyiség")
    category: ProductCategory = Field(..., description="Termék kategória")
    brand: Optional[str] = Field(None, description="Márka")
    images: List[str] = Field(default_factory=list, description="Termékképek URL-jei")
    tags: List[str] = Field(default_factory=list, description="Termék címkék")
    is_active: bool = Field(default=True, description="Aktív termék")
    created_at: datetime = Field(default_factory=datetime.now, description="Létrehozás dátuma")
    updated_at: datetime = Field(default_factory=datetime.now, description="Frissítés dátuma")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OrderItem(BaseModel):
    """Rendelési tétel"""
    product_id: str = Field(..., description="Termék azonosító")
    product_name: str = Field(..., description="Termék neve")
    quantity: int = Field(..., description="Mennyiség")
    unit_price: float = Field(..., description="Egységár (HUF)")
    total_price: float = Field(..., description="Összesen (HUF)")


class Order(BaseModel):
    """Egységes rendelés modell"""
    id: str = Field(..., description="Rendelés egyedi azonosító")
    user_id: str = Field(..., description="Felhasználó azonosító")
    status: OrderStatus = Field(..., description="Rendelési státusz")
    total: float = Field(..., description="Rendelés összege (HUF)")
    currency: str = Field(default="HUF", description="Pénznem")
    items: List[OrderItem] = Field(..., description="Rendelési tételek")
    shipping_address: Optional[Dict[str, Any]] = Field(None, description="Szállítási cím")
    billing_address: Optional[Dict[str, Any]] = Field(None, description="Számlázási cím")
    tracking_number: Optional[str] = Field(None, description="Követési szám")
    notes: Optional[str] = Field(None, description="Megjegyzések")
    created_at: datetime = Field(default_factory=datetime.now, description="Létrehozás dátuma")
    updated_at: datetime = Field(default_factory=datetime.now, description="Frissítés dátuma")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Customer(BaseModel):
    """Egységes ügyfél modell"""
    id: str = Field(..., description="Ügyfél egyedi azonosító")
    email: str = Field(..., description="Email cím")
    first_name: Optional[str] = Field(None, description="Keresztnév")
    last_name: Optional[str] = Field(None, description="Vezetéknév")
    phone: Optional[str] = Field(None, description="Telefonszám")
    address: Optional[Dict[str, Any]] = Field(None, description="Cím")
    created_at: datetime = Field(default_factory=datetime.now, description="Létrehozás dátuma")
    updated_at: datetime = Field(default_factory=datetime.now, description="Frissítés dátuma")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BaseWebshopAPI(ABC):
    """Alap webshop API interfész"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
    
    @abstractmethod
    async def get_products(self, limit: int = 50, offset: int = 0, category: Optional[str] = None) -> List[Product]:
        """Termékek lekérése"""
        pass
    
    @abstractmethod
    async def get_product(self, product_id: str) -> Optional[Product]:
        """Egy termék lekérése"""
        pass
    
    @abstractmethod
    async def search_products(self, query: str, limit: int = 20) -> List[Product]:
        """Termék keresés"""
        pass
    
    @abstractmethod
    async def get_orders(self, limit: int = 50, offset: int = 0) -> List[Order]:
        """Rendelések lekérése"""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Egy rendelés lekérése"""
        pass
    
    @abstractmethod
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Ügyfél adatok lekérése"""
        pass
    
    @abstractmethod
    async def update_order_status(self, order_id: str, status: str) -> bool:
        """Rendelési státusz frissítése"""
        pass 