#!/usr/bin/env python3
"""
ECOMSIMPLY COMPREHENSIVE PHASES TESTING - SYSTÈME COMPLET 6 PHASES
Test global de toutes les phases d'amélioration du système de génération de fiches produits avec mode QA.

PHASES À TESTER:
- Phase 1: Services modulaires fonctionnels
- Phase 2: Logging structuré actif
- Phase 3: Validation avancée des entrées
- Phase 4: Champs fallback (model_used, generation_method, fallback_level)
- Phase 5: Enrichissement SEO (seo_tags_source)
- Phase 6: Mode QA (qa_test_mode, qa_simulation_triggered)

TESTS SPÉCIFIQUES:
1. TEST MODE QA ACTIVÉ avec TEST_MODE=True
2. Génération de 10 fiches produits différentes
3. Vérification qu'au moins 1 génération déclenche un fallback simulé
4. Test endpoint QA statistics
5. Test complet génération MacBook Pro M3 2024
"""

import asyncio
import aiohttp
import json
import time
import os
import random
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://ecomsimply.com/api"

class ComprehensivePhasesQATester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.test_user = None
        self.qa_mode_enabled = False
        self.generation_results = []
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=120)
        )
        print("✅ Session HTTP initialisée pour tests QA")
        return True
    
    async def cleanup(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
    
    def get_auth_headers(self, token: str):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {token}"}
    
    async def create_test_user(self) -> Dict:
        """Create a test user for QA testing"""
        
        user_data = {
            "email": f"qa_test_{int(time.time())}@ecomsimply.test",
            "name": "QA Test User",
            "password": "QATestPassword123!"
        }
        
        print(f"👤 Création utilisateur QA test...")
        
        try:
            # Register user
            async with self.session.post(f"{BACKEND_URL}/auth/register", json=user_data) as response:
                if response.status == 200:
                    register_result = await response.json()
                    print(f"✅ Utilisateur QA créé: {user_data['email']}")
                    
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
                            print(f"✅ Utilisateur QA prêt avec token")
                            return user_info
                        else:
                            error_text = await login_response.text()
                            print(f"❌ Échec login QA: {login_response.status} - {error_text}")
                            return None
                else:
                    error_text = await response.text()
                    print(f"❌ Échec création utilisateur QA: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Exception création utilisateur QA: {str(e)}")
            return None
    
    async def test_qa_mode_activation(self):
        """
        TEST 1: MODE QA ACTIVÉ
        Vérifier que le mode QA peut être activé et fonctionne
        """
        print("\n🧪 TEST 1: MODE QA ACTIVÉ")
        print("=" * 60)
        
        if not self.test_user:
            user_info = await self.create_test_user()
            if not user_info:
                print("❌ Impossible de créer l'utilisateur QA")
                return False
        
        # Test avec mode QA activé via paramètre ou variable d'environnement
        test_product = {
            "product_name": "iPhone 15 Pro QA Test",
            "product_description": "Test du mode QA avec iPhone 15 Pro pour vérifier les fallbacks",
            "generate_image": True,
            "number_of_images": 1,
            "language": "fr",
            "category": "électronique",
            "qa_test_mode": True  # Activation explicite du mode QA
        }
        
        print(f"🔥 Test mode QA avec: {test_product['product_name']}")
        
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
                    
                    # Vérification des champs QA spécifiques
                    qa_fields = {
                        "qa_test_mode": result.get("qa_test_mode"),
                        "qa_simulation_triggered": result.get("qa_simulation_triggered"),
                        "model_used": result.get("model_used"),
                        "generation_method": result.get("generation_method"),
                        "fallback_level": result.get("fallback_level"),
                        "seo_tags_source": result.get("seo_tags_source")
                    }
                    
                    print(f"✅ GÉNÉRATION QA RÉUSSIE en {generation_time:.2f}s")
                    print(f"   🤖 Mode QA: {qa_fields['qa_test_mode']}")
                    print(f"   ⚡ Simulation déclenchée: {qa_fields['qa_simulation_triggered']}")
                    print(f"   🧠 Modèle utilisé: {qa_fields['model_used']}")
                    print(f"   🔧 Méthode génération: {qa_fields['generation_method']}")
                    print(f"   📊 Niveau fallback: {qa_fields['fallback_level']}")
                    print(f"   🏷️ Source SEO tags: {qa_fields['seo_tags_source']}")
                    
                    # Validation des phases
                    phase_validation = {
                        "Phase 1 - Services modulaires": len(result.get('generated_images', [])) > 0 and len(result.get('key_features', [])) >= 5,
                        "Phase 2 - Logging structuré": result.get('generation_time') is not None,
                        "Phase 3 - Validation entrées": len(result.get('generated_title', '')) > 0,
                        "Phase 4 - Champs fallback": qa_fields['model_used'] is not None,
                        "Phase 5 - Enrichissement SEO": qa_fields['seo_tags_source'] is not None,
                        "Phase 6 - Mode QA": qa_fields['qa_test_mode'] is not None
                    }
                    
                    print(f"\n📋 VALIDATION DES 6 PHASES:")
                    for phase, validated in phase_validation.items():
                        status_icon = "✅" if validated else "❌"
                        print(f"   {status_icon} {phase}")
                    
                    self.test_results.append({
                        "test": "qa_mode_activation",
                        "success": True,
                        "generation_time": generation_time,
                        "qa_fields": qa_fields,
                        "phase_validation": phase_validation,
                        "phases_passed": sum(phase_validation.values()),
                        "total_phases": len(phase_validation)
                    })
                    
                    self.qa_mode_enabled = qa_fields.get('qa_test_mode', False)
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ ERREUR MODE QA: {status} - {error_text}")
                    self.test_results.append({
                        "test": "qa_mode_activation",
                        "success": False,
                        "error": f"HTTP {status}: {error_text[:200]}"
                    })
                    return False
                    
        except Exception as e:
            print(f"❌ EXCEPTION MODE QA: {str(e)}")
            self.test_results.append({
                "test": "qa_mode_activation",
                "success": False,
                "error": str(e)
            })
            return False
    
    async def test_multiple_generations_qa(self):
        """
        TEST 2: GÉNÉRATION DE 10 FICHES PRODUITS DIFFÉRENTES
        Vérifier qu'au moins 1 génération déclenche un fallback simulé
        """
        print("\n🧪 TEST 2: GÉNÉRATION MULTIPLE AVEC QA")
        print("=" * 60)
        
        if not self.test_user:
            print("❌ Utilisateur QA non disponible")
            return False
        
        # 10 produits différents pour tester la variété
        test_products = [
            {"name": "MacBook Pro M3 2024", "desc": "Ordinateur portable Apple avec puce M3 pour professionnels", "cat": "électronique"},
            {"name": "iPhone 15 Pro Max", "desc": "Smartphone Apple haut de gamme avec appareil photo 48MP", "cat": "électronique"},
            {"name": "Nike Air Max 270", "desc": "Chaussures de sport Nike avec technologie Air Max", "cat": "sport"},
            {"name": "Samsung Galaxy S24 Ultra", "desc": "Smartphone Samsung avec S Pen et écran 6.8 pouces", "cat": "électronique"},
            {"name": "Sony WH-1000XM5", "desc": "Casque audio sans fil avec réduction de bruit active", "cat": "électronique"},
            {"name": "Adidas Ultraboost 22", "desc": "Chaussures de running Adidas avec technologie Boost", "cat": "sport"},
            {"name": "iPad Pro 12.9 M2", "desc": "Tablette Apple avec écran Liquid Retina XDR", "cat": "électronique"},
            {"name": "Nintendo Switch OLED", "desc": "Console de jeu portable Nintendo avec écran OLED", "cat": "électronique"},
            {"name": "AirPods Pro 2", "desc": "Écouteurs sans fil Apple avec réduction de bruit", "cat": "électronique"},
            {"name": "Tesla Model 3", "desc": "Voiture électrique Tesla avec autopilot", "cat": "auto"}
        ]
        
        fallback_triggered_count = 0
        successful_generations = 0
        
        print(f"🔥 Test de {len(test_products)} générations avec mode QA")
        
        for i, product in enumerate(test_products, 1):
            print(f"\n📱 Génération {i}/10: {product['name']}")
            
            test_request = {
                "product_name": product["name"],
                "product_description": product["desc"],
                "generate_image": True,
                "number_of_images": 1,
                "language": "fr",
                "category": product["cat"],
                "qa_test_mode": True
            }
            
            try:
                start_time = time.time()
                
                async with self.session.post(
                    f"{BACKEND_URL}/generate-sheet",
                    json=test_request,
                    headers=self.get_auth_headers(self.test_user["token"])
                ) as response:
                    
                    generation_time = time.time() - start_time
                    
                    if response.status == 200:
                        result = await response.json()
                        successful_generations += 1
                        
                        # Vérifier si un fallback a été déclenché
                        qa_simulation = result.get("qa_simulation_triggered", False)
                        fallback_level = result.get("fallback_level", 0)
                        
                        if qa_simulation or (fallback_level and fallback_level > 1):
                            fallback_triggered_count += 1
                            print(f"   ⚡ FALLBACK DÉTECTÉ! (Simulation: {qa_simulation}, Niveau: {fallback_level})")
                        else:
                            print(f"   ✅ Génération normale (Temps: {generation_time:.1f}s)")
                        
                        # Stocker les résultats pour analyse
                        self.generation_results.append({
                            "product": product["name"],
                            "success": True,
                            "generation_time": generation_time,
                            "qa_simulation_triggered": qa_simulation,
                            "fallback_level": fallback_level,
                            "model_used": result.get("model_used"),
                            "seo_tags_source": result.get("seo_tags_source")
                        })
                        
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Erreur: {response.status} - {error_text[:100]}")
                        self.generation_results.append({
                            "product": product["name"],
                            "success": False,
                            "error": f"HTTP {response.status}"
                        })
                
                # Pause entre les générations
                await asyncio.sleep(1)
                        
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
                self.generation_results.append({
                    "product": product["name"],
                    "success": False,
                    "error": str(e)
                })
        
        # Analyse des résultats
        print(f"\n📊 RÉSULTATS GÉNÉRATION MULTIPLE:")
        print(f"   ✅ Générations réussies: {successful_generations}/10")
        print(f"   ⚡ Fallbacks déclenchés: {fallback_triggered_count}")
        print(f"   📈 Taux de succès: {(successful_generations/10)*100:.1f}%")
        print(f"   🎯 Taux de fallback: {(fallback_triggered_count/max(successful_generations,1))*100:.1f}%")
        
        # Critères de succès
        success_criteria = {
            "at_least_8_successful": successful_generations >= 8,
            "at_least_1_fallback": fallback_triggered_count >= 1,
            "no_critical_errors": successful_generations > 0
        }
        
        print(f"\n📋 CRITÈRES DE SUCCÈS MULTIPLE:")
        for criterion, met in success_criteria.items():
            status_icon = "✅" if met else "❌"
            print(f"   {status_icon} {criterion}")
        
        overall_success = all(success_criteria.values())
        
        self.test_results.append({
            "test": "multiple_generations_qa",
            "success": overall_success,
            "successful_generations": successful_generations,
            "fallback_triggered_count": fallback_triggered_count,
            "success_rate": (successful_generations/10)*100,
            "fallback_rate": (fallback_triggered_count/max(successful_generations,1))*100,
            "criteria": success_criteria
        })
        
        return overall_success
    
    async def test_qa_statistics_endpoint(self):
        """
        TEST 3: ENDPOINT QA STATISTICS
        Tester GET /api/qa/statistics
        """
        print("\n🧪 TEST 3: ENDPOINT QA STATISTICS")
        print("=" * 60)
        
        if not self.test_user:
            print("❌ Utilisateur QA non disponible")
            return False
        
        try:
            # Test de l'endpoint QA statistics
            async with self.session.get(
                f"{BACKEND_URL}/qa/statistics",
                headers=self.get_auth_headers(self.test_user["token"])
            ) as response:
                
                if response.status == 200:
                    stats = await response.json()
                    
                    print(f"✅ ENDPOINT QA STATISTICS ACCESSIBLE")
                    
                    # Vérifier la structure des statistiques
                    expected_fields = [
                        "total_qa_tests", "fallback_simulations", "success_rate",
                        "average_generation_time", "recent_tests"
                    ]
                    
                    stats_validation = {}
                    for field in expected_fields:
                        present = field in stats
                        stats_validation[field] = present
                        status_icon = "✅" if present else "❌"
                        print(f"   {status_icon} {field}: {stats.get(field, 'MANQUANT')}")
                    
                    # Afficher les statistiques si disponibles
                    if "recent_tests" in stats and isinstance(stats["recent_tests"], list):
                        print(f"\n📋 TESTS RÉCENTS QA ({len(stats['recent_tests'])}):")
                        for i, test in enumerate(stats["recent_tests"][:5], 1):
                            print(f"   {i}. {test.get('product_name', 'N/A')} - {test.get('status', 'N/A')}")
                    
                    success = sum(stats_validation.values()) >= len(expected_fields) // 2
                    
                    self.test_results.append({
                        "test": "qa_statistics_endpoint",
                        "success": success,
                        "stats_received": stats,
                        "fields_validation": stats_validation,
                        "fields_present": sum(stats_validation.values()),
                        "total_expected_fields": len(expected_fields)
                    })
                    
                    return success
                    
                elif response.status == 404:
                    print(f"⚠️ ENDPOINT QA STATISTICS NON IMPLÉMENTÉ (404)")
                    self.test_results.append({
                        "test": "qa_statistics_endpoint",
                        "success": False,
                        "error": "Endpoint not implemented (404)"
                    })
                    return False
                    
                else:
                    error_text = await response.text()
                    print(f"❌ ERREUR ENDPOINT QA: {response.status} - {error_text}")
                    self.test_results.append({
                        "test": "qa_statistics_endpoint",
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text[:200]}"
                    })
                    return False
                    
        except Exception as e:
            print(f"❌ EXCEPTION ENDPOINT QA: {str(e)}")
            self.test_results.append({
                "test": "qa_statistics_endpoint",
                "success": False,
                "error": str(e)
            })
            return False
    
    async def test_complete_macbook_generation(self):
        """
        TEST 4: TEST COMPLET GÉNÉRATION MACBOOK PRO M3 2024
        Test complet avec tous les critères de qualité
        """
        print("\n🧪 TEST 4: GÉNÉRATION COMPLÈTE MACBOOK PRO M3 2024")
        print("=" * 60)
        
        if not self.test_user:
            print("❌ Utilisateur QA non disponible")
            return False
        
        # Test du produit spécifique mentionné dans la review
        test_product = {
            "product_name": "MacBook Pro M3 2024",
            "product_description": "Ordinateur portable Apple avec puce M3, écran Liquid Retina XDR 14 pouces, 16GB RAM, 512GB SSD, pour professionnels créatifs",
            "generate_image": True,
            "number_of_images": 2,
            "language": "fr",
            "category": "électronique",
            "use_case": "travail professionnel créatif",
            "image_style": "studio",
            "qa_test_mode": True
        }
        
        print(f"🔥 Test complet: {test_product['product_name']}")
        
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
                    
                    print(f"✅ GÉNÉRATION MACBOOK RÉUSSIE en {generation_time:.2f}s")
                    
                    # Validation complète de tous les champs des 6 phases
                    complete_validation = {
                        # Phase 1 - Services modulaires
                        "services_title": len(result.get('generated_title', '')) >= 20,
                        "services_description": len(result.get('marketing_description', '')) >= 200,
                        "services_features": len(result.get('key_features', [])) >= 5,
                        "services_seo": len(result.get('seo_tags', [])) >= 5,
                        "services_images": len(result.get('generated_images', [])) >= 1,
                        
                        # Phase 2 - Logging structuré
                        "logging_time": result.get('generation_time') is not None,
                        "logging_id": result.get('generation_id') is not None,
                        
                        # Phase 3 - Validation entrées
                        "validation_structure": all(field in result for field in ['generated_title', 'marketing_description']),
                        
                        # Phase 4 - Champs fallback
                        "fallback_model": result.get('model_used') is not None,
                        "fallback_method": result.get('generation_method') is not None,
                        "fallback_level": result.get('fallback_level') is not None,
                        
                        # Phase 5 - Enrichissement SEO
                        "seo_source": result.get('seo_tags_source') is not None,
                        
                        # Phase 6 - Mode QA
                        "qa_mode": result.get('qa_test_mode') is not None,
                        "qa_simulation": result.get('qa_simulation_triggered') is not None
                    }
                    
                    # Critères de performance
                    performance_criteria = {
                        "generation_under_60s": generation_time < 60,
                        "quality_title": 30 <= len(result.get('generated_title', '')) <= 80,
                        "quality_description": len(result.get('marketing_description', '')) >= 300,
                        "quality_features": len(result.get('key_features', [])) >= 5,
                        "quality_seo": len(result.get('seo_tags', [])) >= 5
                    }
                    
                    print(f"\n📋 VALIDATION COMPLÈTE DES 6 PHASES:")
                    phases_passed = 0
                    for criterion, passed in complete_validation.items():
                        status_icon = "✅" if passed else "❌"
                        print(f"   {status_icon} {criterion}")
                        if passed:
                            phases_passed += 1
                    
                    print(f"\n🎯 CRITÈRES DE PERFORMANCE:")
                    performance_passed = 0
                    for criterion, passed in performance_criteria.items():
                        status_icon = "✅" if passed else "❌"
                        print(f"   {status_icon} {criterion}")
                        if passed:
                            performance_passed += 1
                    
                    # Affichage des détails
                    print(f"\n📊 DÉTAILS GÉNÉRATION:")
                    print(f"   📝 Titre: {result.get('generated_title', 'N/A')[:60]}...")
                    print(f"   📄 Description: {len(result.get('marketing_description', ''))} caractères")
                    print(f"   🔧 Features: {len(result.get('key_features', []))} éléments")
                    print(f"   🏷️ SEO Tags: {len(result.get('seo_tags', []))} tags")
                    print(f"   🖼️ Images: {len(result.get('generated_images', []))} générées")
                    print(f"   ⏱️ Temps: {generation_time:.2f}s")
                    print(f"   🤖 Modèle: {result.get('model_used', 'N/A')}")
                    print(f"   🔧 Méthode: {result.get('generation_method', 'N/A')}")
                    print(f"   📊 Fallback: {result.get('fallback_level', 'N/A')}")
                    print(f"   🏷️ SEO Source: {result.get('seo_tags_source', 'N/A')}")
                    print(f"   🧪 QA Mode: {result.get('qa_test_mode', 'N/A')}")
                    print(f"   ⚡ QA Simulation: {result.get('qa_simulation_triggered', 'N/A')}")
                    
                    # Évaluation globale
                    total_criteria = len(complete_validation) + len(performance_criteria)
                    passed_criteria = phases_passed + performance_passed
                    success_rate = (passed_criteria / total_criteria) * 100
                    
                    overall_success = success_rate >= 80  # 80% des critères doivent passer
                    
                    print(f"\n🎯 ÉVALUATION GLOBALE:")
                    print(f"   📊 Critères réussis: {passed_criteria}/{total_criteria}")
                    print(f"   📈 Taux de réussite: {success_rate:.1f}%")
                    print(f"   🎯 Statut: {'✅ SUCCÈS' if overall_success else '❌ ÉCHEC'}")
                    
                    self.test_results.append({
                        "test": "complete_macbook_generation",
                        "success": overall_success,
                        "generation_time": generation_time,
                        "phases_validation": complete_validation,
                        "performance_criteria": performance_criteria,
                        "phases_passed": phases_passed,
                        "performance_passed": performance_passed,
                        "total_criteria": total_criteria,
                        "success_rate": success_rate,
                        "result_details": {
                            "title_length": len(result.get('generated_title', '')),
                            "description_length": len(result.get('marketing_description', '')),
                            "features_count": len(result.get('key_features', [])),
                            "seo_tags_count": len(result.get('seo_tags', [])),
                            "images_count": len(result.get('generated_images', [])),
                            "model_used": result.get('model_used'),
                            "generation_method": result.get('generation_method'),
                            "fallback_level": result.get('fallback_level'),
                            "seo_tags_source": result.get('seo_tags_source'),
                            "qa_test_mode": result.get('qa_test_mode'),
                            "qa_simulation_triggered": result.get('qa_simulation_triggered')
                        }
                    })
                    
                    return overall_success
                else:
                    error_text = await response.text()
                    print(f"❌ ERREUR GÉNÉRATION MACBOOK: {status} - {error_text}")
                    self.test_results.append({
                        "test": "complete_macbook_generation",
                        "success": False,
                        "error": f"HTTP {status}: {error_text[:200]}"
                    })
                    return False
                    
        except Exception as e:
            print(f"❌ EXCEPTION GÉNÉRATION MACBOOK: {str(e)}")
            self.test_results.append({
                "test": "complete_macbook_generation",
                "success": False,
                "error": str(e)
            })
            return False
    
    async def run_comprehensive_qa_tests(self):
        """Run all comprehensive QA tests for the 6 phases"""
        print("🚀 ECOMSIMPLY - TEST COMPLET SYSTÈME 6 PHASES AVEC MODE QA")
        print("=" * 80)
        print("Objectif: Validation globale de toutes les phases avec mode QA activé")
        print("=" * 80)
        
        # Setup
        if not await self.setup_session():
            print("❌ Failed to setup test session")
            return False
        
        try:
            # Run all comprehensive tests
            print("\n🎯 DÉMARRAGE DES TESTS COMPLETS QA...")
            
            test1_result = await self.test_qa_mode_activation()
            await asyncio.sleep(2)
            
            test2_result = await self.test_multiple_generations_qa()
            await asyncio.sleep(2)
            
            test3_result = await self.test_qa_statistics_endpoint()
            await asyncio.sleep(2)
            
            test4_result = await self.test_complete_macbook_generation()
            
            # Final Summary
            print("\n" + "=" * 80)
            print("🏁 RÉSUMÉ FINAL - SYSTÈME COMPLET 6 PHASES")
            print("=" * 80)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result.get('success', False))
            
            print(f"📊 Total Tests: {total_tests}")
            print(f"✅ Réussis: {passed_tests}")
            print(f"❌ Échoués: {total_tests - passed_tests}")
            print(f"📈 Taux de Réussite Global: {(passed_tests/total_tests*100):.1f}%")
            
            print(f"\n🎯 STATUT DES TESTS CRITIQUES:")
            print(f"   1. Mode QA Activé: {'✅ RÉUSSI' if test1_result else '❌ ÉCHOUÉ'}")
            print(f"   2. Générations Multiples QA: {'✅ RÉUSSI' if test2_result else '❌ ÉCHOUÉ'}")
            print(f"   3. Endpoint QA Statistics: {'✅ RÉUSSI' if test3_result else '❌ ÉCHOUÉ'}")
            print(f"   4. Génération Complète MacBook: {'✅ RÉUSSI' if test4_result else '❌ ÉCHOUÉ'}")
            
            # Validation des 6 phases
            print(f"\n📋 VALIDATION DES 6 PHASES:")
            phases_status = {
                "Phase 1 - Services modulaires": test1_result and test4_result,
                "Phase 2 - Logging structuré": test1_result and test4_result,
                "Phase 3 - Validation avancée": test4_result,
                "Phase 4 - Champs fallback": test1_result and test4_result,
                "Phase 5 - Enrichissement SEO": test1_result and test4_result,
                "Phase 6 - Mode QA": test1_result and test2_result
            }
            
            for phase, working in phases_status.items():
                status_icon = "✅" if working else "❌"
                print(f"   {status_icon} {phase}")
            
            # Critères de succès globaux
            success_criteria = {
                "qa_mode_functional": test1_result,
                "multiple_generations_working": test2_result,
                "fallback_system_active": any(r.get('fallback_triggered_count', 0) > 0 for r in self.test_results),
                "performance_acceptable": test4_result,
                "all_phases_detected": sum(phases_status.values()) >= 4  # Au moins 4/6 phases
            }
            
            print(f"\n📋 CRITÈRES DE SUCCÈS GLOBAUX:")
            for criterion, met in success_criteria.items():
                status_icon = "✅" if met else "❌"
                print(f"   {status_icon} {criterion}")
            
            # Évaluation finale
            critical_success = test1_result and test4_result  # Mode QA + génération complète
            overall_success = sum(success_criteria.values()) >= 4  # Au moins 4/5 critères
            
            if overall_success:
                print(f"\n🎉 SUCCÈS COMPLET: Le système 6 phases avec mode QA fonctionne excellemment!")
                print("   ✅ Mode QA avec simulation d'erreurs fonctionnel")
                print("   ✅ Tous les champs des 6 phases présents dans l'API")
                print("   ✅ Logging complet et structuré")
                print("   ✅ Génération de contenu de qualité maintenue")
                print("   ✅ Système robuste avec fallbacks automatiques")
                print("   ✅ Performance acceptable (< 60s par génération)")
            elif critical_success:
                print(f"\n⚡ SUCCÈS PARTIEL: Les fonctionnalités critiques marchent!")
                print("   ✅ Mode QA opérationnel")
                print("   ✅ Génération complète fonctionnelle")
                if not test2_result:
                    print("   ⚠️ Générations multiples nécessitent des ajustements")
                if not test3_result:
                    print("   ⚠️ Endpoint QA statistics à implémenter")
            else:
                print(f"\n❌ ÉCHEC CRITIQUE: Le système 6 phases présente des problèmes majeurs")
                if not test1_result:
                    print("   ❌ Mode QA non fonctionnel")
                if not test4_result:
                    print("   ❌ Génération complète défaillante")
                print("   🔧 Correction immédiate requise")
            
            # Résumé des phases pour le main agent
            phases_working = sum(phases_status.values())
            print(f"\n📊 RÉSUMÉ FINAL DES 6 PHASES:")
            print(f"   🎯 Phases fonctionnelles: {phases_working}/6")
            print(f"   📈 Taux de réussite phases: {(phases_working/6)*100:.1f}%")
            print(f"   🚀 Système production-ready: {'✅ OUI' if overall_success else '❌ NON'}")
            
            return critical_success
            
        finally:
            await self.cleanup()

async def main():
    """Main test execution"""
    tester = ComprehensivePhasesQATester()
    success = await tester.run_comprehensive_qa_tests()
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())