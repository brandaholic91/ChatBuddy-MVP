"""
Order Status Agent - Pydantic AI Tool Implementation for LangGraph.

This module implements the order status agent as a Pydantic AI tool
that can be integrated into the LangGraph workflow.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from ...models.agent import AgentType


@dataclass
class OrderStatusDependencies:
    """Order status agent függőségei."""
    user_context: Dict[str, Any]
    supabase_client: Optional[Any] = None
    webshop_api: Optional[Any] = None
    security_context: Optional[Any] = None
    audit_logger: Optional[Any] = None


class OrderInfo(BaseModel):
    """Rendelés információs válasz struktúra."""
    order_id: str = Field(description="Rendelés azonosító")
    status: str = Field(description="Rendelés státusza")
    order_date: str = Field(description="Rendelés dátuma")
    estimated_delivery: str = Field(description="Várható szállítás")
    total_amount: float = Field(description="Összeg")
    items: List[Dict[str, Any]] = Field(description="Rendelt termékek", default_factory=list)
    shipping_address: Dict[str, Any] = Field(description="Szállítási cím", default_factory=dict)
    tracking_number: Optional[str] = Field(description="Követési szám", default=None)
    payment_status: str = Field(description="Fizetési státusz")


class OrderResponse(BaseModel):
    """Order agent válasz struktúra."""
    response_text: str = Field(description="Agent válasza")
    confidence: float = Field(description="Bizonyosság", ge=0.0, le=1.0)
    order_info: Optional[OrderInfo] = Field(description="Rendelés információ", default=None)
    status_summary: str = Field(description="Státusz összefoglaló")
    user_orders: List[Dict[str, Any]] = Field(description="Felhasználó rendelései", default_factory=list)
    tracking_info: Optional[Dict[str, Any]] = Field(description="Követési információ", default=None)
    next_steps: List[str] = Field(description="Következő lépések", default_factory=list)
    metadata: Dict[str, Any] = Field(description="Metaadatok", default_factory=dict)


def create_order_status_agent() -> Agent:
    """
    Order status agent létrehozása Pydantic AI-val.
    
    Returns:
        Order status agent
    """
    agent = Agent(
        'openai:gpt-4o',
        deps_type=OrderStatusDependencies,
        output_type=OrderResponse,
        system_prompt=(
            "Te egy rendelés követési ügynök vagy a ChatBuddy webshop chatbot-ban. "
            "Feladatod a rendelések státuszának lekérdezése és követése. "
            "Válaszolj magyarul, barátságosan és részletesen. "
            "Használd a megfelelő tool-okat a rendelés információk lekéréséhez. "
            "Ha nem találsz megfelelő rendelést, kérj el pontosabb információt. "
            "Mindig tartsd szem előtt a biztonsági protokollokat és a GDPR megfelelőséget. "
            "FONTOS: Mindig adj meg egy 'status_summary' mezőt a válaszodban!"
        )
    )
    
    @agent.tool
    async def get_order_by_id(
        ctx: RunContext[OrderStatusDependencies],
        order_id: str
    ) -> OrderInfo:
        """
        Rendelés lekérése azonosító alapján.
        
        Args:
            order_id: Rendelés azonosító
            
        Returns:
            Rendelés információ
        """
        try:
            # Mock implementation for development
            # TODO: Implement actual database query
            
            # Audit logging
            if ctx.deps.audit_logger:
                await ctx.deps.audit_logger.log_data_access(
                    user_id=ctx.deps.user_context.get("user_id", "anonymous"),
                    data_type="order_info",
                    operation="get",
                    success=True,
                    details={"order_id": order_id}
                )
            
            # Mock order data
            mock_order = OrderInfo(
                order_id=order_id,
                status="Feldolgozás alatt",
                order_date="2024-12-19",
                estimated_delivery="2024-12-22",
                total_amount=450000.0,
                items=[
                    {
                        "name": "iPhone 15 Pro",
                        "quantity": 1,
                        "price": 450000.0
                    }
                ],
                shipping_address={
                    "street": "Példa utca 1.",
                    "city": "Budapest",
                    "postal_code": "1000",
                    "country": "Magyarország"
                },
                tracking_number="TRK123456789",
                payment_status="Kifizetve"
            )
            
            return mock_order
            
        except Exception as e:
            # Error handling
            if ctx.deps.audit_logger:
                await ctx.deps.audit_logger.log_data_access(
                    user_id=ctx.deps.user_context.get("user_id", "anonymous"),
                    data_type="order_info",
                    operation="get",
                    success=False,
                    details={"error": str(e)}
                )
            
            # Return empty order on error
            return OrderInfo(
                order_id=order_id,
                status="Ismeretlen",
                order_date="",
                estimated_delivery="",
                total_amount=0.0,
                items=[],
                shipping_address={},
                tracking_number=None,
                payment_status="Ismeretlen"
            )
    
    @agent.tool
    async def get_user_orders(
        ctx: RunContext[OrderStatusDependencies],
        limit: int = 10
    ) -> List[OrderInfo]:
        """
        Felhasználó rendeléseinek lekérése.
        
        Args:
            limit: Eredmények száma
            
        Returns:
            Rendelések listája
        """
        try:
            # Mock implementation for development
            # TODO: Implement actual database query
            
            user_id = ctx.deps.user_context.get("user_id", "anonymous")
            
            # Mock orders
            mock_orders = [
                OrderInfo(
                    order_id="ORD001",
                    status="Szállítás alatt",
                    order_date="2024-12-18",
                    estimated_delivery="2024-12-21",
                    total_amount=450000.0,
                    items=[
                        {
                            "name": "iPhone 15 Pro",
                            "quantity": 1,
                            "price": 450000.0
                        }
                    ],
                    shipping_address={
                        "street": "Példa utca 1.",
                        "city": "Budapest",
                        "postal_code": "1000",
                        "country": "Magyarország"
                    },
                    tracking_number="TRK123456789",
                    payment_status="Kifizetve"
                ),
                OrderInfo(
                    order_id="ORD002",
                    status="Teljesítve",
                    order_date="2024-12-15",
                    estimated_delivery="2024-12-18",
                    total_amount=380000.0,
                    items=[
                        {
                            "name": "Samsung Galaxy S24",
                            "quantity": 1,
                            "price": 380000.0
                        }
                    ],
                    shipping_address={
                        "street": "Példa utca 1.",
                        "city": "Budapest",
                        "postal_code": "1000",
                        "country": "Magyarország"
                    },
                    tracking_number="TRK987654321",
                    payment_status="Kifizetve"
                )
            ]
            
            return mock_orders[:limit]
            
        except Exception as e:
            # Return empty list on error
            return []
    
    @agent.tool
    async def get_tracking_info(
        ctx: RunContext[OrderStatusDependencies],
        tracking_number: str
    ) -> Dict[str, Any]:
        """
        Szállítási követési információk lekérése.
        
        Args:
            tracking_number: Követési szám
            
        Returns:
            Követési információk
        """
        try:
            # Mock implementation for development
            # TODO: Implement actual tracking API call
            
            # Mock tracking info
            tracking_info = {
                "tracking_number": tracking_number,
                "status": "Szállítás alatt",
                "current_location": "Budapest, Magyarország",
                "estimated_delivery": "2024-12-22",
                "events": [
                    {
                        "date": "2024-12-19 10:30",
                        "status": "Csomag átvéve",
                        "location": "Budapest, Magyarország"
                    },
                    {
                        "date": "2024-12-19 14:15",
                        "status": "Szállítás alatt",
                        "location": "Budapest, Magyarország"
                    }
                ]
            }
            
            return tracking_info
            
        except Exception as e:
            # Return error info
            return {
                "tracking_number": tracking_number,
                "status": "Hiba",
                "error": str(e)
            }
    
    return agent


# Convenience function for LangGraph integration
async def call_order_status_agent(
    message: str,
    dependencies: OrderStatusDependencies
) -> OrderResponse:
    """
    Order status agent hívása LangGraph workflow-ból.
    
    Args:
        message: Felhasználói üzenet
        dependencies: Agent függőségek
        
    Returns:
        Order agent válasz
    """
    agent = create_order_status_agent()
    result = await agent.run(message, deps=dependencies)
    return result.output 