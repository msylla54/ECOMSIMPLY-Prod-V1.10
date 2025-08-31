"""
Tests pour ProductDTO - validation et structure données produit
"""

import pytest
from decimal import Decimal
from pydantic import ValidationError
import time

# Import du module à tester
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from scraping.semantic.product_dto import (
    ProductDTO, ImageDTO, PriceDTO, Currency, ProductStatus, ProductPlaceholder
)


class TestImageDTO:
    """Tests pour ImageDTO"""
    
    def test_image_dto_valid(self):
        """Test création ImageDTO valide"""
        image = ImageDTO(
            url="https://example.com/image.jpg",
            alt="Image produit iPhone",
            width=800,
            height=600,
            size_bytes=50000
        )
        
        assert image.url == "https://example.com/image.jpg"
        assert image.alt == "Image produit iPhone"
        assert image.width == 800
        assert image.height == 600
        assert image.size_bytes == 50000
    
    def test_image_dto_https_validation(self):
        """Test validation HTTPS obligatoire"""
        # HTTP rejeté
        with pytest.raises(ValidationError) as exc_info:
            ImageDTO(
                url="http://example.com/image.jpg",
                alt="Image produit"
            )
        assert "URL image doit être en HTTPS" in str(exc_info.value)
        
        # URL malformée rejetée
        with pytest.raises(ValidationError):
            ImageDTO(
                url="ftp://example.com/image.jpg",
                alt="Image produit"
            )
    
    def test_image_dto_alt_text_validation(self):
        """Test validation texte alternatif"""
        # Alt vide rejeté
        with pytest.raises(ValidationError) as exc_info:
            ImageDTO(
                url="https://example.com/image.jpg",
                alt=""
            )
        assert "Texte alternatif ne peut pas être vide" in str(exc_info.value)
        
        # Alt whitespace rejeté
        with pytest.raises(ValidationError):
            ImageDTO(
                url="https://example.com/image.jpg",
                alt="   "
            )
        
        # Alt valide avec whitespace trimmed
        image = ImageDTO(
            url="https://example.com/image.jpg",
            alt="  Image produit  "
        )
        assert image.alt == "Image produit"
    
    def test_image_dto_dimensions_validation(self):
        """Test validation dimensions optionnelles"""
        # Dimensions négatives rejetées
        with pytest.raises(ValidationError):
            ImageDTO(
                url="https://example.com/image.jpg",
                alt="Image produit",
                width=-1
            )
        
        with pytest.raises(ValidationError):
            ImageDTO(
                url="https://example.com/image.jpg",
                alt="Image produit",
                height=0  # 0 non autorisé (ge=1)
            )
        
        # Dimensions valides
        image = ImageDTO(
            url="https://example.com/image.jpg",
            alt="Image produit",
            width=1,
            height=1
        )
        assert image.width == 1
        assert image.height == 1


class TestPriceDTO:
    """Tests pour PriceDTO"""
    
    def test_price_dto_valid(self):
        """Test création PriceDTO valide"""
        price = PriceDTO(
            amount=Decimal('99.99'),
            currency=Currency.EUR,
            original_text="99,99 €"
        )
        
        assert price.amount == Decimal('99.99')
        assert price.currency == Currency.EUR
        assert price.original_text == "99,99 €"
    
    def test_price_dto_amount_validation(self):
        """Test validation montant >= 0"""
        # Montant négatif rejeté
        with pytest.raises(ValidationError) as exc_info:
            PriceDTO(
                amount=Decimal('-10.00'),
                currency=Currency.EUR
            )
        assert "ensure this value is greater than or equal to 0" in str(exc_info.value)
        
        # Montant zéro autorisé
        price = PriceDTO(
            amount=Decimal('0.00'),
            currency=Currency.USD
        )
        assert price.amount == Decimal('0.00')
    
    def test_price_dto_currency_validation(self):
        """Test validation devise"""
        # Devise valide
        for currency in [Currency.EUR, Currency.USD, Currency.GBP]:
            price = PriceDTO(amount=Decimal('100'), currency=currency)
            assert price.currency == currency
        
        # Devise invalide via string
        with pytest.raises(ValidationError):
            PriceDTO(amount=Decimal('100'), currency="JPY")  # Non supporté


class TestProductDTO:
    """Tests pour ProductDTO complet"""
    
    @pytest.fixture
    def valid_image(self):
        return ImageDTO(
            url="https://example.com/product.jpg",
            alt="Image produit test"
        )
    
    @pytest.fixture
    def valid_price(self):
        return PriceDTO(
            amount=Decimal('199.99'),
            currency=Currency.EUR
        )
    
    def test_product_dto_complete_valid(self, valid_image, valid_price):
        """Test ProductDTO complet et valide"""
        product = ProductDTO(
            title="iPhone 15 Pro",
            description_html="<p>Smartphone premium</p>",
            price=valid_price,
            images=[valid_image],
            source_url="https://store.example.com/iphone-15-pro",
            attributes={"brand": "Apple", "storage": "256GB"},
            payload_signature="abc123def456",
            extraction_timestamp=time.time()
        )
        
        assert product.title == "iPhone 15 Pro"
        assert product.price.amount == Decimal('199.99')
        assert len(product.images) == 1
        assert product.status == ProductStatus.COMPLETE  # Défaut
        assert product.is_complete() is True
    
    def test_product_dto_title_validation(self, valid_image):
        """Test validation titre"""
        # Titre vide rejeté
        with pytest.raises(ValidationError):
            ProductDTO(
                title="",
                description_html="<p>Description</p>",
                images=[valid_image],
                source_url="https://example.com/product",
                payload_signature="abc123",
                extraction_timestamp=time.time()
            )
        
        # Titre trop long rejeté
        with pytest.raises(ValidationError):
            ProductDTO(
                title="A" * 501,  # Plus de 500 caractères
                description_html="<p>Description</p>",
                images=[valid_image],
                source_url="https://example.com/product",
                payload_signature="abc123",
                extraction_timestamp=time.time()
            )
        
        # Titre avec whitespace trimmed
        product = ProductDTO(
            title="  Produit Test  ",
            description_html="<p>Description</p>",
            images=[valid_image],
            source_url="https://example.com/product",
            payload_signature="abc123",
            extraction_timestamp=time.time()
        )
        assert product.title == "Produit Test"
    
    def test_product_dto_images_validation(self):
        """Test validation images (au moins 1 requise)"""
        # Aucune image rejetée
        with pytest.raises(ValidationError) as exc_info:
            ProductDTO(
                title="Produit Test",
                description_html="<p>Description</p>",
                images=[],  # Liste vide
                source_url="https://example.com/product",
                payload_signature="abc123",
                extraction_timestamp=time.time()
            )
        assert "Au moins une image requise" in str(exc_info.value)
    
    def test_product_dto_source_url_https_validation(self, valid_image):
        """Test validation source URL HTTPS"""
        # HTTP rejeté
        with pytest.raises(ValidationError) as exc_info:
            ProductDTO(
                title="Produit Test",
                description_html="<p>Description</p>",
                images=[valid_image],
                source_url="http://store.example.com/product",  # HTTP
                payload_signature="abc123",
                extraction_timestamp=time.time()
            )
        assert "URL source doit être en HTTPS" in str(exc_info.value)
        
        # HTTPS valide
        product = ProductDTO(
            title="Produit Test",
            description_html="<p>Description</p>",
            images=[valid_image],
            source_url="https://store.example.com/product",
            payload_signature="abc123",
            extraction_timestamp=time.time()
        )
        assert product.source_url == "https://store.example.com/product"
    
    def test_product_dto_payload_signature_validation(self, valid_image):
        """Test validation signature payload"""
        # Signature vide rejetée
        with pytest.raises(ValidationError) as exc_info:
            ProductDTO(
                title="Produit Test",
                description_html="<p>Description</p>",
                images=[valid_image],
                source_url="https://example.com/product",
                payload_signature="",  # Vide
                extraction_timestamp=time.time()
            )
        assert "Signature payload requise pour idempotence" in str(exc_info.value)
        
        # Signature whitespace rejetée
        with pytest.raises(ValidationError):
            ProductDTO(
                title="Produit Test",
                description_html="<p>Description</p>",
                images=[valid_image],
                source_url="https://example.com/product",
                payload_signature="   ",  # Whitespace
                extraction_timestamp=time.time()
            )
    
    def test_product_dto_optional_fields(self, valid_image):
        """Test champs optionnels"""
        # Prix optionnel
        product = ProductDTO(
            title="Produit Test",
            description_html="<p>Description</p>",
            images=[valid_image],
            source_url="https://example.com/product",
            payload_signature="abc123",
            extraction_timestamp=time.time()
            # price=None (optionnel)
        )
        assert product.price is None
        
        # Attributs par défaut
        assert product.attributes == {}
        assert product.status == ProductStatus.COMPLETE
    
    def test_product_dto_status_incomplete(self, valid_image):
        """Test différents status produit"""
        # Status incomplete media
        product = ProductDTO(
            title="Produit Test",
            description_html="<p>Description</p>",
            images=[valid_image],
            source_url="https://example.com/product",
            status=ProductStatus.INCOMPLETE_MEDIA,
            payload_signature="abc123",
            extraction_timestamp=time.time()
        )
        
        assert product.status == ProductStatus.INCOMPLETE_MEDIA
        assert product.is_complete() is False
    
    def test_product_dto_helper_methods(self, valid_image, valid_price):
        """Test méthodes helper ProductDTO"""
        product = ProductDTO(
            title="iPhone 15 Pro",
            description_html="<p>Smartphone</p>",
            price=valid_price,
            images=[valid_image],
            source_url="https://example.com/product",
            payload_signature="abc123",
            extraction_timestamp=time.time()
        )
        
        # get_primary_image
        primary = product.get_primary_image()
        assert primary == valid_image
        
        # get_price_display
        price_display = product.get_price_display()
        assert price_display == "199.99 EUR"
    
    def test_product_dto_no_price_display(self, valid_image):
        """Test affichage prix quand pas de prix"""
        product = ProductDTO(
            title="Produit Test",
            description_html="<p>Description</p>",
            images=[valid_image],
            source_url="https://example.com/product",
            payload_signature="abc123",
            extraction_timestamp=time.time()
            # price=None
        )
        
        assert product.get_price_display() == "Prix non disponible"
    
    def test_product_dto_no_image_primary(self):
        """Test get_primary_image sans image (théoriquement impossible vu validation)"""
        # Cette situation ne peut normalement pas arriver car validation exige >= 1 image
        # Mais testons la méthode en direct
        product = ProductDTO.__new__(ProductDTO)  # Bypass validation
        product.images = []
        
        assert product.get_primary_image() is None


class TestProductPlaceholder:
    """Tests pour ProductPlaceholder factory"""
    
    def test_create_incomplete_media_product(self):
        """Test création produit avec placeholder image"""
        timestamp = time.time()
        price = PriceDTO(amount=Decimal('99.99'), currency=Currency.EUR)
        
        product = ProductPlaceholder.create_incomplete_media_product(
            title="Produit Sans Image",
            description_html="<p>Description produit</p>",
            source_url="https://example.com/product",
            payload_signature="placeholder123",
            extraction_timestamp=timestamp,
            price=price,
            attributes={"brand": "Test"}
        )
        
        assert isinstance(product, ProductDTO)
        assert product.title == "Produit Sans Image"
        assert product.status == ProductStatus.INCOMPLETE_MEDIA
        assert len(product.images) == 1
        
        # Vérifier placeholder image
        placeholder_img = product.images[0]
        assert "placeholder.com" in placeholder_img.url
        assert placeholder_img.alt == "Image produit non disponible"
        assert placeholder_img.width == 400
        assert placeholder_img.height == 300
    
    def test_create_incomplete_media_product_minimal(self):
        """Test création placeholder avec données minimales"""
        timestamp = time.time()
        
        product = ProductPlaceholder.create_incomplete_media_product(
            title="Produit Minimal",
            description_html="<p>Description</p>",
            source_url="https://example.com/product",
            payload_signature="minimal123",
            extraction_timestamp=timestamp
            # price=None, attributes=None (optionnels)
        )
        
        assert product.price is None
        assert product.attributes == {}
        assert product.status == ProductStatus.INCOMPLETE_MEDIA
        assert len(product.images) == 1  # Placeholder toujours ajouté


class TestProductDTOIntegration:
    """Tests d'intégration et cas complexes"""
    
    def test_product_dto_multiple_images(self, valid_price):
        """Test produit avec plusieurs images"""
        images = [
            ImageDTO(url=f"https://example.com/image{i}.jpg", alt=f"Image {i}")
            for i in range(5)
        ]
        
        product = ProductDTO(
            title="Produit Multi-Images",
            description_html="<p>Produit avec plusieurs images</p>",
            price=valid_price,
            images=images,
            source_url="https://example.com/product",
            payload_signature="multi123",
            extraction_timestamp=time.time()
        )
        
        assert len(product.images) == 5
        assert product.get_primary_image() == images[0]
    
    def test_product_dto_complex_attributes(self, valid_image):
        """Test produit avec attributs complexes"""
        complex_attributes = {
            "brand": "Apple",
            "model": "iPhone 15 Pro",
            "storage": "256GB",
            "color": "Titane Naturel",
            "screen_size": "6.1 pouces",
            "processor": "A17 Pro",
            "camera": "48 Mpx Principal + 12 Mpx Ultra Grand Angle",
            "connectivity": "5G, Wi-Fi 6E, Bluetooth 5.3",
            "os": "iOS 17"
        }
        
        product = ProductDTO(
            title="iPhone 15 Pro Complet",
            description_html="<p>Smartphone premium avec toutes spécifications</p>",
            images=[valid_image],
            source_url="https://apple.com/iphone-15-pro",
            attributes=complex_attributes,
            payload_signature="complex123",
            extraction_timestamp=time.time()
        )
        
        assert len(product.attributes) == 9
        assert product.attributes["brand"] == "Apple"
        assert product.attributes["camera"] == "48 Mpx Principal + 12 Mpx Ultra Grand Angle"
    
    def test_product_dto_all_status_types(self, valid_image):
        """Test tous les types de status"""
        base_data = {
            "title": "Produit Test Status",
            "description_html": "<p>Test</p>",
            "images": [valid_image],
            "source_url": "https://example.com/product",
            "payload_signature": "status123",
            "extraction_timestamp": time.time()
        }
        
        # Test chaque status
        for status in ProductStatus:
            product = ProductDTO(**base_data, status=status)
            assert product.status == status
            
            if status == ProductStatus.COMPLETE:
                assert product.is_complete() is True
            else:
                assert product.is_complete() is False