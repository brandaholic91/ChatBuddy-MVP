"""
Koordinátor Agent - Hibrid LangGraph + Pydantic AI architektúra.

Ez a modul implementálja a fő koordinátor agent-et, amely:
- LangGraph StateGraph workflow orchestration
- Pydantic AI type-safe dependency injection
- Multi-agent routing és kategorizálás
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

from ..models.chat import ChatMessage, ChatSession, ChatState, MessageType
from ..models.agent import AgentType, AgentDecision, AgentResponse
from ..models.user import User


class MessageCategory(Enum):
    """Üzenet kategóriák a routing-hoz."""
    PRODUCT_INFO = "product_info"
    ORDER_STATUS = "order_status" 
    RECOMMENDATION = "recommendation"
    MARKETING = "marketing"
    GENERAL = "general"
    UNKNOWN = "unknown"


@dataclass
class CoordinatorDependencies:
    """Koordinátor agent függőségei."""
    user: Optional[User] = None
    session_id: Optional[str] = None
    llm: Optional[ChatOpenAI] = None


class CoordinatorOutput(BaseModel):
    """Koordinátor agent strukturált kimenete."""
    response_text: str = Field(description="Agent válasza a felhasználónak")
    category: str = Field(description="Üzenet kategóriája")
    confidence: float = Field(description="Válasz bizonyossága", ge=0.0, le=1.0)
    agent_used: str = Field(description="Használt agent típusa")
    metadata: Dict[str, Any] = Field(description="További metaadatok")


# LangGraph State Management - Egyszerűsített megközelítés
class AgentState(TypedDict):
    """LangGraph state management a koordinátor agent-hez."""
    messages: List[BaseMessage]
    current_agent: str
    user_context: Dict[str, Any]
    session_data: Dict[str, Any]
    error_count: int
    retry_attempts: int


def create_coordinator_agent() -> Agent:
    """Koordinátor agent létrehozása Pydantic AI-val."""
    return Agent(
        'openai:gpt-4o',
        deps_type=CoordinatorDependencies,
        output_type=CoordinatorOutput,
        system_prompt=(
            "Te egy webshop chatbot vagy. A felhasználó kérdéseit kategorizáld és "
            "használd a megfelelő tool-okat a válaszadáshoz. "
            "Válaszolj magyarul, barátságosan és segítőkészen."
        )
    )


# LangGraph Tool Functions - ezeket regisztráljuk a LangGraph workflow-ba
async def handle_product_query(ctx: RunContext[CoordinatorDependencies], query: str) -> str:
    """
    Termékekkel kapcsolatos kérdések kezelése.
    
    Args:
        query: Felhasználói kérdés
        
    Returns:
        Termék információs válasz
    """
    query_lower = query.lower()
    if "telefon" in query_lower:
        return "Sokféle telefonunk van készleten! IPhone, Samsung, Xiaomi és más márkák is. Milyen árban gondolkodsz?"
    elif "ár" in query_lower or "árak" in query_lower:
        return "Termékeink árai 50 ezer forinttól 500 ezer forintig terjednek. Van valamilyen konkrét termék, amit keresel?"
    else:
        return f"Termék információs ügynök: {query} - Milyen konkrét termékre vagy kíváncsi?"


async def handle_order_query(ctx: RunContext[CoordinatorDependencies], query: str) -> str:
    """
    Rendelésekkel kapcsolatos kérdések kezelése.
    
    Args:
        query: Felhasználói kérdés
        
    Returns:
        Rendelési információs válasz
    """
    query_lower = query.lower()
    if "státusz" in query_lower or "állapot" in query_lower:
        return "A rendelésed státuszának ellenőrzéséhez szükségem van a rendelési azonosítóra. Meg tudnád adni?"
    elif "szállítás" in query_lower or "megérkezik" in query_lower:
        return "A szállítási idő általában 2-5 munkanap, attól függően, hogy hol laksz. Van konkrét rendelésed?"
    else:
        return f"Rendelési ügynök: {query} - Miben segíthetek a rendeléssel kapcsolatban?"


async def handle_recommendation_query(ctx: RunContext[CoordinatorDependencies], query: str) -> str:
    """
    Ajánlásokkal kapcsolatos kérdések kezelése.
    
    Args:
        query: Felhasználói kérdés
        
    Returns:
        Ajánlási válasz
    """
    query_lower = query.lower()
    if "ajánl" in query_lower or "javasol" in query_lower:
        return "Szeretnék ajánlani néhány népszerű terméket! Mit keresel? Telefon, laptop, vagy valami más?"
    elif "népszerű" in query_lower or "legjobb" in query_lower:
        return "A legnépszerűbb termékeink között szerepel az iPhone 15, Samsung Galaxy S24 és a Xiaomi 14. Melyik érdekel?"
    else:
        return f"Ajánlási ügynök: {query} - Milyen típusú termékre keresel ajánlást?"


async def handle_marketing_query(ctx: RunContext[CoordinatorDependencies], query: str) -> str:
    """
    Marketing és kedvezményekkel kapcsolatos kérdések kezelése.
    
    Args:
        query: Felhasználói kérdés
        
    Returns:
        Marketing információs válasz
    """
    query_lower = query.lower()
    if "kedvezmény" in query_lower or "akció" in query_lower:
        return "Jelenleg több akció is fut! 10% kedvezmény az új vásárlókra, és ingyenes szállítás 50 ezer forint feletti rendelésekre."
    elif "kupon" in query_lower or "kód" in query_lower:
        return "Használd a 'UJ10' kódot 10% kedvezményre, vagy a 'INGYEN' kódot ingyenes szállításra!"
    else:
        return f"Marketing ügynök: {query} - Van valamilyen akciós ajánlatunk, ami érdekel!"


async def handle_general_query(ctx: RunContext[CoordinatorDependencies], query: str) -> str:
    """
    Általános kérdések kezelése.
    
    Args:
        query: Felhasználói kérdés
        
    Returns:
        Általános válasz
    """
    query_lower = query.lower()
    if "szia" in query_lower or "hello" in query_lower:
        return "Szia! Üdvözöllek! Miben segíthetek ma?"
    elif "kosár" in query_lower:
        return "A kosár funkcióval termékeket adhatsz hozzá a rendeléshez. A kosárban lévő termékeket később meg tudod rendelni."
    elif "segít" in query_lower:
        return "Természetesen segítek! Mit szeretnél tudni? Termékekről, rendelésről, vagy valami másról?"
    else:
        return f"Általános kérdés: {query} - Miben segíthetek?"


# LangGraph Workflow Functions
def route_message(state: AgentState) -> Command[Literal["product_agent", "order_agent", "recommendation_agent", "marketing_agent", "general_agent", END]]:
    """
    LangGraph routing node - üzenet kategorizálása és routing.
    
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
    if any(word in content for word in ["telefon", "termék", "ár", "árak", "készlet"]):
        return Command(goto="product_agent")
    elif any(word in content for word in ["rendelés", "státusz", "állapot", "szállítás", "megérkezik"]):
        return Command(goto="order_agent")
    elif any(word in content for word in ["ajánl", "javasol", "népszerű", "legjobb"]):
        return Command(goto="recommendation_agent")
    elif any(word in content for word in ["kedvezmény", "akció", "kupon", "kód"]):
        return Command(goto="marketing_agent")
    else:
        return Command(goto="general_agent")


def call_product_agent(state: AgentState) -> Command[Literal["coordinator"]]:
    """Product agent hívása LangGraph workflow-ban."""
    try:
        # Pydantic AI agent használata
        deps = CoordinatorDependencies(
            user=state["user_context"].get("user"),
            session_id=state["session_data"].get("session_id"),
            llm=ChatOpenAI()
        )
        
        # Agent hívása
        agent = create_coordinator_agent()
        agent.tool(handle_product_query)
        
        # Üzenet feldolgozása
        last_message = state["messages"][-1].content
        result = asyncio.run(agent.run(last_message, deps=deps))
        
        # Válasz hozzáadása
        response = AIMessage(content=result.output.response_text)
        
        return Command(
            goto="coordinator",
            update={"messages": [response]}
        )
    except Exception as e:
        # Error handling
        error_response = AIMessage(content=f"Sajnálom, hiba történt: {str(e)}")
        return Command(
            goto="coordinator",
            update={"messages": [error_response]}
        )


def call_order_agent(state: AgentState) -> Command[Literal["coordinator"]]:
    """Order agent hívása LangGraph workflow-ban."""
    try:
        deps = CoordinatorDependencies(
            user=state["user_context"].get("user"),
            session_id=state["session_data"].get("session_id"),
            llm=ChatOpenAI()
        )
        
        agent = create_coordinator_agent()
        agent.tool(handle_order_query)
        
        last_message = state["messages"][-1].content
        result = asyncio.run(agent.run(last_message, deps=deps))
        
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


def call_recommendation_agent(state: AgentState) -> Command[Literal["coordinator"]]:
    """Recommendation agent hívása LangGraph workflow-ban."""
    try:
        deps = CoordinatorDependencies(
            user=state["user_context"].get("user"),
            session_id=state["session_data"].get("session_id"),
            llm=ChatOpenAI()
        )
        
        agent = create_coordinator_agent()
        agent.tool(handle_recommendation_query)
        
        last_message = state["messages"][-1].content
        result = asyncio.run(agent.run(last_message, deps=deps))
        
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


def call_marketing_agent(state: AgentState) -> Command[Literal["coordinator"]]:
    """Marketing agent hívása LangGraph workflow-ban."""
    try:
        deps = CoordinatorDependencies(
            user=state["user_context"].get("user"),
            session_id=state["session_data"].get("session_id"),
            llm=ChatOpenAI()
        )
        
        agent = create_coordinator_agent()
        agent.tool(handle_marketing_query)
        
        last_message = state["messages"][-1].content
        result = asyncio.run(agent.run(last_message, deps=deps))
        
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


def call_general_agent(state: AgentState) -> Command[Literal["coordinator"]]:
    """General agent hívása LangGraph workflow-ban."""
    try:
        deps = CoordinatorDependencies(
            user=state["user_context"].get("user"),
            session_id=state["session_data"].get("session_id"),
            llm=ChatOpenAI()
        )
        
        agent = create_coordinator_agent()
        agent.tool(handle_general_query)
        
        last_message = state["messages"][-1].content
        result = asyncio.run(agent.run(last_message, deps=deps))
        
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
    workflow = StateGraph(AgentState)
    
    # Nodes hozzáadása
    workflow.add_node("coordinator", route_message)
    workflow.add_node("product_agent", call_product_agent)
    workflow.add_node("order_agent", call_order_agent)
    workflow.add_node("recommendation_agent", call_recommendation_agent)
    workflow.add_node("marketing_agent", call_marketing_agent)
    workflow.add_node("general_agent", call_general_agent)
    
    # Edges hozzáadása
    workflow.add_edge(START, "coordinator")
    workflow.add_edge("product_agent", "coordinator")
    workflow.add_edge("order_agent", "coordinator")
    workflow.add_edge("recommendation_agent", "coordinator")
    workflow.add_edge("marketing_agent", "coordinator")
    workflow.add_edge("general_agent", "coordinator")
    
    return workflow.compile()


class CoordinatorAgent:
    """Koordinátor agent LangGraph + Pydantic AI hibrid architektúrával."""
    
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
        self._coordinator_agent = None
        self._langgraph_workflow = None
    
    def _get_coordinator_agent(self) -> Agent:
        """Koordinátor agent létrehozása vagy lekérése."""
        if self._coordinator_agent is None:
            self._coordinator_agent = create_coordinator_agent()
            
            # Tool-ok regisztrálása
            self._coordinator_agent.tool(handle_product_query)
            self._coordinator_agent.tool(handle_order_query)
            self._coordinator_agent.tool(handle_recommendation_query)
            self._coordinator_agent.tool(handle_marketing_query)
            self._coordinator_agent.tool(handle_general_query)
            
            # System prompt hozzáadása
            @self._coordinator_agent.system_prompt
            async def add_user_context(ctx: RunContext[CoordinatorDependencies]) -> str:
                """Felhasználói kontextus hozzáadása a system prompt-hoz."""
                if ctx.deps.user:
                    return f"A felhasználó neve: {ctx.deps.user.name}"
                return ""
        
        return self._coordinator_agent
    
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
            langgraph_state = AgentState(
                messages=[HumanMessage(content=message)],
                current_agent="coordinator",
                user_context={"user": user},
                session_data={"session_id": session_id},
                error_count=0,
                retry_attempts=0
            )
            
            # LangGraph workflow futtatása
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
            
            # Kategória meghatározása
            category = MessageCategory.GENERAL
            if any(word in message.lower() for word in ["telefon", "termék", "ár"]):
                category = MessageCategory.PRODUCT_INFO
            elif any(word in message.lower() for word in ["rendelés", "státusz"]):
                category = MessageCategory.ORDER_STATUS
            elif any(word in message.lower() for word in ["ajánl", "javasol"]):
                category = MessageCategory.RECOMMENDATION
            elif any(word in message.lower() for word in ["kedvezmény", "akció"]):
                category = MessageCategory.MARKETING
            
            # Válasz létrehozása
            response = AgentResponse(
                agent_type=AgentType.COORDINATOR,
                response_text=response_text,
                confidence=0.9,  # LangGraph workflow biztonsága
                metadata={
                    "category": category.value,
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
                agent_type=AgentType.COORDINATOR,
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
_coordinator_agent: Optional[CoordinatorAgent] = None


def get_coordinator_agent() -> CoordinatorAgent:
    """
    Koordinátor agent singleton instance.
    
    Returns:
        CoordinatorAgent instance
    """
    global _coordinator_agent
    if _coordinator_agent is None:
        _coordinator_agent = CoordinatorAgent()
    return _coordinator_agent


async def process_chat_message(
    message: str,
    user: Optional[User] = None,
    session_id: Optional[str] = None
) -> AgentResponse:
    """
    Chat üzenet feldolgozása LangGraph + Pydantic AI hibrid architektúrával.
    
    Args:
        message: Felhasználói üzenet
        user: Felhasználó objektum
        session_id: Session azonosító
        
    Returns:
        Agent válasz
    """
    agent = get_coordinator_agent()
    return await agent.process_message(message, user, session_id) 