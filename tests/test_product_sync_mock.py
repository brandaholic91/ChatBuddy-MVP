"""
Tesztelés a termékadat szinkronizáció mock implementációjához.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from src.integrations.webshop.mock_data_generator import (
    MockDataGenerator, MockSyncManager, MockEvent, MockEventType
)
from src.integrations.webshop.sync_scheduler import (
    SyncScheduler, SyncJobType, SyncJobConfig, RealTimeSyncManager
)
from src.integrations.webshop.conflict_resolver import (
    ConflictResolver, ConflictType, ResolutionStrategy, ConflictMonitor
)
from src.models.product import Product, ProductCategory


class TestMockDataGenerator:
    """Mock adat generátor tesztelése"""
    
    def test_generate_mock_product(self):
        """Mock termék generálás tesztelése"""
        generator = MockDataGenerator()
        product = generator.generate_mock_product(1001)
        
        assert isinstance(product, Product)
        assert product.id == "1001"
        assert product.name
        assert product.price > 0
        assert product.stock_quantity >= 0
        assert product.category_id in generator.product_categories
        assert product.sku.startswith("SKU-")
    
    def test_generate_mock_products(self):
        """Több mock termék generálás tesztelése"""
        generator = MockDataGenerator()
        products = generator.generate_mock_products(10)
        
        assert len(products) == 10
        assert all(isinstance(p, Product) for p in products)
        
        # Ellenőrizzük, hogy különböző termékek
        product_ids = [p.id for p in products]
        assert len(set(product_ids)) == 10
    
    def test_generate_mock_events(self):
        """Mock események generálás tesztelése"""
        generator = MockDataGenerator()
        events = generator.generate_mock_events(5)
        
        assert len(events) == 5
        assert all(isinstance(e, MockEvent) for e in events)
        assert all(e.event_type in MockEventType for e in events)
        
        # Ellenőrizzük, hogy időrendi sorrendben vannak
        timestamps = [e.timestamp for e in events]
        assert timestamps == sorted(timestamps)


class TestMockSyncManager:
    """Mock szinkronizációs menedzser tesztelése"""
    
    @pytest.fixture
    def sync_manager(self):
        """Sync manager fixture"""
        generator = MockDataGenerator()
        return MockSyncManager(generator)
    
    @pytest.mark.asyncio
    async def test_sync_products(self, sync_manager):
        """Termékek szinkronizálás tesztelése"""
        result = await sync_manager.sync_products()
        
        assert "timestamp" in result
        assert "products_synced" in result
        assert "new_products" in result
        assert "updated_products" in result
        assert "deleted_products" in result
        assert "errors" in result
        
        assert result["products_synced"] > 0
        assert isinstance(result["new_products"], int)
        assert isinstance(result["updated_products"], int)
        assert isinstance(result["deleted_products"], int)
    
    @pytest.mark.asyncio
    async def test_sync_inventory(self, sync_manager):
        """Készlet szinkronizálás tesztelése"""
        result = await sync_manager.sync_inventory()
        
        assert "timestamp" in result
        assert "inventory_updates" in result
        assert "total_updates" in result
        
        assert len(result["inventory_updates"]) > 0
        assert result["total_updates"] == len(result["inventory_updates"])
        
        # Ellenőrizzük az inventory update struktúrát
        for update in result["inventory_updates"]:
            assert "product_id" in update
            assert "old_stock" in update
            assert "new_stock" in update
            assert "change" in update
            assert "timestamp" in update
    
    @pytest.mark.asyncio
    async def test_sync_prices(self, sync_manager):
        """Ár szinkronizálás tesztelése"""
        result = await sync_manager.sync_prices()
        
        assert "timestamp" in result
        assert "price_updates" in result
        assert "total_updates" in result
        
        assert len(result["price_updates"]) > 0
        assert result["total_updates"] == len(result["price_updates"])
        
        # Ellenőrizzük az ár update struktúrát
        for update in result["price_updates"]:
            assert "product_id" in update
            assert "old_price" in update
            assert "new_price" in update
            assert "change_percentage" in update
            assert "timestamp" in update
    
    def test_get_sync_statistics(self, sync_manager):
        """Szinkronizációs statisztikák tesztelése"""
        # Először futtatunk néhány szinkronizációt
        asyncio.run(sync_manager.sync_products())
        asyncio.run(sync_manager.sync_inventory())
        
        stats = sync_manager.get_sync_statistics()
        
        assert "total_syncs" in stats
        assert "last_sync" in stats
        assert "average_products_per_sync" in stats
        assert "total_errors" in stats
        
        assert stats["total_syncs"] > 0
        assert stats["last_sync"] is not None


class TestSyncScheduler:
    """Szinkronizációs scheduler tesztelése"""
    
    @pytest.fixture
    def scheduler(self):
        """Scheduler fixture"""
        generator = MockDataGenerator()
        sync_manager = MockSyncManager(generator)
        return SyncScheduler(sync_manager)
    
    def test_add_job(self, scheduler):
        """Job hozzáadás tesztelése"""
        config = SyncJobConfig(SyncJobType.PRODUCT_SYNC, 30)
        scheduler.add_job(config)
        
        job_id = f"{config.job_type.value}_{config.interval_minutes}min"
        assert job_id in scheduler.jobs
    
    def test_remove_job(self, scheduler):
        """Job eltávolítás tesztelése"""
        config = SyncJobConfig(SyncJobType.PRODUCT_SYNC, 30)
        scheduler.add_job(config)
        
        job_id = f"{config.job_type.value}_{config.interval_minutes}min"
        assert job_id in scheduler.jobs
        
        scheduler.remove_job(job_id)
        assert job_id not in scheduler.jobs
    
    def test_get_job_status(self, scheduler):
        """Job státusz lekérése tesztelése"""
        status = scheduler.get_job_status()
        
        assert "running_jobs" in status
        assert "total_jobs" in status
        assert "enabled_jobs" in status
        assert "job_history_count" in status
        assert "last_jobs" in status
        
        assert isinstance(status["running_jobs"], list)
        assert isinstance(status["total_jobs"], int)
        assert isinstance(status["enabled_jobs"], int)
    
    def test_get_job_statistics(self, scheduler):
        """Job statisztikák tesztelése"""
        stats = scheduler.get_job_statistics()
        
        assert "total_jobs" in stats
        assert "success_rate" in stats
        
        # Kezdetben nincs job history
        assert stats["total_jobs"] == 0
        assert stats["success_rate"] == 0


class TestConflictResolver:
    """Konfliktus feloldó tesztelése"""
    
    @pytest.fixture
    def resolver(self):
        """Conflict resolver fixture"""
        return ConflictResolver()
    
    @pytest.fixture
    def mock_products(self):
        """Mock termékek fixture"""
        from src.models.product import Product, ProductCategory
        
        local_product = Product(
            id="1001",
            name="Test Product Local",
            description="Local test product",
            price=100.0,
            original_price=120.0,
            category_id="Elektronika",
            stock_quantity=50,
            sku="SKU-1001",
            images=[],
            tags=[],
            created_at=datetime.now() - timedelta(days=1),
            updated_at=datetime.now() - timedelta(hours=1)
        )
        
        remote_product = Product(
            id="1001",
            name="Test Product Remote",
            description="Remote test product",
            price=110.0,
            original_price=130.0,
            category_id="Elektronika",
            stock_quantity=45,
            sku="SKU-1001",
            images=[],
            tags=[],
            created_at=datetime.now() - timedelta(days=1),
            updated_at=datetime.now()
        )
        
        return local_product, remote_product
    
    def test_detect_price_conflict(self, resolver, mock_products):
        """Ár konfliktus felismerés tesztelése"""
        local_product, remote_product = mock_products
        
        conflict = resolver.detect_price_conflict(local_product, remote_product)
        
        assert conflict is not None
        assert conflict.conflict_type == ConflictType.PRICE_CONFLICT
        assert conflict.local_data["price"] == 100.0
        assert conflict.remote_data["price"] == 110.0
        assert conflict.severity == "high"
    
    def test_detect_stock_conflict(self, resolver, mock_products):
        """Készlet konfliktus felismerés tesztelése"""
        local_product, remote_product = mock_products
        
        # Módosítjuk a készletet, hogy konfliktus legyen
        local_product.stock_quantity = 50
        remote_product.stock_quantity = 30  # Nagyobb különbség
        
        conflict = resolver.detect_stock_conflict(local_product, remote_product)
        
        assert conflict is not None
        assert conflict.conflict_type == ConflictType.STOCK_CONFLICT
        assert conflict.local_data["stock"] == 50
        assert conflict.remote_data["stock"] == 30
        assert conflict.severity == "medium"
    
    def test_detect_duplicate_product(self, resolver):
        """Duplikált termék felismerés tesztelése"""
        from src.models.product import Product, ProductCategory
        
        products = [
            Product(
                id="1001", name="Product 1", description="", price=100.0,
                original_price=100.0, category_id="Elektronika",
                stock_quantity=10, sku="SKU-1001", images=[], tags=[],
                created_at=datetime.now(), updated_at=datetime.now()
            ),
            Product(
                id="1002", name="Product 2", description="", price=200.0,
                original_price=200.0, category_id="Elektronika",
                stock_quantity=20, sku="SKU-1001", images=[], tags=[],
                created_at=datetime.now(), updated_at=datetime.now()
            )
        ]
        
        conflicts = resolver.detect_duplicate_product(products)
        
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == ConflictType.DUPLICATE_PRODUCT
        assert conflicts[0].description == "Duplikált SKU: SKU-1001"
    
    def test_resolve_conflict(self, resolver, mock_products):
        """Konfliktus feloldás tesztelése"""
        local_product, remote_product = mock_products
        
        conflict = resolver.detect_price_conflict(local_product, remote_product)
        resolution = resolver.resolve_conflict(conflict)
        
        assert "conflict_id" in resolution
        assert "conflict_type" in resolution
        assert "resolution_strategy" in resolution
        assert "resolved_at" in resolution
        assert "resolution_data" in resolution
        
        assert resolution["conflict_type"] == "price_conflict"
        assert resolution["resolution_strategy"] == "keep_remote"
    
    def test_get_conflict_statistics(self, resolver, mock_products):
        """Konfliktus statisztikák tesztelése"""
        local_product, remote_product = mock_products
        
        # Módosítjuk a készletet, hogy konfliktus legyen
        local_product.stock_quantity = 50
        remote_product.stock_quantity = 30
        
        # Néhány konfliktus létrehozása
        conflict1 = resolver.detect_price_conflict(local_product, remote_product)
        conflict2 = resolver.detect_stock_conflict(local_product, remote_product)
        
        resolver.resolve_conflict(conflict1)
        resolver.resolve_conflict(conflict2)
        
        stats = resolver.get_conflict_statistics()
        
        assert "total_conflicts" in stats
        assert "resolved_conflicts" in stats
        assert "unresolved_conflicts" in stats
        assert "conflict_types" in stats
        assert "resolution_rate" in stats
        
        assert stats["total_conflicts"] == 2
        assert stats["resolved_conflicts"] == 2
        assert stats["unresolved_conflicts"] == 0
        assert stats["resolution_rate"] == 100.0


class TestConflictMonitor:
    """Konfliktus monitor tesztelése"""
    
    @pytest.fixture
    def monitor(self):
        """Conflict monitor fixture"""
        resolver = ConflictResolver()
        return ConflictMonitor(resolver)
    
    @pytest.mark.asyncio
    async def test_monitor_sync_operation(self, monitor):
        """Szinkronizációs művelet monitorozás tesztelése"""
        from src.models.product import Product, ProductCategory
        
        local_products = [
            Product(
                id="1001", name="Local Product", description="", price=100.0,
                original_price=100.0, category_id="Elektronika",
                stock_quantity=50, sku="SKU-1001", images=[], tags=[],
                created_at=datetime.now(), updated_at=datetime.now()
            )
        ]
        
        remote_products = [
            Product(
                id="1001", name="Remote Product", description="", price=110.0,
                original_price=110.0, category_id="Elektronika",
                stock_quantity=45, sku="SKU-1001", images=[], tags=[],
                created_at=datetime.now(), updated_at=datetime.now()
            )
        ]
        
        result = await monitor.monitor_sync_operation(local_products, remote_products)
        
        assert "conflicts_detected" in result
        assert "conflicts_resolved" in result
        assert "alert_triggered" in result
        assert "conflict_types" in result
        assert "resolutions" in result
        
        assert result["conflicts_detected"] > 0
        assert result["conflicts_resolved"] > 0


class TestRealTimeSyncManager:
    """Valós idejű szinkronizációs menedzser tesztelése"""
    
    @pytest.fixture
    def realtime_manager(self):
        """Real-time sync manager fixture"""
        generator = MockDataGenerator()
        sync_manager = MockSyncManager(generator)
        return RealTimeSyncManager(sync_manager)
    
    @pytest.mark.asyncio
    async def test_queue_event(self, realtime_manager):
        """Esemény sorba állítás tesztelése"""
        event = MockEvent(
            event_type=MockEventType.PRODUCT_UPDATED,
            timestamp=datetime.now(),
            data={"product_id": 1001}
        )
        
        await realtime_manager.queue_event(event)
        
        assert realtime_manager.event_queue.qsize() == 1
    
    def test_add_event_handler(self, realtime_manager):
        """Event handler hozzáadás tesztelése"""
        def test_handler(event):
            pass
        
        realtime_manager.add_event_handler(MockEventType.PRODUCT_UPDATED, test_handler)
        
        assert MockEventType.PRODUCT_UPDATED in realtime_manager.event_handlers
        assert len(realtime_manager.event_handlers[MockEventType.PRODUCT_UPDATED]) == 1
    
    def test_get_queue_status(self, realtime_manager):
        """Sor státusz lekérése tesztelése"""
        status = realtime_manager.get_queue_status()
        
        assert "queue_size" in status
        assert "registered_handlers" in status
        
        assert isinstance(status["queue_size"], int)
        assert isinstance(status["registered_handlers"], dict)


class TestIntegration:
    """Integrációs tesztelés"""
    
    @pytest.mark.asyncio
    async def test_full_sync_workflow(self):
        """Teljes szinkronizációs workflow tesztelése"""
        # Mock adat generátor
        generator = MockDataGenerator()
        
        # Sync manager
        sync_manager = MockSyncManager(generator)
        
        # Conflict resolver
        resolver = ConflictResolver()
        
        # Scheduler
        scheduler = SyncScheduler(sync_manager)
        
        # Termékek szinkronizálása
        sync_result = await sync_manager.sync_products()
        assert sync_result["products_synced"] > 0
        
        # Készlet frissítések
        inventory_result = await sync_manager.sync_inventory()
        assert inventory_result["total_updates"] > 0
        
        # Ár változások
        price_result = await sync_manager.sync_prices()
        assert price_result["total_updates"] > 0
        
        # Statisztikák
        sync_stats = sync_manager.get_sync_statistics()
        assert sync_stats["total_syncs"] > 0
        
        job_stats = scheduler.get_job_statistics()
        assert "total_jobs" in job_stats
        
        conflict_stats = resolver.get_conflict_statistics()
        assert "total_conflicts" in conflict_stats
        
        print(f"✅ Teljes workflow teszt sikeres:")
        print(f"   - Szinkronizált termékek: {sync_result['products_synced']}")
        print(f"   - Készlet frissítések: {inventory_result['total_updates']}")
        print(f"   - Ár frissítések: {price_result['total_updates']}")
        print(f"   - Szinkronizálások: {sync_stats['total_syncs']}")
        print(f"   - Konfliktusok: {conflict_stats['total_conflicts']}")


if __name__ == "__main__":
    # Futtatás: python -m pytest tests/test_product_sync_mock.py -v
    pytest.main([__file__, "-v"]) 