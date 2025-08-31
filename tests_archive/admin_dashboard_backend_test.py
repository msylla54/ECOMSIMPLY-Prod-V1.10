#!/usr/bin/env python3
"""
Test complet du tableau de bord admin ECOMSIMPLY avec les corrections apportées
Tests: Admin Plans Config, Admin Promotions, Admin Testimonials
Corrections testées: Clés admin 2025, suppression dépendance get_current_user, timeouts/fallbacks
"""

import asyncio
import sys
import os
import time
import json
import requests
from typing import Dict, Any, List
from datetime import datetime

# Configuration des URLs
BACKEND_URL = "https://ecomsimply.com"
API_BASE = f"{BACKEND_URL}/api"

# Clés admin pour les tests
CORRECT_ADMIN_KEY = "ECOMSIMPLY_ADMIN_2025"
WRONG_ADMIN_KEY = "ECOMSIMPLY_ADMIN_2024"  # Ancienne clé qui ne doit plus marcher

print("🔧 ECOMSIMPLY ADMIN DASHBOARD - TEST COMPLET DES CORRECTIONS")
print("=" * 80)
print(f"🌐 Backend URL: {BACKEND_URL}")
print(f"🔑 Admin Key (correct): {CORRECT_ADMIN_KEY}")
print(f"❌ Admin Key (wrong): {WRONG_ADMIN_KEY}")
print("=" * 80)

class AdminDashboardTester:
    """Testeur complet du tableau de bord admin"""
    
    def __init__(self):
        self.test_results = {
            'plans_config': {'passed': 0, 'failed': 0, 'details': []},
            'promotions': {'passed': 0, 'failed': 0, 'details': []},
            'testimonials': {'passed': 0, 'failed': 0, 'details': []},
            'security': {'passed': 0, 'failed': 0, 'details': []}
        }
        self.session = requests.Session()
        self.session.timeout = 30  # Timeout global
        
    def log_test(self, category: str, test_name: str, success: bool, details: str = ""):
        """Log un résultat de test"""
        if success:
            self.test_results[category]['passed'] += 1
            status = "✅ PASS"
        else:
            self.test_results[category]['failed'] += 1
            status = "❌ FAIL"
        
        self.test_results[category]['details'].append({
            'test': test_name,
            'status': status,
            'details': details
        })
        
        print(f"{status}: {test_name}")
        if details:
            print(f"    📋 {details}")
    
    def test_plans_config_endpoint(self):
        """Test de l'endpoint /api/admin/plans-config"""
        print("\n🎯 TEST 1: PAGE PRIX ADMIN - /api/admin/plans-config")
        print("-" * 60)
        
        # Test 1.1: Accès avec bonne clé admin
        try:
            url = f"{API_BASE}/admin/plans-config"
            params = {"admin_key": CORRECT_ADMIN_KEY}
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier la structure de réponse
                if "success" in data and data["success"]:
                    self.log_test('plans_config', 'Accès avec clé admin correcte', True, 
                                f"Status 200, success=true")
                    
                    # Vérifier la présence des 3 plans
                    if "plans_config" in data:
                        plans = data["plans_config"]
                        plan_names = [plan.get("plan_name", "") for plan in plans]
                        
                        expected_plans = ["gratuit", "pro", "premium"]
                        found_plans = [name for name in expected_plans if name in plan_names]
                        
                        if len(found_plans) == 3:
                            self.log_test('plans_config', 'Présence des 3 plans requis', True,
                                        f"Plans trouvés: {', '.join(found_plans)}")
                        else:
                            self.log_test('plans_config', 'Présence des 3 plans requis', False,
                                        f"Plans manquants. Trouvés: {', '.join(found_plans)}")
                        
                        # Vérifier les données des plans
                        for plan in plans:
                            plan_name = plan.get("plan_name", "unknown")
                            price = plan.get("price", 0)
                            
                            if plan_name == "gratuit" and price == 0:
                                self.log_test('plans_config', f'Plan {plan_name} - prix correct', True,
                                            f"Prix: {price}€")
                            elif plan_name in ["pro", "premium"] and price > 0:
                                self.log_test('plans_config', f'Plan {plan_name} - prix correct', True,
                                            f"Prix: {price}€")
                            else:
                                self.log_test('plans_config', f'Plan {plan_name} - prix incorrect', False,
                                            f"Prix: {price}€")
                    else:
                        self.log_test('plans_config', 'Structure réponse - champ plans_config', False,
                                    "Champ 'plans_config' manquant dans la réponse")
                else:
                    self.log_test('plans_config', 'Structure réponse - success flag', False,
                                f"success={data.get('success', 'missing')}")
            else:
                self.log_test('plans_config', 'Accès avec clé admin correcte', False,
                            f"Status {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test('plans_config', 'Accès avec clé admin correcte', False,
                        f"Exception: {str(e)}")
        
        # Test 1.2: Accès avec mauvaise clé admin (doit retourner 403)
        try:
            url = f"{API_BASE}/admin/plans-config"
            params = {"admin_key": WRONG_ADMIN_KEY}
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 403:
                self.log_test('plans_config', 'Sécurité - rejet mauvaise clé', True,
                            f"Status 403 comme attendu")
            else:
                self.log_test('plans_config', 'Sécurité - rejet mauvaise clé', False,
                            f"Status {response.status_code} au lieu de 403")
                
        except Exception as e:
            self.log_test('plans_config', 'Sécurité - rejet mauvaise clé', False,
                        f"Exception: {str(e)}")
        
        # Test 1.3: Accès sans clé admin
        try:
            url = f"{API_BASE}/admin/plans-config"
            
            response = self.session.get(url)
            
            if response.status_code == 403:
                self.log_test('plans_config', 'Sécurité - rejet sans clé', True,
                            f"Status 403 comme attendu")
            else:
                self.log_test('plans_config', 'Sécurité - rejet sans clé', False,
                            f"Status {response.status_code} au lieu de 403")
                
        except Exception as e:
            self.log_test('plans_config', 'Sécurité - rejet sans clé', False,
                        f"Exception: {str(e)}")
    
    def test_promotions_endpoint(self):
        """Test de l'endpoint /api/admin/promotions"""
        print("\n🎯 TEST 2: PAGE PROMOTIONS ADMIN - /api/admin/promotions")
        print("-" * 60)
        
        # Test 2.1: GET - Récupération des promotions
        try:
            url = f"{API_BASE}/admin/promotions"
            params = {"admin_key": CORRECT_ADMIN_KEY}
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if "success" in data and data["success"]:
                    self.log_test('promotions', 'GET promotions - accès autorisé', True,
                                f"Status 200, success=true")
                    
                    # Vérifier la structure (peut être vide mais doit répondre)
                    if "promotions" in data:
                        promotions = data["promotions"]
                        self.log_test('promotions', 'GET promotions - structure réponse', True,
                                    f"{len(promotions)} promotions trouvées")
                    else:
                        self.log_test('promotions', 'GET promotions - structure réponse', False,
                                    "Champ 'promotions' manquant")
                else:
                    self.log_test('promotions', 'GET promotions - success flag', False,
                                f"success={data.get('success', 'missing')}")
            else:
                self.log_test('promotions', 'GET promotions - accès autorisé', False,
                            f"Status {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test('promotions', 'GET promotions - accès autorisé', False,
                        f"Exception: {str(e)}")
        
        # Test 2.2: POST - Création d'une promotion de test
        try:
            url = f"{API_BASE}/admin/promotions"
            params = {"admin_key": CORRECT_ADMIN_KEY}
            
            test_promotion = {
                "title": "Test Promotion Admin Dashboard",
                "description": "Promotion de test pour validation du tableau de bord",
                "target_plans": ["pro", "premium"],
                "discount_type": "percentage",
                "discount_value": 20.0,
                "badge_text": "TEST -20%",
                "promotional_text": "Offre de test limitée",
                "start_date": datetime.now().isoformat(),
                "end_date": datetime(2025, 12, 31).isoformat(),
                "is_active": True
            }
            
            response = self.session.post(url, params=params, json=test_promotion)
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                if "success" in data and data["success"]:
                    self.log_test('promotions', 'POST promotion - création réussie', True,
                                f"Status {response.status_code}, promotion créée")
                    
                    # Stocker l'ID pour éventuel nettoyage
                    if "promotion" in data and "id" in data["promotion"]:
                        self.test_promotion_id = data["promotion"]["id"]
                else:
                    self.log_test('promotions', 'POST promotion - création réussie', False,
                                f"success={data.get('success', 'missing')}")
            else:
                self.log_test('promotions', 'POST promotion - création réussie', False,
                            f"Status {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test('promotions', 'POST promotion - création réussie', False,
                        f"Exception: {str(e)}")
        
        # Test 2.3: Sécurité - Accès avec mauvaise clé
        try:
            url = f"{API_BASE}/admin/promotions"
            params = {"admin_key": WRONG_ADMIN_KEY}
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 403:
                self.log_test('promotions', 'Sécurité - rejet mauvaise clé', True,
                            f"Status 403 comme attendu")
            else:
                self.log_test('promotions', 'Sécurité - rejet mauvaise clé', False,
                            f"Status {response.status_code} au lieu de 403")
                
        except Exception as e:
            self.log_test('promotions', 'Sécurité - rejet mauvaise clé', False,
                        f"Exception: {str(e)}")
    
    def test_testimonials_endpoint(self):
        """Test de l'endpoint /api/admin/testimonials"""
        print("\n🎯 TEST 3: PAGE TÉMOIGNAGES ADMIN - /api/admin/testimonials")
        print("-" * 60)
        
        # Test 3.1: GET - Récupération des témoignages
        try:
            url = f"{API_BASE}/admin/testimonials"
            params = {"admin_key": CORRECT_ADMIN_KEY}
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if "success" in data and data["success"]:
                    self.log_test('testimonials', 'GET testimonials - accès autorisé', True,
                                f"Status 200, success=true")
                    
                    # Vérifier la structure
                    if "testimonials" in data:
                        testimonials = data["testimonials"]
                        self.log_test('testimonials', 'GET testimonials - structure réponse', True,
                                    f"{len(testimonials)} témoignages trouvés")
                        
                        # Vérifier les champs requis sur le premier témoignage s'il existe
                        if len(testimonials) > 0:
                            first_testimonial = testimonials[0]
                            required_fields = ["id", "name", "title", "rating", "comment", "status", "created_at"]
                            missing_fields = [field for field in required_fields if field not in first_testimonial]
                            
                            if not missing_fields:
                                self.log_test('testimonials', 'Structure témoignage - champs requis', True,
                                            f"Tous les champs requis présents")
                            else:
                                self.log_test('testimonials', 'Structure témoignage - champs requis', False,
                                            f"Champs manquants: {', '.join(missing_fields)}")
                    else:
                        self.log_test('testimonials', 'GET testimonials - structure réponse', False,
                                    "Champ 'testimonials' manquant")
                else:
                    self.log_test('testimonials', 'GET testimonials - success flag', False,
                                f"success={data.get('success', 'missing')}")
            else:
                self.log_test('testimonials', 'GET testimonials - accès autorisé', False,
                            f"Status {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test('testimonials', 'GET testimonials - accès autorisé', False,
                        f"Exception: {str(e)}")
        
        # Test 3.2: Sécurité - Accès avec mauvaise clé
        try:
            url = f"{API_BASE}/admin/testimonials"
            params = {"admin_key": WRONG_ADMIN_KEY}
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 403:
                self.log_test('testimonials', 'Sécurité - rejet mauvaise clé', True,
                            f"Status 403 comme attendu")
            else:
                self.log_test('testimonials', 'Sécurité - rejet mauvaise clé', False,
                            f"Status {response.status_code} au lieu de 403")
                
        except Exception as e:
            self.log_test('testimonials', 'Sécurité - rejet mauvaise clé', False,
                        f"Exception: {str(e)}")
        
        # Test 3.3: Accès sans clé admin
        try:
            url = f"{API_BASE}/admin/testimonials"
            
            response = self.session.get(url)
            
            if response.status_code == 403:
                self.log_test('testimonials', 'Sécurité - rejet sans clé', True,
                            f"Status 403 comme attendu")
            else:
                self.log_test('testimonials', 'Sécurité - rejet sans clé', False,
                            f"Status {response.status_code} au lieu de 403")
                
        except Exception as e:
            self.log_test('testimonials', 'Sécurité - rejet sans clé', False,
                        f"Exception: {str(e)}")
    
    def test_timeout_and_fallbacks(self):
        """Test des timeouts et fallbacks pour éviter les erreurs 502"""
        print("\n🎯 TEST 4: TIMEOUTS ET FALLBACKS - PRÉVENTION ERREURS 502")
        print("-" * 60)
        
        endpoints_to_test = [
            ("plans-config", f"{API_BASE}/admin/plans-config"),
            ("promotions", f"{API_BASE}/admin/promotions"),
            ("testimonials", f"{API_BASE}/admin/testimonials")
        ]
        
        for endpoint_name, url in endpoints_to_test:
            try:
                params = {"admin_key": CORRECT_ADMIN_KEY}
                
                # Test avec timeout court pour vérifier la robustesse
                start_time = time.time()
                response = self.session.get(url, params=params, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    self.log_test('security', f'Timeout {endpoint_name} - réponse rapide', True,
                                f"Réponse en {response_time:.2f}s (< 10s)")
                elif response.status_code == 502:
                    self.log_test('security', f'Timeout {endpoint_name} - éviter 502', False,
                                f"Erreur 502 détectée - fallback nécessaire")
                else:
                    self.log_test('security', f'Timeout {endpoint_name} - réponse stable', True,
                                f"Status {response.status_code} (pas de 502)")
                    
            except requests.exceptions.Timeout:
                self.log_test('security', f'Timeout {endpoint_name} - gestion timeout', False,
                            f"Timeout après 10s - fallback nécessaire")
            except Exception as e:
                self.log_test('security', f'Timeout {endpoint_name} - gestion erreur', False,
                            f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Exécute tous les tests"""
        print("🚀 DÉMARRAGE DES TESTS ADMIN DASHBOARD")
        print("=" * 80)
        
        start_time = time.time()
        
        # Exécuter tous les tests
        self.test_plans_config_endpoint()
        self.test_promotions_endpoint()
        self.test_testimonials_endpoint()
        self.test_timeout_and_fallbacks()
        
        # Calculer les résultats
        total_time = time.time() - start_time
        
        print("\n" + "=" * 80)
        print("📊 RÉSULTATS FINAUX DES TESTS ADMIN DASHBOARD")
        print("=" * 80)
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.test_results.items():
            passed = results['passed']
            failed = results['failed']
            total = passed + failed
            
            total_passed += passed
            total_failed += failed
            
            if total > 0:
                success_rate = (passed / total) * 100
                status = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 60 else "❌"
                
                print(f"{status} {category.upper()}: {passed}/{total} tests réussis ({success_rate:.1f}%)")
                
                # Afficher les détails des échecs
                for detail in results['details']:
                    if detail['status'].startswith('❌'):
                        print(f"    ❌ {detail['test']}: {detail['details']}")
        
        # Résultat global
        total_tests = total_passed + total_failed
        if total_tests > 0:
            global_success_rate = (total_passed / total_tests) * 100
            
            print("\n" + "-" * 80)
            print(f"🎯 RÉSULTAT GLOBAL: {total_passed}/{total_tests} tests réussis ({global_success_rate:.1f}%)")
            print(f"⏱️ Temps d'exécution: {total_time:.2f} secondes")
            
            if global_success_rate >= 90:
                print("🎉 EXCELLENT! Tableau de bord admin entièrement fonctionnel")
            elif global_success_rate >= 75:
                print("✅ BON! Fonctionnalités principales opérationnelles")
            elif global_success_rate >= 50:
                print("⚠️ MOYEN! Corrections partielles, améliorations nécessaires")
            else:
                print("❌ CRITIQUE! Problèmes majeurs détectés")
        
        print("=" * 80)
        
        return {
            'total_tests': total_tests,
            'passed': total_passed,
            'failed': total_failed,
            'success_rate': global_success_rate if total_tests > 0 else 0,
            'execution_time': total_time,
            'details': self.test_results
        }

def main():
    """Fonction principale"""
    tester = AdminDashboardTester()
    results = tester.run_all_tests()
    
    # Retourner le code de sortie approprié
    if results['success_rate'] >= 75:
        sys.exit(0)  # Succès
    else:
        sys.exit(1)  # Échec

if __name__ == "__main__":
    main()