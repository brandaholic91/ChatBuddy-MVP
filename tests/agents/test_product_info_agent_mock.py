# tests/agents/test_product_info_agent_mock.py

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.agents.product_info.agent import create_product_info_agent, ProductInfoDependencies, ProductResponse, ProductInfo, ProductSearchResult
from src.models.agent import AgentResponse, AgentType
from src.models.user import User
from src.config.audit_logging import AuditLogger

@pytest.fixture
def product_info_agent_instance():
    return create_product_info_agent()

@pytest.mark.unit
@pytest.mark.agents
@pytest.mark.fast
class TestProductInfoAgentMock:
    
    @pytest.fixture
    def mock_audit_logger(self):
        return AsyncMock(spec=AuditLogger)

    @pytest.fixture
    def sample_user(self):
        return User(id="test_user_123", email="test@example.com")

    @pytest.fixture
    def mock_product_info_dependencies(self, sample_user, mock_audit_logger):
        return ProductInfoDependencies(
            user_context={"user_id": sample_user.id},
            supabase_client=AsyncMock(),
            webshop_api=AsyncMock(),
            security_context=MagicMock(),
            audit_logger=mock_audit_logger
        )
    
    async def test_agent_initialization(self, product_info_agent_instance):
        """Agent inicializálás tesztje."""
        assert product_info_agent_instance.model == 'openai:gpt-4o'
        assert product_info_agent_instance.agent_type == AgentType.PRODUCT_INFO
    
    async def test_search_products_success(self, product_info_agent_instance, mock_product_info_dependencies):
        """Termék keresés sikeres tesztje."""
        mock_products = [
            ProductInfo(
                name="Mock Phone",
                price=1000.0,
                description="A mock phone for testing",
                category="Electronics",
                availability="In Stock"
            )
        ]
        mock_search_result = ProductSearchResult(
            products=mock_products,
            total_count=1,
            search_query="phone"
        )

        with patch.object(product_info_agent_instance._agent, 'run') as mock_run:
            mock_run.return_value = ProductResponse(
                response_text="Itt van a keresési eredmény.",
                confidence=1.0,
                search_results=mock_search_result
            )
            
            result = await product_info_agent_instance.run("Keresek telefont", deps=mock_product_info_dependencies)
            
            assert isinstance(result, AgentResponse)
            assert "keresési eredmény" in result.response_text
            assert result.confidence == 1.0
            assert result.agent_type == AgentType.PRODUCT_INFO
            assert result.metadata["search_results"]["products"][0]["name"] == "Mock Phone"
            mock_product_info_dependencies.audit_logger.log_agent_interaction.assert_called_once()

    async def test_get_product_details_success(self, product_info_agent_instance, mock_product_info_dependencies):
        """Termék részletek lekérdezésének sikeres tesztje."""
        mock_product_details = ProductInfo(
            name="Mock Laptop",
            price=2000.0,
            description="A mock laptop for testing",
            category="Electronics",
            availability="In Stock"
        )

        with patch.object(product_info_agent_instance._agent, 'run') as mock_run:
            mock_run.return_value = ProductResponse(
                response_text="Itt vannak a termék részletei.",
                confidence=1.0,
                product_info=mock_product_details
            )
            
            result = await product_info_agent_instance.run("Mutasd a laptop részleteit", deps=mock_product_info_dependencies)
            
            assert isinstance(result, AgentResponse)
            assert "termék részletei" in result.response_text
            assert result.confidence == 1.0
            assert result.agent_type == AgentType.PRODUCT_INFO
            assert result.metadata["product_info"]["name"] == "Mock Laptop"
            mock_product_info_dependencies.audit_logger.log_agent_interaction.assert_called_once()

    async def test_error_handling(self, product_info_agent_instance, mock_product_info_dependencies):
        """Hibakezelés tesztje."""
        with patch.object(product_info_agent_instance._agent, 'run') as mock_run:
            mock_run.side_effect = Exception("Product info agent error")
            
            result = await product_info_agent_instance.run("test", deps=mock_product_info_dependencies)
            
            assert isinstance(result, AgentResponse)
            assert "hiba történt" in result.response_text.lower()
            assert result.confidence == 0.0
            assert result.agent_type == AgentType.PRODUCT_INFO
            assert "error_type" in result.metadata
            mock_product_info_dependencies.audit_logger.log_agent_interaction.assert_called_once()
            mock_product_info_dependencies.audit_logger.log_error.assert_called_once()
