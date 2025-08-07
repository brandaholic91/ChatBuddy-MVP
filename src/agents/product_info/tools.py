"""
Product Info Agent Tools - Pydantic AI dependency injection pattern.

This module contains tool functions for the Product Info Agent:
- Product search and filtering
- Product details retrieval
- Reviews and ratings
- Related products
- Availability checking
- Pricing information
"""

import asyncio
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from decimal import Decimal

from pydantic import BaseModel, Field
from pydantic_ai import RunContext

from ...models.product import Product, ProductInfo, ProductReview, ProductSearch
from ...models.user import User


@dataclass
class ProductInfoDependencies:
    """Product Info Agent függőségei."""
    user: Optional[User] = None
    session_id: Optional[str] = None
    database_connection: Optional[Any] = None  # Mock database connection
    cache_client: Optional[Any] = None  # Mock cache client


class ProductSearchResult(BaseModel):
    """Termék keresési eredmény."""
    products: List[Product] = Field(description="Talált termékek")
    total_count: int = Field(description="Összes találat száma")
    page: int = Field(description="Aktuális oldal")
    page_size: int = Field(description="Oldal méret")
    search_query: str = Field(description="Keresési kifejezés")
    filters_applied: Dict[str, Any] = Field(description="Alkalmazott szűrők")


class ProductDetailsResult(BaseModel):
    """Termék részletes információk."""
    product: Product = Field(description="Termék adatok")
    product_info: Optional[ProductInfo] = Field(description="Kiterjesztett termék információk")
    reviews: List[ProductReview] = Field(description="Termék értékelések")
    related_products: List[Product] = Field(description="Kapcsolódó termékek")
    availability: Dict[str, Any] = Field(description="Készlet információk")
    pricing: Dict[str, Any] = Field(description="Árazási információk")


async def search_products(
    ctx: RunContext[ProductInfoDependencies],
    query: str,
    category_id: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    in_stock: Optional[bool] = None,
    limit: int = 10
) -> ProductSearchResult:
    """
    Termékek keresése különböző kritériumok alapján.
    
    Args:
        query: Keresési kifejezés
        category_id: Kategória azonosító
        min_price: Minimum ár
        max_price: Maximum ár
        in_stock: Készleten lévő termékek
        limit: Eredmények száma
        
    Returns:
        Keresési eredmények
    """
    # Mock implementation - valós implementációban adatbázis lekérdezés
    mock_products = [
        Product(
            id="1",
            name="iPhone 15 Pro",
            description="Apple iPhone 15 Pro 128GB",
            price=Decimal("450000"),
            currency="HUF",
            category_id="phones",
            brand="Apple",
            stock_quantity=5,
            status="active",
            images=["https://example.com/iphone15.jpg"],
            tags=["telefon", "apple", "iphone"]
        ),
        Product(
            id="2", 
            name="Samsung Galaxy S24",
            description="Samsung Galaxy S24 256GB",
            price=Decimal("380000"),
            currency="HUF",
            category_id="phones",
            brand="Samsung",
            stock_quantity=3,
            status="active",
            images=["https://example.com/s24.jpg"],
            tags=["telefon", "samsung", "galaxy"]
        ),
        Product(
            id="3",
            name="MacBook Air M2",
            description="Apple MacBook Air M2 13 inch",
            price=Decimal("650000"),
            currency="HUF", 
            category_id="laptops",
            brand="Apple",
            stock_quantity=2,
            status="active",
            images=["https://example.com/macbook.jpg"],
            tags=["laptop", "apple", "macbook"]
        )
    ]
    
    # Szűrés a query alapján
    filtered_products = [
        p for p in mock_products 
        if query.lower() in p.name.lower() or query.lower() in p.description.lower()
    ]
    
    # Kategória szűrés
    if category_id:
        filtered_products = [p for p in filtered_products if p.category_id == category_id]
    
    # Ár szűrés
    if min_price:
        filtered_products = [p for p in filtered_products if p.price >= min_price]
    if max_price:
        filtered_products = [p for p in filtered_products if p.price <= max_price]
    
    # Készlet szűrés
    if in_stock is not None:
        if in_stock:
            filtered_products = [p for p in filtered_products if p.stock_quantity > 0]
        else:
            filtered_products = [p for p in filtered_products if p.stock_quantity == 0]
    
    # Limit alkalmazása
    limited_products = filtered_products[:limit]
    
    return ProductSearchResult(
        products=limited_products,
        total_count=len(filtered_products),
        page=1,
        page_size=limit,
        search_query=query,
        filters_applied={
            "category_id": category_id,
            "min_price": min_price,
            "max_price": max_price,
            "in_stock": in_stock
        }
    )


async def get_product_details(
    ctx: RunContext[ProductInfoDependencies],
    product_id: str
) -> ProductDetailsResult:
    """
    Termék részletes információk lekérése.
    
    Args:
        product_id: Termék azonosító
        
    Returns:
        Termék részletes adatok
    """
    # Mock product data
    product = Product(
        id=product_id,
        name="iPhone 15 Pro",
        description="Apple iPhone 15 Pro 128GB - A legújabb iPhone modell",
        short_description="iPhone 15 Pro 128GB",
        price=Decimal("450000"),
        original_price=Decimal("480000"),
        currency="HUF",
        category_id="phones",
        brand="Apple",
        sku="IPHONE15PRO128",
        stock_quantity=5,
        status="active",
        images=[
            "https://example.com/iphone15_1.jpg",
            "https://example.com/iphone15_2.jpg"
        ],
        main_image="https://example.com/iphone15_main.jpg",
        tags=["telefon", "apple", "iphone", "5g"]
    )
    
    product_info = ProductInfo(
        product_id=product_id,
        specifications={
            "screen_size": "6.1 inch",
            "storage": "128GB",
            "color": "Titanium",
            "processor": "A17 Pro",
            "camera": "48MP + 12MP + 12MP"
        },
        features=[
            "5G támogatás",
            "Face ID",
            "MagSafe töltés",
            "ProRAW fotózás",
            "Cinematic mode"
        ],
        benefits=[
            "Professzionális kamera rendszer",
            "Gyors A17 Pro processzor",
            "Titanium design",
            "Hosszú akkumulátor élettartam"
        ],
        warranty="2 év garancia",
        shipping_info="Ingyenes szállítás",
        return_policy="30 napos visszaküldési jog",
        reviews_count=15,
        average_rating=4.8,
        view_count=1250,
        purchase_count=89,
        wishlist_count=45
    )
    
    reviews = [
        ProductReview(
            id="1",
            product_id=product_id,
            user_id="user1",
            rating=5,
            title="Kiváló telefon!",
            comment="Nagyon elégedett vagyok vele, gyors és a kamera fantasztikus!",
            pros=["Gyors", "Jó kamera", "Szép design"],
            cons=["Drága"],
            is_verified_purchase=True,
            is_helpful=12,
            is_not_helpful=0
        ),
        ProductReview(
            id="2", 
            product_id=product_id,
            user_id="user2",
            rating=4,
            title="Jó telefon, de drága",
            comment="Minőségi termék, de az ár magas.",
            pros=["Minőségi", "Gyors"],
            cons=["Drága"],
            is_verified_purchase=True,
            is_helpful=8,
            is_not_helpful=2
        )
    ]
    
    related_products = [
        Product(
            id="2",
            name="Samsung Galaxy S24",
            description="Samsung Galaxy S24 256GB",
            price=Decimal("380000"),
            currency="HUF",
            category_id="phones",
            brand="Samsung",
            stock_quantity=3,
            status="active",
            images=["https://example.com/s24.jpg"],
            tags=["telefon", "samsung", "galaxy"]
        ),
        Product(
            id="4",
            name="iPhone 15",
            description="Apple iPhone 15 128GB",
            price=Decimal("380000"),
            currency="HUF",
            category_id="phones", 
            brand="Apple",
            stock_quantity=8,
            status="active",
            images=["https://example.com/iphone15.jpg"],
            tags=["telefon", "apple", "iphone"]
        )
    ]
    
    availability = {
        "in_stock": product.stock_quantity > 0,
        "stock_quantity": product.stock_quantity,
        "estimated_delivery": "2-3 munkanap",
        "shipping_options": [
            {"name": "Ingyenes szállítás", "price": 0, "days": "3-5"},
            {"name": "Expressz szállítás", "price": 2000, "days": "1-2"}
        ]
    }
    
    pricing = {
        "current_price": product.price,
        "original_price": product.original_price,
        "discount_percentage": 6 if product.original_price else 0,
        "currency": product.currency,
        "installment_options": [
            {"months": 12, "monthly_payment": 37500},
            {"months": 24, "monthly_payment": 18750}
        ]
    }
    
    return ProductDetailsResult(
        product=product,
        product_info=product_info,
        reviews=reviews,
        related_products=related_products,
        availability=availability,
        pricing=pricing
    )


async def get_product_reviews(
    ctx: RunContext[ProductInfoDependencies],
    product_id: str,
    limit: int = 10,
    rating_filter: Optional[int] = None
) -> List[ProductReview]:
    """
    Termék értékelések lekérése.
    
    Args:
        product_id: Termék azonosító
        limit: Eredmények száma
        rating_filter: Értékelés szűrő (1-5)
        
    Returns:
        Termék értékelések
    """
    # Mock reviews
    reviews = [
        ProductReview(
            id="1",
            product_id=product_id,
            user_id="user1",
            rating=5,
            title="Kiváló telefon!",
            comment="Nagyon elégedett vagyok vele, gyors és a kamera fantasztikus!",
            pros=["Gyors", "Jó kamera", "Szép design"],
            cons=["Drága"],
            is_verified_purchase=True,
            is_helpful=12,
            is_not_helpful=0
        ),
        ProductReview(
            id="2",
            product_id=product_id,
            user_id="user2", 
            rating=4,
            title="Jó telefon, de drága",
            comment="Minőségi termék, de az ár magas.",
            pros=["Minőségi", "Gyors"],
            cons=["Drága"],
            is_verified_purchase=True,
            is_helpful=8,
            is_not_helpful=2
        ),
        ProductReview(
            id="3",
            product_id=product_id,
            user_id="user3",
            rating=5,
            title="Legjobb iPhone eddig!",
            comment="A kamera minősége és a teljesítmény kiváló.",
            pros=["Kiváló kamera", "Gyors", "Hosszú akku"],
            cons=[],
            is_verified_purchase=True,
            is_helpful=15,
            is_not_helpful=1
        )
    ]
    
    # Rating szűrés
    if rating_filter:
        reviews = [r for r in reviews if r.rating == rating_filter]
    
    return reviews[:limit]


async def get_related_products(
    ctx: RunContext[ProductInfoDependencies],
    product_id: str,
    limit: int = 5
) -> List[Product]:
    """
    Kapcsolódó termékek lekérése.
    
    Args:
        product_id: Termék azonosító
        limit: Eredmények száma
        
    Returns:
        Kapcsolódó termékek
    """
    # Mock related products
    related_products = [
        Product(
            id="2",
            name="Samsung Galaxy S24",
            description="Samsung Galaxy S24 256GB",
            price=Decimal("380000"),
            currency="HUF",
            category_id="phones",
            brand="Samsung",
            stock_quantity=3,
            status="active",
            images=["https://example.com/s24.jpg"],
            tags=["telefon", "samsung", "galaxy"]
        ),
        Product(
            id="4",
            name="iPhone 15",
            description="Apple iPhone 15 128GB",
            price=Decimal("380000"),
            currency="HUF",
            category_id="phones",
            brand="Apple", 
            stock_quantity=8,
            status="active",
            images=["https://example.com/iphone15.jpg"],
            tags=["telefon", "apple", "iphone"]
        ),
        Product(
            id="5",
            name="AirPods Pro",
            description="Apple AirPods Pro 2. generáció",
            price=Decimal("85000"),
            currency="HUF",
            category_id="accessories",
            brand="Apple",
            stock_quantity=15,
            status="active",
            images=["https://example.com/airpods.jpg"],
            tags=["fülhallgató", "apple", "airpods"]
        )
    ]
    
    return related_products[:limit]


async def check_product_availability(
    ctx: RunContext[ProductInfoDependencies],
    product_id: str
) -> Dict[str, Any]:
    """
    Termék készlet ellenőrzése.
    
    Args:
        product_id: Termék azonosító
        
    Returns:
        Készlet információk
    """
    # Mock availability data
    availability = {
        "product_id": product_id,
        "in_stock": True,
        "stock_quantity": 5,
        "min_stock_level": 2,
        "estimated_restock_date": "2024-02-15",
        "shipping_options": [
            {
                "name": "Ingyenes szállítás",
                "price": 0,
                "delivery_time": "3-5 munkanap",
                "available": True
            },
            {
                "name": "Expressz szállítás", 
                "price": 2000,
                "delivery_time": "1-2 munkanap",
                "available": True
            }
        ],
        "pickup_available": True,
        "pickup_locations": [
            {"name": "Budapest Központ", "address": "Váci utca 1."},
            {"name": "Debrecen", "address": "Piac utca 15."}
        ]
    }
    
    return availability


async def get_product_pricing(
    ctx: RunContext[ProductInfoDependencies],
    product_id: str
) -> Dict[str, Any]:
    """
    Termék árazási információk.
    
    Args:
        product_id: Termék azonosító
        
    Returns:
        Árazási információk
    """
    # Mock pricing data
    pricing = {
        "product_id": product_id,
        "current_price": Decimal("450000"),
        "original_price": Decimal("480000"),
        "discount_percentage": 6,
        "currency": "HUF",
        "price_history": [
            {"date": "2024-01-01", "price": 480000},
            {"date": "2024-01-15", "price": 450000}
        ],
        "installment_options": [
            {
                "months": 12,
                "monthly_payment": 37500,
                "total_interest": 0,
                "available": True
            },
            {
                "months": 24,
                "monthly_payment": 18750,
                "total_interest": 0,
                "available": True
            }
        ],
        "bulk_discounts": [
            {"quantity": 2, "discount_percentage": 5},
            {"quantity": 5, "discount_percentage": 10}
        ],
        "loyalty_discounts": [
            {"type": "first_purchase", "discount_percentage": 10},
            {"type": "vip_customer", "discount_percentage": 15}
        ]
    }
    
    return pricing 