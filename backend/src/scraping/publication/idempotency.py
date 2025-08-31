"""
Idempotency Manager - Gestion des clés d'idempotence pour éviter doublons publication - ECOMSIMPLY
"""

import hashlib
import time
from typing import Dict, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from ..semantic import ProductDTO


@dataclass
class IdempotencyKey:
    """Clé d'idempotence avec métadonnées"""
    key: str
    store_id: str
    product_id: str  
    created_at: float
    payload_hash: str
    metadata: Dict = field(default_factory=dict)
    
    def is_expired(self, ttl_hours: int = 24) -> bool:
        """Vérifier si la clé a expiré"""
        return (time.time() - self.created_at) > (ttl_hours * 3600)
    
    def age_minutes(self) -> float:
        """Âge de la clé en minutes"""
        return (time.time() - self.created_at) / 60


class IdempotencyManager:
    """Gestionnaire d'idempotence avec adaptateur DB/InMemory"""
    
    def __init__(self, storage_adapter=None):
        """
        Args:
            storage_adapter: Adaptateur de stockage (DB, Redis, etc.)
                           Si None, utilise stockage en mémoire
        """
        self.storage_adapter = storage_adapter
        
        # Stockage en mémoire (fallback)
        self._memory_storage: Dict[str, IdempotencyKey] = {}
        
        # Cache local pour performance
        self._local_cache: Set[str] = set()
        self._cache_expire = time.time() + 300  # Cache 5min
        
        # Statistiques
        self.stats = {
            'keys_generated': 0,
            'duplicates_detected': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def generate_idempotency_key(self, store_id: str, product_dto: ProductDTO) -> str:
        """
        Génère clé d'idempotence unique pour éviter doublons publication
        
        Format: sha256(store_id + product_signature + source_url + price)
        
        Args:
            store_id: ID de la boutique cible
            product_dto: ProductDTO à publier
            
        Returns:
            Clé d'idempotence unique (16 chars)
        """
        
        # Éléments pour clé stable
        key_components = [
            store_id.strip(),
            product_dto.payload_signature,  # Déjà unique par produit
            product_dto.source_url,
            str(product_dto.price.amount if product_dto.price else 'no_price'),
            str(product_dto.price.currency if product_dto.price else 'no_currency'),
        ]
        
        # Hash stable
        key_string = '|||'.join(key_components)
        full_hash = hashlib.sha256(key_string.encode('utf-8')).hexdigest()
        
        # Clé courte pour usage pratique
        idempotency_key = full_hash[:16]
        
        self.stats['keys_generated'] += 1
        return idempotency_key
    
    async def exists(self, idempotency_key: str) -> bool:
        """
        Vérifier si la clé existe déjà (éviter doublons)
        
        Returns:
            True si déjà publiée, False sinon
        """
        
        # 1. Cache local rapide
        if self._is_cache_valid() and idempotency_key in self._local_cache:
            self.stats['cache_hits'] += 1
            return True
        
        # 2. Stockage persistant (DB ou mémoire)
        exists = False
        
        if self.storage_adapter:
            # Stockage DB/Redis
            exists = await self.storage_adapter.exists(idempotency_key)
        else:
            # Stockage en mémoire
            if idempotency_key in self._memory_storage:
                key_obj = self._memory_storage[idempotency_key]
                if not key_obj.is_expired():
                    exists = True
                else:
                    # Nettoyer clé expirée
                    del self._memory_storage[idempotency_key]
        
        # 3. Mettre à jour cache local
        if exists:
            self._local_cache.add(idempotency_key)
            self.stats['duplicates_detected'] += 1
        else:
            self.stats['cache_misses'] += 1
        
        return exists
    
    async def store(self, idempotency_key: str, store_id: str, product_dto: ProductDTO, 
                   metadata: Optional[Dict] = None) -> None:
        """
        Stocker clé d'idempotence après publication réussie
        
        Args:
            idempotency_key: Clé générée
            store_id: ID boutique
            product_dto: ProductDTO publié
            metadata: Métadonnées additionnelles
        """
        
        key_obj = IdempotencyKey(
            key=idempotency_key,
            store_id=store_id,
            product_id=product_dto.payload_signature,  # Utilise signature comme ID
            created_at=time.time(),
            payload_hash=product_dto.payload_signature,
            metadata=metadata or {}
        )
        
        # Stockage persistant
        if self.storage_adapter:
            await self.storage_adapter.store(key_obj)
        else:
            # Stockage en mémoire
            self._memory_storage[idempotency_key] = key_obj
        
        # Cache local
        self._local_cache.add(idempotency_key)
    
    async def get_key_info(self, idempotency_key: str) -> Optional[IdempotencyKey]:
        """Obtenir informations détaillées sur une clé"""
        
        if self.storage_adapter:
            return await self.storage_adapter.get(idempotency_key)
        else:
            key_obj = self._memory_storage.get(idempotency_key)
            if key_obj and not key_obj.is_expired():
                return key_obj
        
        return None
    
    async def cleanup_expired(self) -> int:
        """Nettoyer clés expirées"""
        
        cleaned_count = 0
        
        if self.storage_adapter:
            cleaned_count = await self.storage_adapter.cleanup_expired()
        else:
            # Nettoyage mémoire
            expired_keys = [
                key for key, key_obj in self._memory_storage.items()
                if key_obj.is_expired()
            ]
            
            for key in expired_keys:
                del self._memory_storage[key]
                self._local_cache.discard(key)
            
            cleaned_count = len(expired_keys)
        
        return cleaned_count
    
    def _is_cache_valid(self) -> bool:
        """Vérifier si le cache local est valide"""
        current_time = time.time()
        if current_time > self._cache_expire:
            # Cache expiré → vider et renouveler
            self._local_cache.clear()
            self._cache_expire = current_time + 300  # 5 min
            return False
        return True
    
    async def get_stats(self) -> Dict[str, any]:
        """Obtenir statistiques d'utilisation"""
        
        storage_stats = {}
        if self.storage_adapter:
            storage_stats = await self.storage_adapter.get_stats()
        else:
            storage_stats = {
                "memory_keys": len(self._memory_storage),
                "cache_keys": len(self._local_cache)
            }
        
        return {
            **self.stats,
            **storage_stats,
            "cache_valid": self._is_cache_valid()
        }
    
    async def get_duplicate_analysis(self, store_id: str) -> Dict[str, any]:
        """Analyse des doublons détectés pour un store"""
        
        if self.storage_adapter:
            return await self.storage_adapter.get_duplicate_analysis(store_id)
        else:
            # Analyse simple mémoire
            store_keys = [
                key_obj for key_obj in self._memory_storage.values()
                if key_obj.store_id == store_id and not key_obj.is_expired()
            ]
            
            return {
                "store_id": store_id,
                "total_keys": len(store_keys),
                "avg_age_minutes": sum(k.age_minutes() for k in store_keys) / len(store_keys) if store_keys else 0,
                "oldest_key_age": max(k.age_minutes() for k in store_keys) if store_keys else 0
            }


class MockDBAdapter:
    """Adaptateur mock pour tests - simule base de données"""
    
    def __init__(self):
        self.storage: Dict[str, IdempotencyKey] = {}
        self.access_count = 0
    
    async def exists(self, key: str) -> bool:
        self.access_count += 1
        key_obj = self.storage.get(key)
        return key_obj is not None and not key_obj.is_expired()
    
    async def store(self, key_obj: IdempotencyKey) -> None:
        self.access_count += 1
        self.storage[key_obj.key] = key_obj
    
    async def get(self, key: str) -> Optional[IdempotencyKey]:
        self.access_count += 1
        key_obj = self.storage.get(key)
        if key_obj and not key_obj.is_expired():
            return key_obj
        return None
    
    async def cleanup_expired(self) -> int:
        expired_keys = [
            k for k, v in self.storage.items() 
            if v.is_expired()
        ]
        for k in expired_keys:
            del self.storage[k]
        return len(expired_keys)
    
    async def get_stats(self) -> Dict[str, any]:
        return {
            "db_keys": len(self.storage),
            "db_access_count": self.access_count
        }
    
    async def get_duplicate_analysis(self, store_id: str) -> Dict[str, any]:
        store_keys = [v for v in self.storage.values() if v.store_id == store_id]
        return {
            "store_id": store_id,
            "db_keys_for_store": len(store_keys)
        }