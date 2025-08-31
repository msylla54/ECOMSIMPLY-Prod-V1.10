# Routes Amazon Orchestrator - Publication via orchestrateur générique
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from publication.publishers.amazon_spapi import (
    PublicationOrchestrator, ProductDTO, PublicationChannel
)
from routes.amazon_routes import get_database, get_current_user

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Router setup
orchestrator_router = APIRouter(prefix="/api/publication", tags=["Publication Orchestrator"])

# Pydantic Models
class ProductPublicationRequest(BaseModel):
    """Requête de publication générique avec ProductDTO"""
    # Identifiants
    product_id: str = Field(..., description="Identifiant unique du produit")
    sku: str = Field(..., description="SKU du produit")
    
    # Informations de base
    title: str = Field(..., min_length=1, max_length=200, description="Titre du produit")
    brand: str = Field(..., description="Marque du produit")
    description: str = Field(..., min_length=10, description="Description détaillée")
    
    # Contenu structuré
    bullet_points: List[str] = Field(default_factory=list, description="Points clés du produit")
    key_features: List[str] = Field(default_factory=list, description="Caractéristiques principales")
    benefits: List[str] = Field(default_factory=list, description="Avantages du produit")
    
    # Informations commerciales
    price: float = Field(..., gt=0, description="Prix de vente")
    currency: str = Field("EUR", description="Devise")
    stock_quantity: int = Field(1, ge=0, description="Quantité en stock")
    condition: str = Field("new", description="État du produit")
    
    # Identifiants produit
    ean: Optional[str] = Field(None, description="Code EAN")
    upc: Optional[str] = Field(None, description="Code UPC")
    gtin: Optional[str] = Field(None, description="Code GTIN")
    mpn: Optional[str] = Field(None, description="Numéro de pièce fabricant")
    
    # Médias
    images: List[Dict[str, Any]] = Field(default_factory=list, description="Images du produit")
    
    # Métadonnées
    category: str = Field("", description="Catégorie du produit")
    tags: List[str] = Field(default_factory=list, description="Tags du produit")
    
    @validator('bullet_points')
    def validate_bullet_points(cls, v):
        if len(v) > 5:
            raise ValueError("Maximum 5 bullet points autorisés")
        return v
    
    @validator('title')
    def validate_title_length(cls, v):
        if len(v) > 200:
            raise ValueError("Titre maximum 200 caractères")
        return v

class ChannelPublicationRequest(BaseModel):
    """Requête de publication vers un canal spécifique"""
    channel: PublicationChannel = Field(..., description="Canal de publication")
    product: ProductPublicationRequest = Field(..., description="Données produit")
    channel_config: Dict[str, Any] = Field(default_factory=dict, description="Configuration canal")
    
    @validator('channel_config')
    def validate_amazon_config(cls, v, values):
        """Validation configuration Amazon"""
        if values.get('channel') == PublicationChannel.AMAZON:
            if 'marketplace_id' not in v:
                v['marketplace_id'] = 'A13V1IB3VIYZZH'  # France par défaut
            
            # Valider marketplace_id
            valid_marketplaces = [
                'ATVPDKIKX0DER', 'A2EUQ1WTGCTBG2', 'A1AM78C64UM0Y8',
                'A1PA6795UKMFR9', 'A1RKKUPIHCS9HS', 'A13V1IB3VIYZZH',
                'A21TJRUUN4KGV', 'APJ6JRA9NG5V4', 'A1F83G8C2ARO7P',
                'A1VC38T7YXB528', 'ARBP9OOSHTCHU'
            ]
            
            if v['marketplace_id'] not in valid_marketplaces:
                raise ValueError(f"Marketplace ID invalide: {v['marketplace_id']}")
        
        return v

class PublicationResponse(BaseModel):
    """Réponse de publication générique"""
    success: bool
    channel: PublicationChannel
    listing_id: Optional[str] = None
    feed_id: Optional[str] = None
    submission_id: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    published_at: str
    processing_time_ms: Optional[float] = None

# Endpoint de publication générique
@orchestrator_router.post("/publish", response_model=PublicationResponse)
async def publish_product_to_channel(
    request: ChannelPublicationRequest,
    current_user: str = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Publie un produit vers un canal spécifique via l'orchestrateur
    
    Cette route:
    1. Valide les données produit et configuration canal
    2. Convertit la requête en ProductDTO unifié
    3. Utilise l'orchestrateur pour publier vers le canal demandé
    4. Retourne le résultat de publication avec feedId (Amazon)
    
    Canaux supportés:
    - amazon: Requiert marketplace_id, use_images (optionnel)
    
    Erreurs spécifiques:
    - 412 PRECONDITION_FAILED: Connexion canal requise
    - 400 BAD_REQUEST: Données invalides
    - 429 TOO_MANY_REQUESTS: Quota canal dépassé (avec retry automatique)
    """
    try:
        start_time = datetime.utcnow()
        
        logger.info(f"📤 Publication {request.channel} pour user {current_user[:8]}*** produit {request.product.sku}")
        
        # Convertir requête en ProductDTO
        product_dto = ProductDTO(
            product_id=request.product.product_id,
            sku=request.product.sku,
            title=request.product.title,
            brand=request.product.brand,
            description=request.product.description,
            bullet_points=request.product.bullet_points,
            key_features=request.product.key_features,
            benefits=request.product.benefits,
            price=request.product.price,
            currency=request.product.currency,
            stock_quantity=request.product.stock_quantity,
            condition=request.product.condition,
            ean=request.product.ean,
            upc=request.product.upc,
            gtin=request.product.gtin,
            mpn=request.product.mpn,
            images=request.product.images,
            category=request.product.category,
            tags=request.product.tags
        )
        
        # Initialiser orchestrateur
        orchestrator = PublicationOrchestrator(db)
        
        # Publier vers le canal
        result = await orchestrator.publish_to_channel(
            channel=request.channel,
            user_id=current_user,
            product_dto=product_dto,
            channel_config=request.channel_config
        )
        
        # Calculer temps de traitement
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Formatage réponse 
        response = PublicationResponse(
            success=result["success"],
            channel=result["channel"],
            listing_id=result.get("listing_id"),
            feed_id=result.get("feed_id"),
            submission_id=result.get("submission_id"),
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            published_at=result.get("published_at", datetime.utcnow().isoformat()),
            processing_time_ms=processing_time
        )
        
        # Log résultat
        if result["success"]:
            logger.info(f"✅ Publication {request.channel} réussie - feedId: {result.get('feed_id')}")
        else:
            logger.error(f"❌ Publication {request.channel} échouée: {result.get('errors')}")
        
        return response
        
    except HTTPException as e:
        # Réexposer les erreurs HTTP spécifiques (412, etc.)
        raise e
    except Exception as e:
        logger.error(f"❌ Erreur orchestrateur publication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur publication: {str(e)[:100]}"
        )

# Endpoint de publication Amazon directe (raccourci)
@orchestrator_router.post("/amazon/publish", response_model=PublicationResponse)
async def publish_product_to_amazon_direct(
    product: ProductPublicationRequest,
    marketplace_id: str = "A13V1IB3VIYZZH",
    use_images: bool = True,
    current_user: str = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Publication directe vers Amazon (raccourci)
    
    Équivalent à /publish avec channel=amazon mais plus simple d'utilisation.
    Utilise l'orchestrateur en interne pour cohérence.
    """
    try:
        # Construire requête orchestrateur
        channel_request = ChannelPublicationRequest(
            channel=PublicationChannel.AMAZON,
            product=product,
            channel_config={
                "marketplace_id": marketplace_id,
                "use_images": use_images
            }
        )
        
        # Déléguer à l'endpoint générique
        return await publish_product_to_channel(
            request=channel_request,
            current_user=current_user,
            db=db
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur publication Amazon directe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur publication Amazon"
        )

# Endpoint de statut des publications
@orchestrator_router.get("/publications")
async def get_user_publications(
    channel: Optional[PublicationChannel] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: str = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Récupère l'historique des publications multi-canal
    
    Paramètres:
    - channel: Filtrer par canal (optionnel)
    - limit: Nombre maximum de résultats
    - offset: Décalage pour pagination
    """
    try:
        # Construire filtre
        query_filter = {"user_id": current_user}
        if channel:
            query_filter["channel"] = channel
        
        # Récupérer publications
        publications_cursor = db.amazon_publications.find(
            query_filter
        ).sort("published_at", -1).skip(offset).limit(limit)
        
        publications = await publications_cursor.to_list(length=limit)
        
        # Compter total
        total_count = await db.amazon_publications.count_documents(query_filter)
        
        # Formatter résultats
        formatted_publications = []
        for pub in publications:
            formatted_pub = {
                "listing_id": pub.get("listing_id"),
                "feed_id": pub.get("feed_id"),
                "channel": pub.get("channel", "amazon"),
                "product_sku": pub.get("product_sku"),
                "product_title": pub.get("product_title"),
                "success": pub.get("success", False),
                "published_at": pub.get("published_at"),
                "errors": pub.get("errors", []),
                "marketplace_id": pub.get("marketplace_id")
            }
            formatted_publications.append(formatted_pub)
        
        return {
            "publications": formatted_publications,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "filtered_by_channel": channel
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération publications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur récupération publications"
        )

# Endpoint de validation ProductDTO
@orchestrator_router.post("/validate-product")
async def validate_product_data(
    product: ProductPublicationRequest,
    channel: PublicationChannel,
    current_user: str = Depends(get_current_user)
):
    """
    Valide les données produit pour un canal spécifique
    
    Retourne:
    - Validation générale ProductDTO
    - Validation spécifique au canal
    - Recommandations d'amélioration
    """
    try:
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Validation générale ProductDTO
        if not product.title or len(product.title.strip()) < 10:
            validation_result["errors"].append("Titre trop court (minimum 10 caractères)")
            validation_result["valid"] = False
        
        if not product.description or len(product.description.strip()) < 50:
            validation_result["errors"].append("Description trop courte (minimum 50 caractères)")
            validation_result["valid"] = False
        
        if product.price <= 0:
            validation_result["errors"].append("Prix doit être supérieur à 0")
            validation_result["valid"] = False
        
        # Validation spécifique Amazon
        if channel == PublicationChannel.AMAZON:
            if len(product.title) > 200:
                validation_result["errors"].append("Titre Amazon maximum 200 caractères")
                validation_result["valid"] = False
            
            if len(product.bullet_points) == 0:
                validation_result["warnings"].append("Aucun bullet point - recommandé pour Amazon")
            elif len(product.bullet_points) > 5:
                validation_result["errors"].append("Maximum 5 bullet points pour Amazon")
                validation_result["valid"] = False
            
            if not any([product.ean, product.upc, product.gtin]):
                validation_result["warnings"].append("Aucun identifiant produit (EAN/UPC/GTIN) - recommandé")
            
            if not product.images:
                validation_result["warnings"].append("Aucune image - fortement recommandé pour Amazon")
            
            # Recommandations SEO Amazon
            if len(product.bullet_points) < 5:
                validation_result["recommendations"].append("Ajoutez 5 bullet points pour optimiser le référencement Amazon")
            
            if len(product.key_features) < 3:
                validation_result["recommendations"].append("Ajoutez plus de caractéristiques pour améliorer le contenu")
        
        return validation_result
        
    except Exception as e:
        logger.error(f"❌ Erreur validation produit: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur validation produit"
        )