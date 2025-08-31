"""
Tests pour Publishers Mock - Toutes les plateformes ECOMSIMPLY
"""

import pytest
import asyncio
from decimal import Decimal

# Import modules à tester
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from scraping.publication.publishers.base import GenericMockPublisher, IdempotencyStore, PublishResult
from scraping.publication.publishers import get_all_publishers, get_publisher, get_supported_stores
from scraping.publication.constants import STORES
from scraping.semantic.product_dto import ProductDTO, ImageDTO, PriceDTO, Currency


class TestIdempotencyStore:
    """Tests pour IdempotencyStore"""
    
    @pytest.fixture
    def idem_store(self):
        return IdempotencyStore()
    
    def test_store_empty_initially(self, idem_store):
        """Test store vide au départ"""
        assert not idem_store.seen("test_key")
        assert idem_store.get("test_key") is None
        assert idem_store.size() == 0
    
    def test_save_and_retrieve(self, idem_store):
        """Test sauvegarde et récupération"""
        idem_store.save("key1", "value1")
        
        assert idem_store.seen("key1")
        assert idem_store.get("key1") == "value1"
        assert idem_store.size() == 1
        
        # Key inexistante
        assert not idem_store.seen("key2")
        assert idem_store.get("key2") is None
    
    def test_multiple_keys(self, idem_store):
        """Test plusieurs clés"""
        idem_store.save("key1", "value1")
        idem_store.save("key2", "value2")
        
        assert idem_store.size() == 2
        assert idem_store.get("key1") == "value1"
        assert idem_store.get("key2") == "value2"


class TestGenericMockPublisher:
    """Tests pour GenericMockPublisher avec tous les stores"""
    
    @pytest.fixture
    def idem_store(self):
        return IdempotencyStore()
    
    @pytest.fixture
    def sample_product(self):
        """ProductDTO exemple pour tests"""
        return ProductDTO(
            title="Test Product iPhone 15",
            description_html="<p>Smartphone test pour publisher mock</p>",
            price=PriceDTO(amount=Decimal('999.99'), currency=Currency.EUR),
            images=[
                ImageDTO(url="https://example.com/image1.webp", alt="Image test 1"),
                ImageDTO(url="https://example.com/image2.webp", alt="Image test 2")
            ],
            source_url="https://test.example.com/product",
            payload_signature="test_signature_123",
            extraction_timestamp=1703001234.567
        )
    
    @pytest.mark.parametrize("store_name", STORES)
    def test_publisher_creation_all_stores(self, store_name, idem_store):
        """Test création publisher pour chaque store"""
        publisher = GenericMockPublisher(store_name, idem_store)
        
        assert publisher.name == store_name
        assert publisher.idem_store is idem_store
        assert publisher.store_config is not None
        
        # Vérifier config spécifique store
        config = publisher.store_config
        assert 'api_version' in config
        assert 'max_images' in config
        assert isinstance(config['max_images'], int)
        assert config['max_images'] > 0
    
    @pytest.mark.parametrize("store_name", STORES)
    @pytest.mark.asyncio
    async def test_publish_success_all_stores(self, store_name, idem_store, sample_product):
        """Test publication réussie pour chaque store"""
        publisher = GenericMockPublisher(store_name, idem_store)
        idempotency_key = f"test_key_{store_name}_123"
        
        result = await publisher.publish(sample_product, idempotency_key=idempotency_key)
        
        assert isinstance(result, PublishResult)
        assert result.success is True
        assert result.status_code == 201
        assert result.external_id is not None
        assert result.store == store_name
        assert "created (mock" in result.message
        assert result.duration_ms > 0
        
        # Vérifier métadonnées
        assert result.metadata is not None
        assert 'store_config' in result.metadata
        assert result.metadata['product_title'] == sample_product.title
    
    @pytest.mark.parametrize("store_name", STORES)
    @pytest.mark.asyncio
    async def test_idempotency_all_stores(self, store_name, idem_store, sample_product):
        """Test idempotence pour chaque store"""
        publisher = GenericMockPublisher(store_name, idem_store)
        idempotency_key = f"idem_test_{store_name}_456"
        
        # Premier appel → création
        result1 = await publisher.publish(sample_product, idempotency_key=idempotency_key)
        assert result1.success is True
        assert result1.status_code == 201
        external_id_1 = result1.external_id
        
        # Deuxième appel → idempotent hit
        result2 = await publisher.publish(sample_product, idempotency_key=idempotency_key)
        assert result2.success is True
        assert result2.status_code == 200  # Hit idempotent
        assert result2.external_id == external_id_1  # Même external_id
        assert "idempotent-hit" in result2.message
        assert result2.metadata['idempotent'] is True
    
    @pytest.mark.parametrize("store_name", STORES)
    @pytest.mark.asyncio
    async def test_different_keys_different_ids(self, store_name, idem_store, sample_product):
        """Test clés différentes → external_ids différents"""
        publisher = GenericMockPublisher(store_name, idem_store)
        
        result1 = await publisher.publish(sample_product, idempotency_key="key1")
        result2 = await publisher.publish(sample_product, idempotency_key="key2")
        
        assert result1.external_id != result2.external_id
        assert result1.success is True
        assert result2.success is True
    
    @pytest.mark.asyncio
    async def test_store_specific_validation(self, idem_store, sample_product):
        """Test validations spécifiques par store"""
        
        # Test avec trop d'images pour stores restrictifs
        many_images = [
            ImageDTO(url=f"https://example.com/image{i}.webp", alt=f"Image {i}")
            for i in range(15)  # 15 images
        ]
        product_many_images = ProductDTO(
            title="Product with many images",
            description_html="<p>Test</p>",
            images=many_images,
            source_url="https://test.com/product",
            payload_signature="many_images_test",
            extraction_timestamp=1703001234.567
        )
        
        # Test stores avec limite d'images basse
        restrictive_stores = ["wix", "squarespace"]  # max 4-5 images
        
        for store_name in restrictive_stores:
            publisher = GenericMockPublisher(store_name, idem_store)
            result = await publisher.publish(product_many_images, idempotency_key=f"test_{store_name}")
            
            # Devrait échouer car trop d'images
            assert result.success is False
            assert "Trop d'images" in result.message
    
    @pytest.mark.parametrize("store_name", STORES)
    def test_external_id_stability(self, store_name, idem_store):
        """Test stabilité des external_ids générés"""
        publisher = GenericMockPublisher(store_name, idem_store)
        
        # Même clé → même external_id
        key = "stable_test_key"
        id1 = publisher._generate_external_id(key)
        id2 = publisher._generate_external_id(key)
        
        assert id1 == id2
        
        # Différentes clés → différents external_ids
        id3 = publisher._generate_external_id("different_key")
        assert id1 != id3
    
    @pytest.mark.parametrize("store_name", STORES)
    @pytest.mark.asyncio
    async def test_health_check_all_stores(self, store_name, idem_store):
        """Test health check pour chaque store"""
        publisher = GenericMockPublisher(store_name, idem_store)
        
        health = await publisher.health_check()
        
        assert health['store'] == store_name
        assert health['status'] == 'healthy'
        assert 'api_version' in health
        assert 'features' in health
        assert 'inventory' in health['features']
        assert 'variants' in health['features']
        assert 'max_images' in health['features']
        assert health['response_time_ms'] > 0
    
    @pytest.mark.parametrize("store_name", STORES)
    def test_stats_tracking(self, store_name, idem_store):
        """Test tracking statistiques"""
        publisher = GenericMockPublisher(store_name, idem_store)
        
        # Stats initiaux
        stats = publisher.get_stats()
        assert stats['total_publishes'] == 0
        assert stats['successful_publishes'] == 0
        assert stats['store_name'] == store_name


class TestPublisherFactory:
    """Tests pour factory publishers"""
    
    @pytest.fixture
    def idem_store(self):
        return IdempotencyStore()
    
    def test_get_supported_stores(self):
        """Test liste stores supportés"""
        supported = get_supported_stores()
        
        assert isinstance(supported, list)
        assert len(supported) == len(STORES)
        assert all(store in STORES for store in supported)
    
    def test_get_all_publishers(self, idem_store):
        """Test création de tous les publishers"""
        publishers = get_all_publishers(idem_store)
        
        assert isinstance(publishers, dict)
        assert len(publishers) == len(STORES)
        
        for store in STORES:
            assert store in publishers
            publisher = publishers[store]
            assert isinstance(publisher, GenericMockPublisher)
            assert publisher.name == store
            assert publisher.idem_store is idem_store
    
    def test_get_publisher_valid_store(self, idem_store):
        """Test création publisher store valide"""
        for store in STORES:
            publisher = get_publisher(store, idem_store)
            
            assert isinstance(publisher, GenericMockPublisher)
            assert publisher.name == store
    
    def test_get_publisher_invalid_store(self, idem_store):
        """Test échec store invalide"""
        with pytest.raises(ValueError, match="Store 'invalid_store' non supporté"):
            get_publisher('invalid_store', idem_store)
    
    def test_publishers_independence(self, idem_store):
        """Test indépendance des publishers"""
        publishers = get_all_publishers(idem_store)
        
        # Modifier stats d'un publisher ne doit pas affecter les autres
        publishers['shopify'].stats['test_value'] = 999
        
        # Créer nouveaux publishers
        new_publishers = get_all_publishers(IdempotencyStore())
        assert 'test_value' not in new_publishers['shopify'].stats
        
        # Mais même idem_store doit être partagé
        same_idem_publishers = get_all_publishers(idem_store)
        assert same_idem_publishers['shopify'].idem_store is idem_store


class TestPublishersIntegration:
    """Tests d'intégration entre publishers et stores"""
    
    @pytest.fixture
    def idem_store(self):
        return IdempotencyStore()
    
    @pytest.fixture
    def sample_product(self):
        return ProductDTO(
            title="Integration Test Product",
            description_html="<p>Test intégration publishers</p>",
            price=PriceDTO(amount=Decimal('499.99'), currency=Currency.EUR),
            images=[ImageDTO(url="https://cdn.test.com/product.webp", alt="Product test")],
            source_url="https://test.com/product",
            payload_signature="integration_test_sig",
            extraction_timestamp=1703001234.567
        )
    
    @pytest.mark.asyncio
    async def test_cross_store_idempotency(self, idem_store, sample_product):
        """Test idempotence croisée entre stores"""
        publishers = get_all_publishers(idem_store)
        
        # Publier même produit sur différents stores avec clés différentes
        results = {}
        for store in STORES[:3]:  # Test sur 3 stores
            key = f"cross_test_{store}"
            result = await publishers[store].publish(sample_product, idempotency_key=key)
            results[store] = result
            
            assert result.success is True
        
        # Vérifier external_ids différents (clés différentes)
        external_ids = [r.external_id for r in results.values()]
        assert len(set(external_ids)) == len(external_ids)  # Tous différents
        
        # Même store, même clé → même external_id
        key = "same_key_test"
        result1 = await publishers['shopify'].publish(sample_product, idempotency_key=key)
        result2 = await publishers['shopify'].publish(sample_product, idempotency_key=key)
        
        assert result1.external_id == result2.external_id
    
    @pytest.mark.asyncio
    async def test_concurrent_publications(self, idem_store, sample_product):
        """Test publications concurrentes"""
        publishers = get_all_publishers(idem_store)
        
        # Publications concurrentes sur différents stores
        tasks = []
        for i, store in enumerate(STORES):
            key = f"concurrent_test_{i}"
            task = publishers[store].publish(sample_product, idempotency_key=key)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Tous doivent réussir
        for result in results:
            assert result.success is True
            assert result.external_id is not None
        
        # External IDs doivent être différents
        external_ids = [r.external_id for r in results]
        assert len(set(external_ids)) == len(external_ids)
    
    @pytest.mark.asyncio
    async def test_store_config_differences(self, idem_store):
        """Test différences configuration entre stores"""
        publishers = get_all_publishers(idem_store)
        
        configs = {}
        for store, publisher in publishers.items():
            configs[store] = publisher.store_config
        
        # Vérifier différences
        assert configs['shopify']['max_images'] != configs['wix']['max_images']
        assert configs['magento']['typical_latency_ms'][1] > configs['shopify']['typical_latency_ms'][1]
        
        # Vérifier cohérence
        for store, config in configs.items():
            assert config['max_images'] > 0
            assert len(config['typical_latency_ms']) == 2
            assert config['typical_latency_ms'][0] <= config['typical_latency_ms'][1]