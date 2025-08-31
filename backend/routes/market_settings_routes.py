"""
Routes API pour les paramètres de marché multi-pays
ECOMSIMPLY Bloc 4 — Phase 4: Market Settings Routes

Endpoints:
- GET/PUT /api/v1/settings/market - Configuration marché par utilisateur
- GET /api/v1/prices/reference - Prix de référence agrégé
- POST /api/v1/prices/validate - Validation complète prix avec guards
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
import os
import uuid
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# Import des services et modèles
from models.market_settings import MarketSettings, DEFAULT_CURRENCY_BY_COUNTRY
from services.price_guards_service import get_price_guards_service
from services.currency_conversion_service import get_currency_service
from services.multi_country_scraping_service import get_scraping_service
from services.logging_service import log_info, log_error, log_operation
from modules.security import get_current_user_from_token

# Configuration
router = APIRouter(prefix="/api/v1", tags=["market-settings"])

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db_name = os.environ.get('DB_NAME', 'ecomsimply_production')
db = client[db_name]


# Modèles Pydantic pour les requêtes/réponses
class MarketSettingsRequest(BaseModel):
    """Requête de mise à jour des paramètres de marché"""
    country_code: str = Field(..., description="Code pays (FR, GB, US)")
    currency_preference: str = Field(..., description="Devise préférée (EUR, GBP, USD)")
    enabled: bool = Field(default=True, description="Activer le scraping pour ce marché")
    price_publish_min: Optional[float] = Field(None, description="Prix minimum pour auto-publication", ge=0)
    price_publish_max: Optional[float] = Field(None, description="Prix maximum pour auto-publication", ge=0)
    price_variance_threshold: float = Field(default=0.20, description="Seuil de variance relative", ge=0, le=1)


class MarketSettingsResponse(BaseModel):
    """Réponse avec les paramètres de marché"""
    id: str
    user_id: str
    country_code: str
    currency_preference: str
    enabled: bool
    price_publish_min: Optional[float]
    price_publish_max: Optional[float]
    price_variance_threshold: float
    created_at: datetime
    updated_at: datetime


class PriceReferenceRequest(BaseModel):
    """Requête pour obtenir un prix de référence"""
    product_name: str = Field(..., description="Nom du produit")
    country_code: str = Field(..., description="Code pays")
    max_sources: int = Field(default=5, description="Nombre max de sources", ge=1, le=10)


class PriceValidationRequest(BaseModel):
    """Requête pour validation complète d'un prix"""
    product_name: str = Field(..., description="Nom du produit")
    country_code: str = Field(..., description="Code pays")
    max_sources: int = Field(default=5, description="Nombre max de sources", ge=1, le=10)


@router.get("/settings/market", response_model=List[MarketSettingsResponse])
async def get_market_settings(
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
):
    """
    Récupérer les paramètres de marché pour l'utilisateur connecté
    """
    user_id = current_user["user_id"]
    
    log_info(
        "Récupération paramètres de marché",
        user_id=user_id,
        endpoint="GET /api/v1/settings/market"
    )
    
    try:
        # Récupérer tous les settings de l'utilisateur
        settings_data = await db.market_settings.find({
            "user_id": user_id
        }).sort("country_code", 1).to_list(length=None)
        
        if not settings_data:
            # Créer des settings par défaut pour tous les pays supportés
            default_settings = []
            supported_countries = ["FR", "GB", "US"]
            
            for country in supported_countries:
                default_setting = MarketSettings(
                    user_id=user_id,
                    country_code=country,
                    currency_preference=DEFAULT_CURRENCY_BY_COUNTRY[country],
                    enabled=country == "FR",  # FR activé par défaut
                    price_variance_threshold=0.20
                )
                
                # Sauvegarder en base
                await db.market_settings.insert_one(default_setting.dict())
                default_settings.append(default_setting)
            
            log_info(
                "Paramètres de marché par défaut créés",
                user_id=user_id,
                countries_created=supported_countries
            )
            
            return [MarketSettingsResponse(**setting.dict()) for setting in default_settings]
        
        # Convertir en modèles Pydantic
        settings = [MarketSettings(**data) for data in settings_data]
        
        log_info(
            "Paramètres de marché récupérés",
            user_id=user_id,
            settings_count=len(settings)
        )
        
        return [MarketSettingsResponse(**setting.dict()) for setting in settings]
        
    except Exception as e:
        log_error(
            "Erreur récupération paramètres de marché",
            user_id=user_id,
            endpoint="GET /api/v1/settings/market",
            exception=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur récupération paramètres: {str(e)}"
        )


@router.put("/settings/market", response_model=MarketSettingsResponse)
async def update_market_settings(
    request: MarketSettingsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
):
    """
    Mettre à jour les paramètres de marché pour un pays spécifique
    """
    user_id = current_user["user_id"]
    
    log_info(
        "Mise à jour paramètres de marché",
        user_id=user_id,
        country_code=request.country_code,
        endpoint="PUT /api/v1/settings/market"
    )
    
    try:
        # Validation des données
        country_code = request.country_code.upper()
        currency = request.currency_preference.upper()
        
        # Validation des bornes de prix
        if (request.price_publish_min is not None and 
            request.price_publish_max is not None and 
            request.price_publish_max <= request.price_publish_min):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le prix maximum doit être supérieur au prix minimum"
            )
        
        # Chercher les settings existants
        existing_settings = await db.market_settings.find_one({
            "user_id": user_id,
            "country_code": country_code
        })
        
        if existing_settings:
            # Mise à jour
            update_data = {
                "currency_preference": currency,
                "enabled": request.enabled,
                "price_publish_min": request.price_publish_min,
                "price_publish_max": request.price_publish_max,
                "price_variance_threshold": request.price_variance_threshold,
                "updated_at": datetime.utcnow()
            }
            
            await db.market_settings.update_one(
                {"_id": existing_settings["_id"]},
                {"$set": update_data}
            )
            
            # Récupérer les settings mis à jour
            updated_settings = await db.market_settings.find_one({
                "user_id": user_id,
                "country_code": country_code
            })
            
            settings = MarketSettings(**updated_settings)
            
            log_operation(
                "MarketSettingsRoutes",
                "update_settings",
                "success",
                user_id=user_id,
                country_code=country_code,
                enabled=request.enabled,
                currency=currency
            )
            
        else:
            # Création
            new_settings = MarketSettings(
                user_id=user_id,
                country_code=country_code,
                currency_preference=currency,
                enabled=request.enabled,
                price_publish_min=request.price_publish_min,
                price_publish_max=request.price_publish_max,
                price_variance_threshold=request.price_variance_threshold
            )
            
            await db.market_settings.insert_one(new_settings.dict())
            settings = new_settings
            
            log_operation(
                "MarketSettingsRoutes",
                "create_settings",
                "success",
                user_id=user_id,
                country_code=country_code,
                enabled=request.enabled,
                currency=currency
            )
        
        return MarketSettingsResponse(**settings.dict())
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(
            "Erreur mise à jour paramètres de marché",
            user_id=user_id,
            country_code=request.country_code,
            endpoint="PUT /api/v1/settings/market",
            exception=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur mise à jour paramètres: {str(e)}"
        )


@router.get("/prices/reference")
async def get_reference_price(
    product_name: str = Query(..., description="Nom du produit"),
    country_code: str = Query(..., description="Code pays (FR, GB, US)"),
    max_sources: int = Query(default=5, description="Nombre max de sources", ge=1, le=10),
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
):
    """
    Obtenir le prix de référence agrégé pour un produit dans un pays
    """
    user_id = current_user["user_id"]
    correlation_id = f"ref_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    log_info(
        "Demande prix de référence",
        user_id=user_id,
        product_name=product_name,
        country_code=country_code,
        correlation_id=correlation_id,
        endpoint="GET /api/v1/prices/reference"
    )
    
    try:
        # Récupérer les settings de marché
        market_settings = None
        settings_data = await db.market_settings.find_one({
            "user_id": user_id,
            "country_code": country_code.upper(),
            "enabled": True
        })
        
        if not settings_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Marché {country_code} non configuré ou désactivé"
            )
        
        market_settings = MarketSettings(**settings_data)
        
        # Scraper les prix
        scraping_service = await get_scraping_service(db)
        snapshots = await scraping_service.scrape_all_sources_for_country(
            country_code.upper(),
            product_name,
            correlation_id,
            max_sources
        )
        
        if not snapshots:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aucune donnée de prix trouvée"
            )
        
        # Agréger les prix
        price_guards_service = await get_price_guards_service(db)
        aggregation = await price_guards_service.aggregate_prices(
            snapshots,
            market_settings.currency_preference,
            market_settings,
            correlation_id
        )
        
        if not aggregation:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Échec de l'agrégation des prix"
            )
        
        # Préparer la réponse
        response = {
            "correlation_id": correlation_id,
            "product_name": product_name,
            "country_code": country_code.upper(),
            "reference_price": aggregation.reference_price,
            "currency": aggregation.currency,
            "price_range": {
                "min": aggregation.min_price,
                "max": aggregation.max_price,
                "avg": aggregation.avg_price
            },
            "variance": aggregation.price_variance,
            "sources": {
                "total_attempted": len(snapshots),
                "successful": aggregation.successful_sources,
                "success_rate": aggregation.collection_success_rate
            },
            "quality_score": aggregation.quality_score,
            "collected_at": aggregation.aggregated_at.isoformat()
        }
        
        log_operation(
            "MarketSettingsRoutes",
            "get_reference_price",
            "success",
            user_id=user_id,
            product_name=product_name,
            country_code=country_code,
            reference_price=aggregation.reference_price,
            quality_score=aggregation.quality_score,
            correlation_id=correlation_id
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(
            "Erreur récupération prix de référence",
            user_id=user_id,
            product_name=product_name,
            country_code=country_code,
            correlation_id=correlation_id,
            endpoint="GET /api/v1/prices/reference",
            exception=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur récupération prix: {str(e)}"
        )


@router.post("/prices/validate")
async def validate_price_for_publication(
    request: PriceValidationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
):
    """
    Validation complète d'un prix avec Price Guards pour publication
    """
    user_id = current_user["user_id"]
    correlation_id = f"val_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    log_info(
        "Validation prix pour publication",
        user_id=user_id,
        product_name=request.product_name,
        country_code=request.country_code,
        correlation_id=correlation_id,
        endpoint="POST /api/v1/prices/validate"
    )
    
    try:
        # Vérifier que le marché est activé
        settings_data = await db.market_settings.find_one({
            "user_id": user_id,
            "country_code": request.country_code.upper(),
            "enabled": True
        })
        
        if not settings_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Marché {request.country_code} non configuré ou désactivé"
            )
        
        # Validation complète via le service Price Guards
        price_guards_service = await get_price_guards_service(db)
        validation_result = await price_guards_service.validate_price_for_publication(
            request.product_name,
            request.country_code.upper(),
            user_id,
            correlation_id,
            request.max_sources
        )
        
        if not validation_result['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=validation_result.get('error', 'Erreur de validation')
            )
        
        log_operation(
            "MarketSettingsRoutes",
            "validate_price",
            "success",
            user_id=user_id,
            product_name=request.product_name,
            country_code=request.country_code,
            recommendation=validation_result['guards_evaluation']['recommendation'],
            reference_price=validation_result['reference_price'],
            correlation_id=correlation_id
        )
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(
            "Erreur validation prix",
            user_id=user_id,
            product_name=request.product_name,
            country_code=request.country_code,
            correlation_id=correlation_id,
            endpoint="POST /api/v1/prices/validate",
            exception=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur validation prix: {str(e)}"
        )


@router.get("/settings/market/statistics")
async def get_market_statistics(
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
):
    """
    Obtenir les statistiques des marchés et Price Guards
    """
    user_id = current_user["user_id"]
    
    try:
        # Statistiques Price Guards
        price_guards_service = await get_price_guards_service(db)
        guards_stats = await price_guards_service.get_price_guards_statistics(user_id)
        
        # Statistiques de scraping par pays
        scraping_service = await get_scraping_service(db)
        scraping_stats = {}
        
        for country in ["FR", "GB", "US"]:
            stats = await scraping_service.get_scraping_statistics(country)
            scraping_stats[country] = stats
        
        # Statistiques de conversion de devises
        currency_service = await get_currency_service(db)
        currency_stats = await currency_service.get_cache_statistics()
        
        return {
            "user_id": user_id,
            "price_guards": guards_stats,
            "scraping_by_country": scraping_stats,
            "currency_conversion": currency_stats,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        log_error(
            "Erreur récupération statistiques marché",
            user_id=user_id,
            endpoint="GET /api/v1/settings/market/statistics",
            exception=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur récupération statistiques: {str(e)}"
        )