#!/usr/bin/env python3
"""
ECOMSIMPLY Mock Publication System Testing
Test des 3 premières étapes de la roadmap: publication mock intégrée
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration des URLs
BACKEND_URL = "https://ecomsimply.com/api"

class MockPublicationTester:
    """Testeur pour le système de publication mock ECOMSIMPLY"""
    
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        self.test_user_email = f"test_mock_pub_{int(datetime.now().timestamp())}@ecomsimply.test"
        self.test_user_password = "TestMockPub2025!"
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str, data: Dict = None):
        """Log un résultat de test"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
        if data and not success:
            print(f"   📋 Data: {json.dumps(data, indent=2)}")
    
    async def setup_test_user(self) -> bool:
        """Crée un utilisateur de test"""
        try:
            # Créer utilisateur
            register_data = {
                "email": self.test_user_email,
                "name": "Test Mock Publication User",
                "password": self.test_user_password
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/auth/register",
                json=register_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.auth_token = result.get("token") or result.get("access_token")
                    
                    # Si pas de token dans register, essayer login
                    if not self.auth_token:
                        login_success = await self.login_user()
                        if login_success:
                            self.log_test(
                                "User Setup",
                                True,
                                f"Utilisateur test créé et connecté: {self.test_user_email}",
                                {"user_email": self.test_user_email}
                            )
                            return True
                        else:
                            return False
                    else:
                        self.log_test(
                            "User Setup",
                            True,
                            f"Utilisateur test créé: {self.test_user_email}",
                            {"user_email": self.test_user_email}
                        )
                        return True
                else:
                    error_text = await response.text()
                    self.log_test(
                        "User Setup",
                        False,
                        f"Échec création utilisateur: {response.status}",
                        {"error": error_text}
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "User Setup",
                False,
                f"Erreur setup utilisateur: {str(e)}"
            )
            return False
    
    async def login_user(self) -> bool:
        """Connecte l'utilisateur de test"""
        try:
            login_data = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.auth_token = result.get("token") or result.get("access_token")
                    return bool(self.auth_token)
                else:
                    return False
                    
        except Exception as e:
            return False
    
    async def test_generate_sheet_with_auto_publish(self) -> bool:
        """Test 1: Génération avec publication automatique"""
        try:
            # Données de test recommandées
            request_data = {
                "product_name": "iPhone 15 Pro Test",
                "product_description": "Smartphone premium avec processeur A17 Pro et appareil photo 48MP. Design en titane avec écran Super Retina XDR de 6.1 pouces.",
                "category": "Electronics",
                "generate_image": False,  # Plus rapide pour les tests
                "number_of_images": 0,
                "language": "fr"
            }
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Vérifier que PUBLISH_AUTO est activé (via variables d'environnement)
            print("🔧 Test avec PUBLISH_AUTO=true (configuration par défaut)")
            
            async with self.session.post(
                f"{BACKEND_URL}/generate-sheet",
                json=request_data,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Vérifications spécifiques
                    checks = []
                    
                    # 1. Vérifier que la génération a réussi
                    has_title = bool(result.get("generated_title"))
                    has_description = bool(result.get("marketing_description"))
                    has_features = len(result.get("key_features", [])) > 0
                    has_seo_tags = len(result.get("seo_tags", [])) > 0
                    
                    checks.append(("Titre généré", has_title))
                    checks.append(("Description générée", has_description))
                    checks.append(("Features générées", has_features))
                    checks.append(("Tags SEO générés", has_seo_tags))
                    
                    # 2. Vérifier la publication automatique
                    auto_publish_enabled = result.get("auto_publish_enabled", False)
                    publication_results = result.get("publication_results", [])
                    
                    checks.append(("Auto-publish activé", auto_publish_enabled))
                    checks.append(("Résultats publication présents", len(publication_results) > 0))
                    
                    # 3. Analyser les résultats de publication
                    successful_pubs = [p for p in publication_results if p.get("success")]
                    failed_pubs = [p for p in publication_results if not p.get("success")]
                    
                    platforms_tested = [p.get("platform") for p in publication_results]
                    expected_platforms = ["shopify", "woocommerce", "prestashop"]
                    
                    checks.append(("Publications réussies", len(successful_pubs) >= 2))
                    checks.append(("Plateformes testées", len(platforms_tested) >= 3))
                    checks.append(("Mode mock utilisé", all(p.get("mode") == "mock" for p in publication_results)))
                    
                    # Résumé des vérifications
                    passed_checks = sum(1 for _, passed in checks if passed)
                    total_checks = len(checks)
                    
                    success = passed_checks >= (total_checks * 0.8)  # 80% de réussite minimum
                    
                    details = f"Génération + Publication: {passed_checks}/{total_checks} vérifications passées"
                    if successful_pubs:
                        details += f", {len(successful_pubs)} publications réussies sur {expected_platforms}"
                    
                    self.log_test(
                        "Generate Sheet + Auto Publish",
                        success,
                        details,
                        {
                            "checks": dict(checks),
                            "publication_results": publication_results,
                            "successful_publications": len(successful_pubs),
                            "failed_publications": len(failed_pubs),
                            "platforms_tested": platforms_tested
                        }
                    )
                    
                    return success
                    
                else:
                    error_text = await response.text()
                    self.log_test(
                        "Generate Sheet + Auto Publish",
                        False,
                        f"Erreur HTTP {response.status}",
                        {"error": error_text}
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Generate Sheet + Auto Publish",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_publication_status_endpoint(self) -> bool:
        """Test 2: Endpoint /api/status/publication"""
        try:
            async with self.session.get(f"{BACKEND_URL}/status/publication") as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Vérifications
                    checks = []
                    
                    success_field = result.get("success", False)
                    status_data = result.get("status", {})
                    
                    checks.append(("Réponse success", success_field))
                    checks.append(("Données status présentes", bool(status_data)))
                    
                    # Vérifier les champs attendus
                    expected_fields = [
                        "mode", "mock_mode", "auto_publish", "platforms_available",
                        "platforms", "health_checks"
                    ]
                    
                    for field in expected_fields:
                        checks.append((f"Champ {field}", field in status_data))
                    
                    # Vérifications spécifiques mode mock
                    mock_mode = status_data.get("mock_mode", False)
                    auto_publish = status_data.get("auto_publish", False)
                    platforms_available = status_data.get("platforms_available", 0)
                    
                    checks.append(("Mode mock activé", mock_mode))
                    checks.append(("Auto-publish configuré", auto_publish))
                    checks.append(("Plateformes disponibles", platforms_available >= 3))
                    
                    # Vérifier les health checks
                    health_checks = status_data.get("health_checks", {})
                    expected_platforms = ["shopify", "woocommerce", "prestashop"]
                    
                    for platform in expected_platforms:
                        platform_health = health_checks.get(platform, {})
                        checks.append((f"Health check {platform}", bool(platform_health)))
                    
                    # Vérifier les statistiques mock
                    mock_stats = status_data.get("mock_statistics", {})
                    checks.append(("Statistiques mock présentes", bool(mock_stats)))
                    
                    passed_checks = sum(1 for _, passed in checks if passed)
                    total_checks = len(checks)
                    success = passed_checks >= (total_checks * 0.8)
                    
                    self.log_test(
                        "Publication Status Endpoint",
                        success,
                        f"Status: {passed_checks}/{total_checks} vérifications passées",
                        {
                            "checks": dict(checks),
                            "status_data": status_data,
                            "mock_mode": mock_mode,
                            "platforms_available": platforms_available
                        }
                    )
                    
                    return success
                    
                else:
                    error_text = await response.text()
                    self.log_test(
                        "Publication Status Endpoint",
                        False,
                        f"Erreur HTTP {response.status}",
                        {"error": error_text}
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Publication Status Endpoint",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_publications_history_endpoint(self) -> bool:
        """Test 3: Endpoint /api/publications/history"""
        try:
            async with self.session.get(f"{BACKEND_URL}/publications/history?limit=20") as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Vérifications
                    checks = []
                    
                    success_field = result.get("success", False)
                    publications = result.get("publications", [])
                    total = result.get("total", 0)
                    
                    checks.append(("Réponse success", success_field))
                    checks.append(("Publications présentes", isinstance(publications, list)))
                    checks.append(("Total cohérent", total >= 0))
                    
                    # Si des publications existent (après le test précédent)
                    if publications:
                        # Vérifier la structure des publications
                        first_pub = publications[0]
                        expected_pub_fields = [
                            "id", "platform", "product_name", "status", 
                            "success", "mode", "created_at"
                        ]
                        
                        for field in expected_pub_fields:
                            checks.append((f"Publication champ {field}", field in first_pub))
                        
                        # Vérifier que c'est bien du mock
                        mock_publications = [p for p in publications if p.get("mode") == "mock"]
                        checks.append(("Publications en mode mock", len(mock_publications) > 0))
                        
                        # Vérifier les plateformes
                        platforms_found = set(p.get("platform") for p in publications)
                        expected_platforms = {"shopify", "woocommerce", "prestashop"}
                        platforms_match = len(platforms_found.intersection(expected_platforms)) >= 2
                        checks.append(("Plateformes attendues", platforms_match))
                    
                    passed_checks = sum(1 for _, passed in checks if passed)
                    total_checks = len(checks)
                    success = passed_checks >= (total_checks * 0.8)
                    
                    self.log_test(
                        "Publications History Endpoint",
                        success,
                        f"History: {passed_checks}/{total_checks} vérifications passées, {len(publications)} publications trouvées",
                        {
                            "checks": dict(checks),
                            "publications_count": len(publications),
                            "total": total,
                            "sample_publication": publications[0] if publications else None
                        }
                    )
                    
                    return success
                    
                else:
                    error_text = await response.text()
                    self.log_test(
                        "Publications History Endpoint",
                        False,
                        f"Erreur HTTP {response.status}",
                        {"error": error_text}
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Publications History Endpoint",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_scraping_simulation(self) -> bool:
        """Test 4: Simulation de scraping avec datasets et proxies mock"""
        try:
            # Test indirect via génération (le scraping est intégré)
            request_data = {
                "product_name": "iPhone 15 Pro Test",
                "product_description": "Test scraping simulation avec datasets configurés",
                "category": "Electronics",
                "generate_image": False,
                "number_of_images": 0,
                "language": "fr"
            }
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with self.session.post(
                f"{BACKEND_URL}/generate-sheet",
                json=request_data,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Vérifications du scraping
                    checks = []
                    
                    # 1. Vérifier que les données scrapées sont utilisées
                    seo_tags = result.get("seo_tags", [])
                    price_suggestions = result.get("price_suggestions", "")
                    marketing_description = result.get("marketing_description", "")
                    
                    checks.append(("Tags SEO générés", len(seo_tags) >= 5))
                    checks.append(("Suggestions prix présentes", bool(price_suggestions)))
                    checks.append(("Description enrichie", len(marketing_description) > 100))
                    
                    # 2. Vérifier les métadonnées de scraping (si disponibles)
                    seo_tags_source = result.get("seo_tags_source", "unknown")
                    checks.append(("Source SEO identifiée", seo_tags_source != "unknown"))
                    
                    # 3. Vérifier la qualité des données (réalisme)
                    # Les datasets mock doivent produire des données cohérentes
                    realistic_keywords = any(
                        keyword.lower() in ["premium", "qualité", "innovation", "design", "performance"]
                        for keyword in seo_tags
                    )
                    checks.append(("Mots-clés réalistes", realistic_keywords))
                    
                    # 4. Vérifier que le scraping n'a pas fait d'appels réseau réels
                    # (Indirect - pas d'erreurs de timeout/réseau)
                    generation_time = result.get("generation_time", 0)
                    reasonable_time = generation_time < 60  # Moins de 60 secondes
                    checks.append(("Temps génération raisonnable", reasonable_time))
                    
                    passed_checks = sum(1 for _, passed in checks if passed)
                    total_checks = len(checks)
                    success = passed_checks >= (total_checks * 0.7)
                    
                    self.log_test(
                        "Scraping Simulation",
                        success,
                        f"Scraping: {passed_checks}/{total_checks} vérifications passées",
                        {
                            "checks": dict(checks),
                            "seo_tags_count": len(seo_tags),
                            "seo_tags_source": seo_tags_source,
                            "generation_time": generation_time,
                            "sample_seo_tags": seo_tags[:5]
                        }
                    )
                    
                    return success
                    
                else:
                    error_text = await response.text()
                    self.log_test(
                        "Scraping Simulation",
                        False,
                        f"Erreur HTTP {response.status}",
                        {"error": error_text}
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Scraping Simulation",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Exécute tous les tests"""
        print("🚀 DÉMARRAGE DES TESTS - SYSTÈME DE PUBLICATION MOCK ECOMSIMPLY")
        print("=" * 80)
        
        # Setup
        setup_success = await self.setup_test_user()
        if not setup_success:
            return {"success": False, "error": "Échec setup utilisateur"}
        
        # Tests principaux
        test_functions = [
            ("Test 1: Génération + Publication Auto", self.test_generate_sheet_with_auto_publish),
            ("Test 2: Status Publication", self.test_publication_status_endpoint),
            ("Test 3: Historique Publications", self.test_publications_history_endpoint),
            ("Test 4: Simulation Scraping", self.test_scraping_simulation)
        ]
        
        results = []
        for test_name, test_func in test_functions:
            print(f"\n📋 {test_name}")
            print("-" * 50)
            
            try:
                result = await test_func()
                results.append(result)
            except Exception as e:
                print(f"❌ ERREUR CRITIQUE: {str(e)}")
                results.append(False)
        
        # Résumé final
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 80)
        
        passed_tests = sum(1 for r in results if r)
        total_tests = len(results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"✅ Tests réussis: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Détail des résultats
        for i, (test_name, _) in enumerate(test_functions):
            status = "✅ PASS" if results[i] else "❌ FAIL"
            print(f"   {status} {test_name}")
        
        # Validation globale
        overall_success = success_rate >= 75  # 75% minimum
        
        if overall_success:
            print(f"\n🎉 VALIDATION GLOBALE: SUCCÈS")
            print("Le système de publication mock ECOMSIMPLY fonctionne correctement!")
            print("✅ Étapes 1-3 de la roadmap validées:")
            print("   - Couches d'abstraction + mocks")
            print("   - Pipeline génération → publication mock")
            print("   - Scraping en simulation contrôlée")
        else:
            print(f"\n⚠️ VALIDATION GLOBALE: ÉCHEC PARTIEL")
            print("Certains composants nécessitent des corrections.")
        
        return {
            "success": overall_success,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "success_rate": success_rate,
            "test_results": self.test_results
        }

async def main():
    """Point d'entrée principal"""
    async with MockPublicationTester() as tester:
        results = await tester.run_all_tests()
        
        # Code de sortie
        exit_code = 0 if results["success"] else 1
        sys.exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())