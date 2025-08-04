"""
Order Status Agent - Rendelés státusz kezelés és követés

Ez az agent felelős a rendelések státuszának lekérdezéséért, 
szállítási információk megjelenítéséért és rendelés követésért.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field

from src.config.security_prompts import SecurityContext
from src.config.audit_logging import SecurityAuditLogger, SecuritySeverity
from src.models.order import Order, OrderStatus, OrderItem
from src.models.user import User


@dataclass
class OrderStatusDependencies:
    """Order Status Agent függőségei"""
    supabase_client: Any
    webshop_api: Any
    user_context: dict
    security_context: SecurityContext
    audit_logger: SecurityAuditLogger


class OrderStatusResponse(BaseModel):
    """Order Status Agent válasz modell"""
    message: str = Field(description="Felhasználóbarát válasz üzenet")
    order_info: Optional[Order] = Field(None, description="Rendelés információk")
    tracking_info: Optional[Dict[str, Any]] = Field(None, description="Szállítási információk")
    next_steps: Optional[List[str]] = Field(None, description="Következő lépések")
    confidence: float = Field(1.0, description="Válasz bizonyossága")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metaadatok")


# Order Status Agent létrehozása (lazy loading)
_order_status_agent = None


# Tool függvények (ezeket később fogjuk regisztrálni)
async def get_order_by_id(
    ctx: RunContext[OrderStatusDependencies], 
    order_id: str
) -> Order:
    """Rendelés lekérdezése azonosító alapján"""
    try:
        # Supabase lekérdezés
        response = ctx.deps.supabase_client.table('orders').select('*').eq('id', order_id).execute()
        
        if response.data:
            order_data = response.data[0]
            return Order(**order_data)
        else:
            raise ValueError(f"Rendelés nem található: {order_id}")
            
    except Exception as e:
        await ctx.deps.audit_logger.log_error(
            "order_lookup_failed",
            f"Rendelés lekérdezés hiba: {order_id}",
            ctx.deps.user_context.get('user_id'),
            ctx.deps.user_context.get('session_id'),
            "order_status",
            {"order_id": order_id, "error": str(e)}
        )
        raise


async def get_orders_by_user(
    ctx: RunContext[OrderStatusDependencies],
    user_id: str,
    limit: int = 10
) -> List[Order]:
    """Felhasználó rendeléseinek lekérdezése"""
    try:
        response = ctx.deps.supabase_client.table('orders')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(limit)\
            .execute()
            
        return [Order(**order) for order in response.data]
        
    except Exception as e:
        await ctx.deps.audit_logger.log_error(
            "user_orders_lookup_failed", 
            f"Felhasználó rendelései lekérdezés hiba: {user_id}",
            ctx.deps.user_context.get('user_id'),
            ctx.deps.user_context.get('session_id'),
            "order_status",
            {"user_id": user_id, "error": str(e)}
        )
        raise


async def get_tracking_info(
    ctx: RunContext[OrderStatusDependencies],
    tracking_number: str
) -> Dict[str, Any]:
    """Szállítási információk lekérdezése"""
    try:
        # Webshop API hívás szállítási információkhoz
        tracking_data = await ctx.deps.webshop_api.get_tracking_info(tracking_number)
        
        await ctx.deps.audit_logger.log_security_event(
            "tracking_info_retrieved",
            SecuritySeverity.LOW,
            ctx.deps.user_context.get('user_id'),
            f"SZállítási információk lekérdezve: {tracking_number}",
            {"tracking_number": tracking_number}
        )
        
        return tracking_data
        
    except Exception as e:
        await ctx.deps.audit_logger.log_error(
            "tracking_info_failed",
            f"SZállítási információk hiba: {tracking_number}",
            ctx.deps.user_context.get('user_id'),
            ctx.deps.user_context.get('session_id'),
            "order_status",
            {"tracking_number": tracking_number, "error": str(e)}
        )
        raise


async def update_order_status(
    ctx: RunContext[OrderStatusDependencies],
    order_id: str,
    new_status: OrderStatus
) -> Order:
    """Rendelés státusz frissítése"""
    try:
        # Supabase frissítés
        response = ctx.deps.supabase_client.table('orders')\
            .update({"status": new_status.value, "updated_at": datetime.now(timezone.utc).isoformat()})\
            .eq('id', order_id)\
            .execute()
            
        if response.data:
            updated_order = Order(**response.data[0])
            
            await ctx.deps.audit_logger.log_security_event(
                "order_status_updated",
                SecuritySeverity.LOW,
                ctx.deps.user_context.get('user_id'),
                f"Rendelés státusz frissítve: {order_id} -> {new_status.value}",
                {"order_id": order_id, "new_status": new_status.value}
            )
            
            return updated_order
        else:
            raise ValueError(f"Rendelés frissítés sikertelen: {order_id}")
            
    except Exception as e:
        await ctx.deps.audit_logger.log_error(
            "order_status_update_failed",
            f"Rendelés státusz frissítés hiba: {order_id}",
            ctx.deps.user_context.get('user_id'),
            ctx.deps.user_context.get('session_id'),
            "order_status",
            {"order_id": order_id, "new_status": new_status.value, "error": str(e)}
        )
        raise


async def get_order_history(
    ctx: RunContext[OrderStatusDependencies],
    order_id: str
) -> List[Dict[str, Any]]:
    """Rendelés státusz változások előzménye"""
    try:
        response = ctx.deps.supabase_client.table('order_status_history')\
            .select('*')\
            .eq('order_id', order_id)\
            .order('created_at', desc=True)\
            .execute()
            
        return response.data
        
    except Exception as e:
        await ctx.deps.audit_logger.log_error(
            "order_history_failed",
            f"Rendelés előzmények hiba: {order_id}",
            ctx.deps.user_context.get('user_id'),
            ctx.deps.user_context.get('session_id'),
            "order_status",
            {"order_id": order_id, "error": str(e)}
        )
        raise


# Mock agent fallback (fejlesztési célokra)
class MockOrderStatusAgent:
    """Mock Order Status Agent fejlesztési célokra"""
    
    async def run(self, message: str, deps: OrderStatusDependencies) -> OrderStatusResponse:
        return OrderStatusResponse(
            message="Ez egy mock Order Status Agent válasz. A valós implementáció fejlesztés alatt.",
            confidence=0.5,
            metadata={"agent_type": "mock_order_status"}
        )


# Agent factory függvény
def create_order_status_agent() -> Any:
    """Order Status Agent létrehozása"""
    global _order_status_agent
    
    if _order_status_agent is None:
        try:
            # Próbáljuk létrehozni a valós agent-et
            _order_status_agent = Agent(
                'openai:gpt-4o',
                deps_type=OrderStatusDependencies,
                output_type=OrderStatusResponse,
                system_prompt="""Te egy rendelés státusz és szállítás követés szakértő vagy. 
                
                Feladatod:
                1. Rendelések státuszának lekérdezése
                2. Szállítási információk megjelenítése  
                3. Rendelés követés és frissítések
                4. Felhasználóbarát válaszok adása
                
                Mindig használd a megfelelő eszközöket a pontos információk lekéréséhez.
                Válaszaid legyenek barátságosak és informatívak."""
            )
        except Exception as e:
            # Fallback mock agent teszteléshez
            print(f"Warning: Could not create Order Status Agent: {e}")
            _order_status_agent = MockOrderStatusAgent()
    
    return _order_status_agent 