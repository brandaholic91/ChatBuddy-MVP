"""
Data models for Chatbuddy MVP.

This module contains Pydantic models for type-safe data handling:
- Chat messages and sessions
- User profiles and authentication
- Product information and categories
- Order management and tracking
- Agent responses and decisions
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Chat models
    from .chat import ChatMessage, ChatSession, ChatState
    
    # User models  
    from .user import User, UserProfile, UserPreferences
    
    # Product models
    from .product import Product, ProductCategory, ProductInfo
    
    # Order models
    from .order import Order, OrderStatus, OrderItem
    
    # Agent models
    from .agent import AgentDecision, AgentResponse, AgentState
    
    # Marketing models
    from .marketing import EmailTemplate, SMSTemplate, Campaign

# Placeholder exports for now
ChatMessage = None
ChatSession = None
ChatState = None
User = None
UserProfile = None
UserPreferences = None
Product = None
ProductCategory = None
ProductInfo = None
Order = None
OrderStatus = None
OrderItem = None
AgentDecision = None
AgentResponse = None
AgentState = None
EmailTemplate = None
SMSTemplate = None
Campaign = None

__all__ = [
    # Chat models
    "ChatMessage",
    "ChatSession", 
    "ChatState",
    
    # User models
    "User",
    "UserProfile",
    "UserPreferences",
    
    # Product models
    "Product",
    "ProductCategory",
    "ProductInfo",
    
    # Order models
    "Order",
    "OrderStatus",
    "OrderItem",
    
    # Agent models
    "AgentDecision",
    "AgentResponse",
    "AgentState",
    
    # Marketing models
    "EmailTemplate",
    "SMSTemplate",
    "Campaign"
]
