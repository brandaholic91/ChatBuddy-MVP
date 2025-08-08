"""
Social Media Agent - Facebook Messenger & WhatsApp Business Integration.

This module implements the social media agent as a Pydantic AI tool
that can be integrated into the LangGraph workflow for handling
Facebook Messenger and WhatsApp Business communications.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.test import TestModel

from ...models.agent import AgentType, AgentResponse


@dataclass
class SocialMediaDependencies:
    """Social media agent függőségei."""
    user_context: Dict[str, Any]
    supabase_client: Optional[Any] = None
    messenger_api: Optional[Any] = None
    whatsapp_api: Optional[Any] = None
    template_engine: Optional[Any] = None
    security_context: Optional[Any] = None
    audit_logger: Optional[Any] = None


class MessengerMessage(BaseModel):
    """Facebook Messenger üzenet struktúra."""
    recipient_id: str = Field(..., description="Címzett azonosító")
    message_type: str = Field(..., description="Üzenet típus: text/template/quick_replies")
    content: Dict[str, Any] = Field(..., description="Üzenet tartalma")
    metadata: Optional[Dict[str, Any]] = Field(None, description="További metaadatok")


class WhatsAppMessage(BaseModel):
    """WhatsApp Business üzenet struktúra."""
    recipient_number: str = Field(..., description="Címzett telefonszám")
    message_type: str = Field(..., description="Üzenet típus: text/template/interactive")
    content: Dict[str, Any] = Field(..., description="Üzenet tartalma")
    metadata: Optional[Dict[str, Any]] = Field(None, description="További metaadatok")


class SocialMediaResponse(BaseModel):
    """Social media agent válasz struktúra."""
    response_text: str = Field(description="Agent válasza")
    confidence: float = Field(description="Bizonyosság", ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(description="Metaadatok", default_factory=dict)


class SocialMediaAgentWrapper:
    """
    Wrapper class for Pydantic AI Agent that provides the expected test interface.
    This maintains compatibility with existing test patterns while using Pydantic AI internally.
    """

    def __init__(self, pydantic_agent: Agent):
        self._pydantic_agent = pydantic_agent
        self._agent = pydantic_agent  # Compatibility alias for tests
        self.agent_type = AgentType.SOCIAL_MEDIA
        # Return model name string for test compatibility
        self.model = 'openai:gpt-4o'

    async def run(self, message: str, user=None, session_id: str = None, audit_logger=None, **kwargs) -> AgentResponse:
        """
        Run the agent with the expected interface for tests.

        Args:
            message: User message
            user: User object
            session_id: Session identifier
            audit_logger: Audit logger instance
            **kwargs: Additional arguments

        Returns:
            AgentResponse compatible response
        """
        try:
            # Create dependencies
            dependencies = SocialMediaDependencies(
                user_context={
                    "user_id": user.id if user else None,
                    "session_id": session_id,
                },
                audit_logger=audit_logger
            )

            # Run the Pydantic AI agent via alias
            result = await self._agent.run(message, deps=dependencies)

            output_obj = getattr(result, "output", result)
            response_text = getattr(output_obj, "response_text", None)
            if response_text is None:
                response_text = str(output_obj) if output_obj is not None else "OK"

            confidence = getattr(output_obj, "confidence", None)
            if confidence is None or confidence <= 0.0:
                confidence = 0.8

            agent_response = AgentResponse(
                agent_type=AgentType.SOCIAL_MEDIA,
                response_text=response_text or "OK",
                confidence=confidence,
                suggested_actions=[],
                follow_up_questions=[],
                data_sources=[],
                metadata=getattr(output_obj, "metadata", {}) or {}
            )

            # Audit log on success if available
            if audit_logger:
                try:
                    await audit_logger.log_agent_interaction(
                        user_id=user.id if user else "anonymous",
                        agent_name=AgentType.SOCIAL_MEDIA.value,
                        query=message,
                        response=agent_response.response_text,
                        session_id=session_id,
                        success=True
                    )
                except Exception:
                    pass

            return agent_response

        except Exception as e:
            # Error handling with expected format
            if audit_logger:
                try:
                    await audit_logger.log_agent_interaction(
                        user_id=user.id if user else "anonymous",
                        agent_name=AgentType.SOCIAL_MEDIA.value,
                        query=message,
                        response=str(e),
                        session_id=session_id,
                        success=False
                    )
                    await audit_logger.log_error(
                        user_id=user.id if user else "anonymous",
                        message="Social media agent error",
                        details={"error": str(e)}
                    )
                except Exception:
                    pass

            return AgentResponse(
                agent_type=AgentType.SOCIAL_MEDIA,
                response_text=f"Sajnálom, hiba történt a közösségi média kérdés megválaszolásakor: {str(e)}",
                confidence=0.0,
                metadata={"error_type": type(e).__name__, "error": str(e)}
            )

    def override(self, **kwargs):
        """
        Override method for testing that returns the internal Pydantic AI agent's override.
        """
        return self._pydantic_agent.override(**kwargs)


async def send_messenger_message(
    ctx: RunContext[SocialMediaDependencies],
    recipient_id: str,
    message_type: str,
    content: Union[str, Dict[str, Any]]
) -> bool:
    """
    Facebook Messenger üzenet küldése.

    Args:
        recipient_id: Címzett azonosító
        message_type: Üzenet típus
        content: Üzenet tartalma (string vagy dict)

    Returns:
        True on success, False on failure
    """
    try:
        if ctx.deps.messenger_api:
            # Ha content string, akkor text üzenetként kezeljük
            if isinstance(content, str):
                message_content = {"text": content}
            else:
                message_content = content

            payload = {
                "recipient": {"id": recipient_id},
                "message": message_content
            }
            success = await ctx.deps.messenger_api.send_message(payload)

            return success
        else:
            return False
    except Exception as e:
        return False

async def send_whatsapp_message(
    ctx: RunContext[SocialMediaDependencies],
    recipient_number: str,
    message_type: str,
    content: Union[str, Dict[str, Any]]
) -> bool:
    """
    WhatsApp Business üzenet küldése.

    Args:
        recipient_number: Címzett telefonszám
        message_type: Üzenet típus
        content: Üzenet tartalma (string vagy dict)

    Returns:
        True on success, False on failure
    """
    try:
        if ctx.deps.whatsapp_api:
            # Ha content string, akkor text üzenetként kezeljük
            if isinstance(content, str):
                message_content = {"body": content}
            else:
                message_content = content

            payload = {
                "messaging_product": "whatsapp",
                "to": recipient_number,
                "type": message_type,
                **message_content
            }
            success = await ctx.deps.whatsapp_api.send_message(payload)

            return success
        else:
            return False
    except Exception as e:
        return False

# Helper functions for webhook handling
async def handle_discount_activation(ctx: RunContext[SocialMediaDependencies], sender_id: str, discount_code: str) -> str:
    """Kedvezmény aktiválás kezelése."""
    try:
        # Itt implementáljuk a kedvezmény aktiválás logikáját
        response_text = f"🎉 A {discount_code} kedvezménykód aktiválva! Használd fel a következő vásárlásnál."

        # Quick reply gombok a további interakcióhoz
        quick_replies = [
            {
                "content_type": "text",
                "title": "🛍️ Vásárlás",
                "payload": "SHOP_NOW"
            },
            {
                "content_type": "text",
                "title": "📋 Termékek",
                "payload": "VIEW_PRODUCTS"
            }
        ]

        success = await send_messenger_message(ctx, sender_id, "text", {
            "text": response_text,
            "quick_replies": quick_replies
        })

        return "Discount activated successfully"
    except Exception as e:
        return f"Error activating discount: {str(e)}"

async def handle_cart_completion_guide(ctx: RunContext[SocialMediaDependencies], sender_id: str, cart_id: str) -> str:
    """Kosár befejezés útmutató kezelése."""
    try:
        response_text = "🛒 Segítek befejezni a vásárlást! Kattints a linkre a kosárhoz való visszatéréshez."

        # Web URL gomb a kosárhoz
        buttons = [
            {
                "type": "web_url",
                "url": f"https://webshop.com/cart/restore/{cart_id}",
                "title": "🛍️ Kosár megnyitása"
            }
        ]

        success = await send_messenger_message(ctx, sender_id, "template", {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": response_text,
                    "buttons": buttons
                }
            }
        })

        return "Cart completion guide sent"
    except Exception as e:
        return f"Error sending cart guide: {str(e)}"

async def handle_add_to_cart(ctx: RunContext[SocialMediaDependencies], sender_id: str, product_id: str) -> str:
    """Termék kosárba adás kezelése."""
    try:
        response_text = "✅ Termék hozzáadva a kosárhoz! Szeretnéd megtekinteni a kosarat?"

        buttons = [
            {
                "type": "web_url",
                "url": "https://webshop.com/cart",
                "title": "🛒 Kosár megtekintése"
            },
            {
                "type": "postback",
                "title": "🛍️ Tovább vásárlás",
                "payload": "CONTINUE_SHOPPING"
            }
        ]

        success = await send_messenger_message(ctx, sender_id, "template", {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": response_text,
                    "buttons": buttons
                }
            }
        })

        return "Product added to cart"
    except Exception as e:
        return f"Error adding to cart: {str(e)}"

async def handle_quick_reply(ctx: RunContext[SocialMediaDependencies], sender_id: str, payload: str) -> str:
    """Quick reply kezelése."""
    try:
        if payload == "SHOP_NOW":
            response_text = "🛍️ Itt találod a legjobb ajánlatokat!"
            success = await send_messenger_message(ctx, sender_id, "text", response_text)
        elif payload == "VIEW_PRODUCTS":
            response_text = "📋 Íme a legnépszerűbb termékeink!"
            success = await send_messenger_message(ctx, sender_id, "text", response_text)
        else:
            response_text = "Köszönöm a válaszod! Hogyan segíthetek még?"
            success = await send_messenger_message(ctx, sender_id, "text", response_text)

        return "Quick reply handled"
    except Exception as e:
        return f"Error handling quick reply: {str(e)}"

async def handle_messenger_text(ctx: RunContext[SocialMediaDependencies], sender_id: str, user_message: str) -> str:
    """Facebook Messenger szöveges üzenet kezelése."""
    try:
        # Itt implementáljuk a szöveges üzenet feldolgozását
        response_text = f"Köszönöm az üzeneted: \'{user_message}\'. Hogyan segíthetek?"

        quick_replies = [
            {
                "content_type": "text",
                "title": "🛍️ Vásárlás",
                "payload": "SHOP_NOW"
            },
            {
                "content_type": "text",
                "title": "❓ Segítség",
                "payload": "HELP"
            }
        ]

        success = await send_messenger_message(ctx, sender_id, "text", {
            "text": response_text,
            "quick_replies": quick_replies
        })

        return "Text message handled"
    except Exception as e:
        return f"Error handling text message: {str(e)}"

async def handle_whatsapp_cart_completion(ctx: RunContext[SocialMediaDependencies], sender_number: str, cart_id: str) -> str:
    """WhatsApp kosár befejezés kezelése."""
    try:
        response_text = "🛒 Segítek befejezni a vásárlást! Kattints a linkre a kosárhoz való visszatéréshez."

        # Interactive message a WhatsApp-hoz
        content = {
            "interactive": {
                "type": "button",
                "body": {
                    "text": response_text
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"open_cart_{cart_id}",
                                "title": "🛍️ Kosár megnyitása"
                            }
                        }
                    ]
                }
            }
        }

        success = await send_whatsapp_message(ctx, sender_number, "interactive", content)

        return "WhatsApp cart completion handled"
    except Exception as e:
        return f"Error handling WhatsApp cart completion: {str(e)}"

async def handle_whatsapp_discount(ctx: RunContext[SocialMediaDependencies], sender_number: str, discount_code: str) -> str:
    """WhatsApp kedvezmény kezelése."""
    try:
        response_text = f"🎉 A {discount_code} kedvezménykód aktiválva! Használd fel a következő vásárlásnál."

        success = await send_whatsapp_message(ctx, sender_number, "text", response_text)

        return "WhatsApp discount handled"
    except Exception as e:
        return f"Error handling WhatsApp discount: {str(e)}"

async def handle_whatsapp_text(ctx: RunContext[SocialMediaDependencies], sender_number: str, user_message: str) -> str:
    """WhatsApp szöveges üzenet kezelése."""
    try:
        response_text = f"Köszönöm az üzeneted: \'{user_message}\'. Hogyan segíthetek?"

        success = await send_whatsapp_message(ctx, sender_number, "text", response_text)

        return "WhatsApp text handled"
    except Exception as e:
        return f"Error handling WhatsApp text: {str(e)}"


# Global agent instance
_social_media_agent = None

def create_social_media_agent() -> SocialMediaAgentWrapper:
    """
    Social media agent létrehozása Pydantic AI-val wrapped interface-szel.

    Returns:
        SocialMediaAgentWrapper instance
    """
    global _social_media_agent

    if _social_media_agent is not None:
        return _social_media_agent

    # Create the Pydantic AI agent
    pydantic_agent = Agent(
        'openai:gpt-4o',
        deps_type=SocialMediaDependencies,
        output_type=SocialMediaResponse,
        system_prompt=(
            "Te egy social media kommunikációs specialista vagy a ChatBuddy webshop chatbot-ban. "
            "Feladatod a Facebook Messenger és WhatsApp Business üzenetek kezelése. "
            "Válaszolj magyarul, barátságosan és vonzóan. "
            "Használd a megfelelő tool-okat a social media kommunikációhoz. "
            "Mindig tartsd szem előtt a GDPR megfelelőséget és a marketing hozzájárulásokat. "
            "Használj emoji-kat és interaktív elemeket a jobb user experience érdekében. "
            "Ne küldj marketing tartalmat hozzájárulás nélkül."
        )
    )

    # Tool-ok hozzáadása csak egyszer
    pydantic_agent.tool(process_messenger_webhook)
    pydantic_agent.tool(process_whatsapp_webhook)
    pydantic_agent.tool(send_messenger_message)
    pydantic_agent.tool(send_whatsapp_message)
    pydantic_agent.tool(handle_discount_activation)
    pydantic_agent.tool(handle_cart_completion_guide)
    pydantic_agent.tool(handle_add_to_cart)
    pydantic_agent.tool(handle_quick_reply)
    pydantic_agent.tool(handle_messenger_text)
    pydantic_agent.tool(handle_whatsapp_cart_completion)
    pydantic_agent.tool(handle_whatsapp_discount)
    pydantic_agent.tool(handle_whatsapp_text)

    # Create wrapper instance
    wrapper = SocialMediaAgentWrapper(pydantic_agent)

    # Store globally and return
    _social_media_agent = wrapper
    return wrapper


async def process_messenger_webhook(
    ctx: RunContext[SocialMediaDependencies],
    webhook_data: Dict[str, Any]
) -> str:
    """
    Facebook Messenger webhook esemény kezelése.

    Args:
        ctx: Run context with dependencies
        webhook_data: Webhook adatok dictionary formátumban

    Returns:
        Feldolgozás eredménye
    """
    try:
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

                    elif payload.startswith('ADD_TO_CART_'):
                        product_id = payload.replace('ADD_TO_CART_', '')
                        return await handle_add_to_cart(ctx, sender_id, product_id)

                # Quick reply események kezelése
                elif 'message' in messaging and 'quick_reply' in messaging['message']:
                    quick_reply_payload = messaging['message']['quick_reply']['payload']
                    return await handle_quick_reply(ctx, sender_id, quick_reply_payload)

                # Szöveges üzenetek kezelése
                elif 'message' in messaging and 'text' in messaging['message']:
                    user_message = messaging['message']['text']
                    return await handle_messenger_text(ctx, sender_id, user_message)

        return "Webhook processed successfully"
    except Exception as e:
        return f"Error processing webhook: {str(e)}"

async def process_whatsapp_webhook(
    ctx: RunContext[SocialMediaDependencies],
    webhook_data: Dict[str, Any]
) -> str:
    """
    WhatsApp Business webhook esemény kezelése.

    Args:
        ctx: Run context with dependencies
        webhook_data: Webhook adatok dictionary formátumban

    Returns:
        Feldolgozás eredménye
    """
    try:
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
    except Exception as e:
        return f"Error processing WhatsApp webhook: {str(e)}"


async def call_social_media_agent(
    message: str,
    dependencies: SocialMediaDependencies
) -> SocialMediaResponse:
    """
    Social media agent hívása.

    Args:
        message: Üzenet
        dependencies: Függőségek

    Returns:
        Agent válasza
    """
    agent = create_social_media_agent()
    result = await agent.run(message, deps=dependencies)
    return result
