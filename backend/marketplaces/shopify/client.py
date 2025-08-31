# Shopify REST/GraphQL Client with Retry Logic
import os
import time
import json
import logging
import asyncio
from typing import Dict, Any, Optional, Union, List
from datetime import datetime, timedelta
import aiohttp
import base64

logger = logging.getLogger(__name__)

class ShopifyAPIClient:
    """Shopify REST & GraphQL Client with comprehensive retry logic and logging"""
    
    def __init__(self, shop_domain: str, access_token: str):
        self.shop_domain = shop_domain
        self.access_token = access_token
        
        # Endpoints Shopify
        self.rest_base_url = f"https://{shop_domain}/admin/api/2024-01"
        self.graphql_url = f"https://{shop_domain}/admin/api/2024-01/graphql.json"
        
        # Configuration retry pour rate limiting Shopify
        self.max_retries = 3
        self.base_delay = 1.0
        self.max_delay = 60.0
        self.backoff_factor = 2.0
        
        logger.info(f"✅ Shopify client initialized for shop: {shop_domain}")
    
    async def make_rest_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Effectue une requête REST vers l'API Shopify avec retry automatique
        
        Args:
            method: Méthode HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint de l'API (ex: '/products.json')
            params: Paramètres de requête
            json_data: Données JSON à envoyer
            headers: Headers additionnels
            
        Returns:
            Réponse JSON de l'API Shopify
        """
        url = f"{self.rest_base_url}{endpoint}"
        
        # Headers par défaut
        request_headers = {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'ECOMSIMPLY-Shopify/1.0'
        }
        
        if headers:
            request_headers.update(headers)
        
        return await self._execute_request_with_retry(
            method, url, request_headers, params, json_data
        )
    
    async def make_graphql_request(
        self,
        query: str,
        variables: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Effectue une requête GraphQL vers l'API Shopify
        
        Args:
            query: Requête GraphQL
            variables: Variables GraphQL
            headers: Headers additionnels
            
        Returns:
            Réponse JSON de l'API Shopify GraphQL
        """
        # Headers par défaut
        request_headers = {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'ECOMSIMPLY-Shopify/1.0'
        }
        
        if headers:
            request_headers.update(headers)
        
        # Préparer les données GraphQL
        graphql_data = {
            'query': query
        }
        
        if variables:
            graphql_data['variables'] = variables
        
        return await self._execute_request_with_retry(
            'POST', self.graphql_url, request_headers, None, graphql_data
        )
    
    async def _execute_request_with_retry(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Exécute une requête avec retry logic et gestion des rate limits Shopify
        """
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"📡 Shopify {method} {url} (attempt {attempt + 1})")
                
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method=method.upper(),
                        url=url,
                        params=params,
                        json=json_data,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        
                        # Log de la requête
                        self._log_request(method, url, response.status, attempt + 1)
                        
                        # Gestion des codes de statut Shopify
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f"✅ Shopify request successful")
                            return result
                        
                        elif response.status == 429:  # Rate limit exceeded
                            retry_after = self._parse_retry_after(response.headers)
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
                            raise AuthenticationError("Shopify API authentication failed")
                        
                        elif response.status == 403:  # Forbidden
                            error_text = await response.text()
                            logger.error(f"❌ Access forbidden: {error_text}")
                            raise AuthorizationError("Shopify API access forbidden")
                        
                        elif response.status == 404:  # Not found
                            error_text = await response.text()
                            logger.error(f"❌ Resource not found: {error_text}")
                            raise NotFoundError("Shopify resource not found")
                        
                        elif response.status == 422:  # Unprocessable entity
                            error_text = await response.text()
                            error_data = await response.json() if response.content_type == 'application/json' else {}
                            logger.error(f"❌ Validation error: {error_text}")
                            raise ValidationError("Shopify validation error", error_data)
                        
                        else:
                            # Autres erreurs
                            error_text = await response.text()
                            logger.error(f"❌ Shopify API error {response.status}: {error_text}")
                            raise ShopifyAPIError(f"Shopify API error {response.status}: {error_text}")
                        
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
        
        raise ShopifyAPIError("Max retries exceeded")
    
    def _parse_retry_after(self, headers: Dict[str, str]) -> int:
        """Parse Retry-After header or use Shopify rate limit bucket"""
        # Shopify utilise X-Shopify-Shop-Api-Call-Limit
        api_call_limit = headers.get('X-Shopify-Shop-Api-Call-Limit', '0/40')
        
        try:
            current, limit = map(int, api_call_limit.split('/'))
            
            # Si on approche de la limite, attendre plus longtemps
            if current >= limit * 0.9:  # 90% de la limite
                return 10
            elif current >= limit * 0.7:  # 70% de la limite
                return 5
            else:
                return int(headers.get('Retry-After', 2))
        except:
            return int(headers.get('Retry-After', 2))
    
    # Méthodes utilitaires pour les opérations courantes
    
    async def get_shop_info(self) -> Dict[str, Any]:
        """Récupère les informations de la boutique"""
        return await self.make_rest_request('GET', '/shop.json')
    
    async def get_products(self, limit: int = 50, page_info: Optional[str] = None) -> Dict[str, Any]:
        """
        Récupère les produits de la boutique
        
        Args:
            limit: Nombre de produits à récupérer (max 250)
            page_info: Curseur de pagination
            
        Returns:
            Liste des produits avec métadonnées de pagination
        """
        params = {'limit': min(limit, 250)}
        if page_info:
            params['page_info'] = page_info
            
        return await self.make_rest_request('GET', '/products.json', params=params)
    
    async def get_product(self, product_id: str) -> Dict[str, Any]:
        """Récupère un produit spécifique"""
        return await self.make_rest_request('GET', f'/products/{product_id}.json')
    
    async def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouveau produit
        
        Args:
            product_data: Données du produit selon l'API Shopify
            
        Returns:
            Produit créé avec son ID Shopify
        """
        return await self.make_rest_request(
            'POST', 
            '/products.json', 
            json_data={'product': product_data}
        )
    
    async def update_product(self, product_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour un produit existant"""
        return await self.make_rest_request(
            'PUT',
            f'/products/{product_id}.json',
            json_data={'product': product_data}
        )
    
    async def delete_product(self, product_id: str) -> Dict[str, Any]:
        """Supprime un produit"""
        return await self.make_rest_request('DELETE', f'/products/{product_id}.json')
    
    async def get_orders(self, status: str = 'any', limit: int = 50) -> Dict[str, Any]:
        """Récupère les commandes"""
        params = {
            'status': status,
            'limit': min(limit, 250)
        }
        return await self.make_rest_request('GET', '/orders.json', params=params)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Vérifie la santé de la connexion Shopify
        
        Returns:
            Status de santé de l'API
        """
        try:
            start_time = time.time()
            shop_info = await self.get_shop_info()
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time * 1000),
                'shop_name': shop_info.get('shop', {}).get('name', 'Unknown'),
                'plan_name': shop_info.get('shop', {}).get('plan_name', 'Unknown'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _log_request(self, method: str, url: str, status_code: int, attempt: int):
        """Log sécurisé des requêtes Shopify"""
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
        import re
        
        # Pattern pour les tokens dans les paramètres
        patterns = [
            (r'access_token=[^&]+', 'access_token=***'),
            (r'X-Shopify-Access-Token: [^\s]+', 'X-Shopify-Access-Token: ***')
        ]
        
        safe_url = url
        for pattern, replacement in patterns:
            safe_url = re.sub(pattern, replacement, safe_url, flags=re.IGNORECASE)
        
        return safe_url

# Exceptions personnalisées pour Shopify
class ShopifyAPIError(Exception):
    """Exception de base pour les erreurs Shopify API"""
    pass

class AuthenticationError(ShopifyAPIError):
    """Erreur d'authentification Shopify"""
    pass

class AuthorizationError(ShopifyAPIError):
    """Erreur d'autorisation Shopify"""
    pass

class NotFoundError(ShopifyAPIError):
    """Erreur ressource non trouvée"""
    pass

class ValidationError(ShopifyAPIError):
    """Erreur de validation des données"""
    def __init__(self, message: str, errors: Dict[str, Any] = None):
        super().__init__(message)
        self.errors = errors or {}

class NetworkError(ShopifyAPIError):
    """Erreur réseau"""
    pass

class RateLimitError(ShopifyAPIError):
    """Erreur de limite de taux"""
    pass