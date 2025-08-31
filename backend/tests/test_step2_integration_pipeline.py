"""
Tests pour l'étape 2: Intégration endpoint generate-sheet → pipeline mock
"""

import pytest
import asyncio
import os
import json
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock

from backend.services.mock_publishers import mock_storage

@pytest.mark.asyncio
class TestGenerateTriggersMatchPublish:
    """Test que /generate-sheet déclenche la publication mock quand activée"""
    
    @pytest.fixture(autouse=True)
    def clean_storage(self):
        """Nettoie le storage mock avant chaque test"""
        mock_storage.clear_all()
        yield
        mock_storage.clear_all()
    
    @pytest.fixture
    def mock_request_data(self):
        """Données de requête test"""
        return {
            "product_name": "Test Product Publication",
            "product_description": "This is a test product for publication testing",
            "category": "Electronics",
            "generate_image": True,
            "number_of_images": 2,
            "image_style": "professional",
            "use_case": "e-commerce"
        }
    
    @pytest.fixture
    def mock_user(self):
        """Utilisateur mock"""
        user = MagicMock()
        user.id = "test_user_123"
        user.subscription_plan = "pro"
        return user
    
    @pytest.fixture
    def mock_db(self):
        """Database mock"""
        db_mock = MagicMock()
        
        # Mock des collections
        db_mock.product_sheets.count_documents = AsyncMock(return_value=5)
        db_mock.product_sheets.insert_one = AsyncMock()
        db_mock.product_sheets.insert_one.return_value.inserted_id = "mock_sheet_id_123"
        
        return db_mock
    
    @pytest.fixture
    def mock_services(self):
        """Services mock"""
        # Mock ImageGenerationService
        image_service_mock = MagicMock()
        image_service_mock.generate_images = AsyncMock(return_value=[
            "data:image/jpeg;base64,/9j/test1...",
            "data:image/jpeg;base64,/9j/test2..."
        ])
        
        # Mock SEOScrapingService
        seo_service_mock = MagicMock()
        seo_service_mock.scrape_competitor_prices = AsyncMock(return_value={
            "found_prices": 3,
            "min_price": 25.99,
            "max_price": 39.99,
            "avg_price": 32.99
        })
        seo_service_mock.scrape_seo_data = AsyncMock(return_value={
            "keywords": ["test", "product", "electronics"],
            "titles": ["Test Product", "Electronics Test"]
        })
        seo_service_mock.fetch_trending_keywords = AsyncMock(return_value={
            "keywords": ["trending", "popular"],
            "confidence": 0.8,
            "source": "google_trends"
        })
        
        # Mock GPTContentService
        gpt_service_mock = MagicMock()
        gpt_service_mock.generate_product_content = AsyncMock(return_value={
            "generated_title": "Amazing Test Product - Premium Electronics",
            "marketing_description": "This is a comprehensive test product description that showcases all the amazing features and benefits of our premium electronics product.",
            "key_features": ["Feature 1", "Feature 2", "Feature 3"],
            "seo_tags": ["test", "product", "electronics", "premium", "amazing"],
            "price_suggestions": "Prix recommandé: 32.99€ - 39.99€",
            "target_audience": "Tech enthusiasts and professionals",
            "call_to_action": "Order now for the best deal!",
            "model_used": "gpt-4o-mini",
            "generation_method": "full_generation",
            "fallback_level": 1
        })
        
        return {
            "image": image_service_mock,
            "seo": seo_service_mock, 
            "gpt": gpt_service_mock
        }
    
    async def test_generate_triggers_mock_publish_when_enabled(self, mock_request_data, mock_user, mock_db, mock_services):
        """Test: /generate-sheet déclenche publication mock si PUBLISH_AUTO=true"""
        
        with patch.dict(os.environ, {'MOCK_MODE': 'true', 'PUBLISH_AUTO': 'true'}):
            with patch('backend.server.db', mock_db):
                with patch('backend.server.ImageGenerationService', return_value=mock_services["image"]):
                    with patch('backend.server.SEOScrapingService', return_value=mock_services["seo"]):
                        with patch('backend.server.GPTContentService', return_value=mock_services["gpt"]):
                            with patch('backend.server.qa_service') as mock_qa:
                                # Configuration QA service mock
                                mock_qa.should_simulate_failure.return_value = {"simulate": False}
                                mock_qa.log_test_result = MagicMock()
                                mock_qa.test_mode = False
                                
                                # Mock de la fonction de publication
                                with patch('backend.services.publication_factory.publish_product_to_platforms') as mock_publish:
                                    mock_publish.return_value = [
                                        {
                                            "platform": "shopify",
                                            "success": True,
                                            "product_id": "mock_shopify_123",
                                            "mode": "mock"
                                        },
                                        {
                                            "platform": "woocommerce",
                                            "success": True,
                                            "product_id": "mock_woo_456",
                                            "mode": "mock"
                                        },
                                        {
                                            "platform": "prestashop",
                                            "success": False,
                                            "error": "Mock error for testing",
                                            "mode": "mock"
                                        }
                                    ]
                                    
                                    # Import et appel du endpoint
                                    from backend.server import generate_sheet
                                    from backend.server import GenerateProductSheetRequest
                                    
                                    request = GenerateProductSheetRequest(**mock_request_data)
                                    
                                    # Appel du endpoint
                                    response = await generate_sheet(request, mock_user)
                                    
                                    # Vérifications
                                    assert response is not None
                                    assert hasattr(response, 'publication_results')
                                    assert hasattr(response, 'auto_publish_enabled')
                                    assert response.auto_publish_enabled is True
                                    
                                    # Vérifier que la publication a été appelée
                                    mock_publish.assert_called_once()
                                    call_args = mock_publish.call_args
                                    
                                    # Vérifier les arguments d'appel
                                    assert call_args[0][0]["product_name"] == "Test Product Publication"
                                    assert call_args[1]["user_id"] == "test_user_123"
                                    assert call_args[1]["platforms"] is None  # Default platforms
                                    
                                    # Vérifier la réponse contient les résultats
                                    assert len(response.publication_results) == 3
                                    assert response.publication_results[0]["platform"] == "shopify"
                                    assert response.publication_results[0]["success"] is True
    
    async def test_generate_does_not_publish_when_disabled(self, mock_request_data, mock_user, mock_db, mock_services):
        """Test: /generate-sheet ne publie pas si PUBLISH_AUTO=false"""
        
        with patch.dict(os.environ, {'MOCK_MODE': 'true', 'PUBLISH_AUTO': 'false'}):
            with patch('backend.server.db', mock_db):
                with patch('backend.server.ImageGenerationService', return_value=mock_services["image"]):
                    with patch('backend.server.SEOScrapingService', return_value=mock_services["seo"]):
                        with patch('backend.server.GPTContentService', return_value=mock_services["gpt"]):
                            with patch('backend.server.qa_service') as mock_qa:
                                mock_qa.should_simulate_failure.return_value = {"simulate": False}
                                mock_qa.log_test_result = MagicMock()
                                mock_qa.test_mode = False
                                
                                with patch('backend.services.publication_factory.publish_product_to_platforms') as mock_publish:
                                    
                                    from backend.server import generate_sheet
                                    from backend.server import GenerateProductSheetRequest
                                    
                                    request = GenerateProductSheetRequest(**mock_request_data)
                                    
                                    response = await generate_sheet(request, mock_user)
                                    
                                    # Vérifications
                                    assert response.auto_publish_enabled is False
                                    assert response.publication_results == []
                                    
                                    # Publication ne doit pas être appelée
                                    mock_publish.assert_not_called()

    async def test_publish_log_contains_images_and_seo_fields(self, mock_request_data, mock_user, mock_db, mock_services):
        """Test: Publication log contient les images et champs SEO"""
        
        with patch.dict(os.environ, {'MOCK_MODE': 'true', 'PUBLISH_AUTO': 'true'}):
            with patch('backend.server.db', mock_db):
                with patch('backend.server.ImageGenerationService', return_value=mock_services["image"]):
                    with patch('backend.server.SEOScrapingService', return_value=mock_services["seo"]):
                        with patch('backend.server.GPTContentService', return_value=mock_services["gpt"]):
                            with patch('backend.server.qa_service') as mock_qa:
                                mock_qa.should_simulate_failure.return_value = {"simulate": False}
                                mock_qa.log_test_result = MagicMock()
                                mock_qa.test_mode = False
                                
                                # Utiliser le vrai système de publication pour tester les logs
                                from backend.server import generate_sheet
                                from backend.server import GenerateProductSheetRequest
                                
                                request = GenerateProductSheetRequest(**mock_request_data)
                                
                                response = await generate_sheet(request, mock_user)
                                
                                # Vérifier que les publications sont dans le storage
                                publications = mock_storage.get_publications()
                                
                                # Au moins une publication doit exister
                                assert len(publications) > 0
                                
                                # Vérifier le contenu des logs
                                for pub in publications:
                                    assert pub["product_name"] == "Test Product Publication"
                                    assert pub["mode"] == "mock"
                                    assert "created_at" in pub
                                    assert "platform" in pub
                                    assert pub["images_count"] == 2  # 2 images générées
                                    assert pub["tags"] == ["test", "product", "electronics", "premium", "amazing"]

class TestPublicationDataMapping:
    """Test du mapping des données vers le format de publication"""
    
    def test_product_data_mapping_complete(self):
        """Test: Mapping complet des données produit"""
        from backend.services.publication_factory import publish_product_to_platforms
        
        # Données de test complètes
        product_data = {
            "id": "test_123",
            "product_name": "Original Name", 
            "generated_title": "Generated Amazing Product Title",
            "marketing_description": "This is a comprehensive marketing description that should be long enough to test the publication pipeline properly.",
            "price_suggestions": "Prix recommandé: 49.99€ - 59.99€",
            "seo_tags": ["amazing", "product", "test", "electronics"],
            "key_features": ["Premium quality", "Advanced technology", "User-friendly design"],
            "category": "Test Electronics",
            "generated_images": [
                "data:image/jpeg;base64,/9j/4AAQSkZJRgABATest1...",
                "data:image/png;base64,iVBORw0KGgoAAAANSUhEUTest2..."
            ]
        }
        
        # Mock de publication pour tester le mapping
        with patch('backend.services.publication_factory.publication_factory') as mock_factory:
            with patch('backend.services.publication_factory.extract_price_from_suggestions') as mock_extract_price:
                mock_extract_price.return_value = 49.99
                
                # Mock publisher
                mock_publisher = MagicMock()
                mock_publisher.publish_product = AsyncMock(return_value=MagicMock(
                    success=True,
                    product_id="mapped_product_123",
                    mode="mock"
                ))
                
                mock_factory.get_all_available_publishers.return_value = {
                    "shopify": mock_publisher
                }
                
                # Cette fonction sera testée
                # result = await publish_product_to_platforms(product_data, ["shopify"], "test_user")
                
                # Pour l'instant, nous testons juste le mapping des données
                # Vérifier que les ProductDTO sont créés correctement
                from backend.services.publication_interfaces import ProductDTO, ImageDTO
                
                # Création manuelle du DTO pour test
                images = []
                for i, img_data in enumerate(product_data["generated_images"]):
                    images.append(ImageDTO(
                        base64_data=img_data,
                        alt_text=product_data["generated_title"],
                        position=i
                    ))
                
                product_dto = ProductDTO(
                    user_id="test_user",
                    name=product_data["generated_title"],
                    description=product_data["marketing_description"],
                    price=49.99,
                    tags=product_data["seo_tags"],
                    images=images,
                    category=product_data["category"]
                )
                
                # Vérifications mapping
                assert product_dto.name == "Generated Amazing Product Title"
                assert product_dto.description == product_data["marketing_description"]
                assert product_dto.price == 49.99
                assert len(product_dto.images) == 2
                assert product_dto.tags == ["amazing", "product", "test", "electronics"]
                assert product_dto.category == "Test Electronics"
                
                # Test formats spécifiques plateformes
                shopify_format = product_dto.to_shopify_format()
                assert shopify_format["product"]["title"] == "Generated Amazing Product Title"
                assert "amazing,product,test,electronics" in shopify_format["product"]["tags"]
                
                woo_format = product_dto.to_woocommerce_format()
                assert woo_format["name"] == "Generated Amazing Product Title"
                assert woo_format["regular_price"] == "49.99"

@pytest.mark.asyncio
class TestPublicationErrorHandling:
    """Test de la gestion d'erreurs de publication"""
    
    @pytest.fixture(autouse=True)
    def clean_storage(self):
        mock_storage.clear_all()
        yield
        mock_storage.clear_all()
    
    async def test_publication_error_does_not_fail_generation(self):
        """Test: Erreur de publication n'interrompt pas la génération"""
        
        # Mock qui échoue sur publish_product_to_platforms
        with patch('backend.services.publication_factory.publish_product_to_platforms') as mock_publish:
            mock_publish.side_effect = Exception("Publication service unavailable")
            
            # Mock tous les autres services
            with patch('backend.server.db') as mock_db:
                mock_db.product_sheets.count_documents = AsyncMock(return_value=0)
                mock_db.product_sheets.insert_one = AsyncMock()
                mock_db.product_sheets.insert_one.return_value.inserted_id = "test_sheet_id"
                
                with patch('backend.server.ImageGenerationService') as MockImageService:
                    with patch('backend.server.SEOScrapingService') as MockSEOService:
                        with patch('backend.server.GPTContentService') as MockGPTService:
                            with patch('backend.server.qa_service') as mock_qa:
                                
                                # Configuration des mocks
                                MockImageService.return_value.generate_images = AsyncMock(return_value=[])
                                MockSEOService.return_value.scrape_competitor_prices = AsyncMock(return_value={})
                                MockSEOService.return_value.scrape_seo_data = AsyncMock(return_value={})
                                MockSEOService.return_value.fetch_trending_keywords = AsyncMock(return_value={})
                                MockGPTService.return_value.generate_product_content = AsyncMock(return_value={
                                    "generated_title": "Test Product",
                                    "marketing_description": "Test description",
                                    "key_features": ["Feature 1"],
                                    "seo_tags": ["test"],
                                    "price_suggestions": "29.99€",
                                    "target_audience": "Test audience",
                                    "call_to_action": "Buy now!"
                                })
                                
                                mock_qa.should_simulate_failure.return_value = {"simulate": False}
                                mock_qa.log_test_result = MagicMock()
                                mock_qa.test_mode = False
                                
                                # Test
                                from backend.server import generate_sheet, GenerateProductSheetRequest
                                
                                mock_user = MagicMock()
                                mock_user.id = "test_user"
                                mock_user.subscription_plan = "pro"
                                
                                request_data = {
                                    "product_name": "Test Product",
                                    "product_description": "Test description", 
                                    "category": "Electronics",
                                    "generate_image": False,
                                    "number_of_images": 0
                                }
                                
                                request = GenerateProductSheetRequest(**request_data)
                                
                                with patch.dict(os.environ, {'PUBLISH_AUTO': 'true'}):
                                    # Ne devrait pas lever d'exception malgré l'erreur de publication
                                    response = await generate_sheet(request, mock_user)
                                    
                                    # La génération doit réussir
                                    assert response.generated_title == "Test Product"
                                    assert response.publication_results == []  # Vide à cause de l'erreur
                                    
                                    # Vérifier que l'erreur est loggée mais n'interrompt pas le flow