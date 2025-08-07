"""
LangGraph + Pydantic AI Correct Integration Implementation.

This module implements the proper LangGraph workflow that integrates
Pydantic AI agents as tools following the article pattern:
https://atalupadhyay.wordpress.com/2025/02/15/a-step-by-step-guide-with-pydantic-ai-and-langgraph-to-build-ai-agents/
"""

import json
from typing import Dict, Any, List, Optional, Literal, TypedDict, Annotated, AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel

# Import our Pydantic AI agents
from ..agents.product_info.agent import create_product_info_agent, ProductInfoDependencies
from ..agents.order_status.agent import create_order_status_agent, OrderStatusDependencies
from ..agents.recommendations.agent import create_recommendation_agent, RecommendationDependencies
from ..agents.marketing.agent import create_marketing_agent, MarketingDependencies
from ..agents.general.agent import create_general_agent, GeneralDependencies

# Import the new agent cache manager
from .agent_cache_manager import get_cached_agent
from ..models.agent import AgentType

# Security and utilities imports
from ..config.security import get_threat_detector, InputValidator
from ..config.gdpr_compliance import get_gdpr_compliance, ConsentType, DataCategory
from ..utils.state_management import create_initial_state


class AgentState(TypedDict):
    """
    Agent State for LangGraph workflow.
    Following the article pattern for state management.
    """
    messages: Annotated[List[BaseMessage], add_messages]
    current_question: str
    active_agent: str
    user_context: Dict[str, Any]
    security_context: Optional[Dict[str, Any]]
    workflow_steps: List[str]
    agent_responses: Dict[str, Any]
    metadata: Dict[str, Any]


class ToolCallRequest(BaseModel):
    """Tool call request structure for JSON tool calling."""
    tool_name: str
    agent_type: str
    message: str
    context: Dict[str, Any] = {}


def create_agent_dependencies(state: AgentState, agent_type: str) -> Any:
    """
    Create appropriate dependencies for the given agent type.
    
    Args:
        state: Current workflow state
        agent_type: Type of agent (product, order, etc.)
    
    Returns:
        Dependencies object for the agent
    """
    base_context = {
        "user_context": state.get("user_context", {}),
        "supabase_client": state.get("user_context", {}).get("supabase_client"),
        "webshop_api": state.get("user_context", {}).get("webshop_api"),
        "security_context": state.get("security_context"),
        "audit_logger": state.get("user_context", {}).get("audit_logger")
    }
    
    if agent_type == "product":
        return ProductInfoDependencies(**base_context)
    elif agent_type == "order":
        return OrderStatusDependencies(**base_context)
    elif agent_type == "recommendation":
        return RecommendationDependencies(**base_context)
    elif agent_type == "marketing":
        return MarketingDependencies(**base_context)
    elif agent_type == "general":
        return GeneralDependencies(**base_context)
    else:
        return GeneralDependencies(**base_context)


async def agent_selector_node(state: AgentState) -> AgentState:
    """
    Agent selector node - determines which agent should handle the query.
    Following the article's routing pattern.
    """
    try:
        # Get the current question
        current_question = state.get("current_question", "")
        if not current_question and state.get("messages"):
            # Extract from last message if not set
            last_message = state["messages"][-1]
            if isinstance(last_message, HumanMessage):
                current_question = last_message.content
                state["current_question"] = current_question
        
        # Input sanitization
        input_validator = InputValidator()
        sanitized_question = input_validator.sanitize_string(current_question)
        
        # Threat detection
        threat_detector = get_threat_detector()
        threat_analysis = threat_detector.detect_threats(sanitized_question)
        
        if threat_analysis.get("risk_level") == "high":
            state["active_agent"] = "general"
            state["workflow_steps"].append("threat_detected")
            return state
        
        # Simple keyword-based agent selection (following article pattern)
        question_lower = sanitized_question.lower()
        
        # Marketing keywords
        if any(keyword in question_lower for keyword in [
            "kedvezm", "akci", "promo", "hirlevél", "newsletter", 
            "kupon", "kód", "szazal", "ingyenes", "akcio"
        ]):
            selected_agent = "marketing"
        # Order keywords (check before product to catch "rendelesem")
        elif any(keyword in question_lower for keyword in [
            "rendel", "szallit", "status", "kovet", "tracking",
            "delivery", "megerkez", "csomag", "hol a"
        ]):
            selected_agent = "order"
        # Recommendation keywords
        elif any(keyword in question_lower for keyword in [
            "ajanl", "ajanlat", "hasonl", "nepszer", "trend",
            "preferencia", "kedvenc", "mit vegyek", "legjobb", "mit"
        ]):
            selected_agent = "recommendation"
        # Product keywords
        elif any(keyword in question_lower for keyword in [
            "termek", "telefon", "laptop", "ar", "keszlet", "specifikaci",
            "leiras", "marka", "keres", "talal", "milyen", "fajta"
        ]):
            selected_agent = "product"
        else:
            selected_agent = "general"
        
        # Update state
        state["active_agent"] = selected_agent
        state["workflow_steps"].append(f"agent_selected_{selected_agent}")
        
        return state
        
    except Exception as e:
        # Fallback to general agent
        state["active_agent"] = "general"
        state["workflow_steps"].append(f"agent_selection_error_{str(e)}")
        return state


async def pydantic_ai_tool_node(state: AgentState) -> AgentState:
    """
    Pydantic AI tool execution node.
    This is where we properly integrate Pydantic AI agents as tools.
    Following the article's tool calling pattern.
    """
    try:
        active_agent = state.get("active_agent", "general")
        current_question = state.get("current_question", "")
        
        # Generate consistent cache key
        cache_key = f"tool_node:{active_agent}:{hash(current_question)}"
        
        # Check cache first
        cache_service = state.get("cache_service")
        if cache_service:
            cached_response = await cache_service.performance_cache.get_cached_agent_response(cache_key)
            if cached_response and isinstance(cached_response, dict) and "error" not in cached_response:
                # Return cached response
                ai_message = AIMessage(content=cached_response.get("response_text", "Cached response"))
                state["messages"].append(ai_message)
                return state
        
        # Create appropriate dependencies
        dependencies = create_agent_dependencies(state, active_agent)
        
        # Get the appropriate agent and execute
        agent_response = None
        
        try:
            if active_agent == "product":
                agent = get_cached_agent(AgentType.PRODUCT_INFO)
            elif active_agent == "order":
                agent = get_cached_agent(AgentType.ORDER_STATUS)
            elif active_agent == "recommendation":
                agent = get_cached_agent(AgentType.RECOMMENDATION)
            elif active_agent == "marketing":
                agent = get_cached_agent(AgentType.MARKETING)
            else:  # general agent
                agent = get_cached_agent(AgentType.GENERAL)
            
            result = await agent.run(current_question, deps=dependencies)
            agent_response = result.data if hasattr(result, 'data') else result
                
        except Exception as agent_error:
            # Mock response for testing
            agent_response = {
                "response_text": f"Mock válasz - {active_agent} agent működne itt. Kérdés: {current_question}",
                "confidence": 0.5,
                "metadata": {
                    "mock_mode": True,
                    "original_error": str(agent_error),
                    "agent_type": active_agent
                }
            }
        
        # Process agent response
        if isinstance(agent_response, dict):
            # Handle different response formats
            response_text = (
                agent_response.get("response_text") or 
                agent_response.get("response") or 
                str(agent_response)
            )
            confidence = agent_response.get("confidence", 0.8)
            metadata = agent_response.get("metadata", {})
        else:
            response_text = str(agent_response)
            confidence = 0.8
            metadata = {}
        
        # Cache the response
        if cache_service:
            response_data = {
                "response_text": response_text,
                "confidence": confidence,
                "metadata": metadata
            }
            await cache_service.performance_cache.cache_agent_response(cache_key, response_data)
        
        # Add AI message to state
        ai_message = AIMessage(content=response_text)
        state["messages"].append(ai_message)
        
        # Update agent responses
        state["agent_responses"][active_agent] = {
            "response_text": response_text,
            "confidence": confidence,
            "metadata": metadata
        }
        
        # Update workflow steps
        state["workflow_steps"].append(f"agent_executed_{active_agent}")
        
        return state
        
    except Exception as e:
        # Error handling
        error_message = f"Hiba történt a(z) {state.get('active_agent', 'unknown')} agent futtatásakor: {str(e)}"
        ai_message = AIMessage(content=error_message)
        state["messages"].append(ai_message)
        
        state["workflow_steps"].append(f"agent_error_{str(e)}")
        
        return state


def should_continue(state: AgentState) -> Literal["continue", "end"]:
    """
    Decision function to determine if workflow should continue or end.
    Following the article's conditional routing pattern.
    """
    try:
        # Check if we have a response
        if state.get("agent_responses") and state.get("active_agent"):
            active_agent = state["active_agent"]
            if active_agent in state["agent_responses"]:
                # We have a response, end the workflow
                return "end"
        
        # Check workflow steps for errors
        workflow_steps = state.get("workflow_steps", [])
        if any("error" in step for step in workflow_steps):
            # There was an error, end the workflow
            return "end"
        
        # Default: continue
        return "continue"
        
    except Exception:
        # On error, end the workflow
        return "end"


def create_correct_langgraph_workflow() -> StateGraph:
    """
    Create the correct LangGraph workflow with proper Pydantic AI integration.
    Following the article's workflow pattern.
    
    Returns:
        Compiled StateGraph workflow
    """
    # Create StateGraph with our AgentState
    workflow = StateGraph(AgentState)
    
    # Add nodes following the article pattern
    workflow.add_node("agent_selector", agent_selector_node)
    workflow.add_node("tool_executor", pydantic_ai_tool_node)
    
    # Add edges following the article pattern
    workflow.add_edge(START, "agent_selector")
    workflow.add_edge("agent_selector", "tool_executor")
    
    # Add conditional edge for continuation logic
    workflow.add_conditional_edges(
        "tool_executor",
        should_continue,
        {
            "continue": "agent_selector",  # Loop back for multi-step conversations
            "end": END
        }
    )
    
    # Compile the workflow
    return workflow.compile()


class LangGraphWorkflowManagerV2:
    """
    Correct LangGraph Workflow Manager.
    Following the article's best practices for workflow management.
    """
    
    def __init__(self):
        self._workflow = None
        self._initialized = False
    
    def get_workflow(self):
        """Get or create the workflow instance."""
        if self._workflow is None:
            self._workflow = create_correct_langgraph_workflow()
            self._initialized = True
        return self._workflow
    
    async def stream_message(
        self,
        user_message: str,
        user_context: Optional[Dict[str, Any]] = None,
        security_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[AgentState, None]:
        """
        Stream a user message through the correct workflow.
        
        Args:
            user_message: User's input message
            user_context: User context information
            security_context: Security context
            
        Yields:
            AgentState chunks as they become available
        """
        try:
            # Create initial state following the article pattern
            initial_state: AgentState = {
                "messages": [HumanMessage(content=user_message)],
                "current_question": user_message,
                "active_agent": "",
                "user_context": user_context or {},
                "security_context": security_context,
                "workflow_steps": ["workflow_started"],
                "agent_responses": {},
                "metadata": {}
            }
            
            # Get workflow and process
            workflow = self.get_workflow()
            
            async for state_chunk in workflow.astream(initial_state):
                yield state_chunk
            
        except Exception as e:
            # Error handling
            error_state: AgentState = {
                "messages": [
                    HumanMessage(content=user_message),
                    AIMessage(content=f"Sajnálom, hiba történt: {str(e)}")
                ],
                "current_question": user_message,
                "active_agent": "error",
                "user_context": user_context or {},
                "security_context": security_context,
                "workflow_steps": ["workflow_started", f"workflow_error_{str(e)}"],
                "agent_responses": {},
                "metadata": {"error": str(e)}
            }
            yield error_state
    
    async def process_message(
        self,
        user_message: str,
        user_context: Optional[Dict[str, Any]] = None,
        security_context: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        """
        Backward-compatible process_message method.
        
        This method collects all streaming chunks and returns the final state.
        It's provided for backward compatibility with existing tests and code.
        
        Args:
            user_message: User's input message
            user_context: User context information
            security_context: Security context
            
        Returns:
            Final AgentState
        """
        final_state = None
        
        # Collect all streaming states
        async for state_chunk in self.stream_message(user_message, user_context, security_context):
            final_state = state_chunk
        
        # Return the final state or a default if no states were yielded
        if final_state is None:
            final_state = {
                "messages": [
                    HumanMessage(content=user_message),
                    AIMessage(content="Sajnálom, nem sikerült válaszolni.")
                ],
                "current_question": user_message,
                "active_agent": "error",
                "user_context": user_context or {},
                "security_context": security_context,
                "workflow_steps": ["workflow_started", "no_response_error"],
                "agent_responses": {},
                "metadata": {"error": "No response generated"}
            }
        
        return final_state


# Global workflow manager instance
_workflow_manager_v2: Optional[LangGraphWorkflowManagerV2] = None


def get_correct_workflow_manager() -> LangGraphWorkflowManagerV2:
    """Get the global correct workflow manager instance."""
    global _workflow_manager_v2
    if _workflow_manager_v2 is None:
        _workflow_manager_v2 = LangGraphWorkflowManagerV2()
    return _workflow_manager_v2


# Export the new functions
__all__ = [
    'AgentState',
    'create_correct_langgraph_workflow',
    'LangGraphWorkflowManagerV2',
    'get_correct_workflow_manager'
]