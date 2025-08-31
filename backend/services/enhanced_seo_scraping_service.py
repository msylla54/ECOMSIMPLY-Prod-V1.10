"""
Enhanced SEO Scraping Service avec transport robuste - ECOMSIMPLY
Intégration de RequestCoordinator pour gestion robuste des requêtes
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import sys
import os

# Import de notre couche de transport
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from scraping.transport import RequestCoordinator

# Import du logging structuré
from .logging_service import ecomsimply_logger, log_error, log_info, log_operation


class EnhancedSEOScrapingService:
    """Service de scraping SEO amélioré avec transport robuste et cache"""
    
    def __init__(self, max_per_host: int = 3, timeout_s: float = 10.0, cache_ttl_s: int = 180):
        """
        Args:
            max_per_host: Nombre max de requêtes simultanées par host (défaut: 3)
            timeout_s: Timeout global en secondes (défaut: 10s)
            cache_ttl_s: TTL du cache en secondes (défaut: 180s)
        """
        self.coordinator = RequestCoordinator(
            max_per_host=max_per_host, 
            timeout_s=timeout_s, 
            cache_ttl_s=cache_ttl_s
        )
        self.ua = UserAgent()
        
        # Configuration des sources de données
        self.price_sources = [
            {
                'name': 'Amazon',
                'domain': 'amazon.fr',
                'search_url': 'https://www.amazon.fr/s?k={query}',
                'price_selectors': ['.a-price-whole', '.a-price .a-offscreen'],
                'title_selectors': ['.s-title-instructions-style h2 a span', '.s-title']
            },
            {
                'name': 'Cdiscount',
                'domain': 'cdiscount.com',
                'search_url': 'https://www.cdiscount.com/search/10/{query}.html',
                'price_selectors': ['.price', '.prdtPriceWithoutStrikeThrough'],
                'title_selectors': ['.prdtBTit', '.prdtTitle']
            },
            {
                'name': 'Fnac',
                'domain': 'fnac.com',
                'search_url': 'https://www.fnac.com/SearchResult/ResultList.aspx?Search={query}',
                'price_selectors': ['.userPrice', '.price'],
                'title_selectors': ['.Article-title', '.title']
            }
        ]
        
        # Proxys par défaut (à configurer selon les besoins)
        self.default_proxies = [
            # À remplir avec de vrais proxys si disponibles
            # "http://proxy1.example.com:8080",
            # "http://proxy2.example.com:8080",
        ]
    
    async def __aenter__(self):
        """Context manager entry"""
        # Ajouter les proxys par défaut
        for proxy in self.default_proxies:
            await self.coordinator.add_proxy(proxy)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.coordinator.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Générer des headers réalistes"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _extract_prices_from_html(self, html: str, selectors: List[str]) -> List[float]:
        """Extraire les prix d'une page HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        prices = []
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements[:10]:  # Limiter à 10 premiers résultats
                price_text = element.get_text(strip=True)
                if price_text:
                    # Nettoyer le texte et extraire le prix
                    price_text = price_text.replace('€', '').replace(',', '.')
                    price_text = ''.join(c for c in price_text if c.isdigit() or c == '.')
                    
                    try:
                        price = float(price_text)
                        if 0 < price < 10000:  # Filtre de prix raisonnable
                            prices.append(price)
                    except (ValueError, TypeError):
                        continue
        
        return prices
    
    def _extract_titles_from_html(self, html: str, selectors: List[str]) -> List[str]:
        """Extraire les titres d'une page HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        titles = []
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements[:10]:  # Limiter à 10 premiers résultats
                title = element.get_text(strip=True)
                if title and len(title) > 10:  # Filtrer les titres trop courts
                    titles.append(title)
        
        return titles
    
    async def scrape_competitor_prices(self, product_name: str, category: str = "") -> Dict[str, Any]:
        """
        Scraper les prix des concurrents avec transport robuste
        
        Args:
            product_name: Nom du produit à rechercher
            category: Catégorie du produit
        
        Returns:
            Dict avec les prix trouvés par source
        """
        log_info(f"🔍 Début scraping prix pour: {product_name} (catégorie: {category})")
        
        # Préparer la requête de recherche
        search_query = product_name
        if category:
            category_keywords = {
                'electronics': 'électronique high-tech',
                'fashion': 'mode vêtements',
                'home': 'maison décoration',
                'sport': 'sport fitness',
                'auto': 'automobile pièces'
            }
            if category.lower() in category_keywords:
                search_query = f"{product_name} {category_keywords[category.lower()]}"
        
        results = {
            "success": True,
            "product_name": product_name,
            "category": category,
            "search_query": search_query,
            "sources": {},
            "summary": {
                "total_sources": len(self.price_sources),
                "successful_sources": 0,
                "total_prices_found": 0,
                "average_price": 0.0,
                "price_range": {"min": 0.0, "max": 0.0}
            },
            "scraping_stats": {}
        }
        
        headers = self._get_headers()
        
        # Scraper chaque source en parallèle
        tasks = []
        for source in self.price_sources:
            task = self._scrape_single_source(source, search_query, headers)
            tasks.append(task)
        
        # Attendre tous les résultats
        source_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Traiter les résultats
        all_prices = []
        for i, result in enumerate(source_results):
            source = self.price_sources[i]
            source_name = source['name']
            
            if isinstance(result, Exception):
                log_error(f"Erreur scraping {source_name}: {str(result)}")
                results["sources"][source_name] = {
                    "success": False,
                    "error": str(result),
                    "prices": [],
                    "count": 0
                }
            else:
                results["sources"][source_name] = result
                if result["success"]:
                    results["summary"]["successful_sources"] += 1
                    all_prices.extend(result["prices"])
        
        # Calculer les statistiques finales
        if all_prices:
            results["summary"]["total_prices_found"] = len(all_prices)
            results["summary"]["average_price"] = sum(all_prices) / len(all_prices)
            results["summary"]["price_range"] = {
                "min": min(all_prices),
                "max": max(all_prices)
            }
        
        # Ajouter les stats de scraping et cache
        coordinator_stats = await self.coordinator.get_proxy_stats()
        cache_stats = await self.coordinator.get_cache_stats()
        
        results["scraping_stats"] = {
            "proxy_stats": coordinator_stats,
            "cache_stats": cache_stats
        }
        
        log_info(f"✅ Scraping terminé: {results['summary']['successful_sources']}/{results['summary']['total_sources']} sources réussies")
        
        return results
    
    async def _scrape_single_source(self, source: Dict, search_query: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Scraper une source individuelle"""
        source_name = source['name']
        start_time = time.time()
        
        try:
            # Construire l'URL de recherche
            search_url = source['search_url'].format(query=search_query.replace(' ', '+'))
            
            log_info(f"🔍 Scraping {source_name}: {search_url}")
            
            # Effectuer la requête avec notre transport robuste et cache
            response = await self.coordinator.get(search_url, headers=headers, use_cache=True)
            
            # Extraire le contenu HTML
            html_content = response.text
            
            # Extraire les prix
            prices = self._extract_prices_from_html(html_content, source['price_selectors'])
            
            # Extraire les titres pour validation
            titles = self._extract_titles_from_html(html_content, source['title_selectors'])
            
            duration = time.time() - start_time
            
            result = {
                "success": True,
                "source": source_name,
                "url": search_url,
                "prices": prices,
                "count": len(prices),
                "sample_titles": titles[:3],  # Échantillon de titres
                "response_time_ms": int(duration * 1000),
                "status_code": response.status_code
            }
            
            log_info(f"✅ {source_name}: {len(prices)} prix trouvés en {duration:.2f}s")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            log_error(f"❌ Erreur {source_name}: {str(e)}")
            
            return {
                "success": False,
                "source": source_name,
                "error": str(e),
                "error_type": type(e).__name__,
                "prices": [],
                "count": 0,
                "response_time_ms": int(duration * 1000)
            }
    
    async def scrape_seo_data(self, product_name: str, category: str = "") -> Dict[str, Any]:
        """
        Scraper les données SEO (meta titles, descriptions, etc.)
        
        Args:
            product_name: Nom du produit
            category: Catégorie du produit
        
        Returns:
            Dict avec les données SEO collectées
        """
        log_info(f"🔍 Début scraping SEO pour: {product_name}")
        
        search_query = f"{product_name} {category}".strip()
        headers = self._get_headers()
        
        # URLs de recherche pour SEO
        seo_sources = [
            f"https://www.google.fr/search?q={search_query.replace(' ', '+')}",
            f"https://www.bing.com/search?q={search_query.replace(' ', '+')}",
        ]
        
        results = {
            "success": True,
            "product_name": product_name,
            "category": category,
            "seo_data": {
                "meta_titles": [],
                "meta_descriptions": [],
                "keywords": [],
                "competitor_titles": []
            },
            "sources_scraped": len(seo_sources)
        }
        
        # Scraper les sources SEO
        for url in seo_sources:
            try:
                response = await self.coordinator.get(url, headers=headers)
                html_content = response.text
                
                # Extraire les données SEO
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Meta titles des résultats de recherche
                title_elements = soup.select('h3, .r a, .LC20lb')
                for element in title_elements[:10]:
                    title = element.get_text(strip=True)
                    if title and len(title) > 10:
                        results["seo_data"]["competitor_titles"].append(title)
                
                # Meta descriptions
                desc_elements = soup.select('.VwiC3b, .s, .st')
                for element in desc_elements[:10]:
                    desc = element.get_text(strip=True)
                    if desc and len(desc) > 20:
                        results["seo_data"]["meta_descriptions"].append(desc)
                
            except Exception as e:
                log_error(f"Erreur scraping SEO {url}: {str(e)}")
                continue
        
        # Déduplication
        results["seo_data"]["meta_titles"] = list(set(results["seo_data"]["competitor_titles"]))
        results["seo_data"]["meta_descriptions"] = list(set(results["seo_data"]["meta_descriptions"]))
        
        log_info(f"✅ Scraping SEO terminé: {len(results['seo_data']['competitor_titles'])} titres collectés")
        
        return results
    
    async def add_proxy(self, proxy_url: str) -> None:
        """Ajouter un proxy au pool"""
        await self.coordinator.add_proxy(proxy_url)
    
    async def get_transport_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques de transport"""
        return await self.coordinator.get_proxy_stats()


# Fonction utilitaire pour utilisation simple
async def scrape_competitor_prices_enhanced(product_name: str, category: str = "") -> Dict[str, Any]:
    """Fonction utilitaire pour scraper les prix avec transport robuste"""
    async with EnhancedSEOScrapingService() as scraper:
        return await scraper.scrape_competitor_prices(product_name, category)


async def scrape_seo_data_enhanced(product_name: str, category: str = "") -> Dict[str, Any]:
    """Fonction utilitaire pour scraper les données SEO"""
    async with EnhancedSEOScrapingService() as scraper:
        return await scraper.scrape_seo_data(product_name, category)