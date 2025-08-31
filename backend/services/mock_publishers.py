"""
Mock Publishers - ECOMSIMPLY
Implémentations mock pour les publishers e-commerce (aucun appel réseau)
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os
from collections import defaultdict

from .publication_interfaces import (
    IPublisher, ProductDTO, PublishResult, PublicationPlatform, 
    PublicationStatus, ImageDTO, PublicationConfig
)

class MockPublicationStorage:
    """Stockage en mémoire pour les publications mock"""
    
    def __init__(self):
        self._publications: Dict[str, Dict] = {}
        self._products: Dict[str, Dict] = {}
        self._stores: Dict[str, Dict] = {}
        self._logs: List[Dict] = []
        self._stats = defaultdict(int)
    
    async def save_publication(self, result: PublishResult, product: ProductDTO) -> None:
        """Sauvegarde une publication mock"""
        pub_data = {
            "id": result.publication_id,
            "platform": result.platform.value,
            "product_id": result.product_id,
            "product_name": product.name,
            "status": result.status.value,
            "success": result.success,
            "published_at": result.published_at.isoformat() if result.published_at else None,
            "mode": result.mode,
            "dry_run": result.dry_run,
            "error_message": result.error_message,
            "images_count": len(product.images),
            "price": product.price,
            "category": product.category,
            "tags": product.tags,
            "created_at": result.created_at.isoformat()
        }
        
        self._publications[result.publication_id] = pub_data
        
        # Sauvegarder le produit mock
        if result.success and result.product_id:
            self._products[result.product_id] = {
                "id": result.product_id,
                "platform": result.platform.value,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "images": len(product.images),
                "published_at": result.published_at.isoformat() if result.published_at else None,
                "sku": product.sku,
                "tags": product.tags,
                "category": product.category,
                "status": "published"
            }
        
        # Log pour audit
        self._logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "publish_product",
            "platform": result.platform.value,
            "success": result.success,
            "product_name": product.name,
            "publication_id": result.publication_id
        })
        
        # Stats
        self._stats[f"{result.platform.value}_attempts"] += 1
        if result.success:
            self._stats[f"{result.platform.value}_success"] += 1
        else:
            self._stats[f"{result.platform.value}_failures"] += 1
    
    def get_publications(self, platform: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Récupère les publications mock"""
        pubs = list(self._publications.values())
        
        if platform:
            pubs = [p for p in pubs if p["platform"] == platform]
        
        # Trier par date décroissante
        pubs.sort(key=lambda x: x["created_at"], reverse=True)
        
        return pubs[:limit]
    
    def get_product(self, product_id: str) -> Optional[Dict]:
        """Récupère un produit mock"""
        return self._products.get(product_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques"""
        platforms = ["shopify", "woocommerce", "prestashop"]
        stats = dict(self._stats)
        
        # Calculer les taux de succès
        for platform in platforms:
            attempts = stats.get(f"{platform}_attempts", 0)
            success = stats.get(f"{platform}_success", 0)
            stats[f"{platform}_success_rate"] = (success / attempts * 100) if attempts > 0 else 0
        
        stats["total_publications"] = len(self._publications)
        stats["total_products"] = len(self._products)
        stats["last_publication"] = max([p["created_at"] for p in self._publications.values()]) if self._publications else None
        
        return stats
    
    def clear_all(self) -> None:
        """Efface toutes les données mock (pour tests)"""
        self._publications.clear()
        self._products.clear()
        self._stores.clear()
        self._logs.clear()
        self._stats.clear()

# Instance globale pour les mocks
mock_storage = MockPublicationStorage()

class BaseMockPublisher(IPublisher):
    """Classe de base pour les publishers mock"""
    
    def __init__(self, platform: PublicationPlatform):
        self._platform = platform
        self.config = PublicationConfig()
    
    @property
    def platform(self) -> PublicationPlatform:
        return self._platform
    
    @property
    def is_mock(self) -> bool:
        return True
    
    async def _simulate_api_call(self, operation: str, data: Dict = None) -> Dict[str, Any]:
        """Simule un appel API avec délai réaliste"""
        # Délai simulé (50-200ms)
        delay = 0.05 + (hash(operation) % 150) / 1000
        await asyncio.sleep(delay)
        
        # Simule succès à 95% (plus réaliste)
        success_rate = 0.95
        is_success = (hash(str(data)) % 100) < (success_rate * 100)
        
        if is_success:
            return {
                "success": True,
                "id": f"mock_{self._platform.value}_{uuid.uuid4().hex[:8]}",
                "url": f"https://{self._platform.value}-store.example.com/products/mock-product-{uuid.uuid4().hex[:8]}",
                "admin_url": f"https://admin.{self._platform.value}.com/products/mock-product-{uuid.uuid4().hex[:8]}",
                "operation": operation,
                "simulated_at": datetime.utcnow().isoformat()
            }
        else:
            # Simulation d'erreurs réalistes
            errors = [
                {"code": "RATE_LIMIT", "message": "Rate limit exceeded, retry after 60 seconds"},
                {"code": "VALIDATION_ERROR", "message": "Product name is required"},
                {"code": "AUTH_ERROR", "message": "Invalid access token"},
                {"code": "NETWORK_ERROR", "message": "Connection timeout"}
            ]
            error = errors[hash(operation) % len(errors)]
            
            return {
                "success": False,
                "error": error,
                "operation": operation,
                "simulated_at": datetime.utcnow().isoformat()
            }
    
    async def health_check(self, store_config: Dict[str, Any]) -> Dict[str, Any]:
        """Health check mock"""
        result = await self._simulate_api_call("health_check")
        
        return {
            "platform": self._platform.value,
            "status": "healthy" if result["success"] else "unhealthy",
            "mock_mode": True,
            "store_config_provided": bool(store_config),
            "last_check": datetime.utcnow().isoformat(),
            "response_time_ms": 50 + (hash(str(store_config)) % 100),
            "simulated": True
        }

class MockShopifyPublisher(BaseMockPublisher):
    """Publisher mock pour Shopify"""
    
    def __init__(self):
        super().__init__(PublicationPlatform.SHOPIFY)
    
    async def publish_product(self, product: ProductDTO, store_config: Dict[str, Any]) -> PublishResult:
        """Publication mock sur Shopify"""
        start_time = datetime.utcnow()
        
        # Simulation appel API
        api_result = await self._simulate_api_call("create_product", {
            "name": product.name,
            "price": product.price,
            "images": len(product.images)
        })
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        if api_result["success"]:
            result = PublishResult(
                success=True,
                status=PublicationStatus.SUCCESS,
                platform=self._platform,
                product_id=api_result["id"],
                platform_product_id=api_result["id"],
                published_url=api_result["url"],
                admin_url=api_result["admin_url"],
                published_at=datetime.utcnow(),
                processing_time_ms=int(processing_time),
                mode="mock",
                dry_run=self.config.dry_run,
                payload_size_bytes=len(json.dumps(product.to_shopify_format())),
                images_uploaded=len(product.images),
                debug_info={
                    "shopify_format_used": True,
                    "variants_created": 1,
                    "tags_applied": len(product.tags),
                    "seo_optimized": bool(product.seo_title),
                    "simulated_response": api_result
                }
            )
        else:
            error = api_result["error"]
            result = PublishResult(
                success=False,
                status=PublicationStatus.FAILED,
                platform=self._platform,
                error_message=error["message"],
                error_code=error["code"],
                processing_time_ms=int(processing_time),
                mode="mock",
                dry_run=self.config.dry_run,
                retryable=error["code"] in ["RATE_LIMIT", "NETWORK_ERROR"],
                debug_info={
                    "error_simulated": True,
                    "shopify_format_attempted": True,
                    "simulated_response": api_result
                }
            )
        
        # Sauvegarder dans le storage mock
        await mock_storage.save_publication(result, product)
        
        return result
    
    async def update_product(self, product_id: str, product: ProductDTO, store_config: Dict[str, Any]) -> PublishResult:
        """Mise à jour mock"""
        api_result = await self._simulate_api_call("update_product", {"id": product_id})
        
        if api_result["success"]:
            return PublishResult(
                success=True,
                status=PublicationStatus.SUCCESS,
                platform=self._platform,
                product_id=product_id,
                mode="mock",
                debug_info={"operation": "update", "simulated": True}
            )
        else:
            return PublishResult(
                success=False,
                status=PublicationStatus.FAILED,
                platform=self._platform,
                error_message=api_result["error"]["message"],
                mode="mock"
            )
    
    async def delete_product(self, product_id: str, store_config: Dict[str, Any]) -> PublishResult:
        """Suppression mock"""
        api_result = await self._simulate_api_call("delete_product", {"id": product_id})
        
        return PublishResult(
            success=api_result["success"],
            status=PublicationStatus.SUCCESS if api_result["success"] else PublicationStatus.FAILED,
            platform=self._platform,
            product_id=product_id,
            mode="mock",
            debug_info={"operation": "delete", "simulated": True}
        )
    
    async def get_product(self, product_id: str, store_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Récupération mock"""
        return mock_storage.get_product(product_id)

class MockWooCommercePublisher(BaseMockPublisher):
    """Publisher mock pour WooCommerce"""
    
    def __init__(self):
        super().__init__(PublicationPlatform.WOOCOMMERCE)
    
    async def publish_product(self, product: ProductDTO, store_config: Dict[str, Any]) -> PublishResult:
        """Publication mock sur WooCommerce"""
        start_time = datetime.utcnow()
        
        # Simulation appel API WooCommerce
        api_result = await self._simulate_api_call("create_product", {
            "name": product.name,
            "type": "simple",
            "price": product.price
        })
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        if api_result["success"]:
            result = PublishResult(
                success=True,
                status=PublicationStatus.SUCCESS,
                platform=self._platform,
                product_id=api_result["id"],
                published_url=api_result["url"],
                admin_url=api_result["admin_url"],
                published_at=datetime.utcnow(),
                processing_time_ms=int(processing_time),
                mode="mock",
                images_uploaded=len(product.images),
                debug_info={
                    "woocommerce_format_used": True,
                    "categories_assigned": 1 if product.category else 0,
                    "meta_data_added": bool(product.seo_title),
                    "simulated_response": api_result
                }
            )
        else:
            error = api_result["error"]
            result = PublishResult(
                success=False,
                status=PublicationStatus.FAILED,
                platform=self._platform,
                error_message=error["message"],
                error_code=error["code"],
                processing_time_ms=int(processing_time),
                mode="mock",
                retryable=error["code"] in ["RATE_LIMIT", "NETWORK_ERROR"],
                debug_info={"error_simulated": True}
            )
        
        await mock_storage.save_publication(result, product)
        return result
    
    async def update_product(self, product_id: str, product: ProductDTO, store_config: Dict[str, Any]) -> PublishResult:
        """Mise à jour mock WooCommerce"""
        api_result = await self._simulate_api_call("update_product", {"id": product_id})
        
        return PublishResult(
            success=api_result["success"],
            status=PublicationStatus.SUCCESS if api_result["success"] else PublicationStatus.FAILED,
            platform=self._platform,
            product_id=product_id,
            mode="mock"
        )
    
    async def delete_product(self, product_id: str, store_config: Dict[str, Any]) -> PublishResult:
        """Suppression mock WooCommerce"""
        api_result = await self._simulate_api_call("delete_product", {"id": product_id})
        
        return PublishResult(
            success=api_result["success"],
            status=PublicationStatus.SUCCESS if api_result["success"] else PublicationStatus.FAILED,
            platform=self._platform,
            product_id=product_id,
            mode="mock"
        )
    
    async def get_product(self, product_id: str, store_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Récupération mock"""
        return mock_storage.get_product(product_id)

class MockPrestaShopPublisher(BaseMockPublisher):
    """Publisher mock pour PrestaShop"""
    
    def __init__(self):
        super().__init__(PublicationPlatform.PRESTASHOP)
    
    async def publish_product(self, product: ProductDTO, store_config: Dict[str, Any]) -> PublishResult:
        """Publication mock sur PrestaShop"""
        start_time = datetime.utcnow()
        
        # Simulation appel API PrestaShop
        api_result = await self._simulate_api_call("create_product", {
            "name": product.name,
            "price": product.price,
            "active": 1
        })
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        if api_result["success"]:
            result = PublishResult(
                success=True,
                status=PublicationStatus.SUCCESS,
                platform=self._platform,
                product_id=api_result["id"],
                published_url=api_result["url"],
                admin_url=api_result["admin_url"],
                published_at=datetime.utcnow(),
                processing_time_ms=int(processing_time),
                mode="mock",
                images_uploaded=len(product.images),
                debug_info={
                    "prestashop_format_used": True,
                    "multilang_support": True,
                    "advanced_stock_management": product.manage_stock,
                    "simulated_response": api_result
                }
            )
        else:
            error = api_result["error"]
            result = PublishResult(
                success=False,
                status=PublicationStatus.FAILED,
                platform=self._platform,
                error_message=error["message"],
                error_code=error["code"],
                processing_time_ms=int(processing_time),
                mode="mock",
                retryable=error["code"] in ["RATE_LIMIT", "NETWORK_ERROR"]
            )
        
        await mock_storage.save_publication(result, product)
        return result
    
    async def update_product(self, product_id: str, product: ProductDTO, store_config: Dict[str, Any]) -> PublishResult:
        """Mise à jour mock PrestaShop"""
        api_result = await self._simulate_api_call("update_product", {"id": product_id})
        
        return PublishResult(
            success=api_result["success"],
            status=PublicationStatus.SUCCESS if api_result["success"] else PublicationStatus.FAILED,
            platform=self._platform,
            product_id=product_id,
            mode="mock"
        )
    
    async def delete_product(self, product_id: str, store_config: Dict[str, Any]) -> PublishResult:
        """Suppression mock PrestaShop"""
        api_result = await self._simulate_api_call("delete_product", {"id": product_id})
        
        return PublishResult(
            success=api_result["success"],
            status=PublicationStatus.SUCCESS if api_result["success"] else PublicationStatus.FAILED,
            platform=self._platform,
            product_id=product_id,
            mode="mock"
        )
    
    async def get_product(self, product_id: str, store_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Récupération mock"""
        return mock_storage.get_product(product_id)