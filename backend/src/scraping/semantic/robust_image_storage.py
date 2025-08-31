"""
Système de stockage d'images robuste avec URLs stables HTTPS - ECOMSIMPLY
"""

import asyncio
import hashlib
import os
import time
from io import BytesIO
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse, urljoin
import logging

import httpx
from PIL import Image, ImageOps
from PIL.Image import Image as PILImage

logger = logging.getLogger(__name__)


class ImageStorageSystem:
    """Système de stockage d'images avec URLs stables HTTPS et CDN"""
    
    def __init__(self, storage_config: Optional[Dict] = None):
        """
        Args:
            storage_config: Configuration stockage (S3, local, CDN)
        """
        self.config = storage_config or {
            "type": "local_cdn_mock",
            "base_url": "https://cdn.ecomsimply.com/images",
            "storage_path": "/app/backend/storage/images",
            "max_file_size": 10 * 1024 * 1024,  # 10MB
            "supported_formats": ["JPEG", "PNG", "WEBP", "GIF"]
        }
        
        # Créer dossier stockage si local
        if self.config["type"] == "local_cdn_mock":
            os.makedirs(self.config["storage_path"], exist_ok=True)
        
        # Mapping format → extension
        self.format_extensions = {
            "WEBP": "webp",
            "JPEG": "jpg", 
            "PNG": "png",
            "GIF": "gif"
        }
        
        # Images par défaut pour fallback
        self.fallback_images = {
            "product": "https://via.placeholder.com/800x600/f0f0f0/666666?text=Produit",
            "electronics": "https://via.placeholder.com/800x600/e3f2fd/1976d2?text=Électronique",
            "fashion": "https://via.placeholder.com/800x600/fce4ec/c2185b?text=Mode",
            "home": "https://via.placeholder.com/800x600/e8f5e8/4caf50?text=Maison"
        }
    
    async def store_image_with_fallback(self, image_url: str, product_context: Dict = None) -> Dict[str, Any]:
        """
        Stockage robuste avec fallback automatique
        
        Returns:
            {
                'status': 'success|fallback|error',
                'webp_url': 'https://...',
                'jpg_url': 'https://...',  
                'original_url': 'https://...',
                'metadata': {...}
            }
        """
        
        try:
            logger.info(f"🖼️  Stockage image robuste: {image_url}")
            
            # 1. Tentative stockage normal
            result = await self._store_image_primary(image_url, product_context)
            if result['status'] == 'success':
                return result
            
            # 2. Fallback si échec
            logger.warning(f"⚠️ Échec stockage primaire, fallback: {result.get('error')}")
            return await self._store_fallback_image(image_url, product_context)
            
        except Exception as e:
            logger.error(f"❌ Erreur stockage image {image_url}: {e}")
            return await self._store_fallback_image(image_url, product_context)
    
    async def _store_image_primary(self, image_url: str, product_context: Dict = None) -> Dict[str, Any]:
        """Tentative de stockage principal"""
        
        try:
            # Fetch image bytes
            image_bytes = await self._fetch_image_bytes(image_url)
            if not image_bytes:
                return {'status': 'error', 'error': 'Échec fetch bytes'}
            
            # Validation et optimisation
            optimized_images = await self._optimize_multi_format(image_bytes, image_url)
            if not optimized_images:
                return {'status': 'error', 'error': 'Échec optimisation'}
            
            # Génération URLs stables
            image_hash = self._generate_stable_hash(image_url, product_context)
            urls = await self._store_optimized_images(image_hash, optimized_images)
            
            return {
                'status': 'success',
                'webp_url': urls['webp'],
                'jpg_url': urls['jpg'],
                'original_url': urls['original'], 
                'metadata': {
                    'hash': image_hash,
                    'source_url': image_url,
                    'optimized_formats': list(optimized_images.keys()),
                    'file_sizes': {fmt: len(data) for fmt, data in optimized_images.items()},
                    'storage_type': self.config['type']
                }
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def _store_fallback_image(self, original_url: str, product_context: Dict = None) -> Dict[str, Any]:
        """Fallback avec image par défaut catégorisée"""
        
        # Déterminer catégorie pour fallback approprié
        category = self._detect_image_category(original_url, product_context)
        fallback_url = self.fallback_images.get(category, self.fallback_images['product'])
        
        # Hash stable pour fallback aussi
        fallback_hash = self._generate_stable_hash(original_url, product_context, suffix="_fallback")
        
        logger.info(f"🔄 Fallback image catégorie '{category}': {fallback_url}")
        
        return {
            'status': 'fallback',
            'webp_url': fallback_url.replace('via.placeholder.com', 'cdn.ecomsimply.com'),
            'jpg_url': fallback_url,
            'original_url': fallback_url,
            'metadata': {
                'hash': fallback_hash,
                'fallback_category': category,
                'original_failed_url': original_url,
                'fallback_reason': 'Source image inaccessible'
            }
        }
    
    async def _fetch_image_bytes(self, image_url: str, timeout: int = 10) -> Optional[bytes]:
        """Fetch robuste des bytes image"""
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Referer': urlparse(image_url).scheme + '://' + urlparse(image_url).netloc
            }
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(image_url, headers=headers, follow_redirects=True)
                
                if response.status_code != 200:
                    logger.warning(f"Status {response.status_code} pour image: {image_url}")
                    return None
                
                # Vérifier taille
                content_length = len(response.content)
                if content_length > self.config["max_file_size"]:
                    logger.warning(f"Image trop volumineuse: {content_length} bytes")
                    return None
                
                # Vérifier Content-Type
                content_type = response.headers.get('content-type', '').lower()
                if not content_type.startswith('image/'):
                    logger.warning(f"Content-Type non-image: {content_type}")
                    return None
                
                return response.content
                
        except Exception as e:
            logger.error(f"Erreur fetch image {image_url}: {e}")
            return None
    
    async def _optimize_multi_format(self, image_bytes: bytes, source_url: str) -> Optional[Dict[str, bytes]]:
        """Optimisation multi-format (WEBP + JPEG) avec validation"""
        
        try:
            # Validation basique
            if not self._is_valid_image_data(image_bytes):
                return None
            
            with Image.open(BytesIO(image_bytes)) as img:
                # Conversion RGB si nécessaire
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Fond blanc pour transparence
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode in ('RGBA', 'LA'):
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Orientation EXIF
                img = ImageOps.exif_transpose(img)
                
                # Redimensionnement intelligent
                img = self._smart_resize(img)
                
                optimized_formats = {}
                
                # WEBP (priorité)
                webp_buffer = BytesIO()
                img.save(webp_buffer, format='WEBP', quality=80, optimize=True, method=6)
                optimized_formats['webp'] = webp_buffer.getvalue()
                
                # JPEG (fallback)
                jpeg_buffer = BytesIO()
                img.save(jpeg_buffer, format='JPEG', quality=85, optimize=True)
                optimized_formats['jpg'] = jpeg_buffer.getvalue()
                
                # Statistiques optimisation
                original_size = len(image_bytes)
                webp_size = len(optimized_formats['webp'])
                jpeg_size = len(optimized_formats['jpg'])
                
                logger.info(
                    f"✨ Optimisation réussie {source_url}: "
                    f"{original_size} → WEBP:{webp_size} ({webp_size/original_size*100:.1f}%), "
                    f"JPEG:{jpeg_size} ({jpeg_size/original_size*100:.1f}%)"
                )
                
                return optimized_formats
                
        except Exception as e:
            logger.error(f"Erreur optimisation {source_url}: {e}")
            return None
    
    def _smart_resize(self, img: PILImage, max_dimension: int = 1600) -> PILImage:
        """Redimensionnement intelligent préservant qualité"""
        
        width, height = img.size
        
        if max(width, height) <= max_dimension:
            return img  # Pas besoin de redimensionner
        
        # Calculer nouvelles dimensions en préservant ratio
        if width > height:
            new_width = max_dimension
            new_height = int((height * max_dimension) / width)
        else:
            new_height = max_dimension  
            new_width = int((width * max_dimension) / height)
        
        # Redimensionnement avec qualité Lanczos
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def _is_valid_image_data(self, data: bytes) -> bool:
        """Validation rapide données image"""
        
        if len(data) < 100:  # Trop petit
            return False
        
        # Signatures images
        signatures = [
            b'\xFF\xD8\xFF',      # JPEG
            b'\x89PNG\r\n\x1A\n', # PNG  
            b'GIF87a', b'GIF89a', # GIF
            b'RIFF'               # WEBP (contient RIFF)
        ]
        
        header = data[:16]
        for sig in signatures:
            if header.startswith(sig):
                return True
        
        # WEBP spécifique
        if header.startswith(b'RIFF') and b'WEBP' in data[:20]:
            return True
        
        return False
    
    def _generate_stable_hash(self, image_url: str, product_context: Dict = None, suffix: str = "") -> str:
        """Génère hash stable pour URLs permanentes"""
        
        # Éléments pour hash stable
        hash_elements = [
            image_url.strip(),
            str(product_context.get('product_name', '')) if product_context else '',
            str(product_context.get('source_url', '')) if product_context else '', 
            suffix
        ]
        
        hash_string = '|'.join(hash_elements)
        stable_hash = hashlib.sha256(hash_string.encode('utf-8')).hexdigest()[:16]
        
        return stable_hash
    
    async def _store_optimized_images(self, image_hash: str, optimized_images: Dict[str, bytes]) -> Dict[str, str]:
        """Stockage des images optimisées avec URLs stables"""
        
        base_url = self.config["base_url"]
        urls = {}
        
        # Stockage selon type configuré
        if self.config["type"] == "local_cdn_mock":
            # Simulation stockage local avec URLs CDN
            storage_path = self.config["storage_path"]
            
            for format_name, image_data in optimized_images.items():
                ext = self.format_extensions.get(format_name.upper(), format_name.lower())
                filename = f"{image_hash}.{ext}"
                filepath = os.path.join(storage_path, filename)
                
                # Sauvegarde fichier
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                
                # URL stable HTTPS  
                urls[format_name.lower()] = f"{base_url}/{filename}"
            
            # URL original (pointe vers WEBP)
            urls['original'] = urls.get('webp', urls.get('jpg'))
            
        else:
            # Implémentations futures : S3, GCP, Azure...
            pass
        
        logger.debug(f"💾 Images stockées avec hash {image_hash}: {list(urls.keys())}")
        return urls
    
    def _detect_image_category(self, image_url: str, product_context: Dict = None) -> str:
        """Détection catégorie pour fallback approprié"""
        
        # Depuis contexte produit
        if product_context:
            category = product_context.get('category', '').lower()
            if 'électronique' in category or 'tech' in category:
                return 'electronics'
            elif 'mode' in category or 'vêtement' in category:
                return 'fashion' 
            elif 'maison' in category or 'déco' in category:
                return 'home'
        
        # Depuis URL image
        url_lower = image_url.lower()
        if any(word in url_lower for word in ['phone', 'laptop', 'electronic', 'tech']):
            return 'electronics'
        elif any(word in url_lower for word in ['fashion', 'clothes', 'shirt', 'dress']):
            return 'fashion'
        elif any(word in url_lower for word in ['home', 'furniture', 'kitchen']):
            return 'home'
        
        return 'product'  # Défaut
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Statistiques système de stockage"""
        
        stats = {
            "config_type": self.config["type"],
            "base_url": self.config["base_url"],
            "max_file_size_mb": self.config["max_file_size"] / (1024 * 1024)
        }
        
        # Stats stockage local
        if self.config["type"] == "local_cdn_mock":
            storage_path = self.config["storage_path"]
            if os.path.exists(storage_path):
                files = os.listdir(storage_path)
                total_size = sum(
                    os.path.getsize(os.path.join(storage_path, f)) 
                    for f in files if os.path.isfile(os.path.join(storage_path, f))
                )
                
                stats.update({
                    "stored_files": len(files),
                    "total_size_mb": total_size / (1024 * 1024),
                    "webp_files": len([f for f in files if f.endswith('.webp')]),
                    "jpg_files": len([f for f in files if f.endswith('.jpg')])
                })
        
        return stats