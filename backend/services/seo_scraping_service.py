"""
SEO Scraping Service - ECOMSIMPLY
✅ TÂCHE 2 : Service pour le scraping concurrentiel et l'extraction de données SEO
Génération de 20 tags uniques avec diversité Jaccard < 0.7
"""

import aiohttp
import asyncio
import time
import math
from datetime import datetime
from aiohttp_retry import RetryClient, ExponentialRetry
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional, Set

# Import du logging structuré
from .logging_service import ecomsimply_logger, log_error, log_info, log_operation

def get_current_year() -> int:
    """Retourne l'année courante pour usage dynamique dans les tags SEO"""
    return datetime.now().year

class SEOTagGenerator:
    """✅ TÂCHE 2 : Générateur de tags SEO avec diversité Jaccard"""
    
    def __init__(self):
        self.target_tag_count = 20
        self.max_jaccard_similarity = 0.7
        self.min_tag_length = 2
        self.max_tag_length = 5  # 2-5 mots par tag
    
    def calculate_jaccard_similarity(self, tag1: str, tag2: str) -> float:
        """Calcule la similarité Jaccard entre deux tags"""
        words1 = set(tag1.lower().split('-'))
        words2 = set(tag2.lower().split('-'))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def is_diverse_enough(self, new_tag: str, existing_tags: List[str]) -> bool:
        """Vérifie si un nouveau tag est suffisamment diversifié"""
        for existing_tag in existing_tags:
            similarity = self.calculate_jaccard_similarity(new_tag, existing_tag)
            if similarity >= self.max_jaccard_similarity:
                return False
        return True
    
    def validate_tag_format(self, tag: str) -> bool:
        """Valide le format d'un tag (2-5 mots)"""
        if not tag or not tag.strip():
            return False
        
        words = tag.split('-')
        word_count = len([w for w in words if w.strip()])
        
        return self.min_tag_length <= word_count <= self.max_tag_length
    
    def generate_20_seo_tags(
        self,
        product_name: str,
        category: Optional[str] = None,
        trending_keywords: Optional[List[str]] = None,
        ai_generated_tags: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        ✅ TÂCHE 2 : Génère 20 tags SEO uniques avec diversité Jaccard
        Priorité : tendances (8 max) → tags IA → complétion statique
        """
        log_info(
            "Démarrage génération 20 tags SEO",
            user_id=user_id,
            product_name=product_name,
            service="SEOTagGenerator",
            operation="generate_20_seo_tags",
            trending_count=len(trending_keywords or []),
            ai_tags_count=len(ai_generated_tags or [])
        )
        
        final_tags = []
        source_info = {"trending": 0, "ai": 0, "static": 0}
        
        # PHASE 1: Priorité aux mots-clés tendance (max 8)
        if trending_keywords:
            for keyword in trending_keywords[:8]:  # Maximum 8 tendances
                if len(final_tags) >= self.target_tag_count:
                    break
                
                clean_tag = self._clean_and_format_tag(keyword)
                if (clean_tag and 
                    self.validate_tag_format(clean_tag) and 
                    self.is_diverse_enough(clean_tag, final_tags) and
                    clean_tag not in final_tags):
                    
                    final_tags.append(clean_tag)
                    source_info["trending"] += 1
        
        # PHASE 2: Tags générés par IA
        if ai_generated_tags and len(final_tags) < self.target_tag_count:
            for ai_tag in ai_generated_tags:
                if len(final_tags) >= self.target_tag_count:
                    break
                
                clean_tag = self._clean_and_format_tag(ai_tag)
                if (clean_tag and 
                    self.validate_tag_format(clean_tag) and 
                    self.is_diverse_enough(clean_tag, final_tags) and
                    clean_tag not in final_tags):
                    
                    final_tags.append(clean_tag)
                    source_info["ai"] += 1
        
        # PHASE 3: Complétion avec tags statiques
        if len(final_tags) < self.target_tag_count:
            static_tags = self._generate_comprehensive_static_tags(product_name, category)
            
            for static_tag in static_tags:
                if len(final_tags) >= self.target_tag_count:
                    break
                
                clean_tag = self._clean_and_format_tag(static_tag)
                if (clean_tag and 
                    self.validate_tag_format(clean_tag) and 
                    self.is_diverse_enough(clean_tag, final_tags) and
                    clean_tag not in final_tags):
                    
                    final_tags.append(clean_tag)
                    source_info["static"] += 1
        
        # Validation finale de la diversité
        diversity_scores = self._calculate_diversity_matrix(final_tags)
        avg_diversity = sum(diversity_scores) / len(diversity_scores) if diversity_scores else 1.0
        
        result = {
            "tags": final_tags,
            "count": len(final_tags),
            "target_reached": len(final_tags) == self.target_tag_count,
            "source_breakdown": source_info,
            "diversity_score": round(1.0 - avg_diversity, 3),  # Plus haut = plus diversifié
            "average_jaccard": round(avg_diversity, 3),
            "validation_passed": all(self.validate_tag_format(tag) for tag in final_tags)
        }
        
        log_operation(
            "SEOTagGenerator",
            "generate_20_seo_tags",
            "success",
            user_id=user_id,
            product_name=product_name,
            tags_generated=len(final_tags),
            target_reached=result["target_reached"],
            diversity_score=result["diversity_score"],
            **source_info
        )
        
        return result
    
    def _clean_and_format_tag(self, tag: str) -> str:
        """Nettoie et formate un tag"""
        if not tag:
            return ""
        
        # Nettoyer
        clean = tag.strip().lower()
        clean = re.sub(r'[^a-z0-9\-\s]', '', clean)
        clean = re.sub(r'\s+', '-', clean)
        clean = re.sub(r'-+', '-', clean)
        clean = clean.strip('-')
        
        # Vérifier longueur des mots
        words = [w for w in clean.split('-') if w.strip()]
        if len(words) < self.min_tag_length or len(words) > self.max_tag_length:
            return ""
        
        return '-'.join(words)
    
    def _generate_comprehensive_static_tags(self, product_name: str, category: Optional[str] = None) -> List[str]:
        """Génère une liste complète de tags statiques pour atteindre 20"""
        static_tags = []
        
        # Tags basés sur le nom du produit
        product_words = product_name.lower().split()
        main_keyword = '-'.join(product_words)
        static_tags.append(main_keyword)
        
        # Variations du produit
        if len(product_words) > 1:
            for i, word in enumerate(product_words):
                if len(word) > 2:  # Éviter les mots trop courts
                    static_tags.append(word)
                    # Combinaisons de 2 mots
                    for j, other_word in enumerate(product_words):
                        if i != j and len(other_word) > 2:
                            static_tags.append(f"{word}-{other_word}")
        
        # Tags de catégorie
        if category:
            category_clean = category.lower().replace(' ', '-')
            static_tags.extend([
                category_clean,
                f"{category_clean}-premium",
                f"meilleur-{category_clean}",
                f"{category_clean}-qualite",
                f"{category_clean}-pas-cher"
            ])
        
        # Tags commerciaux génériques avec année dynamique
        current_year = get_current_year()
        commercial_tags = [
            "qualite-premium", "prix-competitif", "livraison-gratuite",
            "garantie-incluse", "service-client", "satisfaction-garantie",
            "nouveau-produit", "meilleur-prix", "offre-speciale",
            "reduction-exclusive", "achat-en-ligne", "commande-rapide",
            "stock-disponible", "expedition-rapide", "retour-gratuit",
            "paiement-securise", "avis-clients", "recommande-par-experts",
            f"innovation-{current_year}", "eco-responsable", "made-in-france",
            "haute-performance", "design-moderne", "technologie-avancee",
            "usage-quotidien", "parfait-pour", "ideal-cadeau",
            "rapport-qualite-prix", "choix-populaire", "tendance-actuelle"
        ]
        
        static_tags.extend(commercial_tags)
        
        # Tags saisonniers avec année dynamique
        current_year = get_current_year()
        seasonal_tags = [
            "promotion-hiver", "offre-printemps", "special-ete",
            "reduction-automne", "black-friday", "cyber-monday",
            "soldes-janvier", "rentrée-scolaire", "fete-des-meres",
            f"fete-des-peres", f"noel-{current_year}", "saint-valentin"
        ]
        
        static_tags.extend(seasonal_tags)
        
        return static_tags
    
    def _calculate_diversity_matrix(self, tags: List[str]) -> List[float]:
        """Calcule les scores de diversité entre tous les tags"""
        similarities = []
        
        for i, tag1 in enumerate(tags):
            for j, tag2 in enumerate(tags):
                if i < j:  # Éviter les doublons
                    similarity = self.calculate_jaccard_similarity(tag1, tag2)
                    similarities.append(similarity)
        
        return similarities

class SEOScrapingService:
    """Service pour le scraping SEO et analyse concurrentielle avec génération de 20 tags"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.tag_generator = SEOTagGenerator()  # ✅ TÂCHE 2
        
    async def scrape_competitor_prices(
        self,
        product_name: str,
        category: Optional[str] = None
    ) -> Dict:
        """Scraping avancé des prix concurrents avec analyse statistique"""
        
        print(f"💰 ANALYSE PRIX CONCURRENTS pour: {product_name}")
        
        # Configuration sources prix
        price_sources = [
            {
                "name": "Amazon",
                "search_url": "https://www.amazon.fr/s?k={query}",
                "selectors": [".a-price-whole", ".a-price .a-offscreen", "[data-cy=price-recipe]"],
                "weight": 0.4
            },
            {
                "name": "Fnac", 
                "search_url": "https://www.fnac.com/SearchResult/ResultList.aspx?Search={query}",
                "selectors": ["[class*='price']", "[class*='tarif']", ".userPrice"],
                "weight": 0.25
            }
        ]
        
        try:
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.8',
                'Connection': 'keep-alive',
            }
            
            all_prices = []
            sources_analyzed = []
            
            # Préparation requête avec contexte catégorie
            search_query = product_name
            if category:
                category_keywords = {
                    'électronique': 'électronique high-tech',
                    'mode': 'mode vêtements',
                    'beauté': 'beauté cosmétique',
                    'maison': 'maison décoration',
                    'sport': 'sport fitness',
                    'auto': 'automobile pièces'
                }
                if category.lower() in category_keywords:
                    search_query = f"{product_name} {category_keywords[category.lower()]}"
            
            async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as session:
                
                for source in price_sources:
                    try:
                        print(f"🔍 Analyse prix sur {source['name']}...")
                        
                        search_url = source['search_url'].format(query=search_query.replace(' ', '+'))
                        
                        async with session.get(search_url) as response:
                            if response.status == 200:
                                html_content = await response.text()
                                soup = BeautifulSoup(html_content, 'html.parser')
                                
                                # Recherche prix avec sélecteurs
                                source_prices = []
                                for selector in source['selectors']:
                                    elements = soup.select(selector)
                                    for element in elements[:3]:  # Limite à 3 par sélecteur
                                        price_text = element.get_text(strip=True)
                                        # Extraction prix avec regex
                                        price_matches = re.findall(r'(\d+)[,.](\d+)', price_text)
                                        if price_matches:
                                            try:
                                                price = float(f"{price_matches[0][0]}.{price_matches[0][1]}")
                                                if 10 <= price <= 10000:  # Validation prix raisonnable
                                                    source_prices.append({
                                                        'price': price,
                                                        'source': source['name'],
                                                        'weight': source['weight']
                                                    })
                                            except:
                                                continue
                                
                                if source_prices:
                                    all_prices.extend(source_prices)
                                    sources_analyzed.append(source['name'])
                                    print(f"✅ {source['name']}: {len(source_prices)} prix trouvés")
                            
                            await asyncio.sleep(1)  # Délai entre requêtes
                            
                    except Exception as e:
                        print(f"❌ Erreur {source['name']}: {e}")
                        continue
            
            # Analyse statistique
            if len(all_prices) == 0:
                return self._empty_price_result()
            
            return self._analyze_prices(all_prices, sources_analyzed)
            
        except Exception as e:
            print(f"❌ ERREUR ANALYSE PRIX: {e}")
            return self._empty_price_result()
    
    def _analyze_prices(self, all_prices: List[Dict], sources_analyzed: List[str]) -> Dict:
        """Analyse statistique des prix récupérés"""
        
        prices_only = [p['price'] for p in all_prices]
        weighted_prices = [(p['price'] * p['weight']) for p in all_prices]
        total_weight = sum(p['weight'] for p in all_prices)
        
        min_price = min(prices_only)
        max_price = max(prices_only)
        avg_price = sum(weighted_prices) / total_weight if total_weight > 0 else sum(prices_only) / len(prices_only)
        
        # Stratégies pricing
        price_range = max_price - min_price
        aggressive_price = min_price + (price_range * 0.15)
        competitive_price = avg_price
        premium_price = avg_price + (price_range * 0.25)
        
        # Distribution
        low_threshold = min_price + (price_range * 0.33)
        high_threshold = min_price + (price_range * 0.67)
        
        price_distribution = {
            'low': len([p for p in prices_only if p <= low_threshold]),
            'medium': len([p for p in prices_only if low_threshold < p <= high_threshold]),
            'high': len([p for p in prices_only if p > high_threshold])
        }
        
        print(f"📊 ANALYSE: {len(all_prices)} prix | Fourchette: {min_price:.2f}€ - {max_price:.2f}€")
        
        return {
            'found_prices': len(all_prices),
            'min_price': min_price,
            'max_price': max_price,
            'avg_price': avg_price,
            'sites_analyzed': sources_analyzed,
            'recommended_price_range': {
                'aggressive': round(aggressive_price, 2),
                'competitive': round(competitive_price, 2),
                'premium': round(premium_price, 2)
            },
            'price_distribution': price_distribution,
            'confidence_score': min(100, (len(all_prices) / 10) * 100)
        }
    
    def _empty_price_result(self) -> Dict:
        """Résultat vide en cas d'échec du scraping"""
        return {
            'found_prices': 0,
            'sites_analyzed': [],
            'confidence_score': 0
        }
    
    async def scrape_seo_data(
        self,
        product_name: str,
        category: Optional[str] = None
    ) -> Dict:
        """Scraping de données SEO depuis diverses sources"""
        
        print(f"🔍 SCRAPING SEO DATA pour: {product_name}")
        
        seo_data = {
            "titles": [],
            "descriptions": [],
            "keywords": [],
            "features": [],
            "competitors": []
        }
        
        try:
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            # Sources SEO à analyser
            search_urls = [
                f"https://www.google.fr/search?q={product_name.replace(' ', '+')}+avis",
                f"https://www.amazon.fr/s?k={product_name.replace(' ', '+')}"
            ]
            
            async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as session:
                
                for url in search_urls:
                    try:
                        async with session.get(url) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')
                                
                                # Extraction titres
                                titles = soup.find_all(['h1', 'h2', 'h3'], limit=5)
                                for title in titles:
                                    title_text = title.get_text(strip=True)
                                    if product_name.lower() in title_text.lower():
                                        seo_data["titles"].append(title_text)
                                
                                # Extraction descriptions
                                descriptions = soup.find_all(['p', 'div'], limit=10)
                                for desc in descriptions:
                                    desc_text = desc.get_text(strip=True)
                                    if len(desc_text) > 50 and product_name.lower() in desc_text.lower():
                                        seo_data["descriptions"].append(desc_text[:200])
                                
                                # Extraction mots-clés depuis meta tags
                                meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
                                if meta_keywords and meta_keywords.get('content'):
                                    keywords = meta_keywords['content'].split(',')
                                    seo_data["keywords"].extend([k.strip() for k in keywords[:10]])
                        
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        print(f"❌ Erreur scraping SEO: {e}")
                        continue
            
            # Nettoyage et déduplication
            seo_data = self._clean_seo_data(seo_data)
            
        except Exception as e:
            print(f"❌ Erreur scraping SEO général: {e}")
        
        print(f"📋 SEO DATA: {len(seo_data['titles'])} titres, {len(seo_data['keywords'])} mots-clés")
        return seo_data
    
    def _clean_seo_data(self, seo_data: Dict) -> Dict:
        """Nettoyage et déduplication des données SEO"""
        
        # Déduplication des titres
        seo_data["titles"] = list(dict.fromkeys(seo_data["titles"]))[:5]
        
        # Déduplication des descriptions
        seo_data["descriptions"] = list(dict.fromkeys(seo_data["descriptions"]))[:5]
        
        # Nettoyage des mots-clés
        cleaned_keywords = []
        for keyword in seo_data["keywords"]:
            clean_kw = keyword.strip().lower()
            if len(clean_kw) > 2 and clean_kw not in cleaned_keywords:
                cleaned_keywords.append(clean_kw)
        seo_data["keywords"] = cleaned_keywords[:10]
        
        return seo_data
    
    async def fetch_trending_keywords(
        self,
        product_name: str,
        category: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        ✅ PHASE 5: Récupération de mots-clés tendance avec source tracking
        Retourne: {"keywords": [...], "source": "trending|static", "confidence": 0-100}
        """
        
        log_info(
            "Recherche mots-clés tendance",
            user_id=user_id,
            product_name=product_name,
            service="SEOScrapingService",
            operation="fetch_trending_keywords",
            category=category
        )
        
        trending_keywords = []
        confidence_score = 0
        source = "static"  # Par défaut
        
        try:
            # Simulation d'API Google Trends (en production, utiliser la vraie API)
            # Pour l'instant, on génère des tendances basées sur les patterns actuels
            
            # Base de données de tendances simulée (mise à jour régulièrement avec année dynamique)
            current_year = get_current_year()
            trends_database = {
                "électronique": {
                    str(current_year): ["eco-responsable", "intelligence-artificielle", "5g", "durabilite", "reconditionne"],
                    "seasonal": ["black-friday", "cyber-monday", "rentrée", "noel"]
                },
                "smartphone": {
                    str(current_year): ["camera-pro", "batterie-longue-duree", "ecran-oled", "charge-rapide", "photo-nuit"],
                    "seasonal": [f"comparatif-{current_year}", "meilleur-rapport-qualite-prix"]
                },
                "mode": {
                    str(current_year): ["mode-durable", "seconde-main", "upcycling", "slow-fashion", "made-in-france"],
                    "seasonal": ["tendance-automne", "collection-hiver", "soldes"]
                },
                "beauté": {
                    str(current_year): ["cosmetique-bio", "zero-dechet", "skincare-routine", "anti-age-naturel", "vegan"],
                    "seasonal": ["routine-hiver", "protection-solaire"]
                }
            }
            
            # Recherche des tendances pour la catégorie avec année dynamique
            category_trends = []
            if category and category.lower() in trends_database:
                category_trends.extend(trends_database[category.lower()].get(str(current_year), []))
                category_trends.extend(trends_database[category.lower()].get("seasonal", []))
                source = "trending"
                confidence_score = 75
            
            # Recherche générique basée sur le nom du produit
            product_trends = []
            product_lower = product_name.lower()
            
            # Détection automatique de catégorie si non fournie avec année dynamique
            if not category_trends:
                for cat, trends_data in trends_database.items():
                    if any(keyword in product_lower for keyword in cat.split()):
                        category_trends.extend(trends_data.get(str(current_year), []))
                        source = "trending"
                        confidence_score = 60
                        break
            
            # Génération de mots-clés tendance spécifiques au produit
            product_based_trends = []
            
            # Tendances génériques avec année dynamique
            general_trends = [
                str(current_year), "nouveau", "derniere-generation", "eco-friendly", 
                "innovation", "performance", "qualite-prix", "livraison-rapide"
            ]
            
            # Sélection intelligente basée sur le produit
            for trend in general_trends[:3]:  # Top 3 tendances générales
                product_based_trends.append(f"{product_name.lower().replace(' ', '-')}-{trend}")
            
            # Combinaison des différentes sources
            all_trends = category_trends + product_based_trends
            
            # Nettoyage et validation
            for trend in all_trends[:8]:  # Maximum 8 tendances
                clean_trend = self._clean_keyword(trend)
                if clean_trend and len(clean_trend) > 3:
                    trending_keywords.append(clean_trend)
            
            # Augmenter le score de confiance si on a trouvé des tendances
            if trending_keywords:
                if source == "static":
                    source = "trending"
                    confidence_score = 50
                
                log_info(
                    f"Mots-clés tendance trouvés: {len(trending_keywords)}",
                    user_id=user_id,
                    product_name=product_name,
                    service="SEOScrapingService",
                    keywords_found=len(trending_keywords),
                    confidence=confidence_score,
                    source=source
                )
            else:
                # Fallback vers mots-clés statiques de base
                log_info(
                    "Aucune tendance spécifique, utilisation mots-clés statiques",
                    user_id=user_id,
                    product_name=product_name,
                    service="SEOScrapingService"
                )
                
                static_keywords = self._generate_static_keywords(product_name, category)
                trending_keywords = static_keywords
                source = "static"
                confidence_score = 30
        
        except Exception as e:
            log_error(
                "Erreur récupération mots-clés tendance",
                user_id=user_id,
                product_name=product_name,
                error_source="SEOScrapingService.fetch_trending_keywords",
                exception=e
            )
            
            # Fallback vers statique
            trending_keywords = self._generate_static_keywords(product_name, category)
            source = "static"
            confidence_score = 20
        
        result = {
            "keywords": trending_keywords,
            "source": source,
            "confidence": confidence_score,
            "total_found": len(trending_keywords)
        }
        
        log_operation(
            "SEOScrapingService",
            "fetch_trending_keywords",
            "success",
            user_id=user_id,
            product_name=product_name,
            keywords_count=len(trending_keywords),
            source=source,
            confidence=confidence_score
        )
        
        return result
    
    def _clean_keyword(self, keyword: str) -> str:
        """Nettoyage d'un mot-clé"""
        if not keyword:
            return ""
        
        # Nettoyer et normaliser
        clean = keyword.strip().lower()
        clean = re.sub(r'[^a-z0-9\-\s]', '', clean)  # Garder lettres, chiffres, tirets, espaces
        clean = re.sub(r'\s+', '-', clean)  # Remplacer espaces par tirets
        clean = re.sub(r'-+', '-', clean)  # Éviter tirets multiples
        clean = clean.strip('-')  # Enlever tirets début/fin
        
        return clean
    
    def _generate_static_keywords(self, product_name: str, category: Optional[str] = None) -> List[str]:
        """Génération de mots-clés statiques de base"""
        
        keywords = []
        
        # Mot-clé principal basé sur le nom
        main_keyword = product_name.lower().replace(' ', '-')
        keywords.append(main_keyword)
        
        # Mots-clés catégoriels
        if category:
            keywords.append(category.lower())
            keywords.append(f"{category.lower()}-qualite")
        
        # Mots-clés génériques utiles
        generic_keywords = [
            "pas-cher", "qualite-prix", "livraison-gratuite", 
            "garantie", "avis-clients", "promo"
        ]
        
        keywords.extend(generic_keywords[:4])
        
        return keywords[:8]  # Maximum 8 mots-clés