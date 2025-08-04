"""
State Management Utilities for LangGraph + Pydantic AI Hybrid Architecture.

This module provides utilities for managing the unified LangGraph state
across the ChatBuddy MVP project.
"""

import time
from typing import Dict, Any, Optional, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from ..models.agent import LangGraphState


def create_initial_state(
    user_message: str,
    user_context: Optional[Dict[str, Any]] = None,
    session_data: Optional[Dict[str, Any]] = None,
    security_context: Optional[Any] = None,
    gdpr_compliance: Optional[Any] = None,
    audit_logger: Optional[Any] = None
) -> LangGraphState:
    """
    Inicializálja a LangGraph state-et egy új beszélgetéshez.
    
    Args:
        user_message: Felhasználói üzenet
        user_context: Felhasználói kontextus
        session_data: Session adatok
        security_context: Biztonsági kontextus
        gdpr_compliance: GDPR compliance layer
        audit_logger: Audit logger
        
    Returns:
        Inicializált LangGraph state
    """
    return LangGraphState(
        messages=[HumanMessage(content=user_message)],
        current_agent="coordinator",
        user_context=user_context or {},
        session_data=session_data or {},
        error_count=0,
        retry_attempts=0,
        security_context=security_context,
        gdpr_compliance=gdpr_compliance,
        audit_logger=audit_logger,
        agent_data={},
        conversation_history=[],
        processing_start_time=time.time(),
        processing_end_time=None,
        tokens_used=None,
        cost=None,
        workflow_step="start",
        next_agent=None,
        should_continue=True
    )


def update_state_with_response(
    state: LangGraphState,
    response_text: str,
    agent_name: str,
    confidence: float = 1.0,
    metadata: Optional[Dict[str, Any]] = None
) -> LangGraphState:
    """
    Frissíti a state-et egy agent válaszával.
    
    Args:
        state: Jelenlegi state
        response_text: Agent válasza
        agent_name: Agent neve
        confidence: Válasz bizonyossága
        metadata: További metaadatok
        
    Returns:
        Frissített state
    """
    # Válasz hozzáadása
    response_message = AIMessage(content=response_text)
    state["messages"].append(response_message)
    
    # Agent adatok frissítése
    if "agent_data" not in state:
        state["agent_data"] = {}
    if "agent_responses" not in state["agent_data"]:
        state["agent_data"]["agent_responses"] = []
    
    state["agent_data"]["agent_responses"].append({
        "agent": agent_name,
        "response": response_text,
        "confidence": confidence,
        "timestamp": time.time(),
        "metadata": metadata or {}
    })
    
    # Metadata hozzáadása a state-hez
    if "metadata" not in state:
        state["metadata"] = {}
    state["metadata"].update(metadata or {})
    
    # Konverzáció történet frissítése
    if "conversation_history" not in state:
        state["conversation_history"] = []
    state["conversation_history"].append({
        "type": "agent_response",
        "agent": agent_name,
        "content": response_text,
        "timestamp": time.time(),
        "confidence": confidence
    })
    
    return state


def update_state_with_error(
    state: LangGraphState,
    error_message: str,
    agent_name: str,
    error_type: str = "general"
) -> LangGraphState:
    """
    Frissíti a state-et egy hiba esetén.

    Args:
        state: Jelenlegi state
        error_message: Hiba üzenet
        agent_name: Agent neve
        error_type: Hiba típusa

    Returns:
        Frissített state
    """
    # Hiba számláló növelése
    state["error_count"] += 1

    # Hiba üzenet hozzáadása
    error_response = AIMessage(content=f"Sajnálom, hiba történt: {error_message}")
    state["messages"].append(error_response)

    # Hiba adatok tárolása
    if "agent_data" not in state:
        state["agent_data"] = {}
    if "errors" not in state["agent_data"]:
        state["agent_data"]["errors"] = []
    
    # Initialize agent_data if it's empty
    if not state["agent_data"]:
        state["agent_data"] = {"errors": [], "agent_responses": []}
    
    state["agent_data"]["errors"].append({
        "agent": agent_name,
        "error": error_message,
        "type": error_type,
        "timestamp": time.time()
    })
    
    # Konverzáció történet frissítése
    if "conversation_history" not in state:
        state["conversation_history"] = []
    state["conversation_history"].append({
        "type": "error",
        "agent": agent_name,
        "content": error_message,
        "timestamp": time.time(),
        "error_type": error_type
    })
    
    return state


def finalize_state(
    state: LangGraphState,
    final_response: Optional[str] = None
) -> LangGraphState:
    """
    Finalizálja a state-et a workflow befejezésekor.
    
    Args:
        state: Jelenlegi state
        final_response: Végső válasz (opcionális)
        
    Returns:
        Finalizált state
    """
    # Feldolgozási idő kiszámítása
    if state["processing_start_time"]:
        state["processing_end_time"] = time.time()
        processing_time = state["processing_end_time"] - state["processing_start_time"]
        state["agent_data"]["processing_time"] = processing_time
    
    # Workflow befejezése
    state["workflow_step"] = "completed"
    state["should_continue"] = False
    
    # Végső válasz hozzáadása ha van
    if final_response:
        final_message = AIMessage(content=final_response)
        state["messages"].append(final_message)
        
        state["conversation_history"].append({
            "type": "final_response",
            "content": final_response,
            "timestamp": time.time()
        })
    
    return state


def get_state_summary(state: LangGraphState) -> Dict[str, Any]:
    """
    Összefoglaló a state-ről.
    
    Args:
        state: LangGraph state
        
    Returns:
        State összefoglaló
    """
    return {
        "total_messages": len(state["messages"]),
        "current_agent": state["current_agent"],
        "error_count": state["error_count"],
        "retry_attempts": state["retry_attempts"],
        "workflow_step": state["workflow_step"],
        "processing_time": (
            state["processing_end_time"] - state["processing_start_time"]
            if state["processing_end_time"] and state["processing_start_time"]
            else None
        ),
        "tokens_used": state["tokens_used"],
        "cost": state["cost"],
        "agent_responses_count": len(state["agent_data"].get("agent_responses", [])),
        "errors_count": len(state["agent_data"].get("errors", [])),
        "conversation_history_count": len(state["conversation_history"])
    }


def validate_state(state: LangGraphState) -> bool:
    """
    Validálja a state-et.
    
    Args:
        state: LangGraph state
        
    Returns:
        True ha valid, False ha nem
    """
    try:
        # Alapvető mezők ellenőrzése
        required_fields = [
            "messages", "current_agent", "user_context", "session_data",
            "error_count", "retry_attempts", "agent_data", "conversation_history",
            "workflow_step", "should_continue"
        ]
        
        for field in required_fields:
            if field not in state:
                return False
        
        # Üzenetek ellenőrzése
        if not isinstance(state["messages"], list):
            return False
        
        # Hiba számláló ellenőrzése
        if state["error_count"] < 0:
            return False
        
        # Retry attempts ellenőrzése
        if state["retry_attempts"] < 0:
            return False
        
        return True
        
    except Exception:
        return False


def reset_state_for_retry(state: LangGraphState) -> LangGraphState:
    """
    Reseteli a state-et újrapróbálkozáshoz.
    
    Args:
        state: Jelenlegi state
        
    Returns:
        Resetelt state
    """
    state["retry_attempts"] += 1
    state["workflow_step"] = "retry"
    state["should_continue"] = True
    
    # Feldolgozási idő reset
    state["processing_start_time"] = time.time()
    state["processing_end_time"] = None
    
    return state


def add_agent_data(
    state: LangGraphState,
    agent_name: str,
    data: Dict[str, Any]
) -> LangGraphState:
    """
    Hozzáad agent-specifikus adatokat a state-hez.
    
    Args:
        state: Jelenlegi state
        agent_name: Agent neve
        data: Adatok
        
    Returns:
        Frissített state
    """
    if "agent_specific_data" not in state["agent_data"]:
        state["agent_data"]["agent_specific_data"] = {}
    
    if agent_name not in state["agent_data"]["agent_specific_data"]:
        state["agent_data"]["agent_specific_data"][agent_name] = {}
    
    state["agent_data"]["agent_specific_data"][agent_name].update(data)
    
    return state


def get_agent_data(
    state: LangGraphState,
    agent_name: str
) -> Dict[str, Any]:
    """
    Lekéri agent-specifikus adatokat a state-ből.
    
    Args:
        state: LangGraph state
        agent_name: Agent neve
        
    Returns:
        Agent adatok
    """
    return state["agent_data"].get("agent_specific_data", {}).get(agent_name, {})


def update_performance_metrics(
    state: LangGraphState,
    tokens_used: Optional[int] = None,
    cost: Optional[float] = None
) -> LangGraphState:
    """
    Frissíti a teljesítmény metrikákat.
    
    Args:
        state: Jelenlegi state
        tokens_used: Használt tokenek
        cost: Költség
        
    Returns:
        Frissített state
    """
    if tokens_used is not None:
        state["tokens_used"] = tokens_used
    
    if cost is not None:
        state["cost"] = cost
    
    return state 