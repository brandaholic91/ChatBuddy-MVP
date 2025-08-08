"""
Agent models for Chatbuddy MVP.

This module contains Pydantic models for AI agent management:
- AgentDecision: Agent decision making
- AgentResponse: Agent response handling
- AgentState: Agent state management
- LangGraphState: Unified LangGraph state management
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, TypedDict
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.messages import BaseMessage


class AgentType(str, Enum):
    """Agent típusok"""
    COORDINATOR = "coordinator"
    PRODUCT_INFO = "product_info"
    ORDER_STATUS = "order_status"
    RECOMMENDATION = "recommendation"
    # Alias a visszafelé kompatibilitásért a tesztekhez
    RECOMMENDATIONS = "recommendation"
    MARKETING = "marketing"
    SOCIAL_MEDIA = "social_media"
    GENERAL = "general"


class AgentStatus(str, Enum):
    """Agent státuszok"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class DecisionType(str, Enum):
    """Döntés típusok"""
    ROUTE_TO_AGENT = "route_to_agent"
    PROVIDE_ANSWER = "provide_answer"
    ASK_CLARIFICATION = "ask_clarification"
    ESCALATE = "escalate"
    END_CONVERSATION = "end_conversation"


class AgentDecision(BaseModel):
    """Agent döntési modell"""
    agent_type: AgentType = Field(..., description="Agent típusa")
    decision_type: DecisionType = Field(..., description="Döntés típusa")
    target_agent: Optional[AgentType] = Field(default=None, description="Cél agent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Döntés bizonyossága")
    reasoning: str = Field(..., description="Döntés indoklása")
    context: Dict[str, Any] = Field(default_factory=dict, description="Döntési kontextus")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="További metadata")
    timestamp: datetime = Field(default_factory=datetime.now, description="Döntés időpontja")

    model_config = ConfigDict(
        validate_assignment=True
    )


class AgentResponse(BaseModel):
    """Agent válasz modell"""
    agent_type: AgentType = Field(..., description="Agent típusa")
    response_text: str = Field(..., description="Válasz szövege")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Válasz bizonyossága")
    response_type: str = Field(default="text", description="Válasz típusa")
    suggested_actions: List[Dict[str, Any]] = Field(default_factory=list, description="Javasolt műveletek")
    follow_up_questions: List[str] = Field(default_factory=list, description="Követő kérdések")
    data_sources: List[str] = Field(default_factory=list, description="Használt adatforrások")
    processing_time: Optional[float] = Field(default=None, description="Feldolgozási idő (másodperc)")
    tokens_used: Optional[int] = Field(default=None, description="Használt tokenek")
    cost: Optional[float] = Field(default=None, description="Költség")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="További metadata")
    timestamp: datetime = Field(default_factory=datetime.now, description="Válasz időpontja")

    model_config = ConfigDict(
        validate_assignment=True
    )


# ============================================================================
# LANGGRAPH UNIFIED STATE MANAGEMENT
# ============================================================================

class LangGraphState(TypedDict):
    """
    Egységes LangGraph state management a ChatBuddy MVP projekthez.

    Ez a state kezeli az összes agent közötti kommunikációt és adatmegosztást
    a LangGraph workflow-ban.
    """
    # Core message handling
    messages: List[BaseMessage]
    current_agent: str

    # User and session context
    user_context: Dict[str, Any]
    session_data: Dict[str, Any]

    # Error handling and retry logic
    error_count: int
    retry_attempts: int

    # Security and compliance
    security_context: Optional[Any]  # SecurityContext from config
    gdpr_compliance: Optional[Any]   # GDPR compliance layer
    audit_logger: Optional[Any]      # Audit logger

    # Agent-specific data
    agent_data: Dict[str, Any]       # Agent-specific data storage
    conversation_history: List[Dict[str, Any]]  # Extended conversation history

    # Performance and monitoring
    processing_start_time: Optional[float]
    processing_end_time: Optional[float]
    tokens_used: Optional[int]
    cost: Optional[float]

    # Workflow control
    workflow_step: str
    next_agent: Optional[str]
    should_continue: bool


class AgentState(BaseModel):
    """Agent állapot modell"""
    agent_type: AgentType = Field(..., description="Agent típusa")
    status: AgentStatus = Field(..., description="Agent státusz")
    current_session_id: Optional[str] = Field(default=None, description="Aktuális session")
    active_conversations: int = Field(default=0, description="Aktív beszélgetések száma")
    total_requests: int = Field(default=0, description="Összes kérés")
    successful_requests: int = Field(default=0, description="Sikeres kérések")
    failed_requests: int = Field(default=0, description="Sikertelen kérések")
    average_response_time: Optional[float] = Field(default=None, description="Átlagos válaszidő")
    last_activity: datetime = Field(default_factory=datetime.now, description="Utolsó aktivitás")
    error_count: int = Field(default=0, description="Hiba számláló")
    last_error: Optional[str] = Field(default=None, description="Utolsó hiba")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="Teljesítmény metrikák")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Agent konfiguráció")
    updated_at: datetime = Field(default_factory=datetime.now, description="Utolsó frissítés")

    model_config = ConfigDict(
        validate_assignment=True
    )


class AgentTool(BaseModel):
    """Agent tool modell"""
    name: str = Field(..., description="Tool neve")
    description: str = Field(..., description="Tool leírása")
    agent_type: AgentType = Field(..., description="Agent típusa")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool paraméterek")
    is_required: bool = Field(default=False, description="Kötelező tool")
    is_active: bool = Field(default=True, description="Tool aktív")
    usage_count: int = Field(default=0, description="Használatok száma")
    success_rate: float = Field(default=1.0, ge=0.0, le=1.0, description="Siker arány")
    average_execution_time: Optional[float] = Field(default=None, description="Átlagos végrehajtási idő")
    last_used: Optional[datetime] = Field(default=None, description="Utolsó használat")
    created_at: datetime = Field(default_factory=datetime.now, description="Létrehozás időpontja")

    model_config = ConfigDict(
        validate_assignment=True
    )


class AgentConversation(BaseModel):
    """Agent beszélgetés modell"""
    session_id: str = Field(..., description="Session azonosító")
    agent_type: AgentType = Field(..., description="Agent típusa")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Beszélgetés története")
    context: Dict[str, Any] = Field(default_factory=dict, description="Beszélgetési kontextus")
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="Felhasználói preferenciák")
    agent_memory: Dict[str, Any] = Field(default_factory=dict, description="Agent memória")
    conversation_start: datetime = Field(default_factory=datetime.now, description="Beszélgetés kezdete")
    last_interaction: datetime = Field(default_factory=datetime.now, description="Utolsó interakció")
    message_count: int = Field(default=0, description="Üzenetek száma")
    is_active: bool = Field(default=True, description="Beszélgetés aktív")
    satisfaction_score: Optional[float] = Field(default=None, ge=0.0, le=5.0, description="Elégedettség pontszám")

    model_config = ConfigDict(
        validate_assignment=True
    )


class AgentPerformance(BaseModel):
    """Agent teljesítmény modell"""
    agent_type: AgentType = Field(..., description="Agent típusa")
    date: datetime = Field(..., description="Dátum")
    total_requests: int = Field(default=0, description="Összes kérés")
    successful_requests: int = Field(default=0, description="Sikeres kérések")
    failed_requests: int = Field(default=0, description="Sikertelen kérések")
    average_response_time: float = Field(default=0.0, description="Átlagos válaszidő")
    total_tokens_used: int = Field(default=0, description="Összes használt token")
    total_cost: float = Field(default=0.0, description="Összes költség")
    user_satisfaction: float = Field(default=0.0, ge=0.0, le=5.0, description="Felhasználói elégedettség")
    conversation_completion_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Beszélgetés befejezési arány")
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Hiba arány")
    peak_concurrent_conversations: int = Field(default=0, description="Párhuzamos beszélgetések csúcsa")
    created_at: datetime = Field(default_factory=datetime.now, description="Létrehozás időpontja")

    model_config = ConfigDict(
        validate_assignment=True
    )


class AgentConfig(BaseModel):
    """Agent konfigurációs modell"""
    agent_type: AgentType = Field(..., description="Agent típusa")
    model_name: str = Field(..., description="AI modell neve")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperatúra")
    max_tokens: int = Field(default=1000, ge=1, description="Maximum tokenek")
    system_prompt: str = Field(..., description="Rendszer prompt")
    tools: List[str] = Field(default_factory=list, description="Elérhető tool-ok")
    context_window: int = Field(default=4000, ge=1, description="Kontextus ablak méret")
    memory_size: int = Field(default=10, ge=1, description="Memória méret")
    response_format: str = Field(default="text", description="Válasz formátum")
    fallback_agent: Optional[AgentType] = Field(default=None, description="Fallback agent")
    is_active: bool = Field(default=True, description="Agent aktív")
    created_at: datetime = Field(default_factory=datetime.now, description="Létrehozás időpontja")
    updated_at: datetime = Field(default_factory=datetime.now, description="Utolsó frissítés")

    model_config = ConfigDict(
        validate_assignment=True
    )
