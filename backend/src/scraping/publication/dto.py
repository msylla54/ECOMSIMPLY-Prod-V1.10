"""
Publication DTO - Structure de données pour les tâches de publication - ECOMSIMPLY
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, validator, Field
from enum import Enum
from datetime import datetime

from ..semantic import ProductDTO


class PublicationStatus(str, Enum):
    """Status de publication"""
    PENDING = "pending"           # En attente
    PROCESSING = "processing"     # En cours
    SUCCESS = "success"          # Réussie
    FAILED = "failed"            # Échouée
    SKIPPED_GUARDRAIL = "skipped_guardrail"  # Bloquée par guardrails
    SKIPPED_DUPLICATE = "skipped_duplicate"  # Doublé détecté
    RATE_LIMITED = "rate_limited"            # Rate limit atteint


class StoreType(str, Enum):
    """Types de boutiques supportées"""
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    PRESTASHOP = "prestashop"
    MAGENTO = "magento"
    WIX = "wix"
    SQUARESPACE = "squarespace"
    BIGCOMMERCE = "bigcommerce"
    MOCK_STORE = "mock_store"     # Pour tests


class PublishTask(BaseModel):
    """Tâche de publication individuelle"""
    
    # Identification
    task_id: str = Field(..., description="ID unique de la tâche")
    store_id: str = Field(..., description="ID boutique cible")
    store_type: StoreType = Field(..., description="Type de boutique")
    
    # Données produit
    product_dto: ProductDTO = Field(..., description="ProductDTO à publier")
    
    # Métadonnées publication
    status: PublicationStatus = Field(default=PublicationStatus.PENDING, description="Status publication")
    created_at: datetime = Field(default_factory=datetime.now, description="Date création tâche")
    started_at: Optional[datetime] = Field(None, description="Date début traitement")
    completed_at: Optional[datetime] = Field(None, description="Date fin traitement")
    
    # Résultats
    result_data: Optional[Dict[str, Any]] = Field(None, description="Données résultat")
    error_message: Optional[str] = Field(None, description="Message d'erreur")
    retry_count: int = Field(default=0, description="Nombre de tentatives")
    
    # Configuration
    priority: int = Field(default=5, ge=1, le=10, description="Priorité (1=urgent, 10=bas)")
    publish_options: Dict[str, Any] = Field(default_factory=dict, description="Options publication")
    
    @validator('task_id')
    def validate_task_id_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Task ID ne peut pas être vide')
        return v.strip()
    
    @validator('store_id') 
    def validate_store_id_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Store ID ne peut pas être vide')
        return v.strip()
    
    def is_completed(self) -> bool:
        """Vérifier si la tâche est terminée"""
        return self.status in [
            PublicationStatus.SUCCESS,
            PublicationStatus.FAILED,
            PublicationStatus.SKIPPED_GUARDRAIL,
            PublicationStatus.SKIPPED_DUPLICATE
        ]
    
    def is_retryable(self) -> bool:
        """Vérifier si la tâche peut être retentée"""
        return (
            self.status == PublicationStatus.FAILED and
            self.retry_count < 3 and
            self.error_message and
            'rate_limit' not in self.error_message.lower()
        )
    
    def mark_started(self):
        """Marquer tâche comme démarrée"""
        self.status = PublicationStatus.PROCESSING
        self.started_at = datetime.now()
    
    def mark_success(self, result_data: Dict[str, Any]):
        """Marquer tâche comme réussie"""
        self.status = PublicationStatus.SUCCESS
        self.completed_at = datetime.now()
        self.result_data = result_data
        self.error_message = None
    
    def mark_failed(self, error_message: str):
        """Marquer tâche comme échouée"""
        self.status = PublicationStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error_message
        self.retry_count += 1
    
    def mark_skipped(self, reason: str):
        """Marquer tâche comme ignorée"""
        if 'guardrail' in reason.lower():
            self.status = PublicationStatus.SKIPPED_GUARDRAIL
        elif 'duplicate' in reason.lower():
            self.status = PublicationStatus.SKIPPED_DUPLICATE
        else:
            self.status = PublicationStatus.FAILED
        
        self.completed_at = datetime.now()
        self.error_message = reason
    
    def get_duration(self) -> Optional[float]:
        """Obtenir durée de traitement en secondes"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class PublishBatch(BaseModel):
    """Batch de tâches de publication"""
    
    batch_id: str = Field(..., description="ID unique du batch")
    tasks: List[PublishTask] = Field(..., description="Liste des tâches")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Statistiques
    total_tasks: int = Field(default=0, description="Nombre total de tâches")
    completed_tasks: int = Field(default=0, description="Tâches terminées")
    successful_tasks: int = Field(default=0, description="Tâches réussies")
    failed_tasks: int = Field(default=0, description="Tâches échouées")
    skipped_tasks: int = Field(default=0, description="Tâches ignorées")
    
    def update_stats(self):
        """Mettre à jour les statistiques"""
        self.total_tasks = len(self.tasks)
        self.completed_tasks = len([t for t in self.tasks if t.is_completed()])
        self.successful_tasks = len([t for t in self.tasks if t.status == PublicationStatus.SUCCESS])
        self.failed_tasks = len([t for t in self.tasks if t.status == PublicationStatus.FAILED])
        self.skipped_tasks = len([t for t in self.tasks if t.status.startswith('skipped')])
    
    def is_completed(self) -> bool:
        """Vérifier si le batch est terminé"""
        return self.completed_tasks == self.total_tasks
    
    def get_success_rate(self) -> float:
        """Taux de succès du batch"""
        if self.total_tasks == 0:
            return 0.0
        return (self.successful_tasks / self.total_tasks) * 100
    
    def get_pending_tasks(self) -> List[PublishTask]:
        """Obtenir les tâches en attente"""
        return [t for t in self.tasks if t.status == PublicationStatus.PENDING]
    
    def get_retryable_tasks(self) -> List[PublishTask]:
        """Obtenir les tâches qui peuvent être retentées"""
        return [t for t in self.tasks if t.is_retryable()]


class PublicationConfig(BaseModel):
    """Configuration pour la publication automatique"""
    
    # Fenêtres de publication
    active_hours_start: int = Field(default=8, ge=0, le=23, description="Heure début (8h)")
    active_hours_end: int = Field(default=20, ge=0, le=23, description="Heure fin (20h)")
    
    # Rate limiting
    max_publications_per_hour: int = Field(default=10, ge=1, description="Max publications/heure")
    cooldown_between_publications: int = Field(default=300, ge=60, description="Cooldown en secondes")
    
    # Batch processing
    batch_size: int = Field(default=3, ge=1, le=10, description="Taille batch")
    max_concurrent_workers: int = Field(default=2, ge=1, le=5, description="Workers concurrents max")
    
    # Retry policy
    max_retries: int = Field(default=3, ge=0, le=5, description="Tentatives max")
    retry_delay: int = Field(default=1800, ge=300, description="Délai retry en secondes")
    
    # Guardrails
    enable_price_guardrails: bool = Field(default=True, description="Activer garde-fous prix")
    price_variance_threshold: float = Field(default=0.20, ge=0.1, le=0.5, description="Seuil écart prix")
    min_confidence_score: float = Field(default=0.6, ge=0.1, le=1.0, description="Score confiance min")
    
    def is_active_hours(self, current_hour: Optional[int] = None) -> bool:
        """Vérifier si on est dans les heures actives"""
        if current_hour is None:
            current_hour = datetime.now().hour
        
        return self.active_hours_start <= current_hour <= self.active_hours_end
    
    def calculate_next_slot(self) -> datetime:
        """Calculer le prochain créneau de publication"""
        now = datetime.now()
        
        if self.is_active_hours():
            # Dans les heures actives → prochain slot après cooldown
            return now + datetime.timedelta(seconds=self.cooldown_between_publications)
        else:
            # Hors heures actives → prochain slot le lendemain à l'heure de début
            tomorrow = now.replace(hour=self.active_hours_start, minute=0, second=0, microsecond=0)
            if tomorrow <= now:
                tomorrow += datetime.timedelta(days=1)
            return tomorrow