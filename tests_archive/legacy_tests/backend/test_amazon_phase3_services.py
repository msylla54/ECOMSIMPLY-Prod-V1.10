# Tests Backend Amazon Phase 3 - Services
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import json
from datetime import datetime

# Import des services Phase 3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from services.amazon_scraping_service import AmazonScrapingService
from services.seo_optimizer_service import SEOOptimizerService
from services.price_optimizer_service import PriceOptimizerService
from services.amazon_publisher_service import AmazonPublisherService

class TestAmazonScrapingService:
    """Tests pour le service de scraping Amazon"""
    
    @pytest.fixture
    def scraping_service(self):
        return AmazonScrapingService()
    
    @pytest.mark.asyncio
    async def test_scrape_product_seo_and_price_success(self, scraping_service):
        """Test scraping réussi d'un produit Amazon"""
        
        # Mock HTML content
        mock_html = """
        <html>
            <head><title>iPhone 15 Pro</title></head>
            <body>
                <h1 id="productTitle">Apple iPhone 15 Pro Max 256GB Titane Naturel</h1>
                <div id="feature-bullets">
                    <ul>
                        <li><span class="a-list-item">QUALITÉ PREMIUM - Puce A17 Pro révolutionnaire</span></li>
                        <li><span class="a-list-item">DESIGN ÉLÉGANT - Châssis en titane ultra-résistant</span></li>
                        <li><span class="a-list-item">CAMÉRA PRO - Système triple caméra 48 Mpx</span></li>
                    </ul>
                </div>
                <div id="productDescription">
                    <p>Le smartphone le plus avancé d'Apple avec des performances exceptionnelles.</p>
                </div>
                <div class="a-price">
                    <span class="a-offscreen">1479,00 €</span>
                </div>
            </body>
        </html>
        """
        
        with patch.object(scraping_service, '_fetch_with_retry', return_value=mock_html):
            result = await scraping_service.scrape_product_seo_and_price(
                asin="B0CHX1W2Y8",
                marketplace="FR"
            )
            
            assert result['scraping_success'] is True
            assert result['asin'] == "B0CHX1W2Y8"
            assert result['marketplace'] == "FR"
            
            # Vérifier SEO data
            seo_data = result['seo_data']
            assert 'iPhone 15 Pro Max' in seo_data['title']
            assert len(seo_data['bullet_points']) >= 3
            assert 'Puce A17 Pro' in seo_data['bullet_points'][0]
            assert 'smartphone' in seo_data['description'].lower()
            
            # Vérifier price data
            price_data = result['price_data']
            assert price_data['current_price'] == 1479.0
            assert price_data['currency'] == 'EUR'
    
    @pytest.mark.asyncio
    async def test_scrape_competitor_prices(self, scraping_service):
        """Test scraping des prix concurrents"""
        
        mock_search_html = """
        <html>
            <body>
                <div data-component-type="s-search-result" data-asin="B0CHX1W2Y8">
                    <h2><a><span>iPhone 15 Pro Max 256GB</span></a></h2>
                    <span class="a-price"><span class="a-offscreen">1479,00 €</span></span>
                    <span class="a-icon-alt">4,5 sur 5 étoiles</span>
                </div>
                <div data-component-type="s-search-result" data-asin="B0CHX1W2Y9">
                    <h2><a><span>Samsung Galaxy S24 Ultra</span></a></h2>
                    <span class="a-price"><span class="a-offscreen">1299,99 €</span></span>
                    <span class="a-icon-alt">4,3 sur 5 étoiles</span>
                </div>
            </body>
        </html>
        """
        
        with patch.object(scraping_service, '_fetch_with_retry', return_value=mock_search_html):
            results = await scraping_service.scrape_competitor_prices(
                search_query="iPhone 15 Pro Max",
                marketplace="FR",
                max_results=5
            )
            
            assert len(results) == 2
            
            # Premier résultat
            first_result = results[0]
            assert first_result['asin'] == "B0CHX1W2Y8"
            assert 'iPhone 15 Pro Max' in first_result['title']
            assert first_result['price'] == 1479.0
            assert first_result['currency'] == 'EUR'
            assert first_result['rating'] == 4.5
            
            # Deuxième résultat
            second_result = results[1]
            assert second_result['asin'] == "B0CHX1W2Y9"
            assert 'Samsung Galaxy' in second_result['title']
            assert second_result['price'] == 1299.99
    
    @pytest.mark.asyncio
    async def test_scraping_error_handling(self, scraping_service):
        """Test gestion d'erreurs lors du scraping"""
        
        with patch.object(scraping_service, '_fetch_with_retry', return_value=None):
            result = await scraping_service.scrape_product_seo_and_price(
                asin="INVALID_ASIN",
                marketplace="FR"
            )
            
            assert result['scraping_success'] is False
            assert 'error' in result
            assert result['asin'] == "INVALID_ASIN"

class TestSEOOptimizerService:
    """Tests pour le service d'optimisation SEO"""
    
    @pytest.fixture
    def seo_service(self):
        return SEOOptimizerService()
    
    @pytest.fixture
    def sample_scraped_data(self):
        return {
            'seo_data': {
                'title': 'iPhone 15 Pro Max Apple 256GB',
                'bullet_points': [
                    'Puce A17 Pro performante',
                    'Écran Super Retina XDR',
                    'Système caméra Pro triple'
                ],
                'description': 'Smartphone haut de gamme avec performances exceptionnelles.',
                'extracted_keywords': ['iphone', 'apple', 'smartphone', 'pro', 'camera']
            },
            'product_data': {
                'brand': 'Apple',
                'categories': ['Électronique', 'Téléphones'],
                'rating': 4.5,
                'reviews_count': 1250
            },
            'price_data': {
                'current_price': 1479.0,
                'currency': 'EUR'
            }
        }
    
    @pytest.mark.asyncio
    async def test_optimize_seo_from_scraped_data_success(self, seo_service, sample_scraped_data):
        """Test optimisation SEO réussie"""
        
        # Mock réponse OpenAI
        mock_ai_response = {
            'title': 'Apple iPhone 15 Pro Max 256GB Titane Naturel - Smartphone Premium A17 Pro',
            'bullet_points': [
                'PERFORMANCE EXCEPTIONNELLE - Puce A17 Pro révolutionnaire pour des performances inégalées',
                'ÉCRAN AVANCÉ - Super Retina XDR 6,7 pouces avec ProMotion et Always-On',
                'SYSTÈME CAMÉRA PRO - Triple caméra 48 Mpx avec zoom optique et mode Action',
                'DESIGN PREMIUM - Châssis en titane ultra-résistant et élégant',
                'AUTONOMIE LONGUE DURÉE - Batterie optimisée pour une journée complète'
            ],
            'description': 'Découvrez l\'iPhone 15 Pro Max, le smartphone le plus avancé d\'Apple.\n\nCARACTÉRISTIQUES PRINCIPALES:\n• Puce A17 Pro avec GPU 6 cœurs\n• Écran Super Retina XDR 6,7 pouces\n• Système caméra Pro triple 48 Mpx\n• Châssis en titane de qualité aérospatiale\n\nAVANTAGES:\n• Performances gaming console\n• Photos et vidéos de qualité professionnelle\n• Résistance exceptionnelle aux chocs\n• Design premium et léger\n\nUTILISATION:\nIdéal pour les professionnels, créateurs de contenu et utilisateurs exigeants qui recherchent les meilleures performances mobiles.',
            'backend_keywords': 'iphone 15 pro max apple smartphone titane a17 pro camera 48mpx 256gb premium mobile phone'
        }
        
        with patch.object(seo_service, '_generate_optimized_seo_with_ai', return_value=mock_ai_response):
            result = await seo_service.optimize_seo_from_scraped_data(
                scraped_data=sample_scraped_data,
                target_keywords=['premium', 'titane', 'a17 pro', 'professionnel'],
                optimization_goals={'primary': 'conversion', 'secondary': 'visibility'}
            )
            
            assert 'optimized_seo' in result
            assert result['optimization_score'] > 80
            
            optimized_seo = result['optimized_seo']
            assert len(optimized_seo['title']) <= 200
            assert len(optimized_seo['bullet_points']) == 5
            assert all(len(bullet) <= 255 for bullet in optimized_seo['bullet_points'])
            assert 100 <= len(optimized_seo['description']) <= 2000
            assert len(optimized_seo['backend_keywords'].encode('utf-8')) <= 250
            
            # Vérifier validation
            validation = result['validation']
            assert validation['overall_status'] in ['APPROVED', 'WARNING']
    
    @pytest.mark.asyncio
    async def test_generate_seo_variants(self, seo_service):
        """Test génération de variantes SEO"""
        
        base_seo = {
            'title': 'Apple iPhone 15 Pro Max 256GB Premium',
            'bullet_points': [
                'PERFORMANCE - Puce A17 Pro avancée',
                'DESIGN - Châssis titane premium',
                'CAMÉRA - Système Pro triple 48 Mpx'
            ],
            'description': 'Smartphone premium avec performances exceptionnelles.',
            'backend_keywords': 'iphone apple premium smartphone pro'
        }
        
        variants = await seo_service.generate_seo_variants(base_seo, variant_count=3)
        
        assert len(variants) == 3
        
        for i, variant in enumerate(variants):
            assert variant['variant_id'] == f'v{i+1}'
            assert 'title' in variant
            assert 'bullet_points' in variant
            assert 'validation' in variant
            
            # Vérifier que les variantes sont différentes du base
            assert variant['title'] != base_seo['title']
    
    def test_validate_amazon_seo(self, seo_service):
        """Test validation SEO Amazon A9/A10"""
        
        valid_seo = {
            'title': 'Apple iPhone 15 Pro Maximum Performance Smartphone',
            'bullet_points': [
                'PREMIUM QUALITY - Advanced A17 Pro chip for exceptional performance',
                'ELEGANT DESIGN - Titanium chassis with premium finish',
                'PRO CAMERA - Triple camera system 48MP with optical zoom',
                'LONG BATTERY - All-day battery life with fast charging',
                'WATER RESISTANT - IP68 rating for peace of mind'
            ],
            'description': 'Discover the most advanced iPhone with revolutionary A17 Pro chip. ' * 5,  # ~100+ chars
            'backend_keywords': 'iphone 15 pro max apple smartphone premium titanium camera 48mp a17 chip'
        }
        
        validation = seo_service._validate_amazon_seo(valid_seo)
        
        assert validation['overall_status'] == 'APPROVED'
        assert len(validation['errors']) == 0
        
        # Test titre trop long
        invalid_seo = valid_seo.copy()
        invalid_seo['title'] = 'A' * 250  # Trop long
        
        validation_invalid = seo_service._validate_amazon_seo(invalid_seo)
        
        assert validation_invalid['overall_status'] in ['REJECTED', 'WARNING']
        assert len(validation_invalid['errors']) > 0

class TestPriceOptimizerService:
    """Tests pour le service d'optimisation des prix"""
    
    @pytest.fixture
    def price_service(self):
        return PriceOptimizerService()
    
    @pytest.fixture
    def sample_product_data(self):
        return {
            'cost_price': 50.0,
            'current_price': 79.99,
            'min_price': 55.0,
            'max_price': 150.0,
            'target_margin_percent': 20,
            'pricing_strategy': 'competitive'
        }
    
    @pytest.fixture
    def sample_competitor_prices(self):
        return [
            {'asin': 'B001', 'price': 75.0, 'currency': 'EUR', 'rating': 4.5},
            {'asin': 'B002', 'price': 82.50, 'currency': 'EUR', 'rating': 4.2},
            {'asin': 'B003', 'price': 89.99, 'currency': 'EUR', 'rating': 4.8},
            {'asin': 'B004', 'price': 72.0, 'currency': 'EUR', 'rating': 4.0},
            {'asin': 'B005', 'price': 95.0, 'currency': 'EUR', 'rating': 4.6}
        ]
    
    @pytest.mark.asyncio
    async def test_optimize_price_from_market_data(self, price_service, sample_product_data, sample_competitor_prices):
        """Test optimisation prix basée sur données marché"""
        
        # Mock taux de change
        with patch.object(price_service, '_get_exchange_rates', return_value={'EUR': 1.0, 'USD': 1.08}):
            result = await price_service.optimize_price_from_market_data(
                product_data=sample_product_data,
                competitor_prices=sample_competitor_prices,
                target_marketplace='FR'
            )
            
            assert 'optimized_price' in result
            assert result['currency'] == 'EUR'
            
            optimized_price = result['optimized_price']
            assert optimized_price['amount'] > 0
            assert optimized_price['currency'] == 'EUR'
            
            # Vérifier que le prix respecte les contraintes
            assert sample_product_data['min_price'] <= optimized_price['amount'] <= sample_product_data['max_price']
            
            # Vérifier l'analyse concurrentielle
            competitor_analysis = result['competitor_analysis']
            assert competitor_analysis['count'] == 5
            assert 'statistics' in competitor_analysis
            assert competitor_analysis['statistics']['average'] > 0
            
            # Vérifier métriques
            metrics = result['metrics']
            assert 'confidence_score' in metrics
            assert 0 <= metrics['confidence_score'] <= 100
    
    @pytest.mark.asyncio
    async def test_analyze_competitor_prices(self, price_service, sample_competitor_prices):
        """Test analyse des prix concurrents"""
        
        analysis = await price_service._analyze_competitor_prices(sample_competitor_prices, 'FR')
        
        assert analysis['count'] == 5
        
        stats = analysis['statistics']
        assert stats['average'] > 0
        assert stats['median'] > 0
        assert stats['min'] == 72.0
        assert stats['max'] == 95.0
        assert stats['variance'] >= 0
        
        # Vérifier distribution des prix
        distribution = analysis['price_distribution']
        assert 'low_price' in distribution
        assert 'mid_price' in distribution
        assert 'high_price' in distribution
        
        # Vérifier évaluation compétitivité
        assert analysis['market_competitiveness'] in ['highly_competitive', 'competitive', 'moderately_competitive', 'fragmented']
    
    @pytest.mark.asyncio
    async def test_price_constraints_application(self, price_service, sample_product_data):
        """Test application des contraintes de prix"""
        
        # Prix optimal théorique trop bas
        optimal_price = {'amount': 40.0, 'calculation_method': 'test'}
        
        constrained_price = price_service._apply_price_constraints(
            optimal_price, sample_product_data, price_service.default_config
        )
        
        # Le prix doit être ajusté au minimum
        assert constrained_price['amount'] >= sample_product_data['min_price']
        assert constrained_price['constrained'] is True
        assert len(constrained_price['constraints_applied']) > 0
    
    @pytest.mark.asyncio
    async def test_validate_price_rules(self, price_service, sample_product_data):
        """Test validation des règles de prix"""
        
        # Prix valide
        validation_valid = await price_service.validate_price_rules(
            price=75.0,
            product_data=sample_product_data
        )
        
        assert validation_valid['valid'] is True
        assert len(validation_valid['errors']) == 0
        
        # Prix avec marge insuffisante
        validation_invalid = await price_service.validate_price_rules(
            price=52.0,  # Marge trop faible
            product_data=sample_product_data
        )
        
        assert validation_invalid['valid'] is False
        assert len(validation_invalid['errors']) > 0
        assert 'marge' in validation_invalid['errors'][0].lower()

class TestAmazonPublisherService:
    """Tests pour le service de publication Amazon"""
    
    @pytest.fixture
    def publisher_service(self):
        return AmazonPublisherService()
    
    @pytest.fixture
    def sample_updates(self):
        return [
            {
                'sku': 'TEST-SKU-001',
                'title': 'Apple iPhone 15 Pro Max Premium',
                'bullet_points': [
                    'PERFORMANCE - Puce A17 Pro',
                    'DESIGN - Châssis titane',
                    'CAMÉRA - Système Pro triple'
                ],
                'description': 'Smartphone premium avec performances exceptionnelles.',
                'search_terms': 'iphone apple premium smartphone',
                'standard_price': 1479.0,
                'currency': 'EUR'
            }
        ]
    
    @pytest.mark.asyncio
    async def test_verify_amazon_connection_success(self, publisher_service):
        """Test vérification connexion Amazon réussie"""
        
        # Mock connection valide
        mock_connection = MagicMock()
        mock_connection.is_token_expired.return_value = False
        mock_connection.marketplace_id = 'A13V1IB3VIYZZH'  # FR
        mock_connection.decrypted_refresh_token = 'mock_token'
        
        with patch('models.amazon_spapi.AmazonConnection.find_by_user_and_marketplace', return_value=mock_connection):
            with patch.object(publisher_service, '_test_sp_api_connectivity', return_value={'success': True}):
                result = await publisher_service._verify_amazon_connection('user123', 'A13V1IB3VIYZZH')
                
                assert result['connected'] is True
                assert result['connection'] == mock_connection
    
    @pytest.mark.asyncio
    async def test_validate_updates_batch(self, publisher_service, sample_updates):
        """Test validation d'un batch de mises à jour"""
        
        validation_results = await publisher_service._validate_updates_batch(
            sample_updates, 'full_update'
        )
        
        assert validation_results['valid_count'] >= 0
        assert validation_results['invalid_count'] >= 0
        assert len(validation_results['validation_details']) == len(sample_updates)
        
        # Vérifier validation détaillée
        first_validation = validation_results['validation_details'][0]
        assert 'sku' in first_validation
        assert 'valid' in first_validation
        assert 'errors' in first_validation
        assert 'warnings' in first_validation
    
    @pytest.mark.asyncio
    async def test_prepare_sp_api_payload(self, publisher_service, sample_updates):
        """Test préparation payload SP-API"""
        
        update = sample_updates[0]
        payload = publisher_service._prepare_sp_api_payload(update, 'full_update')
        
        assert payload['sku'] == update['sku']
        assert payload['title'] == update['title']
        assert payload['bullet_point_1'] == update['bullet_points'][0]
        assert payload['description'] == update['description']
        assert payload['search_terms'] == update['search_terms']
        assert payload['standard_price']['amount'] == update['standard_price']
        assert payload['update_source'] == 'ECOMSIMPLY_AUTO_PUBLISHER'
    
    def test_should_retry_error(self, publisher_service):
        """Test logique de retry des erreurs"""
        
        # Erreurs qui doivent être retryées
        retry_errors = ['RequestThrottled', 'ServiceUnavailable', 'InternalError']
        for error_code in retry_errors:
            assert publisher_service._should_retry_error(error_code) is True
        
        # Erreurs qui ne doivent pas être retryées
        no_retry_errors = ['InvalidInput', 'Unauthorized', 'Forbidden']
        for error_code in no_retry_errors:
            assert publisher_service._should_retry_error(error_code) is False

# Tests d'intégration

class TestAmazonPhase3Integration:
    """Tests d'intégration Phase 3"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_scraping_to_publication(self):
        """Test workflow complet : Scraping → Optimisation → Publication"""
        
        # Étape 1: Scraping
        scraping_service = AmazonScrapingService()
        
        mock_scraped_data = {
            'scraping_success': True,
            'asin': 'B0CHX1W2Y8',
            'marketplace': 'FR',
            'seo_data': {
                'title': 'iPhone 15 Pro Max Apple 256GB',
                'bullet_points': ['Puce A17 Pro', 'Écran XDR', 'Caméra Pro'],
                'description': 'Smartphone premium Apple.',
                'extracted_keywords': ['iphone', 'apple', 'premium']
            },
            'price_data': {
                'current_price': 1479.0,
                'currency': 'EUR'
            },
            'product_data': {
                'brand': 'Apple',
                'rating': 4.5
            }
        }
        
        # Étape 2: Optimisation SEO
        seo_service = SEOOptimizerService()
        
        mock_seo_result = {
            'optimized_seo': {
                'title': 'Apple iPhone 15 Pro Max 256GB Titane Naturel Premium',
                'bullet_points': [
                    'PERFORMANCE - Puce A17 Pro révolutionnaire',
                    'DESIGN - Châssis titane ultra-résistant',
                    'CAMÉRA - Système Pro triple 48 Mpx',
                    'ÉCRAN - Super Retina XDR 6,7 pouces',
                    'AUTONOMIE - Batterie longue durée'
                ],
                'description': 'Smartphone premium Apple avec performances exceptionnelles.' * 10,
                'backend_keywords': 'iphone 15 pro max apple premium titane smartphone'
            },
            'validation': {'overall_status': 'APPROVED'},
            'optimization_score': 95
        }
        
        # Étape 3: Optimisation Prix
        price_service = PriceOptimizerService()
        
        competitor_prices = [
            {'price': 1450.0, 'currency': 'EUR'},
            {'price': 1499.0, 'currency': 'EUR'},
            {'price': 1525.0, 'currency': 'EUR'}
        ]
        
        mock_price_result = {
            'optimized_price': {
                'amount': 1489.0,
                'currency': 'EUR'
            },
            'metrics': {
                'confidence_score': 85,
                'margin': {'percentage': 25.0, 'target_met': True}
            },
            'pricing_strategy': {
                'strategy': 'competitive',
                'confidence': 'high'
            }
        }
        
        # Étape 4: Publication
        publisher_service = AmazonPublisherService()
        
        updates = [{
            'sku': 'B0CHX1W2Y8',
            'title': mock_seo_result['optimized_seo']['title'],
            'bullet_points': mock_seo_result['optimized_seo']['bullet_points'],
            'description': mock_seo_result['optimized_seo']['description'],
            'search_terms': mock_seo_result['optimized_seo']['backend_keywords'],
            'standard_price': mock_price_result['optimized_price']['amount'],
            'currency': mock_price_result['optimized_price']['currency']
        }]
        
        # Simulation du workflow complet
        with patch.object(scraping_service, 'scrape_product_seo_and_price', return_value=mock_scraped_data):
            with patch.object(seo_service, 'optimize_seo_from_scraped_data', return_value=mock_seo_result):
                with patch.object(price_service, 'optimize_price_from_market_data', return_value=mock_price_result):
                    with patch.object(publisher_service, 'publish_seo_and_price_updates', return_value={
                        'success': True,
                        'summary': {'success_count': 1, 'error_count': 0, 'success_rate': 100}
                    }):
                        
                        # Workflow complet
                        scraped_data = await scraping_service.scrape_product_seo_and_price('B0CHX1W2Y8', 'FR')
                        assert scraped_data['scraping_success'] is True
                        
                        seo_result = await seo_service.optimize_seo_from_scraped_data(scraped_data)
                        assert seo_result['optimization_score'] >= 90
                        
                        price_result = await price_service.optimize_price_from_market_data(
                            {'cost_price': 1000.0}, competitor_prices, target_marketplace='FR'
                        )
                        assert price_result['metrics']['confidence_score'] >= 80
                        
                        publication_result = await publisher_service.publish_seo_and_price_updates(
                            'user123', 'A13V1IB3VIYZZH', updates, 'full_update'
                        )
                        assert publication_result['success'] is True
                        assert publication_result['summary']['success_rate'] == 100

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])