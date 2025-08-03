"""
Koordinátor Agent - LangGraph prebuilt create_react_agent használatával.

Ez a modul implementálja a fő koordinátor agent-et, amely:
- Üzenet routing és kategorizálás
- Specializált agent-ek közötti koordináció
- Dependency injection pattern
- Error handling és recovery
"""

import asyncio
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

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
class CoordinatorState:
    """Koordinátor agent állapot."""
    messages: List[BaseMessage]
    user: Optional[User] = None
    session_id: Optional[str] = None
    category: Optional[MessageCategory] = None
    decision: Optional[AgentDecision] = None
    response: Optional[AgentResponse] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CoordinatorAgent:
    """
    Koordinátor Agent - LangGraph prebuilt create_react_agent használatával.
    
    Ez az agent felelős:
    - Üzenet kategorizálás és routing
    - Specializált agent-ek közötti koordináció
    - Dependency injection pattern implementálása
    - Error handling és recovery
    """
    
    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        tools: Optional[List] = None,
        verbose: bool = True
    ):
        """
        Inicializálja a koordinátor agent-et.
        
        Args:
            llm: Language model (alapértelmezett: GPT-4o)
            tools: Tool lista a routing-hoz
            verbose: Részletes logging
        """
        self.llm = llm or ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            max_tokens=1000
        )
        
        self.tools = tools or self._create_default_tools()
        self.verbose = verbose
        
        # LangGraph prebuilt create_react_agent
        self.agent = create_react_agent(
            self.llm,
            self.tools
        )
        
        # State management
        self.state = CoordinatorState(messages=[])
    
    def _create_default_tools(self) -> List:
        """Alapértelmezett tool-ok létrehozása."""
        return [
            self._categorize_message,
            self._route_to_product_agent,
            self._route_to_order_agent,
            self._route_to_recommendation_agent,
            self._route_to_marketing_agent,
            self._handle_general_query
        ]
    
    @tool
    def _categorize_message(self, message: str) -> str:
        """
        Üzenet kategorizálása és routing döntés.
        
        Args:
            message: Felhasználói üzenet
            
        Returns:
            Kategória és routing döntés
        """
        # Egyszerű keyword-based kategorizálás
        message_lower = message.lower()
        
        # Termék információs kérdések
        product_keywords = [
            "termék", "ár", "készlet", "leírás", "specifikáció",
            "product", "price", "stock", "description", "specification"
        ]
        
        # Rendelési státusz kérdések
        order_keywords = [
            "rendelés", "szállítás", "státusz", "tracking", "számla",
            "order", "shipping", "status", "invoice", "delivery"
        ]
        
        # Ajánlási kérdések
        recommendation_keywords = [
            "ajánlás", "hasonló", "népszerű", "legjobb", "kedvenc",
            "recommendation", "similar", "popular", "best", "favorite"
        ]
        
        # Marketing kérdések
        marketing_keywords = [
            "kedvezmény", "kupon", "akció", "promóció", "newsletter",
            "discount", "coupon", "sale", "promotion", "offer"
        ]
        
        # Kategorizálás
        if any(keyword in message_lower for keyword in product_keywords):
            return f"category: {MessageCategory.PRODUCT_INFO.value}"
        elif any(keyword in message_lower for keyword in order_keywords):
            return f"category: {MessageCategory.ORDER_STATUS.value}"
        elif any(keyword in message_lower for keyword in recommendation_keywords):
            return f"category: {MessageCategory.RECOMMENDATION.value}"
        elif any(keyword in message_lower for keyword in marketing_keywords):
            return f"category: {MessageCategory.MARKETING.value}"
        else:
            return f"category: {MessageCategory.GENERAL.value}"
    
    @tool
    def _route_to_product_agent(self, query: str) -> str:
        """
        Termék információs agent-hez routing.
        
        Args:
            query: Felhasználói kérdés
            
        Returns:
            Termék agent válasza
        """
        # TODO: Implementálni a Product Info Agent hívását
        return f"Termék információs agent: {query} - Ez a funkció még fejlesztés alatt áll."
    
    @tool
    def _route_to_order_agent(self, query: str) -> str:
        """
        Rendelési státusz agent-hez routing.
        
        Args:
            query: Felhasználói kérdés
            
        Returns:
            Order agent válasza
        """
        # TODO: Implementálni az Order Status Agent hívását
        return f"Rendelési státusz agent: {query} - Ez a funkció még fejlesztés alatt áll."
    
    @tool
    def _route_to_recommendation_agent(self, query: str) -> str:
        """
        Ajánlási agent-hez routing.
        
        Args:
            query: Felhasználói kérdés
            
        Returns:
            Recommendation agent válasza
        """
        # TODO: Implementálni a Recommendation Agent hívását
        return f"Ajánlási agent: {query} - Ez a funkció még fejlesztés alatt áll."
    
    @tool
    def _route_to_marketing_agent(self, query: str) -> str:
        """
        Marketing agent-hez routing.
        
        Args:
            query: Felhasználói kérdés
            
        Returns:
            Marketing agent válasza
        """
        # TODO: Implementálni a Marketing Agent hívását
        return f"Marketing agent: {query} - Ez a funkció még fejlesztés alatt áll."
    
    @tool
    def _handle_general_query(self, query: str) -> str:
        """
        Általános kérdések kezelése.
        
        Args:
            query: Felhasználói kérdés
            
        Returns:
            Általános válasz
        """
        return f"Általános kérdés: {query} - Miben segíthetek?"
    
    async def process_message(
        self,
        message: str,
        user: Optional[User] = None,
        session_id: Optional[str] = None
    ) -> AgentResponse:
        """
        Üzenet feldolgozása a koordinátor agent-tel.
        
        Args:
            message: Felhasználói üzenet
            user: Felhasználó objektum
            session_id: Session azonosító
            
        Returns:
            Agent válasz
        """
        try:
            # State frissítése
            self.state.messages.append(HumanMessage(content=message))
            self.state.user = user
            self.state.session_id = session_id
            
            # LangGraph agent hívása
            result = await self.agent.ainvoke({
                "messages": self.state.messages
            })
            
            # Válasz feldolgozása
            response = AgentResponse(
                agent_type=AgentType.COORDINATOR,
                response_text=result["messages"][-1].content,
                confidence=0.9,
                metadata={
                    "category": self.state.category.value if self.state.category else None,
                    "session_id": session_id,
                    "user_id": user.id if user else None
                }
            )
            
            # State frissítése
            self.state.response = response
            self.state.messages.append(AIMessage(content=response.response_text))
            
            return response
            
        except Exception as e:
            # Error handling
            error_response = AgentResponse(
                agent_type=AgentType.COORDINATOR,
                response_text=f"Sajnálom, hiba történt: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)}
            )
            return error_response
    
    def get_state(self) -> CoordinatorState:
        """Aktuális állapot lekérése."""
        return self.state
    
    def reset_state(self):
        """Állapot visszaállítása."""
        self.state = CoordinatorState(messages=[])


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
    Chat üzenet feldolgozása a koordinátor agent-tel.
    
    Args:
        message: Felhasználói üzenet
        user: Felhasználó objektum
        session_id: Session azonosító
        
    Returns:
        Agent válasz
    """
    agent = get_coordinator_agent()
    return await agent.process_message(message, user, session_id) 