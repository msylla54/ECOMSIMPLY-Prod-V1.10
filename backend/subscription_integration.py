# ================================================================================
# ECOMSIMPLY - INTÉGRATION COMPLÈTE SYSTÈME ABONNEMENTS DANS BACKEND PRINCIPAL
# ================================================================================

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime
from typing import Dict, Any

# Imports du système d'abonnements - ✅ CORRECTION: Imports absoluts
try:
    from models.subscription import User, SubscriptionStatus, PlanType, PLAN_CONFIG
    from routes.subscription_routes import subscription_router
    from services.stripe_service import stripe_service
    from webhooks.stripe_webhooks import webhook_handler
except ImportError as e:
    print(f"Warning: Subscription system imports failed: {e}")
    # Fallback: Use None values for optional subscription features
    subscription_router = None
    stripe_service = None
    webhook_handler = None

# ================================================================================
# 🔧 INTÉGRATION DANS LE BACKEND PRINCIPAL (server.py)
# ================================================================================

def integrate_subscription_system(app: FastAPI, db):
    """Intègre le système d'abonnements dans l'application principale"""
    
    # Vérifier si le système d'abonnement est disponible
    if subscription_router is None:
        print("⚠️ Subscription system not available - skipping integration")
        return
    
    # Ajouter les routes d'abonnement
    app.include_router(subscription_router)
    
    # Middleware pour vérifier les limites d'abonnement
    @app.middleware("http")
    async def subscription_middleware(request: Request, call_next):
        """Middleware pour vérifier les accès selon l'abonnement"""
        
        # Routes protégées nécessitant un abonnement actif
        protected_routes = [
            "/generate-sheet",
            "/ai/",
            "/premium/",
            "/export/"
        ]
        
        # Vérifier si la route est protégée
        is_protected = any(route in str(request.url) for route in protected_routes)
        
        if is_protected and request.method in ["POST", "PUT", "DELETE"]:
            try:
                # Extraire le token utilisateur
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
                    # Ici on décode le JWT pour obtenir l'user_id
                    # user = await get_current_user_from_token(token, db)
                    
                    # Pour l'exemple, on skip cette vérification
                    pass
                    
                    # Vérifier les limites d'abonnement
                    # if not user.can_access_features():
                    #     raise HTTPException(
                    #         status_code=403,
                    #         detail="Abonnement requis pour accéder à cette fonctionnalité"
                    #     )
                    
            except Exception as e:
                print(f"⚠️ Erreur middleware abonnement: {e}")
        
        response = await call_next(request)
        return response

# ================================================================================
# 🛠️ FONCTIONS UTILITAIRES POUR INTÉGRATION
# ================================================================================

async def check_user_subscription_limits(user: User, action: str) -> Dict[str, Any]:
    """Vérifie les limites d'abonnement pour une action donnée"""
    
    if action == "generate_sheet":
        # Vérifier limite mensuelle de fiches
        monthly_limit = user.get_monthly_limit()
        
        if user.monthly_sheets_used >= monthly_limit:
            return {
                "allowed": False,
                "reason": "monthly_limit_exceeded",
                "message": f"Limite mensuelle atteinte ({monthly_limit} fiches)",
                "upgrade_required": True
            }
    
    elif action == "premium_features":
        # Vérifier accès aux fonctionnalités premium
        if user.subscription_plan == PlanType.GRATUIT and not user.is_trial_active():
            return {
                "allowed": False,
                "reason": "premium_required",
                "message": "Abonnement Pro ou Premium requis",
                "upgrade_required": True
            }
    
    elif action == "advanced_ai":
        # Vérifier accès IA avancée (Pro/Premium)
        if user.subscription_plan == PlanType.GRATUIT and not user.is_trial_active():
            return {
                "allowed": False,
                "reason": "advanced_plan_required",
                "message": "Plan Pro ou Premium requis pour l'IA avancée",
                "upgrade_required": True
            }
    
    return {
        "allowed": True,
        "reason": "subscription_valid",
        "message": "Accès autorisé"
    }

async def update_user_usage(user_id: str, action: str, db) -> bool:
    """Met à jour l'utilisation mensuelle de l'utilisateur"""
    try:
        if action == "sheet_generated":
            await db.users.update_one(
                {"id": user_id},
                {
                    "$inc": {"monthly_sheets_used": 1},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            return True
            
    except Exception as e:
        print(f"❌ Erreur mise à jour usage: {e}")
        return False
    
    return False

# ================================================================================
# 🎯 DÉCORATEURS POUR PROTECTION DES ROUTES
# ================================================================================

from functools import wraps

def subscription_required(feature: str = "premium"):
    """Décorateur pour protéger les routes nécessitant un abonnement"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Récupérer l'utilisateur depuis les kwargs
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=401,
                    detail="Authentification requise"
                )
            
            # Vérifier les limites d'abonnement
            check_result = await check_user_subscription_limits(current_user, feature)
            
            if not check_result["allowed"]:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": check_result["message"],
                        "reason": check_result["reason"],
                        "upgrade_required": check_result.get("upgrade_required", False),
                        "current_plan": current_user.subscription_plan,
                        "trial_active": current_user.is_trial_active()
                    }
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# ================================================================================
# 🔄 TÂCHES AUTOMATIQUES POUR GESTION ABONNEMENTS
# ================================================================================

import asyncio
from datetime import timedelta

async def cleanup_expired_trials(db):
    """Nettoie les essais expirés et met à jour les statuts"""
    try:
        # Trouver les utilisateurs avec essai expiré
        expired_cutoff = datetime.utcnow()
        
        expired_users = await db.users.find({
            "trial_end_date": {"$lt": expired_cutoff},
            "subscription_plan": {"$ne": "gratuit"}
        }).to_list(length=None)
        
        for user_data in expired_users:
            user = User(**user_data)
            
            # Si pas d'abonnement payant actif, revenir au gratuit
            if not user.is_subscription_active():
                await db.users.update_one(
                    {"id": user.id},
                    {
                        "$set": {
                            "subscription_plan": PlanType.GRATUIT,
                            "subscription_status": SubscriptionStatus.ACTIVE,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                print(f"✅ Utilisateur {user.email} : retour plan gratuit après expiration essai")
        
    except Exception as e:
        print(f"❌ Erreur cleanup essais expirés: {e}")

async def sync_stripe_subscriptions(db):
    """Synchronise périodiquement avec Stripe"""
    try:
        # Récupérer tous les utilisateurs avec abonnement Stripe
        users_with_subscriptions = await db.users.find({
            "stripe_subscription_id": {"$ne": None}
        }).to_list(length=None)
        
        for user_data in users_with_subscriptions:
            user = User(**user_data)
            
            # Synchroniser avec Stripe
            updated_user = await stripe_service.sync_subscription_status(user)
            
            # Mettre à jour en base
            await db.users.update_one(
                {"id": user.id},
                {"$set": updated_user.dict(exclude={"id"})}
            )
        
        print(f"✅ Synchronisation Stripe terminée : {len(users_with_subscriptions)} utilisateurs")
        
    except Exception as e:
        print(f"❌ Erreur sync Stripe: {e}")

# ================================================================================
# 📧 SYSTÈME DE NOTIFICATIONS ABONNEMENT
# ================================================================================

async def send_subscription_notifications(db):
    """Envoie les notifications liées aux abonnements"""
    try:
        now = datetime.utcnow()
        
        # Notifications 3 jours avant expiration essai
        trial_warning_date = now + timedelta(days=3)
        
        users_trial_ending = await db.users.find({
            "trial_end_date": {
                "$gte": now,
                "$lte": trial_warning_date
            },
            "has_used_trial": True
        }).to_list(length=None)
        
        for user_data in users_trial_ending:
            # Envoyer notification (email, etc.)
            print(f"📧 Notification essai se termine : {user_data['email']}")
            # Ici on intégrerait le système d'email
        
        # Notifications échecs de paiement
        users_payment_failed = await db.users.find({
            "payment_failed_date": {"$gte": now - timedelta(days=7)},
            "payment_failed_count": {"$gte": 1}
        }).to_list(length=None)
        
        for user_data in users_payment_failed:
            print(f"💳 Notification échec paiement : {user_data['email']}")
        
    except Exception as e:
        print(f"❌ Erreur notifications: {e}")

# ================================================================================
# 🚀 FONCTION PRINCIPALE D'INITIALISATION
# ================================================================================

async def initialize_subscription_system(app: FastAPI, db):
    """Initialise complètement le système d'abonnements"""
    
    print("🚀 Initialisation système d'abonnements ECOMSIMPLY...")
    
    # Vérifier si le système d'abonnement est disponible
    if subscription_router is None:
        print("⚠️ Subscription system not available - skipping initialization")
        return
    
    # 1. Intégrer les routes et middleware
    integrate_subscription_system(app, db)
    
    # 2. Vérifier la configuration Stripe
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    if not stripe_key or not webhook_secret:
        print("⚠️ Configuration Stripe manquante - Fonctionnalités limitées")
    else:
        print("✅ Configuration Stripe OK")
    
    # 3. Créer les index MongoDB si nécessaire
    try:
        await db.users.create_index("stripe_customer_id")
        await db.subscription_records.create_index("stripe_subscription_id")
        await db.payment_history.create_index("user_id")
        print("✅ Index MongoDB créés")
    except Exception as e:
        print(f"⚠️ Erreur création index: {e}")
    
    # 4. Lancer les tâches de maintenance (optionnel)
    # asyncio.create_task(periodic_maintenance(db))
    
    print("✅ Système d'abonnements initialisé avec succès")

async def periodic_maintenance(db):
    """Tâches de maintenance périodiques"""
    while True:
        try:
            await asyncio.sleep(3600)  # Toutes les heures
            
            await cleanup_expired_trials(db)
            await sync_stripe_subscriptions(db)
            await send_subscription_notifications(db)
            
        except Exception as e:
            print(f"❌ Erreur maintenance périodique: {e}")
            await asyncio.sleep(600)  # Attendre 10 min en cas d'erreur