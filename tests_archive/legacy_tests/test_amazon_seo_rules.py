"""
Tests unitaires pour le module SEO Amazon A9/A10
ECOMSIMPLY Bloc 5 — Phase 5: Amazon SEO Rules Tests

Tests complets des générateurs, contrôles de longueur et validation des listings.
"""

import unittest
import sys
import os
from typing import List, Dict, Any

# Ajouter le chemin du backend pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from seo.amazon_rules import AmazonSEORules, AmazonListing, ListingValidationStatus


class TestAmazonSEORules(unittest.TestCase):
    """Tests unitaires pour les règles SEO Amazon"""
    
    def setUp(self):
        """Configuration initiale des tests"""
        self.seo_rules = AmazonSEORules()
        
        # Données de test standardisées
        self.test_product_data = {
            'brand': 'Samsung',
            'model': 'Galaxy S24',
            'features': ['5G', 'Triple Camera', 'AMOLED Display', 'Water Resistant'],
            'size': '6.1 inches',
            'color': 'Phantom Black',
            'category': 'électronique'
        }
        
        self.test_listing_valid = AmazonListing(
            title="Samsung Galaxy S24 5G Smartphone 6.1 inches Phantom Black",
            bullets=[
                "✓ PERFORMANCE: Processeur ultra-rapide avec connectivité 5G",
                "✓ PHOTO: Triple caméra professionnelle pour des clichés exceptionnels",
                "✓ ÉCRAN: Écran AMOLED 6.1 pouces haute résolution",
                "✓ RÉSISTANCE: Certifié résistant à l'eau IP68",
                "✓ AUTONOMIE: Batterie longue durée avec charge rapide"
            ],
            description="Découvrez le Samsung Galaxy S24, un smartphone révolutionnaire qui combine performance et élégance.\n\nCARACTÉRISTIQUES PRINCIPALES:\n• Processeur dernière génération\n• Connectivité 5G ultra-rapide\n• Triple système de caméra\n• Écran AMOLED 6.1 pouces\n\nBÉNÉFICES POUR VOUS:\n✓ Photos professionnelles en toute circonstance\n✓ Navigation fluide et rapide\n✓ Design premium et résistant\n\nChoisissez le Samsung Galaxy S24 et rejoignez des milliers de clients satisfaits.",
            backend_keywords="smartphone 5g samsung galaxy camera photo écran amoled résistant eau phone mobile",
            images=["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
            brand="Samsung",
            model="Galaxy S24",
            category="électronique"
        )
    
    def test_title_generation_basic(self):
        """Test génération de titre basique"""
        title = self.seo_rules.generate_optimized_title(
            brand=self.test_product_data['brand'],
            model=self.test_product_data['model'],
            features=self.test_product_data['features'][:2],  # Limiter pour test
            size=self.test_product_data['size'],
            color=self.test_product_data['color'],
            category=self.test_product_data['category']
        )
        
        # Vérifications
        self.assertIsInstance(title, str)
        self.assertGreater(len(title), 0)
        self.assertLessEqual(len(title), self.seo_rules.TITLE_MAX_LENGTH)
        self.assertIn(self.test_product_data['brand'], title)
        self.assertIn(self.test_product_data['model'], title)
        
        # Vérifier absence d'emojis et mots interdits
        self.assertFalse(self.seo_rules.EMOJI_PATTERN.search(title))
        for forbidden in self.seo_rules.FORBIDDEN_WORDS:
            self.assertNotIn(forbidden.lower(), title.lower())
    
    def test_title_length_limit(self):
        """Test limite de longueur du titre"""
        # Créer un titre très long
        long_features = [
            "Super Extra Long Feature Name That Should Be Truncated",
            "Another Very Long Feature Description That Exceeds Normal Length",
            "Yet Another Extremely Long Feature Name For Testing Purposes"
        ]
        
        title = self.seo_rules.generate_optimized_title(
            brand="VeryLongBrandNameForTesting",
            model="ExtremelyLongModelNameThatShouldBeTruncated",
            features=long_features,
            size="Extra Large Size Description",
            color="Very Specific Color Name",
            category="électronique"
        )
        
        self.assertLessEqual(len(title), self.seo_rules.TITLE_MAX_LENGTH)
    
    def test_bullets_generation(self):
        """Test génération des bullet points"""
        bullets = self.seo_rules.generate_optimized_bullets(
            product_name="Samsung Galaxy S24",
            features=self.test_product_data['features'],
            benefits=['Photo professionnelle', 'Performance élevée', 'Design premium'],
            category=self.test_product_data['category'],
            target_keywords=['smartphone', '5g', 'camera']
        )
        
        # Vérifications
        self.assertIsInstance(bullets, list)
        self.assertEqual(len(bullets), self.seo_rules.BULLETS_COUNT)
        
        for bullet in bullets:
            self.assertIsInstance(bullet, str)
            self.assertGreater(len(bullet), 10)  # Minimum raisonnable
            self.assertLessEqual(len(bullet), self.seo_rules.BULLET_MAX_LENGTH)
            self.assertTrue(bullet.startswith("✓"))  # Format attendu
    
    def test_bullets_length_validation(self):
        """Test validation de longueur des bullets"""
        # Test avec contenu très long
        long_features = [
            "This is an extremely long feature description that should definitely exceed the maximum allowed length for a single bullet point in Amazon listings according to their guidelines and requirements for optimal SEO performance"
        ] * 5
        
        bullets = self.seo_rules.generate_optimized_bullets(
            product_name="Test Product",
            features=long_features,
            benefits=[],
            category="électronique"
        )
        
        for bullet in bullets:
            self.assertLessEqual(len(bullet), self.seo_rules.BULLET_MAX_LENGTH)
    
    def test_description_generation(self):
        """Test génération de description"""
        description = self.seo_rules.generate_optimized_description(
            product_name="Samsung Galaxy S24",
            features=self.test_product_data['features'],
            benefits=['Photo exceptionnelle', 'Performance ultra-rapide'],
            use_cases=['Professionnel', 'Personnel', 'Gaming'],
            category=self.test_product_data['category']
        )
        
        # Vérifications
        self.assertIsInstance(description, str)
        self.assertGreaterEqual(len(description), self.seo_rules.DESCRIPTION_MIN_LENGTH)
        self.assertLessEqual(len(description), self.seo_rules.DESCRIPTION_MAX_LENGTH)
        
        # Vérifier structure
        self.assertIn("CARACTÉRISTIQUES", description)
        self.assertIn("BÉNÉFICES", description)
        self.assertIn("Samsung Galaxy S24", description)
    
    def test_backend_keywords_generation(self):
        """Test génération des mots-clés backend"""
        keywords = self.seo_rules.generate_backend_keywords(
            product_name="Samsung Galaxy S24 Smartphone",
            category=self.test_product_data['category'],
            features=self.test_product_data['features'],
            additional_keywords=['mobile', 'phone', 'android']
        )
        
        # Vérifications
        self.assertIsInstance(keywords, str)
        self.assertGreater(len(keywords), 0)
        self.assertLessEqual(len(keywords.encode('utf-8')), self.seo_rules.BACKEND_KEYWORDS_MAX_BYTES)
        
        # Vérifier absence de marques concurrentes
        for competitor in self.seo_rules.COMPETITOR_BRANDS:
            self.assertNotIn(competitor.lower(), keywords.lower())
    
    def test_backend_keywords_byte_limit(self):
        """Test limite en bytes des mots-clés backend"""
        # Générer beaucoup de mots-clés
        many_keywords = [f"keyword{i}" for i in range(100)]
        
        keywords = self.seo_rules.generate_backend_keywords(
            product_name="Test Product",
            additional_keywords=many_keywords
        )
        
        self.assertLessEqual(len(keywords.encode('utf-8')), self.seo_rules.BACKEND_KEYWORDS_MAX_BYTES)
    
    def test_competitor_brands_filtering(self):
        """Test filtrage des marques concurrentes"""
        competitor_keywords = ['apple', 'samsung', 'sony', 'lg', 'nike', 'adidas']
        
        filtered = self.seo_rules._filter_competitor_brands(competitor_keywords)
        
        # Samsung ne devrait pas être filtré car c'est notre marque test
        # Mais apple, sony, lg, nike, adidas devraient être filtrés
        for competitor in ['apple', 'sony', 'lg', 'nike', 'adidas']:
            self.assertNotIn(competitor, filtered)
    
    def test_listing_validation_approved(self):
        """Test validation d'un listing valide (doit être approuvé)"""
        validation = self.seo_rules.validate_amazon_listing(self.test_listing_valid)
        
        # Vérifications
        self.assertEqual(validation.status, ListingValidationStatus.APPROVED)
        self.assertGreaterEqual(validation.score, 90)
        
        # Pas d'erreurs critiques
        critical_errors = [r for r in validation.reasons if 'ERREUR' in r]
        self.assertEqual(len(critical_errors), 0)
    
    def test_listing_validation_rejected_no_title(self):
        """Test validation d'un listing sans titre (doit être rejeté)"""
        invalid_listing = AmazonListing(
            title="",  # Titre vide
            bullets=self.test_listing_valid.bullets,
            description=self.test_listing_valid.description,
            backend_keywords=self.test_listing_valid.backend_keywords,
            images=self.test_listing_valid.images
        )
        
        validation = self.seo_rules.validate_amazon_listing(invalid_listing)
        
        self.assertEqual(validation.status, ListingValidationStatus.REJECTED)
        self.assertIn("Titre manquant", validation.reasons)
    
    def test_listing_validation_rejected_title_too_long(self):
        """Test validation d'un listing avec titre trop long"""
        long_title = "A" * (self.seo_rules.TITLE_MAX_LENGTH + 50)  # Dépasser la limite
        
        invalid_listing = AmazonListing(
            title=long_title,
            bullets=self.test_listing_valid.bullets,
            description=self.test_listing_valid.description,
            backend_keywords=self.test_listing_valid.backend_keywords,
            images=self.test_listing_valid.images
        )
        
        validation = self.seo_rules.validate_amazon_listing(invalid_listing)
        
        self.assertIn(ListingValidationStatus.REJECTED, [validation.status])
        title_error_found = any("Titre trop long" in reason for reason in validation.reasons)
        self.assertTrue(title_error_found)
    
    def test_listing_validation_rejected_emojis_in_title(self):
        """Test validation d'un listing avec emojis dans le titre"""
        emoji_title = "Samsung Galaxy S24 📱 Smartphone 🔥 Amazing Deal! 😍"
        
        invalid_listing = AmazonListing(
            title=emoji_title,
            bullets=self.test_listing_valid.bullets,
            description=self.test_listing_valid.description,
            backend_keywords=self.test_listing_valid.backend_keywords,
            images=self.test_listing_valid.images
        )
        
        validation = self.seo_rules.validate_amazon_listing(invalid_listing)
        
        emoji_error_found = any("Emojis détectés" in reason for reason in validation.reasons)
        self.assertTrue(emoji_error_found)
    
    def test_listing_validation_rejected_no_bullets(self):
        """Test validation d'un listing sans bullets"""
        invalid_listing = AmazonListing(
            title=self.test_listing_valid.title,
            bullets=[],  # Pas de bullets
            description=self.test_listing_valid.description,
            backend_keywords=self.test_listing_valid.backend_keywords,
            images=self.test_listing_valid.images
        )
        
        validation = self.seo_rules.validate_amazon_listing(invalid_listing)
        
        self.assertEqual(validation.status, ListingValidationStatus.REJECTED)
        self.assertIn("Bullets manquants", validation.reasons)
    
    def test_listing_validation_warning_short_description(self):
        """Test validation d'un listing avec description trop courte"""
        invalid_listing = AmazonListing(
            title=self.test_listing_valid.title,
            bullets=self.test_listing_valid.bullets,
            description="Description trop courte.",  # Moins de 100 caractères
            backend_keywords=self.test_listing_valid.backend_keywords,
            images=self.test_listing_valid.images
        )
        
        validation = self.seo_rules.validate_amazon_listing(invalid_listing)
        
        description_error_found = any("Description trop courte" in reason for reason in validation.reasons)
        self.assertTrue(description_error_found)
    
    def test_listing_validation_backend_keywords_too_long(self):
        """Test validation avec mots-clés backend trop longs"""
        long_keywords = "a" * (self.seo_rules.BACKEND_KEYWORDS_MAX_BYTES + 50)
        
        invalid_listing = AmazonListing(
            title=self.test_listing_valid.title,
            bullets=self.test_listing_valid.bullets,
            description=self.test_listing_valid.description,
            backend_keywords=long_keywords,
            images=self.test_listing_valid.images
        )
        
        validation = self.seo_rules.validate_amazon_listing(invalid_listing)
        
        keywords_error_found = any("Backend keywords trop longs" in reason for reason in validation.reasons)
        self.assertTrue(keywords_error_found)
    
    def test_text_cleaning_emojis(self):
        """Test nettoyage des emojis"""
        text_with_emojis = "Samsung Galaxy S24 📱 Smartphone 🔥 Amazing! 😍"
        cleaned_text = self.seo_rules._clean_text(text_with_emojis)
        
        # Vérifier que tous les emojis ont été supprimés
        self.assertFalse(self.seo_rules.EMOJI_PATTERN.search(cleaned_text))
        self.assertIn("Samsung Galaxy S24", cleaned_text)
        self.assertIn("Smartphone", cleaned_text)
    
    def test_text_cleaning_forbidden_words(self):
        """Test nettoyage des mots interdits"""
        text_with_forbidden = "Samsung Galaxy S24 BEST smartphone with AMAZING deal and FREE shipping"
        cleaned_text = self.seo_rules._clean_text(text_with_forbidden)
        
        # Vérifier que les mots interdits ont été supprimés
        for forbidden in ['best', 'amazing', 'deal', 'free']:
            self.assertNotIn(forbidden.lower(), cleaned_text.lower())
        
        # Vérifier que le contenu valide reste
        self.assertIn("Samsung Galaxy S24", cleaned_text)
        self.assertIn("smartphone", cleaned_text)
    
    def test_smart_truncate(self):
        """Test troncature intelligente"""
        long_text = "Samsung Galaxy S24 Ultra Smartphone with Amazing Features and Great Performance"
        
        # Tronquer à 50 caractères
        truncated = self.seo_rules._smart_truncate(long_text, 50)
        
        self.assertLessEqual(len(truncated), 50)
        # Vérifier qu'on ne coupe pas au milieu d'un mot
        self.assertFalse(truncated.endswith(' '))
    
    def test_category_keywords_extraction(self):
        """Test extraction des mots-clés par catégorie"""
        # Test catégorie électronique
        fr_keywords = self.seo_rules._get_category_keywords('électronique', 'fr')
        en_keywords = self.seo_rules._get_category_keywords('électronique', 'en')
        
        self.assertIsInstance(fr_keywords, list)
        self.assertIsInstance(en_keywords, list)
        self.assertGreater(len(fr_keywords), 0)
        self.assertGreater(len(en_keywords), 0)
        
        # Vérifier que les mots-clés sont cohérents
        self.assertIn('technologie', fr_keywords)
        self.assertIn('technology', en_keywords)


class TestAmazonSEOIntegration(unittest.TestCase):
    """Tests d'intégration pour le système SEO Amazon complet"""
    
    def setUp(self):
        """Configuration pour les tests d'intégration"""
        self.seo_rules = AmazonSEORules()
    
    def test_complete_listing_generation_flow(self):
        """Test du flux complet de génération d'un listing"""
        # Données produit complètes
        product_data = {
            'brand': 'Apple',
            'model': 'MacBook Air M3',
            'features': ['Puce M3', 'Écran Liquid Retina', '8 Core CPU', '16 GB RAM'],
            'size': '13 pouces',
            'color': 'Argent',
            'category': 'électronique'
        }
        
        # 1. Générer le titre
        title = self.seo_rules.generate_optimized_title(**product_data)
        
        # 2. Générer les bullets
        bullets = self.seo_rules.generate_optimized_bullets(
            product_name=f"{product_data['brand']} {product_data['model']}",
            features=product_data['features'],
            benefits=['Performance exceptionnelle', 'Portabilité premium'],
            category=product_data['category']
        )
        
        # 3. Générer la description
        description = self.seo_rules.generate_optimized_description(
            product_name=f"{product_data['brand']} {product_data['model']}",
            features=product_data['features'],
            benefits=['Performance exceptionnelle', 'Portabilité premium'],
            category=product_data['category']
        )
        
        # 4. Générer les mots-clés backend
        keywords = self.seo_rules.generate_backend_keywords(
            product_name=f"{product_data['brand']} {product_data['model']}",
            category=product_data['category'],
            features=product_data['features']
        )
        
        # 5. Créer et valider le listing complet
        listing = AmazonListing(
            title=title,
            bullets=bullets,
            description=description,
            backend_keywords=keywords,
            images=["https://example.com/macbook1.jpg", "https://example.com/macbook2.jpg"],
            **product_data
        )
        
        validation = self.seo_rules.validate_amazon_listing(listing)
        
        # Vérifications d'intégration
        self.assertIn(ListingValidationStatus.APPROVED, [validation.status, ListingValidationStatus.WARNING])
        self.assertGreaterEqual(validation.score, 70)  # Score minimum acceptable
        
        # Vérifier cohérence entre les éléments
        brand_in_title = product_data['brand'] in title
        brand_in_description = product_data['brand'] in description
        self.assertTrue(brand_in_title and brand_in_description)
    
    def test_validation_edge_cases(self):
        """Test des cas limites de validation"""
        edge_cases = [
            # Cas 1: Listing minimal mais valide
            {
                'title': 'Apple MacBook Air M3 13 pouces Argent',
                'bullets': [f'✓ FEATURE: Feature {i+1}' for i in range(5)],
                'description': 'Description minimale mais suffisante pour respecter la limite de 100 caractères minimum avec du contenu utile.',
                'backend_keywords': 'apple macbook air laptop computer',
                'images': ['https://example.com/image.jpg']
            },
            # Cas 2: Listing à la limite des longueurs
            {
                'title': 'A' * 199,  # Juste sous la limite
                'bullets': ['✓ BULLET: ' + 'B' * 245 for _ in range(5)],  # Juste sous la limite par bullet
                'description': 'D' * 1999,  # Juste sous la limite
                'backend_keywords': 'k' * 240,  # Juste sous la limite en bytes
                'images': ['https://example.com/image.jpg']
            }
        ]
        
        for i, case_data in enumerate(edge_cases):
            with self.subTest(case=i):
                listing = AmazonListing(**case_data)
                validation = self.seo_rules.validate_amazon_listing(listing)
                
                # Au minimum, ne doit pas être rejeté pour des raisons de longueur
                length_errors = [r for r in validation.reasons if 'trop long' in r or 'trop court' in r]
                self.assertEqual(len(length_errors), 0, f"Cas {i}: Erreurs de longueur inattendues: {length_errors}")


def run_amazon_seo_tests():
    """Exécute tous les tests SEO Amazon et retourne le résultat"""
    print("🚀 DÉMARRAGE TESTS SEO AMAZON A9/A10")
    print("=" * 60)
    
    # Créer la suite de tests
    test_suite = unittest.TestSuite()
    
    # Ajouter les tests unitaires
    test_classes = [TestAmazonSEORules, TestAmazonSEOIntegration]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Exécuter les tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(test_suite)
    
    # Résumé des résultats
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS SEO AMAZON")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success_count = total_tests - failures - errors
    success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
    
    print(f"✅ Tests réussis: {success_count}/{total_tests} ({success_rate:.1f}%)")
    print(f"❌ Échecs: {failures}")
    print(f"🔥 Erreurs: {errors}")
    
    if result.failures:
        print("\n🔍 ÉCHECS DÉTAILLÉS:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n🔥 ERREURS DÉTAILLÉES:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Error:')[-1].strip()}")
    
    # Status final
    if success_rate >= 100:
        print(f"\n🎉 TOUS LES TESTS PASSENT - SEO AMAZON PRÊT POUR PRODUCTION!")
    elif success_rate >= 90:
        print(f"\n✅ TESTS LARGEMENT RÉUSSIS - SEO Amazon opérationnel avec quelques optimisations mineures")
    elif success_rate >= 70:
        print(f"\n⚠️ TESTS PARTIELLEMENT RÉUSSIS - SEO Amazon nécessite des corrections")
    else:
        print(f"\n❌ TESTS ÉCHOUÉS - SEO Amazon nécessite des corrections majeures")
    
    return {
        'total_tests': total_tests,
        'success_count': success_count,
        'failures': failures,
        'errors': errors,
        'success_rate': success_rate,
        'status': 'PASSED' if success_rate == 100 else 'PARTIAL' if success_rate >= 70 else 'FAILED'
    }


if __name__ == "__main__":
    run_amazon_seo_tests()