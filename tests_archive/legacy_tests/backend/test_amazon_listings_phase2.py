# Tests automatiques pour Amazon Listings Phase 2
import pytest
import asyncio
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Tests pour le générateur IA
class TestAmazonListingGenerator:
    """Tests pour le générateur de fiches Amazon par IA"""
    
    @pytest.fixture
    def generator(self):
        """Fixture pour le générateur"""
        from amazon.listings.generator import AmazonListingGenerator
        return AmazonListingGenerator()
    
    @pytest.fixture
    def sample_product_data(self):
        """Données produit de test"""
        return {
            "brand": "Apple",
            "product_name": "iPhone 15 Pro Max",
            "features": ["A17 Pro chip", "Titanium design", "Action Button", "Pro camera system"],
            "category": "électronique",
            "target_keywords": ["smartphone", "premium", "apple", "iphone"],
            "size": "6.7 pouces",
            "color": "Titanium naturel",
            "price": 1479.00,
            "description": "Le smartphone le plus avancé d'Apple avec puce A17 Pro"
        }
    
    def test_generator_initialization(self, generator):
        """Test de l'initialisation du générateur"""
        assert generator.title_rules['max_length'] == 200
        assert generator.bullet_rules['max_count'] == 5
        assert generator.keywords_rules['max_bytes'] == 250
        assert generator.image_rules['min_resolution'] == 1000
    
    @pytest.mark.asyncio
    async def test_generate_complete_listing(self, generator, sample_product_data):
        """Test de génération complète d'une fiche"""
        result = await generator.generate_amazon_listing(sample_product_data)
        
        # Vérifier la structure
        assert 'listing_id' in result
        assert 'generated_at' in result
        assert 'seo_content' in result
        assert 'generation_metadata' in result
        
        # Vérifier le contenu SEO
        seo_content = result['seo_content']
        assert 'title' in seo_content
        assert 'bullet_points' in seo_content
        assert 'description' in seo_content
        assert 'backend_keywords' in seo_content
        assert 'image_requirements' in seo_content
        
        # Vérifier les métadonnées
        metadata = result['generation_metadata']
        assert 'optimization_score' in metadata
        assert metadata['optimization_score'] >= 0
        assert metadata['optimization_score'] <= 100
    
    @pytest.mark.asyncio
    async def test_title_generation(self, generator, sample_product_data):
        """Test de génération de titre"""
        title = await generator._generate_title(sample_product_data)
        
        assert isinstance(title, str)
        assert len(title) <= 200
        assert len(title) >= 15
        assert "Apple" in title
        assert "iPhone 15 Pro Max" in title
    
    @pytest.mark.asyncio
    async def test_bullets_generation(self, generator, sample_product_data):
        """Test de génération de bullets"""
        bullets = await generator._generate_bullets(sample_product_data)
        
        assert isinstance(bullets, list)
        assert len(bullets) <= 5
        assert len(bullets) >= 1
        
        for bullet in bullets:
            assert isinstance(bullet, str)
            assert len(bullet) <= 255
            assert len(bullet) >= 10
    
    @pytest.mark.asyncio
    async def test_description_generation(self, generator, sample_product_data):
        """Test de génération de description"""
        description = await generator._generate_description(sample_product_data)
        
        assert isinstance(description, str)
        assert len(description) >= 100
        assert len(description) <= 2000
        assert '<h3>' in description or '<h4>' in description  # Structure HTML
        assert 'Apple' in description
    
    @pytest.mark.asyncio
    async def test_keywords_generation(self, generator, sample_product_data):
        """Test de génération de mots-clés"""
        keywords = await generator._generate_backend_keywords(sample_product_data)
        
        assert isinstance(keywords, str)
        assert len(keywords.encode('utf-8')) <= 250
        assert 'apple' in keywords.lower()
        assert 'iphone' in keywords.lower()
    
    def test_input_validation(self, generator):
        """Test de validation des données d'entrée"""
        # Test données manquantes
        with pytest.raises(ValueError):
            generator._validate_input_data({})
        
        with pytest.raises(ValueError):
            generator._validate_input_data({"brand": "Apple"})  # product_name manquant
        
        with pytest.raises(ValueError):
            generator._validate_input_data({"brand": "A"})  # brand trop court
        
        # Test données valides
        valid_data = {
            "brand": "Apple",
            "product_name": "iPhone",
            "category": "électronique"
        }
        generator._validate_input_data(valid_data)  # Ne doit pas lever d'exception

# Tests pour le validateur
class TestAmazonListingValidator:
    """Tests pour le validateur de fiches Amazon"""
    
    @pytest.fixture
    def validator(self):
        """Fixture pour le validateur"""
        from amazon.listings.validators import AmazonListingValidator
        return AmazonListingValidator()
    
    @pytest.fixture
    def sample_listing_data(self):
        """Données de fiche de test"""
        return {
            "listing_id": "test_123",
            "product_data": {
                "brand": "Apple",
                "product_name": "iPhone 15 Pro Max",
                "category": "électronique"
            },
            "seo_content": {
                "title": "Apple iPhone 15 Pro Max 256GB Titanium naturel - Smartphone Premium",
                "bullet_points": [
                    "✅ PERFORMANCE SUPÉRIEURE : Puce A17 Pro pour des performances exceptionnelles",
                    "🎯 DESIGN TITANIUM : Construction premium en titanium naturel résistant",
                    "📸 SYSTÈME CAMÉRAS PRO : Triple caméra 48MP avec zoom optique 5x",
                    "⚡ BATTERIE LONGUE DURÉE : Jusqu'à 29h de lecture vidéo en continu",
                    "🔒 SÉCURITÉ AVANCÉE : Face ID et chiffrement avancé pour vos données"
                ],
                "description": "<h3>🌟 Apple iPhone 15 Pro Max</h3><p>Découvrez notre <strong>iPhone 15 Pro Max</strong> conçu pour répondre à tous vos besoins en matière de <em>électronique</em>.</p>",
                "backend_keywords": "apple, iphone, smartphone, premium, titanium, pro, 15, max",
                "image_requirements": {
                    "main_image": {
                        "description": "Image principale iPhone 15 Pro Max sur fond blanc",
                        "min_resolution": "1000x1000",
                        "required": True
                    },
                    "total_count": 5
                }
            }
        }
    
    def test_validator_initialization(self, validator):
        """Test de l'initialisation du validateur"""
        assert validator.validation_rules['title']['max_length'] == 200
        assert validator.validation_rules['bullets']['max_count'] == 5
        assert validator.validation_rules['keywords']['max_bytes'] == 250
    
    def test_complete_validation_success(self, validator, sample_listing_data):
        """Test de validation complète réussie"""
        result = validator.validate_complete_listing(sample_listing_data)
        
        assert 'validation_id' in result
        assert 'overall_status' in result
        assert 'validation_score' in result
        assert 'details' in result
        
        # Score doit être raisonnable
        assert result['validation_score'] >= 0
        assert result['validation_score'] <= 100
    
    def test_title_validation(self, validator):
        """Test de validation de titre"""
        # Titre valide
        result = validator._validate_title("Apple iPhone 15 Pro Max 256GB Titanium")
        assert result['status'] == 'APPROVED'
        assert result['score'] == 100.0
        
        # Titre trop court
        result = validator._validate_title("iPhone")
        assert result['status'] == 'REJECTED'
        assert result['score'] == 0.0
        
        # Titre trop long
        long_title = "A" * 201
        result = validator._validate_title(long_title)
        assert result['status'] == 'REJECTED'
        
        # Titre avec mots interdits
        result = validator._validate_title("Best iPhone Ever - Cheapest Price")
        assert result['status'] == 'REJECTED'
        assert len(result['errors']) > 0
    
    def test_bullets_validation(self, validator):
        """Test de validation des bullets"""
        # Bullets valides
        valid_bullets = [
            "Performance exceptionnelle avec puce A17 Pro",
            "Design titanium premium et résistant",
            "Système caméra avancé triple objectif"
        ]
        result = validator._validate_bullets(valid_bullets)
        assert result['score'] >= 80
        
        # Pas de bullets
        result = validator._validate_bullets([])
        assert result['status'] == 'REJECTED'
        
        # Trop de bullets
        too_many_bullets = ["Bullet " + str(i) for i in range(7)]
        result = validator._validate_bullets(too_many_bullets)
        assert result['status'] == 'REJECTED'
        
        # Bullet trop long
        long_bullet = "A" * 256
        result = validator._validate_bullets([long_bullet])
        assert result['score'] < 80
    
    def test_description_validation(self, validator):
        """Test de validation de description"""
        # Description valide
        valid_desc = "<h3>Test Product</h3><p>This is a valid description with enough content to meet minimum requirements.</p>"
        result = validator._validate_description(valid_desc)
        assert result['score'] >= 80
        
        # Description trop courte
        result = validator._validate_description("Short")
        assert result['status'] == 'REJECTED'
        
        # Description trop longue
        long_desc = "A" * 2001
        result = validator._validate_description(long_desc)
        assert result['status'] == 'REJECTED'
    
    def test_keywords_validation(self, validator):
        """Test de validation des mots-clés"""
        # Keywords valides
        valid_keywords = "apple, iphone, smartphone, premium, titanium"
        result = validator._validate_keywords(valid_keywords)
        assert result['score'] >= 80
        
        # Keywords trop longs
        long_keywords = ", ".join(["keyword" + str(i) for i in range(100)])
        result = validator._validate_keywords(long_keywords)
        assert result['status'] == 'REJECTED'
    
    def test_validation_summary(self, validator, sample_listing_data):
        """Test de génération de résumé"""
        validation_result = validator.validate_complete_listing(sample_listing_data)
        summary = validator.get_validation_summary(validation_result)
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert any(word in summary for word in ['✅', '⚠️', '❌'])

# Tests pour le publisher
class TestAmazonListingPublisher:
    """Tests pour le publisher Amazon SP-API"""
    
    @pytest.fixture
    def publisher(self):
        """Fixture pour le publisher"""
        with patch('amazon.listings.publisher.AmazonSPAPIClient'), \
             patch('amazon.listings.publisher.AmazonOAuthService'):
            from amazon.listings.publisher import AmazonListingPublisher
            return AmazonListingPublisher()
    
    @pytest.fixture
    def sample_product_data(self):
        """Données produit pour publication"""
        return {
            "brand": "Apple",
            "product_name": "iPhone 15 Pro Max",
            "category": "électronique",
            "price": 1479.00
        }
    
    @pytest.fixture
    def sample_seo_data(self):
        """Données SEO pour publication"""
        return {
            "title": "Apple iPhone 15 Pro Max 256GB Titanium",
            "bullet_points": [
                "Performance exceptionnelle avec puce A17 Pro",
                "Design titanium premium"
            ],
            "description": "<h3>iPhone 15 Pro Max</h3><p>Le meilleur smartphone d'Apple</p>",
            "backend_keywords": "apple, iphone, smartphone, premium"
        }
    
    @pytest.fixture
    def sample_connection_data(self):
        """Données de connexion pour publication"""
        return {
            "user_id": "test_user",
            "seller_id": "TEST_SELLER_123",
            "marketplace_id": "A13V1IB3VIYZZH",
            "region": "eu",
            "encrypted_refresh_token": "encrypted_token_123",
            "token_encryption_nonce": "nonce_123"
        }
    
    def test_publisher_initialization(self, publisher):
        """Test de l'initialisation du publisher"""
        assert publisher.product_type_mapping['électronique'] == 'CONSUMER_ELECTRONICS'
        assert 'maison' in publisher.product_type_mapping
    
    def test_sku_generation(self, publisher, sample_product_data):
        """Test de génération de SKU"""
        sku = publisher._generate_sku(sample_product_data)
        
        assert isinstance(sku, str)
        assert len(sku) > 10
        assert 'APPLE' in sku
        assert 'IPHONE' in sku
    
    def test_listing_url_generation(self, publisher):
        """Test de génération d'URL de listing"""
        url = publisher._generate_listing_url("TEST_SKU", "A13V1IB3VIYZZH")
        
        assert isinstance(url, str)
        assert 'amazon.fr' in url
        assert 'TEST_SKU' in url
    
    @pytest.mark.asyncio
    async def test_prepare_spapi_payload(self, publisher, sample_product_data, sample_seo_data):
        """Test de préparation du payload SP-API"""
        payload = await publisher._prepare_spapi_payload(sample_product_data, sample_seo_data)
        
        assert 'productType' in payload
        assert 'attributes' in payload
        assert 'item_name' in payload['attributes']
        assert 'brand' in payload['attributes']
        assert 'bullet_point' in payload['attributes']
        
        # Vérifier le format
        assert payload['productType'] == 'CONSUMER_ELECTRONICS'
        assert payload['attributes']['item_name'][0]['value'] == sample_seo_data['title']
    
    def test_publish_params_validation(self, publisher, sample_product_data, sample_seo_data, sample_connection_data):
        """Test de validation des paramètres de publication"""
        # Paramètres valides
        publisher._validate_publish_params(sample_product_data, sample_seo_data, sample_connection_data)
        
        # Paramètres invalides
        with pytest.raises(ValueError):
            publisher._validate_publish_params({}, sample_seo_data, sample_connection_data)
        
        with pytest.raises(ValueError):
            publisher._validate_publish_params(sample_product_data, {}, sample_connection_data)
        
        with pytest.raises(ValueError):
            publisher._validate_publish_params(sample_product_data, sample_seo_data, {})

# Tests d'intégration
class TestAmazonListingsIntegration:
    """Tests d'intégration pour le workflow complet"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_simulation(self):
        """Test du workflow complet : génération → validation → préparation publication"""
        
        # Données de test
        product_data = {
            "brand": "TestBrand",
            "product_name": "TestProduct Pro",
            "features": ["Feature 1", "Feature 2"],
            "category": "électronique",
            "target_keywords": ["test", "product", "pro"]
        }
        
        # 1. Génération
        from amazon.listings.generator import AmazonListingGenerator
        generator = AmazonListingGenerator()
        
        generated_listing = await generator.generate_amazon_listing(product_data)
        assert generated_listing is not None
        assert 'seo_content' in generated_listing
        
        # 2. Validation
        from amazon.listings.validators import AmazonListingValidator
        validator = AmazonListingValidator()
        
        validation_result = validator.validate_complete_listing(generated_listing)
        assert validation_result is not None
        assert 'overall_status' in validation_result
        
        # 3. Préparation publication
        with patch('amazon.listings.publisher.AmazonSPAPIClient'), \
             patch('amazon.listings.publisher.AmazonOAuthService'):
            from amazon.listings.publisher import AmazonListingPublisher
            publisher = AmazonListingPublisher()
            
            # Test préparation payload
            payload = await publisher._prepare_spapi_payload(
                product_data, 
                generated_listing['seo_content']
            )
            assert payload is not None
            assert 'productType' in payload
    
    def test_error_handling(self):
        """Test de gestion d'erreurs"""
        from amazon.listings.generator import AmazonListingGenerator
        from amazon.listings.validators import AmazonListingValidator
        
        generator = AmazonListingGenerator()
        validator = AmazonListingValidator()
        
        # Test données invalides pour générateur
        with pytest.raises(ValueError):
            generator._validate_input_data({})
        
        # Test données invalides pour validateur
        result = validator.validate_complete_listing({})
        assert result['overall_status'] == 'REJECTED'
        assert len(result['errors']) > 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])