"""
Tests pour SemanticParser - extraction données structurées depuis HTML
"""

import pytest
from bs4 import BeautifulSoup

# Import du module à tester
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from scraping.semantic.parser import SemanticParser


class TestSemanticParser:
    """Tests pour la classe SemanticParser"""
    
    @pytest.fixture
    def parser(self):
        return SemanticParser()
    
    def test_extract_title_from_og(self, parser):
        """Test extraction titre depuis OpenGraph"""
        html = """
        <html>
            <head>
                <meta property="og:title" content="iPhone 15 Pro - Apple Store" />
                <title>Page Title</title>
            </head>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        title = parser._extract_title(soup)
        assert title == "iPhone 15 Pro - Apple Store"
    
    def test_extract_title_fallback_h1(self, parser):
        """Test fallback titre depuis H1"""
        html = """
        <html>
            <body>
                <h1>Samsung Galaxy S24 Ultra</h1>
                <title>Generic Site</title>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        title = parser._extract_title(soup)
        assert title == "Samsung Galaxy S24 Ultra"
    
    def test_extract_title_schema_org(self, parser):
        """Test extraction titre Schema.org"""
        html = """
        <html>
            <body>
                <div itemprop="name">MacBook Pro 16 pouces</div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        title = parser._extract_title(soup)
        assert title == "MacBook Pro 16 pouces"
    
    def test_extract_price_text_schema_org(self, parser):
        """Test extraction prix Schema.org"""
        html = """
        <html>
            <body>
                <span itemprop="price" content="1299.99">1 299,99 €</span>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        price_text = parser._extract_price_text(soup)
        assert price_text == "1299.99"
    
    def test_extract_price_text_class(self, parser):
        """Test extraction prix par classe CSS"""
        html = """
        <html>
            <body>
                <div class="price">€ 899,50</div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        price_text = parser._extract_price_text(soup)
        assert price_text == "€ 899,50"
    
    def test_extract_price_text_pattern_matching(self, parser):
        """Test extraction prix par pattern regex dans tout le contenu"""
        html = """
        <html>
            <body>
                <p>Ce produit coûte $1,234.56 et est disponible immédiatement.</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        price_text = parser._extract_price_text(soup)
        assert price_text == "$1,234.56"
    
    def test_extract_currency_hint_domain(self, parser):
        """Test détection devise depuis domaine"""
        html = "<html><body>Test</body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        
        # Test domaine français
        currency = parser._extract_currency_hint(soup, "https://store.fr/product")
        assert currency == "EUR"
        
        # Test domaine britannique
        currency = parser._extract_currency_hint(soup, "https://store.co.uk/product")
        assert currency == "GBP"
        
        # Test domaine américain
        currency = parser._extract_currency_hint(soup, "https://store.com/product")
        assert currency == "USD"
    
    def test_extract_currency_hint_schema_org(self, parser):
        """Test devise Schema.org"""
        html = """
        <html>
            <body>
                <span itemprop="priceCurrency" content="GBP">£</span>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        currency = parser._extract_currency_hint(soup, "https://example.com")
        assert currency == "GBP"
    
    def test_extract_currency_hint_content_symbols(self, parser):
        """Test devise depuis symboles dans contenu"""
        html_eur = "<html><body><p>Prix: 100€</p></body></html>"
        html_gbp = "<html><body><p>Price: £75</p></body></html>"
        html_usd = "<html><body><p>Price: $50</p></body></html>"
        
        soup_eur = BeautifulSoup(html_eur, 'html.parser')
        currency_eur = parser._extract_currency_hint(soup_eur, "https://shop.example.fr")  # Domaine français
        assert currency_eur == "EUR"
        
        soup_gbp = BeautifulSoup(html_gbp, 'html.parser')
        currency_gbp = parser._extract_currency_hint(soup_gbp, "https://shop.example.co.uk")  # Domaine britannique
        assert currency_gbp == "GBP"
        
        soup_usd = BeautifulSoup(html_usd, 'html.parser')
        currency_usd = parser._extract_currency_hint(soup_usd, "https://shop.example.com")  # Domaine américain
        assert currency_usd == "USD"
    
    def test_extract_image_urls_og_priority(self, parser):
        """Test extraction images avec priorité OpenGraph"""
        html = """
        <html>
            <head>
                <meta property="og:image" content="product-main.jpg" />
            </head>
            <body>
                <img src="other-image.jpg" />
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        base_url = "https://store.example.com/product/"
        
        image_urls = parser._extract_image_urls(soup, base_url)
        
        assert len(image_urls) >= 1
        assert "https://store.example.com/product/product-main.jpg" in image_urls[0]
    
    def test_extract_image_urls_relative_to_absolute(self, parser):
        """Test résolution URLs relatives en absolues HTTPS"""
        html = """
        <html>
            <body>
                <img src="/images/product1.jpg" />
                <img src="images/product2.jpg" />
                <img src="http://example.com/product3.jpg" />
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        base_url = "https://store.example.com/product/"
        
        image_urls = parser._extract_image_urls(soup, base_url)
        
        # Toutes les URLs doivent être absolues et HTTPS
        for url in image_urls:
            assert url.startswith("https://")
        
        # Vérifier résolution relative
        assert any("https://store.example.com/images/product1.jpg" in url for url in image_urls)
        assert any("https://store.example.com/product/images/product2.jpg" in url for url in image_urls)
        assert any("https://example.com/product3.jpg" in url for url in image_urls)
    
    def test_extract_image_urls_deduplication(self, parser):
        """Test déduplication des URLs images"""
        html = """
        <html>
            <head>
                <meta property="og:image" content="same-image.jpg" />
            </head>
            <body>
                <img src="same-image.jpg" />
                <img src="same-image.jpg" />
                <img src="different-image.jpg" />
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        base_url = "https://store.example.com/"
        
        image_urls = parser._extract_image_urls(soup, base_url)
        
        # Déduplication: même URL ne doit apparaître qu'une fois
        assert len(set(image_urls)) == len(image_urls)  # Pas de doublons
        assert len(image_urls) == 2  # same-image.jpg + different-image.jpg
    
    def test_extract_image_urls_limit_8_max(self, parser):
        """Test limitation à 8 images maximum"""
        # Générer HTML avec 15 images
        img_tags = [f'<img src="image{i}.jpg" />' for i in range(15)]
        html = f"""
        <html>
            <body>
                {''.join(img_tags)}
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        base_url = "https://store.example.com/"
        
        image_urls = parser._extract_image_urls(soup, base_url)
        
        # Maximum 8 images
        assert len(image_urls) <= 8
    
    def test_extract_attributes_schema_org(self, parser):
        """Test extraction attributs Schema.org"""
        html = """
        <html>
            <body>
                <div itemprop="brand">Apple</div>
                <div itemprop="model">iPhone 15 Pro</div>
                <div itemprop="sku">APL-IPH15P-256GB</div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        attributes = parser._extract_attributes(soup)
        
        assert attributes['brand'] == 'Apple'
        assert attributes['model'] == 'iPhone 15 Pro'
        assert attributes['sku'] == 'APL-IPH15P-256GB'
    
    def test_extract_attributes_opengraph(self, parser):
        """Test extraction attributs OpenGraph product"""
        html = """
        <html>
            <head>
                <meta property="product:brand" content="Samsung" />
                <meta property="product:category" content="Smartphones" />
                <meta property="product:price:amount" content="899.99" />
                <meta property="product:price:currency" content="EUR" />
            </head>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        attributes = parser._extract_attributes(soup)
        
        assert attributes['brand'] == 'Samsung'
        assert attributes['category'] == 'Smartphones'
        assert attributes['price_amount'] == '899.99'
        assert attributes['price_currency'] == 'EUR'
    
    def test_parse_html_complete_integration(self, parser):
        """Test intégration complète parse_html"""
        html = """
        <html lang="fr">
            <head>
                <meta property="og:title" content="MacBook Pro M3 14 pouces" />
                <meta property="og:description" content="Le MacBook Pro le plus avancé jamais créé" />
                <meta property="og:image" content="/images/macbook-main.jpg" />
                <meta property="product:brand" content="Apple" />
                <meta property="product:price:currency" content="EUR" />
            </head>
            <body>
                <div class="price" itemprop="price">2 499,00 €</div>
                <img src="/images/macbook-side.jpg" alt="Vue de côté" />
                <img src="/images/macbook-back.jpg" alt="Vue arrière" />
            </body>
        </html>
        """
        base_url = "https://store.apple.fr/product/"  # Domaine français pour EUR
        
        result = parser.parse_html(html, base_url)
        
        # Vérifier structure complète
        assert result['title'] == "MacBook Pro M3 14 pouces"
        assert "MacBook Pro le plus avancé" in result['description_html']
        assert result['price_text'] == "2 499,00 €"
        assert result['currency_hint'] == "EUR"  # Depuis domaine .fr + langue FR
        assert len(result['image_urls']) == 3  # og:image + 2 img
        assert result['attributes']['brand'] == 'Apple'
        
        # Vérifier HTTPS forcé
        for url in result['image_urls']:
            assert url.startswith("https://")


class TestSemanticParserEdgeCases:
    """Tests cas limites et erreurs"""
    
    @pytest.fixture
    def parser(self):
        return SemanticParser()
    
    def test_parse_empty_html(self, parser):
        """Test HTML vide ou malformé"""
        result = parser.parse_html("", "https://example.fr")  # Domaine français pour pas de USD par défaut
        
        assert result['title'] == "Titre non disponible"
        assert result['description_html'] == "<p>Description non disponible</p>"
        assert result['price_text'] is None
        assert result['currency_hint'] == "EUR"  # Depuis domaine .fr
        assert result['image_urls'] == []
        assert result['attributes'] == {}
    
    def test_parse_no_content_html(self, parser):
        """Test HTML sans contenu utile"""
        html = "<html><head></head><body></body></html>"
        result = parser.parse_html(html, "https://example.com")
        
        assert result['title'] == "Titre non disponible"
        assert result['price_text'] is None
        assert len(result['image_urls']) == 0
    
    def test_extract_price_no_valid_pattern(self, parser):
        """Test extraction prix sans pattern valide"""
        html = """
        <html>
            <body>
                <div class="price">Nous contacter</div>
                <div class="amount">Sur devis</div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        price_text = parser._extract_price_text(soup)
        
        assert price_text is None
    
    def test_force_https_edge_cases(self, parser):
        """Test conversion HTTPS cas limites"""
        # HTTP → HTTPS
        assert parser._force_https("http://example.com/image.jpg") == "https://example.com/image.jpg"
        
        # Déjà HTTPS → inchangé
        assert parser._force_https("https://example.com/image.jpg") == "https://example.com/image.jpg"
        
        # URL relative → ajout HTTPS
        assert parser._force_https("//cdn.example.com/image.jpg") == "https://cdn.example.com/image.jpg"
        assert parser._force_https("cdn.example.com/image.jpg") == "https://cdn.example.com/image.jpg"