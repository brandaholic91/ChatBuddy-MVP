
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from src.integrations.social_media.messenger import FacebookMessengerClient, create_messenger_client
from src.integrations.social_media.whatsapp import WhatsAppBusinessClient, create_whatsapp_client

# Facebook Messenger Tests
@pytest.fixture
def messenger_client():
    return FacebookMessengerClient(
        page_access_token="test_token",
        app_secret="test_secret",
        verify_token="test_verify_token"
    )

@pytest.mark.asyncio
async def test_messenger_verify_webhook_success(messenger_client):
    challenge = await messenger_client.verify_webhook("subscribe", "test_verify_token", "12345")
    assert challenge == 12345

@pytest.mark.asyncio
async def test_messenger_verify_webhook_failure(messenger_client):
    with pytest.raises(HTTPException):
        await messenger_client.verify_webhook("unsubscribe", "wrong_token", "12345")

def test_messenger_verify_signature(messenger_client):
    body = b'{"object":"page","entry":[{"id":"<PAGE_ID>","time":1458692752478,"messaging":[{"sender":{"id":"<PSID>"},"recipient":{"id":"<PAGE_ID>"},"timestamp":1458692752478,"message":{"mid":"m_1458692752478"}}]}]}'
    signature = "sha256=a4e7b0e0b0f0c0a0e0b0f0c0a0e0b0f0c0a0e0b0f0c0a0e0b0f0c0a0e0b0f0c0"
    with patch('hmac.new') as mock_hmac:
        mock_hmac.return_value.hexdigest.return_value = "a4e7b0e0b0f0c0a0e0b0f0c0a0e0b0f0c0a0e0b0f0c0a0e0b0f0c0a0e0b0f0c0"
        assert messenger_client.verify_signature(signature, body) is True

@pytest.mark.asyncio
async def test_messenger_send_message_success(messenger_client):
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        result = await messenger_client.send_message({"test": "payload"})
        assert result is True

@pytest.mark.asyncio
async def test_messenger_send_message_failure(messenger_client):
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        result = await messenger_client.send_message({"test": "payload"})
        assert result is False

@pytest.mark.asyncio
async def test_messenger_get_user_profile_success(messenger_client):
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"first_name": "Test"}
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        profile = await messenger_client.get_user_profile("test_user_id")
        assert profile["first_name"] == "Test"

@pytest.mark.asyncio
async def test_messenger_get_user_profile_failure(messenger_client):
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        profile = await messenger_client.get_user_profile("test_user_id")
        assert profile is None

def test_create_messenger_client_success():
    with patch.dict('os.environ', {
        "FACEBOOK_PAGE_ACCESS_TOKEN": "test_token",
        "FACEBOOK_APP_SECRET": "test_secret",
        "FACEBOOK_WEBHOOK_VERIFY_TOKEN": "test_verify"
    }):
        client = create_messenger_client()
        assert isinstance(client, FacebookMessengerClient)

def test_create_messenger_client_failure():
    with patch.dict('os.environ', {}, clear=True):
        client = create_messenger_client()
        assert client is None

@pytest.mark.asyncio
async def test_messenger_send_text_message(messenger_client):
    with patch.object(messenger_client, 'send_message', new_callable=AsyncMock) as mock_send:
        await messenger_client.send_text_message("test_recipient", "test_text")
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_messenger_send_generic_template(messenger_client):
    with patch.object(messenger_client, 'send_message', new_callable=AsyncMock) as mock_send:
        await messenger_client.send_generic_template("test_recipient", [{"title": "test"}])
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_messenger_send_quick_replies(messenger_client):
    with patch.object(messenger_client, 'send_message', new_callable=AsyncMock) as mock_send:
        await messenger_client.send_quick_replies("test_recipient", "test_text", [{"title": "test"}])
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_messenger_send_button_template(messenger_client):
    with patch.object(messenger_client, 'send_message', new_callable=AsyncMock) as mock_send:
        await messenger_client.send_button_template("test_recipient", "test_text", [{"title": "test"}])
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_messenger_send_product_carousel(messenger_client):
    with patch.object(messenger_client, 'send_generic_template', new_callable=AsyncMock) as mock_send:
        products = [{'name': 'Test Product', 'price': 100, 'url': 'http://test.com', 'id': '123'}]
        await messenger_client.send_product_carousel("test_recipient", products)
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_messenger_send_abandoned_cart_reminder(messenger_client):
    with patch.object(messenger_client, 'send_generic_template', new_callable=AsyncMock) as mock_send:
        await messenger_client.send_abandoned_cart_reminder("test_recipient", "Test User", 100, "cart123", "DISCOUNT10")
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_messenger_send_welcome_message(messenger_client):
    with patch.object(messenger_client, 'send_quick_replies', new_callable=AsyncMock) as mock_send:
        await messenger_client.send_welcome_message("test_recipient", "Test User")
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_messenger_send_help_message(messenger_client):
    with patch.object(messenger_client, 'send_button_template', new_callable=AsyncMock) as mock_send:
        await messenger_client.send_help_message("test_recipient")
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_messenger_set_persistent_menu(messenger_client):
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        result = await messenger_client.set_persistent_menu([{"title": "test"}])
        assert result is True

# WhatsApp Business Tests
@pytest.fixture
def whatsapp_client():
    return WhatsAppBusinessClient(
        access_token="test_token",
        phone_number_id="test_phone_id",
        verify_token="test_verify_token"
    )

@pytest.mark.asyncio
async def test_whatsapp_verify_webhook_success(whatsapp_client):
    challenge = await whatsapp_client.verify_webhook("subscribe", "test_verify_token", "12345")
    assert challenge == 12345

@pytest.mark.asyncio
async def test_whatsapp_verify_webhook_failure(whatsapp_client):
    with pytest.raises(HTTPException):
        await whatsapp_client.verify_webhook("unsubscribe", "wrong_token", "12345")

@pytest.mark.asyncio
async def test_whatsapp_send_message_success(whatsapp_client):
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        result = await whatsapp_client.send_message({"test": "payload"})
        assert result is True

@pytest.mark.asyncio
async def test_whatsapp_send_message_failure(whatsapp_client):
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        result = await whatsapp_client.send_message({"test": "payload"})
        assert result is False

@pytest.mark.asyncio
async def test_whatsapp_get_message_status_success(whatsapp_client):
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "delivered"}
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        status = await whatsapp_client.get_message_status("test_message_id")
        assert status["status"] == "delivered"

@pytest.mark.asyncio
async def test_whatsapp_get_message_status_failure(whatsapp_client):
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        status = await whatsapp_client.get_message_status("test_message_id")
        assert status is None

@pytest.mark.asyncio
async def test_whatsapp_send_text_message(whatsapp_client):
    with patch.object(whatsapp_client, 'send_message', new_callable=AsyncMock) as mock_send:
        await whatsapp_client.send_text_message("test_recipient", "test_text")
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_whatsapp_send_template_message(whatsapp_client):
    with patch.object(whatsapp_client, 'send_message', new_callable=AsyncMock) as mock_send:
        await whatsapp_client.send_template_message("test_recipient", "test_template")
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_whatsapp_send_interactive_message(whatsapp_client):
    with patch.object(whatsapp_client, 'send_message', new_callable=AsyncMock) as mock_send:
        await whatsapp_client.send_interactive_message("test_recipient", "test_body", [{"title": "test"}])
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_whatsapp_send_list_message(whatsapp_client):
    with patch.object(whatsapp_client, 'send_message', new_callable=AsyncMock) as mock_send:
        await whatsapp_client.send_list_message("test_recipient", "test_body", "test_button", [{"title": "test"}])
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_whatsapp_send_media_message(whatsapp_client):
    with patch.object(whatsapp_client, 'send_message', new_callable=AsyncMock) as mock_send:
        await whatsapp_client.send_media_message("test_recipient", "image", "http://test.com/img.png")
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_whatsapp_send_abandoned_cart_template(whatsapp_client):
    with patch.object(whatsapp_client, 'send_template_message', new_callable=AsyncMock) as mock_send:
        await whatsapp_client.send_abandoned_cart_template("test_recipient", "Test User", 100, "cart123", "DISCOUNT10")
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_whatsapp_send_welcome_message(whatsapp_client):
    with patch.object(whatsapp_client, 'send_interactive_message', new_callable=AsyncMock) as mock_send:
        await whatsapp_client.send_welcome_message("test_recipient", "Test User")
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_whatsapp_send_help_message(whatsapp_client):
    with patch.object(whatsapp_client, 'send_list_message', new_callable=AsyncMock) as mock_send:
        await whatsapp_client.send_help_message("test_recipient")
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_whatsapp_send_product_catalog(whatsapp_client):
    with patch.object(whatsapp_client, 'send_list_message', new_callable=AsyncMock) as mock_send:
        products = [{'name': 'Test Product', 'price': 100, 'id': '123'}]
        await whatsapp_client.send_product_catalog("test_recipient", products)
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_whatsapp_send_order_status(whatsapp_client):
    with patch.object(whatsapp_client, 'send_interactive_message', new_callable=AsyncMock) as mock_send:
        await whatsapp_client.send_order_status("test_recipient", "order123", "shipped", "http://track.com")
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_whatsapp_get_phone_number_info(whatsapp_client):
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"display_phone_number": "+1 555-555-5555"}
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        info = await whatsapp_client.get_phone_number_info()
        assert info["display_phone_number"] == "+1 555-555-5555"

def test_create_whatsapp_client_success():
    with patch.dict('os.environ', {
        "WHATSAPP_ACCESS_TOKEN": "test_token",
        "WHATSAPP_PHONE_NUMBER_ID": "test_phone_id",
        "WHATSAPP_WEBHOOK_VERIFY_TOKEN": "test_verify"
    }):
        client = create_whatsapp_client()
        assert isinstance(client, WhatsAppBusinessClient)

def test_create_whatsapp_client_failure():
    with patch.dict('os.environ', {}, clear=True):
        client = create_whatsapp_client()
        assert client is None
