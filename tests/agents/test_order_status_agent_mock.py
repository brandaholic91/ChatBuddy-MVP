# tests/agents/test_order_status_agent_mock.py

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.agents.order_status.agent import create_order_status_agent, OrderStatusDependencies, OrderResponse, OrderInfo
from src.models.agent import AgentResponse, AgentType

@pytest.fixture
def order_status_agent_instance():
    return create_order_status_agent()

@pytest.mark.unit
@pytest.mark.agents
@pytest.mark.fast
class TestOrderStatusAgentMock:

    @pytest.fixture
    def mock_order_status_dependencies(self, sample_user, mock_audit_logger):
        return OrderStatusDependencies(
            user_context={"user_id": sample_user.id},
            supabase_client=AsyncMock(),
            webshop_api=AsyncMock(),
            security_context=MagicMock(),
            audit_logger=mock_audit_logger
        )
    
    async def test_agent_initialization(self, order_status_agent_instance):
        """Agent inicializálás tesztje."""
        assert order_status_agent_instance.model == 'openai:gpt-4o'
        assert order_status_agent_instance.agent_type == AgentType.ORDER_STATUS
    
    async def test_get_order_by_id_success(self, order_status_agent_instance, mock_order_status_dependencies):
        """Rendelés lekérdezés azonosító alapján sikeres tesztje."""
        mock_order_info = OrderInfo(
            order_id="ORD123",
            status="Feldolgozás alatt",
            order_date="2024-01-01",
            estimated_delivery="2024-01-05",
            total_amount=100.0,
            items=[],
            shipping_address={},
            tracking_number="TRK123",
            payment_status="Kifizetve"
        )

        with patch.object(order_status_agent_instance._agent, 'run') as mock_run:
            mock_run.return_value = OrderResponse(
                response_text="Itt van a rendelés információja.",
                confidence=1.0,
                order_info=mock_order_info,
                status_summary="Feldolgozás alatt"
            )
            
            result = await order_status_agent_instance.run("Rendelés ORD123 státusza", deps=mock_order_status_dependencies)
            
            assert isinstance(result, AgentResponse)
            assert "rendelés információja" in result.response_text
            assert result.confidence == 1.0
            assert result.agent_type == AgentType.ORDER_STATUS
            assert result.metadata["order_info"]["order_id"] == "ORD123"
            mock_order_status_dependencies.audit_logger.log_agent_interaction.assert_called_once()

    async def test_get_user_orders_success(self, order_status_agent_instance, mock_order_status_dependencies):
        """Felhasználó rendeléseinek lekérdezése sikeres tesztje."""
        mock_orders = [
            OrderInfo(
                order_id="ORD123",
                status="Feldolgozás alatt",
                order_date="2024-01-01",
                estimated_delivery="2024-01-05",
                total_amount=100.0,
                items=[],
                shipping_address={},
                tracking_number="TRK123",
                payment_status="Kifizetve"
            )
        ]

        with patch.object(order_status_agent_instance._agent, 'run') as mock_run:
            mock_run.return_value = OrderResponse(
                response_text="Itt vannak a rendeléseid.",
                confidence=1.0,
                user_orders=[o.model_dump() for o in mock_orders],
                status_summary="Rendelések listája"
            )
            
            result = await order_status_agent_instance.run("Mik a rendeléseim?", deps=mock_order_status_dependencies)
            
            assert isinstance(result, AgentResponse)
            assert "rendeléseid" in result.response_text
            assert result.confidence == 1.0
            assert result.agent_type == AgentType.ORDER_STATUS
            assert len(result.metadata["user_orders"]) == 1
            mock_order_status_dependencies.audit_logger.log_agent_interaction.assert_called_once()

    async def test_error_handling(self, order_status_agent_instance, mock_order_status_dependencies):
        """Hibakezelés tesztje."""
        with patch.object(order_status_agent_instance._agent, 'run') as mock_run:
            mock_run.side_effect = Exception("Order status agent error")
            
            result = await order_status_agent_instance.run("test", deps=mock_order_status_dependencies)
            
            assert isinstance(result, AgentResponse)
            assert "hiba történt" in result.response_text.lower()
            assert result.confidence == 0.0
            assert result.agent_type == AgentType.ORDER_STATUS
            assert "error_type" in result.metadata
            mock_order_status_dependencies.audit_logger.log_agent_interaction.assert_called_once()
            mock_order_status_dependencies.audit_logger.log_error.assert_called_once()
