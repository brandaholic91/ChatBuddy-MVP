"""
User models for Chatbuddy MVP.

This module contains Pydantic models for user management:
- User: Basic user information
- UserProfile: Extended user profile
- UserPreferences: User preferences and settings
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, EmailStr


class UserRole(str, Enum):
    """Felhasználói szerepkörök"""
    CUSTOMER = "customer"
    ADMIN = "admin"
    SUPPORT = "support"
    AGENT = "agent"


class UserStatus(str, Enum):
    """Felhasználói státuszok"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(BaseModel):
    """Alapvető felhasználói modell"""
    id: str = Field(..., description="Egyedi felhasználói azonosító")
    email: EmailStr = Field(..., description="Felhasználó email címe")
    name: Optional[str] = Field(default=None, description="Felhasználó neve")
    role: UserRole = Field(default=UserRole.CUSTOMER, description="Felhasználói szerepkör")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="Felhasználói státusz")
    created_at: datetime = Field(default_factory=datetime.now, description="Regisztráció időpontja")
    last_login: Optional[datetime] = Field(default=None, description="Utolsó bejelentkezés")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="További felhasználói adatok")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class UserProfile(BaseModel):
    """Kiterjesztett felhasználói profil"""
    user_id: str = Field(..., description="Felhasználói azonosító")
    phone: Optional[str] = Field(default=None, description="Telefonszám")
    address: Optional[str] = Field(default=None, description="Cím")
    city: Optional[str] = Field(default=None, description="Város")
    postal_code: Optional[str] = Field(default=None, description="Irányítószám")
    country: Optional[str] = Field(default="Hungary", description="Ország")
    birth_date: Optional[datetime] = Field(default=None, description="Születési dátum")
    gender: Optional[str] = Field(default=None, description="Nem")
    language: str = Field(default="hu", description="Nyelv")
    timezone: str = Field(default="Europe/Budapest", description="Időzóna")
    avatar_url: Optional[str] = Field(default=None, description="Profilkép URL")
    bio: Optional[str] = Field(default=None, description="Rövid leírás")
    updated_at: datetime = Field(default_factory=datetime.now, description="Utolsó frissítés")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class UserPreferences(BaseModel):
    """Felhasználói preferenciák"""
    user_id: str = Field(..., description="Felhasználói azonosító")
    notification_email: bool = Field(default=True, description="Email értesítések")
    notification_sms: bool = Field(default=False, description="SMS értesítések")
    notification_push: bool = Field(default=True, description="Push értesítések")
    marketing_emails: bool = Field(default=True, description="Marketing email-ek")
    newsletter: bool = Field(default=False, description="Hírlevél feliratkozás")
    chat_history: bool = Field(default=True, description="Chat történet mentése")
    auto_save_cart: bool = Field(default=True, description="Kosár automatikus mentése")
    product_recommendations: bool = Field(default=True, description="Termékajánlások")
    personalized_offers: bool = Field(default=True, description="Személyre szabott ajánlatok")
    theme: str = Field(default="light", description="Téma (light/dark)")
    language: str = Field(default="hu", description="Nyelv")
    currency: str = Field(default="HUF", description="Pénznem")
    updated_at: datetime = Field(default_factory=datetime.now, description="Utolsó frissítés")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class UserSession(BaseModel):
    """Felhasználói session információk"""
    session_id: str = Field(..., description="Session azonosító")
    user_id: str = Field(..., description="Felhasználói azonosító")
    device_info: Optional[Dict[str, Any]] = Field(default=None, description="Eszköz információk")
    ip_address: Optional[str] = Field(default=None, description="IP cím")
    user_agent: Optional[str] = Field(default=None, description="User agent")
    started_at: datetime = Field(default_factory=datetime.now, description="Session kezdete")
    last_activity: datetime = Field(default_factory=datetime.now, description="Utolsó aktivitás")
    is_active: bool = Field(default=True, description="Session aktív")
    expires_at: Optional[datetime] = Field(default=None, description="Session lejárat")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class UserActivity(BaseModel):
    """Felhasználói aktivitás napló"""
    id: str = Field(..., description="Aktivitás azonosító")
    user_id: str = Field(..., description="Felhasználói azonosító")
    activity_type: str = Field(..., description="Aktivitás típusa")
    description: str = Field(..., description="Aktivitás leírása")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="További adatok")
    timestamp: datetime = Field(default_factory=datetime.now, description="Aktivitás időpontja")
    session_id: Optional[str] = Field(default=None, description="Session azonosító")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class UserAuth(BaseModel):
    """Felhasználói autentikáció"""
    user_id: str = Field(..., description="Felhasználói azonosító")
    password_hash: str = Field(..., description="Jelszó hash")
    salt: str = Field(..., description="Salt érték")
    reset_token: Optional[str] = Field(default=None, description="Jelszó visszaállítás token")
    reset_expires: Optional[datetime] = Field(default=None, description="Token lejárat")
    failed_attempts: int = Field(default=0, description="Sikertelen bejelentkezési kísérletek")
    locked_until: Optional[datetime] = Field(default=None, description="Fiók zárolás ideje")
    last_password_change: datetime = Field(default_factory=datetime.now, description="Utolsó jelszóváltoztatás")
    
    model_config = ConfigDict(
        validate_assignment=True
    ) 