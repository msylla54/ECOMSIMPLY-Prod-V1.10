"""
Hybrid Scraping Service - ECOMSIMPLY Phase 3
Service unifié combinant seo_scraping_service + enhanced_scraping_service
avec retry logic, proxy intelligent, et détection outliers
"""

import asyncio
import time
import os
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics
import random
import json

from .enhanced_scraping_service import EnhancedScrapingService, RetryConfig, ScrapingResult
from .proxy_providers import proxy_factory
from .seo_scraping_service import SEOScrapingService

@dataclass
class OutlierDetectionResult:
    """Résultat de détection d'outliers"""
    outliers_detected: List[Dict[str, Any]]
    clean_prices: List[float]
    method_used: str
    original_count: int
    clean_count: int
    outlier_count: int
    confidence_score: float

@dataclass
class PriceAnalysisResult:
    """Résultat d'analyse de prix complet"""
    found_prices: int
    sources_successful: int
    sources_analyzed: int
    price_statistics: Dict[str, float]
    outlier_analysis: OutlierDetectionResult
    cache_hit: bool
    total_response_time_ms: int
    sources_detail: Dict[str, Any]

class PriceOutlierDetector:
    """Détecteur d'outliers multi-méthodes pour validation prix"""
    
    @staticmethod
    def detect_outliers_zscore(prices: List[float], threshold: float = 2.0) -> Dict[str, Any]:
        """Détection outliers avec Z-score"""
        if len(prices) < 3:
            return {
                "outliers": [], 
                "clean_prices": prices, 
                "method": "zscore_insufficient_data",
                "confidence": 0.1
            }
        
        mean_price = statistics.mean(prices)
        try:
            stdev_price = statistics.stdev(prices)
        except statistics.StatisticsError:
            return {
                "outliers": [], 
                "clean_prices": prices, 
                "method": "zscore_no_variation",
                "confidence": 0.2
            }
        
        if stdev_price == 0:
            return {
                "outliers": [], 
                "clean_prices": prices, 
                "method": "zscore_no_variation",
                "confidence": 0.2
            }
        
        outliers = []
        clean_prices = []
        
        for price in prices:
            zscore = abs(price - mean_price) / stdev_price
            if zscore > threshold:
                outliers.append({"price": price, "zscore": zscore})
            else:
                clean_prices.append(price)
        
        confidence = 0.9 if len(clean_prices) >= len(prices) * 0.7 else 0.6
        
        return {
            "outliers": outliers,
            "clean_prices": clean_prices,
            "method": "zscore",
            "threshold": threshold,
            "confidence": confidence
        }
    
    @staticmethod
    def detect_outliers_contextual(
        prices: List[float], 
        product_name: str, 
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Détection outliers contextuelle avec règles métier"""
        
        # Auto-détection catégorie
        if not category and product_name:
            product_lower = product_name.lower()
            if any(kw in product_lower for kw in ["iphone", "samsung", "galaxy", "smartphone"]):
                category = "smartphone"
            elif any(kw in product_lower for kw in ["macbook", "laptop", "pc", "ordinateur"]):
                category = "laptop"
            elif any(kw in product_lower for kw in ["airpods", "casque", "chargeur", "cable"]):
                category = "accessory"
            else:
                category = "default"
        
        # Règles contextuelles
        rules = {
            "smartphone": {"min": 50, "max": 2500, "reasonable": (200, 1800)},
            "laptop": {"min": 200, "max": 6000, "reasonable": (500, 4000)},
            "accessory": {"min": 5, "max": 500, "reasonable": (20, 350)},
            "default": {"min": 10, "max": 15000, "reasonable": (50, 3000)}
        }.get(category, {"min": 10, "max": 15000, "reasonable": (50, 3000)})
        
        outliers = []
        clean_prices = []
        
        for price in prices:
            reasons = []
            is_outlier = False
            
            # Règles contextuelles strictes
            if price < rules["min"]:
                is_outlier = True
                reasons.append(f"below_min_{rules['min']}")
            elif price > rules["max"]:
                is_outlier = True  
                reasons.append(f"above_max_{rules['max']}")
            
            # Prix suspects
            if price in [9999, 9999.99, 1111, 2222, 3333]:
                is_outlier = True
                reasons.append("suspicious_round_price")
            
            if is_outlier:
                outliers.append({"price": price, "reasons": reasons})
            else:
                clean_prices.append(price)
        
        confidence = 0.95 if category != "default" else 0.7
        
        return {
            "outliers": outliers,
            "clean_prices": clean_prices,
            "method": "contextual",
            "category": category,
            "confidence": confidence
        }
    
    def detect_outliers_combined(
        self, 
        prices: List[float], 
        product_name: str, 
        category: Optional[str] = None
    ) -> OutlierDetectionResult:
        """Détection combinée avec consensus des méthodes"""
        
        if len(prices) == 0:
            return OutlierDetectionResult(
                outliers_detected=[],
                clean_prices=[],
                method_used="no_data",
                original_count=0,
                clean_count=0,
                outlier_count=0,
                confidence_score=0.0
            )
        
        # Application des 3 méthodes
        zscore_result = self.detect_outliers_zscore(prices)
        contextual_result = self.detect_outliers_contextual(prices, product_name, category)
        
        # Union des outliers détectés (approche conservatrice)
        zscore_outliers = {o["price"] for o in zscore_result["outliers"]}
        contextual_outliers = {o["price"] for o in contextual_result["outliers"]}
        
        # Consensus: outlier si détecté par contextuel OU (zscore ET prix > seuil contextuel)
        final_outliers = []
        final_clean = []
        
        for price in prices:
            is_outlier = False
            
            # Priorité à la détection contextuelle (plus fiable)
            if price in contextual_outliers:
                is_outlier = True
                final_outliers.append({
                    "price": price, 
                    "methods": ["contextual"], 
                    "reason": "contextual_rules"
                })
            elif price in zscore_outliers and len(prices) >= 5:
                # Z-score seulement si assez de données ET outlier contextuel pas détecté
                is_outlier = True
                final_outliers.append({
                    "price": price,
                    "methods": ["zscore"], 
                    "reason": "statistical_anomaly"
                })
            
            if not is_outlier:
                final_clean.append(price)
        
        # Score de confiance combiné
        confidence_score = (zscore_result["confidence"] + contextual_result["confidence"]) / 2
        
        return OutlierDetectionResult(
            outliers_detected=final_outliers,
            clean_prices=final_clean,
            method_used="combined_consensus",
            original_count=len(prices),
            clean_count=len(final_clean),
            outlier_count=len(final_outliers),
            confidence_score=confidence_score
        )

class ScrapingCache:
    """Cache court terme pour éviter re-scraping"""
    
    def __init__(self, ttl_seconds: int = 1800):  # 30 minutes par défaut
        self.ttl_seconds = ttl_seconds
        self.memory_cache: Dict[str, Dict] = {}
        self.cache_stats = {"hits": 0, "misses": 0, "invalidations": 0}
    
    def _generate_cache_key(self, product_name: str, sources: List[str]) -> str:
        """Génère clé cache basée sur produit et sources"""
        sources_str = "-".join(sorted(sources))
        product_key = product_name.lower().replace(" ", "_")[:50]
        return f"prices_{product_key}_{sources_str}"
    
    def get_cached_prices(self, product_name: str, sources: List[str]) -> Optional[Dict[str, Any]]:
        """Récupère prix du cache si valides"""
        cache_key = self._generate_cache_key(product_name, sources)
        
        if cache_key not in self.memory_cache:
            self.cache_stats["misses"] += 1
            return None
        
        cached_data = self.memory_cache[cache_key]
        
        # Vérifier expiration
        cached_time = cached_data.get("timestamp", 0)
        if time.time() - cached_time > self.ttl_seconds:
            del self.memory_cache[cache_key]
            self.cache_stats["invalidations"] += 1
            self.cache_stats["misses"] += 1
            return None
        
        self.cache_stats["hits"] += 1
        return cached_data.get("data")
    
    def set_cached_prices(self, product_name: str, sources: List[str], data: Dict[str, Any]) -> None:
        """Stock prix en cache"""
        cache_key = self._generate_cache_key(product_name, sources)
        
        self.memory_cache[cache_key] = {
            "data": data,
            "timestamp": time.time()
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Statistiques du cache"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_ratio = self.cache_stats["hits"] / total_requests if total_requests > 0 else 0
        
        return {
            "total_requests": total_requests,
            "cache_hits": self.cache_stats["hits"],
            "cache_misses": self.cache_stats["misses"],
            "hit_ratio": hit_ratio,
            "cached_entries": len(self.memory_cache),
            "invalidations": self.cache_stats["invalidations"]
        }

class HybridScrapingService:
    """Service de scraping hybride - Phase 3 ECOMSIMPLY"""
    
    def __init__(self):
        # Services de base
        self.enhanced_service = EnhancedScrapingService()
        self.seo_service = SEOScrapingService()
        
        # Configuration retry (from enhanced service)
        self.retry_config = RetryConfig(
            max_attempts=3,
            base_delay_ms=1000,
            exponential_factor=2.0,
            jitter=True
        )
        
        # Providers
        self.proxy_provider = proxy_factory.get_proxy_provider()
        self.outlier_detector = PriceOutlierDetector()
        self.cache = ScrapingCache(ttl_seconds=1800)  # 30 min cache
        
        # Sources étendues (5 plateformes)
        self.price_sources = self._initialize_extended_sources()
        
        # Stats monitoring
        self.monitoring_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_prices_found": 0,
            "total_outliers_detected": 0,
            "avg_response_time_ms": 0,
            "sources_stats": {}
        }
    
    def _initialize_extended_sources(self) -> List[Dict[str, Any]]:
        """Initialise les 5 sources de prix étendues"""
        return [
            {
                "name": "amazon",
                "weight": 0.35,
                "priority": 1,
                "retry_max": 3,
                "expected_success_rate": 0.85
            },
            {
                "name": "fnac", 
                "weight": 0.25,
                "priority": 2,
                "retry_max": 2,
                "expected_success_rate": 0.90
            },
            {
                "name": "cdiscount",
                "weight": 0.20,
                "priority": 3,
                "retry_max": 2,
                "expected_success_rate": 0.92
            },
            {
                "name": "google_shopping",
                "weight": 0.15,
                "priority": 4,
                "retry_max": 2,
                "expected_success_rate": 0.88
            },
            {
                "name": "aliexpress",
                "weight": 0.05,
                "priority": 5,
                "retry_max": 3,
                "expected_success_rate": 0.80
            }
        ]
    
    async def scrape_prices_unified(
        self, 
        product_name: str, 
        category: Optional[str] = None,
        use_cache: bool = True
    ) -> PriceAnalysisResult:
        """
        Scraping unifié avec retry, proxy, outliers et cache
        Point d'entrée principal Phase 3
        """
        
        start_time = time.time()
        self.monitoring_stats["total_requests"] += 1
        
        # Extraction des sources à utiliser
        sources_to_use = [source["name"] for source in self.price_sources]
        
        # 1. Vérification cache
        cached_result = None
        if use_cache:
            cached_result = self.cache.get_cached_prices(product_name, sources_to_use)
            if cached_result:
                return PriceAnalysisResult(
                    found_prices=cached_result["found_prices"],
                    sources_successful=cached_result["sources_successful"],
                    sources_analyzed=cached_result["sources_analyzed"],
                    price_statistics=cached_result["price_statistics"],
                    outlier_analysis=OutlierDetectionResult(**cached_result["outlier_analysis"]),
                    cache_hit=True,
                    total_response_time_ms=int((time.time() - start_time) * 1000),
                    sources_detail=cached_result["sources_detail"]
                )
        
        # 2. Scraping multi-sources avec enhanced service
        scraping_result = await self.enhanced_service.scrape_competitor_prices_enhanced(
            product_name=product_name,
            category=category,
            sources=sources_to_use
        )
        
        # 3. Extraction prix de tous les résultats
        all_prices = []
        sources_detail = {}
        
        scraped_results = scraping_result.get("scraped_results", {})
        for source_name, source_data in scraped_results.items():
            products = source_data.get("products", [])
            source_prices = []
            
            for product in products:
                if "price" in product and isinstance(product["price"], (int, float)):
                    price = float(product["price"])
                    all_prices.append(price)
                    source_prices.append(price)
            
            sources_detail[source_name] = {
                "prices_found": len(source_prices),
                "prices": source_prices,
                "success": len(source_prices) > 0,
                "avg_price": sum(source_prices) / len(source_prices) if source_prices else 0
            }
        
        # 4. Détection et suppression outliers
        outlier_analysis = self.outlier_detector.detect_outliers_combined(
            all_prices, product_name, category
        )
        
        # 5. Calculs statistiques finaux sur prix propres
        clean_prices = outlier_analysis.clean_prices
        price_stats = {}
        
        if clean_prices:
            price_stats = {
                "min_price": min(clean_prices),
                "max_price": max(clean_prices),
                "avg_price": round(sum(clean_prices) / len(clean_prices), 2),
                "median_price": round(statistics.median(clean_prices), 2),
                "price_range": round(max(clean_prices) - min(clean_prices), 2),
                "price_variance": round(statistics.variance(clean_prices), 2) if len(clean_prices) > 1 else 0
            }
        
        # 6. Création résultat final
        total_response_time = int((time.time() - start_time) * 1000)
        
        final_result = PriceAnalysisResult(
            found_prices=len(all_prices),
            sources_successful=scraping_result.get("sources_successful", 0),
            sources_analyzed=scraping_result.get("sources_analyzed", 0),
            price_statistics=price_stats,
            outlier_analysis=outlier_analysis,
            cache_hit=False,
            total_response_time_ms=total_response_time,
            sources_detail=sources_detail
        )
        
        # 7. Mise en cache si succès
        if all_prices and use_cache:
            cache_data = {
                "found_prices": final_result.found_prices,
                "sources_successful": final_result.sources_successful,
                "sources_analyzed": final_result.sources_analyzed,
                "price_statistics": final_result.price_statistics,
                "outlier_analysis": {
                    "outliers_detected": final_result.outlier_analysis.outliers_detected,
                    "clean_prices": final_result.outlier_analysis.clean_prices,
                    "method_used": final_result.outlier_analysis.method_used,
                    "original_count": final_result.outlier_analysis.original_count,
                    "clean_count": final_result.outlier_analysis.clean_count,
                    "outlier_count": final_result.outlier_analysis.outlier_count,
                    "confidence_score": final_result.outlier_analysis.confidence_score
                },
                "sources_detail": final_result.sources_detail
            }
            self.cache.set_cached_prices(product_name, sources_to_use, cache_data)
        
        # 8. Mise à jour stats monitoring
        self._update_monitoring_stats(final_result, scraping_result)
        
        return final_result
    
    def _update_monitoring_stats(self, result: PriceAnalysisResult, raw_result: Dict) -> None:
        """Met à jour les statistiques de monitoring"""
        
        if result.found_prices > 0:
            self.monitoring_stats["successful_requests"] += 1
        else:
            self.monitoring_stats["failed_requests"] += 1
        
        self.monitoring_stats["total_prices_found"] += result.found_prices
        self.monitoring_stats["total_outliers_detected"] += result.outlier_analysis.outlier_count
        
        # Moyenne mobile temps de réponse
        current_avg = self.monitoring_stats["avg_response_time_ms"]
        total_requests = self.monitoring_stats["total_requests"]
        new_avg = ((current_avg * (total_requests - 1)) + result.total_response_time_ms) / total_requests
        self.monitoring_stats["avg_response_time_ms"] = round(new_avg, 2)
        
        # Stats par source
        for source_name, source_detail in result.sources_detail.items():
            if source_name not in self.monitoring_stats["sources_stats"]:
                self.monitoring_stats["sources_stats"][source_name] = {
                    "requests": 0, "successes": 0, "total_prices": 0
                }
            
            source_stats = self.monitoring_stats["sources_stats"][source_name]
            source_stats["requests"] += 1
            if source_detail["success"]:
                source_stats["successes"] += 1
            source_stats["total_prices"] += source_detail["prices_found"]
    
    def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Données pour dashboard monitoring mock"""
        
        # Stats générales
        success_rate = 0
        if self.monitoring_stats["total_requests"] > 0:
            success_rate = self.monitoring_stats["successful_requests"] / self.monitoring_stats["total_requests"]
        
        # Stats par source avec taux de succès
        sources_performance = {}
        for source_name, stats in self.monitoring_stats["sources_stats"].items():
            source_success_rate = stats["successes"] / stats["requests"] if stats["requests"] > 0 else 0
            sources_performance[source_name] = {
                "success_rate": round(source_success_rate, 3),
                "total_requests": stats["requests"],
                "avg_prices_per_request": stats["total_prices"] / stats["requests"] if stats["requests"] > 0 else 0
            }
        
        # Stats cache
        cache_stats = self.cache.get_cache_stats()
        
        # Stats proxy
        proxy_stats = self.proxy_provider.get_provider_stats()
        
        return {
            "overview": {
                "total_requests": self.monitoring_stats["total_requests"],
                "success_rate": round(success_rate, 3),
                "avg_response_time_ms": self.monitoring_stats["avg_response_time_ms"],
                "total_prices_found": self.monitoring_stats["total_prices_found"],
                "outliers_detected": self.monitoring_stats["total_outliers_detected"]
            },
            "sources_performance": sources_performance,
            "cache_performance": cache_stats,
            "proxy_health": {
                "healthy_proxies": proxy_stats.get("healthy_proxies", 0),
                "total_proxies": proxy_stats.get("total_proxies", 0),
                "avg_success_rate": proxy_stats.get("avg_success_rate", 0)
            },
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def get_system_health_status(self) -> Dict[str, Any]:
        """Status santé du système pour monitoring"""
        
        dashboard_data = self.get_monitoring_dashboard_data()
        
        # Calcul status général
        overall_success_rate = dashboard_data["overview"]["success_rate"]
        proxy_health = dashboard_data["proxy_health"]["healthy_proxies"] / dashboard_data["proxy_health"]["total_proxies"] if dashboard_data["proxy_health"]["total_proxies"] > 0 else 0
        cache_hit_ratio = dashboard_data["cache_performance"]["hit_ratio"]
        
        # Détermination status
        if overall_success_rate >= 0.95 and proxy_health >= 0.85:
            system_status = "healthy"
        elif overall_success_rate >= 0.80 and proxy_health >= 0.70:
            system_status = "degraded" 
        else:
            system_status = "unhealthy"
        
        return {
            "system_status": system_status,
            "components": {
                "scraping_service": "healthy" if overall_success_rate >= 0.80 else "degraded",
                "proxy_provider": "healthy" if proxy_health >= 0.85 else "degraded",
                "cache_system": "healthy" if cache_hit_ratio >= 0.40 else "degraded",
                "outlier_detection": "healthy"  # Toujours sain en mock
            },
            "metrics": dashboard_data,
            "recommendations": self._generate_health_recommendations(dashboard_data)
        }
    
    def _generate_health_recommendations(self, dashboard_data: Dict) -> List[str]:
        """Génère recommandations basées sur performance"""
        recommendations = []
        
        overview = dashboard_data["overview"]
        cache_perf = dashboard_data["cache_performance"]
        proxy_health = dashboard_data["proxy_health"]
        
        if overview["success_rate"] < 0.85:
            recommendations.append("Taux succès faible: vérifier santé sources et proxies")
        
        if overview["avg_response_time_ms"] > 10000:
            recommendations.append("Temps réponse élevé: optimiser retry ou ajouter proxies")
        
        if cache_perf["hit_ratio"] < 0.40:
            recommendations.append("Cache hit ratio faible: augmenter TTL ou optimiser clés")
        
        if proxy_health["healthy_proxies"] / proxy_health["total_proxies"] < 0.80:
            recommendations.append("Santé proxy dégradée: vérifier pool et rotation")
        
        if overview["outliers_detected"] > overview["total_prices_found"] * 0.15:
            recommendations.append("Taux outliers élevé: vérifier règles détection")
        
        return recommendations

# Instance globale
hybrid_scraping_service = HybridScrapingService()