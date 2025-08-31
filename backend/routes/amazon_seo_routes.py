"""
Routes API pour SEO Amazon avancé A9/A10
ECOMSIMPLY Bloc 5 — Phase 5: Amazon SEO Routes

Endpoints pour générer, valider et optimiser les listings Amazon selon les règles SEO.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
import os
from motor.motor_asyncio import AsyncIOMotorClient

from services.amazon_seo_integration_service import get_amazon_seo_integration_service
from services.logging_service import log_info, log_error, log_operation
from modules.security import get_current_user_from_token

# Configuration
router = APIRouter(prefix="/api/amazon/seo", tags=["amazon-seo"])

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db_name = os.environ.get('DB_NAME', 'ecomsimply_production')
db = client[db_name]


# Modèles Pydantic pour les requêtes/réponses

class ProductSEORequest(BaseModel):
    """Requête pour génération SEO d'un produit"""
    product_name: str = Field(..., description="Nom du produit")
    brand: Optional[str] = Field(None, description="Marque du produit")
    model: Optional[str] = Field(None, description="Modèle du produit")
    category: str = Field(..., description="Catégorie du produit")
    features: List[str] = Field(default_factory=list, description="Caractéristiques du produit")
    benefits: List[str] = Field(default_factory=list, description="Bénéfices du produit")
    use_cases: List[str] = Field(default_factory=list, description="Cas d'usage")
    size: Optional[str] = Field(None, description="Taille du produit")
    color: Optional[str] = Field(None, description="Couleur du produit")
    images: List[str] = Field(default_factory=list, description="URLs des images")
    additional_keywords: List[str] = Field(default_factory=list, description="Mots-clés additionnels")


class ListingValidationRequest(BaseModel):
    """Requête pour validation d'un listing existant"""
    title: str = Field(..., description="Titre du listing")
    bullets: List[str] = Field(..., description="Bullet points (5 max)")
    description: str = Field(..., description="Description du produit")
    backend_keywords: str = Field(..., description="Mots-clés backend")
    images: List[str] = Field(default_factory=list, description="URLs des images")
    brand: Optional[str] = Field(None, description="Marque")
    model: Optional[str] = Field(None, description="Modèle")
    category: Optional[str] = Field(None, description="Catégorie")


class ListingOptimizationRequest(BaseModel):
    """Requête pour optimisation d'un listing existant"""
    current_listing: ListingValidationRequest
    optimization_options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Options d'optimisation")


@router.post("/generate")
async def generate_optimized_listing(
    request: ProductSEORequest,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
):
    """
    Génère un listing Amazon optimisé selon les règles SEO A9/A10
    """
    user_id = current_user["user_id"]
    
    log_info(
        "Génération listing SEO Amazon",
        user_id=user_id,
        product_name=request.product_name,
        category=request.category,
        endpoint="POST /api/amazon/seo/generate"
    )
    
    try:
        # Convertir la requête en données produit
        product_data = {
            'product_name': request.product_name,
            'brand': request.brand,
            'model': request.model,
            'category': request.category,
            'features': request.features,
            'benefits': request.benefits,
            'use_cases': request.use_cases,
            'size': request.size,
            'color': request.color,
            'images': request.images,
            'additional_keywords': request.additional_keywords
        }
        
        # Génération via le service d'intégration
        seo_service = get_amazon_seo_integration_service()
        result = await seo_service.generate_optimized_listing(product_data)
        
        # Sauvegarder en base pour historique (optionnel)
        if db:
            try:
                await db.amazon_seo_generations.insert_one({
                    "user_id": user_id,
                    "product_name": request.product_name,
                    "category": request.category,
                    "generated_listing": result['listing'],
                    "validation_result": result['validation'],
                    "generated_at": result['generation_info']['generated_at']
                })
            except Exception as e:
                log_error(
                    "Erreur sauvegarde génération SEO",
                    user_id=user_id,
                    product_name=request.product_name,
                    exception=str(e)
                )
        
        log_operation(
            "AmazonSEORoutes",
            "generate_listing",
            "success",
            user_id=user_id,
            product_name=request.product_name,
            validation_status=result['validation']['status'],
            validation_score=result['validation']['score']
        )
        
        return {
            "success": True,
            "data": result,
            "message": "Listing Amazon optimisé généré avec succès"
        }
        
    except Exception as e:
        log_error(
            "Erreur génération listing SEO Amazon",
            user_id=user_id,
            product_name=request.product_name,
            category=request.category,
            endpoint="POST /api/amazon/seo/generate",
            exception=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération du listing optimisé: {str(e)}"
        )


@router.post("/validate")
async def validate_listing(
    request: ListingValidationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
):
    """
    Valide un listing Amazon existant selon les règles SEO A9/A10
    """
    user_id = current_user["user_id"]
    
    log_info(
        "Validation listing Amazon",
        user_id=user_id,
        title_length=len(request.title),
        bullets_count=len(request.bullets),
        endpoint="POST /api/amazon/seo/validate"
    )
    
    try:
        # Convertir la requête en données de listing
        listing_data = {
            'title': request.title,
            'bullets': request.bullets,
            'description': request.description,
            'backend_keywords': request.backend_keywords,
            'images': request.images,
            'brand': request.brand,
            'model': request.model,
            'category': request.category
        }
        
        # Validation via le service d'intégration
        seo_service = get_amazon_seo_integration_service()
        result = await seo_service.validate_existing_listing(listing_data)
        
        log_operation(
            "AmazonSEORoutes",
            "validate_listing",
            "success",
            user_id=user_id,
            validation_status=result['validation']['status'],
            validation_score=result['validation']['score'],
            critical_issues=result['compliance']['critical_issues']
        )
        
        return {
            "success": True,
            "data": result,
            "message": "Validation du listing terminée"
        }
        
    except Exception as e:
        log_error(
            "Erreur validation listing Amazon",
            user_id=user_id,
            endpoint="POST /api/amazon/seo/validate",
            exception=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la validation du listing: {str(e)}"
        )


@router.post("/optimize")
async def optimize_listing(
    request: ListingOptimizationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
):
    """
    Optimise un listing Amazon existant selon les règles SEO A9/A10
    """
    user_id = current_user["user_id"]
    
    log_info(
        "Optimisation listing Amazon",
        user_id=user_id,
        title_length=len(request.current_listing.title),
        endpoint="POST /api/amazon/seo/optimize"
    )
    
    try:
        # Convertir le listing actuel
        listing_data = {
            'title': request.current_listing.title,
            'bullets': request.current_listing.bullets,
            'description': request.current_listing.description,
            'backend_keywords': request.current_listing.backend_keywords,
            'images': request.current_listing.images,
            'brand': request.current_listing.brand,
            'model': request.current_listing.model,
            'category': request.current_listing.category
        }
        
        # Optimisation via le service d'intégration
        seo_service = get_amazon_seo_integration_service()
        result = await seo_service.optimize_existing_listing(
            listing_data, 
            request.optimization_options
        )
        
        log_operation(
            "AmazonSEORoutes",
            "optimize_listing",
            "success",
            user_id=user_id,
            score_improvement=result['recommendations']['score_improvement'],
            should_update=result['recommendations']['should_update']
        )
        
        return {
            "success": True,
            "data": result,
            "message": "Optimisation du listing terminée"
        }
        
    except Exception as e:
        log_error(
            "Erreur optimisation listing Amazon",
            user_id=user_id,
            endpoint="POST /api/amazon/seo/optimize",
            exception=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'optimisation du listing: {str(e)}"
        )


@router.post("/prepare-for-publisher")
async def prepare_for_publisher(
    request: ProductSEORequest,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
):
    """
    Prépare un listing optimisé pour le Amazon Publisher
    """
    user_id = current_user["user_id"]
    
    log_info(
        "Préparation listing pour Publisher",
        user_id=user_id,
        product_name=request.product_name,
        endpoint="POST /api/amazon/seo/prepare-for-publisher"
    )
    
    try:
        # Convertir la requête en données produit
        product_data = {
            'product_name': request.product_name,
            'brand': request.brand,
            'model': request.model,
            'category': request.category,
            'features': request.features,
            'benefits': request.benefits,
            'use_cases': request.use_cases,
            'size': request.size,
            'color': request.color,
            'images': request.images,
            'additional_keywords': request.additional_keywords
        }
        
        # Préparation via le service d'intégration
        seo_service = get_amazon_seo_integration_service()
        result = await seo_service.prepare_listing_for_publisher(product_data)
        
        log_operation(
            "AmazonSEORoutes",
            "prepare_for_publisher",
            "success",
            user_id=user_id,
            product_name=request.product_name,
            ready_for_publication=result['validation_summary']['ready_for_publication']
        )
        
        return {
            "success": True,
            "data": result,
            "message": "Listing préparé pour le Publisher Amazon"
        }
        
    except Exception as e:
        log_error(
            "Erreur préparation listing pour Publisher",
            user_id=user_id,
            product_name=request.product_name,
            endpoint="POST /api/amazon/seo/prepare-for-publisher",
            exception=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la préparation pour le Publisher: {str(e)}"
        )


@router.get("/rules")
async def get_seo_rules(
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
):
    """
    Retourne les règles SEO Amazon A9/A10 actuelles
    """
    user_id = current_user["user_id"]
    
    log_info(
        "Consultation règles SEO Amazon",
        user_id=user_id,
        endpoint="GET /api/amazon/seo/rules"
    )
    
    try:
        rules_info = {
            "title_rules": {
                "max_length": 200,
                "format": "{Brand} {Model} {Feature} {Size} {Color}",
                "forbidden": ["emojis", "mots promotionnels"],
                "examples": [
                    "Samsung Galaxy S24 Ultra Smartphone 256GB Noir",
                    "Apple MacBook Air M3 Ordinateur Portable 13 pouces Argent"
                ]
            },
            "bullets_rules": {
                "count": 5,
                "max_length_per_bullet": 255,
                "format": "✓ [CATEGORY]: [Benefit with keywords]",
                "focus": "bénéfices clairs, mots-clés pertinents"
            },
            "description_rules": {
                "min_length": 100,
                "max_length": 2000,
                "structure": ["intro", "caractéristiques", "bénéfices", "cas d'usage", "conclusion"],
                "style": "texte riche, lisible, structuré"
            },
            "backend_keywords_rules": {
                "max_bytes": 250,
                "languages": ["français", "anglais"],
                "forbidden": ["marques concurrentes"],
                "format": "mots-clés séparés par espaces"
            },
            "images_rules": {
                "min_size": "1000x1000 pixels",
                "main_image": "fond blanc obligatoire",
                "additional_images": "lifestyle, détails, utilisation",
                "formats": ["JPEG", "PNG"],
                "requirements": "haute qualité, bien éclairées"
            },
            "a9_a10_optimization": {
                "a9_focus": "pertinence recherche, mots-clés, conversion",
                "a10_focus": "engagement, rétention, recommendations",
                "key_factors": ["CTR", "conversion rate", "session duration", "repeat purchases"]
            }
        }
        
        return {
            "success": True,
            "data": rules_info,
            "message": "Règles SEO Amazon A9/A10 récupérées"
        }
        
    except Exception as e:
        log_error(
            "Erreur récupération règles SEO",
            user_id=user_id,
            endpoint="GET /api/amazon/seo/rules",
            exception=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des règles: {str(e)}"
        )


@router.get("/history")
async def get_seo_history(
    limit: int = 10,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
):
    """
    Récupère l'historique des générations SEO de l'utilisateur
    """
    user_id = current_user["user_id"]
    
    log_info(
        "Consultation historique SEO",
        user_id=user_id,
        limit=limit,
        endpoint="GET /api/amazon/seo/history"
    )
    
    try:
        history = []
        
        if db:
            # Récupérer l'historique depuis MongoDB
            cursor = db.amazon_seo_generations.find({
                "user_id": user_id
            }).sort("generated_at", -1).limit(limit)
            
            async for doc in cursor:
                history.append({
                    "id": str(doc.get("_id")),
                    "product_name": doc.get("product_name"),
                    "category": doc.get("category"),
                    "validation_status": doc.get("validation_result", {}).get("status"),
                    "validation_score": doc.get("validation_result", {}).get("score"),
                    "generated_at": doc.get("generated_at")
                })
        
        return {
            "success": True,
            "data": {
                "history": history,
                "total_count": len(history)
            },
            "message": f"Historique SEO récupéré ({len(history)} éléments)"
        }
        
    except Exception as e:
        log_error(
            "Erreur récupération historique SEO",
            user_id=user_id,
            endpoint="GET /api/amazon/seo/history",
            exception=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération de l'historique: {str(e)}"
        )


@router.get("/analytics")
async def get_seo_analytics(
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
):
    """
    Retourne les analytics SEO pour l'utilisateur
    """
    user_id = current_user["user_id"]
    
    log_info(
        "Consultation analytics SEO",
        user_id=user_id,
        endpoint="GET /api/amazon/seo/analytics"
    )
    
    try:
        analytics = {
            "total_generations": 0,
            "avg_validation_score": 0,
            "status_distribution": {
                "approved": 0,
                "warning": 0,
                "rejected": 0
            },
            "category_performance": {},
            "recent_activity": 0
        }
        
        if db:
            # Statistiques générales
            total_count = await db.amazon_seo_generations.count_documents({"user_id": user_id})
            analytics["total_generations"] = total_count
            
            # Score moyen
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": None,
                    "avg_score": {"$avg": "$validation_result.score"}
                }}
            ]
            
            async for doc in db.amazon_seo_generations.aggregate(pipeline):
                analytics["avg_validation_score"] = round(doc.get("avg_score", 0), 1)
            
            # Distribution des statuts
            status_pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": "$validation_result.status",
                    "count": {"$sum": 1}
                }}
            ]
            
            async for doc in db.amazon_seo_generations.aggregate(status_pipeline):
                status = doc.get("_id", "unknown")
                count = doc.get("count", 0)
                if status in analytics["status_distribution"]:
                    analytics["status_distribution"][status] = count
        
        return {
            "success": True,
            "data": analytics,
            "message": "Analytics SEO récupérées"
        }
        
    except Exception as e:
        log_error(
            "Erreur récupération analytics SEO",
            user_id=user_id,
            endpoint="GET /api/amazon/seo/analytics",
            exception=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des analytics: {str(e)}"
        )