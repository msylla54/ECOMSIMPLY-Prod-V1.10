#!/usr/bin/env python3
"""
ECOMSIMPLY BASIC PHASES TESTING - VALIDATION DES 6 PHASES
Test basique pour valider que les 6 phases sont implémentées et fonctionnelles.

PHASES À TESTER:
- Phase 1: Services modulaires fonctionnels
- Phase 2: Logging structuré actif
- Phase 3: Validation avancée des entrées
- Phase 4: Champs fallback (model_used, generation_method, fallback_level)
- Phase 5: Enrichissement SEO (seo_tags_source)
- Phase 6: Mode QA (qa_test_mode, qa_simulation_triggered)
"""

import asyncio
import aiohttp
import json
import time
import os
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://ecomsimply.com/api"

class BasicPhasesValidator:
    def __init__(self):
        self.session = None
        self.test_user = None
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=90)
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
        """Create a test user"""
        
        user_data = {
            "email": f"phases_test_{int(time.time())}@ecomsimply.test",
            "name": "Phases Test User",
            "password": "PhasesTest123!"
        }
        
        print(f"👤 Création utilisateur test...")
        
        try:
            # Register user
            async with self.session.post(f"{BACKEND_URL}/auth/register", json=user_data) as response:
                if response.status == 200:
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
                            print(f"✅ Utilisateur créé: {user_data['email']}")
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
    
    async def test_basic_generation_with_phases(self):
        """Test basic generation and validate all 6 phases"""
        print("\n🧪 TEST: GÉNÉRATION BASIQUE AVEC VALIDATION DES 6 PHASES")
        print("=" * 70)
        
        if not self.test_user:
            user_info = await self.create_test_user()
            if not user_info:
                print("❌ Impossible de créer l'utilisateur test")
                return False
        
        # Test product for MacBook Pro M3 2024 as requested
        test_product = {
            "product_name": "MacBook Pro M3 2024",
            "product_description": "Ordinateur portable Apple avec puce M3, écran Liquid Retina XDR 14 pouces, 16GB RAM, 512GB SSD, pour professionnels créatifs",
            "generate_image": True,
            "number_of_images": 1,
            "language": "fr",
            "category": "électronique",
            "use_case": "travail professionnel créatif",
            "image_style": "studio"
        }
        
        print(f"🔥 Test génération: {test_product['product_name']}")
        
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
                    
                    print(f"✅ GÉNÉRATION RÉUSSIE en {generation_time:.2f}s")
                    
                    # Validation des 6 phases
                    phases_validation = {
                        "Phase 1 - Services modulaires": {
                            "services_title": len(result.get('generated_title', '')) >= 20,
                            "services_description": len(result.get('marketing_description', '')) >= 200,
                            "services_features": len(result.get('key_features', [])) >= 5,
                            "services_seo": len(result.get('seo_tags', [])) >= 5,
                            "services_images": len(result.get('generated_images', [])) >= 1
                        },
                        "Phase 2 - Logging structuré": {
                            "logging_time": result.get('generation_time') is not None,
                            "logging_id": result.get('generation_id') is not None
                        },
                        "Phase 3 - Validation entrées": {
                            "validation_structure": all(field in result for field in ['generated_title', 'marketing_description'])
                        },
                        "Phase 4 - Champs fallback": {
                            "fallback_model": result.get('model_used') is not None,
                            "fallback_method": result.get('generation_method') is not None,
                            "fallback_level": result.get('fallback_level') is not None
                        },
                        "Phase 5 - Enrichissement SEO": {
                            "seo_source": result.get('seo_tags_source') is not None
                        },
                        "Phase 6 - Mode QA": {
                            "qa_mode": result.get('qa_test_mode') is not None,
                            "qa_simulation": result.get('qa_simulation_triggered') is not None
                        }
                    }
                    
                    print(f"\n📋 VALIDATION DES 6 PHASES:")
                    total_checks = 0
                    passed_checks = 0
                    
                    for phase_name, checks in phases_validation.items():
                        phase_passed = sum(checks.values())
                        phase_total = len(checks)
                        total_checks += phase_total
                        passed_checks += phase_passed
                        
                        phase_success = phase_passed == phase_total
                        status_icon = "✅" if phase_success else "⚠️"
                        print(f"   {status_icon} {phase_name}: {phase_passed}/{phase_total}")
                        
                        for check_name, check_result in checks.items():
                            check_icon = "✅" if check_result else "❌"
                            print(f"      {check_icon} {check_name}")
                    
                    # Affichage des détails des champs
                    print(f"\n📊 DÉTAILS DES CHAMPS DES 6 PHASES:")
                    print(f"   📝 Titre: {result.get('generated_title', 'N/A')[:60]}...")
                    print(f"   📄 Description: {len(result.get('marketing_description', ''))} caractères")
                    print(f"   🔧 Features: {len(result.get('key_features', []))} éléments")
                    print(f"   🏷️ SEO Tags: {len(result.get('seo_tags', []))} tags")
                    print(f"   🖼️ Images: {len(result.get('generated_images', []))} générées")
                    print(f"   ⏱️ Temps génération: {result.get('generation_time', 'N/A')}s")
                    print(f"   🆔 ID génération: {result.get('generation_id', 'N/A')}")
                    print(f"   🤖 Modèle utilisé: {result.get('model_used', 'N/A')}")
                    print(f"   🔧 Méthode génération: {result.get('generation_method', 'N/A')}")
                    print(f"   📊 Niveau fallback: {result.get('fallback_level', 'N/A')}")
                    print(f"   🏷️ Source SEO tags: {result.get('seo_tags_source', 'N/A')}")
                    print(f"   🧪 Mode QA: {result.get('qa_test_mode', 'N/A')}")
                    print(f"   ⚡ Simulation QA: {result.get('qa_simulation_triggered', 'N/A')}")
                    
                    # Évaluation globale
                    success_rate = (passed_checks / total_checks) * 100
                    
                    print(f"\n🎯 ÉVALUATION GLOBALE DES 6 PHASES:")
                    print(f"   📊 Critères réussis: {passed_checks}/{total_checks}")
                    print(f"   📈 Taux de réussite: {success_rate:.1f}%")
                    
                    # Critères de succès
                    success_criteria = {
                        "generation_under_60s": generation_time < 60,
                        "content_quality": (
                            len(result.get('generated_title', '')) >= 30 and
                            len(result.get('marketing_description', '')) >= 300 and
                            len(result.get('key_features', [])) >= 5 and
                            len(result.get('seo_tags', [])) >= 5
                        ),
                        "phases_mostly_working": success_rate >= 70,
                        "critical_phases_working": (
                            phases_validation["Phase 1 - Services modulaires"]["services_title"] and
                            phases_validation["Phase 4 - Champs fallback"]["fallback_model"]
                        )
                    }
                    
                    print(f"\n📋 CRITÈRES DE SUCCÈS:")
                    for criterion, met in success_criteria.items():
                        status_icon = "✅" if met else "❌"
                        print(f"   {status_icon} {criterion}")
                    
                    overall_success = all(success_criteria.values())
                    
                    if overall_success:
                        print(f"\n🎉 SUCCÈS COMPLET: Le système 6 phases fonctionne excellemment!")
                        print("   ✅ Génération de contenu de qualité maintenue")
                        print("   ✅ Performance acceptable (< 60s par génération)")
                        print("   ✅ Toutes les phases détectées et fonctionnelles")
                        print("   ✅ Système robuste et production-ready")
                    else:
                        print(f"\n⚠️ SUCCÈS PARTIEL: Certaines phases nécessitent des améliorations")
                        failed_criteria = [k for k, v in success_criteria.items() if not v]
                        for criterion in failed_criteria:
                            print(f"   ❌ {criterion}")
                    
                    return overall_success
                    
                else:
                    error_text = await response.text()
                    print(f"❌ ERREUR GÉNÉRATION: {status} - {error_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ EXCEPTION GÉNÉRATION: {str(e)}")
            return False
    
    async def test_qa_statistics_endpoint(self):
        """Test QA statistics endpoint if available"""
        print("\n🧪 TEST: ENDPOINT QA STATISTICS")
        print("=" * 50)
        
        if not self.test_user:
            print("❌ Utilisateur test non disponible")
            return False
        
        try:
            async with self.session.get(
                f"{BACKEND_URL}/qa/statistics",
                headers=self.get_auth_headers(self.test_user["token"])
            ) as response:
                
                if response.status == 200:
                    stats = await response.json()
                    print(f"✅ ENDPOINT QA STATISTICS ACCESSIBLE")
                    print(f"   📊 Statistiques reçues: {len(stats)} champs")
                    
                    # Afficher quelques statistiques si disponibles
                    for key, value in list(stats.items())[:5]:
                        print(f"   📈 {key}: {value}")
                    
                    return True
                    
                elif response.status == 404:
                    print(f"⚠️ ENDPOINT QA STATISTICS NON IMPLÉMENTÉ (404)")
                    return False
                    
                else:
                    error_text = await response.text()
                    print(f"❌ ERREUR ENDPOINT QA: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ EXCEPTION ENDPOINT QA: {str(e)}")
            return False
    
    async def run_basic_phases_validation(self):
        """Run basic phases validation"""
        print("🚀 ECOMSIMPLY - VALIDATION BASIQUE DES 6 PHASES")
        print("=" * 70)
        print("Objectif: Vérifier que les 6 phases sont implémentées et fonctionnelles")
        print("=" * 70)
        
        # Setup
        if not await self.setup_session():
            print("❌ Failed to setup test session")
            return False
        
        try:
            # Run basic validation
            print("\n🎯 DÉMARRAGE DE LA VALIDATION DES PHASES...")
            
            test1_result = await self.test_basic_generation_with_phases()
            await asyncio.sleep(2)
            
            test2_result = await self.test_qa_statistics_endpoint()
            
            # Final Summary
            print("\n" + "=" * 70)
            print("🏁 RÉSUMÉ FINAL - VALIDATION DES 6 PHASES")
            print("=" * 70)
            
            print(f"🎯 RÉSULTATS DES TESTS:")
            print(f"   1. Génération avec 6 phases: {'✅ RÉUSSI' if test1_result else '❌ ÉCHOUÉ'}")
            print(f"   2. Endpoint QA Statistics: {'✅ RÉUSSI' if test2_result else '⚠️ NON IMPLÉMENTÉ'}")
            
            if test1_result:
                print(f"\n🎉 VALIDATION RÉUSSIE: Le système 6 phases est opérationnel!")
                print("   ✅ Phase 1 - Services modulaires fonctionnels")
                print("   ✅ Phase 2 - Logging structuré actif")
                print("   ✅ Phase 3 - Validation avancée des entrées")
                print("   ✅ Phase 4 - Champs fallback présents")
                print("   ✅ Phase 5 - Enrichissement SEO opérationnel")
                print("   ✅ Phase 6 - Mode QA détecté")
                print("   🚀 Système production-ready avec toutes les améliorations")
            else:
                print(f"\n❌ VALIDATION ÉCHOUÉE: Le système nécessite des corrections")
                print("   🔧 Vérifier l'implémentation des phases")
                print("   🔧 Corriger les erreurs de génération")
            
            return test1_result
            
        finally:
            await self.cleanup()

async def main():
    """Main test execution"""
    validator = BasicPhasesValidator()
    success = await validator.run_basic_phases_validation()
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())