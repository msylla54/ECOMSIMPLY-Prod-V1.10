# Amazon Integration Routes - Phase 1 Fondations
from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
import logging
import os
import jwt
from datetime import datetime

from integrations.amazon.auth import AmazonOAuthService
from integrations.amazon.client import AmazonSPAPIClient
from integrations.amazon.models import (
    AmazonConnection, ConnectionRequest, ConnectionResponse, 
    ConnectionStatus, OAuthCallback, AmazonRegion,
    SUPPORTED_MARKETPLACES
)

logger = logging.getLogger(__name__)

# Router avec préfixe /api/amazon
amazon_integration_router = APIRouter(prefix="/api/amazon", tags=["Amazon Integration Phase 1"])

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

# 1. POST /api/amazon/connect - Lancer OAuth Amazon
@amazon_integration_router.post("/connect", response_model=ConnectionResponse)
async def connect_amazon_account(
    request: ConnectionRequest,
    current_user: str = Depends(get_current_user),
    db = Depends(get_database),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Lance le processus de connexion OAuth Amazon SP-API
    
    Étapes:
    1. Valider le marketplace et la région
    2. Générer une URL OAuth sécurisée avec state CSRF
    3. Créer un enregistrement de connexion en attente
    4. Retourner l'URL pour redirection utilisateur
    """
    try:
        logger.info(f"🔗 Initiating Amazon connection for user {current_user[:8]}*** marketplace {request.marketplace_id}")
        
        # Auto-détecter la région si non fournie
        if not request.region:
            marketplace_regions = {
                'ATVPDKIKX0DER': AmazonRegion.NA,  # US
                'A2EUQ1WTGCTBG2': AmazonRegion.NA, # CA
                'A1AM78C64UM0Y8': AmazonRegion.NA, # MX
                'A1PA6795UKMFR9': AmazonRegion.EU, # DE
                'A1RKKUPIHCS9HS': AmazonRegion.EU, # ES
                'A13V1IB3VIYZZH': AmazonRegion.EU, # FR
                'APJ6JRA9NG5V4': AmazonRegion.EU,  # IT
                'A1F83G8C2ARO7P': AmazonRegion.EU, # UK
                'A21TJRUUN4KGV': AmazonRegion.EU,  # IN
                'A1VC38T7YXB528': AmazonRegion.FE, # JP
                'ARBP9OOSHTCHU': AmazonRegion.FE   # EG
            }
            request.region = marketplace_regions.get(request.marketplace_id, AmazonRegion.EU)
        
        # Vérifier si une connexion existe déjà pour ce marketplace
        existing_connection = await db.amazon_connections.find_one({
            "user_id": current_user,
            "marketplace_id": request.marketplace_id,
            "status": {"$ne": "revoked"}
        })
        
        if existing_connection:
            logger.warning(f"⚠️ Connection already exists for marketplace {request.marketplace_id}")
            raise HTTPException(
                status_code=409,
                detail="Une connexion existe déjà pour ce marketplace"
            )
        
        # Initialiser le service OAuth
        oauth_service = AmazonOAuthService()
        
        # Générer l'URL OAuth avec state sécurisé
        oauth_data = oauth_service.generate_oauth_url(
            marketplace_id=request.marketplace_id,
            region=request.region.value
        )
        
        # Créer l'enregistrement de connexion en attente
        connection = AmazonConnection(
            user_id=current_user,
            marketplace_id=request.marketplace_id,
            region=request.region,
            status="pending",
            oauth_state=oauth_data['state'],
            oauth_state_expires=oauth_data['expires_at']
        )
        
        # Sauvegarder en base
        connection_dict = connection.dict(by_alias=True)
        connection_dict['_id'] = connection.id
        await db.amazon_connections.insert_one(connection_dict)
        
        # Programmer nettoyage des états expirés en arrière-plan
        background_tasks.add_task(cleanup_expired_oauth_states, db)
        
        logger.info(f"✅ Amazon OAuth initiated successfully: {connection.id}")
        
        return ConnectionResponse(
            connection_id=connection.id,
            authorization_url=oauth_data['authorization_url'],
            state=oauth_data['state'],
            expires_at=oauth_data['expires_at'],
            marketplace_id=request.marketplace_id,
            region=request.region.value
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to initiate Amazon connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Échec de l'initialisation de la connexion Amazon"
        )

# 2. GET /api/amazon/callback - Traiter retour OAuth
@amazon_integration_router.get("/callback")
async def handle_amazon_oauth_callback(
    request: Request,
    state: str,
    selling_partner_id: str,
    spapi_oauth_code: str,
    mws_auth_token: Optional[str] = None,
    db = Depends(get_database)
):
    """
    Traite le callback OAuth Amazon et génère le refresh token
    
    Processus complet:
    1. Valider le state OAuth (protection CSRF)
    2. Échanger le code contre access_token + refresh_token 
    3. Chiffrer et stocker le refresh_token en base
    4. Mettre à jour le statut de connexion
    5. Rediriger vers l'interface avec succès
    """
    try:
        logger.info(f"📞 Processing Amazon OAuth callback with state {state[:20]}***")
        
        # Valider les paramètres requis
        if not all([state, selling_partner_id, spapi_oauth_code]):
            logger.error("❌ Missing required OAuth callback parameters")
            return _generate_error_response(
                "missing_parameters",
                "Paramètres OAuth manquants"
            )
        
        # Trouver la connexion en attente avec ce state
        connection_doc = await db.amazon_connections.find_one({
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
        oauth_service = AmazonOAuthService()
        
        # Vérifier la signature HMAC du state
        if not oauth_service._verify_state(state):
            logger.error("❌ OAuth state HMAC verification failed")
            return _generate_error_response(
                "state_verification_failed",
                "Vérification de sécurité échouée"
            )
        
        # Échanger le code contre les tokens
        token_data = await oauth_service.exchange_code_for_tokens(
            code=spapi_oauth_code,
            state=state,
            region=connection_doc['region']
        )
        
        # Chiffrer le refresh token
        encrypted_token_data = oauth_service.encrypt_refresh_token(
            refresh_token=token_data['refresh_token'],
            user_id=connection_doc['user_id']
        )
        
        # Mettre à jour la connexion en base
        update_data = {
            "seller_id": selling_partner_id,
            "status": "connected",
            "connected_at": datetime.utcnow(),
            "encrypted_refresh_token": encrypted_token_data['encrypted_token'],
            "token_encryption_nonce": encrypted_token_data['nonce'],
            "oauth_state": None,  # Nettoyer le state utilisé
            "oauth_state_expires": None,
            "updated_at": datetime.utcnow(),
            "error_message": None  # Nettoyer les anciennes erreurs
        }
        
        await db.amazon_connections.update_one(
            {"_id": connection_doc['_id']},
            {"$set": update_data}
        )
        
        logger.info(f"✅ Amazon connection successful: {connection_doc['_id']}")
        
        # Redirection vers le dashboard avec succès
        return _generate_success_response()
        
    except Exception as e:
        logger.error(f"❌ OAuth callback error: {str(e)}")
        
        # Mettre à jour le statut d'erreur si possible
        if 'connection_doc' in locals():
            await db.amazon_connections.update_one(
                {"_id": connection_doc['_id']},
                {"$set": {
                    "status": "error",
                    "error_message": str(e),
                    "updated_at": datetime.utcnow()
                }}
            )
        
        return _generate_error_response(
            "callback_error",
            "Erreur lors de la connexion Amazon"
        )

# 3. GET /api/amazon/status - État connexion utilisateur
@amazon_integration_router.get("/status")
async def get_amazon_connection_status(
    current_user: str = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Retourne l'état global des connexions Amazon pour l'utilisateur
    
    États possibles:
    - none: Aucune connexion
    - connected: Au moins une connexion active
    - error: Connexions en erreur uniquement
    - revoked: Connexions révoquées uniquement
    """
    try:
        logger.info(f"🔍 Getting Amazon status for user {current_user[:8]}***")
        
        # Récupérer toutes les connexions utilisateur
        connections_cursor = db.amazon_connections.find({
            "user_id": current_user
        }).sort("created_at", -1)
        
        connections = await connections_cursor.to_list(length=None)
        
        if not connections:
            return {
                "status": "none",
                "message": "Aucune connexion Amazon",
                "connections_count": 0,
                "active_marketplaces": []
            }
        
        # Analyser les statuts
        statuses = [conn.get('status') for conn in connections]
        active_connections = [conn for conn in connections if conn.get('status') == 'connected']
        
        if active_connections:
            # Au moins une connexion active
            active_marketplaces = [
                {
                    "connection_id": conn['_id'],
                    "marketplace_id": conn['marketplace_id'],
                    "seller_id": conn.get('seller_id'),
                    "region": conn['region'],
                    "connected_at": conn.get('connected_at')
                }
                for conn in active_connections
            ]
            
            return {
                "status": "connected", 
                "message": f"{len(active_connections)} connexion(s) Amazon active(s)",
                "connections_count": len(active_connections),
                "total_connections": len(connections),
                "active_marketplaces": active_marketplaces
            }
        
        elif "pending" in statuses:
            return {
                "status": "pending",
                "message": "Connexions Amazon en cours",
                "connections_count": len([s for s in statuses if s == "pending"]),
                "total_connections": len(connections)
            }
        
        elif "error" in statuses:
            error_connections = [conn for conn in connections if conn.get('status') == 'error']
            return {
                "status": "error",
                "message": "Erreurs de connexion Amazon",
                "connections_count": len(error_connections),
                "total_connections": len(connections),
                "last_error": error_connections[0].get('error_message') if error_connections else None
            }
        
        else:
            return {
                "status": "revoked",
                "message": "Connexions Amazon révoquées", 
                "connections_count": len([s for s in statuses if s == "revoked"]),
                "total_connections": len(connections)
            }
            
    except Exception as e:
        logger.error(f"❌ Failed to get Amazon status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération du statut"
        )

# 4. POST /api/amazon/disconnect - Déconnecter
@amazon_integration_router.post("/disconnect")
async def disconnect_amazon_connections(
    current_user: str = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Déconnecte toutes les connexions Amazon de l'utilisateur
    
    Actions:
    1. Marquer toutes les connexions comme révoquées
    2. Supprimer les tokens chiffrés
    3. Nettoyer les états OAuth en cours
    """
    try:
        logger.info(f"🔌 Disconnecting Amazon connections for user {current_user[:8]}***")
        
        # Mettre à jour toutes les connexions utilisateur
        result = await db.amazon_connections.update_many(
            {
                "user_id": current_user,
                "status": {"$ne": "revoked"}
            },
            {
                "$set": {
                    "status": "revoked",
                    "encrypted_refresh_token": None,
                    "token_encryption_nonce": None,
                    "oauth_state": None,
                    "oauth_state_expires": None,
                    "updated_at": datetime.utcnow(),
                    "error_message": "Déconnexion manuelle"
                }
            }
        )
        
        logger.info(f"✅ Disconnected {result.modified_count} Amazon connections")
        
        return {
            "status": "revoked",
            "message": f"{result.modified_count} connexion(s) Amazon déconnectée(s)",
            "disconnected_count": result.modified_count
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to disconnect Amazon connections: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la déconnexion"
        )

# 5. GET /api/amazon/marketplaces - Liste des marketplaces
@amazon_integration_router.get("/marketplaces")
async def get_supported_marketplaces():
    """
    Retourne la liste des marketplaces Amazon supportés
    """
    return {
        "marketplaces": [marketplace.dict() for marketplace in SUPPORTED_MARKETPLACES],
        "total_count": len(SUPPORTED_MARKETPLACES)
    }

# Fonctions utilitaires
def _generate_success_response() -> RedirectResponse:
    """Génère la redirection de succès"""
    frontend_url = os.environ.get('APP_BASE_URL', 'https://app.ecomsimply.com')
    success_url = f"{frontend_url}/?amazon=connected"
    return RedirectResponse(url=success_url, status_code=302)

def _generate_error_response(error_type: str, error_message: str) -> RedirectResponse:
    """Génère la redirection d'erreur"""
    frontend_url = os.environ.get('APP_BASE_URL', 'https://app.ecomsimply.com')
    error_url = f"{frontend_url}/?amazon_error={error_type}&message={error_message}"
    return RedirectResponse(url=error_url, status_code=302)

async def cleanup_expired_oauth_states(db):
    """Nettoie les états OAuth expirés (tâche d'arrière-plan)"""
    try:
        result = await db.amazon_connections.delete_many({
            "status": "pending",
            "oauth_state_expires": {"$lt": datetime.utcnow()}
        })
        
        if result.deleted_count > 0:
            logger.info(f"🧹 Cleaned up {result.deleted_count} expired OAuth states")
            
    except Exception as e:
        logger.error(f"❌ Failed to cleanup expired states: {str(e)}")