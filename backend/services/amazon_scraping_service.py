# Amazon Scraping Service - Phase 3
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
import logging
import time
import random
from urllib.parse import urljoin, quote
import json
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup
import os

logger = logging.getLogger(__name__)

class AmazonScrapingService:
    """
    Service de scraping Amazon pour extraction SEO + prix réels
    Respect des quotas et retry avec backoff exponential
    """
    
    def __init__(self):
        self.base_delay = 1.0  # Délai de base entre requêtes
        self.max_retries = 3
        self.timeout = 30
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # Configuration des marketplaces Amazon
        self.marketplaces = {
            'FR': 'amazon.fr',
            'DE': 'amazon.de', 
            'UK': 'amazon.co.uk',
            'US': 'amazon.com',
            'IT': 'amazon.it',
            'ES': 'amazon.es'
        }
        
    async def scrape_product_seo_and_price(
        self, 
        asin: str, 
        marketplace: str = 'FR'
    ) -> Dict[str, Any]:
        """
        Scraper SEO + prix réels pour un ASIN donné
        
        Args:
            asin: Amazon Standard Identification Number
            marketplace: Marketplace Amazon (FR, DE, UK, US, IT, ES)
            
        Returns:
            Dict contenant SEO et prix extraits
        """
        try:
            logger.info(f"🔍 Starting scraping for ASIN {asin} on {marketplace}")
            
            # Construire l'URL Amazon
            domain = self.marketplaces.get(marketplace, 'amazon.fr')
            url = f"https://www.{domain}/dp/{asin}"
            
            # Scraper la page produit
            html_content = await self._fetch_with_retry(url)
            if not html_content:
                raise Exception(f"Failed to fetch content for {asin}")
            
            # Parser le contenu HTML
            scraped_data = await self._parse_amazon_page(html_content, asin, marketplace)
            
            # Enrichir avec métadonnées
            scraped_data.update({
                'asin': asin,
                'marketplace': marketplace,
                'scraped_at': datetime.utcnow().isoformat(),
                'scraping_source': f'{domain}/dp/{asin}',
                'scraping_success': True
            })
            
            logger.info(f"✅ Scraping completed for {asin} - Title: {scraped_data.get('title', 'N/A')[:50]}...")
            return scraped_data
            
        except Exception as e:
            logger.error(f"❌ Scraping failed for {asin}: {str(e)}")
            return {
                'asin': asin,
                'marketplace': marketplace,
                'scraped_at': datetime.utcnow().isoformat(),
                'scraping_success': False,
                'error': str(e),
                'seo_data': {},
                'price_data': {}
            }
    
    async def _fetch_with_retry(self, url: str) -> Optional[str]:
        """
        Fetch URL avec retry et backoff exponential
        """
        for attempt in range(self.max_retries):
            try:
                # Délai entre requêtes avec jitter
                if attempt > 0:
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
                    await asyncio.sleep(delay)
                
                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none'
                }
                
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            content = await response.text()
                            logger.info(f"✅ Successfully fetched {url} (attempt {attempt + 1})")
                            return content
                        elif response.status == 503:
                            logger.warning(f"⚠️ Rate limited (503) for {url}, retrying...")
                            continue
                        else:
                            logger.warning(f"⚠️ HTTP {response.status} for {url}")
                            continue
                            
            except asyncio.TimeoutError:
                logger.warning(f"⏰ Timeout for {url} (attempt {attempt + 1})")
                continue
            except Exception as e:
                logger.warning(f"❌ Error fetching {url} (attempt {attempt + 1}): {str(e)}")
                continue
        
        logger.error(f"❌ Failed to fetch {url} after {self.max_retries} attempts")
        return None
    
    async def _parse_amazon_page(self, html: str, asin: str, marketplace: str) -> Dict[str, Any]:
        """
        Parser le contenu HTML d'une page Amazon pour extraire SEO + prix
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extraction SEO
        seo_data = await self._extract_seo_data(soup)
        
        # Extraction prix
        price_data = await self._extract_price_data(soup, marketplace)
        
        # Extraction métadonnées produit
        product_data = await self._extract_product_metadata(soup)
        
        return {
            'seo_data': seo_data,
            'price_data': price_data,
            'product_data': product_data,
            'raw_html_length': len(html)
        }
    
    async def _extract_seo_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extraire les données SEO (titre, bullets, description, keywords)
        """
        seo_data = {}
        
        try:
            # Titre produit
            title_selectors = [
                '#productTitle',
                '.product_title',
                '[data-automation-id="title"]',
                'h1.a-size-large'
            ]
            
            title = None
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element:
                    title = element.get_text(strip=True)
                    break
            
            seo_data['title'] = title or 'Titre non trouvé'
            
            # Bullet points
            bullets = []
            bullet_selectors = [
                '#feature-bullets ul li:not(.aok-hidden) span.a-list-item',
                '.a-unordered-list.a-vertical.a-spacing-mini .a-list-item',
                '[data-automation-id="feature-bullets"] li'
            ]
            
            for selector in bullet_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 10 and not text.startswith('Make sure'):
                        bullets.append(text)
                        if len(bullets) >= 5:
                            break
                if bullets:
                    break
            
            seo_data['bullet_points'] = bullets[:5]
            
            # Description
            description_selectors = [
                '#productDescription p',
                '.a-section.a-spacing-medium .a-size-base',
                '[data-automation-id="productDescription"]'
            ]
            
            description = ''
            for selector in description_selectors:
                elements = soup.select(selector)
                if elements:
                    description = '\n'.join([elem.get_text(strip=True) for elem in elements])
                    break
            
            seo_data['description'] = description or 'Description non trouvée'
            
            # Keywords depuis métadonnées
            keywords = []
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords:
                keywords.extend(meta_keywords.get('content', '').split(','))
            
            # Keywords depuis le titre et bullets
            title_words = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', seo_data['title'].lower())
            keywords.extend(title_words)
            
            for bullet in bullets:
                bullet_words = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', bullet.lower())
                keywords.extend(bullet_words)
            
            # Nettoyer et déduplicater les keywords
            unique_keywords = list(set([kw.strip().lower() for kw in keywords if kw.strip()]))
            seo_data['extracted_keywords'] = unique_keywords[:20]  # Limiter à 20 mots-clés
            
            logger.info(f"✅ SEO data extracted - Title: {len(seo_data['title'])} chars, Bullets: {len(bullets)}, Keywords: {len(unique_keywords)}")
            
        except Exception as e:
            logger.error(f"❌ Error extracting SEO data: {str(e)}")
            seo_data = {
                'title': 'Erreur extraction titre',
                'bullet_points': [],
                'description': 'Erreur extraction description',
                'extracted_keywords': [],
                'extraction_error': str(e)
            }
        
        return seo_data
    
    async def _extract_price_data(self, soup: BeautifulSoup, marketplace: str) -> Dict[str, Any]:
        """
        Extraire les données de prix
        """
        price_data = {
            'currency': self._get_marketplace_currency(marketplace),
            'prices_found': []
        }
        
        try:
            # Sélecteurs pour les prix
            price_selectors = [
                '.a-price.a-text-price.a-size-medium.apexPriceToPay .a-offscreen',
                '.a-price-whole',
                '#price_inside_buybox',
                '.a-price .a-offscreen',
                '[data-automation-id="list-price"]'
            ]
            
            prices = []
            for selector in price_selectors:
                elements = soup.select(selector)
                for element in elements:
                    price_text = element.get_text(strip=True)
                    price_value = self._parse_price_string(price_text)
                    if price_value:
                        prices.append({
                            'value': price_value,
                            'formatted': price_text,
                            'selector_used': selector
                        })
            
            # Prix de référence (généralement le premier trouvé)
            if prices:
                price_data['current_price'] = prices[0]['value']
                price_data['current_price_formatted'] = prices[0]['formatted']
                price_data['prices_found'] = prices
            else:
                price_data['current_price'] = None
                price_data['extraction_error'] = 'Aucun prix trouvé'
            
            # Prix de comparaison (prix barré, etc.)
            compare_selectors = [
                '.a-price.a-text-price .a-offscreen',
                '[data-automation-id="was-price"]'
            ]
            
            compare_prices = []
            for selector in compare_selectors:
                elements = soup.select(selector)
                for element in elements:
                    price_text = element.get_text(strip=True)
                    price_value = self._parse_price_string(price_text)
                    if price_value and price_value != price_data.get('current_price'):
                        compare_prices.append({
                            'value': price_value,
                            'formatted': price_text,
                            'type': 'compare'
                        })
            
            price_data['compare_prices'] = compare_prices
            
            logger.info(f"✅ Price extracted - Current: {price_data.get('current_price')} {price_data['currency']}")
            
        except Exception as e:
            logger.error(f"❌ Error extracting price data: {str(e)}")
            price_data['extraction_error'] = str(e)
        
        return price_data
    
    async def _extract_product_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extraire les métadonnées produit (marque, catégorie, etc.)
        """
        metadata = {}
        
        try:
            # Marque
            brand_selectors = [
                '[data-automation-id="brand-name"]',
                '#bylineInfo',
                '.a-row.a-spacing-small .a-size-small'
            ]
            
            for selector in brand_selectors:
                element = soup.select_one(selector)
                if element:
                    brand_text = element.get_text(strip=True)
                    if 'Marque' in brand_text or 'Brand' in brand_text:
                        metadata['brand'] = brand_text.split(':')[-1].strip()
                        break
                    elif len(brand_text) < 50:  # Probablement une marque
                        metadata['brand'] = brand_text
                        break
            
            # Catégorie depuis breadcrumb
            breadcrumb_element = soup.select_one('#wayfinding-breadcrumbs_feature_div')
            if breadcrumb_element:
                categories = [cat.get_text(strip=True) for cat in breadcrumb_element.select('a')]
                metadata['categories'] = [cat for cat in categories if cat]
            
            # Rating
            rating_element = soup.select_one('.a-icon-alt')
            if rating_element:
                rating_text = rating_element.get_text()
                rating_match = re.search(r'(\d+,?\d*)', rating_text)
                if rating_match:
                    metadata['rating'] = float(rating_match.group(1).replace(',', '.'))
            
            # Nombre de reviews
            reviews_element = soup.select_one('#acrCustomerReviewText')
            if reviews_element:
                reviews_text = reviews_element.get_text()
                reviews_match = re.search(r'(\d+)', reviews_text.replace(' ', '').replace(',', ''))
                if reviews_match:
                    metadata['reviews_count'] = int(reviews_match.group(1))
            
        except Exception as e:
            logger.error(f"❌ Error extracting metadata: {str(e)}")
            metadata['extraction_error'] = str(e)
        
        return metadata
    
    def _parse_price_string(self, price_text: str) -> Optional[float]:
        """
        Parser une chaîne de prix en valeur numérique
        """
        if not price_text:
            return None
        
        # Nettoyer le texte du prix
        cleaned = re.sub(r'[^\d,.\s]', '', price_text)
        
        # Patterns pour différents formats de prix
        patterns = [
            r'(\d+)[,.](\d{2})',  # 29,99 ou 29.99
            r'(\d+)',             # 29
        ]
        
        for pattern in patterns:
            match = re.search(pattern, cleaned)
            if match:
                if len(match.groups()) == 2:
                    return float(f"{match.group(1)}.{match.group(2)}")
                else:
                    return float(match.group(1))
        
        return None
    
    def _get_marketplace_currency(self, marketplace: str) -> str:
        """
        Obtenir la devise du marketplace
        """
        currency_map = {
            'FR': 'EUR',
            'DE': 'EUR',
            'IT': 'EUR',
            'ES': 'EUR',
            'UK': 'GBP',
            'US': 'USD'
        }
        return currency_map.get(marketplace, 'EUR')
    
    async def scrape_competitor_prices(
        self, 
        search_query: str, 
        marketplace: str = 'FR',
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Scraper les prix des concurrents pour une recherche donnée
        """
        try:
            logger.info(f"🔍 Scraping competitor prices for: {search_query}")
            
            domain = self.marketplaces.get(marketplace, 'amazon.fr')
            search_url = f"https://www.{domain}/s?k={quote(search_query)}"
            
            html_content = await self._fetch_with_retry(search_url)
            if not html_content:
                return []
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extraire les résultats de recherche
            results = []
            product_containers = soup.select('[data-component-type="s-search-result"]')
            
            for container in product_containers[:max_results]:
                try:
                    # ASIN
                    asin = container.get('data-asin')
                    if not asin:
                        continue
                    
                    # Titre
                    title_element = container.select_one('h2 a span')
                    title = title_element.get_text(strip=True) if title_element else 'N/A'
                    
                    # Prix
                    price_element = container.select_one('.a-price .a-offscreen')
                    price = None
                    if price_element:
                        price = self._parse_price_string(price_element.get_text())
                    
                    # Rating
                    rating_element = container.select_one('.a-icon-alt')
                    rating = None
                    if rating_element:
                        rating_text = rating_element.get_text()
                        rating_match = re.search(r'(\d+,?\d*)', rating_text)
                        if rating_match:
                            rating = float(rating_match.group(1).replace(',', '.'))
                    
                    if price:  # Seulement ajouter si on a trouvé un prix
                        results.append({
                            'asin': asin,
                            'title': title,
                            'price': price,
                            'rating': rating,
                            'currency': self._get_marketplace_currency(marketplace),
                            'search_query': search_query
                        })
                
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing search result: {str(e)}")
                    continue
            
            logger.info(f"✅ Found {len(results)} competitor prices for '{search_query}'")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error scraping competitor prices: {str(e)}")
            return []