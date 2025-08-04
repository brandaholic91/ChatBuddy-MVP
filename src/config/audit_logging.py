"""
Audit Logging System - Chatbuddy MVP.

Ez a modul implementálja a comprehensive audit logging rendszert
minden agent interakcióra és biztonsági eseményre.
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import asyncio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Audit esemény típusok."""
    AGENT_INTERACTION = "agent_interaction"
    SECURITY_EVENT = "security_event"
    DATA_ACCESS = "data_access"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    GDPR_EVENT = "gdpr_event"
    SYSTEM_EVENT = "system_event"
    ERROR_EVENT = "error_event"


class SecuritySeverity(Enum):
    """Biztonsági események súlyossága."""
    LOW = "low"
    MEDIUM = "medium"
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
    agent_type: Optional[str]
    severity: SecuritySeverity
    source_ip: Optional[str]
    user_agent: Optional[str]
    event_data: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class SecurityEvent:
    """Biztonsági esemény rekord."""
    event_id: str
    event_type: str
    severity: SecuritySeverity
    timestamp: datetime
    user_id: Optional[str]
    source_ip: Optional[str]
    description: str
    details: Dict[str, Any]
    mitigated: bool = False
    mitigation_notes: Optional[str] = None


class SecurityAuditLogger:
    """Biztonsági audit logger."""
    
    def __init__(self, supabase_client=None, logfire_client=None):
        self.supabase = supabase_client
        self.logfire = logfire_client
        self.audit_queue = asyncio.Queue()
        self.running = False
        
    async def start(self):
        """Audit logger indítása."""
        if not self.running:
            self.running = True
            asyncio.create_task(self._process_audit_queue())
            logger.info("Security audit logger started")
    
    async def stop(self):
        """Audit logger leállítása."""
        self.running = False
        # Wait for queue to be processed
        while not self.audit_queue.empty():
            await asyncio.sleep(0.1)
        logger.info("Security audit logger stopped")
    
    async def _process_audit_queue(self):
        """Audit queue feldolgozása."""
        while self.running:
            try:
                event = await asyncio.wait_for(self.audit_queue.get(), timeout=1.0)
                await self._log_event(event)
                self.audit_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing audit queue: {e}")
    
    async def log_agent_interaction(
        self,
        agent_type: str,
        user_id: str,
        session_id: str,
        query: str,
        response: str,
        metadata: Dict[str, Any] = None
    ):
        """
        Agent interakció naplózása.
        
        Args:
            agent_type: Agent típusa
            user_id: Felhasználó azonosító
            session_id: Session azonosító
            query: Felhasználói kérés
            response: Agent válasz
            metadata: További metaadatok
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.AGENT_INTERACTION,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            session_id=session_id,
            agent_type=agent_type,
            severity=SecuritySeverity.LOW,
            source_ip=metadata.get("source_ip") if metadata else None,
            user_agent=metadata.get("user_agent") if metadata else None,
            event_data={
                "query": self._sanitize_input(query),
                "response": self._sanitize_output(response),
                "query_length": len(query),
                "response_length": len(response),
                "processing_time": metadata.get("processing_time") if metadata else None
            },
            metadata=metadata or {}
        )
        
        await self.audit_queue.put(event)
    
    async def log_security_event(
        self,
        event_type: str,
        severity: SecuritySeverity,
        user_id: Optional[str],
        description: str,
        details: Dict[str, Any] = None,
        source_ip: Optional[str] = None
    ):
        """
        Biztonsági esemény naplózása.
        
        Args:
            event_type: Esemény típusa
            severity: Súlyosság
            user_id: Felhasználó azonosító
            description: Leírás
            details: Részletek
            source_ip: Forrás IP
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.SECURITY_EVENT,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            session_id=None,
            agent_type=None,
            severity=severity,
            source_ip=source_ip,
            user_agent=None,
            event_data={
                "security_event_type": event_type,
                "description": description,
                "details": self._sanitize_data(details or {})
            },
            metadata={}
        )
        
        await self.audit_queue.put(event)
        
        # Critical events need immediate attention
        if severity == SecuritySeverity.CRITICAL:
            await self._handle_critical_event(event)
    
    async def log_data_access(
        self,
        user_id: str,
        data_type: str,
        operation: str,
        success: bool,
        details: Dict[str, Any] = None
    ):
        """
        Adathozzáférés naplózása.
        
        Args:
            user_id: Felhasználó azonosító
            data_type: Adattípus
            operation: Művelet
            success: Sikeres volt-e
            details: Részletek
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.DATA_ACCESS,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            session_id=None,
            agent_type=None,
            severity=SecuritySeverity.MEDIUM if not success else SecuritySeverity.LOW,
            source_ip=None,
            user_agent=None,
            event_data={
                "data_type": data_type,
                "operation": operation,
                "success": success,
                "details": self._sanitize_data(details or {})
            },
            metadata={}
        )
        
        await self.audit_queue.put(event)
    
    async def log_authentication(
        self,
        user_id: str,
        success: bool,
        method: str,
        source_ip: str,
        details: Dict[str, Any] = None
    ):
        """
        Hitelesítés naplózása.
        
        Args:
            user_id: Felhasználó azonosító
            success: Sikeres volt-e
            method: Hitelesítési módszer
            source_ip: Forrás IP
            details: Részletek
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.AUTHENTICATION,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            session_id=None,
            agent_type=None,
            severity=SecuritySeverity.HIGH if not success else SecuritySeverity.LOW,
            source_ip=source_ip,
            user_agent=details.get("user_agent") if details else None,
            event_data={
                "success": success,
                "method": method,
                "details": self._sanitize_data(details or {})
            },
            metadata={}
        )
        
        await self.audit_queue.put(event)
        
        # Failed authentication attempts need attention
        if not success:
            await self._handle_failed_auth(event)
    
    async def log_authorization(
        self,
        user_id: str,
        resource: str,
        action: str,
        granted: bool,
        details: Dict[str, Any] = None
    ):
        """
        Jogosultság naplózása.
        
        Args:
            user_id: Felhasználó azonosító
            resource: Erőforrás
            action: Művelet
            granted: Engedélyezett volt-e
            details: Részletek
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.AUTHORIZATION,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            session_id=None,
            agent_type=None,
            severity=SecuritySeverity.HIGH if not granted else SecuritySeverity.LOW,
            source_ip=None,
            user_agent=None,
            event_data={
                "resource": resource,
                "action": action,
                "granted": granted,
                "details": self._sanitize_data(details or {})
            },
            metadata={}
        )
        
        await self.audit_queue.put(event)
    
    async def log_gdpr_event(
        self,
        event_type: str,
        user_id: str,
        data_type: str,
        details: Dict[str, Any] = None
    ):
        """
        GDPR esemény naplózása.
        
        Args:
            event_type: Esemény típusa
            user_id: Felhasználó azonosító
            data_type: Adattípus
            details: Részletek
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.GDPR_EVENT,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            session_id=None,
            agent_type=None,
            severity=SecuritySeverity.MEDIUM,
            source_ip=None,
            user_agent=None,
            event_data={
                "gdpr_event_type": event_type,
                "data_type": data_type,
                "details": self._sanitize_data(details or {})
            },
            metadata={}
        )
        
        await self.audit_queue.put(event)
    
    async def log_error(
        self,
        error_type: str,
        error_message: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        details: Dict[str, Any] = None
    ):
        """
        Hiba esemény naplózása.
        
        Args:
            error_type: Hiba típusa
            error_message: Hiba üzenet
            user_id: Felhasználó azonosító
            session_id: Session azonosító
            agent_type: Agent típusa
            details: Részletek
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.ERROR_EVENT,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            session_id=session_id,
            agent_type=agent_type,
            severity=SecuritySeverity.HIGH,
            source_ip=None,
            user_agent=None,
            event_data={
                "error_type": error_type,
                "error_message": self._sanitize_input(error_message),
                "details": self._sanitize_data(details or {})
            },
            metadata={}
        )
        
        await self.audit_queue.put(event)
    
    async def _log_event(self, event: AuditEvent):
        """Esemény naplózása minden célrendszerbe."""
        try:
            # Log to Supabase
            if self.supabase:
                await self._log_to_supabase(event)
            
            # Log to Logfire
            if self.logfire:
                await self._log_to_logfire(event)
            
            # Console log for development
            if os.getenv("ENVIRONMENT") == "development":
                self._log_to_console(event)
            
            # File log for backup
            await self._log_to_file(event)
            
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
    
    async def _log_to_supabase(self, event: AuditEvent):
        """Esemény naplózása Supabase-ba."""
        try:
            event_data = asdict(event)
            event_data["timestamp"] = event.timestamp.isoformat()
            event_data["event_type"] = event.event_type.value
            event_data["severity"] = event.severity.value
            
            await self.supabase.table("audit_logs").insert(event_data).execute()
            
        except Exception as e:
            logger.error(f"Error logging to Supabase: {e}")
    
    async def _log_to_logfire(self, event: AuditEvent):
        """Esemény naplózása Logfire-be."""
        try:
            if self.logfire:
                self.logfire.info(
                    f"Audit Event: {event.event_type.value}",
                    event_id=event.event_id,
                    user_id=event.user_id,
                    session_id=event.session_id,
                    agent_type=event.agent_type,
                    severity=event.severity.value,
                    source_ip=event.source_ip,
                    event_data=event.event_data,
                    metadata=event.metadata
                )
                
        except Exception as e:
            logger.error(f"Error logging to Logfire: {e}")
    
    def _log_to_console(self, event: AuditEvent):
        """Esemény naplózása konzolra (development)."""
        log_level = {
            SecuritySeverity.LOW: logging.INFO,
            SecuritySeverity.MEDIUM: logging.WARNING,
            SecuritySeverity.HIGH: logging.ERROR,
            SecuritySeverity.CRITICAL: logging.CRITICAL
        }.get(event.severity, logging.INFO)
        
        logger.log(
            log_level,
            f"AUDIT: {event.event_type.value} - User: {event.user_id} - "
            f"Severity: {event.severity.value} - {event.event_data}"
        )
    
    async def _log_to_file(self, event: AuditEvent):
        """Esemény naplózása fájlba (backup)."""
        try:
            log_file = os.getenv("AUDIT_LOG_FILE", "audit.log")
            event_data = asdict(event)
            event_data["timestamp"] = event.timestamp.isoformat()
            event_data["event_type"] = event.event_type.value
            event_data["severity"] = event.severity.value
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_data, ensure_ascii=False) + "\n")
                
        except Exception as e:
            logger.error(f"Error logging to file: {e}")
    
    async def _handle_critical_event(self, event: AuditEvent):
        """Kritikus esemény kezelése."""
        try:
            # Send alert to security team
            await self._send_security_alert(event)
            
            # Log to separate critical events log
            await self._log_critical_event(event)
            
        except Exception as e:
            logger.error(f"Error handling critical event: {e}")
    
    async def _handle_failed_auth(self, event: AuditEvent):
        """Sikertelen hitelesítés kezelése."""
        try:
            # Check for potential brute force attack
            if await self._is_potential_brute_force(event.user_id, event.source_ip):
                await self._handle_brute_force_attempt(event)
                
        except Exception as e:
            logger.error(f"Error handling failed auth: {e}")
    
    async def _is_potential_brute_force(self, user_id: str, source_ip: str) -> bool:
        """Brute force támadás felismerése."""
        # TODO: Implement brute force detection logic
        # This should check recent failed attempts from the same IP/user
        return False
    
    async def _handle_brute_force_attempt(self, event: AuditEvent):
        """Brute force támadás kezelése."""
        try:
            # Block IP temporarily
            await self._block_ip(event.source_ip)
            
            # Log security event
            await self.log_security_event(
                "brute_force_detected",
                SecuritySeverity.CRITICAL,
                event.user_id,
                f"Brute force attack detected from IP {event.source_ip}",
                {"blocked_ip": event.source_ip}
            )
            
        except Exception as e:
            logger.error(f"Error handling brute force attempt: {e}")
    
    async def _block_ip(self, ip_address: str):
        """IP cím blokkolása."""
        # TODO: Implement IP blocking logic
        # This should add the IP to a blocklist
        pass
    
    async def _send_security_alert(self, event: AuditEvent):
        """Biztonsági riasztás küldése."""
        # TODO: Implement security alert system
        # This should send alerts to security team via email/SMS/Slack
        pass
    
    async def _log_critical_event(self, event: AuditEvent):
        """Kritikus esemény külön naplózása."""
        try:
            critical_log_file = os.getenv("CRITICAL_AUDIT_LOG_FILE", "critical_audit.log")
            event_data = asdict(event)
            event_data["timestamp"] = event.timestamp.isoformat()
            event_data["event_type"] = event.event_type.value
            event_data["severity"] = event.severity.value
            
            with open(critical_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_data, ensure_ascii=False) + "\n")
                
        except Exception as e:
            logger.error(f"Error logging critical event: {e}")
    
    def _generate_event_id(self) -> str:
        """Egyedi esemény azonosító generálása."""
        return f"audit_{hashlib.md5(f'{datetime.now()}_{os.getpid()}'.encode()).hexdigest()}"
    
    def _sanitize_input(self, input_data: str) -> str:
        """Bemeneti adatok sanitizálása."""
        if not input_data:
            return ""
        
        import re
        
        # Remove XSS patterns
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<script[^>]*>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>'
        ]
        
        sanitized = input_data
        for pattern in xss_patterns:
            sanitized = re.sub(pattern, '***XSS_BLOCKED***', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove SQL injection patterns
        sql_patterns = [
            r'DROP\s+TABLE',
            r'DELETE\s+FROM',
            r'INSERT\s+INTO',
            r'UPDATE\s+SET',
            r'UNION\s+SELECT',
            r'OR\s+1\s*=\s*1',
            r'OR\s+\'1\'\s*=\s*\'1\'',
            r'--\s*$',
            r'/\*.*?\*/',
            r';\s*$'
        ]
        
        for pattern in sql_patterns:
            sanitized = re.sub(pattern, '***SQL_BLOCKED***', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove potentially sensitive information
        sensitive_patterns = [
            r'password["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'token["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'key["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'secret["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'secret\w+',  # Match words starting with "secret"
            r'password\w+',  # Match words starting with "password"
            r'token\w+',  # Match words starting with "token"
            r'key\w+'  # Match words starting with "key"
        ]
        
        for pattern in sensitive_patterns:
            sanitized = re.sub(pattern, '***MASKED***', sanitized, flags=re.IGNORECASE)
        
        # Limit length
        if len(sanitized) > 1000:
            sanitized = sanitized[:997] + "..."
        
        return sanitized
    
    def _sanitize_output(self, output_data: str) -> str:
        """Kimeneti adatok sanitizálása."""
        if not output_data:
            return ""
        
        import re
        
        # Remove XSS patterns
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<script[^>]*>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>'
        ]
        
        sanitized = output_data
        for pattern in xss_patterns:
            sanitized = re.sub(pattern, '***XSS_BLOCKED***', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove potentially sensitive information from responses
        sensitive_patterns = [
            r'jelszó["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'kártyaszám["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'cvv["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'pin["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'jelszava["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'secret\w+',  # Match words starting with "secret"
            r'password\w+',  # Match words starting with "password"
            r'token\w+',  # Match words starting with "token"
            r'key\w+',  # Match words starting with "key"
            r'secret\d+',  # Match "secret" followed by numbers
            r'password\d+',  # Match "password" followed by numbers
            r'token\d+',  # Match "token" followed by numbers
            r'key\d+'  # Match "key" followed by numbers
        ]
        
        for pattern in sensitive_patterns:
            sanitized = re.sub(pattern, '***MASKED***', sanitized, flags=re.IGNORECASE)
        
        # Limit length
        if len(sanitized) > 1000:
            sanitized = sanitized[:997] + "..."
        
        return sanitized
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Adatok sanitizálása."""
        if not data:
            return {}
        
        sanitized = {}
        sensitive_keys = ["password", "token", "key", "secret", "jelszó", "kártyaszám", "cvv", "pin"]
        
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "***MASKED***"
            elif isinstance(value, str):
                sanitized[key] = self._sanitize_input(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            else:
                sanitized[key] = value
        
        return sanitized


# Singleton instance
_security_audit_logger: Optional[SecurityAuditLogger] = None


def get_security_audit_logger() -> SecurityAuditLogger:
    """
    Security audit logger singleton instance.
    
    Returns:
        SecurityAuditLogger instance
    """
    global _security_audit_logger
    if _security_audit_logger is None:
        _security_audit_logger = SecurityAuditLogger()
    return _security_audit_logger


@asynccontextmanager
async def audit_context(
    agent_type: str,
    user_id: str,
    session_id: str,
    query: str,
    metadata: Dict[str, Any] = None
):
    """
    Audit context manager agent interakciókhoz.
    
    Args:
        agent_type: Agent típusa
        user_id: Felhasználó azonosító
        session_id: Session azonosító
        query: Felhasználói kérés
        metadata: Metaadatok
    """
    start_time = datetime.now(timezone.utc)
    audit_logger = get_security_audit_logger()
    
    try:
        yield
    finally:
        end_time = datetime.now(timezone.utc)
        processing_time = (end_time - start_time).total_seconds()
        
        # Add processing time to metadata
        if metadata is None:
            metadata = {}
        metadata["processing_time"] = processing_time
        
        # Log the interaction
        await audit_logger.log_agent_interaction(
            agent_type=agent_type,
            user_id=user_id,
            session_id=session_id,
            query=query,
            response="[Response captured in context]",
            metadata=metadata
        ) 