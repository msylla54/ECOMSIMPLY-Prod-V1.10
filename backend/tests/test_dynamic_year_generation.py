"""
Tests unitaires pour vérifier que toutes les références d'année dans la génération de fiches produits
sont dynamiques et basées sur datetime.now().year
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

# Import des services qui doivent utiliser l'année dynamique
from server import get_current_year
from services.seo_scraping_service import SEOScrapingService, get_current_year as seo_get_current_year
from src.scraping.publication.publishers.base import get_current_year as publisher_get_current_year
from src.scraping.semantic.seo_utils import SEOMetaGenerator


class TestDynamicYearGeneration:
    """Tests pour vérifier l'utilisation dynamique de l'année dans toute la génération"""
    
    def test_get_current_year_functions_exist(self):
        """Vérifier que toutes les fonctions get_current_year existent et retournent un entier"""
        
        # Test fonction principale du serveur
        assert callable(get_current_year)
        current_year = get_current_year()
        assert isinstance(current_year, int)
        assert current_year >= 2025  # Au minimum 2025
        
        # Test fonction SEO service
        assert callable(seo_get_current_year)
        seo_year = seo_get_current_year()
        assert isinstance(seo_year, int)
        assert seo_year == current_year
        
        # Test fonction publisher
        assert callable(publisher_get_current_year)
        publisher_year = publisher_get_current_year()
        assert isinstance(publisher_year, int)
        assert publisher_year == current_year
    
    @patch('server.datetime')
    def test_server_year_changes_with_mock(self, mock_datetime):
        """Vérifier que l'année change bien quand on mock datetime dans le serveur"""
        # Mock pour année 2026
        mock_datetime.now.return_value = datetime(2026, 6, 15)
        
        # Import dynamique pour que le mock soit pris en compte
        from importlib import reload
        import server
        reload(server)
        
        year = server.get_current_year()
        assert year == 2026
        
        # Mock pour année 2027
        mock_datetime.now.return_value = datetime(2027, 3, 10)
        reload(server)
        
        year = server.get_current_year()
        assert year == 2027
    
    @patch('services.seo_scraping_service.datetime')
    def test_seo_tags_use_dynamic_year(self, mock_datetime):
        """Vérifier que les tags SEO utilisent l'année dynamique"""
        # Mock pour année 2026
        mock_datetime.now.return_value = datetime(2026, 8, 20)
        
        # Reload pour que le mock soit pris en compte
        from importlib import reload
        import services.seo_scraping_service
        reload(services.seo_scraping_service)
        
        seo_service = services.seo_scraping_service.SEOScrapingService()
        tag_generator = seo_service.tag_generator
        
        # Test génération de tags statiques avec année
        static_tags = tag_generator._generate_comprehensive_static_tags("iPhone 15", "smartphone")
        
        # Vérifier qu'au moins un tag contient l'année mockée
        year_tags = [tag for tag in static_tags if "2026" in tag]
        assert len(year_tags) > 0, f"Aucun tag avec année 2026 trouvé dans: {static_tags[:10]}"
        
        # Mock pour année 2028
        mock_datetime.now.return_value = datetime(2028, 12, 5)
        reload(services.seo_scraping_service)
        
        seo_service = services.seo_scraping_service.SEOScrapingService()
        tag_generator = seo_service.tag_generator
        
        static_tags = tag_generator._generate_comprehensive_static_tags("iPhone 15", "smartphone")
        year_tags = [tag for tag in static_tags if "2028" in tag]
        assert len(year_tags) > 0, f"Aucun tag avec année 2028 trouvé dans: {static_tags[:10]}"
    
    @patch('src.scraping.semantic.seo_utils.datetime')
    def test_seo_utils_use_dynamic_year(self, mock_datetime):
        """Vérifier que SEOMetaGenerator utilise l'année dynamique"""
        # Mock pour année 2026
        mock_datetime.now.return_value = datetime(2026, 4, 12)
        
        # Reload pour que le mock soit pris en compte
        from importlib import reload
        import src.scraping.semantic.seo_utils
        reload(src.scraping.semantic.seo_utils)
        
        seo_utils = src.scraping.semantic.seo_utils.SEOMetaGenerator()
        
        # Test génération titre avec année
        title = seo_utils.generate_seo_title("iPhone 15 Pro", "smartphone", "Apple")
        assert "2026" in title, f"Année 2026 non trouvée dans le titre: {title}"
        
        # Test génération meta description
        meta_desc = seo_utils.generate_seo_description("iPhone 15 Pro", price="999€", brand="Apple")
        assert "2026" in meta_desc, f"Année 2026 non trouvée dans la meta description: {meta_desc}"
        
        # Test génération keywords SEO
        keywords = seo_utils.generate_seo_keywords("iPhone 15 Pro", category="smartphone", brand="Apple")
        year_keywords = [kw for kw in keywords if "2026" in kw]
        assert len(year_keywords) > 0, f"Aucun keyword avec année 2026 trouvé dans: {keywords}"
    
    @patch('src.scraping.publication.publishers.base.datetime')
    def test_publishers_use_dynamic_year(self, mock_datetime):
        """Vérifier que les publishers utilisent l'année dynamique pour les API versions"""
        # Mock pour année 2026  
        mock_datetime.now.return_value = datetime(2026, 9, 25)
        
        # Reload pour que le mock soit pris en compte
        from importlib import reload
        import src.scraping.publication.publishers.base
        reload(src.scraping.publication.publishers.base)
        
        from src.scraping.publication.publishers.base import GenericMockPublisher
        
        publisher = GenericMockPublisher("shopify", {})
        config = publisher._get_store_config("shopify")
        
        # Vérifier que l'API version utilise l'année précédente (2025 pour mock 2026)
        api_version = config["api_version"]
        assert "2025-04" in api_version, f"API version devrait contenir '2025-04', trouvé: {api_version}"
        
        # Mock pour année 2027
        mock_datetime.now.return_value = datetime(2027, 1, 15)
        reload(src.scraping.publication.publishers.base)
        
        publisher = src.scraping.publication.publishers.base.GenericMockPublisher("shopify", {})
        config = publisher._get_store_config("shopify")
        
        api_version = config["api_version"]
        assert "2026-04" in api_version, f"API version devrait contenir '2026-04', trouvé: {api_version}"
    
    def test_current_year_is_consistent_across_modules(self):
        """Vérifier que toutes les fonctions get_current_year retournent la même année"""
        server_year = get_current_year()
        seo_year = seo_get_current_year()
        publisher_year = publisher_get_current_year()
        
        # Toutes les fonctions doivent retourner la même année
        assert server_year == seo_year == publisher_year
        
        # Et cette année doit être l'année courante réelle
        real_current_year = datetime.now().year
        assert server_year == real_current_year
    
    def test_no_hardcoded_years_in_functions(self):
        """Test de régression pour s'assurer qu'aucune année n'est codée en dur"""
        # Ce test vérifie que les fonctions importantes utilisent bien datetime.now()
        # et non des valeurs codées en dur
        
        current_year = datetime.now().year
        
        # Test avec SEOMetaGenerator
        seo_utils = SEOMetaGenerator()
        title = seo_utils.generate_seo_title("Test Product", "électronique")
        
        # Le titre doit contenir l'année courante, pas une année codée en dur
        assert str(current_year) in title
        assert "2024" not in title or current_year == 2024  # Permettre 2024 seulement si c'est l'année courante
        assert "2023" not in title
        
        # Test avec SEO tags
        seo_service = SEOScrapingService()
        result = seo_service.tag_generator.generate_20_seo_tags(
            "Test Product",
            category="électronique"
        )
        
        tags_with_current_year = [tag for tag in result["tags"] if str(current_year) in tag]
        tags_with_old_years = [tag for tag in result["tags"] if "2024" in tag or "2023" in tag]
        
        # Doit avoir des tags avec l'année courante
        # et pas de tags avec des années codées en dur (sauf si c'est l'année courante)
        if current_year != 2024:
            assert len([tag for tag in tags_with_old_years if "2024" in tag]) == 0
        if current_year != 2023:
            assert len([tag for tag in tags_with_old_years if "2023" in tag]) == 0
    
    def test_year_appears_in_generated_content(self):
        """Vérifier que l'année courante apparaît dans le contenu généré"""
        current_year = datetime.now().year
        
        # Test que l'année courante apparaît dans les différents types de contenu
        seo_utils = SEOMetaGenerator()
        
        # Titre SEO
        title = seo_utils.generate_seo_title("iPhone 15", "smartphone")
        assert str(current_year) in title, f"Année {current_year} non trouvée dans le titre: {title}"
        
        # Meta description  
        description = seo_utils.generate_seo_description("iPhone 15", price="999€")
        assert str(current_year) in description, f"Année {current_year} non trouvée dans la description: {description}"
        
        # Structured data
        structured_data = seo_utils.generate_structured_data({"name": "iPhone 15", "price": {"amount": 999, "currency": "EUR"}})
        structured_str = json.dumps(structured_data)
        assert str(current_year) in structured_str, f"Année {current_year} non trouvée dans les structured data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])