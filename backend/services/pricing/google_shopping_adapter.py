"""
Google Shopping Price Extraction Adapter - Production Safe
Extrait les prix depuis Google Shopping avec fallback sans browser
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


class GoogleShoppingPriceAdapter(BasePriceAdapter):
    """Adaptateur pour extraction de prix Google Shopping - Production safe"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://shopping.google.com"
    
    async def extract_price(self, search_query: str) -> PriceExtractionResult:
        """Extrait le prix depuis Google Shopping avec fallback production"""
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("⚠️ Google Shopping pricing fallback - Playwright indisponible")
            return PriceExtractionResult(
                price=Decimal("24.99"),  # Prix par défaut
                currency="EUR",
                source="google_shopping_fallback",
                success=False,
                error="Playwright non disponible en production"
            )
        
        try:
            page = await self.context.new_page()
            search_url = f"{self.base_url}/search?q={search_query}&hl=fr&gl=fr"
            await page.goto(search_url, wait_until='domcontentloaded')
            
            # Sélecteurs de prix Google Shopping
            price_selectors = [
                '[data-sh-pr] span',
                '.translate-content span[aria-hidden="true"]',
                '.sh-pr__price'
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
                                source="google_shopping",
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
            logger.error(f"❌ Erreur extraction Google Shopping: {e}")
            return PriceExtractionResult(
                price=Decimal("24.99"),  # Fallback
                currency="EUR",
                source="google_shopping_fallback",
                success=False,
                error=str(e)
            )