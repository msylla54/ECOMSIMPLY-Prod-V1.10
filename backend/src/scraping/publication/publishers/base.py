"""
Publisher Mock Générique - Template pour toutes les plateformes ECOMSIMPLY
"""

import hashlib
import uuid
import time
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

from ...semantic import ProductDTO
from ..idempotency import IdempotencyManager

logger = logging.getLogger(__name__)


def get_current_year() -> int:
    """Retourne l'année courante pour usage dans les publishers"""
    from datetime import datetime
    return datetime.now().year


@dataclass
class PublishResult:
    """Résultat de publication"""
    success: bool
    external_id: Optional[str] = None
    status_code: int = 200
    message: str = ""
    store: str = ""
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class IdempotencyStore:
    """Store simple pour idempotence dans publishers"""
    
    def __init__(self):
        self._store: Dict[str, str] = {}
    
    def seen(self, key: str) -> bool:
        """Vérifie si clé déjà vue"""
        return key in self._store
    
    def get(self, key: str) -> Optional[str]:
        """Récupère valeur pour clé"""
        return self._store.get(key)
    
    def save(self, key: str, value: str) -> None:
        """Sauvegarde clé-valeur"""
        self._store[key] = value
    
    def size(self) -> int:
        """Nombre d'entrées"""
        return len(self._store)


class GenericMockPublisher:
    """Publisher mock générique pour toutes les plateformes"""
    
    def __init__(self, name: str, idem_store: IdempotencyStore):
        """
        Args:
            name: Nom du store (shopify, woocommerce, etc.)
            idem_store: Store d'idempotence
        """
        self.name = name
        self.idem_store = idem_store
        
        # Statistiques
        self.stats = {
            'total_publishes': 0,
            'successful_publishes': 0,
            'idempotent_hits': 0,
            'failed_publishes': 0,
            'total_duration_ms': 0.0
        }
        
        # Configuration spécifique par store (simulation)
        self.store_config = self._get_store_config(name)
    
    def _get_store_config(self, store_name: str) -> Dict[str, Any]:
        """Configuration simulée par store"""
        
        configs = {
            "shopify": {
                "api_version": f"{get_current_year() - 1}-04",  # Utilise l'année précédente comme pattern API
                "requires_inventory": True,
                "supports_variants": True,
                "max_images": 10,
                "typical_latency_ms": (100, 300)
            },
            "woocommerce": {
                "api_version": "wc/v3",
                "requires_inventory": False, 
                "supports_variants": True,
                "max_images": 8,
                "typical_latency_ms": (200, 600)
            },
            "prestashop": {
                "api_version": "1.7",
                "requires_inventory": True,
                "supports_variants": True,
                "max_images": 6,
                "typical_latency_ms": (300, 800)
            },
            "magento": {
                "api_version": "V1",
                "requires_inventory": True,
                "supports_variants": True,
                "max_images": 12,
                "typical_latency_ms": (400, 1000)
            },
            "wix": {
                "api_version": "1.0",
                "requires_inventory": False,
                "supports_variants": False,
                "max_images": 5,
                "typical_latency_ms": (500, 1200)
            },
            "squarespace": {
                "api_version": "1.0",
                "requires_inventory": False,
                "supports_variants": False,
                "max_images": 4,
                "typical_latency_ms": (600, 1500)
            },
            "bigcommerce": {
                "api_version": "v3",
                "requires_inventory": True,
                "supports_variants": True,
                "max_images": 8,
                "typical_latency_ms": (150, 400)
            }
        }
        
        return configs.get(store_name, configs["shopify"])  # Fallback
    
    async def publish(self, product: ProductDTO, *, idempotency_key: str) -> PublishResult:
        """
        Publie un produit avec idempotence
        
        Args:
            product: ProductDTO à publier
            idempotency_key: Clé d'idempotence
            
        Returns:
            PublishResult avec succès/échec
        """
        
        start_time = time.time()
        self.stats['total_publishes'] += 1
        
        logger.info(f"📤 Publication {self.name}: {product.title[:30]}... (key: {idempotency_key[:8]}...)")
        
        try:
            # 1. Vérification idempotence
            if self.idem_store.seen(idempotency_key):
                existing_id = self.idem_store.get(idempotency_key)
                self.stats['idempotent_hits'] += 1
                
                duration_ms = (time.time() - start_time) * 1000
                self.stats['total_duration_ms'] += duration_ms
                
                logger.info(f"♻️  Hit idempotent {self.name}: {existing_id}")
                
                return PublishResult(
                    success=True,
                    external_id=existing_id,
                    status_code=200,
                    message="idempotent-hit",
                    store=self.name,
                    duration_ms=duration_ms,
                    metadata={"idempotent": True, "store_config": self.store_config}
                )
            
            # 2. Simulation latence réseau
            await self._simulate_network_latency()
            
            # 3. Validation spécifique store
            validation_result = self._validate_product_for_store(product)
            if not validation_result['valid']:
                self.stats['failed_publishes'] += 1
                duration_ms = (time.time() - start_time) * 1000
                
                return PublishResult(
                    success=False,
                    status_code=400,
                    message=f"Validation {self.name}: {validation_result['reason']}",
                    store=self.name,
                    duration_ms=duration_ms
                )
            
            # 4. Génération external_id stable
            external_id = self._generate_external_id(idempotency_key)
            
            # 5. Sauvegarde idempotence
            self.idem_store.save(idempotency_key, external_id)
            
            # 6. Résultat succès
            self.stats['successful_publishes'] += 1
            duration_ms = (time.time() - start_time) * 1000
            self.stats['total_duration_ms'] += duration_ms
            
            logger.info(f"✅ Publication réussie {self.name}: {external_id} en {duration_ms:.0f}ms")
            
            return PublishResult(
                success=True,
                external_id=external_id,
                status_code=201,
                message=f"created (mock {self.name})",
                store=self.name,
                duration_ms=duration_ms,
                metadata={
                    "store_config": self.store_config,
                    "validation": validation_result,
                    "product_title": product.title
                }
            )
            
        except Exception as e:
            # 7. Gestion erreurs
            self.stats['failed_publishes'] += 1
            duration_ms = (time.time() - start_time) * 1000
            self.stats['total_duration_ms'] += duration_ms
            
            logger.error(f"❌ Échec publication {self.name}: {e}")
            
            return PublishResult(
                success=False,
                status_code=500,
                message=f"Erreur {self.name}: {str(e)}",
                store=self.name,
                duration_ms=duration_ms
            )
    
    async def _simulate_network_latency(self):
        """Simule latence réseau réaliste par store"""
        
        min_latency, max_latency = self.store_config['typical_latency_ms']
        
        # Latence aléatoire dans la fourchette
        import random
        latency_ms = random.randint(min_latency, max_latency)
        
        # Simulation async
        await asyncio.sleep(latency_ms / 1000.0)
    
    def _validate_product_for_store(self, product: ProductDTO) -> Dict[str, Any]:
        """Validation spécifique par store"""
        
        config = self.store_config
        
        # Validation images selon limite store
        if len(product.images) > config['max_images']:
            return {
                'valid': False,
                'reason': f"Trop d'images: {len(product.images)} > {config['max_images']}"
            }
        
        # Validation inventaire requis
        if config['requires_inventory'] and not product.attributes.get('stock'):
            # Ajouter stock simulé si requis
            product.attributes['stock'] = '10'  # Stock simulé
        
        # Validation prix pour stores payants
        if self.name in ['squarespace', 'wix'] and not product.price:
            return {
                'valid': False,
                'reason': f"Prix obligatoire pour {self.name}"
            }
        
        # Validation variants
        if not config['supports_variants'] and len(product.attributes) > 5:
            # Simplifier attributs si pas de support variants
            simplified_attrs = dict(list(product.attributes.items())[:5])
            product.attributes = simplified_attrs
        
        return {
            'valid': True,
            'reason': 'Validation réussie',
            'adaptations': {
                'images_count': len(product.images),
                'inventory_added': config['requires_inventory'],
                'variants_simplified': not config['supports_variants']
            }
        }
    
    def _generate_external_id(self, idempotency_key: str) -> str:
        """Génère ID externe stable depuis clé idempotence"""
        
        # Hash stable pour UUID déterministe
        hash_input = f"{self.name}:{idempotency_key}"
        hash_bytes = hashlib.sha1(hash_input.encode()).hexdigest()
        
        # UUID déterministe depuis hash
        uuid_hex = hash_bytes[:32]  # 32 chars pour UUID
        formatted_uuid = f"{uuid_hex[:8]}-{uuid_hex[8:12]}-{uuid_hex[12:16]}-{uuid_hex[16:20]}-{uuid_hex[20:32]}"
        
        return str(uuid.UUID(formatted_uuid))
    
    def get_stats(self) -> Dict[str, Any]:
        """Statistiques du publisher"""
        
        stats = self.stats.copy()
        
        # Métriques calculées
        if stats['total_publishes'] > 0:
            stats['success_rate'] = (stats['successful_publishes'] / stats['total_publishes']) * 100
            stats['avg_duration_ms'] = stats['total_duration_ms'] / stats['total_publishes']
        else:
            stats['success_rate'] = 0.0
            stats['avg_duration_ms'] = 0.0
        
        stats['store_name'] = self.name
        stats['store_config'] = self.store_config
        stats['idempotency_store_size'] = self.idem_store.size()
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Check santé du publisher mock"""
        
        return {
            'store': self.name,
            'status': 'healthy',
            'api_version': self.store_config.get('api_version', 'unknown'),
            'features': {
                'inventory': self.store_config['requires_inventory'],
                'variants': self.store_config['supports_variants'],
                'max_images': self.store_config['max_images']
            },
            'response_time_ms': self.store_config['typical_latency_ms'][0]  # Min latency
        }