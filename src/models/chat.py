"""
Chat models for Chatbuddy MVP.

This module contains Pydantic models for chat functionality:
- ChatMessage: Individual chat messages
- ChatSession: Chat session management
- ChatState: Chat conversation state
- MessageType: Message type enumeration
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class MessageType(str, Enum):
    """Üzenet típusok a chat rendszerben"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"
    TOOL = "tool"


class ChatMessage(BaseModel):
    """Alapvető chat üzenet modell"""
    id: str = Field(..., description="Egyedi üzenet azonosító")
    session_id: str = Field(..., description="Session azonosító")
    type: MessageType = Field(..., description="Üzenet típusa")
    content: str = Field(..., min_length=1, description="Üzenet tartalma")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Üzenet létrehozásának időpontja")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="További metadata")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class ChatSession(BaseModel):
    """Felhasználói session információk"""
    session_id: str = Field(..., description="Egyedi session azonosító")
    user_id: Optional[str] = Field(default=None, description="Felhasználó azonosító ha beazonosított")
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Session kezdési időpont")
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Utolsó aktivitás időpontja")
    context: Dict[str, Any] = Field(default_factory=dict, description="Session kontextus adatok")
    is_active: bool = Field(default=True, description="Session aktív státusza")
    messages: List[ChatMessage] = Field(default_factory=list, description="Session üzenetei")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class ChatState(BaseModel):
    """Chat konverzáció állapota"""
    session_id: str = Field(..., description="Session azonosító")
    current_agent: Optional[str] = Field(default=None, description="Jelenlegi aktív agent")
    conversation_history: List[ChatMessage] = Field(default_factory=list, description="Konverzáció története")
    user_context: Dict[str, Any] = Field(default_factory=dict, description="Felhasználói kontextus")
    agent_context: Dict[str, Any] = Field(default_factory=dict, description="Agent kontextus")
    last_interaction: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Utolsó interakció")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class ChatRequest(BaseModel):
    """Chat kérés modell"""
    session_id: str = Field(..., description="Session azonosító")
    message: str = Field(..., min_length=1, description="Felhasználói üzenet")
    user_id: Optional[str] = Field(default=None, description="Felhasználó azonosító")
    context: Optional[Dict[str, Any]] = Field(default=None, description="További kontextus")
    
    model_config = ConfigDict(validate_assignment=True)


class ChatResponse(BaseModel):
    """Chat válasz modell"""
    session_id: str = Field(..., description="Session azonosító")
    message: str = Field(..., description="Válasz üzenet")
    agent_used: Optional[str] = Field(default=None, description="Használt agent")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Válasz bizonyossága")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="További metadata")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Válasz időpontja")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class WebSocketMessage(BaseModel):
    """WebSocket üzenet modell"""
    type: str = Field(..., description="Üzenet típusa")
    data: Dict[str, Any] = Field(..., description="Üzenet adatai")
    session_id: str = Field(..., description="Session azonosító")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Üzenet időpontja")
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class ChatError(BaseModel):
    """Chat hiba modell"""
    session_id: str = Field(..., description="Session azonosító")
    error_type: str = Field(..., description="Hiba típusa")
    error_message: str = Field(..., description="Hiba üzenet")
    error_code: Optional[str] = Field(default=None, description="Hiba kód")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Hiba időpontja")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="További hiba információk")
    
    model_config = ConfigDict(
        validate_assignment=True
    ) 