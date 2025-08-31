"""
Tests d'intégration pour SEO Amazon avec Publisher
ECOMSIMPLY Bloc 5 — Phase 5: Amazon SEO Integration Tests

Tests d'intégration entre les règles SEO et le Publisher Amazon.
"""

import unittest
import asyncio
import sys
import os
from typing import Dict, Any

# Ajouter les chemins pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.amazon_seo_integration_service import AmazonSEOIntegrationService


class TestAmazonSEOIntegration(unittest.TestCase):
    """Tests d'intégration pour le service SEO Amazon"""
    
    def setUp(self):
        """Configuration initiale des tests"""
        self.seo_integration = AmazonSEOIntegrationService()
        
        # Données de test pour produits électroniques
        self.test_product_electronics = {
            'product_name': 'iPhone 15 Pro Max',
            'brand': 'Apple',
            'model': 'iPhone 15 Pro Max',
            'category': 'électronique',
            'features': [
                'Puce A17 Pro',
                'Appareil photo 48 Mpx',
                'Écran Super Retina XDR 6,7 pouces',
                'Titanium Grade 5',
                'USB-C'
            ],
            'benefits': [
                'Photos et vidéos de qualité professionnelle',
                'Performance gaming exceptionnelle',
                'Design premium ultra-résistant',
                'Recharge rapide et sans fil'
            ],
            'use_cases': [
                'Photographie professionnelle',
                'Gaming haute performance',
                'Productivité mobile',
                'Création de contenu'
            ],
            'size': '6.7 pouces',
            'color': 'Titanium Naturel',
            'images': [
                'https://example.com/iphone15-main.jpg',
                'https://example.com/iphone15-back.jpg',
                'https://example.com/iphone15-camera.jpg'
            ],
            'additional_keywords': [
                '5G', 'iOS', 'Face ID', 'MagSafe', 'ProRAW'
            ]
        }
        
        # Données de test pour mode/fashion
        self.test_product_fashion = {
            'product_name': 'Nike Air Max 270',
            'brand': 'Nike',
            'model': 'Air Max 270',
            'category': 'mode',
            'features': [
                'Amorti Air Max',
                'Tige en mesh respirant',
                'Semelle en mousse',
                'Design moderne'
            ],
            'benefits': [
                'Confort optimal toute la journée',
                'Style urbain tendance',
                'Respirabilité exceptionnelle',
                'Durabilité éprouvée'
            ],
            'size': '42 EU',
            'color': 'Noir/Blanc',
            'images': [
                'https://example.com/nike-airmax-main.jpg',
                'https://example.com/nike-airmax-side.jpg'
            ]
        }
    
    def test_generate_listing_electronics_valid(self):
        """Test génération listing électronique valide"""
        async def run_test():
            result = await self.seo_integration.generate_optimized_listing(
                self.test_product_electronics
            )
            
            # Vérifications structure de base
            self.assertIn('listing', result)
            self.assertIn('validation', result)
            self.assertIn('generation_info', result)
            
            listing = result['listing']
            validation = result['validation']
            
            # Vérifications du listing généré
            self.assertIn('title', listing)
            self.assertIn('bullets', listing)
            self.assertIn('description', listing)
            self.assertIn('backend_keywords', listing)
            
            # Vérifications du titre
            title = listing['title']
            self.assertLessEqual(len(title), 200)
            self.assertIn('iPhone 15 Pro Max', title)
            self.assertIn('Apple', title)
            
            # Vérifications des bullets
            bullets = listing['bullets']
            self.assertEqual(len(bullets), 5)
            for bullet in bullets:
                self.assertLessEqual(len(bullet), 255)
                self.assertTrue(bullet.startswith('✓'))
            
            # Vérifications de la description
            description = listing['description']
            self.assertGreaterEqual(len(description), 100)
            self.assertLessEqual(len(description), 2000)
            self.assertIn('iPhone 15 Pro Max', description)
            
            # Vérifications des mots-clés backend
            keywords = listing['backend_keywords']
            self.assertLessEqual(len(keywords.encode('utf-8')), 250)
            
            # Vérifications de la validation
            self.assertIn(validation['status'], ['approved', 'warning'])
            self.assertGreaterEqual(validation['score'], 70)
            
            return result
        
        result = asyncio.run(run_test())
        return result
    
    def test_generate_listing_fashion_valid(self):
        """Test génération listing mode valide"""
        async def run_test():
            result = await self.seo_integration.generate_optimized_listing(
                self.test_product_fashion
            )
            
            listing = result['listing']
            validation = result['validation']
            
            # Vérifications spécifiques à la mode
            title = listing['title']
            self.assertIn('Nike', title)
            self.assertIn('Air Max 270', title)
            
            # Vérifier mots-clés de mode dans description
            description = listing['description']
            mode_keywords = ['style', 'fashion', 'tendance']
            has_mode_keyword = any(keyword in description.lower() for keyword in mode_keywords)
            self.assertTrue(has_mode_keyword, "La description devrait contenir des mots-clés de mode")
            
            return result
        
        result = asyncio.run(run_test())
        return result
    
    def test_validate_existing_listing_approved(self):
        """Test validation d'un listing existant (cas approuvé)"""
        async def run_test():
            valid_listing = {
                'title': 'Samsung Galaxy S24 Ultra Smartphone 5G 256GB Titanium Gray',
                'bullets': [
                    '✓ PERFORMANCE: Processeur Snapdragon 8 Gen 3 pour une puissance exceptionnelle',
                    '✓ PHOTO: Système de caméra AI avancé avec zoom 100x Space Zoom',
                    '✓ ÉCRAN: Écran Dynamic AMOLED 2X 6.8 pouces QHD+ 120Hz',
                    '✓ S PEN: S Pen intégré pour productivité et créativité maximales',
                    '✓ AUTONOMIE: Batterie 5000mAh avec charge rapide 45W'
                ],
                'description': 'Découvrez le Samsung Galaxy S24 Ultra, le smartphone le plus avancé de Samsung.\n\nCARACTÉRISTIQUES PRINCIPALES:\n• Processeur Snapdragon 8 Gen 3\n• 12 GB de RAM et 256 GB de stockage\n• Système de caméra quadruple avec IA\n• Écran Dynamic AMOLED 2X\n\nBÉNÉFICES POUR VOUS:\n✓ Photos et vidéos de qualité professionnelle\n✓ Multitâche fluide et gaming haute performance\n✓ Productivité mobile avec S Pen\n✓ Durabilité premium avec Gorilla Glass Armor\n\nChoisissez le Galaxy S24 Ultra et découvrez l\'innovation Samsung.',
                'backend_keywords': 'samsung galaxy smartphone 5g android camera photo zoom écran amoled titanium',
                'images': [
                    'https://example.com/galaxy-s24-main.jpg',
                    'https://example.com/galaxy-s24-back.jpg'
                ],
                'brand': 'Samsung',
                'model': 'Galaxy S24 Ultra',
                'category': 'électronique'
            }
            
            result = await self.seo_integration.validate_existing_listing(valid_listing)
            
            # Vérifications
            self.assertIn('validation', result)
            self.assertIn('compliance', result)
            
            validation = result['validation']
            compliance = result['compliance']
            
            self.assertIn(validation['status'], ['approved', 'warning'])
            self.assertGreaterEqual(validation['score'], 80)
            self.assertTrue(compliance['ready_for_publication'])
            self.assertEqual(compliance['critical_issues'], 0)
            
            return result
        
        result = asyncio.run(run_test())
        return result
    
    def test_validate_existing_listing_rejected(self):
        """Test validation d'un listing existant (cas rejeté)"""
        async def run_test():
            invalid_listing = {
                'title': '',  # Titre vide - erreur critique
                'bullets': [],  # Pas de bullets - erreur critique
                'description': 'Description trop courte.',  # < 100 caractères
                'backend_keywords': 'a' * 300,  # Trop long en bytes
                'images': [],  # Pas d'images
                'brand': 'TestBrand',
                'model': 'TestModel',
                'category': 'électronique'
            }
            
            result = await self.seo_integration.validate_existing_listing(invalid_listing)
            
            # Vérifications
            validation = result['validation']
            compliance = result['compliance']
            
            self.assertEqual(validation['status'], 'rejected')
            self.assertLess(validation['score'], 70)
            self.assertFalse(compliance['ready_for_publication'])
            self.assertGreater(compliance['critical_issues'], 0)
            
            # Vérifier présence d'erreurs spécifiques
            reasons = validation['reasons']
            self.assertTrue(any('Titre manquant' in reason for reason in reasons))
            self.assertTrue(any('Bullets manquants' in reason for reason in reasons))
            
            return result
        
        result = asyncio.run(run_test())
        return result
    
    def test_optimize_existing_listing(self):
        """Test optimisation d'un listing existant"""
        async def run_test():
            # Listing sous-optimal
            suboptimal_listing = {
                'title': 'iPhone 15',  # Titre trop court
                'bullets': [
                    'Good phone',  # Bullets trop simples
                    'Nice camera',
                    'Fast processor'
                ],  # Seulement 3 bullets au lieu de 5
                'description': 'iPhone 15 is a good phone with nice features.',  # Description trop courte
                'backend_keywords': 'iphone phone',  # Mots-clés insuffisants
                'images': ['https://example.com/iphone.jpg'],
                'brand': 'Apple',
                'model': 'iPhone 15',
                'category': 'électronique'
            }
            
            result = await self.seo_integration.optimize_existing_listing(suboptimal_listing)
            
            # Vérifications
            self.assertIn('original', result)
            self.assertIn('optimized', result)
            self.assertIn('comparison', result)
            self.assertIn('recommendations', result)
            
            original = result['original']
            optimized = result['optimized']
            recommendations = result['recommendations']
            
            # L'optimisation devrait améliorer le score
            original_score = original['validation']['score']
            optimized_score = optimized['validation']['score']
            
            self.assertGreater(optimized_score, original_score)
            self.assertTrue(recommendations['should_update'])
            self.assertGreater(recommendations['score_improvement'], 0)
            
            # Vérifier que l'optimisation a corrigé les problèmes
            optimized_listing = optimized['listing']
            self.assertGreater(len(optimized_listing['title']), len(suboptimal_listing['title']))
            self.assertEqual(len(optimized_listing['bullets']), 5)
            self.assertGreater(len(optimized_listing['description']), 100)
            
            return result
        
        result = asyncio.run(run_test())
        return result
    
    def test_prepare_for_publisher_valid(self):
        """Test préparation listing pour Publisher"""
        async def run_test():
            result = await self.seo_integration.prepare_listing_for_publisher(
                self.test_product_electronics
            )
            
            # Vérifications
            self.assertIn('listing_data', result)
            self.assertIn('metadata', result)
            self.assertIn('validation_summary', result)
            self.assertIn('seo_insights', result)
            
            listing_data = result['listing_data']
            metadata = result['metadata']
            validation = result['validation_summary']
            
            # Format Publisher Amazon
            expected_fields = [
                'title', 'bullet_point_1', 'bullet_point_2', 'bullet_point_3',
                'bullet_point_4', 'bullet_point_5', 'description', 'search_terms',
                'main_image', 'additional_images'
            ]
            
            for field in expected_fields:
                self.assertIn(field, listing_data)
            
            # Métadonnées
            self.assertTrue(metadata['seo_optimized'])
            self.assertTrue(metadata['a9_a10_compliant'])
            self.assertGreaterEqual(metadata['validation_score'], 70)
            
            # Validation pour publication
            self.assertTrue(validation['ready_for_publication'])
            self.assertEqual(validation['critical_issues_count'], 0)
            
            return result
        
        result = asyncio.run(run_test())
        return result
    
    def test_prepare_for_publisher_invalid_rejected(self):
        """Test préparation listing invalide pour Publisher (doit échouer)"""
        async def run_test():
            invalid_product = {
                'product_name': '',  # Nom vide
                'brand': '',
                'model': '',
                'category': '',
                'features': [],
                'benefits': [],
                'images': []
            }
            
            with self.assertRaises(Exception) as context:
                await self.seo_integration.prepare_listing_for_publisher(invalid_product)
            
            # Vérifier que l'erreur contient des informations sur la non-conformité
            error_message = str(context.exception)
            self.assertIn('non conforme', error_message.lower())
            
            return True
        
        result = asyncio.run(run_test())
        return result
    
    def test_brand_model_extraction(self):
        """Test extraction automatique marque/modèle"""
        async def run_test():
            # Produit sans marque/modèle explicites
            product_no_brand = {
                'product_name': 'Samsung Galaxy S24 Smartphone Android',
                'category': 'électronique',
                'features': ['5G', 'Camera', 'AMOLED'],
                'benefits': ['Fast performance'],
                'images': ['https://example.com/phone.jpg']
            }
            
            result = await self.seo_integration.generate_optimized_listing(product_no_brand)
            
            listing = result['listing']
            metadata = listing['metadata']
            
            # Vérifier extraction automatique
            self.assertEqual(metadata['brand'], 'Samsung')  # Premier mot
            self.assertEqual(metadata['model'], 'Galaxy')   # Deuxième mot
            
            # Vérifier présence dans le titre
            title = listing['title']
            self.assertIn('Samsung', title)
            self.assertIn('Galaxy', title)
            
            return result
        
        result = asyncio.run(run_test())
        return result


class TestAmazonSEOPublisherIntegration(unittest.TestCase):
    """Tests d'intégration avec le Publisher Amazon existant"""
    
    def setUp(self):
        """Configuration pour tests Publisher"""
        self.seo_integration = AmazonSEOIntegrationService()
    
    def test_publisher_format_compatibility(self):
        """Test compatibilité format Publisher Amazon"""
        async def run_test():
            product_data = {
                'product_name': 'MacBook Pro M3 Max',
                'brand': 'Apple',
                'model': 'MacBook Pro',
                'category': 'électronique',
                'features': ['Puce M3 Max', 'Écran Liquid Retina XDR', '64 GB RAM'],
                'benefits': ['Performance extrême', 'Écran professionnel'],
                'images': [
                    'https://example.com/macbook-main.jpg',
                    'https://example.com/macbook-side.jpg',
                    'https://example.com/macbook-screen.jpg'
                ]
            }
            
            result = await self.seo_integration.prepare_listing_for_publisher(product_data)
            listing_data = result['listing_data']
            
            # Vérifications format Publisher
            # Titre unique
            self.assertIsInstance(listing_data['title'], str)
            self.assertLessEqual(len(listing_data['title']), 200)
            
            # 5 bullets séparés
            for i in range(1, 6):
                bullet_key = f'bullet_point_{i}'
                self.assertIn(bullet_key, listing_data)
                if listing_data[bullet_key]:  # Si non vide
                    self.assertLessEqual(len(listing_data[bullet_key]), 255)
            
            # Description
            self.assertIsInstance(listing_data['description'], str)
            self.assertGreaterEqual(len(listing_data['description']), 100)
            
            # Search terms (backend keywords)
            self.assertIsInstance(listing_data['search_terms'], str)
            self.assertLessEqual(len(listing_data['search_terms'].encode('utf-8')), 250)
            
            # Images
            self.assertIsInstance(listing_data['main_image'], (str, type(None)))
            self.assertIsInstance(listing_data['additional_images'], list)
            
            return result
        
        result = asyncio.run(run_test())
        return result
    
    def test_multiple_categories_optimization(self):
        """Test optimisation pour différentes catégories"""
        categories_test = {
            'électronique': {
                'product_name': 'Sony WH-1000XM5',
                'expected_keywords': ['technology', 'technologie', 'electronic']
            },
            'mode': {
                'product_name': 'Adidas Ultraboost 22',
                'expected_keywords': ['style', 'fashion', 'trendy']
            },
            'maison': {
                'product_name': 'Dyson V15 Detect',
                'expected_keywords': ['home', 'maison', 'practical']
            },
            'sport': {
                'product_name': 'Garmin Forerunner 955',
                'expected_keywords': ['sport', 'fitness', 'performance']
            }
        }
        
        async def run_test():
            results = {}
            
            for category, test_data in categories_test.items():
                product = {
                    'product_name': test_data['product_name'],
                    'category': category,
                    'features': ['Feature 1', 'Feature 2'],
                    'benefits': ['Benefit 1'],
                    'images': ['https://example.com/image.jpg']
                }
                
                result = await self.seo_integration.generate_optimized_listing(product)
                
                # Vérifier présence de mots-clés de catégorie
                backend_keywords = result['listing']['backend_keywords']
                description = result['listing']['description']
                
                has_category_keyword = False
                for keyword in test_data['expected_keywords']:
                    if keyword.lower() in backend_keywords.lower() or keyword.lower() in description.lower():
                        has_category_keyword = True
                        break
                
                results[category] = {
                    'has_category_keywords': has_category_keyword,
                    'validation_score': result['validation']['score']
                }
                
                self.assertTrue(has_category_keyword, 
                    f"Catégorie {category}: aucun mot-clé spécifique trouvé")
            
            return results
        
        results = asyncio.run(run_test())
        return results


def run_amazon_seo_integration_tests():
    """Exécute tous les tests d'intégration SEO Amazon"""
    print("🚀 DÉMARRAGE TESTS INTÉGRATION SEO AMAZON")
    print("=" * 60)
    
    # Créer la suite de tests
    test_suite = unittest.TestSuite()
    
    # Ajouter les tests d'intégration
    test_classes = [TestAmazonSEOIntegration, TestAmazonSEOPublisherIntegration]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Exécuter les tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(test_suite)
    
    # Résumé des résultats
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ TESTS INTÉGRATION SEO AMAZON")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success_count = total_tests - failures - errors
    success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
    
    print(f"✅ Tests réussis: {success_count}/{total_tests} ({success_rate:.1f}%)")
    print(f"❌ Échecs: {failures}")
    print(f"🔥 Erreurs: {errors}")
    
    # Détails des échecs
    if result.failures:
        print("\n🔍 ÉCHECS DÉTAILLÉS:")
        for test, traceback in result.failures:
            print(f"- {test}")
            print(f"  {traceback.split('AssertionError:')[-1].strip() if 'AssertionError:' in traceback else traceback}")
    
    if result.errors:
        print("\n🔥 ERREURS DÉTAILLÉES:")
        for test, traceback in result.errors:
            print(f"- {test}")
            print(f"  {traceback.split('Error:')[-1].strip() if 'Error:' in traceback else traceback}")
    
    # Status final
    if success_rate >= 100:
        print(f"\n🎉 INTÉGRATION SEO AMAZON PARFAITE - Prêt pour production!")
    elif success_rate >= 90:
        print(f"\n✅ INTÉGRATION SEO AMAZON EXCELLENTE - Opérationnel avec optimisations mineures")
    elif success_rate >= 70:
        print(f"\n⚠️ INTÉGRATION SEO AMAZON ACCEPTABLE - Corrections recommandées")
    else:
        print(f"\n❌ INTÉGRATION SEO AMAZON DÉFAILLANTE - Corrections majeures requises")
    
    return {
        'total_tests': total_tests,
        'success_count': success_count,
        'failures': failures,
        'errors': errors,
        'success_rate': success_rate,
        'status': 'PASSED' if success_rate == 100 else 'PARTIAL' if success_rate >= 70 else 'FAILED'
    }


if __name__ == "__main__":
    run_amazon_seo_integration_tests()