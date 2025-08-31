"""
Classe de base pour les adapters de prix
"""
import asyncio
import re
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Production-safe imports - Playwright non requis
try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    # Mock classes pour production sans Playwright
    PLAYWRIGHT_AVAILABLE = False
    Browser = object
    BrowserContext = object
    Page = object
    
    class async_playwright:
        @staticmethod
        async def start():
            raise NotImplementedError("Playwright not available in production - use fallback pricing")


@dataclass
class PriceExtractionResult:
    """Résultat d'extraction de prix depuis une source"""
    price: Optional[Decimal]
    currency: str
    url: str
    selector: str
    screenshot_path: Optional[str]
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    raw_price_text: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour sérialisation"""
        return {
            'price': float(self.price) if self.price else None,
            'currency': self.currency,
            'url': self.url,
            'selector': self.selector,  
            'screenshot_path': self.screenshot_path,
            'timestamp': self.timestamp.isoformat(),
            'success': self.success,
            'error_message': self.error_message,
            'raw_price_text': self.raw_price_text
        }


class BasePriceAdapter(ABC):
    """Classe de base pour tous les adapters de prix"""
    
    def __init__(self, name: str):
        self.name = name
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.request_count = 0
        self.success_count = 0
        self.last_request_time = None
        
        # Configuration du throttling (1.5 req/s par domaine)
        self.min_delay_between_requests = 1.5
        
        # Répertoire pour les screenshots
        self.screenshots_dir = Path("/app/backend/static/screenshots/price_truth")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    async def __aenter__(self):
        """Context manager - initialisation"""
        await self._setup_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager - nettoyage"""
        await self._cleanup_browser()
    
    async def _setup_browser(self):
        """Initialise le navigateur pour scraping - Production safe"""
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("⚠️ Playwright non disponible - utilisation des prix par défaut")
            return
            
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                ]
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
        except Exception as e:
            logger.error(f"❌ Erreur setup browser: {e}")
            # Continuer sans browser - utiliser fallback
    
    async def _cleanup_browser(self):
        """Nettoie les ressources Playwright"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
        except Exception as e:
            print(f"⚠️ Erreur cleanup browser {self.name}: {e}")
    
    async def _throttle_request(self):
        """Applique le throttling entre les requêtes"""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.min_delay_between_requests:
                sleep_time = self.min_delay_between_requests - elapsed
                await asyncio.sleep(sleep_time)
        
        self.last_request_time = datetime.now()
        self.request_count += 1
    
    def _clean_price_text(self, price_text: str) -> Optional[Decimal]:
        """Nettoie et convertit le texte prix en Decimal"""
        if not price_text:
            return None
        
        try:
            # Nettoyer le texte : enlever caractères non numériques sauf . et ,
            cleaned = re.sub(r'[^\d.,]', '', price_text.strip())
            
            if not cleaned:
                return None
            
            # Gestion des formats européens vs américains
            if ',' in cleaned and '.' in cleaned:
                # Format type 1.234,56 (européen) ou 1,234.56 (américain)
                if cleaned.rfind(',') > cleaned.rfind('.'):
                    # Européen : 1.234,56
                    cleaned = cleaned.replace('.', '').replace(',', '.')
                else:
                    # Américain : 1,234.56
                    cleaned = cleaned.replace(',', '')
            elif ',' in cleaned:
                # Si seule virgule, vérifier si c'est un séparateur décimal
                comma_pos = cleaned.rfind(',')
                after_comma = cleaned[comma_pos + 1:]
                if len(after_comma) <= 2 and after_comma.isdigit():
                    # Séparateur décimal : 123,45
                    cleaned = cleaned.replace(',', '.')
                else:
                    # Séparateur milliers : 1,234
                    cleaned = cleaned.replace(',', '')
            
            return Decimal(cleaned)
            
        except (InvalidOperation, ValueError) as e:
            print(f"⚠️ {self.name}: Impossible de parser '{price_text}': {e}")
            return None
    
    async def _take_screenshot(self, page: Page, query: str) -> Optional[str]:
        """Prend un screenshot de la page"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.name}_{query.replace(' ', '_')}_{timestamp}.png"
            screenshot_path = self.screenshots_dir / filename
            
            await page.screenshot(path=str(screenshot_path), full_page=False)
            return str(screenshot_path)
        except Exception as e:
            print(f"⚠️ {self.name}: Erreur screenshot: {e}")
            return None
    
    @abstractmethod
    def _get_search_url(self, query: str) -> str:
        """Construit l'URL de recherche pour la requête"""
        pass
    
    @abstractmethod
    def _get_price_selectors(self) -> List[str]:
        """Retourne la liste des sélecteurs CSS pour les prix (ordre de priorité)"""
        pass
    
    @abstractmethod
    async def _extract_price_from_page(self, page: Page, query: str) -> PriceExtractionResult:
        """Extrait le prix depuis la page"""
        pass
    
    async def extract_price(self, query: str, max_retries: int = 2) -> PriceExtractionResult:
        """
        Extrait le prix pour une requête donnée
        
        Args:
            query: Requête de recherche
            max_retries: Nombre de tentatives max
            
        Returns:
            PriceExtractionResult avec le résultat
        """
        if not self.context:
            await self._setup_browser()
        
        for attempt in range(max_retries + 1):
            try:
                await self._throttle_request()
                
                page = await self.context.new_page()
                
                try:
                    # Timeout de 12s comme spécifié
                    page.set_default_timeout(12000)
                    
                    search_url = self._get_search_url(query)
                    print(f"🔍 {self.name}: Recherche '{query}' -> {search_url}")
                    
                    await page.goto(search_url, wait_until='domcontentloaded')
                    
                    # Attendre un peu pour le chargement dynamique
                    await page.wait_for_timeout(2000)
                    
                    result = await self._extract_price_from_page(page, query)
                    
                    if result.success:
                        self.success_count += 1
                        print(f"✅ {self.name}: Prix trouvé {result.price}€ pour '{query}'")
                    else:
                        print(f"⚠️ {self.name}: Échec extraction '{query}': {result.error_message}")
                    
                    return result
                    
                finally:
                    await page.close()
                    
            except Exception as e:
                error_msg = f"Erreur tentative {attempt + 1}/{max_retries + 1}: {str(e)}"
                print(f"❌ {self.name}: {error_msg}")
                
                if attempt == max_retries:
                    return PriceExtractionResult(
                        price=None,
                        currency="EUR",
                        url=self._get_search_url(query),
                        selector="none",
                        screenshot_path=None,
                        timestamp=datetime.now(),
                        success=False,
                        error_message=error_msg
                    )
                
                # Délai croissant entre les tentatives
                await asyncio.sleep(2 ** attempt)
        
        # Ne devrait jamais arriver
        return PriceExtractionResult(
            price=None,
            currency="EUR", 
            url=self._get_search_url(query),
            selector="none",
            screenshot_path=None,
            timestamp=datetime.now(),
            success=False,
            error_message="Max retries exceeded"
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de l'adapter"""
        success_rate = (self.success_count / max(1, self.request_count)) * 100
        return {
            'name': self.name,
            'requests': self.request_count,
            'successes': self.success_count,
            'success_rate': f"{success_rate:.1f}%",
            'last_request': self.last_request_time.isoformat() if self.last_request_time else None
        }