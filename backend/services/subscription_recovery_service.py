# ================================================================================
# ECOMSIMPLY - SERVICE RECOVERY D'ABONNEMENTS - NOUVEAU
# ================================================================================

import stripe
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from ..models.subscription import (
    User, PaymentAttempt, SubscriptionStatus, PlanType,
    RecoveryRequest, IncompleteSubscriptionInfo
)
from .stripe_service import stripe_service

logger = logging.getLogger(__name__)

class SubscriptionRecoveryService:
    """Service pour gérer la récupération d'abonnements échoués"""
    
    def __init__(self):
        self.frontend_url = os.getenv('FRONTEND_URL', 'https://localhost:3000')
    
    # ================================================================================
    # 🔍 DÉTECTION ABONNEMENTS INCOMPLETS
    # ================================================================================
    
    async def check_incomplete_subscriptions(self, user: User) -> List[IncompleteSubscriptionInfo]:
        """Vérifie les abonnements incomplets sur Stripe"""
        try:
            if not user.stripe_customer_id:
                return []
            
            # Récupérer les abonnements incomplets et expirés
            incomplete_subs = []
            
            # Abonnements incomplets
            subs = stripe.Subscription.list(
                customer=user.stripe_customer_id,
                status='incomplete',
                limit=10
            )
            
            for sub in subs.data:
                incomplete_subs.append(self._format_incomplete_subscription(sub, 'incomplete'))
            
            # Abonnements expirés incomplets
            expired_subs = stripe.Subscription.list(
                customer=user.stripe_customer_id,
                status='incomplete_expired',
                limit=5
            )
            
            for sub in expired_subs.data:
                # Vérifier si pas trop ancien (moins de 30 jours)
                created = datetime.fromtimestamp(sub.created)
                if datetime.utcnow() - created < timedelta(days=30):
                    incomplete_subs.append(self._format_incomplete_subscription(sub, 'incomplete_expired'))
            
            return incomplete_subs
            
        except Exception as e:
            logger.error(f"❌ Erreur check incomplete subscriptions: {str(e)}")
            return []
    
    def _format_incomplete_subscription(self, subscription, status_override=None) -> IncompleteSubscriptionInfo:
        """Formate les données d'abonnement incomplet"""
        try:
            price_data = subscription['items']['data'][0]['price']
            plan_name = price_data.get('nickname', f"Plan {price_data['unit_amount']/100}€")
            
            failure_reason = self._get_failure_reason(subscription)
            can_retry = status_override != 'incomplete_expired' and failure_reason != 'card_declined'
            
            return IncompleteSubscriptionInfo(
                id=subscription.id,
                status=status_override or subscription.status,
                plan_name=plan_name,
                amount=price_data['unit_amount'] / 100,
                currency=price_data['currency'],
                created_at=datetime.fromtimestamp(subscription.created),
                failure_reason=failure_reason,
                can_retry=can_retry
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur format abonnement incomplet: {str(e)}")
            return IncompleteSubscriptionInfo(
                id=subscription.id,
                status="unknown",
                plan_name="Plan inconnu",
                amount=0,
                currency="eur",
                created_at=datetime.utcnow(),
                can_retry=False
            )
    
    def _get_failure_reason(self, subscription) -> Optional[str]:
        """Récupère la raison d'échec détaillée"""
        try:
            if subscription.latest_invoice:
                invoice = stripe.Invoice.retrieve(subscription.latest_invoice)
                if invoice.payment_intent:
                    pi = stripe.PaymentIntent.retrieve(invoice.payment_intent)
                    if pi.last_payment_error:
                        error_code = pi.last_payment_error.get('code', '')
                        error_message = pi.last_payment_error.get('message', '')
                        
                        # Messages personnalisés selon le code d'erreur
                        if error_code == 'card_declined':
                            return "Carte refusée"
                        elif error_code == 'insufficient_funds':
                            return "Fonds insuffisants"
                        elif error_code == 'expired_card':
                            return "Carte expirée"
                        elif error_code == 'authentication_required':
                            return "Authentification requise"
                        else:
                            return error_message or "Erreur de paiement"
        except Exception as e:
            logger.error(f"❌ Erreur récupération raison échec: {str(e)}")
        
        return "Erreur inconnue"
    
    # ================================================================================
    # 🔄 RETRY ET RÉCUPÉRATION
    # ================================================================================
    
    async def retry_incomplete_subscription(self, user: User, recovery_request: RecoveryRequest) -> Dict[str, Any]:
        """Relance un abonnement incomplet"""
        try:
            if not recovery_request.subscription_id:
                return {
                    "success": False,
                    "message": "ID abonnement requis"
                }
            
            subscription = stripe.Subscription.retrieve(recovery_request.subscription_id)
            
            # Vérifier propriété
            if subscription.customer != user.stripe_customer_id:
                return {
                    "success": False,
                    "message": "Abonnement non autorisé"
                }
            
            # Créer session de récupération selon le type
            if recovery_request.recovery_type == "retry":
                return await self._create_retry_session(user, subscription, recovery_request)
            elif recovery_request.recovery_type == "update_payment":
                return await self._create_update_payment_session(user, subscription)
            else:
                return {
                    "success": False,
                    "message": "Type de récupération non supporté"
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur retry abonnement: {str(e)}")
            return {
                "success": False,
                "message": f"Erreur technique: {str(e)}"
            }
    
    async def _create_retry_session(self, user: User, subscription, recovery_request: RecoveryRequest) -> Dict[str, Any]:
        """Crée une session de retry pour finaliser l'abonnement"""
        try:
            if subscription.latest_invoice:
                invoice = stripe.Invoice.retrieve(subscription.latest_invoice)
                
                # Si l'invoice est payable, créer une session checkout
                if invoice.status in ['open', 'draft'] and invoice.payment_intent:
                    
                    # Créer session Checkout pour finaliser le paiement
                    session = stripe.checkout.Session.create(
                        customer=user.stripe_customer_id,
                        payment_method_types=['card'],
                        line_items=[{
                            'price': subscription.items.data[0].price.id,
                            'quantity': 1,
                        }],
                        mode='subscription',
                        success_url=f"{self.frontend_url}/subscription/retry-success?session_id={{CHECKOUT_SESSION_ID}}",
                        cancel_url=f"{self.frontend_url}/subscription/plans",
                        subscription_data={
                            'metadata': {
                                'user_id': user.id,
                                'recovery_attempt': str(user.recovery_attempts + 1),
                                'original_subscription': subscription.id
                            }
                        },
                        metadata={
                            'recovery_type': 'retry',
                            'original_subscription': subscription.id,
                            'user_id': user.id
                        }
                    )
                    
                    # Mettre à jour utilisateur
                    user.recovery_attempts += 1
                    user.last_subscription_attempt = datetime.utcnow()
                    
                    return {
                        "success": True,
                        "retry_url": session.url,
                        "session_id": session.id,
                        "message": "Session de récupération créée"
                    }
            
            return {
                "success": False,
                "message": "Impossible de créer une session de récupération"
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur création session retry: {str(e)}")
            return {
                "success": False,
                "message": "Erreur technique lors de la création de la session"
            }
    
    async def _create_update_payment_session(self, user: User, subscription) -> Dict[str, Any]:
        """Crée une session pour mettre à jour le mode de paiement"""
        try:
            session = stripe.checkout.Session.create(
                customer=user.stripe_customer_id,
                mode='setup',
                success_url=f"{self.frontend_url}/subscription/payment-updated?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{self.frontend_url}/subscription/plans",
                setup_intent_data={
                    'metadata': {
                        'user_id': user.id,
                        'subscription_id': subscription.id,
                        'recovery_type': 'update_payment'
                    }
                }
            )
            
            return {
                "success": True,
                "update_url": session.url,
                "session_id": session.id,
                "message": "Session de mise à jour de paiement créée"
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur session update payment: {str(e)}")
            return {
                "success": False,
                "message": "Erreur création session mise à jour paiement"
            }
    
    # ================================================================================
    # 🆕 NOUVELLE SOUSCRIPTION POST-ÉCHEC
    # ================================================================================
    
    async def create_new_subscription_after_failure(
        self, 
        user: User, 
        plan_type: PlanType,
        price_id: str
    ) -> Dict[str, Any]:
        """Crée un nouvel abonnement après un échec précédent"""
        try:
            # Nettoyer les abonnements incomplets anciens
            await self._cleanup_old_incomplete_subscriptions(user)
            
            # Créer nouvelle tentative via le service principal
            from ..models.subscription import CreateSubscriptionRequest
            
            request = CreateSubscriptionRequest(
                plan_type=plan_type,
                price_id=price_id,
                success_url=f"{self.frontend_url}/subscription/success",
                cancel_url=f"{self.frontend_url}/subscription/cancel",
                with_trial=user.can_start_trial()  # Respect des règles d'essai
            )
            
            response = await stripe_service.create_subscription_checkout(user, request)
            
            if response.status == "checkout_created":
                return {
                    "success": True,
                    "checkout_url": response.checkout_url,
                    "message": "Nouvelle tentative d'abonnement créée"
                }
            else:
                return {
                    "success": False,
                    "message": response.message
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur nouvelle souscription post-échec: {str(e)}")
            return {
                "success": False,
                "message": f"Erreur technique: {str(e)}"
            }
    
    async def _cleanup_old_incomplete_subscriptions(self, user: User):
        """Nettoie les anciens abonnements incomplets"""
        try:
            if not user.stripe_customer_id:
                return
            
            # Récupérer les abonnements incomplets anciens (>7 jours)
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            subs = stripe.Subscription.list(
                customer=user.stripe_customer_id,
                status='incomplete',
                limit=20
            )
            
            for sub in subs.data:
                created = datetime.fromtimestamp(sub.created)
                if created < cutoff_date:
                    try:
                        # Annuler l'ancien abonnement incomplet
                        stripe.Subscription.delete(sub.id)
                        logger.info(f"✅ Abonnement incomplet nettoyé: {sub.id}")
                    except Exception as e:
                        logger.error(f"❌ Erreur nettoyage abonnement {sub.id}: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Erreur cleanup abonnements incomplets: {str(e)}")
    
    # ================================================================================
    # 📊 STATISTIQUES ET MONITORING
    # ================================================================================
    
    async def get_recovery_statistics(self, user: User) -> Dict[str, Any]:
        """Récupère les statistiques de récupération pour l'utilisateur"""
        try:
            incomplete_subs = await self.check_incomplete_subscriptions(user)
            
            total_attempts = len(user.payment_attempts)
            failed_attempts = len([a for a in user.payment_attempts if a.status in ["failed", "abandoned"]])
            
            return {
                "total_payment_attempts": total_attempts,
                "failed_payment_attempts": failed_attempts,
                "recovery_attempts": user.recovery_attempts,
                "incomplete_subscriptions_count": len(incomplete_subs),
                "can_retry_subscription": user.can_retry_subscription,
                "last_attempt_date": user.last_subscription_attempt,
                "incomplete_subscriptions": incomplete_subs
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération stats: {str(e)}")
            return {}

# Instance globale du service
recovery_service = SubscriptionRecoveryService()