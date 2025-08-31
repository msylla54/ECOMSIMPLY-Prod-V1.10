"""
Amazon Publication Pipeline Routes
Routes API pour le pipeline de publication automatique SEO + Prix + Amazon

Author: ECOMSIMPLY
Date: 2025-01-01
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import os
from motor.motor_asyncio import AsyncIOMotorClient

from modules.security import get_current_user_from_token as get_current_user
from services.amazon_publication_pipeline_service import AmazonPublicationPipelineService, PipelineMonitor

logger = logging.getLogger(__name__)

# Initialize database connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db_name = os.environ.get('DB_NAME', 'ecomsimply_production')
db = client[db_name]

# Initialiser le service et moniteur avec database
pipeline_service = AmazonPublicationPipelineService(database=db)
pipeline_monitor = PipelineMonitor()

router = APIRouter(prefix="/api/amazon/pipeline", tags=["amazon-pipeline"])

class PipelineRequest(BaseModel):
    """Modèle pour les requêtes de pipeline"""
    product_data: Dict[str, Any]
    publication_settings: Optional[Dict[str, Any]] = None
    auto_publish: bool = True

class PipelineResponse(BaseModel):
    """Modèle pour les réponses de pipeline"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    pipeline_id: Optional[str] = None

@router.post("/execute", response_model=PipelineResponse)
async def execute_publication_pipeline(
    request: PipelineRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Exécuter le pipeline complet de publication automatique
    
    Pipeline: Génération SEO → Scraping prix réels → Validation → Publication Amazon
    """
    try:
        logger.info(f"🚀 Pipeline execution requested by user {current_user.get('email')} for product: {request.product_data.get('product_name')}")
        
        # Vérifier les prérequis
        user_config = {
            **current_user,
            'country_code': current_user.get('market_settings', {}).get('country_code', 'FR'),
            'currency_preference': current_user.get('market_settings', {}).get('currency_preference', 'EUR'),
            'amazon_credentials': current_user.get('amazon_connection'),
            'price_guards': current_user.get('market_settings', {}).get('price_guards'),
            'subscription_plan': current_user.get('subscription_plan', 'gratuit')
        }
        
        prerequisites_check = await pipeline_service.validate_pipeline_prerequisites(user_config)
        
        if not prerequisites_check["valid"]:
            return PipelineResponse(
                success=False,
                message=f"Prerequisites not met: {', '.join(prerequisites_check['errors'])}",
                data={"prerequisites": prerequisites_check}
            )
        
        # Exécuter le pipeline
        if request.auto_publish:
            # Exécution asynchrone en arrière-plan
            background_tasks.add_task(
                _execute_pipeline_background,
                request.product_data,
                user_config,
                request.publication_settings
            )
            
            return PipelineResponse(
                success=True,
                message="Pipeline started in background. Check status endpoint for updates.",
                data={"execution_mode": "background"}
            )
        else:
            # Exécution synchrone
            result = await pipeline_service.execute_full_pipeline(
                request.product_data,
                user_config,
                request.publication_settings
            )
            
            # Suivre le pipeline
            if result.get("pipeline_id"):
                pipeline_monitor.track_pipeline(result["pipeline_id"], result)
            
            return PipelineResponse(
                success=result["status"] in ["completed", "pending_review"],
                message=result.get("error", "Pipeline executed"),
                data=result,
                pipeline_id=result.get("pipeline_id")
            )
    
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")

async def _execute_pipeline_background(
    product_data: Dict[str, Any],
    user_config: Dict[str, Any], 
    publication_settings: Optional[Dict[str, Any]]
):
    """Exécuter le pipeline en arrière-plan"""
    try:
        result = await pipeline_service.execute_full_pipeline(
            product_data,
            user_config,
            publication_settings
        )
        
        # Suivre le pipeline
        if result.get("pipeline_id"):
            pipeline_monitor.track_pipeline(result["pipeline_id"], result)
            
        logger.info(f"Background pipeline {result.get('pipeline_id')} completed with status: {result.get('status')}")
        
    except Exception as e:
        logger.error(f"Background pipeline failed: {e}")

@router.get("/status/{pipeline_id}")
async def get_pipeline_status(
    pipeline_id: str,
    current_user = Depends(get_current_user)
):
    """Récupérer le statut d'un pipeline spécifique"""
    try:
        # Récupérer depuis le moniteur
        if pipeline_id in pipeline_monitor.active_pipelines:
            pipeline_data = pipeline_monitor.active_pipelines[pipeline_id]
            return {
                "success": True,
                "data": pipeline_data
            }
        else:
            # Fallback vers le service
            status = await pipeline_service.get_pipeline_status(pipeline_id)
            return {
                "success": True,
                "data": status
            }
    
    except Exception as e:
        logger.error(f"Failed to get pipeline status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get pipeline status: {str(e)}")

@router.get("/stats")
async def get_pipeline_stats(
    current_user = Depends(get_current_user)
):
    """Récupérer les statistiques des pipelines"""
    try:
        stats = pipeline_monitor.get_pipeline_stats()
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to get pipeline stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get pipeline stats: {str(e)}")

@router.post("/validate-prerequisites")
async def validate_pipeline_prerequisites(
    current_user = Depends(get_current_user)
):
    """Valider que l'utilisateur peut exécuter le pipeline"""
    try:
        user_config = {
            **current_user,
            'country_code': current_user.get('market_settings', {}).get('country_code', 'FR'),
            'currency_preference': current_user.get('market_settings', {}).get('currency_preference', 'EUR'),
            'amazon_credentials': current_user.get('amazon_connection'),
            'price_guards': current_user.get('market_settings', {}).get('price_guards'),
            'subscription_plan': current_user.get('subscription_plan', 'gratuit')
        }
        
        validation = await pipeline_service.validate_pipeline_prerequisites(user_config)
        
        return {
            "success": True,
            "data": validation
        }
    
    except Exception as e:
        logger.error(f"Prerequisites validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prerequisites validation failed: {str(e)}")

# Routes de test pour développement
@router.post("/test/seo-only")
async def test_seo_generation_only(
    request: PipelineRequest,
    current_user = Depends(get_current_user)
):
    """Test : Génération SEO uniquement (sans prix ni publication)"""
    try:
        user_config = {**current_user}
        
        # Exécuter seulement la génération SEO
        seo_result = await pipeline_service._generate_optimized_seo(request.product_data, user_config)
        
        return {
            "success": seo_result["success"],
            "data": seo_result,
            "test_mode": "seo_only"
        }
    
    except Exception as e:
        logger.error(f"SEO-only test failed: {e}")
        raise HTTPException(status_code=500, detail=f"SEO-only test failed: {str(e)}")

@router.post("/test/price-scraping-only") 
async def test_price_scraping_only(
    request: PipelineRequest,
    current_user = Depends(get_current_user)
):
    """Test : Scraping prix uniquement (sans SEO ni publication)"""
    try:
        user_config = {
            **current_user,
            'country_code': current_user.get('market_settings', {}).get('country_code', 'FR'),
            'currency_preference': current_user.get('market_settings', {}).get('currency_preference', 'EUR')
        }
        
        # Exécuter seulement le scraping prix
        price_result = await pipeline_service._get_real_prices(request.product_data, user_config)
        
        return {
            "success": price_result["success"],
            "data": price_result,
            "test_mode": "price_scraping_only"
        }
    
    except Exception as e:
        logger.error(f"Price scraping test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Price scraping test failed: {str(e)}")

@router.post("/test/full-pipeline-dry-run")
async def test_full_pipeline_dry_run(
    request: PipelineRequest,
    current_user = Depends(get_current_user)
):
    """Test : Pipeline complet en mode simulation (sans publication réelle)"""
    try:
        user_config = {
            **current_user,
            'country_code': current_user.get('market_settings', {}).get('country_code', 'FR'),
            'currency_preference': current_user.get('market_settings', {}).get('currency_preference', 'EUR'),
            'amazon_credentials': current_user.get('amazon_connection'),
            'price_guards': current_user.get('market_settings', {}).get('price_guards'),
            'subscription_plan': current_user.get('subscription_plan', 'gratuit')
        }
        
        # Exécuter le pipeline en mode dry-run (simulation)
        # TODO: Modifier le service pour supporter le mode dry-run
        result = await pipeline_service.execute_full_pipeline(
            request.product_data,
            user_config,
            {**request.publication_settings, "dry_run": True} if request.publication_settings else {"dry_run": True}
        )
        
        return {
            "success": True,
            "data": result,
            "test_mode": "dry_run"
        }
    
    except Exception as e:
        logger.error(f"Dry run test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Dry run test failed: {str(e)}")