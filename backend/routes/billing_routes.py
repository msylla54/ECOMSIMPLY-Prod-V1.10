# ================================================================================
# ECOMSIMPLY - ROUTES BILLING AVEC CONFIG CENTRALISÉE ENV-FIRST
# ================================================================================

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
from datetime import datetime
import os
import logging
from ..models.subscription import PlanType
from ..services.stripe_service import stripe_service
from ..core.config import settings, require_stripe

from database import get_db

logger = logging.getLogger(__name__)

billing_router = APIRouter(prefix="/api/billing", tags=["billing"])

# Import temporaire pour get_current_user
import jwt
from datetime import timedelta

JWT_SECRET = settings.JWT_SECRET
JWT_ALGORITHM = "HS256"

async def get_current_user(request: Request):
    """
    Fonction get_current_user pour l'authentification JWT
    """
    try:
        # Extract Bearer token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Token d'autorisation manquant")
        
        token = auth_header.split(" ")[1]
        
        # Decode JWT token
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("user_id")
            email = payload.get("email")
            
            if not user_id or not email:
                raise HTTPException(status_code=401, detail="Token invalide")
                
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expiré")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Token invalide")
        
        # Get user from database
        db = await get_db()
        user = await db["users"].find_one({"email": email})
        
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur serveur")

@billing_router.post("/checkout", response_model=Dict[str, Any])
async def create_checkout_session(
    request: Request,
    db = Depends(get_db)
):
    """
    Crée une session Stripe Checkout pour l'offre unique Premium avec essai 3 jours
    MODE PRODUCTION - Configuration entièrement via ENV
    """
    try:
        # Authentification utilisateur
        current_user = await get_current_user(request)
        
        # Require Stripe configuration from ENV
        stripe_config = require_stripe()
        
        logger.info(f"🛒 Creating checkout session for user: {current_user.get('email', 'unknown')}")
        
        # Validation - Utilisateur ne doit pas avoir d'abonnement actif
        if current_user.get('subscription_plan') == 'premium' and current_user.get('subscription_status') in ['active', 'trialing']:
            logger.warning(f"User already has active premium subscription: {current_user.get('email')}")
            raise HTTPException(
                status_code=400, 
                detail="Vous avez déjà un abonnement Premium actif"
            )
        
        # Récupérer l'IP client pour tracking
        client_ip = None
        if request:
            client_ip = request.client.host
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                client_ip = forwarded_for.split(',')[0].strip()
        
        # Créer ou récupérer customer Stripe
        customer_id = current_user.get('stripe_customer_id')
        if not customer_id:
            import stripe
            stripe.api_key = stripe_config["secret_key"]
            
            customer = stripe.Customer.create(
                email=current_user.get('email'),
                name=current_user.get('name', ''),
                metadata={
                    "user_id": current_user.get('id'),
                    "platform": "ecomsimply"
                }
            )
            customer_id = customer.id
            
            # Mettre à jour l'utilisateur avec customer_id
            await db.users.update_one(
                {"_id": current_user["_id"]},
                {"$set": {"stripe_customer_id": customer_id}}
            )
            
            logger.info(f"✅ Created Stripe customer: {customer_id}")
        
        # Configuration session Checkout pour Premium avec essai 3 jours
        # IMPORTANT : Le trial_period_days=3 est configuré au niveau du Price dans Stripe Dashboard
        import stripe
        stripe.api_key = stripe_config["secret_key"]
        
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": stripe_config["price_premium"],  # ✅ ENV-FIRST
                "quantity": 1,
            }],
            mode="subscription",
            success_url=stripe_config["success_url"] or f"{settings.APP_BASE_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=stripe_config["cancel_url"] or f"{settings.APP_BASE_URL}/billing/cancel",
            metadata={
                "user_id": current_user.get('id'),
                "plan_type": "premium",
                "platform": "ecomsimply",
                "checkout_version": "v3_premium_only",
                "trial_days": "3",
                "client_ip_hash": f"ip_{hash(client_ip)}" if client_ip else None
            },
            # Permettre codes promo
            allow_promotion_codes=True,
            # Configuration de facturation
            billing_address_collection="required",
        )
        
        logger.info(f"✅ Checkout session created: {session.id} for user {current_user.get('email')}")
        
        return {
            "success": True,
            "checkout_url": session.url,
            "session_id": session.id,
            "customer_id": customer_id,
            "plan_type": "premium",
            "trial_days": 3,
            "message": "Session de paiement créée avec succès - Essai gratuit 3 jours inclus"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating checkout session: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la création de la session de paiement: {str(e)}"
        )

@billing_router.post("/webhook")
async def handle_stripe_webhook(request: Request, db = Depends(get_db)):
    """
    Endpoint webhook Stripe pour gérer les événements de paiement
    """
    try:
        from ..webhooks.stripe_webhooks import webhook_handler
        
        # Vérifier et traiter le webhook
        event_result = await webhook_handler.verify_webhook_signature(request, db)
        
        if event_result.get("duplicate", False):
            logger.info("🔄 Duplicate webhook event ignored")
            return {"received": True, "processed": False, "reason": "duplicate"}
        
        # Traiter l'événement
        success = await webhook_handler.handle_webhook(event_result["event"], db)
        
        if success:
            logger.info(f"✅ Webhook processed successfully: {event_result['event']['type']}")
            return {"received": True, "processed": True}
        else:
            logger.warning(f"⚠️ Webhook processing failed: {event_result['event']['type']}")
            return {"received": True, "processed": False}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Webhook error: {str(e)}")
        # Pour les webhooks, toujours retourner 200 même en cas d'erreur pour éviter les retry
        return {"received": True, "processed": False, "error": "internal_error"}

@billing_router.get("/config")
async def get_billing_config():
    """
    Retourne la configuration billing pour le frontend
    """
    stripe_config = settings.get_stripe_config()
    
    return {
        "success": True,
        "stripe_enabled": stripe_config["enabled"],
        "stripe_price_id": stripe_config["price_premium"] if stripe_config["enabled"] else None,
        "plan": {
            "name": "Premium",
            "plan_id": "premium",
            "price": 99,
            "currency": "EUR",
            "trial_days": 3,
            "stripe_price_id": stripe_config["price_premium"] if stripe_config["enabled"] else None,
            "features": [
                "Fiches produits illimitées",
                "IA Premium + Automation complète",
                "Publication multi-plateformes",
                "Analytics avancées + exports",
                "Support prioritaire 24/7",
                "API accès complet",
                "Intégrations personnalisées"
            ]
        },
        "trial_text_fr": "3 jours d'essai gratuit",
        "trial_text_en": "3-day free trial",
        "cta_text_fr": "Commencer essai 3 jours",
        "cta_text_en": "Start 3-day trial"
    }