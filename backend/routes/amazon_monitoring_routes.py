"""
Amazon Monitoring Routes - Phase 5
Routes API pour le système de monitoring et d'optimisation automatique
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field

from models.amazon_monitoring import (
    MonitoringJob, ProductSnapshot, OptimizationDecision, MonitoringAlert,
    DesiredState, MonitoringKPIs, MonitoringDashboardData,
    MonitoringJobResponse, MonitoringKPIResponse, OptimizationHistoryResponse,
    MonitoringStatus, OptimizationStatus, OptimizationAction
)
from services.amazon_monitoring_service import monitoring_service
from amazon.monitoring.orchestrator import monitoring_orchestrator
from amazon.optimizer.closed_loop import closed_loop_optimizer
from modules.security import get_current_user_from_token as get_current_user

logger = logging.getLogger(__name__)

# Créer le router
router = APIRouter(prefix="/api/amazon/monitoring", tags=["Amazon Monitoring"])


# ==================== MODÈLES DE REQUÊTE ====================

class CreateMonitoringJobRequest(BaseModel):
    marketplace_id: str = Field(default="A13V1IB3VIYZZH", description="ID marketplace Amazon")
    skus: List[str] = Field(..., description="Liste des SKUs à monitorer")
    monitoring_frequency_hours: int = Field(default=6, ge=1, le=168, description="Fréquence monitoring en heures")
    optimization_frequency_hours: int = Field(default=24, ge=1, le=168, description="Fréquence optimisation en heures")
    auto_optimization_enabled: bool = Field(default=True, description="Auto-optimisation activée")
    buybox_loss_threshold: float = Field(default=0.8, ge=0, le=1, description="Seuil alerte perte Buy Box")
    price_deviation_threshold: float = Field(default=0.05, ge=0, le=1, description="Seuil écart prix")
    seo_score_threshold: float = Field(default=0.7, ge=0, le=1, description="Seuil score SEO")


class UpdateMonitoringJobRequest(BaseModel):
    monitoring_enabled: Optional[bool] = None
    auto_optimization_enabled: Optional[bool] = None
    monitoring_frequency_hours: Optional[int] = Field(None, ge=1, le=168)
    optimization_frequency_hours: Optional[int] = Field(None, ge=1, le=168)
    buybox_loss_threshold: Optional[float] = Field(None, ge=0, le=1)
    price_deviation_threshold: Optional[float] = Field(None, ge=0, le=1)
    seo_score_threshold: Optional[float] = Field(None, ge=0, le=1)
    status: Optional[MonitoringStatus] = None


class CreateDesiredStateRequest(BaseModel):
    sku: str = Field(..., description="SKU du produit")
    marketplace_id: str = Field(default="A13V1IB3VIYZZH", description="ID marketplace")
    
    # SEO désiré
    desired_title: Optional[str] = None
    desired_description: Optional[str] = None
    desired_bullet_points: Optional[List[str]] = None
    desired_keywords: Optional[List[str]] = None
    
    # Pricing désiré
    desired_price: Optional[float] = Field(None, gt=0)
    price_strategy: Optional[str] = None
    min_price: Optional[float] = Field(None, gt=0)
    max_price: Optional[float] = Field(None, gt=0)
    
    # Objectifs
    target_buybox_share: float = Field(default=0.9, ge=0, le=1)
    target_conversion_rate: Optional[float] = Field(None, ge=0, le=1)
    target_ctr: Optional[float] = Field(None, ge=0, le=1)
    
    # Configuration
    auto_correction_enabled: bool = Field(default=True)
    correction_max_frequency_hours: int = Field(default=24, ge=1, le=168)


class TriggerOptimizationRequest(BaseModel):
    sku: Optional[str] = Field(None, description="SKU spécifique (optionnel)")
    marketplace_id: str = Field(default="A13V1IB3VIYZZH", description="ID marketplace")
    force: bool = Field(default=False, description="Forcer optimisation même si récente")


class MonitoringFilters(BaseModel):
    marketplace_id: Optional[str] = None
    sku: Optional[str] = None
    status: Optional[str] = None
    days_back: int = Field(default=7, ge=1, le=365)
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=50, ge=1, le=200)


# ==================== ROUTES MONITORING JOBS ====================

@router.post("/jobs", response_model=MonitoringJobResponse)
async def create_monitoring_job(
    request: CreateMonitoringJobRequest,
    current_user = Depends(get_current_user)
):
    """Créer un nouveau job de monitoring"""
    try:
        logger.info(f"Creating monitoring job for {len(request.skus)} SKUs by user {current_user['user_id']}")
        
        # Créer le job de monitoring
        job = MonitoringJob(
            user_id=current_user['user_id'],
            marketplace_id=request.marketplace_id,
            skus=request.skus,
            monitoring_frequency_hours=request.monitoring_frequency_hours,
            optimization_frequency_hours=request.optimization_frequency_hours,
            auto_optimization_enabled=request.auto_optimization_enabled,
            buybox_loss_threshold=request.buybox_loss_threshold,
            price_deviation_threshold=request.price_deviation_threshold,
            seo_score_threshold=request.seo_score_threshold
        )
        
        # Calculer prochaine exécution
        job.next_run_at = datetime.utcnow() + timedelta(hours=request.monitoring_frequency_hours)
        
        job_id = await monitoring_service.create_monitoring_job(job)
        
        return MonitoringJobResponse(
            success=True,
            job=job,
            message=f"Job de monitoring créé pour {len(request.skus)} SKUs"
        )
        
    except Exception as e:
        logger.error(f"Error creating monitoring job: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la création du job de monitoring")


@router.get("/jobs", response_model=List[MonitoringJob])
async def get_monitoring_jobs(
    marketplace_id: Optional[str] = Query(None, description="Filtrer par marketplace"),
    status: Optional[MonitoringStatus] = Query(None, description="Filtrer par statut"),
    current_user = Depends(get_current_user)
):
    """Récupérer les jobs de monitoring de l'utilisateur"""
    try:
        jobs = await monitoring_service.get_user_monitoring_jobs(
            user_id=current_user['user_id'],
            marketplace_id=marketplace_id,
            status=status
        )
        
        return jobs
        
    except Exception as e:
        logger.error(f"Error getting monitoring jobs: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des jobs")


@router.get("/jobs/{job_id}", response_model=MonitoringJob)
async def get_monitoring_job(
    job_id: str,
    current_user = Depends(get_current_user)
):
    """Récupérer un job de monitoring par ID"""
    try:
        job = await monitoring_service.get_monitoring_job(
            user_id=current_user['user_id'],
            job_id=job_id
        )
        
        if not job:
            raise HTTPException(status_code=404, detail="Job de monitoring non trouvé")
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting monitoring job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération du job")


@router.put("/jobs/{job_id}", response_model=MonitoringJobResponse)
async def update_monitoring_job(
    job_id: str,
    request: UpdateMonitoringJobRequest,
    current_user = Depends(get_current_user)
):
    """Mettre à jour un job de monitoring"""
    try:
        # Vérifier que le job existe
        existing_job = await monitoring_service.get_monitoring_job(
            user_id=current_user['user_id'],
            job_id=job_id
        )
        
        if not existing_job:
            raise HTTPException(status_code=404, detail="Job de monitoring non trouvé")
        
        # Préparer les mises à jour
        updates = {}
        for field, value in request.model_dump(exclude_unset=True).items():
            if value is not None:
                updates[field] = value
        
        # Appliquer les mises à jour
        success = await monitoring_service.update_monitoring_job(
            user_id=current_user['user_id'],
            job_id=job_id,
            updates=updates
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Échec de la mise à jour")
        
        # Récupérer le job mis à jour
        updated_job = await monitoring_service.get_monitoring_job(
            user_id=current_user['user_id'],
            job_id=job_id
        )
        
        return MonitoringJobResponse(
            success=True,
            job=updated_job,
            message="Job de monitoring mis à jour"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating monitoring job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour du job")


@router.delete("/jobs/{job_id}")
async def delete_monitoring_job(
    job_id: str,
    current_user = Depends(get_current_user)
):
    """Supprimer un job de monitoring"""
    try:
        success = await monitoring_service.delete_monitoring_job(
            user_id=current_user['user_id'],
            job_id=job_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Job de monitoring non trouvé")
        
        return {"success": True, "message": "Job de monitoring supprimé"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting monitoring job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression du job")


# ==================== ROUTES DESIRED STATES ====================

@router.post("/desired-states", response_model=Dict[str, Any])
async def create_desired_state(
    request: CreateDesiredStateRequest,
    current_user = Depends(get_current_user)
):
    """Créer ou mettre à jour un état désiré"""
    try:
        logger.info(f"Creating desired state for SKU {request.sku} by user {current_user['user_id']}")
        
        # Validation des prix
        if request.min_price and request.max_price and request.max_price <= request.min_price:
            raise HTTPException(
                status_code=400,
                detail="Le prix maximum doit être supérieur au prix minimum"
            )
        
        # Créer l'état désiré
        desired_state = DesiredState(
            user_id=current_user['user_id'],
            sku=request.sku,
            marketplace_id=request.marketplace_id,
            desired_title=request.desired_title,
            desired_description=request.desired_description,
            desired_bullet_points=request.desired_bullet_points or [],
            desired_keywords=request.desired_keywords or [],
            desired_price=request.desired_price,
            price_strategy=request.price_strategy,
            min_price=request.min_price,
            max_price=request.max_price,
            target_buybox_share=request.target_buybox_share,
            target_conversion_rate=request.target_conversion_rate,
            target_ctr=request.target_ctr,
            auto_correction_enabled=request.auto_correction_enabled,
            correction_max_frequency_hours=request.correction_max_frequency_hours
        )
        
        state_id = await monitoring_service.create_desired_state(desired_state)
        
        return {
            "success": True,
            "desired_state_id": state_id,
            "message": f"État désiré créé pour SKU {request.sku}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating desired state: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la création de l'état désiré")


@router.get("/desired-states/{sku}", response_model=Optional[DesiredState])
async def get_desired_state(
    sku: str,
    marketplace_id: str = Query("A13V1IB3VIYZZH", description="ID marketplace"),
    current_user = Depends(get_current_user)
):
    """Récupérer l'état désiré pour un SKU"""
    try:
        desired_state = await monitoring_service.get_desired_state(
            user_id=current_user['user_id'],
            sku=sku,
            marketplace_id=marketplace_id
        )
        
        return desired_state
        
    except Exception as e:
        logger.error(f"Error getting desired state for SKU {sku}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération de l'état désiré")


# ==================== ROUTES SNAPSHOTS ====================

@router.get("/snapshots", response_model=List[ProductSnapshot])
async def get_product_snapshots(
    sku: Optional[str] = Query(None, description="Filtrer par SKU"),
    marketplace_id: Optional[str] = Query(None, description="Filtrer par marketplace"),
    days_back: int = Query(7, ge=1, le=365, description="Nombre de jours en arrière"),
    limit: int = Query(50, ge=1, le=200, description="Nombre maximum de résultats"),
    current_user = Depends(get_current_user)
):
    """Récupérer les snapshots produits"""
    try:
        snapshots = await monitoring_service.get_product_snapshots(
            user_id=current_user['user_id'],
            sku=sku,
            marketplace_id=marketplace_id,
            days_back=days_back,
            limit=limit
        )
        
        return snapshots
        
    except Exception as e:
        logger.error(f"Error getting product snapshots: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des snapshots")


# ==================== ROUTES OPTIMISATIONS ====================

@router.get("/optimizations", response_model=OptimizationHistoryResponse)
async def get_optimization_history(
    sku: Optional[str] = Query(None, description="Filtrer par SKU"),
    marketplace_id: Optional[str] = Query(None, description="Filtrer par marketplace"),
    status: Optional[OptimizationStatus] = Query(None, description="Filtrer par statut"),
    action_type: Optional[OptimizationAction] = Query(None, description="Filtrer par type d'action"),
    days_back: int = Query(30, ge=1, le=365, description="Nombre de jours en arrière"),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(50, ge=1, le=200, description="Nombre maximum d'éléments"),
    current_user = Depends(get_current_user)
):
    """Récupérer l'historique des optimisations"""
    try:
        decisions = await monitoring_service.get_optimization_decisions(
            user_id=current_user['user_id'],
            sku=sku,
            marketplace_id=marketplace_id,
            status=status,
            days_back=days_back,
            skip=skip,
            limit=limit
        )
        
        # Compter le total pour pagination
        total_count = len(decisions)  # Approximation
        
        return OptimizationHistoryResponse(
            success=True,
            decisions=decisions,
            total_count=total_count,
            page=skip // limit + 1,
            per_page=limit,
            message=f"{len(decisions)} décisions d'optimisation récupérées"
        )
        
    except Exception as e:
        logger.error(f"Error getting optimization history: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération de l'historique")


@router.post("/optimize")
async def trigger_optimization(
    request: TriggerOptimizationRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Déclencher une optimisation manuelle"""
    try:
        logger.info(f"Manual optimization triggered by user {current_user['user_id']}")
        
        # Lancer l'optimisation en arrière-plan
        if request.sku:
            # Optimisation pour un SKU spécifique
            background_tasks.add_task(
                optimize_specific_sku,
                current_user['user_id'],
                request.sku,
                request.marketplace_id,
                request.force
            )
            
            message = f"Optimisation lancée pour SKU {request.sku}"
        else:
            # Optimisation globale
            background_tasks.add_task(
                closed_loop_optimizer.run_optimization_cycle
            )
            
            message = "Cycle d'optimisation global lancé"
        
        return {
            "success": True,
            "message": message,
            "triggered_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error triggering optimization: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors du déclenchement de l'optimisation")


# ==================== ROUTES KPIs ET DASHBOARD ====================

@router.get("/kpis", response_model=MonitoringKPIResponse)
async def get_monitoring_kpis(
    marketplace_id: str = Query("A13V1IB3VIYZZH", description="ID marketplace"),
    period_hours: int = Query(24, ge=1, le=168, description="Période en heures"),
    current_user = Depends(get_current_user)
):
    """Récupérer les KPIs de monitoring"""
    try:
        # Calculer les KPIs pour la période demandée
        kpis = await monitoring_service.calculate_and_save_kpis(
            user_id=current_user['user_id'],
            marketplace_id=marketplace_id,
            period_hours=period_hours
        )
        
        return MonitoringKPIResponse(
            success=True,
            kpis=kpis,
            message=f"KPIs calculés pour les dernières {period_hours}h"
        )
        
    except Exception as e:
        logger.error(f"Error getting monitoring KPIs: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des KPIs")


@router.get("/dashboard", response_model=MonitoringDashboardData)
async def get_monitoring_dashboard(
    marketplace_id: str = Query("A13V1IB3VIYZZH", description="ID marketplace"),
    current_user = Depends(get_current_user)
):
    """Récupérer les données du dashboard monitoring"""
    try:
        dashboard_data = await monitoring_service.get_dashboard_data(
            user_id=current_user['user_id'],
            marketplace_id=marketplace_id
        )
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error getting monitoring dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération du dashboard")


@router.get("/alerts", response_model=List[MonitoringAlert])
async def get_monitoring_alerts(
    marketplace_id: Optional[str] = Query(None, description="Filtrer par marketplace"),
    severity: Optional[str] = Query(None, description="Filtrer par sévérité"),
    current_user = Depends(get_current_user)
):
    """Récupérer les alertes de monitoring actives"""
    try:
        alerts = await monitoring_service.get_active_alerts(
            user_id=current_user['user_id'],
            marketplace_id=marketplace_id,
            severity=severity
        )
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error getting monitoring alerts: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des alertes")


# ==================== ROUTES ADMINISTRATION ====================

@router.post("/system/trigger-cycle")
async def trigger_monitoring_cycle(
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Déclencher manuellement un cycle de monitoring (admin seulement)"""
    try:
        # TODO: Vérifier permissions admin
        
        logger.info(f"Manual monitoring cycle triggered by user {current_user['user_id']}")
        
        # Lancer le cycle en arrière-plan
        background_tasks.add_task(
            monitoring_orchestrator._run_monitoring_cycle
        )
        
        return {
            "success": True,
            "message": "Cycle de monitoring lancé manuellement",
            "triggered_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error triggering monitoring cycle: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors du déclenchement du cycle")


@router.get("/system/stats")
async def get_system_stats(
    current_user = Depends(get_current_user)
):
    """Récupérer les statistiques système du monitoring"""
    try:
        # TODO: Vérifier permissions admin
        
        stats = {
            "orchestrator_stats": monitoring_orchestrator.job_stats,
            "optimizer_stats": closed_loop_optimizer.stats,
            "circuit_breaker": monitoring_orchestrator.circuit_breaker,
            "system_health": "healthy"  # À calculer
        }
        
        return {
            "success": True,
            "stats": stats,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des statistiques")


# ==================== FONCTIONS UTILITAIRES ====================

async def optimize_specific_sku(
    user_id: str, 
    sku: str, 
    marketplace_id: str, 
    force: bool = False
):
    """Optimiser un SKU spécifique en arrière-plan"""
    try:
        logger.info(f"Optimizing specific SKU {sku} for user {user_id}")
        
        # Récupérer le snapshot le plus récent
        snapshots = await monitoring_service.get_product_snapshots(
            user_id=user_id,
            sku=sku,
            marketplace_id=marketplace_id,
            days_back=1,
            limit=1
        )
        
        if not snapshots:
            logger.warning(f"No recent snapshot found for SKU {sku}")
            return
        
        snapshot = snapshots[0]
        
        # Analyser et optimiser
        decision = await closed_loop_optimizer._analyze_and_optimize(snapshot)
        
        if decision:
            logger.info(f"Optimization decision made for SKU {sku}: {decision.action_type.value}")
        else:
            logger.info(f"No optimization needed for SKU {sku}")
        
    except Exception as e:
        logger.error(f"Error optimizing specific SKU {sku}: {str(e)}")