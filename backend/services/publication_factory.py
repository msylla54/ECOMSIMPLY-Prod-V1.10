"""
Publication Factory - ECOMSIMPLY
Factory pattern pour sélectionner les publishers mock/réel selon la configuration
"""

import os
from typing import Dict, List, Optional, Any, Type
from enum import Enum

from .publication_interfaces import (
    IPublisher, PublicationPlatform, PublicationConfig
)
from .mock_publishers import (
    MockShopifyPublisher, MockWooCommercePublisher, MockPrestaShopPublisher
)

class PublisherMode(str, Enum):
    """Modes de publication disponibles"""
    MOCK = "mock"
    REAL = "real"
    DRY_RUN = "dry_run"

class PublicationFactory:
    """Factory pour créer les publishers appropriés"""
    
    def __init__(self):
        self.config = PublicationConfig()
        self._mock_publishers = {}
        self._real_publishers = {}
        self._init_publishers()
    
    def _init_publishers(self):
        """Initialise les publishers disponibles"""
        # Publishers mock (toujours disponibles)
        self._mock_publishers = {
            PublicationPlatform.SHOPIFY: MockShopifyPublisher,
            PublicationPlatform.WOOCOMMERCE: MockWooCommercePublisher,
            PublicationPlatform.PRESTASHOP: MockPrestaShopPublisher
        }
        
        # Publishers réels (chargés dynamiquement si disponibles)
        # Sera implémenté dans les étapes suivantes
        self._real_publishers = {}
    
    def get_publisher(self, platform: PublicationPlatform) -> Optional[IPublisher]:
        """Récupère le publisher approprié pour une plateforme"""
        
        if self.config.mock_mode:
            # Mode mock : toujours utiliser les mocks
            publisher_class = self._mock_publishers.get(platform)
            if publisher_class:
                return publisher_class()
            return None
        
        # Mode réel : vérifier disponibilité puis fallback mock
        if self.config.is_platform_available(platform):
            publisher_class = self._real_publishers.get(platform)
            if publisher_class:
                return publisher_class()
        
        # Fallback vers mock si réel pas disponible
        publisher_class = self._mock_publishers.get(platform)
        if publisher_class:
            return publisher_class()
        
        return None
    
    def get_all_available_publishers(self) -> Dict[PublicationPlatform, IPublisher]:
        """Récupère tous les publishers disponibles"""
        publishers = {}
        
        for platform in self.config.enabled_platforms:
            publisher = self.get_publisher(platform)
            if publisher:
                publishers[platform] = publisher
        
        return publishers
    
    def get_platform_status(self, platform: PublicationPlatform) -> Dict[str, Any]:
        """Récupère le statut d'une plateforme"""
        publisher = self.get_publisher(platform)
        
        if not publisher:
            return {
                "platform": platform.value,
                "available": False,
                "reason": "Publisher not found",
                "mode": None,
                "missing_env": self.config.get_missing_env_vars(platform)
            }
        
        return {
            "platform": platform.value,
            "available": True,
            "mode": "mock" if publisher.is_mock else "real",
            "platform_available": self.config.is_platform_available(platform),
            "missing_env": self.config.get_missing_env_vars(platform) if not self.config.mock_mode else [],
            "dry_run": self.config.dry_run
        }
    
    def get_global_status(self) -> Dict[str, Any]:
        """Récupère le statut global de publication"""
        platforms_status = {}
        available_count = 0
        real_count = 0
        
        for platform in PublicationPlatform:
            if platform in [PublicationPlatform.SHOPIFY, PublicationPlatform.WOOCOMMERCE, PublicationPlatform.PRESTASHOP]:
                status = self.get_platform_status(platform)
                platforms_status[platform.value] = status
                
                if status["available"]:
                    available_count += 1
                    if status["mode"] == "real":
                        real_count += 1
        
        # Détection des variables manquantes globales
        all_missing = set()
        for platform in [PublicationPlatform.SHOPIFY, PublicationPlatform.WOOCOMMERCE, PublicationPlatform.PRESTASHOP]:
            missing = self.config.get_missing_env_vars(platform)
            all_missing.update(missing)
        
        return {
            "mode": "mock" if self.config.mock_mode else "real",
            "mock_mode": self.config.mock_mode,
            "dry_run": self.config.dry_run,
            "auto_publish": self.config.publish_auto,
            "platforms_available": available_count,
            "platforms_real": real_count,
            "platforms_mock": available_count - real_count,
            "platforms": platforms_status,
            "missing_env_vars": list(all_missing),
            "ready_for_production": real_count > 0 and not self.config.mock_mode,
            "configuration": {
                "max_retries": self.config.max_retries,
                "timeout_seconds": self.config.timeout_seconds,
                "batch_size": self.config.batch_size,
                "parallel_publications": self.config.parallel_publications,
                "max_concurrent": self.config.max_concurrent,
                "validate_before_publish": self.config.validate_before_publish
            },
            "health_check_timestamp": None  # Sera rempli par le health check
        }

# Instance globale
publication_factory = PublicationFactory()

async def publish_product_to_platforms(
    product_data: Dict[str, Any],
    platforms: Optional[List[str]] = None,
    user_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fonction utilitaire pour publier un produit sur plusieurs plateformes
    """
    from .publication_interfaces import ProductDTO, ImageDTO
    
    # Conversion vers ProductDTO
    images = []
    if product_data.get("generated_images"):
        for i, img_data in enumerate(product_data["generated_images"]):
            if isinstance(img_data, str) and img_data.startswith("data:image"):
                images.append(ImageDTO(
                    base64_data=img_data,
                    alt_text=product_data.get("product_name", "Product image"),
                    position=i
                ))
    
    product = ProductDTO(
        user_id=user_id or "anonymous",
        name=product_data.get("generated_title", product_data.get("product_name", "Unnamed Product")),
        description=product_data.get("marketing_description", ""),
        short_description=product_data.get("marketing_description", "")[:160] if product_data.get("marketing_description") else "",
        price=extract_price_from_suggestions(product_data.get("price_suggestions", "")),
        seo_title=product_data.get("generated_title", ""),
        seo_description=product_data.get("marketing_description", "")[:160] if product_data.get("marketing_description") else "",
        keywords=product_data.get("keywords", []),
        tags=product_data.get("seo_tags", [])[:20],  # Limite raisonnable
        key_features=product_data.get("key_features", []),
        images=images,
        category=product_data.get("category", "General"),
        sku=f"ECOM-{product_data.get('id', 'unknown')[:8]}",
        status="published"
    )
    
    # Sélection des plateformes
    if not platforms:
        platforms = ["shopify", "woocommerce", "prestashop"]
    
    results = []
    publishers = publication_factory.get_all_available_publishers()
    
    for platform_name in platforms:
        try:
            platform_enum = PublicationPlatform(platform_name)
            publisher = publishers.get(platform_enum)
            
            if not publisher:
                results.append({
                    "platform": platform_name,
                    "success": False,
                    "error": f"Publisher not available for {platform_name}",
                    "mode": "none"
                })
                continue
            
            # Configuration de boutique mock
            store_config = {
                "id": f"mock_{platform_name}_store",
                "name": f"Mock {platform_name.title()} Store",
                "url": f"https://{platform_name}-store.example.com"
            }
            
            # Publication
            result = await publisher.publish_product(product, store_config)
            
            results.append({
                "platform": platform_name,
                "success": result.success,
                "product_id": result.product_id,
                "published_url": result.published_url,
                "error": result.error_message,
                "mode": result.mode,
                "processing_time_ms": result.processing_time_ms,
                "publication_id": result.publication_id,
                "images_uploaded": result.images_uploaded,
                "warnings": result.warnings
            })
            
        except Exception as e:
            results.append({
                "platform": platform_name,
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "mode": "error"
            })
    
    return results

def extract_price_from_suggestions(price_suggestions: str) -> Optional[float]:
    """Extrait le prix depuis les suggestions de prix IA"""
    if not price_suggestions:
        return None
    
    import re
    
    # Recherche de patterns de prix (ordre de priorité)
    patterns = [
        r'(\d+[.,]\d+)\s*€',     # 29.99€ ou 29,99€ (avec décimales)
        r'(\d+[.,]\d+)\s*EUR',   # 29.99 EUR ou 29,99 EUR
        r'€\s*(\d+[.,]\d+)',     # € 29.99 ou € 29,99
        r'(\d+[.,]\d+)',         # 29.99 ou 29,99 (nu avec décimales)
        r'(\d+)\s*€',            # 29€ (entier)
        r'(\d+)\s*EUR',          # 29 EUR
        r'€\s*(\d+)',            # € 29
        r'(\d+)'                 # 29 (nu entier)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, price_suggestions)
        if match:
            price_str = match.group(1).replace(',', '.')
            try:
                return float(price_str)
            except ValueError:
                continue
    
    return None