"""
Product DTO - Structure de données pour les produits extraits
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, validator, Field
from decimal import Decimal
from enum import Enum
from datetime import datetime
import re


class Currency(str, Enum):
    """Devises supportées"""
    EUR = "EUR"
    USD = "USD"
    GBP = "GBP"


class PriceDTO(BaseModel):
    """Structure prix avec validation stricte"""
    amount: Decimal = Field(..., ge=0, description="Montant >= 0")
    currency: Currency = Field(..., description="Devise supportée")
    original_text: Optional[str] = Field(None, description="Texte prix original")


class ImageDTO(BaseModel):
    """Structure image avec validation HTTPS"""
    url: str = Field(..., description="URL image HTTPS uniquement")
    alt: str = Field(..., min_length=1, description="Texte alternatif non vide")
    width: Optional[int] = Field(None, ge=1)
    height: Optional[int] = Field(None, ge=1)
    size_bytes: Optional[int] = Field(None, ge=0)
    
    @validator('url')
    def validate_https_url(cls, v):
        if not v.startswith('https://'):
            raise ValueError('URL image doit être en HTTPS')
        return v
    
    @validator('alt')
    def validate_alt_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Texte alternatif ne peut pas être vide')
        return v.strip()


class ProductStatus(str, Enum):
    """Status du produit extrait"""
    COMPLETE = "complete"
    INCOMPLETE_MEDIA = "incomplete_media"  # Pas d'image valide
    INCOMPLETE_PRICE = "incomplete_price"   # Prix non détecté
    INCOMPLETE_DATA = "incomplete_data"     # Données manquantes


class ProductDTO(BaseModel):
    """Structure complète produit avec validation stricte et SEO dynamique"""
    
    # Champs obligatoires
    title: str = Field(..., min_length=1, max_length=500, description="Titre produit")
    description_html: str = Field(..., description="Description HTML sanitizée")
    price: Optional[PriceDTO] = Field(None, description="Prix si détecté")
    images: List[ImageDTO] = Field(..., min_items=1, description="Au moins 1 image")
    
    # Métadonnées
    source_url: str = Field(..., description="URL source du produit")
    attributes: Dict[str, str] = Field(default_factory=dict, description="Attributs extraits")
    status: ProductStatus = Field(default=ProductStatus.COMPLETE, description="Status extraction")
    
    # SEO et idempotence
    payload_signature: str = Field(..., description="Hash du contenu pour idempotence")
    extraction_timestamp: float = Field(..., description="Timestamp extraction")
    
    # Nouveaux champs SEO dynamiques
    seo_title: Optional[str] = Field(None, description="Titre SEO optimisé avec année courante")
    seo_description: Optional[str] = Field(None, description="Meta description avec année")
    seo_keywords: List[str] = Field(default_factory=list, description="Mots-clés SEO")
    structured_data: Optional[Dict[str, Any]] = Field(None, description="JSON-LD structured data")
    current_year: int = Field(default_factory=lambda: datetime.now().year, description="Année courante")
    
    @validator('title')
    def validate_title(cls, v):
        return v.strip()
    
    @validator('description_html')
    def validate_description_html(cls, v):
        # HTML déjà sanitizé par le normalizer
        return v.strip()
    
    @validator('images')
    def validate_at_least_one_image(cls, v):
        if len(v) == 0:
            raise ValueError('Au moins une image requise')
        return v
    
    @validator('source_url')
    def validate_source_https(cls, v):
        if not v.startswith('https://'):
            raise ValueError('URL source doit être en HTTPS')
        return v
    
    @validator('payload_signature')
    def validate_signature_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Signature payload requise pour idempotence')
        return v.strip()
    
    def is_complete(self) -> bool:
        """Vérifie si le produit est complet"""
        return self.status == ProductStatus.COMPLETE
    
    def get_primary_image(self) -> Optional[ImageDTO]:
        """Retourne la première image (principale)"""
        return self.images[0] if self.images else None
    
    def get_price_display(self) -> str:
        """Affichage formaté du prix"""
        if not self.price:
            return "Prix non disponible"
        return f"{self.price.amount} {self.price.currency.value}"


class ProductPlaceholder:
    """Factory pour créer des placeholders"""
    
    @staticmethod
    def create_incomplete_media_product(
        title: str,
        description_html: str,
        source_url: str,
        payload_signature: str,
        extraction_timestamp: float,
        price: Optional[PriceDTO] = None,
        attributes: Optional[Dict[str, str]] = None
    ) -> ProductDTO:
        """Crée un produit avec placeholder image"""
        
        placeholder_image = ImageDTO(
            url="https://via.placeholder.com/400x300/cccccc/666666?text=Image+Non+Disponible",
            alt="Image produit non disponible",
            width=400,
            height=300
        )
        
        return ProductDTO(
            title=title,
            description_html=description_html,
            price=price,
            images=[placeholder_image],
            source_url=source_url,
            attributes=attributes or {},
            status=ProductStatus.INCOMPLETE_MEDIA,
            payload_signature=payload_signature,
            extraction_timestamp=extraction_timestamp
        )