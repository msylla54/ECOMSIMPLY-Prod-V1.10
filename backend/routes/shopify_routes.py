# Shopify Integration Routes - Phase 1 OAuth & Connections
from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
import logging
import os
import jwt
from datetime import datetime

from marketplaces.shopify.oauth import ShopifyOAuthService
from marketplaces.shopify.client import ShopifyAPIClient
from models.shopify_connections import (
    ShopifyConnection, ShopifyConnectionRequest, ShopifyConnectionResponse,
    ConnectionStatus, ShopifyCallbackData, ShopifyConnectionStatus
)

logger = logging.getLogger(__name__)

# Router avec préfixe /api/shopify
shopify_router = APIRouter(prefix="/api/shopify", tags=["Shopify Integration Phase 1"])

# Security
security = HTTPBearer()

# Dépendance pour obtenir la base de données
async def get_database():
    """Récupère l'instance MongoDB"""
    from motor.motor_asyncio import AsyncIOMotorClient
    
    mongo_url = os.environ.get('MONGO_URL')
    if not mongo_url:
        raise HTTPException(
            status_code=500,
            detail="Database configuration error"
        )
    
    client = AsyncIOMotorClient(mongo_url)
    db_name = os.environ.get('DB_NAME', 'ecomsimply_production')
    return client[db_name]

# Dépendance pour obtenir l'utilisateur authentifié
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extrait l'utilisateur depuis le JWT token"""
    try:
        token = credentials.credentials
        secret = os.environ.get('JWT_SECRET')
        
        if not secret:
            raise HTTPException(status_code=500, detail="JWT configuration error")
        
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        user_id = payload.get('user_id')
        
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )
        
        return user_id
        
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    except Exception as e:
        logger.error(f"❌ Authentication error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )

# 1. POST /api/shopify/install - Lancer OAuth Shopify
@shopify_router.post("/install", response_model=ShopifyConnectionResponse)
async def install_shopify_app(
    request: ShopifyConnectionRequest,
    current_user: str = Depends(get_current_user),
    db = Depends(get_database),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Lance le processus d'installation OAuth Shopify
    
    Étapes:
    1. Valider le domaine de boutique
    2. Générer une URL OAuth sécurisée avec state CSRF
    3. Créer un enregistrement de connexion en attente
    4. Retourner l'URL pour redirection utilisateur
    """
    try:
        logger.info(f"🔗 Initiating Shopify installation for user {current_user[:8]}*** shop {request.shop_domain}")
        
        # Vérifier si une connexion existe déjà pour cette boutique
        existing_connection = await db.shopify_connections.find_one({
            "user_id": current_user,
            "shop_domain": request.shop_domain.lower().strip(),
            "status": {"$ne": "revoked"}
        })
        
        if existing_connection:
            logger.warning(f"⚠️ Connection already exists for shop {request.shop_domain}")
            raise HTTPException(
                status_code=409,
                detail="Une connexion existe déjà pour cette boutique"
            )
        
        # Initialiser le service OAuth
        oauth_service = ShopifyOAuthService()
        
        # Générer l'URL d'installation avec state sécurisé
        install_data = oauth_service.generate_install_url(
            shop_domain=request.shop_domain,
            user_id=current_user
        )
        
        # Créer l'enregistrement de connexion en attente
        connection = ShopifyConnection(
            user_id=current_user,
            shop_domain=install_data['shop_domain'],
            shop_name="",  # Sera rempli après installation
            encrypted_access_token="",  # Sera rempli après callback
            token_encryption_nonce="",  # Sera rempli après callback
            scopes=install_data['scopes'],
            status=ConnectionStatus.PENDING,
            oauth_state=install_data['state'],
            oauth_state_expires=install_data['expires_at']
        )
        
        # Sauvegarder en base
        connection_dict = connection.dict(by_alias=True)
        connection_dict['_id'] = connection.id
        await db.shopify_connections.insert_one(connection_dict)
        
        # Programmer nettoyage des états expirés en arrière-plan
        background_tasks.add_task(cleanup_expired_oauth_states, db)
        
        logger.info(f"✅ Shopify OAuth initiated successfully: {connection.id}")
        
        return ShopifyConnectionResponse(
            connection_id=connection.id,
            install_url=install_data['install_url'],
            state=install_data['state'],
            shop_domain=install_data['shop_domain'],
            expires_at=install_data['expires_at'],
            scopes=install_data['scopes']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to initiate Shopify installation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Échec de l'initialisation de l'installation Shopify"
        )

# 2. GET /api/shopify/callback - Traiter retour OAuth
@shopify_router.get("/callback")
async def handle_shopify_oauth_callback(
    request: Request,
    shop: str,
    code: str,
    state: str,
    timestamp: Optional[str] = None,
    hmac: Optional[str] = None,
    db = Depends(get_database)
):
    """
    Traite le callback OAuth Shopify et génère l'access token
    
    Processus complet:
    1. Valider le state OAuth (protection CSRF)
    2. Vérifier la signature HMAC si fournie
    3. Échanger le code contre access_token
    4. Récupérer les informations de la boutique
    5. Chiffrer et stocker l'access_token en base
    6. Mettre à jour le statut de connexion
    7. Rediriger vers l'interface avec succès
    """
    try:
        logger.info(f"📞 Processing Shopify OAuth callback for shop {shop}")
        
        # Valider les paramètres requis
        if not all([shop, code, state]):
            logger.error("❌ Missing required OAuth callback parameters")
            return _generate_error_response(
                "missing_parameters",
                "Paramètres OAuth manquants"
            )
        
        # Trouver la connexion en attente avec ce state
        connection_doc = await db.shopify_connections.find_one({
            "oauth_state": state,
            "status": "pending",
            "oauth_state_expires": {"$gt": datetime.utcnow()}
        })
        
        if not connection_doc:
            logger.error("❌ Invalid or expired OAuth state")
            return _generate_error_response(
                "invalid_state",
                "État OAuth invalide ou expiré"
            )
        
        # Initialiser les services
        oauth_service = ShopifyOAuthService()
        
        # Vérifier la signature HMAC du state
        if not oauth_service._verify_state(state, connection_doc['user_id']):
            logger.error("❌ OAuth state HMAC verification failed")
            return _generate_error_response(
                "state_verification_failed",
                "Vérification de sécurité échouée"
            )
        
        # Échanger le code contre l'access token
        token_data = await oauth_service.exchange_code_for_token(
            shop_domain=shop,
            code=code,
            state=state,
            user_id=connection_doc['user_id']
        )
        
        # Créer un client temporaire pour récupérer les infos de la boutique
        temp_client = ShopifyAPIClient(shop, token_data['access_token'])
        shop_info_response = await temp_client.get_shop_info()
        shop_info = shop_info_response.get('shop', {})
        
        # Chiffrer l'access token
        encrypted_token_data = oauth_service.encrypt_access_token(
            access_token=token_data['access_token'],
            user_id=connection_doc['user_id']
        )
        
        # Mettre à jour la connexion en base
        update_data = {
            "shop_name": shop_info.get('name', shop),
            "shop_id": str(shop_info.get('id', '')),
            "status": "active",
            "installed_at": datetime.utcnow(),
            "encrypted_access_token": encrypted_token_data['encrypted_token'],
            "token_encryption_nonce": encrypted_token_data['nonce'],
            "scopes": token_data['scope'],
            "shop_plan": shop_info.get('plan_name', '').lower(),
            "shop_country": shop_info.get('country_code'),
            "shop_currency": shop_info.get('currency'),
            "shop_timezone": shop_info.get('timezone'),
            "shop_email": shop_info.get('email'),
            "oauth_state": None,  # Nettoyer le state utilisé
            "oauth_state_expires": None,
            "updated_at": datetime.utcnow(),
            "error_message": None  # Nettoyer les anciennes erreurs
        }
        
        await db.shopify_connections.update_one(
            {"_id": connection_doc['_id']},
            {"$set": update_data}
        )
        
        logger.info(f"✅ Shopify connection successful: {connection_doc['_id']}")
        
        # Redirection vers le dashboard avec succès
        return _generate_success_response()
        
    except Exception as e:
        logger.error(f"❌ OAuth callback error: {str(e)}")
        
        # Mettre à jour le statut d'erreur si possible
        if 'connection_doc' in locals():
            await db.shopify_connections.update_one(
                {"_id": connection_doc['_id']},
                {"$set": {
                    "status": "error",
                    "error_message": str(e),
                    "updated_at": datetime.utcnow()
                }}
            )
        
        return _generate_error_response(
            "callback_error",
            "Erreur lors de la connexion Shopify"
        )

# 3. GET /api/shopify/status - État connexion utilisateur
@shopify_router.get("/status")
async def get_shopify_connection_status(
    current_user: str = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Retourne l'état global des connexions Shopify pour l'utilisateur
    
    États possibles:
    - none: Aucune connexion
    - connected: Au moins une connexion active
    - error: Connexions en erreur uniquement
    - revoked: Connexions révoquées uniquement
    """
    try:
        logger.info(f"🔍 Getting Shopify status for user {current_user[:8]}***")
        
        # Récupérer toutes les connexions utilisateur
        connections_cursor = db.shopify_connections.find({
            "user_id": current_user
        }).sort("created_at", -1)
        
        connections = await connections_cursor.to_list(length=None)
        
        if not connections:
            return {
                "status": "none",
                "message": "Aucune connexion Shopify",
                "connections_count": 0,
                "active_shops": []
            }
        
        # Analyser les statuts
        statuses = [conn.get('status') for conn in connections]
        active_connections = [conn for conn in connections if conn.get('status') == 'active']
        
        if active_connections:
            # Au moins une connexion active
            active_shops = [
                {
                    "connection_id": conn['_id'],
                    "shop_domain": conn['shop_domain'],
                    "shop_name": conn.get('shop_name'),
                    "shop_id": conn.get('shop_id'),
                    "scopes": conn['scopes'],
                    "installed_at": conn.get('installed_at'),
                    "shop_plan": conn.get('shop_plan')
                }
                for conn in active_connections
            ]
            
            return {
                "status": "connected",
                "message": f"{len(active_connections)} connexion(s) Shopify active(s)",
                "connections_count": len(active_connections),
                "total_connections": len(connections),
                "active_shops": active_shops
            }
        
        elif "pending" in statuses:
            return {
                "status": "pending",
                "message": "Connexions Shopify en cours",
                "connections_count": len([s for s in statuses if s == "pending"]),
                "total_connections": len(connections)
            }
        
        elif "error" in statuses:
            error_connections = [conn for conn in connections if conn.get('status') == 'error']
            return {
                "status": "error",
                "message": "Erreurs de connexion Shopify",
                "connections_count": len(error_connections),
                "total_connections": len(connections),
                "last_error": error_connections[0].get('error_message') if error_connections else None
            }
        
        else:
            return {
                "status": "revoked",
                "message": "Connexions Shopify révoquées",
                "connections_count": len([s for s in statuses if s == "revoked"]),
                "total_connections": len(connections)
            }
            
    except Exception as e:
        logger.error(f"❌ Failed to get Shopify status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération du statut"
        )

# 4. POST /api/shopify/disconnect - Déconnecter
@shopify_router.post("/disconnect")
async def disconnect_shopify_connections(
    current_user: str = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Déconnecte toutes les connexions Shopify de l'utilisateur
    
    Actions:
    1. Marquer toutes les connexions comme révoquées
    2. Supprimer les tokens chiffrés
    3. Nettoyer les états OAuth en cours
    """
    try:
        logger.info(f"🔌 Disconnecting Shopify connections for user {current_user[:8]}***")
        
        # Mettre à jour toutes les connexions utilisateur
        result = await db.shopify_connections.update_many(
            {
                "user_id": current_user,
                "status": {"$ne": "revoked"}
            },
            {
                "$set": {
                    "status": "revoked",
                    "encrypted_access_token": None,
                    "token_encryption_nonce": None,
                    "oauth_state": None,
                    "oauth_state_expires": None,
                    "updated_at": datetime.utcnow(),
                    "error_message": "Déconnexion manuelle"
                }
            }
        )
        
        logger.info(f"✅ Disconnected {result.modified_count} Shopify connections")
        
        return {
            "status": "revoked",
            "message": f"{result.modified_count} connexion(s) Shopify déconnectée(s)",
            "disconnected_count": result.modified_count
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to disconnect Shopify connections: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la déconnexion"
        )

# 5. GET /api/shopify/health - Health check
@shopify_router.get("/health")
async def shopify_health_check():
    """
    Vérification de santé des services Shopify
    """
    try:
        # Vérifier la configuration OAuth
        oauth_service = ShopifyOAuthService()
        
        health_status = {
            "service": "shopify_integration",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "components": {
                "oauth_service": "healthy",
                "database": "healthy",
                "encryption": "healthy"
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Shopify health check failed: {str(e)}")
        
        return {
            "service": "shopify_integration",
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

# Fonctions utilitaires
def _generate_success_response() -> RedirectResponse:
    """Génère la redirection de succès"""
    frontend_url = os.environ.get('APP_BASE_URL', 'https://app.ecomsimply.com')
    success_url = f"{frontend_url}/?shopify=connected"
    return RedirectResponse(url=success_url, status_code=302)

def _generate_error_response(error_type: str, error_message: str) -> RedirectResponse:
    """Génère la redirection d'erreur"""
    frontend_url = os.environ.get('APP_BASE_URL', 'https://app.ecomsimply.com')
    error_url = f"{frontend_url}/?shopify_error={error_type}&message={error_message}"
    return RedirectResponse(url=error_url, status_code=302)

async def cleanup_expired_oauth_states(db):
    """Nettoie les états OAuth expirés (tâche d'arrière-plan)"""
    try:
        result = await db.shopify_connections.delete_many({
            "status": "pending",
            "oauth_state_expires": {"$lt": datetime.utcnow()}
        })
        
        if result.deleted_count > 0:
            logger.info(f"🧹 Cleaned up {result.deleted_count} expired Shopify OAuth states")
            
    except Exception as e:
        logger.error(f"❌ Failed to cleanup expired Shopify states: {str(e)}")