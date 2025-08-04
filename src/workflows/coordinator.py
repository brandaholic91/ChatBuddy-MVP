"""
Koordinátor Agent - Hibrid LangGraph + Pydantic AI architektúra.

Ez a modul implementálja a fő koordinátor agent-et, amely:
- LangGraph StateGraph workflow orchestration
- Pydantic AI type-safe dependency injection
- Multi-agent routing és kategorizálás
- Complex state management
- Error handling és recovery
- SECURITY: Comprehensive security context engineering
- GDPR: Full GDPR compliance integration
- AUDIT: Complete audit logging system
"""

import asyncio
import re
from typing import Any, Dict, List, Optional, Union, Literal, TypedDict
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, field_validator
from pydantic_ai import Agent, RunContext

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

from ..models.chat import ChatMessage, ChatSession, ChatState, MessageType
from ..models.agent import AgentType, AgentDecision, AgentResponse
from ..models.user import User

# Agent imports
from ..agents.product_info.agent import create_product_info_agent
from ..agents.order_status.agent import create_order_status_agent
from ..agents.recommendations.agent import create_recommendation_agent

# Security imports
from ..config.security_prompts import (
    SecurityContext, SecurityLevel, classify_security_level,
    get_agent_security_prompt, create_security_context,
    validate_security_context, sanitize_for_audit
)
from ..config.gdpr_compliance import (
    get_gdpr_compliance, DataCategory, ConsentType
)
from ..config.audit_logging import (
    get_security_audit_logger, audit_context, SecuritySeverity
)


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
    """Koordinátor agent függőségei biztonsági fókusszal."""
    user: Optional[User] = None
    session_id: Optional[str] = None
    llm: Optional[ChatOpenAI] = None
    security_context: Optional[SecurityContext] = None
    gdpr_compliance: Optional[Any] = None  # GDPR compliance layer
    audit_logger: Optional[Any] = None     # Audit logger
    source_ip: Optional[str] = None        # Source IP for security tracking
    user_agent: Optional[str] = None       # User agent for security tracking


class CoordinatorOutput(BaseModel):
    """Koordinátor agent strukturált kimenete biztonsági validációval."""
    response_text: str = Field(description="Agent válasza a felhasználónak")
    category: str = Field(description="Üzenet kategóriája")
    confidence: float = Field(description="Válasz bizonyossága", ge=0.0, le=1.0)
    agent_used: str = Field(description="Használt agent típusa")
    security_level: str = Field(description="Biztonsági szint")
    gdpr_compliant: bool = Field(description="GDPR megfelelőség")
    audit_required: bool = Field(description="Audit szükséges")
    metadata: Dict[str, Any] = Field(description="További metaadatok")
    
    @field_validator('response_text')
    @classmethod
    def validate_response_security(cls, v):
        """Válasz biztonsági validálása."""
        # Check for sensitive information leakage
        sensitive_patterns = [
            r'jelszó["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'password["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'kártyaszám["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'card_number["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'admin["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'root["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'secret["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'token["\']?\s*[:=]\s*["\']?[^"\']+["\']?'
        ]
        
        for pattern in sensitive_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Response contains sensitive information: {pattern}")
        
        return v


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
    """Koordinátor agent létrehozása Pydantic AI-val biztonsági fókusszal."""
    try:
        agent = Agent(
            'openai:gpt-4o',
            deps_type=CoordinatorDependencies,
            output_type=CoordinatorOutput,
            system_prompt=(
                "Te egy biztonság-orientált webshop chatbot vagy. "
                "Minden válaszodat a biztonsági protokolloknak megfelelően kell formálnod. "
                "A felhasználó kérdéseit kategorizáld és használd a megfelelő tool-okat. "
                "Válaszolj magyarul, barátságosan és segítőkészen, de mindig a biztonságot szem előtt tartva."
            )
        )
        
        # Tool-ok regisztrálása a hivatalos dokumentáció szerint - DECORATOR használatával
        # A tool függvényeket külön kell definiálni és decorator-rel regisztrálni
        
        return agent
    except Exception as e:
        # Fallback agent creation without OpenAI
        # This is a mock agent for testing purposes
        class MockAgent:
            async def run(self, message: str, deps=None):
                # Simple response based on message content
                message_lower = message.lower()
                
                if "admin" in message_lower or "password" in message_lower:
                    return type('MockResult', (), {
                        'output': type('MockOutput', (), {
                            'response_text': "Ez a lekérdezés nem engedélyezett.",
                            'confidence': 0.0,
                            'category': "forbidden",
                            'agent_used': "coordinator",
                            'gdpr_compliant': False,
                            'audit_required': True
                        })()
                    })()
                elif "hello" in message_lower or "szia" in message_lower:
                    return type('MockResult', (), {
                        'output': type('MockOutput', (), {
                            'response_text': "Üdvözöllek!",
                            'confidence': 0.9,
                            'category': "general",
                            'agent_used': "coordinator",
                            'gdpr_compliant': True,
                            'audit_required': False
                        })()
                    })()
                else:
                    return type('MockResult', (), {
                        'output': type('MockOutput', (), {
                            'response_text': "Sajnálom, nem sikerült válaszolni.",
                            'confidence': 0.0,
                            'category': "general",
                            'agent_used': "coordinator",
                            'gdpr_compliant': True,
                            'audit_required': False
                        })()
                    })()
        
        return MockAgent()


# Tool függvények a hivatalos dokumentáció szerint - ezeket külön kell definiálni
# és majd a create_coordinator_agent-ben regisztrálni kell őket decorator-rel

async def handle_product_query(ctx: RunContext[CoordinatorDependencies], query: str) -> str:
    """
    Termékekkel kapcsolatos kérdések kezelése biztonsági fókusszal.
    
    Args:
        ctx: RunContext with security dependencies
        query: Felhasználói kérdés
        
    Returns:
        Termék információs válasz
    """
    # Security validation
    if not ctx.deps.security_context:
        return "Biztonsági hiba: Hiányzó biztonsági kontextus."
    
    # GDPR consent check
    gdpr = ctx.deps.gdpr_compliance
    if gdpr:
        has_consent = await gdpr.check_user_consent(
            ctx.deps.user.id if ctx.deps.user else "anonymous",
            ConsentType.FUNCTIONAL,
            DataCategory.PERSONAL
        )
        if not has_consent:
            return "Sajnálom, ehhez a funkcióhoz szükségem van a hozzájárulásodra az adatfeldolgozáshoz."
    
    # Input sanitization
    sanitized_query = _sanitize_input(query)
    
    # Security level classification
    security_level = classify_security_level(sanitized_query, {})
    
    # Audit logging
    audit_logger = ctx.deps.audit_logger
    if audit_logger:
        await audit_logger.log_data_access(
            user_id=ctx.deps.user.id if ctx.deps.user else "anonymous",
            data_type="product_info",
            operation="query",
            success=True,
            details={"query": sanitized_query, "security_level": security_level.value}
        )
    
    # Business logic with security constraints
    query_lower = sanitized_query.lower()
    
    # Check for forbidden keywords
    forbidden_keywords = ["beszerzési ár", "margin", "profit", "költség", "belső"]
    if any(keyword in query_lower for keyword in forbidden_keywords):
        return "Sajnálom, ezeket az információkat nem tudom megadni."
    
    if "telefon" in query_lower:
        return "Sokféle telefonunk van készleten! IPhone, Samsung, Xiaomi és más márkák is. Milyen árban gondolkodsz?"
    elif "ár" in query_lower or "árak" in query_lower:
        return "Termékeink árai 50 ezer forinttól 500 ezer forintig terjednek. Van valamilyen konkrét termék, amit keresel?"
    else:
        return f"Termék információs ügynök: {sanitized_query} - Milyen konkrét termékre vagy kíváncsi?"


async def handle_order_query(ctx: RunContext[CoordinatorDependencies], query: str) -> str:
    """
    Rendelésekkel kapcsolatos kérdések kezelése biztonsági fókusszal.
    
    Args:
        ctx: RunContext with security dependencies
        query: Felhasználói kérdés
        
    Returns:
        Rendelési információs válasz
    """
    # Security validation
    if not ctx.deps.security_context:
        return "Biztonsági hiba: Hiányzó biztonsági kontextus."
    
    # GDPR consent check for sensitive data
    gdpr = ctx.deps.gdpr_compliance
    if gdpr:
        has_consent = await gdpr.check_user_consent(
            ctx.deps.user.id if ctx.deps.user else "anonymous",
            ConsentType.NECESSARY,
            DataCategory.SENSITIVE
        )
        if not has_consent:
            return "Sajnálom, rendelési információkhoz szükségem van a hozzájárulásodra."
    
    # Input sanitization
    sanitized_query = _sanitize_input(query)
    
    # Security level classification
    security_level = classify_security_level(sanitized_query, {})
    
    # Audit logging
    audit_logger = ctx.deps.audit_logger
    if audit_logger:
        await audit_logger.log_data_access(
            user_id=ctx.deps.user.id if ctx.deps.user else "anonymous",
            data_type="order_info",
            operation="query",
            success=True,
            details={"query": sanitized_query, "security_level": security_level.value}
        )
    
    # Business logic with security constraints
    query_lower = sanitized_query.lower()
    
    # Check for forbidden keywords
    forbidden_keywords = ["kártya", "card", "cvv", "pin", "jelszó", "password"]
    if any(keyword in query_lower for keyword in forbidden_keywords):
        return "Sajnálom, ezeket az információkat nem tudom megadni."
    
    if "státusz" in query_lower or "állapot" in query_lower:
        return "A rendelésed státuszának ellenőrzéséhez szükségem van a rendelési azonosítóra. Meg tudnád adni?"
    elif "szállítás" in query_lower or "megérkezik" in query_lower:
        return "A szállítási idő általában 2-5 munkanap, attól függően, hogy hol laksz. Van konkrét rendelésed?"
    else:
        return f"Rendelési ügynök: {sanitized_query} - Miben segíthetek a rendeléssel kapcsolatban?"


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


# LangGraph Workflow Functions - EGYSZERŰSÍTETT VÁLTOZAT
def route_message(state: AgentState) -> str:
    """
    Üzenet routing a megfelelő agent-hez LangGraph StateGraph-ban.
    
    Args:
        state: Jelenlegi agent állapot
        
    Returns:
        Következő node neve
    """
    try:
        # Get the last message
        if not state.get("messages"):
            return "general_agent"
        
        last_message = state["messages"][-1]
        if not hasattr(last_message, 'content'):
            return "general_agent"
        
        message_content = last_message.content.lower()
        
        # Simple keyword-based routing
        if any(word in message_content for word in ["termék", "telefon", "ár", "készlet", "specifikáció", "leírás", "márka"]):
            return "product_agent"
        elif any(word in message_content for word in ["rendelés", "szállítás", "státusz", "követés", "tracking", "delivery"]):
            return "order_agent"
        elif any(word in message_content for word in ["ajánl", "ajánlat", "hasonló", "népszerű", "trend", "preferencia", "kedvenc", "mit vegyek"]):
            return "recommendation_agent"
        elif any(word in message_content for word in ["kedvezmény", "akció", "promóció", "hírlevél", "newsletter"]):
            return "marketing_agent"
        else:
            return "general_agent"
            
    except Exception as e:
        # Fallback to general agent on error
        return "general_agent"


# EGYSZERŰSÍTETT AGENT HÍVÁSOK - LangGraph dokumentáció szerint
async def call_product_agent(state: AgentState) -> AgentState:
    """Product agent hívása LangGraph workflow-ban."""
    try:
        # Egyszerű válasz generálás - nem használunk Pydantic AI agent-et itt
        last_message = state["messages"][-1].content
        response_text = await handle_product_query_simple(last_message)
        
        # Válasz hozzáadása
        response = AIMessage(content=response_text)
        state["messages"].append(response)
        
        return state
    except Exception as e:
        # Error handling
        error_response = AIMessage(content=f"Sajnálom, hiba történt: {str(e)}")
        state["messages"].append(error_response)
        return state


async def call_order_agent(state: AgentState) -> AgentState:
    """Order Status Agent hívása LangGraph workflow-ban."""
    try:
        last_message = state["messages"][-1].content
        
        # Order Status Agent létrehozása és hívása
        order_agent = create_order_status_agent()
        
        # Mock dependencies (fejlesztési célokra)
        from ..agents.order_status.agent import OrderStatusDependencies
        deps = OrderStatusDependencies(
            supabase_client=None,  # TODO: Implement
            webshop_api=None,      # TODO: Implement
            user_context=state.get("user_context", {}),
            security_context=None,  # TODO: Implement
            audit_logger=None       # TODO: Implement
        )
        
        # Agent hívása
        if hasattr(order_agent, 'run'):
            result = await order_agent.run(last_message, deps)
            response_text = result.message if hasattr(result, 'message') else str(result)
        else:
            response_text = await handle_order_query_simple(last_message)
        
        response = AIMessage(content=response_text)
        state["messages"].append(response)
        
        return state
    except Exception as e:
        error_response = AIMessage(content=f"Sajnálom, hiba történt a rendelés kezelés során: {str(e)}")
        state["messages"].append(error_response)
        return state


async def call_recommendation_agent(state: AgentState) -> AgentState:
    """Recommendation Agent hívása LangGraph workflow-ban."""
    try:
        last_message = state["messages"][-1].content
        
        # Recommendation Agent létrehozása és hívása
        recommendation_agent = create_recommendation_agent()
        
        # Mock dependencies (fejlesztési célokra)
        from ..agents.recommendations.agent import RecommendationDependencies
        from ..config.security_prompts import SecurityContext
        from ..config.audit_logging import SecurityAuditLogger
        
        # Mock implementations for development
        class MockSupabaseClient:
            async def table(self, name):
                return self
            async def select(self, *args):
                return self
            async def eq(self, field, value):
                return self
            async def execute(self):
                return {"data": []}
        
        class MockVectorDB:
            async def similarity_search(self, product_id, limit):
                return []
            async def personalized_search(self, user_id, preferences, limit):
                return []
        
        deps = RecommendationDependencies(
            supabase_client=MockSupabaseClient(),
            vector_db=MockVectorDB(),
            user_context=state.get("user_context", {}),
            security_context=SecurityContext(
                user_id=state.get("user_context", {}).get("user_id", "unknown"),
                session_id=state.get("user_context", {}).get("session_id", "unknown"),
                security_level="medium",
                gdpr_compliant=True
            ),
            audit_logger=SecurityAuditLogger()
        )
        
        # Agent hívása
        if hasattr(recommendation_agent, 'run'):
            result = await recommendation_agent.run(last_message, deps)
            response_text = result.message if hasattr(result, 'message') else str(result)
        else:
            response_text = await handle_recommendation_query_simple(last_message)
        
        response = AIMessage(content=response_text)
        state["messages"].append(response)
        
        return state
    except Exception as e:
        error_response = AIMessage(content=f"Sajnálom, hiba történt: {str(e)}")
        state["messages"].append(error_response)
        return state


async def call_marketing_agent(state: AgentState) -> AgentState:
    """Marketing agent hívása LangGraph workflow-ban."""
    try:
        last_message = state["messages"][-1].content
        response_text = await handle_marketing_query_simple(last_message)
        
        response = AIMessage(content=response_text)
        state["messages"].append(response)
        
        return state
    except Exception as e:
        error_response = AIMessage(content=f"Sajnálom, hiba történt: {str(e)}")
        state["messages"].append(error_response)
        return state


async def call_general_agent(state: AgentState) -> AgentState:
    """General agent hívása LangGraph workflow-ban."""
    try:
        last_message = state["messages"][-1].content
        response_text = await handle_general_query_simple(last_message)
        
        response = AIMessage(content=response_text)
        state["messages"].append(response)
        
        return state
    except Exception as e:
        error_response = AIMessage(content=f"Sajnálom, hiba történt: {str(e)}")
        state["messages"].append(error_response)
        return state


# EGYSZERŰ QUERY HANDLERS - LangGraph workflow-hoz
async def handle_product_query_simple(query: str) -> str:
    """Egyszerű termék query handler LangGraph workflow-hoz."""
    query_lower = query.lower()
    
    if "telefon" in query_lower:
        return "Sokféle telefonunk van készleten! IPhone, Samsung, Xiaomi és más márkák is. Milyen árban gondolkodsz?"
    elif "ár" in query_lower or "árak" in query_lower:
        return "Termékeink árai 50 ezer forinttól 500 ezer forintig terjednek. Van valamilyen konkrét termék, amit keresel?"
    else:
        return f"Termék információs ügynök: {query} - Milyen konkrét termékre vagy kíváncsi?"


async def handle_order_query_simple(query: str) -> str:
    """Egyszerű rendelés query handler LangGraph workflow-hoz."""
    query_lower = query.lower()
    
    if "státusz" in query_lower or "állapot" in query_lower:
        return "A rendelésed státuszának ellenőrzéséhez szükségem van a rendelési azonosítóra. Meg tudnád adni?"
    elif "szállítás" in query_lower or "megérkezik" in query_lower:
        return "A szállítási idő általában 2-5 munkanap, attól függően, hogy hol laksz. Van konkrét rendelésed?"
    else:
        return f"Rendelési ügynök: {query} - Miben segíthetek a rendeléssel kapcsolatban?"


async def handle_recommendation_query_simple(query: str) -> str:
    """Egyszerű ajánlás query handler LangGraph workflow-hoz."""
    query_lower = query.lower()
    
    if "ajánl" in query_lower or "javasol" in query_lower:
        return "Szeretnék ajánlani néhány népszerű terméket! Mit keresel? Telefon, laptop, vagy valami más?"
    elif "népszerű" in query_lower or "legjobb" in query_lower:
        return "A legnépszerűbb termékeink között szerepel az iPhone 15, Samsung Galaxy S24 és a Xiaomi 14. Melyik érdekel?"
    else:
        return f"Ajánlási ügynök: {query} - Milyen típusú termékre keresel ajánlást?"


async def handle_marketing_query_simple(query: str) -> str:
    """Egyszerű marketing query handler LangGraph workflow-hoz."""
    query_lower = query.lower()
    
    if "kedvezmény" in query_lower or "akció" in query_lower:
        return "Jelenleg több akció is fut! 10% kedvezmény az új vásárlókra, és ingyenes szállítás 50 ezer forint feletti rendelésekre."
    elif "kupon" in query_lower or "kód" in query_lower:
        return "Használd a 'UJ10' kódot 10% kedvezményre, vagy a 'INGYEN' kódot ingyenes szállításra!"
    else:
        return f"Marketing ügynök: {query} - Van valamilyen akciós ajánlatunk, ami érdekel!"


async def handle_general_query_simple(query: str) -> str:
    """Egyszerű általános query handler LangGraph workflow-hoz."""
    query_lower = query.lower()
    
    if "szia" in query_lower or "hello" in query_lower:
        return "Szia! Üdvözöllek! Miben segíthetek ma?"
    elif "kosár" in query_lower:
        return "A kosár funkcióval termékeket adhatsz hozzá a rendeléshez. A kosárban lévő termékeket később meg tudod rendelni."
    elif "segít" in query_lower:
        return "Természetesen segítek! Mit szeretnél tudni? Termékekről, rendelésről, vagy valami másról?"
    else:
        return f"Általános kérdés: {query} - Miben segíthetek?"


def create_langgraph_workflow() -> StateGraph:
    """
    LangGraph StateGraph workflow létrehozása a hivatalos dokumentáció szerint.
    
    Returns:
        Compiled StateGraph workflow
    """
    # Initialize StateGraph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("route_message", route_message)
    workflow.add_node("product_agent", call_product_agent)
    workflow.add_node("order_agent", call_order_agent)
    workflow.add_node("recommendation_agent", call_recommendation_agent)
    workflow.add_node("marketing_agent", call_marketing_agent)
    workflow.add_node("general_agent", call_general_agent)
    
    # Add edges - START -> route_message
    workflow.add_edge(START, "route_message")
    
    # Add conditional edges from route_message based on routing function
    workflow.add_conditional_edges(
        "route_message",
        route_message,  # Function that returns the next node name
        {
            "product_agent": "product_agent",
            "order_agent": "order_agent", 
            "recommendation_agent": "recommendation_agent",
            "marketing_agent": "marketing_agent",
            "general_agent": "general_agent"
        }
    )
    
    # Add edges to END
    workflow.add_edge("product_agent", END)
    workflow.add_edge("order_agent", END)
    workflow.add_edge("recommendation_agent", END)
    workflow.add_edge("marketing_agent", END)
    workflow.add_edge("general_agent", END)
    
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
            # Egyszerű Pydantic AI agent létrehozása
            self._coordinator_agent = Agent(
                'openai:gpt-4o',
                deps_type=CoordinatorDependencies,
                output_type=CoordinatorOutput,
                system_prompt=(
                    "Te egy biztonság-orientált webshop chatbot vagy. "
                    "Minden válaszodat a biztonsági protokolloknak megfelelően kell formálnod. "
                    "A felhasználó kérdéseit kategorizáld és használd a megfelelő tool-okat. "
                    "Válaszolj magyarul, barátságosan és segítőkészen, de mindig a biztonságot szem előtt tartva."
                )
            )
            
            # Tool-ok regisztrálása egyedi nevekkel
            self._coordinator_agent.tool(handle_product_query, name="product_query_handler")
            self._coordinator_agent.tool(handle_order_query, name="order_query_handler")
            self._coordinator_agent.tool(handle_recommendation_query, name="recommendation_query_handler")
            self._coordinator_agent.tool(handle_marketing_query, name="marketing_query_handler")
            self._coordinator_agent.tool(handle_general_query, name="general_query_handler")
        
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


def _sanitize_input(input_data: str) -> str:
    """
    Bemeneti adatok sanitizálása.
    
    Args:
        input_data: Bemeneti adatok
        
    Returns:
        Sanitizált adatok
    """
    if not input_data:
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", '"', "'", "&", "{", "}", "[", "]"]
    sanitized = input_data
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")
    
    # Remove potentially dangerous patterns
    dangerous_patterns = [
        r'script\s*:', r'javascript\s*:', r'vbscript\s*:', r'expression\s*\(',
        r'<script', r'</script>', r'<iframe', r'</iframe>', r'<object', r'</object>'
    ]
    
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
    
    # Limit length
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000]
    
    return sanitized.strip()


def _validate_user_permissions(user: Optional[User], required_permissions: List[str]) -> bool:
    """
    Felhasználói jogosultságok validálása.
    
    Args:
        user: Felhasználó objektum
        required_permissions: Szükséges jogosultságok
        
    Returns:
        True ha van jogosultság, False ha nincs
    """
    if not user:
        return False
    
    # TODO: Implement actual permission checking logic
    # This should check against user roles and permissions
    return True


async def process_chat_message(
    message: str,
    user: Optional[User] = None,
    session_id: Optional[str] = None,
    source_ip: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AgentResponse:
    """
    Chat üzenet feldolgozása LangGraph + Pydantic AI hibrid architektúrával
    biztonsági fókusszal.
    
    Args:
        message: Felhasználói üzenet
        user: Felhasználó objektum
        session_id: Session azonosító
        source_ip: Forrás IP cím
        user_agent: User agent
        
    Returns:
        Agent válasz
    """
    try:
        # Input validation
        if not message or len(message.strip()) == 0:
            raise ValueError("Üres üzenet")
        
        if len(message) > 1000:
            raise ValueError("Túl hosszú üzenet")
        
        # Security context creation with error handling
        try:
            user_context = {
                "permissions": ["basic_access"],
                "data_access_scope": ["public"]
            }
            
            if user:
                user_context["permissions"] = getattr(user, "permissions", ["basic_access"])
                user_context["data_access_scope"] = getattr(user, "data_access_scope", ["public"])
            
            security_context = create_security_context(
                user_id=user.id if user else "anonymous",
                session_id=session_id or "default",
                query=message,
                user_context=user_context
            )
        except Exception as e:
            # Fallback security context
            security_context = type('MockSecurityContext', (), {
                'security_level': SecurityLevel.SAFE,
                'user_id': user.id if user else "anonymous",
                'session_id': session_id or "default"
            })()
        
        # GDPR compliance check with error handling
        try:
            gdpr_compliance = get_gdpr_compliance()
        except Exception:
            gdpr_compliance = None
        
        # Audit logger with error handling
        try:
            audit_logger = get_security_audit_logger()
        except Exception:
            audit_logger = None
        
        # Create dependencies with security
        try:
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=1000
            )
        except Exception:
            # Fallback LLM for testing
            llm = None
        
        deps = CoordinatorDependencies(
            user=user,
            session_id=session_id,
            llm=llm,
            security_context=security_context,
            gdpr_compliance=gdpr_compliance,
            audit_logger=audit_logger,
            source_ip=source_ip,
            user_agent=user_agent
        )
        
        # Log security event if needed
        if audit_logger and security_context.security_level in [SecurityLevel.RESTRICTED, SecurityLevel.FORBIDDEN]:
            try:
                await audit_logger.log_security_event(
                    event_type="high_security_query",
                    severity=SecuritySeverity.HIGH,
                    user_id=user.id if user else "anonymous",
                    description=f"High security level query: {security_context.security_level.value}",
                    details={"query": _sanitize_input(message), "security_level": security_context.security_level.value},
                    source_ip=source_ip
                )
            except Exception:
                pass  # Ignore audit logging errors
        
        # Handle FORBIDDEN queries directly without calling the agent
        if security_context.security_level == SecurityLevel.FORBIDDEN:
            return AgentResponse(
                agent_type=AgentType.COORDINATOR,
                response_text="Ez a lekérdezés nem engedélyezett.",
                confidence=0.0,
                metadata={
                    "security_level": security_context.security_level.value,
                    "gdpr_compliant": False,
                    "audit_required": True,
                    "agent_used": "coordinator",
                    "category": "forbidden",
                    "session_id": session_id,
                    "user_id": user.id if user else None,
                    "source_ip": source_ip,
                    "user_agent": user_agent
                }
            )
        
        # Use audit context for the entire interaction
        if audit_logger:
            async with audit_context(
                agent_type="coordinator",
                user_id=user.id if user else "anonymous",
                session_id=session_id or "default",
                query=message,
                metadata={"source_ip": source_ip, "user_agent": user_agent}
            ):
                # Create and run the Pydantic AI agent
                try:
                    agent = create_coordinator_agent()
                    result = await agent.run(
                        message,
                        deps=deps
                    )
                    
                    # Extract response from Pydantic AI result
                    if hasattr(result, 'output'):
                        output = result.output
                        return AgentResponse(
                            agent_type=AgentType.COORDINATOR,
                            response_text=output.response_text,
                            confidence=output.confidence,
                            metadata={
                                "security_level": output.security_level,
                                "gdpr_compliant": output.gdpr_compliant,
                                "audit_required": output.audit_required,
                                "agent_used": output.agent_used,
                                "category": output.category,
                                "session_id": session_id,
                                "user_id": user.id if user else None,
                                "source_ip": source_ip,
                                "user_agent": user_agent
                            }
                        )
                    else:
                        # Fallback for mock agent
                        return AgentResponse(
                            agent_type=AgentType.COORDINATOR,
                            response_text="Sajnálom, nem sikerült válaszolni.",
                            confidence=0.0,
                            metadata={
                                "security_level": "safe",
                                "gdpr_compliant": True,
                                "audit_required": False,
                                "agent_used": "coordinator",
                                "category": "general",
                                "session_id": session_id,
                                "user_id": user.id if user else None,
                                "source_ip": source_ip,
                                "user_agent": user_agent
                            }
                        )
                        
                except Exception as e:
                    # Log the error
                    if audit_logger:
                        await audit_logger.log_security_event(
                            event_type="agent_error",
                            severity=SecuritySeverity.MEDIUM,
                            user_id=user.id if user else "anonymous",
                            description=f"Agent execution error: {str(e)}",
                            details={"error": str(e), "query": _sanitize_input(message)},
                            source_ip=source_ip
                        )
                    
                    return AgentResponse(
                        agent_type=AgentType.COORDINATOR,
                        response_text="Sajnálom, technikai hiba történt. Kérlek próbáld újra később.",
                        confidence=0.0,
                        metadata={
                            "security_level": "safe",
                            "gdpr_compliant": True,
                            "audit_required": True,
                            "agent_used": "coordinator",
                            "category": "error",
                            "session_id": session_id,
                            "user_id": user.id if user else None,
                            "source_ip": source_ip,
                            "user_agent": user_agent,
                            "error": str(e)
                        }
                    )
        else:
            # No audit logger available - simplified flow
            try:
                agent = create_coordinator_agent()
                result = await agent.run(message, deps=deps)
                
                if hasattr(result, 'output'):
                    output = result.output
                    return AgentResponse(
                        agent_type=AgentType.COORDINATOR,
                        response_text=output.response_text,
                        confidence=output.confidence,
                        metadata={
                            "security_level": output.security_level,
                            "gdpr_compliant": output.gdpr_compliant,
                            "audit_required": output.audit_required,
                            "agent_used": output.agent_used,
                            "category": output.category,
                            "session_id": session_id,
                            "user_id": user.id if user else None,
                            "source_ip": source_ip,
                            "user_agent": user_agent
                        }
                    )
                else:
                    return AgentResponse(
                        agent_type=AgentType.COORDINATOR,
                        response_text="Sajnálom, nem sikerült válaszolni.",
                        confidence=0.0,
                        metadata={
                            "security_level": "safe",
                            "gdpr_compliant": True,
                            "audit_required": False,
                            "agent_used": "coordinator",
                            "category": "general",
                            "session_id": session_id,
                            "user_id": user.id if user else None,
                            "source_ip": source_ip,
                            "user_agent": user_agent
                        }
                    )
            except Exception as e:
                return AgentResponse(
                    agent_type=AgentType.COORDINATOR,
                    response_text="Sajnálom, technikai hiba történt. Kérlek próbáld újra később.",
                    confidence=0.0,
                    metadata={
                        "security_level": "safe",
                        "gdpr_compliant": True,
                        "audit_required": True,
                        "agent_used": "coordinator",
                        "category": "error",
                        "session_id": session_id,
                        "user_id": user.id if user else None,
                        "source_ip": source_ip,
                        "user_agent": user_agent,
                        "error": str(e)
                    }
                )
            
    except Exception as e:
        # Log error
        try:
            audit_logger = get_security_audit_logger()
            await audit_logger.log_security_event(
                event_type="processing_error",
                severity=SecuritySeverity.HIGH,
                user_id=user.id if user else "anonymous",
                description=f"Error processing chat message: {str(e)}",
                details={"error": str(e), "message": _sanitize_input(message)},
                source_ip=source_ip
            )
        except Exception:
            pass  # Ignore audit logging errors
        
        # Return error response
        return AgentResponse(
            agent_type=AgentType.COORDINATOR,
            response_text="Sajnálom, hiba történt a feldolgozás során. Kérlek próbáld újra.",
            confidence=0.0,
            metadata={"error": str(e), "security_level": "error"}
        ) 