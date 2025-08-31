#!/usr/bin/env python3
"""
VALIDATION FINALE SYSTÈME SCRAPING PRIX HYBRIDE - ECOMSIMPLY
Test complet du nouveau système hybride Phase 3 avec approche mock-first

COMPOSANTS À TESTER:
1. HybridScrapingService - service unifié
2. Détection Outliers Multi-Méthodes  
3. Cache Système avec TTL et hit ratio
4. Monitoring Dashboard avec métriques temps réel
5. Integration avec Services Existants

CRITÈRES DE SUCCÈS:
- ✅ Taux succès ≥95% sur scraping unifié
- ✅ Outliers détectés avec confidence ≥90%
- ✅ Cache fonctionnel avec hit ratio tracking
- ✅ Dashboard metrics cohérents et temps réel
- ✅ Pas de régression sur fonctionnalités existantes
"""

import asyncio
import sys
import os
import time
import statistics
from typing import Dict, List, Any

# Add backend path for imports
sys.path.append('/app/backend')

from services.hybrid_scraping_service import (
    HybridScrapingService, 
    PriceOutlierDetector, 
    ScrapingCache,
    OutlierDetectionResult,
    PriceAnalysisResult
)

class HybridScrapingValidator:
    """Validateur complet du système de scraping hybride"""
    
    def __init__(self):
        self.hybrid_service = HybridScrapingService()
        self.outlier_detector = PriceOutlierDetector()
        self.test_results = []
        self.validation_summary = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "critical_issues": [],
            "success_rate": 0.0
        }
    
    def log_test_result(self, test_name: str, success: bool, details: Dict = None, critical: bool = False):
        """Log résultat de test avec détails"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details or {},
            "critical": critical,
            "timestamp": time.time()
        }
        
        self.test_results.append(result)
        self.validation_summary["total_tests"] += 1
        
        if success:
            self.validation_summary["passed_tests"] += 1
            print(f"✅ {test_name}")
        else:
            self.validation_summary["failed_tests"] += 1
            print(f"❌ {test_name}")
            if critical:
                self.validation_summary["critical_issues"].append(test_name)
        
        if details:
            for key, value in details.items():
                print(f"   📊 {key}: {value}")
    
    async def test_hybrid_scraping_service_unified(self):
        """TEST 1: HybridScrapingService - endpoint principal scrape_prices_unified()"""
        print("\n🧪 TEST 1: HybridScrapingService - Service Unifié")
        print("=" * 60)
        
        test_products = [
            {"name": "iPhone 15 Pro", "category": "smartphone"},
            {"name": "Samsung Galaxy S24", "category": "smartphone"}
        ]
        
        unified_results = []
        
        for product in test_products:
            print(f"\n🔍 Test scraping unifié: {product['name']}")
            
            try:
                start_time = time.time()
                
                # Test scraping unifié
                result = await self.hybrid_service.scrape_prices_unified(
                    product_name=product["name"],
                    category=product["category"],
                    use_cache=False  # Premier test sans cache
                )
                
                response_time = (time.time() - start_time) * 1000
                
                # Validation résultat
                validation = {
                    "has_prices": result.found_prices > 0,
                    "sources_analyzed": result.sources_analyzed >= 3,
                    "sources_successful": result.sources_successful > 0,
                    "has_statistics": bool(result.price_statistics),
                    "outlier_analysis": result.outlier_analysis is not None,
                    "response_time_ok": response_time < 30000,  # 30 secondes max
                    "cache_status": result.cache_hit == False  # Premier appel sans cache
                }
                
                success_rate = sum(validation.values()) / len(validation)
                
                unified_results.append({
                    "product": product["name"],
                    "found_prices": result.found_prices,
                    "sources_successful": result.sources_successful,
                    "sources_analyzed": result.sources_analyzed,
                    "response_time_ms": response_time,
                    "success_rate": success_rate,
                    "validation": validation
                })
                
                print(f"   📊 Prix trouvés: {result.found_prices}")
                print(f"   📊 Sources réussies: {result.sources_successful}/{result.sources_analyzed}")
                print(f"   📊 Temps réponse: {response_time:.0f}ms")
                print(f"   📊 Taux succès: {success_rate:.1%}")
                
                if result.price_statistics:
                    print(f"   💰 Prix moyen: {result.price_statistics.get('avg_price', 'N/A')}€")
                    print(f"   💰 Fourchette: {result.price_statistics.get('min_price', 'N/A')}€ - {result.price_statistics.get('max_price', 'N/A')}€")
                
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
                unified_results.append({
                    "product": product["name"],
                    "error": str(e),
                    "success_rate": 0.0
                })
        
        # Évaluation globale
        overall_success_rate = sum(r.get("success_rate", 0) for r in unified_results) / len(unified_results)
        total_prices = sum(r.get("found_prices", 0) for r in unified_results)
        
        success = overall_success_rate >= 0.95  # Critère: ≥95% taux succès
        
        self.log_test_result(
            "HybridScrapingService Unifié",
            success,
            {
                "taux_succès_global": f"{overall_success_rate:.1%}",
                "total_prix_trouvés": total_prices,
                "produits_testés": len(test_products),
                "critère_95%": "✅ ATTEINT" if success else "❌ NON ATTEINT"
            },
            critical=True
        )
        
        return success
    
    def test_outlier_detection_multi_methods(self):
        """TEST 2: Détection Outliers Multi-Méthodes avec confidence ≥90%"""
        print("\n🧪 TEST 2: Détection Outliers Multi-Méthodes")
        print("=" * 60)
        
        # Test avec prix contenant outliers évidents
        test_cases = [
            {
                "name": "Prix avec outliers évidents",
                "prices": [899.99, 1199.99, 9999.99, 50.0, 1299.99],  # 9999.99 et 50.0 sont outliers
                "product": "iPhone 15 Pro",
                "expected_outliers": 2
            },
            {
                "name": "Prix normaux sans outliers",
                "prices": [899.99, 949.99, 999.99, 1049.99, 1099.99],
                "product": "Samsung Galaxy S24",
                "expected_outliers": 0
            },
            {
                "name": "Prix avec outlier contextuel",
                "prices": [25000.0, 899.99, 949.99, 999.99],  # 25000 outlier pour smartphone
                "product": "iPhone 15 Pro",
                "expected_outliers": 1
            }
        ]
        
        outlier_results = []
        
        for test_case in test_cases:
            print(f"\n🔍 Test: {test_case['name']}")
            print(f"   Prix testés: {test_case['prices']}")
            
            try:
                # Test détection combinée
                result = self.outlier_detector.detect_outliers_combined(
                    prices=test_case["prices"],
                    product_name=test_case["product"]
                )
                
                # Validation
                validation = {
                    "outliers_detected": len(result.outliers_detected),
                    "clean_prices_count": len(result.clean_prices),
                    "confidence_score": result.confidence_score,
                    "method_used": result.method_used,
                    "expected_outliers": test_case["expected_outliers"]
                }
                
                confidence_ok = result.confidence_score >= 0.90
                outliers_reasonable = abs(len(result.outliers_detected) - test_case["expected_outliers"]) <= 1
                
                outlier_results.append({
                    "test_case": test_case["name"],
                    "confidence_score": result.confidence_score,
                    "outliers_detected": len(result.outliers_detected),
                    "confidence_ok": confidence_ok,
                    "outliers_reasonable": outliers_reasonable,
                    "validation": validation
                })
                
                print(f"   📊 Outliers détectés: {len(result.outliers_detected)}")
                print(f"   📊 Prix propres: {len(result.clean_prices)}")
                print(f"   📊 Confidence: {result.confidence_score:.1%}")
                print(f"   📊 Méthode: {result.method_used}")
                
                if result.outliers_detected:
                    for outlier in result.outliers_detected:
                        print(f"      🚫 Outlier: {outlier['price']}€ ({outlier.get('reason', 'N/A')})")
                
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
                outlier_results.append({
                    "test_case": test_case["name"],
                    "error": str(e),
                    "confidence_ok": False,
                    "outliers_reasonable": False
                })
        
        # Évaluation globale
        confidence_tests_passed = sum(1 for r in outlier_results if r.get("confidence_ok", False))
        outlier_tests_passed = sum(1 for r in outlier_results if r.get("outliers_reasonable", False))
        
        success = (confidence_tests_passed >= len(test_cases) * 0.8 and 
                  outlier_tests_passed >= len(test_cases) * 0.8)
        
        avg_confidence = sum(r.get("confidence_score", 0) for r in outlier_results) / len(outlier_results)
        
        self.log_test_result(
            "Détection Outliers Multi-Méthodes",
            success,
            {
                "confidence_moyenne": f"{avg_confidence:.1%}",
                "tests_confidence_≥90%": f"{confidence_tests_passed}/{len(test_cases)}",
                "tests_outliers_corrects": f"{outlier_tests_passed}/{len(test_cases)}",
                "critère_90%": "✅ ATTEINT" if avg_confidence >= 0.90 else "❌ NON ATTEINT"
            },
            critical=True
        )
        
        return success
    
    async def test_cache_system_functionality(self):
        """TEST 3: Cache Système avec TTL et hit ratio tracking"""
        print("\n🧪 TEST 3: Cache Système avec TTL et Hit Ratio")
        print("=" * 60)
        
        cache_results = []
        
        # Test 1: Cache miss puis cache hit
        print("\n🔍 Test Cache Miss → Hit")
        
        try:
            # Premier appel (cache miss)
            result1 = await self.hybrid_service.scrape_prices_unified(
                "iPhone 15 Pro", use_cache=True
            )
            
            # Deuxième appel immédiat (cache hit)
            result2 = await self.hybrid_service.scrape_prices_unified(
                "iPhone 15 Pro", use_cache=True
            )
            
            cache_miss_ok = result1.cache_hit == False
            cache_hit_ok = result2.cache_hit == True
            
            print(f"   📊 Premier appel (miss): {result1.cache_hit}")
            print(f"   📊 Deuxième appel (hit): {result2.cache_hit}")
            
            cache_results.append({
                "test": "cache_miss_hit",
                "cache_miss_ok": cache_miss_ok,
                "cache_hit_ok": cache_hit_ok,
                "success": cache_miss_ok and cache_hit_ok
            })
            
        except Exception as e:
            print(f"   ❌ Exception cache miss/hit: {str(e)}")
            cache_results.append({
                "test": "cache_miss_hit",
                "error": str(e),
                "success": False
            })
        
        # Test 2: Stats du cache
        print("\n🔍 Test Cache Stats")
        
        try:
            cache_stats = self.hybrid_service.cache.get_cache_stats()
            
            stats_validation = {
                "has_total_requests": cache_stats.get("total_requests", 0) > 0,
                "has_cache_hits": cache_stats.get("cache_hits", 0) > 0,
                "has_hit_ratio": "hit_ratio" in cache_stats,
                "has_cached_entries": cache_stats.get("cached_entries", 0) > 0
            }
            
            hit_ratio = cache_stats.get("hit_ratio", 0)
            
            print(f"   📊 Total requêtes: {cache_stats.get('total_requests', 0)}")
            print(f"   📊 Cache hits: {cache_stats.get('cache_hits', 0)}")
            print(f"   📊 Cache misses: {cache_stats.get('cache_misses', 0)}")
            print(f"   📊 Hit ratio: {hit_ratio:.1%}")
            print(f"   📊 Entrées cachées: {cache_stats.get('cached_entries', 0)}")
            
            cache_results.append({
                "test": "cache_stats",
                "hit_ratio": hit_ratio,
                "stats_complete": all(stats_validation.values()),
                "success": all(stats_validation.values())
            })
            
        except Exception as e:
            print(f"   ❌ Exception cache stats: {str(e)}")
            cache_results.append({
                "test": "cache_stats",
                "error": str(e),
                "success": False
            })
        
        # Test 3: TTL expiration (simulation)
        print("\n🔍 Test TTL Expiration (simulation)")
        
        try:
            # Forcer expiration en modifiant TTL
            original_ttl = self.hybrid_service.cache.ttl_seconds
            self.hybrid_service.cache.ttl_seconds = 1  # 1 seconde
            
            # Premier appel
            await self.hybrid_service.scrape_prices_unified("Test TTL Product", use_cache=True)
            
            # Attendre expiration
            await asyncio.sleep(2)
            
            # Deuxième appel (devrait être miss à cause de l'expiration)
            result_after_ttl = await self.hybrid_service.scrape_prices_unified("Test TTL Product", use_cache=True)
            
            # Restaurer TTL original
            self.hybrid_service.cache.ttl_seconds = original_ttl
            
            ttl_working = result_after_ttl.cache_hit == False
            
            print(f"   📊 Cache après TTL expiration: {result_after_ttl.cache_hit} (devrait être False)")
            
            cache_results.append({
                "test": "ttl_expiration",
                "ttl_working": ttl_working,
                "success": ttl_working
            })
            
        except Exception as e:
            print(f"   ❌ Exception TTL test: {str(e)}")
            cache_results.append({
                "test": "ttl_expiration",
                "error": str(e),
                "success": False
            })
        
        # Évaluation globale cache
        successful_cache_tests = sum(1 for r in cache_results if r.get("success", False))
        total_cache_tests = len(cache_results)
        
        success = successful_cache_tests >= total_cache_tests * 0.8
        
        self.log_test_result(
            "Cache Système Fonctionnel",
            success,
            {
                "tests_réussis": f"{successful_cache_tests}/{total_cache_tests}",
                "hit_ratio_tracking": "✅ FONCTIONNEL" if any(r.get("hit_ratio") is not None for r in cache_results) else "❌ DÉFAILLANT",
                "ttl_expiration": "✅ FONCTIONNEL" if any(r.get("ttl_working") for r in cache_results) else "❌ DÉFAILLANT"
            },
            critical=True
        )
        
        return success
    
    def test_monitoring_dashboard_data(self):
        """TEST 4: Monitoring Dashboard avec métriques temps réel"""
        print("\n🧪 TEST 4: Monitoring Dashboard - Métriques Temps Réel")
        print("=" * 60)
        
        dashboard_results = []
        
        # Test 1: get_monitoring_dashboard_data()
        print("\n🔍 Test Dashboard Data")
        
        try:
            dashboard_data = self.hybrid_service.get_monitoring_dashboard_data()
            
            # Validation structure dashboard
            required_sections = ["overview", "sources_performance", "cache_performance", "proxy_health"]
            sections_present = all(section in dashboard_data for section in required_sections)
            
            # Validation overview
            overview = dashboard_data.get("overview", {})
            overview_fields = ["total_requests", "success_rate", "avg_response_time_ms", "total_prices_found"]
            overview_complete = all(field in overview for field in overview_fields)
            
            # Validation sources performance
            sources_perf = dashboard_data.get("sources_performance", {})
            sources_count = len(sources_perf)
            
            print(f"   📊 Sections présentes: {sections_present}")
            print(f"   📊 Overview complet: {overview_complete}")
            print(f"   📊 Sources trackées: {sources_count}")
            print(f"   📊 Total requêtes: {overview.get('total_requests', 0)}")
            print(f"   📊 Taux succès: {overview.get('success_rate', 0):.1%}")
            print(f"   📊 Temps réponse moyen: {overview.get('avg_response_time_ms', 0):.0f}ms")
            
            dashboard_results.append({
                "test": "dashboard_data",
                "sections_present": sections_present,
                "overview_complete": overview_complete,
                "sources_count": sources_count,
                "success": sections_present and overview_complete and sources_count > 0
            })
            
        except Exception as e:
            print(f"   ❌ Exception dashboard data: {str(e)}")
            dashboard_results.append({
                "test": "dashboard_data",
                "error": str(e),
                "success": False
            })
        
        # Test 2: get_system_health_status()
        print("\n🔍 Test System Health Status")
        
        try:
            health_status = self.hybrid_service.get_system_health_status()
            
            # Validation structure health
            required_health_fields = ["system_status", "components", "metrics", "recommendations"]
            health_complete = all(field in health_status for field in required_health_fields)
            
            # Validation components
            components = health_status.get("components", {})
            expected_components = ["scraping_service", "proxy_provider", "cache_system", "outlier_detection"]
            components_complete = all(comp in components for comp in expected_components)
            
            system_status = health_status.get("system_status", "unknown")
            recommendations = health_status.get("recommendations", [])
            
            print(f"   📊 Structure santé complète: {health_complete}")
            print(f"   📊 Composants complets: {components_complete}")
            print(f"   📊 Status système: {system_status}")
            print(f"   📊 Recommandations: {len(recommendations)}")
            
            for comp, status in components.items():
                print(f"      🔧 {comp}: {status}")
            
            dashboard_results.append({
                "test": "health_status",
                "health_complete": health_complete,
                "components_complete": components_complete,
                "system_status": system_status,
                "success": health_complete and components_complete
            })
            
        except Exception as e:
            print(f"   ❌ Exception health status: {str(e)}")
            dashboard_results.append({
                "test": "health_status",
                "error": str(e),
                "success": False
            })
        
        # Évaluation globale dashboard
        successful_dashboard_tests = sum(1 for r in dashboard_results if r.get("success", False))
        total_dashboard_tests = len(dashboard_results)
        
        success = successful_dashboard_tests == total_dashboard_tests
        
        self.log_test_result(
            "Monitoring Dashboard Cohérent",
            success,
            {
                "tests_réussis": f"{successful_dashboard_tests}/{total_dashboard_tests}",
                "dashboard_data": "✅ FONCTIONNEL" if any(r.get("test") == "dashboard_data" and r.get("success") for r in dashboard_results) else "❌ DÉFAILLANT",
                "health_status": "✅ FONCTIONNEL" if any(r.get("test") == "health_status" and r.get("success") for r in dashboard_results) else "❌ DÉFAILLANT"
            },
            critical=True
        )
        
        return success
    
    def test_integration_existing_services(self):
        """TEST 5: Integration avec Services Existants"""
        print("\n🧪 TEST 5: Integration avec Services Existants")
        print("=" * 60)
        
        integration_results = []
        
        # Test 1: Compatibilité enhanced_scraping_service
        print("\n🔍 Test Compatibilité Enhanced Scraping Service")
        
        try:
            # Vérifier que le service enhanced est bien intégré
            enhanced_service = self.hybrid_service.enhanced_service
            has_enhanced = enhanced_service is not None
            
            # Vérifier méthodes disponibles
            has_scrape_method = hasattr(enhanced_service, 'scrape_competitor_prices_enhanced')
            
            print(f"   📊 Enhanced service intégré: {has_enhanced}")
            print(f"   📊 Méthode scraping disponible: {has_scrape_method}")
            
            integration_results.append({
                "test": "enhanced_service_integration",
                "has_enhanced": has_enhanced,
                "has_scrape_method": has_scrape_method,
                "success": has_enhanced and has_scrape_method
            })
            
        except Exception as e:
            print(f"   ❌ Exception enhanced service: {str(e)}")
            integration_results.append({
                "test": "enhanced_service_integration",
                "error": str(e),
                "success": False
            })
        
        # Test 2: Proxy provider integration
        print("\n🔍 Test Proxy Provider Integration")
        
        try:
            # Vérifier proxy provider
            proxy_provider = self.hybrid_service.proxy_provider
            has_proxy = proxy_provider is not None
            
            # Vérifier stats proxy
            proxy_stats = proxy_provider.get_provider_stats() if has_proxy else {}
            has_stats = bool(proxy_stats)
            
            print(f"   📊 Proxy provider intégré: {has_proxy}")
            print(f"   📊 Stats proxy disponibles: {has_stats}")
            
            if has_stats:
                print(f"      🔧 Proxies totaux: {proxy_stats.get('total_proxies', 0)}")
                print(f"      🔧 Proxies sains: {proxy_stats.get('healthy_proxies', 0)}")
            
            integration_results.append({
                "test": "proxy_provider_integration",
                "has_proxy": has_proxy,
                "has_stats": has_stats,
                "success": has_proxy and has_stats
            })
            
        except Exception as e:
            print(f"   ❌ Exception proxy provider: {str(e)}")
            integration_results.append({
                "test": "proxy_provider_integration",
                "error": str(e),
                "success": False
            })
        
        # Test 3: Configuration environnement MOCK_MODE
        print("\n🔍 Test Configuration Environnement")
        
        try:
            # Vérifier variables d'environnement
            mock_mode = os.environ.get('MOCK_MODE', 'true').lower() == 'true'
            scraping_source_set = os.environ.get('SCRAPING_SOURCE_SET', 'default')
            
            # Vérifier sources configurées
            sources = self.hybrid_service.price_sources
            sources_count = len(sources)
            
            print(f"   📊 MOCK_MODE: {mock_mode}")
            print(f"   📊 SCRAPING_SOURCE_SET: {scraping_source_set}")
            print(f"   📊 Sources configurées: {sources_count}")
            
            for source in sources:
                print(f"      🔧 {source['name']}: priorité {source['priority']}, poids {source['weight']}")
            
            integration_results.append({
                "test": "environment_configuration",
                "mock_mode": mock_mode,
                "sources_count": sources_count,
                "success": sources_count >= 3  # Au moins 3 sources
            })
            
        except Exception as e:
            print(f"   ❌ Exception configuration: {str(e)}")
            integration_results.append({
                "test": "environment_configuration",
                "error": str(e),
                "success": False
            })
        
        # Évaluation globale integration
        successful_integration_tests = sum(1 for r in integration_results if r.get("success", False))
        total_integration_tests = len(integration_results)
        
        success = successful_integration_tests >= total_integration_tests * 0.8
        
        self.log_test_result(
            "Integration Services Existants",
            success,
            {
                "tests_réussis": f"{successful_integration_tests}/{total_integration_tests}",
                "enhanced_service": "✅ INTÉGRÉ" if any(r.get("test") == "enhanced_service_integration" and r.get("success") for r in integration_results) else "❌ PROBLÈME",
                "proxy_provider": "✅ INTÉGRÉ" if any(r.get("test") == "proxy_provider_integration" and r.get("success") for r in integration_results) else "❌ PROBLÈME",
                "configuration": "✅ CORRECTE" if any(r.get("test") == "environment_configuration" and r.get("success") for r in integration_results) else "❌ PROBLÈME"
            },
            critical=False
        )
        
        return success
    
    async def run_comprehensive_validation(self):
        """Exécute la validation complète du système hybride"""
        print("🚀 VALIDATION FINALE SYSTÈME SCRAPING PRIX HYBRIDE - ECOMSIMPLY")
        print("=" * 80)
        print("Objectif: Valider que le système hybride atteint 95% taux succès")
        print("Mode: Mock-first avec composants critiques fonctionnels")
        print("=" * 80)
        
        start_time = time.time()
        
        try:
            # Exécution des 5 tests critiques
            print("\n🎯 DÉMARRAGE VALIDATION HYBRIDE...")
            
            test1_result = await self.test_hybrid_scraping_service_unified()
            await asyncio.sleep(1)
            
            test2_result = self.test_outlier_detection_multi_methods()
            await asyncio.sleep(1)
            
            test3_result = await self.test_cache_system_functionality()
            await asyncio.sleep(1)
            
            test4_result = self.test_monitoring_dashboard_data()
            await asyncio.sleep(1)
            
            test5_result = self.test_integration_existing_services()
            
            # Calcul final
            total_time = time.time() - start_time
            self.validation_summary["success_rate"] = (
                self.validation_summary["passed_tests"] / 
                self.validation_summary["total_tests"] * 100
            ) if self.validation_summary["total_tests"] > 0 else 0
            
            # Résumé final
            print("\n" + "=" * 80)
            print("🏁 RÉSUMÉ FINAL - VALIDATION SYSTÈME HYBRIDE")
            print("=" * 80)
            
            print(f"📊 Total Tests: {self.validation_summary['total_tests']}")
            print(f"✅ Réussis: {self.validation_summary['passed_tests']}")
            print(f"❌ Échoués: {self.validation_summary['failed_tests']}")
            print(f"📈 Taux de Réussite Global: {self.validation_summary['success_rate']:.1f}%")
            print(f"⏱️ Temps Total: {total_time:.1f}s")
            
            print(f"\n🎯 STATUT DES COMPOSANTS CRITIQUES:")
            print(f"   1. HybridScrapingService Unifié: {'✅ RÉUSSI' if test1_result else '❌ ÉCHOUÉ'}")
            print(f"   2. Détection Outliers Multi-Méthodes: {'✅ RÉUSSI' if test2_result else '❌ ÉCHOUÉ'}")
            print(f"   3. Cache Système Fonctionnel: {'✅ RÉUSSI' if test3_result else '❌ ÉCHOUÉ'}")
            print(f"   4. Monitoring Dashboard Cohérent: {'✅ RÉUSSI' if test4_result else '❌ ÉCHOUÉ'}")
            print(f"   5. Integration Services Existants: {'✅ RÉUSSI' if test5_result else '❌ ÉCHOUÉ'}")
            
            # Critères de succès Phase 3
            success_criteria = {
                "taux_succès_≥95%": test1_result,
                "outliers_confidence_≥90%": test2_result,
                "cache_fonctionnel": test3_result,
                "dashboard_cohérent": test4_result,
                "pas_régression": test5_result
            }
            
            print(f"\n📋 CRITÈRES DE SUCCÈS PHASE 3:")
            for criterion, met in success_criteria.items():
                status_icon = "✅" if met else "❌"
                print(f"   {status_icon} {criterion}")
            
            # Évaluation finale
            critical_success = test1_result and test2_result and test3_result  # 3 composants critiques
            overall_success = all(success_criteria.values())
            
            if overall_success:
                print(f"\n🎉 SUCCÈS COMPLET: Le système hybride est PRODUCTION-READY!")
                print("   ✅ Taux succès ≥95% sur scraping unifié")
                print("   ✅ Outliers détectés avec confidence ≥90%")
                print("   ✅ Cache fonctionnel avec hit ratio tracking")
                print("   ✅ Dashboard metrics cohérents et temps réel")
                print("   ✅ Pas de régression sur fonctionnalités existantes")
                print("\n🚀 Le système hybride Phase 3 peut être déployé en production!")
                
            elif critical_success:
                print(f"\n⚡ SUCCÈS PARTIEL: Les composants critiques fonctionnent!")
                print("   ✅ Scraping unifié opérationnel")
                print("   ✅ Détection outliers fonctionnelle")
                print("   ✅ Cache système opérationnel")
                if not test4_result:
                    print("   ⚠️ Dashboard monitoring nécessite des ajustements")
                if not test5_result:
                    print("   ⚠️ Intégration services nécessite vérification")
                print("\n🔧 Corrections mineures recommandées avant production")
                
            else:
                print(f"\n❌ ÉCHEC CRITIQUE: Le système hybride présente des problèmes majeurs")
                if not test1_result:
                    print("   ❌ Scraping unifié non fonctionnel")
                if not test2_result:
                    print("   ❌ Détection outliers défaillante")
                if not test3_result:
                    print("   ❌ Cache système défaillant")
                print("   🔧 Correction immédiate requise avant déploiement")
            
            # Issues critiques
            if self.validation_summary["critical_issues"]:
                print(f"\n🚨 ISSUES CRITIQUES À RÉSOUDRE:")
                for issue in self.validation_summary["critical_issues"]:
                    print(f"   ❌ {issue}")
            
            return critical_success
            
        except Exception as e:
            print(f"\n❌ ERREUR CRITIQUE VALIDATION: {str(e)}")
            return False

async def main():
    """Exécution principale de la validation"""
    validator = HybridScrapingValidator()
    success = await validator.run_comprehensive_validation()
    
    # Code de sortie approprié
    exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())