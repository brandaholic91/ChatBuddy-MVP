"""
General Agent - Pydantic AI Tool Implementation for LangGraph.

This module implements the general agent as a Pydantic AI tool
that can be integrated into the LangGraph workflow.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from ...models.agent import AgentType


@dataclass
class GeneralDependencies:
    """General agent függőségei."""
    user_context: Dict[str, Any]
    supabase_client: Optional[Any] = None
    webshop_api: Optional[Any] = None
    security_context: Optional[Any] = None
    audit_logger: Optional[Any] = None


class GeneralResponse(BaseModel):
    """General agent válasz struktúra."""
    response_text: str = Field(description="Agent válasza")
    confidence: float = Field(description="Bizonyosság", ge=0.0, le=1.0)
    suggested_actions: Optional[List[str]] = Field(description="Javasolt műveletek", default=None)
    help_topics: Optional[List[str]] = Field(description="Segítség témák", default=None)
    metadata: Dict[str, Any] = Field(description="Metaadatok", default_factory=dict)


# Global agent instance
_general_agent = None

def create_general_agent() -> Agent:
    """
    General agent létrehozása Pydantic AI-val.
    
    Returns:
        General agent
    """
    global _general_agent
    
    if _general_agent is not None:
        return _general_agent
    
    agent = Agent(
        'openai:gpt-4o',
        deps_type=GeneralDependencies,
        output_type=GeneralResponse,
        system_prompt=(
            "Te egy általános segítő ügynök vagy a ChatBuddy webshop chatbot-ban. "
            "Feladatod a felhasználók segítése általános kérdésekben és irányításuk "
            "a megfelelő szakértő ügynökök felé. Válaszolj magyarul, barátságosan és "
            "segítőkészen. Ha nem tudod megválaszolni a kérdést, javasold a megfelelő "
            "szakértő ügynököt. Mindig tartsd szem előtt a biztonsági protokollokat "
            "és a GDPR megfelelőséget."
        )
    )
    
    @agent.tool
    async def get_help_topics(
        ctx: RunContext[GeneralDependencies]
    ) -> List[str]:
        """
        Elérhető segítség témák lekérése.
        
        Returns:
            Segítség témák listája
        """
        try:
            # Mock implementáció fejlesztési célokra
            # TODO: Implementálni valós segítség témák lekérést
            
            help_topics = [
                "Termékek keresése és vásárlása",
                "Rendelések követése",
                "Szállítási információk",
                "Visszaküldés és garancia",
                "Fiók kezelése",
                "Fizetési módok",
                "Kedvezmények és kuponok",
                "Technikai támogatás",
                "Gyakran ismételt kérdések",
                "Kapcsolatfelvétel"
            ]
            
            return help_topics
            
        except Exception as e:
            # TODO: Implementálni error handling-et
            raise Exception(f"Hiba a segítség témák lekérésekor: {str(e)}")
    
    @agent.tool
    async def get_contact_info(
        ctx: RunContext[GeneralDependencies]
    ) -> Dict[str, Any]:
        """
        Kapcsolatfelvételi információk lekérése.
        
        Returns:
            Kapcsolatfelvételi információk
        """
        try:
            # Mock implementáció fejlesztési célokra
            # TODO: Implementálni valós kapcsolatfelvételi információk lekérést
            
            contact_info = {
                "customer_service": {
                    "phone": "+36 1 234 5678",
                    "email": "ugyfelszolgalat@chatbuddy.hu",
                    "hours": "Hétfő-Péntek: 9:00-18:00"
                },
                "technical_support": {
                    "phone": "+36 1 234 5679",
                    "email": "tamogatas@chatbuddy.hu",
                    "hours": "Hétfő-Vasárnap: 0:00-24:00"
                },
                "sales": {
                    "phone": "+36 1 234 5680",
                    "email": "eladas@chatbuddy.hu",
                    "hours": "Hétfő-Péntek: 8:00-20:00"
                },
                "address": {
                    "street": "ChatBuddy utca 1.",
                    "city": "Budapest",
                    "postal_code": "1000",
                    "country": "Magyarország"
                }
            }
            
            return contact_info
            
        except Exception as e:
            # TODO: Implementálni error handling-et
            raise Exception(f"Hiba a kapcsolatfelvételi információk lekérésekor: {str(e)}")
    
    @agent.tool
    async def get_faq_answers(
        ctx: RunContext[GeneralDependencies],
        question: str
    ) -> Dict[str, Any]:
        """
        Gyakran ismételt kérdések válaszainak lekérése.
        
        Args:
            question: Felhasználói kérdés
            
        Returns:
            FAQ válasz
        """
        try:
            # Mock implementáció fejlesztési célokra
            # TODO: Implementálni valós FAQ válaszok lekérést
            
            # Simple keyword matching for demo
            question_lower = question.lower()
            
            faq_answers = {
                "szállítás": {
                    "question": "Mennyi idő alatt érkezik meg a rendelésem?",
                    "answer": "A szállítási idő 1-3 munkanap, attól függően, hogy melyik szállítási módot választja.",
                    "category": "szállítás"
                },
                "visszaküldés": {
                    "question": "Hogyan küldhetem vissza a terméket?",
                    "answer": "A visszaküldés 14 napon belül ingyenes, ha a termék eredeti állapotában van.",
                    "category": "visszaküldés"
                },
                "fizetés": {
                    "question": "Milyen fizetési módokkal fizethetem ki a rendelésem?",
                    "answer": "Elfogadunk bankkártyát, PayPal-t, és utánvétet is.",
                    "category": "fizetés"
                },
                "garancia": {
                    "question": "Milyen garanciát kapok a termékekre?",
                    "answer": "Minden termékre 2 év garanciát adunk, ami a gyártói garancia felett jár.",
                    "category": "garancia"
                }
            }
            
            # Find matching FAQ
            for keyword, faq in faq_answers.items():
                if keyword in question_lower:
                    return faq
            
            # Default response if no match found
            return {
                "question": question,
                "answer": "Sajnos nem találtam megfelelő választ erre a kérdésre. Kérjük, forduljon ügyfélszolgálatunkhoz.",
                "category": "általános"
            }
            
        except Exception as e:
            # TODO: Implementálni error handling-et
            raise Exception(f"Hiba a FAQ válaszok lekérésekor: {str(e)}")
    
    @agent.tool
    async def get_website_info(
        ctx: RunContext[GeneralDependencies]
    ) -> Dict[str, Any]:
        """
        Weboldal információk lekérése.
        
        Returns:
            Weboldal információk
        """
        try:
            # Mock implementáció fejlesztési célokra
            # TODO: Implementálni valós weboldal információk lekérést
            
            website_info = {
                "name": "ChatBuddy Webshop",
                "description": "Magyarország vezető elektronikai webshopja",
                "founded": "2020",
                "employees": "150+",
                "customers": "100,000+",
                "products": "50,000+",
                "categories": [
                    "Telefonok",
                    "Tabletek",
                    "Laptopok",
                    "Asztali számítógépek",
                    "Kiegészítők",
                    "Otthoni elektronika"
                ],
                "features": [
                    "Ingyenes szállítás 50.000 Ft felett",
                    "30 napos visszaküldési garancia",
                    "2 év gyártói garancia",
                    "24/7 ügyfélszolgálat",
                    "Biztonságos fizetés",
                    "Gyors szállítás"
                ]
            }
            
            return website_info
            
        except Exception as e:
            # TODO: Implementálni error handling-et
            raise Exception(f"Hiba a weboldal információk lekérésekor: {str(e)}")
    
    @agent.tool
    async def get_user_guide(
        ctx: RunContext[GeneralDependencies],
        topic: str
    ) -> Dict[str, Any]:
        """
        Felhasználói útmutató lekérése.
        
        Args:
            topic: Téma
            
        Returns:
            Felhasználói útmutató
        """
        try:
            # Mock implementáció fejlesztési célokra
            # TODO: Implementálni valós felhasználói útmutató lekérést
            
            user_guides = {
                "regisztráció": {
                    "title": "Fiók létrehozása",
                    "steps": [
                        "Kattintson a 'Regisztráció' gombra",
                        "Töltse ki az adatokat",
                        "Erősítse meg az email címét",
                        "Jelentkezzen be"
                    ],
                    "tips": [
                        "Használjon erős jelszót",
                        "Mentse el a bejelentkezési adatait"
                    ]
                },
                "rendelés": {
                    "title": "Rendelés leadása",
                    "steps": [
                        "Válassza ki a terméket",
                        "Adja hozzá a kosárhoz",
                        "Jelentkezzen be",
                        "Adja meg a szállítási adatokat",
                        "Válassza ki a fizetési módot",
                        "Erősítse meg a rendelést"
                    ],
                    "tips": [
                        "Ellenőrizze a szállítási adatokat",
                        "Használjon kedvezménykódot"
                    ]
                },
                "visszaküldés": {
                    "title": "Termék visszaküldése",
                    "steps": [
                        "Jelentkezzen be a fiókjába",
                        "Keresse meg a rendelést",
                        "Kattintson a 'Visszaküldés' gombra",
                        "Válassza ki a visszaküldés okát",
                        "Nyomtassa ki a szállítási címkét",
                        "Küldje el a csomagot"
                    ],
                    "tips": [
                        "Tartsa meg az eredeti csomagolást",
                        "Küldje el 14 napon belül"
                    ]
                }
            }
            
            return user_guides.get(topic, {
                "title": "Útmutató nem található",
                "steps": [],
                "tips": []
            })
            
        except Exception as e:
            # TODO: Implementálni error handling-et
            raise Exception(f"Hiba a felhasználói útmutató lekérésekor: {str(e)}")
    
    # Store globally and return
    _general_agent = agent
    return agent


# Export tool functions for testing
__all__ = [
    'create_general_agent',
    'call_general_agent',
    'GeneralDependencies',
    'GeneralResponse',
    'get_help_topics',
    'get_contact_info',
    'get_faq_answers',
    'get_website_info',
    'get_user_guide'
]


async def call_general_agent(
    message: str,
    dependencies: GeneralDependencies
) -> GeneralResponse:
    """
    General agent hívása.
    
    Args:
        message: Felhasználói üzenet
        dependencies: Agent függőségei
        
    Returns:
        Agent válasza
    """
    try:
        # Agent létrehozása
        agent = create_general_agent()
        
        # Agent futtatása
        result = await agent.run(message, deps=dependencies)
        
        return result.output
        
    except Exception as e:
        # Error handling
        return GeneralResponse(
            response_text=f"Sajnálom, hiba történt az általános kérdés megválaszolásakor: {str(e)}",
            confidence=0.0,
            metadata={"error": str(e)}
        ) 