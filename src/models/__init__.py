"""
Data models for Chatbuddy MVP.

This module contains Pydantic models for type-safe data handling:
- Chat messages and sessions
- User profiles and authentication
- Product information and categories
- Order management and tracking
- Agent responses and decisions
- Marketing automation
"""

# Chat models
from .chat import (
    ChatMessage,
    ChatSession,
    ChatState,
    ChatRequest,
    ChatResponse,
    WebSocketMessage,
    ChatError,
    MessageType
)

# User models
from .user import (
    User,
    UserProfile,
    UserPreferences,
    UserSession,
    UserActivity,
    UserAuth,
    UserRole,
    UserStatus
)

# Product models
from .product import (
    Product,
    ProductCategory,
    ProductInfo,
    ProductVariant,
    ProductReview,
    ProductSearch,
    ProductStatus,
    ProductType
)

# Order models
from .order import (
    Order,
    OrderItem,
    OrderStatusHistory,
    OrderPayment,
    OrderShipping,
    OrderRefund,
    OrderSearch,
    OrderStatus,
    PaymentStatus,
    PaymentMethod,
    ShippingMethod
)

# Agent models
from .agent import (
    AgentDecision,
    AgentResponse,
    AgentState,
    AgentTool,
    AgentConversation,
    AgentPerformance,
    AgentConfig,
    AgentType,
    AgentStatus,
    DecisionType
)

# Marketing models
from .marketing import (
    EmailTemplate,
    SMSTemplate,
    Campaign,
    AbandonedCart,
    MarketingMessage,
    DiscountCode,
    MarketingMetrics,
    TemplateType,
    CampaignType,
    CampaignStatus
)

__all__ = [
    # Chat models
    "ChatMessage",
    "ChatSession", 
    "ChatState",
    "ChatRequest",
    "ChatResponse",
    "WebSocketMessage",
    "ChatError",
    "MessageType",
    
    # User models
    "User",
    "UserProfile",
    "UserPreferences",
    "UserSession",
    "UserActivity",
    "UserAuth",
    "UserRole",
    "UserStatus",
    
    # Product models
    "Product",
    "ProductCategory",
    "ProductInfo",
    "ProductVariant",
    "ProductReview",
    "ProductSearch",
    "ProductStatus",
    "ProductType",
    
    # Order models
    "Order",
    "OrderItem",
    "OrderStatusHistory",
    "OrderPayment",
    "OrderShipping",
    "OrderRefund",
    "OrderSearch",
    "OrderStatus",
    "PaymentStatus",
    "PaymentMethod",
    "ShippingMethod",
    
    # Agent models
    "AgentDecision",
    "AgentResponse",
    "AgentState",
    "AgentTool",
    "AgentConversation",
    "AgentPerformance",
    "AgentConfig",
    "AgentType",
    "AgentStatus",
    "DecisionType",
    
    # Marketing models
    "EmailTemplate",
    "SMSTemplate",
    "Campaign",
    "AbandonedCart",
    "MarketingMessage",
    "DiscountCode",
    "MarketingMetrics",
    "TemplateType",
    "CampaignType",
    "CampaignStatus"
]
