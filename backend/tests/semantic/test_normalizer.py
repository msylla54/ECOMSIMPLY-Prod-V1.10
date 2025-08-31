"""
Tests pour DataNormalizer - nettoyage et normalisation des données
"""

import pytest
from decimal import Decimal

# Import du module à tester
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from scraping.semantic.normalizer import DataNormalizer
from scraping.semantic.product_dto import Currency, PriceDTO


class TestDataNormalizer:
    """Tests pour la classe DataNormalizer"""
    
    @pytest.fixture
    def normalizer(self):
        return DataNormalizer()
    
    def test_normalize_title_basic(self, normalizer):
        """Test normalisation titre basique"""
        # HTML entities
        title = normalizer.normalize_title("iPhone 15 Pro &amp; Accessoires")
        assert title == "iPhone 15 Pro & Accessoires"
        
        # Whitespace excessif
        title = normalizer.normalize_title("  MacBook   Pro    M3  ")
        assert title == "MacBook Pro M3"
        
        # Titre vide
        title = normalizer.normalize_title("")
        assert title == "Titre non disponible"
    
    def test_normalize_title_length_limit(self, normalizer):
        """Test limitation longueur titre"""
        long_title = "A" * 600  # Plus de 500 caractères
        normalized = normalizer.normalize_title(long_title)
        
        assert len(normalized) == 500
        assert normalized.endswith("...")
    
    def test_normalize_description_html_sanitization(self, normalizer):
        """Test sanitization HTML description"""
        # Tags autorisés conservés
        html = "<p>Description avec <strong>texte important</strong> et <em>emphase</em>.</p>"
        result = normalizer.normalize_description_html(html)
        assert "<strong>" in result
        assert "<em>" in result
        assert "<p>" in result
    
    def test_normalize_description_html_dangerous_tags_removed(self, normalizer):
        """Test suppression tags dangereux"""
        html = """
        <div>
            <p>Description sécurisée</p>
            <script>alert('XSS')</script>
            <img src="malicious.jpg" onerror="alert('XSS')" />
            <a href="javascript:void(0)">Lien dangereux</a>
        </div>
        """
        result = normalizer.normalize_description_html(html)
        
        # Tags dangereux supprimés
        assert "<script>" not in result
        assert "<img>" not in result
        assert "<a>" not in result
        assert "<div>" not in result
        
        # Contenu texte conservé
        assert "Description sécurisée" in result
        assert "Lien dangereux" in result  # Texte conservé, tag supprimé
    
    def test_normalize_description_html_attributes_removed(self, normalizer):
        """Test suppression attributs HTML"""
        html = '<p class="description" id="desc" style="color:red;">Texte</p>'
        result = normalizer.normalize_description_html(html)
        
        assert 'class=' not in result
        assert 'id=' not in result
        assert 'style=' not in result
        assert 'Texte' in result
    
    def test_normalize_description_empty_fallback(self, normalizer):
        """Test fallback description vide"""
        result = normalizer.normalize_description_html("")
        assert result == "<p>Description non disponible</p>"
        
        result = normalizer.normalize_description_html("   ")
        assert result == "<p>Description non disponible</p>"
    
    def test_normalize_price_eur_format(self, normalizer):
        """Test normalisation prix format européen"""
        # Format 1.234,56 €
        price = normalizer.normalize_price("€ 1.234,56", "EUR")
        assert price is not None
        assert price.amount == Decimal('1234.56')
        assert price.currency == Currency.EUR
        assert price.original_text == "€ 1.234,56"
        
        # Format 1234,56 EUR
        price = normalizer.normalize_price("1234,56 EUR")
        assert price is not None
        assert price.amount == Decimal('1234.56')
        assert price.currency == Currency.EUR
    
    def test_normalize_price_usd_format(self, normalizer):
        """Test normalisation prix format USD"""
        # Format $1,234.56
        price = normalizer.normalize_price("$1,234.56", "USD")
        assert price is not None
        assert price.amount == Decimal('1234.56')
        assert price.currency == Currency.USD
        
        # Format 1234.56 USD
        price = normalizer.normalize_price("1234.56 USD")
        assert price is not None
        assert price.amount == Decimal('1234.56')
        assert price.currency == Currency.USD
    
    def test_normalize_price_gbp_format(self, normalizer):
        """Test normalisation prix format GBP"""
        # Format £1,234.56
        price = normalizer.normalize_price("£1,234.56")
        assert price is not None
        assert price.amount == Decimal('1234.56')
        assert price.currency == Currency.GBP
        
        # Format 1234.56 GBP
        price = normalizer.normalize_price("1234.56 GBP")
        assert price is not None
        assert price.amount == Decimal('1234.56')
        assert price.currency == Currency.GBP
    
    def test_normalize_price_currency_hint_fallback(self, normalizer):
        """Test fallback vers currency_hint"""
        # Prix sans symbole/code devise → utilise hint
        price = normalizer.normalize_price("899.99", "EUR")
        assert price is not None
        assert price.amount == Decimal('899.99')
        assert price.currency == Currency.EUR
    
    def test_normalize_price_invalid_cases(self, normalizer):
        """Test cas invalides prix"""
        # Prix vide
        assert normalizer.normalize_price("") is None
        assert normalizer.normalize_price(None) is None
        
        # Pas de partie numérique
        assert normalizer.normalize_price("Nous contacter") is None
        assert normalizer.normalize_price("Sur devis") is None
        
        # Devise non supportée
        assert normalizer.normalize_price("100 YEN") is None
        
        # Montant négatif (théoriquement filtré)
        result = normalizer._extract_numeric_amount("-100.50")
        assert result is None
    
    def test_extract_numeric_amount_european_format(self, normalizer):
        """Test extraction montant format européen"""
        # Format 1.234,56
        amount = normalizer._extract_numeric_amount("€ 1.234,56")
        assert amount == Decimal('1234.56')
        
        # Format 1234,56
        amount = normalizer._extract_numeric_amount("1234,56 EUR")
        assert amount == Decimal('1234.56')
        
        # Format avec espaces
        amount = normalizer._extract_numeric_amount("1 234,56")
        assert amount == Decimal('1234.56')
    
    def test_extract_numeric_amount_american_format(self, normalizer):
        """Test extraction montant format américain"""
        # Format 1,234.56
        amount = normalizer._extract_numeric_amount("$1,234.56")
        assert amount == Decimal('1234.56')
        
        # Format simple
        amount = normalizer._extract_numeric_amount("1234.56")
        assert amount == Decimal('1234.56')
    
    def test_extract_numeric_amount_mixed_separators(self, normalizer):
        """Test gestion séparateurs mixtes"""
        # Format européen: 1.234,56 (point = milliers, virgule = décimal)
        amount = normalizer._extract_numeric_amount("€ 1.234,56")
        assert amount == Decimal('1234.56')
        
        # Format américain: 1,234.56 (virgule = milliers, point = décimal)
        amount = normalizer._extract_numeric_amount("$1,234.56")
        assert amount == Decimal('1234.56')
        
        # Cas ambigus → dernier séparateur est décimal
        amount = normalizer._extract_numeric_amount("1.234.567,89")  # Européen
        assert amount == Decimal('1234567.89')
        
        amount = normalizer._extract_numeric_amount("1,234,567.89")  # Américain
        assert amount == Decimal('1234567.89')
    
    def test_normalize_image_urls_https_enforcement(self, normalizer):
        """Test force HTTPS sur URLs images"""
        urls = [
            "http://example.com/image1.jpg",
            "https://example.com/image2.jpg",
            "//cdn.example.com/image3.jpg",
        ]
        
        result = normalizer.normalize_image_urls(urls)
        
        # Toutes en HTTPS
        for url in result:
            assert url.startswith("https://")
        
        assert "https://example.com/image1.jpg" in result
        assert "https://example.com/image2.jpg" in result
    
    def test_normalize_image_urls_deduplication(self, normalizer):
        """Test déduplication URLs images"""
        urls = [
            "https://example.com/image1.jpg",
            "http://example.com/image1.jpg",  # Même image après conversion HTTPS
            "https://example.com/image2.jpg",
            "https://example.com/image2.jpg",  # Doublon exact
        ]
        
        result = normalizer.normalize_image_urls(urls)
        
        # Pas de doublons
        assert len(result) == len(set(result))
        assert len(result) == 2  # image1 et image2 uniques
    
    def test_normalize_image_urls_limit_8_max(self, normalizer):
        """Test limitation 8 images maximum"""
        urls = [f"https://example.com/image{i}.jpg" for i in range(15)]
        
        result = normalizer.normalize_image_urls(urls)
        
        assert len(result) <= 8
    
    def test_normalize_image_urls_filter_invalid(self, normalizer):
        """Test filtrage URLs invalides"""
        urls = [
            "https://example.com/valid.jpg",
            "ftp://example.com/invalid.jpg",  # Protocole non supporté
            "",  # URL vide
            None,  # URL None
            "not-a-url",  # URL malformée
            "javascript:alert('xss')",  # URL dangereuse
        ]
        
        result = normalizer.normalize_image_urls(urls)
        
        assert len(result) == 1
        assert result[0] == "https://example.com/valid.jpg"
    
    def test_normalize_attributes_basic(self, normalizer):
        """Test normalisation attributs basique"""
        attributes = {
            "Brand": "Apple",
            "Model Number": "A1234", 
            "Storage Size": "256 GB",
            "": "valeur_vide_clé",  # Clé vide
            "Color": "",  # Valeur vide
            "Weight": "   195 g   ",  # Whitespace
        }
        
        result = normalizer.normalize_attributes(attributes)
        
        assert result['brand'] == 'Apple'
        assert result['model_number'] == 'A1234'
        assert result['storage_size'] == '256 GB'
        assert result['weight'] == '195 g'
        
        # Clés/valeurs vides filtrées
        assert '' not in result
        assert 'color' not in result
    
    def test_normalize_attributes_html_entities(self, normalizer):
        """Test décodage HTML entities dans attributs"""
        attributes = {
            "Description": "Écran &quot;Retina&quot; &amp; processeur M3",
            "Features": "&lt;strong&gt;Performance&lt;/strong&gt;"
        }
        
        result = normalizer.normalize_attributes(attributes)
        
        assert result['description'] == 'Écran "Retina" & processeur M3'
        assert result['features'] == '<strong>Performance</strong>'
    
    def test_normalize_attributes_length_limit(self, normalizer):
        """Test limitation longueur valeurs attributs"""
        long_value = "A" * 250  # Plus de 200 caractères
        attributes = {"long_desc": long_value}
        
        result = normalizer.normalize_attributes(attributes)
        
        assert len(result['long_desc']) == 200
        assert result['long_desc'].endswith("...")
    
    def test_validate_extraction_quality_complete(self, normalizer):
        """Test validation qualité extraction complète"""
        parsed_data = {
            'title': 'iPhone 15 Pro',
            'description_html': '<p>Smartphone premium avec processeur A17 Pro et appareil photo professionnel</p>',
            'price_text': '€ 1.199,00',
            'currency_hint': 'EUR',
            'image_urls': ['https://example.com/image1.jpg', 'https://example.com/image2.jpg'],
            'attributes': {'brand': 'Apple', 'model': 'iPhone 15 Pro'}
        }
        
        is_valid, issues = normalizer.validate_extraction_quality(parsed_data)
        
        assert is_valid is True
        # Peut avoir des warnings mais pas d'erreurs critiques
        critical_issues = [issue for issue in issues if not issue.endswith("(warning)")]
        assert len(critical_issues) == 0
    
    def test_validate_extraction_quality_missing_critical(self, normalizer):
        """Test validation avec données critiques manquantes"""
        parsed_data = {
            'title': '',  # Titre manquant
            'description_html': '<p>Description</p>',
            'price_text': None,  # Prix manquant
            'currency_hint': 'EUR',
            'image_urls': [],  # Images manquantes
            'attributes': {}
        }
        
        is_valid, issues = normalizer.validate_extraction_quality(parsed_data)
        
        assert is_valid is False
        assert len(issues) >= 3  # Au moins titre, prix, images manquants
        
        # Vérifier issues critiques
        critical_issues = [issue for issue in issues if not issue.endswith("(warning)")]
        assert "Titre non disponible" in critical_issues
        assert "Prix non détecté" in critical_issues
        assert "Aucune image détectée" in critical_issues
    
    def test_validate_extraction_quality_warnings_only(self, normalizer):
        """Test validation avec seulement des warnings (pas d'erreurs critiques)"""
        parsed_data = {
            'title': 'Produit valide',
            'description_html': '<p>Description suffisante pour validation</p>',
            'price_text': '99.99',
            'currency_hint': None,  # Warning: devise non détectée
            'image_urls': ['https://example.com/image.jpg'],
            'attributes': {}  # Warning: aucun attribut
        }
        
        is_valid, issues = normalizer.validate_extraction_quality(parsed_data)
        
        assert is_valid is True  # Warnings ne bloquent pas
        assert len(issues) >= 2  # Au moins 2 warnings
        
        # Vérifier que ce sont des warnings
        warning_issues = [issue for issue in issues if issue.endswith("(warning)")]
        assert len(warning_issues) >= 2


class TestDataNormalizerEdgeCases:
    """Tests cas limites et erreurs"""
    
    @pytest.fixture
    def normalizer(self):
        return DataNormalizer()
    
    def test_normalize_price_edge_cases(self, normalizer):
        """Test cas limites normalisation prix"""
        # Montant zéro (valide)
        price = normalizer.normalize_price("0.00 EUR")
        assert price is not None
        assert price.amount == Decimal('0')
        
        # Très grand montant
        price = normalizer.normalize_price("€ 999,999.99")
        assert price is not None
        assert price.amount == Decimal('999999.99')
        
        # Format avec beaucoup d'espaces
        price = normalizer.normalize_price("  €   1   234  ,  56   ")
        assert price is not None
        assert price.amount == Decimal('1234.56')
    
    def test_extract_numeric_amount_invalid_formats(self, normalizer):
        """Test formats numériques invalides"""
        # Seulement des séparateurs
        assert normalizer._extract_numeric_amount(".,.,") is None
        
        # Caractères alphanumériques mélangés
        assert normalizer._extract_numeric_amount("12a34.56") is None
        
        # Multiple points décimaux
        assert normalizer._extract_numeric_amount("12.34.56") is not None  # Traité comme 1234.56
        
        # Chaîne vide après nettoyage
        assert normalizer._extract_numeric_amount("€$£") is None