"""
Amazon Phase 6 Models - Optimisations avancées
Modèles pour A/B Testing, A+ Content, Variations Builder, Compliance Scanner
"""
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class ExperimentStatus(str, Enum):
    """Statut des expérimentations A/B"""
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class ExperimentType(str, Enum):
    """Type d'expérimentation"""
    TITLE = "title"
    MAIN_IMAGE = "main_image"
    BULLET_POINTS = "bullet_points"
    A_PLUS_CONTENT = "a_plus_content"
    MULTIVARIATE = "multivariate"


class VariationStatus(str, Enum):
    """Statut des variations"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"
    SUPPRESSED = "suppressed"


class ComplianceIssueType(str, Enum):
    """Types de problèmes de conformité"""
    BATTERY = "battery"
    HAZMAT = "hazmat"
    DIMENSIONS = "dimensions"
    IMAGES = "images"
    CATEGORY = "category"
    CONTENT_POLICY = "content_policy"
    TRADEMARK = "trademark"
    MISSING_ATTRIBUTE = "missing_attribute"


class ComplianceSeverity(str, Enum):
    """Sévérité des problèmes de conformité"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AplusContentStatus(str, Enum):
    """Statut du contenu A+"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    ARCHIVED = "archived"


# ==================== A/B TESTING MODELS ====================

class ExperimentVariant(BaseModel):
    """Variante d'expérimentation A/B"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Nom de la variante")
    content: Dict[str, Any] = Field(..., description="Contenu de la variante")
    traffic_percentage: float = Field(default=50.0, ge=0, le=100, description="% de trafic assigné")
    
    # Métriques
    impressions: int = Field(default=0, description="Nombre d'impressions")
    clicks: int = Field(default=0, description="Nombre de clics")
    conversions: int = Field(default=0, description="Nombre de conversions")
    revenue: float = Field(default=0.0, description="Revenus générés")
    
    # Métriques calculées
    @property
    def ctr(self) -> float:
        """Click-through rate"""
        return (self.clicks / self.impressions * 100) if self.impressions > 0 else 0.0
    
    @property
    def conversion_rate(self) -> float:
        """Taux de conversion"""
        return (self.conversions / self.clicks * 100) if self.clicks > 0 else 0.0
    
    @property
    def revenue_per_click(self) -> float:
        """Revenus par clic"""
        return (self.revenue / self.clicks) if self.clicks > 0 else 0.0


class ABTestExperiment(BaseModel):
    """Expérimentation A/B Testing"""
    
    # Identifiants
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="ID utilisateur")
    sku: str = Field(..., description="SKU du produit testé")
    marketplace_id: str = Field(..., description="ID marketplace Amazon")
    
    # Configuration expérimentation
    name: str = Field(..., description="Nom de l'expérimentation")
    description: Optional[str] = None
    experiment_type: ExperimentType = Field(..., description="Type d'expérimentation")
    status: ExperimentStatus = Field(default=ExperimentStatus.DRAFT)
    
    # Variantes
    variants: List[ExperimentVariant] = Field(default_factory=list)
    
    # Configuration temporelle
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    duration_days: int = Field(default=14, ge=1, le=90, description="Durée en jours")
    
    # Critères de succès
    primary_metric: str = Field(default="conversion_rate", description="Métrique principale")
    confidence_level: float = Field(default=95.0, ge=90, le=99.9, description="Niveau de confiance %")
    minimum_sample_size: int = Field(default=1000, description="Taille d'échantillon minimum")
    
    # Résultats
    winner_variant_id: Optional[str] = None
    statistical_significance: Optional[float] = None
    auto_apply_winner: bool = Field(default=False, description="Appliquer automatiquement le gagnant")
    
    # SP-API Integration
    amazon_experiment_id: Optional[str] = None  # ID retourné par Amazon
    sp_api_status: Optional[str] = None
    
    # Métadonnées
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== A+ CONTENT MODELS ====================

class AplusModule(BaseModel):
    """Module de contenu A+"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    module_type: str = Field(..., description="Type de module (TEXT, IMAGE_TEXT, etc.)")
    position: int = Field(..., description="Position dans le contenu")
    
    # Contenu
    title: Optional[str] = None
    content: Dict[str, Any] = Field(default_factory=dict, description="Contenu du module")
    images: List[str] = Field(default_factory=list, description="URLs des images")
    
    # Configuration
    enabled: bool = Field(default=True)
    ai_generated: bool = Field(default=False, description="Généré par IA")


class AplusContent(BaseModel):
    """Contenu A+ Amazon"""
    
    # Identifiants
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="ID utilisateur")
    sku: str = Field(..., description="SKU du produit")
    marketplace_id: str = Field(..., description="ID marketplace Amazon")
    
    # Configuration contenu
    name: str = Field(..., description="Nom du contenu A+")
    description: Optional[str] = None
    language: str = Field(default="fr-FR", description="Langue du contenu")
    
    # Modules
    modules: List[AplusModule] = Field(default_factory=list)
    
    # État
    status: AplusContentStatus = Field(default=AplusContentStatus.DRAFT)
    
    # SP-API Integration
    amazon_content_id: Optional[str] = None  # Content Reference ID Amazon
    submission_id: Optional[str] = None
    approval_status: Optional[str] = None
    rejection_reasons: List[str] = Field(default_factory=list)
    
    # Métriques
    views: int = Field(default=0)
    engagement_rate: float = Field(default=0.0)
    conversion_impact: float = Field(default=0.0, description="Impact sur le taux de conversion")
    
    # IA Configuration
    ai_prompt: Optional[str] = None
    ai_style_preferences: Dict[str, Any] = Field(default_factory=dict)
    
    # Métadonnées
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None


# ==================== VARIATIONS BUILDER MODELS ====================

class ProductRelationship(BaseModel):
    """Relation entre produits (Parent/Child)"""
    
    parent_sku: str = Field(..., description="SKU du produit parent")
    child_sku: str = Field(..., description="SKU du produit enfant")
    variation_theme: str = Field(..., description="Thème de variation (Size, Color, etc.)")
    relationship_type: str = Field(default="Variation", description="Type de relation")
    
    # Attributs de variation
    variation_attributes: Dict[str, str] = Field(default_factory=dict)
    
    # Métadonnées
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VariationFamily(BaseModel):
    """Famille de variations de produits"""
    
    # Identifiants
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="ID utilisateur")
    marketplace_id: str = Field(..., description="ID marketplace Amazon")
    
    # Configuration famille
    parent_sku: str = Field(..., description="SKU du produit parent")
    family_name: str = Field(..., description="Nom de la famille")
    variation_theme: str = Field(..., description="Thème de variation principal")
    
    # Produits
    child_skus: List[str] = Field(default_factory=list, description="Liste des SKUs enfants")
    relationships: List[ProductRelationship] = Field(default_factory=list)
    
    # Configuration
    auto_manage: bool = Field(default=True, description="Gestion automatique des variations")
    sync_pricing: bool = Field(default=False, description="Synchroniser les prix")
    sync_inventory: bool = Field(default=False, description="Synchroniser les stocks")
    
    # État
    status: VariationStatus = Field(default=VariationStatus.ACTIVE)
    
    # SP-API Integration
    amazon_relationship_feed_id: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    sync_errors: List[str] = Field(default_factory=list)
    
    # Métadonnées
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== COMPLIANCE SCANNER MODELS ====================

class ComplianceIssue(BaseModel):
    """Problème de conformité détecté"""
    
    # Identifiants
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="ID utilisateur")
    sku: str = Field(..., description="SKU concerné")
    marketplace_id: str = Field(..., description="ID marketplace Amazon")
    
    # Classification problème
    issue_type: ComplianceIssueType = Field(..., description="Type de problème")
    severity: ComplianceSeverity = Field(..., description="Sévérité du problème")
    
    # Description
    title: str = Field(..., description="Titre du problème")
    description: str = Field(..., description="Description détaillée")
    amazon_error_code: Optional[str] = None
    
    # Détection
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    detection_method: str = Field(default="automated_scan", description="Méthode de détection")
    
    # Résolution
    status: str = Field(default="open", description="open, in_progress, resolved, ignored")
    resolution_type: Optional[str] = None  # auto_fix, manual_fix, acknowledged
    resolution_description: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    
    # Actions suggérées
    suggested_actions: List[str] = Field(default_factory=list)
    auto_fixable: bool = Field(default=False, description="Peut être corrigé automatiquement")
    
    # SP-API Data
    suppression_reason: Optional[str] = None
    amazon_case_id: Optional[str] = None
    
    # Métadonnées
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Données supplémentaires")


class ComplianceReport(BaseModel):
    """Rapport de conformité"""
    
    # Identifiants
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="ID utilisateur")
    marketplace_id: str = Field(..., description="ID marketplace Amazon")
    
    # Configuration scan
    scan_type: str = Field(default="full_scan", description="Type de scan")
    skus_scanned: List[str] = Field(default_factory=list)
    
    # Résultats
    total_skus: int = Field(default=0)
    compliant_skus: int = Field(default=0)
    issues_found: int = Field(default=0)
    critical_issues: int = Field(default=0)
    
    # Issues détectées
    issues: List[ComplianceIssue] = Field(default_factory=list)
    
    # Métriques
    compliance_score: float = Field(default=100.0, ge=0, le=100, description="Score de conformité %")
    
    # Exécution
    scan_started_at: datetime = Field(default_factory=datetime.utcnow)
    scan_completed_at: Optional[datetime] = None
    scan_duration_seconds: Optional[int] = None
    
    # Métadonnées
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== API RESPONSE MODELS ====================

class ABTestResponse(BaseModel):
    """Réponse API pour A/B Testing"""
    success: bool
    experiment: Optional[ABTestExperiment] = None
    message: str
    errors: List[str] = Field(default_factory=list)


class AplusContentResponse(BaseModel):
    """Réponse API pour A+ Content"""
    success: bool
    content: Optional[AplusContent] = None
    message: str
    amazon_response: Optional[Dict[str, Any]] = None


class VariationFamilyResponse(BaseModel):
    """Réponse API pour Variation Families"""
    success: bool
    family: Optional[VariationFamily] = None
    message: str
    sp_api_responses: List[Dict[str, Any]] = Field(default_factory=list)


class ComplianceReportResponse(BaseModel):
    """Réponse API pour Compliance Report"""
    success: bool
    report: Optional[ComplianceReport] = None
    message: str
    auto_fixes_applied: int = Field(default=0)


class Phase6DashboardData(BaseModel):
    """Données dashboard Phase 6"""
    
    # A/B Testing stats
    active_experiments: int = Field(default=0)
    completed_experiments: int = Field(default=0)
    avg_lift_rate: float = Field(default=0.0)
    
    # A+ Content stats
    published_content: int = Field(default=0)
    pending_approval: int = Field(default=0)
    avg_engagement_rate: float = Field(default=0.0)
    
    # Variations stats
    variation_families: int = Field(default=0)
    total_child_products: int = Field(default=0)
    sync_success_rate: float = Field(default=100.0)
    
    # Compliance stats
    compliance_score: float = Field(default=100.0)
    critical_issues: int = Field(default=0)
    auto_fixes_applied_24h: int = Field(default=0)
    
    # Métadonnées
    last_updated: datetime = Field(default_factory=datetime.utcnow)