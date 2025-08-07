"""
Marketing models for Chatbuddy MVP.

This module contains Pydantic models for marketing automation:
- EmailTemplate: Email template management
- SMSTemplate: SMS template management
- Campaign: Marketing campaign management
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class TemplateType(str, Enum):
    """Template típusok"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    MESSENGER = "messenger"
    WHATSAPP = "whatsapp"


class CampaignType(str, Enum):
    """Kampány típusok"""
    ABANDONED_CART = "abandoned_cart"
    WELCOME = "welcome"
    BIRTHDAY = "birthday"
    PROMOTIONAL = "promotional"
    NEWSLETTER = "newsletter"
    PRODUCT_LAUNCH = "product_launch"
    FLASH_SALE = "flash_sale"
    CUSTOMER_REVIEW = "customer_review"
    RE_ENGAGEMENT = "re_engagement"


class CampaignStatus(str, Enum):
    """Kampány státuszok"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EmailTemplate(BaseModel):
    """Email template modell"""
    id: str = Field(..., description="Template azonosító")
    name: str = Field(..., min_length=1, description="Template neve")
    subject: str = Field(..., min_length=1, description="Email tárgy")
    html_content: str = Field(..., min_length=1, description="HTML tartalom")
    text_content: Optional[str] = Field(default=None, description="Szöveges tartalom")
    template_type: TemplateType = Field(default=TemplateType.EMAIL, description="Template típusa")
    campaign_type: Optional[CampaignType] = Field(default=None, description="Kampány típusa")
    variables: List[str] = Field(default_factory=list, description="Template változók")
    is_active: bool = Field(default=True, description="Template aktív")
    is_default: bool = Field(default=False, description="Alapértelmezett template")
    language: str = Field(default="hu", description="Nyelv")
    category: Optional[str] = Field(default=None, description="Kategória")
    tags: List[str] = Field(default_factory=list, description="Címkék")
    usage_count: int = Field(default=0, description="Használatok száma")
    success_rate: float = Field(default=1.0, ge=0.0, le=1.0, description="Siker arány")
    open_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Megnyitási arány")
    click_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Kattintási arány")
    created_at: datetime = Field(default_factory=datetime.now, description="Létrehozás időpontja")
    updated_at: datetime = Field(default_factory=datetime.now, description="Utolsó frissítés")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class SMSTemplate(BaseModel):
    """SMS template modell"""
    id: str = Field(..., description="Template azonosító")
    name: str = Field(..., min_length=1, description="Template neve")
    content: str = Field(..., min_length=1, max_length=160, description="SMS tartalom")
    template_type: TemplateType = Field(default=TemplateType.SMS, description="Template típusa")
    campaign_type: Optional[CampaignType] = Field(default=None, description="Kampány típusa")
    variables: List[str] = Field(default_factory=list, description="Template változók")
    is_active: bool = Field(default=True, description="Template aktív")
    is_default: bool = Field(default=False, description="Alapértelmezett template")
    language: str = Field(default="hu", description="Nyelv")
    category: Optional[str] = Field(default=None, description="Kategória")
    tags: List[str] = Field(default_factory=list, description="Címkék")
    usage_count: int = Field(default=0, description="Használatok száma")
    success_rate: float = Field(default=1.0, ge=0.0, le=1.0, description="Siker arány")
    delivery_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Kézbesítési arány")
    created_at: datetime = Field(default_factory=datetime.now, description="Létrehozás időpontja")
    updated_at: datetime = Field(default_factory=datetime.now, description="Utolsó frissítés")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class Campaign(BaseModel):
    """Marketing kampány modell"""
    id: str = Field(..., description="Kampány azonosító")
    name: str = Field(..., min_length=1, description="Kampány neve")
    description: Optional[str] = Field(default=None, description="Kampány leírása")
    campaign_type: CampaignType = Field(..., description="Kampány típusa")
    status: CampaignStatus = Field(default=CampaignStatus.DRAFT, description="Kampány státusz")
    template_id: str = Field(..., description="Template azonosító")
    template_type: TemplateType = Field(..., description="Template típusa")
    target_audience: Dict[str, Any] = Field(default_factory=dict, description="Célközönség")
    trigger_conditions: Dict[str, Any] = Field(default_factory=dict, description="Indító feltételek")
    schedule: Optional[Dict[str, Any]] = Field(default=None, description="Ütemezés")
    channels: List[str] = Field(default_factory=list, description="Csatornák")
    subject_line: Optional[str] = Field(default=None, description="Email tárgy")
    preview_text: Optional[str] = Field(default=None, description="Előnézet szöveg")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Kampány változók")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Kampány beállítások")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Kampány metrikák")
    is_active: bool = Field(default=True, description="Kampány aktív")
    created_at: datetime = Field(default_factory=datetime.now, description="Létrehozás időpontja")
    updated_at: datetime = Field(default_factory=datetime.now, description="Utolsó frissítés")
    scheduled_at: Optional[datetime] = Field(default=None, description="Ütemezett időpont")
    started_at: Optional[datetime] = Field(default=None, description="Kezdési időpont")
    ended_at: Optional[datetime] = Field(default=None, description="Befejezési időpont")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class AbandonedCart(BaseModel):
    """Kosárelhagyás modell"""
    id: str = Field(..., description="Kosárelhagyás azonosító")
    user_id: str = Field(..., description="Felhasználói azonosító")
    session_id: str = Field(..., description="Session azonosító")
    cart_items: List[Dict[str, Any]] = Field(default_factory=list, description="Kosár tételek")
    total_value: float = Field(..., ge=0, description="Kosár értéke")
    currency: str = Field(default="HUF", description="Pénznem")
    abandoned_at: datetime = Field(default_factory=datetime.now, description="Elhagyás időpontja")
    follow_up_sent: bool = Field(default=False, description="Follow-up elküldve")
    follow_up_count: int = Field(default=0, description="Follow-up számláló")
    last_follow_up: Optional[datetime] = Field(default=None, description="Utolsó follow-up")
    recovered: bool = Field(default=False, description="Visszahívva")
    recovered_at: Optional[datetime] = Field(default=None, description="Visszahívás időpontja")
    discount_code: Optional[str] = Field(default=None, description="Kedvezmény kód")
    discount_percentage: Optional[int] = Field(default=None, ge=0, le=100, description="Kedvezmény százalék")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="További adatok")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class MarketingMessage(BaseModel):
    """Marketing üzenet modell"""
    id: str = Field(..., description="Üzenet azonosító")
    campaign_id: str = Field(..., description="Kampány azonosító")
    user_id: str = Field(..., description="Felhasználói azonosító")
    template_id: str = Field(..., description="Template azonosító")
    channel: str = Field(..., description="Csatorna")
    subject: Optional[str] = Field(default=None, description="Tárgy")
    content: str = Field(..., description="Tartalom")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Üzenet változók")
    status: str = Field(default="pending", description="Üzenet státusz")
    scheduled_at: Optional[datetime] = Field(default=None, description="Ütemezett időpont")
    sent_at: Optional[datetime] = Field(default=None, description="Elküldés időpontja")
    delivered_at: Optional[datetime] = Field(default=None, description="Kézbesítés időpontja")
    opened_at: Optional[datetime] = Field(default=None, description="Megnyitás időpontja")
    clicked_at: Optional[datetime] = Field(default=None, description="Kattintás időpontja")
    bounce_reason: Optional[str] = Field(default=None, description="Visszapattanás oka")
    error_message: Optional[str] = Field(default=None, description="Hiba üzenet")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="További adatok")
    created_at: datetime = Field(default_factory=datetime.now, description="Létrehozás időpontja")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class DiscountCode(BaseModel):
    """Kedvezmény kód modell"""
    id: str = Field(..., description="Kedvezmény azonosító")
    code: str = Field(..., min_length=3, description="Kedvezmény kód")
    type: str = Field(..., description="Kedvezmény típusa (percentage/fixed)")
    value: float = Field(..., ge=0, description="Kedvezmény értéke")
    currency: str = Field(default="HUF", description="Pénznem")
    minimum_order_value: Optional[float] = Field(default=None, ge=0, description="Minimum rendelési érték")
    maximum_discount: Optional[float] = Field(default=None, ge=0, description="Maximum kedvezmény")
    usage_limit: Optional[int] = Field(default=None, ge=1, description="Használati limit")
    used_count: int = Field(default=0, description="Használatok száma")
    user_limit: Optional[int] = Field(default=None, ge=1, description="Felhasználónkénti limit")
    valid_from: datetime = Field(..., description="Érvényesség kezdete")
    valid_until: datetime = Field(..., description="Érvényesség vége")
    is_active: bool = Field(default=True, description="Kedvezmény aktív")
    is_single_use: bool = Field(default=False, description="Egyszeri használat")
    applicable_products: List[str] = Field(default_factory=list, description="Alkalmazható termékek")
    excluded_products: List[str] = Field(default_factory=list, description="Kizárt termékek")
    applicable_categories: List[str] = Field(default_factory=list, description="Alkalmazható kategóriák")
    excluded_categories: List[str] = Field(default_factory=list, description="Kizárt kategóriák")
    campaign_id: Optional[str] = Field(default=None, description="Kampány azonosító")
    created_at: datetime = Field(default_factory=datetime.now, description="Létrehozás időpontja")
    updated_at: datetime = Field(default_factory=datetime.now, description="Utolsó frissítés")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class MarketingMetrics(BaseModel):
    """Marketing metrikák modell"""
    campaign_id: str = Field(..., description="Kampány azonosító")
    date: datetime = Field(..., description="Dátum")
    messages_sent: int = Field(default=0, description="Elküldött üzenetek")
    messages_delivered: int = Field(default=0, description="Kézbesített üzenetek")
    messages_opened: int = Field(default=0, description="Megnyitott üzenetek")
    messages_clicked: int = Field(default=0, description="Kattintott üzenetek")
    messages_bounced: int = Field(default=0, description="Visszapattant üzenetek")
    messages_failed: int = Field(default=0, description="Sikertelen üzenetek")
    unsubscribed: int = Field(default=0, description="Leiratkozások")
    complaints: int = Field(default=0, description="Panaszok")
    revenue_generated: float = Field(default=0.0, description="Generált bevétel")
    orders_generated: int = Field(default=0, description="Generált rendelések")
    conversion_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Konverziós arány")
    open_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Megnyitási arány")
    click_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Kattintási arány")
    bounce_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Visszapattanási arány")
    created_at: datetime = Field(default_factory=datetime.now, description="Létrehozás időpontja")
    
    model_config = ConfigDict(
        validate_assignment=True
    ) 