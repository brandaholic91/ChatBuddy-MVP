"""
Security Context Engineering - Chatbuddy MVP.

Ez a modul implementálja a biztonsági prompt-okat és context engineering-et
minden agent számára, GDPR megfelelőséggel és defense-in-depth megközelítéssel.
"""

from typing import Dict, Any, List
from enum import Enum
from dataclasses import dataclass


class SecurityLevel(Enum):
    """Biztonsági szintek klasszifikáció."""
    SAFE = "safe"           # Nyilvános, általános információk
    SENSITIVE = "sensitive" # Ügyfél specifikus, de nem kritikus
    RESTRICTED = "restricted" # Érzékeny üzleti információk
    FORBIDDEN = "forbidden"   # Tilos információk (jelszavak, belső rendszerek)


@dataclass
class SecurityContext:
    """Biztonsági kontextus minden agent interakcióhoz."""
    user_id: str
    session_id: str
    security_level: SecurityLevel
    permissions: List[str]
    data_access_scope: List[str]
    audit_required: bool = True


# =============================================================================
# COORDINATOR AGENT SECURITY PROMPTS
# =============================================================================

COORDINATOR_SECURITY_PROMPT = """
Te egy tapasztalt magyar ügyfélszolgálati koordinátor vagy, aki szigorú biztonsági protokollokat követ.

BIZTONSÁGI SZABÁLYOK:
1. SOHA ne közölj belső rendszer információkat
2. SOHA ne dolgozz fel személyes adatokat a jóváhagyás nélkül
3. Minden kérdéses kérést EMBERI FELÜGYELETRE továbbíts
4. Naplózd minden döntésedet audit célokra
5. Csak a minimálisan szükséges adatokat oszd meg
6. Minden kérést biztonsági szint szerint kategorizálj

KLASSZIFIKÁCIÓS PROTOKOLL:
- BIZTONSÁGOS: általános termékinformációk, nyilvános adatok, árak
- ÉRZÉKENY: rendelési adatok, ügyfél specifikus információk, preferenciák
- TILOS: jelszavak, belső dokumentumok, admin funkciók, beszerzési árak

VÁLASZ STRUKTÚRA:
1. Biztonsági klasszifikáció (SAFE/SENSITIVE/RESTRICTED/FORBIDDEN)
2. Szükséges ügynök azonosítása
3. Kockázatértékelés (1-10 skálán)
4. Döntés indoklása
5. Audit log bejegyzés

GDPR MEGFELELŐSÉG:
- Csak a szükséges minimális adatokat dolgozd fel
- Felhasználói hozzájárulás ellenőrzése minden adatművelet előtt
- Automatikus adatmaszkolás érzékeny információkhoz
- Right to be forgotten támogatás

Válasz előtt mindig értékeld a kérés biztonsági szintjét!
"""


# =============================================================================
# PRODUCT INFO AGENT SECURITY PROMPTS
# =============================================================================

PRODUCT_AGENT_SECURITY_PROMPT = """
Te egy termékszakértő vagy, aki csak ELLENŐRZÖTT és NYILVÁNOS termékadatokat közöl.

ADATBIZTONSÁGI SZABÁLYOK:
- Csak a termék publikus adatait közöld
- SOHA ne adj ki beszerzési árakat vagy margin információkat
- Készlet adatokat csak általános formában (van/nincs készleten)
- Versenytárs információkat ne közölj
- Termék leírásokat csak ellenőrzött forrásokból használd

VÁLASZ PROTOKOLL:
1. Adatok forrásának ellenőrzése
2. Publikációs engedély validálása
3. Strukturált válasz generálása
4. Biztonsági audit log bejegyzés

TILTOTT INFORMÁCIÓK:
- Beszerzési árak
- Szállítói adatok  
- Belső költségstruktúra
- Fejlesztés alatt álló termékek
- Versenytárs specifikus információk
- Belső termék kódok

GDPR COMPLIANCE:
- Termék adatok csak nyilvános forrásokból
- Nincs személyes adat feldolgozás
- Automatikus adatminimalizáció
"""


# =============================================================================
# ORDER STATUS AGENT SECURITY PROMPTS
# =============================================================================

ORDER_AGENT_SECURITY_PROMPT = """
Te egy rendeléskezelő szakértő vagy, aki **SZIGORÚ** adatvédelmi protokollokat követ.

HOZZÁFÉRÉS VALIDÁCIÓ:
1. Ügyfél identitás KÖTELEZŐ ellenőrzése
2. Jogosultság validálása rendelés hozzáféréshez
3. Adatmaszkolás nem jogosult kérések esetén
4. Session timeout ellenőrzése

GDPR MEGFELELŐSÉG:
- Csak a szükséges minimális adatok megosztása
- Automatikus anonimizálás 30 nap után
- Felhasználói hozzájárulás ellenőrzése
- Right to be forgotten támogatás

ÉRZÉKENY ADATOK KEZELÉSE:
- Kártyaszámok SOHA nem jeleníthetők meg
- Szállítási címek csak részlegesen
- Számlázási adatok csak jogosult hozzáférés esetén
- Jelszavak és PIN kódok soha nem

SECURITY WORKFLOW:
1. Identity verification
2. Authorization check
3. Data level assessment
4. Minimal exposure principle
5. Audit logging
6. Data masking

AUDIT REQUIREMENTS:
- Minden adathozzáférés naplózása
- Felhasználói hozzájárulás dokumentálása
- Adatmegőrzési időszak követése
- Security incident reporting
"""


# =============================================================================
# RECOMMENDATION AGENT SECURITY PROMPTS
# =============================================================================

RECOMMENDATION_AGENT_SECURITY_PROMPT = """
Te egy termékajánló szakértő vagy, aki GDPR-compliant ajánlásokat ad.

AJÁNLÁSI BIZTONSÁG:
- Csak felhasználói hozzájárulás alapján dolgozz fel preferenciákat
- Anonimizált ajánlási algoritmusok használata
- Nincs személyes adat tárolás ajánlásokhoz
- Opt-out mechanizmus minden ajánláshoz

ADATFELDOLGOZÁSI SZABÁLYOK:
- Preferenciák csak session alatt tárolva
- Nincs cross-session tracking
- Automatikus adattörlés session végén
- Transzparens ajánlási logika

GDPR COMPLIANCE:
- Explicit consent minden adatfeldolgozáshoz
- Data minimization principle
- Purpose limitation
- Storage limitation
- Accountability és audit trail
"""


# =============================================================================
# MARKETING AGENT SECURITY PROMPTS
# =============================================================================

MARKETING_AGENT_SECURITY_PROMPT = """
Te egy marketing szakértő vagy, aki GDPR-compliant marketing kommunikációt végez.

MARKETING BIZTONSÁG:
- Csak explicit consent alapján küldj marketing üzeneteket
- Opt-out mechanizmus minden kommunikációban
- Nincs unsolicited marketing
- Preference center támogatás

ADATFELDOLGOZÁSI SZABÁLYOK:
- Marketing preferences csak consent alapján
- Unsubscribe minden email-ben
- Preference management dashboard
- Data retention policy követése

GDPR COMPLIANCE:
- Lawful basis for processing
- Consent management
- Right to withdraw consent
- Data portability
- Marketing preference controls
"""


# =============================================================================
# SECURITY CONTEXT VALIDATION FUNCTIONS
# =============================================================================

def validate_security_context(context: SecurityContext) -> bool:
    """
    Biztonsági kontextus validálása.
    
    Args:
        context: SecurityContext objektum
        
    Returns:
        True ha valid, False ha nem
    """
    if not context.user_id or not context.session_id:
        return False
    
    if not isinstance(context.permissions, list):
        return False
    
    if not isinstance(context.data_access_scope, list):
        return False
    
    return True


def classify_security_level(query: str, user_context: Dict[str, Any]) -> SecurityLevel:
    """
    Kérés biztonsági szintjének meghatározása.
    
    Args:
        query: Felhasználói kérés
        user_context: Felhasználói kontextus
        
    Returns:
        SecurityLevel enum
    """
    query_lower = query.lower()
    
    # FORBIDDEN keywords
    forbidden_keywords = [
        "jelszó", "jelszavam", "password", "admin", "root", "system", "internal",
        "beszerzési ár", "margin", "profit", "költség", "belső",
        "source code", "database", "config", "secret", "key"
    ]
    
    if any(keyword in query_lower for keyword in forbidden_keywords):
        return SecurityLevel.FORBIDDEN
    
    # RESTRICTED keywords
    restricted_keywords = [
        "rendelés", "order", "számla", "invoice", "fizetés", "payment",
        "kártya", "card", "szállítási cím", "billing", "személyes"
    ]
    
    if any(keyword in query_lower for keyword in restricted_keywords):
        return SecurityLevel.RESTRICTED
    
    # SENSITIVE keywords
    sensitive_keywords = [
        "ajánlás", "recommendation", "preferencia", "preference",
        "kedvezmény", "discount", "kupon", "coupon", "akció", "promotion"
    ]
    
    if any(keyword in query_lower for keyword in sensitive_keywords):
        return SecurityLevel.SENSITIVE
    
    # Default to SAFE
    return SecurityLevel.SAFE


def sanitize_for_audit(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adatok sanitizálása audit log-hoz.
    
    Args:
        data: Eredeti adatok
        
    Returns:
        Sanitizált adatok
    """
    sensitive_fields = [
        "password", "jelszó", "token", "key", "secret", "card_number",
        "kártyaszám", "cvv", "pin", "email", "telefon", "cím"
    ]
    
    def _sanitize_recursive(obj):
        if isinstance(obj, dict):
            sanitized = {}
            for key, value in obj.items():
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    sanitized[key] = "***MASKED***"
                else:
                    sanitized[key] = _sanitize_recursive(value)
            return sanitized
        elif isinstance(obj, list):
            return [_sanitize_recursive(item) for item in obj]
        else:
            return obj
    
    return _sanitize_recursive(data)


# =============================================================================
# GDPR COMPLIANCE FUNCTIONS
# =============================================================================

def check_user_consent(user_id: str, data_type: str) -> bool:
    """
    Felhasználói hozzájárulás ellenőrzése.
    
    Args:
        user_id: Felhasználó azonosító
        data_type: Adattípus
        
    Returns:
        True ha van hozzájárulás, False ha nincs
    """
    # TODO: Implement actual consent checking logic
    # This should check against a consent management system
    return True


def log_gdpr_event(event_type: str, user_id: str, data_type: str, details: Dict[str, Any]):
    """
    GDPR esemény naplózása.
    
    Args:
        event_type: Esemény típusa
        user_id: Felhasználó azonosító
        data_type: Adattípus
        details: További részletek
    """
    # TODO: Implement GDPR event logging
    # This should log to a GDPR-compliant audit system
    pass


def anonymize_user_data(user_id: str) -> bool:
    """
    Felhasználói adatok anonimizálása (Right to be forgotten).
    
    Args:
        user_id: Felhasználó azonosító
        
    Returns:
        True ha sikeres, False ha nem
    """
    # TODO: Implement data anonymization
    # This should anonymize all user data across the system
    return True


# =============================================================================
# SECURITY PROMPT TEMPLATES
# =============================================================================

def get_agent_security_prompt(agent_type: str, context: SecurityContext) -> str:
    """
    Agent-specifikus biztonsági prompt generálása.
    
    Args:
        agent_type: Agent típusa
        context: Biztonsági kontextus
        
    Returns:
        Biztonsági prompt
    """
    base_prompts = {
        "coordinator": COORDINATOR_SECURITY_PROMPT,
        "product": PRODUCT_AGENT_SECURITY_PROMPT,
        "order": ORDER_AGENT_SECURITY_PROMPT,
        "recommendation": RECOMMENDATION_AGENT_SECURITY_PROMPT,
        "marketing": MARKETING_AGENT_SECURITY_PROMPT
    }
    
    base_prompt = base_prompts.get(agent_type, COORDINATOR_SECURITY_PROMPT)
    
    # Add context-specific information
    context_info = f"""
AKTUÁLIS BIZTONSÁGI KONTEXTUS:
- Felhasználó ID: {context.user_id}
- Session ID: {context.session_id}
- Biztonsági szint: {context.security_level.value}
- Jogosultságok: {', '.join(context.permissions)}
- Adathozzáférési scope: {', '.join(context.data_access_scope)}
- Audit szükséges: {context.audit_required}

Minden válaszodat ezek alapján kell formálnod!
"""
    
    return base_prompt + context_info


def create_security_context(
    user_id: str,
    session_id: str,
    query: str,
    user_context: Dict[str, Any]
) -> SecurityContext:
    """
    Biztonsági kontextus létrehozása.
    
    Args:
        user_id: Felhasználó azonosító
        session_id: Session azonosító
        query: Felhasználói kérés
        user_context: Felhasználói kontextus
        
    Returns:
        SecurityContext objektum
    """
    security_level = classify_security_level(query, user_context)
    
    # Determine permissions based on user context
    permissions = user_context.get("permissions", ["basic_access"])
    
    # Determine data access scope
    data_access_scope = user_context.get("data_access_scope", ["public"])
    
    return SecurityContext(
        user_id=user_id,
        session_id=session_id,
        security_level=security_level,
        permissions=permissions,
        data_access_scope=data_access_scope,
        audit_required=security_level in [SecurityLevel.RESTRICTED, SecurityLevel.FORBIDDEN]
    ) 