"""
Services de récupération de prix depuis multiples sources
"""
from .base_adapter import BasePriceAdapter, PriceExtractionResult
from .amazon_adapter import AmazonPriceAdapter
from .google_shopping_adapter import GoogleShoppingAdapter
from .cdiscount_adapter import CdiscountAdapter
from .fnac_adapter import FnacAdapter

__all__ = [
    'BasePriceAdapter',
    'PriceExtractionResult',
    'AmazonPriceAdapter',
    'GoogleShoppingAdapter',
    'CdiscountAdapter',
    'FnacAdapter',
]