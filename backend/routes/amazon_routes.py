# Amazon SP-API FastAPI Routes
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
from typing import List, Optional
import logging
import os
import secrets
from datetime import datetime, timedelta

from models.amazon_spapi import (
    SPAPIConnectionRequest, SPAPIConnectionResponse, SPAPIConnectionStatus,
    SPAPICallbackData, SPAPIRegion, ConnectionStatus
)
from services.amazon_connection_service import AmazonConnectionService

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Router setup
amazon_router = APIRouter(prefix="/api/amazon", tags=["Amazon SP-API Integration"])

# Dependency to get database
async def get_database():
    """Get database dependency - implement based on your DB setup"""
    from motor.motor_asyncio import AsyncIOMotorClient
    import os
    
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db_name = os.environ.get('DB_NAME', 'ecomsimply_production')
    return client[db_name]

# Dependency to check Amazon service availability
def get_amazon_service_status():
    """Check if Amazon SP-API service is available with required credentials"""
    required_env_vars = ['AMAZON_LWA_CLIENT_ID', 'AMAZON_LWA_CLIENT_SECRET', 'AMAZON_APP_ID']
    missing_vars = [var for var in required_env_vars if not os.environ.get(var) or os.environ.get(var).startswith('demo-')]
    
    return {
        'available': len(missing_vars) == 0,
        'missing_vars': missing_vars,
        'demo_mode': len(missing_vars) > 0
    }

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token - implement based on your auth system"""
    import jwt
    import os
    
    try:
        # Decode JWT token
        token = credentials.credentials
        secret = os.environ.get('JWT_SECRET')
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        user_id = payload.get('user_id')
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return user_id
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")

# Quick connection endpoint for UI button
@amazon_router.get("/connect")
async def get_amazon_connect_url(
    marketplace_id: str = "A13V1IB3VIYZZH",
    current_user: str = Depends(get_current_user),
    db=Depends(get_database),
    amazon_status=Depends(get_amazon_service_status)
):
    """
    GET endpoint to initiate Amazon connection for UI button
    
    This endpoint provides a simple GET interface for the Amazon button:
    1. Creates connection with default marketplace (France)
    2. Returns authorization URL for immediate redirect
    3. Compatible with simple button click actions
    
    Query Parameters:
    - marketplace_id: Optional marketplace ID (defaults to France)
    """
    try:
        logger.info(f"🔗 GET Amazon connect for user {current_user[:8]}*** marketplace {marketplace_id}")
        
        # Check if Amazon service is available
        if amazon_status['demo_mode']:
            logger.warning(f"⚠️ Amazon credentials not configured: {amazon_status['missing_vars']}")
            # Return demo response for development
            return {
                "authorization_url": f"https://sellercentral.amazon.com/apps/authorize/consent?state=demo-{secrets.token_hex(8)}&client_id=demo",
                "connection_id": f"demo-connection-{secrets.token_hex(8)}",
                "marketplace_id": marketplace_id,
                "region": "eu",
                "demo_mode": True,
                "message": "Mode démo Amazon - configurez AMAZON_* env vars pour production"
            }
        
        # Map marketplace to region
        marketplace_regions = {
            'A13V1IB3VIYZZH': 'eu',  # France
            'A1PA6795UKMFR9': 'eu',  # Germany
            'A1RKKUPIHCS9HS': 'eu',  # Spain
            'APJ6JRA9NG5V4': 'eu',   # Italy
            'A1F83G8C2ARO7P': 'eu',  # UK
            'ATVPDKIKX0DER': 'na',   # US
            'A2EUQ1WTGCTBG2': 'na',  # Canada
            'A1VC38T7YXB528': 'fe'   # Japan
        }
        
        region = marketplace_regions.get(marketplace_id, 'eu')
        
        # Initialize connection service (only if credentials available)
        connection_service = AmazonConnectionService(db)
        
        # Create new connection
        connection_result = await connection_service.create_connection(
            user_id=current_user,
            marketplace_id=marketplace_id,
            region=region
        )
        
        logger.info(f"✅ GET connection created: {connection_result['connection_id']}")
        
        # Return authorization URL for redirect
        return {
            "authorization_url": connection_result["authorization_url"],
            "connection_id": connection_result["connection_id"],
            "marketplace_id": marketplace_id,
            "region": region
        }
        
    except Exception as e:
        logger.error(f"❌ GET connect failed: {type(e).__name__}")
        
        # Return demo response as fallback instead of 500 error
        logger.info("🔧 Mode démo Amazon - Returning demo response due to service failure")
        return {
            "authorization_url": f"https://sellercentral.amazon.com/apps/authorize/consent?state=demo-fallback-{secrets.token_hex(8)}&client_id=demo",
            "connection_id": f"demo-connection-fallback-{secrets.token_hex(8)}",
            "marketplace_id": marketplace_id,
            "region": "eu",
            "demo_mode": True,
            "message": "Mode démo Amazon - service temporairement indisponible"
        }

# Connection status endpoint  
@amazon_router.get("/status")
async def get_amazon_status(
    current_user: str = Depends(get_current_user),
    db=Depends(get_database),
    amazon_status=Depends(get_amazon_service_status)
):
    """
    Get Amazon connection status for current user
    
    Returns overall connection status:
    - connected: User has at least one active connection
    - revoked: User had connections but all are revoked
    - none: User never connected or no connections found
    
    Used by UI to determine button state
    """
    try:
        logger.info(f"🔍 Getting Amazon status for user {current_user[:8]}***")
        
        # Check if Amazon service is available
        if amazon_status['demo_mode']:
            logger.warning(f"⚠️ Amazon service in demo mode: {amazon_status['missing_vars']}")
            return {
                "status": "none",
                "message": "Mode démo Amazon - aucune connexion réelle disponible",
                "connections_count": 0,
                "demo_mode": True,
                "missing_vars": amazon_status['missing_vars']
            }
        
        connection_service = AmazonConnectionService(db)
        
        # Get user connections
        connections = await connection_service.get_user_connections(current_user)
        
        if not connections:
            return {
                "status": "none",
                "message": "Aucune connexion Amazon trouvée",
                "connections_count": 0
            }
        
        # Check if any connection is active
        active_connections = [conn for conn in connections if conn.status == 'active']
        
        if active_connections:
            active_conn = active_connections[0]  # Get first active connection
            return {
                "status": "connected",
                "message": "Connexion Amazon active",
                "connections_count": len(active_connections),
                "active_connection": {
                    "connection_id": active_conn.connection_id,
                    "marketplace_id": active_conn.marketplace_id,
                    "seller_id": active_conn.seller_id,
                    "region": active_conn.region,
                    "connected_at": active_conn.connected_at
                }
            }
        else:
            # Check if any are revoked/expired
            revoked_connections = [conn for conn in connections if conn.status in ['revoked', 'expired', 'error']]
            
            if revoked_connections:
                return {
                    "status": "revoked", 
                    "message": "Connexions Amazon expirées ou révoquées",
                    "connections_count": len(connections)
                }
            else:
                return {
                    "status": "pending",
                    "message": "Connexions Amazon en attente", 
                    "connections_count": len(connections)
                }
        
    except Exception as e:
        logger.error(f"❌ Failed to get Amazon status: {type(e).__name__}")
        
        # Return demo status as fallback instead of 500 error
        logger.info("🔧 Mode démo Amazon - Returning demo status due to service failure")
        return {
            "status": "none",
            "message": "Mode démo Amazon - service temporairement indisponible",
            "connections_count": 0,
            "demo_mode": True,
            "service_error": True
        }

# Connection initiation endpoint
@amazon_router.post("/connect", response_model=SPAPIConnectionResponse)
async def initiate_amazon_connection(
    request: SPAPIConnectionRequest,
    current_user: str = Depends(get_current_user),
    db=Depends(get_database),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Initiate Amazon SP-API OAuth connection
    
    This endpoint:
    1. Creates a new pending connection record
    2. Generates secure OAuth state for CSRF protection  
    3. Returns Amazon authorization URL
    4. Schedules cleanup of expired states
    
    Security:
    - Requires valid JWT authentication
    - CSRF protection via OAuth state parameter
    - Multi-tenant isolation by user_id
    """
    try:
        logger.info(f"🔗 Initiating Amazon connection for user {current_user[:8]}*** marketplace {request.marketplace_id}")
        
        # Check if Amazon credentials are configured
        required_env_vars = ['AMAZON_LWA_CLIENT_ID', 'AMAZON_LWA_CLIENT_SECRET', 'AMAZON_APP_ID']
        missing_vars = [var for var in required_env_vars if not os.environ.get(var) or os.environ.get(var).startswith('demo-')]
        
        if missing_vars:
            logger.warning(f"⚠️ Amazon credentials not configured: {missing_vars}")
            # Return demo/mock response for development
            demo_response = SPAPIConnectionResponse(
                connection_id=f"demo-connection-{secrets.token_hex(8)}",
                authorization_url="https://sellercentral.amazon.com/apps/authorize/consent?state=demo&client_id=demo",
                state=f"demo-state-{secrets.token_hex(16)}",
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            logger.info("🔧 Mode démo Amazon - Returning demo Amazon connection (configure AMAZON_* env vars for production)")
            return demo_response
        
        # Initialize connection service
        connection_service = AmazonConnectionService(db)
        
        # Create new connection
        connection_result = await connection_service.create_connection(
            user_id=current_user,
            marketplace_id=request.marketplace_id,
            region=request.region
        )
        
        # Schedule background cleanup of expired states
        background_tasks.add_task(connection_service.cleanup_expired_states)
        
        # Return connection details
        response = SPAPIConnectionResponse(
            connection_id=connection_result["connection_id"],
            authorization_url=connection_result["authorization_url"],
            state=connection_result["state"],
            expires_at=connection_result["expires_at"]
        )
        
        logger.info(f"✅ Connection initiated successfully: {response.connection_id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Connection initiation failed: {type(e).__name__}")
        
        # Return demo response as fallback instead of 500 error
        logger.info("🔧 Mode démo Amazon - Returning demo response due to service failure")
        demo_response = SPAPIConnectionResponse(
            connection_id=f"demo-connection-fallback-{secrets.token_hex(8)}",
            authorization_url=f"https://sellercentral.amazon.com/apps/authorize/consent?state=demo-fallback-{secrets.token_hex(8)}&client_id=demo",
            state=f"demo-state-fallback-{secrets.token_hex(16)}",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        return demo_response

# OAuth callback endpoint avec génération automatique du refresh token
@amazon_router.get("/callback")
async def handle_amazon_oauth_callback(
    request: Request,
    state: str,
    selling_partner_id: str,
    spapi_oauth_code: str,
    mws_auth_token: Optional[str] = None,
    popup: Optional[str] = None,
    db=Depends(get_database)
):
    """
    Gestion complète du callback OAuth Amazon avec génération automatique du refresh token
    
    Processus:
    1. Recevoir code + state depuis Amazon
    2. Vérifier state (CSRF protection)
    3. Échanger code contre access_token + refresh_token via LWA
    4. Stocker le refresh token en base lié à l'utilisateur/tenant (chiffré AES-GCM + KMS)
    5. Retourner redirection 302 ou page HTML avec postMessage
    
    Sécurité:
    - Validation OAuth state contre CSRF
    - Tokens jamais loggés ou exposés
    - Chiffrement AES-GCM avec AWS KMS
    - Isolation multi-tenant
    """
    try:
        logger.info(f"📞 Processing Amazon OAuth callback with state {state[:20]}*** popup={popup}")
        
        # 1. Recevoir et valider les paramètres
        if not state or not selling_partner_id or not spapi_oauth_code:
            logger.error("❌ Missing required OAuth callback parameters")
            return _generate_error_response(
                popup, "missing_parameters", 
                "Paramètres OAuth manquants"
            )
        
        # 2. Initialiser le service de connexion
        connection_service = AmazonConnectionService(db)
        
        # 3. Gérer le callback OAuth avec vérification CSRF et génération automatique des tokens
        # Le processus inclut: exchange_code_for_tokens → refresh_token automatique → chiffrement AES-GCM
        callback_success = await connection_service.handle_oauth_callback(
            state=state,
            authorization_code=spapi_oauth_code,
            selling_partner_id=selling_partner_id
        )
        
        if callback_success:
            logger.info("✅ OAuth callback successful - refresh token automatically generated and stored")
            
            # 4. Retourner la réponse selon le mode
            if popup == "true":
                # Mode popup : page HTML avec postMessage
                return _generate_popup_success_response()
            else:
                # Mode redirect : redirection 302
                return _generate_redirect_success_response()
        else:
            logger.error("❌ OAuth callback processing failed")
            return _generate_error_response(
                popup, "callback_failed", 
                "Échec du traitement OAuth"
            )
            
    except ValueError as e:
        logger.error(f"❌ OAuth callback validation error: {str(e)}")
        return _generate_error_response(
            popup, "validation_error", 
            "Erreur de validation OAuth"
        )
    except Exception as e:
        logger.error(f"❌ OAuth callback internal error: {type(e).__name__}")
        return _generate_error_response(
            popup, "internal_error", 
            "Erreur interne du serveur"
        )

def _generate_popup_success_response() -> HTMLResponse:
    """Génère la réponse HTML pour le mode popup avec postMessage"""
    frontend_url = os.environ.get('APP_BASE_URL', 'https://app.ecomsimply.com')
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Amazon Connection Success</title>
        <meta charset="UTF-8">
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                text-align: center; 
                padding: 60px 40px; 
                background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                margin: 0;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
            }}
            .success-container {{
                background: white;
                padding: 40px;
                border-radius: 16px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                max-width: 400px;
                width: 100%;
            }}
            .success-icon {{ 
                font-size: 48px; 
                margin-bottom: 20px; 
                animation: bounce 0.6s ease-in-out;
            }}
            .success-title {{ 
                color: #059669; 
                font-size: 24px; 
                font-weight: 600;
                margin-bottom: 16px; 
            }}
            .success-message {{ 
                color: #374151; 
                font-size: 16px; 
                line-height: 1.5;
            }}
            @keyframes bounce {{
                0%, 20%, 60%, 100% {{ transform: translateY(0); }}
                40% {{ transform: translateY(-10px); }}
                80% {{ transform: translateY(-5px); }}
            }}
        </style>
    </head>
    <body>
        <div class="success-container">
            <div class="success-icon">✅</div>
            <div class="success-title">Amazon Connecté avec Succès!</div>
            <div class="success-message">
                Votre compte Amazon a été connecté et vos tokens ont été générés automatiquement.
                <br><br>
                Fermeture automatique et mise à jour du dashboard...
            </div>
        </div>
        <script>
            // Envoyer le message de succès à la fenêtre parent
            if (window.opener) {{
                window.opener.postMessage({{
                    type: 'AMAZON_CONNECTED',
                    success: true,
                    message: 'Amazon connection successful with automatic refresh token generation',
                    timestamp: new Date().toISOString()
                }}, '{frontend_url}');
                
                // Fermer la popup après un court délai pour que l'utilisateur voie le message
                setTimeout(() => {{
                    window.close();
                }}, 2000);
            }} else {{
                // Fallback: redirection si pas d'opener
                setTimeout(() => {{
                    window.location.href = '{frontend_url}/?amazon_connected=true&tab=stores';
                }}, 2000);
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

def _generate_redirect_success_response() -> RedirectResponse:
    """Génère la redirection 302 pour le mode redirect"""
    frontend_url = os.environ.get('APP_BASE_URL', 'https://app.ecomsimply.com')
    success_url = f"{frontend_url}/dashboard?amazon=connected"
    return RedirectResponse(url=success_url, status_code=302)

def _generate_error_response(popup: Optional[str], error_type: str, error_message: str):
    """Génère la réponse d'erreur selon le mode"""
    frontend_url = os.environ.get('APP_BASE_URL', 'https://app.ecomsimply.com')
    
    if popup == "true":
        # Mode popup : page HTML avec postMessage d'erreur
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Amazon Connection Error</title>
            <meta charset="UTF-8">
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    text-align: center; 
                    padding: 60px 40px; 
                    background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
                    margin: 0;
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                }}
                .error-container {{
                    background: white;
                    padding: 40px;
                    border-radius: 16px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                    max-width: 400px;
                    width: 100%;
                }}
                .error-icon {{ 
                    font-size: 48px; 
                    margin-bottom: 20px; 
                }}
                .error-title {{ 
                    color: #dc2626; 
                    font-size: 24px; 
                    font-weight: 600;
                    margin-bottom: 16px; 
                }}
                .error-message {{ 
                    color: #374151; 
                    font-size: 16px; 
                    line-height: 1.5;
                }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <div class="error-icon">❌</div>
                <div class="error-title">Erreur de Connexion Amazon</div>
                <div class="error-message">
                    {error_message}
                    <br><br>
                    Veuillez réessayer ou contacter le support si le problème persiste.
                </div>
            </div>
            <script>
                // Envoyer le message d'erreur à la fenêtre parent
                if (window.opener) {{
                    window.opener.postMessage({{
                        type: 'AMAZON_CONNECTION_ERROR',
                        success: false,
                        error: '{error_type}',
                        message: '{error_message}',
                        timestamp: new Date().toISOString()
                    }}, '{frontend_url}');
                    
                    // Fermer la popup après un court délai
                    setTimeout(() => {{
                        window.close();
                    }}, 3000);
                }} else {{
                    // Fallback: redirection si pas d'opener
                    setTimeout(() => {{
                        window.location.href = '{frontend_url}/?amazon_error={error_type}&tab=stores';
                    }}, 3000);
                }}
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    else:
        # Mode redirect : redirection 302 avec paramètre d'erreur
        error_url = f"{frontend_url}/dashboard?amazon_error={error_type}"
        return RedirectResponse(url=error_url, status_code=302)

# Get user connections
@amazon_router.get("/connections", response_model=List[SPAPIConnectionStatus])
async def get_amazon_connections(
    current_user: str = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Get all Amazon connections for current user
    
    Returns:
    - List of connection status objects
    - Connection metadata (never includes tokens)
    - Multi-tenant isolated by user_id
    
    Security:
    - Requires valid JWT authentication
    - Returns only connections owned by requesting user
    - No sensitive token data in response
    """
    try:
        logger.info(f"📋 Retrieving Amazon connections for user {current_user[:8]}***")
        
        # Initialize connection service
        connection_service = AmazonConnectionService(db)
        
        # Get user connections
        connections = await connection_service.get_user_connections(current_user)
        
        logger.info(f"✅ Retrieved {len(connections)} connections")
        return connections
        
    except Exception as e:
        logger.error(f"❌ Failed to retrieve connections: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve connections"
        )

# Connection status endpoint
@amazon_router.get("/connections/{connection_id}/status")
async def get_connection_status(
    connection_id: str,
    current_user: str = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Get detailed status for specific connection
    
    Security:
    - Requires valid JWT authentication
    - Returns only if user owns the connection
    - No sensitive token data in response
    """
    try:
        logger.info(f"🔍 Getting status for connection {connection_id}")
        
        connection_service = AmazonConnectionService(db)
        
        # Get connection (will return None if not owned by user)
        connection = await connection_service.get_active_connection(
            user_id=current_user
        )
        
        if not connection or connection.id != connection_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        # Return connection status
        status_response = SPAPIConnectionStatus(
            connection_id=connection.id,
            status=connection.status,
            marketplace_id=connection.marketplace_id,
            seller_id=connection.seller_id,
            region=connection.region,
            connected_at=connection.created_at if connection.status == "active" else None,
            last_used_at=connection.last_used_at,
            error_message=connection.error_message
        )
        
        return status_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get connection status: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get connection status"
        )

# Disconnect connection
@amazon_router.delete("/connections/{connection_id}")
async def disconnect_amazon_connection(
    connection_id: str,
    current_user: str = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Disconnect Amazon SP-API connection
    
    This endpoint:
    1. Validates user owns the connection
    2. Updates connection status to revoked
    3. Clears encrypted token data
    4. Returns success confirmation
    
    Security:
    - Requires valid JWT authentication
    - Only allows disconnecting user's own connections
    - Securely removes all token data
    """
    try:
        logger.info(f"🔌 Disconnecting Amazon connection {connection_id} for user {current_user[:8]}***")
        
        connection_service = AmazonConnectionService(db)
        
        # Disconnect connection
        success = await connection_service.disconnect_connection(
            connection_id=connection_id,
            user_id=current_user
        )
        
        if success:
            logger.info(f"✅ Connection {connection_id} disconnected successfully")
            return {"message": "Connection disconnected successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found or not owned by user"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to disconnect connection: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect connection"
        )

# Disconnect all user connections
@amazon_router.post("/disconnect")
async def disconnect_amazon_user_connections(
    current_user: str = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Disconnect all Amazon SP-API connections for current user
    
    This endpoint:
    1. Finds all active connections for the user
    2. Revokes and clears all encrypted token data
    3. Updates connection status to "revoked"
    4. Returns overall disconnection status
    
    Security:
    - Requires valid JWT authentication
    - Multi-tenant isolation by user_id
    - Securely removes all token data
    """
    try:
        logger.info(f"🔌 Disconnecting all Amazon connections for user {current_user[:8]}***")
        
        connection_service = AmazonConnectionService(db)
        
        # Get all user connections
        connections = await connection_service.get_user_connections(current_user)
        
        if not connections:
            logger.info(f"ℹ️ No connections found for user {current_user[:8]}***")
            return {
                "status": "revoked",
                "message": "Aucune connexion Amazon trouvée",
                "disconnected_count": 0
            }
        
        # Disconnect all active connections
        disconnected_count = 0
        for connection_status in connections:
            if connection_status.status in [ConnectionStatus.ACTIVE, ConnectionStatus.PENDING]:
                success = await connection_service.disconnect_connection(
                    connection_id=connection_status.connection_id,
                    user_id=current_user
                )
                if success:
                    disconnected_count += 1
        
        logger.info(f"✅ Disconnected {disconnected_count} connections for user {current_user[:8]}***")
        
        return {
            "status": "revoked",
            "message": f"{disconnected_count} connexion(s) Amazon déconnectée(s) avec succès",
            "disconnected_count": disconnected_count,
            "total_connections": len(connections)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to disconnect user connections: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect Amazon connections"
        )

# Health check endpoint
@amazon_router.get("/health")
async def amazon_integration_health(db=Depends(get_database)):
    """
    Health check for Amazon SP-API integration
    
    Checks:
    - Database connectivity
    - AWS KMS access
    - Connection statistics
    - Service status
    
    Public endpoint for monitoring
    """
    try:
        logger.info("💚 Performing Amazon integration health check")
        
        connection_service = AmazonConnectionService(db)
        health_data = await connection_service.health_check_connections()
        
        return {
            "status": "healthy" if health_data.get("kms_access") else "degraded",
            "service": "Amazon SP-API Integration",
            "version": "1.0.0",
            "details": health_data
        }
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {type(e).__name__}")
        return {
            "status": "unhealthy",
            "service": "Amazon SP-API Integration",
            "version": "1.0.0",
            "error": "Health check failed"
        }

# Test endpoint pour validation refresh token (development seulement)
@amazon_router.post("/test/validate-refresh-token")
async def test_validate_refresh_token(
    current_user: str = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Test endpoint pour valider la génération et l'utilisation du refresh token
    
    Ce endpoint vérifie:
    1. Présence du refresh token chiffré en base
    2. Capacité à déchiffrer le refresh token
    3. Utilisation automatique pour rafraîchir l'access token
    4. Re-chiffrement et stockage des nouveaux tokens
    
    Sécurité:
    - Requiert une authentification JWT valide
    - Disponible uniquement en développement
    - Ne retourne jamais les tokens en clair
    - Isolation multi-tenant par user_id
    """
    try:
        # Vérifier l'environnement de développement
        if os.environ.get('ENVIRONMENT') != 'development':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Test endpoints available only in development"
            )
        
        logger.info(f"🧪 Testing refresh token functionality for user {current_user[:8]}***")
        
        connection_service = AmazonConnectionService(db)
        
        # Obtenir la connexion active
        connection = await connection_service.get_active_connection(current_user)
        
        if not connection:
            return {
                "success": False,
                "error": "no_active_connection",
                "message": "Aucune connexion Amazon active trouvée"
            }
        
        # Vérifier la présence du refresh token chiffré
        if not connection.encrypted_refresh_token or not connection.token_encryption_nonce:
            return {
                "success": False,
                "error": "missing_encrypted_tokens",
                "message": "Refresh token chiffré manquant en base",
                "connection_id": connection.id
            }
        
        # Tester le déchiffrement et l'utilisation du refresh token
        try:
            access_token = await connection_service.get_valid_access_token(connection)
            
            if access_token:
                # Récupérer les informations de connexion mises à jour
                updated_connection = await connection_service.get_active_connection(current_user)
                
                return {
                    "success": True,
                    "message": "Refresh token généré et fonctionnel",
                    "details": {
                        "connection_id": connection.id,
                        "seller_id": connection.seller_id,
                        "marketplace_id": connection.marketplace_id,
                        "region": connection.region,
                        "encryption_key_id": connection.encryption_key_id,
                        "connected_at": connection.connected_at.isoformat() if connection.connected_at else None,
                        "last_used_at": updated_connection.last_used_at.isoformat() if updated_connection and updated_connection.last_used_at else None,
                        "token_features": {
                            "refresh_token_present": bool(connection.encrypted_refresh_token),
                            "encryption_nonce_present": bool(connection.token_encryption_nonce),
                            "kms_encryption": bool(connection.encryption_key_id),
                            "access_token_retrieved": bool(access_token),
                            "automatic_refresh_working": True
                        }
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "token_retrieval_failed",
                    "message": "Échec de récupération de l'access token",
                    "connection_id": connection.id
                }
                
        except Exception as token_error:
            logger.error(f"❌ Refresh token test failed: {str(token_error)}")
            return {
                "success": False,
                "error": "refresh_token_error",
                "message": f"Erreur lors du test du refresh token: {str(token_error)}",
                "connection_id": connection.id
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Refresh token validation test failed: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Test de validation refresh token échoué"
        )