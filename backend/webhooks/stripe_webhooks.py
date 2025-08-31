# ================================================================================
# ECOMSIMPLY - WEBHOOKS STRIPE SÉCURISÉS AVEC ANTI-REPLAY
# ================================================================================

import stripe
import logging
from fastapi import HTTPException, Request
from typing import Dict, Any
from datetime import datetime, timedelta
from ..models.subscription import (
    User, SubscriptionRecord, PaymentHistory,
    SubscriptionStatus, PlanType, PLAN_CONFIG
)
from ..services.stripe_service import stripe_service
from ..services.trial_eligibility_service import trial_eligibility_service
import hashlib

logger = logging.getLogger(__name__)

class StripeWebhookHandler:
    """Gestionnaire sécurisé des webhooks Stripe avec anti-replay et signature raw"""
    
    def __init__(self):
        self.webhook_secret = stripe_service.webhook_secret
        self.replay_window_seconds = 300  # 5 minutes window pour anti-replay
    
    # ================================================================================
    # 🔐 VÉRIFICATION SIGNATURE AVEC RAW BODY + ANTI-REPLAY
    # ================================================================================
    
    async def verify_webhook_signature(self, request: Request, db) -> Dict[str, Any]:
        """Vérifie la signature du webhook Stripe avec raw body et anti-replay"""
        try:
            # 1. Récupérer le RAW body (crucial pour signature Stripe)
            payload = await request.body()
            sig_header = request.headers.get('stripe-signature')
            
            if not sig_header:
                logger.error("❌ Webhook signature header missing")
                raise HTTPException(status_code=400, detail="Missing Stripe signature")
            
            # 2. Vérifier la signature Stripe avec le raw payload
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, self.webhook_secret
                )
            except stripe.error.SignatureVerificationError as e:
                logger.error(f"❌ Invalid webhook signature: {str(e)}")
                raise HTTPException(status_code=400, detail="Invalid signature")
            except ValueError as e:
                logger.error(f"❌ Invalid webhook payload: {str(e)}")
                raise HTTPException(status_code=400, detail="Invalid payload")
            
            # 3. Vérification anti-replay
            event_id = event['id']
            event_created = event.get('created', 0)
            
            # Vérifier si l'événement n'est pas trop ancien
            current_timestamp = datetime.utcnow().timestamp()
            if current_timestamp - event_created > self.replay_window_seconds:
                logger.warning(f"⚠️ Webhook event too old: {event_id}")
                raise HTTPException(status_code=400, detail="Event too old")
            
            # 4. Vérifier si l'événement n'a pas déjà été traité (anti-replay)
            is_duplicate = await self._check_and_record_event(event_id, event['type'], event_created, db)
            
            if is_duplicate:
                logger.warning(f"🔄 Duplicate webhook event blocked: {event_id}")
                # Retourner succès pour éviter les retry Stripe, mais ne pas traiter
                return {
                    "event": event,
                    "duplicate": True,
                    "message": "Duplicate event ignored"
                }
            
            # 5. Log sécurisé (sans PII)
            event_type = event['type']
            event_hash = self._hash_event_id(event_id)
            
            logger.info(
                f"📨 Valid webhook received: type={event_type}, "
                f"id_hash={event_hash[:12]}..., created={event_created}"
            )
            
            return {
                "event": event,
                "duplicate": False,
                "message": "Valid webhook event"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Webhook verification error: {str(e)}")
            raise HTTPException(status_code=400, detail="Webhook verification failed")
    
    async def _check_and_record_event(self, event_id: str, event_type: str, event_created: int, db) -> bool:
        """Vérifie et enregistre l'événement pour anti-replay"""
        try:
            if not db:
                logger.warning("⚠️ No database connection for anti-replay check")
                return False
            
            # Vérifier si l'événement existe déjà
            existing_event = await db.webhook_events.find_one({"event_id": event_id})
            
            if existing_event:
                # Événement déjà traité
                return True
            
            # Enregistrer le nouvel événement
            await db.webhook_events.insert_one({
                "event_id": event_id,
                "event_type": event_type,
                "event_created": datetime.fromtimestamp(event_created),
                "processed_at": datetime.utcnow(),
                "event_id_hash": self._hash_event_id(event_id)  # Pour logs sécurisés
            })
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error in anti-replay check: {e}")
            # En cas d'erreur, traiter l'événement (être permissif)
            return False
    
    def _hash_event_id(self, event_id: str) -> str:
        """Hash sécurisé de l'event ID pour les logs"""
        return hashlib.sha256(f"event:{event_id}".encode()).hexdigest()
    
    # ================================================================================
    # 🎯 HANDLERS PAR TYPE D'ÉVÉNEMENT (VERSIONS SÉCURISÉES)
    # ================================================================================
    
    async def handle_checkout_session_completed(self, event_data: Dict[str, Any], db) -> bool:
        """Gère la finalisation d'une session de checkout - VERSION SÉCURISÉE"""
        try:
            session = event_data['object']
            user_id = session['metadata'].get('user_id')
            plan_type = session['metadata'].get('plan_type')
            
            if not user_id or not plan_type:
                logger.warning("❌ Missing metadata in checkout session")
                return False
            
            # Récupérer l'utilisateur
            user = await db.users.find_one({"id": user_id})
            if not user:
                logger.error(f"❌ User not found: {user_id[:8]}...")
                return False
            
            user_obj = User(**user)
            
            # Mettre à jour les informations utilisateur
            user_updates = {
                "stripe_customer_id": session['customer'],
                "subscription_plan": plan_type,
                "updated_at": datetime.utcnow()
            }
            
            # Récupérer l'abonnement créé
            if session['subscription']:
                subscription = stripe.Subscription.retrieve(session['subscription'])
                
                user_updates.update({
                    "stripe_subscription_id": subscription.id,
                    "subscription_status": subscription.status
                })
                
                # Gérer l'essai gratuit ET enregistrer son utilisation
                if subscription.trial_end:
                    trial_end_date = datetime.fromtimestamp(subscription.trial_end)
                    
                    user_updates.update({
                        "has_used_trial": True,
                        "trial_used_at": datetime.utcnow(),  # NOUVEAU: timestamp exact
                        "trial_start_date": datetime.fromtimestamp(subscription.trial_start),
                        "trial_end_date": trial_end_date
                    })
                    
                    # Enregistrer l'utilisation de l'essai avec le service dédié
                    payment_fingerprint = session.get('payment_intent', {}).get('payment_method', {}).get('fingerprint') if session.get('payment_intent') else None
                    
                    await trial_eligibility_service.record_trial_usage(
                        user=user_obj,
                        payment_fingerprint=payment_fingerprint,
                        client_ip=None,  # Non disponible dans webhook
                        plan_type=PlanType(plan_type),
                        db=db
                    )
                    
                    # Log sécurisé
                    user_hash = trial_eligibility_service._hash_user_id(user_id)
                    logger.info(f"🎁 Trial activated and recorded: user_hash={user_hash[:8]}..., end_date={trial_end_date}")
                
                # Créer l'enregistrement d'abonnement
                subscription_record = SubscriptionRecord(
                    user_id=user_id,
                    stripe_subscription_id=subscription.id,
                    stripe_customer_id=session['customer'],
                    stripe_price_id=subscription['items']['data'][0]['price']['id'],
                    plan_type=PlanType(plan_type),
                    status=SubscriptionStatus(subscription.status),
                    current_period_start=datetime.fromtimestamp(subscription.current_period_start),
                    current_period_end=datetime.fromtimestamp(subscription.current_period_end),
                    trial_start=datetime.fromtimestamp(subscription.trial_start) if subscription.trial_start else None,
                    trial_end=datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None,
                    amount=subscription['items']['data'][0]['price']['unit_amount'] / 100,
                    currency=subscription['items']['data'][0]['price']['currency'],
                    webhook_events=[{
                        "type": "checkout.session.completed",
                        "timestamp": datetime.utcnow(),
                        "event_id_hash": self._hash_event_id(event_data.get('id', 'unknown'))
                    }]
                )
                
                await db.subscription_records.insert_one(subscription_record.dict())
            
            # Mettre à jour l'utilisateur
            await db.users.update_one(
                {"id": user_id},
                {"$set": user_updates}
            )
            
            # Log sécurisé (sans email)
            user_hash = hashlib.sha256(f"user:{user_id}".encode()).hexdigest()
            logger.info(f"✅ Checkout completed: user_hash={user_hash[:8]}..., plan={plan_type}")
            
            # Métrique
            self._record_metric("checkout_completed", {"plan_type": plan_type})
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in checkout completed handler: {str(e)}")
            return False
    
    async def handle_invoice_payment_succeeded(self, event_data: Dict[str, Any], db) -> bool:
        """Gère les paiements réussis - VERSION SÉCURISÉE"""
        try:
            invoice = event_data['object']
            customer_id = invoice['customer']
            
            # Trouver l'utilisateur
            user = await db.users.find_one({"stripe_customer_id": customer_id})
            if not user:
                logger.warning(f"❌ User not found for customer: {customer_id[:8]}...")
                return False
            
            # Enregistrer le paiement (logs sécurisés)
            payment_record = PaymentHistory(
                user_id=user['id'],
                stripe_invoice_id=invoice['id'],
                stripe_payment_intent_id=invoice['payment_intent'],
                amount=invoice['amount_paid'] / 100,
                currency=invoice['currency'],
                status='succeeded',
                plan_type=user['subscription_plan'],
                billing_reason=invoice['billing_reason'],
                paid_at=datetime.fromtimestamp(invoice['created'])
            )
            
            await db.payment_history.insert_one(payment_record.dict())
            
            # Mettre à jour l'utilisateur
            await db.users.update_one(
                {"id": user['id']},
                {
                    "$set": {
                        "last_payment_date": datetime.utcnow(),
                        "payment_failed_count": 0,
                        "payment_failed_date": None,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Log sécurisé
            user_hash = hashlib.sha256(f"user:{user['id']}".encode()).hexdigest()
            amount = invoice['amount_paid'] / 100
            logger.info(f"✅ Payment succeeded: user_hash={user_hash[:8]}..., amount={amount}€")
            
            # Métrique
            self._record_metric("payment_succeeded", {"amount": amount, "currency": invoice['currency']})
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in payment succeeded handler: {str(e)}")
            return False
    
    async def handle_invoice_payment_failed(self, event_data: Dict[str, Any], db) -> bool:
        """Gère les échecs de paiement - VERSION SÉCURISÉE"""
        try:
            invoice = event_data['object']
            customer_id = invoice['customer']
            
            # Trouver l'utilisateur
            user = await db.users.find_one({"stripe_customer_id": customer_id})
            if not user:
                logger.warning(f"❌ User not found for customer: {customer_id[:8]}...")
                return False
            
            # Enregistrer l'échec de paiement (sans détails sensibles)
            payment_record = PaymentHistory(
                user_id=user['id'],
                stripe_invoice_id=invoice['id'],
                amount=invoice['amount_due'] / 100,
                currency=invoice['currency'],
                status='failed',
                plan_type=user['subscription_plan'],
                billing_reason=invoice['billing_reason'],
                failure_reason="payment_failed"  # Générique pour sécurité
            )
            
            await db.payment_history.insert_one(payment_record.dict())
            
            # Mettre à jour l'utilisateur
            payment_failed_count = user.get('payment_failed_count', 0) + 1
            
            updates = {
                "payment_failed_date": datetime.utcnow(),
                "payment_failed_count": payment_failed_count,
                "updated_at": datetime.utcnow()
            }
            
            # Si trop d'échecs, désactiver l'accès
            if payment_failed_count >= 3:
                updates["subscription_status"] = SubscriptionStatus.UNPAID
                logger.warning(f"⚠️ Access disabled after {payment_failed_count} failures: user_hash={user['id'][:8]}...")
            
            await db.users.update_one(
                {"id": user['id']},
                {"$set": updates}
            )
            
            # Log sécurisé
            user_hash = hashlib.sha256(f"user:{user['id']}".encode()).hexdigest()
            logger.info(f"❌ Payment failed: user_hash={user_hash[:8]}..., attempt={payment_failed_count}")
            
            # Métrique
            self._record_metric("payment_failed", {"attempt": payment_failed_count})
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in payment failed handler: {str(e)}")
            return False
    
    async def handle_subscription_updated(self, event_data: Dict[str, Any], db) -> bool:
        """Gère les mises à jour d'abonnement - VERSION SÉCURISÉE"""
        try:
            subscription = event_data['object']
            customer_id = subscription['customer']
            
            # Trouver l'utilisateur
            user = await db.users.find_one({"stripe_customer_id": customer_id})
            if not user:
                logger.warning(f"❌ User not found for customer: {customer_id[:8]}...")
                return False
            
            # Déterminer le type de plan
            price_id = subscription['items']['data'][0]['price']['id']
            plan_type = PlanType.PRO  # Default
            
            for plan, config in PLAN_CONFIG.items():
                if config.get('stripe_price_id') == price_id:
                    plan_type = plan
                    break
            
            # Mettre à jour l'utilisateur
            updates = {
                "subscription_plan": plan_type,
                "subscription_status": subscription['status'],
                "stripe_subscription_id": subscription['id'],
                "updated_at": datetime.utcnow()
            }
            
            # Gérer les changements d'état
            if subscription['status'] == 'canceled':
                updates.update({
                    "subscription_plan": PlanType.GRATUIT,
                    "stripe_subscription_id": None
                })
            
            await db.users.update_one(
                {"id": user['id']},
                {"$set": updates}
            )
            
            # Mettre à jour l'enregistrement d'abonnement
            await db.subscription_records.update_one(
                {"stripe_subscription_id": subscription['id']},
                {
                    "$set": {
                        "status": subscription['status'],
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {
                        "webhook_events": {
                            "type": "customer.subscription.updated",
                            "timestamp": datetime.utcnow(),
                            "event_id_hash": self._hash_event_id(event_data.get('id', 'unknown'))
                        }
                    }
                }
            )
            
            # Log sécurisé
            user_hash = hashlib.sha256(f"user:{user['id']}".encode()).hexdigest()
            logger.info(f"✅ Subscription updated: user_hash={user_hash[:8]}..., status={subscription['status']}")
            
            # Métrique
            self._record_metric("subscription_updated", {"status": subscription['status']})
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in subscription updated handler: {str(e)}")
            return False
    
    async def handle_subscription_deleted(self, event_data: Dict[str, Any], db) -> bool:
        """Gère la suppression d'abonnement - VERSION SÉCURISÉE"""
        try:
            subscription = event_data['object']
            customer_id = subscription['customer']
            
            # Trouver l'utilisateur
            user = await db.users.find_one({"stripe_customer_id": customer_id})
            if not user:
                logger.warning(f"❌ User not found for customer: {customer_id[:8]}...")
                return False
            
            # Révoquer l'accès premium
            await db.users.update_one(
                {"id": user['id']},
                {
                    "$set": {
                        "subscription_plan": PlanType.GRATUIT,
                        "subscription_status": SubscriptionStatus.CANCELED,
                        "stripe_subscription_id": None,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Marquer l'enregistrement d'abonnement comme terminé
            await db.subscription_records.update_one(
                {"stripe_subscription_id": subscription['id']},
                {
                    "$set": {
                        "status": SubscriptionStatus.CANCELED,
                        "ended_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Log sécurisé
            user_hash = hashlib.sha256(f"user:{user['id']}".encode()).hexdigest()
            logger.info(f"✅ Subscription deleted: user_hash={user_hash[:8]}...")
            
            # Métrique
            self._record_metric("subscription_deleted", {})
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in subscription deleted handler: {str(e)}")
            return False
    
    # ================================================================================
    # 📊 MÉTRIQUES ET MONITORING
    # ================================================================================
    
    def _record_metric(self, metric_name: str, data: Dict[str, Any] = None):
        """Enregistre une métrique (sans PII)"""
        try:
            # Ici vous pourriez intégrer avec votre système de métriques
            # (Prometheus, CloudWatch, DataDog, etc.)
            logger.info(f"📊 Metric: {metric_name} - {data or {}}")
        except Exception as e:
            logger.error(f"❌ Error recording metric {metric_name}: {e}")
    
    # ================================================================================
    # 🎯 ROUTER PRINCIPAL DES WEBHOOKS SÉCURISÉ
    # ================================================================================
    
    async def handle_webhook(self, event: Dict[str, Any], db) -> bool:
        """Route les événements webhook vers les bons handlers - VERSION SÉCURISÉE"""
        
        # Vérifier si c'est un événement dupliqué
        if event.get("duplicate", False):
            return True  # Succès silencieux pour les doublons
        
        event_type = event['type']
        event_data = event['data']
        event_id = event.get('id', 'unknown')
        
        handlers = {
            'checkout.session.completed': self.handle_checkout_session_completed,
            'invoice.payment_succeeded': self.handle_invoice_payment_succeeded,
            'invoice.payment_failed': self.handle_invoice_payment_failed,
            'customer.subscription.updated': self.handle_subscription_updated,
            'customer.subscription.deleted': self.handle_subscription_deleted,
        }
        
        handler = handlers.get(event_type)
        if handler:
            try:
                result = await handler(event_data, db)
                
                # Log et métrique
                event_hash = self._hash_event_id(event_id)
                logger.info(f"✅ Webhook {event_type} processed: id_hash={event_hash[:8]}..., result={result}")
                self._record_metric("webhook_processed", {"event_type": event_type, "success": result})
                
                return result
            except Exception as e:
                event_hash = self._hash_event_id(event_id)
                logger.error(f"❌ Error processing webhook {event_type}: id_hash={event_hash[:8]}..., error={str(e)}")
                self._record_metric("webhook_error", {"event_type": event_type})
                return False
        else:
            logger.info(f"ℹ️ Webhook {event_type} ignored (no handler)")
            self._record_metric("webhook_ignored", {"event_type": event_type})
            return True
    
    # ================================================================================
    # 🧹 MAINTENANCE DES ÉVÉNEMENTS
    # ================================================================================
    
    async def cleanup_old_webhook_events(self, db, retention_days: int = 30) -> int:
        """Nettoie les anciens événements webhook pour économiser l'espace"""
        try:
            if not db:
                return 0
            
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            result = await db.webhook_events.delete_many({
                "processed_at": {"$lt": cutoff_date}
            })
            
            deleted_count = result.deleted_count
            logger.info(f"🧹 Cleaned up {deleted_count} old webhook events (>{retention_days} days)")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up webhook events: {e}")
            return 0

# Instance globale du handler sécurisé
webhook_handler = StripeWebhookHandler()