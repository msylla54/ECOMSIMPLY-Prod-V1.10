# ================================================================================
# ECOMSIMPLY - MODÈLES COMPLETS POUR GESTION ABONNEMENTS STRIPE - VERSION ROBUSTE
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
    """Plans disponibles"""
    GRATUIT = "gratuit"
    PRO = "pro" 
    PREMIUM = "premium"

class PaymentAttempt(BaseModel):
    """Tentative de paiement"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stripe_checkout_session_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    plan_type: PlanType
    amount: float
    currency: str = "eur"
    status: str  # pending, succeeded, failed, abandoned
    with_trial: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class User(BaseModel):
    """Modèle utilisateur avec gestion abonnement robuste"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    password_hash: str
    name: Optional[str] = None
    
    # 🔥 GESTION ABONNEMENT STRIPE
    stripe_customer_id: Optional[str] = None
    subscription_plan: PlanType = PlanType.GRATUIT
    subscription_status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    stripe_subscription_id: Optional[str] = None
    
    # 🎯 LOGIQUE ESSAI GRATUIT ROBUSTE
    has_used_trial: bool = False
    trial_start_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    trial_attempts: List[PaymentAttempt] = Field(default_factory=list)
    
    # 📊 HISTORIQUE PAIEMENTS ÉTENDU
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
    
    # 🎫 LIMITES PAR PLAN
    monthly_sheets_limit: int = 1  # Gratuit: 1, Pro: 100, Premium: illimité
    monthly_sheets_used: int = 0
    
    # 🎨 BLOC 3 - PHASE 3: GESTION IMAGES
    generate_images: bool = True  # Contrôle la génération des images dans la fiche
    include_images_manual: bool = True  # Contrôle l'inclusion en publication manuelle (si images générées)
    
    def is_trial_active(self) -> bool:
        """Vérifie si l'essai gratuit est actuel"""
        if not self.trial_end_date:
            return False
        return datetime.utcnow() < self.trial_end_date and self.subscription_status == SubscriptionStatus.TRIALING
    
    def is_trial_expired(self) -> bool:
        """Vérifie si l'essai est expiré"""
        if not self.trial_end_date:
            return False
        return datetime.utcnow() > self.trial_end_date
    
    def can_start_trial(self) -> bool:
        """Peut démarrer un essai gratuit (une seule fois)"""
        return not self.has_used_trial
    
    def can_start_new_subscription(self) -> bool:
        """Peut démarrer un nouvel abonnement (même après échec)"""
        return self.can_retry_subscription and self.subscription_plan == PlanType.GRATUIT
    
    def has_had_successful_payment(self) -> bool:
        """A déjà eu un paiement réussi"""
        return self.last_payment_date is not None
    
    def has_incomplete_subscriptions(self) -> bool:
        """A des abonnements incomplets à récupérer"""
        return len(self.incomplete_subscriptions) > 0
    
    def is_subscription_active(self) -> bool:
        """Vérifie si l'abonnement est actif"""
        if self.subscription_plan == PlanType.GRATUIT:
            return True
        
        # Si en période d'essai active
        if self.is_trial_active():
            return True
            
        # Si abonnement payant actif
        return self.subscription_status in [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING
        ]
    
    def can_access_features(self) -> bool:
        """Peut accéder aux fonctionnalités premium"""
        return self.is_subscription_active()
    
    def requires_payment_action(self) -> bool:
        """Nécessite une action de paiement"""
        return self.subscription_status in [
            SubscriptionStatus.PAST_DUE,
            SubscriptionStatus.UNPAID,
            SubscriptionStatus.INCOMPLETE
        ] or self.payment_failed_count > 0
    
    def get_monthly_limit(self) -> int:
        """Retourne la limite mensuelle selon le plan"""
        limits = {
            PlanType.GRATUIT: 1,
            PlanType.PRO: 100,
            PlanType.PREMIUM: float('inf')
        }
        return limits.get(self.subscription_plan, 1)
    
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
    """Historique des abonnements"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # 💳 STRIPE DATA
    stripe_subscription_id: str
    stripe_customer_id: str
    stripe_price_id: str
    
    # 📋 PLAN INFO
    plan_type: PlanType
    status: SubscriptionStatus
    
    # 📅 DATES
    current_period_start: datetime
    current_period_end: datetime
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    
    # 💰 PRICING
    amount: float
    currency: str = "eur"
    interval: str = "month"  # month, year
    
    # 🔄 METADATA
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    canceled_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    # 📊 WEBHOOKS TRACKING
    last_webhook_event: Optional[str] = None
    webhook_events: List[Dict[str, Any]] = Field(default_factory=list)

class PaymentHistory(BaseModel):
    """Historique des paiements"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # 💳 STRIPE DATA
    stripe_invoice_id: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    stripe_charge_id: Optional[str] = None
    
    # 💰 PAYMENT INFO
    amount: float
    currency: str = "eur"
    status: str  # succeeded, failed, pending, incomplete
    
    # 📋 DETAILS
    plan_type: PlanType
    billing_reason: Optional[str] = None  # subscription_create, subscription_cycle, etc.
    failure_reason: Optional[str] = None
    
    # 📅 DATES
    created_at: datetime = Field(default_factory=datetime.utcnow)
    paid_at: Optional[datetime] = None
    
    # 🔄 METADATA
    metadata: Dict[str, Any] = Field(default_factory=dict)

# ================================================================================
# MODÈLES DE REQUÊTE API
# ================================================================================

class CreateSubscriptionRequest(BaseModel):
    """Demande de création d'abonnement"""
    plan_type: PlanType
    price_id: str
    success_url: str
    cancel_url: str
    with_trial: bool = False

class SubscriptionResponse(BaseModel):
    """Réponse abonnement"""
    checkout_url: Optional[str] = None
    subscription_id: Optional[str] = None
    customer_id: Optional[str] = None
    status: str
    message: str
    trial_active: bool = False
    trial_end_date: Optional[datetime] = None

class UserSubscriptionStatus(BaseModel):
    """Statut complet de l'abonnement utilisateur"""
    user_id: str
    plan_type: PlanType
    status: SubscriptionStatus
    
    # 🎯 TRIAL INFO
    can_start_trial: bool
    has_used_trial: bool
    trial_active: bool
    trial_end_date: Optional[datetime] = None
    
    # 📊 USAGE INFO
    monthly_limit: int
    monthly_used: int
    can_access_features: bool
    
    # 💰 BILLING INFO
    next_billing_date: Optional[datetime] = None
    amount: Optional[float] = None
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
    """Demande de récupération d'abonnement"""
    subscription_id: Optional[str] = None
    plan_type: Optional[PlanType] = None
    recovery_type: str = "retry"  # retry, new, update_payment

class IncompleteSubscriptionInfo(BaseModel):
    """Informations abonnement incomplet"""
    id: str
    status: str
    plan_name: str
    amount: float
    currency: str
    created_at: datetime
    failure_reason: Optional[str] = None
    can_retry: bool = True

# ================================================================================
# CONFIGURATION STRIPE
# ================================================================================

STRIPE_PRICE_IDS = {
    "pro_monthly": "price_1Rrw3UGK8qzu5V5Wu8PnvKzK",
    "premium_monthly": "price_1RrxgjGK8qzu5V5WvOSb4uPd"
}

PLAN_CONFIG = {
    PlanType.GRATUIT: {
        "name": "Gratuit",
        "price": 0,
        "currency": "eur",
        "features": ["1 fiche/mois", "IA basique", "Export CSV"],
        "sheets_limit": 1
    },
    PlanType.PRO: {
        "name": "Pro",
        "price": 29,
        "currency": "eur", 
        "stripe_price_id": "price_1Rrw3UGK8qzu5V5Wu8PnvKzK",
        "features": ["100 fiches/mois", "IA avancée", "Images HD", "Export multi-format"],
        "sheets_limit": 100
    },
    PlanType.PREMIUM: {
        "name": "Premium",
        "price": 99,
        "currency": "eur",
        "stripe_price_id": "price_1RrxgjGK8qzu5V5WvOSb4uPd", 
        "features": ["Fiches illimitées", "IA premium", "Images HD", "Analytics", "Support dédié"],
        "sheets_limit": float('inf')
    }
}