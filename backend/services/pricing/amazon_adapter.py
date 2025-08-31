"""
Amazon Price Extraction Adapter - Production Safe
Extrait les prix depuis Amazon avec fallback sans browser
"""

import logging
from decimal import Decimal
from typing import Optional

# Production-safe imports
try:
    from playwright.async_api import Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = object

from .base_adapter import BasePriceAdapter, PriceExtractionResult

logger = logging.getLogger(__name__)


class AmazonPriceAdapter(BasePriceAdapter):
    """Adaptateur pour extraction de prix Amazon - Production safe"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.amazon.fr"
    
    async def extract_price(self, product_url: str) -> PriceExtractionResult:
        """Extrait le prix depuis Amazon avec fallback production"""
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("⚠️ Amazon pricing fallback - Playwright indisponible")
            return PriceExtractionResult(
                price=Decimal("29.99"),  # Prix par défaut
                currency="EUR",
                source="amazon_fallback",
                success=False,
                error="Playwright non disponible en production"
            )
        
        try:
            page = await self.context.new_page()
            await page.goto(product_url, wait_until='domcontentloaded')
            
            # Sélecteurs de prix Amazon
            price_selectors = [
                '.a-price-whole',
                '.a-price .a-offscreen',
                '#priceblock_dealprice',
                '#priceblock_ourprice'
            ]
            
            for selector in price_selectors:
                try:
                    price_element = await page.wait_for_selector(selector, timeout=3000)
                    if price_element:
                        price_text = await price_element.text_content()
                        price = self._parse_price(price_text)
                        if price:
                            await page.close()
                            return PriceExtractionResult(
                                price=price,
                                currency="EUR",
                                source="amazon",
                                success=True
                            )
                except:
                    continue
            
            await page.close()
            return PriceExtractionResult(
                price=None,
                currency="EUR", 
                success=False,
                error="Prix non trouvé"
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction Amazon: {e}")
            return PriceExtractionResult(
                price=Decimal("29.99"),  # Fallback
                currency="EUR",
                source="amazon_fallback",
                success=False,
                error=str(e)
            )