"""
Normalizer pour nettoyer et normaliser les données extraites - ECOMSIMPLY
"""

import re
import html
from typing import List, Dict, Optional, Tuple
from decimal import Decimal, InvalidOperation
from bs4 import BeautifulSoup
import logging

from .product_dto import Currency, PriceDTO

logger = logging.getLogger(__name__)


class DataNormalizer:
    """Normalise et nettoie les données brutes extraites"""
    
    def __init__(self):
        # Patterns prix pour extraction montant/devise
        self.currency_symbols = {
            '€': Currency.EUR,
            '$': Currency.USD, 
            '£': Currency.GBP
        }
        
        # Whitelist HTML tags autorisés
        self.allowed_html_tags = {'p', 'ul', 'li', 'strong', 'em', 'br'}
        
        # Patterns prix numériques
        self.price_clean_pattern = re.compile(r'[^\d,\.]')
        self.decimal_comma_pattern = re.compile(r'(\d+),(\d{2})(?!\d)')  # 1.234,56 format
    
    def normalize_title(self, title: str) -> str:
        """Normalise le titre produit"""
        if not title:
            return "Titre non disponible"
        
        # Décoder HTML entities
        title = html.unescape(title)
        
        # Nettoyer whitespace excessif
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Limiter longueur
        if len(title) > 500:
            title = title[:497] + "..."
        
        return title
    
    def normalize_description_html(self, description_html: str) -> str:
        """Sanitize et normalise HTML description"""
        if not description_html:
            return "<p>Description non disponible</p>"
        
        # Parse HTML
        soup = BeautifulSoup(description_html, 'html.parser')
        
        # Supprimer tags dangereux
        for tag in soup.find_all():
            if tag.name not in self.allowed_html_tags:
                # Conserver contenu texte mais supprimer tag
                tag.unwrap()
        
        # Supprimer attributs (pas d'event handlers, styles, etc.)
        for tag in soup.find_all():
            tag.attrs = {}
        
        # Décoder HTML entities
        clean_html = str(soup)
        clean_html = html.unescape(clean_html)
        
        # Nettoyer whitespace
        clean_html = re.sub(r'\s+', ' ', clean_html).strip()
        
        if not clean_html or clean_html.isspace():
            return "<p>Description non disponible</p>"
        
        return clean_html
    
    def normalize_price(self, price_text: str, currency_hint: Optional[str] = None) -> Optional[PriceDTO]:
        """
        Normalise texte prix → PriceDTO
        
        Examples:
            "€ 1.234,56" → PriceDTO(amount=1234.56, currency=EUR)
            "$1,234.56" → PriceDTO(amount=1234.56, currency=USD)
            "1234.56 EUR" → PriceDTO(amount=1234.56, currency=EUR)
        """
        if not price_text:
            return None
        
        original_text = price_text
        logger.debug(f"Normalisation prix: '{price_text}'")
        
        try:
            # 1. Détecter devise depuis symboles
            detected_currency = None
            for symbol, currency in self.currency_symbols.items():
                if symbol in price_text:
                    detected_currency = currency
                    break
            
            # 2. Détecter devise depuis codes ISO
            if not detected_currency:
                price_upper = price_text.upper()
                for currency_code in Currency:
                    if currency_code.value in price_upper:
                        detected_currency = currency_code
                        break
            
            # 3. Fallback vers currency_hint
            if not detected_currency and currency_hint:
                try:
                    detected_currency = Currency(currency_hint.upper())
                except ValueError:
                    pass
            
            if not detected_currency:
                logger.warning(f"Devise non détectée dans: '{price_text}'")
                return None
            
            # 4. Extraire partie numérique
            amount = self._extract_numeric_amount(price_text)
            if amount is None:
                logger.warning(f"Montant non extrait de: '{price_text}'")
                return None
            
            return PriceDTO(
                amount=amount,
                currency=detected_currency,
                original_text=original_text
            )
            
        except Exception as e:
            logger.error(f"Erreur normalisation prix '{price_text}': {e}")
            return None
    
    def _extract_numeric_amount(self, price_text: str) -> Optional[Decimal]:
        """Extrait montant numérique du texte prix"""
        
        # Nettoyer tout sauf chiffres, virgules, points
        numeric_part = re.sub(r'[^\d,\.]', '', price_text)
        
        if not numeric_part:
            return None
        
        # Gérer formats européens (1.234,56) vs américains (1,234.56)
        if ',' in numeric_part and '.' in numeric_part:
            # Les deux présents → déterminer lequel est décimal
            last_comma = numeric_part.rfind(',')
            last_dot = numeric_part.rfind('.')
            
            if last_comma > last_dot:
                # Format européen: 1.234,56
                numeric_part = numeric_part.replace('.', '').replace(',', '.')
            else:
                # Format américain: 1,234.56
                numeric_part = numeric_part.replace(',', '')
        
        elif ',' in numeric_part:
            # Seulement virgule → vérifier si c'est séparateur décimal
            if self.decimal_comma_pattern.search(numeric_part):
                # Format décimal européen: 1234,56
                numeric_part = numeric_part.replace(',', '.')
            else:
                # Séparateur milliers: 1,234
                numeric_part = numeric_part.replace(',', '')
        
        # Convertir en Decimal
        try:
            amount = Decimal(numeric_part)
            if amount < 0:
                return None
            return amount
        except (InvalidOperation, ValueError):
            logger.warning(f"Conversion impossible: '{numeric_part}' depuis '{price_text}'")
            return None
    
    def normalize_image_urls(self, image_urls: List[str]) -> List[str]:
        """
        Normalise liste URLs images:
        - Force HTTPS
        - Déduplique  
        - Limite à 8 max
        - Filtre URLs valides
        """
        if not image_urls:
            return []
        
        normalized_urls = []
        seen_urls = set()
        
        for url in image_urls:
            if not url or not isinstance(url, str):
                continue
            
            # Force HTTPS
            if url.startswith('http://'):
                url = url.replace('http://', 'https://', 1)
            elif not url.startswith('https://'):
                continue  # Ignorer URLs malformées
            
            # Déduplication
            if url in seen_urls:
                continue
            
            seen_urls.add(url)
            normalized_urls.append(url)
            
            # Limite performance
            if len(normalized_urls) >= 8:
                break
        
        logger.info(f"Images normalisées: {len(image_urls)} → {len(normalized_urls)} (HTTPS uniques)")
        return normalized_urls
    
    def normalize_attributes(self, attributes: Dict[str, str]) -> Dict[str, str]:
        """Normalise attributs produit"""
        if not attributes:
            return {}
        
        normalized = {}
        
        for key, value in attributes.items():
            if not key or not value:
                continue
            
            # Normaliser clé
            clean_key = key.strip().lower().replace(' ', '_')
            
            # Normaliser valeur
            clean_value = html.unescape(str(value)).strip()
            
            # Filtrer valeurs vides
            if clean_value and clean_key:
                # Limiter longueur valeur
                if len(clean_value) > 200:
                    clean_value = clean_value[:197] + "..."
                
                normalized[clean_key] = clean_value
        
        return normalized
    
    def validate_extraction_quality(self, parsed_data: Dict) -> Tuple[bool, List[str]]:
        """
        Valide la qualité des données extraites
        
        Returns:
            (is_valid, issues_list)
        """
        issues = []
        
        # Vérifications critiques
        if not parsed_data.get('title') or parsed_data['title'] == "Titre non disponible":
            issues.append("Titre non disponible")
        
        if not parsed_data.get('image_urls'):
            issues.append("Aucune image détectée")
        
        if not parsed_data.get('price_text'):
            issues.append("Prix non détecté")
        
        if not parsed_data.get('description_html') or len(parsed_data['description_html']) < 20:
            issues.append("Description insuffisante")
        
        # Warnings non bloquants
        if not parsed_data.get('currency_hint'):
            issues.append("Devise non détectée (warning)")
        
        if not parsed_data.get('attributes'):
            issues.append("Aucun attribut extrait (warning)")
        
        # Considérer valide si pas d'erreurs critiques (juste warnings OK)
        critical_issues = [issue for issue in issues if not issue.endswith("(warning)")]
        is_valid = len(critical_issues) == 0
        
        return is_valid, issues