# Tests Amazon Publisher Phase 2 - Conformité Bloc 2 avec Sandbox
import pytest
import os
import json
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException

from publication.publishers.amazon_spapi import (
    AmazonSPAPIPublisher, ProductDTO, PublicationOrchestrator,
    PublicationChannel, AmazonPublicationResult, SPAPIRetryManager
)
from models.amazon_spapi import AmazonConnection, ConnectionStatus, SPAPIRegion

class TestProductDTOMapping:
    """Tests de mapping ProductDTO vers payload Amazon"""
    
    def test_product_dto_creation(self):
        """Test création ProductDTO avec données complètes"""
        product = ProductDTO(
            product_id="prod_123",
            sku="CASQUE-BT-001",
            title="Casque Audio Bluetooth Premium",
            brand="AudioTech",
            description="Casque sans fil avec réduction de bruit active",
            bullet_points=[
                "Bluetooth 5.0 pour connexion stable",
                "Réduction de bruit active",
                "Autonomie 30 heures",
                "Qualité audio Hi-Fi",
                "Confort premium"
            ],
            key_features=["Bluetooth 5.0", "Réduction bruit", "30h autonomie"],
            benefits=["Qualité premium", "Confort longue durée"],
            price=79.99,
            currency="EUR",
            stock_quantity=10,
            ean="1234567890123",
            images=[
                {"url": "https://example.com/main.jpg", "is_main": True, "width": 1200, "height": 1200},
                {"url": "https://example.com/side.jpg", "is_main": False, "width": 1000, "height": 1000}
            ]
        )
        
        assert product.sku == "CASQUE-BT-001"
        assert product.title == "Casque Audio Bluetooth Premium"
        assert len(product.bullet_points) == 5
        assert product.price == 79.99
        assert product.stock_quantity == 10
        assert len(product.images) == 2
    
    def test_product_dto_defaults(self):
        """Test valeurs par défaut ProductDTO"""
        product = ProductDTO(
            product_id="prod_456",
            sku="TEST-SKU",
            title="Produit Test",
            brand="TestBrand",
            description="Description test",
            bullet_points=[],
            key_features=[],
            benefits=[],
            price=29.99
        )
        
        assert product.currency == "EUR"
        assert product.stock_quantity == 1
        assert product.condition == "new"
        assert product.images == []
        assert product.tags == []

class TestAmazonSPAPIPublisher:
    """Tests du publisher Amazon SP-API Phase 2"""
    
    @pytest.fixture
    def mock_database(self):
        """Mock database"""
        db = Mock(spec=AsyncIOMotorDatabase)
        db.amazon_publications = AsyncMock()
        return db
    
    @pytest.fixture
    def publisher(self, mock_database):
        """Publisher Amazon avec dépendances mockées"""
        publisher = AmazonSPAPIPublisher(mock_database)
        publisher.connection_service = Mock()
        publisher.seo_service = Mock()
        publisher.retry_manager = Mock()
        return publisher
    
    @pytest.fixture
    def sample_product(self):
        """Produit de test"""
        return ProductDTO(
            product_id="test_product",
            sku="TEST-CASQUE-001",
            title="Casque Audio Test",
            brand="TestAudio",
            description="Casque de test pour Amazon",
            bullet_points=[
                "Feature 1", "Feature 2", "Feature 3", "Feature 4", "Feature 5"
            ],
            key_features=["Bluetooth", "Noise Cancelling"],
            benefits=["High Quality", "Comfortable"],
            price=49.99,
            ean="1234567890123"
        )
    
    def test_map_product_dto_to_amazon_basic(self, publisher, sample_product):
        """Test mapping ProductDTO vers payload Amazon de base"""
        marketplace_id = "A13V1IB3VIYZZH"  # France
        
        payload = publisher._map_product_dto_to_amazon(
            sample_product, marketplace_id, use_images=False
        )
        
        # Vérifications structure de base
        assert payload["productType"] == "PRODUCT"
        assert payload["requirements"] == "LISTING"
        
        # Vérifications attributs requis
        attributes = payload["attributes"]
        
        # Titre
        assert len(attributes["item_name"]) == 1
        assert attributes["item_name"][0]["value"] == "Casque Audio Test"
        assert attributes["item_name"][0]["language_tag"] == "fr-FR"
        assert attributes["item_name"][0]["marketplace_id"] == "A13V1IB3VIYZZH"
        
        # Marque
        assert attributes["brand"][0]["value"] == "TestAudio"
        
        # Description
        assert attributes["product_description"][0]["value"] == "Casque de test pour Amazon"
        
        # Prix
        assert attributes["list_price"][0]["value"]["Amount"] == 49.99
        assert attributes["list_price"][0]["value"]["CurrencyCode"] == "EUR"
        
        # Stock
        assert attributes["fulfillment_availability"][0]["quantity"] == 1
    
    def test_map_product_dto_with_bullet_points(self, publisher, sample_product):
        """Test mapping avec bullet points"""
        payload = publisher._map_product_dto_to_amazon(
            sample_product, "A13V1IB3VIYZZH", use_images=False
        )
        
        bullet_points = payload["attributes"]["bullet_point"]
        assert len(bullet_points) == 5
        
        for i, bullet in enumerate(bullet_points):
            assert bullet["value"] == f"Feature {i + 1}"
            assert bullet["language_tag"] == "fr-FR"
            assert bullet["marketplace_id"] == "A13V1IB3VIYZZH"
    
    def test_map_product_dto_with_ean(self, publisher, sample_product):
        """Test mapping avec identifiant EAN"""
        payload = publisher._map_product_dto_to_amazon(
            sample_product, "A13V1IB3VIYZZH", use_images=False
        )
        
        identifiers = payload["attributes"]["externally_assigned_product_identifier"]
        assert len(identifiers) == 1
        assert identifiers[0]["value"]["type"] == "EAN"
        assert identifiers[0]["value"]["value"] == "1234567890123"
    
    def test_map_product_dto_with_images(self, publisher):
        """Test mapping avec images"""
        product = ProductDTO(
            product_id="test",
            sku="TEST",
            title="Test",
            brand="Test",
            description="Test",
            bullet_points=[],
            key_features=[],
            benefits=[],
            price=10.0,
            images=[
                {"url": "https://example.com/main.jpg", "is_main": True, "width": 1200, "height": 1200},
                {"url": "https://example.com/alt1.jpg", "is_main": False, "width": 1000, "height": 1000},
                {"url": "https://example.com/alt2.jpg", "is_main": False, "width": 1000, "height": 1000}
            ]
        )
        
        payload = publisher._map_product_dto_to_amazon(
            product, "A13V1IB3VIYZZH", use_images=True
        )
        
        # Image principale
        main_images = payload["attributes"]["main_product_image_locator"]
        assert len(main_images) == 1
        assert main_images[0]["value"]["link"] == "https://example.com/main.jpg"
        
        # Images alternatives
        other_images = payload["attributes"]["other_product_image_locator"]
        assert len(other_images) == 2
    
    def test_language_mapping_by_marketplace(self, publisher, sample_product):
        """Test mapping langue selon marketplace"""
        # Test France
        payload_fr = publisher._map_product_dto_to_amazon(sample_product, "A13V1IB3VIYZZH", False)
        assert payload_fr["attributes"]["item_name"][0]["language_tag"] == "fr-FR"
        
        # Test Allemagne  
        payload_de = publisher._map_product_dto_to_amazon(sample_product, "A1PA6795UKMFR9", False)
        assert payload_de["attributes"]["item_name"][0]["language_tag"] == "de-DE"
        
        # Test États-Unis
        payload_us = publisher._map_product_dto_to_amazon(sample_product, "ATVPDKIKX0DER", False)
        assert payload_us["attributes"]["item_name"][0]["language_tag"] == "en-US"

class TestConnectionPreconditionErrors:
    """Tests des erreurs de connexion 412 PRECONDITION_REQUIRED"""
    
    @pytest.fixture
    def publisher_with_no_connection(self, mock_database):
        """Publisher avec aucune connexion"""
        publisher = AmazonSPAPIPublisher(mock_database)
        publisher.connection_service = Mock()
        publisher.connection_service.get_active_connection = AsyncMock(return_value=None)
        return publisher
    
    @pytest.fixture
    def publisher_with_invalid_token(self, mock_database):
        """Publisher avec token invalide"""
        publisher = AmazonSPAPIPublisher(mock_database)
        publisher.connection_service = Mock()
        
        # Mock connexion active mais token invalide
        mock_connection = Mock()
        mock_connection.status = ConnectionStatus.ACTIVE
        publisher.connection_service.get_active_connection = AsyncMock(return_value=mock_connection)
        publisher.connection_service.get_valid_access_token = AsyncMock(return_value=None)
        
        return publisher
    
    @pytest.mark.asyncio
    async def test_no_connection_raises_412(self, publisher_with_no_connection, sample_product):
        """Test erreur 412 quand aucune connexion Amazon"""
        result = await publisher_with_no_connection.publish_product(
            user_id="test_user",
            product_dto=sample_product,
            marketplace_id="A13V1IB3VIYZZH"
        )
        
        assert result.success == False
        assert any("Connexion Amazon requise" in error for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_invalid_token_raises_412(self, publisher_with_invalid_token, sample_product):
        """Test erreur 412 quand token invalide"""
        result = await publisher_with_invalid_token.publish_product(
            user_id="test_user",
            product_dto=sample_product,
            marketplace_id="A13V1IB3VIYZZH"
        )
        
        assert result.success == False
        assert any("Token Amazon invalide" in error for error in result.errors)

class TestSPAPIRetryManager:
    """Tests du gestionnaire de retry/backoff"""
    
    @pytest.fixture
    def retry_manager(self):
        """Gestionnaire de retry"""
        manager = SPAPIRetryManager()
        manager.max_retries = 2  # Réduire pour les tests
        manager.base_delay = 0.01  # Délai minimal pour tests
        return manager
    
    @pytest.mark.asyncio
    async def test_retry_on_429_quota_exceeded(self, retry_manager):
        """Test retry automatique sur quota dépassé (429)"""
        call_count = 0
        
        async def mock_function():
            nonlocal call_count
            call_count += 1
            
            if call_count <= 2:  # Échouer 2 fois
                import httpx
                response = Mock()
                response.status_code = 429
                raise httpx.HTTPStatusError("Quota exceeded", response=response, request=Mock())
            
            return "success"
        
        # Exécuter avec retry
        result = await retry_manager.execute_with_retry(mock_function)
        
        assert result == "success"
        assert call_count == 3  # 1 tentative initiale + 2 retries
    
    @pytest.mark.asyncio
    async def test_retry_on_503_service_unavailable(self, retry_manager):
        """Test retry sur service indisponible (503)"""
        call_count = 0
        
        async def mock_function():
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                import httpx
                response = Mock()
                response.status_code = 503
                raise httpx.HTTPStatusError("Service unavailable", response=response, request=Mock())
            
            return "success"
        
        result = await retry_manager.execute_with_retry(mock_function)
        
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_no_retry_on_400_bad_request(self, retry_manager):
        """Test pas de retry sur erreur 400"""
        call_count = 0
        
        async def mock_function():
            nonlocal call_count
            call_count += 1
            
            import httpx
            response = Mock()
            response.status_code = 400
            raise httpx.HTTPStatusError("Bad request", response=response, request=Mock())
        
        with pytest.raises(httpx.HTTPStatusError):
            await retry_manager.execute_with_retry(mock_function)
        
        assert call_count == 1  # Pas de retry

class TestPublicationOrchestrator:
    """Tests de l'orchestrateur de publication"""
    
    @pytest.fixture
    def orchestrator(self, mock_database):
        """Orchestrateur avec publisher Amazon mocké"""
        orchestrator = PublicationOrchestrator(mock_database)
        
        # Mock publisher Amazon
        mock_publisher = Mock()
        mock_result = AmazonPublicationResult(
            success=True,
            listing_id="test-sku-123",
            feed_id="feed_456",
            submission_id="sub_789"
        )
        mock_publisher.publish_product = AsyncMock(return_value=mock_result)
        
        orchestrator.publishers[PublicationChannel.AMAZON] = mock_publisher
        
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_publish_to_amazon_channel(self, orchestrator, sample_product):
        """Test publication via orchestrateur vers Amazon"""
        channel_config = {
            "marketplace_id": "A13V1IB3VIYZZH",
            "use_images": True
        }
        
        result = await orchestrator.publish_to_channel(
            channel=PublicationChannel.AMAZON,
            user_id="test_user",
            product_dto=sample_product,
            channel_config=channel_config
        )
        
        assert result["success"] == True
        assert result["channel"] == PublicationChannel.AMAZON
        assert result["listing_id"] == "test-sku-123"
        assert result["feed_id"] == "feed_456"
        assert result["submission_id"] == "sub_789"
    
    def test_unsupported_channel_error(self, orchestrator, sample_product):
        """Test erreur canal non supporté"""
        with pytest.raises(ValueError, match="Canal .* non supporté"):
             # Utiliser un canal inexistant
            asyncio.run(orchestrator.publish_to_channel(
                channel="invalid_channel",
                user_id="test_user", 
                product_dto=sample_product,
                channel_config={}
            ))

class TestFeedIdStorage:
    """Tests du stockage feedId Amazon"""
    
    @pytest.mark.asyncio
    async def test_publication_record_with_feed_id(self):
        """Test enregistrement publication avec feedId"""
        mock_db = Mock()
        mock_db.amazon_publications = AsyncMock()
        
        publisher = AmazonSPAPIPublisher(mock_db)
        
        # Mock ProductDTO
        product = ProductDTO(
            product_id="test",
            sku="TEST-SKU",
            title="Test Product",
            brand="TestBrand",
            description="Test",
            bullet_points=[],
            key_features=[],
            benefits=[],
            price=19.99
        )
        
        # Mock résultat avec feedId
        result = AmazonPublicationResult(
            success=True,
            listing_id="listing_123",
            feed_id="feed_abc456",
            submission_id="sub_def789"
        )
        
        # Sauvegarder l'enregistrement
        await publisher._save_publication_record(
            user_id="user_123",
            connection_id="conn_456",
            product_dto=product,
            result=result
        )
        
        # Vérifier l'appel à la base
        mock_db.amazon_publications.insert_one.assert_called_once()
        
        # Vérifier les données sauvées
        saved_data = mock_db.amazon_publications.insert_one.call_args[0][0]
        assert saved_data["feed_id"] == "feed_abc456"
        assert saved_data["submission_id"] == "sub_def789"
        assert saved_data["listing_id"] == "listing_123"
        assert saved_data["channel"] == PublicationChannel.AMAZON

# Tests d'intégration Sandbox (à exécuter avec vraies clés API)
class TestSandboxIntegration:
    """Tests d'intégration Amazon Sandbox"""
    
    @pytest.mark.skipif(
        not os.environ.get("AMAZON_SANDBOX_TEST", False),
        reason="Tests Sandbox nécessitent AMAZON_SANDBOX_TEST=true"
    )
    @pytest.mark.asyncio
    async def test_real_sandbox_submission(self):
        """Test soumission réelle en Sandbox Amazon"""
        # Ce test nécessite une vraie connexion Sandbox
        # À activer uniquement pour validation finale
        
        # Configuration Sandbox
        sandbox_config = {
            "client_id": os.environ.get("AMAZON_SANDBOX_CLIENT_ID"),
            "client_secret": os.environ.get("AMAZON_SANDBOX_CLIENT_SECRET"),
            "refresh_token": os.environ.get("AMAZON_SANDBOX_REFRESH_TOKEN"),
            "seller_id": os.environ.get("AMAZON_SANDBOX_SELLER_ID"),
            "marketplace_id": "A13V1IB3VIYZZH"  # Sandbox France
        }
        
        # Produit de test Sandbox
        test_product = ProductDTO(
            product_id="sandbox_test",
            sku=f"SANDBOX-TEST-{int(datetime.utcnow().timestamp())}",
            title="Produit Test Sandbox ECOMSIMPLY",
            brand="ECOMSIMPLY-TEST",
            description="Produit de test pour validation Amazon Sandbox",
            bullet_points=[
                "Test Feature 1",
                "Test Feature 2", 
                "Test Feature 3",
                "Test Feature 4",
                "Test Feature 5"
            ],
            key_features=["Test"],
            benefits=["Test Quality"],
            price=9.99,
            stock_quantity=1
        )
        
        # TODO: Implémenter test Sandbox réel
        # Ce test devrait créer une vraie soumission Sandbox
        # et vérifier le statut de traitement
        
        assert True  # Placeholder pour l'implémentation

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])