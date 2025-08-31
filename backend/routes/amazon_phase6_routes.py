"""
Amazon Phase 6 Routes - Optimisations avancées
Routes API pour A/B Testing, A+ Content, Variations Builder, Compliance Scanner
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from models.amazon_phase6 import (
    ABTestExperiment, AplusContent, VariationFamily, ComplianceReport,
    Phase6DashboardData, ABTestResponse, AplusContentResponse, 
    VariationFamilyResponse, ComplianceReportResponse,
    ExperimentStatus, AplusContentStatus, VariationStatus, 
    ExperimentType, ComplianceIssueType
)
from services.amazon_phase6_service import amazon_phase6_service
from modules.security import get_current_user_from_token as get_current_user

logger = logging.getLogger(__name__)

# Router principal Phase 6
router = APIRouter(prefix="/api/amazon/phase6", tags=["Amazon Phase 6"])

# ==================== REQUEST MODELS ====================

class CreateABTestRequest(BaseModel):
    """Requête de création d'expérimentation A/B"""
    sku: str = Field(..., description="SKU du produit à tester")
    marketplace_id: str = Field(..., description="ID marketplace Amazon")
    name: str = Field(..., description="Nom de l'expérimentation")
    description: Optional[str] = None
    experiment_type: ExperimentType = Field(..., description="Type d'expérimentation")
    duration_days: int = Field(default=14, ge=1, le=90, description="Durée en jours")
    primary_metric: str = Field(default="conversion_rate", description="Métrique principale")
    confidence_level: float = Field(default=95.0, ge=90, le=99.9)
    auto_apply_winner: bool = Field(default=False)
    variants: List[Dict[str, Any]] = Field(..., description="Configuration des variantes")

class CreateAplusContentRequest(BaseModel):
    """Requête de création de contenu A+"""
    sku: str = Field(..., description="SKU du produit")
    marketplace_id: str = Field(..., description="ID marketplace Amazon")
    name: str = Field(..., description="Nom du contenu A+")
    description: Optional[str] = None
    language: str = Field(default="fr-FR", description="Langue du contenu")
    use_ai_generation: bool = Field(default=True, description="Utiliser l'IA pour générer le contenu")
    modules_types: List[str] = Field(default=["STANDARD_SINGLE_IMAGE_TEXT"], description="Types de modules")
    style_preferences: Dict[str, Any] = Field(default_factory=dict)

class CreateVariationFamilyRequest(BaseModel):
    """Requête de création de famille de variations"""
    marketplace_id: str = Field(..., description="ID marketplace Amazon")
    parent_sku: str = Field(..., description="SKU du produit parent")
    family_name: str = Field(..., description="Nom de la famille")
    variation_theme: str = Field(..., description="Thème de variation")
    child_skus: List[str] = Field(..., description="SKUs des produits enfants")
    auto_manage: bool = Field(default=True)
    sync_pricing: bool = Field(default=False)
    sync_inventory: bool = Field(default=False)
    children: List[Dict[str, Any]] = Field(default_factory=list, description="Configuration enfants")

class ComplianceScanRequest(BaseModel):
    """Requête de scan de conformité"""
    marketplace_id: str = Field(..., description="ID marketplace Amazon")
    sku_list: Optional[List[str]] = Field(None, description="SKUs spécifiques à scanner")
    scan_types: Optional[List[ComplianceIssueType]] = Field(None, description="Types de scan")

class ApplyComplianceFixesRequest(BaseModel):
    """Requête d'application de corrections conformité"""
    report_id: str = Field(..., description="ID du rapport de conformité")
    dry_run: bool = Field(default=True, description="Mode simulation")

# ==================== A/B TESTING ENDPOINTS ====================

@router.get("/dashboard")
async def get_phase6_dashboard(
    marketplace_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupérer les données dashboard Phase 6"""
    try:
        user_id = current_user['user_id']
        
        dashboard_data = await amazon_phase6_service.get_phase6_dashboard_data(
            user_id=user_id,
            marketplace_id=marketplace_id
        )
        
        return {
            "success": True,
            "data": dashboard_data,
            "message": "Dashboard Phase 6 récupéré avec succès"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting Phase 6 dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/experiments", response_model=ABTestResponse)
async def create_ab_experiment(
    request: CreateABTestRequest,
    current_user: dict = Depends(get_current_user)
):
    """Créer une nouvelle expérimentation A/B"""
    try:
        user_id = current_user['user_id']
        
        experiment_config = {
            'name': request.name,
            'description': request.description,
            'experiment_type': request.experiment_type,
            'duration_days': request.duration_days,
            'primary_metric': request.primary_metric,
            'confidence_level': request.confidence_level,
            'auto_apply_winner': request.auto_apply_winner,
            'variants': request.variants
        }
        
        experiment = await amazon_phase6_service.create_ab_experiment(
            user_id=user_id,
            sku=request.sku,
            marketplace_id=request.marketplace_id,
            experiment_config=experiment_config
        )
        
        return ABTestResponse(
            success=True,
            experiment=experiment,
            message="Expérimentation A/B créée avec succès"
        )
        
    except Exception as e:
        logger.error(f"❌ Error creating A/B experiment: {str(e)}")
        return ABTestResponse(
            success=False,
            message=f"Erreur lors de la création: {str(e)}",
            errors=[str(e)]
        )

@router.post("/experiments/{experiment_id}/start")
async def start_ab_experiment(
    experiment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Démarrer une expérimentation A/B"""
    try:
        user_id = current_user['user_id']
        
        success = await amazon_phase6_service.start_ab_experiment(
            experiment_id=experiment_id,
            user_id=user_id
        )
        
        if success:
            return {
                "success": True,
                "message": "Expérimentation démarrée avec succès"
            }
        else:
            raise HTTPException(status_code=400, detail="Impossible de démarrer l'expérimentation")
            
    except Exception as e:
        logger.error(f"❌ Error starting experiment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/experiments/{experiment_id}/metrics")
async def get_experiment_metrics(
    experiment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Collecter les métriques d'une expérimentation"""
    try:
        user_id = current_user['user_id']
        
        metrics = await amazon_phase6_service.collect_experiment_metrics(
            experiment_id=experiment_id,
            user_id=user_id
        )
        
        return {
            "success": True,
            "data": metrics,
            "message": "Métriques collectées avec succès"
        }
        
    except Exception as e:
        logger.error(f"❌ Error collecting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/experiments/{experiment_id}/analysis")
async def analyze_experiment_results(
    experiment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Analyser les résultats statistiques d'une expérimentation"""
    try:
        user_id = current_user['user_id']
        
        analysis = await amazon_phase6_service.analyze_experiment_results(
            experiment_id=experiment_id,
            user_id=user_id
        )
        
        return {
            "success": True,
            "data": analysis,
            "message": "Analyse statistique effectuée"
        }
        
    except Exception as e:
        logger.error(f"❌ Error analyzing experiment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/experiments/{experiment_id}/apply-winner")
async def apply_experiment_winner(
    experiment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Appliquer automatiquement la variante gagnante"""
    try:
        user_id = current_user['user_id']
        
        success = await amazon_phase6_service.apply_experiment_winner(
            experiment_id=experiment_id,
            user_id=user_id
        )
        
        if success:
            return {
                "success": True,
                "message": "Variante gagnante appliquée avec succès"
            }
        else:
            raise HTTPException(status_code=400, detail="Impossible d'appliquer la variante gagnante")
            
    except Exception as e:
        logger.error(f"❌ Error applying winner: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/experiments")
async def get_user_experiments(
    marketplace_id: Optional[str] = None,
    status: Optional[ExperimentStatus] = None,
    current_user: dict = Depends(get_current_user)
):
    """Récupérer les expérimentations d'un utilisateur"""
    try:
        user_id = current_user['user_id']
        
        experiments = await amazon_phase6_service.get_user_experiments(
            user_id=user_id,
            marketplace_id=marketplace_id,
            status=status
        )
        
        return {
            "success": True,
            "data": experiments,
            "count": len(experiments),
            "message": f"{len(experiments)} expérimentation(s) trouvée(s)"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting experiments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== A+ CONTENT ENDPOINTS ====================

@router.post("/aplus-content", response_model=AplusContentResponse)
async def create_aplus_content(
    request: CreateAplusContentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Créer un nouveau contenu A+"""
    try:
        user_id = current_user['user_id']
        
        content_config = {
            'name': request.name,
            'description': request.description,
            'language': request.language,
            'use_ai_generation': request.use_ai_generation,
            'modules_types': request.modules_types,
            'style_preferences': request.style_preferences
        }
        
        aplus_content = await amazon_phase6_service.create_aplus_content(
            user_id=user_id,
            sku=request.sku,
            marketplace_id=request.marketplace_id,
            content_config=content_config
        )
        
        return AplusContentResponse(
            success=True,
            content=aplus_content,
            message="Contenu A+ créé avec succès"
        )
        
    except Exception as e:
        logger.error(f"❌ Error creating A+ content: {str(e)}")
        return AplusContentResponse(
            success=False,
            message=f"Erreur lors de la création: {str(e)}"
        )

@router.post("/aplus-content/{content_id}/publish")
async def publish_aplus_content(
    content_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Publier un contenu A+ vers Amazon"""
    try:
        user_id = current_user['user_id']
        
        success = await amazon_phase6_service.publish_aplus_content(
            content_id=content_id,
            user_id=user_id
        )
        
        if success:
            return {
                "success": True,
                "message": "Contenu A+ publié avec succès vers Amazon"
            }
        else:
            raise HTTPException(status_code=400, detail="Impossible de publier le contenu A+")
            
    except Exception as e:
        logger.error(f"❌ Error publishing A+ content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/aplus-content/{content_id}/status")
async def check_aplus_approval_status(
    content_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Vérifier le statut d'approbation d'un contenu A+"""
    try:
        user_id = current_user['user_id']
        
        status = await amazon_phase6_service.check_aplus_approval_status(
            content_id=content_id,
            user_id=user_id
        )
        
        return {
            "success": True,
            "status": status,
            "message": f"Statut: {status}"
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking A+ status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/aplus-content/{content_id}/metrics")
async def get_aplus_performance_metrics(
    content_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupérer les métriques de performance d'un contenu A+"""
    try:
        user_id = current_user['user_id']
        
        metrics = await amazon_phase6_service.get_aplus_performance_metrics(
            content_id=content_id,
            user_id=user_id
        )
        
        return {
            "success": True,
            "data": metrics,
            "message": "Métriques de performance récupérées"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting A+ metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/aplus-content")
async def get_user_aplus_contents(
    marketplace_id: Optional[str] = None,
    status: Optional[AplusContentStatus] = None,
    current_user: dict = Depends(get_current_user)
):
    """Récupérer les contenus A+ d'un utilisateur"""
    try:
        user_id = current_user['user_id']
        
        contents = await amazon_phase6_service.get_user_aplus_contents(
            user_id=user_id,
            marketplace_id=marketplace_id,
            status=status
        )
        
        return {
            "success": True,
            "data": contents,
            "count": len(contents),
            "message": f"{len(contents)} contenu(s) A+ trouvé(s)"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting A+ contents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== VARIATIONS BUILDER ENDPOINTS ====================

@router.get("/variations/detect")
async def detect_variation_families(
    marketplace_id: str,
    sku_list: Optional[str] = None,  # CSV de SKUs
    current_user: dict = Depends(get_current_user)
):
    """Détecter automatiquement les familles de variations"""
    try:
        user_id = current_user['user_id']
        
        # Convertir la liste CSV en liste Python si fournie
        sku_list_parsed = None
        if sku_list:
            sku_list_parsed = [sku.strip() for sku in sku_list.split(',')]
        
        families = await amazon_phase6_service.detect_variation_families(
            user_id=user_id,
            marketplace_id=marketplace_id,
            sku_list=sku_list_parsed
        )
        
        return {
            "success": True,
            "data": families,
            "count": len(families),
            "message": f"{len(families)} famille(s) de variations détectée(s)"
        }
        
    except Exception as e:
        logger.error(f"❌ Error detecting variation families: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/variations", response_model=VariationFamilyResponse)
async def create_variation_family(
    request: CreateVariationFamilyRequest,
    current_user: dict = Depends(get_current_user)
):
    """Créer une famille de variations"""
    try:
        user_id = current_user['user_id']
        
        family_config = {
            'parent_sku': request.parent_sku,
            'family_name': request.family_name,
            'variation_theme': request.variation_theme,
            'child_skus': request.child_skus,
            'auto_manage': request.auto_manage,
            'sync_pricing': request.sync_pricing,
            'sync_inventory': request.sync_inventory,
            'children': request.children
        }
        
        family = await amazon_phase6_service.create_variation_family(
            user_id=user_id,
            marketplace_id=request.marketplace_id,
            family_config=family_config
        )
        
        return VariationFamilyResponse(
            success=True,
            family=family,
            message="Famille de variations créée avec succès"
        )
        
    except Exception as e:
        logger.error(f"❌ Error creating variation family: {str(e)}")
        return VariationFamilyResponse(
            success=False,
            message=f"Erreur lors de la création: {str(e)}"
        )

@router.post("/variations/{family_id}/sync")
async def sync_family_inventory_pricing(
    family_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Synchroniser stocks et prix d'une famille"""
    try:
        user_id = current_user['user_id']
        
        success = await amazon_phase6_service.sync_family_inventory_pricing(
            family_id=family_id,
            user_id=user_id
        )
        
        if success:
            return {
                "success": True,
                "message": "Synchronisation de la famille terminée avec succès"
            }
        else:
            raise HTTPException(status_code=400, detail="Impossible de synchroniser la famille")
            
    except Exception as e:
        logger.error(f"❌ Error syncing family: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/variations")
async def get_user_variation_families(
    marketplace_id: Optional[str] = None,
    status: Optional[VariationStatus] = None,
    current_user: dict = Depends(get_current_user)
):
    """Récupérer les familles de variations d'un utilisateur"""
    try:
        user_id = current_user['user_id']
        
        families = await amazon_phase6_service.get_user_variation_families(
            user_id=user_id,
            marketplace_id=marketplace_id,
            status=status
        )
        
        return {
            "success": True,
            "data": families,
            "count": len(families),
            "message": f"{len(families)} famille(s) de variations trouvée(s)"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting variation families: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== COMPLIANCE SCANNER ENDPOINTS ====================

@router.post("/compliance/scan", response_model=ComplianceReportResponse)
async def scan_compliance(
    request: ComplianceScanRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Scanner la conformité des produits"""
    try:
        user_id = current_user['user_id']
        
        # Lancer le scan en arrière-plan pour les gros volumes
        if request.sku_list and len(request.sku_list) > 20:
            background_tasks.add_task(
                _background_compliance_scan,
                user_id,
                request.marketplace_id,
                request.sku_list,
                request.scan_types
            )
            
            return ComplianceReportResponse(
                success=True,
                message="Scan de conformité lancé en arrière-plan. Vous recevrez une notification à la fin."
            )
        else:
            # Scan synchrone pour les petits volumes
            report = await amazon_phase6_service.scan_compliance(
                user_id=user_id,
                marketplace_id=request.marketplace_id,
                sku_list=request.sku_list,
                scan_types=request.scan_types
            )
            
            return ComplianceReportResponse(
                success=True,
                report=report,
                message=f"Scan terminé: {report.compliance_score:.1f}% de conformité"
            )
            
    except Exception as e:
        logger.error(f"❌ Error scanning compliance: {str(e)}")
        return ComplianceReportResponse(
            success=False,
            message=f"Erreur lors du scan: {str(e)}"
        )

@router.post("/compliance/auto-fix")
async def apply_compliance_auto_fixes(
    request: ApplyComplianceFixesRequest,
    current_user: dict = Depends(get_current_user)
):
    """Appliquer les corrections automatiques de conformité"""
    try:
        user_id = current_user['user_id']
        
        fix_results = await amazon_phase6_service.apply_compliance_auto_fixes(
            report_id=request.report_id,
            user_id=user_id,
            dry_run=request.dry_run
        )
        
        return {
            "success": True,
            "data": fix_results,
            "message": f"{fix_results.get('fixed', 0)} correction(s) appliquée(s)"
        }
        
    except Exception as e:
        logger.error(f"❌ Error applying auto-fixes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compliance/dashboard")
async def get_compliance_dashboard(
    marketplace_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupérer les données dashboard de conformité"""
    try:
        user_id = current_user['user_id']
        
        dashboard_data = await amazon_phase6_service.get_compliance_dashboard_data(
            user_id=user_id,
            marketplace_id=marketplace_id
        )
        
        return {
            "success": True,
            "data": dashboard_data,
            "message": "Dashboard conformité récupéré avec succès"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting compliance dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== BACKGROUND TASKS ====================

async def _background_compliance_scan(
    user_id: str,
    marketplace_id: str,
    sku_list: Optional[List[str]],
    scan_types: Optional[List[ComplianceIssueType]]
):
    """Tâche de scan de conformité en arrière-plan"""
    try:
        logger.info(f"🔍 Starting background compliance scan for user {user_id}")
        
        report = await amazon_phase6_service.scan_compliance(
            user_id=user_id,
            marketplace_id=marketplace_id,
            sku_list=sku_list,
            scan_types=scan_types
        )
        
        # TODO: Envoyer une notification à l'utilisateur
        logger.info(f"✅ Background compliance scan completed: {report.compliance_score:.1f}% compliance")
        
    except Exception as e:
        logger.error(f"❌ Error in background compliance scan: {str(e)}")