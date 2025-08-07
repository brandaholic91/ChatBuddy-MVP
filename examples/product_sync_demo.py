"""
Demonstráció a termékadat szinkronizáció mock implementációjához.
Ez a fájl bemutatja, hogyan lehet valós webshop nélkül fejleszteni a szinkronizációt.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.integrations.webshop.mock_data_generator import (
    MockDataGenerator, MockSyncManager, MockEvent, MockEventType
)
from src.integrations.webshop.sync_scheduler import (
    SyncScheduler, SyncJobType, SyncJobConfig, RealTimeSyncManager
)
from src.integrations.webshop.conflict_resolver import (
    ConflictResolver, ConflictType, ResolutionStrategy, ConflictMonitor
)


# Logging beállítása
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductSyncDemo:
    """Termékadat szinkronizáció demonstráció"""
    
    def __init__(self):
        # Mock komponensek inicializálása
        self.data_generator = MockDataGenerator()
        self.sync_manager = MockSyncManager(self.data_generator)
        self.scheduler = SyncScheduler(self.sync_manager)
        self.conflict_resolver = ConflictResolver()
        self.conflict_monitor = ConflictMonitor(self.conflict_resolver)
        self.realtime_manager = RealTimeSyncManager(self.sync_manager)
        
        # Event handler-ek beállítása
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Event handler-ek beállítása"""
        
        async def on_sync_completed(job_result: Dict):
            """Szinkronizációs job befejezés esemény"""
            logger.info(f"✅ Szinkronizáció befejezve: {job_result['job_type']}")
            logger.info(f"   - Végrehajtási idő: {job_result['execution_time']:.2f}s")
            logger.info(f"   - Eredmény: {job_result['result']}")
        
        async def on_product_updated(event: MockEvent):
            """Termék frissítés esemény"""
            logger.info(f"🔄 Termék frissítve: {event.data.get('product_id')}")
        
        async def on_inventory_changed(event: MockEvent):
            """Készlet változás esemény"""
            logger.info(f"📦 Készlet változás: {event.data.get('product_id')}")
            logger.info(f"   - Régi készlet: {event.data.get('old_stock')}")
            logger.info(f"   - Új készlet: {event.data.get('new_stock')}")
        
        async def on_price_changed(event: MockEvent):
            """Ár változás esemény"""
            logger.info(f"💰 Ár változás: {event.data.get('product_id')}")
            logger.info(f"   - Régi ár: {event.data.get('old_price')}")
            logger.info(f"   - Új ár: {event.data.get('new_price')}")
        
        # Event handler-ek regisztrálása
        self.scheduler.add_event_handler(on_sync_completed)
        self.realtime_manager.add_event_handler(MockEventType.PRODUCT_UPDATED, on_product_updated)
        self.realtime_manager.add_event_handler(MockEventType.INVENTORY_CHANGED, on_inventory_changed)
        self.realtime_manager.add_event_handler(MockEventType.PRICE_CHANGED, on_price_changed)
    
    async def demo_basic_sync(self):
        """Alapvető szinkronizáció demonstráció"""
        logger.info("🚀 Alapvető szinkronizáció demonstráció")
        logger.info("=" * 50)
        
        # Termékek szinkronizálása
        logger.info("📋 Termékek szinkronizálása...")
        sync_result = await self.sync_manager.sync_products()
        logger.info(f"   - Szinkronizált termékek: {sync_result['products_synced']}")
        logger.info(f"   - Új termékek: {sync_result['new_products']}")
        logger.info(f"   - Frissített termékek: {sync_result['updated_products']}")
        logger.info(f"   - Törölt termékek: {sync_result['deleted_products']}")
        
        # Készlet frissítések
        logger.info("\n📦 Készlet frissítések...")
        inventory_result = await self.sync_manager.sync_inventory()
        logger.info(f"   - Frissítések száma: {inventory_result['total_updates']}")
        
        for update in inventory_result['inventory_updates'][:3]:  # Csak az első 3
            logger.info(f"   - Termék {update['product_id']}: {update['old_stock']} → {update['new_stock']}")
        
        # Ár változások
        logger.info("\n💰 Ár változások...")
        price_result = await self.sync_manager.sync_prices()
        logger.info(f"   - Frissítések száma: {price_result['total_updates']}")
        
        for update in price_result['price_updates'][:3]:  # Csak az első 3
            logger.info(f"   - Termék {update['product_id']}: {update['old_price']} → {update['new_price']} ({update['change_percentage']}%)")
        
        # Statisztikák
        logger.info("\n📊 Szinkronizációs statisztikák...")
        stats = self.sync_manager.get_sync_statistics()
        logger.info(f"   - Összes szinkronizáció: {stats['total_syncs']}")
        logger.info(f"   - Átlagos termékek/szinkronizáció: {stats['average_products_per_sync']:.1f}")
        logger.info(f"   - Összes hiba: {stats['total_errors']}")
    
    async def demo_conflict_resolution(self):
        """Konfliktus feloldás demonstráció"""
        logger.info("\n🔧 Konfliktus feloldás demonstráció")
        logger.info("=" * 50)
        
        # Mock termékek generálása konfliktusokkal
        local_products = self.data_generator.generate_mock_products(5)
        remote_products = self.data_generator.generate_mock_products(5)
        
        # Konfliktusok felismerése és feloldása
        logger.info("🔍 Konfliktusok felismerése...")
        monitor_result = await self.conflict_monitor.monitor_sync_operation(local_products, remote_products)
        
        logger.info(f"   - Felismert konfliktusok: {monitor_result['conflicts_detected']}")
        logger.info(f"   - Feloldott konfliktusok: {monitor_result['conflicts_resolved']}")
        logger.info(f"   - Konfliktus típusok: {', '.join(monitor_result['conflict_types'])}")
        
        if monitor_result['alert_triggered']:
            logger.warning("   ⚠️  Riasztás aktiválva!")
        
        # Konfliktus statisztikák
        logger.info("\n📈 Konfliktus statisztikák...")
        conflict_stats = self.conflict_resolver.get_conflict_statistics()
        logger.info(f"   - Összes konfliktus: {conflict_stats['total_conflicts']}")
        logger.info(f"   - Feloldott konfliktusok: {conflict_stats['resolved_conflicts']}")
        logger.info(f"   - Feloldási ráta: {conflict_stats['resolution_rate']}%")
        
        # Konfliktus típusok eloszlása
        for conflict_type, count in conflict_stats['conflict_types'].items():
            logger.info(f"   - {conflict_type}: {count}")
    
    async def demo_scheduled_jobs(self):
        """Időzített job-ok demonstráció"""
        logger.info("\n⏰ Időzített job-ok demonstráció")
        logger.info("=" * 50)
        
        # Job státusz
        logger.info("📋 Job státusz...")
        job_status = self.scheduler.get_job_status()
        logger.info(f"   - Összes job: {job_status['total_jobs']}")
        logger.info(f"   - Engedélyezett job-ok: {job_status['enabled_jobs']}")
        logger.info(f"   - Futó job-ok: {len(job_status['running_jobs'])}")
        
        # Job statisztikák
        logger.info("\n📊 Job statisztikák...")
        job_stats = self.scheduler.get_job_statistics()
        logger.info(f"   - Összes job: {job_stats['total_jobs']}")
        logger.info(f"   - Sikereségi ráta: {job_stats['success_rate']}%")
        if 'average_execution_time' in job_stats:
            logger.info(f"   - Átlagos végrehajtási idő: {job_stats['average_execution_time']:.2f}s")
        
        # Új job hozzáadása
        logger.info("\n➕ Új job hozzáadása...")
        custom_job = SyncJobConfig(SyncJobType.PRODUCT_SYNC, 5)  # 5 percenként
        self.scheduler.add_job(custom_job)
        logger.info(f"   - Új job hozzáadva: {custom_job.job_type.value} ({custom_job.interval_minutes} percenként)")
    
    async def demo_realtime_sync(self):
        """Valós idejű szinkronizáció demonstráció"""
        logger.info("\n⚡ Valós idejű szinkronizáció demonstráció")
        logger.info("=" * 50)
        
        # Real-time manager indítása
        await self.realtime_manager.start()
        logger.info("✅ Valós idejű szinkronizáció elindítva")
        
        # Néhány esemény generálása
        logger.info("🔄 Események generálása...")
        
        events = [
            MockEvent(MockEventType.PRODUCT_UPDATED, datetime.now(), {"product_id": 1001}),
            MockEvent(MockEventType.INVENTORY_CHANGED, datetime.now(), {
                "product_id": 1002, "old_stock": 50, "new_stock": 45
            }),
            MockEvent(MockEventType.PRICE_CHANGED, datetime.now(), {
                "product_id": 1003, "old_price": 100.0, "new_price": 95.0
            }),
            MockEvent(MockEventType.ORDER_CREATED, datetime.now(), {"order_id": 5001}),
            MockEvent(MockEventType.PRODUCT_CREATED, datetime.now(), {"product_id": 1004})
        ]
        
        # Események sorba állítása
        for event in events:
            await self.realtime_manager.queue_event(event)
            await asyncio.sleep(0.5)  # Rövid várakozás
        
        # Sor státusz
        logger.info("\n📊 Real-time sor státusz...")
        queue_status = self.realtime_manager.get_queue_status()
        logger.info(f"   - Sor méret: {queue_status['queue_size']}")
        logger.info(f"   - Regisztrált handler-ek: {queue_status['registered_handlers']}")
        
        # Várakozás az események feldolgozására
        await asyncio.sleep(2)
        
        # Real-time manager leállítása
        await self.realtime_manager.stop()
        logger.info("✅ Valós idejű szinkronizáció leállítva")
    
    async def demo_advanced_features(self):
        """Fejlett funkciók demonstráció"""
        logger.info("\n🚀 Fejlett funkciók demonstráció")
        logger.info("=" * 50)
        
        # Konfliktus feloldási szabályok testreszabása
        logger.info("⚙️  Konfliktus feloldási szabályok testreszabása...")
        self.conflict_resolver.set_resolution_rule(ConflictType.PRICE_CONFLICT, ResolutionStrategy.KEEP_LOCAL)
        self.conflict_resolver.set_resolution_rule(ConflictType.STOCK_CONFLICT, ResolutionStrategy.MERGE)
        logger.info("   - Ár konfliktusok: helyi adat megtartása")
        logger.info("   - Készlet konfliktusok: adatok összevonása")
        
        # Automatikus feloldás be/kikapcsolása
        logger.info("\n🤖 Automatikus feloldás beállítása...")
        self.conflict_resolver.enable_auto_resolve(True)
        logger.info("   - Automatikus feloldás: bekapcsolva")
        
        # Mock adatok generálása
        logger.info("\n🎲 Mock adatok generálása...")
        products = self.data_generator.generate_mock_products(10)
        events = self.data_generator.generate_mock_events(5)
        
        logger.info(f"   - Generált termékek: {len(products)}")
        logger.info(f"   - Generált események: {len(events)}")
        
        # Termékek megjelenítése
        logger.info("\n📋 Generált termékek (első 3):")
        for i, product in enumerate(products[:3]):
            logger.info(f"   {i+1}. {product.name}")
            logger.info(f"      - Ár: {product.price} Ft")
            logger.info(f"      - Készlet: {product.stock_quantity} db")
            logger.info(f"      - Kategória: {product.category_id}")
        
        # Események megjelenítése
        logger.info("\n📅 Generált események:")
        for i, event in enumerate(events[:3]):
            logger.info(f"   {i+1}. {event.event_type.value} - {event.timestamp.strftime('%H:%M:%S')}")
            logger.info(f"      - Adatok: {event.data}")
    
    async def run_full_demo(self):
        """Teljes demonstráció futtatása"""
        logger.info("🎬 TERMÉKADAT SZINKRONIZÁCIÓ MOCK DEMONSTRÁCIÓ")
        logger.info("=" * 60)
        logger.info("Ez a demonstráció bemutatja, hogyan lehet valós webshop nélkül")
        logger.info("fejleszteni a termékadat szinkronizációt mock adatokkal és eseményekkel.")
        logger.info("=" * 60)
        
        try:
            # Alapvető szinkronizáció
            await self.demo_basic_sync()
            
            # Konfliktus feloldás
            await self.demo_conflict_resolution()
            
            # Időzített job-ok
            await self.demo_scheduled_jobs()
            
            # Valós idejű szinkronizáció
            await self.demo_realtime_sync()
            
            # Fejlett funkciók
            await self.demo_advanced_features()
            
            logger.info("\n🎉 DEMONSTRÁCIÓ SIKERESEN BEFEJEZVE!")
            logger.info("=" * 60)
            logger.info("✅ Minden funkció működik mock adatokkal")
            logger.info("✅ Konfliktus feloldás implementálva")
            logger.info("✅ Időzített job-ok működnek")
            logger.info("✅ Valós idejű események kezelhetők")
            logger.info("✅ Tesztelés és fejlesztés lehetséges valós webshop nélkül")
            
        except Exception as e:
            logger.error(f"❌ Demonstráció hiba: {e}")
            raise


async def main():
    """Fő függvény"""
    demo = ProductSyncDemo()
    await demo.run_full_demo()


if __name__ == "__main__":
    # Futtatás: python examples/product_sync_demo.py
    asyncio.run(main()) 