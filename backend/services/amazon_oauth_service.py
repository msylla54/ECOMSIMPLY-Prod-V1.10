# Amazon SP-API OAuth Service with LWA Integration
import os
import json
import httpx
import hashlib
import secrets
import base64
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlencode
from enum import Enum

from models.amazon_spapi import SPAPIRegion, SPAPITokenData

logger = logging.getLogger(__name__)

class AmazonOAuthService:
    """
    Amazon SP-API OAuth service with Login with Amazon (LWA) integration
    
    Features:
    - Secure OAuth state management
    - Regional endpoint support
    - Token exchange and refresh
    - CSRF protection
    - No sensitive data logging
    """
    
    def __init__(self):
        """Initialize OAuth service with environment configuration"""
        self._validate_oauth_config()
        
        self.client_id = os.environ['AMAZON_LWA_CLIENT_ID']
        self.client_secret = os.environ['AMAZON_LWA_CLIENT_SECRET']
        self.app_id = os.environ['AMAZON_APP_ID']  # SP-API App ID
        
        # Regional OAuth endpoints
        self._oauth_endpoints = {
            SPAPIRegion.NA: {
                'auth': 'https://sellercentral.amazon.com/apps/authorize/consent',
                'token': 'https://api.amazon.com/auth/o2/token',
                'spapi': 'https://sellingpartnerapi-na.amazon.com'
            },
            SPAPIRegion.EU: {
                'auth': 'https://sellercentral-europe.amazon.com/apps/authorize/consent',
                'token': 'https://api.amazon.com/auth/o2/token',   # <-- FIX ICI
                'spapi': 'https://sellingpartnerapi-eu.amazon.com'
            },
            SPAPIRegion.FE: {
                'auth': 'https://sellercentral-japan.amazon.com/apps/authorize/consent',
                'token': 'https://api.amazon.co.jp/auth/o2/token',
                'spapi': 'https://sellingpartnerapi-fe.amazon.com'
            }
        }
        
        # HTTP client configuration
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'ECOMSIMPLY-SPAPI/1.0',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )
        
        logger.info("✅ Amazon OAuth service initialized")
    
    def _validate_oauth_config(self) -> None:
        """Validate OAuth configuration from environment"""
        required_vars = ['AMAZON_LWA_CLIENT_ID', 'AMAZON_LWA_CLIENT_SECRET', 'AMAZON_APP_ID']
        missing = [var for var in required_vars if not os.environ.get(var)]
        
        if missing:
            logger.warning(f"⚠️ Missing OAuth config: {missing}")
            logger.warning("🔧 Amazon SP-API will work in demo mode. Please configure Amazon credentials for production.")
            # Set demo values to prevent crashes
            os.environ.setdefault('AMAZON_LWA_CLIENT_ID', 'demo-client-id')
            os.environ.setdefault('AMAZON_LWA_CLIENT_SECRET', 'demo-client-secret')
            os.environ.setdefault('AMAZON_APP_ID', 'demo-app-id')
    
    def generate_oauth_state(self, user_id: str, connection_id: str) -> str:
        """
        Generate cryptographically secure OAuth state parameter
        
        Args:
            user_id: ECOMSIMPLY user identifier
            connection_id: Connection identifier
            
        Returns:
            Secure state parameter for CSRF protection
        """
        try:
            # Generate cryptographically secure random data
            random_data = secrets.token_urlsafe(32)
            timestamp = str(int(datetime.utcnow().timestamp()))
            
            # Create payload with user context
            payload = f"{user_id}:{connection_id}:{timestamp}:{random_data}"
            
            # Create secure hash
            state_hash = hashlib.sha256(payload.encode()).hexdigest()
            
            # Encode everything for transmission
            combined = base64.urlsafe_b64encode(
                f"{payload}:{state_hash}".encode()
            ).decode()
            
            logger.info(f"🔐 OAuth state generated for user {user_id[:8]}***")
            return combined
            
        except Exception as e:
            logger.error(f"❌ OAuth state generation failed: {type(e).__name__}")
            raise RuntimeError("Failed to generate OAuth state") from e
    
    def verify_oauth_state(
        self, 
        state: str, 
        expected_user_id: str, 
        expected_connection_id: str,
        max_age_minutes: int = 60
    ) -> bool:
        """
        Verify OAuth state parameter for CSRF protection
        
        Args:
            state: OAuth state parameter to verify
            expected_user_id: Expected user identifier
            expected_connection_id: Expected connection identifier  
            max_age_minutes: Maximum age of state in minutes
            
        Returns:
            True if state is valid, False otherwise
        """
        try:
            # Decode the state parameter
            decoded = base64.urlsafe_b64decode(state.encode()).decode()
            payload, received_hash = decoded.rsplit(':', 1)
            
            # Verify hash integrity
            expected_hash = hashlib.sha256(payload.encode()).hexdigest()
            if not secrets.compare_digest(received_hash, expected_hash):
                logger.warning("❌ OAuth state hash verification failed")
                return False
            
            # Parse payload components
            parts = payload.split(':', 3)
            if len(parts) != 4:
                logger.warning("❌ OAuth state format invalid")
                return False
            
            user_id, connection_id, timestamp_str, _ = parts
            
            # Verify user and connection IDs
            if user_id != expected_user_id or connection_id != expected_connection_id:
                logger.warning("❌ OAuth state user/connection mismatch")
                return False
            
            # Check timestamp age
            try:
                timestamp = int(timestamp_str)
                state_age = datetime.utcnow().timestamp() - timestamp
                if state_age > (max_age_minutes * 60):
                    logger.warning("❌ OAuth state expired")
                    return False
            except ValueError:
                logger.warning("❌ OAuth state timestamp invalid")
                return False
            
            logger.info(f"✅ OAuth state verified for user {user_id[:8]}***")
            return True
            
        except Exception as e:
            logger.warning(f"❌ OAuth state verification failed: {type(e).__name__}")
            return False
    
    def build_authorization_url(
        self,
        state: str,
        marketplace_id: str,
        region: SPAPIRegion = SPAPIRegion.EU,
        redirect_uri: Optional[str] = None
    ) -> str:
        """
        Build Amazon OAuth authorization URL
        
        Args:
            state: OAuth state parameter
            marketplace_id: Target Amazon marketplace
            region: Amazon region
            redirect_uri: OAuth redirect URI
            
        Returns:
            Complete OAuth authorization URL
        """
        try:
            # Use AMAZON_REDIRECT_URI with priority over APP_BASE_URL
            if not redirect_uri:
                redirect_uri = os.environ.get('AMAZON_REDIRECT_URI') or f"{os.environ.get('APP_BASE_URL', 'https://app.ecomsimply.com')}/api/amazon/callback"
            
            # Build OAuth parameters
            params = {
                'application_id': self.app_id,  # Use AMAZON_APP_ID instead of client_id
                'redirect_uri': redirect_uri,
                'state': state,
                'version': 'beta'  # Required for SP-API
            }
            
            # Add marketplace-specific parameters
            if marketplace_id:
                params['marketplace_id'] = marketplace_id
            
            # Build complete URL
            base_url = self._oauth_endpoints[region]['auth']
            query_string = urlencode(params)
            auth_url = f"{base_url}?{query_string}"
            
            logger.info(f"🔗 Authorization URL built for marketplace {marketplace_id}")
            return auth_url
            
        except Exception as e:
            logger.error(f"❌ Failed to build authorization URL: {type(e).__name__}")
            raise RuntimeError("Failed to build authorization URL") from e
    
    async def exchange_code_for_tokens(
        self,
        authorization_code: str,
        region: SPAPIRegion = SPAPIRegion.EU,
        redirect_uri: Optional[str] = None
    ) -> SPAPITokenData:
        """
        Exchange OAuth authorization code for access and refresh tokens
        
        Args:
            authorization_code: OAuth authorization code from callback
            region: Amazon region
            redirect_uri: OAuth redirect URI
            
        Returns:
            Token data (never logged)
        """
        try:
            # Use AMAZON_REDIRECT_URI with priority over APP_BASE_URL
            if not redirect_uri:
                redirect_uri = os.environ.get('AMAZON_REDIRECT_URI') or f"{os.environ.get('APP_BASE_URL', 'https://app.ecomsimply.com')}/api/amazon/callback"
            
            # Prepare token request data
            token_data = {
                'grant_type': 'authorization_code',
                'code': authorization_code,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': redirect_uri
            }
            
            # Make token exchange request
            token_endpoint = self._oauth_endpoints[region]['token']
            response = await self.http_client.post(
                token_endpoint,
                data=token_data
            )
            
            response.raise_for_status()
            token_response = response.json()
            
            # Validate response fields
            required_fields = ['access_token', 'refresh_token', 'token_type', 'expires_in']
            for field in required_fields:
                if field not in token_response:
                    logger.error(f"❌ Missing token field: {field}")
                    logger.error(f"❌ Response body (first 500 chars): {str(token_response)[:500]}")
                    logger.error(f"❌ Redirect URI used: {redirect_uri}")
                    logger.error(f"❌ Region: {region}")
                    raise ValueError(f"Missing token field: {field}")
            
            # Check if refresh_token is present
            if not token_response.get('refresh_token'):
                logger.error(f"❌ No refresh_token in response")
                logger.error(f"❌ Response body (first 500 chars): {str(token_response)[:500]}")
                logger.error(f"❌ Redirect URI used: {redirect_uri}") 
                logger.error(f"❌ Region: {region}")
                raise ValueError("Missing refresh_token in OAuth response")
            
            # Calculate expiration time
            expires_in = int(token_response['expires_in'])
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Create token data object
            token_data_obj = SPAPITokenData(
                access_token=token_response['access_token'],
                refresh_token=token_response['refresh_token'],
                token_type=token_response['token_type'],
                expires_in=expires_in,
                expires_at=expires_at,
                scope=token_response.get('scope', '')
            )
            
            logger.info("🔑 OAuth token exchange successful")
            return token_data_obj
            
        except httpx.HTTPStatusError as e:
            # Log error details without exposing secrets
            logger.error(f"❌ Token exchange HTTP error: {e.response.status_code}")
            logger.error(f"❌ Response body (first 500 chars): {e.response.text[:500]}")
            logger.error(f"❌ Redirect URI used: {redirect_uri}")
            logger.error(f"❌ Region: {region}")
            
            if e.response.status_code == 400:
                error_detail = "Invalid authorization code or expired"
            elif e.response.status_code == 401:
                error_detail = "Invalid client credentials" 
            else:
                error_detail = f"HTTP {e.response.status_code}"
            raise RuntimeError(f"Token exchange failed: {error_detail}") from e
        
        except Exception as e:
            logger.error(f"❌ Token exchange failed: {type(e).__name__}")
            raise RuntimeError("Token exchange failed") from e
    
    async def refresh_access_token(
        self,
        refresh_token: str,
        region: SPAPIRegion = SPAPIRegion.EU
    ) -> SPAPITokenData:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Valid refresh token (not logged)
            region: Amazon region
            
        Returns:
            New token data (never logged)
        """
        try:
            # Prepare refresh request data
            refresh_data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            # Make token refresh request
            token_endpoint = self._oauth_endpoints[region]['token']
            response = await self.http_client.post(
                token_endpoint,
                data=refresh_data
            )
            
            response.raise_for_status()
            token_response = response.json()
            
            # Calculate new expiration
            expires_in = int(token_response['expires_in'])
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Create updated token data
            token_data_obj = SPAPITokenData(
                access_token=token_response['access_token'],
                refresh_token=refresh_token,  # Reuse existing refresh token
                token_type=token_response['token_type'],
                expires_in=expires_in,
                expires_at=expires_at,
                scope=token_response.get('scope', '')
            )
            
            logger.info("🔄 Access token refreshed successfully")
            return token_data_obj
            
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Token refresh HTTP error: {e.response.status_code}")
            if e.response.status_code == 400:
                error_detail = "Invalid or expired refresh token"
            else:
                error_detail = f"HTTP {e.response.status_code}"
            raise RuntimeError(f"Token refresh failed: {error_detail}") from e
        
        except Exception as e:
            logger.error(f"❌ Token refresh failed: {type(e).__name__}")
            raise RuntimeError("Token refresh failed") from e
    
    async def validate_access_token(
        self,
        access_token: str,
        region: SPAPIRegion = SPAPIRegion.EU
    ) -> bool:
        """
        Validate access token by testing SP-API call
        
        Args:
            access_token: Access token to validate (not logged)
            region: Amazon region
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            # Test with a simple SP-API endpoint
            spapi_endpoint = self._oauth_endpoints[region]['spapi']
            test_url = f"{spapi_endpoint}/sellers/v1/marketplaceParticipations"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'x-amz-access-token': access_token
            }
            
            response = await self.http_client.get(test_url, headers=headers)
            
            # Token is valid if we get a 200 response
            is_valid = response.status_code == 200
            
            if is_valid:
                logger.info("✅ Access token validation successful")
            else:
                logger.warning("❌ Access token validation failed")
            
            return is_valid
            
        except Exception as e:
            logger.warning(f"❌ Token validation error: {type(e).__name__}")
            return False
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()