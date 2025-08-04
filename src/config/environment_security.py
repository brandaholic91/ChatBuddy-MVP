"""
Environment Variables Security Validation - Chatbuddy MVP.

Ez a modul implementálja a környezeti változók biztonsági validációját
és a production-ready environment setup-ot.
"""

import os
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class EnvironmentType(Enum):
    """Környezet típusok."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class SecurityRequirement:
    """Biztonsági követelmény környezeti változóhoz."""
    name: str
    required: bool
    min_length: Optional[int] = None
    pattern: Optional[str] = None
    allowed_values: Optional[List[str]] = None
    sensitive: bool = False
    description: str = ""


class EnvironmentSecurityValidator:
    """Környezeti változók biztonsági validátora."""
    
    def __init__(self):
        self.requirements = self._get_security_requirements()
        self.environment = self._get_environment_type()
    
    def _get_environment_type(self) -> EnvironmentType:
        """Környezet típusának meghatározása."""
        env_str = os.getenv("ENVIRONMENT", "development").lower()
        
        if env_str == "production":
            return EnvironmentType.PRODUCTION
        elif env_str == "staging":
            return EnvironmentType.STAGING
        elif env_str == "testing":
            return EnvironmentType.TESTING
        else:
            return EnvironmentType.DEVELOPMENT
    
    def _get_security_requirements(self) -> Dict[str, SecurityRequirement]:
        """Biztonsági követelmények definiálása."""
        return {
            # AI API Keys
            "OPENAI_API_KEY": SecurityRequirement(
                name="OPENAI_API_KEY",
                required=True,
                min_length=20,
                pattern=r"^sk-[a-zA-Z0-9_-]{32,}$",
                sensitive=True,
                description="OpenAI API kulcs"
            ),
            "ANTHROPIC_API_KEY": SecurityRequirement(
                name="ANTHROPIC_API_KEY",
                required=False,
                min_length=20,
                pattern=r"^sk-ant-[a-zA-Z0-9_-]{32,}$",
                sensitive=True,
                description="Anthropic API kulcs"
            ),
            
            # Database
            "SUPABASE_URL": SecurityRequirement(
                name="SUPABASE_URL",
                required=True,
                pattern=r"^https://[a-zA-Z0-9-]+\.supabase\.co$",
                sensitive=False,
                description="Supabase URL"
            ),
            "SUPABASE_ANON_KEY": SecurityRequirement(
                name="SUPABASE_ANON_KEY",
                required=True,
                min_length=100,
                sensitive=True,
                description="Supabase anonim kulcs"
            ),
            "SUPABASE_SERVICE_KEY": SecurityRequirement(
                name="SUPABASE_SERVICE_KEY",
                required=True,
                min_length=100,
                sensitive=True,
                description="Supabase service kulcs"
            ),
            
            # Security
            "SECRET_KEY": SecurityRequirement(
                name="SECRET_KEY",
                required=True,
                min_length=32,
                sensitive=True,
                description="Alkalmazás titkos kulcs"
            ),
            "JWT_SECRET": SecurityRequirement(
                name="JWT_SECRET",
                required=True,
                min_length=32,
                sensitive=True,
                description="JWT titkos kulcs"
            ),
            
            # Redis
            "REDIS_URL": SecurityRequirement(
                name="REDIS_URL",
                required=False,
                pattern=r"^redis://[a-zA-Z0-9.-]+:\d+$",
                sensitive=False,
                description="Redis kapcsolat URL"
            ),
            "REDIS_PASSWORD": SecurityRequirement(
                name="REDIS_PASSWORD",
                required=False,
                min_length=8,
                sensitive=True,
                description="Redis jelszó"
            ),
            
            # Rate Limiting
            "RATE_LIMIT_DEFAULT": SecurityRequirement(
                name="RATE_LIMIT_DEFAULT",
                required=False,
                allowed_values=["100/minute", "200/minute", "500/minute"],
                sensitive=False,
                description="Alapértelmezett rate limit"
            ),
            
            # CORS
            "ALLOWED_ORIGINS": SecurityRequirement(
                name="ALLOWED_ORIGINS",
                required=False,
                sensitive=False,
                description="Engedélyezett CORS origin-ok"
            ),
            
            # Monitoring
            "LOGFIRE_TOKEN": SecurityRequirement(
                name="LOGFIRE_TOKEN",
                required=False,
                min_length=20,
                sensitive=True,
                description="Logfire monitoring token"
            ),
            
            # Email
            "SENDGRID_API_KEY": SecurityRequirement(
                name="SENDGRID_API_KEY",
                required=False,
                min_length=20,
                sensitive=True,
                description="SendGrid API kulcs"
            ),
            
            # SMS
            "TWILIO_ACCOUNT_SID": SecurityRequirement(
                name="TWILIO_ACCOUNT_SID",
                required=False,
                min_length=20,
                sensitive=True,
                description="Twilio Account SID"
            ),
            "TWILIO_AUTH_TOKEN": SecurityRequirement(
                name="TWILIO_AUTH_TOKEN",
                required=False,
                min_length=20,
                sensitive=True,
                description="Twilio Auth Token"
            ),
        }
    
    def validate_environment(self) -> Dict[str, Any]:
        """
        Teljes környezet validálása.
        
        Returns:
            Validációs eredmények
        """
        results = {
            "valid": True,
            "environment": self.environment.value,
            "missing_vars": [],
            "invalid_vars": [],
            "warnings": [],
            "sensitive_vars_present": []
        }
        
        for var_name, requirement in self.requirements.items():
            value = os.getenv(var_name)
            
            # Ellenőrizzük, hogy szükséges-e
            if requirement.required and not value:
                results["missing_vars"].append({
                    "name": var_name,
                    "description": requirement.description
                })
                results["valid"] = False
                continue
            
            # Ha nincs érték és nem szükséges, folytatjuk
            if not value:
                continue
            
            # Érzékeny változók jelenlétének ellenőrzése
            if requirement.sensitive:
                results["sensitive_vars_present"].append(var_name)
            
            # Hossz ellenőrzése
            if requirement.min_length and len(value) < requirement.min_length:
                results["invalid_vars"].append({
                    "name": var_name,
                    "reason": f"Túl rövid (minimum {requirement.min_length} karakter)",
                    "description": requirement.description
                })
                results["valid"] = False
                continue
            
            # Pattern ellenőrzése
            if requirement.pattern and not re.match(requirement.pattern, value):
                results["invalid_vars"].append({
                    "name": var_name,
                    "reason": "Nem megfelelő formátum",
                    "description": requirement.description
                })
                results["valid"] = False
                continue
            
            # Engedélyezett értékek ellenőrzése
            if requirement.allowed_values and value not in requirement.allowed_values:
                results["invalid_vars"].append({
                    "name": var_name,
                    "reason": f"Érték nem engedélyezett. Engedélyezett: {', '.join(requirement.allowed_values)}",
                    "description": requirement.description
                })
                results["valid"] = False
                continue
        
        # Production környezet speciális ellenőrzések
        if self.environment == EnvironmentType.PRODUCTION:
            production_warnings = self._validate_production_requirements()
            results["warnings"].extend(production_warnings)
        
        return results
    
    def _validate_production_requirements(self) -> List[str]:
        """Production környezet speciális ellenőrzései."""
        warnings = []
        
        # Production-ban minden érzékeny változónak jelen kell lennie
        required_production_vars = [
            "SECRET_KEY", "JWT_SECRET", "SUPABASE_SERVICE_KEY"
        ]
        
        for var_name in required_production_vars:
            if not os.getenv(var_name):
                warnings.append(f"Production környezetben {var_name} kötelező")
        
        # Production-ban nem lehet development értékek
        development_patterns = [
            (r"localhost", "localhost URL production-ban"),
            (r"127\.0\.0\.1", "localhost IP production-ban"),
            (r"test", "test értékek production-ban"),
            (r"dev", "development értékek production-ban")
        ]
        
        for var_name, value in os.environ.items():
            for pattern, warning in development_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    warnings.append(f"{var_name}: {warning}")
        
        return warnings
    
    def get_environment_summary(self) -> Dict[str, Any]:
        """
        Környezet összefoglaló (érzékeny adatok nélkül).
        
        Returns:
            Környezet összefoglaló
        """
        summary = {
            "environment": self.environment.value,
            "total_vars": len(self.requirements),
            "required_vars": len([r for r in self.requirements.values() if r.required]),
            "sensitive_vars": len([r for r in self.requirements.values() if r.sensitive]),
            "present_vars": 0,
            "missing_vars": 0,
            "sensitive_vars_present": 0
        }
        
        for var_name, requirement in self.requirements.items():
            if os.getenv(var_name):
                summary["present_vars"] += 1
                if requirement.sensitive:
                    summary["sensitive_vars_present"] += 1
            elif requirement.required:
                summary["missing_vars"] += 1
        
        return summary
    
    def validate_specific_variable(self, var_name: str) -> Dict[str, Any]:
        """
        Egy konkrét változó validálása.
        
        Args:
            var_name: Változó neve
            
        Returns:
            Validációs eredmény
        """
        if var_name not in self.requirements:
            return {
                "valid": False,
                "reason": "Ismeretlen változó",
                "sensitive": False
            }
        
        requirement = self.requirements[var_name]
        value = os.getenv(var_name)
        
        result = {
            "valid": True,
            "present": bool(value),
            "sensitive": requirement.sensitive,
            "required": requirement.required,
            "description": requirement.description,
            "issues": []
        }
        
        if requirement.required and not value:
            result["valid"] = False
            result["issues"].append("Kötelező változó hiányzik")
            return result
        
        if not value:
            return result
        
        # Hossz ellenőrzése
        if requirement.min_length and len(value) < requirement.min_length:
            result["valid"] = False
            result["issues"].append(f"Túl rövid (minimum {requirement.min_length} karakter)")
        
        # Pattern ellenőrzése
        if requirement.pattern and not re.match(requirement.pattern, value):
            result["valid"] = False
            result["issues"].append("Nem megfelelő formátum")
        
        # Engedélyezett értékek ellenőrzése
        if requirement.allowed_values and value not in requirement.allowed_values:
            result["valid"] = False
            result["issues"].append(f"Érték nem engedélyezett. Engedélyezett: {', '.join(requirement.allowed_values)}")
        
        return result


# Singleton instance
_environment_validator: Optional[EnvironmentSecurityValidator] = None


def get_environment_validator() -> EnvironmentSecurityValidator:
    """
    Environment validator singleton instance.
    
    Returns:
        EnvironmentSecurityValidator instance
    """
    global _environment_validator
    if _environment_validator is None:
        _environment_validator = EnvironmentSecurityValidator()
    return _environment_validator


def validate_environment_on_startup() -> bool:
    """
    Környezet validálása alkalmazás indításakor.
    
    Returns:
        True ha valid, False ha nem
    """
    validator = get_environment_validator()
    results = validator.validate_environment()
    
    if not results["valid"]:
        print("❌ Környezeti változók validálása SIKERTELEN:")
        
        if results["missing_vars"]:
            print("\nHiányzó kötelező változók:")
            for var in results["missing_vars"]:
                print(f"  - {var['name']}: {var['description']}")
        
        if results["invalid_vars"]:
            print("\nÉrvénytelen változók:")
            for var in results["invalid_vars"]:
                print(f"  - {var['name']}: {var['reason']}")
        
        if results["warnings"]:
            print("\nFigyelmeztetések:")
            for warning in results["warnings"]:
                print(f"  - {warning}")
        
        return False
    
    print("✅ Környezeti változók validálása SIKERES")
    
    if results["warnings"]:
        print("\n⚠️  Figyelmeztetések:")
        for warning in results["warnings"]:
            print(f"  - {warning}")
    
    summary = validator.get_environment_summary()
    print(f"\n📊 Környezet összefoglaló:")
    print(f"  - Környezet: {summary['environment']}")
    print(f"  - Jelen lévő változók: {summary['present_vars']}/{summary['total_vars']}")
    print(f"  - Érzékeny változók: {summary['sensitive_vars_present']}/{summary['sensitive_vars']}")
    
    return True 