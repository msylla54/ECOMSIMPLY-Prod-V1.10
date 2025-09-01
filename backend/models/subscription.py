# ================================================================================
# ECOMSIMPLY - MODÈLES SIMPLIFIÉS OFFRE UNIQUE PREMIUM - VERSION PRODUCTION
# ================================================================================

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
import uuid

class SubscriptionStatus(str, Enum):
    """États possibles de l'abonnement"""
    ACTIVE = "active"
    TRIALING = "trialing" 
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAUSED = "paused"

class PlanType(str, Enum):
    """Plan unique Premium"""
    PREMIUM = "premium"

class PaymentAttempt(BaseModel):
    """Tentative de paiement"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stripe_checkout_session_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    plan_type: PlanType = PlanType.PREMIUM
    amount: float = 99.0
    currency: str = "eur"
    status: str  # pending, succeeded, failed, abandoned
    with_trial: bool = True  # Toujours avec essai 3 jours
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class User(BaseModel):
    """Modèle utilisateur simplifié pour offre unique Premium"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    password_hash: str
    name: Optional[str] = None
    
    # 🔥 GESTION ABONNEMENT STRIPE PREMIUM UNIQUEMENT
    stripe_customer_id: Optional[str] = None
    subscription_plan: PlanType = PlanType.PREMIUM
    subscription_status: SubscriptionStatus = SubscriptionStatus.TRIALING
    stripe_subscription_id: Optional[str] = None
    
    # 🎯 ESSAI GRATUIT 3 JOURS UNIQUE
    has_used_trial: bool = False
    trial_start_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    trial_attempts: List[PaymentAttempt] = Field(default_factory=list)
    
    # 📊 HISTORIQUE PAIEMENTS
    last_payment_date: Optional[datetime] = None
    payment_failed_date: Optional[datetime] = None
    payment_failed_count: int = 0
    payment_attempts: List[PaymentAttempt] = Field(default_factory=list)
    
    # 🔄 RECOVERY & GESTION ÉTATS
    failed_checkout_sessions: List[str] = Field(default_factory=list)
    incomplete_subscriptions: List[str] = Field(default_factory=list)
    can_retry_subscription: bool = True
    last_subscription_attempt: Optional[datetime] = None
    recovery_attempts: int = 0
    
    # 🔄 MÉTADONNÉES
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 🎫 USAGE PREMIUM ILLIMITÉ
    monthly_sheets_limit: int = float('inf')  # Premium illimité
    monthly_sheets_used: int = 0
    
    # 🎨 FONCTIONNALITÉS PREMIUM
    generate_images: bool = True
    include_images_manual: bool = True
    
    def is_trial_active(self) -> bool:
        """Vérifie si l'essai gratuit 3 jours est actuel"""
        if not self.trial_end_date:
            return False
        return datetime.utcnow() < self.trial_end_date and self.subscription_status == SubscriptionStatus.TRIALING
    
    def is_trial_expired(self) -> bool:
        """Vérifie si l'essai 3 jours est expiré"""
        if not self.trial_end_date:
            return False
        return datetime.utcnow() > self.trial_end_date
    
    def can_start_trial(self) -> bool:
        """Peut démarrer un essai gratuit 3 jours (une seule fois)"""
        return not self.has_used_trial
    
    def can_start_new_subscription(self) -> bool:
        """Peut démarrer un nouvel abonnement Premium"""
        return self.can_retry_subscription
    
    def has_had_successful_payment(self) -> bool:
        """A déjà eu un paiement réussi"""
        return self.last_payment_date is not None
    
    def has_incomplete_subscriptions(self) -> bool:
        """A des abonnements incomplets à récupérer"""
        return len(self.incomplete_subscriptions) > 0
    
    def is_subscription_active(self) -> bool:
        """Vérifie si l'abonnement Premium est actif"""
        # Si en période d'essai 3 jours active
        if self.is_trial_active():
            return True
            
        # Si abonnement Premium payant actif
        return self.subscription_status in [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING
        ]
    
    def can_access_features(self) -> bool:
        """Peut accéder aux fonctionnalités Premium"""
        return self.is_subscription_active()
    
    def requires_payment_action(self) -> bool:
        """Nécessite une action de paiement"""
        return self.subscription_status in [
            SubscriptionStatus.PAST_DUE,
            SubscriptionStatus.UNPAID,
            SubscriptionStatus.INCOMPLETE
        ] or self.payment_failed_count > 0
    
    def get_monthly_limit(self) -> int:
        """Retourne la limite mensuelle Premium illimitée"""
        return float('inf')
    
    def get_recovery_options(self) -> Dict[str, Any]:
        """Options de récupération disponibles"""
        return {
            "can_start_trial": self.can_start_trial(),
            "can_subscribe_directly": self.can_start_new_subscription(),
            "needs_payment_update": self.payment_failed_count > 0,
            "has_incomplete_subscriptions": self.has_incomplete_subscriptions(),
            "requires_payment_action": self.requires_payment_action(),
            "recovery_attempts": self.recovery_attempts,
            "can_retry": self.can_retry_subscription,
            "last_attempt": self.last_subscription_attempt
        }
    
    def add_payment_attempt(self, attempt: PaymentAttempt):
        """Ajoute une tentative de paiement à l'historique"""
        self.payment_attempts.append(attempt)
        self.last_subscription_attempt = datetime.utcnow()
        
        if attempt.with_trial:
            self.trial_attempts.append(attempt)
        
        # Limiter l'historique à 50 tentatives max
        if len(self.payment_attempts) > 50:
            self.payment_attempts = self.payment_attempts[-50:]

class SubscriptionRecord(BaseModel):
    """Historique des abonnements Premium"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # 💳 STRIPE DATA
    stripe_subscription_id: str
    stripe_customer_id: str
    stripe_price_id: str = "price_1RrxgjGK8qzu5V5WvOSb4uPd"  # Premium uniquement
    
    # 📋 PLAN INFO
    plan_type: PlanType = PlanType.PREMIUM
    status: SubscriptionStatus
    
    # 📅 DATES
    current_period_start: datetime
    current_period_end: datetime
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    
    # 💰 PRICING PREMIUM
    amount: float = 99.0
    currency: str = "eur"
    interval: str = "month"
    
    # 🔄 METADATA
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    canceled_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    # 📊 WEBHOOKS TRACKING
    last_webhook_event: Optional[str] = None
    webhook_events: List[Dict[str, Any]] = Field(default_factory=list)

class PaymentHistory(BaseModel):
    """Historique des paiements Premium"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # 💳 STRIPE DATA
    stripe_invoice_id: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    stripe_charge_id: Optional[str] = None
    
    # 💰 PAYMENT INFO
    amount: float = 99.0
    currency: str = "eur"
    status: str  # succeeded, failed, pending, incomplete
    
    # 📋 DETAILS
    plan_type: PlanType = PlanType.PREMIUM
    billing_reason: Optional[str] = None
    failure_reason: Optional[str] = None
    
    # 📅 DATES
    created_at: datetime = Field(default_factory=datetime.utcnow)
    paid_at: Optional[datetime] = None
    
    # 🔄 METADATA
    metadata: Dict[str, Any] = Field(default_factory=dict)

# ================================================================================
# MODÈLES DE REQUÊTE API SIMPLIFIÉS
# ================================================================================

class CreateSubscriptionRequest(BaseModel):
    """Demande de création d'abonnement Premium"""
    plan_type: PlanType = PlanType.PREMIUM
    price_id: str = "price_1RrxgjGK8qzu5V5WvOSb4uPd"
    success_url: str
    cancel_url: str
    with_trial: bool = True  # Toujours avec essai 3 jours

class SubscriptionResponse(BaseModel):
    """Réponse abonnement Premium"""
    checkout_url: Optional[str] = None
    subscription_id: Optional[str] = None
    customer_id: Optional[str] = None
    status: str
    message: str
    trial_active: bool = True
    trial_days: int = 3
    trial_end_date: Optional[datetime] = None

class UserSubscriptionStatus(BaseModel):
    """Statut complet de l'abonnement Premium"""
    user_id: str
    plan_type: PlanType = PlanType.PREMIUM
    status: SubscriptionStatus
    
    # 🎯 TRIAL INFO 3 JOURS
    can_start_trial: bool
    has_used_trial: bool
    trial_active: bool
    trial_days: int = 3
    trial_end_date: Optional[datetime] = None
    
    # 📊 USAGE INFO PREMIUM
    monthly_limit: int = float('inf')
    monthly_used: int
    can_access_features: bool
    
    # 💰 BILLING INFO
    next_billing_date: Optional[datetime] = None
    amount: float = 99.0
    currency: str = "eur"
    
    # 🚨 ALERTS & RECOVERY
    payment_failed: bool = False
    requires_action: bool = False
    requires_payment_action: bool = False
    has_incomplete_subscriptions: bool = False
    can_subscribe_directly: bool = True
    recovery_options: Dict[str, Any] = Field(default_factory=dict)
    message: Optional[str] = None

class RecoveryRequest(BaseModel):
    """Demande de récupération d'abonnement Premium"""
    subscription_id: Optional[str] = None
    plan_type: PlanType = PlanType.PREMIUM
    recovery_type: str = "retry"

class IncompleteSubscriptionInfo(BaseModel):
    """Informations abonnement Premium incomplet"""
    id: str
    status: str
    plan_name: str = "Premium"
    amount: float = 99.0
    currency: str = "eur"
    created_at: datetime
    failure_reason: Optional[str] = None
    can_retry: bool = True

# ================================================================================
# CONFIGURATION STRIPE PREMIUM UNIQUEMENT
# ================================================================================

STRIPE_PRICE_IDS = {
    "premium_monthly": "price_1RrxgjGK8qzu5V5WvOSb4uPd"
}

PLAN_CONFIG = {
    PlanType.PREMIUM: {
        "name": "Premium",
        "price": 99.0,
        "currency": "eur",
        "stripe_price_id": "price_1RrxgjGK8qzu5V5WvOSb4uPd", 
        "trial_days": 3,
        "features": [
            "Fiches produits illimitées",
            "IA Premium + Automation complète", 
            "Publication multi-plateformes",
            "Analytics avancées + exports",
            "Support prioritaire 24/7",
            "API accès complet",
            "Intégrations personnalisées"
        ],
        "sheets_limit": float('inf')
    }
}