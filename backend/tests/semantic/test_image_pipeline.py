"""
Tests pour ImagePipeline - fetch, optimize, et persistence images
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from io import BytesIO
from PIL import Image

# Import du module à tester
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from scraping.semantic.image_pipeline import ImageOptimizer, ImagePersistence, ImagePipeline
from scraping.semantic.product_dto import ImageDTO
from scraping.transport import RequestCoordinator


class TestImageOptimizer:
    """Tests pour la classe ImageOptimizer"""
    
    @pytest.fixture
    def optimizer(self):
        return ImageOptimizer()
    
    def test_optimize_image_basic(self, optimizer):
        """Test optimisation image basique"""
        # Créer une image test PNG 2000x1500
        img = Image.new('RGB', (2000, 1500), color='red')
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        image_bytes = img_buffer.getvalue()
        
        result = optimizer.optimize_image(image_bytes, "https://example.com/test.png")
        
        assert result is not None
        assert 'webp_data' in result
        assert 'jpeg_data' in result
        assert result['width'] <= optimizer.max_dimension
        assert result['height'] <= optimizer.max_dimension
        assert result['optimized_size'] < result['original_size']
        assert len(result['webp_data']) > 0
        assert len(result['jpeg_data']) > 0
    
    def test_optimize_image_resize_large(self, optimizer):
        """Test redimensionnement images trop grandes"""
        # Image 3000x2000 → doit être redimensionnée à ≤1600px
        img = Image.new('RGB', (3000, 2000), color='blue')
        img_buffer = BytesIO()
        img.save(img_buffer, format='JPEG')
        image_bytes = img_buffer.getvalue()
        
        result = optimizer.optimize_image(image_bytes, "https://example.com/large.jpg")
        
        assert result is not None
        assert max(result['width'], result['height']) <= optimizer.max_dimension
        # Conserver ratio aspect
        assert abs((result['width'] / result['height']) - (3000 / 2000)) < 0.01
    
    def test_optimize_image_small_no_resize(self, optimizer):
        """Test pas de redimensionnement pour petites images"""
        # Image 800x600 → pas de redimensionnement
        original_size = (800, 600)
        img = Image.new('RGB', original_size, color='green')
        img_buffer = BytesIO()
        img.save(img_buffer, format='JPEG')
        image_bytes = img_buffer.getvalue()
        
        result = optimizer.optimize_image(image_bytes, "https://example.com/small.jpg")
        
        assert result is not None
        assert result['width'] == original_size[0]
        assert result['height'] == original_size[1]
    
    def test_optimize_image_rgba_to_rgb(self, optimizer):
        """Test conversion RGBA → RGB avec fond blanc"""
        # Image PNG avec transparence
        img = Image.new('RGBA', (400, 300), color=(255, 0, 0, 128))  # Rouge semi-transparent
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        image_bytes = img_buffer.getvalue()
        
        result = optimizer.optimize_image(image_bytes, "https://example.com/transparent.png")
        
        assert result is not None
        # Vérifier que WEBP et JPEG sont générés (pas de transparence)
        assert len(result['webp_data']) > 0
        assert len(result['jpeg_data']) > 0
    
    def test_optimize_image_too_large_rejected(self, optimizer):
        """Test rejet images trop volumineuses (>10MB)"""
        # Simuler image très volumineuse
        large_bytes = b'fake_image_data' * (optimizer.max_file_size // 10 + 1)
        
        result = optimizer.optimize_image(large_bytes, "https://example.com/huge.jpg")
        
        assert result is None
    
    def test_optimize_image_invalid_format(self, optimizer):
        """Test rejet format image invalide"""
        # Bytes non-image
        invalid_bytes = b"This is not an image"
        
        result = optimizer.optimize_image(invalid_bytes, "https://example.com/fake.jpg")
        
        assert result is None
    
    def test_optimize_image_corrupted_data(self, optimizer):
        """Test gestion données corrompues"""
        # Début de JPEG valide puis corruption
        corrupted_bytes = b'\xFF\xD8\xFF\xE0' + b'corrupted_data' * 100
        
        result = optimizer.optimize_image(corrupted_bytes, "https://example.com/corrupted.jpg")
        
        assert result is None


class TestImagePersistence:
    """Tests pour la classe ImagePersistence"""
    
    @pytest.fixture
    def persistence(self):
        return ImagePersistence("https://cdn.test.com/images")
    
    def test_generate_image_urls(self, persistence):
        """Test génération URLs images"""
        image_hash = "abc123def456"
        optimized_data = {
            'webp_data': b'fake_webp_data',
            'jpeg_data': b'fake_jpeg_data',
            'width': 800,
            'height': 600,
            'original_size': 50000,
            'optimized_size': 25000
        }
        
        urls = persistence.generate_image_urls(image_hash, optimized_data)
        
        assert urls['webp_url'] == "https://cdn.test.com/images/abc123def456.webp"
        assert urls['jpeg_url'] == "https://cdn.test.com/images/abc123def456.jpg"
        assert urls['original_url'] == "https://cdn.test.com/images/abc123def456.original"
        
        # Vérifier stockage mock
        assert image_hash in persistence.stored_images
        assert persistence.stored_images[image_hash]['webp_data'] == b'fake_webp_data'


class TestImagePipeline:
    """Tests pour la classe ImagePipeline"""
    
    @pytest_asyncio.fixture
    async def coordinator(self):
        """Mock RequestCoordinator"""
        coordinator = Mock(spec=RequestCoordinator)
        coordinator.get = AsyncMock()
        return coordinator
    
    @pytest.fixture
    def pipeline(self, coordinator):
        return ImagePipeline(coordinator)
    
    @pytest.mark.asyncio
    async def test_fetch_image_bytes_success(self, pipeline):
        """Test fetch image bytes succès"""
        # Mock réponse HTTP 200 avec bytes image
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'\xFF\xD8\xFF\xE0fake_jpeg_data'  # Début JPEG
        
        pipeline.coordinator.get.return_value = mock_response
        
        result = await pipeline._fetch_image_bytes("https://example.com/image.jpg")
        
        assert result == b'\xFF\xD8\xFF\xE0fake_jpeg_data'
        pipeline.coordinator.get.assert_called_once()
        call_args = pipeline.coordinator.get.call_args
        assert call_args[0][0] == "https://example.com/image.jpg"
        assert call_args[1]['use_cache'] is False  # Pas de cache pour images
    
    @pytest.mark.asyncio
    async def test_fetch_image_bytes_http_error(self, pipeline):
        """Test fetch image avec erreur HTTP"""
        mock_response = Mock()
        mock_response.status_code = 404
        
        pipeline.coordinator.get.return_value = mock_response
        
        result = await pipeline._fetch_image_bytes("https://example.com/missing.jpg")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_fetch_image_bytes_network_error(self, pipeline):
        """Test fetch image avec erreur réseau"""
        pipeline.coordinator.get.side_effect = Exception("Network error")
        
        result = await pipeline._fetch_image_bytes("https://example.com/image.jpg")
        
        assert result is None
    
    def test_is_valid_image_content_valid_formats(self, pipeline):
        """Test validation contenu image formats valides"""
        # JPEG
        assert pipeline._is_valid_image_content(b'\xFF\xD8\xFF\xE0' + b'jpeg_data') is True
        
        # PNG
        assert pipeline._is_valid_image_content(b'\x89PNG\r\n\x1A\n' + b'png_data') is True
        
        # GIF
        assert pipeline._is_valid_image_content(b'GIF87a' + b'gif_data') is True
        assert pipeline._is_valid_image_content(b'GIF89a' + b'gif_data') is True
        
        # WEBP
        assert pipeline._is_valid_image_content(b'RIFF\x00\x00\x00\x00WEBP' + b'webp_data') is True
    
    def test_is_valid_image_content_invalid_formats(self, pipeline):
        """Test validation contenu non-image"""
        # HTML
        assert pipeline._is_valid_image_content(b'<html><body>Not an image</body></html>') is False
        assert pipeline._is_valid_image_content(b'<!DOCTYPE html>') is False
        
        # Texte plain
        assert pipeline._is_valid_image_content(b'This is just text') is False
        
        # Bytes trop courts
        assert pipeline._is_valid_image_content(b'short') is False
        
        # Bytes vides
        assert pipeline._is_valid_image_content(b'') is False
    
    def test_generate_alt_text_from_filename(self, pipeline):
        """Test génération alt text depuis nom fichier"""
        optimized_data = {'width': 800, 'height': 600}
        
        # Nom fichier descriptif
        alt = pipeline._generate_alt_text("https://example.com/iphone-15-pro-main.jpg", optimized_data)
        assert alt == "Image produit: Iphone 15 Pro Main"
        
        # Nom avec tirets et underscores
        alt = pipeline._generate_alt_text("https://shop.com/product_image_front-view.png", optimized_data)
        assert alt == "Image produit: Product Image Front View"
        
        # URL sans nom fichier descriptif
        alt = pipeline._generate_alt_text("https://cdn.com/img/123.jpg", optimized_data)
        assert alt == "Image produit: 123"
    
    def test_generate_alt_text_fallback(self, pipeline):
        """Test fallback alt text générique"""
        optimized_data = {'width': 1200, 'height': 800}
        
        # URL sans nom fichier
        alt = pipeline._generate_alt_text("https://example.com/", optimized_data)
        assert alt == "Image produit optimisée 1200x800"
        
        # Nom fichier trop court
        alt = pipeline._generate_alt_text("https://example.com/a.jpg", optimized_data)
        assert alt == "Image produit optimisée 1200x800"
    
    @pytest.mark.asyncio
    async def test_process_image_urls_empty_list(self, pipeline):
        """Test traitement liste vide"""
        result = await pipeline.process_image_urls([])
        
        assert result == []
        pipeline.coordinator.get.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_image_urls_concurrency_limit(self, pipeline):
        """Test respect limite concurrence (max 3 images simultanées)"""
        # Vérifier semaphore configuré à 3
        assert pipeline.image_semaphore._value == 3
        
        # Test avec plus de 3 URLs
        image_urls = [f"https://example.com/image{i}.jpg" for i in range(5)]
        
        # Mock fetch pour simuler traitement lent
        async def slow_fetch_mock(url):
            await asyncio.sleep(0.01)  # Petite pause
            return None  # Simuler échec pour simplifier test
        
        with patch.object(pipeline, '_fetch_and_process_image', side_effect=slow_fetch_mock):
            result = await pipeline.process_image_urls(image_urls)
        
        # Le nombre d'appels doit correspondre au nombre d'URLs
        assert pipeline._fetch_and_process_image.call_count == 5
    
    @pytest.mark.asyncio 
    async def test_process_single_image_end_to_end(self, pipeline):
        """Test traitement complet une image (end-to-end mock)"""
        # Mock fetch bytes
        fake_image_bytes = self._create_fake_jpeg_bytes()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = fake_image_bytes
        pipeline.coordinator.get.return_value = mock_response
        
        # Mock optimizer pour retourner données réalistes
        mock_optimized_data = {
            'webp_data': b'fake_webp',
            'jpeg_data': b'fake_jpeg',
            'width': 800,
            'height': 600,
            'original_size': 50000,
            'optimized_size': 25000
        }
        
        with patch.object(pipeline.optimizer, 'optimize_image', return_value=mock_optimized_data):
            result = await pipeline._process_single_image("https://example.com/test.jpg")
        
        assert result is not None
        assert isinstance(result, ImageDTO)
        assert result.url.startswith("https://")
        assert result.url.endswith(".webp")  # WEBP en priorité
        assert result.width == 800
        assert result.height == 600
        assert result.alt.startswith("Image produit:")
    
    def _create_fake_jpeg_bytes(self):
        """Crée des bytes JPEG factices mais valides"""
        # Créer vraie image JPEG
        img = Image.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        return buffer.getvalue()
    
    @pytest.mark.asyncio
    async def test_fetch_and_process_image_invalid_content(self, pipeline):
        """Test rejet contenu non-image"""
        # Mock réponse avec HTML au lieu d'image
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html><body>Not an image</body></html>'
        
        pipeline.coordinator.get.return_value = mock_response
        
        result = await pipeline._fetch_and_process_image("https://example.com/fake.jpg")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_fetch_and_process_image_optimization_failure(self, pipeline):
        """Test échec optimisation image"""
        # Mock fetch réussi
        fake_image_bytes = self._create_fake_jpeg_bytes()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = fake_image_bytes
        pipeline.coordinator.get.return_value = mock_response
        
        # Mock optimizer échec
        with patch.object(pipeline.optimizer, 'optimize_image', return_value=None):
            result = await pipeline._fetch_and_process_image("https://example.com/test.jpg")
        
        assert result is None


class TestImagePipelineIntegration:
    """Tests d'intégration ImagePipeline"""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_multiple_images(self):
        """Test pipeline complet avec plusieurs images (mocks)"""
        # Setup coordinator mock
        coordinator = Mock(spec=RequestCoordinator)
        pipeline = ImagePipeline(coordinator)
        
        # URLs test
        image_urls = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.png",
            "https://example.com/invalid.txt",  # Sera rejetée
        ]
        
        # Mock réponses différentiées
        def mock_get_side_effect(url, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            
            if "image1.jpg" in url:
                mock_response.content = self._create_fake_jpeg_bytes()
            elif "image2.png" in url:
                mock_response.content = self._create_fake_png_bytes()
            else:
                mock_response.content = b"Not an image"
            
            return mock_response
        
        coordinator.get.side_effect = mock_get_side_effect
        
        result = await pipeline.process_image_urls(image_urls)
        
        # 2 images valides sur 3
        assert len(result) == 2
        
        for img_dto in result:
            assert isinstance(img_dto, ImageDTO)
            assert img_dto.url.startswith("https://")
            assert img_dto.width > 0
            assert img_dto.height > 0
            assert len(img_dto.alt) > 0
    
    def _create_fake_jpeg_bytes(self):
        """Crée bytes JPEG factices"""
        img = Image.new('RGB', (400, 300), color='blue')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        return buffer.getvalue()
    
    def _create_fake_png_bytes(self):
        """Crée bytes PNG factices"""
        img = Image.new('RGBA', (300, 200), color=(255, 0, 0, 128))
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()