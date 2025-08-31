"""
Test Phase 1: Audit - Scraping Latency Measurement  
Tests pour mesurer les temps de réponse et latences de scraping
"""

import pytest
import asyncio
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.enhanced_scraping_service import EnhancedScrapingService
from services.proxy_providers import proxy_factory

class TestScrapingLatencyMeasurement:
    """Tests pour mesurer les latences de scraping"""
    
    @pytest.fixture
    def enhanced_service(self):
        return EnhancedScrapingService()
    
    @pytest.mark.asyncio
    async def test_scraping_latency_single_source(self, enhanced_service):
        """Test: Mesurer latence scraping source unique"""
        
        start_time = time.time()
        
        result = await enhanced_service.scrape_competitor_prices_enhanced(
            product_name="iPhone 15 Pro",
            sources=["amazon"]  # Source unique pour mesure précise
        )
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        # Validation des résultats
        assert "avg_response_time_ms" in result
        assert result["sources_analyzed"] == 1
        assert result["found_prices"] >= 0
        
        # Validation latence acceptable (mock devrait être rapide)
        assert latency_ms < 5000  # Moins de 5 secondes
        
        print(f"✅ Latence source unique (amazon): {latency_ms:.2f}ms")
        print(f"  - Temps réponse moyen rapporté: {result['avg_response_time_ms']:.2f}ms")
        print(f"  - Prix trouvés: {result['found_prices']}")
    
    @pytest.mark.asyncio
    async def test_scraping_latency_multiple_sources(self, enhanced_service):
        """Test: Mesurer latence scraping multiple sources"""
        
        sources_to_test = ["amazon", "fnac", "cdiscount"]
        
        start_time = time.time()
        
        result = await enhanced_service.scrape_competitor_prices_enhanced(
            product_name="Samsung Galaxy S24",
            sources=sources_to_test
        )
        
        end_time = time.time()
        total_latency_ms = (end_time - start_time) * 1000
        
        # Validation résultats
        assert result["sources_analyzed"] == len(sources_to_test)
        assert "avg_response_time_ms" in result
        assert "total_attempts" in result
        
        # Calcul latence par source
        avg_latency_per_source = total_latency_ms / len(sources_to_test)
        
        # Validation performance acceptable  
        assert total_latency_ms < 15000  # Moins de 15 secondes pour 3 sources
        assert avg_latency_per_source < 8000  # Moins de 8s par source en moyenne
        
        print(f"✅ Latence multiple sources ({len(sources_to_test)}): {total_latency_ms:.2f}ms")
        print(f"  - Latence moyenne par source: {avg_latency_per_source:.2f}ms") 
        print(f"  - Sources réussies: {result['sources_successful']}")
        print(f"  - Total tentatives: {result['total_attempts']}")
    
    @pytest.mark.asyncio
    async def test_scraping_latency_with_retry_logic(self, enhanced_service):
        """Test: Mesurer impact retry sur latence"""
        
        # Test avec retry config modifiée pour mesures
        original_max_attempts = enhanced_service.retry_config.max_attempts
        enhanced_service.retry_config.max_attempts = 2  # Réduire pour test
        
        start_time = time.time()
        
        result = await enhanced_service.scrape_competitor_prices_enhanced(
            product_name="MacBook Pro",
            sources=["amazon", "fnac"]
        )
        
        end_time = time.time()
        retry_latency_ms = (end_time - start_time) * 1000
        
        # Restaurer config originale
        enhanced_service.retry_config.max_attempts = original_max_attempts
        
        # Validation impact retry
        assert "total_attempts" in result
        total_attempts = result["total_attempts"]
        expected_base_attempts = len(["amazon", "fnac"])  # 2 sources
        
        # Si retry, total_attempts peut être > sources
        assert total_attempts >= expected_base_attempts
        
        print(f"✅ Latence avec retry (max 2 attempts): {retry_latency_ms:.2f}ms")
        print(f"  - Total tentatives: {total_attempts}")
        print(f"  - Tentatives attendues minimum: {expected_base_attempts}")
        
        if total_attempts > expected_base_attempts:
            print(f"  - Retry détectés: {total_attempts - expected_base_attempts}")
    
    @pytest.mark.asyncio
    async def test_scraping_latency_proxy_impact(self, enhanced_service):
        """Test: Mesurer impact proxy sur latence"""
        
        proxy_provider = proxy_factory.get_proxy_provider()
        
        # Test récupération proxy
        start_proxy = time.time()
        proxy = await proxy_provider.get_proxy()
        end_proxy = time.time()
        proxy_selection_ms = (end_proxy - start_proxy) * 1000
        
        # Validation proxy récupéré
        if proxy:
            assert proxy.id is not None
            assert proxy.avg_response_time_ms > 0
            print(f"✅ Proxy sélectionné: {proxy.id}")
            print(f"  - Temps sélection proxy: {proxy_selection_ms:.2f}ms") 
            print(f"  - Latence proxy moyenne: {proxy.avg_response_time_ms}ms")
            print(f"  - Pays: {proxy.country}")
        else:
            print("⚠️ Aucun proxy disponible")
            
        # Test pool de proxies pour mesure batch
        start_pool = time.time()
        proxy_pool = await proxy_provider.get_proxy_pool(size=5)
        end_pool = time.time()
        pool_selection_ms = (end_pool - start_pool) * 1000
        
        assert len(proxy_pool) > 0
        avg_pool_latency = sum(p.avg_response_time_ms for p in proxy_pool) / len(proxy_pool)
        
        print(f"✅ Pool proxy ({len(proxy_pool)} proxies):")
        print(f"  - Temps sélection pool: {pool_selection_ms:.2f}ms")
        print(f"  - Latence moyenne pool: {avg_pool_latency:.2f}ms")
    
    @pytest.mark.asyncio  
    async def test_scraping_latency_dataset_comparison(self, enhanced_service):
        """Test: Comparer latences entre datasets"""
        
        # Test dataset default
        os.environ["SCRAPING_SOURCE_SET"] = "default"
        
        start_default = time.time()
        result_default = await enhanced_service.scrape_competitor_prices_enhanced(
            product_name="AirPods Pro"
        )
        end_default = time.time()
        latency_default_ms = (end_default - start_default) * 1000
        
        # Test dataset extended  
        os.environ["SCRAPING_SOURCE_SET"] = "extended"
        
        start_extended = time.time()
        result_extended = await enhanced_service.scrape_competitor_prices_enhanced(
            product_name="AirPods Pro"
        )
        end_extended = time.time()
        latency_extended_ms = (end_extended - start_extended) * 1000
        
        # Validation datasets
        assert result_default["dataset_used"] == "default"
        assert result_extended["dataset_used"] == "extended"
        
        # Comparaison performance
        sources_default = result_default["sources_analyzed"]
        sources_extended = result_extended["sources_analyzed"]
        
        assert sources_extended >= sources_default  # Extended doit avoir plus de sources
        
        print("✅ Comparaison latences par dataset:")
        print(f"  - Default ({sources_default} sources): {latency_default_ms:.2f}ms")
        print(f"  - Extended ({sources_extended} sources): {latency_extended_ms:.2f}ms")
        print(f"  - Ratio latence: {latency_extended_ms/latency_default_ms:.2f}x")
        
        # Nettoyer env
        if "SCRAPING_SOURCE_SET" in os.environ:
            del os.environ["SCRAPING_SOURCE_SET"]

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])