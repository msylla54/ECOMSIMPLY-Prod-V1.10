# Amazon Publishing Models - Modèles pour la publication Amazon
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import uuid

class AmazonPublicationStatus(str, Enum):
    """Statuts de publication Amazon"""
    PENDING = "pending"
    PROCESSING = "processing"
    ACTIVE = "active"
    SUPPRESSED = "suppressed"
    INCOMPLETE = "incomplete"
    INVALID = "invalid"
    REJECTED = "rejected"

class AmazonImageRequirements(BaseModel):
    """Exigences d'images Amazon"""
    min_width: int = 1000
    min_height: int = 1000
    max_file_size_mb: int = 10
    allowed_formats: List[str] = ["JPEG", "PNG", "GIF", "TIFF"]
    white_background_required: bool = True  # Pour image principale
    max_images_count: int = 9

class AmazonListingImage(BaseModel):
    """Image pour listing Amazon"""
    url: str = Field(..., description="URL de l'image")
    alt_text: str = Field("", description="Texte alternatif")
    is_main: bool = Field(False, description="Image principale")
    width: int = Field(0, description="Largeur en pixels")
    height: int = Field(0, description="Hauteur en pixels")
    file_size_mb: float = Field(0.0, description="Taille du fichier en MB")
    format: str = Field("JPEG", description="Format de l'image")
    
    # Conformité Amazon
    amazon_compliant: bool = Field(False, description="Conforme aux exigences Amazon")
    compliance_issues: List[str] = Field(default_factory=list, description="Problèmes de conformité")
    
    @validator('format')
    def validate_format(cls, v):
        allowed = ["JPEG", "JPG", "PNG", "GIF", "TIFF"]
        if v.upper() not in allowed:
            raise ValueError(f"Format non supporté: {v}. Formats autorisés: {allowed}")
        return v.upper()
    
    def check_amazon_compliance(self) -> bool:
        """Vérifie la conformité aux exigences Amazon"""
        issues = []
        
        # Vérifier les dimensions
        if self.width < 1000 or self.height < 1000:
            issues.append(f"Dimensions insuffisantes: {self.width}x{self.height} (minimum 1000x1000)")
        
        # Vérifier la taille du fichier
        if self.file_size_mb > 10:
            issues.append(f"Fichier trop volumineux: {self.file_size_mb}MB (maximum 10MB)")
        
        # Vérifier le format
        if self.format not in ["JPEG", "JPG", "PNG", "GIF", "TIFF"]:
            issues.append(f"Format non supporté: {self.format}")
        
        # Image principale doit avoir un fond blanc (à vérifier manuellement)
        if self.is_main:
            issues.append("Vérifiez que l'image principale a un fond blanc")
        
        self.compliance_issues = issues
        self.amazon_compliant = len(issues) == 0
        
        return self.amazon_compliant

class AmazonProductListing(BaseModel):
    """Modèle complet de listing produit Amazon"""
    # Identifiants
    listing_id: Optional[str] = Field(None, description="ID du listing Amazon")
    sku: str = Field(..., description="SKU unique du produit")
    asin: Optional[str] = Field(None, description="ASIN Amazon (généré par Amazon)")
    
    # Informations produit de base
    title: str = Field(..., min_length=1, max_length=200, description="Titre du produit")
    brand: str = Field(..., description="Marque du produit")
    manufacturer: Optional[str] = Field(None, description="Fabricant")
    model: Optional[str] = Field(None, description="Modèle")
    
    # Contenu SEO optimisé
    bullet_points: List[str] = Field(..., min_items=5, max_items=5, description="5 points clés du produit")
    description: str = Field(..., description="Description détaillée du produit")
    backend_keywords: str = Field(..., description="Mots-clés backend (Search Terms)")
    
    # Images
    images: List[AmazonListingImage] = Field(default_factory=list, description="Images du produit")
    
    # Informations commerciales
    price: float = Field(..., gt=0, description="Prix de vente")
    currency: str = Field("EUR", description="Devise")
    condition: str = Field("new", description="État du produit")
    quantity: int = Field(1, ge=0, description="Quantité disponible")
    
    # Identifiants produit
    upc: Optional[str] = Field(None, description="Code UPC")
    ean: Optional[str] = Field(None, description="Code EAN")
    isbn: Optional[str] = Field(None, description="Code ISBN pour livres")
    mpn: Optional[str] = Field(None, description="Numéro de pièce fabricant")
    
    # Catégorie et attributs
    category: str = Field("", description="Catégorie principale")
    subcategory: Optional[str] = Field(None, description="Sous-catégorie")
    product_type: str = Field("PRODUCT", description="Type de produit Amazon")
    
    # Dimensions et poids (optionnel)
    dimensions: Optional[Dict[str, float]] = Field(None, description="Dimensions (length, width, height en cm)")
    weight: Optional[float] = Field(None, description="Poids en kg")
    
    # Informations de conformité
    certifications: List[str] = Field(default_factory=list, description="Certifications du produit")
    safety_warnings: List[str] = Field(default_factory=list, description="Avertissements de sécurité")
    
    # Métadonnées de publication
    marketplace_id: str = Field(..., description="ID du marketplace Amazon")
    publication_status: AmazonPublicationStatus = Field(AmazonPublicationStatus.PENDING, description="Statut de publication")
    
    # Validation SEO
    seo_score: float = Field(0.0, ge=0.0, le=1.0, description="Score SEO (0-1)")
    seo_issues: List[str] = Field(default_factory=list, description="Problèmes SEO détectés")
    seo_recommendations: List[str] = Field(default_factory=list, description="Recommandations SEO")
    
    # Horodatage
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = Field(None, description="Date de publication sur Amazon")
    
    @validator('bullet_points')
    def validate_bullet_points(cls, v):
        if len(v) != 5:
            raise ValueError("Exactement 5 bullet points requis pour Amazon")
        
        for i, bullet in enumerate(v):
            if len(bullet) > 255:
                raise ValueError(f"Bullet point {i+1} trop long (max 255 caractères)")
            if len(bullet) < 10:
                raise ValueError(f"Bullet point {i+1} trop court (min 10 caractères)")
        
        return v
    
    @validator('backend_keywords')
    def validate_backend_keywords(cls, v):
        # Vérifier la limite de 250 bytes
        if len(v.encode('utf-8')) > 250:
            raise ValueError("Mots-clés backend dépassent 250 bytes")
        
        # Vérifier qu'il n'y a pas de virgules (Amazon préfère les espaces)
        if ',' in v:
            raise ValueError("Utilisez des espaces pour séparer les mots-clés, pas de virgules")
        
        return v
    
    @validator('title')
    def validate_title(cls, v):
        # Vérifier les mots interdits par Amazon
        forbidden_words = [
            'best', 'meilleur', 'top', '#1', 'nouveau', 'new',
            'livraison gratuite', 'free shipping', 'promo', 'sale'
        ]
        
        v_lower = v.lower()
        found_forbidden = [word for word in forbidden_words if word in v_lower]
        
        if found_forbidden:
            raise ValueError(f"Mots interdits dans le titre: {', '.join(found_forbidden)}")
        
        return v
    
    def calculate_seo_score(self) -> float:
        """Calcule le score SEO basé sur les critères Amazon"""
        score = 0.0
        max_score = 100.0
        
        # Titre (25 points)
        if 50 <= len(self.title) <= 200:
            score += 25
        elif 30 <= len(self.title) < 50:
            score += 15
        else:
            score += 5
        
        # Bullet points (30 points)
        if len(self.bullet_points) == 5:
            score += 20
            # Bonus pour la qualité des bullets
            if all(len(bullet) >= 50 for bullet in self.bullet_points):
                score += 10
        
        # Description (20 points)
        if 500 <= len(self.description) <= 2000:
            score += 20
        elif 200 <= len(self.description) < 500:
            score += 15
        else:
            score += 5
        
        # Mots-clés backend (15 points)
        if 100 <= len(self.backend_keywords) <= 250:
            score += 15
        elif 50 <= len(self.backend_keywords) < 100:
            score += 10
        else:
            score += 5
        
        # Images (10 points)
        if self.images:
            compliant_images = sum(1 for img in self.images if img.check_amazon_compliance())
            score += min(10, compliant_images * 2)
        
        return min(1.0, score / max_score)
    
    def validate_for_amazon(self) -> Dict[str, Any]:
        """Validation complète pour Amazon"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "seo_score": 0.0
        }
        
        try:
            # Vérifier les champs requis
            required_fields = ['title', 'brand', 'bullet_points', 'description', 'price']
            missing_fields = [field for field in required_fields if not getattr(self, field)]
            
            if missing_fields:
                validation_result["errors"].extend([f"Champ requis manquant: {field}" for field in missing_fields])
                validation_result["is_valid"] = False
            
            # Calculer le score SEO
            seo_score = self.calculate_seo_score()
            validation_result["seo_score"] = seo_score
            self.seo_score = seo_score
            
            # Vérifier les images
            if not self.images:
                validation_result["warnings"].append("Aucune image fournie")
            else:
                main_images = [img for img in self.images if img.is_main]
                if not main_images:
                    validation_result["warnings"].append("Aucune image principale définie")
                elif len(main_images) > 1:
                    validation_result["errors"].append("Une seule image principale autorisée")
                    validation_result["is_valid"] = False
            
            # Vérifier les identifiants produit
            if not any([self.upc, self.ean, self.isbn]):
                validation_result["warnings"].append("Aucun identifiant produit (UPC/EAN/ISBN) fourni")
            
            # Score SEO minimum requis
            if seo_score < 0.7:
                validation_result["warnings"].append(f"Score SEO faible: {seo_score:.2f} (recommandé: ≥0.7)")
            
        except Exception as e:
            validation_result["errors"].append(f"Erreur de validation: {str(e)}")
            validation_result["is_valid"] = False
        
        return validation_result

class AmazonPublicationRecord(BaseModel):
    """Enregistrement de publication Amazon"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="ID utilisateur ECOMSIMPLY")
    connection_id: str = Field(..., description="ID de la connexion Amazon")
    
    # Données du listing
    listing: AmazonProductListing = Field(..., description="Données du listing publié")
    
    # Résultat de publication
    success: bool = Field(False, description="Succès de la publication")
    listing_id: Optional[str] = Field(None, description="ID du listing Amazon créé")
    submission_id: Optional[str] = Field(None, description="ID de soumission Amazon")
    
    # Erreurs et avertissements
    errors: List[str] = Field(default_factory=list, description="Erreurs de publication")
    warnings: List[str] = Field(default_factory=list, description="Avertissements")
    
    # Métriques
    processing_time_seconds: float = Field(0.0, description="Temps de traitement en secondes")
    retry_count: int = Field(0, description="Nombre de tentatives")
    
    # Horodatage
    created_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = Field(None, description="Date de publication réussie")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AmazonMarketplaceConfig(BaseModel):
    """Configuration par marketplace Amazon"""
    marketplace_id: str = Field(..., description="ID du marketplace")
    name: str = Field(..., description="Nom du marketplace")
    country_code: str = Field(..., description="Code pays (FR, US, etc.)")
    currency: str = Field(..., description="Devise par défaut")
    language: str = Field(..., description="Langue par défaut")
    
    # URLs SP-API
    spapi_endpoint: str = Field(..., description="Endpoint SP-API pour cette région")
    
    # Exigences spécifiques
    requires_tax_info: bool = Field(False, description="Informations fiscales requises")
    requires_certification: bool = Field(False, description="Certifications requises")
    restricted_categories: List[str] = Field(default_factory=list, description="Catégories restreintes")
    
    # Configuration SEO
    title_max_length: int = Field(200, description="Longueur max du titre")
    keyword_language_code: str = Field("fr-FR", description="Code langue pour mots-clés")
    
    @classmethod
    def get_marketplace_configs(cls) -> Dict[str, "AmazonMarketplaceConfig"]:
        """Retourne les configurations des marketplaces supportés"""
        configs = {
            "A13V1IB3VIYZZH": cls(
                marketplace_id="A13V1IB3VIYZZH",
                name="Amazon France",
                country_code="FR", 
                currency="EUR",
                language="fr-FR",
                spapi_endpoint="https://sellingpartnerapi-eu.amazon.com",
                keyword_language_code="fr-FR"
            ),
            "A1PA6795UKMFR9": cls(
                marketplace_id="A1PA6795UKMFR9",
                name="Amazon Germany",
                country_code="DE",
                currency="EUR", 
                language="de-DE",
                spapi_endpoint="https://sellingpartnerapi-eu.amazon.com",
                keyword_language_code="de-DE"
            ),
            "ATVPDKIKX0DER": cls(
                marketplace_id="ATVPDKIKX0DER", 
                name="Amazon US",
                country_code="US",
                currency="USD",
                language="en-US",
                spapi_endpoint="https://sellingpartnerapi-na.amazon.com",
                keyword_language_code="en-US"
            ),
            "A1F83G8C2ARO7P": cls(
                marketplace_id="A1F83G8C2ARO7P",
                name="Amazon UK", 
                country_code="GB",
                currency="GBP",
                language="en-GB", 
                spapi_endpoint="https://sellingpartnerapi-eu.amazon.com",
                keyword_language_code="en-GB"
            )
        }
        
        return configs

class AmazonPublishingResult(BaseModel):
    """Résultat d'une opération de publication Amazon"""
    success: bool = Field(False, description="Succès de l'opération")
    sku: Optional[str] = Field(None, description="SKU du produit")
    asin: Optional[str] = Field(None, description="ASIN Amazon")
    feed_id: Optional[str] = Field(None, description="ID du feed Amazon")
    submission_id: Optional[str] = Field(None, description="ID de soumission")
    
    # Messages et erreurs
    message: str = Field("", description="Message de résultat")
    errors: List[str] = Field(default_factory=list, description="Erreurs rencontrées")
    warnings: List[str] = Field(default_factory=list, description="Avertissements")
    
    # Statut de traitement
    status: str = Field("PENDING", description="Statut du traitement")
    processing_time: float = Field(0.0, description="Temps de traitement en secondes")
    
    # Métadonnées
    marketplace_id: str = Field("", description="Marketplace de publication")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)