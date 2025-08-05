"""
Order Status Agent Tools - Rendelés kezelés eszközök

Ez a modul tartalmazza az Order Status Agent által használt 
eszközöket és segédfüggvényeket.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import re
from enum import Enum

from src.models.order import Order, OrderStatus, OrderItem
from src.config.audit_logging import AuditLogger


class OrderQueryType(Enum):
    """Rendelés lekérdezés típusok"""
    BY_ID = "by_id"
    BY_USER = "by_user"
    BY_TRACKING = "by_tracking"
    BY_DATE_RANGE = "by_date_range"
    BY_STATUS = "by_status"


def extract_order_id_from_text(text: str) -> Optional[str]:
    """Rendelés azonosító kinyerése szövegből"""
    # Különböző formátumok támogatása
    patterns = [
        r'#(\d{6,10})',  # #123456
        r'RENDELÉS[:\s]*(\d{6,10})',  # RENDELÉS: 123456
        r'ORDER[:\s]*(\d{6,10})',  # ORDER: 123456
        r'(\d{6,10})',  # Csak számok
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def extract_tracking_number_from_text(text: str) -> Optional[str]:
    """Szállítási szám kinyerése szövegből"""
    # Különböző szállítási szám formátumok
    patterns = [
        r'TRACKING[:\s]*([A-Z0-9]{10,20})',  # TRACKING: ABC123456789
        r'KÖVETÉS[:\s]*([A-Z0-9]{10,20})',  # KÖVETÉS: ABC123456789
        r'([A-Z]{2,4}\d{8,12})',  # GLS123456789, DPD123456789
        r'([A-Z0-9]{10,20})',  # Általános formátum
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def classify_order_query(message: str) -> Dict[str, Any]:
    """Rendelés lekérdezés osztályozása"""
    message_lower = message.lower()
    
    # Kulcsszavak alapján osztályozás
    if any(word in message_lower for word in ['rendelés', 'order', 'megrendelés']):
        if any(word in message_lower for word in ['státusz', 'status', 'állapot']):
            return {
                'type': OrderQueryType.BY_STATUS,
                'confidence': 0.9,
                'keywords': ['rendelés', 'státusz']
            }
        elif any(word in message_lower for word in ['követés', 'tracking', 'szállítás']):
            return {
                'type': OrderQueryType.BY_TRACKING,
                'confidence': 0.8,
                'keywords': ['követés', 'szállítás']
            }
        else:
            return {
                'type': OrderQueryType.BY_USER,
                'confidence': 0.7,
                'keywords': ['rendelés']
            }
    
    # Szállítási szám keresés
    tracking_number = extract_tracking_number_from_text(message)
    if tracking_number:
        return {
            'type': OrderQueryType.BY_TRACKING,
            'confidence': 0.9,
            'tracking_number': tracking_number,
            'keywords': ['követés', 'szállítás']
        }
    
    # Rendelés azonosító keresés
    order_id = extract_order_id_from_text(message)
    if order_id:
        return {
            'type': OrderQueryType.BY_ID,
            'confidence': 0.9,
            'order_id': order_id,
            'keywords': ['rendelés', 'azonosító']
        }
    
    return {
        'type': OrderQueryType.BY_USER,
        'confidence': 0.5,
        'keywords': ['általános']
    }


def format_order_status(order: Order) -> str:
    """Rendelés státusz formázása felhasználóbarát módon"""
    status_messages = {
        OrderStatus.PENDING: "Rendelés feldolgozás alatt",
        OrderStatus.CONFIRMED: "Rendelés megerősítve",
        OrderStatus.PROCESSING: "Rendelés előkészítés alatt",
        OrderStatus.SHIPPED: "Rendelés szállítás alatt",
        OrderStatus.DELIVERED: "Rendelés kézbesítve",
        OrderStatus.CANCELLED: "Rendelés törölve",
        OrderStatus.REFUNDED: "Rendelés visszatérítve"
    }
    
    return status_messages.get(order.status, "Ismeretlen státusz")


def format_tracking_info(tracking_data: Dict[str, Any]) -> str:
    """Szállítási információk formázása"""
    if not tracking_data:
        return "Szállítási információk nem elérhetők"
    
    status = tracking_data.get('status', 'Ismeretlen')
    location = tracking_data.get('location', '')
    estimated_delivery = tracking_data.get('estimated_delivery', '')
    
    message = f"SZállítási státusz: {status}"
    
    if location:
        message += f"\nJelenlegi hely: {location}"
    
    if estimated_delivery:
        message += f"\nVárható kézbesítés: {estimated_delivery}"
    
    return message


def generate_next_steps(order: Order) -> List[str]:
    """Következő lépések generálása rendelés státusz alapján"""
    steps = []
    
    if order.status == OrderStatus.PENDING:
        steps.extend([
            "Rendelés feldolgozása 1-2 munkanap alatt",
            "Email értesítés a megerősítésről"
        ])
    
    elif order.status == OrderStatus.CONFIRMED:
        steps.extend([
            "Rendelés előkészítése raktárban",
            "Szállítási címke generálása"
        ])
    
    elif order.status == OrderStatus.PROCESSING:
        steps.extend([
            "Termékek csomagolása",
            "Szállítási információk frissítése"
        ])
    
    elif order.status == OrderStatus.SHIPPED:
        steps.extend([
            "Szállítási követés aktiválása",
            "Kézbesítési értesítés"
        ])
    
    elif order.status == OrderStatus.DELIVERED:
        steps.extend([
            "Rendelés teljesítve",
            "Vélemény írása opcionális"
        ])
    
    return steps


def validate_order_access(user_id: str, order: Order, audit_logger: AuditLogger) -> bool:
    """Rendelés hozzáférés validálása"""
    # Alapvető validáció
    if not user_id or not order:
        audit_logger.log_warning(
            "order_access_validation_failed",
            "Hiányzó user_id vagy order",
            {"user_id": user_id, "order_id": getattr(order, 'id', None)}
        )
        return False
    
    # Felhasználó saját rendelésének ellenőrzése
    if order.user_id != user_id:
        audit_logger.log_warning(
            "order_access_unauthorized",
            "Felhasználó nem férhet hozzá a rendeléshez",
            {"user_id": user_id, "order_id": order.id, "order_user_id": order.user_id}
        )
        return False
    
    return True


def calculate_delivery_estimate(order: Order) -> Optional[str]:
    """Kézbesítési idő becslése"""
    if not order.created_at:
        return None
    
    created_date = datetime.fromisoformat(order.created_at.replace('Z', '+00:00'))
    
    # Alapvető kézbesítési idő (3-5 munkanap)
    delivery_days = 4
    delivery_date = created_date + timedelta(days=delivery_days)
    
    # Hétvége kezelése
    while delivery_date.weekday() >= 5:  # Szombat = 5, Vasárnap = 6
        delivery_date += timedelta(days=1)
    
    return delivery_date.strftime("%Y-%m-%d")


def format_order_summary(order: Order) -> str:
    """Rendelés összefoglaló formázása"""
    summary = f"Rendelés #{order.id}\n"
    summary += f"Státusz: {format_order_status(order)}\n"
    summary += f"Dátum: {order.created_at[:10]}\n"
    
    if order.total_amount:
        summary += f"Összeg: {order.total_amount} Ft\n"
    
    if order.tracking_number:
        summary += f"SZállítási szám: {order.tracking_number}\n"
    
    return summary 