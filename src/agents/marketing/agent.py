"""
Marketing Agent - Pydantic AI Tool Implementation for LangGraph.

This module implements the marketing agent as a Pydantic AI tool
that can be integrated into the LangGraph workflow.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from ...models.agent import AgentType


@dataclass
class MarketingDependencies:
    """Marketing agent függőségei."""
    user_context: Dict[str, Any]
    supabase_client: Optional[Any] = None
    webshop_api: Optional[Any] = None
    security_context: Optional[Any] = None
    audit_logger: Optional[Any] = None


class Promotion(BaseModel):
    """Promóció struktúra."""
    promotion_id: str = Field(description="Promóció azonosító")
    name: str = Field(description="Promóció neve")
    description: str = Field(description="Promóció leírása")
    discount_percentage: float = Field(description="Kedvezmény százalék")
    valid_from: str = Field(description="Érvényesség kezdete")
    valid_until: str = Field(description="Érvényesség vége")
    minimum_purchase: float = Field(description="Minimum vásárlási érték")
    applicable_categories: List[str] = Field(description="Alkalmazható kategóriák")
    code: str = Field(description="Kupon kód")


class Newsletter(BaseModel):
    """Hírlevél struktúra."""
    newsletter_id: str = Field(description="Hírlevél azonosító")
    name: str = Field(description="Hírlevél neve")
    description: str = Field(description="Hírlevél leírása")
    frequency: str = Field(description="Küldési gyakoriság")
    categories: List[str] = Field(description="Érdeklődési körök")
    is_active: bool = Field(description="Aktív hírlevél")


class MarketingResponse(BaseModel):
    """Marketing agent válasz struktúra."""
    response_text: str = Field(description="Agent válasza")
    confidence: float = Field(description="Bizonyosság", ge=0.0, le=1.0)
    promotions: List[Promotion] = Field(description="Aktív promóciók", default_factory=list)
    newsletters: List[Newsletter] = Field(description="Elérhető hírlevelek", default_factory=list)
    personalized_offers: Dict[str, Any] = Field(description="Személyre szabott ajánlatok", default_factory=dict)
    metadata: Dict[str, Any] = Field(description="Metaadatok", default_factory=dict)


def create_marketing_agent() -> Agent:
    """
    Marketing agent létrehozása Pydantic AI-val.
    
    Returns:
        Marketing agent
    """
    agent = Agent(
        'openai:gpt-4o',
        deps_type=MarketingDependencies,
        output_type=MarketingResponse,
        system_prompt=(
            "Te egy marketing ügynök vagy a ChatBuddy webshop chatbot-ban. "
            "Feladatod a promóciók, kedvezmények és hírlevelek kezelése. "
            "Válaszolj magyarul, barátságosan és vonzóan. "
            "Használd a megfelelő tool-okat a marketing információk lekéréséhez. "
            "Mindig tartsd szem előtt a GDPR megfelelőséget és a marketing hozzájárulásokat. "
            "Ne küldj marketing tartalmat hozzájárulás nélkül."
        )
    )
    
    @agent.tool
    async def get_active_promotions(
        ctx: RunContext[MarketingDependencies],
        category: Optional[str] = None
    ) -> List[Promotion]:
        """
        Aktív promóciók lekérése.
        
        Args:
            category: Kategória (opcionális)
            
        Returns:
            Aktív promóciók
        """
        try:
            # Mock implementation for development
            # TODO: Implement actual promotions retrieval
            
            # Mock active promotions
            active_promotions = [
                Promotion(
                    promotion_id="PROMO001",
                    name="Telefon kedvezmény",
                    description="20% kedvezmény minden telefonra",
                    discount_percentage=20.0,
                    valid_from="2024-12-01",
                    valid_until="2024-12-31",
                    minimum_purchase=100000.0,
                    applicable_categories=["Telefon"],
                    code="TELEFON20"
                ),
                Promotion(
                    promotion_id="PROMO002",
                    name="Laptop akció",
                    description="15% kedvezmény laptopokra",
                    discount_percentage=15.0,
                    valid_from="2024-12-15",
                    valid_until="2024-12-25",
                    minimum_purchase=200000.0,
                    applicable_categories=["Laptop"],
                    code="LAPTOP15"
                ),
                Promotion(
                    promotion_id="PROMO003",
                    name="Általános kedvezmény",
                    description="10% kedvezmény minden termékre",
                    discount_percentage=10.0,
                    valid_from="2024-12-01",
                    valid_until="2024-12-31",
                    minimum_purchase=50000.0,
                    applicable_categories=["Telefon", "Laptop", "Tablet", "Kiegészítő"],
                    code="MINDEN10"
                )
            ]
            
            # Filter by category if specified
            if category:
                active_promotions = [
                    p for p in active_promotions 
                    if category in p.applicable_categories
                ]
            
            return active_promotions
            
        except Exception as e:
            # Return empty list on error
            return []
    
    @agent.tool
    async def get_available_newsletters(
        ctx: RunContext[MarketingDependencies]
    ) -> List[Newsletter]:
        """
        Elérhető hírlevelek lekérése.
        
        Returns:
            Elérhető hírlevelek
        """
        try:
            # Mock implementation for development
            # TODO: Implement actual newsletters retrieval
            
            # Mock available newsletters
            newsletters = [
                Newsletter(
                    newsletter_id="NEWS001",
                    name="Technológiai hírek",
                    description="A legfrissebb technológiai hírek és trendek",
                    frequency="hetente",
                    categories=["technológia", "hírek"],
                    is_active=True
                ),
                Newsletter(
                    newsletter_id="NEWS002",
                    name="Kedvezmények és akciók",
                    description="Exkluzív kedvezmények és promóciók",
                    frequency="havonta",
                    categories=["kedvezmények", "akciók"],
                    is_active=True
                ),
                Newsletter(
                    newsletter_id="NEWS003",
                    name="Új termékek",
                    description="Új termékek és bemutatók",
                    frequency="havonta",
                    categories=["új termékek", "bemutatók"],
                    is_active=True
                )
            ]
            
            return newsletters
            
        except Exception as e:
            # Return empty list on error
            return []
    
    @agent.tool
    async def get_personalized_offers(
        ctx: RunContext[MarketingDependencies]
    ) -> Dict[str, Any]:
        """
        Személyre szabott ajánlatok lekérése.
        
        Returns:
            Személyre szabott ajánlatok
        """
        try:
            # Mock implementation for development
            # TODO: Implement actual personalized offers retrieval
            
            user_id = ctx.deps.user_context.get("user_id", "anonymous")
            
            # Mock personalized offers
            personalized_offers = {
                "special_discount": "VIP10",
                "discount_percentage": 10.0,
                "valid_until": "2024-12-31",
                "recommended_products": [
                    {
                        "product_id": "PHONE_001",
                        "name": "iPhone 15 Pro",
                        "discount": 50000.0
                    }
                ],
                "loyalty_points": 1500,
                "next_reward": "Ingyenes szállítás"
            }
            
            return personalized_offers
            
        except Exception as e:
            # Return empty offers on error
            return {}
    
    @agent.tool
    async def check_marketing_consent(
        ctx: RunContext[MarketingDependencies]
    ) -> bool:
        """
        Marketing hozzájárulás ellenőrzése.
        
        Returns:
            True ha van hozzájárulás, False ha nincs
        """
        try:
            # Mock implementation for development
            # TODO: Implement actual consent checking
            
            user_id = ctx.deps.user_context.get("user_id", "anonymous")
            
            # Mock consent status
            # In a real implementation, this would check the user's consent status
            return True
            
        except Exception as e:
            # Return False on error (fail safe)
            return False
    
    @agent.tool
    async def subscribe_to_newsletter(
        ctx: RunContext[MarketingDependencies],
        newsletter_id: str
    ) -> Dict[str, Any]:
        """
        Hírlevél feliratkozás.
        
        Args:
            newsletter_id: Hírlevél azonosító
            
        Returns:
            Feliratkozás eredménye
        """
        try:
            # Mock implementation for development
            # TODO: Implement actual newsletter subscription
            
            user_id = ctx.deps.user_context.get("user_id", "anonymous")
            
            # Mock subscription result
            result = {
                "success": True,
                "newsletter_id": newsletter_id,
                "subscription_date": "2024-12-19",
                "message": "Sikeresen feliratkoztál a hírlevélre!"
            }
            
            return result
            
        except Exception as e:
            # Return error result
            return {
                "success": False,
                "error": str(e),
                "message": "Hiba történt a feliratkozás során."
            }
    
    return agent


# Convenience function for LangGraph integration
async def call_marketing_agent(
    message: str,
    dependencies: MarketingDependencies
) -> MarketingResponse:
    """
    Marketing agent hívása LangGraph workflow-ból.
    
    Args:
        message: Felhasználói üzenet
        dependencies: Agent függőségek
        
    Returns:
        Marketing agent válasz
    """
    agent = create_marketing_agent()
    result = await agent.run(message, deps=dependencies)
    return result.output 