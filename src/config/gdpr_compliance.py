"""
GDPR Compliance Layer - Chatbuddy MVP.

Ez a modul implementálja a GDPR megfelelőséget és adatvédelmi intézkedéseket
a Chatbuddy MVP rendszerében.
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DataCategory(Enum):
    """Adatkategóriák GDPR szerint."""
    PERSONAL = "personal"           # Személyes adatok
    SENSITIVE = "sensitive"         # Érzékeny adatok
    TECHNICAL = "technical"         # Technikai adatok
    ANALYTICAL = "analytical"       # Analitikai adatok
    MARKETING = "marketing"         # Marketing adatok


class ConsentType(Enum):
    """Hozzájárulás típusok."""
    NECESSARY = "necessary"         # Szükséges működéshez
    FUNCTIONAL = "functional"       # Funkcionális
    ANALYTICAL = "analytical"       # Analitikai
    MARKETING = "marketing"         # Marketing
    THIRD_PARTY = "third_party"     # Harmadik fél


@dataclass
class UserConsent:
    """Felhasználói hozzájárulás rekord."""
    user_id: str
    consent_type: ConsentType
    data_category: DataCategory
    granted: bool
    granted_at: datetime
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class DataProcessingRecord:
    """Adatfeldolgozási rekord GDPR audit-hoz."""
    processing_id: str
    user_id: str
    data_category: DataCategory
    purpose: str
    legal_basis: str
    processed_at: datetime
    retention_period: timedelta
    data_subjects: List[str]
    data_recipients: List[str]
    third_country_transfers: List[str]
    safeguards: List[str]


class GDPRComplianceLayer:
    """GDPR megfelelőségi réteg."""
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self.retention_policies = self._load_retention_policies()
        self.legal_bases = self._load_legal_bases()
    
    def _load_retention_policies(self) -> Dict[DataCategory, timedelta]:
        """Adatmegőrzési politikák betöltése."""
        return {
            DataCategory.PERSONAL: timedelta(days=30),
            DataCategory.SENSITIVE: timedelta(days=7),
            DataCategory.TECHNICAL: timedelta(days=90),
            DataCategory.ANALYTICAL: timedelta(days=365),
            DataCategory.MARKETING: timedelta(days=730)
        }
    
    def _load_legal_bases(self) -> Dict[str, str]:
        """Jogi alapok betöltése."""
        return {
            "consent": "Felhasználói hozzájárulás",
            "contract": "Szerződés teljesítése",
            "legitimate_interest": "Jogos érdek",
            "legal_obligation": "Jogi kötelezettség",
            "vital_interest": "Életfontosságú érdek",
            "public_task": "Közkötelezettség"
        }
    
    async def check_user_consent(
        self, 
        user_id: str, 
        consent_type: ConsentType,
        data_category: DataCategory
    ) -> bool:
        """
        Felhasználói hozzájárulás ellenőrzése.
        
        Args:
            user_id: Felhasználó azonosító
            consent_type: Hozzájárulás típusa
            data_category: Adatkategória
            
        Returns:
            True ha van érvényes hozzájárulás, False ha nincs
        """
        try:
            if self.supabase:
                # Supabase-ból ellenőrzés
                response = await self.supabase.table('user_consents').select('*').eq(
                    'user_id', user_id
                ).eq('consent_type', consent_type.value).eq(
                    'data_category', data_category.value
                ).eq('granted', True).execute()
                
                if response.data:
                    consent = response.data[0]
                    # Ellenőrizzük, hogy nem járt-e le
                    if consent.get('expires_at'):
                        expires_at = datetime.fromisoformat(consent['expires_at'])
                        if datetime.now() > expires_at:
                            return False
                    
                    # Ellenőrizzük, hogy nem vonották-e vissza
                    if consent.get('revoked_at'):
                        return False
                    
                    return True
            
            # Fallback: alapértelmezett hozzájárulás szükséges működéshez
            if consent_type == ConsentType.NECESSARY:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Consent check error: {e}")
            return False
    
    async def record_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        data_category: DataCategory,
        granted: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Felhasználói hozzájárulás rögzítése.
        
        Args:
            user_id: Felhasználó azonosító
            consent_type: Hozzájárulás típusa
            data_category: Adatkategória
            granted: Hozzájárulás adott-e
            ip_address: IP cím
            user_agent: User agent
            
        Returns:
            True ha sikeres, False ha nem
        """
        try:
            consent = UserConsent(
                user_id=user_id,
                consent_type=consent_type,
                data_category=data_category,
                granted=granted,
                granted_at=datetime.now(),
                expires_at=self._calculate_expiry(consent_type),
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            if self.supabase:
                await self.supabase.table('user_consents').insert(
                    asdict(consent)
                ).execute()
            
            # Audit log
            await self._log_gdpr_event(
                "consent_recorded",
                user_id,
                data_category.value,
                {
                    "consent_type": consent_type.value,
                    "granted": granted,
                    "ip_address": ip_address
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Consent recording error: {e}")
            return False
    
    def _calculate_expiry(self, consent_type: ConsentType) -> Optional[datetime]:
        """Hozzájárulás lejárati időpontjának kiszámítása."""
        expiry_periods = {
            ConsentType.NECESSARY: None,  # Nem jár le
            ConsentType.FUNCTIONAL: timedelta(days=365),
            ConsentType.ANALYTICAL: timedelta(days=180),
            ConsentType.MARKETING: timedelta(days=90),
            ConsentType.THIRD_PARTY: timedelta(days=30)
        }
        
        period = expiry_periods.get(consent_type)
        if period:
            return datetime.now() + period
        
        return None
    
    async def revoke_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        data_category: DataCategory
    ) -> bool:
        """
        Felhasználói hozzájárulás visszavonása.
        
        Args:
            user_id: Felhasználó azonosító
            consent_type: Hozzájárulás típusa
            data_category: Adatkategória
            
        Returns:
            True ha sikeres, False ha nem
        """
        try:
            if self.supabase:
                await self.supabase.table('user_consents').update({
                    'revoked_at': datetime.now().isoformat()
                }).eq('user_id', user_id).eq(
                    'consent_type', consent_type.value
                ).eq('data_category', data_category.value).execute()
            
            # Audit log
            await self._log_gdpr_event(
                "consent_revoked",
                user_id,
                data_category.value,
                {"consent_type": consent_type.value}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Consent revocation error: {e}")
            return False
    
    async def delete_user_data(self, user_id: str) -> bool:
        """
        Felhasználói adatok törlése (Right to be forgotten).
        
        Args:
            user_id: Felhasználó azonosító
            
        Returns:
            True ha sikeres, False ha nem
        """
        try:
            # Anonymize instead of delete for audit purposes
            if self.supabase:
                # Anonymize user data
                await self.supabase.table('users').update({
                    'anonymized': True,
                    'anonymized_at': datetime.now().isoformat(),
                    'email': f"deleted_{hashlib.md5(user_id.encode()).hexdigest()}@deleted.com",
                    'name': "Deleted User"
                }).eq('id', user_id).execute()
                
                # Anonymize chat sessions
                await self.supabase.table('chat_sessions').update({
                    'anonymized': True,
                    'anonymized_at': datetime.now().isoformat()
                }).eq('user_id', user_id).execute()
                
                # Anonymize orders
                await self.supabase.table('orders').update({
                    'anonymized': True,
                    'anonymized_at': datetime.now().isoformat()
                }).eq('user_id', user_id).execute()
            
            # Audit log
            await self._log_gdpr_event(
                "data_deletion_requested",
                user_id,
                "all",
                {"deletion_type": "right_to_be_forgotten"}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Data deletion error: {e}")
            return False
    
    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Felhasználói adatok exportálása (Data portability).
        
        Args:
            user_id: Felhasználó azonosító
            
        Returns:
            Exportált adatok
        """
        try:
            export_data = {
                "user_id": user_id,
                "exported_at": datetime.now().isoformat(),
                "data": {}
            }
            
            if self.supabase:
                # Export user profile
                user_response = await self.supabase.table('users').select('*').eq(
                    'id', user_id
                ).execute()
                
                if user_response.data:
                    export_data["data"]["profile"] = user_response.data[0]
                
                # Export chat sessions
                chat_response = await self.supabase.table('chat_sessions').select('*').eq(
                    'user_id', user_id
                ).execute()
                
                if chat_response.data:
                    export_data["data"]["chat_sessions"] = chat_response.data
                
                # Export orders
                orders_response = await self.supabase.table('orders').select('*').eq(
                    'user_id', user_id
                ).execute()
                
                if orders_response.data:
                    export_data["data"]["orders"] = orders_response.data
                
                # Export consents
                consents_response = await self.supabase.table('user_consents').select('*').eq(
                    'user_id', user_id
                ).execute()
                
                if consents_response.data:
                    export_data["data"]["consents"] = consents_response.data
            
            # Audit log
            await self._log_gdpr_event(
                "data_export_requested",
                user_id,
                "all",
                {"export_format": "json"}
            )
            
            return export_data
            
        except Exception as e:
            logger.error(f"Data export error: {e}")
            return {"error": str(e)}
    
    async def record_data_processing(
        self,
        user_id: str,
        data_category: DataCategory,
        purpose: str,
        legal_basis: str,
        data_subjects: List[str],
        data_recipients: List[str] = None,
        third_country_transfers: List[str] = None,
        safeguards: List[str] = None
    ) -> bool:
        """
        Adatfeldolgozási rekord létrehozása.
        
        Args:
            user_id: Felhasználó azonosító
            data_category: Adatkategória
            purpose: Feldolgozás célja
            legal_basis: Jogi alap
            data_subjects: Feldolgozott adatok
            data_recipients: Adatcímzettek
            third_country_transfers: Harmadik országba történő átadások
            safeguards: Védelmi intézkedések
            
        Returns:
            True ha sikeres, False ha nem
        """
        try:
            processing_record = DataProcessingRecord(
                processing_id=f"proc_{hashlib.md5(f'{user_id}_{datetime.now()}'.encode()).hexdigest()}",
                user_id=user_id,
                data_category=data_category,
                purpose=purpose,
                legal_basis=legal_basis,
                processed_at=datetime.now(),
                retention_period=self.retention_policies[data_category],
                data_subjects=data_subjects,
                data_recipients=data_recipients or [],
                third_country_transfers=third_country_transfers or [],
                safeguards=safeguards or []
            )
            
            if self.supabase:
                await self.supabase.table('data_processing_records').insert(
                    asdict(processing_record)
                ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Data processing record error: {e}")
            return False
    
    async def _log_gdpr_event(
        self,
        event_type: str,
        user_id: str,
        data_type: str,
        details: Dict[str, Any]
    ) -> None:
        """
        GDPR esemény naplózása.
        
        Args:
            event_type: Esemény típusa
            user_id: Felhasználó azonosító
            data_type: Adattípus
            details: További részletek
        """
        try:
            event_data = {
                "event_type": event_type,
                "user_id": user_id,
                "data_type": data_type,
                "timestamp": datetime.now().isoformat(),
                "details": details
            }
            
            if self.supabase:
                await self.supabase.table('gdpr_audit_log').insert(event_data).execute()
            
            # Console log is
            logger.info(f"GDPR Event: {event_type} for user {user_id}")
            
        except Exception as e:
            logger.error(f"GDPR event logging error: {e}")
    
    async def cleanup_expired_data(self) -> Dict[str, int]:
        """
        Lejárt adatok tisztítása.
        
        Returns:
            Tisztított adatok száma kategóriánként
        """
        try:
            cleanup_stats = {}
            
            for category, retention_period in self.retention_policies.items():
                if not retention_period:
                    continue
                
                cutoff_date = datetime.now() - retention_period
                
                if self.supabase:
                    # Cleanup expired data
                    response = await self.supabase.table('data_processing_records').delete().lt(
                        'processed_at', cutoff_date.isoformat()
                    ).eq('data_category', category.value).execute()
                    
                    cleanup_stats[category.value] = len(response.data) if response.data else 0
            
            # Audit log
            await self._log_gdpr_event(
                "data_cleanup",
                "system",
                "all",
                cleanup_stats
            )
            
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Data cleanup error: {e}")
            return {}
    
    def get_privacy_policy_url(self) -> str:
        """Adatvédelmi nyilatkozat URL-je."""
        return os.getenv("PRIVACY_POLICY_URL", "/privacy-policy")
    
    def get_cookie_policy_url(self) -> str:
        """Cookie policy URL-je."""
        return os.getenv("COOKIE_POLICY_URL", "/cookie-policy")
    
    def get_consent_management_url(self) -> str:
        """Hozzájárulás kezelés URL-je."""
        return os.getenv("CONSENT_MANAGEMENT_URL", "/consent-management")


# Singleton instance
_gdpr_compliance: Optional[GDPRComplianceLayer] = None


def get_gdpr_compliance() -> GDPRComplianceLayer:
    """
    GDPR compliance singleton instance.
    
    Returns:
        GDPRComplianceLayer instance
    """
    global _gdpr_compliance
    if _gdpr_compliance is None:
        # Check if we're in test mode
        if os.getenv("ENVIRONMENT") == "development" and os.getenv("MOCK_GDPR_CONSENT") == "true":
            # Use mock GDPR compliance for testing
            class MockGDPRCompliance(GDPRComplianceLayer):
                async def check_user_consent(
                    self, 
                    user_id: str, 
                    consent_type: ConsentType,
                    data_category: DataCategory
                ) -> bool:
                    """Mock consent - minden hozzájárulást megadunk teszteléshez."""
                    print(f"🔐 Mock GDPR Consent: {consent_type.value} - {data_category.value} -> ✅ GRANTED")
                    return True
            
            _gdpr_compliance = MockGDPRCompliance()
        else:
            _gdpr_compliance = GDPRComplianceLayer()
    return _gdpr_compliance 