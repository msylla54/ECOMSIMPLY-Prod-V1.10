# Amazon SP-API Connection Management Service
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.amazon_spapi import (
    AmazonConnection, ConnectionStatus, SPAPITokenData,
    SPAPIRegion, SPAPIConnectionStatus
)
from services.amazon_encryption_service import AmazonTokenEncryptionService
from services.amazon_oauth_service import AmazonOAuthService

logger = logging.getLogger(__name__)

class AmazonConnectionService:
    """
    Service for managing Amazon SP-API connections with multi-tenant support
    
    Features:
    - Multi-tenant connection isolation
    - Encrypted token storage
    - Connection lifecycle management  
    - Automatic token refresh
    - Health monitoring
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        """Initialize connection service"""
        self.db = database
        self.connections_collection = database.amazon_connections
        self.encryption_service = AmazonTokenEncryptionService()
        self.oauth_service = AmazonOAuthService()
        
        logger.info("✅ Amazon Connection Service initialized")
    
    async def create_connection(
        self,
        user_id: str,
        marketplace_id: str,
        region: SPAPIRegion = SPAPIRegion.EU
    ) -> Dict[str, Any]:
        """
        Create new SP-API connection for user
        
        Args:
            user_id: ECOMSIMPLY user identifier
            marketplace_id: Amazon marketplace ID
            region: Amazon region
            
        Returns:
            Dictionary with connection_id, authorization_url, state, expires_at
        """
        try:
            # Create new connection record
            connection = AmazonConnection(
                user_id=user_id,
                marketplace_id=marketplace_id,
                region=region,
                seller_id="",  # Will be set during OAuth callback
                encrypted_refresh_token="",  # Will be set during OAuth callback
                token_encryption_nonce="",  # Will be set during OAuth callback
                encryption_key_id="",  # Will be set during OAuth callback
                status=ConnectionStatus.PENDING
            )
            
            # Generate OAuth state for CSRF protection
            oauth_state = self.oauth_service.generate_oauth_state(user_id, connection.id)
            connection.oauth_state = oauth_state
            connection.oauth_state_expires = datetime.utcnow() + timedelta(hours=1)
            
            # Store connection in database
            connection_dict = connection.dict()
            await self.connections_collection.insert_one(connection_dict)
            
            # Build authorization URL
            auth_url = self.oauth_service.build_authorization_url(
                state=oauth_state,
                marketplace_id=marketplace_id,
                region=region
            )
            
            logger.info(f"🔗 Connection created for user {user_id[:8]}*** marketplace {marketplace_id}")
            
            return {
                "connection_id": connection.id,
                "authorization_url": auth_url,
                "state": oauth_state,
                "expires_at": connection.oauth_state_expires
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create connection: {type(e).__name__}")
            raise RuntimeError("Failed to create Amazon connection") from e
    
    async def handle_oauth_callback(
        self,
        state: str,
        authorization_code: str,
        selling_partner_id: str
    ) -> bool:
        """
        Gestion complète du callback OAuth avec génération automatique du refresh token
        
        Processus:
        1. Trouver la connexion par OAuth state
        2. Vérifier state (protection CSRF)
        3. Échanger code contre access_token + refresh_token via LWA
        4. Chiffrer et stocker le refresh token en base (AES-GCM + KMS)
        5. Mettre à jour le statut de connexion
        
        Args:
            state: Paramètre OAuth state pour validation CSRF
            authorization_code: Code d'autorisation OAuth depuis Amazon
            selling_partner_id: ID du vendeur Amazon
            
        Returns:
            True si le callback est traité avec succès et refresh token généré
        """
        try:
            logger.info(f"🔄 Processing OAuth callback for seller {selling_partner_id}")
            
            # 1. Trouver la connexion par OAuth state
            connection_doc = await self.connections_collection.find_one({
                "oauth_state": state,
                "status": ConnectionStatus.PENDING,
                "oauth_state_expires": {"$gt": datetime.utcnow()}
            })
            
            if not connection_doc:
                logger.error("❌ No matching pending connection found for OAuth state")
                return False
            
            connection = AmazonConnection(**connection_doc)
            logger.info(f"✅ Found pending connection {connection.id} for user {connection.user_id}")
            
            # 2. Vérifier OAuth state (protection CSRF)
            if not self.oauth_service.verify_oauth_state(
                state, connection.user_id, connection.id
            ):
                logger.error("❌ OAuth state CSRF verification failed")
                await self._mark_connection_error(connection.id, "CSRF validation failed")
                return False
            
            logger.info("✅ OAuth state CSRF verification successful")
            
            # 3. Échanger code contre access_token + refresh_token via LWA
            try:
                token_data = await self.oauth_service.exchange_code_for_tokens(
                    authorization_code=authorization_code,
                    region=connection.region
                )
                logger.info("✅ OAuth token exchange successful - refresh token automatically generated")
                
                # Vérifier que le refresh token est présent
                if not token_data.refresh_token:
                    logger.error("❌ No refresh token received from Amazon LWA")
                    await self._mark_connection_error(connection.id, "Missing refresh token")
                    return False
                
            except Exception as e:
                logger.error(f"❌ Token exchange failed: {str(e)}")
                await self._mark_connection_error(connection.id, f"Token exchange failed: {str(e)}")
                return False
            
            # 4. Chiffrer et stocker le refresh token en base (AES-GCM + KMS)
            try:
                encrypted_data, nonce = await self.encryption_service.encrypt_token_data(
                    token_data=token_data.dict(),
                    user_id=connection.user_id,
                    connection_id=connection.id
                )
                logger.info("✅ Refresh token encrypted and secured with AES-GCM + KMS")
                
            except Exception as e:
                logger.error(f"❌ Token encryption failed: {str(e)}")
                await self._mark_connection_error(connection.id, f"Token encryption failed: {str(e)}")
                return False
            
            # 5. Mettre à jour la connexion avec tokens et informations vendeur
            update_data = {
                "seller_id": selling_partner_id,
                "encrypted_refresh_token": encrypted_data,
                "token_encryption_nonce": nonce,
                "encryption_key_id": self.encryption_service.kms_key_id,
                "status": ConnectionStatus.ACTIVE,
                "connected_at": datetime.utcnow(),
                "oauth_state": None,  # Effacer le state après utilisation
                "oauth_state_expires": None,
                "error_message": None,  # Effacer les erreurs précédentes
                "updated_at": datetime.utcnow()
            }
            
            result = await self.connections_collection.update_one(
                {"id": connection.id},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                logger.error("❌ Failed to update connection in database")
                return False
            
            logger.info(f"✅ OAuth callback completed successfully for connection {connection.id}")
            logger.info(f"✅ Refresh token automatically generated and stored securely")
            logger.info(f"✅ Connection {connection.id} activated for seller {selling_partner_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ OAuth callback handling failed: {type(e).__name__}: {str(e)}")
            # Tenter de marquer la connexion en erreur si possible
            try:
                if 'connection' in locals():
                    await self._mark_connection_error(connection.id, f"Callback processing failed: {str(e)}")
            except:
                pass  # Ignorer les erreurs de nettoyage
            return False
    
    async def _mark_connection_error(self, connection_id: str, error_message: str):
        """Marquer une connexion en erreur avec un message"""
        try:
            await self.connections_collection.update_one(
                {"id": connection_id},
                {"$set": {
                    "status": ConnectionStatus.ERROR,
                    "error_message": error_message,
                    "updated_at": datetime.utcnow()
                }}
            )
            logger.info(f"🔴 Connection {connection_id} marked as error: {error_message}")
        except Exception as e:
            logger.error(f"❌ Failed to mark connection as error: {str(e)}")
    
    async def get_user_connections(self, user_id: str) -> List[SPAPIConnectionStatus]:
        """
        Get all connections for a user
        
        Args:
            user_id: ECOMSIMPLY user identifier
            
        Returns:
            List of connection status objects
        """
        try:
            # Query connections for user
            cursor = self.connections_collection.find({"user_id": user_id})
            connections_data = await cursor.to_list(length=100)
            
            connection_statuses = []
            for conn_data in connections_data:
                connection = AmazonConnection(**conn_data)
                
                status = SPAPIConnectionStatus(
                    connection_id=connection.id,
                    status=connection.status,
                    marketplace_id=connection.marketplace_id,
                    seller_id=connection.seller_id,
                    region=connection.region,
                    connected_at=connection.connected_at if connection.status == ConnectionStatus.ACTIVE else None,
                    last_used_at=connection.last_used_at,
                    error_message=connection.error_message
                )
                
                connection_statuses.append(status)
            
            logger.info(f"📋 Retrieved {len(connection_statuses)} connections for user {user_id[:8]}***")
            return connection_statuses
            
        except Exception as e:
            logger.error(f"❌ Failed to get user connections: {type(e).__name__}")
            return []
    
    async def get_active_connection(
        self,
        user_id: str,
        marketplace_id: Optional[str] = None
    ) -> Optional[AmazonConnection]:
        """
        Get active connection for user and marketplace
        
        Args:
            user_id: ECOMSIMPLY user identifier
            marketplace_id: Specific marketplace (optional)
            
        Returns:
            Active connection or None
        """
        try:
            query = {
                "user_id": user_id,
                "status": ConnectionStatus.ACTIVE
            }
            
            if marketplace_id:
                query["marketplace_id"] = marketplace_id
            
            connection_doc = await self.connections_collection.find_one(
                query,
                sort=[("created_at", -1)]  # Get most recent
            )
            
            if connection_doc:
                connection = AmazonConnection(**connection_doc)
                logger.info(f"🔍 Found active connection {connection.id} for user {user_id[:8]}***")
                return connection
            
            logger.info(f"❌ No active connection found for user {user_id[:8]}***")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get active connection: {type(e).__name__}")
            return None
    
    async def get_valid_access_token(self, connection: AmazonConnection) -> Optional[str]:
        """
        Get valid access token for connection, refreshing if necessary
        
        Args:
            connection: Amazon connection object
            
        Returns:
            Valid access token or None if failed
        """
        try:
            # Decrypt token data
            token_data_dict = await self.encryption_service.decrypt_token_data(
                encrypted_data=connection.encrypted_refresh_token,
                nonce_b64=connection.token_encryption_nonce,
                user_id=connection.user_id,
                connection_id=connection.id
            )
            
            token_data = SPAPITokenData(**token_data_dict)
            
            # Check if access token is expired (with 5 minute buffer)
            if datetime.utcnow() + timedelta(minutes=5) >= token_data.expires_at:
                logger.info(f"🔄 Access token expired, refreshing for connection {connection.id}")
                
                # Refresh access token
                new_token_data = await self.oauth_service.refresh_access_token(
                    refresh_token=token_data.refresh_token,
                    region=connection.region
                )
                
                # Re-encrypt and store updated tokens
                encrypted_data, nonce = await self.encryption_service.encrypt_token_data(
                    token_data=new_token_data.dict(),
                    user_id=connection.user_id,
                    connection_id=connection.id
                )
                
                # Update connection in database
                await self.connections_collection.update_one(
                    {"id": connection.id},
                    {
                        "$set": {
                            "encrypted_refresh_token": encrypted_data,
                            "token_encryption_nonce": nonce,
                            "last_used_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                token_data = new_token_data
            
            # Update last used timestamp
            await self.connections_collection.update_one(
                {"id": connection.id},
                {"$set": {"last_used_at": datetime.utcnow()}}
            )
            
            logger.info(f"🔑 Valid access token retrieved for connection {connection.id}")
            return token_data.access_token
            
        except Exception as e:
            logger.error(f"❌ Failed to get valid access token: {type(e).__name__}")
            
            # Mark connection as error
            await self.connections_collection.update_one(
                {"id": connection.id},
                {
                    "$set": {
                        "status": ConnectionStatus.ERROR,
                        "error_message": f"Token retrieval failed: {type(e).__name__}",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return None
    
    async def disconnect_connection(self, connection_id: str, user_id: str) -> bool:
        """
        Disconnect and revoke SP-API connection
        
        Args:
            connection_id: Connection identifier
            user_id: User identifier (for security)
            
        Returns:
            True if disconnection successful
        """
        try:
            # Update connection status to revoked
            result = await self.connections_collection.update_one(
                {
                    "id": connection_id,
                    "user_id": user_id  # Ensure user owns the connection
                },
                {
                    "$set": {
                        "status": ConnectionStatus.REVOKED,
                        "encrypted_refresh_token": "",
                        "token_encryption_nonce": "",
                        "error_message": "Connection revoked by user",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"🔌 Connection {connection_id} disconnected for user {user_id[:8]}***")
                return True
            else:
                logger.warning(f"❌ Connection {connection_id} not found or not owned by user")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to disconnect connection: {type(e).__name__}")
            return False
    
    async def cleanup_expired_states(self) -> int:
        """
        Clean up expired OAuth states
        
        Returns:
            Number of expired states cleaned
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=2)
            
            result = await self.connections_collection.update_many(
                {
                    "oauth_state_expires": {"$lt": cutoff_time},
                    "status": ConnectionStatus.PENDING
                },
                {
                    "$set": {
                        "status": ConnectionStatus.EXPIRED,
                        "oauth_state": None,
                        "oauth_state_expires": None,
                        "error_message": "OAuth authorization expired",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"🧹 Cleaned up {result.modified_count} expired OAuth states")
            
            return result.modified_count
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup expired states: {type(e).__name__}")
            return 0
    
    async def health_check_connections(self) -> Dict[str, Any]:
        """
        Perform health check on active connections
        
        Returns:
            Health check summary
        """
        try:
            # Count connections by status
            pipeline = [
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]
            
            cursor = self.connections_collection.aggregate(pipeline)
            status_counts = {doc["_id"]: doc["count"] async for doc in cursor}
            
            # Test KMS access
            kms_healthy = self.encryption_service.test_kms_access()
            
            health_summary = {
                "total_connections": sum(status_counts.values()),
                "status_breakdown": status_counts,
                "kms_access": kms_healthy,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"💚 Health check completed: {health_summary['total_connections']} total connections")
            return health_summary
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {type(e).__name__}")
            return {
                "error": "Health check failed",
                "timestamp": datetime.utcnow().isoformat()
            }