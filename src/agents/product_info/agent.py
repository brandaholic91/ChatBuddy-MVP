"""
Product Info Agent - LangGraph + Pydantic AI hibrid architektúra.

Ez a modul implementálja a Product Info Agent-et, amely:
- LangGraph StateGraph workflow orchestration
- Pydantic AI type-safe dependency injection
- Structured output for product information
- Tool-based product search and recommendations
- Complex state management
- Error handling és recovery
"""

import asyncio
from typing import Any, Dict, List, Optional, Union, Literal, TypedDict
from dataclasses import dataclass
from enum import Enum

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

from ...models.chat import ChatMessage, ChatSession, ChatState, MessageType
from ...models.agent import AgentType, AgentDecision, AgentResponse
from ...models.user import User
from ...models.product import Product, ProductInfo, ProductReview
from .tools import (
    ProductInfoDependencies,
    ProductSearchResult,
    ProductDetailsResult,
    search_products,
    get_product_details,
    get_product_reviews,
    get_related_products,
    check_product_availability,
    get_product_pricing
)


class ProductQueryType(Enum):
    """Termék lekérdezés típusok."""
    SEARCH = "search"
    DETAILS = "details"
    REVIEWS = "reviews"
    RELATED = "related"
    AVAILABILITY = "availability"
    PRICING = "pricing"
    COMPARISON = "comparison"
    RECOMMENDATION = "recommendation"
    GENERAL = "general"


class ProductInfoOutput(BaseModel):
    """Product Info Agent strukturált kimenete."""
    response_text: str = Field(description="Agent válasza a felhasználónak")
    query_type: str = Field(description="Lekérdezés típusa")
    products_found: int = Field(description="Talált termékek száma", ge=0)
    confidence: float = Field(description="Válasz bizonyossága", ge=0.0, le=1.0)
    product_ids: List[str] = Field(description="Érintett termék azonosítók")
    metadata: Dict[str, Any] = Field(description="További metaadatok")


# LangGraph State Management
class ProductAgentState(TypedDict):
    """LangGraph state management a Product Info Agent-hez."""
    messages: List[BaseMessage]
    current_query_type: str
    search_results: Optional[ProductSearchResult]
    product_details: Optional[ProductDetailsResult]
    user_context: Dict[str, Any]
    session_data: Dict[str, Any]
    error_count: int
    retry_attempts: int


def create_product_info_agent() -> Agent:
    """Product Info Agent létrehozása Pydantic AI-val."""
    agent = Agent(
        'openai:gpt-4o',
        deps_type=ProductInfoDependencies,
        output_type=ProductInfoOutput,
        system_prompt=(
            "Te egy termék információs chatbot vagy. Segíts a felhasználóknak "
            "termékeket keresni, információkat szerezni róluk, és ajánlásokat adni. "
            "Használd a megfelelő tool-okat a termék adatok lekéréséhez. "
            "Válaszolj magyarul, barátságosan és részletesen."
        )
    )
    
    # Tool-ok regisztrálása a hivatalos dokumentáció szerint
    agent.tool(handle_product_search)
    agent.tool(handle_product_details)
    agent.tool(handle_product_reviews)
    agent.tool(handle_product_availability)
    agent.tool(handle_product_pricing)
    
    # System prompt hozzáadása
    @agent.system_prompt
    async def add_user_context(ctx: RunContext[ProductInfoDependencies]) -> str:
        """Felhasználói kontextus hozzáadása a system prompt-hoz."""
        if ctx.deps.user:
            return f"A felhasználó neve: {ctx.deps.user.name}"
        return ""
    
    return agent


# LangGraph Tool Functions
async def handle_product_search(
    ctx: RunContext[ProductInfoDependencies],
    query: str,
    category_id: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None
) -> str:
    """
    Termék keresés kezelése.
    
    Args:
        query: Keresési kifejezés
        category_id: Kategória azonosító
        min_price: Minimum ár
        max_price: Maximum ár
        in_stock: Készleten lévő termékek
        
    Returns:
        Keresési eredmények válasza
    """
    try:
        from decimal import Decimal
        
        # Paraméterek konvertálása
        min_price_decimal = Decimal(str(min_price)) if min_price else None
        max_price_decimal = Decimal(str(max_price)) if max_price else None
        
        # Keresés végrehajtása
        result = await search_products(
            ctx,
            query=query,
            category_id=category_id,
            min_price=min_price_decimal,
            max_price=max_price_decimal,
            in_stock=in_stock,
            limit=10
        )
        
        if result.products:
            products_info = []
            for product in result.products:
                price_info = f"{product.price:,} {product.currency}"
                stock_info = "Készleten" if product.stock_quantity > 0 else "Nincs készleten"
                products_info.append(f"• {product.name} - {price_info} ({stock_info})")
            
            response = f"Találtam {len(result.products)} terméket a '{query}' keresésre:\n\n"
            response += "\n".join(products_info)
            
            if result.total_count > len(result.products):
                response += f"\n\nÖsszesen {result.total_count} termék található. Szeretnél szűrni?"
        else:
            response = f"Sajnos nem találtam termékeket a '{query}' keresésre. Próbálj más kulcsszavakat!"
        
        return response
        
    except Exception as e:
        return f"Sajnálom, hiba történt a keresés során: {str(e)}"


async def handle_product_details(
    ctx: RunContext[ProductInfoDependencies],
    product_id: str
) -> str:
    """
    Termék részletes információk kezelése.
    
    Args:
        product_id: Termék azonosító
        
    Returns:
        Termék részletes információk válasza
    """
    try:
        result = await get_product_details(ctx, product_id)
        product = result.product
        product_info = result.product_info
        
        response = f"📱 **{product.name}**\n\n"
        response += f"**Ár:** {product.price:,} {product.currency}"
        if product.original_price and product.original_price > product.price:
            discount = ((product.original_price - product.price) / product.original_price) * 100
            response += f" (eredeti: {product.original_price:,} {product.currency}, {discount:.0f}% kedvezmény)"
        response += "\n\n"
        
        if product.description:
            response += f"**Leírás:** {product.description}\n\n"
        
        if product_info:
            if product_info.specifications:
                response += "**Specifikációk:**\n"
                for key, value in product_info.specifications.items():
                    response += f"• {key}: {value}\n"
                response += "\n"
            
            if product_info.features:
                response += "**Jellemzők:**\n"
                for feature in product_info.features:
                    response += f"• {feature}\n"
                response += "\n"
            
            if product_info.benefits:
                response += "**Előnyök:**\n"
                for benefit in product_info.benefits:
                    response += f"• {benefit}\n"
                response += "\n"
            
            if product_info.warranty:
                response += f"**Garancia:** {product_info.warranty}\n\n"
            
            if product_info.shipping_info:
                response += f"**Szállítás:** {product_info.shipping_info}\n\n"
            
            if product_info.return_policy:
                response += f"**Visszaküldés:** {product_info.return_policy}\n\n"
        
        # Készlet információk
        stock_status = "✅ Készleten" if product.stock_quantity > 0 else "❌ Nincs készleten"
        response += f"**Készlet:** {stock_status} ({product.stock_quantity} db)\n\n"
        
        # Értékelések
        if result.reviews:
            avg_rating = sum(r.rating for r in result.reviews) / len(result.reviews)
            response += f"**Értékelés:** {avg_rating:.1f}/5 ({len(result.reviews)} értékelés)\n\n"
        
        # Kapcsolódó termékek
        if result.related_products:
            response += "**Kapcsolódó termékek:**\n"
            for related in result.related_products[:3]:
                response += f"• {related.name} - {related.price:,} {related.currency}\n"
        
        return response
        
    except Exception as e:
        return f"Sajnálom, hiba történt a termék adatok lekérése során: {str(e)}"


async def handle_product_reviews(
    ctx: RunContext[ProductInfoDependencies],
    product_id: str,
    limit: int = 5
) -> str:
    """
    Termék értékelések kezelése.
    
    Args:
        product_id: Termék azonosító
        limit: Eredmények száma
        
    Returns:
        Értékelések válasza
    """
    try:
        reviews = await get_product_reviews(ctx, product_id, limit=limit)
        
        if not reviews:
            return "Még nincsenek értékelések ehhez a termékhez."
        
        response = f"📝 **Termék értékelések** ({len(reviews)} db):\n\n"
        
        for review in reviews:
            stars = "⭐" * review.rating
            response += f"{stars} **{review.title}**\n"
            response += f"*{review.user_id}* - {review.rating}/5\n"
            
            if review.comment:
                response += f"{review.comment}\n"
            
            if review.pros:
                response += f"✅ **Előnyök:** {', '.join(review.pros)}\n"
            
            if review.cons:
                response += f"❌ **Hátrányok:** {', '.join(review.cons)}\n"
            
            if review.is_verified_purchase:
                response += "✅ **Igazolt vásárlás**\n"
            
            response += f"👍 {review.is_helpful} | 👎 {review.is_not_helpful}\n\n"
        
        return response
        
    except Exception as e:
        return f"Sajnálom, hiba történt az értékelések lekérése során: {str(e)}"


async def handle_product_availability(
    ctx: RunContext[ProductInfoDependencies],
    product_id: str
) -> str:
    """
    Termék készlet ellenőrzés kezelése.
    
    Args:
        product_id: Termék azonosító
        
    Returns:
        Készlet információk válasza
    """
    try:
        availability = await check_product_availability(ctx, product_id)
        
        response = f"📦 **Készlet információk**\n\n"
        
        if availability["in_stock"]:
            response += f"✅ **Készleten:** {availability['stock_quantity']} db\n"
        else:
            response += "❌ **Nincs készleten**\n"
        
        if "estimated_restock_date" in availability:
            response += f"🔄 **Várható újrakészlet:** {availability['estimated_restock_date']}\n\n"
        
        if availability["shipping_options"]:
            response += "🚚 **Szállítási opciók:**\n"
            for option in availability["shipping_options"]:
                price_text = "Ingyenes" if option["price"] == 0 else f"{option['price']:,} Ft"
                response += f"• {option['name']}: {price_text} ({option['delivery_time']})\n"
        
        if availability.get("pickup_available"):
            response += "\n🏪 **Személyes átvétel:**\n"
            for location in availability["pickup_locations"]:
                response += f"• {location['name']}: {location['address']}\n"
        
        return response
        
    except Exception as e:
        return f"Sajnálom, hiba történt a készlet ellenőrzése során: {str(e)}"


async def handle_product_pricing(
    ctx: RunContext[ProductInfoDependencies],
    product_id: str
) -> str:
    """
    Termék árazási információk kezelése.
    
    Args:
        product_id: Termék azonosító
        
    Returns:
        Árazási információk válasza
    """
    try:
        pricing = await get_product_pricing(ctx, product_id)
        
        response = f"💰 **Árazási információk**\n\n"
        response += f"**Jelenlegi ár:** {pricing['current_price']:,} {pricing['currency']}\n"
        
        if pricing.get("original_price"):
            discount = pricing["discount_percentage"]
            response += f"**Eredeti ár:** {pricing['original_price']:,} {pricing['currency']} ({discount}% kedvezmény)\n"
        
        if pricing.get("installment_options"):
            response += "\n💳 **Részletfizetési opciók:**\n"
            for option in pricing["installment_options"]:
                response += f"• {option['months']} hónap: {option['monthly_payment']:,} Ft/hó\n"
        
        if pricing.get("bulk_discounts"):
            response += "\n📦 **Mennyiségi kedvezmények:**\n"
            for discount in pricing["bulk_discounts"]:
                response += f"• {discount['quantity']} db: {discount['discount_percentage']}% kedvezmény\n"
        
        if pricing.get("loyalty_discounts"):
            response += "\n👑 **Hűségi kedvezmények:**\n"
            for discount in pricing["loyalty_discounts"]:
                response += f"• {discount['type']}: {discount['discount_percentage']}% kedvezmény\n"
        
        return response
        
    except Exception as e:
        return f"Sajnálom, hiba történt az árazási információk lekérése során: {str(e)}"


# LangGraph Workflow Functions
def route_product_query(state: ProductAgentState) -> Command[Literal["search_products", "get_details", "get_reviews", "check_availability", "get_pricing", "general_response", END]]:
    """
    LangGraph routing node - termék lekérdezés kategorizálása és routing.
    
    Args:
        state: LangGraph state
        
    Returns:
        Command a következő agent-hez
    """
    messages = state["messages"]
    if not messages:
        return Command(goto=END)
    
    last_message = messages[-1]
    if not isinstance(last_message, HumanMessage):
        return Command(goto=END)
    
    content = last_message.content.lower()
    
    # Routing logic
    if any(word in content for word in ["keres", "keress", "talál", "milyen", "milyenek"]):
        return Command(goto="search_products")
    elif any(word in content for word in ["részlete", "információ", "adatok", "specifikáció"]):
        return Command(goto="get_details")
    elif any(word in content for word in ["értékelés", "vélemény", "review", "mit mondanak"]):
        return Command(goto="get_reviews")
    elif any(word in content for word in ["készlet", "elérhető", "kapható", "raktár"]):
        return Command(goto="check_availability")
    elif any(word in content for word in ["ár", "árak", "kedvezmény", "részlet", "fizetés"]):
        return Command(goto="get_pricing")
    else:
        return Command(goto="general_response")


async def call_search_products(state: ProductAgentState) -> Command[Literal["coordinator"]]:
    """Product search hívása LangGraph workflow-ban."""
    try:
        deps = ProductInfoDependencies(
            user=state["user_context"].get("user"),
            session_id=state["session_data"].get("session_id")
        )
        
        agent = create_product_info_agent()
        agent.tool(handle_product_search)
        
        last_message = state["messages"][-1].content
        result = await agent.run(last_message, deps=deps)
        
        response = AIMessage(content=result.output.response_text)
        
        return Command(
            goto="coordinator",
            update={"messages": [response]}
        )
    except Exception as e:
        error_response = AIMessage(content=f"Sajnálom, hiba történt: {str(e)}")
        return Command(
            goto="coordinator",
            update={"messages": [error_response]}
        )


async def call_get_details(state: ProductAgentState) -> Command[Literal["coordinator"]]:
    """Product details hívása LangGraph workflow-ban."""
    try:
        deps = ProductInfoDependencies(
            user=state["user_context"].get("user"),
            session_id=state["session_data"].get("session_id")
        )
        
        agent = create_product_info_agent()
        agent.tool(handle_product_details)
        
        last_message = state["messages"][-1].content
        result = await agent.run(last_message, deps=deps)
        
        response = AIMessage(content=result.output.response_text)
        
        return Command(
            goto="coordinator",
            update={"messages": [response]}
        )
    except Exception as e:
        error_response = AIMessage(content=f"Sajnálom, hiba történt: {str(e)}")
        return Command(
            goto="coordinator",
            update={"messages": [error_response]}
        )


async def call_get_reviews(state: ProductAgentState) -> Command[Literal["coordinator"]]:
    """Product reviews hívása LangGraph workflow-ban."""
    try:
        deps = ProductInfoDependencies(
            user=state["user_context"].get("user"),
            session_id=state["session_data"].get("session_id")
        )
        
        agent = create_product_info_agent()
        agent.tool(handle_product_reviews)
        
        last_message = state["messages"][-1].content
        result = await agent.run(last_message, deps=deps)
        
        response = AIMessage(content=result.output.response_text)
        
        return Command(
            goto="coordinator",
            update={"messages": [response]}
        )
    except Exception as e:
        error_response = AIMessage(content=f"Sajnálom, hiba történt: {str(e)}")
        return Command(
            goto="coordinator",
            update={"messages": [error_response]}
        )


async def call_check_availability(state: ProductAgentState) -> Command[Literal["coordinator"]]:
    """Product availability hívása LangGraph workflow-ban."""
    try:
        deps = ProductInfoDependencies(
            user=state["user_context"].get("user"),
            session_id=state["session_data"].get("session_id")
        )
        
        agent = create_product_info_agent()
        agent.tool(handle_product_availability)
        
        last_message = state["messages"][-1].content
        result = await agent.run(last_message, deps=deps)
        
        response = AIMessage(content=result.output.response_text)
        
        return Command(
            goto="coordinator",
            update={"messages": [response]}
        )
    except Exception as e:
        error_response = AIMessage(content=f"Sajnálom, hiba történt: {str(e)}")
        return Command(
            goto="coordinator",
            update={"messages": [error_response]}
        )


async def call_get_pricing(state: ProductAgentState) -> Command[Literal["coordinator"]]:
    """Product pricing hívása LangGraph workflow-ban."""
    try:
        deps = ProductInfoDependencies(
            user=state["user_context"].get("user"),
            session_id=state["session_data"].get("session_id")
        )
        
        agent = create_product_info_agent()
        agent.tool(handle_product_pricing)
        
        last_message = state["messages"][-1].content
        result = await agent.run(last_message, deps=deps)
        
        response = AIMessage(content=result.output.response_text)
        
        return Command(
            goto="coordinator",
            update={"messages": [response]}
        )
    except Exception as e:
        error_response = AIMessage(content=f"Sajnálom, hiba történt: {str(e)}")
        return Command(
            goto="coordinator",
            update={"messages": [error_response]}
        )


async def call_general_response(state: ProductAgentState) -> Command[Literal["coordinator"]]:
    """General response hívása LangGraph workflow-ban."""
    try:
        deps = ProductInfoDependencies(
            user=state["user_context"].get("user"),
            session_id=state["session_data"].get("session_id")
        )
        
        agent = create_product_info_agent()
        
        last_message = state["messages"][-1].content
        result = await agent.run(last_message, deps=deps)
        
        response = AIMessage(content=result.output.response_text)
        
        return Command(
            goto="coordinator",
            update={"messages": [response]}
        )
    except Exception as e:
        error_response = AIMessage(content=f"Sajnálom, hiba történt: {str(e)}")
        return Command(
            goto="coordinator",
            update={"messages": [error_response]}
        )


def create_langgraph_workflow() -> StateGraph:
    """LangGraph workflow létrehozása."""
    workflow = StateGraph(ProductAgentState)
    
    # Nodes hozzáadása - async függvények
    workflow.add_node("coordinator", route_product_query)
    workflow.add_node("search_products", call_search_products)
    workflow.add_node("get_details", call_get_details)
    workflow.add_node("get_reviews", call_get_reviews)
    workflow.add_node("check_availability", call_check_availability)
    workflow.add_node("get_pricing", call_get_pricing)
    workflow.add_node("general_response", call_general_response)
    
    # Edges hozzáadása
    workflow.add_edge(START, "coordinator")
    workflow.add_edge("search_products", "coordinator")
    workflow.add_edge("get_details", "coordinator")
    workflow.add_edge("get_reviews", "coordinator")
    workflow.add_edge("check_availability", "coordinator")
    workflow.add_edge("get_pricing", "coordinator")
    workflow.add_edge("general_response", "coordinator")
    
    return workflow.compile()


class ProductInfoAgent:
    """Product Info Agent LangGraph + Pydantic AI hibrid architektúrával."""
    
    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        verbose: bool = True
    ):
        self.llm = llm or ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            verbose=verbose
        )
        self.state = {"messages": []}
        self._product_info_agent = None
        self._langgraph_workflow = None
    
    def _get_product_info_agent(self) -> Agent:
        """Product Info Agent létrehozása vagy lekérése."""
        if self._product_info_agent is None:
            self._product_info_agent = create_product_info_agent()
        
        return self._product_info_agent
    
    def _get_langgraph_workflow(self):
        """LangGraph workflow létrehozása vagy lekérése."""
        if self._langgraph_workflow is None:
            self._langgraph_workflow = create_langgraph_workflow()
        return self._langgraph_workflow
    
    async def process_message(
        self,
        message: str,
        user: Optional[User] = None,
        session_id: Optional[str] = None
    ) -> AgentResponse:
        """
        Üzenet feldolgozása LangGraph + Pydantic AI hibrid architektúrával.
        
        Args:
            message: Felhasználói üzenet
            user: Felhasználó objektum
            session_id: Session azonosító
            
        Returns:
            Agent válasz
        """
        try:
            # LangGraph state létrehozása
            langgraph_state = ProductAgentState(
                messages=[HumanMessage(content=message)],
                current_query_type="unknown",
                search_results=None,
                product_details=None,
                user_context={"user": user},
                session_data={"session_id": session_id},
                error_count=0,
                retry_attempts=0
            )
            
            # LangGraph workflow futtatása - async context-ben
            workflow = self._get_langgraph_workflow()
            result = await workflow.ainvoke(langgraph_state)
            
            # Válasz kinyerése
            if result["messages"]:
                last_message = result["messages"][-1]
                if isinstance(last_message, AIMessage):
                    response_text = last_message.content
                else:
                    response_text = "Sajnálom, nem sikerült válaszolni."
            else:
                response_text = "Sajnálom, nem sikerült válaszolni."
            
            # Query típus meghatározása
            query_type = ProductQueryType.GENERAL
            if any(word in message.lower() for word in ["keres", "keress", "talál"]):
                query_type = ProductQueryType.SEARCH
            elif any(word in message.lower() for word in ["részlete", "információ"]):
                query_type = ProductQueryType.DETAILS
            elif any(word in message.lower() for word in ["értékelés", "vélemény"]):
                query_type = ProductQueryType.REVIEWS
            elif any(word in message.lower() for word in ["készlet", "elérhető"]):
                query_type = ProductQueryType.AVAILABILITY
            elif any(word in message.lower() for word in ["ár", "árak"]):
                query_type = ProductQueryType.PRICING
            
            # Válasz létrehozása
            response = AgentResponse(
                agent_type=AgentType.PRODUCT_INFO,
                response_text=response_text,
                confidence=0.9,  # LangGraph workflow biztonsága
                metadata={
                    "query_type": query_type.value,
                    "session_id": session_id,
                    "user_id": user.id if user else None,
                    "langgraph_used": True,
                    "workflow_steps": len(result["messages"]) if result["messages"] else 0
                }
            )
            
            # State frissítése
            self.state["messages"].append(HumanMessage(content=message))
            self.state["messages"].append(AIMessage(content=response.response_text))
            
            return response
            
        except Exception as e:
            # Error handling
            error_response = AgentResponse(
                agent_type=AgentType.PRODUCT_INFO,
                response_text=f"Sajnálom, hiba történt: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e), "langgraph_used": True}
            )
            return error_response
    
    def get_state(self) -> Dict[str, Any]:
        """Aktuális állapot lekérése."""
        return self.state
    
    def reset_state(self):
        """Állapot visszaállítása."""
        self.state = {"messages": []}


# Singleton instance
_product_info_agent: Optional[ProductInfoAgent] = None


def get_product_info_agent() -> ProductInfoAgent:
    """
    Product Info Agent singleton instance.
    
    Returns:
        ProductInfoAgent instance
    """
    global _product_info_agent
    if _product_info_agent is None:
        _product_info_agent = ProductInfoAgent()
    return _product_info_agent


async def process_product_query(
    message: str,
    user: Optional[User] = None,
    session_id: Optional[str] = None
) -> AgentResponse:
    """
    Product query feldolgozása LangGraph + Pydantic AI hibrid architektúrával.
    
    Args:
        message: Felhasználói üzenet
        user: Felhasználó objektum
        session_id: Session azonosító
        
    Returns:
        Agent válasz
    """
    agent = get_product_info_agent()
    return await agent.process_message(message, user, session_id) 