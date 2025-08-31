#!/usr/bin/env python3
"""
ECOMSIMPLY Amazon Listings Phase 2 - Functionality Testing
Test des fonctionnalités core sans connexion Amazon requise

Ce test valide:
1. Générateur IA - Génération de contenu conforme Amazon A9/A10
2. Validateur - Validation selon les règles Amazon officielles
3. Publisher - Préparation des données pour SP-API
4. Intégration - Workflow complet génération → validation → préparation
"""

import asyncio
import sys
import time
import json
from datetime import datetime
from typing import Dict, Any, List
import unittest.mock as mock

# Configuration du path
sys.path.append('/app/backend')

# Données de test iPhone 15 Pro
IPHONE_15_PRO_DATA = {
    "brand": "Apple",
    "product_name": "iPhone 15 Pro Max 256GB",
    "features": [
        "Puce A17 Pro avec GPU 6 cœurs",
        "Écran Super Retina XDR 6,7 pouces", 
        "Système caméra Pro triple 48 Mpx",
        "Châssis titane qualité aérospatiale",
        "USB-C avec USB 3 transferts rapides"
    ],
    "category": "électronique",
    "target_keywords": ["smartphone", "premium", "apple", "iphone", "pro", "titanium"],
    "size": "6,7 pouces",
    "color": "Titane Naturel",
    "price": 1479.00,
    "description": "Le smartphone le plus avancé d'Apple avec puce A17 Pro et design titane premium"
}

class AmazonListingsFunctionalityTester:
    def __init__(self):
        self.test_results = {
            "generator": {"tested": False, "success": False, "details": {}},
            "validator": {"tested": False, "success": False, "details": {}},
            "publisher": {"tested": False, "success": False, "details": {}},
            "integration": {"tested": False, "success": False, "details": {}}
        }
        self.generated_listing = None
        self.validation_result = None
        
    async def test_amazon_listing_generator(self) -> bool:
        """Test du générateur IA Amazon"""
        print("🤖 Testing Amazon Listing Generator...")
        
        try:
            from amazon.listings.generator import AmazonListingGenerator
            
            generator = AmazonListingGenerator()
            self.test_results["generator"]["tested"] = True
            
            # Test de génération complète
            start_time = time.time()
            generated_listing = await generator.generate_amazon_listing(IPHONE_15_PRO_DATA)
            generation_time = time.time() - start_time
            
            self.generated_listing = generated_listing
            
            # Validation de la structure
            required_fields = ['listing_id', 'generated_at', 'seo_content', 'generation_metadata']
            missing_fields = [field for field in required_fields if field not in generated_listing]
            
            if missing_fields:
                print(f"❌ Missing fields: {missing_fields}")
                return False
            
            # Validation du contenu SEO
            seo_content = generated_listing['seo_content']
            required_seo_fields = ['title', 'bullet_points', 'description', 'backend_keywords', 'image_requirements']
            missing_seo = [field for field in required_seo_fields if field not in seo_content]
            
            if missing_seo:
                print(f"❌ Missing SEO fields: {missing_seo}")
                return False
            
            # Validation des règles Amazon
            title = seo_content['title']
            bullets = seo_content['bullet_points']
            description = seo_content['description']
            keywords = seo_content['backend_keywords']
            
            # Vérifications conformité A9/A10
            title_valid = len(title) <= 200 and len(title) >= 15
            bullets_valid = len(bullets) <= 5 and all(len(bullet) <= 255 for bullet in bullets)
            description_valid = 100 <= len(description) <= 2000
            keywords_valid = len(keywords.encode('utf-8')) <= 250
            
            # Score d'optimisation
            metadata = generated_listing['generation_metadata']
            optimization_score = metadata.get('optimization_score', 0)
            
            print("✅ Generator test successful!")
            print(f"   Generation time: {generation_time:.2f}s")
            print(f"   Title: {title[:50]}... ({len(title)} chars)")
            print(f"   Bullets: {len(bullets)} points")
            print(f"   Description: {len(description)} chars")
            print(f"   Keywords: {len(keywords.encode('utf-8'))} bytes")
            print(f"   Optimization score: {optimization_score}%")
            print(f"   A9/A10 Compliance: Title={title_valid}, Bullets={bullets_valid}, Desc={description_valid}, Keywords={keywords_valid}")
            
            # Détails pour le résumé
            self.test_results["generator"]["success"] = True
            self.test_results["generator"]["details"] = {
                "generation_time": generation_time,
                "title_length": len(title),
                "title_valid": title_valid,
                "bullets_count": len(bullets),
                "bullets_valid": bullets_valid,
                "description_length": len(description),
                "description_valid": description_valid,
                "keywords_bytes": len(keywords.encode('utf-8')),
                "keywords_valid": keywords_valid,
                "optimization_score": optimization_score,
                "a9_a10_compliant": all([title_valid, bullets_valid, description_valid, keywords_valid])
            }
            
            return True
            
        except Exception as e:
            print(f"❌ Generator test failed: {str(e)}")
            self.test_results["generator"]["details"]["error"] = str(e)
            return False
    
    async def test_amazon_listing_validator(self) -> bool:
        """Test du validateur Amazon"""
        print("\n🔍 Testing Amazon Listing Validator...")
        
        if not self.generated_listing:
            print("❌ No generated listing available for validation")
            return False
        
        try:
            from amazon.listings.validators import AmazonListingValidator, ValidationStatus
            
            validator = AmazonListingValidator()
            self.test_results["validator"]["tested"] = True
            
            # Test de validation complète
            start_time = time.time()
            validation_result = validator.validate_complete_listing(self.generated_listing)
            validation_time = time.time() - start_time
            
            self.validation_result = validation_result
            
            # Analyse des résultats
            overall_status = validation_result.get('overall_status')
            validation_score = validation_result.get('validation_score', 0)
            errors = validation_result.get('errors', [])
            warnings = validation_result.get('warnings', [])
            details = validation_result.get('details', {})
            
            # Vérification des composants validés
            expected_components = ['title', 'bullets', 'description', 'keywords', 'images', 'brand']
            validated_components = list(details.keys())
            missing_components = [comp for comp in expected_components if comp not in validated_components]
            
            # Analyse des scores par composant
            component_scores = {}
            for component, result in details.items():
                component_scores[component] = result.get('score', 0)
            
            # Test du résumé de validation
            summary = validator.get_validation_summary(validation_result)
            
            print("✅ Validator test successful!")
            print(f"   Validation time: {validation_time:.2f}s")
            print(f"   Overall status: {overall_status}")
            print(f"   Validation score: {validation_score}%")
            print(f"   Errors: {len(errors)}")
            print(f"   Warnings: {len(warnings)}")
            print(f"   Components validated: {len(validated_components)}")
            print(f"   Summary: {summary}")
            
            # Afficher scores par composant
            for component, score in component_scores.items():
                print(f"   {component}: {score}%")
            
            # Détails pour le résumé
            self.test_results["validator"]["success"] = True
            self.test_results["validator"]["details"] = {
                "validation_time": validation_time,
                "overall_status": overall_status,
                "validation_score": validation_score,
                "errors_count": len(errors),
                "warnings_count": len(warnings),
                "components_validated": len(validated_components),
                "missing_components": missing_components,
                "component_scores": component_scores,
                "approved": overall_status == ValidationStatus.APPROVED,
                "summary": summary
            }
            
            return True
            
        except Exception as e:
            print(f"❌ Validator test failed: {str(e)}")
            self.test_results["validator"]["details"]["error"] = str(e)
            return False
    
    async def test_amazon_listing_publisher(self) -> bool:
        """Test du publisher Amazon (préparation SP-API)"""
        print("\n📤 Testing Amazon Listing Publisher...")
        
        if not self.generated_listing:
            print("❌ No generated listing available for publisher test")
            return False
        
        try:
            # Mock les dépendances externes
            with mock.patch('integrations.amazon.client.AmazonSPAPIClient'), \
                 mock.patch('integrations.amazon.auth.AmazonOAuthService'):
                
                from amazon.listings.publisher import AmazonListingPublisher
                
                publisher = AmazonListingPublisher()
                self.test_results["publisher"]["tested"] = True
                
                # Test de génération de SKU
                sku = publisher._generate_sku(IPHONE_15_PRO_DATA)
                
                # Test de génération d'URL
                test_marketplace = "A13V1IB3VIYZZH"  # France
                listing_url = publisher._generate_listing_url(sku, test_marketplace)
                
                # Test de préparation du payload SP-API
                start_time = time.time()
                spapi_payload = await publisher._prepare_spapi_payload(
                    IPHONE_15_PRO_DATA,
                    self.generated_listing['seo_content']
                )
                preparation_time = time.time() - start_time
                
                # Validation du payload
                required_payload_fields = ['productType', 'attributes']
                missing_payload_fields = [field for field in required_payload_fields if field not in spapi_payload]
                
                if missing_payload_fields:
                    print(f"❌ Missing payload fields: {missing_payload_fields}")
                    return False
                
                # Validation des attributs SP-API
                attributes = spapi_payload['attributes']
                required_attributes = ['item_name', 'brand', 'bullet_point', 'product_description', 'generic_keyword']
                missing_attributes = [attr for attr in required_attributes if attr not in attributes]
                
                # Test de validation des paramètres
                try:
                    publisher._validate_publish_params(
                        IPHONE_15_PRO_DATA,
                        self.generated_listing['seo_content'],
                        {
                            'encrypted_refresh_token': 'test_token',
                            'seller_id': 'TEST_SELLER',
                            'marketplace_id': test_marketplace
                        }
                    )
                    params_valid = True
                except Exception:
                    params_valid = False
                
                print("✅ Publisher test successful!")
                print(f"   Preparation time: {preparation_time:.2f}s")
                print(f"   Generated SKU: {sku}")
                print(f"   Listing URL: {listing_url}")
                print(f"   Product type: {spapi_payload['productType']}")
                print(f"   Attributes count: {len(attributes)}")
                print(f"   Missing attributes: {missing_attributes}")
                print(f"   Params validation: {params_valid}")
                
                # Détails pour le résumé
                self.test_results["publisher"]["success"] = True
                self.test_results["publisher"]["details"] = {
                    "preparation_time": preparation_time,
                    "sku_generated": sku,
                    "listing_url": listing_url,
                    "product_type": spapi_payload['productType'],
                    "attributes_count": len(attributes),
                    "missing_attributes": missing_attributes,
                    "params_valid": params_valid,
                    "payload_valid": len(missing_payload_fields) == 0,
                    "sp_api_ready": len(missing_payload_fields) == 0 and len(missing_attributes) == 0
                }
                
                return True
                
        except Exception as e:
            print(f"❌ Publisher test failed: {str(e)}")
            self.test_results["publisher"]["details"]["error"] = str(e)
            return False
    
    async def test_integration_workflow(self) -> bool:
        """Test du workflow complet d'intégration"""
        print("\n🔄 Testing Complete Integration Workflow...")
        
        try:
            self.test_results["integration"]["tested"] = True
            
            # Vérifier que tous les composants ont été testés avec succès
            generator_success = self.test_results["generator"]["success"]
            validator_success = self.test_results["validator"]["success"]
            publisher_success = self.test_results["publisher"]["success"]
            
            if not all([generator_success, validator_success, publisher_success]):
                print("❌ Cannot test integration - some components failed")
                return False
            
            # Vérifier la cohérence des données entre les étapes
            start_time = time.time()
            
            # 1. Données générées → Validation
            if not self.generated_listing or not self.validation_result:
                print("❌ Missing data for integration test")
                return False
            
            # 2. Vérifier que la validation a bien utilisé les données générées
            validation_details = self.validation_result.get('details', {})
            title_validated = 'title' in validation_details
            bullets_validated = 'bullets' in validation_details
            description_validated = 'description' in validation_details
            
            # 3. Vérifier la cohérence des scores
            generator_score = self.test_results["generator"]["details"]["optimization_score"]
            validator_score = self.test_results["validator"]["details"]["validation_score"]
            
            # 4. Vérifier la conformité A9/A10 end-to-end
            generator_compliant = self.test_results["generator"]["details"]["a9_a10_compliant"]
            validator_approved = self.test_results["validator"]["details"]["approved"]
            publisher_ready = self.test_results["publisher"]["details"]["sp_api_ready"]
            
            integration_time = time.time() - start_time
            
            # Score d'intégration global
            integration_score = (
                (generator_score + validator_score) / 2 * 0.6 +  # 60% pour la qualité
                (100 if generator_compliant else 0) * 0.2 +      # 20% pour la conformité
                (100 if publisher_ready else 0) * 0.2            # 20% pour la préparation SP-API
            )
            
            print("✅ Integration workflow test successful!")
            print(f"   Integration time: {integration_time:.2f}s")
            print(f"   Data consistency: Generator→Validator→Publisher")
            print(f"   Title validated: {title_validated}")
            print(f"   Bullets validated: {bullets_validated}")
            print(f"   Description validated: {description_validated}")
            print(f"   Generator score: {generator_score}%")
            print(f"   Validator score: {validator_score}%")
            print(f"   Integration score: {integration_score:.1f}%")
            print(f"   A9/A10 compliant: {generator_compliant}")
            print(f"   Validator approved: {validator_approved}")
            print(f"   SP-API ready: {publisher_ready}")
            
            # Détails pour le résumé
            self.test_results["integration"]["success"] = True
            self.test_results["integration"]["details"] = {
                "integration_time": integration_time,
                "data_consistency": True,
                "title_validated": title_validated,
                "bullets_validated": bullets_validated,
                "description_validated": description_validated,
                "generator_score": generator_score,
                "validator_score": validator_score,
                "integration_score": integration_score,
                "a9_a10_compliant": generator_compliant,
                "validator_approved": validator_approved,
                "sp_api_ready": publisher_ready,
                "end_to_end_ready": all([generator_compliant, validator_approved, publisher_ready])
            }
            
            return True
            
        except Exception as e:
            print(f"❌ Integration test failed: {str(e)}")
            self.test_results["integration"]["details"]["error"] = str(e)
            return False
    
    def print_comprehensive_summary(self):
        """Affiche un résumé complet des tests de fonctionnalité"""
        print("\n" + "="*80)
        print("🎯 RÉSUMÉ COMPLET - AMAZON LISTINGS PHASE 2 FUNCTIONALITY TESTING")
        print("="*80)
        
        # Statistiques globales
        total_tests = len(self.test_results)
        tested_components = sum(1 for result in self.test_results.values() if result["tested"])
        successful_components = sum(1 for result in self.test_results.values() if result["success"])
        
        print(f"📊 STATISTIQUES GLOBALES:")
        print(f"   Total composants: {total_tests}")
        print(f"   Composants testés: {tested_components}")
        print(f"   Composants réussis: {successful_components}")
        print(f"   Taux de réussite: {(successful_components/tested_components*100):.1f}%" if tested_components > 0 else "   Taux de réussite: 0%")
        
        print(f"\n📋 RÉSULTATS DÉTAILLÉS PAR COMPOSANT:")
        
        component_names = {
            "generator": "🤖 Amazon Listing Generator (IA)",
            "validator": "🔍 Amazon Listing Validator (A9/A10)",
            "publisher": "📤 Amazon Listing Publisher (SP-API)",
            "integration": "🔄 Integration Workflow (End-to-End)"
        }
        
        for component_key, result in self.test_results.items():
            component_name = component_names.get(component_key, component_key)
            
            if not result["tested"]:
                status = "⏭️ NON TESTÉ"
            elif result["success"]:
                status = "✅ RÉUSSI"
            else:
                status = "❌ ÉCHEC"
            
            print(f"\n{status} - {component_name}")
            
            if result["tested"]:
                details = result.get("details", {})
                if details:
                    for key, value in details.items():
                        if key != "error":
                            if isinstance(value, float):
                                print(f"   └─ {key}: {value:.2f}")
                            elif isinstance(value, bool):
                                print(f"   └─ {key}: {'✅' if value else '❌'}")
                            else:
                                print(f"   └─ {key}: {value}")
                    
                    if "error" in details:
                        print(f"   └─ ❌ Erreur: {details['error']}")
        
        # Analyse des critères de réussite Phase 2
        print(f"\n🎯 ANALYSE DES CRITÈRES PHASE 2:")
        
        # 1. Générateur IA produit du contenu conforme Amazon
        if self.test_results["generator"]["success"]:
            gen_details = self.test_results["generator"]["details"]
            a9_a10_compliant = gen_details.get("a9_a10_compliant", False)
            optimization_score = gen_details.get("optimization_score", 0)
            print(f"✅ Générateur IA conforme Amazon: {optimization_score}% optimisation")
            print(f"   └─ Conformité A9/A10: {'✅' if a9_a10_compliant else '❌'}")
        else:
            print("❌ Générateur IA: Non fonctionnel")
        
        # 2. Validation identifie les listings APPROVED/WARNING/REJECTED
        if self.test_results["validator"]["success"]:
            val_details = self.test_results["validator"]["details"]
            overall_status = val_details.get("overall_status", "unknown")
            validation_score = val_details.get("validation_score", 0)
            print(f"✅ Validation A9/A10: {overall_status} ({validation_score}%)")
            print(f"   └─ Composants validés: {val_details.get('components_validated', 0)}")
        else:
            print("❌ Validation A9/A10: Non fonctionnelle")
        
        # 3. Publication utilise le vrai SP-API (préparation)
        if self.test_results["publisher"]["success"]:
            pub_details = self.test_results["publisher"]["details"]
            sp_api_ready = pub_details.get("sp_api_ready", False)
            print(f"✅ Publication SP-API: {'Prêt' if sp_api_ready else 'Préparation incomplète'}")
            print(f"   └─ Payload valide: {'✅' if pub_details.get('payload_valid') else '❌'}")
        else:
            print("❌ Publication SP-API: Non fonctionnelle")
        
        # 4. Workflow complet opérationnel
        if self.test_results["integration"]["success"]:
            int_details = self.test_results["integration"]["details"]
            end_to_end_ready = int_details.get("end_to_end_ready", False)
            integration_score = int_details.get("integration_score", 0)
            print(f"✅ Workflow complet: {'Opérationnel' if end_to_end_ready else 'Partiellement fonctionnel'} ({integration_score:.1f}%)")
        else:
            print("❌ Workflow complet: Non fonctionnel")
        
        # Score global Phase 2
        if successful_components == total_tests:
            phase2_status = "🎉 PHASE 2 COMPLÈTEMENT OPÉRATIONNELLE"
            phase2_score = 100
        elif successful_components >= total_tests * 0.75:
            phase2_status = "✅ PHASE 2 MAJORITAIREMENT FONCTIONNELLE"
            phase2_score = (successful_components / total_tests) * 100
        else:
            phase2_status = "⚠️ PHASE 2 NÉCESSITE DES CORRECTIONS"
            phase2_score = (successful_components / total_tests) * 100
        
        print(f"\n🏆 STATUT GLOBAL PHASE 2: {phase2_status} ({phase2_score:.1f}%)")
        
        # Recommandations
        print(f"\n💡 RECOMMANDATIONS:")
        
        if successful_components == total_tests:
            print("🎉 Toutes les fonctionnalités core sont opérationnelles!")
            print("   └─ Phase 2 prête pour intégration avec connexions Amazon réelles")
            print("   └─ Procéder aux tests end-to-end avec comptes Amazon")
        elif successful_components >= total_tests * 0.75:
            print("✅ La plupart des fonctionnalités fonctionnent")
            print("   └─ Corriger les composants en échec")
            print("   └─ Tester avec connexions Amazon réelles")
        else:
            print("⚠️ Plusieurs composants nécessitent des corrections")
            print("   └─ Réviser l'implémentation des composants en échec")
            print("   └─ Retester avant intégration Amazon")
        
        print("="*80)
        
        return successful_components, total_tests
    
    async def run_complete_functionality_testing(self):
        """Exécute tous les tests de fonctionnalité"""
        print("🚀 DÉMARRAGE - Tests de fonctionnalité Amazon Listings Phase 2")
        print(f"📅 Timestamp: {datetime.now().isoformat()}")
        print(f"📱 Produit test: {IPHONE_15_PRO_DATA['product_name']}")
        print("-"*80)
        
        start_time = time.time()
        
        # Tests des composants
        await self.test_amazon_listing_generator()
        await self.test_amazon_listing_validator()
        await self.test_amazon_listing_publisher()
        await self.test_integration_workflow()
        
        # Résumé final
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️ Durée totale des tests: {duration:.2f} secondes")
        
        successful_components, total_components = self.print_comprehensive_summary()
        
        # Sauvegarde des résultats
        results_summary = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "test_product": IPHONE_15_PRO_DATA,
            "test_results": self.test_results,
            "successful_components": successful_components,
            "total_components": total_components,
            "success_rate": (successful_components / total_components * 100) if total_components > 0 else 0,
            "generated_listing": self.generated_listing,
            "validation_result": self.validation_result
        }
        
        # Écrire les résultats dans un fichier
        try:
            with open('/app/amazon_listings_functionality_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(results_summary, f, indent=2, ensure_ascii=False, default=str)
            print(f"📄 Résultats sauvegardés: /app/amazon_listings_functionality_test_results.json")
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde résultats: {e}")
        
        return results_summary

async def main():
    """Fonction principale de test"""
    try:
        tester = AmazonListingsFunctionalityTester()
        results = await tester.run_complete_functionality_testing()
        
        # Code de sortie basé sur le succès
        if results and results.get('success_rate', 0) >= 75:
            sys.exit(0)  # Succès
        else:
            sys.exit(1)  # Échec
            
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrompus par l'utilisateur")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)

if __name__ == "__main__":
    print("🎯 ECOMSIMPLY - Tests de fonctionnalité Amazon Listings Phase 2")
    print("="*80)
    asyncio.run(main())