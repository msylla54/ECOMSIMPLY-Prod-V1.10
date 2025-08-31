"""
Tests end-to-end pour SemanticOrchestrator - pipeline complet
"""

import pytest
import pytest_asyncio
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal

# Import du module à tester
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from scraping.semantic.orchestrator import SemanticOrchestrator
from scraping.semantic.product_dto import ProductDTO, ProductStatus, ImageDTO, PriceDTO, Currency
from scraping.transport import RequestCoordinator


class TestSemanticOrchestrator:
    """Tests pour SemanticOrchestrator"""
    
    @pytest_asyncio.fixture
    async def coordinator(self):
        """Mock RequestCoordinator"""
        coordinator = Mock(spec=RequestCoordinator)
        coordinator.get = AsyncMock()
        coordinator.get_proxy_stats = AsyncMock(return_value={"total_proxies": 0})
        coordinator.get_cache_stats = AsyncMock(return_value={"total_entries": 0})
        coordinator.timeout_s = 10.0
        return coordinator
    
    @pytest.fixture
    def orchestrator(self, coordinator):
        return SemanticOrchestrator(coordinator)
    
    @pytest.mark.asyncio
    async def test_scrape_product_semantic_complete_success(self, orchestrator):
        """Test pipeline complet avec succès total"""
        # Mock HTML response valide
        html_content = """
        <html lang="fr">
            <head>
                <meta property="og:title" content="iPhone 15 Pro 256GB" />
                <meta property="og:description" content="Smartphone premium avec puce A17 Pro" />
                <meta property="og:image" content="/images/iphone-main.jpg" />
            </head>
            <body>
                <div class="price">1 199,00 €</div>
                <img src="/images/iphone-side.jpg" alt="Vue de côté" />
                <div itemprop="brand">Apple</div>
            </body>
        </html>
        """
        
        # Mock coordinator response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_response.headers = {'content-type': 'text/html'}
        orchestrator.coordinator.get.return_value = mock_response
        
        # Mock image processing success
        mock_images = [
            ImageDTO(url="https://cdn.ecomsimply.com/images/abc123.webp", alt="iPhone 15 Pro principal"),
            ImageDTO(url="https://cdn.ecomsimply.com/images/def456.webp", alt="iPhone 15 Pro côté")
        ]
        
        with patch.object(orchestrator.image_pipeline, 'process_image_urls', return_value=mock_images):
            result = await orchestrator.scrape_product_semantic("https://store.apple.com/fr/iphone-15-pro")
        
        # Vérifications
        assert result is not None
        assert isinstance(result, ProductDTO)
        assert result.title == "iPhone 15 Pro 256GB"
        assert "puce A17 Pro" in result.description_html
        assert result.price is not None
        assert result.price.amount == Decimal('1199.00')
        assert result.price.currency == Currency.EUR
        assert len(result.images) == 2
        assert result.status == ProductStatus.COMPLETE
        assert len(result.payload_signature) == 16  # Hash tronqué
        assert result.source_url == "https://store.apple.com/fr/iphone-15-pro"
    
    @pytest.mark.asyncio
    async def test_scrape_product_semantic_http_error(self, orchestrator):
        """Test gestion erreur HTTP"""
        # Mock erreur 404
        mock_response = Mock()
        mock_response.status_code = 404
        orchestrator.coordinator.get.return_value = mock_response
        
        result = await orchestrator.scrape_product_semantic("https://example.com/not-found")
        
        assert result is None
        orchestrator.coordinator.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_scrape_product_semantic_non_html_content(self, orchestrator):
        """Test rejet contenu non-HTML"""
        # Mock réponse JSON au lieu HTML
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        orchestrator.coordinator.get.return_value = mock_response
        
        result = await orchestrator.scrape_product_semantic("https://api.example.com/product.json")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_scrape_product_semantic_network_error(self, orchestrator):
        """Test gestion erreur réseau"""
        # Mock exception réseau
        orchestrator.coordinator.get.side_effect = Exception("Network timeout")
        
        result = await orchestrator.scrape_product_semantic("https://example.com/product")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_scrape_product_semantic_no_valid_images(self, orchestrator):
        """Test produit sans images valides → placeholder"""
        # Mock HTML sans images utilisables
        html_content = """
        <html>
            <head>
                <title>Produit Sans Image</title>
            </head>
            <body>
                <h1>Produit Test</h1>
                <p>Description basique du produit</p>
                <div class="price">€ 99,99</div>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_response.headers = {'content-type': 'text/html; charset=utf-8'}
        orchestrator.coordinator.get.return_value = mock_response
        
        # Mock image processing échec (aucune image valide)
        with patch.object(orchestrator.image_pipeline, 'process_image_urls', return_value=[]):
            result = await orchestrator.scrape_product_semantic("https://example.com/no-images")
        
        # Vérifications placeholder
        assert result is not None
        assert result.status == ProductStatus.INCOMPLETE_MEDIA
        assert len(result.images) == 1
        assert "placeholder.com" in result.images[0].url
        assert result.images[0].alt == "Image produit non disponible"
    
    @pytest.mark.asyncio
    async def test_scrape_product_semantic_no_price_detected(self, orchestrator):
        """Test produit sans prix détecté"""
        html_content = """
        <html>
            <head>
                <title>Produit Sur Devis</title>
                <meta property="og:image" content="/image.jpg" />
            </head>
            <body>
                <h1>Produit Sur Devis</h1>
                <p>Contactez-nous pour le prix</p>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_response.headers = {'content-type': 'text/html'}
        orchestrator.coordinator.get.return_value = mock_response
        
        # Mock image processing avec 1 image valide
        mock_images = [ImageDTO(url="https://cdn.example.com/image.webp", alt="Produit")]
        
        with patch.object(orchestrator.image_pipeline, 'process_image_urls', return_value=mock_images):
            result = await orchestrator.scrape_product_semantic("https://example.com/no-price")
        
        assert result is not None
        assert result.price is None
        assert result.status == ProductStatus.INCOMPLETE_PRICE
        assert len(result.images) == 1
    
    @pytest.mark.asyncio
    async def test_scrape_product_semantic_complex_mixed_case(self, orchestrator):
        """Test cas complexe avec données partielles"""
        html_content = """
        <!DOCTYPE html>
        <html lang="en-US">
            <head>
                <meta property="og:title" content="Samsung Galaxy S24 Ultra" />
                <meta property="og:description" content="Revolutionary smartphone with AI features" />
                <meta property="og:image" content="https://images.samsung.com/main.jpg" />
                <meta property="product:brand" content="Samsung" />
                <meta property="product:price:currency" content="USD" />
            </head>
            <body>
                <div class="product-info">
                    <h1>Samsung Galaxy S24 Ultra 512GB</h1>
                    <div class="price-container">
                        <span class="current-price">$1,299.99</span>
                        <span class="original-price">$1,399.99</span>
                    </div>
                    <div class="images">
                        <img src="/images/galaxy-front.webp" alt="Vue avant" />
                        <img src="/images/galaxy-back.webp" alt="Vue arrière" />
                        <img src="invalid-url" alt="Image cassée" />
                    </div>
                    <div class="specs" itemscope>
                        <span itemprop="model">SM-S928B</span>
                        <span itemprop="sku">SAMS24U512</span>
                        <div itemprop="description">Écran 6.8" Dynamic AMOLED, S Pen inclus</div>
                    </div>
                </div>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_response.headers = {'content-type': 'text/html; charset=utf-8'}
        orchestrator.coordinator.get.return_value = mock_response
        
        # Mock 2 images valides sur 3 (une cassée)
        mock_images = [
            ImageDTO(url="https://cdn.ecomsimply.com/images/front123.webp", alt="Samsung Galaxy S24 Ultra avant"),
            ImageDTO(url="https://cdn.ecomsimply.com/images/back456.webp", alt="Samsung Galaxy S24 Ultra arrière")
        ]
        
        with patch.object(orchestrator.image_pipeline, 'process_image_urls', return_value=mock_images):
            result = await orchestrator.scrape_product_semantic("https://samsung.com/us/galaxy-s24-ultra")
        
        # Vérifications complètes
        assert result is not None
        assert result.title == "Samsung Galaxy S24 Ultra"  # OpenGraph priority
        assert result.price.amount == Decimal('1299.99')
        assert result.price.currency == Currency.USD
        assert len(result.images) == 2
        assert result.status == ProductStatus.COMPLETE
        
        # Vérifier attributs extraits
        assert result.attributes["brand"] == "Samsung"
        assert result.attributes["model"] == "SM-S928B"
        assert result.attributes["sku"] == "SAMS24U512"
        
        # Vérifier métadonnées
        assert result.source_url == "https://samsung.com/us/galaxy-s24-ultra"
        assert len(result.payload_signature) == 16
        assert result.extraction_timestamp > 0
    
    @pytest.mark.asyncio
    async def test_fetch_html_content_headers(self, orchestrator):
        """Test headers HTTP corrects pour scraping"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.headers = {'content-type': 'text/html'}
        orchestrator.coordinator.get.return_value = mock_response
        
        result = await orchestrator._fetch_html_content("https://example.com/product")
        
        assert result == "<html><body>Test</body></html>"
        
        # Vérifier headers envoyés
        call_args = orchestrator.coordinator.get.call_args
        headers = call_args[1]['headers']
        assert 'User-Agent' in headers
        assert 'Mozilla/5.0' in headers['User-Agent']
        assert headers['Accept'].startswith('text/html')
        assert headers['Accept-Language'] == 'fr-FR,fr;q=0.9,en;q=0.8'
        assert call_args[1]['use_cache'] is True  # Cache HTML activé
    
    @pytest.mark.asyncio
    async def test_normalize_parsed_data(self, orchestrator):
        """Test normalisation données parsées"""
        parsed_data = {
            'title': '  iPhone 15 Pro &amp; Accessories  ',
            'description_html': '<div><p>Premium smartphone</p><script>alert("xss")</script></div>',
            'price_text': '€ 1.299,99',
            'currency_hint': 'EUR',
            'image_urls': [
                'http://example.com/image1.jpg',  # HTTP → HTTPS
                'https://example.com/image2.jpg',
                'https://example.com/image2.jpg'   # Doublon
            ],
            'attributes': {
                'Brand': 'Apple',
                'Storage Size': '256 GB'
            }
        }
        
        result = await orchestrator._normalize_parsed_data(parsed_data)
        
        # Vérifications normalisation
        assert result['title'] == 'iPhone 15 Pro & Accessories'  # HTML entities + trim
        assert '<script>' not in result['description_html']  # Sanitization
        assert result['price'].amount == Decimal('1299.99')
        assert result['price'].currency == Currency.EUR
        assert len(result['image_urls']) == 2  # Déduplication + HTTPS
        assert all(url.startswith('https://') for url in result['image_urls'])
        assert result['attributes']['brand'] == 'Apple'  # Clés normalisées
        assert result['attributes']['storage_size'] == '256 GB'
    
    def test_generate_payload_signature(self, orchestrator):
        """Test génération signature idempotence"""
        normalized_data = {
            'title': 'Test Product',
            'description_html': '<p>Description</p>',
            'price': {'amount': '99.99', 'currency': 'EUR'},
            'attributes': {'brand': 'TestBrand', 'model': 'TestModel'}
        }
        image_urls = ['https://example.com/image1.jpg', 'https://example.com/image2.jpg']
        
        signature1 = orchestrator._generate_payload_signature(normalized_data, image_urls)
        signature2 = orchestrator._generate_payload_signature(normalized_data, image_urls)
        
        # Même données → même signature
        assert signature1 == signature2
        assert len(signature1) == 16  # Tronquée à 16 chars
        
        # Données différentes → signature différente
        different_data = normalized_data.copy()
        different_data['title'] = 'Different Title'
        signature3 = orchestrator._generate_payload_signature(different_data, image_urls)
        assert signature3 != signature1
    
    @pytest.mark.asyncio
    async def test_get_orchestrator_stats(self, orchestrator):
        """Test statistiques complètes orchestrator"""
        # Mock stats coordinateur
        orchestrator.coordinator.get_proxy_stats.return_value = {
            "total_proxies": 3,
            "available_proxies": 2
        }
        orchestrator.coordinator.get_cache_stats.return_value = {
            "total_entries": 15,
            "active_entries": 12
        }
        
        # Mock images stockées
        orchestrator.image_pipeline.persistence.stored_images = {
            "img1": {},
            "img2": {},
            "img3": {}
        }
        
        stats = await orchestrator.get_orchestrator_stats()
        
        assert stats['transport_layer']['proxy_stats']['total_proxies'] == 3
        assert stats['transport_layer']['cache_stats']['total_entries'] == 15
        assert stats['image_processing']['stored_images'] == 3
        assert stats['pipeline_config']['fetch_timeout'] == 10.0
        assert stats['pipeline_config']['image_concurrency'] == 3
        assert stats['pipeline_config']['max_images_per_product'] == 8


class TestSemanticOrchestratorEdgeCases:
    """Tests cas limites et erreurs"""
    
    @pytest_asyncio.fixture
    async def coordinator(self):
        coordinator = Mock(spec=RequestCoordinator)
        coordinator.get = AsyncMock()
        coordinator.get_proxy_stats = AsyncMock(return_value={})
        coordinator.get_cache_stats = AsyncMock(return_value={})
        coordinator.timeout_s = 10.0
        return coordinator
    
    @pytest.fixture
    def orchestrator(self, coordinator):
        return SemanticOrchestrator(coordinator)
    
    @pytest.mark.asyncio
    async def test_scrape_product_semantic_empty_html(self, orchestrator):
        """Test HTML complètement vide"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = ""
        mock_response.headers = {'content-type': 'text/html'}
        orchestrator.coordinator.get.return_value = mock_response
        
        result = await orchestrator.scrape_product_semantic("https://example.com/empty")
        
        assert result is not None  # Devrait créer placeholder
        assert result.status == ProductStatus.INCOMPLETE_MEDIA
        assert result.title == "Titre non disponible"
    
    @pytest.mark.asyncio
    async def test_scrape_product_semantic_malformed_html(self, orchestrator):
        """Test HTML malformé"""
        html_content = """
        <html>
            <head>
                <title>Produit Test
            </head>
            <body>
                <h1>Titre Non Fermé
                <p>Description incomplète
                <div class="price">99.99 EUR
        <!-- HTML non fermé proprement -->
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_response.headers = {'content-type': 'text/html'}
        orchestrator.coordinator.get.return_value = mock_response
        
        mock_images = [ImageDTO(url="https://cdn.example.com/img.webp", alt="Test")]
        
        with patch.object(orchestrator.image_pipeline, 'process_image_urls', return_value=mock_images):
            result = await orchestrator.scrape_product_semantic("https://example.com/malformed")
        
        # BeautifulSoup devrait parser même HTML malformé
        assert result is not None
        assert result.title == "Produit Test"  # Titre extrait malgré malformation
    
    @pytest.mark.asyncio
    async def test_build_product_dto_exception_handling(self, orchestrator):
        """Test gestion exception lors construction DTO"""
        normalized_data = {
            'title': 'Test Product',
            'description_html': '<p>Description</p>',
            'price': None,
            'attributes': {}
        }
        
        # Mock images valides
        mock_images = [ImageDTO(url="https://cdn.example.com/img.webp", alt="Test")]
        
        # Forcer exception lors création DTO (données invalides)
        with patch('scraping.semantic.orchestrator.ProductDTO', side_effect=Exception("DTO creation failed")):
            result = await orchestrator._build_product_dto(
                "https://example.com/product",
                normalized_data,
                mock_images,
                time.time()
            )
        
        assert result is None  # Exception gérée gracieusement