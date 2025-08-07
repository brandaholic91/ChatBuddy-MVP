"""
Conflict resolution rendszer a termékadat szinkronizációhoz.
Mock alapú implementáció valós webshop nélkül.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from src.models.product import Product
from src.models.order import Order

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Konfliktus típusok"""
    PRICE_CONFLICT = "price_conflict"
    STOCK_CONFLICT = "stock_conflict"
    PRODUCT_DELETED = "product_deleted"
    DUPLICATE_PRODUCT = "duplicate_product"
    CATEGORY_MISMATCH = "category_mismatch"
    DATA_INTEGRITY = "data_integrity"


class ResolutionStrategy(Enum):
    """Konfliktus feloldási stratégiák"""
    KEEP_LOCAL = "keep_local"
    KEEP_REMOTE = "keep_remote"
    MERGE = "merge"
    MANUAL_REVIEW = "manual_review"
    AUTO_RESOLVE = "auto_resolve"


@dataclass
class Conflict:
    """Konfliktus adatstruktúra"""
    conflict_type: ConflictType
    local_data: Dict
    remote_data: Dict
    timestamp: datetime
    severity: str = "medium"  # low, medium, high, critical
    description: str = ""
    resolution_strategy: Optional[ResolutionStrategy] = None


class ConflictResolver:
    """Konfliktus feloldó rendszer"""
    
    def __init__(self):
        self.conflict_history: List[Conflict] = []
        self.resolution_rules: Dict[ConflictType, ResolutionStrategy] = {}
        self.auto_resolve_enabled = True
        
        # Alapértelmezett feloldási szabályok
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Alapértelmezett feloldási szabályok beállítása"""
        self.resolution_rules = {
            ConflictType.PRICE_CONFLICT: ResolutionStrategy.KEEP_REMOTE,
            ConflictType.STOCK_CONFLICT: ResolutionStrategy.MERGE,
            ConflictType.PRODUCT_DELETED: ResolutionStrategy.MANUAL_REVIEW,
            ConflictType.DUPLICATE_PRODUCT: ResolutionStrategy.AUTO_RESOLVE,
            ConflictType.CATEGORY_MISMATCH: ResolutionStrategy.KEEP_REMOTE,
            ConflictType.DATA_INTEGRITY: ResolutionStrategy.MANUAL_REVIEW
        }
    
    def detect_price_conflict(self, local_product: Product, remote_product: Product) -> Optional[Conflict]:
        """Ár konfliktus felismerése"""
        if abs(local_product.price - remote_product.price) > 0.01:
            return Conflict(
                conflict_type=ConflictType.PRICE_CONFLICT,
                local_data={"price": local_product.price, "updated_at": local_product.updated_at},
                remote_data={"price": remote_product.price, "updated_at": remote_product.updated_at},
                timestamp=datetime.now(),
                severity="high",
                description=f"Ár eltérés: helyi {local_product.price} vs távoli {remote_product.price}"
            )
        return None
    
    def detect_stock_conflict(self, local_product: Product, remote_product: Product) -> Optional[Conflict]:
        """Készlet konfliktus felismerése"""
        stock_diff = abs(local_product.stock_quantity - remote_product.stock_quantity)
        if stock_diff > 5:  # 5-nél nagyobb eltérés
            return Conflict(
                conflict_type=ConflictType.STOCK_CONFLICT,
                local_data={"stock": local_product.stock_quantity, "updated_at": local_product.updated_at},
                remote_data={"stock": remote_product.stock_quantity, "updated_at": remote_product.updated_at},
                timestamp=datetime.now(),
                severity="medium",
                description=f"Készlet eltérés: helyi {local_product.stock_quantity} vs távoli {remote_product.stock_quantity}"
            )
        return None
    
    def detect_duplicate_product(self, products: List[Product]) -> List[Conflict]:
        """Duplikált termékek felismerése"""
        conflicts = []
        seen_skus = {}
        
        for product in products:
            if product.sku in seen_skus:
                conflicts.append(Conflict(
                    conflict_type=ConflictType.DUPLICATE_PRODUCT,
                    local_data={"sku": product.sku, "id": product.id},
                    remote_data={"sku": seen_skus[product.sku].sku, "id": seen_skus[product.sku].id},
                    timestamp=datetime.now(),
                    severity="medium",
                    description=f"Duplikált SKU: {product.sku}"
                ))
            else:
                seen_skus[product.sku] = product
        
        return conflicts
    
    def detect_category_mismatch(self, local_product: Product, remote_product: Product) -> Optional[Conflict]:
        """Kategória eltérés felismerése"""
        if local_product.category_id != remote_product.category_id:
            return Conflict(
                conflict_type=ConflictType.CATEGORY_MISMATCH,
                local_data={"category": local_product.category_id},
                remote_data={"category": remote_product.category_id},
                timestamp=datetime.now(),
                severity="low",
                description=f"Kategória eltérés: helyi {local_product.category_id} vs távoli {remote_product.category_id}"
            )
        return None
    
    def detect_data_integrity_issues(self, product: Product) -> List[Conflict]:
        """Adat integritási problémák felismerése"""
        conflicts = []
        
        # Ár ellenőrzés
        if product.price <= 0:
            conflicts.append(Conflict(
                conflict_type=ConflictType.DATA_INTEGRITY,
                local_data={"price": product.price},
                remote_data={},
                timestamp=datetime.now(),
                severity="high",
                description="Érvénytelen ár: 0 vagy negatív"
            ))
        
        # Készlet ellenőrzés
        if product.stock_quantity < 0:
            conflicts.append(Conflict(
                conflict_type=ConflictType.DATA_INTEGRITY,
                local_data={"stock": product.stock_quantity},
                remote_data={},
                timestamp=datetime.now(),
                severity="medium",
                description="Érvénytelen készlet: negatív érték"
            ))
        
        # Név ellenőrzés
        if not product.name or len(product.name.strip()) < 2:
            conflicts.append(Conflict(
                conflict_type=ConflictType.DATA_INTEGRITY,
                local_data={"name": product.name},
                remote_data={},
                timestamp=datetime.now(),
                severity="high",
                description="Érvénytelen terméknév: túl rövid vagy üres"
            ))
        
        return conflicts
    
    def resolve_conflict(self, conflict: Conflict) -> Dict:
        """Konfliktus feloldása"""
        strategy = conflict.resolution_strategy or self.resolution_rules.get(conflict.conflict_type)
        
        if not strategy:
            strategy = ResolutionStrategy.MANUAL_REVIEW
        
        resolution_result = {
            "conflict_id": len(self.conflict_history),
            "conflict_type": conflict.conflict_type.value,
            "resolution_strategy": strategy.value,
            "resolved_at": datetime.now(),
            "resolution_data": {}
        }
        
        if strategy == ResolutionStrategy.KEEP_LOCAL:
            resolution_result["resolution_data"] = conflict.local_data
            logger.info(f"Konfliktus feloldva: helyi adat megtartva ({conflict.conflict_type.value})")
        
        elif strategy == ResolutionStrategy.KEEP_REMOTE:
            resolution_result["resolution_data"] = conflict.remote_data
            logger.info(f"Konfliktus feloldva: távoli adat megtartva ({conflict.conflict_type.value})")
        
        elif strategy == ResolutionStrategy.MERGE:
            resolution_result["resolution_data"] = self._merge_data(conflict)
            logger.info(f"Konfliktus feloldva: adatok összevonva ({conflict.conflict_type.value})")
        
        elif strategy == ResolutionStrategy.AUTO_RESOLVE:
            resolution_result["resolution_data"] = self._auto_resolve(conflict)
            logger.info(f"Konfliktus automatikusan feloldva ({conflict.conflict_type.value})")
        
        else:  # MANUAL_REVIEW
            resolution_result["resolution_data"] = {"requires_manual_review": True}
            logger.warning(f"Konfliktus manuális felülvizsgálatot igényel ({conflict.conflict_type.value})")
        
        # Konfliktus rögzítése
        conflict.resolution_strategy = strategy
        self.conflict_history.append(conflict)
        
        return resolution_result
    
    def _merge_data(self, conflict: Conflict) -> Dict:
        """Adatok összevonása"""
        if conflict.conflict_type == ConflictType.STOCK_CONFLICT:
            # Készlet esetén a nagyobb értéket vesszük
            local_stock = conflict.local_data.get("stock", 0)
            remote_stock = conflict.remote_data.get("stock", 0)
            merged_stock = max(local_stock, remote_stock)
            
            return {
                "stock": merged_stock,
                "merged_from": {"local": local_stock, "remote": remote_stock}
            }
        
        elif conflict.conflict_type == ConflictType.PRICE_CONFLICT:
            # Ár esetén a frissebb adatot vesszük
            local_time = conflict.local_data.get("updated_at")
            remote_time = conflict.remote_data.get("updated_at")
            
            if local_time and remote_time:
                if local_time > remote_time:
                    return conflict.local_data
                else:
                    return conflict.remote_data
            else:
                return conflict.remote_data  # Alapértelmezetten távoli
        
        return conflict.remote_data  # Alapértelmezett
    
    def _auto_resolve(self, conflict: Conflict) -> Dict:
        """Automatikus feloldás"""
        if conflict.conflict_type == ConflictType.DUPLICATE_PRODUCT:
            # Duplikált termék esetén a frissebb adatot tartjuk meg
            local_id = conflict.local_data.get("id")
            remote_id = conflict.remote_data.get("id")
            
            # Egyszerű logika: nagyobb ID = frissebb
            if int(local_id) > int(remote_id):
                return {"keep_id": local_id, "remove_id": remote_id}
            else:
                return {"keep_id": remote_id, "remove_id": local_id}
        
        return conflict.remote_data  # Alapértelmezett
    
    def get_conflict_statistics(self) -> Dict:
        """Konfliktus statisztikák"""
        if not self.conflict_history:
            return {"total_conflicts": 0, "resolved_conflicts": 0}
        
        total_conflicts = len(self.conflict_history)
        resolved_conflicts = len([c for c in self.conflict_history if c.resolution_strategy])
        
        conflict_types = {}
        for conflict in self.conflict_history:
            conflict_type = conflict.conflict_type.value
            conflict_types[conflict_type] = conflict_types.get(conflict_type, 0) + 1
        
        return {
            "total_conflicts": total_conflicts,
            "resolved_conflicts": resolved_conflicts,
            "unresolved_conflicts": total_conflicts - resolved_conflicts,
            "conflict_types": conflict_types,
            "resolution_rate": round((resolved_conflicts / total_conflicts) * 100, 2) if total_conflicts > 0 else 0
        }
    
    def get_recent_conflicts(self, limit: int = 10) -> List[Dict]:
        """Legutóbbi konfliktusok"""
        recent = self.conflict_history[-limit:] if self.conflict_history else []
        
        return [{
            "conflict_type": conflict.conflict_type.value,
            "timestamp": conflict.timestamp,
            "severity": conflict.severity,
            "description": conflict.description,
            "resolution_strategy": conflict.resolution_strategy.value if conflict.resolution_strategy else None
        } for conflict in recent]
    
    def set_resolution_rule(self, conflict_type: ConflictType, strategy: ResolutionStrategy):
        """Feloldási szabály beállítása"""
        self.resolution_rules[conflict_type] = strategy
        logger.info(f"Feloldási szabály beállítva: {conflict_type.value} -> {strategy.value}")
    
    def enable_auto_resolve(self, enabled: bool = True):
        """Automatikus feloldás be/kikapcsolása"""
        self.auto_resolve_enabled = enabled
        logger.info(f"Automatikus feloldás: {'bekapcsolva' if enabled else 'kikapcsolva'}")


class ConflictMonitor:
    """Konfliktus monitor rendszer"""
    
    def __init__(self, resolver: ConflictResolver):
        self.resolver = resolver
        self.monitoring_enabled = True
        self.alert_threshold = 5  # Konfliktusok száma riasztáshoz
    
    async def monitor_sync_operation(self, local_data: List[Product], remote_data: List[Product]) -> Dict:
        """Szinkronizációs művelet monitorozása"""
        if not self.monitoring_enabled:
            return {"monitoring_disabled": True}
        
        conflicts = []
        
        # Termékek páronként összehasonlítása
        local_dict = {p.id: p for p in local_data}
        remote_dict = {p.id: p for p in remote_data}
        
        # Közös termékek ellenőrzése
        common_ids = set(local_dict.keys()) & set(remote_dict.keys())
        
        for product_id in common_ids:
            local_product = local_dict[product_id]
            remote_product = remote_dict[product_id]
            
            # Ár konfliktus
            price_conflict = self.resolver.detect_price_conflict(local_product, remote_product)
            if price_conflict:
                conflicts.append(price_conflict)
            
            # Készlet konfliktus
            stock_conflict = self.resolver.detect_stock_conflict(local_product, remote_product)
            if stock_conflict:
                conflicts.append(stock_conflict)
            
            # Kategória eltérés
            category_conflict = self.resolver.detect_category_mismatch(local_product, remote_product)
            if category_conflict:
                conflicts.append(category_conflict)
        
        # Duplikált termékek
        all_products = local_data + remote_data
        duplicate_conflicts = self.resolver.detect_duplicate_product(all_products)
        conflicts.extend(duplicate_conflicts)
        
        # Adat integritási problémák
        for product in all_products:
            integrity_conflicts = self.resolver.detect_data_integrity_issues(product)
            conflicts.extend(integrity_conflicts)
        
        # Konfliktusok feloldása
        resolutions = []
        for conflict in conflicts:
            resolution = self.resolver.resolve_conflict(conflict)
            resolutions.append(resolution)
        
        # Riasztás ellenőrzése
        alert_triggered = len(conflicts) >= self.alert_threshold
        
        return {
            "conflicts_detected": len(conflicts),
            "conflicts_resolved": len(resolutions),
            "alert_triggered": alert_triggered,
            "conflict_types": list(set(c.conflict_type.value for c in conflicts)),
            "resolutions": resolutions
        }


# Singleton instances
conflict_resolver = ConflictResolver()
conflict_monitor = ConflictMonitor(conflict_resolver) 