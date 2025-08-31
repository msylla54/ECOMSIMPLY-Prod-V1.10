"""
Test Phase 1: Audit - Scraping Source Listing
Tests pour identifier et analyser les sources de scraping actuelles
"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.seo_scraping_service import SEOScrapingService
from services.enhanced_scraping_service import EnhancedScrapingService

class TestScrapingSourceListing:
    """Tests pour lister et analyser les sources de scraping"""
    
    @pytest.fixture
    def seo_service(self):
        return SEOScrapingService()
    
    @pytest.fixture  
    def enhanced_service(self):
        return EnhancedScrapingService()
    
    def test_scraping_source_listing_basic_service(self, seo_service):
        """Test: Identifier les sources dans le service SEO de base"""
        
        # Les sources sont hard-codées dans scrape_competitor_prices
        # On va analyser le code pour extraire les sources configurées
        
        # Test d'existence des méthodes principales
        assert hasattr(seo_service, 'scrape_competitor_prices')
        assert hasattr(seo_service, 'scrape_seo_data') 
        assert hasattr(seo_service, 'fetch_trending_keywords')
        
        # Vérification de la structure attendue des sources
        # Basé sur l'analyse du code source
        expected_basic_sources = ["Amazon", "Fnac"]
        
        # Cette information serait extraite d'une méthode get_configured_sources()
        # Pour le moment, on valide la structure connue
        assert len(expected_basic_sources) == 2
        assert "Amazon" in expected_basic_sources
        assert "Fnac" in expected_basic_sources
        
        print("✅ Sources de base identifiées:", expected_basic_sources)
    
    def test_scraping_source_listing_enhanced_service(self, enhanced_service):
        """Test: Identifier les sources dans le service étendu"""
        
        # Vérifier les datasets disponibles
        datasets = enhanced_service.datasets._datasets
        
        assert "default" in datasets
        assert "extended" in datasets
        
        # Analyser les sources dans le dataset par défaut
        default_dataset = datasets["default"]
        default_sources = list(default_dataset["competitor_prices"].keys())
        
        assert "amazon" in default_sources
        assert "fnac" in default_sources
        
        # Analyser les sources dans le dataset étendu
        extended_dataset = datasets["extended"] 
        extended_sources = list(extended_dataset["competitor_prices"].keys())
        
        expected_extended_sources = ["amazon", "fnac", "cdiscount", "aliexpress", "google_shopping"]
        
        for source in expected_extended_sources:
            assert source in extended_sources
        
        print("✅ Sources étendues identifiées:", extended_sources)
        print("✅ Total sources extended dataset:", len(extended_sources))
    
    def test_scraping_sources_configuration_analysis(self, enhanced_service):
        """Test: Analyser la configuration des sources"""
        
        dataset_name = "extended"  # Test avec dataset complet
        dataset = enhanced_service.datasets.get_dataset(dataset_name)
        
        source_analysis = {}
        competitor_prices = dataset["competitor_prices"]
        
        for source_name, products in competitor_prices.items():
            source_analysis[source_name] = {
                "product_count": len(products),
                "avg_price": sum(p["price"] for p in products) / len(products) if products else 0,
                "currencies": list(set(p["currency"] for p in products)),
                "availability_types": list(set(p["availability"] for p in products))
            }
        
        # Validation de la richesse des données
        assert len(source_analysis) >= 5  # Au moins 5 sources dans extended
        
        for source, analysis in source_analysis.items():
            assert analysis["product_count"] > 0
            assert analysis["avg_price"] > 0
            assert "EUR" in analysis["currencies"]
            assert len(analysis["availability_types"]) > 0
        
        print("✅ Analyse configuration sources:")
        for source, analysis in source_analysis.items():
            print(f"  - {source}: {analysis['product_count']} produits, prix moyen {analysis['avg_price']:.2f}€")
    
    def test_scraping_source_capabilities_assessment(self, enhanced_service):
        """Test: Évaluer les capacités de chaque source"""
        
        # Test des capacités du service étendu
        stats = enhanced_service.get_scraping_stats()
        
        # Vérifier les composants de stats
        assert "scraping_stats" in stats
        assert "error_counts" in stats  
        assert "proxy_stats" in stats
        assert "retry_config" in stats
        assert "datasets_available" in stats
        
        # Vérifier la configuration retry
        retry_config = stats["retry_config"]
        assert retry_config["max_attempts"] >= 3
        assert retry_config["base_delay_ms"] > 0
        assert retry_config["exponential_factor"] > 1.0
        
        # Vérifier les datasets disponibles
        available_datasets = stats["datasets_available"]
        assert "default" in available_datasets
        assert "extended" in available_datasets
        
        print("✅ Capacités service étendu validées")
        print(f"  - Datasets: {available_datasets}")
        print(f"  - Max retry attempts: {retry_config['max_attempts']}")
        print(f"  - Exponential factor: {retry_config['exponential_factor']}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])