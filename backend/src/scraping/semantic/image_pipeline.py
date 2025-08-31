"""
Image Pipeline - Fetch, optimize, et persistence des images - ECOMSIMPLY
"""

import asyncio
import hashlib
import time
from io import BytesIO
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
import logging

import httpx
from PIL import Image, ImageOps
from PIL.Image import Image as PILImage

from .product_dto import ImageDTO
from ..transport import RequestCoordinator

logger = logging.getLogger(__name__)


class ImageOptimizer:
    """Optimise images pour le web (WEBP + JPEG fallback)"""
    
    def __init__(self):
        self.max_dimension = 1600  # Taille max côté 
        self.webp_quality = 80
        self.jpeg_quality = 85
        self.max_file_size = 10 * 1024 * 1024  # 10MB limit
    
    def optimize_image(self, image_bytes: bytes, original_url: str) -> Optional[Dict[str, Any]]:
        """
        Optimise image bytes → WEBP + JPEG fallback
        
        Returns:
            {
                'webp_data': bytes,
                'jpeg_data': bytes,
                'width': int,
                'height': int,
                'original_size': int,
                'optimized_size': int
            }
        """
        try:
            if len(image_bytes) > self.max_file_size:
                logger.warning(f"Image trop volumineuse: {len(image_bytes)} bytes depuis {original_url}")
                return None
            
            # Ouvrir image
            with Image.open(BytesIO(image_bytes)) as img:
                # Convertir RGBA → RGB si nécessaire
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Fond blanc pour transparence
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                original_size = len(image_bytes)
                original_width, original_height = img.size
                
                # Redimensionner si nécessaire
                if max(img.size) > self.max_dimension:
                    img = ImageOps.exif_transpose(img)  # Fix orientation EXIF
                    img.thumbnail((self.max_dimension, self.max_dimension), Image.Resampling.LANCZOS)
                
                final_width, final_height = img.size
                
                # Générer WEBP
                webp_buffer = BytesIO()
                img.save(webp_buffer, format='WEBP', quality=self.webp_quality, optimize=True)
                webp_data = webp_buffer.getvalue()
                
                # Générer JPEG fallback
                jpeg_buffer = BytesIO()
                img.save(jpeg_buffer, format='JPEG', quality=self.jpeg_quality, optimize=True)
                jpeg_data = jpeg_buffer.getvalue()
                
                optimized_size = len(webp_data)  # Taille WEBP comme référence
                
                logger.info(
                    f"Image optimisée: {original_width}x{original_height} → {final_width}x{final_height}, "
                    f"{original_size} → {optimized_size} bytes ({optimized_size/original_size*100:.1f}%)"
                )
                
                return {
                    'webp_data': webp_data,
                    'jpeg_data': jpeg_data,
                    'width': final_width,
                    'height': final_height,
                    'original_size': original_size,
                    'optimized_size': optimized_size
                }
                
        except Exception as e:
            logger.error(f"Erreur optimisation image depuis {original_url}: {e}")
            return None


class ImagePersistence:
    """Mock persistence - simule stockage images et retourne URLs HTTPS"""
    
    def __init__(self, base_storage_url: str = "https://cdn.ecomsimply.com/images"):
        self.base_storage_url = base_storage_url.rstrip('/')
        self.stored_images = {}  # Mock storage en mémoire
    
    def generate_image_urls(self, image_hash: str, optimized_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Simule stockage et génère URLs HTTPS pour WEBP + JPEG
        
        Returns:
            {
                'webp_url': 'https://cdn.ecomsimply.com/images/abc123.webp',
                'jpeg_url': 'https://cdn.ecomsimply.com/images/abc123.jpg',
                'original_url': 'https://cdn.ecomsimply.com/images/abc123.original'
            }
        """
        webp_url = f"{self.base_storage_url}/{image_hash}.webp"
        jpeg_url = f"{self.base_storage_url}/{image_hash}.jpg"
        original_url = f"{self.base_storage_url}/{image_hash}.original"
        
        # Mock storage
        self.stored_images[image_hash] = {
            'webp_data': optimized_data['webp_data'],
            'jpeg_data': optimized_data['jpeg_data'],
            'metadata': {
                'width': optimized_data['width'],
                'height': optimized_data['height'],
                'original_size': optimized_data['original_size'],
                'optimized_size': optimized_data['optimized_size']
            }
        }
        
        return {
            'webp_url': webp_url,
            'jpeg_url': jpeg_url,
            'original_url': original_url
        }


class ImagePipeline:
    """Pipeline complet pour traitement images asynchrone"""
    
    def __init__(self, coordinator: RequestCoordinator):
        self.coordinator = coordinator
        self.optimizer = ImageOptimizer()
        self.persistence = ImagePersistence()
        self.fetch_timeout = 10.0  # Timeout fetch image
        
        # Concurrence limitée pour images (max 3 simultanées)
        self.image_semaphore = asyncio.Semaphore(3)
    
    async def process_image_urls(self, image_urls: List[str]) -> List[ImageDTO]:
        """
        Traite liste URLs images → ImageDTO validées
        
        Pipeline: fetch → validate → optimize → persist → DTO
        """
        if not image_urls:
            logger.warning("Aucune URL image à traiter")
            return []
        
        logger.info(f"Démarrage traitement {len(image_urls)} images")
        start_time = time.time()
        
        # Traitement concurrent avec limite
        tasks = [
            self._process_single_image(url) 
            for url in image_urls
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrer résultats valides
        valid_images = []
        for result in results:
            if isinstance(result, ImageDTO):
                valid_images.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Erreur traitement image: {result}")
        
        duration = time.time() - start_time
        logger.info(
            f"Traitement images terminé: {len(image_urls)} brutes → {len(valid_images)} valides "
            f"en {duration:.2f}s"
        )
        
        return valid_images
    
    async def _process_single_image(self, image_url: str) -> Optional[ImageDTO]:
        """Traite une image individuelle avec contrôle concurrence"""
        
        async with self.image_semaphore:  # Limite concurrence
            return await self._fetch_and_process_image(image_url)
    
    async def _fetch_and_process_image(self, image_url: str) -> Optional[ImageDTO]:
        """Pipeline complet pour une image"""
        
        try:
            # 1. Fetch image
            image_bytes = await self._fetch_image_bytes(image_url)
            if not image_bytes:
                return None
            
            # 2. Validate content type
            if not self._is_valid_image_content(image_bytes):
                logger.warning(f"Contenu non-image détecté: {image_url}")
                return None
            
            # 3. Optimize
            optimized_data = self.optimizer.optimize_image(image_bytes, image_url)
            if not optimized_data:
                return None
            
            # 4. Generate storage URLs
            image_hash = hashlib.sha256(image_bytes).hexdigest()[:16]
            storage_urls = self.persistence.generate_image_urls(image_hash, optimized_data)
            
            # 5. Generate alt text
            alt_text = self._generate_alt_text(image_url, optimized_data)
            
            # 6. Create DTO (utilise WEBP URL en priorité)
            return ImageDTO(
                url=storage_urls['webp_url'],  # WEBP en priorité
                alt=alt_text,
                width=optimized_data['width'],
                height=optimized_data['height'],
                size_bytes=optimized_data['optimized_size']
            )
            
        except Exception as e:
            logger.error(f"Erreur pipeline image {image_url}: {e}")
            return None
    
    async def _fetch_image_bytes(self, image_url: str) -> Optional[bytes]:
        """Fetch bytes image avec timeout"""
        
        try:
            headers = {
                'User-Agent': 'ECOMSIMPLY-ImageBot/1.0',
                'Accept': 'image/*,*/*;q=0.8'
            }
            
            response = await self.coordinator.get(
                image_url, 
                headers=headers,
                use_cache=False  # Pas de cache pour images
            )
            
            if response.status_code != 200:
                logger.warning(f"Status {response.status_code} pour image: {image_url}")
                return None
            
            return response.content
            
        except Exception as e:
            logger.error(f"Erreur fetch image {image_url}: {e}")
            return None
    
    def _is_valid_image_content(self, content_bytes: bytes) -> bool:
        """Valide que les bytes sont bien une image"""
        
        if not content_bytes or len(content_bytes) < 100:
            return False
        
        # Vérifier signatures images communes
        image_signatures = [
            b'\xFF\xD8\xFF',      # JPEG
            b'\x89PNG\r\n\x1A\n', # PNG
            b'GIF87a',            # GIF87a
            b'GIF89a',            # GIF89a
            b'RIFF',              # WEBP (contient RIFF)
            b'\x00\x00\x01\x00', # ICO
            b'BM',                # BMP
        ]
        
        content_start = content_bytes[:16]
        
        for signature in image_signatures:
            if content_start.startswith(signature):
                return True
        
        # Vérifier WEBP plus spécifiquement
        if content_start.startswith(b'RIFF') and b'WEBP' in content_bytes[:20]:
            return True
        
        # Vérifier Content-Type si pas de signature (très basique)
        if b'<html' in content_start.lower() or b'<!doctype' in content_start.lower():
            return False
        
        return True
    
    def _generate_alt_text(self, original_url: str, optimized_data: Dict[str, Any]) -> str:
        """Génère texte alternatif basique depuis URL"""
        
        # Extraire nom fichier
        parsed = urlparse(original_url)
        filename = parsed.path.split('/')[-1]
        
        if filename:
            # Nettoyer extension et caractères
            name = filename.split('.')[0]
            name = name.replace('_', ' ').replace('-', ' ')
            name = ' '.join(word.capitalize() for word in name.split() if word)
            
            if name and len(name) > 2:
                return f"Image produit: {name}"
        
        # Fallback générique
        width = optimized_data.get('width', 0)
        height = optimized_data.get('height', 0)
        return f"Image produit optimisée {width}x{height}"