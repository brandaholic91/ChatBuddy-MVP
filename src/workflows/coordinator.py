"""
Koordinátor Agent - Refactored LangGraph + Pydantic AI architektúra.

Ez a modul implementálja a fő koordinátor agent-et az új egységes
LangGraph workflow architektúrával.
"""

import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from ..models.agent import AgentType, AgentResponse, LangGraphState
from ..models.user import User
from ..utils.state_management import create_initial_state, get_state_summary
from .langgraph_workflow import get_workflow_manager


@dataclass
class CoordinatorDependencies:
    """Koordinátor agent függőségei."""
    user: Optional[User] = None
    session_id: Optional[str] = None
    llm: Optional[ChatOpenAI] = None
    supabase_client: Optional[Any] = None
    webshop_api: Optional[Any] = None
    security_context: Optional[Any] = None
    audit_logger: Optional[Any] = None


class CoordinatorAgent:
    """
    Koordinátor Agent - LangGraph + Pydantic AI hibrid architektúra.
    
    Ez az agent koordinálja a különböző szakértő agent-eket a LangGraph
    workflow segítségével.
    """
    
    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        verbose: bool = True
    ):
        self.llm = llm
        self.verbose = verbose
        self._workflow_manager = get_workflow_manager()
    
    async def process_message(
        self,
        message: str,
        user: Optional[User] = None,
        session_id: Optional[str] = None,
        dependencies: Optional[CoordinatorDependencies] = None
    ) -> AgentResponse:
        """
        Üzenet feldolgozása a koordinátor agent-tel.
        
        Args:
            message: Felhasználói üzenet
            user: Felhasználó objektum
            session_id: Session azonosító
            dependencies: Koordinátor függőségei
            
        Returns:
            Agent válasz
        """
        try:
            # Prepare dependencies
            if dependencies is None:
                dependencies = CoordinatorDependencies(
                    user=user,
                    session_id=session_id,
                    llm=self.llm
                )
            
            # Create initial LangGraph state
            initial_state = create_initial_state(
                user_message=message,
                user_context={
                    "user_id": user.id if user else None,
                    "email": user.email if user else None,
                    "phone": getattr(user, 'phone', None) if user else None,
                    "preferences": getattr(user, 'preferences', {}) if user else {},
                    "supabase_client": dependencies.supabase_client,
                    "webshop_api": dependencies.webshop_api
                },
                session_data={
                    "session_id": session_id,
                    "timestamp": asyncio.get_event_loop().time()
                },
                security_context=dependencies.security_context,
                audit_logger=dependencies.audit_logger
            )
            
            # Process message through LangGraph workflow
            final_state = await self._workflow_manager.process_message(initial_state)
            
            # Extract response from final state
            response_text = self._extract_response_from_state(final_state)
            confidence = self._extract_confidence_from_state(final_state)
            metadata = self._extract_metadata_from_state(final_state)
            
            # Create agent response
            response = AgentResponse(
                agent_type=AgentType.COORDINATOR,
                response_text=response_text,
                confidence=confidence,
                metadata={
                    "session_id": session_id,
                    "user_id": user.id if user else None,
                    "langgraph_used": True,
                    "workflow_summary": get_state_summary(final_state),
                    **metadata
                }
            )
            
            if self.verbose:
                print(f"Koordinátor Agent válasz: {response_text[:100]}...")
            
            return response
            
        except Exception as e:
            # Error handling
            error_response = AgentResponse(
                agent_type=AgentType.COORDINATOR,
                response_text=f"Sajnálom, hiba történt az üzenet feldolgozása során: {str(e)}",
                confidence=0.0,
                metadata={
                    "error": str(e),
                    "session_id": session_id,
                    "user_id": user.id if user else None,
                    "langgraph_used": True
                }
            )
            
            if self.verbose:
                print(f"Koordinátor Agent hiba: {e}")
            
            return error_response
    
    def _extract_response_from_state(self, state: LangGraphState) -> str:
        """Válasz kinyerése a LangGraph state-ből."""
        try:
            if state.get("messages") and len(state["messages"]) > 1:
                last_message = state["messages"][-1]
                if isinstance(last_message, AIMessage):
                    return last_message.content
                elif hasattr(last_message, 'content'):
                    return str(last_message.content)
            
            # Fallback to error message if available
            if state.get("error_message"):
                return state["error_message"]
            
            return "Sajnálom, nem sikerült válaszolni."
            
        except Exception as e:
            return f"Hiba a válasz kinyerésekor: {str(e)}"
    
    def _extract_confidence_from_state(self, state: LangGraphState) -> float:
        """Bizonyosság kinyerése a LangGraph state-ből."""
        try:
            # Try to get confidence from metadata
            metadata = state.get("metadata", {})
            if "confidence" in metadata:
                return float(metadata["confidence"])
            
            # Try to get from agent-specific metadata
            for key, value in metadata.items():
                if isinstance(value, dict) and "confidence" in value:
                    return float(value["confidence"])
            
            # Default confidence
            return 0.8
            
        except Exception:
            return 0.5
    
    def _extract_metadata_from_state(self, state: LangGraphState) -> Dict[str, Any]:
        """Metaadatok kinyerése a LangGraph state-ből."""
        try:
            metadata = state.get("metadata", {})
            
            # Extract agent-specific information
            extracted_metadata = {}
            
            # Agent type
            if "current_agent" in state:
                extracted_metadata["agent_type"] = state["current_agent"]
            
            # Error information
            if "error_message" in state:
                extracted_metadata["error"] = state["error_message"]
            
            # User context
            if "user_context" in state:
                extracted_metadata["user_context"] = state["user_context"]
            
            # Session data
            if "session_data" in state:
                extracted_metadata["session_data"] = state["session_data"]
            
            # Merge with existing metadata
            extracted_metadata.update(metadata)
            
            return extracted_metadata
            
        except Exception as e:
            return {"metadata_extraction_error": str(e)}
    
    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Beszélgetési előzmények lekérése.
        
        Args:
            session_id: Session azonosító
            limit: Eredmények száma
            
        Returns:
            Beszélgetési előzmények
        """
        try:
            # TODO: Implement conversation history retrieval
            # This would typically query a database or cache
            
            # Mock implementation for now
            return [
                {
                    "timestamp": "2024-12-19T10:00:00Z",
                    "message": "Üdvözöllek!",
                    "response": "Üdvözöllek! Miben segíthetek?",
                    "agent_type": "coordinator"
                }
            ]
            
        except Exception as e:
            if self.verbose:
                print(f"Hiba a beszélgetési előzmények lekérésekor: {e}")
            return []
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Agent státusz lekérése.
        
        Returns:
            Agent státusz információk
        """
        try:
            return {
                "agent_type": "coordinator",
                "status": "active",
                "workflow_manager": "initialized",
                "llm_available": self.llm is not None,
                "verbose_mode": self.verbose
            }
            
        except Exception as e:
            return {
                "agent_type": "coordinator",
                "status": "error",
                "error": str(e)
            }


# Global coordinator agent instance
_coordinator_agent: Optional[CoordinatorAgent] = None


def get_coordinator_agent(
    llm: Optional[ChatOpenAI] = None,
    verbose: bool = True
) -> CoordinatorAgent:
    """
    Koordinátor agent singleton instance.
    
    Args:
        llm: Language model
        verbose: Verbose mode
        
    Returns:
        CoordinatorAgent instance
    """
    global _coordinator_agent
    if _coordinator_agent is None:
        _coordinator_agent = CoordinatorAgent(llm=llm, verbose=verbose)
    return _coordinator_agent


async def process_coordinator_message(
    message: str,
    user: Optional[User] = None,
    session_id: Optional[str] = None,
    dependencies: Optional[CoordinatorDependencies] = None
) -> AgentResponse:
    """
    Koordinátor üzenet feldolgozása.
    
    Args:
        message: Felhasználói üzenet
        user: Felhasználó objektum
        session_id: Session azonosító
        dependencies: Koordinátor függőségei
        
    Returns:
        Agent válasz
    """
    agent = get_coordinator_agent()
    return await agent.process_message(
        message=message,
        user=user,
        session_id=session_id,
        dependencies=dependencies
    ) 