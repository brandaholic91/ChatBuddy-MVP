"""
LangGraph Workflow Implementation for ChatBuddy MVP.

This module implements the unified LangGraph workflow that integrates
Pydantic AI agents as tools in a coordinated manner.
"""

from typing import Dict, Any, Optional
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, START, END

from ..models.agent import LangGraphState
from ..utils.state_management import (
    update_state_with_response,
    update_state_with_error,
    finalize_state
)
from ..agents.product_info.agent import (
    call_product_info_agent,
    ProductInfoDependencies
)
from ..agents.order_status.agent import (
    call_order_status_agent,
    OrderStatusDependencies
)
from ..agents.recommendations.agent import (
    call_recommendation_agent,
    RecommendationDependencies
)
from ..agents.marketing.agent import (
    call_marketing_agent,
    MarketingDependencies
)
from ..agents.general.agent import (
    call_general_agent,
    GeneralDependencies
)
# Security imports
from ..config.security import get_threat_detector, InputValidator
from ..config.gdpr_compliance import get_gdpr_compliance, ConsentType, DataCategory


def route_message(state: LangGraphState) -> Dict[str, str]:
    """
    Üzenet routing a megfelelő agent-hez LangGraph StateGraph-ban.
    
    Args:
        state: Jelenlegi agent állapot
        
    Returns:
        Következő node neve dict formátumban
    """
    try:
        # Security validation before routing
        if not _validate_security_context(state):
            return {"next": "general_agent"}
        
        # Get the last message
        if not state.get("messages"):
            return {"next": "general_agent"}
        
        last_message = state["messages"][-1]
        if not hasattr(last_message, 'content'):
            return {"next": "general_agent"}
        
        message_content = last_message.content.lower()
        
        # Input sanitization
        sanitized_content = InputValidator.sanitize_string(message_content)
        if sanitized_content != message_content:
            # Update the message with sanitized content
            last_message.content = sanitized_content
            message_content = sanitized_content.lower()
        
        # Threat detection
        threat_detector = get_threat_detector()
        threat_analysis = threat_detector.detect_threats(message_content)
        
        if threat_analysis["risk_level"] == "high":
            # Log security event
            if state.get("audit_logger"):
                state["audit_logger"].log_security_event(
                    "high_threat_detected",
                    state.get("user_context", {}).get("user_id", "anonymous"),
                    threat_analysis
                )
            return {"next": "general_agent"}
        
        # Keyword-based routing (prioritized order)
        if any(word in message_content for word in [
            "kedvezmény", "akció", "promóció", "hírlevél", 
            "newsletter", "kupon", "kód"
        ]):
            return {"next": "marketing_agent"}
        elif any(word in message_content for word in [
            "ajánl", "ajánlat", "hasonló", "népszerű", "trend", 
            "preferencia", "kedvenc", "mit vegyek"
        ]):
            return {"next": "recommendation_agent"}
        elif any(word in message_content for word in [
            "rendelés", "szállítás", "státusz", "követés", 
            "tracking", "delivery", "megérkezik"
        ]):
            return {"next": "order_agent"}
        elif any(word in message_content for word in [
            "termék", "telefon", "ár", "készlet", "specifikáció", 
            "leírás", "márka", "keres", "talál", "milyen"
        ]):
            return {"next": "product_agent"}
        else:
            return {"next": "general_agent"}
            
    except Exception as e:
        # Fallback to general agent on error
        return {"next": "general_agent"}


def _validate_security_context(state: LangGraphState) -> bool:
    """Validálja a security context-et."""
    try:
        # Check if security context exists
        security_context = state.get("security_context")
        if not security_context:
            return True  # Allow if no security context (for development)
        
        # Add additional security validations here
        return True
        
    except Exception:
        return False


async def _validate_gdpr_consent(
    state: LangGraphState,
    consent_type: ConsentType,
    data_category: DataCategory
) -> bool:
    """Validálja a GDPR hozzájárulást."""
    try:
        gdpr_compliance = state.get("gdpr_compliance")
        if not gdpr_compliance:
            return True  # Allow if no GDPR compliance (for development)
        
        user_id = state.get("user_context", {}).get("user_id", "anonymous")
        
        # Check consent
        has_consent = await gdpr_compliance.check_user_consent(
            user_id=user_id,
            consent_type=consent_type,
            data_category=data_category
        )
        
        return has_consent
        
    except Exception:
        return True  # Allow on error (fail open for development)


    async def call_product_agent(state: LangGraphState) -> LangGraphState:
        """Product agent hívása LangGraph workflow-ban."""
        try:
            # Security validation
            if not _validate_security_context(state):
                error_response = AIMessage(content="Biztonsági hiba: Hiányzó biztonsági kontextus.")
                state["messages"].append(error_response)
                return state
            
            # GDPR consent check
            if not await _validate_gdpr_consent(state, ConsentType.FUNCTIONAL, DataCategory.PERSONAL):
                error_response = AIMessage(content="Sajnálom, ehhez a funkcióhoz szükségem van a hozzájárulásodra.")
                state["messages"].append(error_response)
                return state
            
            # Get the last message
            last_message = state["messages"][-1].content
            
            # Create dependencies
            deps = ProductInfoDependencies(
                supabase_client=state.get("user_context", {}).get("supabase_client"),
                webshop_api=state.get("user_context", {}).get("webshop_api"),
                user_context=state.get("user_context", {}),
                security_context=state.get("security_context"),
                audit_logger=state.get("audit_logger")
            )
            
            # Call Pydantic AI agent
            result = await call_product_info_agent(last_message, deps)
            
            # Audit logging
            audit_logger = state.get("audit_logger")
            if audit_logger:
                await audit_logger.log_data_access(
                    user_id=state.get("user_context", {}).get("user_id", "anonymous"),
                    data_type="product_info",
                    operation="query",
                    success=True
                )
            
            # Update state with response
            state = update_state_with_response(
                state=state,
                response_text=result.response_text,
                agent_name="product_agent",
                confidence=result.confidence,
                metadata={
                    "category": result.category,
                    "product_info": result.product_info.dict() if result.product_info else None,
                    "search_results": result.search_results.dict() if result.search_results else None,
                    **result.metadata
                }
            )
            
            return state
            
        except Exception as e:
            # Error handling
            state = update_state_with_error(
            state=state,
            error_message=f"Product agent hiba: {str(e)}",
            agent_name="product_agent"
        )
        return state


async def call_order_agent(state: LangGraphState) -> LangGraphState:
    """Order agent hívása LangGraph workflow-ban."""
    try:
        # Security validation
        if not _validate_security_context(state):
            error_response = AIMessage(content="Biztonsági hiba: Hiányzó biztonsági kontextus.")
            state["messages"].append(error_response)
            return state
        
        # GDPR consent check
        if not await _validate_gdpr_consent(state, ConsentType.FUNCTIONAL, DataCategory.PERSONAL):
            error_response = AIMessage(content="Sajnálom, ehhez a funkcióhoz szükségem van a hozzájárulásodra.")
            state["messages"].append(error_response)
            return state
        
        # Get the last message
        last_message = state["messages"][-1].content
        
        # Create dependencies
        deps = OrderStatusDependencies(
            supabase_client=state.get("user_context", {}).get("supabase_client"),
            webshop_api=state.get("user_context", {}).get("webshop_api"),
            user_context=state.get("user_context", {}),
            security_context=state.get("security_context"),
            audit_logger=state.get("audit_logger")
        )
        
        # Call Pydantic AI agent
        result = await call_order_status_agent(last_message, deps)
        
        # Audit logging
        audit_logger = state.get("audit_logger")
        if audit_logger:
            await audit_logger.log_data_access(
                user_id=state.get("user_context", {}).get("user_id", "anonymous"),
                data_type="order_info",
                operation="query",
                success=True
            )
        
        # Update state with response
        state = update_state_with_response(
            state=state,
            response_text=result.response_text,
            agent_name="order_agent",
            confidence=result.confidence,
            metadata={
                "order_info": result.order_info.dict() if result.order_info else None,
                "status_summary": result.status_summary,
                "next_steps": result.next_steps,
                **result.metadata
            }
        )
        
        return state
        
    except Exception as e:
        # Error handling
        state = update_state_with_error(
            state=state,
            error_message=f"Order agent hiba: {str(e)}",
            agent_name="order_agent"
        )
        return state


async def call_recommendation_agent(state: LangGraphState) -> LangGraphState:
    """Recommendation agent hívása LangGraph workflow-ban."""
    try:
        # Security validation
        if not _validate_security_context(state):
            error_response = AIMessage(content="Biztonsági hiba: Hiányzó biztonsági kontextus.")
            state["messages"].append(error_response)
            return state
        
        # GDPR consent check
        if not await _validate_gdpr_consent(state, ConsentType.FUNCTIONAL, DataCategory.PERSONAL):
            error_response = AIMessage(content="Sajnálom, ehhez a funkcióhoz szükségem van a hozzájárulásodra.")
            state["messages"].append(error_response)
            return state
        
        # Get the last message
        last_message = state["messages"][-1].content
        
        # Create dependencies
        deps = RecommendationDependencies(
            supabase_client=state.get("user_context", {}).get("supabase_client"),
            webshop_api=state.get("user_context", {}).get("webshop_api"),
            user_context=state.get("user_context", {}),
            security_context=state.get("security_context"),
            audit_logger=state.get("audit_logger")
        )
        
        # Call Pydantic AI agent
        result = await call_recommendation_agent(last_message, deps)
        
        # Audit logging
        audit_logger = state.get("audit_logger")
        if audit_logger:
            await audit_logger.log_data_access(
                user_id=state.get("user_context", {}).get("user_id", "anonymous"),
                data_type="recommendations",
                operation="query",
                success=True
            )
        
        # Update state with response
        state = update_state_with_response(
            state=state,
            response_text=result.response_text,
            agent_name="recommendation_agent",
            confidence=result.confidence,
            metadata={
                "recommendations": [rec.dict() for rec in result.recommendations],
                "category": result.category,
                "user_preferences": result.user_preferences,
                **result.metadata
            }
        )
        
        return state
        
    except Exception as e:
        # Error handling
        state = update_state_with_error(
            state=state,
            error_message=f"Recommendation agent hiba: {str(e)}",
            agent_name="recommendation_agent"
        )
        return state


async def call_marketing_agent(state: LangGraphState) -> LangGraphState:
    """Marketing agent hívása LangGraph workflow-ban."""
    try:
        # Security validation
        if not _validate_security_context(state):
            error_response = AIMessage(content="Biztonsági hiba: Hiányzó biztonsági kontextus.")
            state["messages"].append(error_response)
            return state
        
        # GDPR consent check for marketing
        if not _validate_gdpr_consent(state, ConsentType.MARKETING, DataCategory.MARKETING):
            error_response = AIMessage(content="Sajnálom, a marketing funkciókhoz szükségem van a marketing hozzájárulásodra.")
            state["messages"].append(error_response)
            return state
        
        # Get the last message
        last_message = state["messages"][-1].content
        
        # Create dependencies
        deps = MarketingDependencies(
            supabase_client=state.get("user_context", {}).get("supabase_client"),
            webshop_api=state.get("user_context", {}).get("webshop_api"),
            user_context=state.get("user_context", {}),
            security_context=state.get("security_context"),
            audit_logger=state.get("audit_logger")
        )
        
        # Call Pydantic AI agent
        result = await call_marketing_agent(last_message, deps)
        
        # Audit logging
        audit_logger = state.get("audit_logger")
        if audit_logger:
            await audit_logger.log_data_access(
                user_id=state.get("user_context", {}).get("user_id", "anonymous"),
                data_type="marketing",
                operation="query",
                success=True
            )
        
        # Update state with response
        state = update_state_with_response(
            state=state,
            response_text=result.response_text,
            agent_name="marketing_agent",
            confidence=result.confidence,
            metadata={
                "promotions": [promo.dict() for promo in result.promotions],
                "newsletters": [news.dict() for news in result.newsletters],
                "personalized_offers": result.personalized_offers,
                **result.metadata
            }
        )
        
        return state
        
    except Exception as e:
        # Error handling
        state = update_state_with_error(
            state=state,
            error_message=f"Marketing agent hiba: {str(e)}",
            agent_name="marketing_agent"
        )
        return state


async def call_general_agent(state: LangGraphState) -> LangGraphState:
    """General agent hívása LangGraph workflow-ban."""
    try:
        # Security validation
        if not _validate_security_context(state):
            error_response = AIMessage(content="Biztonsági hiba: Hiányzó biztonsági kontextus.")
            state["messages"].append(error_response)
            return state
        
        # GDPR consent check for basic functionality
        if not _validate_gdpr_consent(state, ConsentType.NECESSARY, DataCategory.TECHNICAL):
            error_response = AIMessage(content="Sajnálom, a szolgáltatás használatához szükségem van az alapvető hozzájárulásodra.")
            state["messages"].append(error_response)
            return state
        
        # Get the last message
        last_message = state["messages"][-1].content
        
        # Create dependencies
        deps = GeneralDependencies(
            supabase_client=state.get("user_context", {}).get("supabase_client"),
            webshop_api=state.get("user_context", {}).get("webshop_api"),
            user_context=state.get("user_context", {}),
            security_context=state.get("security_context"),
            audit_logger=state.get("audit_logger")
        )
        
        # Call Pydantic AI agent
        result = await call_general_agent(last_message, deps)
        
        # Audit logging
        audit_logger = state.get("audit_logger")
        if audit_logger:
            await audit_logger.log_data_access(
                user_id=state.get("user_context", {}).get("user_id", "anonymous"),
                data_type="general",
                operation="query",
                success=True
            )
        
        # Update state with response
        state = update_state_with_response(
            state=state,
            response_text=result.response_text,
            agent_name="general_agent",
            confidence=result.confidence,
            metadata={
                "suggested_actions": result.suggested_actions,
                "help_topics": result.help_topics,
                **result.metadata
            }
        )
        
        return state
        
    except Exception as e:
        # Error handling
        state = update_state_with_error(
            state=state,
            error_message=f"General agent hiba: {str(e)}",
            agent_name="general_agent"
        )
        return state


def create_langgraph_workflow() -> StateGraph:
    """
    LangGraph workflow létrehozása.
    
    Returns:
        Compiled LangGraph workflow
    """
    # Initialize StateGraph
    workflow = StateGraph(LangGraphState)
    
    # Add nodes
    workflow.add_node("route_message", route_message)
    workflow.add_node("product_agent", call_product_agent)
    workflow.add_node("order_agent", call_order_agent)
    workflow.add_node("recommendation_agent", call_recommendation_agent)
    workflow.add_node("marketing_agent", call_marketing_agent)
    workflow.add_node("general_agent", call_general_agent)
    
    # Add edges - START -> route_message
    workflow.add_edge(START, "route_message")
    
    # Add conditional edges from route_message
    workflow.add_conditional_edges(
        "route_message",
        lambda x: x["next"],
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


class LangGraphWorkflowManager:
    """LangGraph workflow manager singleton."""
    
    def __init__(self):
        self._workflow = None
    
    def get_workflow(self):
        """Get or create the workflow."""
        if self._workflow is None:
            self._workflow = create_langgraph_workflow()
        return self._workflow
    
    async def process_message(
        self,
        state: LangGraphState
    ) -> LangGraphState:
        """
        Process a message through the workflow.
        
        Args:
            state: Initial state
            
        Returns:
            Final state after processing
        """
        try:
            # Get workflow
            workflow = self.get_workflow()
            
            # Process message
            result = await workflow.ainvoke(state)
            
            # Finalize state
            result = finalize_state(result)
            
            return result
            
        except Exception as e:
            # Error handling
            state = update_state_with_error(
                state=state,
                error_message=f"Workflow hiba: {str(e)}",
                agent_name="workflow_manager"
            )
            return state


# Global workflow manager instance
_workflow_manager: Optional[LangGraphWorkflowManager] = None


def get_workflow_manager() -> LangGraphWorkflowManager:
    """Get the global workflow manager instance."""
    global _workflow_manager
    if _workflow_manager is None:
        _workflow_manager = LangGraphWorkflowManager()
    return _workflow_manager 