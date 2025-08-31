# Amazon SP-API REST Client with Retry Logic
import os
import time
import json
import logging
import asyncio
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
import aiohttp
import hashlib
import hmac
import base64
from urllib.parse import quote

logger = logging.getLogger(__name__)

class AmazonSPAPIClient:
    """Amazon SP-API REST Client with comprehensive retry logic and logging"""
    
    def __init__(self, region: str = 'eu'):
        self.region = region
        
        # Endpoints SP-API par région
        self.endpoints = {
            'na': 'https://sellingpartnerapi-na.amazon.com',
            'eu': 'https://sellingpartnerapi-eu.amazon.com', 
            'fe': 'https://sellingpartnerapi-fe.amazon.com'
        }
        
        self.base_url = self.endpoints.get(region)
        if not self.base_url:
            raise ValueError(f"Unsupported region: {region}")
        
        # Configuration retry
        self.max_retries = 3
        self.base_delay = 1.0
        self.max_delay = 60.0
        self.backoff_factor = 2.0
        
        logger.info(f"✅ SP-API client initialized for region: {region}")
    
    async def make_authenticated_request(
        self,
        method: str,
        path: str,
        access_token: str,
        seller_id: str,
        marketplace_id: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Effectue une requête authentifiée vers SP-API avec retry automatique
        
        Args:
            method: Méthode HTTP (GET, POST, PUT, DELETE)
            path: Chemin de l'API (ex: '/listings/2021-08-01/items')
            access_token: Token d'accès Amazon
            seller_id: ID du vendeur Amazon
            marketplace_id: ID du marketplace
            params: Paramètres de requête
            json_data: Données JSON à envoyer
            headers: Headers additionnels
            
        Returns:
            Réponse JSON de l'API Amazon
        """
        url = f"{self.base_url}{path}"
        
        # Headers par défaut
        request_headers = {
            'Authorization': f'Bearer {access_token}',
            'x-amz-access-token': access_token,
            'x-amz-date': datetime.utcnow().strftime('%Y%m%dT%H%M%SZ'),
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'ECOMSIMPLY-SP-API/1.0',
            'Host': self.base_url.replace('https://', ''),
            'x-amz-security-token': seller_id
        }
        
        if headers:
            request_headers.update(headers)
        
        # Ajouter marketplace dans les paramètres si nécessaire
        if params is None:
            params = {}
        if 'marketplaceIds' not in params:
            params['marketplaceIds'] = marketplace_id
        
        # Retry logic avec exponential backoff
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"📡 SP-API {method} {path} (attempt {attempt + 1})")
                
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method=method.upper(),
                        url=url,
                        params=params,
                        json=json_data,
                        headers=request_headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        
                        # Log de la requête
                        self._log_request(method, url, response.status, attempt + 1)
                        
                        # Gestion des codes de statut
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f"✅ SP-API request successful")
                            return result
                        
                        elif response.status == 429:  # Rate limit
                            retry_after = int(response.headers.get('Retry-After', 60))
                            logger.warning(f"⚠️ Rate limited, retry after {retry_after}s")
                            
                            if attempt < self.max_retries:
                                await asyncio.sleep(retry_after)
                                continue
                        
                        elif response.status in [500, 502, 503, 504]:  # Server errors
                            if attempt < self.max_retries:
                                delay = min(
                                    self.base_delay * (self.backoff_factor ** attempt),
                                    self.max_delay
                                )
                                logger.warning(f"⚠️ Server error {response.status}, retry in {delay}s")
                                await asyncio.sleep(delay)
                                continue
                        
                        elif response.status == 401:  # Unauthorized
                            error_text = await response.text()
                            logger.error(f"❌ Authentication failed: {error_text}")
                            raise AuthenticationError("Amazon SP-API authentication failed")
                        
                        elif response.status == 403:  # Forbidden
                            error_text = await response.text()
                            logger.error(f"❌ Access forbidden: {error_text}")
                            raise AuthorizationError("Amazon SP-API access forbidden")
                        
                        else:
                            # Autres erreurs
                            error_text = await response.text()
                            logger.error(f"❌ SP-API error {response.status}: {error_text}")
                            raise SPAPIError(f"SP-API error {response.status}: {error_text}")
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.error(f"❌ Network error: {str(e)}")
                
                if attempt < self.max_retries:
                    delay = min(
                        self.base_delay * (self.backoff_factor ** attempt),
                        self.max_delay
                    )
                    logger.info(f"🔄 Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise NetworkError(f"Max retries exceeded: {str(e)}")
        
        raise SPAPIError("Max retries exceeded")
    
    async def get_seller_info(self, access_token: str, seller_id: str) -> Dict[str, Any]:
        """
        Récupère les informations du vendeur
        
        Args:
            access_token: Token d'accès Amazon
            seller_id: ID du vendeur
            
        Returns:
            Informations du vendeur
        """
        return await self.make_authenticated_request(
            method='GET',
            path='/sellers/v1/marketplaceParticipations',
            access_token=access_token,
            seller_id=seller_id,
            marketplace_id='',  # Non requis pour cette API
            params={}
        )
    
    async def get_listings(
        self,
        access_token: str,
        seller_id: str,
        marketplace_id: str,
        sku: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Récupère les listings du vendeur
        
        Args:
            access_token: Token d'accès Amazon
            seller_id: ID du vendeur
            marketplace_id: ID du marketplace
            sku: SKU spécifique (optionnel)
            
        Returns:
            Liste des produits
        """
        path = '/listings/2021-08-01/items'
        params = {'marketplaceIds': marketplace_id}
        
        if sku:
            path = f'/listings/2021-08-01/items/{quote(sku)}'
        
        return await self.make_authenticated_request(
            method='GET',
            path=path,
            access_token=access_token,
            seller_id=seller_id,
            marketplace_id=marketplace_id,
            params=params
        )
    
    async def create_listing(
        self,
        access_token: str,
        seller_id: str,
        marketplace_id: str,
        sku: str,
        product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crée un nouveau listing sur Amazon
        
        Args:
            access_token: Token d'accès Amazon
            seller_id: ID du vendeur
            marketplace_id: ID du marketplace
            sku: SKU du produit
            product_data: Données du produit
            
        Returns:
            Résultat de la création
        """
        return await self.make_authenticated_request(
            method='PUT',
            path=f'/listings/2021-08-01/items/{quote(sku)}',
            access_token=access_token,
            seller_id=seller_id,
            marketplace_id=marketplace_id,
            json_data=product_data
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Vérifie la santé des endpoints SP-API
        
        Returns:
            Status de santé des endpoints
        """
        health_results = {}
        
        for region, endpoint in self.endpoints.items():
            try:
                start_time = time.time()
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        endpoint,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        response_time = time.time() - start_time
                        
                        health_results[region] = {
                            'status': 'healthy' if response.status in [200, 401, 403] else 'unhealthy',
                            'response_time_ms': round(response_time * 1000),
                            'status_code': response.status,
                            'endpoint': endpoint
                        }
                        
            except Exception as e:
                health_results[region] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'endpoint': endpoint
                }
        
        return {
            'overall_status': 'healthy' if all(
                r.get('status') == 'healthy' for r in health_results.values()
            ) else 'degraded',
            'regions': health_results,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _log_request(self, method: str, url: str, status_code: int, attempt: int):
        """Log sécurisé des requêtes SP-API"""
        # Masquer les tokens dans l'URL
        safe_url = self._sanitize_url_for_logging(url)
        
        if status_code < 300:
            logger.info(f"✅ {method} {safe_url} → {status_code} (attempt {attempt})")
        elif status_code < 500:
            logger.warning(f"⚠️ {method} {safe_url} → {status_code} (attempt {attempt})")
        else:
            logger.error(f"❌ {method} {safe_url} → {status_code} (attempt {attempt})")
    
    def _sanitize_url_for_logging(self, url: str) -> str:
        """Retire les informations sensibles des URLs pour le logging"""
        # Remplacer les tokens par des étoiles
        import re
        
        # Pattern pour les tokens dans les paramètres
        patterns = [
            (r'access_token=[^&]+', 'access_token=***'),
            (r'seller_id=[^&]+', 'seller_id=***'),
            (r'Authorization: Bearer [^\s]+', 'Authorization: Bearer ***')
        ]
        
        safe_url = url
        for pattern, replacement in patterns:
            safe_url = re.sub(pattern, replacement, safe_url, flags=re.IGNORECASE)
        
        return safe_url

# Exceptions personnalisées
class SPAPIError(Exception):
    """Exception de base pour les erreurs SP-API"""
    pass

class AuthenticationError(SPAPIError):
    """Erreur d'authentification SP-API"""
    pass

class AuthorizationError(SPAPIError):
    """Erreur d'autorisation SP-API"""
    pass

class NetworkError(SPAPIError):
    """Erreur réseau"""
    pass

class RateLimitError(SPAPIError):
    """Erreur de limite de taux"""
    pass