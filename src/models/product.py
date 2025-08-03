"""
Product models for Chatbuddy MVP.

This module contains Pydantic models for product management:
- Product: Basic product information
- ProductCategory: Product categories
- ProductInfo: Extended product information
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class ProductStatus(str, Enum):
    """Termék státuszok"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"
    DRAFT = "draft"


class ProductType(str, Enum):
    """Termék típusok"""
    PHYSICAL = "physical"
    DIGITAL = "digital"
    SERVICE = "service"
    SUBSCRIPTION = "subscription"


class Product(BaseModel):
    """Alapvető termék modell"""
    id: str = Field(..., description="Egyedi termék azonosító")
    name: str = Field(..., min_length=1, description="Termék neve")
    description: Optional[str] = Field(default=None, description="Termék leírása")
    short_description: Optional[str] = Field(default=None, description="Rövid leírás")
    price: Decimal = Field(..., ge=0, description="Termék ára")
    original_price: Optional[Decimal] = Field(default=None, ge=0, description="Eredeti ár")
    currency: str = Field(default="HUF", description="Pénznem")
    category_id: Optional[str] = Field(default=None, description="Kategória azonosító")
    brand: Optional[str] = Field(default=None, description="Márka")
    sku: Optional[str] = Field(default=None, description="SKU kód")
    barcode: Optional[str] = Field(default=None, description="Vonalkód")
    weight: Optional[float] = Field(default=None, ge=0, description="Súly (kg)")
    dimensions: Optional[Dict[str, float]] = Field(default=None, description="Méretek (cm)")
    status: ProductStatus = Field(default=ProductStatus.ACTIVE, description="Termék státusz")
    product_type: ProductType = Field(default=ProductType.PHYSICAL, description="Termék típusa")
    stock_quantity: int = Field(default=0, description="Készlet mennyiség")
    min_stock_level: int = Field(default=0, description="Minimum készlet szint")
    max_stock_level: Optional[int] = Field(default=None, description="Maximum készlet szint")
    is_featured: bool = Field(default=False, description="Kiemelt termék")
    is_bestseller: bool = Field(default=False, description="Bestseller")
    is_new: bool = Field(default=False, description="Új termék")
    is_on_sale: bool = Field(default=False, description="Akciós termék")
    sale_percentage: Optional[int] = Field(default=None, ge=0, le=100, description="Akció százalék")
    tags: List[str] = Field(default_factory=list, description="Címkék")
    images: List[str] = Field(default_factory=list, description="Kép URL-ek")
    main_image: Optional[str] = Field(default=None, description="Fő kép URL")
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="További termék adatok")
    created_at: datetime = Field(default_factory=datetime.now, description="Létrehozás időpontja")
    updated_at: datetime = Field(default_factory=datetime.now, description="Utolsó frissítés")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class ProductCategory(BaseModel):
    """Termék kategória modell"""
    id: str = Field(..., description="Kategória azonosító")
    name: str = Field(..., min_length=1, description="Kategória neve")
    description: Optional[str] = Field(default=None, description="Kategória leírása")
    parent_id: Optional[str] = Field(default=None, description="Szülő kategória azonosító")
    slug: str = Field(..., description="SEO-barát URL slug")
    image_url: Optional[str] = Field(default=None, description="Kategória kép URL")
    is_active: bool = Field(default=True, description="Kategória aktív")
    sort_order: int = Field(default=0, description="Rendezési sorrend")
    level: int = Field(default=0, description="Kategória szint (0 = gyökér)")
    path: List[str] = Field(default_factory=list, description="Kategória útvonal")
    product_count: int = Field(default=0, description="Termékek száma")
    created_at: datetime = Field(default_factory=datetime.now, description="Létrehozás időpontja")
    updated_at: datetime = Field(default_factory=datetime.now, description="Utolsó frissítés")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class ProductInfo(BaseModel):
    """Kiterjesztett termék információk"""
    product_id: str = Field(..., description="Termék azonosító")
    specifications: Dict[str, Any] = Field(default_factory=dict, description="Termék specifikációk")
    features: List[str] = Field(default_factory=list, description="Termék jellemzők")
    benefits: List[str] = Field(default_factory=list, description="Termék előnyök")
    warranty: Optional[str] = Field(default=None, description="Garancia információk")
    shipping_info: Optional[str] = Field(default=None, description="Szállítási információk")
    return_policy: Optional[str] = Field(default=None, description="Visszaküldési feltételek")
    reviews_count: int = Field(default=0, description="Értékelések száma")
    average_rating: float = Field(default=0.0, ge=0.0, le=5.0, description="Átlagos értékelés")
    view_count: int = Field(default=0, description="Megtekintések száma")
    purchase_count: int = Field(default=0, description="Vásárlások száma")
    wishlist_count: int = Field(default=0, description="Kívánságlistára tették száma")
    related_products: List[str] = Field(default_factory=list, description="Kapcsolódó termékek")
    cross_sell_products: List[str] = Field(default_factory=list, description="Cross-sell termékek")
    up_sell_products: List[str] = Field(default_factory=list, description="Up-sell termékek")
    seo_title: Optional[str] = Field(default=None, description="SEO cím")
    seo_description: Optional[str] = Field(default=None, description="SEO leírás")
    seo_keywords: List[str] = Field(default_factory=list, description="SEO kulcsszavak")
    updated_at: datetime = Field(default_factory=datetime.now, description="Utolsó frissítés")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class ProductVariant(BaseModel):
    """Termék variáns modell"""
    id: str = Field(..., description="Variáns azonosító")
    product_id: str = Field(..., description="Termék azonosító")
    name: str = Field(..., description="Variáns neve")
    sku: Optional[str] = Field(default=None, description="Variáns SKU")
    price: Decimal = Field(..., ge=0, description="Variáns ár")
    original_price: Optional[Decimal] = Field(default=None, ge=0, description="Eredeti ár")
    stock_quantity: int = Field(default=0, description="Készlet mennyiség")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Variáns attribútumok")
    images: List[str] = Field(default_factory=list, description="Variáns képek")
    is_active: bool = Field(default=True, description="Variáns aktív")
    sort_order: int = Field(default=0, description="Rendezési sorrend")
    created_at: datetime = Field(default_factory=datetime.now, description="Létrehozás időpontja")
    updated_at: datetime = Field(default_factory=datetime.now, description="Utolsó frissítés")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class ProductReview(BaseModel):
    """Termék értékelés modell"""
    id: str = Field(..., description="Értékelés azonosító")
    product_id: str = Field(..., description="Termék azonosító")
    user_id: str = Field(..., description="Felhasználói azonosító")
    rating: int = Field(..., ge=1, le=5, description="Értékelés (1-5)")
    title: Optional[str] = Field(default=None, description="Értékelés címe")
    comment: Optional[str] = Field(default=None, description="Értékelés szövege")
    pros: List[str] = Field(default_factory=list, description="Előnyök")
    cons: List[str] = Field(default_factory=list, description="Hátrányok")
    is_verified_purchase: bool = Field(default=False, description="Igazolt vásárlás")
    is_helpful: int = Field(default=0, description="Hasznos szavazatok")
    is_not_helpful: int = Field(default=0, description="Nem hasznos szavazatok")
    images: List[str] = Field(default_factory=list, description="Értékelés képek")
    status: str = Field(default="approved", description="Értékelés státusz")
    created_at: datetime = Field(default_factory=datetime.now, description="Létrehozás időpontja")
    updated_at: datetime = Field(default_factory=datetime.now, description="Utolsó frissítés")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class ProductSearch(BaseModel):
    """Termék keresési paraméterek"""
    query: Optional[str] = Field(default=None, description="Keresési kifejezés")
    category_id: Optional[str] = Field(default=None, description="Kategória azonosító")
    brand: Optional[str] = Field(default=None, description="Márka")
    min_price: Optional[Decimal] = Field(default=None, ge=0, description="Minimum ár")
    max_price: Optional[Decimal] = Field(default=None, ge=0, description="Maximum ár")
    in_stock: Optional[bool] = Field(default=None, description="Készleten lévő")
    is_featured: Optional[bool] = Field(default=None, description="Kiemelt termékek")
    is_on_sale: Optional[bool] = Field(default=None, description="Akciós termékek")
    tags: List[str] = Field(default_factory=list, description="Címkék")
    sort_by: str = Field(default="relevance", description="Rendezési szempont")
    sort_order: str = Field(default="desc", description="Rendezési sorrend")
    page: int = Field(default=1, ge=1, description="Oldal szám")
    page_size: int = Field(default=20, ge=1, le=100, description="Oldal méret")
    
    model_config = ConfigDict(
        validate_assignment=True
    ) 