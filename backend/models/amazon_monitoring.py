"""
Amazon Monitoring Models - Phase 5
Models for monitoring, optimization history and KPI tracking
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class MonitoringStatus(str, Enum):
    """Statut du monitoring"""
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class OptimizationAction(str, Enum):
    """Type d'action d'optimisation"""
    SEO_UPDATE = "seo_update"
    PRICE_UPDATE = "price_update" 
    CONTENT_UPDATE = "content_update"
    CATALOG_UPDATE = "catalog_update"
    AUTO_CORRECTION = "auto_correction"


class OptimizationStatus(str, Enum):
    """Statut d'une optimisation"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERTED = "reverted"


class BuyBoxStatus(str, Enum):
    """Statut Buy Box détaillé"""
    WON = "won"          # ✅ Nous avons la Buy Box
    LOST = "lost"        # ❌ Buy Box perdue  
    SHARED = "shared"    # 🔄 Buy Box partagée
    ELIGIBLE = "eligible" # ⏳ Éligible mais pas gagnante
    NOT_ELIGIBLE = "not_eligible"  # ❌ Non éligible
    UNKNOWN = "unknown"   # ❓ État indéterminé


class MarketplaceConfig(BaseModel):
    """Configuration par marketplace"""
    marketplace_id: str = Field(..., description="ID marketplace Amazon")
    country_code: str = Field(..., description="Code pays (FR, UK, US, DE, etc.)")
    currency: str = Field(..., description="Devise (EUR, GBP, USD, etc.)")
    domain: str = Field(..., description="Domaine Amazon (amazon.fr, amazon.co.uk, etc.)")
    enabled: bool = Field(default=True, description="Monitoring activé pour ce marketplace")
    monitoring_frequency_hours: int = Field(default=6, description="Fréquence monitoring en heures")


class MonitoringJob(BaseModel):
    """Job de monitoring schedulé"""
    
    # Identifiants
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="ID utilisateur")
    marketplace_id: str = Field(..., description="ID marketplace")
    
    # Configuration
    skus: List[str] = Field(..., description="Liste des SKUs à monitorer")
    monitoring_enabled: bool = Field(default=True, description="Monitoring actif")
    auto_optimization_enabled: bool = Field(default=True, description="Auto-optimisation activée")
    
    # Fréquences
    monitoring_frequency_hours: int = Field(default=6, description="Fréquence monitoring")
    optimization_frequency_hours: int = Field(default=24, description="Fréquence optimisation")
    
    # Seuils d'alerte
    buybox_loss_threshold: float = Field(default=0.8, description="Seuil alerte perte Buy Box")
    price_deviation_threshold: float = Field(default=0.05, description="Seuil écart prix %")
    seo_score_threshold: float = Field(default=0.7, description="Seuil score SEO")
    
    # État
    status: MonitoringStatus = Field(default=MonitoringStatus.ACTIVE)
    last_run_at: Optional[datetime] = Field(None, description="Dernière exécution")
    next_run_at: Optional[datetime] = Field(None, description="Prochaine exécution")
    run_count: int = Field(default=0, description="Nombre d'exécutions")
    
    # Métadonnées
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProductSnapshot(BaseModel):
    """Snapshot des données produit à un moment donné"""
    
    # Identifiants
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str = Field(..., description="ID du job de monitoring")
    user_id: str
    sku: str
    asin: Optional[str] = None
    marketplace_id: str
    
    # Données Catalog API
    title: Optional[str] = None
    description: Optional[str] = None
    bullet_points: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    main_image_url: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    brand: Optional[str] = None
    
    # Données Pricing API
    current_price: Optional[float] = None
    currency: Optional[str] = None
    list_price: Optional[float] = None
    sale_price: Optional[float] = None
    
    # Buy Box Data
    buybox_price: Optional[float] = None
    buybox_winner: Optional[str] = None
    buybox_status: BuyBoxStatus = Field(default=BuyBoxStatus.UNKNOWN)
    buybox_eligibility: bool = Field(default=False)
    
    # Concurrents
    competitors_count: int = Field(default=0)
    min_competitor_price: Optional[float] = None
    avg_competitor_price: Optional[float] = None
    
    # Métriques Performance (si Brand Owner)
    impressions: Optional[int] = None
    clicks: Optional[int] = None
    ctr_percent: Optional[float] = None
    conversions: Optional[int] = None
    conversion_rate_percent: Optional[float] = None
    
    # États de publication
    listing_status: Optional[str] = None  # ACTIVE, INACTIVE, INCOMPLETE, etc.
    fulfillment_channel: Optional[str] = None  # FBA, FBM
    quantity_available: Optional[int] = None
    
    # Méta
    snapshot_at: datetime = Field(default_factory=datetime.utcnow)
    api_call_duration_ms: int = Field(default=0)
    data_completeness_score: float = Field(default=0.0, ge=0, le=1.0)


class DesiredState(BaseModel):
    """État désiré pour un produit (défini par les règles utilisateur)"""
    
    # Identifiants
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    sku: str
    marketplace_id: str
    
    # SEO désiré
    desired_title: Optional[str] = None
    desired_description: Optional[str] = None
    desired_bullet_points: List[str] = Field(default_factory=list)
    desired_keywords: List[str] = Field(default_factory=list)
    
    # Pricing désiré
    desired_price: Optional[float] = None
    price_strategy: Optional[str] = None  # De PricingRule
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    
    # Objectifs Business
    target_buybox_share: float = Field(default=0.9, description="Objectif Buy Box share")
    target_conversion_rate: Optional[float] = None
    target_ctr: Optional[float] = None
    
    # Configuration
    auto_correction_enabled: bool = Field(default=True)
    correction_max_frequency_hours: int = Field(default=24)
    
    # Métadonnées
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OptimizationDecision(BaseModel):
    """Décision d'optimisation prise par le système"""
    
    # Identifiants
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    user_id: str
    sku: str
    marketplace_id: str
    
    # Contexte de la décision
    current_snapshot_id: str = Field(description="Snapshot ayant déclenché l'optimisation")
    desired_state_id: str = Field(description="État désiré de référence")
    
    # Type de décision
    action_type: OptimizationAction
    priority: int = Field(default=5, ge=1, le=10, description="Priorité 1=urgent, 10=low")
    
    # Changements identifiés
    detected_changes: Dict[str, Any] = Field(default_factory=dict)
    recommended_changes: Dict[str, Any] = Field(default_factory=dict)
    
    # Justification
    reasoning: str = Field(description="Explication de la décision")
    confidence_score: float = Field(ge=0, le=1, description="Confiance dans la décision")
    risk_score: float = Field(ge=0, le=1, description="Score de risque")
    
    # Exécution
    status: OptimizationStatus = Field(default=OptimizationStatus.PENDING)
    execution_plan: Dict[str, Any] = Field(default_factory=dict)
    sp_api_calls: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Résultats
    execution_started_at: Optional[datetime] = None
    execution_completed_at: Optional[datetime] = None
    execution_duration_ms: Optional[int] = None
    sp_api_responses: List[Dict[str, Any]] = Field(default_factory=list)
    success: Optional[bool] = None
    error_message: Optional[str] = None
    
    # Metrics
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MonitoringKPIs(BaseModel):
    """KPIs de monitoring agrégés"""
    
    # Période
    period_start: datetime
    period_end: datetime
    marketplace_id: str
    user_id: str
    
    # Métriques générales
    total_skus_monitored: int = 0
    active_listings: int = 0
    inactive_listings: int = 0
    
    # Buy Box
    buybox_won_count: int = 0
    buybox_lost_count: int = 0
    buybox_share_avg: float = 0.0
    buybox_share_change: float = 0.0
    
    # Pricing
    price_updates_count: int = 0
    price_optimizations_successful: int = 0
    price_optimizations_failed: int = 0
    avg_price_change_percent: float = 0.0
    
    # SEO
    seo_updates_count: int = 0
    seo_optimizations_successful: int = 0
    seo_optimizations_failed: int = 0
    avg_seo_score: float = 0.0
    
    # Performance (si disponible)
    total_impressions: Optional[int] = None
    total_clicks: Optional[int] = None
    avg_ctr_percent: Optional[float] = None
    total_conversions: Optional[int] = None
    avg_conversion_rate_percent: Optional[float] = None
    
    # Auto-corrections
    auto_corrections_triggered: int = 0
    auto_corrections_successful: int = 0
    auto_corrections_failed: int = 0
    
    # Santé système
    monitoring_jobs_successful: int = 0
    monitoring_jobs_failed: int = 0
    api_calls_count: int = 0
    api_errors_count: int = 0
    avg_api_response_time_ms: float = 0.0
    
    # Métadonnées
    calculated_at: datetime = Field(default_factory=datetime.utcnow)


class MonitoringAlert(BaseModel):
    """Alerte de monitoring"""
    
    # Identifiants
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    user_id: str
    sku: str
    marketplace_id: str
    
    # Type d'alerte
    alert_type: str = Field(..., description="buybox_lost, price_drift, seo_degraded, etc.")
    severity: str = Field(..., description="critical, warning, info")
    
    # Détails
    title: str = Field(..., description="Titre de l'alerte")
    description: str = Field(..., description="Description détaillée")
    current_value: Optional[float] = None
    threshold_value: Optional[float] = None
    
    # Actions
    auto_correction_attempted: bool = Field(default=False)
    auto_correction_successful: Optional[bool] = None
    manual_action_required: bool = Field(default=False)
    
    # État
    status: str = Field(default="active", description="active, acknowledged, resolved")
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    
    # Métadonnées
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Modèles de réponse API
class MonitoringJobResponse(BaseModel):
    """Réponse API pour job de monitoring"""
    success: bool
    job: Optional[MonitoringJob] = None
    message: str
    errors: List[str] = Field(default_factory=list)


class MonitoringKPIResponse(BaseModel):
    """Réponse API pour KPIs"""
    success: bool
    kpis: Optional[MonitoringKPIs] = None
    message: str


class OptimizationHistoryResponse(BaseModel):
    """Réponse API pour historique optimisations"""
    success: bool
    decisions: List[OptimizationDecision]
    total_count: int
    page: int
    per_page: int
    message: str


class MonitoringDashboardData(BaseModel):
    """Données complètes pour dashboard monitoring"""
    kpis: MonitoringKPIs
    recent_snapshots: List[ProductSnapshot]
    recent_optimizations: List[OptimizationDecision] 
    active_alerts: List[MonitoringAlert]
    jobs_status: List[MonitoringJob]