"""
Scheduled sync jobs a termékadat szinkronizációhoz.
Mock alapú implementáció valós webshop nélkül.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from .mock_data_generator import MockDataGenerator, MockSyncManager, MockEvent, MockEventType

logger = logging.getLogger(__name__)


class SyncJobType(Enum):
    """Szinkronizációs job típusok"""
    PRODUCT_SYNC = "product_sync"
    INVENTORY_SYNC = "inventory_sync"
    PRICE_SYNC = "price_sync"
    ORDER_SYNC = "order_sync"
    FULL_SYNC = "full_sync"


@dataclass
class SyncJobConfig:
    """Szinkronizációs job konfiguráció"""
    job_type: SyncJobType
    interval_minutes: int
    enabled: bool = True
    retry_count: int = 3
    retry_delay_seconds: int = 60
    max_execution_time: int = 300  # 5 perc


class SyncScheduler:
    """Szinkronizációs job scheduler"""
    
    def __init__(self, sync_manager: MockSyncManager):
        self.sync_manager = sync_manager
        self.jobs: Dict[str, SyncJobConfig] = {}
        self.running_jobs: Dict[str, asyncio.Task] = {}
        self.job_history: List[Dict] = []
        self.event_handlers: List[Callable] = []
        
        # Alapértelmezett job konfigurációk
        self._setup_default_jobs()
    
    def _setup_default_jobs(self):
        """Alapértelmezett job-ok beállítása"""
        default_jobs = [
            SyncJobConfig(SyncJobType.PRODUCT_SYNC, 60),      # Óránként
            SyncJobConfig(SyncJobType.INVENTORY_SYNC, 15),    # 15 percenként
            SyncJobConfig(SyncJobType.PRICE_SYNC, 30),        # 30 percenként
            SyncJobConfig(SyncJobType.ORDER_SYNC, 10),        # 10 percenként
            SyncJobConfig(SyncJobType.FULL_SYNC, 1440),       # Naponta
        ]
        
        for job_config in default_jobs:
            self.add_job(job_config)
    
    def add_job(self, config: SyncJobConfig):
        """Új job hozzáadása"""
        job_id = f"{config.job_type.value}_{config.interval_minutes}min"
        self.jobs[job_id] = config
        logger.info(f"Job hozzáadva: {job_id}")
    
    def remove_job(self, job_id: str):
        """Job eltávolítása"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            logger.info(f"Job eltávolítva: {job_id}")
    
    def start_all_jobs(self):
        """Összes job indítása"""
        for job_id, config in self.jobs.items():
            if config.enabled:
                self._start_job(job_id, config)
    
    def stop_all_jobs(self):
        """Összes job leállítása"""
        for job_id in list(self.running_jobs.keys()):
            self._stop_job(job_id)
    
    def _start_job(self, job_id: str, config: SyncJobConfig):
        """Egy job indítása"""
        if job_id in self.running_jobs:
            logger.warning(f"Job már fut: {job_id}")
            return
        
        task = asyncio.create_task(self._run_job_loop(job_id, config))
        self.running_jobs[job_id] = task
        logger.info(f"Job elindítva: {job_id}")
    
    def _stop_job(self, job_id: str):
        """Egy job leállítása"""
        if job_id in self.running_jobs:
            task = self.running_jobs[job_id]
            task.cancel()
            del self.running_jobs[job_id]
            logger.info(f"Job leállítva: {job_id}")
    
    async def _run_job_loop(self, job_id: str, config: SyncJobConfig):
        """Job loop futtatása"""
        while True:
            try:
                start_time = datetime.now()
                
                # Job végrehajtása
                result = await self._execute_job(config.job_type)
                
                # Eredmény rögzítése
                execution_time = (datetime.now() - start_time).total_seconds()
                job_result = {
                    "job_id": job_id,
                    "job_type": config.job_type.value,
                    "start_time": start_time,
                    "end_time": datetime.now(),
                    "execution_time": execution_time,
                    "success": True,
                    "result": result,
                    "error": None
                }
                
                self.job_history.append(job_result)
                logger.info(f"Job sikeres: {job_id} ({execution_time:.2f}s)")
                
                # Event handler-ek hívása
                await self._notify_event_handlers(job_result)
                
            except asyncio.CancelledError:
                logger.info(f"Job megszakítva: {job_id}")
                break
            except Exception as e:
                logger.error(f"Job hiba: {job_id} - {e}")
                
                # Retry logika
                for attempt in range(config.retry_count):
                    try:
                        await asyncio.sleep(config.retry_delay_seconds)
                        result = await self._execute_job(config.job_type)
                        logger.info(f"Job retry sikeres: {job_id} (attempt {attempt + 1})")
                        break
                    except Exception as retry_error:
                        logger.error(f"Job retry hiba: {job_id} (attempt {attempt + 1}) - {retry_error}")
                else:
                    logger.error(f"Job végleges hiba: {job_id}")
            
            # Várakozás a következő futtatásig
            await asyncio.sleep(config.interval_minutes * 60)
    
    async def _execute_job(self, job_type: SyncJobType) -> Dict:
        """Job végrehajtása típus szerint"""
        if job_type == SyncJobType.PRODUCT_SYNC:
            return await self.sync_manager.sync_products()
        elif job_type == SyncJobType.INVENTORY_SYNC:
            return await self.sync_manager.sync_inventory()
        elif job_type == SyncJobType.PRICE_SYNC:
            return await self.sync_manager.sync_prices()
        elif job_type == SyncJobType.ORDER_SYNC:
            return await self.sync_manager.sync_orders()
        elif job_type == SyncJobType.FULL_SYNC:
            return await self._execute_full_sync()
        else:
            raise ValueError(f"Ismeretlen job típus: {job_type}")
    
    async def _execute_full_sync(self) -> Dict:
        """Teljes szinkronizáció végrehajtása"""
        results = {}
        
        # Termékek szinkronizálása
        results["products"] = await self.sync_manager.sync_products()
        
        # Készlet frissítések
        results["inventory"] = await self.sync_manager.sync_inventory()
        
        # Ár változások
        results["prices"] = await self.sync_manager.sync_prices()
        
        # Rendelések
        results["orders"] = await self.sync_manager.sync_orders()
        
        return {
            "timestamp": datetime.now(),
            "full_sync_completed": True,
            "results": results
        }
    
    def add_event_handler(self, handler: Callable):
        """Event handler hozzáadása"""
        self.event_handlers.append(handler)
    
    async def _notify_event_handlers(self, job_result: Dict):
        """Event handler-ek értesítése"""
        for handler in self.event_handlers:
            try:
                await handler(job_result)
            except Exception as e:
                logger.error(f"Event handler hiba: {e}")
    
    def get_job_status(self) -> Dict:
        """Job státusz lekérése"""
        return {
            "running_jobs": list(self.running_jobs.keys()),
            "total_jobs": len(self.jobs),
            "enabled_jobs": len([j for j in self.jobs.values() if j.enabled]),
            "job_history_count": len(self.job_history),
            "last_jobs": self.job_history[-5:] if self.job_history else []
        }
    
    def get_job_statistics(self) -> Dict:
        """Job statisztikák"""
        if not self.job_history:
            return {"total_jobs": 0, "success_rate": 0}
        
        total_jobs = len(self.job_history)
        successful_jobs = len([j for j in self.job_history if j["success"]])
        success_rate = (successful_jobs / total_jobs) * 100
        
        avg_execution_time = sum(j["execution_time"] for j in self.job_history) / total_jobs
        
        return {
            "total_jobs": total_jobs,
            "successful_jobs": successful_jobs,
            "failed_jobs": total_jobs - successful_jobs,
            "success_rate": round(success_rate, 2),
            "average_execution_time": round(avg_execution_time, 2)
        }


class RealTimeSyncManager:
    """Valós idejű szinkronizációs menedzser"""
    
    def __init__(self, sync_manager: MockSyncManager):
        self.sync_manager = sync_manager
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None
        self.event_handlers: Dict[MockEventType, List[Callable]] = {}
        
    async def start(self):
        """Valós idejű feldolgozás indítása"""
        self.processing_task = asyncio.create_task(self._process_events())
        logger.info("Valós idejű szinkronizáció elindítva")
    
    async def stop(self):
        """Valós idejű feldolgozás leállítása"""
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        logger.info("Valós idejű szinkronizáció leállítva")
    
    async def _process_events(self):
        """Események feldolgozása"""
        while True:
            try:
                event = await self.event_queue.get()
                await self._handle_event(event)
                self.event_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Esemény feldolgozási hiba: {e}")
    
    async def _handle_event(self, event: MockEvent):
        """Egy esemény kezelése"""
        handlers = self.event_handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Event handler hiba: {e}")
    
    def add_event_handler(self, event_type: MockEventType, handler: Callable):
        """Event handler hozzáadása"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def queue_event(self, event: MockEvent):
        """Esemény sorba állítása"""
        await self.event_queue.put(event)
    
    def get_queue_status(self) -> Dict:
        """Sor státusz lekérése"""
        return {
            "queue_size": self.event_queue.qsize(),
            "registered_handlers": {
                event_type.value: len(handlers)
                for event_type, handlers in self.event_handlers.items()
            }
        }


# Singleton instances
mock_sync_manager = MockSyncManager(MockDataGenerator())
sync_scheduler = SyncScheduler(mock_sync_manager)
realtime_sync_manager = RealTimeSyncManager(mock_sync_manager) 