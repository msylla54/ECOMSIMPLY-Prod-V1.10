"""
Test Phase 2: Plan d'amélioration - Proxy Mock Switching
Tests pour valider la commutation et gestion des proxies mock
"""

import pytest
import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.proxy_providers import proxy_factory, IProxyProvider, MockProxyProvider
from services.enhanced_scraping_service import EnhancedScrapingService

class TestProxyMockSwitching:
    """Tests pour validation commutation proxies mock"""
    
    @pytest.fixture
    def proxy_provider(self):
        return proxy_factory.get_proxy_provider()
    
    @pytest.fixture
    def enhanced_service(self):
        return EnhancedScrapingService()
    
    @pytest.mark.asyncio
    async def test_proxy_mock_switching_basic(self, proxy_provider):
        """Test: Commutation basique entre proxies mock"""
        
        # Vérifier type de provider
        assert isinstance(proxy_provider, MockProxyProvider)
        assert proxy_provider.is_mock == True
        assert proxy_provider.provider_name == "MockProxyProvider"
        
        # Test sélection initiale
        proxy1 = await proxy_provider.get_proxy()
        proxy2 = await proxy_provider.get_proxy()
        proxy3 = await proxy_provider.get_proxy()
        
        # Validation proxies différents (rotation)
        assert proxy1 is not None
        assert proxy2 is not None  
        assert proxy3 is not None
        
        # IDs devraient être différents avec rotation intelligente
        proxy_ids = {proxy1.id, proxy2.id, proxy3.id}
        assert len(proxy_ids) >= 2, "Rotation devrait donner des proxies différents"
        
        print("✅ Commutation proxies mock basique:")
        print(f"  - Proxy 1: {proxy1.id} ({proxy1.country})")
        print(f"  - Proxy 2: {proxy2.id} ({proxy2.country})")
        print(f"  - Proxy 3: {proxy3.id} ({proxy3.country})")
        print(f"  - IDs uniques: {len(proxy_ids)}")
    
    @pytest.mark.asyncio
    async def test_proxy_mock_switching_by_country(self, proxy_provider):
        """Test: Commutation proxies par pays"""
        
        # Test sélection par pays spécifiques
        countries_to_test = ["FR", "DE", "US", "UK"]
        country_proxies = {}
        
        for country in countries_to_test:
            proxy = await proxy_provider.get_proxy(country=country)
            if proxy:
                country_proxies[country] = proxy
                assert proxy.country == country, f"Proxy devrait être du pays {country}"
        
        print("✅ Commutation proxies par pays:")
        for country, proxy in country_proxies.items():
            print(f"  - {country}: {proxy.id} ({proxy.region})")
        
        # Validation diversité géographique
        assert len(country_proxies) > 0, "Au moins quelques pays disponibles"
        
        # Test pays non disponible
        exotic_proxy = await proxy_provider.get_proxy(country="ZZ")  
        if exotic_proxy:
            # Si un proxy est retourné, il devrait être d'un autre pays (fallback)
            assert exotic_proxy.country != "ZZ"
        
        print(f"  - Pays inexistant (ZZ): {'Fallback proxy' if exotic_proxy else 'Aucun proxy'}")
    
    @pytest.mark.asyncio
    async def test_proxy_mock_switching_pool_management(self, proxy_provider):
        """Test: Gestion pool de proxies avec commutation"""
        
        # Récupérer pool de différentes tailles
        pool_sizes = [3, 5, 10, 15]
        pools = {}
        
        for size in pool_sizes:
            pool = await proxy_provider.get_proxy_pool(size=size)
            pools[size] = pool
            
            # Validation taille pool
            assert len(pool) > 0, f"Pool taille {size} devrait contenir des proxies"
            assert len(pool) <= size, f"Pool ne devrait pas dépasser {size}"
            
            # Validation unicité dans le pool
            pool_ids = {p.id for p in pool}
            assert len(pool_ids) == len(pool), f"Tous proxies du pool taille {size} devraient être uniques"
        
        print("✅ Gestion pools de proxies:")
        for size, pool in pools.items():
            countries = list({p.country for p in pool if p.country})
            print(f"  - Pool {size}: {len(pool)} proxies, {len(countries)} pays ({countries})")
        
        # Test diversité géographique dans pools
        large_pool = pools.get(10, [])
        if large_pool:
            pool_countries = {p.country for p in large_pool if p.country}
            assert len(pool_countries) > 1, "Pool important devrait avoir diversité géographique"
    
    @pytest.mark.asyncio
    async def test_proxy_mock_switching_health_tracking(self, proxy_provider):
        """Test: Suivi santé proxies avec commutation"""
        
        # Obtenir proxy initial
        proxy = await proxy_provider.get_proxy()
        assert proxy is not None
        
        original_health = proxy.is_healthy
        original_success_rate = proxy.success_rate
        
        # Test health check
        health_result = await proxy_provider.health_check(proxy)
        
        # Validation health check
        assert "proxy_id" in health_result
        assert "status" in health_result
        assert "available" in health_result
        assert "response_time_ms" in health_result
        assert health_result["proxy_id"] == proxy.id
        assert health_result["mock_provider"] == True
        
        print("✅ Suivi santé proxy:")
        print(f"  - Proxy: {proxy.id}")
        print(f"  - Santé originale: {original_health}")
        print(f"  - Status check: {health_result['status']}")
        print(f"  - Disponible: {health_result['available']}")
        print(f"  - Temps réponse: {health_result['response_time_ms']}ms")
        
        # Test signalement statut (succès)
        await proxy_provider.report_proxy_status(proxy.id, success=True, response_time_ms=200)
        
        # Vérifier amélioration stats
        updated_proxy = None
        pool = await proxy_provider.get_proxy_pool(size=20)  # Pool large pour trouver le proxy
        for p in pool:
            if p.id == proxy.id:
                updated_proxy = p
                break
        
        if updated_proxy:
            print(f"  - Success rate après succès: {updated_proxy.success_rate:.3f}")
            assert updated_proxy.success_rate >= original_success_rate, "Succès devrait maintenir/améliorer taux"
        
        # Test signalement échec
        await proxy_provider.report_proxy_status(proxy.id, success=False, response_time_ms=5000)
        print(f"  - Échec signalé pour {proxy.id}")
    
    @pytest.mark.asyncio
    async def test_proxy_mock_switching_integration_scraping(self, enhanced_service):
        """Test: Intégration commutation proxy avec scraping"""
        
        # Test scraping avec rotation proxy automatique
        scraping_results = []
        
        for i in range(3):
            result = await enhanced_service.scrape_competitor_prices_enhanced(
                product_name="iPhone 15 Pro",
                sources=["amazon", "fnac"]
            )
            scraping_results.append(result)
        
        # Analyser utilisation proxies
        proxy_countries_used = set()
        total_proxy_usage = 0
        
        for result in scraping_results:
            scraped_data = result.get("scraped_results", {})
            for source_data in scraped_data.values():
                if "proxy_country" in source_data and source_data["proxy_country"]:
                    proxy_countries_used.add(source_data["proxy_country"])
                    total_proxy_usage += 1
        
        print("✅ Intégration proxy-scraping:")
        print(f"  - Requêtes scraping: {len(scraping_results)}")
        print(f"  - Utilisations proxy: {total_proxy_usage}")
        print(f"  - Pays proxy utilisés: {list(proxy_countries_used)}")
        
        # Validation intégration
        assert len(scraping_results) == 3
        assert total_proxy_usage > 0, "Proxies devraient être utilisés pour scraping"
        assert len(proxy_countries_used) > 0, "Au moins un pays proxy utilisé"
        
        # Test stats intégrées
        service_stats = enhanced_service.get_scraping_stats()
        proxy_stats = service_stats.get("proxy_stats", {})
        
        assert "provider_name" in proxy_stats
        assert "total_proxies" in proxy_stats
        assert proxy_stats["is_mock"] == True
        
        print(f"  - Provider: {proxy_stats['provider_name']}")
        print(f"  - Total proxies disponibles: {proxy_stats['total_proxies']}")
        print(f"  - Proxies sains: {proxy_stats['healthy_proxies']}")
    
    @pytest.mark.asyncio
    async def test_proxy_mock_switching_configuration_modes(self, proxy_provider):
        """Test: Différents modes de configuration proxy"""
        
        # Test stats provider current
        current_stats = proxy_provider.get_provider_stats()
        
        # Validation stats complètes
        required_fields = [
            "provider_name", "is_mock", "total_proxies", "healthy_proxies",
            "countries_available", "usage_stats", "avg_success_rate"
        ]
        
        for field in required_fields:
            assert field in current_stats, f"Champ {field} manquant dans stats"
        
        print("✅ Configuration modes proxy:")
        print(f"  - Provider: {current_stats['provider_name']}")
        print(f"  - Mode mock: {current_stats['is_mock']}")
        print(f"  - Proxies: {current_stats['healthy_proxies']}/{current_stats['total_proxies']}")
        print(f"  - Pays: {len(current_stats['countries_available'])}")
        print(f"  - Taux succès moyen: {current_stats['avg_success_rate']:.3f}")
        
        # Test factory status  
        factory_status = proxy_factory.get_provider_status()
        
        assert "configured_provider" in factory_status
        assert "mock_mode" in factory_status
        assert factory_status["mock_mode"] == True
        
        print(f"  - Provider configuré: {factory_status['configured_provider']}")
        print(f"  - Mode mock factory: {factory_status['mock_mode']}")
        
        # Test variables d'environnement
        original_provider = os.getenv("PROXY_PROVIDER")
        
        # Test mode none
        os.environ["PROXY_PROVIDER"] = "none"
        none_provider = proxy_factory.get_proxy_provider()
        assert none_provider.is_mock == True  # Fallback vers mock
        
        # Test mode non existant (fallback)
        os.environ["PROXY_PROVIDER"] = "unknown_provider"
        fallback_provider = proxy_factory.get_proxy_provider()
        assert fallback_provider.is_mock == True
        
        # Restaurer configuration
        if original_provider:
            os.environ["PROXY_PROVIDER"] = original_provider
        elif "PROXY_PROVIDER" in os.environ:
            del os.environ["PROXY_PROVIDER"]
        
        print("✅ Tests fallback configuration OK")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])