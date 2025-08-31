# Tests API Amazon Phase 3 - Routes
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import json
from datetime import datetime

# Import du serveur FastAPI
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from server import app

class TestAmazonPhase3APIRoutes:
    """Tests pour les routes API Phase 3"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_token(self):
        """Token JWT mock pour l'authentification"""
        return "Bearer mock_jwt_token"
    
    @pytest.fixture
    def mock_user_payload(self):
        return {
            'user_id': 'test_user_123',
            'email': 'test@example.com'
        }

    def test_health_check_phase3(self, client):
        """Test du health check Phase 3"""
        
        response = client.get("/api/amazon/health/phase3")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['success'] is True
        assert 'health' in data
        assert data['health']['phase'] == 'Phase 3 - SEO + Prix Amazon'
        assert 'services' in data['health']
        assert 'external_dependencies' in data['health']
        
        # Vérifier services
        services = data['health']['services']
        expected_services = ['scraping_service', 'seo_optimizer', 'price_optimizer', 'publisher_service']
        for service in expected_services:
            assert service in services
            assert services[service] == 'healthy'

    def test_get_phase3_configuration(self, client, mock_token, mock_user_payload):
        """Test récupération configuration Phase 3"""
        
        with patch('modules.security.verify_jwt_token', return_value=mock_user_payload):
            response = client.get(
                "/api/amazon/config/phase3",
                headers={"Authorization": mock_token}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data['success'] is True
            assert 'configuration' in data
            
            config = data['configuration']
            assert 'scraping' in config
            assert 'seo_optimization' in config
            assert 'price_optimization' in config
            assert 'publication' in config
            assert config['user_id'] == mock_user_payload['user_id']
            
            # Vérifier configuration scraping
            scraping_config = config['scraping']
            assert 'supported_marketplaces' in scraping_config
            assert 'FR' in scraping_config['supported_marketplaces']
            assert scraping_config['max_competitor_results'] == 10

    def test_scrape_amazon_product_success(self, client, mock_token, mock_user_payload):
        """Test scraping produit Amazon réussi"""
        
        mock_scraped_data = {
            'asin': 'B0CHX1W2Y8',
            'marketplace': 'FR',
            'scraped_at': datetime.utcnow().isoformat(),
            'scraping_success': True,
            'seo_data': {
                'title': 'Apple iPhone 15 Pro Max 256GB Titane Naturel',
                'bullet_points': [
                    'QUALITÉ PREMIUM - Puce A17 Pro révolutionnaire',
                    'DESIGN ÉLÉGANT - Châssis en titane ultra-résistant',
                    'CAMÉRA PRO - Système triple caméra 48 Mpx'
                ],
                'description': 'Le smartphone le plus avancé d\'Apple.',
                'extracted_keywords': ['iphone', 'apple', 'premium', 'smartphone']
            },
            'price_data': {
                'current_price': 1479.0,
                'currency': 'EUR',
                'prices_found': [{'value': 1479.0, 'formatted': '1479,00 €'}]
            },
            'product_data': {
                'brand': 'Apple',
                'categories': ['Électronique', 'Téléphones'],
                'rating': 4.5,
                'reviews_count': 1250
            }
        }
        
        with patch('modules.security.verify_jwt_token', return_value=mock_user_payload):
            with patch('services.amazon_scraping_service.AmazonScrapingService.scrape_product_seo_and_price', 
                      return_value=mock_scraped_data):
                
                response = client.get(
                    "/api/amazon/scraping/B0CHX1W2Y8?marketplace=FR",
                    headers={"Authorization": mock_token}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data['success'] is True
                assert data['asin'] == 'B0CHX1W2Y8'
                assert data['marketplace'] == 'FR'
                assert 'data' in data
                
                scraped_data = data['data']
                assert scraped_data['scraping_success'] is True
                assert 'iPhone 15 Pro Max' in scraped_data['seo_data']['title']
                assert scraped_data['price_data']['current_price'] == 1479.0
                assert scraped_data['product_data']['brand'] == 'Apple'

    def test_scrape_competitor_prices_success(self, client, mock_token, mock_user_payload):
        """Test scraping prix concurrents réussi"""
        
        mock_competitor_data = [
            {
                'asin': 'B0CHX1W2Y8',
                'title': 'Apple iPhone 15 Pro Max 256GB Titane Naturel',
                'price': 1479.0,
                'rating': 4.5,
                'currency': 'EUR',
                'search_query': 'iPhone 15 Pro Max'
            },
            {
                'asin': 'B0CHX1W2Y9',
                'title': 'Samsung Galaxy S24 Ultra 512GB',
                'price': 1299.99,
                'rating': 4.3,
                'currency': 'EUR',
                'search_query': 'iPhone 15 Pro Max'
            }
        ]
        
        with patch('modules.security.verify_jwt_token', return_value=mock_user_payload):
            with patch('services.amazon_scraping_service.AmazonScrapingService.scrape_competitor_prices',
                      return_value=mock_competitor_data):
                
                response = client.get(
                    "/api/amazon/scraping/competitors/iPhone%2015%20Pro%20Max?marketplace=FR&max_results=5",
                    headers={"Authorization": mock_token}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data['success'] is True
                assert data['search_query'] == 'iPhone 15 Pro Max'
                assert data['marketplace'] == 'FR'
                assert data['results_count'] == 2
                assert len(data['data']) == 2
                
                first_result = data['data'][0]
                assert first_result['asin'] == 'B0CHX1W2Y8'
                assert first_result['price'] == 1479.0

    def test_optimize_seo_content_success(self, client, mock_token, mock_user_payload):
        """Test optimisation SEO réussie"""
        
        request_data = {
            'scraped_data': {
                'seo_data': {
                    'title': 'iPhone 15 Pro Max Apple 256GB',
                    'bullet_points': ['Puce A17 Pro', 'Écran XDR'],
                    'description': 'Smartphone premium Apple.',
                    'extracted_keywords': ['iphone', 'apple']
                },
                'product_data': {'brand': 'Apple'},
                'price_data': {'current_price': 1479.0, 'currency': 'EUR'}
            },
            'target_keywords': ['premium', 'titane', 'professionnel'],
            'optimization_goals': {'primary': 'conversion'}
        }
        
        mock_optimization_result = {
            'optimized_seo': {
                'title': 'Apple iPhone 15 Pro Max 256GB Titane Naturel Premium Smartphone',
                'bullet_points': [
                    'PERFORMANCE EXCEPTIONNELLE - Puce A17 Pro révolutionnaire',
                    'DESIGN PREMIUM - Châssis en titane ultra-résistant',
                    'CAMÉRA PROFESSIONNELLE - Système triple caméra 48 Mpx',
                    'ÉCRAN AVANCÉ - Super Retina XDR 6,7 pouces',
                    'AUTONOMIE LONGUE DURÉE - Batterie optimisée'
                ],
                'description': 'Découvrez le smartphone le plus avancé d\'Apple avec la puce A17 Pro.',
                'backend_keywords': 'iphone 15 pro max apple premium titane smartphone professionnel'
            },
            'validation': {
                'overall_status': 'APPROVED',
                'errors': [],
                'warnings': []
            },
            'optimization_score': 95,
            'optimization_metadata': {
                'optimized_at': datetime.utcnow().isoformat(),
                'target_keywords': ['premium', 'titane', 'professionnel'],
                'ai_model': 'gpt-4-turbo-preview'
            }
        }
        
        with patch('modules.security.verify_jwt_token', return_value=mock_user_payload):
            with patch('services.seo_optimizer_service.SEOOptimizerService.optimize_seo_from_scraped_data',
                      return_value=mock_optimization_result):
                
                response = client.post(
                    "/api/amazon/seo/optimize",
                    headers={"Authorization": mock_token},
                    json=request_data
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data['success'] is True
                assert 'optimization_result' in data
                
                result = data['optimization_result']
                assert result['optimization_score'] == 95
                assert result['validation']['overall_status'] == 'APPROVED'
                assert len(result['optimized_seo']['bullet_points']) == 5

    def test_generate_seo_variants_success(self, client, mock_token, mock_user_payload):
        """Test génération variantes SEO réussie"""
        
        request_data = {
            'base_seo': {
                'title': 'Apple iPhone 15 Pro Max Premium',
                'bullet_points': [
                    'PERFORMANCE - Puce A17 Pro',
                    'DESIGN - Châssis titane',
                    'CAMÉRA - Système Pro triple'
                ],
                'description': 'Smartphone premium.',
                'backend_keywords': 'iphone apple premium'
            },
            'variant_count': 3
        }
        
        mock_variants = [
            {
                'variant_id': 'v1',
                'title': 'Professionnel Apple iPhone 15 Pro Max Premium',
                'bullet_points': ['AVANTAGE UNIQUE - Puce A17 Pro', 'CARACTÉRISTIQUE - Châssis titane'],
                'validation': {'overall_status': 'APPROVED'}
            },
            {
                'variant_id': 'v2', 
                'title': 'Haute Qualité Apple iPhone 15 Pro Max Premium',
                'bullet_points': ['BÉNÉFICE CLEF - Puce A17 Pro', 'INNOVATION - Châssis titane'],
                'validation': {'overall_status': 'APPROVED'}
            },
            {
                'variant_id': 'v3',
                'title': 'Apple iPhone 15 Professionnel Maximum Premium',
                'bullet_points': ['PERFORMANCE - Puce A17 Professionnel', 'DESIGN - Châssis titane'],
                'validation': {'overall_status': 'WARNING'}
            }
        ]
        
        with patch('modules.security.verify_jwt_token', return_value=mock_user_payload):
            with patch('services.seo_optimizer_service.SEOOptimizerService.generate_seo_variants',
                      return_value=mock_variants):
                
                response = client.post(
                    "/api/amazon/seo/variants",
                    headers={"Authorization": mock_token},
                    json=request_data
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data['success'] is True
                assert len(data['variants']) == 3
                
                for i, variant in enumerate(data['variants']):
                    assert variant['variant_id'] == f'v{i+1}'
                    assert 'title' in variant
                    assert 'validation' in variant

    def test_optimize_product_price_success(self, client, mock_token, mock_user_payload):
        """Test optimisation prix réussie"""
        
        request_data = {
            'product_data': {
                'cost_price': 50.0,
                'current_price': 79.99,
                'min_price': 55.0,
                'max_price': 150.0,
                'target_margin_percent': 20,
                'pricing_strategy': 'competitive'
            },
            'competitor_prices': [
                {'asin': 'B001', 'price': 75.0, 'currency': 'EUR'},
                {'asin': 'B002', 'price': 82.50, 'currency': 'EUR'},
                {'asin': 'B003', 'price': 89.99, 'currency': 'EUR'}
            ],
            'target_marketplace': 'FR'
        }
        
        mock_price_optimization = {
            'optimized_price': {
                'amount': 78.50,
                'currency': 'EUR',
                'calculation_method': 'weighted_competitor_cost',
                'constrained': False,
                'constraints_applied': []
            },
            'competitor_analysis': {
                'count': 3,
                'statistics': {'average': 82.50, 'median': 82.50, 'min': 75.0, 'max': 89.99},
                'market_competitiveness': 'competitive'
            },
            'pricing_strategy': {
                'strategy': 'competitive',
                'rationale': 'Prix aligné sur le marché (-4.8%)',
                'confidence': 'high'
            },
            'metrics': {
                'margin': {'amount': 28.50, 'percentage': 57.0, 'target_met': True},
                'competitive_position': {'percentile': 25.0, 'positioning': 'value'},
                'confidence_score': 85
            },
            'optimization_metadata': {
                'optimized_at': datetime.utcnow().isoformat(),
                'competitors_analyzed': 3,
                'confidence_score': 85
            }
        }
        
        with patch('modules.security.verify_jwt_token', return_value=mock_user_payload):
            with patch('services.price_optimizer_service.PriceOptimizerService.optimize_price_from_market_data',
                      return_value=mock_price_optimization):
                
                response = client.post(
                    "/api/amazon/price/optimize",
                    headers={"Authorization": mock_token},
                    json=request_data
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data['success'] is True
                assert 'price_optimization' in data
                
                result = data['price_optimization']
                assert result['optimized_price']['amount'] == 78.50
                assert result['optimized_price']['currency'] == 'EUR'
                assert result['metrics']['confidence_score'] == 85
                assert result['pricing_strategy']['strategy'] == 'competitive'

    def test_validate_price_rules_success(self, client, mock_token, mock_user_payload):
        """Test validation prix réussie"""
        
        request_data = {
            'price': 75.0,
            'product_data': {
                'cost_price': 50.0,
                'min_price': 55.0,
                'max_price': 150.0
            },
            'rules': {
                'min_margin_percent': 15,
                'max_margin_percent': 40
            }
        }
        
        mock_validation = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'details': {
                'margin': {
                    'current': 50.0,
                    'minimum_required': 15,
                    'valid': True
                },
                'price_bounds': {
                    'current': 75.0,
                    'minimum': 55.0,
                    'maximum': 150.0,
                    'within_bounds': True
                }
            }
        }
        
        with patch('modules.security.verify_jwt_token', return_value=mock_user_payload):
            with patch('services.price_optimizer_service.PriceOptimizerService.validate_price_rules',
                      return_value=mock_validation):
                
                response = client.post(
                    "/api/amazon/price/validate",
                    headers={"Authorization": mock_token},
                    json=request_data
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data['success'] is True
                assert data['validation']['valid'] is True
                assert len(data['validation']['errors']) == 0
                assert data['price'] == 75.0

    def test_publish_seo_and_price_updates_sync(self, client, mock_token, mock_user_payload):
        """Test publication synchrone réussie"""
        
        request_data = {
            'marketplace_id': 'A13V1IB3VIYZZH',  # FR
            'updates': [
                {
                    'sku': 'TEST-SKU-001',
                    'title': 'Apple iPhone 15 Pro Max Premium',
                    'bullet_points': [
                        'PERFORMANCE - Puce A17 Pro',
                        'DESIGN - Châssis titane'
                    ],
                    'description': 'Smartphone premium Apple.',
                    'search_terms': 'iphone apple premium',
                    'standard_price': 1479.0,
                    'currency': 'EUR'
                }
            ],
            'update_type': 'full_update',
            'validation_required': True,
            'async_mode': False
        }
        
        mock_publication_result = {
            'success': True,
            'session_id': 'pub_test_user_123_1640995200',
            'summary': {
                'total_updates': 1,
                'success_count': 1,
                'error_count': 0,
                'success_rate': 100.0
            },
            'timing': {
                'started_at': datetime.utcnow().isoformat(),
                'completed_at': datetime.utcnow().isoformat(),
                'duration_seconds': 3.5
            },
            'feed_tracking': {
                'feed_ids_created': ['feed_abc123def456'],
                'feeds_count': 1
            },
            'detailed_results': [
                {
                    'sku': 'TEST-SKU-001',
                    'success': True,
                    'feed_id': 'feed_abc123def456',
                    'processing_status': 'SUBMITTED'
                }
            ]
        }
        
        with patch('modules.security.verify_jwt_token', return_value=mock_user_payload):
            with patch('services.amazon_publisher_service.AmazonPublisherService.publish_seo_and_price_updates',
                      return_value=mock_publication_result):
                
                response = client.post(
                    "/api/amazon/publish",
                    headers={"Authorization": mock_token},
                    json=request_data
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data['success'] is True
                assert data['async_mode'] is False
                assert 'publication_result' in data
                
                result = data['publication_result']
                assert result['success'] is True
                assert result['summary']['success_rate'] == 100.0
                assert len(result['feed_tracking']['feed_ids_created']) == 1

    def test_publish_seo_and_price_updates_async(self, client, mock_token, mock_user_payload):
        """Test publication asynchrone"""
        
        request_data = {
            'marketplace_id': 'A13V1IB3VIYZZH',
            'updates': [
                {
                    'sku': 'TEST-SKU-002',
                    'title': 'Samsung Galaxy S24 Ultra Premium',
                    'standard_price': 1299.99
                }
            ],
            'update_type': 'price_only',
            'async_mode': True
        }
        
        with patch('modules.security.verify_jwt_token', return_value=mock_user_payload):
            response = client.post(
                "/api/amazon/publish",
                headers={"Authorization": mock_token},
                json=request_data
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data['success'] is True
            assert data['async_mode'] is True
            assert 'session_id' in data
            assert data['message'] == 'Publication started in background'

    def test_get_monitoring_data(self, client, mock_token, mock_user_payload):
        """Test récupération données monitoring"""
        
        mock_monitoring_data = {
            'user_id': mock_user_payload['user_id'],
            'session_filter': None,
            'total_entries': 0,
            'entries': [],
            'summary': {
                'scraping_operations': 5,
                'seo_optimizations': 3,
                'price_optimizations': 2,
                'publications': 1,
                'success_rate': 95
            },
            'last_24h_activity': {
                'operations_count': 11,
                'avg_response_time': 2.3,
                'error_rate': 5
            },
            'queried_at': datetime.utcnow().isoformat()
        }
        
        with patch('modules.security.verify_jwt_token', return_value=mock_user_payload):
            response = client.get(
                "/api/amazon/monitoring?limit=20",
                headers={"Authorization": mock_token}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data['success'] is True
            assert 'monitoring_data' in data
            
            monitoring = data['monitoring_data']
            assert monitoring['user_id'] == mock_user_payload['user_id']
            assert 'summary' in monitoring
            assert 'last_24h_activity' in monitoring

    def test_get_session_status(self, client, mock_token, mock_user_payload):
        """Test récupération statut session"""
        
        session_id = 'pub_test_user_123_1640995200'
        
        mock_session_status = {
            'session_id': session_id,
            'status': 'completed',
            'message': 'Publication completed successfully'
        }
        
        with patch('modules.security.verify_jwt_token', return_value=mock_user_payload):
            with patch('services.amazon_publisher_service.AmazonPublisherService.get_publication_status',
                      return_value=mock_session_status):
                
                response = client.get(
                    f"/api/amazon/monitoring/session/{session_id}",
                    headers={"Authorization": mock_token}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data['success'] is True
                assert data['session_status']['session_id'] == session_id
                assert data['session_status']['status'] == 'completed'

    def test_cancel_publication_session(self, client, mock_token, mock_user_payload):
        """Test annulation session publication"""
        
        session_id = 'pub_test_user_123_1640995201'
        
        mock_cancellation_result = {
            'session_id': session_id,
            'cancelled': True,
            'message': 'Publication cancelled successfully'
        }
        
        with patch('modules.security.verify_jwt_token', return_value=mock_user_payload):
            with patch('services.amazon_publisher_service.AmazonPublisherService.cancel_publication',
                      return_value=mock_cancellation_result):
                
                response = client.post(
                    f"/api/amazon/monitoring/session/{session_id}/cancel",
                    headers={"Authorization": mock_token}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data['success'] is True
                assert data['cancellation_result']['cancelled'] is True

    # Tests d'erreurs

    def test_scrape_product_missing_asin(self, client, mock_token, mock_user_payload):
        """Test scraping sans ASIN"""
        
        with patch('modules.security.verify_jwt_token', return_value=mock_user_payload):
            response = client.get(
                "/api/amazon/scraping/?marketplace=FR",  # ASIN manquant
                headers={"Authorization": mock_token}
            )
            
            assert response.status_code == 404  # Route pas trouvée sans ASIN

    def test_seo_optimize_missing_data(self, client, mock_token, mock_user_payload):
        """Test optimisation SEO sans données"""
        
        request_data = {}  # Données manquantes
        
        with patch('modules.security.verify_jwt_token', return_value=mock_user_payload):
            response = client.post(
                "/api/amazon/seo/optimize",
                headers={"Authorization": mock_token},
                json=request_data
            )
            
            assert response.status_code == 400
            data = response.json()
            assert 'scraped_data is required' in data['detail']

    def test_price_optimize_missing_product_data(self, client, mock_token, mock_user_payload):
        """Test optimisation prix sans données produit"""
        
        request_data = {
            'competitor_prices': [],
            'target_marketplace': 'FR'
        }  # product_data manquant
        
        with patch('modules.security.verify_jwt_token', return_value=mock_user_payload):
            response = client.post(
                "/api/amazon/price/optimize",
                headers={"Authorization": mock_token},
                json=request_data
            )
            
            assert response.status_code == 400
            data = response.json()
            assert 'product_data is required' in data['detail']

    def test_publish_missing_marketplace(self, client, mock_token, mock_user_payload):
        """Test publication sans marketplace"""
        
        request_data = {
            'updates': [{'sku': 'TEST-001'}],
            'update_type': 'full_update'
        }  # marketplace_id manquant
        
        with patch('modules.security.verify_jwt_token', return_value=mock_user_payload):
            response = client.post(
                "/api/amazon/publish",
                headers={"Authorization": mock_token},
                json=request_data
            )
            
            assert response.status_code == 400
            data = response.json()
            assert 'marketplace_id is required' in data['detail']

    def test_unauthorized_access(self, client):
        """Test accès non autorisé"""
        
        response = client.get("/api/amazon/scraping/B0CHX1W2Y8")
        
        assert response.status_code == 403  # Pas de token fourni

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])