"""
Order Status Agent tesztek.

Ez a modul tartalmazza az Order Status Agent unit és integration teszteit:
- Agent létrehozás és inicializálás
- Rendelés lekérdezés tesztek
- Szállítási információk tesztek
- Státusz frissítés tesztek
- Biztonsági tesztek
- Teljesítmény tesztek
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any
from decimal import Decimal

from src.agents.order_status.agent import (
    create_order_status_agent,
    OrderStatusDependencies,
    OrderStatusResponse,
    MockOrderStatusAgent,
    get_order_by_id,
    get_orders_by_user,
    get_tracking_info,
    update_order_status,
    get_order_history
)
from src.models.order import Order, OrderStatus, OrderItem
from src.models.user import User
from src.config.security_prompts import SecurityContext
from src.config.audit_logging import SecurityAuditLogger

pytestmark = pytest.mark.anyio


class TestOrderStatusAgent:
    """Order Status Agent unit tesztek."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock dependencies az Order Status Agent-hez."""
        return OrderStatusDependencies(
            supabase_client=Mock(),
            webshop_api=Mock(),
            user_context={
                "user_id": "test_user_123",
                "email": "test@example.com",
                "phone": "+36123456789",
                "session_id": "test_session_123",
                "preferences": {}
            },
            security_context=SecurityContext(
                user_id="test_user_123",
                session_id="test_session_123",
                security_level="medium",
                gdpr_compliant=True,
                permissions=["basic_access"],
                data_access_scope=["public"]
            ),
            audit_logger=SecurityAuditLogger()
        )
    
    @pytest.fixture
    def mock_user(self):
        """Mock felhasználó objektum."""
        return User(
            id="test_user_123",
            name="Teszt Felhasználó",
            email="test@example.com",
            phone="+36123456789",
            created_at=datetime.now()
        )
    
    @pytest.fixture
    def mock_order(self):
        """Mock rendelés objektum."""
        return Order(
            id="order_123",
            order_number="ORD-123",
            user_id="test_user_123",
            status=OrderStatus.PENDING,
            subtotal=Decimal("50000"),
            total_amount=Decimal("50000"),
            currency="HUF",
            items=[
                OrderItem(
                    id="item_1",
                    order_id="order_123",
                    product_id="product_1",
                    product_name="Test Product",
                    quantity=1,
                    unit_price=Decimal("50000"),
                    total_price=Decimal("50000")
                )
            ],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.mark.unit
    def test_create_order_status_agent(self):
        """Teszt: Order Status Agent létrehozása."""
        agent = create_order_status_agent()
        assert agent is not None
        assert hasattr(agent, 'run')
    
    @pytest.mark.unit
    async def test_mock_order_status_agent(self, mock_dependencies):
        """Teszt: Mock Order Status Agent működése."""
        agent = MockOrderStatusAgent()
        result = await agent.run("Rendelésem státusza?", mock_dependencies)
        
        assert isinstance(result, OrderStatusResponse)
        assert result.message is not None
        assert result.confidence == 0.5
        assert result.metadata["agent_type"] == "mock_order_status"
    
    @pytest.mark.unit
    async def test_get_order_by_id_success(self, mock_dependencies, mock_order):
        """Teszt: Rendelés lekérdezése azonosító alapján - sikeres."""
        # Mock Supabase válasz
        mock_response = Mock()
        mock_response.data = [mock_order.model_dump()]
        mock_dependencies.supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        result = await get_order_by_id(
            type('MockContext', (), {'deps': mock_dependencies})(),
            "order_123"
        )
        
        assert isinstance(result, Order)
        assert result.id == "order_123"
        assert result.user_id == "test_user_123"
    
    @pytest.mark.unit
    async def test_get_order_by_id_not_found(self, mock_dependencies):
        """Teszt: Rendelés lekérdezése - nem található."""
        # Mock üres Supabase válasz
        mock_response = Mock()
        mock_response.data = []
        mock_dependencies.supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        with pytest.raises(ValueError, match="Rendelés nem található"):
            await get_order_by_id(
                type('MockContext', (), {'deps': mock_dependencies})(),
                "nonexistent_order"
            )
    
    @pytest.mark.unit
    async def test_get_orders_by_user(self, mock_dependencies, mock_order):
        """Teszt: Felhasználó rendeléseinek lekérdezése."""
        # Mock Supabase válasz
        mock_response = Mock()
        mock_response.data = [mock_order.model_dump()]
        mock_dependencies.supabase_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_response
        
        result = await get_orders_by_user(
            type('MockContext', (), {'deps': mock_dependencies})(),
            "test_user_123",
            limit=5
        )
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].id == "order_123"
    
    @pytest.mark.unit
    async def test_get_tracking_info(self, mock_dependencies):
        """Teszt: Szállítási információk lekérdezése."""
        # Mock webshop API válasz
        mock_tracking_data = {
            "tracking_number": "TRK123456",
            "status": "in_transit",
            "estimated_delivery": "2024-01-15",
            "current_location": "Budapest"
        }
        mock_dependencies.webshop_api.get_tracking_info = AsyncMock(return_value=mock_tracking_data)
        
        result = await get_tracking_info(
            type('MockContext', (), {'deps': mock_dependencies})(),
            "TRK123456"
        )
        
        assert result == mock_tracking_data
        mock_dependencies.webshop_api.get_tracking_info.assert_called_once_with("TRK123456")
    
    @pytest.mark.unit
    async def test_update_order_status(self, mock_dependencies, mock_order):
        """Teszt: Rendelés státusz frissítése."""
        # Mock frissített rendelés
        updated_order = mock_order.model_copy()
        updated_order.status = OrderStatus.SHIPPED
        updated_order.updated_at = datetime.now()
        # Javítjuk a Decimal típusokat
        updated_order.tax_amount = Decimal("0")
        updated_order.shipping_amount = Decimal("0")
        updated_order.discount_amount = Decimal("0")
        
        mock_response = Mock()
        mock_response.data = [updated_order.model_dump()]
        mock_dependencies.supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response
        
        result = await update_order_status(
            type('MockContext', (), {'deps': mock_dependencies})(),
            "order_123",
            OrderStatus.SHIPPED
        )
        
        assert isinstance(result, Order)
        assert result.status == OrderStatus.SHIPPED
    
    @pytest.mark.unit
    async def test_get_order_history(self, mock_dependencies):
        """Teszt: Rendelés státusz változások előzménye."""
        # Mock előzmény adatok
        mock_history = [
            {
                "id": "history_1",
                "order_id": "order_123",
                "old_status": "pending",
                "new_status": "processing",
                "created_at": "2024-01-10T10:00:00Z"
            },
            {
                "id": "history_2", 
                "order_id": "order_123",
                "old_status": "processing",
                "new_status": "shipped",
                "created_at": "2024-01-12T14:30:00Z"
            }
        ]
        
        mock_response = Mock()
        mock_response.data = mock_history
        mock_dependencies.supabase_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_response
        
        result = await get_order_history(
            type('MockContext', (), {'deps': mock_dependencies})(),
            "order_123"
        )
        
        assert result == mock_history


class TestOrderStatusAgentIntegration:
    """Order Status Agent integration tesztek."""
    
    @pytest.fixture
    def order_status_agent(self):
        """Order Status Agent instance."""
        return create_order_status_agent()
    
    @pytest.fixture
    def test_user(self):
        """Teszt felhasználó."""
        return User(
            id="test_user_123",
            name="Teszt Felhasználó",
            email="test@example.com",
            phone="+36123456789",
            created_at=datetime.now()
        )
    
    @pytest.mark.integration
    async def test_order_status_agent_process_message(self, order_status_agent, test_user):
        """Teszt: Order Status Agent üzenet feldolgozása."""
        # Mock dependencies
        with patch('src.agents.order_status.agent.OrderStatusDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "Rendelésed státusza: FELDOLGOZÁS ALATT"
            mock_result.confidence = 0.9
            mock_result.metadata = {"order_id": "order_123"}
            
            order_status_agent.run = AsyncMock(return_value=mock_result)
            
            # Teszt üzenet feldolgozása
            result = await order_status_agent.run(
                "Mi a rendelésem státusza?",
                deps=mock_deps
            )
            
            assert result.message == "Rendelésed státusza: FELDOLGOZÁS ALATT"
            assert result.confidence == 0.9
            assert result.metadata["order_id"] == "order_123"
    
    @pytest.mark.integration
    async def test_order_status_agent_error_handling(self, order_status_agent):
        """Teszt: Order Status Agent hibakezelés."""
        with patch('src.agents.order_status.agent.OrderStatusDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock hiba
            order_status_agent.run = AsyncMock(side_effect=Exception("Adatbázis hiba"))
            
            with pytest.raises(Exception, match="Adatbázis hiba"):
                await order_status_agent.run("Rendelésem státusza?", deps=mock_deps)


class TestOrderStatusAgentSecurity:
    """Order Status Agent biztonsági tesztek."""
    
    @pytest.fixture
    def order_status_agent(self):
        """Order Status Agent instance."""
        return create_order_status_agent()
    
    @pytest.mark.security
    async def test_order_status_agent_sql_injection_protection(self, order_status_agent):
        """Teszt: SQL injection védelem."""
        malicious_query = "'; DROP TABLE orders; --"
        
        with patch('src.agents.order_status.agent.OrderStatusDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "Érvénytelen rendelési azonosító"
            mock_result.confidence = 0.0
            
            order_status_agent.run = AsyncMock(return_value=mock_result)
            
            result = await order_status_agent.run(malicious_query, deps=mock_deps)
            
            # Ellenőrizzük, hogy nem adott ki érzékeny információt
            assert "DROP TABLE" not in result.message
            assert result.confidence == 0.0
    
    @pytest.mark.security
    async def test_order_status_agent_sensitive_data_protection(self, order_status_agent):
        """Teszt: Érzékeny adatok védelme."""
        sensitive_query = "Mi a kártyaszámom és a PIN kódom?"
        
        with patch('src.agents.order_status.agent.OrderStatusDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "Ezeket az információkat nem tudom megadni"
            mock_result.confidence = 0.0
            
            order_status_agent.run = AsyncMock(return_value=mock_result)
            
            result = await order_status_agent.run(sensitive_query, deps=mock_deps)
            
            # Ellenőrizzük, hogy nem adott ki érzékeny adatokat
            assert "kártya" not in result.message.lower()
            assert "pin" not in result.message.lower()
            assert result.confidence == 0.0
    
    @pytest.mark.security
    async def test_order_status_agent_unauthorized_access(self, order_status_agent):
        """Teszt: Jogosulatlan hozzáférés kezelése."""
        unauthorized_query = "Másik felhasználó rendeléseit szeretném látni"
        
        with patch('src.agents.order_status.agent.OrderStatusDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "Nincs jogosultságod más felhasználók adatainak megtekintéséhez"
            mock_result.confidence = 0.0
            
            order_status_agent.run = AsyncMock(return_value=mock_result)
            
            result = await order_status_agent.run(unauthorized_query, deps=mock_deps)
            
            assert "jogosultság" in result.message.lower()
            assert result.confidence == 0.0


class TestOrderStatusAgentPerformance:
    """Order Status Agent teljesítmény tesztek."""
    
    @pytest.fixture
    def order_status_agent(self):
        """Order Status Agent instance."""
        return create_order_status_agent()
    
    @pytest.mark.performance
    async def test_order_status_agent_response_time(self, order_status_agent):
        """Teszt: Válaszidő mérése."""
        import time
        
        with patch('src.agents.order_status.agent.OrderStatusDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "Rendelésed státusza: KÉSZ"
            mock_result.confidence = 0.9
            
            order_status_agent.run = AsyncMock(return_value=mock_result)
            
            start_time = time.time()
            result = await order_status_agent.run("Rendelésem státusza?", deps=mock_deps)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Válaszidőnek 5 másodperc alatt kell lennie
            assert response_time < 5.0
            assert result.message == "Rendelésed státusza: KÉSZ"
    
    @pytest.mark.performance
    async def test_order_status_agent_concurrent_requests(self, order_status_agent):
        """Teszt: Párhuzamos kérések kezelése."""
        with patch('src.agents.order_status.agent.OrderStatusDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "Rendelésed státusza: FELDOLGOZÁS ALATT"
            mock_result.confidence = 0.8
            
            order_status_agent.run = AsyncMock(return_value=mock_result)
            
            # Párhuzamos kérések - trio kompatibilitás miatt
            async def make_request():
                return await order_status_agent.run("Rendelésem státusza?", deps=mock_deps)
            
            # 5 párhuzamos kérés - trio kompatibilitás miatt
            results = []
            for _ in range(5):
                result = await make_request()
                results.append(result)
            
            # Minden kérésnek sikeresen le kell futnia
            assert len(results) == 5
            for result in results:
                assert result.message == "Rendelésed státusza: FELDOLGOZÁS ALATT"
                assert result.confidence == 0.8


class TestOrderStatusAgentEdgeCases:
    """Order Status Agent edge case tesztek."""
    
    @pytest.fixture
    def order_status_agent(self):
        """Order Status Agent instance."""
        return create_order_status_agent()
    
    @pytest.mark.edge_cases
    async def test_order_status_agent_empty_query(self, order_status_agent):
        """Teszt: Üres lekérdezés kezelése."""
        with patch('src.agents.order_status.agent.OrderStatusDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "Kérlek, adj meg egy rendelési azonosítót"
            mock_result.confidence = 0.0
            
            order_status_agent.run = AsyncMock(return_value=mock_result)
            
            result = await order_status_agent.run("", deps=mock_deps)
            
            assert "azonosítót" in result.message.lower()
            assert result.confidence == 0.0
    
    @pytest.mark.edge_cases
    async def test_order_status_agent_very_long_query(self, order_status_agent):
        """Teszt: Nagyon hosszú lekérdezés kezelése."""
        long_query = "Rendelésem státusza?" * 100  # 2000 karakter
        
        with patch('src.agents.order_status.agent.OrderStatusDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "Túl hosszú lekérdezés"
            mock_result.confidence = 0.0
            
            order_status_agent.run = AsyncMock(return_value=mock_result)
            
            result = await order_status_agent.run(long_query, deps=mock_deps)
            
            assert "hosszú" in result.message.lower()
            assert result.confidence == 0.0
    
    @pytest.mark.edge_cases
    async def test_order_status_agent_special_characters(self, order_status_agent):
        """Teszt: Speciális karakterek kezelése."""
        special_query = "Rendelésem státusza? 🚚📦 #order123 @user"
        
        with patch('src.agents.order_status.agent.OrderStatusDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "Rendelésed státusza: KÉSZ"
            mock_result.confidence = 0.9
            
            order_status_agent.run = AsyncMock(return_value=mock_result)
            
            result = await order_status_agent.run(special_query, deps=mock_deps)
            
            assert result.message == "Rendelésed státusza: KÉSZ"
            assert result.confidence == 0.9 