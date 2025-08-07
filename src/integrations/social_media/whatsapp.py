"""
WhatsApp Business API Integration.

This module provides the WhatsApp Business API client for sending
messages, handling webhooks, and managing WhatsApp Business features.
"""

import json
from typing import Dict, Any, List, Optional
import httpx
from fastapi import HTTPException

from ...config.logging import get_logger

logger = get_logger(__name__)


class WhatsAppBusinessClient:
    """WhatsApp Business API kliens."""
    
    def __init__(self, access_token: str, phone_number_id: str, verify_token: str):
        """
        WhatsApp Business kliens inicializálása.
        
        Args:
            access_token: WhatsApp Business API Access Token
            phone_number_id: Phone Number ID
            verify_token: Webhook verify token
        """
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.verify_token = verify_token
        self.base_url = "https://graph.facebook.com/v18.0"
        
    async def verify_webhook(self, hub_mode: str, hub_verify_token: str, hub_challenge: str) -> int:
        """
        WhatsApp Business webhook verification.
        
        Args:
            hub_mode: Hub mode
            hub_verify_token: Verify token
            hub_challenge: Challenge string
            
        Returns:
            Challenge response
        """
        if hub_mode == "subscribe" and hub_verify_token == self.verify_token:
            return int(hub_challenge)
        raise HTTPException(status_code=403, detail="Forbidden")
    
    async def send_message(self, payload: Dict[str, Any]) -> bool:
        """
        Üzenet küldése WhatsApp Business API-n keresztül.
        
        Args:
            payload: Üzenet payload
            
        Returns:
            Küldés sikeressége
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/{self.phone_number_id}/messages",
                    params={"access_token": self.access_token},
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info("WhatsApp Business message sent successfully")
                    return True
                else:
                    logger.error(f"WhatsApp Business API error: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending WhatsApp Business message: {e}")
            return False
    
    async def send_text_message(self, recipient_number: str, text: str) -> bool:
        """
        Szöveges üzenet küldése.
        
        Args:
            recipient_number: Címzett telefonszám
            text: Üzenet szövege
            
        Returns:
            Küldés sikeressége
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_number,
            "type": "text",
            "text": {
                "body": text
            }
        }
        return await self.send_message(payload)
    
    async def send_template_message(
        self,
        recipient_number: str,
        template_name: str,
        language_code: str = "hu",
        components: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Template üzenet küldése.
        
        Args:
            recipient_number: Címzett telefonszám
            template_name: Template neve
            language_code: Nyelvi kód
            components: Template komponensek
            
        Returns:
            Küldés sikeressége
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        
        if components:
            payload["template"]["components"] = components
        
        return await self.send_message(payload)
    
    async def send_interactive_message(
        self,
        recipient_number: str,
        body_text: str,
        buttons: List[Dict[str, Any]]
    ) -> bool:
        """
        Interaktív üzenet küldése.
        
        Args:
            recipient_number: Címzett telefonszám
            body_text: Üzenet szövege
            buttons: Gombok
            
        Returns:
            Küldés sikeressége
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": body_text
                },
                "action": {
                    "buttons": buttons
                }
            }
        }
        return await self.send_message(payload)
    
    async def send_list_message(
        self,
        recipient_number: str,
        body_text: str,
        button_text: str,
        sections: List[Dict[str, Any]]
    ) -> bool:
        """
        Lista üzenet küldése.
        
        Args:
            recipient_number: Címzett telefonszám
            body_text: Üzenet szövege
            button_text: Gomb szövege
            sections: Lista szekciók
            
        Returns:
            Küldés sikeressége
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_number,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {
                    "text": body_text
                },
                "action": {
                    "button": button_text,
                    "sections": sections
                }
            }
        }
        return await self.send_message(payload)
    
    async def send_media_message(
        self,
        recipient_number: str,
        media_type: str,
        media_url: str,
        caption: Optional[str] = None
    ) -> bool:
        """
        Média üzenet küldése.
        
        Args:
            recipient_number: Címzett telefonszám
            media_type: Média típus (image/video/document)
            media_url: Média URL
            caption: Felirat (opcionális)
            
        Returns:
            Küldés sikeressége
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_number,
            "type": media_type,
            media_type: {
                "link": media_url
            }
        }
        
        if caption:
            payload[media_type]["caption"] = caption
        
        return await self.send_message(payload)
    
    async def send_abandoned_cart_template(
        self,
        recipient_number: str,
        customer_name: str,
        cart_value: float,
        cart_id: str,
        discount_code: Optional[str] = None
    ) -> bool:
        """
        Kosárelhagyás template üzenet küldése.
        
        Args:
            recipient_number: Címzett telefonszám
            customer_name: Vásárló neve
            cart_value: Kosár értéke
            cart_id: Kosár azonosító
            discount_code: Kedvezmény kód (opcionális)
            
        Returns:
            Küldés sikeressége
        """
        components = [
            {
                "type": "body",
                "parameters": [
                    {
                        "type": "text",
                        "text": customer_name
                    },
                    {
                        "type": "text",
                        "text": f"{cart_value:,.0f} Ft"
                    }
                ]
            }
        ]
        
        # Kedvezmény kód hozzáadása, ha van
        if discount_code:
            components.append({
                "type": "button",
                "sub_type": "url",
                "index": 0,
                "parameters": [
                    {
                        "type": "text",
                        "text": discount_code
                    }
                ]
            })
        
        return await self.send_template_message(
            recipient_number,
            "abandoned_cart_reminder",
            "hu",
            components
        )
    
    async def send_welcome_message(self, recipient_number: str, customer_name: str) -> bool:
        """
        Üdvözlő üzenet küldése.
        
        Args:
            recipient_number: Címzett telefonszám
            customer_name: Vásárló neve
            
        Returns:
            Küldés sikeressége
        """
        text = f"👋 Szia {customer_name}! Üdvözöllek a ChatBuddy webshopban! Hogyan segíthetek?"
        
        buttons = [
            {
                "type": "reply",
                "reply": {
                    "id": "shop_now",
                    "title": "🛍️ Vásárlás"
                }
            },
            {
                "type": "reply",
                "reply": {
                    "id": "view_products",
                    "title": "📋 Termékek"
                }
            },
            {
                "type": "reply",
                "reply": {
                    "id": "help",
                    "title": "❓ Segítség"
                }
            }
        ]
        
        return await self.send_interactive_message(recipient_number, text, buttons)
    
    async def send_help_message(self, recipient_number: str) -> bool:
        """
        Segítség üzenet küldése.
        
        Args:
            recipient_number: Címzett telefonszám
            
        Returns:
            Küldés sikeressége
        """
        text = "🔧 Itt van, amiben segíthetek:"
        
        sections = [
            {
                "title": "Segítség",
                "rows": [
                    {
                        "id": "help_guide",
                        "title": "📖 Segítség útmutató",
                        "description": "Részletes útmutató"
                    },
                    {
                        "id": "contact",
                        "title": "📞 Kapcsolat",
                        "description": "Vegye fel a kapcsolatot"
                    }
                ]
            },
            {
                "title": "Vásárlás",
                "rows": [
                    {
                        "id": "shop_now",
                        "title": "🛍️ Vásárlás",
                        "description": "Böngésszen termékek között"
                    }
                ]
            }
        ]
        
        return await self.send_list_message(recipient_number, text, "Válassz opciót", sections)
    
    async def send_product_catalog(
        self,
        recipient_number: str,
        products: List[Dict[str, Any]]
    ) -> bool:
        """
        Termék katalógus küldése.
        
        Args:
            recipient_number: Címzett telefonszám
            products: Termékek listája
            
        Returns:
            Küldés sikeressége
        """
        text = "🛍️ Íme a legnépszerűbb termékeink:"
        
        sections = [
            {
                "title": "Termékek",
                "rows": []
            }
        ]
        
        for product in products[:10]:  # Max 10 termék
            sections[0]["rows"].append({
                "id": f"product_{product['id']}",
                "title": product['name'],
                "description": f"{product['price']:,.0f} Ft"
            })
        
        return await self.send_list_message(recipient_number, text, "Termékek megtekintése", sections)
    
    async def send_order_status(
        self,
        recipient_number: str,
        order_id: str,
        status: str,
        tracking_url: Optional[str] = None
    ) -> bool:
        """
        Rendelési státusz üzenet küldése.
        
        Args:
            recipient_number: Címzett telefonszám
            order_id: Rendelés azonosító
            status: Rendelési státusz
            tracking_url: Követési URL (opcionális)
            
        Returns:
            Küldés sikeressége
        """
        text = f"📦 Rendelés #{order_id} státusza: {status}"
        
        buttons = []
        if tracking_url:
            buttons.append({
                "type": "reply",
                "reply": {
                    "id": f"track_order_{order_id}",
                    "title": "🚚 Követés"
                }
            })
        
        buttons.append({
            "type": "reply",
            "reply": {
                "id": "shop_now",
                "title": "🛍️ Új vásárlás"
            }
        })
        
        return await self.send_interactive_message(recipient_number, text, buttons)
    
    async def get_message_status(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Üzenet státusz lekérése.
        
        Args:
            message_id: Üzenet azonosító
            
        Returns:
            Üzenet státusz adatok
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/{message_id}",
                    params={"access_token": self.access_token},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Error getting message status: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting message status: {e}")
            return None
    
    async def get_phone_number_info(self) -> Optional[Dict[str, Any]]:
        """
        Telefonszám információk lekérése.
        
        Returns:
            Telefonszám információk
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/{self.phone_number_id}",
                    params={"access_token": self.access_token},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Error getting phone number info: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting phone number info: {e}")
            return None


def create_whatsapp_client() -> WhatsAppBusinessClient:
    """
    WhatsApp Business kliens létrehozása.
    
    Returns:
        WhatsApp kliens
    """
    import os
    
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    verify_token = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN")
    
    if not all([access_token, phone_number_id, verify_token]):
        logger.warning("WhatsApp Business credentials not found in environment variables")
        return None
    
    return WhatsAppBusinessClient(access_token, phone_number_id, verify_token)
