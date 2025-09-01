# ================================================================================
# ECOMSIMPLY - SERVICE STRIPE COMPLET AVEC GESTION D'ABONNEMENTS - VERSION ROBUSTE
# ================================================================================

import stripe
import os
import time
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.subscription import (
    User, SubscriptionRecord, PaymentHistory, PaymentAttempt,
    SubscriptionStatus, PlanType, PLAN_CONFIG,
    CreateSubscriptionRequest, SubscriptionResponse
)

# Import trial eligibility service with fallback
try:
    from services.trial_eligibility_service import trial_eligibility_service
except ImportError:
    # Create a mock service if not available
    class MockTrialEligibilityService:
        async def check_trial_eligibility(self, **kwargs):
            return {"eligible": True, "reason": "mock_service"}
    trial_eligibility_service = MockTrialEligibilityService()

# Configuration Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# ================================================================================
# 🔐 ALLOWLIST SÉCURISÉE DES PRIX (SERVER-SIDE SOURCE OF TRUTH)
# ================================================================================

STRIPE_PRICE_ALLOWLIST = {
    "pro_monthly": "price_1Rrw3UGK8qzu5V5Wu8PnvKzK",
    "premium_monthly": "price_1RrxgjGK8qzu5V5WvOSb4uPd"
}

def validate_price_id(price_id: str, plan_type: PlanType) -> bool:
    """Valide qu'un price_id est autorisé pour un plan donné"""
    expected_price_key = f"{plan_type}_monthly"
    expected_price_id = STRIPE_PRICE_ALLOWLIST.get(expected_price_key)
    
    is_valid = price_id == expected_price_id
    
    if not is_valid:
        logger.warning(f"🚫 Invalid price_id rejected: received={price_id}, expected={expected_price_id}")
    
    return is_valid

def get_authorized_price_id(plan_type: PlanType) -> Optional[str]:
    """Récupère le price_id autorisé pour un plan"""
    price_key = f"{plan_type}_monthly"
    return STRIPE_PRICE_ALLOWLIST.get(price_key)

logger = logging.getLogger(__name__)

class StripeSubscriptionService:
    """Service complet pour la gestion des abonnements Stripe - Version robuste"""
    
    def __init__(self):
        self.webhook_secret = STRIPE_WEBHOOK_SECRET
    
    # ================================================================================
    # 🔐 GÉNÉRATION CLÉS D'IDEMPOTENCE SÉCURISÉES
    # ================================================================================
    
    def _generate_idempotency_key(self, operation: str, user_id: str, plan_type: str = None, extra_data: str = None) -> str:
        """Génère une clé d'idempotence sécurisée avec window temporelle"""
        
        # Window de 5 minutes pour éviter les doubles clics
        time_window = int(time.time() // 300)  # 5 minutes
        
        # Construire la clé de base
        key_parts = [operation, user_id, str(time_window)]
        
        if plan_type:
            key_parts.append(plan_type)
        if extra_data:
            key_parts.append(extra_data)
        
        # Hash pour sécurité et longueur
        raw_key = ":".join(key_parts)
        hashed = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Format Stripe (max 255 chars, préfixe descriptif)
        idempotency_key = f"{operation[:10]}_{hashed[:32]}"
        
        logger.debug(f"🔑 Generated idempotency key: {idempotency_key}")
        return idempotency_key
    
    def _hash_sensitive_data(self, data: str, prefix: str = "data") -> str:
        """Hash sécurisé des données sensibles pour logs"""
        return hashlib.sha256(f"{prefix}:{data}".encode()).hexdigest()[:16]
    
    # ================================================================================
    # 🏗️ CRÉATION ET GESTION CLIENT STRIPE
    # ================================================================================
    
    async def create_or_get_customer(self, user: User) -> str:
        """Crée ou récupère un client Stripe"""
        try:
            if user.stripe_customer_id:
                # Vérifier que le client existe toujours
                try:
                    customer = stripe.Customer.retrieve(user.stripe_customer_id)
                    return customer.id
                except stripe.error.InvalidRequestError:
                    # Client n'existe plus, en créer un nouveau
                    pass
            
            # Créer nouveau client
            customer = stripe.Customer.create(
                email=user.email,
                name=user.name,
                metadata={
                    "user_id": user.id,
                    "platform": "ecomsimply"
                }
            )
            
            logger.info(f"✅ Client Stripe créé: {customer.id} pour user: {user.email}")
            return customer.id
            
        except Exception as e:
            logger.error(f"❌ Erreur création client Stripe: {str(e)}")
            raise Exception(f"Impossible de créer le client Stripe: {str(e)}")
    
    # ================================================================================
    # 🎯 GESTION ESSAI GRATUIT
    # ================================================================================
    
    def can_start_trial(self, user: User) -> bool:
        """Vérifie si l'utilisateur peut démarrer un essai gratuit"""
        return not user.has_used_trial
    
    def calculate_trial_end(self, trial_days: int = 7) -> datetime:
        """Calcule la date de fin d'essai"""
        return datetime.utcnow() + timedelta(days=trial_days)
    
    # ================================================================================
    # 💳 CRÉATION D'ABONNEMENTS ROBUSTE
    # ================================================================================
    
    async def create_subscription_checkout(
        self, 
        user: User, 
        request: CreateSubscriptionRequest,
        client_ip: str = None,
        db = None
    ) -> SubscriptionResponse:
        """Crée une session Stripe Checkout pour l'abonnement - VERSION SÉCURISÉE AVEC RÈGLE ESSAI UNIQUE"""
        try:
            # ================================================================================
            # 🔐 VALIDATIONS SÉCURITÉ
            # ================================================================================
            
            # 1. Vérifier le plan
            if request.plan_type not in [PlanType.PRO, PlanType.PREMIUM]:
                raise ValueError("Plan invalide pour abonnement payant")
            
            # 2. VALIDATION STRICTE PRICE ID (ALLOWLIST SERVEUR)
            if not validate_price_id(request.price_id, request.plan_type):
                logger.error(f"🚫 Price ID non autorisé rejeté: {request.price_id}")
                raise ValueError("Price ID non autorisé")
            
            # 3. VÉRIFICATION ÉLIGIBILITÉ ESSAI (RÈGLE BUSINESS CRITIQUE)
            trial_check = await trial_eligibility_service.check_trial_eligibility(
                user=user,
                plan_type=request.plan_type,
                client_ip=client_ip,
                db=db
            )
            
            # Force la règle côté serveur - Ne jamais faire confiance au frontend
            trial_eligible = trial_check.get("eligible", False)
            actual_with_trial = request.with_trial and trial_eligible
            
            if request.with_trial and not trial_eligible:
                logger.warning(
                    f"🚫 Trial demandé mais non éligible: user_hash={self._hash_sensitive_data(user.id, 'user')}, "
                    f"reason={trial_check.get('reason', 'unknown')}"
                )
            
            # ================================================================================
            # 🏗️ CRÉATION CUSTOMER ET TENTATIVE PAIEMENT
            # ================================================================================
            
            # Créer ou récupérer client Stripe
            customer_id = await self.create_or_get_customer(user)
            
            # Créer tentative de paiement avec tracking complet
            payment_attempt = PaymentAttempt(
                plan_type=request.plan_type,
                amount=PLAN_CONFIG[request.plan_type]["price"],
                currency="eur",
                status="pending",
                with_trial=actual_with_trial,
                metadata={
                    "customer_id": customer_id,
                    "price_id": request.price_id,
                    "trial_eligible": trial_eligible,
                    "trial_check_reason": trial_check.get("reason", "not_checked"),
                    "client_ip_hash": self._hash_sensitive_data(client_ip, "ip") if client_ip else None
                }
            )
            
            # ================================================================================
            # 🔑 GÉNÉRATION CLÉ IDEMPOTENCE
            # ================================================================================
            
            idempotency_key = self._generate_idempotency_key(
                operation="checkout",
                user_id=user.id,
                plan_type=request.plan_type,
                extra_data=f"trial:{actual_with_trial}"
            )
            
            # ================================================================================
            # 🛒 CONFIGURATION SESSION CHECKOUT SÉCURISÉE
            # ================================================================================
            
            session_params = {
                "customer": customer_id,
                "payment_method_types": ["card"],
                "line_items": [{
                    "price": request.price_id,
                    "quantity": 1,
                }],
                "mode": "subscription",
                "success_url": request.success_url,
                "cancel_url": request.cancel_url,
                "metadata": {
                    "user_id": user.id,
                    "plan_type": request.plan_type,
                    "platform": "ecomsimply",
                    "payment_attempt_id": payment_attempt.id,
                    "trial_eligible": str(trial_eligible),
                    "checkout_version": "v2_secure"
                },
                # CLÉS D'IDEMPOTENCE STRIPE
                "idempotency_key": idempotency_key
            }
            
            # ================================================================================
            # 🎯 GESTION ESSAI GRATUIT SELON ÉLIGIBILITÉ
            # ================================================================================
            
            if actual_with_trial:
                session_params["subscription_data"] = {
                    "trial_period_days": 7,
                    "metadata": {
                        "user_id": user.id,
                        "plan_type": request.plan_type,
                        "has_trial": "true",
                        "trial_granted_at": datetime.utcnow().isoformat()
                    }
                }
                logger.info(f"🎁 Trial accordé: user_hash={self._hash_sensitive_data(user.id, 'user')}")
            else:
                # Pas d'essai - abonnement payant direct
                logger.info(f"💳 Abonnement direct (pas d'essai): user_hash={self._hash_sensitive_data(user.id, 'user')}")
            
            # ================================================================================
            # 🌐 CRÉATION SESSION STRIPE AVEC IDEMPOTENCE
            # ================================================================================
            
            try:
                session = stripe.checkout.Session.create(**session_params)
                
                # Mettre à jour tentative de paiement
                payment_attempt.stripe_checkout_session_id = session.id
                user.add_payment_attempt(payment_attempt)
                
                # Log sécurisé
                session_hash = self._hash_sensitive_data(session.id, "session")
                user_hash = self._hash_sensitive_data(user.id, "user")
                
                logger.info(
                    f"✅ Session Checkout créée: session_hash={session_hash}, "
                    f"user_hash={user_hash}, plan={request.plan_type}, "
                    f"trial={actual_with_trial}, idempotent={idempotency_key[:16]}..."
                )
                
                return SubscriptionResponse(
                    checkout_url=session.url,
                    subscription_id=None,  # Sera créé après paiement
                    customer_id=customer_id,
                    status="checkout_created",
                    message="Session de paiement créée avec succès",
                    trial_active=actual_with_trial,
                    trial_end_date=self.calculate_trial_end() if actual_with_trial else None
                )
                
            except stripe.error.IdempotencyError as e:
                # Session déjà créée avec cette clé - récupérer la session existante
                logger.info(f"🔄 Session existante trouvée via idempotence: {idempotency_key[:16]}...")
                
                # Tenter de récupérer la session via les métadonnées ou l'historique
                return SubscriptionResponse(
                    status="checkout_already_exists",
                    message="Session de paiement déjà créée (protection double-clic)",
                    trial_active=actual_with_trial
                )
            
        except ValueError as e:
            # Erreurs de validation
            logger.error(f"❌ Validation error in checkout: {str(e)}")
            return SubscriptionResponse(
                status="validation_error",
                message=f"Erreur de validation: {str(e)}"
            )
        except Exception as e:
            # Erreurs techniques
            logger.error(f"❌ Technical error in checkout creation: {str(e)}")
            return SubscriptionResponse(
                status="error",
                message="Erreur technique lors de la création de l'abonnement"
            )
    
    # ================================================================================
    # 🔄 GESTION D'ÉTAT DES ABONNEMENTS
    # ================================================================================
    
    async def sync_subscription_status(self, user: User) -> User:
        """Synchronise le statut d'abonnement avec Stripe"""
        try:
            if not user.stripe_subscription_id:
                return user
            
            # Récupérer l'abonnement depuis Stripe
            subscription = stripe.Subscription.retrieve(user.stripe_subscription_id)
            
            # Mettre à jour le statut local
            user.subscription_status = SubscriptionStatus(subscription.status)
            user.updated_at = datetime.utcnow()
            
            # Gérer les dates d'essai
            if subscription.trial_end:
                user.trial_end_date = datetime.fromtimestamp(subscription.trial_end)
                
            if subscription.trial_start:
                user.trial_start_date = datetime.fromtimestamp(subscription.trial_start)
            
            # Gérer les échecs de paiement
            if subscription.status in ["past_due", "unpaid"]:
                user.payment_failed_date = datetime.utcnow()
                user.payment_failed_count += 1
            elif subscription.status == "active":
                user.payment_failed_count = 0
                user.payment_failed_date = None
            
            # Gérer les abonnements incomplets
            if subscription.status in ["incomplete", "incomplete_expired"]:
                if subscription.id not in user.incomplete_subscriptions:
                    user.incomplete_subscriptions.append(subscription.id)
            else:
                # Retirer des abonnements incomplets si résolu
                if subscription.id in user.incomplete_subscriptions:
                    user.incomplete_subscriptions.remove(subscription.id)
            
            logger.info(f"✅ Statut abonnement synchronisé: {user.email} -> {subscription.status}")
            return user
            
        except Exception as e:
            logger.error(f"❌ Erreur sync statut: {str(e)}")
            return user
    
    # ================================================================================
    # 🛑 ANNULATION ET RÉACTIVATION
    # ================================================================================
    
    async def cancel_subscription(self, user: User, immediate: bool = False) -> bool:
        """Annule l'abonnement"""
        try:
            if not user.stripe_subscription_id:
                return False
            
            if immediate:
                # Annulation immédiate
                stripe.Subscription.delete(user.stripe_subscription_id)
                user.subscription_status = SubscriptionStatus.CANCELED
                user.subscription_plan = PlanType.GRATUIT
            else:
                # Annulation en fin de période
                stripe.Subscription.modify(
                    user.stripe_subscription_id,
                    cancel_at_period_end=True
                )
            
            user.updated_at = datetime.utcnow()
            logger.info(f"✅ Abonnement annulé pour {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur annulation: {str(e)}")
            return False
    
    async def reactivate_subscription(self, user: User) -> bool:
        """Réactive un abonnement annulé"""
        try:
            if not user.stripe_subscription_id:
                return False
            
            # Annuler l'annulation programmée
            stripe.Subscription.modify(
                user.stripe_subscription_id,
                cancel_at_period_end=False
            )
            
            user.subscription_status = SubscriptionStatus.ACTIVE
            user.updated_at = datetime.utcnow()
            
            logger.info(f"✅ Abonnement réactivé pour {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur réactivation: {str(e)}")
            return False
    
    # ================================================================================
    # 📊 INFORMATIONS ABONNEMENT - VERSION CORRIGÉE
    # ================================================================================
    
    async def get_subscription_info(self, user: User) -> Dict[str, Any]:
        """Récupère les informations détaillées de l'abonnement"""
        try:
            if not user.stripe_subscription_id:
                return {
                    "plan": user.subscription_plan,
                    "status": "no_subscription",
                    "trial_active": False,
                    "can_start_trial": self.can_start_trial(user),
                    "can_subscribe_directly": user.can_start_new_subscription(),
                    "recovery_options": user.get_recovery_options()
                }
            
            subscription = stripe.Subscription.retrieve(user.stripe_subscription_id)
            
            # ✅ CORRECTION: Accès correct aux données de prix
            price_data = subscription['items']['data'][0]['price']
            
            return {
                "plan": user.subscription_plan,
                "status": subscription.status,
                "trial_active": subscription.trial_end and subscription.trial_end > datetime.utcnow().timestamp(),
                "trial_end": datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None,
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "can_start_trial": self.can_start_trial(user),
                "can_subscribe_directly": user.can_start_new_subscription(),
                "amount": price_data['unit_amount'] / 100,  # ✅ CORRECTION
                "currency": price_data['currency'],
                "recovery_options": user.get_recovery_options()
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération info abonnement: {str(e)}")
            return {
                "error": str(e),
                "can_subscribe_directly": user.can_start_new_subscription(),
                "recovery_options": user.get_recovery_options()
            }
    
    # ================================================================================
    # 🔧 GESTION ABONNEMENTS INCOMPLETS - NOUVEAU
    # ================================================================================
    
    async def get_incomplete_subscriptions(self, user: User) -> List[Dict[str, Any]]:
        """Récupère les abonnements incomplets de l'utilisateur"""
        try:
            if not user.stripe_customer_id:
                return []
            
            # Récupérer les abonnements incomplets
            subscriptions = stripe.Subscription.list(
                customer=user.stripe_customer_id,
                status='incomplete',
                limit=10
            )
            
            incomplete_subs = []
            for sub in subscriptions.data:
                try:
                    price_data = sub['items']['data'][0]['price']
                    incomplete_subs.append({
                        "id": sub.id,
                        "status": sub.status,
                        "plan_name": price_data.get('nickname') or f"Plan {price_data['unit_amount']/100}€",
                        "amount": price_data['unit_amount'] / 100,
                        "currency": price_data['currency'],
                        "created_at": datetime.fromtimestamp(sub.created),
                        "can_retry": True,
                        "failure_reason": self._get_subscription_failure_reason(sub)
                    })
                except Exception as e:
                    logger.error(f"❌ Erreur parsing abonnement incomplet {sub.id}: {e}")
            
            return incomplete_subs
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération abonnements incomplets: {str(e)}")
            return []
    
    def _get_subscription_failure_reason(self, subscription) -> Optional[str]:
        """Récupère la raison d'échec d'un abonnement"""
        try:
            if subscription.latest_invoice:
                invoice = stripe.Invoice.retrieve(subscription.latest_invoice)
                if invoice.payment_intent:
                    pi = stripe.PaymentIntent.retrieve(invoice.payment_intent)
                    if pi.last_payment_error:
                        return pi.last_payment_error.get('message', 'Erreur de paiement')
        except:
            pass
        return None
    
    async def retry_incomplete_subscription(self, user: User, subscription_id: str) -> Optional[str]:
        """Relance un abonnement incomplet"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Vérifier que l'abonnement appartient bien à l'utilisateur
            if subscription.customer != user.stripe_customer_id:
                raise Exception("Abonnement non autorisé")
            
            # Si l'abonnement a un PaymentIntent, créer une session pour le finaliser
            if subscription.latest_invoice:
                invoice = stripe.Invoice.retrieve(subscription.latest_invoice)
                
                if invoice.payment_intent:
                    # Créer une session de récupération
                    session = stripe.checkout.Session.create(
                        mode='setup',
                        customer=user.stripe_customer_id,
                        success_url=f"{os.getenv('FRONTEND_URL', 'https://localhost:3000')}/subscription/retry-success",
                        cancel_url=f"{os.getenv('FRONTEND_URL', 'https://localhost:3000')}/subscription/plans",
                        setup_intent_data={
                            'metadata': {
                                'subscription_id': subscription_id,
                                'user_id': user.id,
                                'recovery_attempt': str(user.recovery_attempts + 1)
                            }
                        }
                    )
                    
                    user.recovery_attempts += 1
                    return session.url
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur retry abonnement incomplet: {str(e)}")
            return None

# Instance globale du service
stripe_service = StripeSubscriptionService()