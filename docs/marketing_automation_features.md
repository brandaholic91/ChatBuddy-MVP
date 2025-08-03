# Marketing Automation & Kosárelhagyás Follow-up

## 🛒 Áttekintés

A Chatbuddy MVP marketing automation rendszere intelligens follow-up üzenetekkel segíti a vásárlók visszatérését és növeli a konverziós rátákat. A rendszer automatikusan felismeri a kosárelhagyást és személyre szabott üzeneteket küld multiple csatornákon keresztül.

---

## 🎯 **Főbb Funkciók**

### **🔍 Abandoned Cart Detection**
- **Automatikus felismerés**: Session inaktivitás alapú kosárelhagyás detektálás
- **Intelligens timing**: 30 perc inaktivitás után trigger aktiválás
- **Kosár értékelés**: Minimális kosárérték alapú priorizáció
- **User behavior tracking**: Visszatérési minták elemzése

### **📧 Multi-Channel Follow-up**
- **Email automation**: Személyre szabott HTML email sablonok
- **SMS notifications**: Rövid, sürgető üzenetek mobilon
- **In-app chat**: Visszatérő felhasználók üdvözlése chatbot-ban
- **Facebook Messenger**: Interaktív üzenetek és carousel kártyák
- **WhatsApp Business**: Gazdag médiatartalom és quick reply gombok
- **Push notifications**: Browser push értesítések (jövőbeli bővítés)

### **🌐 Social Media Integration**
- **Facebook Messenger Platform**: Template messages, generic templates, quick replies
- **WhatsApp Business API**: Interactive messages, media messages, template messages
- **Cross-platform messaging**: Egységes üzenet delivery minden csatornán
- **Social CRM**: Messenger és WhatsApp conversation tracking

### **🎨 Személyre Szabás**
- **Dynamic content**: Termékképek és -leírások beillesztése
- **Pricing intelligence**: Dinamikus kedvezmények és ajánlatok
- **Behavioral targeting**: Múltbeli vásárlások alapú ajánlások
- **Segmentation**: Vásárlói csoportok alapú üzenet testreszabás

---

## 🏗️ **Architektúra és Implementáció**

### **1. Marketing Automation Agent**

```python
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
import asyncio

@dataclass
class MarketingDependencies:
    """Marketing automation ügynök függőségei"""
    supabase_client: Any
    email_service: Any      # SendGrid integration
    sms_service: Any        # Twilio integration  
    messenger_service: Any  # Facebook Messenger API
    whatsapp_service: Any   # WhatsApp Business API
    webshop_api: Any
    template_engine: Any    # Jinja2 templates
    user_context: dict

class AbandonedCartEvent(BaseModel):
    """Kosárelhagyás esemény modell"""
    cart_id: str = Field(..., description="Kosár egyedi azonosító")
    customer_id: str = Field(..., description="Ügyfél azonosító")
    session_id: str = Field(..., description="Session azonosító")
    abandoned_at: datetime = Field(..., description="Elhagyás időpontja")
    cart_value: float = Field(..., ge=0, description="Kosár értéke")
    items: List[dict] = Field(..., description="Kosár elemek listája")
    customer_email: Optional[str] = Field(None, description="Ügyfél email címe")
    customer_phone: Optional[str] = Field(None, description="Ügyfél telefonszáma")
    follow_up_attempts: int = Field(default=0, description="Küldött emlékeztetők száma")
    returned: bool = Field(default=False, description="Visszatért-e a vásárló")

class FollowUpCampaign(BaseModel):
    """Follow-up kampány konfigurációs modell"""
    campaign_type: str = Field(..., description="Kampány típusa")
    trigger_delay_minutes: int = Field(..., description="Trigger késés percekben")
    message_template: str = Field(..., description="Üzenet sablon azonosító")
    discount_percentage: Optional[float] = Field(None, description="Kedvezmény százalék")
    max_attempts: int = Field(default=3, description="Maximum próbálkozások")
    active: bool = Field(default=True, description="Kampány aktív státusza")

# Marketing Automation Agent inicializálása
marketing_agent = Agent(
    'openai:gpt-4o',
    deps_type=MarketingDependencies,
    system_prompt="""
    Te egy marketing automation specialista vagy, aki segíti a vásárlóknak visszatérni és befejezni a vásárlásukat.
    
    Feladataid:
    - Kosárelhagyás felismerése és follow-up üzenetek küldése
    - Személyre szabott ajánlatok és kedvezmények generálása  
    - Vásárlói visszatérés optimalizálása
    - Marketing kampányok eredményességének követése
    
    Mindig barátságos, segítőkész és nem tolakodó hangnemet használj.
    A magyar vásárlói szokásokat és kultúrát vedd figyelembe.
    """
)
```

### **2. Core Tools és Funkciók**

```python
@marketing_agent.tool
async def detect_abandoned_cart(
    ctx: RunContext[MarketingDependencies],
    session_id: str,
    threshold_minutes: int = 30
) -> Optional[AbandonedCartEvent]:
    """Kosárelhagyás automatikus felismerése"""
    
    # Session utolsó aktivitás ellenőrzése
    session = await ctx.deps.supabase_client.table('user_sessions').select('*').eq('session_id', session_id).single().execute()
    
    if not session.data:
        return None
    
    last_activity = datetime.fromisoformat(session.data['last_activity'])
    time_inactive = (datetime.now() - last_activity).total_seconds() / 60
    
    if time_inactive < threshold_minutes:
        return None
    
    # Kosár tartalom lekérése
    cart_items = await ctx.deps.webshop_api.get_cart_items(session_id)
    
    if not cart_items or len(cart_items) == 0:
        return None
    
    # Kosár érték kalkuláció
    total_value = sum(item['price'] * item['quantity'] for item in cart_items)
    
    # Minimum kosárérték ellenőrzés (pl. 5000 Ft felett)
    if total_value < 5000:
        return None
    
    # Abandoned cart event létrehozása
    abandoned_event = AbandonedCartEvent(
        cart_id=f"cart_{session_id}",
        customer_id=session.data.get('customer_id', 'anonymous'),
        session_id=session_id,
        abandoned_at=datetime.now(),
        cart_value=total_value,
        items=cart_items,
        customer_email=session.data.get('customer_email'),
        customer_phone=session.data.get('customer_phone')
    )
    
    # Esemény mentése adatbázisba
    await ctx.deps.supabase_client.table('abandoned_carts').insert(abandoned_event.dict()).execute()
    
    return abandoned_event

@marketing_agent.tool
async def send_follow_up_email(
    ctx: RunContext[MarketingDependencies],
    abandoned_cart: AbandonedCartEvent,
    template_name: str = 'abandoned_cart_reminder'
) -> bool:
    """Személyre szabott follow-up email küldése"""
    
    if not abandoned_cart.customer_email:
        return False
    
    # Email sablon renderelése
    template_data = {
        'customer_name': await get_customer_name(ctx, abandoned_cart.customer_id),
        'cart_items': abandoned_cart.items,
        'cart_total': f"{abandoned_cart.cart_value:,.0f} Ft",
        'return_url': f"https://webshop.com/cart/restore/{abandoned_cart.cart_id}",
        'discount_code': await generate_discount_code(ctx, abandoned_cart.customer_id)
    }
    
    email_content = await ctx.deps.template_engine.render(
        template_name, 
        **template_data
    )
    
    # Email küldés SendGrid-del
    success = await ctx.deps.email_service.send_email(
        to_email=abandoned_cart.customer_email,
        subject="🛒 Ne felejtsd el! Vár rád a kosaradban...",
        html_content=email_content
    )
    
    if success:
        # Follow-up attempt tracking
        await ctx.deps.supabase_client.table('abandoned_carts').update({
            'follow_up_attempts': abandoned_cart.follow_up_attempts + 1,
            'last_follow_up': datetime.now().isoformat()
        }).eq('cart_id', abandoned_cart.cart_id).execute()
    
    return success

@marketing_agent.tool  
async def send_follow_up_sms(
    ctx: RunContext[MarketingDependencies],
    abandoned_cart: AbandonedCartEvent
) -> bool:
    """Rövid SMS emlékeztető küldése"""
    
    if not abandoned_cart.customer_phone:
        return False
    
    # SMS sablon personalizálása
    customer_name = await get_customer_name(ctx, abandoned_cart.customer_id)
    discount_code = await generate_discount_code(ctx, abandoned_cart.customer_id)
    
    sms_message = f"""
    Szia {customer_name}! 🛒 
    
    {abandoned_cart.cart_value:,.0f} Ft értékben maradt valami a kosaradban.
    
    Használd a {discount_code} kódot 10% kedvezményért!
    
    Vásárlás befejezése: https://short.ly/cart/{abandoned_cart.cart_id}
    """
    
    # SMS küldés Twilio-val
    success = await ctx.deps.sms_service.send_sms(
        to_phone=abandoned_cart.customer_phone,
        message=sms_message.strip()
    )
    
    return success

@marketing_agent.tool
async def send_messenger_follow_up(
    ctx: RunContext[MarketingDependencies],
    abandoned_cart: AbandonedCartEvent
) -> bool:
    """Facebook Messenger interaktív üzenet küldése"""
    
    messenger_id = await get_customer_messenger_id(ctx, abandoned_cart.customer_id)
    if not messenger_id:
        return False
    
    customer_name = await get_customer_name(ctx, abandoned_cart.customer_id)
    discount_code = await generate_discount_code(ctx, abandoned_cart.customer_id)
    
    # Facebook Messenger carousel üzenet template
    messenger_payload = {
        "recipient": {"id": messenger_id},
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": [
                        {
                            "title": f"Szia {customer_name}! 🛒",
                            "subtitle": f"{abandoned_cart.cart_value:,.0f} Ft maradt a kosaradban",
                            "image_url": "https://your-domain.com/cart-reminder.jpg",
                            "buttons": [
                                {
                                    "type": "web_url",
                                    "url": f"https://webshop.com/cart/restore/{abandoned_cart.cart_id}",
                                    "title": "Vásárlás befejezése 🛍️"
                                },
                                {
                                    "type": "postback",
                                    "title": f"🎁 {discount_code} kód használata",
                                    "payload": f"USE_DISCOUNT_{discount_code}"
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }
    
    # Facebook Messenger API hívás
    success = await ctx.deps.messenger_service.send_message(messenger_payload)
    
    if success:
        # Messenger follow-up tracking
        await ctx.deps.supabase_client.table('abandoned_carts').update({
            'messenger_sent': True,
            'messenger_sent_at': datetime.now().isoformat()
        }).eq('cart_id', abandoned_cart.cart_id).execute()
    
    return success

@marketing_agent.tool
async def send_whatsapp_follow_up(
    ctx: RunContext[MarketingDependencies],
    abandoned_cart: AbandonedCartEvent
) -> bool:
    """WhatsApp Business interaktív üzenet küldése"""
    
    whatsapp_number = await get_customer_whatsapp(ctx, abandoned_cart.customer_id)
    if not whatsapp_number:
        return False
    
    customer_name = await get_customer_name(ctx, abandoned_cart.customer_id)
    discount_code = await generate_discount_code(ctx, abandoned_cart.customer_id)
    
    # WhatsApp Business API template message
    whatsapp_payload = {
        "messaging_product": "whatsapp",
        "to": whatsapp_number,
        "type": "template",
        "template": {
            "name": "abandoned_cart_hu",  # Pre-approved WhatsApp template
            "language": {
                "code": "hu"
            },
            "components": [
                {
                    "type": "header",
                    "parameters": [
                        {
                            "type": "image",
                            "image": {
                                "link": "https://your-domain.com/cart-image.jpg"
                            }
                        }
                    ]
                },
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": customer_name
                        },
                        {
                            "type": "text", 
                            "text": f"{abandoned_cart.cart_value:,.0f}"
                        },
                        {
                            "type": "text",
                            "text": discount_code
                        }
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": "0",
                    "parameters": [
                        {
                            "type": "text",
                            "text": abandoned_cart.cart_id
                        }
                    ]
                }
            ]
        }
    }
    
    # Alternative: Interactive message with quick replies
    interactive_payload = {
        "messaging_product": "whatsapp",
        "to": whatsapp_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "text",
                "text": f"🛒 Szia {customer_name}!"
            },
            "body": {
                "text": f"{abandoned_cart.cart_value:,.0f} Ft értékben maradt valami a kosaradban.\n\n🎁 Használd a *{discount_code}* kódot 10% kedvezményért!"
            },
            "footer": {
                "text": "Webshop csapata"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"complete_cart_{abandoned_cart.cart_id}",
                            "title": "🛍️ Vásárlás befejezése"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"use_discount_{discount_code}",
                            "title": f"🎁 {discount_code} használata"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "remind_later",
                            "title": "⏰ Emlékeztess később"
                        }
                    }
                ]
            }
        }
    }
    
    # WhatsApp Business API hívás (interactive message preferált)
    success = await ctx.deps.whatsapp_service.send_message(interactive_payload)
    
    if success:
        # WhatsApp follow-up tracking
        await ctx.deps.supabase_client.table('abandoned_carts').update({
            'whatsapp_sent': True,
            'whatsapp_sent_at': datetime.now().isoformat()
        }).eq('cart_id', abandoned_cart.cart_id).execute()
    
    return success

@marketing_agent.tool
async def handle_cart_return(
    ctx: RunContext[MarketingDependencies],
    cart_id: str,
    customer_id: str
) -> str:
    """Visszatérő vásárló üdvözlése"""
    
    # Kosár visszaállítása
    cart_restored = await ctx.deps.webshop_api.restore_cart(cart_id)
    
    if cart_restored:
        # Abandoned cart esemény lezárása
        await ctx.deps.supabase_client.table('abandoned_carts').update({
            'returned': True,
            'returned_at': datetime.now().isoformat()
        }).eq('cart_id', cart_id).execute()
        
        return """
        🎉 Örülök, hogy visszatértél! 
        
        Visszaállítottam a kosaradat. Van egy kis meglepetésem számodra - 
        használd a WELCOME10 kódot 10% kedvezményért!
        
        Segíthetek befejezni a rendelést?
        """
    
    return "Sajnos nem sikerült visszaállítani a kosaradat. Segítek újra összeállítani?"

@marketing_agent.tool
async def generate_personalized_offers(
    ctx: RunContext[MarketingDependencies],
    customer_id: str,
    abandoned_items: List[dict]
) -> List[dict]:
    """Személyre szabott ajánlatok generálása"""
    
    # Vásárlási előzmények elemzése
    purchase_history = await ctx.deps.webshop_api.get_customer_history(customer_id)
    
    # Hasonló termékek keresése vector search-el
    recommendations = []
    for item in abandoned_items:
        similar_products = await ctx.deps.vector_db.similarity_search(
            f"{item['name']} {item['category']}", 
            limit=3
        )
        recommendations.extend(similar_products)
    
    # Ajánlatok személyre szabása
    personalized_offers = []
    for product in recommendations:
        offer = {
            'product_id': product['id'],
            'product_name': product['name'],
            'original_price': product['price'],
            'discounted_price': product['price'] * 0.9,  # 10% kedvezmény
            'reason': 'Hasonló termék, amit mások is vásároltak',
            'urgency': 'Limitált idejű ajánlat - csak 24 órán át!'
        }
        personalized_offers.append(offer)
    
    return personalized_offers[:5]  # Top 5 ajánlat
```

### **3. Social Media Communication Agent**

```python
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from typing import Dict, Any, Optional

@dataclass
class SocialMediaDependencies:
    """Social media kommunikációs ügynök függőségei"""
    messenger_api: Any      # Facebook Messenger Platform API
    whatsapp_api: Any       # WhatsApp Business API
    supabase_client: Any
    template_engine: Any
    user_context: dict

class SocialMediaMessage(BaseModel):
    """Social media üzenet modell"""
    platform: str = Field(..., description="Platform: messenger/whatsapp")
    recipient_id: str = Field(..., description="Címzett azonosító")
    message_type: str = Field(..., description="Üzenet típus: text/template/interactive")
    content: Dict[str, Any] = Field(..., description="Üzenet tartalma")
    metadata: Optional[Dict[str, Any]] = Field(None, description="További metaadatok")

# Social Media Communication Agent
social_media_agent = Agent(
    'openai:gpt-4o',
    deps_type=SocialMediaDependencies,
    system_prompt="""
    Te egy social media kommunikációs specialista vagy. A feladatod:
    
    - Facebook Messenger és WhatsApp üzenetek kezelése
    - Interaktív üzenetek és template-ek létrehozása
    - Cross-platform conversation tracking
    - Customer engagement optimalizálása
    
    Minden üzenet legyen barátságos, segítőkész és a magyar kultúrának megfelelő.
    Használj emoji-kat és interaktív elemeket a jobb user experience érdekében.
    """
)

@social_media_agent.tool
async def handle_messenger_webhook(
    ctx: RunContext[SocialMediaDependencies],
    webhook_data: Dict[str, Any]
) -> str:
    """Facebook Messenger webhook esemény kezelése"""
    
    for entry in webhook_data.get('entry', []):
        for messaging in entry.get('messaging', []):
            sender_id = messaging['sender']['id']
            
            # Postback események kezelése (gomb kattintások)
            if 'postback' in messaging:
                payload = messaging['postback']['payload']
                
                if payload.startswith('USE_DISCOUNT_'):
                    discount_code = payload.replace('USE_DISCOUNT_', '')
                    return await handle_discount_activation(ctx, sender_id, discount_code)
                
                elif payload.startswith('COMPLETE_CART_'):
                    cart_id = payload.replace('COMPLETE_CART_', '')
                    return await handle_cart_completion_guide(ctx, sender_id, cart_id)
            
            # Quick reply események kezelése
            elif 'message' in messaging and 'quick_reply' in messaging['message']:
                quick_reply_payload = messaging['message']['quick_reply']['payload']
                return await handle_quick_reply(ctx, sender_id, quick_reply_payload)
            
            # Szöveges üzenetek kezelése
            elif 'message' in messaging and 'text' in messaging['message']:
                user_message = messaging['message']['text']
                return await handle_messenger_text(ctx, sender_id, user_message)
    
    return "Webhook processed successfully"

@social_media_agent.tool
async def handle_whatsapp_webhook(
    ctx: RunContext[SocialMediaDependencies],
    webhook_data: Dict[str, Any]
) -> str:
    """WhatsApp Business webhook esemény kezelése"""
    
    for entry in webhook_data.get('entry', []):
        for change in entry.get('changes', []):
            if change.get('field') == 'messages':
                for message in change.get('value', {}).get('messages', []):
                    sender_number = message['from']
                    
                    # Interactive message button click
                    if message.get('type') == 'interactive':
                        button_reply = message['interactive']['button_reply']
                        button_id = button_reply['id']
                        
                        if button_id.startswith('complete_cart_'):
                            cart_id = button_id.replace('complete_cart_', '')
                            return await handle_whatsapp_cart_completion(ctx, sender_number, cart_id)
                        
                        elif button_id.startswith('use_discount_'):
                            discount_code = button_id.replace('use_discount_', '')
                            return await handle_whatsapp_discount(ctx, sender_number, discount_code)
                    
                    # Text message
                    elif message.get('type') == 'text':
                        user_message = message['text']['body']
                        return await handle_whatsapp_text(ctx, sender_number, user_message)
    
    return "WhatsApp webhook processed successfully"

@social_media_agent.tool
async def create_messenger_product_carousel(
    ctx: RunContext[SocialMediaDependencies],
    recipient_id: str,
    products: List[Dict[str, Any]]
) -> bool:
    """Facebook Messenger termék carousel létrehozása"""
    
    elements = []
    for product in products[:10]:  # Max 10 elem carousel-ben
        element = {
            "title": product['name'],
            "subtitle": f"{product['price']:,.0f} Ft • {product.get('description', '')[:80]}...",
            "image_url": product.get('image_url', 'https://via.placeholder.com/300x200'),
            "default_action": {
                "type": "web_url",
                "url": product['url'],
                "messenger_extensions": True,
                "webview_height_ratio": "tall"
            },
            "buttons": [
                {
                    "type": "web_url",
                    "url": product['url'],
                    "title": "🛍️ Megtekintés"
                },
                {
                    "type": "postback",
                    "title": "📦 Kosárba",
                    "payload": f"ADD_TO_CART_{product['id']}"
                }
            ]
        }
        elements.append(element)
    
    carousel_payload = {
        "recipient": {"id": recipient_id},
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": elements
                }
            }
        }
    }
    
    success = await ctx.deps.messenger_api.send_message(carousel_payload)
    return success

@social_media_agent.tool
async def create_whatsapp_product_list(
    ctx: RunContext[SocialMediaDependencies],
    recipient_number: str,
    products: List[Dict[str, Any]]
) -> bool:
    """WhatsApp interaktív termék lista létrehozása"""
    
    sections = [{
        "title": "Kiemelt termékek",
        "rows": []
    }]
    
    for product in products[:10]:  # Max 10 termék
        row = {
            "id": f"product_{product['id']}",
            "title": product['name'][:24],  # WhatsApp title limit
            "description": f"{product['price']:,.0f} Ft • {product.get('description', '')[:72]}"
        }
        sections[0]["rows"].append(row)
    
    list_payload = {
        "messaging_product": "whatsapp",
        "to": recipient_number,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "🛍️ Termékajánlataink"
            },
            "body": {
                "text": "Válassz a kedvenc termékeid közül! Minden termékre ingyenes szállítás és 30 napos visszavitel."
            },
            "footer": {
                "text": "Webshop csapata"
            },
            "action": {
                "button": "Termékek megtekintése",
                "sections": sections
            }
        }
    }
    
    success = await ctx.deps.whatsapp_api.send_message(list_payload)
    return success
```

### **4. Background Task System**

```python
from celery import Celery
import asyncio

# Celery app inicializálása
celery_app = Celery('marketing_automation')
celery_app.config_from_object('celery_config')

@celery_app.task
async def abandoned_cart_workflow(cart_id: str):
    """Automatikus kosárelhagyás follow-up workflow"""
    
    # 30 perc várakozás
    await asyncio.sleep(30 * 60)
    
    # Első emlékeztető email
    abandoned_cart = await get_abandoned_cart(cart_id)
    if abandoned_cart and not abandoned_cart.returned:
        await marketing_agent.run(
            f"Küldj follow-up emailt a {cart_id} kosárhoz",
            deps=marketing_deps
        )
    
    # 2 óra várakozás
    await asyncio.sleep(2 * 60 * 60)
    
    # SMS emlékeztető kedvezménnyel
    if abandoned_cart and not abandoned_cart.returned:
        await marketing_agent.run(
            f"Küldj SMS emlékeztetőt kedvezménnyel a {cart_id} kosárhoz",
            deps=marketing_deps
        )
    
    # 24 óra várakozás  
    await asyncio.sleep(24 * 60 * 60)
    
    # Végső ajánlat nagyobb kedvezménnyel
    if abandoned_cart and not abandoned_cart.returned:
        await marketing_agent.run(
            f"Küldj végső ajánlatot 20% kedvezménnyel a {cart_id} kosárhoz",
            deps=marketing_deps
        )

@celery_app.task
def trigger_abandoned_cart_detection():
    """Rendszeres kosárelhagyás detektálás (minden 15 percben)"""
    active_sessions = get_active_sessions()
    
    for session in active_sessions:
        abandoned_cart_workflow.delay(session['session_id'])
```

---

## 🛠️ **Adatbázis Schema Bővítések**

### **Supabase Tábla Definíciók**

```sql
-- Kosárelhagyás események tárolása (Social Media Support)
CREATE TABLE abandoned_carts (
    id SERIAL PRIMARY KEY,
    cart_id TEXT UNIQUE NOT NULL,
    customer_id TEXT,
    session_id TEXT NOT NULL,
    abandoned_at TIMESTAMP NOT NULL DEFAULT NOW(),
    cart_value DECIMAL(10,2) NOT NULL,
    items JSONB NOT NULL,
    customer_email TEXT,
    customer_phone TEXT,
    customer_messenger_id TEXT,        -- Facebook Messenger PSID
    customer_whatsapp TEXT,            -- WhatsApp Business number
    follow_up_attempts INTEGER DEFAULT 0,
    last_follow_up TIMESTAMP,
    email_sent BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMP,
    sms_sent BOOLEAN DEFAULT FALSE,
    sms_sent_at TIMESTAMP,
    messenger_sent BOOLEAN DEFAULT FALSE,  -- Facebook Messenger küldés
    messenger_sent_at TIMESTAMP,
    whatsapp_sent BOOLEAN DEFAULT FALSE,   -- WhatsApp küldés
    whatsapp_sent_at TIMESTAMP,
    returned BOOLEAN DEFAULT FALSE,
    returned_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Marketing kampányok konfigurációja
CREATE TABLE marketing_campaigns (
    id SERIAL PRIMARY KEY,
    campaign_name TEXT NOT NULL,
    campaign_type TEXT NOT NULL, -- 'abandoned_cart', 'product_recommendation', 'seasonal'
    trigger_rules JSONB NOT NULL,
    message_templates JSONB NOT NULL,
    scheduling_config JSONB,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Email/SMS üzenet küldési log
CREATE TABLE marketing_messages (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES marketing_campaigns(id),
    abandoned_cart_id INTEGER REFERENCES abandoned_carts(id),
    message_type TEXT NOT NULL, -- 'email', 'sms', 'chat', 'push'
    recipient TEXT NOT NULL,
    subject TEXT,
    content TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT NOW(),
    delivery_status TEXT DEFAULT 'pending', -- 'pending', 'sent', 'delivered', 'failed'
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    converted BOOLEAN DEFAULT FALSE
);

-- Kedvezmény kódok generálása és tracking
CREATE TABLE discount_codes (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    customer_id TEXT,
    discount_percentage DECIMAL(5,2),
    discount_amount DECIMAL(10,2),
    minimum_order_value DECIMAL(10,2),
    valid_from TIMESTAMP DEFAULT NOW(),
    valid_until TIMESTAMP NOT NULL,
    usage_limit INTEGER DEFAULT 1,
    times_used INTEGER DEFAULT 0,
    created_for TEXT, -- 'abandoned_cart', 'loyalty', 'seasonal'
    active BOOLEAN DEFAULT TRUE
);

-- Indexek teljesítmény optimalizáláshoz
CREATE INDEX idx_abandoned_carts_customer_id ON abandoned_carts(customer_id);
CREATE INDEX idx_abandoned_carts_abandoned_at ON abandoned_carts(abandoned_at);
CREATE INDEX idx_abandoned_carts_returned ON abandoned_carts(returned);
CREATE INDEX idx_marketing_messages_sent_at ON marketing_messages(sent_at);
CREATE INDEX idx_discount_codes_customer_id ON discount_codes(customer_id);
```

---

## ⚙️ **Környezeti Változók és Konfiguráció**

### **Environment Variables (.env frissítés)**

```bash
# Marketing Automation Configuration
EMAIL_SERVICE_PROVIDER=sendgrid
EMAIL_API_KEY=your_sendgrid_api_key
EMAIL_FROM_ADDRESS=no-reply@yourwebshop.com
EMAIL_FROM_NAME=YourWebshop Ügyfélszolgálat

# SMS Configuration  
SMS_SERVICE_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+36123456789

# Abandoned Cart Settings
ABANDONED_CART_TIMEOUT_MINUTES=30
FOLLOW_UP_EMAIL_DELAY_MINUTES=30
FOLLOW_UP_SMS_DELAY_HOURS=2
FINAL_OFFER_DELAY_HOURS=24
MINIMUM_CART_VALUE_FOR_FOLLOWUP=5000

# Discount Configuration
DEFAULT_DISCOUNT_PERCENTAGE=10
URGENT_DISCOUNT_PERCENTAGE=20
DISCOUNT_CODE_VALIDITY_DAYS=7
MAX_FOLLOW_UP_ATTEMPTS=3

# Background Tasks (Celery + Redis)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_TIMEZONE=Europe/Budapest

# Template Configuration
EMAIL_TEMPLATE_DIR=templates/email/
SMS_TEMPLATE_DIR=templates/sms/
DEFAULT_LANGUAGE=hu
```

### **Requirements.txt Kiegészítések**

```bash
# Marketing Automation & Messaging
sendgrid>=6.9.0
twilio>=8.2.0
jinja2>=3.1.0

# Background Task Processing
celery>=5.3.0
redis>=5.0.0
kombu>=5.3.0

# Email Template Rendering
premailer>=3.10.0  # CSS inlining for emails
html2text>=2020.1.16  # HTML to text conversion

# Analytics and Tracking
mixpanel>=4.9.0  # Optional: advanced analytics
segment-analytics-python>=2.2.0  # Optional: customer data platform
```

---

## 📊 **Analytics és Monitoring**

### **Kampány Teljesítmény Metrikák**

```python
class MarketingAnalytics:
    """Marketing automation teljesítmény tracking"""
    
    async def get_abandoned_cart_stats(self, date_range: tuple) -> dict:
        """Kosárelhagyás statisztikák"""
        stats = await self.supabase.rpc('get_abandoned_cart_stats', {
            'start_date': date_range[0],
            'end_date': date_range[1]
        }).execute()
        
        return {
            'total_abandoned_carts': stats.data['total_abandoned'],
            'total_abandoned_value': stats.data['total_value'],
            'follow_up_sent': stats.data['follow_ups_sent'],
            'return_rate': stats.data['return_rate'],
            'conversion_rate': stats.data['conversion_rate'],
            'recovered_revenue': stats.data['recovered_revenue']
        }
    
    async def get_email_campaign_performance(self, campaign_id: int) -> dict:
        """Email kampány teljesítmény"""
        performance = await self.supabase.table('marketing_messages').select('''
            COUNT(*) as sent_count,
            COUNT(opened_at) as opened_count,
            COUNT(clicked_at) as clicked_count,
            COUNT(CASE WHEN converted = true THEN 1 END) as converted_count
        ''').eq('campaign_id', campaign_id).execute()
        
        data = performance.data[0]
        
        return {
            'sent_count': data['sent_count'],
            'open_rate': (data['opened_count'] / data['sent_count']) * 100,
            'click_rate': (data['clicked_count'] / data['sent_count']) * 100,
            'conversion_rate': (data['converted_count'] / data['sent_count']) * 100
        }
```

### **Pydantic Logfire Integration**

```python
import logfire

# Marketing events logging
@logfire.instrument
async def log_abandoned_cart_event(cart_id: str, cart_value: float):
    logfire.info(
        "Abandoned cart detected",
        cart_id=cart_id,
        cart_value=cart_value,
        event_type="abandoned_cart"
    )

@logfire.instrument
async def log_follow_up_sent(cart_id: str, message_type: str, success: bool):
    logfire.info(
        "Follow-up message sent",
        cart_id=cart_id,
        message_type=message_type,
        success=success,
        event_type="follow_up_sent"
    )

@logfire.instrument  
async def log_cart_recovery(cart_id: str, recovered_value: float):
    logfire.info(
        "Cart recovered successfully",
        cart_id=cart_id,
        recovered_value=recovered_value,
        event_type="cart_recovered"
    )
```

---

## 🎨 **Email és SMS Sablonok**

### **HTML Email Sablon (Jinja2)**

```html
<!-- templates/email/abandoned_cart_reminder.html -->
<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ne felejtsd el a kosaradat!</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #2c3e50;">🛒 Szia {{ customer_name }}!</h1>
        
        <p>Észrevettem, hogy valami maradt a kosaradban. Ne hagyd, hogy elmenjanak ezek a nagyszerű termékek!</p>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2>A kosaradban található:</h2>
            {% for item in cart_items %}
            <div style="border-bottom: 1px solid #dee2e6; padding: 10px 0;">
                <strong>{{ item.name }}</strong><br>
                Mennyiség: {{ item.quantity }} db<br>
                Ár: {{ item.price | number_format }} Ft
            </div>
            {% endfor %}
            
            <h3 style="color: #e74c3c; margin-top: 20px;">
                Összesen: {{ cart_total }}
            </h3>
        </div>
        
        {% if discount_code %}
        <div style="background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <strong>🎉 Különleges ajánlat csak neked!</strong><br>
            Használd a <strong>{{ discount_code }}</strong> kódot és kapsz 10% kedvezményt!
        </div>
        {% endif %}
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{ return_url }}" style="background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                Vásárlás befejezése 
            </a>
        </div>
        
        <p style="color: #6c757d; font-size: 14px;">
            Ha bármilyen kérdésed van, írj nekünk vagy hívd ügyfélszolgálatunkat!<br>
            <strong>Chatbot:</strong> Azonnal válaszolok a webshopban<br>
            <strong>Telefon:</strong> +36 1 234 5678
        </p>
        
        <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
        
        <p style="color: #6c757d; font-size: 12px;">
            Ha nem szeretnél több ilyen emailt kapni, 
            <a href="{{ unsubscribe_url }}">iratkozz le itt</a>.
        </p>
    </div>
</body>
</html>
```

### **SMS Sablon**

```python
# templates/sms/abandoned_cart_sms.txt
"""
🛒 Szia {{ customer_name }}! 

{{ cart_total }} értékben maradt valami a kosaradban.

{% if discount_code %}
🎁 Használd a {{ discount_code }} kódot 10% kedvezményért!
{% endif %}

Befejezés: {{ short_url }}

YourWebshop csapata
"""
```

---

## 🚀 **Implementációs Roadmap**

### **Phase 1: Core Infrastructure (1-2 hét)**
- [x] Adatbázis schema létrehozása
- [x] Marketing Agent alapstruktúra
- [x] Background task system setup (Celery + Redis)
- [x] Email/SMS service integráció alapok

### **Phase 2: Basic Automation (1 hét)**  
- [x] Abandoned cart detection algoritmus
- [x] Egyszerű email follow-up
- [x] Basic analytics és logging
- [x] Template engine setup

### **Phase 3: Advanced Features (1-2 hét)**
- [x] SMS integration
- [x] Personalized offers és discount codes
- [x] Multi-stage follow-up campaigns
- [x] A/B testing framework

### **Phase 4: Optimization & Analytics (1 hét)**
- [x] Advanced analytics dashboard
- [x] Performance monitoring
- [x] Campaign optimization
- [x] GDPR compliance audit

---

## 📈 **Várható Eredmények**

### **Industry Benchmarks:**
- **Email open rate**: 15-25% (e-commerce átlag)
- **Click-through rate**: 2-5%
- **Cart recovery rate**: 10-15%
- **ROI**: 300-500% az automation kampányokon

### **Optimalizációs Célok:**
- **30% növekedés** a kosár abandon rate csökkentésében
- **20% növekedés** az average order value-ban
- **15% növekedés** a customer lifetime value-ban
- **50% csökkentés** a manual marketing tasks-okban

---

## 🔒 **GDPR Compliance és Adatvédelem**

### **Adatvédelmi Megfontolások**
- **Explicit consent**: Email/SMS marketing hozzájárulás kérése
- **Right to be forgotten**: Unsubscribe és adat törlési lehetőség
- **Data minimization**: Csak szükséges adatok tárolása
- **Audit trail**: Minden marketing aktivitás naplózása

### **Compliance Implementation**
```python
class GDPRCompliantMarketing:
    async def check_marketing_consent(self, customer_id: str) -> bool:
        """Marketing hozzájárulás ellenőrzése"""
        consent = await self.supabase.table('customer_consents').select('*').eq('customer_id', customer_id).execute()
        return consent.data and consent.data[0].get('marketing_emails', False)
    
    async def process_unsubscribe(self, customer_id: str, token: str) -> bool:
        """Leiratkozás feldolgozása"""
        # Token validáció
        # Marketing consent visszavonása
        # Audit log bejegyzés
        pass
    
    async def delete_customer_marketing_data(self, customer_id: str) -> bool:
        """Ügyfél marketing adatok törlése (GDPR right to be forgotten)"""
        # Abandoned carts törlése
        # Marketing messages törlése  
        # Discount codes deaktiválása
        # Audit log bejegyzés
        pass
```

---

## 🎯 **Következő Lépések**

1. **✅ Dokumentáció elkészült**
2. **🔄 Adatbázis schema implementálása**
3. **🔄 Email service (SendGrid) beállítása**
4. **🔄 SMS service (Twilio) beállítása**
5. **🔄 Celery background tasks konfigurálása**
6. **🔄 Marketing Agent fejlesztése**
7. **🔄 Email/SMS template engine**
8. **🔄 Analytics dashboard létrehozása**

**🚀 A marketing automation funkció hozzáadásával a Chatbuddy MVP egy teljes körű e-commerce marketing platformmá válik, amely automatikusan növeli a konverziós rátákat és javítja a customer experience-t!**