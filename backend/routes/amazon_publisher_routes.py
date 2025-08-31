# Amazon Publisher FastAPI Routes - Publication automatique
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from services.amazon_publisher_service import AmazonPublisherService
from models.amazon_publishing import AmazonPublishingResult
from services.amazon_seo_service import AmazonSEORules
from routes.amazon_routes import get_database, get_current_user

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Router setup
publisher_router = APIRouter(prefix="/api/amazon/publisher", tags=["Amazon Publishing"])

# Pydantic Models pour les requêtes
class AmazonPublishRequest(BaseModel):
    """Requête de publication Amazon"""
    product_data: Dict[str, Any] = Field(..., description="Données produit à publier")
    marketplace_id: str = Field(..., description="ID marketplace Amazon")
    options: Dict[str, Any] = Field(default_factory=dict, description="Options de publication")
    
    @validator('marketplace_id')
    def validate_marketplace_id(cls, v):
        valid_marketplaces = [
            'ATVPDKIKX0DER', 'A2EUQ1WTGCTBG2', 'A1AM78C64UM0Y8',
            'A1PA6795UKMFR9', 'A1RKKUPIHCS9HS', 'A13V1IB3VIYZZH',
            'A21TJRUUN4KGV', 'APJ6JRA9NG5V4', 'A1F83G8C2ARO7P',
            'A1VC38T7YXB528', 'ARBP9OOSHTCHU'
        ]
        if v not in valid_marketplaces:
            raise ValueError(f"Marketplace ID invalide: {v}")
        return v

class AmazonUpdateRequest(BaseModel):
    """Requête de mise à jour listing Amazon"""
    listing_id: str = Field(..., description="ID du listing Amazon")
    update_data: Dict[str, Any] = Field(..., description="Données à mettre à jour")
    marketplace_id: str = Field(..., description="ID marketplace Amazon")

class SEOOptimizationRequest(BaseModel):
    """Requête d'optimisation SEO"""
    product_data: Dict[str, Any] = Field(..., description="Données produit à optimiser")
    marketplace_id: Optional[str] = Field(None, description="Marketplace pour optimisation ciblée")

class AmazonPublishResponse(BaseModel):
    """Réponse de publication Amazon"""
    success: bool
    listing_id: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    seo_score: float = 0.0
    published_at: datetime
    recommendations: List[str] = Field(default_factory=list)

class SEOOptimizationResponse(BaseModel):
    """Réponse d'optimisation SEO"""
    optimized_title: str
    bullet_points: List[str]
    description: str
    backend_keywords: str
    seo_score: float
    recommendations: List[str]
    issues: List[str] = Field(default_factory=list)

# Endpoint de publication de produit
@publisher_router.post("/publish", response_model=AmazonPublishResponse)
async def publish_product_to_amazon(
    request: AmazonPublishRequest,
    current_user: str = Depends(get_current_user),
    db=Depends(get_database),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Publie un produit sur Amazon avec optimisation SEO automatique
    
    Cette route:
    1. Valide les données produit
    2. Optimise le contenu selon les règles Amazon A9/A10
    3. Publie via SP-API avec la connexion utilisateur
    4. Retourne le résultat avec score SEO et recommandations
    
    Sécurité:
    - Authentification JWT requise
    - Validation des données produit
    - Vérification de la connexion Amazon active
    """
    try:
        logger.info(f"📤 Demande publication Amazon pour user {current_user[:8]}*** marketplace {request.marketplace_id}")
        
        # Initialiser le service de publication  
        publisher_service = AmazonPublisherService(db)
        
        # BLOC 2 PHASE 2: Vérification de connexion Amazon (HTTP 412)
        from services.amazon_connection_service import AmazonConnectionService
        connection_service = AmazonConnectionService(db)
        connection = await connection_service.get_active_connection(current_user)
        
        if not connection:
            logger.warning(f"❌ HTTP 412: Aucune connexion Amazon pour user {current_user[:8]}***")
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail={
                    "error": "Aucune connexion Amazon active",
                    "message": "Vous devez d'abord vous connecter à Amazon Seller Central pour publier des produits.",
                    "action_required": "connection",
                    "redirect_url": "/integrations/amazon/connect",
                    "marketplace_id": request.marketplace_id
                }
            )
        
        # Validation des données produit requises
        required_fields = ['product_name', 'description']
        missing_fields = [field for field in required_fields if not request.product_data.get(field)]
        
        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Champs requis manquants: {', '.join(missing_fields)}"
            )
        
        # Publication du produit
        result = await publisher_service.publish_product_to_amazon(
            user_id=current_user,
            product_data=request.product_data,
            marketplace_id=request.marketplace_id,
            options=request.options
        )
        
        # Préparation de la réponse
        response = AmazonPublishResponse(
            success=result.success,
            listing_id=result.listing_id,
            errors=result.errors,
            warnings=result.warnings,
            seo_score=result.seo_score,
            published_at=result.published_at,
            recommendations=request.product_data.get('seo_recommendations', [])
        )
        
        # Log du résultat
        if result.success:
            logger.info(f"✅ Publication Amazon réussie: listing {result.listing_id}")
        else:
            logger.error(f"❌ Publication Amazon échouée: {result.errors}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur publication Amazon: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne lors de la publication"
        )

# Endpoint de mise à jour de listing
@publisher_router.put("/update", response_model=AmazonPublishResponse)
async def update_amazon_listing(
    request: AmazonUpdateRequest,
    current_user: str = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Met à jour un listing Amazon existant
    
    Cette route:
    1. Vérifie que l'utilisateur possède le listing
    2. Optimise les nouvelles données
    3. Met à jour via SP-API
    4. Retourne le résultat de la mise à jour
    """
    try:
        logger.info(f"📝 Mise à jour listing Amazon {request.listing_id}")
        
        publisher_service = AmazonPublisherService(db)
        
        # Mise à jour du listing
        result = await publisher_service.update_amazon_listing(
            user_id=current_user,
            listing_id=request.listing_id,
            update_data=request.update_data,
            marketplace_id=request.marketplace_id
        )
        
        response = AmazonPublishResponse(
            success=result.success,
            listing_id=result.listing_id,
            errors=result.errors,
            warnings=result.warnings,
            seo_score=result.seo_score,
            published_at=result.published_at
        )
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour listing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour"
        )

# Endpoint d'optimisation SEO
@publisher_router.post("/optimize-seo", response_model=SEOOptimizationResponse)
async def optimize_product_seo(
    request: SEOOptimizationRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Optimise le contenu produit pour Amazon SEO (A9/A10)
    
    Cette route:
    1. Analyse les données produit
    2. Applique les règles SEO Amazon
    3. Génère titre, bullets, description optimisés
    4. Calcule un score SEO et fournit des recommandations
    
    Utile pour:
    - Prévisualiser l'optimisation avant publication
    - Améliorer le SEO de produits existants
    - Analyser la qualité du contenu
    """
    try:
        logger.info(f"🎯 Optimisation SEO Amazon pour user {current_user[:8]}***")
        
        seo_service = AmazonSEORules()
        
        # Optimisation du titre
        optimized_title, title_recommendations = seo_service.optimize_title(request.product_data)
        
        # Génération des bullet points
        bullet_points, bullet_recommendations = seo_service.generate_bullet_points(request.product_data)
        
        # Optimisation de la description
        description, desc_recommendations = seo_service.optimize_description(request.product_data)
        
        # Génération des mots-clés backend
        backend_keywords, keyword_recommendations = seo_service.generate_backend_keywords(request.product_data)
        
        # Compilation du listing optimisé pour validation
        optimized_listing = {
            'title': optimized_title,
            'bullet_points': bullet_points,
            'description': description,
            'backend_keywords': backend_keywords,
            'images': request.product_data.get('images', [])
        }
        
        # Validation SEO complète
        validation = seo_service.validate_listing(optimized_listing)
        
        # Compilation de toutes les recommandations
        all_recommendations = (
            title_recommendations + 
            bullet_recommendations + 
            desc_recommendations + 
            keyword_recommendations
        )
        
        response = SEOOptimizationResponse(
            optimized_title=optimized_title,
            bullet_points=bullet_points,
            description=description,
            backend_keywords=backend_keywords,
            seo_score=validation.score,
            recommendations=all_recommendations,
            issues=validation.issues
        )
        
        logger.info(f"✅ SEO optimisé - Score: {validation.score:.2f}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Erreur optimisation SEO: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'optimisation SEO"
        )

# Endpoint de statut de listing
@publisher_router.get("/listings/{listing_id}/status")
async def get_amazon_listing_status(
    listing_id: str,
    marketplace_id: str,
    current_user: str = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Récupère le statut d'un listing Amazon
    
    Retourne:
    - Statut actuel du listing (ACTIVE, PENDING, SUPPRESSED, etc.)
    - Dernière mise à jour
    - Erreurs ou avertissements éventuels
    """
    try:
        publisher_service = AmazonPublisherService(db)
        
        status_data = await publisher_service.get_amazon_listing_status(
            user_id=current_user,
            listing_id=listing_id,
            marketplace_id=marketplace_id
        )
        
        return status_data
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération statut: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération du statut"
        )

# Endpoint de liste des publications
@publisher_router.get("/publications")
async def get_user_publications(
    limit: int = 20,
    offset: int = 0,
    marketplace_id: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Récupère l'historique des publications Amazon de l'utilisateur
    
    Paramètres:
    - limit: Nombre maximum de résultats (défaut: 20)
    - offset: Décalage pour pagination (défaut: 0)
    - marketplace_id: Filtrer par marketplace (optionnel)
    """
    try:
        # Construire le filtre de requête
        query_filter = {"user_id": current_user}
        if marketplace_id:
            query_filter["marketplace_id"] = marketplace_id
        
        # Récupérer les publications
        publications_cursor = db.amazon_publications.find(
            query_filter
        ).sort("published_at", -1).skip(offset).limit(limit)
        
        publications = await publications_cursor.to_list(length=limit)
        
        # Compter le total pour la pagination
        total_count = await db.amazon_publications.count_documents(query_filter)
        
        # Formatter les résultats
        formatted_publications = []
        for pub in publications:
            formatted_pub = {
                "listing_id": pub.get("listing_id"),
                "success": pub.get("success", False),
                "seo_score": pub.get("seo_score", 0.0),
                "published_at": pub.get("published_at"),
                "errors": pub.get("errors", []),
                "warnings": pub.get("warnings", [])
            }
            formatted_publications.append(formatted_pub)
        
        return {
            "publications": formatted_publications,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération publications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des publications"
        )

# Endpoint de validation SEO
@publisher_router.post("/validate-seo")
async def validate_amazon_seo(
    listing_data: Dict[str, Any],
    current_user: str = Depends(get_current_user)
):
    """
    Valide le SEO d'un listing Amazon sans l'optimiser
    
    Utile pour:
    - Vérifier la conformité d'un listing existant
    - Auditer le SEO avant publication
    - Obtenir des recommandations d'amélioration
    """
    try:
        seo_service = AmazonSEORules()
        validation = seo_service.validate_listing(listing_data)
        
        return {
            "is_valid": validation.is_valid,
            "score": validation.score,
            "issues": validation.issues,
            "recommendations": validation.recommendations,
            "validation_details": {
                "title_length": len(listing_data.get('title', '')),
                "bullet_points_count": len(listing_data.get('bullet_points', [])),
                "description_length": len(listing_data.get('description', '')),
                "backend_keywords_bytes": len(listing_data.get('backend_keywords', '').encode('utf-8')),
                "images_count": len(listing_data.get('images', []))
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur validation SEO: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la validation SEO"
        )

# BLOC 2 PHASE 2: Endpoint avec generic orchestrator et ProductDTO mapping
@publisher_router.post("/publish-via-orchestrator", response_model=AmazonPublishResponse)
async def publish_via_generic_orchestrator(
    product_dto: Dict[str, Any],
    marketplace_id: str,
    options: Dict[str, Any] = {},
    current_user: str = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Publication via l'orchestrateur générique avec mapping ProductDTO
    
    Cette route implémente Bloc 2 Phase 2:
    1. Utilise le generic orchestrator Amazon
    2. Mappe ProductDTO vers Amazon Listing format
    3. Gestion retry/backoff pour quotas SP-API
    4. Stockage du feedId pour suivi
    5. Gestion HTTP 412 pour connexion manquante
    """
    try:
        logger.info(f"🔄 Publication via orchestrateur - user {current_user[:8]}*** marketplace {marketplace_id}")
        
        # Initialiser le publisher générique Amazon
        from src.scraping.publication.publishers.amazon_spapi import AmazonSPAPIPublisher
        amazon_publisher = AmazonSPAPIPublisher(db)
        
        # Options de publication avec retry
        publish_options = {
            "marketplace_id": marketplace_id,
            "max_retries": options.get("max_retries", 3),
            "include_images": options.get("include_images", True)
        }
        
        # Publication via l'orchestrateur avec ProductDTO mapping
        result = await amazon_publisher.publish(
            user_id=current_user,
            product_dto=product_dto,
            options=publish_options
        )
        
        # Conversion vers le format de réponse standard
        if result["success"]:
            response = AmazonPublishResponse(
                success=True,
                listing_id=result.get("listing_id"),
                errors=[],
                warnings=[],
                seo_score=result.get("seo_score", 0.0),
                published_at=result.get("published_at", datetime.utcnow()),
                recommendations=[]
            )
            logger.info(f"✅ Publication orchestrateur réussie: feedId {result.get('feed_id')}")
        else:
            # Gestion des erreurs spécifiques
            if result.get("error_code") == "HTTP_412":
                raise HTTPException(
                    status_code=status.HTTP_412_PRECONDITION_FAILED,
                    detail=result.get("error")
                )
            elif result.get("error_code") == "QUOTA_ERROR":
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Quota SP-API dépassé, veuillez réessayer plus tard"
                )
            else:
                response = AmazonPublishResponse(
                    success=False,
                    listing_id=None,
                    errors=result.get("errors", [result.get("error", "Erreur inconnue")]),
                    warnings=[],
                    seo_score=0.0,
                    published_at=datetime.utcnow(),
                    recommendations=[]
                )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur orchestrateur Amazon: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne de l'orchestrateur"
        )

# BLOC 2 PHASE 2: Endpoint pour récupérer le statut via feedId
@publisher_router.get("/feed/{feed_id}/status")
async def get_feed_status(
    feed_id: str,
    current_user: str = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Récupère le statut d'une publication via feedId
    
    Fonctionnalité Bloc 2 Phase 2:
    - Suivi des publications via feedId stocké
    - Statut temps réel depuis Amazon SP-API
    """
    try:
        logger.info(f"📊 Statut feed {feed_id} pour user {current_user[:8]}***")
        
        # Utiliser l'orchestrateur pour récupérer le statut
        from src.scraping.publication.publishers.amazon_spapi import AmazonSPAPIPublisher
        amazon_publisher = AmazonSPAPIPublisher(db)
        
        status = await amazon_publisher.get_publication_status(
            user_id=current_user,
            feed_id=feed_id
        )
        
        return status
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération statut feed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération du statut"
        )
# BLOC 2 PHASE 2: Endpoint pour tests Sandbox réels
@publisher_router.post("/test-sandbox")
async def run_sandbox_tests(
    current_user: str = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Lance une suite complète de tests Amazon Sandbox
    
    Tests Bloc 2 Phase 2:
    1. Vérification connexion active  
    2. Validation token d'accès
    3. Test endpoints Catalog/Listings
    4. Gestion erreur HTTP 412
    5. Mécanisme retry/backoff
    6. Mapping ProductDTO  
    7. Stockage feedId
    """
    try:
        logger.info(f"🧪 Lancement tests Sandbox pour user {current_user[:8]}***")
        
        # Initialiser le service de tests
        from services.amazon_sandbox_testing_service import AmazonSandboxTestingService
        sandbox_service = AmazonSandboxTestingService(db)
        
        # Lancer la suite de tests complète
        test_report = await sandbox_service.run_comprehensive_sandbox_tests(current_user)
        
        return test_report
        
    except Exception as e:
        logger.error(f"❌ Erreur tests Sandbox: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors des tests Sandbox"
        )

# Endpoint de test de connexion SP-API
@publisher_router.post("/test-connection")
async def test_spapi_connection(
    marketplace_id: str,
    current_user: str = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Teste la connexion SP-API pour un marketplace donné
    
    Vérifie:
    - Connexion Amazon active
    - Validité du token d'accès
    - Accès aux API de publication
    - Permissions sur le marketplace
    """
    try:
        publisher_service = AmazonPublisherService(db)
        
        # Test simple : récupération du statut d'un listing fictif
        test_result = await publisher_service.get_amazon_listing_status(
            user_id=current_user,
            listing_id="TEST",
            marketplace_id=marketplace_id
        )
        
        if "error" in test_result:
            return {
                "connected": False,
                "error": test_result["error"],
                "marketplace_id": marketplace_id
            }
        
        return {
            "connected": True,
            "marketplace_id": marketplace_id,
            "test_time": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur test connexion: {str(e)}")
        return {
            "connected": False,
            "error": f"Test échoué: {str(e)}",
            "marketplace_id": marketplace_id
        }