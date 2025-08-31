"""
Tests pour l'étape 1: Couches d'abstraction + mocks
"""

import pytest
import asyncio
import os
from datetime import datetime
from unittest.mock import patch

from backend.services.publication_interfaces import (
    ProductDTO, PublishResult, PublicationPlatform, PublicationStatus, 
    PublicationConfig, ImageDTO
)
from backend.services.publication_factory import (
    PublicationFactory, publication_factory, publish_product_to_platforms,
    extract_price_from_suggestions
)
from backend.services.mock_publishers import (
    MockShopifyPublisher, MockWooCommercePublisher, MockPrestaShopPublisher,
    mock_storage
)

class TestPublicationFactoryMockMode:
    """Test de la factory en mode mock"""
    
    @pytest.fixture(autouse=True)
    def setup_mock_mode(self):
        """Force le mode mock pour les tests"""
        with patch.dict(os.environ, {'MOCK_MODE': 'true'}):
            yield
    
    @pytest.fixture
    def clean_storage(self):
        """Nettoie le storage mock avant chaque test"""
        mock_storage.clear_all()
        yield
        mock_storage.clear_all()
    
    def test_publication_factory_mock_mode(self, clean_storage):
        """Test: Factory retourne publishers mock en mode mock"""
        factory = PublicationFactory()
        
        # Vérifier mode mock activé
        assert factory.config.mock_mode is True
        
        # Tester tous les publishers supportés
        shopify_pub = factory.get_publisher(PublicationPlatform.SHOPIFY)
        woo_pub = factory.get_publisher(PublicationPlatform.WOOCOMMERCE)  
        presta_pub = factory.get_publisher(PublicationPlatform.PRESTASHOP)
        
        # Vérifier que tous sont disponibles et sont des mocks
        assert shopify_pub is not None
        assert isinstance(shopify_pub, MockShopifyPublisher)
        assert shopify_pub.is_mock is True
        
        assert woo_pub is not None
        assert isinstance(woo_pub, MockWooCommercePublisher)
        assert woo_pub.is_mock is True
        
        assert presta_pub is not None
        assert isinstance(presta_pub, MockPrestaShopPublisher)
        assert presta_pub.is_mock is True
        
        # Tester publisher non-supporté
        ebay_pub = factory.get_publisher(PublicationPlatform.EBAY)
        assert ebay_pub is None
    
    def test_get_all_available_publishers(self, clean_storage):
        """Test: Récupération de tous les publishers disponibles"""
        factory = PublicationFactory()
        publishers = factory.get_all_available_publishers()
        
        # Vérifier qu'on a les 3 plateformes principales
        expected_platforms = {
            PublicationPlatform.SHOPIFY,
            PublicationPlatform.WOOCOMMERCE,
            PublicationPlatform.PRESTASHOP
        }
        
        assert set(publishers.keys()) == expected_platforms
        assert all(pub.is_mock for pub in publishers.values())
    
    def test_platform_status_in_mock_mode(self, clean_storage):
        """Test: Statut des plateformes en mode mock"""
        factory = PublicationFactory()
        
        shopify_status = factory.get_platform_status(PublicationPlatform.SHOPIFY)
        
        assert shopify_status["available"] is True
        assert shopify_status["mode"] == "mock"
        assert shopify_status["platform"] == "shopify"
        assert len(shopify_status["missing_env"]) == 0  # Pas de vérif env en mode mock
    
    def test_global_status_mock_mode(self, clean_storage):
        """Test: Statut global en mode mock"""
        factory = PublicationFactory()
        status = factory.get_global_status()
        
        assert status["mode"] == "mock"
        assert status["mock_mode"] is True
        assert status["platforms_available"] == 3
        assert status["platforms_mock"] == 3
        assert status["platforms_real"] == 0
        assert status["ready_for_production"] is False

@pytest.mark.asyncio
class TestMockPublishersCreateLog:
    """Test que les publishers mock créent bien des logs"""
    
    @pytest.fixture
    def sample_product(self):
        """Produit échantillon pour les tests"""
        return ProductDTO(
            user_id="test_user_123",
            name="Test Product Mock",
            description="This is a test product for mock publication testing",
            price=29.99,
            tags=["test", "mock", "ecommerce"],
            category="Electronics",
            sku="TEST-MOCK-001"
        )
    
    @pytest.fixture(autouse=True)
    def clean_storage(self):
        """Nettoie le storage mock avant chaque test"""
        mock_storage.clear_all()
        yield
        mock_storage.clear_all()
    
    async def test_mock_publish_creates_log_shopify(self, sample_product):
        """Test: Publication mock Shopify crée un log"""
        publisher = MockShopifyPublisher()
        store_config = {"id": "test_store", "name": "Test Store"}
        
        # Publication
        result = await publisher.publish_product(sample_product, store_config)
        
        # Vérifications du résultat
        assert isinstance(result, PublishResult)
        assert result.platform == PublicationPlatform.SHOPIFY
        assert result.mode == "mock"
        assert result.publication_id is not None
        
        # Vérification que le log est créé
        publications = mock_storage.get_publications()
        assert len(publications) == 1
        
        pub_log = publications[0]
        assert pub_log["platform"] == "shopify"
        assert pub_log["product_name"] == "Test Product Mock"
        assert pub_log["mode"] == "mock"
        assert "created_at" in pub_log
        
        # Vérification des stats
        stats = mock_storage.get_stats()
        assert stats["shopify_attempts"] == 1
        if result.success:
            assert stats["shopify_success"] == 1
            assert stats["shopify_success_rate"] == 100.0
        else:
            assert stats["shopify_failures"] == 1
    
    async def test_mock_publish_creates_log_woocommerce(self, sample_product):
        """Test: Publication mock WooCommerce crée un log"""
        publisher = MockWooCommercePublisher()
        store_config = {"id": "test_woo_store", "name": "Test WooCommerce"}
        
        result = await publisher.publish_product(sample_product, store_config)
        
        assert result.platform == PublicationPlatform.WOOCOMMERCE
        assert result.mode == "mock"
        
        publications = mock_storage.get_publications()
        assert len(publications) == 1
        assert publications[0]["platform"] == "woocommerce"
    
    async def test_mock_publish_creates_log_prestashop(self, sample_product):
        """Test: Publication mock PrestaShop crée un log"""
        publisher = MockPrestaShopPublisher()
        store_config = {"id": "test_presta_store", "name": "Test PrestaShop"}
        
        result = await publisher.publish_product(sample_product, store_config)
        
        assert result.platform == PublicationPlatform.PRESTASHOP
        assert result.mode == "mock"
        
        publications = mock_storage.get_publications()
        assert len(publications) == 1
        assert publications[0]["platform"] == "prestashop"
    
    async def test_multiple_mock_publications_logged(self, sample_product):
        """Test: Plusieurs publications sont bien loggées"""
        publishers = [
            MockShopifyPublisher(),
            MockWooCommercePublisher(), 
            MockPrestaShopPublisher()
        ]
        
        store_config = {"id": "multi_test", "name": "Multi Test Store"}
        
        # Publier sur toutes les plateformes
        results = []
        for publisher in publishers:
            result = await publisher.publish_product(sample_product, store_config)
            results.append(result)
        
        # Vérifications
        publications = mock_storage.get_publications()
        assert len(publications) == 3
        
        platforms = {pub["platform"] for pub in publications}
        expected_platforms = {"shopify", "woocommerce", "prestashop"}
        assert platforms == expected_platforms
        
        # Toutes les publications ont le même produit
        assert all(pub["product_name"] == "Test Product Mock" for pub in publications)

class TestStatusPublicationReportsMissingEnv:
    """Test que /status/publication rapporte correctement les variables manquantes"""
    
    @pytest.fixture(autouse=True) 
    def clean_env(self):
        """Nettoie les variables d'environnement"""
        env_vars = [
            'SHOPIFY_STORE_URL', 'SHOPIFY_ACCESS_TOKEN',
            'WOO_STORE_URL', 'WOO_CONSUMER_KEY', 'WOO_CONSUMER_SECRET',
            'PRESTA_STORE_URL', 'PRESTA_API_KEY'
        ]
        
        original_values = {}
        for var in env_vars:
            original_values[var] = os.getenv(var)
            if var in os.environ:
                del os.environ[var]
        
        yield
        
        # Restaurer les valeurs originales
        for var, value in original_values.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]
    
    def test_status_publication_reports_missing_env(self):
        """Test: Status endpoint rapporte les variables manquantes"""
        with patch.dict(os.environ, {'MOCK_MODE': 'false'}):  # Mode réel
            factory = PublicationFactory()
            status = factory.get_global_status()
            
            # En mode réel sans env vars, toutes devraient être manquantes
            assert status["mock_mode"] is False
            assert len(status["missing_env_vars"]) > 0
            
            expected_missing = [
                'SHOPIFY_STORE_URL', 'SHOPIFY_ACCESS_TOKEN',
                'WOO_STORE_URL', 'WOO_CONSUMER_KEY', 'WOO_CONSUMER_SECRET', 
                'PRESTA_STORE_URL', 'PRESTA_API_KEY'
            ]
            
            for var in expected_missing:
                assert var in status["missing_env_vars"]
            
            # Vérifier statut des plateformes individuelles
            for platform in ["shopify", "woocommerce", "prestashop"]:
                platform_status = status["platforms"][platform]
                assert len(platform_status["missing_env"]) > 0
    
    def test_status_with_partial_env_vars(self):
        """Test: Status avec variables partielles"""
        partial_env = {
            'MOCK_MODE': 'false',
            'SHOPIFY_STORE_URL': 'https://test-store.myshopify.com'
            # SHOPIFY_ACCESS_TOKEN manquant
        }
        
        with patch.dict(os.environ, partial_env):
            factory = PublicationFactory()
            shopify_status = factory.get_platform_status(PublicationPlatform.SHOPIFY)
            
            # Shopify devrait toujours être indisponible car ACCESS_TOKEN manque
            assert shopify_status["available"] is True  # Available via mock fallback
            assert shopify_status["mode"] == "mock"  # Fallback to mock
            assert "SHOPIFY_ACCESS_TOKEN" in shopify_status["missing_env"]
    
    def test_mock_mode_ignores_missing_env(self):
        """Test: Mode mock ignore les variables manquantes"""
        with patch.dict(os.environ, {'MOCK_MODE': 'true'}):
            factory = PublicationFactory()
            status = factory.get_global_status()
            
            # Mode mock ne devrait pas rapporter de missing env
            assert status["mock_mode"] is True
            
            # Les plateformes devraient être disponibles malgré les env manquantes
            for platform in ["shopify", "woocommerce", "prestashop"]:
                platform_status = status["platforms"][platform]
                assert platform_status["available"] is True
                assert platform_status["mode"] == "mock"

class TestPriceExtraction:
    """Test de l'extraction de prix depuis les suggestions IA"""
    
    def test_extract_price_from_suggestions(self):
        """Test: Extraction de prix depuis différents formats"""
        test_cases = [
            ("Prix recommandé: 29.99€", 29.99),
            ("Entre 25,50€ et 35,00€", 25.50),  # Premier prix trouvé
            ("€ 19.90", 19.90),
            ("Environ 150 EUR", 150.0),
            ("45€", 45.0),
            ("Prix: 12.5", 12.5),
            ("Gratuit", None),
            ("Sur demande", None),
            ("", None),
            ("abc", None)
        ]
        
        for price_text, expected in test_cases:
            result = extract_price_from_suggestions(price_text)
            assert result == expected, f"Failed for '{price_text}': expected {expected}, got {result}"

@pytest.mark.asyncio
class TestPublishProductToPlatforms:
    """Test de la fonction utilitaire de publication multi-plateformes"""
    
    @pytest.fixture(autouse=True)
    def clean_storage(self):
        """Nettoie le storage mock"""
        mock_storage.clear_all()
        yield
        mock_storage.clear_all()
    
    @pytest.fixture
    def sample_product_data(self):
        """Données produit échantillon"""
        return {
            "id": "test_product_123",
            "product_name": "Test Product",
            "generated_title": "Amazing Test Product - Premium Quality",
            "marketing_description": "This is a comprehensive test product description that should be long enough for proper testing of the publication pipeline.",
            "price_suggestions": "Prix recommandé: 39.99€ - 49.99€",
            "seo_tags": ["test", "product", "amazing", "premium"],
            "key_features": ["Feature 1", "Feature 2", "Feature 3"],
            "category": "Test Category",
            "generated_images": ["data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."]  # Mock base64
        }
    
    async def test_publish_product_to_all_platforms(self, sample_product_data):
        """Test: Publication sur toutes les plateformes par défaut"""
        with patch.dict(os.environ, {'MOCK_MODE': 'true'}):
            results = await publish_product_to_platforms(
                sample_product_data, 
                user_id="test_user"
            )
            
            # Devrait avoir 3 résultats (shopify, woocommerce, prestashop)
            assert len(results) == 3
            
            platforms = {result["platform"] for result in results}
            expected_platforms = {"shopify", "woocommerce", "prestashop"}
            assert platforms == expected_platforms
            
            # Tous devraient être en mode mock
            assert all(result["mode"] == "mock" for result in results)
            
            # Vérifier que les publications sont dans le storage
            publications = mock_storage.get_publications()
            assert len(publications) >= 3
    
    async def test_publish_product_to_specific_platforms(self, sample_product_data):
        """Test: Publication sur plateformes spécifiques"""
        with patch.dict(os.environ, {'MOCK_MODE': 'true'}):
            results = await publish_product_to_platforms(
                sample_product_data,
                platforms=["shopify", "woocommerce"],
                user_id="test_user"
            )
            
            assert len(results) == 2
            platforms = {result["platform"] for result in results}
            assert platforms == {"shopify", "woocommerce"}
    
    async def test_publish_product_with_images(self, sample_product_data):
        """Test: Publication avec images intégrées"""
        # Ajouter plusieurs images
        sample_product_data["generated_images"] = [
            "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..."
        ]
        
        with patch.dict(os.environ, {'MOCK_MODE': 'true'}):
            results = await publish_product_to_platforms(
                sample_product_data,
                platforms=["shopify"],
                user_id="test_user"
            )
            
            assert len(results) == 1
            result = results[0]
            
            # Vérifier que les images sont comptées
            assert result["images_uploaded"] == 2