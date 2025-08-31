"""
Transport Layer robuste pour scraping ECOMSIMPLY
- Concurrence par domaine (Semaphore par host)
- Retry avec exponential backoff + jitter
- Pool de proxys avec score de santé
- Cache TTL court (180s) pour réponses HTML
"""

import asyncio
import hashlib
import random
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse
import logging

import httpx
from httpx import Response, TimeoutException

# Configuration du logger
logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Entrée de cache avec TTL"""
    content: str
    timestamp: float
    status_code: int
    headers: Dict[str, str]
    
    def is_expired(self, ttl_seconds: int = 180) -> bool:
        """Vérifier si l'entrée de cache a expiré"""
        return (time.time() - self.timestamp) > ttl_seconds


class ResponseCache:
    """Cache simple avec TTL pour les réponses HTML"""
    
    def __init__(self, ttl_seconds: int = 180):
        """
        Args:
            ttl_seconds: Durée de vie du cache en secondes
        """
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
    
    def _get_cache_key(self, url: str, method: str = "GET", headers: Optional[Dict] = None) -> str:
        """Générer une clé de cache"""
        # Inclure URL, méthode et headers importants dans la clé
        key_data = f"{method}:{url}"
        if headers:
            # Ne considérer que certains headers pour le cache
            cache_headers = {k: v for k, v in headers.items() 
                           if k.lower() in ['accept', 'accept-language']}
            if cache_headers:
                key_data += f":{sorted(cache_headers.items())}"
        
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, url: str, method: str = "GET", headers: Optional[Dict] = None) -> Optional[CacheEntry]:
        """Récupérer une entrée du cache si elle existe et n'a pas expiré"""
        cache_key = self._get_cache_key(url, method, headers)
        
        async with self._lock:
            if cache_key in self.cache:
                entry = self.cache[cache_key]
                if not entry.is_expired(self.ttl_seconds):
                    logger.debug(f"Cache HIT pour {url} (âge: {time.time() - entry.timestamp:.1f}s)")
                    return entry
                else:
                    # Supprimer l'entrée expirée
                    del self.cache[cache_key]
                    logger.debug(f"Cache EXPIRED pour {url}")
        
        logger.debug(f"Cache MISS pour {url}")
        return None
    
    async def set(self, url: str, response: Response, method: str = "GET", headers: Optional[Dict] = None) -> None:
        """Mettre en cache une réponse (seulement si HTML et succès)"""
        # Ne mettre en cache que les réponses HTML avec succès
        content_type = response.headers.get('content-type', '').lower()
        if (response.status_code == 200 and 
            ('text/html' in content_type or 'application/xhtml' in content_type)):
            
            cache_key = self._get_cache_key(url, method, headers)
            
            async with self._lock:
                self.cache[cache_key] = CacheEntry(
                    content=response.text,
                    timestamp=time.time(),
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
                logger.debug(f"Cache SET pour {url} (taille: {len(response.text)} chars)")
    
    async def clear_expired(self) -> int:
        """Nettoyer les entrées expirées du cache"""
        async with self._lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired(self.ttl_seconds)
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.info(f"Cache nettoyé: {len(expired_keys)} entrées expirées supprimées")
            
            return len(expired_keys)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques du cache"""
        async with self._lock:
            total_entries = len(self.cache)
            expired_entries = sum(
                1 for entry in self.cache.values()
                if entry.is_expired(self.ttl_seconds)
            )
            
            return {
                "total_entries": total_entries,
                "active_entries": total_entries - expired_entries,
                "expired_entries": expired_entries,
                "ttl_seconds": self.ttl_seconds
            }


@dataclass
class ProxyInfo:
    """Information sur un proxy avec score de santé"""
    url: str
    score: float = 0.0  # Score ∈ [-1, +1]
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[float] = None
    consecutive_failures: int = 0


class ProxyPool:
    """Pool de proxys avec score de santé et rotation automatique"""
    
    def __init__(self, eviction_threshold: float = -0.5):
        """
        Args:
            eviction_threshold: Seuil en dessous duquel un proxy est évincé
        """
        self.proxies: Dict[str, ProxyInfo] = {}
        self.eviction_threshold = eviction_threshold
        self._lock = asyncio.Lock()
        
    async def add(self, proxy_url: str) -> None:
        """Ajouter un proxy au pool"""
        async with self._lock:
            if proxy_url not in self.proxies:
                self.proxies[proxy_url] = ProxyInfo(url=proxy_url)
                logger.info(f"Proxy ajouté au pool: {proxy_url}")
    
    async def pick(self) -> Optional[str]:
        """Sélectionner le meilleur proxy disponible"""
        async with self._lock:
            if not self.proxies:
                return None
            
            # Filtrer les proxys non évincés
            available_proxies = [
                p for p in self.proxies.values() 
                if p.score >= self.eviction_threshold
            ]
            
            if not available_proxies:
                logger.warning("Aucun proxy disponible dans le pool")
                return None
            
            # Sélectionner le proxy avec le meilleur score
            # En cas d'égalité, privilégier celui utilisé le moins récemment
            best_proxy = max(
                available_proxies,
                key=lambda p: (p.score, -(p.last_used or 0))
            )
            
            best_proxy.last_used = time.time()
            logger.debug(f"Proxy sélectionné: {best_proxy.url} (score: {best_proxy.score:.2f})")
            return best_proxy.url
    
    async def report_success(self, proxy_url: str) -> None:
        """Rapporter un succès pour un proxy"""
        async with self._lock:
            if proxy_url in self.proxies:
                proxy = self.proxies[proxy_url]
                proxy.success_count += 1
                proxy.consecutive_failures = 0
                
                # Augmenter le score (max +1)
                proxy.score = min(1.0, proxy.score + 0.1)
                
                logger.debug(f"Succès rapporté pour proxy {proxy_url} (score: {proxy.score:.2f})")
    
    async def report_failure(self, proxy_url: str, error_type: str = "unknown") -> None:
        """Rapporter un échec pour un proxy"""
        async with self._lock:
            if proxy_url in self.proxies:
                proxy = self.proxies[proxy_url]
                proxy.failure_count += 1
                proxy.consecutive_failures += 1
                
                # Diminuer le score selon le type d'erreur
                penalty = 0.2 if error_type in ["timeout", "429"] else 0.1
                proxy.score = max(-1.0, proxy.score - penalty)
                
                logger.warning(f"Échec rapporté pour proxy {proxy_url} "
                             f"(type: {error_type}, score: {proxy.score:.2f})")
                
                # Éviction automatique si score trop bas
                if proxy.score < self.eviction_threshold:
                    logger.info(f"Proxy évincé: {proxy_url} (score: {proxy.score:.2f})")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques du pool"""
        async with self._lock:
            return {
                "total_proxies": len(self.proxies),
                "available_proxies": len([
                    p for p in self.proxies.values() 
                    if p.score >= self.eviction_threshold
                ]),
                "evicted_proxies": len([
                    p for p in self.proxies.values() 
                    if p.score < self.eviction_threshold
                ]),
                "average_score": sum(p.score for p in self.proxies.values()) / len(self.proxies) if self.proxies else 0,
                "proxies": [
                    {
                        "url": p.url,
                        "score": p.score,
                        "success_count": p.success_count,
                        "failure_count": p.failure_count,
                        "consecutive_failures": p.consecutive_failures
                    }
                    for p in self.proxies.values()
                ]
            }


class RequestCoordinator:
    """Coordinateur de requêtes avec gestion de concurrence, retry et cache"""
    
    def __init__(self, max_per_host: int = 3, timeout_s: float = 10.0, cache_ttl_s: int = 180):
        """
        Args:
            max_per_host: Nombre max de requêtes simultanées par host (défaut: 3)
            timeout_s: Timeout global en secondes (défaut: 10s)
            cache_ttl_s: TTL du cache en secondes (défaut: 180s)
        """
        self.max_per_host = max_per_host
        self.timeout_s = timeout_s
        
        # Semaphores par host pour limiter la concurrence
        self.host_semaphores: Dict[str, asyncio.Semaphore] = defaultdict(
            lambda: asyncio.Semaphore(max_per_host)
        )
        
        # Pool de proxys
        self.proxy_pool = ProxyPool()
        
        # Cache de réponses avec TTL
        self.cache = ResponseCache(ttl_seconds=cache_ttl_s)
        
        # Client HTTP avec configuration robuste
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_s),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            follow_redirects=True
        )
        
        # Configuration retry
        self.retry_codes = {408, 429, 500, 502, 503, 504}  # Codes à retry
        self.max_retries = 3
        self.base_delay = 1.0  # Délai de base en secondes
        self.max_delay = 30.0  # Délai maximum
        self.backoff_factor = 2.0
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Fermer le client HTTP"""
        await self.client.aclose()
    
    def _get_host(self, url: str) -> str:
        """Extraire le host d'une URL"""
        return urlparse(url).netloc
    
    def _calculate_backoff_delay(self, attempt: int, jitter: bool = True) -> float:
        """Calculer le délai d'attente avec exponential backoff + jitter"""
        delay = min(
            self.base_delay * (self.backoff_factor ** attempt),
            self.max_delay
        )
        
        if jitter:
            # Ajouter un jitter de ±25%
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    def _should_retry(self, response: Optional[Response], exception: Optional[Exception]) -> bool:
        """Déterminer si on doit retry la requête"""
        if exception:
            # Retry sur timeout et erreurs réseau
            return isinstance(exception, (TimeoutException, httpx.ConnectError, httpx.ReadError))
        
        if response:
            # Retry sur codes d'erreur spécifiques
            return response.status_code in self.retry_codes
        
        return False
    
    async def get(self, url: str, *, headers: Optional[Dict[str, str]] = None, 
                  proxy: Optional[str] = None, use_cache: bool = True) -> Response:
        """Méthode GET simplifiée avec cache"""
        return await self.fetch(url, method="GET", headers=headers, proxy=proxy, use_cache=use_cache)
    
    async def fetch(self, url: str, method: str = "GET", *,
                   headers: Optional[Dict[str, str]] = None,
                   data: Optional[Union[str, bytes, Dict]] = None,
                   proxy: Optional[str] = None,
                   use_cache: bool = True,
                   **kwargs) -> Response:
        """
        Effectuer une requête HTTP avec gestion complète de la robustesse et cache
        
        Args:
            url: URL à requêter
            method: Méthode HTTP
            headers: Headers HTTP optionnels
            data: Données à envoyer
            proxy: Proxy spécifique à utiliser (sinon sélection automatique)
            use_cache: Utiliser le cache pour les requêtes GET HTML
            **kwargs: Arguments supplémentaires pour httpx
        
        Returns:
            Response HTTP
        
        Raises:
            httpx.HTTPStatusError: Si tous les retries échouent
        """
        # Vérifier le cache pour les requêtes GET HTML
        if use_cache and method.upper() == "GET" and data is None:
            cached_response = await self.cache.get(url, method, headers)
            if cached_response:
                # Créer une Response simulée à partir du cache
                mock_response = httpx.Response(
                    status_code=cached_response.status_code,
                    headers=cached_response.headers,
                    content=cached_response.content.encode('utf-8')
                )
                return mock_response
        
        host = self._get_host(url)
        semaphore = self.host_semaphores[host]
        
        # Gestion de la concurrence par host
        async with semaphore:
            response = await self._fetch_with_retry(
                url, method, headers=headers, data=data, proxy=proxy, **kwargs
            )
            
            # Mettre en cache si applicable
            if use_cache and method.upper() == "GET" and data is None:
                await self.cache.set(url, response, method, headers)
            
            return response
    
    async def _fetch_with_retry(self, url: str, method: str, *,
                               headers: Optional[Dict[str, str]] = None,
                               data: Optional[Union[str, bytes, Dict]] = None,
                               proxy: Optional[str] = None,
                               **kwargs) -> Response:
        """Effectuer la requête avec logique de retry"""
        
        last_exception = None
        last_response = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Sélectionner un proxy si non spécifié
                current_proxy = proxy or await self.proxy_pool.pick()
                
                # Préparer les options de la requête
                request_kwargs = {
                    **kwargs,
                    "headers": headers,
                    "timeout": self.timeout_s
                }
                
                # Configuration du proxy si nécessaire
                if current_proxy:
                    # Créer un nouveau client avec proxy pour cette requête
                    proxy_client = httpx.AsyncClient(
                        proxy=current_proxy,
                        timeout=httpx.Timeout(self.timeout_s),
                        limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
                        follow_redirects=True
                    )
                    client = proxy_client
                else:
                    client = self.client
                
                if data is not None:
                    if method.upper() in ["POST", "PUT", "PATCH"]:
                        if isinstance(data, dict):
                            request_kwargs["json"] = data
                        else:
                            request_kwargs["content"] = data
                
                # Effectuer la requête
                start_time = time.time()
                response = await client.request(method, url, **request_kwargs)
                duration = time.time() - start_time
                
                # Fermer le client proxy temporaire si utilisé
                if current_proxy:
                    await proxy_client.aclose()
                
                # Log de la requête
                logger.info(f"Requête {method} {url} - Status: {response.status_code} "
                           f"- Durée: {duration:.2f}s - Proxy: {current_proxy or 'None'}")
                
                # Vérifier si la réponse est un succès
                if response.status_code < 400:
                    # Rapporter le succès du proxy
                    if current_proxy:
                        await self.proxy_pool.report_success(current_proxy)
                    return response
                
                # Enregistrer la réponse d'erreur
                last_response = response
                
                # Rapporter l'échec du proxy
                if current_proxy:
                    error_type = "429" if response.status_code == 429 else "http_error"
                    await self.proxy_pool.report_failure(current_proxy, error_type)
                
                # Vérifier si on doit retry
                if not self._should_retry(response, None):
                    response.raise_for_status()
                    return response
                
            except Exception as e:
                last_exception = e
                
                # Fermer le client proxy temporaire si utilisé
                if current_proxy and 'proxy_client' in locals():
                    try:
                        await proxy_client.aclose()
                    except:
                        pass
                
                # Rapporter l'échec du proxy
                if current_proxy:
                    error_type = "timeout" if isinstance(e, TimeoutException) else "connection_error"
                    await self.proxy_pool.report_failure(current_proxy, error_type)
                
                # Vérifier si on doit retry
                if not self._should_retry(None, e):
                    raise
                
                logger.warning(f"Tentative {attempt + 1} échouée pour {url}: {str(e)}")
            
            # Si ce n'est pas la dernière tentative, attendre avant de retry
            if attempt < self.max_retries:
                delay = self._calculate_backoff_delay(attempt)
                logger.info(f"Retry dans {delay:.2f}s pour {url}")
                await asyncio.sleep(delay)
        
        # Tous les retries ont échoué
        if last_response:
            logger.error(f"Tous les retries échoués pour {url} - Dernier status: {last_response.status_code}")
            last_response.raise_for_status()
            return last_response
        
        if last_exception:
            logger.error(f"Tous les retries échoués pour {url} - Dernière exception: {str(last_exception)}")
            raise last_exception
        
        # Ne devrait jamais arriver
        raise RuntimeError(f"Erreur inattendue pour {url}")
    
    async def add_proxy(self, proxy_url: str) -> None:
        """Ajouter un proxy au pool"""
        await self.proxy_pool.add(proxy_url)
    
    async def get_proxy_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques des proxys"""
        return await self.proxy_pool.get_stats()
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques du cache"""
        return await self.cache.get_stats()
    
    async def clear_cache(self) -> int:
        """Nettoyer le cache et retourner le nombre d'entrées supprimées"""
        return await self.cache.clear_expired()