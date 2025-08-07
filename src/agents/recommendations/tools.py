"""
Recommendation Agent Tools - Termékajánlás és trend elemzés eszközök
================================================================

Ez a modul tartalmazza az Recommendation Agent által használt
segédfüggvényeket és utility osztályokat.
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re
from enum import Enum

from src.models.product import Product, ProductCategory
from src.config.audit_logging import AuditLogger

class RecommendationType(Enum):
    """Ajánlás típusok"""
    SIMILAR_PRODUCTS = "similar_products"
    PERSONALIZED = "personalized"
    TREND_BASED = "trend_based"
    CATEGORY_BASED = "category_based"
    PRICE_BASED = "price_based"

class QueryIntent(Enum):
    """Lekérdezés szándék típusok"""
    RECOMMEND_PRODUCTS = "recommend_products"
    FIND_SIMILAR = "find_similar"
    ANALYZE_TRENDS = "analyze_trends"
    GET_PREFERENCES = "get_preferences"
    EXPLORE_CATEGORY = "explore_category"

def extract_product_id_from_text(text: str) -> Optional[str]:
    """
    Termék azonosító kinyerése szövegből
    
    Args:
        text: Bemeneti szöveg
        
    Returns:
        Termék azonosító vagy None
    """
    # Pattern: termék, product, azonosító, ID
    patterns = [
        r'termék[:\s]*([a-zA-Z0-9_-]+)',
        r'product[:\s]*([a-zA-Z0-9_-]+)',
        r'azonosító[:\s]*([a-zA-Z0-9_-]+)',
        r'id[:\s]*([a-zA-Z0-9_-]+)',
        r'([a-zA-Z0-9_-]{8,})'  # Általános ID pattern
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def extract_category_from_text(text: str) -> Optional[str]:
    """
    Kategória kinyerése szövegből
    
    Args:
        text: Bemeneti szöveg
        
    Returns:
        Kategória vagy None
    """
    # Magyar kategóriák
    categories = {
        'elektronika': 'electronics',
        'könyvek': 'books',
        'ruházat': 'clothing',
        'cipők': 'shoes',
        'kiegészítők': 'accessories',
        'otthon': 'home',
        'sport': 'sports',
        'játékok': 'toys',
        'szépségápolás': 'beauty',
        'autó': 'automotive'
    }
    
    text_lower = text.lower()
    for hu_category, en_category in categories.items():
        if hu_category in text_lower:
            return en_category
    
    return None

def classify_recommendation_query(message: str) -> Dict[str, Any]:
    """
    Ajánlás lekérdezés klasszifikálása
    
    Args:
        message: Felhasználói üzenet
        
    Returns:
        Klasszifikációs eredmény
    """
    message_lower = message.lower()
    
    # Kulcsszavak azonosítása
    keywords = {
        'ajánl': QueryIntent.RECOMMEND_PRODUCTS,
        'ajánlat': QueryIntent.RECOMMEND_PRODUCTS,
        'hasonló': QueryIntent.FIND_SIMILAR,
        'hasonlít': QueryIntent.FIND_SIMILAR,
        'trend': QueryIntent.ANALYZE_TRENDS,
        'népszerű': QueryIntent.ANALYZE_TRENDS,
        'preferencia': QueryIntent.GET_PREFERENCES,
        'kedvenc': QueryIntent.GET_PREFERENCES,
        'kategória': QueryIntent.EXPLORE_CATEGORY,
        'típus': QueryIntent.EXPLORE_CATEGORY
    }
    
    detected_intent = None
    confidence = 0.0
    
    for keyword, intent in keywords.items():
        if keyword in message_lower:
            detected_intent = intent
            confidence = 0.8
            break
    
    # Alapértelmezett intent
    if not detected_intent:
        detected_intent = QueryIntent.RECOMMEND_PRODUCTS
        confidence = 0.5
    
    return {
        'intent': detected_intent,
        'confidence': confidence,
        'product_id': extract_product_id_from_text(message),
        'category': extract_category_from_text(message),
        'keywords': [k for k in keywords.keys() if k in message_lower]
    }

def format_recommendations(recommendations: List[Product]) -> str:
    """
    Ajánlatok formázása felhasználóbarát szöveggé
    
    Args:
        recommendations: Ajánlott termékek listája
        
    Returns:
        Formázott szöveg
    """
    if not recommendations:
        return "Sajnos nem találtam megfelelő ajánlatokat."
    
    formatted = "Íme az ajánlott termékek:\n\n"
    
    for i, product in enumerate(recommendations[:5], 1):  # Max 5 termék
        formatted += f"{i}. **{product.name}**\n"
        formatted += f"   Ár: {product.price:,} Ft\n"
        formatted += f"   Kategória: {product.category.value}\n"
        if product.description:
            formatted += f"   Leírás: {product.description[:100]}...\n"
        formatted += "\n"
    
    return formatted

def format_trend_analysis(trends: Dict[str, Any]) -> str:
    """
    Trend elemzés formázása
    
    Args:
        trends: Trend információk
        
    Returns:
        Formázott trend jelentés
    """
    if not trends:
        return "Sajnos nem áll rendelkezésre trend információ."
    
    formatted = f"**Trend elemzés - {trends.get('category', 'Ismeretlen kategória')}**\n\n"
    
    if 'trending_products' in trends:
        formatted += f"🔥 **Népszerű termékek:** {', '.join(trends['trending_products'][:3])}\n"
    
    if 'popular_brands' in trends:
        formatted += f"🏆 **Népszerű márkák:** {', '.join(trends['popular_brands'])}\n"
    
    if 'price_trend' in trends:
        trend_emoji = "📈" if trends['price_trend'] == 'increasing' else "📉"
        formatted += f"{trend_emoji} **Ár trend:** {trends['price_trend']}\n"
    
    if 'demand_level' in trends:
        demand_emoji = "🔥" if trends['demand_level'] == 'high' else "📊"
        formatted += f"{demand_emoji} **Kereslet:** {trends['demand_level']}\n"
    
    if 'seasonal_factors' in trends:
        formatted += f"🌍 **Szezonalitás:** {', '.join(trends['seasonal_factors'])}\n"
    
    return formatted

def generate_recommendation_reasoning(
    user_preferences: Dict[str, Any],
    recommendations: List[Product],
    query_intent: QueryIntent
) -> str:
    """
    Ajánlás indoklásának generálása
    
    Args:
        user_preferences: Felhasználói preferenciák
        recommendations: Ajánlott termékek
        query_intent: Lekérdezés szándék
        
    Returns:
        Indoklás szövege
    """
    reasoning = "Az ajánlásokat a következők alapján készítettem:\n\n"
    
    if query_intent == QueryIntent.PERSONALIZED:
        if user_preferences.get('categories'):
            reasoning += f"• Kedvenc kategóriáid: {', '.join(user_preferences['categories'])}\n"
        
        if user_preferences.get('price_range'):
            price_range = user_preferences['price_range']
            reasoning += f"• Árkeret: {price_range['min']:,} - {price_range['max']:,} Ft\n"
        
        if user_preferences.get('brands'):
            reasoning += f"• Kedvenc márkáid: {', '.join(user_preferences['brands'])}\n"
    
    elif query_intent == QueryIntent.FIND_SIMILAR:
        reasoning += "• Hasonló termékek keresése a megadott termék alapján\n"
        reasoning += "• Kategória és ár alapú hasonlóság\n"
    
    elif query_intent == QueryIntent.TREND_BASED:
        reasoning += "• Aktuális trendek és népszerűség alapján\n"
        reasoning += "• Piaci kereslet és szezonalitás figyelembevételével\n"
    
    reasoning += f"\nÖsszesen {len(recommendations)} terméket ajánlok."
    
    return reasoning

def validate_user_access(user_id: str, audit_logger: AuditLogger) -> bool:
    """
    Felhasználói hozzáférés validálása
    
    Args:
        user_id: Felhasználó azonosítója
        audit_logger: Audit logger
        
    Returns:
        Hozzáférés engedélyezve
    """
    # TODO: Implement real user validation
    # For now, allow all users
    return True

def calculate_recommendation_confidence(
    user_preferences: Dict[str, Any],
    recommendations: List[Product],
    query_intent: QueryIntent
) -> float:
    """
    Ajánlás bizonyosságának kiszámítása
    
    Args:
        user_preferences: Felhasználói preferenciák
        recommendations: Ajánlott termékek
        query_intent: Lekérdezés szándék
        
    Returns:
        Bizonyosság (0.0 - 1.0)
    """
    base_confidence = 0.7
    
    # Növelés preferenciák alapján
    if user_preferences.get('categories'):
        base_confidence += 0.1
    
    if user_preferences.get('price_range'):
        base_confidence += 0.1
    
    if user_preferences.get('brands'):
        base_confidence += 0.1
    
    # Növelés ajánlatok számához
    if len(recommendations) >= 3:
        base_confidence += 0.1
    
    # Intent alapú módosítás
    if query_intent == QueryIntent.PERSONALIZED:
        base_confidence += 0.1
    elif query_intent == QueryIntent.FIND_SIMILAR:
        base_confidence += 0.05
    
    return min(base_confidence, 1.0)

def filter_recommendations_by_preferences(
    recommendations: List[Product],
    preferences: Dict[str, Any]
) -> List[Product]:
    """
    Ajánlatok szűrése preferenciák alapján
    
    Args:
        recommendations: Eredeti ajánlatok
        preferences: Felhasználói preferenciák
        
    Returns:
        Szűrt ajánlatok
    """
    if not preferences:
        return recommendations
    
    filtered = []
    
    for product in recommendations:
        include = True
        
        # Kategória szűrés
        if preferences.get('categories') and product.category.value not in preferences['categories']:
            include = False
        
        # Ár szűrés
        if preferences.get('price_range'):
            price_range = preferences['price_range']
            if not (price_range['min'] <= product.price <= price_range['max']):
                include = False
        
        # Márka szűrés
        if preferences.get('brands') and hasattr(product, 'brand'):
            if product.brand not in preferences['brands']:
                include = False
        
        if include:
            filtered.append(product)
    
    return filtered or recommendations  # Ha üres, adjuk vissza az eredetit

def create_recommendation_summary(
    recommendations: List[Product],
    reasoning: str,
    confidence: float
) -> str:
    """
    Ajánlás összefoglaló létrehozása
    
    Args:
        recommendations: Ajánlott termékek
        reasoning: Indoklás
        confidence: Bizonyosság
        
    Returns:
        Összefoglaló szöveg
    """
    summary = f"🎯 **{len(recommendations)} termék ajánlva**\n\n"
    summary += f"📊 **Bizonyosság:** {confidence:.1%}\n\n"
    summary += reasoning
    
    if recommendations:
        total_value = sum(p.price for p in recommendations)
        avg_price = total_value / len(recommendations)
        summary += f"\n\n💰 **Átlagár:** {avg_price:,.0f} Ft"
    
    return summary 