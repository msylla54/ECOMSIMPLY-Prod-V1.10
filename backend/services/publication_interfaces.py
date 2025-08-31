"""
Publication Interfaces & DTOs - ECOMSIMPLY
Interfaces d'abstraction pour publications e-commerce avec support mock/réel
"""

import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
import uuid
from enum import Enum

class PublicationPlatform(str, Enum):
    """Plateformes e-commerce supportées"""
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    PRESTASHOP = "prestashop"
    AMAZON = "amazon"
    EBAY = "ebay"
    ETSY = "etsy"
    FACEBOOK = "facebook"

class PublicationStatus(str, Enum):
    """Statuts de publication"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    PARTIAL = "partial"
    SKIPPED = "skipped"

class ImageDTO(BaseModel):
    """DTO pour les images produit"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    base64_data: str
    format: str = "jpeg"  # jpeg, png, webp
    size_kb: Optional[int] = None
    alt_text: Optional[str] = None
    position: int = 0

class ProductDTO(BaseModel):
    """DTO standardisé pour les produits à publier"""
    
    # Identifiants
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    sheet_id: Optional[str] = None
    
    # Données produit principales
    name: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = None
    description: str = Field(..., min_length=10)
    short_description: Optional[str] = None
    
    # Pricing
    price: Optional[float] = None
    compare_at_price: Optional[float] = None
    cost_per_item: Optional[float] = None
    currency: str = "EUR"
    
    # SEO & Marketing
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    
    # Contenu structuré
    key_features: List[str] = Field(default_factory=list)
    specifications: Dict[str, Any] = Field(default_factory=dict)
    
    # Images
    images: List[ImageDTO] = Field(default_factory=list)
    featured_image: Optional[ImageDTO] = None
    
    # Classification
    category: Optional[str] = None
    product_type: Optional[str] = None
    vendor: Optional[str] = None
    brand: Optional[str] = None
    
    # Inventaire
    sku: Optional[str] = None
    barcode: Optional[str] = None
    track_quantity: bool = True
    quantity: int = 100
    manage_stock: bool = True
    
    # Publication
    status: str = "draft"  # draft, published, private
    visibility: str = "visible"  # visible, hidden, password
    featured: bool = False
    
    # Métadonnées
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_shopify_format(self) -> Dict[str, Any]:
        """Convertit vers le format Shopify API"""
        return {
            "product": {
                "title": self.name,
                "body_html": self.description,
                "product_type": self.product_type or self.category or "",
                "vendor": self.vendor or self.brand or "",
                "tags": ",".join(self.tags[:10]),  # Limite Shopify
                "status": self.status,
                "variants": [{
                    "price": str(self.price) if self.price else "0.00",
                    "compare_at_price": str(self.compare_at_price) if self.compare_at_price else None,
                    "cost": str(self.cost_per_item) if self.cost_per_item else None,
                    "sku": self.sku or "",
                    "barcode": self.barcode or "",
                    "inventory_management": "shopify" if self.manage_stock else None,
                    "inventory_quantity": self.quantity if self.track_quantity else None,
                    "requires_shipping": True
                }],
                "images": [{"alt": img.alt_text or self.name} for img in self.images],
                "options": [{"name": "Title", "values": ["Default Title"]}]
            }
        }
    
    def to_woocommerce_format(self) -> Dict[str, Any]:
        """Convertit vers le format WooCommerce API"""
        return {
            "name": self.name,
            "type": "simple",
            "regular_price": str(self.price) if self.price else "0",
            "sale_price": "",
            "description": self.description,
            "short_description": self.short_description or self.description[:160],
            "sku": self.sku or "",
            "manage_stock": self.manage_stock,
            "stock_quantity": self.quantity if self.track_quantity else None,
            "stock_status": "instock",
            "featured": self.featured,
            "catalog_visibility": self.visibility,
            "status": self.status,
            "categories": [{"name": self.category}] if self.category else [],
            "tags": [{"name": tag} for tag in self.tags],
            "images": [{"alt": img.alt_text or self.name} for img in self.images],
            "meta_data": [
                {"key": "_yoast_wpseo_title", "value": self.seo_title or self.name},
                {"key": "_yoast_wpseo_metadesc", "value": self.seo_description or self.short_description}
            ] if self.seo_title or self.seo_description else []
        }
    
    def to_prestashop_format(self) -> Dict[str, Any]:
        """Convertit vers le format PrestaShop API"""
        return {
            "product": {
                "name": [{"id": 1, "value": self.name}],  # Multi-langue
                "description": [{"id": 1, "value": self.description}],
                "description_short": [{"id": 1, "value": self.short_description or self.description[:160]}],
                "price": str(self.price) if self.price else "0.00",
                "wholesale_price": str(self.cost_per_item) if self.cost_per_item else "0.00",
                "reference": self.sku or "",
                "ean13": self.barcode or "",
                "active": "1" if self.status == "published" else "0",
                "available_for_order": "1",
                "show_price": "1",
                "online_only": "0",
                "meta_title": [{"id": 1, "value": self.seo_title or self.name}],
                "meta_description": [{"id": 1, "value": self.seo_description or ""}],
                "link_rewrite": [{"id": 1, "value": self.slug or self.name.lower().replace(" ", "-")}],
                "state": "1",
                "advanced_stock_management": "1" if self.manage_stock else "0",
                "depends_on_stock": "1" if self.track_quantity else "0"
            }
        }

class PublishResult(BaseModel):
    """Résultat d'une tentative de publication"""
    
    # Statut
    success: bool
    status: PublicationStatus
    platform: PublicationPlatform
    
    # Identifiants
    publication_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: Optional[str] = None  # ID sur la plateforme
    platform_product_id: Optional[str] = None  # ID natif plateforme
    store_id: Optional[str] = None
    
    # Données de publication
    published_url: Optional[str] = None
    admin_url: Optional[str] = None
    product_sku: Optional[str] = None
    
    # Métriques
    published_at: Optional[datetime] = None
    processing_time_ms: Optional[int] = None
    
    # Erreurs et debug
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    retryable: bool = True
    
    # Métadonnées
    mode: str = "mock"  # mock ou real
    dry_run: bool = False
    payload_size_bytes: Optional[int] = None
    images_uploaded: int = 0
    
    # Logs structurés
    debug_info: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

class IPublisher(ABC):
    """Interface pour les publishers e-commerce"""
    
    @abstractmethod
    async def publish_product(self, product: ProductDTO, store_config: Dict[str, Any]) -> PublishResult:
        """Publie un produit sur la plateforme"""
        pass
    
    @abstractmethod
    async def update_product(self, product_id: str, product: ProductDTO, store_config: Dict[str, Any]) -> PublishResult:
        """Met à jour un produit existant"""
        pass
    
    @abstractmethod
    async def delete_product(self, product_id: str, store_config: Dict[str, Any]) -> PublishResult:
        """Supprime un produit"""
        pass
    
    @abstractmethod
    async def get_product(self, product_id: str, store_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Récupère un produit depuis la plateforme"""
        pass
    
    @abstractmethod
    async def health_check(self, store_config: Dict[str, Any]) -> Dict[str, Any]:
        """Vérifie la santé de la connexion"""
        pass
    
    @property
    @abstractmethod
    def platform(self) -> PublicationPlatform:
        """Retourne la plateforme supportée"""
        pass
    
    @property
    @abstractmethod
    def is_mock(self) -> bool:
        """Indique si c'est une implémentation mock"""
        pass

class PublicationConfig(BaseModel):
    """Configuration globale de publication"""
    
    mock_mode: bool = Field(default_factory=lambda: os.getenv("MOCK_MODE", "true").lower() == "true")
    publish_auto: bool = Field(default_factory=lambda: os.getenv("PUBLISH_AUTO", "true").lower() == "true")
    dry_run: bool = Field(default_factory=lambda: os.getenv("PUBLISH_DRY_RUN", "false").lower() == "true")
    
    # Plateformes actives
    enabled_platforms: List[PublicationPlatform] = Field(default_factory=lambda: [
        PublicationPlatform.SHOPIFY,
        PublicationPlatform.WOOCOMMERCE,
        PublicationPlatform.PRESTASHOP
    ])
    
    # Configuration retry
    max_retries: int = 3
    retry_delay_ms: int = 1000
    timeout_seconds: int = 30
    
    # Batch processing
    batch_size: int = 10
    parallel_publications: bool = True
    max_concurrent: int = 5
    
    # Validation
    validate_before_publish: bool = True
    require_images: bool = False
    min_description_length: int = 50
    
    def is_platform_available(self, platform: PublicationPlatform) -> bool:
        """Vérifie si une plateforme est disponible (config + env)"""
        if self.mock_mode:
            return platform in self.enabled_platforms
        
        # Vérification des variables d'environnement pour mode réel
        env_vars = {
            PublicationPlatform.SHOPIFY: ["SHOPIFY_STORE_URL", "SHOPIFY_ACCESS_TOKEN"],
            PublicationPlatform.WOOCOMMERCE: ["WOO_STORE_URL", "WOO_CONSUMER_KEY", "WOO_CONSUMER_SECRET"],
            PublicationPlatform.PRESTASHOP: ["PRESTA_STORE_URL", "PRESTA_API_KEY"]
        }
        
        required_vars = env_vars.get(platform, [])
        return all(os.getenv(var) for var in required_vars)
    
    def get_missing_env_vars(self, platform: PublicationPlatform) -> List[str]:
        """Retourne les variables d'environnement manquantes pour une plateforme"""
        env_vars = {
            PublicationPlatform.SHOPIFY: ["SHOPIFY_STORE_URL", "SHOPIFY_ACCESS_TOKEN"],
            PublicationPlatform.WOOCOMMERCE: ["WOO_STORE_URL", "WOO_CONSUMER_KEY", "WOO_CONSUMER_SECRET"],
            PublicationPlatform.PRESTASHOP: ["PRESTA_STORE_URL", "PRESTA_API_KEY"]
        }
        
        required_vars = env_vars.get(platform, [])
        return [var for var in required_vars if not os.getenv(var)]