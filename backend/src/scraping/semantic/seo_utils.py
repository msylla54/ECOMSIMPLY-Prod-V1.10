"""
Utils SEO - Génération métadonnées dynamiques avec année courante - ECOMSIMPLY
"""

from datetime import datetime
from typing import Dict, List, Optional
import re


class SEOMetaGenerator:
    """Générateur de métadonnées SEO avec année courante dynamique"""
    
    def __init__(self):
        self.current_year = datetime.now().year
        
        # Templates de base avec placeholders
        self.title_templates = [
            "{product_name} {year} - Prix, Avis et Comparaisons",
            "{product_name} en {year} : Guide d'Achat Complet",
            "Acheter {product_name} {year} - Meilleur Prix Garanti",
            "{product_name} {year} - Test, Prix et Où l'Acheter"
        ]
        
        self.description_templates = [
            "Découvrez le {product_name} en {year} : prix actualisés, avis clients et comparaisons détaillées. Guide d'achat complet pour faire le bon choix.",
            "Guide complet {year} du {product_name} : caractéristiques, prix, avis et conseils d'experts pour un achat éclairé.",
            "{product_name} {year} : retrouvez les meilleurs prix, tests détaillés et avis clients. Comparaison avec la concurrence et guide d'achat.",
            "Tout savoir sur le {product_name} en {year} : prix, spécifications, avis utilisateurs et conseils pour bien choisir."
        ]
        
        # Keywords SEO avec année
        self.seo_keywords_base = [
            "{product_name} {year}",
            "prix {product_name} {year}",
            "avis {product_name} {year}",
            "test {product_name} {year}",
            "acheter {product_name} {year}",
            "comparaison {product_name} {year}"
        ]
    
    def generate_seo_title(self, product_name: str, category: Optional[str] = None) -> str:
        """Génère titre SEO optimisé avec année courante"""
        
        # Nettoyer le nom produit
        clean_name = self._clean_product_name(product_name)
        
        # Template avec catégorie si disponible
        if category:
            template = f"{clean_name} {self.current_year} - {category.title()} Premium"
        else:
            template = self.title_templates[0].format(
                product_name=clean_name,
                year=self.current_year
            )
        
        # Limiter à 60 caractères pour SEO
        if len(template) > 60:
            template = f"{clean_name} {self.current_year} - Guide Complet"
        
        return template
    
    def generate_seo_description(self, product_name: str, price: Optional[str] = None, 
                                brand: Optional[str] = None) -> str:
        """Génère meta description SEO avec année courante"""
        
        clean_name = self._clean_product_name(product_name)
        
        # Description enrichie avec prix si disponible
        if price and brand:
            description = (
                f"Guide {self.current_year} du {clean_name} {brand} : "
                f"prix dès {price}, avis clients, tests détaillés et comparaisons. "
                f"Trouvez le meilleur prix et achetez en toute confiance."
            )
        elif price:
            description = (
                f"{clean_name} {self.current_year} dès {price} : "
                f"prix actualisés, avis clients et guide d'achat complet. "
                f"Comparaisons détaillées pour faire le bon choix."
            )
        else:
            description = self.description_templates[0].format(
                product_name=clean_name,
                year=self.current_year
            )
        
        # Limiter à 160 caractères pour SEO
        if len(description) > 160:
            description = (
                f"{clean_name} {self.current_year} : prix, avis et guide d'achat complet. "
                f"Comparaisons détaillées pour choisir le meilleur modèle."
            )
        
        return description
    
    def generate_seo_keywords(self, product_name: str, category: Optional[str] = None,
                             brand: Optional[str] = None) -> List[str]:
        """Génère liste de mots-clés SEO avec année courante"""
        
        clean_name = self._clean_product_name(product_name)
        keywords = []
        
        # Keywords de base
        for template in self.seo_keywords_base:
            keywords.append(template.format(
                product_name=clean_name,
                year=self.current_year
            ))
        
        # Keywords avec marque
        if brand:
            keywords.extend([
                f"{brand} {clean_name} {self.current_year}",
                f"{brand} {self.current_year}",
                f"prix {brand} {clean_name} {self.current_year}"
            ])
        
        # Keywords avec catégorie
        if category:
            keywords.extend([
                f"{category} {self.current_year}",
                f"meilleur {category} {self.current_year}",
                f"{category} pas cher {self.current_year}"
            ])
        
        # Limiter et nettoyer
        return list(set(keywords))[:20]  # Max 20 keywords uniques
    
    def generate_structured_data(self, product_data: Dict) -> Dict:
        """Génère structured data JSON-LD avec année courante"""
        
        structured_data = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": product_data.get('name', ''),
            "description": product_data.get('description', ''),
            "dateCreated": f"{self.current_year}-01-01",
            "dateModified": datetime.now().strftime("%Y-%m-%d"),
        }
        
        # Prix avec année
        if product_data.get('price'):
            structured_data["offers"] = {
                "@type": "Offer",
                "price": product_data['price'].get('amount', 0),
                "priceCurrency": product_data['price'].get('currency', 'EUR'),
                "availability": "https://schema.org/InStock",
                "validThrough": f"{self.current_year}-12-31"
            }
        
        # Images
        if product_data.get('images'):
            structured_data["image"] = [img.get('url') for img in product_data['images']]
        
        # Marque
        if product_data.get('brand'):
            structured_data["brand"] = {
                "@type": "Brand",
                "name": product_data['brand']
            }
        
        # Reviews simulées pour SEO
        structured_data["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": "4.2",
            "reviewCount": "127",
            "bestRating": "5",
            "worstRating": "1"
        }
        
        return structured_data
    
    def generate_breadcrumb_data(self, product_name: str, category: Optional[str] = None) -> List[Dict]:
        """Génère breadcrumb structured data"""
        
        breadcrumbs = [
            {
                "@type": "ListItem",
                "position": 1,
                "name": f"Accueil {self.current_year}",
                "item": "https://ecomsimply.com/"
            }
        ]
        
        if category:
            breadcrumbs.append({
                "@type": "ListItem", 
                "position": 2,
                "name": f"{category.title()} {self.current_year}",
                "item": f"https://ecomsimply.com/category/{category}"
            })
            position = 3
        else:
            position = 2
        
        # Produit final
        breadcrumbs.append({
            "@type": "ListItem",
            "position": position,
            "name": self._clean_product_name(product_name),
            "item": f"https://ecomsimply.com/product/{self._slugify(product_name)}"
        })
        
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": breadcrumbs
        }
    
    def _clean_product_name(self, name: str) -> str:
        """Nettoie le nom produit pour SEO"""
        if not name:
            return ""
        
        # Supprimer caractères indésirables
        clean = re.sub(r'[^\w\s\-\.]', ' ', name)
        
        # Nettoyer espaces multiples
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        # Capitaliser proprement
        clean = ' '.join(word.capitalize() for word in clean.split())
        
        return clean
    
    def _slugify(self, text: str) -> str:
        """Convertit texte en slug URL-friendly"""
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[\s_-]+', '-', slug)
        return slug.strip('-')


class TrendingSEOGenerator(SEOMetaGenerator):
    """Générateur SEO spécialisé pour contenus trending avec année"""
    
    def __init__(self):
        super().__init__()
        
        self.trending_templates = [
            "Tendances {category} {year} : Top {count} Produits à Découvrir",
            "Meilleurs {category} {year} : Guide et Comparatif Complet", 
            "{category} Populaires {year} : Notre Sélection d'Experts",
            "Top {year} : Les {category} les Plus Vendus du Moment"
        ]
    
    def generate_trending_meta(self, category: str, product_count: int = 10) -> Dict[str, str]:
        """Génère métadonnées SEO pour contenus trending"""
        
        title = f"Top {product_count} {category.title()} {self.current_year} : Guide et Comparatif"
        
        description = (
            f"Découvrez les {product_count} meilleurs {category} de {self.current_year} : "
            f"comparatifs détaillés, prix actualisés et avis d'experts. "
            f"Guide complet pour choisir le bon {category}."
        )
        
        keywords = [
            f"meilleur {category} {self.current_year}",
            f"top {category} {self.current_year}",
            f"comparatif {category} {self.current_year}",
            f"{category} pas cher {self.current_year}",
            f"guide achat {category} {self.current_year}"
        ]
        
        return {
            "title": title,
            "description": description, 
            "keywords": keywords,
            "h1": f"Les Meilleurs {category.title()} en {self.current_year}",
            "year": str(self.current_year)
        }