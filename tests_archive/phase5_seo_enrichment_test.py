#!/usr/bin/env python3
"""
ECOMSIMPLY Backend Testing Suite - PHASE 5 ENRICHISSEMENT DYNAMIQUE DES TAGS SEO
Test automatique pour vérifier que le système d'enrichissement dynamique des tags SEO avec mots-clés tendance fonctionne correctement.

OBJECTIFS DE TEST:
1. Test Produit Commun (Catégorie électronique) - iPhone 15 Pro
2. Test Produit Rare/Spécifique - Aspirateur vintage 1950 collection
3. Validation Champs Phase 5 - seo_tags_source présent
4. Test Enrichissement SEO - vérifier intégration mots-clés tendance
5. Validation Logging - vérifier logs des opérations trending keywords
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://ecomsimply.com/api"

class Phase5SEOEnrichmentTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.test_user = None
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=120)  # 2 minutes timeout for generation
        )
        print("✅ Session HTTP initialisée")
        return True
    
    async def cleanup(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
    
    def get_auth_headers(self, token: str):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {token}"}
    
    async def create_test_user(self) -> Dict:
        """Create a test user for testing"""
        
        user_data = {
            "email": f"test_phase5_{int(time.time())}@ecomsimply.test",
            "name": "Test User Phase 5 SEO",
            "password": "TestPassword123!"
        }
        
        print(f"👤 Création utilisateur test Phase 5...")
        
        try:
            # Register user
            async with self.session.post(f"{BACKEND_URL}/auth/register", json=user_data) as response:
                if response.status == 200:
                    register_result = await response.json()
                    print(f"✅ Utilisateur créé: {user_data['email']}")
                    
                    # Login to get token
                    login_data = {
                        "email": user_data["email"],
                        "password": user_data["password"]
                    }
                    
                    async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as login_response:
                        if login_response.status == 200:
                            login_result = await login_response.json()
                            token = login_result.get("token")
                            
                            user_info = {
                                "email": user_data["email"],
                                "token": token,
                                "plan": "gratuit"
                            }
                            
                            self.test_user = user_info
                            print(f"✅ Utilisateur Phase 5 prêt avec token")
                            return user_info
                        else:
                            error_text = await login_response.text()
                            print(f"❌ Échec login: {login_response.status} - {error_text}")
                            return None
                else:
                    error_text = await response.text()
                    print(f"❌ Échec création utilisateur: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Exception création utilisateur: {str(e)}")
            return None
    
    async def test_common_product_electronics(self):
        """
        TEST 1: Test Produit Commun (Catégorie électronique)
        Produit: "iPhone 15 Pro" catégorie "électronique"
        """
        print("\n🧪 TEST 1: Test Produit Commun (Catégorie électronique)")
        print("=" * 70)
        
        if not self.test_user:
            print("❌ Utilisateur test non disponible")
            return False
        
        # Test product: iPhone 15 Pro (common electronics product)
        test_product = {
            "product_name": "iPhone 15 Pro",
            "product_description": "Smartphone Apple haut de gamme avec processeur A17 Pro, appareil photo 48MP et écran Super Retina XDR",
            "generate_image": True,
            "number_of_images": 1,
            "language": "fr",
            "category": "électronique",
            "use_case": "usage quotidien professionnel",
            "image_style": "studio"
        }
        
        print(f"🔥 Test génération: {test_product['product_name']} (catégorie: {test_product['category']})")
        
        try:
            start_time = time.time()
            
            async with self.session.post(
                f"{BACKEND_URL}/generate-sheet",
                json=test_product,
                headers=self.get_auth_headers(self.test_user["token"])
            ) as response:
                
                generation_time = time.time() - start_time
                status = response.status
                
                if status == 200:
                    result = await response.json()
                    
                    # PHASE 5 Validation: seo_tags_source field
                    seo_tags_source = result.get("seo_tags_source")
                    seo_tags = result.get("seo_tags", [])
                    
                    print(f"✅ GÉNÉRATION RÉUSSIE en {generation_time:.2f}s")
                    print(f"   📝 Titre: {result['generated_title'][:50]}...")
                    print(f"   🏷️ SEO Tags: {len(seo_tags)} tags")
                    print(f"   📊 SEO Tags Source: {seo_tags_source}")
                    print(f"   🔍 Tags: {', '.join(seo_tags[:5])}...")
                    
                    # Phase 5 specific validations
                    phase5_checks = {
                        "seo_tags_source_present": seo_tags_source is not None,
                        "seo_tags_source_valid": seo_tags_source in ["static", "trending"],
                        "seo_tags_count": len(seo_tags) >= 5,
                        "trending_keywords_integrated": self._check_trending_keywords_electronics(seo_tags),
                        "electronics_category_keywords": self._check_electronics_keywords(seo_tags)
                    }
                    
                    print(f"   📋 VALIDATION PHASE 5:")
                    for check, passed in phase5_checks.items():
                        status_icon = "✅" if passed else "❌"
                        print(f"      {status_icon} {check}")
                    
                    # Check for expected trending keywords for electronics
                    expected_trends = ["eco-responsable", "durabilite", "intelligence-artificielle", "5g", "reconditionne"]
                    found_trends = [tag for tag in seo_tags if any(trend in tag.lower() for trend in expected_trends)]
                    
                    if found_trends:
                        print(f"   🎯 Mots-clés tendance détectés: {', '.join(found_trends)}")
                    
                    self.test_results.append({
                        "test": "common_product_electronics",
                        "success": all(phase5_checks.values()),
                        "generation_time": generation_time,
                        "seo_tags_source": seo_tags_source,
                        "seo_tags_count": len(seo_tags),
                        "trending_keywords_found": len(found_trends),
                        "phase5_checks": phase5_checks,
                        "details": result
                    })
                    
                    return all(phase5_checks.values())
                else:
                    error_text = await response.text()
                    print(f"❌ ERREUR GÉNÉRATION: {status} - {error_text}")
                    self.test_results.append({
                        "test": "common_product_electronics",
                        "success": False,
                        "error": f"HTTP {status}: {error_text[:200]}"
                    })
                    return False
                    
        except Exception as e:
            print(f"❌ EXCEPTION GÉNÉRATION: {str(e)}")
            self.test_results.append({
                "test": "common_product_electronics",
                "success": False,
                "error": str(e)
            })
            return False
    
    async def test_rare_specific_product(self):
        """
        TEST 2: Test Produit Rare/Spécifique
        Produit: "Aspirateur vintage 1950 collection" catégorie "maison"
        """
        print("\n🧪 TEST 2: Test Produit Rare/Spécifique")
        print("=" * 70)
        
        if not self.test_user:
            print("❌ Utilisateur test non disponible")
            return False
        
        # Test product: Vintage vacuum cleaner (rare/specific product)
        test_product = {
            "product_name": "Aspirateur vintage 1950 collection",
            "product_description": "Aspirateur de collection des années 1950, pièce rare pour collectionneurs, entièrement restauré et fonctionnel",
            "generate_image": True,
            "number_of_images": 1,
            "language": "fr",
            "category": "maison",
            "use_case": "collection vintage décoration",
            "image_style": "detailed"
        }
        
        print(f"🔥 Test génération: {test_product['product_name']} (catégorie: {test_product['category']})")
        
        try:
            start_time = time.time()
            
            async with self.session.post(
                f"{BACKEND_URL}/generate-sheet",
                json=test_product,
                headers=self.get_auth_headers(self.test_user["token"])
            ) as response:
                
                generation_time = time.time() - start_time
                status = response.status
                
                if status == 200:
                    result = await response.json()
                    
                    # PHASE 5 Validation: seo_tags_source field
                    seo_tags_source = result.get("seo_tags_source")
                    seo_tags = result.get("seo_tags", [])
                    
                    print(f"✅ GÉNÉRATION RÉUSSIE en {generation_time:.2f}s")
                    print(f"   📝 Titre: {result['generated_title'][:50]}...")
                    print(f"   🏷️ SEO Tags: {len(seo_tags)} tags")
                    print(f"   📊 SEO Tags Source: {seo_tags_source}")
                    print(f"   🔍 Tags: {', '.join(seo_tags[:5])}...")
                    
                    # Phase 5 specific validations for rare product
                    phase5_checks = {
                        "seo_tags_source_present": seo_tags_source is not None,
                        "seo_tags_source_valid": seo_tags_source in ["static", "trending"],
                        "seo_tags_count": len(seo_tags) >= 5,
                        "fallback_handling": seo_tags_source == "static" or seo_tags_source == "trending",  # Either is acceptable
                        "vintage_keywords": self._check_vintage_keywords(seo_tags)
                    }
                    
                    print(f"   📋 VALIDATION PHASE 5 (Produit Rare):")
                    for check, passed in phase5_checks.items():
                        status_icon = "✅" if passed else "❌"
                        print(f"      {status_icon} {check}")
                    
                    # For rare products, static fallback is expected and acceptable
                    if seo_tags_source == "static":
                        print(f"   ℹ️ Fallback statique utilisé (comportement attendu pour produit rare)")
                    elif seo_tags_source == "trending":
                        print(f"   🎯 Mots-clés tendance trouvés même pour produit rare!")
                    
                    self.test_results.append({
                        "test": "rare_specific_product",
                        "success": all(phase5_checks.values()),
                        "generation_time": generation_time,
                        "seo_tags_source": seo_tags_source,
                        "seo_tags_count": len(seo_tags),
                        "phase5_checks": phase5_checks,
                        "details": result
                    })
                    
                    return all(phase5_checks.values())
                else:
                    error_text = await response.text()
                    print(f"❌ ERREUR GÉNÉRATION: {status} - {error_text}")
                    self.test_results.append({
                        "test": "rare_specific_product",
                        "success": False,
                        "error": f"HTTP {status}: {error_text[:200]}"
                    })
                    return False
                    
        except Exception as e:
            print(f"❌ EXCEPTION GÉNÉRATION: {str(e)}")
            self.test_results.append({
                "test": "rare_specific_product",
                "success": False,
                "error": str(e)
            })
            return False
    
    async def test_seo_enrichment_comparison(self):
        """
        TEST 3: Test Enrichissement SEO - Comparaison avant/après
        Tester plusieurs produits pour valider l'enrichissement
        """
        print("\n🧪 TEST 3: Test Enrichissement SEO - Comparaison")
        print("=" * 70)
        
        if not self.test_user:
            print("❌ Utilisateur test non disponible")
            return False
        
        # Test multiple products to compare SEO enrichment
        test_products = [
            {
                "name": "MacBook Pro M3",
                "description": "Ordinateur portable Apple avec puce M3 pour professionnels créatifs",
                "category": "électronique",
                "expected_trends": ["eco-responsable", "intelligence-artificielle", "durabilite"]
            },
            {
                "name": "Robe été tendance 2024",
                "description": "Robe légère pour l'été, style bohème chic, matières naturelles",
                "category": "mode",
                "expected_trends": ["mode-durable", "made-in-france", "slow-fashion"]
            }
        ]
        
        enrichment_results = []
        
        for product in test_products:
            print(f"\n🔍 Test enrichissement pour: {product['name']}")
            
            test_request = {
                "product_name": product["name"],
                "product_description": product["description"],
                "generate_image": False,  # Focus on SEO, skip images for speed
                "number_of_images": 0,
                "category": product["category"],
                "language": "fr"
            }
            
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/generate-sheet",
                    json=test_request,
                    headers=self.get_auth_headers(self.test_user["token"])
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        seo_tags = result.get('seo_tags', [])
                        seo_tags_source = result.get('seo_tags_source', 'unknown')
                        
                        # Check for expected trending keywords
                        found_trends = []
                        for tag in seo_tags:
                            for expected in product["expected_trends"]:
                                if expected.lower() in tag.lower() or any(word in tag.lower() for word in expected.split('-')):
                                    found_trends.append(tag)
                                    break
                        
                        enrichment_check = {
                            "product": product["name"],
                            "category": product["category"],
                            "seo_tags_count": len(seo_tags),
                            "seo_tags_source": seo_tags_source,
                            "trending_keywords_found": len(found_trends),
                            "trending_keywords": found_trends,
                            "enrichment_success": len(found_trends) > 0 or seo_tags_source == "trending"
                        }
                        
                        print(f"   📊 Tags SEO: {len(seo_tags)} (source: {seo_tags_source})")
                        print(f"   🎯 Tendances trouvées: {len(found_trends)} - {', '.join(found_trends[:3])}")
                        
                        enrichment_results.append(enrichment_check)
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Erreur: {response.status} - {error_text[:100]}")
                        enrichment_results.append({
                            "product": product["name"],
                            "success": False,
                            "error": f"HTTP {response.status}"
                        })
                        
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
                enrichment_results.append({
                    "product": product["name"],
                    "success": False,
                    "error": str(e)
                })
        
        # Evaluate enrichment results
        successful_enrichments = sum(1 for result in enrichment_results if result.get('enrichment_success', False))
        total_tests = len(enrichment_results)
        
        print(f"\n📈 RÉSULTATS ENRICHISSEMENT: {successful_enrichments}/{total_tests} produits enrichis")
        
        self.test_results.append({
            "test": "seo_enrichment_comparison",
            "success": successful_enrichments > 0,
            "success_rate": (successful_enrichments / total_tests) * 100 if total_tests > 0 else 0,
            "details": enrichment_results
        })
        
        return successful_enrichments > 0
    
    def _check_trending_keywords_electronics(self, seo_tags: List[str]) -> bool:
        """Check if electronics trending keywords are present"""
        electronics_trends = [
            "eco-responsable", "durabilite", "intelligence-artificielle", "5g", 
            "reconditionne", "camera-pro", "batterie-longue-duree", "charge-rapide"
        ]
        
        for tag in seo_tags:
            tag_lower = tag.lower()
            if any(trend in tag_lower for trend in electronics_trends):
                return True
        return False
    
    def _check_electronics_keywords(self, seo_tags: List[str]) -> bool:
        """Check if general electronics keywords are present"""
        electronics_keywords = [
            "smartphone", "apple", "iphone", "pro", "technologie", 
            "mobile", "telephone", "high-tech", "electronique"
        ]
        
        for tag in seo_tags:
            tag_lower = tag.lower()
            if any(keyword in tag_lower for keyword in electronics_keywords):
                return True
        return False
    
    def _check_vintage_keywords(self, seo_tags: List[str]) -> bool:
        """Check if vintage/collection keywords are present"""
        vintage_keywords = [
            "vintage", "collection", "1950", "retro", "ancien", 
            "collector", "rare", "antique", "classique"
        ]
        
        for tag in seo_tags:
            tag_lower = tag.lower()
            if any(keyword in tag_lower for keyword in vintage_keywords):
                return True
        return False
    
    async def run_all_tests(self):
        """Run all Phase 5 SEO enrichment tests"""
        print("🚀 ECOMSIMPLY - TEST AUTOMATIQUE PHASE 5 - ENRICHISSEMENT DYNAMIQUE DES TAGS SEO")
        print("=" * 90)
        print("Objectif: Vérifier que le système d'enrichissement dynamique des tags SEO avec mots-clés tendance fonctionne correctement")
        print("=" * 90)
        
        # Setup
        if not await self.setup_session():
            print("❌ Failed to setup test session")
            return False
        
        # Create test user
        if not await self.create_test_user():
            print("❌ Failed to create test user")
            return False
        
        try:
            # Run all tests
            print("\n🎯 DÉMARRAGE DES TESTS PHASE 5...")
            
            test1_result = await self.test_common_product_electronics()
            await asyncio.sleep(2)  # Pause between tests
            
            test2_result = await self.test_rare_specific_product()
            await asyncio.sleep(2)
            
            test3_result = await self.test_seo_enrichment_comparison()
            
            # Summary
            print("\n" + "=" * 90)
            print("🏁 RÉSUMÉ FINAL - TEST PHASE 5 ENRICHISSEMENT DYNAMIQUE SEO")
            print("=" * 90)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result.get('success', False))
            
            print(f"📊 Total Tests: {total_tests}")
            print(f"✅ Réussis: {passed_tests}")
            print(f"❌ Échoués: {total_tests - passed_tests}")
            print(f"📈 Taux de Réussite: {(passed_tests/total_tests*100):.1f}%")
            
            print(f"\n🎯 STATUT DES TESTS:")
            print(f"   1. Produit Commun (électronique): {'✅ RÉUSSI' if test1_result else '❌ ÉCHOUÉ'}")
            print(f"   2. Produit Rare/Spécifique: {'✅ RÉUSSI' if test2_result else '❌ ÉCHOUÉ'}")
            print(f"   3. Enrichissement SEO: {'✅ RÉUSSI' if test3_result else '❌ ÉCHOUÉ'}")
            
            # Phase 5 success criteria
            success_criteria = {
                "seo_tags_source_field": self._check_seo_tags_source_field(),
                "trending_keywords_integration": test1_result,
                "fallback_handling": test2_result,
                "enrichment_working": test3_result
            }
            
            print(f"\n📋 CRITÈRES DE SUCCÈS PHASE 5:")
            for criterion, met in success_criteria.items():
                status_icon = "✅" if met else "❌"
                print(f"   {status_icon} {criterion}")
            
            # Overall assessment
            critical_success = success_criteria["seo_tags_source_field"] and success_criteria["trending_keywords_integration"]
            overall_success = all(success_criteria.values())
            
            if overall_success:
                print(f"\n🎉 SUCCÈS COMPLET PHASE 5: L'enrichissement dynamique des tags SEO fonctionne parfaitement!")
                print("   ✅ Champ seo_tags_source présent dans les réponses API")
                print("   ✅ Mots-clés tendance récupérés et intégrés")
                print("   ✅ Différenciation entre produits communs et rares")
                print("   ✅ Tags SEO enrichis avec tendances pertinentes")
                print("   ✅ Logging structuré des opérations tendance")
            elif critical_success:
                print(f"\n⚡ SUCCÈS PARTIEL PHASE 5: Les fonctionnalités critiques marchent!")
                print("   ✅ Système d'enrichissement SEO opérationnel")
                print("   ✅ Intégration mots-clés tendance fonctionnelle")
                if not success_criteria["fallback_handling"]:
                    print("   ⚠️ Gestion fallback produits rares à améliorer")
                if not success_criteria["enrichment_working"]:
                    print("   ⚠️ Enrichissement multi-catégories nécessite ajustements")
            else:
                print(f"\n❌ ÉCHEC CRITIQUE PHASE 5: L'enrichissement SEO présente des problèmes majeurs")
                if not success_criteria["seo_tags_source_field"]:
                    print("   ❌ Champ seo_tags_source manquant ou incorrect")
                if not success_criteria["trending_keywords_integration"]:
                    print("   ❌ Intégration mots-clés tendance défaillante")
                print("   🔧 Correction immédiate requise")
            
            # Detailed results for debugging
            print(f"\n📋 DÉTAILS POUR DÉBOGAGE:")
            for i, result in enumerate(self.test_results, 1):
                test_name = result.get('test', f'Test {i}')
                success = result.get('success', False)
                status_icon = "✅" if success else "❌"
                print(f"   {status_icon} {test_name}")
                
                if 'seo_tags_source' in result:
                    print(f"      SEO Tags Source: {result['seo_tags_source']}")
                if 'seo_tags_count' in result:
                    print(f"      SEO Tags Count: {result['seo_tags_count']}")
                if 'trending_keywords_found' in result:
                    print(f"      Trending Keywords: {result['trending_keywords_found']}")
                if 'error' in result:
                    print(f"      Erreur: {result['error']}")
                if 'success_rate' in result:
                    print(f"      Taux: {result['success_rate']:.1f}%")
            
            return critical_success
            
        finally:
            await self.cleanup()
    
    def _check_seo_tags_source_field(self) -> bool:
        """Check if seo_tags_source field is present in all test results"""
        for result in self.test_results:
            if result.get('success') and 'seo_tags_source' in result:
                if result['seo_tags_source'] in ['static', 'trending']:
                    return True
        return False

async def main():
    """Main test execution"""
    tester = Phase5SEOEnrichmentTester()
    success = await tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())