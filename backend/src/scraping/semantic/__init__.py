"""
Module Scraping Sémantique - ECOMSIMPLY

Pipeline: HTML → Parser → Normalizer → ImagePipeline → ProductDTO
"""

from .product_dto import ProductDTO, ImageDTO, PriceDTO, Currency, ProductStatus, ProductPlaceholder
from .parser import SemanticParser
from .normalizer import DataNormalizer
from .image_pipeline import ImagePipeline, ImageOptimizer
from .orchestrator import SemanticOrchestrator
from .seo_utils import SEOMetaGenerator, TrendingSEOGenerator
from .robust_image_storage import ImageStorageSystem

__all__ = [
    'ProductDTO',
    'ImageDTO', 
    'PriceDTO',
    'Currency',
    'ProductStatus',
    'ProductPlaceholder',
    'SemanticParser',
    'DataNormalizer', 
    'ImagePipeline',
    'ImageOptimizer',
    'SemanticOrchestrator',
    'SEOMetaGenerator',
    'TrendingSEOGenerator',
    'ImageStorageSystem'
]