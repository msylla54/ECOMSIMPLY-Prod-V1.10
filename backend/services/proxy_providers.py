"""
Mock Proxy Provider - ECOMSIMPLY
Interface et implémentation mock pour les providers de proxy (aucun appel réseau)
"""

import asyncio
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import os

@dataclass
class ProxyEndpoint:
    """Représentation d'un endpoint proxy"""
    id: str
    host: str
    port: int
    protocol: str = "http"  # http, https, socks5
    username: Optional[str] = None
    password: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    is_healthy: bool = True
    last_used: Optional[datetime] = None
    success_rate: float = 0.95
    avg_response_time_ms: int = 200

    @property
    def url(self) -> str:
        """Retourne l'URL complète du proxy"""
        auth = ""
        if self.username and self.password:
            auth = f"{self.username}:{self.password}@"
        return f"{self.protocol}://{auth}{self.host}:{self.port}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Conversion en dictionnaire"""
        return {
            "id": self.id,
            "url": self.url,
            "host": self.host,
            "port": self.port,
            "protocol": self.protocol,
            "country": self.country,
            "region": self.region,
            "is_healthy": self.is_healthy,
            "success_rate": self.success_rate,
            "avg_response_time_ms": self.avg_response_time_ms,
            "last_used": self.last_used.isoformat() if self.last_used else None
        }

class IProxyProvider(ABC):
    """Interface pour les providers de proxy"""
    
    @abstractmethod
    async def get_proxy(self, country: Optional[str] = None) -> Optional[ProxyEndpoint]:
        """Récupère un proxy disponible"""
        pass
    
    @abstractmethod
    async def get_proxy_pool(self, size: int = 10) -> List[ProxyEndpoint]:
        """Récupère un pool de proxies"""
        pass
    
    @abstractmethod
    async def health_check(self, proxy: ProxyEndpoint) -> Dict[str, Any]:
        """Vérifie la santé d'un proxy"""
        pass
    
    @abstractmethod
    async def report_proxy_status(self, proxy_id: str, success: bool, response_time_ms: int) -> None:
        """Signale le statut d'utilisation d'un proxy"""
        pass
    
    @abstractmethod
    def get_provider_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques du provider"""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nom du provider"""
        pass
    
    @property
    @abstractmethod
    def is_mock(self) -> bool:
        """Indique si c'est une implémentation mock"""
        pass

class MockProxyProvider(IProxyProvider):
    """Provider de proxy mock (aucun appel réseau)"""
    
    def __init__(self):
        self._proxy_pool: List[ProxyEndpoint] = []
        self._used_proxies: Set[str] = set()
        self._usage_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "unique_proxies_used": 0
        }
        self._rotation_index = 0
        self._initialize_mock_proxies()
    
    def _initialize_mock_proxies(self):
        """Initialise le pool de proxies mock"""
        mock_proxies_data = [
            # Pool de proxies européens simulés
            {"host": "proxy-fr-1.mock.local", "port": 8080, "country": "FR", "region": "Paris"},
            {"host": "proxy-fr-2.mock.local", "port": 8080, "country": "FR", "region": "Lyon"},
            {"host": "proxy-de-1.mock.local", "port": 3128, "country": "DE", "region": "Berlin"},
            {"host": "proxy-de-2.mock.local", "port": 3128, "country": "DE", "region": "Munich"},
            {"host": "proxy-uk-1.mock.local", "port": 8888, "country": "UK", "region": "London"},
            {"host": "proxy-uk-2.mock.local", "port": 8888, "country": "UK", "region": "Manchester"},
            {"host": "proxy-es-1.mock.local", "port": 9090, "country": "ES", "region": "Madrid"},
            {"host": "proxy-it-1.mock.local", "port": 8080, "country": "IT", "region": "Milan"},
            
            # Pool de proxies US simulés
            {"host": "proxy-us-1.mock.local", "port": 8080, "country": "US", "region": "New York"},
            {"host": "proxy-us-2.mock.local", "port": 3128, "country": "US", "region": "California"},
            {"host": "proxy-us-3.mock.local", "port": 8888, "country": "US", "region": "Texas"},
            
            # Pool de proxies Asia-Pacific simulés
            {"host": "proxy-jp-1.mock.local", "port": 8080, "country": "JP", "region": "Tokyo"},
            {"host": "proxy-sg-1.mock.local", "port": 3128, "country": "SG", "region": "Singapore"},
            {"host": "proxy-au-1.mock.local", "port": 8888, "country": "AU", "region": "Sydney"},
        ]
        
        for i, proxy_data in enumerate(mock_proxies_data):
            proxy = ProxyEndpoint(
                id=f"mock_proxy_{i+1:03d}",
                host=proxy_data["host"],
                port=proxy_data["port"],
                protocol="http",
                username=f"user_{i+1}",
                password=f"pass_{i+1}",
                country=proxy_data["country"],
                region=proxy_data["region"],
                is_healthy=random.choice([True, True, True, False]),  # 75% healthy
                success_rate=round(random.uniform(0.85, 0.98), 3),
                avg_response_time_ms=random.randint(50, 500)
            )
            self._proxy_pool.append(proxy)
    
    async def get_proxy(self, country: Optional[str] = None) -> Optional[ProxyEndpoint]:
        """Récupère un proxy disponible avec rotation intelligente"""
        
        # Simuler délai réaliste de sélection
        await asyncio.sleep(0.001)
        
        available_proxies = [p for p in self._proxy_pool if p.is_healthy]
        
        if country:
            # Filtrer par pays si spécifié
            country_proxies = [p for p in available_proxies if p.country == country.upper()]
            if country_proxies:
                available_proxies = country_proxies
        
        if not available_proxies:
            return None
        
        # Rotation avec priorité aux proxies moins utilisés
        unused_proxies = [p for p in available_proxies if p.id not in self._used_proxies]
        
        if unused_proxies:
            # Prioriser les proxies non utilisés
            selected_proxy = random.choice(unused_proxies)
        else:
            # Round-robin sur tous les proxies disponibles
            selected_proxy = available_proxies[self._rotation_index % len(available_proxies)]
            self._rotation_index += 1
        
        # Marquer comme utilisé
        self._used_proxies.add(selected_proxy.id)
        selected_proxy.last_used = datetime.utcnow()
        
        # Stats
        self._usage_stats["total_requests"] += 1
        self._usage_stats["unique_proxies_used"] = len(self._used_proxies)
        
        return selected_proxy
    
    async def get_proxy_pool(self, size: int = 10) -> List[ProxyEndpoint]:
        """Récupère un pool de proxies diversifiés"""
        
        # Simuler délai de récupération pool
        await asyncio.sleep(0.005)
        
        available_proxies = [p for p in self._proxy_pool if p.is_healthy]
        
        if len(available_proxies) <= size:
            return available_proxies
        
        # Sélection diversifiée par pays
        countries = list(set(p.country for p in available_proxies if p.country))
        selected_proxies = []
        
        # Au moins un proxy par pays disponible
        for country in countries[:size]:
            country_proxies = [p for p in available_proxies if p.country == country]
            if country_proxies:
                selected_proxies.append(random.choice(country_proxies))
        
        # Compléter avec des proxies aléatoires
        remaining_size = size - len(selected_proxies)
        if remaining_size > 0:
            remaining_proxies = [p for p in available_proxies if p not in selected_proxies]
            additional_proxies = random.sample(
                remaining_proxies, 
                min(remaining_size, len(remaining_proxies))
            )
            selected_proxies.extend(additional_proxies)
        
        return selected_proxies[:size]
    
    async def health_check(self, proxy: ProxyEndpoint) -> Dict[str, Any]:
        """Vérifie la santé d'un proxy (simulation)"""
        
        # Simuler délai de health check
        response_time = random.randint(50, 1000)
        await asyncio.sleep(response_time / 1000)
        
        # Simuler différents statuts de santé
        health_outcomes = [
            {"status": "healthy", "available": True, "reason": None},
            {"status": "healthy", "available": True, "reason": None},
            {"status": "healthy", "available": True, "reason": None},
            {"status": "slow", "available": True, "reason": "High latency"},
            {"status": "unhealthy", "available": False, "reason": "Connection timeout"},
        ]
        
        outcome = random.choice(health_outcomes)
        proxy.is_healthy = outcome["available"]
        proxy.avg_response_time_ms = response_time
        
        return {
            "proxy_id": proxy.id,
            "proxy_url": proxy.url,
            "status": outcome["status"],
            "available": outcome["available"],
            "reason": outcome["reason"],
            "response_time_ms": response_time,
            "country": proxy.country,
            "region": proxy.region,
            "check_timestamp": datetime.utcnow().isoformat(),
            "mock_provider": True
        }
    
    async def report_proxy_status(self, proxy_id: str, success: bool, response_time_ms: int) -> None:
        """Signale le statut d'utilisation d'un proxy"""
        
        # Trouver le proxy
        proxy = next((p for p in self._proxy_pool if p.id == proxy_id), None)
        
        if proxy:
            # Mettre à jour les stats du proxy
            if success:
                proxy.success_rate = min(0.99, proxy.success_rate + 0.01)
                self._usage_stats["successful_requests"] += 1
            else:
                proxy.success_rate = max(0.50, proxy.success_rate - 0.05)
                self._usage_stats["failed_requests"] += 1
                
                # Marquer comme unhealthy si trop d'échecs
                if proxy.success_rate < 0.70:
                    proxy.is_healthy = False
            
            # Mettre à jour temps de réponse moyen
            proxy.avg_response_time_ms = int(
                (proxy.avg_response_time_ms + response_time_ms) / 2
            )
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques du provider"""
        
        healthy_proxies = [p for p in self._proxy_pool if p.is_healthy]
        countries = list(set(p.country for p in self._proxy_pool if p.country))
        
        return {
            "provider_name": self.provider_name,
            "is_mock": self.is_mock,
            "total_proxies": len(self._proxy_pool),
            "healthy_proxies": len(healthy_proxies),
            "unhealthy_proxies": len(self._proxy_pool) - len(healthy_proxies),
            "countries_available": countries,
            "usage_stats": self._usage_stats.copy(),
            "avg_success_rate": sum(p.success_rate for p in self._proxy_pool) / len(self._proxy_pool),
            "avg_response_time_ms": sum(p.avg_response_time_ms for p in self._proxy_pool) / len(self._proxy_pool),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    @property
    def provider_name(self) -> str:
        return "MockProxyProvider"
    
    @property
    def is_mock(self) -> bool:
        return True

class ProxyProviderFactory:
    """Factory pour créer le provider de proxy approprié"""
    
    def __init__(self):
        self._provider_cache = {}
    
    def get_proxy_provider(self) -> IProxyProvider:
        """Récupère le provider de proxy selon la configuration"""
        
        provider_type = os.getenv("PROXY_PROVIDER", "mock").lower()
        
        if provider_type in self._provider_cache:
            return self._provider_cache[provider_type]
        
        if provider_type == "mock" or provider_type == "none":
            provider = MockProxyProvider()
        elif provider_type == "scraperapi":
            # TODO: Implémentation ScraperAPI
            provider = MockProxyProvider()  # Fallback
        elif provider_type == "brightdata":
            # TODO: Implémentation BrightData
            provider = MockProxyProvider()  # Fallback
        else:
            # Fallback vers mock
            provider = MockProxyProvider()
        
        self._provider_cache[provider_type] = provider
        return provider
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Récupère le statut du provider actuel"""
        
        provider = self.get_proxy_provider()
        provider_type = os.getenv("PROXY_PROVIDER", "mock").lower()
        
        status = provider.get_provider_stats()
        status.update({
            "configured_provider": provider_type,
            "mock_mode": provider.is_mock,
            "proxy_api_key_configured": bool(os.getenv("PROXY_API_KEY")),
            "proxy_endpoint_configured": bool(os.getenv("PROXY_ENDPOINT"))
        })
        
        return status

# Instance globale
proxy_factory = ProxyProviderFactory()