"""
Amazon Pricing Models - Phase 4
Models for pricing rules and history management
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class PricingStrategy(str, Enum):
    """Stratégies de pricing disponibles"""
    BUYBOX_MATCH = "buybox_match"  # Matcher le prix Buy Box
    MARGIN_TARGET = "margin_target"  # Cibler une marge spécifique
    FLOOR_CEILING = "floor_ceiling"  # Rester entre min/max avec variance


class PricingRuleStatus(str, Enum):
    """Statut des règles de pricing"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"


class BuyBoxStatus(str, Enum):
    """Statut Buy Box"""
    WON = "won"  # ✅ Nous avons la Buy Box
    LOST = "lost"  # ❌ Buy Box perdue
    RISK = "risk"  # ⚠️ Risque de perdre la Buy Box
    UNKNOWN = "unknown"  # État inconnu


class PricingRule(BaseModel):
    """Règle de pricing par SKU et marketplace"""
    
    # Identifiants
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="ID utilisateur propriétaire")
    sku: str = Field(..., description="SKU Amazon du produit")
    marketplace_id: str = Field(..., description="ID marketplace Amazon (ex: A13V1IB3VIYZZH)")
    
    # Règles de prix
    min_price: float = Field(..., gt=0, description="Prix minimum autorisé")
    max_price: float = Field(..., gt=0, description="Prix maximum autorisé")
    variance_pct: float = Field(default=5.0, ge=0, le=100, description="Variance % autorisée")
    map_price: Optional[float] = Field(None, description="Prix MAP (Minimum Advertised Price)")
    
    # Stratégie
    strategy: PricingStrategy = Field(..., description="Stratégie de pricing")
    margin_target: Optional[float] = Field(None, ge=0, le=100, description="Marge cible % (si strategy=margin_target)")
    
    # Configuration
    auto_update: bool = Field(default=True, description="Mise à jour automatique activée")
    update_frequency: int = Field(default=300, description="Fréquence MAJ en secondes")
    
    # Métadonnées
    status: PricingRuleStatus = Field(default=PricingRuleStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_applied_at: Optional[datetime] = Field(None, description="Dernière application")
    
    # Validation
    def model_post_init(self, __context):
        if self.max_price <= self.min_price:
            raise ValueError("max_price must be greater than min_price")
        if self.strategy == PricingStrategy.MARGIN_TARGET and self.margin_target is None:
            raise ValueError("margin_target is required when strategy is margin_target")


class CompetitorOffer(BaseModel):
    """Offre concurrente depuis Product Pricing API"""
    seller_id: str = Field(..., description="ID vendeur")
    condition: str = Field(default="New", description="État du produit")
    price: float = Field(..., description="Prix offre")
    shipping: float = Field(default=0.0, description="Frais de livraison")
    landed_price: float = Field(..., description="Prix total (prix + shipping)")
    is_buy_box_winner: bool = Field(default=False, description="Gagne la Buy Box")
    is_featured_merchant: bool = Field(default=False, description="Marchand mis en avant")


class PricingCalculation(BaseModel):
    """Résultat d'un calcul de prix"""
    
    # Contexte
    sku: str
    marketplace_id: str
    current_price: Optional[float] = None
    
    # Données concurrentielles
    competitors: List[CompetitorOffer] = Field(default_factory=list)
    buybox_price: Optional[float] = None
    buybox_winner: Optional[str] = None
    our_offer: Optional[CompetitorOffer] = None
    
    # Calcul
    recommended_price: float
    price_change: float = Field(default=0.0, description="Changement de prix")
    price_change_pct: float = Field(default=0.0, description="% changement")
    
    # Statut
    buybox_status: BuyBoxStatus
    within_rules: bool = Field(description="Prix respecte les règles")
    
    # Diagnostics
    reasoning: str = Field(description="Explication du calcul")
    warnings: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=100, description="Confiance dans le calcul")
    
    # Métadonnées
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    calculation_duration_ms: Optional[int] = None


class PricingHistory(BaseModel):
    """Historique des décisions de pricing"""
    
    # Identifiants
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    sku: str
    marketplace_id: str
    rule_id: str = Field(description="ID de la règle appliquée")
    
    # Prix
    old_price: Optional[float] = None
    new_price: float
    price_change: float
    price_change_pct: float
    
    # Contexte de décision
    buybox_price: Optional[float] = None
    competitors_count: int = Field(default=0)
    buybox_status_before: BuyBoxStatus
    buybox_status_after: Optional[BuyBoxStatus] = None
    
    # Résultats
    publication_success: bool = Field(description="Publication SP-API réussie")
    publication_method: Optional[str] = Field(None, description="listings_items ou feeds")
    sp_api_response: Optional[Dict[str, Any]] = Field(None, description="Réponse SP-API")
    
    # Diagnostics
    reasoning: str
    confidence: float
    warnings: List[str] = Field(default_factory=list)
    
    # Performance
    calculation_duration_ms: int
    publication_duration_ms: Optional[int] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    effective_at: Optional[datetime] = Field(None, description="Quand le prix est effectif")


class PricingBatch(BaseModel):
    """Traitement par lot de pricing"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    skus: List[str] = Field(..., description="SKUs à traiter")
    marketplace_id: str
    
    # Configuration du lot
    force_update: bool = Field(default=False, description="Forcer MAJ même si prix identique")
    dry_run: bool = Field(default=False, description="Simulation sans publication")
    
    # Résultats
    total_skus: int = Field(default=0)
    processed_skus: int = Field(default=0)
    successful_updates: int = Field(default=0)
    failed_updates: int = Field(default=0)
    skipped_skus: int = Field(default=0)
    
    # État
    status: str = Field(default="pending", description="pending|processing|completed|failed")
    progress_pct: float = Field(default=0.0, ge=0, le=100)
    
    # Résultats détaillés
    results: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Modèles de réponse API
class PricingRuleResponse(BaseModel):
    """Réponse API pour une règle de pricing"""
    success: bool
    rule: Optional[PricingRule] = None
    message: str
    errors: List[str] = Field(default_factory=list)


class PricingCalculationResponse(BaseModel):
    """Réponse API pour un calcul de prix"""
    success: bool
    calculation: Optional[PricingCalculation] = None
    message: str
    errors: List[str] = Field(default_factory=list)


class PricingHistoryResponse(BaseModel):
    """Réponse API pour l'historique"""
    success: bool
    history: List[PricingHistory]
    total_count: int
    page: int
    per_page: int
    message: str


class PricingBatchResponse(BaseModel):
    """Réponse API pour traitement par lot"""
    success: bool
    batch: Optional[PricingBatch] = None
    message: str
    errors: List[str] = Field(default_factory=list)


class PricingStats(BaseModel):
    """Statistiques de pricing"""
    total_rules: int = 0
    active_rules: int = 0
    skus_with_buybox: int = 0
    skus_at_risk: int = 0
    avg_price_change_pct: float = 0.0
    successful_updates_24h: int = 0
    failed_updates_24h: int = 0
    last_update: Optional[datetime] = None


class PricingDashboardData(BaseModel):
    """Données pour dashboard pricing"""
    stats: PricingStats
    recent_history: List[PricingHistory]
    rules_summary: List[Dict[str, Any]]
    buybox_alerts: List[Dict[str, Any]]