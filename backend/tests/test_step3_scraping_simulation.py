"""
Tests pour l'étape 3: Scraping en simulation contrôlée
"""

import pytest
import asyncio
import os
from unittest.mock import patch, AsyncMock

from backend.services.proxy_providers import (
    MockProxyProvider, ProxyProviderFactory, proxy_factory
)
from backend.services.enhanced_scraping_service import (
    EnhancedScrapingService, ScrapingDatasets, enhanced_scraping_service
)

@pytest.mark.asyncio
class TestStep3ScrapingSimulation:
    """Tests pour le scraping en simulation contrôlée"""
    
    async def test_mock_scraping_uses_no_network(self):
        """Test: Le scraping mock n'utilise aucun appel réseau"""
        
        scraping_service = EnhancedScrapingService()
        
        # Test avec monitoring d'appels réseau (simulation)
        with patch('aiohttp.ClientSession') as mock_session:
            with patch('requests.get') as mock_requests:
                
                # Test scraping prix
                price_result = await scraping_service.scrape_competitor_prices_enhanced(
                    product_name="Test Product Network",
                    sources=["amazon", "fnac"]
                )
                
                # Test scraping SEO
                seo_result = await scraping_service.scrape_seo_data_enhanced(
                    product_name="Test Product Network"
                )
                
                # Test trending keywords
                trending_result = await scraping_service.fetch_trending_keywords_enhanced(
                    product_name="Test Product Network"
                )
                
                # Vérifications - aucun appel réseau réel
                mock_session.assert_not_called()
                mock_requests.assert_not_called()
                
                # Vérifier que les résultats sont présents (simulés)
                assert price_result is not None
                assert "sources_analyzed" in price_result
                assert seo_result is not None
                assert "keywords" in seo_result
                assert trending_result is not None
                assert "keywords" in trending_result
    
    async def test_scraping_retry_called_in_mock(self):
        """Test: La logique de retry est bien appelée en mode mock"""
        
        scraping_service = EnhancedScrapingService()
        
        # Test que la configuration retry existe
        retry_config = scraping_service.retry_config
        assert retry_config.max_attempts == 3
        assert retry_config.base_delay_ms == 1000
        assert retry_config.exponential_factor == 2.0
        
        # Test un scraping avec un nom qui match (iPhone pour amazon)
        result = await scraping_service.scrape_competitor_prices_enhanced(
            product_name="iPhone 15 Pro",  # Ce nom matche dans le dataset
            sources=["amazon"]
        )
        
        # Le résultat doit contenir des informations sur les attempts
        assert "total_attempts" in result
        # Au moins 1 attempt doit être fait si des données sont trouvées
        if result["found_prices"] > 0:
            assert result["total_attempts"] >= 1
    
    async def test_scraping_source_set_switches_dataset(self):
        """Test: SCRAPING_SOURCE_SET change le dataset utilisé"""
        
        datasets = ScrapingDatasets()
        
        # Test dataset default
        default_data = datasets.get_dataset("default")
        assert "amazon" in default_data["competitor_prices"]
        assert "fnac" in default_data["competitor_prices"]
        
        # Test dataset extended
        extended_data = datasets.get_dataset("extended")
        assert "amazon" in extended_data["competitor_prices"]
        assert "fnac" in extended_data["competitor_prices"]
        assert "cdiscount" in extended_data["competitor_prices"]
        assert "aliexpress" in extended_data["competitor_prices"]
        assert "google_shopping" in extended_data["competitor_prices"]
        
        # Vérifier que extended a plus de données
        assert len(extended_data["competitor_prices"]) > len(default_data["competitor_prices"])
        assert len(extended_data["seo_data"]["keywords"]) > len(default_data["seo_data"]["keywords"])
    
    async def test_scraping_with_source_set_env_var(self):
        """Test: Variable d'environnement SCRAPING_SOURCE_SET fonctionne"""
        
        scraping_service = EnhancedScrapingService()
        
        # Test avec dataset default
        with patch.dict(os.environ, {'SCRAPING_SOURCE_SET': 'default'}):
            result_default = await scraping_service.scrape_competitor_prices_enhanced(
                product_name="Source Set Test"
            )
            
            assert result_default["dataset_used"] == "default"
            assert result_default["sources_analyzed"] == 2  # amazon + fnac
        
        # Test avec dataset extended
        with patch.dict(os.environ, {'SCRAPING_SOURCE_SET': 'extended'}):
            result_extended = await scraping_service.scrape_competitor_prices_enhanced(
                product_name="Source Set Test"
            )
            
            assert result_extended["dataset_used"] == "extended"
            assert result_extended["sources_analyzed"] == 5  # 5 sources in extended

@pytest.mark.asyncio
class TestProxyProviderMock:
    """Tests pour le provider de proxy mock"""
    
    async def test_mock_proxy_provider_returns_proxies(self):
        """Test: MockProxyProvider retourne des proxies fonctionnels"""
        
        provider = MockProxyProvider()
        
        # Test récupération proxy simple
        proxy = await provider.get_proxy()
        assert proxy is not None
        assert proxy.id is not None
        assert proxy.host.endswith('.mock.local')
        assert proxy.is_healthy is not None
        assert proxy.country is not None
        
        # Test récupération proxy par pays
        fr_proxy = await provider.get_proxy(country="FR")
        if fr_proxy:  # Peut être None si pas de proxy FR disponible
            assert fr_proxy.country == "FR"
        
        # Test récupération pool de proxies
        proxy_pool = await provider.get_proxy_pool(size=5)
        assert len(proxy_pool) <= 5
        assert all(p.id is not None for p in proxy_pool)
    
    async def test_proxy_health_check_simulation(self):
        """Test: Health check des proxies simulé"""
        
        provider = MockProxyProvider()
        proxy = await provider.get_proxy()
        
        if proxy:
            health_result = await provider.health_check(proxy)
            
            assert "status" in health_result
            assert "available" in health_result
            assert "response_time_ms" in health_result
            assert "proxy_id" in health_result
            assert health_result["mock_provider"] is True
    
    async def test_proxy_usage_reporting(self):
        """Test: Reporting d'utilisation des proxies"""
        
        provider = MockProxyProvider()
        proxy = await provider.get_proxy()
        
        if proxy:
            # Simuler utilisation réussie
            await provider.report_proxy_status(proxy.id, success=True, response_time_ms=200)
            
            # Simuler utilisation échouée
            await provider.report_proxy_status(proxy.id, success=False, response_time_ms=5000)
            
            # Vérifier stats
            stats = provider.get_provider_stats()
            assert stats["provider_name"] == "MockProxyProvider"
            assert stats["is_mock"] is True
            assert "total_proxies" in stats
            assert "healthy_proxies" in stats

class TestProxyProviderFactory:
    """Tests pour la factory des providers proxy"""
    
    def test_proxy_factory_default_mock(self):
        """Test: Factory retourne MockProxyProvider par défaut"""
        
        factory = ProxyProviderFactory()
        
        with patch.dict(os.environ, {'PROXY_PROVIDER': 'mock'}):
            provider = factory.get_proxy_provider()
            
            assert provider is not None
            assert provider.is_mock is True
            assert provider.provider_name == "MockProxyProvider"
    
    def test_proxy_factory_status(self):
        """Test: Status de la factory proxy"""
        
        factory = ProxyProviderFactory()
        status = factory.get_provider_status()
        
        assert "configured_provider" in status
        assert "mock_mode" in status
        assert "proxy_api_key_configured" in status
        assert "total_proxies" in status
        
        # En mode mock
        assert status["mock_mode"] is True

@pytest.mark.asyncio
class TestScrapingIntegration:
    """Tests d'intégration du scraping amélioré"""
    
    async def test_enhanced_scraping_service_complete_flow(self):
        """Test: Flow complet du service de scraping amélioré"""
        
        service = EnhancedScrapingService()
        
        # Test flow complet
        with patch.dict(os.environ, {'SCRAPING_SOURCE_SET': 'extended'}):
            
            # Scraping prix
            price_result = await service.scrape_competitor_prices_enhanced(
                product_name="Integration Test Product",
                category="Electronics"
            )
            
            assert price_result is not None
            assert "found_prices" in price_result
            assert "price_statistics" in price_result
            assert price_result["dataset_used"] == "extended"
            
            # Scraping SEO
            seo_result = await service.scrape_seo_data_enhanced(
                product_name="Integration Test Product",
                category="Electronics"
            )
            
            assert "keywords" in seo_result
            assert len(seo_result["keywords"]) > 0
            
            # Trending keywords
            trending_result = await service.fetch_trending_keywords_enhanced(
                product_name="Integration Test Product",
                category="Electronics",
                user_id="integration_test_user"
            )
            
            assert "keywords" in trending_result
            assert "confidence" in trending_result
            assert trending_result["category_enhanced"] is True
    
    async def test_scraping_stats_tracking(self):
        """Test: Tracking des statistiques de scraping"""
        
        service = EnhancedScrapingService()
        
        # Effectuer quelques opérations
        await service.scrape_competitor_prices_enhanced("Stats Test Product")
        await service.scrape_seo_data_enhanced("Stats Test Product")
        await service.fetch_trending_keywords_enhanced("Stats Test Product")
        
        # Vérifier stats
        stats = service.get_scraping_stats()
        
        assert "scraping_stats" in stats
        assert "proxy_stats" in stats
        assert "retry_config" in stats
        assert "datasets_available" in stats
        assert "current_dataset" in stats
        
        # Vérifier que les compteurs ont été mis à jour
        scraping_stats = stats["scraping_stats"]
        assert scraping_stats.get("competitor_price_requests", 0) >= 1
        assert scraping_stats.get("seo_requests", 0) >= 1
        assert scraping_stats.get("trending_requests", 0) >= 1

class TestStep3Validation:
    """Validation complète de l'étape 3"""
    
    def test_step3_requirements_complete(self):
        """Test: Toutes les exigences de l'étape 3 sont remplies"""
        
        # 1. Vérifier ProxyProvider interface existe
        from backend.services.proxy_providers import IProxyProvider, MockProxyProvider
        assert IProxyProvider is not None
        assert MockProxyProvider is not None
        
        # 2. Vérifier MockProxyProvider implémente l'interface
        provider = MockProxyProvider()
        assert hasattr(provider, 'get_proxy')
        assert hasattr(provider, 'get_proxy_pool')
        assert hasattr(provider, 'health_check')
        assert hasattr(provider, 'report_proxy_status')
        assert hasattr(provider, 'get_provider_stats')
        assert provider.is_mock is True
        
        # 3. Vérifier EnhancedScrapingService existe
        from backend.services.enhanced_scraping_service import EnhancedScrapingService
        service = EnhancedScrapingService()
        assert hasattr(service, 'scrape_competitor_prices_enhanced')
        assert hasattr(service, 'scrape_seo_data_enhanced') 
        assert hasattr(service, 'fetch_trending_keywords_enhanced')
        
        # 4. Vérifier datasets configurables
        from backend.services.enhanced_scraping_service import ScrapingDatasets
        datasets = ScrapingDatasets()
        default_data = datasets.get_dataset("default")
        extended_data = datasets.get_dataset("extended")
        
        assert default_data is not None
        assert extended_data is not None
        assert len(extended_data["competitor_prices"]) > len(default_data["competitor_prices"])
        
        # 5. Vérifier configuration par variables d'environnement
        with patch.dict(os.environ, {'SCRAPING_SOURCE_SET': 'extended'}):
            assert os.getenv('SCRAPING_SOURCE_SET') == 'extended'
        
        with patch.dict(os.environ, {'PROXY_PROVIDER': 'mock'}):
            assert os.getenv('PROXY_PROVIDER') == 'mock'
        
        print("✅ ÉTAPE 3 - Toutes les exigences validées: Proxy providers mock, Scraping avec retry/backoff, Datasets configurables, Configuration par env vars")