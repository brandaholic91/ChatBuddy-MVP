"""
Order models for Chatbuddy MVP.

This module contains Pydantic models for order management:
- Order: Basic order information
- OrderStatus: Order status tracking
- OrderItem: Order line items
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class OrderStatus(str, Enum):
    """Rendelési státuszok"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    RETURNED = "returned"
    ON_HOLD = "on_hold"


class PaymentStatus(str, Enum):
    """Fizetési státuszok"""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """Fizetési módok"""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    CASH_ON_DELIVERY = "cash_on_delivery"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    CRYPTO = "crypto"


class ShippingMethod(str, Enum):
    """Szállítási módok"""
    STANDARD = "standard"
    EXPRESS = "express"
    NEXT_DAY = "next_day"
    SAME_DAY = "same_day"
    PICKUP = "pickup"
    INTERNATIONAL = "international"


class Order(BaseModel):
    """Alapvető rendelési modell"""
    id: str = Field(..., description="Egyedi rendelési azonosító")
    order_number: str = Field(..., description="Rendelési szám")
    user_id: str = Field(..., description="Felhasználói azonosító")
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="Rendelési státusz")
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING, description="Fizetési státusz")
    payment_method: Optional[PaymentMethod] = Field(default=None, description="Fizetési mód")
    subtotal: Decimal = Field(..., ge=0, description="Részösszeg")
    tax_amount: Decimal = Field(default=0, ge=0, description="Adó összeg")
    shipping_amount: Decimal = Field(default=0, ge=0, description="Szállítási költség")
    discount_amount: Decimal = Field(default=0, ge=0, description="Kedvezmény összeg")
    total_amount: Decimal = Field(..., ge=0, description="Végösszeg")
    currency: str = Field(default="HUF", description="Pénznem")
    shipping_method: Optional[ShippingMethod] = Field(default=None, description="Szállítási mód")
    shipping_address: Optional[Dict[str, Any]] = Field(default=None, description="Szállítási cím")
    billing_address: Optional[Dict[str, Any]] = Field(default=None, description="Számlázási cím")
    tracking_number: Optional[str] = Field(default=None, description="Követési szám")
    tracking_url: Optional[str] = Field(default=None, description="Követési URL")
    estimated_delivery: Optional[datetime] = Field(default=None, description="Becsült szállítás")
    notes: Optional[str] = Field(default=None, description="Megjegyzések")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="További rendelési adatok")
    created_at: datetime = Field(default_factory=datetime.now, description="Rendelés létrehozása")
    updated_at: datetime = Field(default_factory=datetime.now, description="Utolsó frissítés")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class OrderItem(BaseModel):
    """Rendelési tétel modell"""
    id: str = Field(..., description="Tétel azonosító")
    order_id: str = Field(..., description="Rendelési azonosító")
    product_id: str = Field(..., description="Termék azonosító")
    variant_id: Optional[str] = Field(default=None, description="Variáns azonosító")
    product_name: str = Field(..., description="Termék neve")
    product_sku: Optional[str] = Field(default=None, description="Termék SKU")
    quantity: int = Field(..., gt=0, description="Mennyiség")
    unit_price: Decimal = Field(..., ge=0, description="Egységár")
    total_price: Decimal = Field(..., ge=0, description="Tétel összesen")
    discount_amount: Decimal = Field(default=0, ge=0, description="Kedvezmény összeg")
    tax_amount: Decimal = Field(default=0, ge=0, description="Adó összeg")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Termék attribútumok")
    image_url: Optional[str] = Field(default=None, description="Termék kép URL")
    created_at: datetime = Field(default_factory=datetime.now, description="Létrehozás időpontja")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class OrderStatusHistory(BaseModel):
    """Rendelési státusz történet"""
    id: str = Field(..., description="Történet azonosító")
    order_id: str = Field(..., description="Rendelési azonosító")
    status: OrderStatus = Field(..., description="Státusz")
    previous_status: Optional[OrderStatus] = Field(default=None, description="Előző státusz")
    comment: Optional[str] = Field(default=None, description="Megjegyzés")
    updated_by: Optional[str] = Field(default=None, description="Frissítő felhasználó")
    created_at: datetime = Field(default_factory=datetime.now, description="Státusz változás időpontja")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class OrderPayment(BaseModel):
    """Rendelési fizetés modell"""
    id: str = Field(..., description="Fizetés azonosító")
    order_id: str = Field(..., description="Rendelési azonosító")
    payment_method: PaymentMethod = Field(..., description="Fizetési mód")
    amount: Decimal = Field(..., ge=0, description="Fizetett összeg")
    currency: str = Field(default="HUF", description="Pénznem")
    status: PaymentStatus = Field(..., description="Fizetési státusz")
    transaction_id: Optional[str] = Field(default=None, description="Tranzakció azonosító")
    gateway_response: Optional[Dict[str, Any]] = Field(default=None, description="Gateway válasz")
    processed_at: Optional[datetime] = Field(default=None, description="Feldolgozás időpontja")
    created_at: datetime = Field(default_factory=datetime.now, description="Létrehozás időpontja")
    updated_at: datetime = Field(default_factory=datetime.now, description="Utolsó frissítés")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class OrderShipping(BaseModel):
    """Rendelési szállítás modell"""
    id: str = Field(..., description="Szállítás azonosító")
    order_id: str = Field(..., description="Rendelési azonosító")
    shipping_method: ShippingMethod = Field(..., description="Szállítási mód")
    tracking_number: Optional[str] = Field(default=None, description="Követési szám")
    tracking_url: Optional[str] = Field(default=None, description="Követési URL")
    carrier: Optional[str] = Field(default=None, description="Szállító cég")
    estimated_delivery: Optional[datetime] = Field(default=None, description="Becsült szállítás")
    shipped_at: Optional[datetime] = Field(default=None, description="Szállítás időpontja")
    delivered_at: Optional[datetime] = Field(default=None, description="Kézbesítés időpontja")
    shipping_address: Dict[str, Any] = Field(..., description="Szállítási cím")
    shipping_cost: Decimal = Field(..., ge=0, description="Szállítási költség")
    created_at: datetime = Field(default_factory=datetime.now, description="Létrehozás időpontja")
    updated_at: datetime = Field(default_factory=datetime.now, description="Utolsó frissítés")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class OrderRefund(BaseModel):
    """Rendelési visszatérítés modell"""
    id: str = Field(..., description="Visszatérítés azonosító")
    order_id: str = Field(..., description="Rendelési azonosító")
    amount: Decimal = Field(..., ge=0, description="Visszatérített összeg")
    reason: str = Field(..., description="Visszatérítés indoka")
    status: str = Field(default="pending", description="Visszatérítés státusz")
    refund_method: Optional[str] = Field(default=None, description="Visszatérítés módja")
    transaction_id: Optional[str] = Field(default=None, description="Tranzakció azonosító")
    processed_at: Optional[datetime] = Field(default=None, description="Feldolgozás időpontja")
    created_at: datetime = Field(default_factory=datetime.now, description="Létrehozás időpontja")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class OrderSearch(BaseModel):
    """Rendelési keresési paraméterek"""
    user_id: Optional[str] = Field(default=None, description="Felhasználói azonosító")
    order_number: Optional[str] = Field(default=None, description="Rendelési szám")
    status: Optional[OrderStatus] = Field(default=None, description="Rendelési státusz")
    payment_status: Optional[PaymentStatus] = Field(default=None, description="Fizetési státusz")
    date_from: Optional[datetime] = Field(default=None, description="Dátumtól")
    date_to: Optional[datetime] = Field(default=None, description="Dátumig")
    min_amount: Optional[Decimal] = Field(default=None, ge=0, description="Minimum összeg")
    max_amount: Optional[Decimal] = Field(default=None, ge=0, description="Maximum összeg")
    sort_by: str = Field(default="created_at", description="Rendezési szempont")
    sort_order: str = Field(default="desc", description="Rendezési sorrend")
    page: int = Field(default=1, ge=1, description="Oldal szám")
    page_size: int = Field(default=20, ge=1, le=100, description="Oldal méret")
    
    model_config = ConfigDict(
        validate_assignment=True
    ) 