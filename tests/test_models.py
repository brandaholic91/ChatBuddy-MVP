"""
Tests for Chatbuddy MVP data models.

This module contains tests for all Pydantic models to ensure they work correctly.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from src.models import (
    # Chat models
    ChatMessage, ChatSession, ChatState, ChatRequest, ChatResponse, MessageType,
    # User models
    User, UserProfile, UserPreferences, UserRole, UserStatus,
    # Product models
    Product, ProductCategory, ProductInfo, ProductStatus, ProductType,
    # Order models
    Order, OrderItem, OrderStatus, PaymentStatus, PaymentMethod, ShippingMethod,
    # Agent models
    AgentDecision, AgentResponse, AgentState, AgentType, AgentStatus, DecisionType,
    # Marketing models
    EmailTemplate, SMSTemplate, Campaign, TemplateType, CampaignType, CampaignStatus
)


class TestChatModels:
    """Tests for chat-related models."""
    
    def test_chat_message_creation(self):
        """Test ChatMessage model creation."""
        message = ChatMessage(
            id="msg_123",
            session_id="session_456",
            type=MessageType.USER,
            content="Szia! Keresek egy telefont."
        )
        
        assert message.id == "msg_123"
        assert message.session_id == "session_456"
        assert message.type == MessageType.USER
        assert message.content == "Szia! Keresek egy telefont."
        assert isinstance(message.timestamp, datetime)
    
    def test_chat_session_creation(self):
        """Test ChatSession model creation."""
        session = ChatSession(
            session_id="session_123",
            user_id="user_456"
        )
        
        assert session.session_id == "session_123"
        assert session.user_id == "user_456"
        assert session.is_active is True
        assert isinstance(session.started_at, datetime)
    
    def test_chat_request_creation(self):
        """Test ChatRequest model creation."""
        request = ChatRequest(
            session_id="session_123",
            message="Keresek egy telefont",
            user_id="user_456"
        )
        
        assert request.session_id == "session_123"
        assert request.message == "Keresek egy telefont"
        assert request.user_id == "user_456"


class TestUserModels:
    """Tests for user-related models."""
    
    def test_user_creation(self):
        """Test User model creation."""
        user = User(
            id="user_123",
            email="test@example.com",
            name="Teszt Felhasználó",
            role=UserRole.CUSTOMER
        )
        
        assert user.id == "user_123"
        assert user.email == "test@example.com"
        assert user.name == "Teszt Felhasználó"
        assert user.role == UserRole.CUSTOMER
        assert user.status == UserStatus.ACTIVE
    
    def test_user_profile_creation(self):
        """Test UserProfile model creation."""
        profile = UserProfile(
            user_id="user_123",
            phone="+36123456789",
            city="Budapest",
            language="hu"
        )
        
        assert profile.user_id == "user_123"
        assert profile.phone == "+36123456789"
        assert profile.city == "Budapest"
        assert profile.language == "hu"
        assert profile.country == "Hungary"


class TestProductModels:
    """Tests for product-related models."""
    
    def test_product_creation(self):
        """Test Product model creation."""
        product = Product(
            id="prod_123",
            name="iPhone 15 Pro",
            description="Apple iPhone 15 Pro 128GB",
            price=Decimal("299000"),
            category_id="cat_phones",
            brand="Apple",
            sku="IPHONE15PRO128"
        )
        
        assert product.id == "prod_123"
        assert product.name == "iPhone 15 Pro"
        assert product.price == Decimal("299000")
        assert product.currency == "HUF"
        assert product.status == ProductStatus.ACTIVE
        assert product.product_type == ProductType.PHYSICAL
    
    def test_product_category_creation(self):
        """Test ProductCategory model creation."""
        category = ProductCategory(
            id="cat_phones",
            name="Telefonok",
            description="Mobiltelefonok és okostelefonok",
            slug="telefonok",
            level=0
        )
        
        assert category.id == "cat_phones"
        assert category.name == "Telefonok"
        assert category.slug == "telefonok"
        assert category.is_active is True


class TestOrderModels:
    """Tests for order-related models."""
    
    def test_order_creation(self):
        """Test Order model creation."""
        order = Order(
            id="order_123",
            order_number="ORD-2024-001",
            user_id="user_456",
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            subtotal=Decimal("299000"),
            total_amount=Decimal("299000"),
            currency="HUF"
        )
        
        assert order.id == "order_123"
        assert order.order_number == "ORD-2024-001"
        assert order.status == OrderStatus.PENDING
        assert order.total_amount == Decimal("299000")
    
    def test_order_item_creation(self):
        """Test OrderItem model creation."""
        item = OrderItem(
            id="item_123",
            order_id="order_456",
            product_id="prod_789",
            product_name="iPhone 15 Pro",
            quantity=1,
            unit_price=Decimal("299000"),
            total_price=Decimal("299000")
        )
        
        assert item.id == "item_123"
        assert item.order_id == "order_456"
        assert item.product_name == "iPhone 15 Pro"
        assert item.quantity == 1
        assert item.total_price == Decimal("299000")


class TestAgentModels:
    """Tests for agent-related models."""
    
    def test_agent_decision_creation(self):
        """Test AgentDecision model creation."""
        decision = AgentDecision(
            agent_type=AgentType.COORDINATOR,
            decision_type=DecisionType.ROUTE_TO_AGENT,
            target_agent=AgentType.PRODUCT_INFO,
            confidence=0.95,
            reasoning="A felhasználó termékeket keres, irányítom a termék agent-hez."
        )
        
        assert decision.agent_type == AgentType.COORDINATOR
        assert decision.decision_type == DecisionType.ROUTE_TO_AGENT
        assert decision.target_agent == AgentType.PRODUCT_INFO
        assert decision.confidence == 0.95
    
    def test_agent_response_creation(self):
        """Test AgentResponse model creation."""
        response = AgentResponse(
            agent_type=AgentType.PRODUCT_INFO,
            response_text="Találtam néhány telefont, ami megfelelhet az igényeinek.",
            confidence=0.9,
            response_type="text"
        )
        
        assert response.agent_type == AgentType.PRODUCT_INFO
        assert "telefont" in response.response_text
        assert response.confidence == 0.9


class TestMarketingModels:
    """Tests for marketing-related models."""
    
    def test_email_template_creation(self):
        """Test EmailTemplate model creation."""
        template = EmailTemplate(
            id="template_123",
            name="Kosárelhagyás emlékeztető",
            subject="Visszahívjuk a kosarát!",
            html_content="<h1>Visszahívjuk a kosarát!</h1>",
            template_type=TemplateType.EMAIL,
            campaign_type=CampaignType.ABANDONED_CART
        )
        
        assert template.id == "template_123"
        assert template.name == "Kosárelhagyás emlékeztető"
        assert template.template_type == TemplateType.EMAIL
        assert template.campaign_type == CampaignType.ABANDONED_CART
    
    def test_sms_template_creation(self):
        """Test SMSTemplate model creation."""
        template = SMSTemplate(
            id="sms_template_123",
            name="Kosárelhagyás SMS",
            content="Visszahívjuk a kosarát! 10% kedvezmény: KOSAR10",
            template_type=TemplateType.SMS
        )
        
        assert template.id == "sms_template_123"
        assert len(template.content) <= 160  # SMS hossz korlátozás
        assert template.template_type == TemplateType.SMS
    
    def test_campaign_creation(self):
        """Test Campaign model creation."""
        campaign = Campaign(
            id="campaign_123",
            name="Kosárelhagyás Follow-up",
            campaign_type=CampaignType.ABANDONED_CART,
            status=CampaignStatus.ACTIVE,
            template_id="template_456",
            template_type=TemplateType.EMAIL,
            channels=["email", "sms"]
        )
        
        assert campaign.id == "campaign_123"
        assert campaign.campaign_type == CampaignType.ABANDONED_CART
        assert campaign.status == CampaignStatus.ACTIVE
        assert "email" in campaign.channels


class TestModelValidation:
    """Tests for model validation."""
    
    def test_chat_message_validation(self):
        """Test ChatMessage validation."""
        # Valid message
        message = ChatMessage(
            id="msg_123",
            session_id="session_456",
            type=MessageType.USER,
            content="Szia!"
        )
        assert message.content == "Szia!"
        
        # Invalid: empty content
        with pytest.raises(ValueError):
            ChatMessage(
                id="msg_123",
                session_id="session_456",
                type=MessageType.USER,
                content=""
            )
    
    def test_product_price_validation(self):
        """Test Product price validation."""
        # Valid price
        product = Product(
            id="prod_123",
            name="Test Product",
            price=Decimal("1000")
        )
        assert product.price == Decimal("1000")
        
        # Invalid: negative price
        with pytest.raises(ValueError):
            Product(
                id="prod_123",
                name="Test Product",
                price=Decimal("-100")
            )
    
    def test_agent_confidence_validation(self):
        """Test AgentDecision confidence validation."""
        # Valid confidence
        decision = AgentDecision(
            agent_type=AgentType.COORDINATOR,
            decision_type=DecisionType.ROUTE_TO_AGENT,
            target_agent=AgentType.PRODUCT_INFO,
            confidence=0.8,
            reasoning="Test reasoning"
        )
        assert decision.confidence == 0.8
        
        # Invalid: confidence > 1.0
        with pytest.raises(ValueError):
            AgentDecision(
                agent_type=AgentType.COORDINATOR,
                decision_type=DecisionType.ROUTE_TO_AGENT,
                target_agent=AgentType.PRODUCT_INFO,
                confidence=1.5,
                reasoning="Test reasoning"
            )


class TestModelSerialization:
    """Tests for model serialization."""
    
    def test_chat_message_serialization(self):
        """Test ChatMessage serialization."""
        message = ChatMessage(
            id="msg_123",
            session_id="session_456",
            type=MessageType.USER,
            content="Test message"
        )
        
        # Test to dict
        message_dict = message.model_dump()
        assert message_dict["id"] == "msg_123"
        assert message_dict["content"] == "Test message"
        assert message_dict["type"] == "user"
        
        # Test to JSON
        message_json = message.model_dump_json()
        assert "msg_123" in message_json
        assert "Test message" in message_json
    
    def test_product_serialization(self):
        """Test Product serialization."""
        product = Product(
            id="prod_123",
            name="Test Product",
            price=Decimal("1000"),
            currency="HUF"
        )
        
        # Test to dict
        product_dict = product.model_dump()
        assert product_dict["id"] == "prod_123"
        assert product_dict["price"] == Decimal("1000")  # Decimal remains as Decimal
        assert product_dict["currency"] == "HUF"


if __name__ == "__main__":
    pytest.main([__file__]) 