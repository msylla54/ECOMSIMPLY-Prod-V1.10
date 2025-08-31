"""
HTML Parser pour extraction sémantique - ECOMSIMPLY
Parse HTML → données structurées (title, description, price, images, attributs)
"""

import re
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag
import logging

logger = logging.getLogger(__name__)


class SemanticParser:
    """Parser HTML sémantique avec support OpenGraph, Schema.org, meta tags"""
    
    def __init__(self):
        # Patterns prix communs (€, $, £, prix avec séparateurs)
        self.price_patterns = [
            r'[\€\$\£]\s*[\d\s,\.]+',           # €123.45, $1,234.56
            r'[\d\s,\.]+\s*[\€\$\£]',           # 123.45€, 1,234.56 $  
            r'[\d\s,\.]+\s*(?:EUR|USD|GBP)',     # 123.45 EUR
            r'(?:EUR|USD|GBP)\s*[\d\s,\.]+',     # EUR 123.45
        ]
        self.compiled_price_patterns = [re.compile(p, re.IGNORECASE) for p in self.price_patterns]
        
        # Sélecteurs images prioritaires
        self.image_selectors = [
            'meta[property="og:image"]',
            'meta[name="twitter:image"]', 
            '[itemProp="image"]',
            '.product-image img',
            '.main-image img',
            'img[data-src]',
            'img[src]'
        ]
    
    def parse_html(self, html_content: str, base_url: str) -> Dict[str, Any]:
        """
        Parse HTML pour extraire données sémantiques
        
        Returns:
            {
                'title': str,
                'description_html': str,
                'price_text': Optional[str],
                'currency_hint': Optional[str],
                'image_urls': List[str],
                'attributes': Dict[str, str]
            }
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        return {
            'title': self._extract_title(soup),
            'description_html': self._extract_description(soup),
            'price_text': self._extract_price_text(soup),
            'currency_hint': self._extract_currency_hint(soup, base_url),
            'image_urls': self._extract_image_urls(soup, base_url),
            'attributes': self._extract_attributes(soup)
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extrait titre avec priorité OpenGraph > meta > h1 > title"""
        
        # 1. OpenGraph
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()
        
        # 2. Twitter card
        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
        if twitter_title and twitter_title.get('content'):
            return twitter_title['content'].strip()
            
        # 3. Schema.org
        schema_title = soup.find(attrs={'itemprop': 'name'})
        if schema_title:
            title_text = schema_title.get_text(strip=True)
            if title_text:
                return title_text
        
        # 4. Premier H1
        h1 = soup.find('h1')
        if h1:
            title_text = h1.get_text(strip=True)
            if title_text:
                return title_text
        
        # 5. Title tag
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        return "Titre non disponible"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extrait description avec priorité meta description > OpenGraph > contenu"""
        
        # 1. Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            desc = meta_desc['content'].strip()
            if desc:
                return f"<p>{desc}</p>"
        
        # 2. OpenGraph
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            desc = og_desc['content'].strip()
            if desc:
                return f"<p>{desc}</p>"
        
        # 3. Schema.org description
        schema_desc = soup.find(attrs={'itemprop': 'description'})
        if schema_desc:
            desc = schema_desc.get_text(strip=True)
            if desc:
                return f"<p>{desc}</p>"
        
        # 4. Contenu probable (divs avec classes description)
        desc_selectors = [
            '.product-description',
            '.description',
            '.product-details',
            '.summary',
            '[data-description]'
        ]
        
        for selector in desc_selectors:
            desc_element = soup.select_one(selector)
            if desc_element:
                # Nettoyer et extraire HTML interne
                desc_html = str(desc_element)
                if desc_html.strip():
                    return desc_html
        
        return "<p>Description non disponible</p>"
    
    def _extract_price_text(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrait texte prix brut avec patterns regex"""
        
        # 1. Schema.org price
        schema_price = soup.find(attrs={'itemprop': 'price'})
        if schema_price:
            price_text = schema_price.get('content') or schema_price.get_text(strip=True)
            if price_text:
                return price_text
        
        # 2. Classes prix communes
        price_selectors = [
            '.price',
            '.product-price', 
            '.current-price',
            '.sale-price',
            '[data-price]',
            '.amount'
        ]
        
        for selector in price_selectors:
            price_element = soup.select_one(selector)
            if price_element:
                price_text = price_element.get_text(strip=True)
                if price_text and self._contains_price_pattern(price_text):
                    return price_text
        
        # 3. Recherche dans tout le texte avec patterns
        all_text = soup.get_text()
        for pattern in self.compiled_price_patterns:
            matches = pattern.findall(all_text)
            if matches:
                # Retourner le premier match trouvé
                return matches[0].strip()
        
        return None
    
    def _contains_price_pattern(self, text: str) -> bool:
        """Vérifie si le texte contient un pattern de prix"""
        for pattern in self.compiled_price_patterns:
            if pattern.search(text):
                return True
        return False
    
    def _extract_currency_hint(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Devine la devise probable depuis domaine/langue/contenu"""
        
        # 1. Schema.org currency
        schema_currency = soup.find(attrs={'itemprop': 'priceCurrency'})
        if schema_currency:
            currency = schema_currency.get('content') or schema_currency.get_text(strip=True)
            if currency:
                return currency.upper()
        
        # 2. Domaine géographique
        domain = urlparse(base_url).netloc.lower()
        if any(tld in domain for tld in ['.fr', '.be', '.lu']):
            return 'EUR'
        if any(tld in domain for tld in ['.co.uk', '.uk']):
            return 'GBP'
        if any(tld in domain for tld in ['.com', '.us']):
            return 'USD'
        
        # 3. Langue HTML
        html_lang = soup.find('html')
        if html_lang and html_lang.get('lang'):
            lang = html_lang['lang'].lower()
            if lang.startswith('fr'):
                return 'EUR'
            if lang.startswith('en-gb'):
                return 'GBP'
            if lang.startswith('en'):
                return 'USD'
        
        # 4. Contenu page (chercher symboles)
        text_content = soup.get_text()
        if '€' in text_content:
            return 'EUR'
        if '£' in text_content:
            return 'GBP'
        if '$' in text_content:
            return 'USD'
        
        return None
    
    def _extract_image_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extrait URLs images avec priorité sémantique"""
        
        image_urls = []
        seen_urls = set()
        
        # Parcourir sélecteurs par priorité
        for selector in self.image_selectors:
            elements = soup.select(selector)
            
            for element in elements:
                url = None
                
                # Extraire URL selon type élément
                if element.name == 'meta':
                    url = element.get('content')
                elif element.name == 'img':
                    # Priorité data-src > src
                    url = element.get('data-src') or element.get('src')
                
                if url:
                    # Résoudre URL relative en absolue HTTPS
                    absolute_url = urljoin(base_url, url)
                    absolute_url = self._force_https(absolute_url)
                    
                    if absolute_url not in seen_urls:
                        seen_urls.add(absolute_url)
                        image_urls.append(absolute_url)
                        
                        # Limite 8 images max pour performance
                        if len(image_urls) >= 8:
                            break
            
            if len(image_urls) >= 8:
                break
        
        logger.info(f"Images extraites: {len(image_urls)} URLs uniques")
        return image_urls
    
    def _force_https(self, url: str) -> str:
        """Force HTTPS sur l'URL"""
        if url.startswith('http://'):
            return url.replace('http://', 'https://', 1)
        elif not url.startswith('https://'):
            return f"https://{url.lstrip('/')}"
        return url
    
    def _extract_attributes(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extrait attributs produit (brand, model, etc.)"""
        
        attributes = {}
        
        # Schema.org structured data
        schema_mappings = {
            'brand': 'brand',
            'model': 'model', 
            'manufacturer': 'manufacturer',
            'category': 'category',
            'sku': 'sku',
            'gtin': 'gtin'
        }
        
        for attr_name, schema_prop in schema_mappings.items():
            element = soup.find(attrs={'itemprop': schema_prop})
            if element:
                value = element.get('content') or element.get_text(strip=True)
                if value:
                    attributes[attr_name] = value
        
        # OpenGraph product data
        og_mappings = {
            'brand': 'product:brand',
            'category': 'product:category',
            'price_amount': 'product:price:amount',
            'price_currency': 'product:price:currency'
        }
        
        for attr_name, og_prop in og_mappings.items():
            og_element = soup.find('meta', property=og_prop)
            if og_element and og_element.get('content'):
                attributes[attr_name] = og_element['content']
        
        logger.debug(f"Attributs extraits: {list(attributes.keys())}")
        return attributes