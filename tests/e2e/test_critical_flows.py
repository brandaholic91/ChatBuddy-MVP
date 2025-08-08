# tests/e2e/test_critical_flows.py

import pytest
import os
from fastapi.testclient import TestClient
from src.main import app
from src.models.chat import ChatRequest
from src.models.user import User

@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.requires_openai
@pytest.mark.requires_supabase
class TestCriticalFlows:
    """Kritikus üzleti folyamatok valódi tesztje."""
    
    @pytest.fixture(scope="class")
    def client(self):
        """FastAPI test client."""
        return TestClient(app)

    async def test_complete_chat_flow(self, client):
        """Teljes chat folyamat E2E tesztje."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available")
        
        # 1. Chat request
        request_data = ChatRequest(
            message="Milyen iPhone modellek vannak?",
            user_id="test_user_e2e",
            session_id="session_e2e"
        )
        
        # 2. Process through real coordinator
        response = client.post("/api/v1/chat", json=request_data.model_dump())
            
        # 3. Assertions
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 0
        assert data["agent_used"] == "product_info" # Expect product_info agent to be used
    
    async def test_agent_handoff_flow(self, client):
        """Agent átadási folyamat tesztje."""
        # Scenario: User asks about product, then asks about order status
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available")

        # First message: product inquiry
        product_request = ChatRequest(
            message="Milyen laptopokat ajánlanál?",
            user_id="test_user_handoff",
            session_id="session_handoff_1"
        )
        product_response = client.post("/api/v1/chat", json=product_request.model_dump())
        assert product_response.status_code == 200
        product_data = product_response.json()
        assert product_data["agent_used"] == "product_info"

        # Second message: order status inquiry (should trigger handoff)
        order_request = ChatRequest(
            message="Hol van a rendelésem?",
            user_id="test_user_handoff",
            session_id="session_handoff_1" # Same session to maintain context
        )
        order_response = client.post("/api/v1/chat", json=order_request.model_dump())
        assert order_response.status_code == 200
        order_data = order_response.json()
        assert order_data["agent_used"] == "order_status" # Expect handoff to order_status agent

    async def test_error_recovery_flow(self, client):
        """Hiba helyreállítási folyamat tesztje."""
        # Scenario: Invalid input, then valid input
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available")

        # First message: invalid input (too long)
        invalid_message = "a" * 5000 # Exceeds 4000 char limit
        invalid_request = ChatRequest(
            message=invalid_message,
            user_id="test_user_error",
            session_id="session_error_1"
        )
        invalid_response = client.post("/api/v1/chat", json=invalid_request.model_dump())
        assert invalid_response.status_code == 400 # Expect validation error
        error_data = invalid_response.json()
        assert "Túl hosszú üzenet" in error_data["message"]

        # Second message: valid input in the same session
        valid_request = ChatRequest(
            message="Szia, minden rendben?",
            user_id="test_user_error",
            session_id="session_error_1"
        )
        valid_response = client.post("/api/v1/chat", json=valid_request.model_dump())
        assert valid_response.status_code == 200 # Expect successful recovery
        valid_data = valid_response.json()
        assert "message" in valid_data
        assert len(valid_data["message"]) > 0
        assert valid_data["agent_used"] == "general" # Expect general agent to handle
