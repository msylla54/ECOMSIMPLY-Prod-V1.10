"""
Orchestrator - Pipeline complet scraping sémantique avec SEO et images robustes - ECOMSIMPLY
RequestCoordinator → Parser → Normalizer → ImagePipeline → ProductDTO + SEO + Images robustes
"""

import time
import hashlib
import asyncio
from typing import Optional, Dict, Any
import logging

from .parser import SemanticParser
from .normalizer import DataNormalizer
from .image_pipeline import ImagePipeline
from .product_dto import ProductDTO, ProductStatus, ProductPlaceholder
from .seo_utils import SEOMetaGenerator
from .robust_image_storage import ImageStorageSystem
from ..transport import RequestCoordinator

logger = logging.getLogger(__name__)


class SemanticOrchestrator:
    """Orchestrateur principal du pipeline de scraping sémantique avec SEO et images robustes"""
    
    def __init__(self, coordinator: RequestCoordinator):
        self.coordinator = coordinator
        self.parser = SemanticParser()
        self.normalizer = DataNormalizer()
        self.image_pipeline = ImagePipeline(coordinator)
        
        # Nouveaux composants Phase 1.5
        self.seo_generator = SEOMetaGenerator()
        self.image_storage = ImageStorageSystem()
    
    async def scrape_product_semantic(self, product_url: str) -> Optional[ProductDTO]:
        """
        Pipeline complet avec SEO dynamique et images robustes:
        
        Pipeline:
        1. Fetch HTML (RequestCoordinator)
        2. Parse HTML → données structurées (SemanticParser)
        3. Normalize données → nettoyage (DataNormalizer)  
        4. Process images → optimisation + stockage robuste (ImageStorageSystem)
        5. Generate SEO → métadonnées avec année courante (SEOMetaGenerator)
        6. Build ProductDTO → validation finale avec SEO
        """
        
        start_time = time.time()
        logger.info(f"🔍 Démarrage scraping sémantique + SEO + images robustes: {product_url}")
        
        try:
            # 1. Fetch HTML avec transport robuste
            html_content = await self._fetch_html_content(product_url)
            if not html_content:
                logger.error(f"❌ Échec fetch HTML: {product_url}")
                return None
            
            # 2. Parse HTML → données structurées
            parsed_data = self.parser.parse_html(html_content, product_url)
            logger.debug(f"Parser extractions: title={bool(parsed_data['title'])}, "
                        f"price={bool(parsed_data['price_text'])}, "
                        f"images={len(parsed_data['image_urls'])}")
            
            # 3. Validate qualité extraction
            is_valid, issues = self.normalizer.validate_extraction_quality(parsed_data)
            if issues:
                logger.warning(f"Issues détectées: {issues}")
            
            # 4. Normalize données
            normalized_data = await self._normalize_parsed_data(parsed_data)
            
            # 5. Process images avec stockage robuste + fallback
            valid_images = await self._process_images_robust(
                normalized_data['image_urls'],
                {'product_name': normalized_data['title'], 'source_url': product_url}
            )
            
            # 6. Generate SEO métadonnées avec année courante
            seo_data = await self._generate_seo_metadata(normalized_data, parsed_data)
            
            # 7. Build ProductDTO final avec SEO
            product_dto = await self._build_product_dto_with_seo(
                product_url,
                normalized_data, 
                valid_images,
                seo_data,
                start_time
            )
            
            duration = time.time() - start_time
            if product_dto:
                logger.info(f"✅ Scraping + SEO + images réussi en {duration:.2f}s: {product_dto.title[:50]}... "
                           f"({len(product_dto.images)} images, SEO: {bool(product_dto.seo_title)}, "
                           f"status={product_dto.status.value})")
            
            return product_dto
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ Erreur scraping sémantique + SEO après {duration:.2f}s: {e}")
            return None
    
    async def _fetch_html_content(self, url: str) -> Optional[str]:
        """Fetch HTML avec headers optimisés pour scraping"""
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'max-age=0',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = await self.coordinator.get(
                url,
                headers=headers,
                use_cache=True  # Cache HTML activé
            )
            
            if response.status_code != 200:
                logger.warning(f"Status {response.status_code} pour {url}")
                return None
            
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                logger.warning(f"Content-Type non-HTML: {content_type}")
                return None
            
            return response.text
            
        except Exception as e:
            logger.error(f"Erreur fetch HTML {url}: {e}")
            return None
    
    async def _process_images_robust(self, image_urls: list, product_context: Dict) -> list:
        """Traitement images avec stockage robuste et fallback automatique"""
        
        if not image_urls:
            logger.warning("Aucune URL image à traiter → fallback automatique")
            # Fallback immédiat si pas d'images
            fallback_result = await self.image_storage.store_image_with_fallback(
                "https://placeholder.ecomsimply.com/product.jpg",
                product_context
            )
            
            from .product_dto import ImageDTO
            return [ImageDTO(
                url=fallback_result['webp_url'],
                alt=f"Image {product_context.get('product_name', 'produit')} (fallback)",
                width=800,
                height=600
            )]
        
        logger.info(f"🖼️  Traitement robuste {len(image_urls)} images avec fallback")
        
        # Traitement concurrent des images avec stockage robuste
        tasks = []
        for url in image_urls[:8]:  # Limite 8 max
            tasks.append(self._process_single_image_robust(url, product_context))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collecter images valides
        valid_images = []
        for result in results:
            if isinstance(result, dict) and result.get('image_dto'):
                valid_images.append(result['image_dto'])
            elif isinstance(result, Exception):
                logger.error(f"Erreur traitement image: {result}")
        
        # Garantir au moins 1 image (fallback si nécessaire)
        if not valid_images:
            logger.warning("Aucune image valide → fallback final")
            fallback_result = await self.image_storage.store_image_with_fallback(
                "https://placeholder.ecomsimply.com/product.jpg",
                product_context
            )
            
            from .product_dto import ImageDTO
            valid_images = [ImageDTO(
                url=fallback_result['webp_url'],
                alt=f"Image {product_context.get('product_name', 'produit')} (fallback final)",
                width=800,
                height=600
            )]
        
        logger.info(f"✅ Images robustes: {len(image_urls)} → {len(valid_images)} finales")
        return valid_images
    
    async def _process_single_image_robust(self, image_url: str, product_context: Dict) -> Optional[Dict]:
        """Traite une image avec stockage robuste"""
        
        try:
            # Stockage robuste avec fallback automatique
            storage_result = await self.image_storage.store_image_with_fallback(
                image_url, product_context
            )
            
            if storage_result['status'] in ['success', 'fallback']:
                from .product_dto import ImageDTO
                
                # Générer alt text intelligent
                alt_text = self._generate_smart_alt_text(
                    image_url, 
                    product_context,
                    storage_result
                )
                
                # Créer ImageDTO robuste
                image_dto = ImageDTO(
                    url=storage_result['webp_url'],  # WEBP en priorité
                    alt=alt_text,
                    width=storage_result.get('metadata', {}).get('width', 800),
                    height=storage_result.get('metadata', {}).get('height', 600),
                    size_bytes=storage_result.get('metadata', {}).get('file_sizes', {}).get('webp', 0)
                )
                
                return {
                    'image_dto': image_dto,
                    'storage_result': storage_result
                }
            
        except Exception as e:
            logger.error(f"Erreur traitement image robuste {image_url}: {e}")
        
        return None
    
    def _generate_smart_alt_text(self, image_url: str, product_context: Dict, 
                                storage_result: Dict) -> str:
        """Génère alt text intelligent selon contexte"""
        
        product_name = product_context.get('product_name', 'Produit')
        
        # Si fallback, indiquer type  
        if storage_result['status'] == 'fallback':
            category = storage_result.get('metadata', {}).get('fallback_category', 'produit')
            return f"Image {product_name} - {category.title()}"
        
        # Alt text depuis nom produit + position
        from urllib.parse import urlparse
        parsed = urlparse(image_url)
        filename = parsed.path.split('/')[-1]
        
        if 'main' in filename.lower() or '001' in filename:
            return f"{product_name} - Image principale"
        elif 'back' in filename.lower() or 'rear' in filename.lower():
            return f"{product_name} - Vue arrière"
        elif 'side' in filename.lower() or 'profile' in filename.lower():
            return f"{product_name} - Vue de profil"
        elif 'detail' in filename.lower():
            return f"{product_name} - Détail"
        else:
            return f"Image {product_name}"
    
    async def _generate_seo_metadata(self, normalized_data: Dict, parsed_data: Dict) -> Dict:
        """Génère métadonnées SEO avec année courante"""
        
        product_name = normalized_data.get('title', '')
        price_display = None
        brand = normalized_data.get('attributes', {}).get('brand')
        
        # Formatage prix pour SEO
        if normalized_data.get('price'):
            price = normalized_data['price']
            price_display = f"{price.amount} {price.currency.value}"
        
        # Génération SEO complète
        seo_title = self.seo_generator.generate_seo_title(product_name)
        seo_description = self.seo_generator.generate_seo_description(
            product_name, price_display, brand
        )
        seo_keywords = self.seo_generator.generate_seo_keywords(
            product_name, 
            normalized_data.get('attributes', {}).get('category'),
            brand
        )
        
        # Structured data avec année courante
        structured_data = self.seo_generator.generate_structured_data({
            'name': product_name,
            'description': normalized_data.get('description_html', ''),
            'price': normalized_data.get('price'),
            'images': [],  # Sera rempli après traitement images
            'brand': brand
        })
        
        return {
            'seo_title': seo_title,
            'seo_description': seo_description,
            'seo_keywords': seo_keywords,
            'structured_data': structured_data
        }
    
    async def _normalize_parsed_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Applique toutes les normalisations"""
        
        return {
            'title': self.normalizer.normalize_title(parsed_data['title']),
            'description_html': self.normalizer.normalize_description_html(parsed_data['description_html']),
            'price': self.normalizer.normalize_price(
                parsed_data['price_text'],
                parsed_data['currency_hint']
            ),
            'image_urls': self.normalizer.normalize_image_urls(parsed_data['image_urls']),
            'attributes': self.normalizer.normalize_attributes(parsed_data['attributes'])
        }
    
    async def _build_product_dto_with_seo(
        self,
        source_url: str,
        normalized_data: Dict[str, Any],
        valid_images: list,
        seo_data: Dict,
        start_time: float
    ) -> Optional[ProductDTO]:
        """Construit le ProductDTO final avec SEO et gestion des cas incomplets"""
        
        extraction_timestamp = start_time
        
        # Générer signature idempotence (inclut données SEO)
        payload_signature = self._generate_payload_signature_with_seo(
            normalized_data, 
            [img.url for img in valid_images],
            seo_data
        )
        
        # Cas 1: Aucune image valide → Ne devrait plus arriver grâce au robuste
        if not valid_images:
            logger.warning(f"Aucune image valide pour {source_url} → placeholder avec SEO")
            
            return ProductPlaceholder.create_incomplete_media_product(
                title=normalized_data['title'],
                description_html=normalized_data['description_html'],
                source_url=source_url,
                payload_signature=payload_signature,
                extraction_timestamp=extraction_timestamp,
                price=normalized_data['price'],
                attributes=normalized_data['attributes']
            )
        
        # Cas 2: Produit complet avec SEO
        try:
            status = ProductStatus.COMPLETE
            
            # Ajuster status selon qualité données
            if not normalized_data['price']:
                status = ProductStatus.INCOMPLETE_PRICE
            
            # Construction ProductDTO avec tous les nouveaux champs SEO
            product_dto = ProductDTO(
                title=normalized_data['title'],
                description_html=normalized_data['description_html'],
                price=normalized_data['price'],
                images=valid_images,
                source_url=source_url,
                attributes=normalized_data['attributes'],
                status=status,
                payload_signature=payload_signature,
                extraction_timestamp=extraction_timestamp,
                
                # Nouveaux champs SEO avec année courante
                seo_title=seo_data['seo_title'],
                seo_description=seo_data['seo_description'],
                seo_keywords=seo_data['seo_keywords'],
                structured_data=seo_data['structured_data']
                # current_year est auto-rempli par le default_factory
            )
            
            return product_dto
            
        except Exception as e:
            logger.error(f"Erreur construction ProductDTO avec SEO: {e}")
            return None
    
    def _generate_payload_signature_with_seo(self, normalized_data: Dict, image_urls: list, seo_data: Dict) -> str:
        """Génère signature unique pour idempotence incluant SEO"""
        
        # Construire string déterministe avec SEO
        signature_parts = [
            normalized_data.get('title', ''),
            normalized_data.get('description_html', ''),
            str(normalized_data.get('price', '')),
            '|'.join(sorted(image_urls)),
            str(sorted(normalized_data.get('attributes', {}).items())),
            seo_data.get('seo_title', ''),
            '|'.join(sorted(seo_data.get('seo_keywords', [])))
        ]
        
        signature_string = '|||'.join(signature_parts)
        return hashlib.sha256(signature_string.encode('utf-8')).hexdigest()[:16]

    async def _build_product_dto(
        self,
        source_url: str,
        normalized_data: Dict[str, Any],
        valid_images: list,
        start_time: float
    ) -> Optional[ProductDTO]:
        """Construit le ProductDTO final avec gestion des cas incomplets"""
        
        extraction_timestamp = start_time
        
        # Générer signature idempotence
        payload_signature = self._generate_payload_signature(
            normalized_data, 
            [img.url for img in valid_images]
        )
        
        # Cas 1: Aucune image valide → Placeholder
        if not valid_images:
            logger.warning(f"Aucune image valide pour {source_url} → placeholder")
            
            return ProductPlaceholder.create_incomplete_media_product(
                title=normalized_data['title'],
                description_html=normalized_data['description_html'],
                source_url=source_url,
                payload_signature=payload_signature,
                extraction_timestamp=extraction_timestamp,
                price=normalized_data['price'],
                attributes=normalized_data['attributes']
            )
        
        # Cas 2: Produit complet
        try:
            status = ProductStatus.COMPLETE
            
            # Ajuster status selon qualité données
            if not normalized_data['price']:
                status = ProductStatus.INCOMPLETE_PRICE
            
            product_dto = ProductDTO(
                title=normalized_data['title'],
                description_html=normalized_data['description_html'],
                price=normalized_data['price'],
                images=valid_images,
                source_url=source_url,
                attributes=normalized_data['attributes'],
                status=status,
                payload_signature=payload_signature,
                extraction_timestamp=extraction_timestamp
            )
            
            return product_dto
            
        except Exception as e:
            logger.error(f"Erreur construction ProductDTO: {e}")
            return None
    
    def _generate_payload_signature(self, normalized_data: Dict, image_urls: list) -> str:
        """Génère signature unique pour idempotence"""
        
        # Construire string déterministe
        signature_parts = [
            normalized_data.get('title', ''),
            normalized_data.get('description_html', ''),
            str(normalized_data.get('price', '')),
            '|'.join(sorted(image_urls)),
            str(sorted(normalized_data.get('attributes', {}).items()))
        ]
        
        signature_string = '|||'.join(signature_parts)
        return hashlib.sha256(signature_string.encode('utf-8')).hexdigest()[:16]
    
    async def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Statistiques complètes du pipeline"""
        
        # Stats transport layer
        proxy_stats = await self.coordinator.get_proxy_stats()
        cache_stats = await self.coordinator.get_cache_stats()
        
        # Stats image storage (mock)
        stored_images_count = len(self.image_pipeline.persistence.stored_images)
        
        return {
            'transport_layer': {
                'proxy_stats': proxy_stats,
                'cache_stats': cache_stats
            },
            'image_processing': {
                'stored_images': stored_images_count,
                'max_dimension': self.image_pipeline.optimizer.max_dimension,
                'webp_quality': self.image_pipeline.optimizer.webp_quality
            },
            'pipeline_config': {
                'fetch_timeout': self.coordinator.timeout_s,
                'image_concurrency': self.image_pipeline.image_semaphore._value,
                'max_images_per_product': 8
            }
        }