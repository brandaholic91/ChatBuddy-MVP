"""
Audit Logging System for ChatBuddy MVP.

Ez a modul implementálja a részletes audit logging rendszert
a ChatBuddy MVP biztonsági és GDPR megfelelőségi követelményeihez.
"""

import os
import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Audit esemény típusok."""
    # Security events
    SECURITY_LOGIN = "security_login"
    SECURITY_LOGOUT = "security_logout"
    SECURITY_FAILED_LOGIN = "security_failed_login"
    SECURITY_PASSWORD_CHANGE = "security_password_change"
    SECURITY_ACCOUNT_LOCKED = "security_account_locked"
    SECURITY_IP_BLOCKED = "security_ip_blocked"
    SECURITY_THREAT_DETECTED = "security_threat_detected"

    # Data access events
    DATA_ACCESS = "data_access"
    DATA_CREATE = "data_create"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"

    # GDPR events
    GDPR_CONSENT_GRANTED = "gdpr_consent_granted"
    GDPR_CONSENT_REVOKED = "gdpr_consent_revoked"
    GDPR_DATA_DELETION = "gdpr_data_deletion"
    GDPR_DATA_EXPORT = "gdpr_data_export"
    GDPR_DATA_ACCESS_REQUEST = "gdpr_data_access_request"

    # Agent events
    AGENT_QUERY = "agent_query"
    AGENT_RESPONSE = "agent_response"
    AGENT_ERROR = "agent_error"
    AGENT_TOOL_USAGE = "agent_tool_usage"

    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_ERROR = "system_error"
    SYSTEM_CONFIG_CHANGE = "system_config_change"


class AuditSeverity(Enum):
    """Audit súlyossági szintek."""
    LOW = "low"
    MEDIUM = "medium"
    ERROR = "error"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit esemény rekord."""
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    severity: AuditSeverity
    details: Dict[str, Any]
    metadata: Dict[str, Any]
    source: str = "chatbuddy_mvp"
    version: str = "1.0.0"


class AuditLogger:
    """Audit logging rendszer."""

    def __init__(self, supabase_client=None, log_file_path: Optional[str] = None):
        self.supabase = supabase_client
        self.log_file_path = log_file_path or os.getenv("AUDIT_LOG_FILE", "audit.log")
        self.logger = self._setup_logger()
        self._event_queue = asyncio.Queue()
        self._processing_task = None

    def _setup_logger(self) -> logging.Logger:
        """Logger beállítása."""
        audit_logger = logging.getLogger("audit")
        audit_logger.setLevel(logging.INFO)

        # File handler
        file_handler = logging.FileHandler(self.log_file_path)
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        audit_logger.addHandler(file_handler)
        audit_logger.addHandler(console_handler)

        return audit_logger

    def _generate_event_id(self, event_type: AuditEventType, user_id: Optional[str] = None) -> str:
        """Egyedi esemény azonosító generálása."""
        timestamp = datetime.now(timezone.utc).isoformat()
        base_string = f"{event_type.value}_{timestamp}_{user_id or 'anonymous'}"
        return hashlib.md5(base_string.encode()).hexdigest()

    async def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Audit esemény naplózása.

        Args:
            event_type: Esemény típusa
            user_id: Felhasználó azonosító
            session_id: Session azonosító
            ip_address: IP cím
            user_agent: User agent
            severity: Súlyosság
            details: Részletek
            metadata: Metaadatok

        Returns:
            Esemény azonosító
        """
        try:
            event_id = self._generate_event_id(event_type, user_id)

            audit_event = AuditEvent(
                event_id=event_id,
                event_type=event_type,
                timestamp=datetime.now(timezone.utc),
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                severity=severity,
                details=details or {},
                metadata=metadata or {}
            )

            # Add to queue for async processing
            await self._event_queue.put(audit_event)

            # Immediate console log for critical events
            if severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL]:
                self.logger.critical(
                    f"CRITICAL AUDIT EVENT: {event_type.value} - User: {user_id} - Details: {details}"
                )

            return event_id

        except Exception as e:
            logger.error(f"Audit logging error: {e}")
            return "error"

    async def log_security_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: Optional[AuditSeverity] = None
    ) -> str:
        """
        Biztonsági esemény naplózása.

        Args:
            event_type: Esemény típusa
            user_id: Felhasználó azonosító
            details: Részletek
            ip_address: IP cím
            user_agent: User agent

        Returns:
            Esemény azonosító
        """
        # Map string event types to AuditEventType
        event_type_mapping = {
            "login": AuditEventType.SECURITY_LOGIN,
            "logout": AuditEventType.SECURITY_LOGOUT,
            "failed_login": AuditEventType.SECURITY_FAILED_LOGIN,
            "password_change": AuditEventType.SECURITY_PASSWORD_CHANGE,
            "account_locked": AuditEventType.SECURITY_ACCOUNT_LOCKED,
            "ip_blocked": AuditEventType.SECURITY_IP_BLOCKED,
            "threat_detected": AuditEventType.SECURITY_THREAT_DETECTED,
            "high_threat_detected": AuditEventType.SECURITY_THREAT_DETECTED
        }

        audit_event_type = event_type_mapping.get(event_type, AuditEventType.SECURITY_THREAT_DETECTED)
        computed_severity = severity or (AuditSeverity.HIGH if "threat" in event_type else AuditSeverity.MEDIUM)

        return await self.log_event(
            event_type=audit_event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=computed_severity,
            details=details,
            metadata={"security_event": True}
        )

    async def log_data_access(
        self,
        user_id: str,
        data_type: str,
        operation: str,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Adathozzáférés naplózása.

        Args:
            user_id: Felhasználó azonosító
            data_type: Adattípus
            operation: Művelet
            success: Sikeres volt-e
            details: Részletek
            session_id: Session azonosító

        Returns:
            Esemény azonosító
        """
        severity = AuditSeverity.LOW if success else AuditSeverity.MEDIUM

        return await self.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            session_id=session_id,
            severity=severity,
            details={
                "data_type": data_type,
                "operation": operation,
                "success": success,
                **(details or {})
            },
            metadata={"data_access": True}
        )

    async def log_gdpr_event(
        self,
        event_type: str,
        user_id: str,
        data_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        GDPR esemény naplózása.

        Args:
            event_type: Esemény típusa
            user_id: Felhasználó azonosító
            data_type: Adattípus
            details: Részletek

        Returns:
            Esemény azonosító
        """
        # Map GDPR event types
        event_type_mapping = {
            "consent_granted": AuditEventType.GDPR_CONSENT_GRANTED,
            "consent_revoked": AuditEventType.GDPR_CONSENT_REVOKED,
            "data_deletion": AuditEventType.GDPR_DATA_DELETION,
            "data_export": AuditEventType.GDPR_DATA_EXPORT,
            "data_access_request": AuditEventType.GDPR_DATA_ACCESS_REQUEST
        }

        audit_event_type = event_type_mapping.get(event_type, AuditEventType.GDPR_CONSENT_GRANTED)

        return await self.log_event(
            event_type=audit_event_type,
            user_id=user_id,
            severity=AuditSeverity.MEDIUM,
            details={
                "data_type": data_type,
                **(details or {})
            },
            metadata={"gdpr_event": True}
        )

    async def log_agent_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Agent esemény naplózása.

        Args:
            event_type: Esemény típusa
            user_id: Felhasználó azonosító
            agent_name: Agent neve
            details: Részletek
            session_id: Session azonosító

        Returns:
            Esemény azonosító
        """
        # Map agent event types
        event_type_mapping = {
            "query": AuditEventType.AGENT_QUERY,
            "response": AuditEventType.AGENT_RESPONSE,
            "error": AuditEventType.AGENT_ERROR,
            "tool_usage": AuditEventType.AGENT_TOOL_USAGE
        }

        audit_event_type = event_type_mapping.get(event_type, AuditEventType.AGENT_QUERY)
        severity = AuditSeverity.LOW if event_type != "error" else AuditSeverity.MEDIUM

        return await self.log_event(
            event_type=audit_event_type,
            user_id=user_id,
            session_id=session_id,
            severity=severity,
            details={
                "agent_name": agent_name,
                **(details or {})
            },
            metadata={"agent_event": True}
        )

    async def _process_audit_queue(self):
        """Audit események feldolgozása a queue-ból."""
        while True:
            try:
                # Get event from queue
                event = await self._event_queue.get()

                # Log to file
                self.logger.info(f"AUDIT: {json.dumps(asdict(event), default=str)}")

                # Store in database if available
                if self.supabase:
                    try:
                        await self.supabase.table('audit_logs').insert(
                            asdict(event)
                        ).execute()
                    except Exception as e:
                        logger.error(f"Database audit logging error: {e}")

                # Mark as done
                self._event_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Audit queue processing error: {e}")

    async def start_processing(self):
        """Audit feldolgozás indítása."""
        if self._processing_task is None:
            self._processing_task = asyncio.create_task(self._process_audit_queue())

    async def stop_processing(self):
        """Audit feldolgozás leállítása."""
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
            self._processing_task = None

    # Convenience instance wrappers expected by tests
    async def log_agent_interaction(self,
        user_id: str,
        agent_name: str,
        query: str,
        response: str,
        session_id: Optional[str] = None,
        success: bool = True
    ) -> None:
        await log_agent_interaction(
            user_id=user_id,
            agent_name=agent_name,
            query=query,
            response=response,
            session_id=session_id,
            success=success
        )

    async def log_error(self,
        user_id: Optional[str] = None,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        severity: AuditSeverity = AuditSeverity.ERROR
    ) -> str:
        return await self.log_event(
            event_type=AuditEventType.SYSTEM_ERROR,
            user_id=user_id,
            severity=severity,
            details={"message": message, **(details or {})},
            metadata={"error": True}
        )

    async def get_audit_events(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Audit események lekérése.

        Args:
            user_id: Felhasználó azonosító
            event_type: Esemény típusa
            start_date: Kezdő dátum
            end_date: Záró dátum
            limit: Eredmények száma

        Returns:
            Audit események listája
        """
        try:
            if self.supabase:
                query = self.supabase.table('audit_logs').select('*')

                if user_id:
                    query = query.eq('user_id', user_id)

                if event_type:
                    query = query.eq('event_type', event_type.value)

                if start_date:
                    query = query.gte('timestamp', start_date.isoformat())

                if end_date:
                    query = query.lte('timestamp', end_date.isoformat())

                query = query.order('timestamp', desc=True).limit(limit)

                response = await query.execute()
                return response.data or []

            return []

        except Exception as e:
            logger.error(f"Audit events retrieval error: {e}")
            return []

    async def cleanup_old_events(self, days: int = 90) -> int:
        """
        Régi audit események törlése.

        Args:
            days: Hány napnál régebbi eseményeket töröljünk

        Returns:
            Törölt események száma
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            if self.supabase:
                response = await self.supabase.table('audit_logs').delete().lt(
                    'timestamp', cutoff_date.isoformat()
                ).execute()

                deleted_count = len(response.data) if response.data else 0

                # Log cleanup
                await self.log_event(
                    event_type=AuditEventType.SYSTEM_CONFIG_CHANGE,
                    user_id="system",
                    severity=AuditSeverity.LOW,
                    details={
                        "action": "audit_cleanup",
                        "deleted_count": deleted_count,
                        "cutoff_date": cutoff_date.isoformat()
                    }
                )

                return deleted_count

            return 0

        except Exception as e:
            logger.error(f"Audit cleanup error: {e}")
            return 0


# Singleton instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger(supabase_client=None) -> AuditLogger:
    """
    Audit logger singleton instance.

    Args:
        supabase_client: Supabase kliens

    Returns:
        AuditLogger instance
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(supabase_client=supabase_client)
    return _audit_logger


async def setup_audit_logging(supabase_client=None) -> AuditLogger:
    """
    Audit logging beállítása.

    Args:
        supabase_client: Supabase kliens

    Returns:
        AuditLogger instance
    """
    audit_logger = get_audit_logger(supabase_client)
    await audit_logger.start_processing()
    return audit_logger


async def shutdown_audit_logging():
    """Audit logging leállítása."""
    global _audit_logger
    if _audit_logger:
        await _audit_logger.stop_processing()


# Utility functions for common audit scenarios
async def log_user_login(user_id: str, ip_address: str, user_agent: str, success: bool = True):
    """Felhasználói bejelentkezés naplózása."""
    audit_logger = get_audit_logger()

    event_type = "login" if success else "failed_login"
    severity = AuditSeverity.MEDIUM if success else AuditSeverity.HIGH

    await audit_logger.log_security_event(
        event_type=event_type,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={"success": success}
    )


async def log_agent_interaction(
    user_id: str,
    agent_name: str,
    query: str,
    response: str,
    session_id: Optional[str] = None,
    success: bool = True
):
    """Agent interakció naplózása."""
    audit_logger = get_audit_logger()

    # Log query
    await audit_logger.log_agent_event(
        event_type="query",
        user_id=user_id,
        agent_name=agent_name,
        session_id=session_id,
        details={
            "query": query[:500],  # Limit length for storage
            "success": success
        }
    )

    # Log response
    await audit_logger.log_agent_event(
        event_type="response",
        user_id=user_id,
        agent_name=agent_name,
        session_id=session_id,
        details={
            "response_length": len(response),
            "success": success
        }
    )


async def log_data_processing(
    user_id: str,
    data_type: str,
    operation: str,
    data_size: Optional[int] = None,
    session_id: Optional[str] = None
):
    """Adatfeldolgozás naplózása."""
    audit_logger = get_audit_logger()

    await audit_logger.log_data_access(
        user_id=user_id,
        data_type=data_type,
        operation=operation,
        session_id=session_id,
        details={
            "data_size": data_size,
            "processing_time": None  # Could be added later
        }
    )


async def log_system_event(
    event_type: str,
    details: Optional[Dict[str, Any]] = None,
    severity: AuditSeverity = AuditSeverity.MEDIUM
):
    """Rendszer esemény naplózása."""
    audit_logger = get_audit_logger()

    # Map system event types
    event_type_mapping = {
        "startup": AuditEventType.SYSTEM_STARTUP,
        "shutdown": AuditEventType.SYSTEM_SHUTDOWN,
        "error": AuditEventType.SYSTEM_ERROR,
        "config_change": AuditEventType.SYSTEM_CONFIG_CHANGE
    }

    audit_event_type = event_type_mapping.get(event_type, AuditEventType.SYSTEM_ERROR)

    await audit_logger.log_event(
        event_type=audit_event_type,
        user_id="system",
        severity=severity,
        details=details or {},
        metadata={"system_event": True}
    )

    # ------------------------------------------------------------------
    # Instance-level convenience wrapper to align with tests expecting
    # audit_logger.log_agent_interaction(...)
    # ------------------------------------------------------------------
    async def log_agent_interaction(self,
        user_id: str,
        agent_name: str,
        query: str,
        response: str,
        session_id: Optional[str] = None,
        success: bool = True
    ) -> None:
        """Instance wrapper a modul szintű log_agent_interaction-hoz."""
        await log_agent_interaction(
            user_id=user_id,
            agent_name=agent_name,
            query=query,
            response=response,
            session_id=session_id,
            success=success
        )
