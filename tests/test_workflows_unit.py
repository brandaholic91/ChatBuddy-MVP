"""
Unit tests for workflow components.
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.workflows.coordinator import Coordinator
from src.workflows.langgraph_workflow import LangGraphWorkflow


class TestCoordinator:
    """Unit tests for Coordinator."""
    
    @pytest.mark.unit
    @pytest.mark.workflow
    def test_coordinator_initialization(self, mock_workflow_config):
        """Test Coordinator initialization."""
        coordinator = Coordinator(config=mock_workflow_config)
        assert coordinator is not None
        assert coordinator.config == mock_workflow_config
    
    @pytest.mark.unit
    @pytest.mark.workflow
    @pytest.mark.asyncio
    async def test_coordinator_route_message(self, mock_workflow_config, mock_chat_message):
        """Test Coordinator message routing."""
        coordinator = Coordinator(config=mock_workflow_config)
        route = await coordinator.route_message(mock_chat_message)
        assert route is not None
        assert isinstance(route, str)
    
    @pytest.mark.unit
    @pytest.mark.workflow
    def test_coordinator_get_available_agents(self, mock_workflow_config):
        """Test Coordinator available agents."""
        coordinator = Coordinator(config=mock_workflow_config)
        agents = coordinator.get_available_agents()
        assert isinstance(agents, list)
        assert len(agents) > 0
    
    @pytest.mark.unit
    @pytest.mark.workflow
    @pytest.mark.asyncio
    async def test_coordinator_process_conversation(self, mock_workflow_config, mock_agent_state):
        """Test Coordinator conversation processing."""
        coordinator = Coordinator(config=mock_workflow_config)
        result = await coordinator.process_conversation(mock_agent_state)
        assert result is not None
        assert "response" in result


class TestLangGraphWorkflow:
    """Unit tests for LangGraphWorkflow."""
    
    @pytest.mark.unit
    @pytest.mark.workflow
    @pytest.mark.ai
    def test_langgraph_workflow_initialization(self, mock_workflow_config):
        """Test LangGraphWorkflow initialization."""
        workflow = LangGraphWorkflow(config=mock_workflow_config)
        assert workflow is not None
        assert workflow.config == mock_workflow_config
    
    @pytest.mark.unit
    @pytest.mark.workflow
    @pytest.mark.ai
    @pytest.mark.asyncio
    async def test_langgraph_workflow_create_graph(self, mock_workflow_config):
        """Test LangGraphWorkflow graph creation."""
        workflow = LangGraphWorkflow(config=mock_workflow_config)
        graph = await workflow.create_graph()
        assert graph is not None
    
    @pytest.mark.unit
    @pytest.mark.workflow
    @pytest.mark.ai
    @pytest.mark.asyncio
    async def test_langgraph_workflow_execute(self, mock_workflow_config, mock_agent_state):
        """Test LangGraphWorkflow execution."""
        workflow = LangGraphWorkflow(config=mock_workflow_config)
        result = await workflow.execute(mock_agent_state)
        assert result is not None
        assert "output" in result
    
    @pytest.mark.unit
    @pytest.mark.workflow
    @pytest.mark.ai
    def test_langgraph_workflow_get_nodes(self, mock_workflow_config):
        """Test LangGraphWorkflow nodes."""
        workflow = LangGraphWorkflow(config=mock_workflow_config)
        nodes = workflow.get_nodes()
        assert isinstance(nodes, list)
        assert len(nodes) > 0
    
    @pytest.mark.unit
    @pytest.mark.workflow
    @pytest.mark.ai
    def test_langgraph_workflow_get_edges(self, mock_workflow_config):
        """Test LangGraphWorkflow edges."""
        workflow = LangGraphWorkflow(config=mock_workflow_config)
        edges = workflow.get_edges()
        assert isinstance(edges, list)
        assert len(edges) > 0 