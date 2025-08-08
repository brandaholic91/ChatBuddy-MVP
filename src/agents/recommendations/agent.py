"""
Recommendations Agent - Pydantic AI Tool Implementation for LangGraph.

This module implements the recommendations agent as a Pydantic AI tool
that can be integrated into the LangGraph workflow.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.test import TestModel

from ...models.agent import AgentType, AgentResponse


@dataclass
class RecommendationDependencies:
    """Recommendations agent függőségei."""
    user_context: Dict[str, Any]
    supabase_client: Optional[Any] = None
    webshop_api: Optional[Any] = None
    security_context: Optional[Any] = None
    audit_logger: Optional[Any] = None


class ProductRecommendation(BaseModel):
    """Termék ajánlás struktúra."""
    product_id: str = Field(description="Termék azonosító")
    name: str = Field(description="Termék neve")
    price: float = Field(description="Termék ára")
    description: str = Field(description="Termék leírása")
    category: str = Field(description="Kategória")
    rating: float = Field(description="Értékelés", ge=0.0, le=5.0)
    review_count: int = Field(description="Értékelések száma")
    image_url: str = Field(description="Termék kép URL")
    recommendation_reason: str = Field(description="Ajánlás indoka")
    confidence_score: float = Field(description="Ajánlás bizonyossága", ge=0.0, le=1.0)


class RecommendationResponse(BaseModel):
    """Recommendations agent válasz struktúra."""
    response_text: str = Field(description="Agent válasza")
    confidence: float = Field(description="Bizonyosság", ge=0.0, le=1.0)
    recommendations: List[ProductRecommendation] = Field(description="Termék ajánlások", default_factory=list)
    category: Optional[str] = Field(default=None, description="Ajánlás kategóriája")
    user_preferences: Dict[str, Any] = Field(description="Felhasználói preferenciák", default_factory=dict)
    popular_products: List[Dict[str, Any]] = Field(description="Népszerű termékek", default_factory=list)
    similar_products: List[Dict[str, Any]] = Field(description="Hasonló termékek", default_factory=list)
    trending_products: List[Dict[str, Any]] = Field(description="Trending termékek", default_factory=list)
    metadata: Dict[str, Any] = Field(description="Metaadatok", default_factory=dict)


class RecommendationAgentWrapper:
    """
    Wrapper class for Pydantic AI Agent that provides the expected test interface.
    This maintains compatibility with existing test patterns while using Pydantic AI internally.
    """

    def __init__(self, pydantic_agent: Agent):
        self._pydantic_agent = pydantic_agent
        self._agent = pydantic_agent  # Compatibility alias for tests
        self.agent_type = AgentType.RECOMMENDATION
        # Return model name string for test compatibility
        self.model = 'openai:gpt-4o'

    async def run(self, message: str, user=None, session_id: str = None, audit_logger=None, **kwargs) -> AgentResponse:
        """
        Run the agent with the expected interface for tests.

        Args:
            message: User message
            user: User object
            session_id: Session identifier
            audit_logger: Audit logger instance
            **kwargs: Additional arguments

        Returns:
            AgentResponse compatible response
        """
        try:
            # Create dependencies
            dependencies = RecommendationDependencies(
                user_context={
                    "user_id": user.id if user else None,
                    "session_id": session_id,
                },
                audit_logger=audit_logger
            )

            # Run the Pydantic AI agent via alias
            result = await self._agent.run(message, deps=dependencies)

            output_obj = getattr(result, "output", result)
            response_text = getattr(output_obj, "response_text", None)
            if response_text is None:
                response_text = str(output_obj) if output_obj is not None else "OK"

            confidence = getattr(output_obj, "confidence", None)
            if confidence is None or confidence <= 0.0:
                confidence = 0.8

            agent_response = AgentResponse(
                agent_type=AgentType.RECOMMENDATION,
                response_text=response_text or "OK",
                confidence=confidence,
                suggested_actions=[],
                follow_up_questions=[],
                data_sources=[],
                metadata=getattr(output_obj, "metadata", {}) or {}
            )

            # Audit log on success if available
            if audit_logger:
                try:
                    await audit_logger.log_agent_interaction(
                        user_id=user.id if user else "anonymous",
                        agent_name=AgentType.RECOMMENDATION.value,
                        query=message,
                        response=agent_response.response_text,
                        session_id=session_id,
                        success=True
                    )
                except Exception:
                    pass

            return agent_response

        except Exception as e:
            # Error handling with expected format
            if audit_logger:
                try:
                    await audit_logger.log_agent_interaction(
                        user_id=user.id if user else "anonymous",
                        agent_name=AgentType.RECOMMENDATION.value,
                        query=message,
                        response=str(e),
                        session_id=session_id,
                        success=False
                    )
                    await audit_logger.log_error(
                        user_id=user.id if user else "anonymous",
                        message="Recommendation agent error",
                        details={"error": str(e)}
                    )
                except Exception:
                    pass

            return AgentResponse(
                agent_type=AgentType.RECOMMENDATION,
                response_text=f"Sajnálom, hiba történt az ajánlás generálásakor: {str(e)}",
                confidence=0.0,
                metadata={"error_type": type(e).__name__, "error": str(e)}
            )

    def override(self, **kwargs):
        """
        Override method for testing that returns the internal Pydantic AI agent's override.
        """
        return self._pydantic_agent.override(**kwargs)


# Global agent instance
_recommendation_agent = None

def create_recommendation_agent() -> RecommendationAgentWrapper:
    """
    Recommendations agent létrehozása Pydantic AI-val wrapped interface-szel.

    Returns:
        RecommendationAgentWrapper instance
    """
    global _recommendation_agent

    if _recommendation_agent is not None:
        return _recommendation_agent

    # Create the Pydantic AI agent
    pydantic_agent = Agent(
        'openai:gpt-4o',
        deps_type=RecommendationDependencies,
        output_type=RecommendationResponse,
        system_prompt=(
            "Te egy termék ajánló ügynök vagy a ChatBuddy webshop chatbot-ban. "
            "Feladatod a felhasználók számára személyre szabott termék ajánlások készítése. "
            "Válaszolj magyarul, barátságosan és részletesen. "
            "Használd a megfelelő tool-okat a termék ajánlások generálásához. "
            "Mindig tartsd szem előtt a felhasználói preferenciákat és a korábbi vásárlásokat. "
            "Mindig tartsd szem előtt a biztonsági protokollokat és a GDPR megfelelőséget."
        )
    )

    @pydantic_agent.tool
    async def get_user_preferences(
        ctx: RunContext[RecommendationDependencies]
    ) -> Dict[str, Any]:
        """
        Felhasználói preferenciák lekérése.

        Returns:
            Felhasználói preferenciák
        """
        try:
            # Mock implementation for development
            # TODO: Implement actual user preferences retrieval

            user_id = ctx.deps.user_context.get("user_id", "anonymous")

            # Mock user preferences
            preferences = {
                "preferred_categories": ["Telefon", "Laptop", "Tablet"],
                "price_range": {"min": 100000, "max": 500000},
                "brand_preferences": ["Apple", "Samsung", "Dell"],
                "previous_purchases": [
                    {"product_id": "PHONE_001", "category": "Telefon", "rating": 5},
                    {"product_id": "LAPTOP_001", "category": "Laptop", "rating": 4}
                ],
                "interests": ["technológia", "gaming", "munka"]
            }

            return preferences

        except Exception as e:
            # Return default preferences on error
            return {
                "preferred_categories": ["Telefon", "Laptop"],
                "price_range": {"min": 50000, "max": 1000000},
                "brand_preferences": [],
                "previous_purchases": [],
                "interests": []
            }

    @pydantic_agent.tool
    async def get_popular_products(
        ctx: RunContext[RecommendationDependencies],
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[ProductRecommendation]:
        """
        Népszerű termékek lekérése.

        Args:
            category: Kategória (opcionális)
            limit: Eredmények száma

        Returns:
            Népszerű termékek
        """
        try:
            # Mock implementation for development
            # TODO: Implement actual popular products retrieval

            # Mock popular products
            popular_products = [
                ProductRecommendation(
                    product_id="PHONE_001",
                    name="iPhone 15 Pro",
                    price=450000.0,
                    description="Apple iPhone 15 Pro 128GB Titanium",
                    category="Telefon",
                    rating=4.8,
                    review_count=156,
                    image_url="iphone15pro.jpg",
                    recommendation_reason="Népszerű és magas értékelésű telefon",
                    confidence_score=0.9
                ),
                ProductRecommendation(
                    product_id="LAPTOP_001",
                    name="MacBook Pro 14",
                    price=850000.0,
                    description="Apple MacBook Pro 14 inch M3 Pro",
                    category="Laptop",
                    rating=4.9,
                    review_count=89,
                    image_url="macbookpro14.jpg",
                    recommendation_reason="Professzionális laptop magas teljesítménnyel",
                    confidence_score=0.85
                ),
                ProductRecommendation(
                    product_id="TABLET_001",
                    name="iPad Pro 12.9",
                    price=380000.0,
                    description="Apple iPad Pro 12.9 inch M2",
                    category="Tablet",
                    rating=4.7,
                    review_count=67,
                    image_url="ipadpro12.jpg",
                    recommendation_reason="Prémium tablet kreatív munkához",
                    confidence_score=0.8
                )
            ]

            # Filter by category if specified
            if category:
                popular_products = [
                    p for p in popular_products
                    if category.lower() in p.category.lower()
                ]

            return popular_products[:limit]

        except Exception as e:
            # Return empty list on error
            return []

    @pydantic_agent.tool
    async def get_similar_products(
        ctx: RunContext[RecommendationDependencies],
        product_id: str,
        limit: int = 5
    ) -> List[ProductRecommendation]:
        """
        Hasonló termékek lekérése.

        Args:
            product_id: Termék azonosító
            limit: Eredmények száma

        Returns:
            Hasonló termékek
        """
        try:
            # Mock implementation for development
            # TODO: Implement actual similar products retrieval

            # Mock similar products based on product_id
            if "PHONE" in product_id:
                similar_products = [
                    ProductRecommendation(
                        product_id="PHONE_002",
                        name="Samsung Galaxy S24",
                        price=380000.0,
                        description="Samsung Galaxy S24 256GB Phantom Black",
                        category="Telefon",
                        rating=4.6,
                        review_count=89,
                        image_url="galaxys24.jpg",
                        recommendation_reason="Hasonló kategóriájú és árú telefon",
                        confidence_score=0.75
                    ),
                    ProductRecommendation(
                        product_id="PHONE_003",
                        name="Google Pixel 8 Pro",
                        price=420000.0,
                        description="Google Pixel 8 Pro 128GB Obsidian",
                        category="Telefon",
                        rating=4.5,
                        review_count=45,
                        image_url="pixel8pro.jpg",
                        recommendation_reason="Hasonló prémium telefon",
                        confidence_score=0.7
                    )
                ]
            else:
                similar_products = []

            return similar_products[:limit]

        except Exception as e:
            # Return empty list on error
            return []

    @pydantic_agent.tool
    async def get_trending_products(
        ctx: RunContext[RecommendationDependencies],
        limit: int = 10
    ) -> List[ProductRecommendation]:
        """
        Trendi termékek lekérése.

        Args:
            limit: Eredmények száma

        Returns:
            Trendi termékek
        """
        try:
            # Mock implementation for development
            # TODO: Implement actual trending products retrieval

            # Mock trending products
            trending_products = [
                ProductRecommendation(
                    product_id="WATCH_001",
                    name="Apple Watch Series 9",
                    price=180000.0,
                    description="Apple Watch Series 9 45mm GPS",
                    category="Okosóra",
                    rating=4.7,
                    review_count=123,
                    image_url="applewatch9.jpg",
                    recommendation_reason="Trendi okosóra magas értékeléssel",
                    confidence_score=0.85
                ),
                ProductRecommendation(
                    product_id="HEADPHONES_001",
                    name="AirPods Pro 2",
                    price=85000.0,
                    description="Apple AirPods Pro 2. generáció",
                    category="Fülhallgató",
                    rating=4.6,
                    review_count=234,
                    image_url="airpodspro2.jpg",
                    recommendation_reason="Népszerű vezetéknélküli fülhallgató",
                    confidence_score=0.8
                )
            ]

            return trending_products[:limit]

        except Exception as e:
            # Return empty list on error
            return []

    # Create wrapper instance
    wrapper = RecommendationAgentWrapper(pydantic_agent)

    # Store globally and return
    _recommendation_agent = wrapper
    return wrapper


# Convenience function for LangGraph integration
async def call_recommendation_agent(
    message: str,
    dependencies: RecommendationDependencies
) -> RecommendationResponse:
    """
    Recommendations agent hívása LangGraph workflow-ból.

    Args:
        message: Felhasználói üzenet
        dependencies: Agent függőségek

    Returns:
        Recommendations agent válasz
    """
    agent = create_recommendation_agent()
    result = await agent.run(message, deps=dependencies)
    return result.output
