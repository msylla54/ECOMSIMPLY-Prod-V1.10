# ================================================================================
# ECOMSIMPLY - ROUTES API COMPLÈTES POUR GESTION ABONNEMENTS - VERSION ROBUSTE
# ================================================================================

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any, List
from datetime import datetime
from ..models.subscription import (
    User, CreateSubscriptionRequest, SubscriptionResponse, 
    UserSubscriptionStatus, PlanType, PLAN_CONFIG, RecoveryRequest
)
from ..services.stripe_service import stripe_service
from ..services.subscription_recovery_service import recovery_service
from ..services.trial_eligibility_service import trial_eligibility_service
from ..webhooks.stripe_webhooks import webhook_handler
# ✅ CORRECTION: Import temporaire direct pour get_current_user 
# Note: get_current_user sera déplacé dans un module auth séparé plus tard
import logging

# Import temporaire direct depuis server.py pour résoudre l'erreur d'import
try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from server import get_current_user
except ImportError:
    # Fallback si l'import échoue
    def get_current_user():
        """Placeholder temporaire - sera remplacé par l'import correct"""
        raise HTTPException(status_code=500, detail="Authentication service unavailable")

logger = logging.getLogger(__name__)

subscription_router = APIRouter(prefix="/subscription", tags=["subscriptions"])

# ✅ CORRECTION: Fonction pour injection DB (à adapter selon votre setup)
async def get_database():
    """Retourne l'instance de base de données - À adapter selon votre configuration"""
    # Cette fonction doit retourner votre instance MongoDB
    # Exemple : return your_db_instance
    pass

@subscription_router.get("/trial-eligibility", response_model=Dict[str, Any])
async def check_trial_eligibility(
    plan: str,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db = Depends(get_database)
):
    """Vérifie l'éligibilité à l'essai gratuit - SERVER-SIDE SOURCE OF TRUTH"""
    try:
        # Validation du plan
        try:
            plan_type = PlanType(plan.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Plan invalide")
        
        if plan_type not in [PlanType.PRO, PlanType.PREMIUM]:
            raise HTTPException(status_code=400, detail="Essai non disponible pour ce plan")
        
        # Récupérer l'IP client pour la vérification
        client_ip = None
        if request:
            client_ip = request.client.host
            # Vérifier les headers proxy pour IP réelle
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                client_ip = forwarded_for.split(',')[0].strip()
        
        # Vérification complète d'éligibilité
        eligibility_result = await trial_eligibility_service.check_trial_eligibility(
            user=current_user,
            plan_type=plan_type,
            client_ip=client_ip,
            db=db
        )
        
        # Format de réponse standardisé
        response = {
            "eligible": eligibility_result["eligible"],
            "reason": eligibility_result["reason"],
            "plan_type": plan,
            "timestamp": eligibility_result["timestamp"],
            "message": _get_eligibility_message(eligibility_result)
        }
        
        # Log sécurisé (sans PII)
        user_hash = trial_eligibility_service._hash_user_id(current_user.id)
        logger.info(
            f"🔍 Trial eligibility check: user_hash={user_hash[:8]}..., "
            f"plan={plan}, eligible={eligibility_result['eligible']}, "
            f"reason={eligibility_result['reason']}"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error checking trial eligibility: {str(e)}")
        # Retourner non-éligible en cas d'erreur pour sécurité
        return {
            "eligible": False,
            "reason": "eligibility_check_failed",
            "plan_type": plan,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Vérification d'éligibilité échouée - Veuillez réessayer"
        }

def _get_eligibility_message(eligibility_result: Dict[str, Any]) -> str:
    """Génère un message d'éligibilité convivial"""
    if eligibility_result["eligible"]:
        return "Vous êtes éligible à l'essai gratuit de 7 jours !"
    
    reason = eligibility_result["reason"]
    
    messages = {
        "trial_already_used": "Vous avez déjà utilisé votre essai gratuit. Vous pouvez souscrire directement.",
        "trial_already_used_legacy": "Essai gratuit déjà utilisé. Souscription directe disponible.",
        "payment_fingerprint_already_used": "Ce moyen de paiement a déjà été utilisé pour un essai.",
        "email_already_used_trial": "Cette adresse email a déjà bénéficié d'un essai gratuit.",
        "ip_trial_limit_exceeded": "Limite d'essais atteinte pour cette connexion.",
        "eligibility_check_error": "Erreur lors de la vérification. Veuillez réessayer."
    }
    
    return messages.get(reason, "Essai gratuit non disponible. Souscription directe possible.")

# ================================================================================
# 📋 ENDPOINTS INFORMATIONS ABONNEMENT (EXISTING)
# ================================================================================

@subscription_router.get("/plans", response_model=Dict[str, Any])
async def get_available_plans():
    """Retourne tous les plans disponibles avec leurs détails"""
    try:
        plans_info = {}
        
        for plan_type, config in PLAN_CONFIG.items():
            plans_info[plan_type.value] = {
                "name": config["name"],
                "price": config["price"],
                "currency": config["currency"],
                "features": config["features"],
                "sheets_limit": config["sheets_limit"],
                "recommended": plan_type == PlanType.PRO,  # Pro recommandé
                "stripe_price_id": config.get("stripe_price_id")
            }
        
        return {
            "success": True,
            "plans": plans_info,
            "currency": "eur",
            "trial_days": 7
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération plans: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur récupération des plans")

@subscription_router.get("/status", response_model=UserSubscriptionStatus)
async def get_subscription_status(current_user: User = Depends(get_current_user)):
    """Retourne le statut complet de l'abonnement utilisateur"""
    try:
        # Synchroniser avec Stripe si nécessaire
        if current_user.stripe_subscription_id:
            current_user = await stripe_service.sync_subscription_status(current_user)
        
        # Construire le statut complet
        subscription_info = await stripe_service.get_subscription_info(current_user)
        recovery_options = current_user.get_recovery_options()
        
        status = UserSubscriptionStatus(
            user_id=current_user.id,
            plan_type=current_user.subscription_plan,
            status=current_user.subscription_status,
            
            # Trial info
            can_start_trial=current_user.can_start_trial(),
            has_used_trial=current_user.has_used_trial,
            trial_active=current_user.is_trial_active(),
            trial_end_date=current_user.trial_end_date,
            
            # Usage info
            monthly_limit=current_user.get_monthly_limit(),
            monthly_used=current_user.monthly_sheets_used,
            can_access_features=current_user.can_access_features(),
            
            # Billing info
            next_billing_date=subscription_info.get('current_period_end'),
            amount=subscription_info.get('amount'),
            currency=subscription_info.get('currency', 'eur'),
            
            # ✅ NOUVEAU: Alerts et recovery étendus
            payment_failed=current_user.payment_failed_date is not None,
            requires_action=not current_user.can_access_features(),
            requires_payment_action=current_user.requires_payment_action(),
            has_incomplete_subscriptions=current_user.has_incomplete_subscriptions(),
            can_subscribe_directly=current_user.can_start_new_subscription(),
            recovery_options=recovery_options,
            message=_get_status_message(current_user, subscription_info, recovery_options)
        )
        
        return status
        
    except Exception as e:
        logger.error(f"❌ Erreur statut abonnement: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur récupération du statut")

def _get_status_message(user: User, subscription_info: Dict[str, Any], recovery_options: Dict[str, Any]) -> str:
    """Génère un message de statut personnalisé - VERSION AMÉLIORÉE"""
    if user.is_trial_active():
        days_left = (user.trial_end_date - datetime.utcnow()).days
        return f"Essai gratuit actif - {days_left} jours restants"
    
    if user.requires_payment_action():
        return "Paiement requis - Mettre à jour votre mode de paiement"
    
    if user.has_incomplete_subscriptions():
        return "Abonnement en attente - Finaliser le paiement"
    
    if user.subscription_plan == PlanType.GRATUIT and user.has_used_trial:
        return "Essai expiré - Abonnez-vous pour continuer"
    
    if user.subscription_plan in [PlanType.PRO, PlanType.PREMIUM]:
        if subscription_info.get('cancel_at_period_end'):
            return "Abonnement annulé - Accès jusqu'à la fin de la période"
        return f"Abonnement {user.subscription_plan.value} actif"
    
    return "Plan gratuit actif"

# ================================================================================
# 💳 ENDPOINTS CRÉATION ET GESTION ABONNEMENTS
# ================================================================================

@subscription_router.post("/create", response_model=SubscriptionResponse)
async def create_subscription(
    request: CreateSubscriptionRequest,
    current_user: User = Depends(get_current_user)
):
    """Crée un nouvel abonnement avec redirection Stripe"""
    try:
        # ✅ CORRECTION: Logique plus flexible pour permettre retry
        if current_user.subscription_plan != PlanType.GRATUIT and current_user.is_subscription_active():
            raise HTTPException(
                status_code=400, 
                detail="Vous avez déjà un abonnement actif"
            )
        
        # Vérifier le plan demandé
        if request.plan_type not in [PlanType.PRO, PlanType.PREMIUM]:
            raise HTTPException(
                status_code=400,
                detail="Plan invalide pour abonnement payant"
            )
        
        # Vérifier la Price ID
        plan_config = PLAN_CONFIG.get(request.plan_type)
        if not plan_config or plan_config.get("stripe_price_id") != request.price_id:
            raise HTTPException(
                status_code=400,
                detail="Price ID invalide pour ce plan"
            )
        
        # ✅ CORRECTION: Gérer l'essai gratuit ET permettre abonnement direct
        with_trial = request.with_trial and current_user.can_start_trial()
        
        # Créer la session Checkout
        response = await stripe_service.create_subscription_checkout(
            current_user, request
        )
        
        logger.info(f"✅ Abonnement créé pour {current_user.email}: {request.plan_type}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur création abonnement: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@subscription_router.post("/cancel")
async def cancel_subscription(
    immediate: bool = False,
    current_user: User = Depends(get_current_user)
):
    """Annule l'abonnement utilisateur"""
    try:
        if current_user.subscription_plan == PlanType.GRATUIT:
            raise HTTPException(
                status_code=400,
                detail="Aucun abonnement à annuler"
            )
        
        success = await stripe_service.cancel_subscription(current_user, immediate)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Erreur lors de l'annulation"
            )
        
        return {
            "success": True,
            "message": "Abonnement annulé avec succès",
            "immediate": immediate
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur annulation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@subscription_router.post("/reactivate")
async def reactivate_subscription(current_user: User = Depends(get_current_user)):
    """Réactive un abonnement annulé"""
    try:
        if not current_user.stripe_subscription_id:
            raise HTTPException(
                status_code=400,
                detail="Aucun abonnement à réactiver"
            )
        
        success = await stripe_service.reactivate_subscription(current_user)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Erreur lors de la réactivation"
            )
        
        return {
            "success": True,
            "message": "Abonnement réactivé avec succès"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur réactivation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================================================================
# 🔧 NOUVEAUX ENDPOINTS RECOVERY
# ================================================================================

@subscription_router.get("/incomplete")
async def get_incomplete_subscriptions(current_user: User = Depends(get_current_user)):
    """Retourne les abonnements incomplets de l'utilisateur"""
    try:
        incomplete_subs = await recovery_service.check_incomplete_subscriptions(current_user)
        
        return {
            "success": True,
            "incomplete": [sub.dict() for sub in incomplete_subs],
            "count": len(incomplete_subs),
            "can_retry": current_user.can_retry_subscription
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération abonnements incomplets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@subscription_router.post("/retry")
async def retry_subscription(
    request: RecoveryRequest,
    current_user: User = Depends(get_current_user)
):
    """Relance un abonnement échoué"""
    try:
        if not current_user.can_retry_subscription:
            raise HTTPException(
                status_code=400,
                detail="Retry non autorisé pour cet utilisateur"
            )
        
        result = await recovery_service.retry_incomplete_subscription(current_user, request)
        
        if result["success"]:
            return {
                "success": True,
                "retry_url": result.get("retry_url"),
                "update_url": result.get("update_url"),
                "message": result["message"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur retry abonnement: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@subscription_router.post("/new-after-failure")
async def create_new_subscription_after_failure(
    plan_type: PlanType,
    current_user: User = Depends(get_current_user)
):
    """Crée un nouvel abonnement après échec précédent"""
    try:
        if not current_user.can_start_new_subscription():
            raise HTTPException(
                status_code=400,
                detail="Nouvelle souscription non autorisée"
            )
        
        plan_config = PLAN_CONFIG.get(plan_type)
        if not plan_config:
            raise HTTPException(status_code=400, detail="Plan invalide")
        
        price_id = plan_config.get("stripe_price_id")
        if not price_id:
            raise HTTPException(status_code=400, detail="Price ID non trouvé pour ce plan")
        
        result = await recovery_service.create_new_subscription_after_failure(
            current_user, plan_type, price_id
        )
        
        if result["success"]:
            return {
                "success": True,
                "checkout_url": result["checkout_url"],
                "message": result["message"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur nouvelle souscription post-échec: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================================================================
# 🎯 WEBHOOK ENDPOINT - VERSION CORRIGÉE
# ================================================================================

@subscription_router.post("/webhook")
async def handle_stripe_webhook(request: Request, db = Depends(get_database)):
    """Endpoint pour recevoir les webhooks Stripe"""
    try:
        # Vérifier la signature
        event = await webhook_handler.verify_webhook_signature(request)
        
        # ✅ CORRECTION: Passage correct de l'instance DB
        success = await webhook_handler.handle_webhook(event, db)
        
        if success:
            return {"received": True, "processed": True}
        else:
            return {"received": True, "processed": False}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur webhook: {str(e)}")
        raise HTTPException(status_code=400, detail="Webhook processing failed")

# ================================================================================
# 📊 ENDPOINTS HISTORIQUE ET ANALYTICS
# ================================================================================

@subscription_router.get("/history")
async def get_subscription_history(current_user: User = Depends(get_current_user)):
    """Retourne l'historique des abonnements et paiements"""
    try:
        recovery_stats = await recovery_service.get_recovery_statistics(current_user)
        
        return {
            "success": True,
            "payment_attempts": [attempt.dict() for attempt in current_user.payment_attempts[-10:]],  # 10 dernières
            "recovery_statistics": recovery_stats,
            "summary": {
                "total_attempts": len(current_user.payment_attempts),
                "recovery_attempts": current_user.recovery_attempts,
                "has_used_trial": current_user.has_used_trial,
                "can_retry": current_user.can_retry_subscription
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur historique: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================================================================
# 🛠️ ENDPOINTS UTILITAIRES
# ================================================================================

@subscription_router.get("/validate-trial-eligibility")
async def validate_trial_eligibility(current_user: User = Depends(get_current_user)):
    """Valide l'éligibilité à l'essai gratuit"""
    return {
        "eligible": current_user.can_start_trial(),
        "has_used_trial": current_user.has_used_trial,
        "current_plan": current_user.subscription_plan,
        "can_subscribe_directly": current_user.can_start_new_subscription(),
        "recovery_options": current_user.get_recovery_options(),
        "message": "Éligible à l'essai gratuit" if current_user.can_start_trial() else "Essai déjà utilisé - Abonnement direct possible"
    }

@subscription_router.post("/update-usage")
async def update_monthly_usage(
    sheets_used: int,
    current_user: User = Depends(get_current_user)
):
    """Met à jour l'usage mensuel de l'utilisateur"""
    try:
        # Dans une vraie implémentation, ceci serait dans la DB
        current_user.monthly_sheets_used = sheets_used
        
        return {
            "success": True,
            "monthly_used": sheets_used,
            "monthly_limit": current_user.get_monthly_limit(),
            "remaining": current_user.get_monthly_limit() - sheets_used if current_user.get_monthly_limit() != float('inf') else float('inf')
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour usage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))