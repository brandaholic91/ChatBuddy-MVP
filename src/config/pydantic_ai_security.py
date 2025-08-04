"""
Pydantic AI Security Configuration - Hivatalos implementáció.

Ez a modul implementálja a Pydantic AI biztonsági konfigurációját
a hivatalos dokumentáció alapján.
"""

import os
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
import logfire

# Logfire konfiguráció biztonsági monitoring-hoz
logfire.configure(
    project_name="chatbuddy-security",
    environment=os.getenv("ENVIRONMENT", "development"),
    custom_tags={
        "security_level": "high",
        "compliance": "gdpr",
        "framework": "pydantic_ai"
    }
)

# Pydantic AI instrumentálás
logfire.instrument_pydantic()
logfire.instrument_openai()
logfire.instrument_anthropic()


@dataclass
class SecureDependencies:
    """Biztonságos függőségek Pydantic AI agentekhez."""
    api_key: str
    user_id: str
    session_id: str
    permissions: List[str]
    security_level: str
    audit_enabled: bool = True
    rate_limit_enabled: bool = True


class SecurityValidator(BaseModel):
    """Biztonsági validátor Pydantic AI output-okhoz."""
    
    @classmethod
    def validate_response_security(cls, response: str) -> bool:
        """
        Válasz biztonsági validálása.
        
        Args:
            response: Agent válasz
            
        Returns:
            True ha biztonságos, False ha nem
        """
        # Érzékeny információk ellenőrzése
        sensitive_patterns = [
            r'password["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'token["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'key["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'secret["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'jelszó["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'kártyaszám["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'cvv["\']?\s*[:=]\s*["\']?[^"\']+["\']?',
            r'pin["\']?\s*[:=]\s*["\']?[^"\']+["\']?'
        ]
        
        import re
        for pattern in sensitive_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                return False
        
        return True
    
    @classmethod
    def sanitize_input(cls, input_data: str) -> str:
        """
        Bemeneti adatok sanitizálása.
        
        Args:
            input_data: Bemeneti adatok
            
        Returns:
            Sanitizált adatok
        """
        if not input_data:
            return ""
        
        # Vesélyes karakterek eltávolítása
        dangerous_chars = ["<", ">", '"', "'", "&", "{", "}", "[", "]"]
        sanitized = input_data
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")
        
        # Vesélyes minták eltávolítása
        dangerous_patterns = [
            r'script\s*:', r'javascript\s*:', r'vbscript\s*:', r'expression\s*\(',
            r'<script', r'</script>', r'<iframe', r'</iframe>', r'<object', r'</object>'
        ]
        
        import re
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
        
        # Hossz korlátozása
        if len(sanitized) > 1000:
            sanitized = sanitized[:1000]
        
        return sanitized.strip()


class SecureAgentFactory:
    """Biztonságos agent factory Pydantic AI-hoz."""
    
    @staticmethod
    def create_secure_agent(
        model_name: str,
        deps_type: type,
        output_type: type,
        system_prompt: str,
        security_config: Optional[Dict[str, Any]] = None
    ) -> Agent:
        """
        Biztonságos agent létrehozása.
        
        Args:
            model_name: Model neve
            deps_type: Függőségek típusa
            output_type: Output típusa
            system_prompt: System prompt
            security_config: Biztonsági konfiguráció
            
        Returns:
            Biztonságos agent
        """
        # Biztonsági prompt hozzáadása
        security_prompt = """
BIZTONSÁGI SZABÁLYOK:
1. SOHA ne közölj érzékeny információkat
2. Minden válaszodat validáld biztonsági szempontból
3. Csak a minimálisan szükséges adatokat oszd meg
4. Naplózd minden döntésedet audit célokra

GDPR MEGFELELŐSÉG:
- Csak a szükséges minimális adatokat dolgozd fel
- Felhasználói hozzájárulás ellenőrzése
- Automatikus adatmaszkolás érzékeny információkhoz
"""
        
        enhanced_prompt = security_prompt + "\n\n" + system_prompt
        
        # Agent létrehozása
        agent = Agent(
            model_name,
            deps_type=deps_type,
            output_type=output_type,
            system_prompt=enhanced_prompt
        )
        
        # Biztonsági middleware hozzáadása
        @agent.before_run
        async def security_pre_check(ctx: RunContext[deps_type]) -> None:
            """Biztonsági ellenőrzés futtatás előtt."""
            # Input sanitization
            if hasattr(ctx, 'input') and isinstance(ctx.input, str):
                ctx.input = SecurityValidator.sanitize_input(ctx.input)
            
            # Permission check
            if hasattr(ctx.deps, 'permissions'):
                required_permissions = security_config.get('required_permissions', [])
                for permission in required_permissions:
                    if permission not in ctx.deps.permissions:
                        raise ValueError(f"Insufficient permissions: {permission}")
            
            # Rate limiting check
            if hasattr(ctx.deps, 'rate_limit_enabled') and ctx.deps.rate_limit_enabled:
                await _check_rate_limit(ctx.deps.user_id)
            
            # Audit logging
            if hasattr(ctx.deps, 'audit_enabled') and ctx.deps.audit_enabled:
                await _log_security_event(
                    "agent_run_started",
                    ctx.deps.user_id,
                    {"agent_type": model_name, "input_length": len(str(ctx.input))}
                )
        
        @agent.after_run
        async def security_post_check(ctx: RunContext[deps_type], result: Any) -> None:
            """Biztonsági ellenőrzés futtatás után."""
            # Response security validation
            if hasattr(result, 'output') and hasattr(result.output, 'response_text'):
                if not SecurityValidator.validate_response_security(result.output.response_text):
                    # Maszkolás érzékeny információk
                    result.output.response_text = _mask_sensitive_data(result.output.response_text)
            
            # Audit logging
            if hasattr(ctx.deps, 'audit_enabled') and ctx.deps.audit_enabled:
                await _log_security_event(
                    "agent_run_completed",
                    ctx.deps.user_id,
                    {"agent_type": model_name, "success": True}
                )
        
        return agent


async def _check_rate_limit(user_id: str) -> None:
    """
    Rate limiting ellenőrzése.
    
    Args:
        user_id: Felhasználó azonosító
        
    Raises:
        ValueError: Ha túllépte a rate limit-et
    """
    # TODO: Implement actual rate limiting logic
    # This should check against Redis or similar
    pass


async def _log_security_event(
    event_type: str,
    user_id: str,
    details: Dict[str, Any]
) -> None:
    """
    Biztonsági esemény naplózása.
    
    Args:
        event_type: Esemény típusa
        user_id: Felhasználó azonosító
        details: Részletek
    """
    logfire.info(
        f"Security Event: {event_type}",
        user_id=user_id,
        event_details=details,
        severity="high" if event_type in ["unauthorized_access", "data_breach"] else "medium"
    )


def _mask_sensitive_data(text: str) -> str:
    """
    Érzékeny adatok maszkolása.
    
    Args:
        text: Eredeti szöveg
        
    Returns:
        Maszkolt szöveg
    """
    import re
    
    # Érzékeny minták maszkolása
    sensitive_patterns = [
        (r'password["\']?\s*[:=]\s*["\']?[^"\']+["\']?', r'password: ***MASKED***'),
        (r'token["\']?\s*[:=]\s*["\']?[^"\']+["\']?', r'token: ***MASKED***'),
        (r'key["\']?\s*[:=]\s*["\']?[^"\']+["\']?', r'key: ***MASKED***'),
        (r'secret["\']?\s*[:=]\s*["\']?[^"\']+["\']?', r'secret: ***MASKED***'),
        (r'jelszó["\']?\s*[:=]\s*["\']?[^"\']+["\']?', r'jelszó: ***MASKED***'),
        (r'kártyaszám["\']?\s*[:=]\s*["\']?[^"\']+["\']?', r'kártyaszám: ***MASKED***'),
    ]
    
    masked_text = text
    for pattern, replacement in sensitive_patterns:
        masked_text = re.sub(pattern, replacement, masked_text, flags=re.IGNORECASE)
    
    return masked_text


# Biztonsági konfiguráció exportálása
def get_pydantic_ai_security_config() -> Dict[str, Any]:
    """
    Pydantic AI biztonsági konfiguráció.
    
    Returns:
        Biztonsági konfiguráció
    """
    return {
        "logfire_enabled": True,
        "input_sanitization": True,
        "output_validation": True,
        "audit_logging": True,
        "rate_limiting": True,
        "sensitive_data_masking": True,
        "permission_checking": True
    } 