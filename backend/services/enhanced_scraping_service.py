"""
Enhanced Scraping Service - ECOMSIMPLY
Version améliorée avec simulation contrôlée, retry logic et datasets configurables
"""

import asyncio
import random
import os
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from collections import defaultdict

from .proxy_providers import proxy_factory, IProxyProvider, ProxyEndpoint

@dataclass
class ScrapingResult:
    """Résultat d'une opération de scraping"""
    success: bool
    data: Dict[str, Any]
    source: str
    response_time_ms: int
    proxy_used: Optional[str] = None
    attempt_number: int = 1
    error_message: Optional[str] = None
    error_type: Optional[str] = None

@dataclass 
class RetryConfig:
    """Configuration des retry pour scraping"""
    max_attempts: int = 3
    base_delay_ms: int = 1000
    max_delay_ms: int = 10000
    exponential_factor: float = 2.0
    jitter: bool = True

class ScrapingDatasets:
    """Gestionnaire des datasets de scraping mock"""
    
    def __init__(self):
        self._datasets = {
            "default": self._create_default_dataset(),
            "extended": self._create_extended_dataset()
        }
    
    def _create_default_dataset(self) -> Dict[str, Any]:
        """Dataset par défaut - données basiques"""
        return {
            "competitor_prices": {
                "amazon": [
                    {"name": "iPhone 15 Pro", "price": 1229.99, "currency": "EUR", "availability": "in_stock"},
                    {"name": "Samsung Galaxy S24", "price": 899.99, "currency": "EUR", "availability": "in_stock"}, 
                    {"name": "MacBook Air M2", "price": 1199.99, "currency": "EUR", "availability": "limited"},
                    {"name": "AirPods Pro", "price": 279.99, "currency": "EUR", "availability": "in_stock"},
                    {"name": "iPad Pro", "price": 899.99, "currency": "EUR", "availability": "in_stock"}
                ],
                "fnac": [
                    {"name": "iPhone 15 Pro", "price": 1199.99, "currency": "EUR", "availability": "in_stock"},
                    {"name": "Samsung Galaxy S24", "price": 849.99, "currency": "EUR", "availability": "in_stock"},
                    {"name": "MacBook Air M2", "price": 1249.99, "currency": "EUR", "availability": "in_stock"},
                    {"name": "AirPods Pro", "price": 259.99, "currency": "EUR", "availability": "limited"}
                ]
            },
            "seo_data": {
                "keywords": ["premium", "qualité", "innovation", "design", "performance"],
                "popular_titles": [
                    "Produit Premium de Qualité Supérieure", 
                    "Innovation et Design Moderne",
                    "Performance Exceptionnelle"
                ],
                "descriptions": [
                    "Découvrez ce produit exceptionnel alliant qualité et innovation",
                    "Design moderne et performance optimale pour une expérience unique"
                ]
            },
            "trending_keywords": ["tendance", "populaire", "nouveau", "exclusif", "recommandé"]
        }
    
    def _create_extended_dataset(self) -> Dict[str, Any]:
        """Dataset étendu - données plus riches"""
        extended = self._create_default_dataset().copy()
        
        # Ajouter plus de sources prix
        extended["competitor_prices"]["cdiscount"] = [
            {"name": "iPhone 15 Pro", "price": 1189.99, "currency": "EUR", "availability": "in_stock"},
            {"name": "Samsung Galaxy S24", "price": 829.99, "currency": "EUR", "availability": "in_stock"},
            {"name": "Xiaomi 14", "price": 599.99, "currency": "EUR", "availability": "in_stock"}
        ]
        
        extended["competitor_prices"]["aliexpress"] = [
            {"name": "iPhone 15 Pro", "price": 1099.99, "currency": "EUR", "availability": "pre_order"},
            {"name": "Samsung Galaxy S24", "price": 789.99, "currency": "EUR", "availability": "in_stock"},
            {"name": "OnePlus 12", "price": 699.99, "currency": "EUR", "availability": "in_stock"}
        ]
        
        extended["competitor_prices"]["google_shopping"] = [
            {"name": "iPhone 15 Pro", "price": 1249.99, "currency": "EUR", "availability": "in_stock"},
            {"name": "Samsung Galaxy S24", "price": 879.99, "currency": "EUR", "availability": "in_stock"}
        ]
        
        # Enrichir les données SEO
        extended["seo_data"]["keywords"].extend([
            "haut de gamme", "technologie", "élégant", "fiable", "durable",
            "intelligent", "connecté", "éco-responsable", "garanti"
        ])
        
        extended["trending_keywords"].extend([
            "viral", "tendance 2025", "must-have", "coup de cœur", 
            "édition limitée", "bestseller"
        ])
        
        return extended
    
    def get_dataset(self, dataset_name: str = "default") -> Dict[str, Any]:
        """Récupère un dataset par nom"""
        return self._datasets.get(dataset_name, self._datasets["default"])
    
    def get_competitor_data(self, product_name: str, dataset_name: str = "default") -> Dict[str, List[Dict]]:
        """Récupère les données concurrentes pour un produit"""
        dataset = self.get_dataset(dataset_name)
        competitor_prices = dataset.get("competitor_prices", {})
        
        # Simulation de recherche par nom de produit
        results = {}
        
        for source, products in competitor_prices.items():
            matching_products = []
            for product in products:
                # Simulation de matching par similarité de nom
                if self._matches_product(product_name, product["name"]):
                    # Ajouter variation de prix pour réalisme
                    varied_price = self._add_price_variation(product["price"])
                    matching_product = product.copy()
                    matching_product["price"] = varied_price
                    matching_products.append(matching_product)
            
            if matching_products:
                results[source] = matching_products
        
        return results
    
    def _matches_product(self, search_name: str, product_name: str) -> bool:
        """Simulation de matching de produit"""
        search_words = set(search_name.lower().split())
        product_words = set(product_name.lower().split())
        
        # Match si au moins 30% des mots correspondent
        if len(search_words) == 0:
            return False
        
        common_words = search_words.intersection(product_words)
        return len(common_words) / len(search_words) >= 0.3
    
    def _add_price_variation(self, base_price: float) -> float:
        """Ajoute une variation réaliste au prix"""
        variation = random.uniform(-0.1, 0.1)  # ±10%
        return round(base_price * (1 + variation), 2)

class EnhancedScrapingService:
    """Service de scraping amélioré avec simulation contrôlée"""
    
    def __init__(self):
        self.proxy_provider: IProxyProvider = proxy_factory.get_proxy_provider()
        self.datasets = ScrapingDatasets()
        self.retry_config = RetryConfig()
        self._scraping_stats = defaultdict(int)
        self._error_counts = defaultdict(int)
    
    async def scrape_competitor_prices_enhanced(
        self, 
        product_name: str, 
        category: Optional[str] = None,
        sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Scraping prix concurrent avec retry et simulation avancée"""
        
        dataset_name = os.getenv("SCRAPING_SOURCE_SET", "default")
        
        # Sélection des sources
        if not sources:
            if dataset_name == "extended":
                sources = ["amazon", "fnac", "cdiscount", "aliexpress", "google_shopping"]
            else:
                sources = ["amazon", "fnac"]
        
        competitor_data = self.datasets.get_competitor_data(product_name, dataset_name)
        
        # Simulation de scraping avec retry pour chaque source
        scraped_results = {}
        total_found_prices = 0
        all_prices = []
        
        for source in sources:
            if source in competitor_data:
                result = await self._scrape_source_with_retry(
                    source, 
                    competitor_data[source], 
                    product_name
                )
                
                scraped_results[source] = result
                
                if result.success and result.data.get("products"):
                    prices = [p["price"] for p in result.data["products"]]
                    all_prices.extend(prices)
                    total_found_prices += len(prices)
        
        # Calculs statistiques
        price_stats = {}
        if all_prices:
            price_stats = {
                "min_price": min(all_prices),
                "max_price": max(all_prices),
                "avg_price": round(sum(all_prices) / len(all_prices), 2),
                "median_price": round(sorted(all_prices)[len(all_prices) // 2], 2),
                "price_range": round(max(all_prices) - min(all_prices), 2)
            }
        
        # Mettre à jour les stats
        self._scraping_stats["competitor_price_requests"] += 1
        if all_prices:
            self._scraping_stats["competitor_price_successes"] += 1
        
        return {
            "found_prices": total_found_prices,
            "sources_analyzed": len(sources),
            "sources_successful": len([r for r in scraped_results.values() if r.success]),
            "sources_failed": len([r for r in scraped_results.values() if not r.success]),
            "scraped_results": {k: v.data for k, v in scraped_results.items()},
            "price_statistics": price_stats,
            "dataset_used": dataset_name,
            "scraping_timestamp": datetime.utcnow().isoformat(),
            "total_attempts": sum(r.attempt_number for r in scraped_results.values()),
            "avg_response_time_ms": sum(r.response_time_ms for r in scraped_results.values()) / len(scraped_results) if scraped_results else 0
        }
    
    async def _scrape_source_with_retry(
        self, 
        source: str, 
        source_data: List[Dict], 
        product_name: str
    ) -> ScrapingResult:
        """Scrape une source avec retry logic"""
        
        last_error = None
        
        for attempt in range(1, self.retry_config.max_attempts + 1):
            try:
                # Obtenir un proxy
                proxy = await self.proxy_provider.get_proxy()
                
                # Simulation de scraping
                result = await self._simulate_source_scraping(
                    source, source_data, product_name, proxy, attempt
                )
                
                # Signaler le statut du proxy
                if proxy:
                    await self.proxy_provider.report_proxy_status(
                        proxy.id, result.success, result.response_time_ms
                    )
                
                if result.success:
                    return result
                
                last_error = result.error_message
                
                # Attendre avant retry
                if attempt < self.retry_config.max_attempts:
                    await self._wait_before_retry(attempt)
                
            except Exception as e:
                last_error = str(e)
                if attempt < self.retry_config.max_attempts:
                    await self._wait_before_retry(attempt)
        
        # Échec après tous les retry
        self._error_counts[source] += 1
        
        return ScrapingResult(
            success=False,
            data={"products": [], "error": "Max retries exceeded"},
            source=source,
            response_time_ms=0,
            attempt_number=self.retry_config.max_attempts,
            error_message=last_error,
            error_type="retry_exhausted"
        )
    
    async def _simulate_source_scraping(
        self, 
        source: str, 
        source_data: List[Dict], 
        product_name: str,
        proxy: Optional[ProxyEndpoint],
        attempt: int
    ) -> ScrapingResult:
        """Simule le scraping d'une source"""
        
        # Temps de réponse simulé
        base_response_time = random.randint(200, 1500)
        if proxy:
            # Ajouter la latence du proxy
            proxy_latency = proxy.avg_response_time_ms
            response_time = base_response_time + proxy_latency
        else:
            response_time = base_response_time + 200  # Pénalité sans proxy
        
        # Simuler délai réseau
        await asyncio.sleep(response_time / 1000)
        
        # Taux de succès basé sur la source et le proxy
        success_rate = 0.9  # Base
        
        if proxy:
            success_rate *= proxy.success_rate
        else:
            success_rate *= 0.7  # Pénalité sans proxy
        
        # Pénalité par attempt
        success_rate *= (1.0 - (attempt - 1) * 0.1)
        
        # Simulation d'erreurs spécifiques par source
        source_error_rates = {
            "amazon": 0.15,      # Plus difficile à scraper
            "fnac": 0.10,        # Modéré
            "cdiscount": 0.08,   # Plus facile
            "aliexpress": 0.20,  # Très difficile
            "google_shopping": 0.12
        }
        
        success_rate *= (1.0 - source_error_rates.get(source, 0.1))
        
        # Déterminer le résultat
        is_success = random.random() < success_rate
        
        if is_success:
            return ScrapingResult(
                success=True,
                data={
                    "products": source_data,
                    "source": source,
                    "scraped_count": len(source_data),
                    "proxy_country": proxy.country if proxy else None
                },
                source=source,
                response_time_ms=response_time,
                proxy_used=proxy.id if proxy else None,
                attempt_number=attempt
            )
        else:
            # Simulation d'erreurs réalistes
            error_types = [
                ("rate_limited", "Rate limit exceeded by source"),
                ("blocked", "Request blocked by anti-bot"),
                ("timeout", "Connection timeout"),
                ("parsing_error", "Failed to parse response"),
                ("proxy_error", "Proxy connection failed")
            ]
            
            error_type, error_message = random.choice(error_types)
            
            return ScrapingResult(
                success=False,
                data={"products": [], "error": error_message},
                source=source,
                response_time_ms=response_time,
                proxy_used=proxy.id if proxy else None,
                attempt_number=attempt,
                error_message=error_message,
                error_type=error_type
            )
    
    async def _wait_before_retry(self, attempt: int) -> None:
        """Attend avant un retry avec backoff exponentiel"""
        
        delay = min(
            self.retry_config.base_delay_ms * (self.retry_config.exponential_factor ** (attempt - 1)),
            self.retry_config.max_delay_ms
        )
        
        if self.retry_config.jitter:
            # Ajouter du jitter pour éviter les retry simultanés
            jitter = random.uniform(0.5, 1.5)
            delay *= jitter
        
        await asyncio.sleep(delay / 1000)
    
    async def scrape_seo_data_enhanced(
        self, 
        product_name: str, 
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Scraping données SEO avec simulation enrichie"""
        
        dataset_name = os.getenv("SCRAPING_SOURCE_SET", "default")
        dataset = self.datasets.get_dataset(dataset_name)
        seo_base_data = dataset.get("seo_data", {})
        
        # Simulation de scraping SEO multi-sources
        seo_result = await self._simulate_seo_scraping(seo_base_data, product_name)
        
        self._scraping_stats["seo_requests"] += 1
        if seo_result.success:
            self._scraping_stats["seo_successes"] += 1
        
        return seo_result.data
    
    async def _simulate_seo_scraping(self, seo_data: Dict, product_name: str) -> ScrapingResult:
        """Simule le scraping de données SEO"""
        
        # Temps de réponse simulé
        response_time = random.randint(300, 800)
        await asyncio.sleep(response_time / 1000)
        
        # Succès simulé (95% de réussite pour SEO)
        if random.random() < 0.95:
            # Contextualiser les données selon le produit
            contextualized_keywords = []
            for keyword in seo_data.get("keywords", []):
                contextualized_keywords.append(keyword)
            
            # Ajouter des keywords contextuels
            product_words = product_name.lower().split()
            for word in product_words:
                if len(word) > 3:  # Éviter les mots trop courts
                    contextualized_keywords.append(word)
            
            return ScrapingResult(
                success=True,
                data={
                    "keywords": list(set(contextualized_keywords)),  # Dédupliqué
                    "titles": seo_data.get("popular_titles", []),
                    "descriptions": seo_data.get("descriptions", []),
                    "context_keywords": product_words,
                    "total_keywords_found": len(contextualized_keywords),
                    "source": "mock_seo_aggregator"
                },
                source="seo_data",
                response_time_ms=response_time
            )
        else:
            return ScrapingResult(
                success=False,
                data={"keywords": [], "error": "SEO data scraping failed"},
                source="seo_data",
                response_time_ms=response_time,
                error_message="Mock SEO scraping failure",
                error_type="seo_timeout"
            )
    
    async def fetch_trending_keywords_enhanced(
        self, 
        product_name: str, 
        category: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Récupération mots-clés tendance avec dataset configurable"""
        
        dataset_name = os.getenv("SCRAPING_SOURCE_SET", "default")
        dataset = self.datasets.get_dataset(dataset_name)
        trending_base = dataset.get("trending_keywords", [])
        
        # Simulation avec proxy
        proxy = await self.proxy_provider.get_proxy()
        
        response_time = random.randint(500, 1200)
        await asyncio.sleep(response_time / 1000)
        
        # Contextualiser les trending keywords
        contextualized_trending = []
        
        # Ajouter des trending keywords basés sur la catégorie
        if category:
            category_trends = {
                "Electronics": ["tech", "gadget", "innovation"],
                "Fashion": ["style", "tendance", "mode"],
                "Sports": ["performance", "sport", "fitness"],
                "Home": ["maison", "décoration", "confort"]
            }
            
            category_keywords = category_trends.get(category, [])
            contextualized_trending.extend(category_keywords)
        
        # Ajouter les trending de base
        selected_trending = random.sample(
            trending_base, 
            min(len(trending_base), random.randint(3, 8))
        )
        contextualized_trending.extend(selected_trending)
        
        if proxy:
            await self.proxy_provider.report_proxy_status(proxy.id, True, response_time)
        
        self._scraping_stats["trending_requests"] += 1
        self._scraping_stats["trending_successes"] += 1
        
        return {
            "keywords": list(set(contextualized_trending)),
            "confidence": random.uniform(0.7, 0.95),
            "source": f"mock_trends_{dataset_name}",
            "category_enhanced": bool(category),
            "total_trending_found": len(contextualized_trending),
            "proxy_country": proxy.country if proxy else None,
            "response_time_ms": response_time,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_scraping_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques de scraping"""
        
        return {
            "scraping_stats": dict(self._scraping_stats),
            "error_counts": dict(self._error_counts),
            "proxy_stats": self.proxy_provider.get_provider_stats(),
            "retry_config": {
                "max_attempts": self.retry_config.max_attempts,
                "base_delay_ms": self.retry_config.base_delay_ms,
                "exponential_factor": self.retry_config.exponential_factor,
                "jitter_enabled": self.retry_config.jitter
            },
            "datasets_available": list(self.datasets._datasets.keys()),
            "current_dataset": os.getenv("SCRAPING_SOURCE_SET", "default"),
            "last_updated": datetime.utcnow().isoformat()
        }

# Instance globale
enhanced_scraping_service = EnhancedScrapingService()