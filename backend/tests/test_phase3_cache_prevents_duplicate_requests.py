"""
Test Phase 3: Implémentation améliorations - Cache Prevents Duplicate Requests
Tests pour valider que le cache évite les requêtes scraping dupliquées
"""

import pytest
import asyncio
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.hybrid_scraping_service import HybridScrapingService

class TestCachePreventsDuplicateRequests:
    """Tests pour validation cache anti-doublons"""
    
    @pytest.fixture
    def hybrid_service(self):
        return HybridScrapingService()
    
    @pytest.mark.asyncio
    async def test_cache_prevents_duplicate_requests_basic(self, hybrid_service):
        """Test: Cache évite requêtes dupliquées basiques"""
        
        product_name = "iPhone 15 Pro"
        
        # Première requête - devrait aller chercher les données
        start_time1 = time.time()
        result1 = await hybrid_service.scrape_prices_unified(
            product_name=product_name,
            use_cache=True
        )
        time1 = time.time() - start_time1
        
        # Validation première requête
        assert result1.cache_hit == False, "Première requête ne devrait pas être un cache hit"
        assert result1.found_prices > 0, "Première requête devrait trouver des prix"
        
        # Seconde requête immédiate - devrait utiliser cache
        start_time2 = time.time()
        result2 = await hybrid_service.scrape_prices_unified(
            product_name=product_name,
            use_cache=True
        )
        time2 = time.time() - start_time2
        
        # Validation seconde requête (cache hit)
        assert result2.cache_hit == True, "Seconde requête devrait être un cache hit"
        assert result2.found_prices == result1.found_prices, "Nombre prix devrait être identique (cache)"
        assert result2.price_statistics == result1.price_statistics, "Stats prix identiques (cache)"
        
        # Validation performance cache
        assert time2 < time1, "Requête cache devrait être plus rapide"
        
        print("✅ Cache évite doublons basiques:")
        print(f"  - 1ère requête: {time1*1000:.1f}ms (cache_hit: {result1.cache_hit})")
        print(f"  - 2ème requête: {time2*1000:.1f}ms (cache_hit: {result2.cache_hit})")
        print(f"  - Gain performance: {((time1-time2)/time1)*100:.1f}%")
    
    @pytest.mark.asyncio
    async def test_cache_prevents_duplicate_requests_different_products(self, hybrid_service):
        """Test: Cache différencie correctement les produits"""
        
        products = ["iPhone 15 Pro", "Samsung Galaxy S24", "MacBook Air M2"]
        results = {}
        
        # Première passe - remplir cache
        for product in products:
            result = await hybrid_service.scrape_prices_unified(
                product_name=product,
                use_cache=True
            )
            results[product] = result
            
            assert result.cache_hit == False, f"Première requête {product} devrait être sans cache"
        
        # Seconde passe - utiliser cache
        for product in products:
            cached_result = await hybrid_service.scrape_prices_unified(
                product_name=product,
                use_cache=True
            )
            
            assert cached_result.cache_hit == True, f"Seconde requête {product} devrait utiliser cache"
            
            # Vérifier que les données sont les mêmes
            original = results[product]
            assert cached_result.found_prices == original.found_prices
            assert cached_result.sources_detail == original.sources_detail
        
        print("✅ Cache différencie produits:")
        for product in products:
            print(f"  - {product}: cache fonctionne indépendamment")
    
    @pytest.mark.asyncio
    async def test_cache_prevents_duplicate_requests_ttl_expiration(self, hybrid_service):
        """Test: Cache expire correctement selon TTL"""
        
        # Configuration cache avec TTL court pour test
        original_ttl = hybrid_service.cache.ttl_seconds
        hybrid_service.cache.ttl_seconds = 2  # 2 secondes pour test
        
        product_name = "AirPods Pro"
        
        # Première requête
        result1 = await hybrid_service.scrape_prices_unified(
            product_name=product_name,
            use_cache=True
        )
        assert result1.cache_hit == False
        
        # Requête immédiate - cache hit
        result2 = await hybrid_service.scrape_prices_unified(
            product_name=product_name,
            use_cache=True
        )
        assert result2.cache_hit == True
        
        # Attendre expiration cache
        await asyncio.sleep(2.5)
        
        # Requête après expiration - devrait refaire scraping
        result3 = await hybrid_service.scrape_prices_unified(
            product_name=product_name,
            use_cache=True
        )
        assert result3.cache_hit == False, "Cache devrait être expiré"
        
        # Restaurer TTL original
        hybrid_service.cache.ttl_seconds = original_ttl
        
        print("✅ TTL expiration cache:")
        print(f"  - Requête 1: cache_hit={result1.cache_hit} (initial)")
        print(f"  - Requête 2: cache_hit={result2.cache_hit} (cache valide)")
        print(f"  - Requête 3: cache_hit={result3.cache_hit} (après expiration)")
    
    @pytest.mark.asyncio
    async def test_cache_prevents_duplicate_requests_cache_stats(self, hybrid_service):
        """Test: Statistiques cache correctes"""
        
        # Réinitialiser stats cache
        hybrid_service.cache.cache_stats = {"hits": 0, "misses": 0, "invalidations": 0}
        
        # Scénario mixte hits/misses
        test_requests = [
            ("iPhone 15 Pro", True),   # Miss
            ("iPhone 15 Pro", True),   # Hit  
            ("Samsung Galaxy S24", True), # Miss
            ("iPhone 15 Pro", True),   # Hit
            ("Samsung Galaxy S24", True), # Hit
            ("MacBook Air M2", True),  # Miss
            ("MacBook Air M2", True),  # Hit
        ]
        
        for product, use_cache in test_requests:
            await hybrid_service.scrape_prices_unified(
                product_name=product,
                use_cache=use_cache
            )
        
        # Vérifier stats cache
        cache_stats = hybrid_service.cache.get_cache_stats()
        
        print("✅ Statistiques cache:")
        print(f"  - Total requêtes: {cache_stats['total_requests']}")
        print(f"  - Cache hits: {cache_stats['cache_hits']}")
        print(f"  - Cache misses: {cache_stats['cache_misses']}")
        print(f"  - Hit ratio: {cache_stats['hit_ratio']:.2%}")
        print(f"  - Entrées cachées: {cache_stats['cached_entries']}")
        
        # Validations
        assert cache_stats["total_requests"] == 7, "7 requêtes au total"
        assert cache_stats["cache_hits"] == 4, "4 hits attendus"  
        assert cache_stats["cache_misses"] == 3, "3 misses attendus"
        assert cache_stats["hit_ratio"] == 4/7, "Ratio hit correct"
        assert cache_stats["cached_entries"] == 3, "3 produits en cache"
    
    @pytest.mark.asyncio
    async def test_cache_prevents_duplicate_requests_cache_disabled(self, hybrid_service):
        """Test: Fonctionnement normal quand cache désactivé"""
        
        product_name = "iPad Pro"
        
        # Deux requêtes avec cache désactivé
        result1 = await hybrid_service.scrape_prices_unified(
            product_name=product_name,
            use_cache=False  # Cache désactivé
        )
        
        result2 = await hybrid_service.scrape_prices_unified(
            product_name=product_name,
            use_cache=False  # Cache désactivé
        )
        
        # Validation: aucune ne devrait être un cache hit
        assert result1.cache_hit == False
        assert result2.cache_hit == False
        
        # Les résultats peuvent varier légèrement (simulation réaliste)
        print("✅ Cache désactivé:")
        print(f"  - Résultat 1: {result1.found_prices} prix (cache_hit: {result1.cache_hit})")
        print(f"  - Résultat 2: {result2.found_prices} prix (cache_hit: {result2.cache_hit})")
    
    @pytest.mark.asyncio
    async def test_cache_prevents_duplicate_requests_sources_variation(self, hybrid_service):
        """Test: Cache différencie requêtes selon sources utilisées"""
        
        product_name = "Samsung Galaxy S24"
        
        # Modifier temporairement les sources pour test
        original_sources = hybrid_service.price_sources.copy()
        
        # Configuration sources 1: toutes sources
        hybrid_service.price_sources = original_sources
        result_all_sources = await hybrid_service.scrape_prices_unified(
            product_name=product_name,
            use_cache=True
        )
        
        # Configuration sources 2: sources réduites
        hybrid_service.price_sources = original_sources[:3]  # 3 premières sources seulement
        result_limited_sources = await hybrid_service.scrape_prices_unified(
            product_name=product_name,
            use_cache=True
        )
        
        # Restaurer sources originales
        hybrid_service.price_sources = original_sources
        
        # Validation: devraient être des cache misses car sources différentes
        assert result_all_sources.cache_hit == False
        assert result_limited_sources.cache_hit == False
        
        # Le nombre de sources analysées devrait différer
        assert result_all_sources.sources_analyzed >= result_limited_sources.sources_analyzed
        
        print("✅ Cache et variation sources:")
        print(f"  - Toutes sources: {result_all_sources.sources_analyzed} sources analysées")
        print(f"  - Sources limitées: {result_limited_sources.sources_analyzed} sources analysées")
        print(f"  - Cache différencie correctly les configurations")
    
    @pytest.mark.asyncio
    async def test_cache_prevents_duplicate_requests_monitoring_integration(self, hybrid_service):
        """Test: Intégration cache avec monitoring dashboard"""
        
        # Générer activité pour monitoring
        test_products = ["iPhone 15 Pro", "Samsung Galaxy S24", "MacBook Air M2"]
        
        for product in test_products:
            # Première requête (miss)
            await hybrid_service.scrape_prices_unified(product, use_cache=True)
            
            # Seconde requête (hit)  
            await hybrid_service.scrape_prices_unified(product, use_cache=True)
        
        # Récupérer données dashboard
        dashboard_data = hybrid_service.get_monitoring_dashboard_data()
        
        # Vérifier intégration stats cache
        cache_performance = dashboard_data["cache_performance"]
        
        assert "total_requests" in cache_performance
        assert "cache_hits" in cache_performance
        assert "hit_ratio" in cache_performance
        assert "cached_entries" in cache_performance
        
        print("✅ Intégration monitoring cache:")
        print(f"  - Hit ratio: {cache_performance['hit_ratio']:.2%}")
        print(f"  - Entrées cache: {cache_performance['cached_entries']}")
        print(f"  - Requêtes totales: {cache_performance['total_requests']}")
        
        # Validation cohérence données monitoring
        assert cache_performance["hit_ratio"] > 0, "Ratio hits devrait être > 0"
        assert cache_performance["cached_entries"] == len(test_products), "Entrées = produits testés"
        assert cache_performance["total_requests"] == len(test_products) * 2, "2 requêtes par produit"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])