"""
Test Phase 1: Audit - Scraping Success Rate Calculation
Tests pour calculer et analyser les taux de succès de scraping  
"""

import pytest
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.enhanced_scraping_service import EnhancedScrapingService
from services.proxy_providers import proxy_factory

class TestScrapingSuccessRateCalculation:
    """Tests pour calculer les taux de succès de scraping"""
    
    @pytest.fixture
    def enhanced_service(self):
        return EnhancedScrapingService()
    
    @pytest.mark.asyncio
    async def test_scraping_success_rate_single_batch(self, enhanced_service):
        """Test: Calculer taux de succès sur un batch unique"""
        
        batch_results = []
        test_products = ["iPhone 15", "Samsung Galaxy S24", "MacBook Air"]
        
        for product in test_products:
            result = await enhanced_service.scrape_competitor_prices_enhanced(
                product_name=product,
                sources=["amazon", "fnac"]
            )
            batch_results.append(result)
        
        # Calcul taux de succès
        total_sources_tested = sum(r["sources_analyzed"] for r in batch_results)
        total_sources_successful = sum(r["sources_successful"] for r in batch_results)
        
        success_rate = (total_sources_successful / total_sources_tested) * 100 if total_sources_tested > 0 else 0
        
        # Validation calculs
        assert total_sources_tested > 0
        assert total_sources_successful >= 0
        assert 0 <= success_rate <= 100
        
        # Statistiques détaillées
        total_prices_found = sum(r["found_prices"] for r in batch_results)
        avg_prices_per_request = total_prices_found / len(batch_results) if batch_results else 0
        
        print(f"✅ Taux de succès batch unique ({len(test_products)} produits):")
        print(f"  - Sources testées: {total_sources_tested}")
        print(f"  - Sources réussies: {total_sources_successful}")  
        print(f"  - Taux de succès: {success_rate:.2f}%")
        print(f"  - Prix trouvés total: {total_prices_found}")
        print(f"  - Prix moyen par requête: {avg_prices_per_request:.1f}")
    
    @pytest.mark.asyncio
    async def test_scraping_success_rate_by_source(self, enhanced_service):
        """Test: Calculer taux de succès par source individuellement"""
        
        test_sources = ["amazon", "fnac", "cdiscount", "aliexpress", "google_shopping"]
        source_stats = {}
        
        for source in test_sources:
            source_results = []
            
            # Test 3 requêtes par source
            for i in range(3):
                result = await enhanced_service.scrape_competitor_prices_enhanced(
                    product_name=f"Test Product {i+1}",
                    sources=[source]
                )
                source_results.append(result)
            
            # Calculs par source
            total_tests = len(source_results)
            successful_tests = sum(1 for r in source_results if r["sources_successful"] > 0)
            total_prices = sum(r["found_prices"] for r in source_results)
            avg_response_time = sum(r["avg_response_time_ms"] for r in source_results) / total_tests
            
            success_rate = (successful_tests / total_tests) * 100
            
            source_stats[source] = {
                "tests_run": total_tests,
                "successful_tests": successful_tests,
                "success_rate": success_rate,
                "total_prices_found": total_prices,
                "avg_response_time_ms": avg_response_time
            }
        
        print("✅ Taux de succès par source:")
        for source, stats in source_stats.items():
            print(f"  - {source}: {stats['success_rate']:.1f}% " +
                  f"({stats['successful_tests']}/{stats['tests_run']} tests, " +
                  f"{stats['total_prices_found']} prix, " +
                  f"{stats['avg_response_time_ms']:.0f}ms)")
        
        # Validation globale
        all_success_rates = [stats["success_rate"] for stats in source_stats.values()]
        assert all(0 <= rate <= 100 for rate in all_success_rates)
        assert len(source_stats) == len(test_sources)
    
    @pytest.mark.asyncio
    async def test_scraping_success_rate_with_retry_analysis(self, enhanced_service):
        """Test: Analyser impact retry sur taux de succès"""
        
        # Test avec retry désactivé (max_attempts = 1)
        original_max_attempts = enhanced_service.retry_config.max_attempts
        enhanced_service.retry_config.max_attempts = 1
        
        no_retry_results = []
        for i in range(5):
            result = await enhanced_service.scrape_competitor_prices_enhanced(
                product_name=f"No Retry Test {i+1}",
                sources=["amazon", "fnac"]
            )
            no_retry_results.append(result)
        
        # Test avec retry activé (max_attempts = 3)
        enhanced_service.retry_config.max_attempts = 3
        
        with_retry_results = []
        for i in range(5):
            result = await enhanced_service.scrape_competitor_prices_enhanced(
                product_name=f"With Retry Test {i+1}",
                sources=["amazon", "fnac"]
            )
            with_retry_results.append(result)
        
        # Restaurer config
        enhanced_service.retry_config.max_attempts = original_max_attempts
        
        # Calculs comparative
        def calculate_batch_success_rate(results):
            total_sources = sum(r["sources_analyzed"] for r in results)
            total_successful = sum(r["sources_successful"] for r in results)
            return (total_successful / total_sources) * 100 if total_sources > 0 else 0
        
        no_retry_rate = calculate_batch_success_rate(no_retry_results)
        with_retry_rate = calculate_batch_success_rate(with_retry_results)
        
        # Calcul moyenne tentatives
        avg_attempts_no_retry = sum(r["total_attempts"] for r in no_retry_results) / len(no_retry_results)
        avg_attempts_with_retry = sum(r["total_attempts"] for r in with_retry_results) / len(with_retry_results)
        
        print("✅ Comparaison impact retry sur succès:")
        print(f"  - Sans retry (max=1): {no_retry_rate:.1f}% succès, {avg_attempts_no_retry:.1f} tentatives moy.")
        print(f"  - Avec retry (max=3): {with_retry_rate:.1f}% succès, {avg_attempts_with_retry:.1f} tentatives moy.")
        print(f"  - Amélioration retry: {with_retry_rate - no_retry_rate:+.1f} points de %")
        
        # Validation logique
        assert avg_attempts_with_retry >= avg_attempts_no_retry
        assert with_retry_rate >= no_retry_rate  # Retry doit améliorer ou maintenir le taux
    
    @pytest.mark.asyncio
    async def test_scraping_success_rate_proxy_correlation(self, enhanced_service):
        """Test: Analyser corrélation proxy/taux de succès"""
        
        proxy_provider = proxy_factory.get_proxy_provider()
        
        # Obtenir stats proxy avant tests
        initial_proxy_stats = proxy_provider.get_provider_stats()
        
        # Exécuter batch de tests
        test_results = []
        for i in range(10):
            result = await enhanced_service.scrape_competitor_prices_enhanced(
                product_name=f"Proxy Correlation Test {i+1}",
                sources=["amazon", "fnac", "cdiscount"]
            )
            test_results.append(result)
        
        # Obtenir stats proxy après tests
        final_proxy_stats = proxy_provider.get_provider_stats()
        
        # Calcul taux de succès global
        total_sources = sum(r["sources_analyzed"] for r in test_results)
        total_successful = sum(r["sources_successful"] for r in test_results)
        global_success_rate = (total_successful / total_sources) * 100 if total_sources > 0 else 0
        
        # Analyse proxy
        healthy_proxies = final_proxy_stats["healthy_proxies"]
        total_proxies = final_proxy_stats["total_proxies"]
        proxy_health_rate = (healthy_proxies / total_proxies) * 100 if total_proxies > 0 else 0
        
        print("✅ Corrélation proxy/succès:")
        print(f"  - Taux succès scraping: {global_success_rate:.1f}%")
        print(f"  - Taux santé proxy: {proxy_health_rate:.1f}%") 
        print(f"  - Proxies sains: {healthy_proxies}/{total_proxies}")
        print(f"  - Requêtes proxy totales: {final_proxy_stats['usage_stats']['total_requests']}")
        print(f"  - Succès proxy: {final_proxy_stats['usage_stats']['successful_requests']}")
        print(f"  - Échecs proxy: {final_proxy_stats['usage_stats']['failed_requests']}")
        
        # Validation cohérence
        assert 0 <= global_success_rate <= 100
        assert 0 <= proxy_health_rate <= 100
        assert healthy_proxies <= total_proxies
    
    @pytest.mark.asyncio
    async def test_scraping_success_rate_historical_tracking(self, enhanced_service):
        """Test: Suivre évolution taux de succès dans le temps"""
        
        # Simulation batch historique (3 périodes)
        historical_results = {
            "period_1": [],
            "period_2": [],  
            "period_3": []
        }
        
        for period in historical_results.keys():
            for i in range(3):  # 3 tests par période
                result = await enhanced_service.scrape_competitor_prices_enhanced(
                    product_name=f"{period} Product {i+1}",
                    sources=["amazon", "fnac"]
                )
                historical_results[period].append(result)
        
        # Calcul évolution taux de succès
        period_stats = {}
        for period, results in historical_results.items():
            total_sources = sum(r["sources_analyzed"] for r in results)
            total_successful = sum(r["sources_successful"] for r in results)
            success_rate = (total_successful / total_sources) * 100 if total_sources > 0 else 0
            
            avg_prices = sum(r["found_prices"] for r in results) / len(results)
            avg_response_time = sum(r["avg_response_time_ms"] for r in results) / len(results)
            
            period_stats[period] = {
                "success_rate": success_rate,
                "avg_prices_per_request": avg_prices,
                "avg_response_time_ms": avg_response_time,
                "total_requests": len(results)
            }
        
        print("✅ Évolution historique taux de succès:")
        for period, stats in period_stats.items():
            print(f"  - {period}: {stats['success_rate']:.1f}% succès, " +
                  f"{stats['avg_prices_per_request']:.1f} prix/req, " +
                  f"{stats['avg_response_time_ms']:.0f}ms")
        
        # Validation données complètes
        assert len(period_stats) == 3
        assert all(0 <= stats["success_rate"] <= 100 for stats in period_stats.values())
        assert all(stats["total_requests"] == 3 for stats in period_stats.values())

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])