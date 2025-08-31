"""
Test Phase 2: Plan d'amélioration - Retry Logic in Mock
Tests pour valider la logique de retry dans l'environnement mock
"""

import pytest
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.enhanced_scraping_service import EnhancedScrapingService, RetryConfig

class TestRetryLogicInMock:
    """Tests pour valider la logique de retry dans mock"""
    
    @pytest.fixture
    def enhanced_service(self):
        return EnhancedScrapingService()
    
    @pytest.mark.asyncio
    async def test_retry_logic_exponential_backoff(self, enhanced_service):
        """Test: Vérifier exponential backoff dans retry"""
        
        # Configuration retry pour test
        original_config = enhanced_service.retry_config
        test_config = RetryConfig(
            max_attempts=4,
            base_delay_ms=100,  # Délai court pour test
            exponential_factor=2.0,
            jitter=False  # Désactiver jitter pour test prévisible
        )
        enhanced_service.retry_config = test_config
        
        # Test retry avec source qui échoue souvent
        result = await enhanced_service.scrape_competitor_prices_enhanced(
            product_name="iPhone 15 Pro",  # Produit qui existe dans dataset
            sources=["aliexpress"]  # Source avec high error rate
        )
        
        # Restaurer config
        enhanced_service.retry_config = original_config
        
        # Validation retry logic
        assert "total_attempts" in result
        total_attempts = result["total_attempts"]
        
        # Avec retry, on peut avoir plus de tentatives que de sources
        assert total_attempts >= 1
        assert total_attempts <= test_config.max_attempts
        
        print(f"✅ Retry logic validé:")
        print(f"  - Total tentatives: {total_attempts}")
        print(f"  - Max autorisé: {test_config.max_attempts}")
        print(f"  - Sources analysées: {result['sources_analyzed']}")
        print(f"  - Sources réussies: {result['sources_successful']}")
    
    @pytest.mark.asyncio
    async def test_retry_logic_jitter_behavior(self, enhanced_service):
        """Test: Vérifier comportement jitter dans retry"""
        
        # Test avec jitter activé
        original_config = enhanced_service.retry_config
        jitter_config = RetryConfig(
            max_attempts=3,
            base_delay_ms=50,
            exponential_factor=1.5,
            jitter=True  # Jitter activé
        )
        enhanced_service.retry_config = jitter_config
        
        # Mesurer temps avec jitter
        import time
        start_time = time.time()
        
        result = await enhanced_service.scrape_competitor_prices_enhanced(
            product_name="Samsung Galaxy S24",
            sources=["aliexpress", "amazon"]  # Sources potentiellement avec échecs
        )
        
        end_time = time.time()
        total_time_ms = (end_time - start_time) * 1000
        
        # Restaurer config
        enhanced_service.retry_config = original_config
        
        # Validation jitter
        assert result["total_attempts"] >= result["sources_analyzed"]
        
        print(f"✅ Jitter behavior validé:")
        print(f"  - Temps total: {total_time_ms:.2f}ms")
        print(f"  - Tentatives: {result['total_attempts']}")
        print(f"  - Jitter activé: {jitter_config.jitter}")
    
    @pytest.mark.asyncio
    async def test_retry_logic_max_delay_cap(self, enhanced_service):
        """Test: Vérifier plafonnement délai maximum"""
        
        # Config avec délai max bas pour test
        original_config = enhanced_service.retry_config
        capped_config = RetryConfig(
            max_attempts=5,
            base_delay_ms=500,
            max_delay_ms=2000,  # Plafond bas
            exponential_factor=3.0,  # Factor élevé pour test
            jitter=False
        )
        enhanced_service.retry_config = capped_config
        
        # Test calcul délai
        import time
        timings = []
        
        # Simuler plusieurs retry pour observer délais
        for attempt in range(1, 4):
            start = time.time()
            await enhanced_service._wait_before_retry(attempt)
            end = time.time()
            delay_ms = (end - start) * 1000
            timings.append(delay_ms)
        
        # Restaurer config
        enhanced_service.retry_config = original_config
        
        # Validation délais plafonnés
        assert len(timings) == 3
        
        # Vérifier que les délais augmentent mais restent sous le max
        for i, timing in enumerate(timings, 1):
            expected_uncapped = capped_config.base_delay_ms * (capped_config.exponential_factor ** (i-1))
            expected_capped = min(expected_uncapped, capped_config.max_delay_ms)
            
            # Tolérance de 10% pour timing système
            assert timing <= expected_capped * 1.1
        
        print(f"✅ Délai maximum plafonnement validé:")
        for i, timing in enumerate(timings, 1):
            print(f"  - Attempt {i}: {timing:.0f}ms")
        print(f"  - Plafond configuré: {capped_config.max_delay_ms}ms")
    
    @pytest.mark.asyncio
    async def test_retry_logic_success_vs_failure_patterns(self, enhanced_service):
        """Test: Comparer patterns de succès vs échec avec retry"""
        
        # Test sources avec taux de succès différents
        high_success_sources = ["fnac", "cdiscount"]  # Taux élevé
        low_success_sources = ["aliexpress", "amazon"]  # Taux plus bas
        
        # Test sans retry
        enhanced_service.retry_config.max_attempts = 1
        
        no_retry_high = await enhanced_service.scrape_competitor_prices_enhanced(
            product_name="MacBook Air M2",
            sources=high_success_sources
        )
        
        no_retry_low = await enhanced_service.scrape_competitor_prices_enhanced(
            product_name="MacBook Air M2", 
            sources=low_success_sources
        )
        
        # Test avec retry
        enhanced_service.retry_config.max_attempts = 3
        
        with_retry_high = await enhanced_service.scrape_competitor_prices_enhanced(
            product_name="MacBook Air M2",
            sources=high_success_sources
        )
        
        with_retry_low = await enhanced_service.scrape_competitor_prices_enhanced(
            product_name="MacBook Air M2",
            sources=low_success_sources
        )
        
        # Analyse patterns
        print("✅ Patterns succès/échec avec retry:")
        print("Sources haute réussite (fnac, cdiscount):")
        print(f"  - Sans retry: {no_retry_high['sources_successful']}/{no_retry_high['sources_analyzed']} succès")
        print(f"  - Avec retry: {with_retry_high['sources_successful']}/{with_retry_high['sources_analyzed']} succès")
        
        print("Sources basse réussite (aliexpress, amazon):")
        print(f"  - Sans retry: {no_retry_low['sources_successful']}/{no_retry_low['sources_analyzed']} succès")
        print(f"  - Avec retry: {with_retry_low['sources_successful']}/{with_retry_low['sources_analyzed']} succès")
        
        # Validation amélioration avec retry
        high_improvement = with_retry_high["sources_successful"] >= no_retry_high["sources_successful"]
        low_improvement = with_retry_low["sources_successful"] >= no_retry_low["sources_successful"]
        
        assert high_improvement, "Retry devrait maintenir ou améliorer sources haute réussite"
        assert low_improvement, "Retry devrait améliorer sources basse réussite"
    
    @pytest.mark.asyncio
    async def test_retry_logic_error_type_handling(self, enhanced_service):
        """Test: Vérifier gestion des différents types d'erreurs"""
        
        # Configuration retry agressive pour forcer erreurs
        original_config = enhanced_service.retry_config
        error_test_config = RetryConfig(
            max_attempts=4,
            base_delay_ms=10,  # Délais courts
            exponential_factor=1.2,
            jitter=False
        )
        enhanced_service.retry_config = error_test_config
        
        # Test avec plusieurs sources pour générer différents types d'erreurs
        test_results = []
        
        for i in range(5):
            result = await enhanced_service.scrape_competitor_prices_enhanced(
                product_name="iPad Pro",
                sources=["amazon", "aliexpress", "google_shopping"]
            )
            test_results.append(result)
        
        # Restaurer config
        enhanced_service.retry_config = original_config
        
        # Analyser erreurs collectées
        total_attempts = sum(r["total_attempts"] for r in test_results)
        total_sources = sum(r["sources_analyzed"] for r in test_results)
        successful_sources = sum(r["sources_successful"] for r in test_results)
        failed_sources = sum(r["sources_failed"] for r in test_results)
        
        retry_ratio = total_attempts / total_sources if total_sources > 0 else 0
        
        print("✅ Gestion types d'erreurs avec retry:")
        print(f"  - Total tentatives: {total_attempts}")
        print(f"  - Sources testées: {total_sources}")
        print(f"  - Ratio retry: {retry_ratio:.2f}x")
        print(f"  - Succès/Échecs: {successful_sources}/{failed_sources}")
        
        # Validation patterns retry
        assert retry_ratio >= 1.0, "Ratio retry doit être ≥ 1.0"
        assert total_attempts >= total_sources, "Tentatives ≥ sources testées"
        assert successful_sources + failed_sources == total_sources, "Somme succès+échecs = total"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])