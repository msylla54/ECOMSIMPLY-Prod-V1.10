#!/usr/bin/env python3
"""
Test complet et détaillé du tableau de bord admin ECOMSIMPLY
Validation complète des corrections apportées selon la review request
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
WRONG_ADMIN_KEY = "ECOMSIMPLY_ADMIN_2024"

print("🎯 ECOMSIMPLY ADMIN DASHBOARD - VALIDATION COMPLÈTE DES CORRECTIONS")
print("=" * 80)
print(f"🌐 Backend URL: {BACKEND_URL}")
print(f"✅ Admin Key (correct): {CORRECT_ADMIN_KEY}")
print(f"❌ Admin Key (wrong): {WRONG_ADMIN_KEY}")
print("=" * 80)

class ComprehensiveAdminTester:
    """Testeur complet et détaillé du tableau de bord admin"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 30
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_result(self, test_name: str, success: bool, details: str = "", category: str = ""):
        """Log un résultat de test avec détails"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = {
            'test': test_name,
            'category': category,
            'status': status,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"    📋 {details}")
    
    def test_plans_config_comprehensive(self):
        """Test complet de l'endpoint /api/admin/plans-config"""
        print("\n🎯 TEST DÉTAILLÉ: PAGE PRIX ADMIN")
        print("-" * 60)
        
        # Test 1: Accès avec bonne clé admin
        try:
            url = f"{API_BASE}/admin/plans-config"
            params = {"admin_key": CORRECT_ADMIN_KEY}
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier success flag
                if data.get("success") == True:
                    self.log_result("Plans Config - Success Flag", True, 
                                  "success=true présent dans la réponse", "plans_config")
                else:
                    self.log_result("Plans Config - Success Flag", False,
                                  f"success={data.get('success', 'missing')}", "plans_config")
                
                # Vérifier structure plans_config
                if "plans_config" in data:
                    plans = data["plans_config"]
                    self.log_result("Plans Config - Structure Response", True,
                                  f"Champ 'plans_config' présent avec {len(plans)} plans", "plans_config")
                    
                    # Vérifier les 3 plans requis
                    plan_names = [plan.get("plan_name", "") for plan in plans]
                    expected_plans = ["gratuit", "pro", "premium"]
                    
                    for expected_plan in expected_plans:
                        if expected_plan in plan_names:
                            self.log_result(f"Plans Config - Plan {expected_plan}", True,
                                          f"Plan {expected_plan} trouvé", "plans_config")
                        else:
                            self.log_result(f"Plans Config - Plan {expected_plan}", False,
                                          f"Plan {expected_plan} manquant", "plans_config")
                    
                    # Vérifier les données de chaque plan
                    for plan in plans:
                        plan_name = plan.get("plan_name", "unknown")
                        price = plan.get("price", 0)
                        currency = plan.get("currency", "")
                        
                        # Vérifier prix gratuit
                        if plan_name == "gratuit":
                            if price == 0:
                                self.log_result(f"Plans Config - Prix {plan_name}", True,
                                              f"Prix gratuit correct: {price}€", "plans_config")
                            else:
                                self.log_result(f"Plans Config - Prix {plan_name}", False,
                                              f"Prix gratuit incorrect: {price}€", "plans_config")
                        
                        # Vérifier prix payants
                        elif plan_name in ["pro", "premium"]:
                            if price > 0:
                                self.log_result(f"Plans Config - Prix {plan_name}", True,
                                              f"Prix {plan_name}: {price}€", "plans_config")
                            else:
                                self.log_result(f"Plans Config - Prix {plan_name}", False,
                                              f"Prix {plan_name} invalide: {price}€", "plans_config")
                        
                        # Vérifier devise
                        if currency == "EUR":
                            self.log_result(f"Plans Config - Devise {plan_name}", True,
                                          f"Devise correcte: {currency}", "plans_config")
                        else:
                            self.log_result(f"Plans Config - Devise {plan_name}", False,
                                          f"Devise incorrecte: {currency}", "plans_config")
                else:
                    self.log_result("Plans Config - Structure Response", False,
                                  "Champ 'plans_config' manquant", "plans_config")
            else:
                self.log_result("Plans Config - Access Authorized", False,
                              f"Status {response.status_code}: {response.text[:200]}", "plans_config")
                
        except Exception as e:
            self.log_result("Plans Config - Access Authorized", False,
                          f"Exception: {str(e)}", "plans_config")
        
        # Test 2: Sécurité avec mauvaise clé
        try:
            url = f"{API_BASE}/admin/plans-config"
            params = {"admin_key": WRONG_ADMIN_KEY}
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 403:
                self.log_result("Plans Config - Security Wrong Key", True,
                              "Status 403 pour mauvaise clé admin", "security")
            else:
                self.log_result("Plans Config - Security Wrong Key", False,
                              f"Status {response.status_code} au lieu de 403", "security")
                
        except Exception as e:
            self.log_result("Plans Config - Security Wrong Key", False,
                          f"Exception: {str(e)}", "security")
    
    def test_promotions_comprehensive(self):
        """Test complet de l'endpoint /api/admin/promotions"""
        print("\n🎯 TEST DÉTAILLÉ: PAGE PROMOTIONS ADMIN")
        print("-" * 60)
        
        # Test 1: GET promotions
        try:
            url = f"{API_BASE}/admin/promotions"
            params = {"admin_key": CORRECT_ADMIN_KEY}
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier success flag
                if data.get("success") == True:
                    self.log_result("Promotions - Success Flag", True,
                                  "success=true présent dans la réponse", "promotions")
                else:
                    self.log_result("Promotions - Success Flag", False,
                                  f"success={data.get('success', 'missing')}", "promotions")
                
                # Vérifier structure promotions
                if "promotions" in data:
                    promotions = data["promotions"]
                    self.log_result("Promotions - Structure Response", True,
                                  f"Champ 'promotions' présent avec {len(promotions)} promotions", "promotions")
                    
                    # Si des promotions existent, vérifier leur structure
                    if len(promotions) > 0:
                        first_promo = promotions[0]
                        required_fields = ["id", "title", "description", "target_plans", 
                                         "discount_type", "discount_value", "is_active"]
                        
                        missing_fields = [field for field in required_fields if field not in first_promo]
                        
                        if not missing_fields:
                            self.log_result("Promotions - Fields Structure", True,
                                          "Tous les champs requis présents", "promotions")
                        else:
                            self.log_result("Promotions - Fields Structure", False,
                                          f"Champs manquants: {', '.join(missing_fields)}", "promotions")
                else:
                    self.log_result("Promotions - Structure Response", False,
                                  "Champ 'promotions' manquant", "promotions")
            else:
                self.log_result("Promotions - GET Access", False,
                              f"Status {response.status_code}: {response.text[:200]}", "promotions")
                
        except Exception as e:
            self.log_result("Promotions - GET Access", False,
                          f"Exception: {str(e)}", "promotions")
        
        # Test 2: POST création promotion
        try:
            url = f"{API_BASE}/admin/promotions"
            params = {"admin_key": CORRECT_ADMIN_KEY}
            
            test_promotion = {
                "title": "Test Validation Admin Dashboard",
                "description": "Promotion de test pour validation complète",
                "target_plans": ["pro", "premium"],
                "discount_type": "percentage",
                "discount_value": 15.0,
                "badge_text": "VALIDATION -15%",
                "promotional_text": "Test de validation du tableau de bord",
                "start_date": datetime.now().isoformat(),
                "end_date": datetime(2025, 12, 31).isoformat(),
                "is_active": True
            }
            
            response = self.session.post(url, params=params, json=test_promotion)
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                if data.get("success") == True:
                    self.log_result("Promotions - POST Creation", True,
                                  f"Promotion créée avec succès", "promotions")
                    
                    # Vérifier que la promotion a été créée avec les bonnes données
                    if "promotion" in data:
                        created_promo = data["promotion"]
                        if created_promo.get("title") == test_promotion["title"]:
                            self.log_result("Promotions - POST Data Integrity", True,
                                          "Données de promotion correctement sauvegardées", "promotions")
                        else:
                            self.log_result("Promotions - POST Data Integrity", False,
                                          "Données de promotion incorrectes", "promotions")
                else:
                    self.log_result("Promotions - POST Creation", False,
                                  f"success={data.get('success', 'missing')}", "promotions")
            else:
                self.log_result("Promotions - POST Creation", False,
                              f"Status {response.status_code}: {response.text[:200]}", "promotions")
                
        except Exception as e:
            self.log_result("Promotions - POST Creation", False,
                          f"Exception: {str(e)}", "promotions")
        
        # Test 3: Sécurité
        try:
            url = f"{API_BASE}/admin/promotions"
            params = {"admin_key": WRONG_ADMIN_KEY}
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 403:
                self.log_result("Promotions - Security Wrong Key", True,
                              "Status 403 pour mauvaise clé admin", "security")
            else:
                self.log_result("Promotions - Security Wrong Key", False,
                              f"Status {response.status_code} au lieu de 403", "security")
                
        except Exception as e:
            self.log_result("Promotions - Security Wrong Key", False,
                          f"Exception: {str(e)}", "security")
    
    def test_testimonials_comprehensive(self):
        """Test complet de l'endpoint /api/admin/testimonials"""
        print("\n🎯 TEST DÉTAILLÉ: PAGE TÉMOIGNAGES ADMIN")
        print("-" * 60)
        
        # Test 1: GET testimonials
        try:
            url = f"{API_BASE}/admin/testimonials"
            params = {"admin_key": CORRECT_ADMIN_KEY}
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier success flag
                if data.get("success") == True:
                    self.log_result("Testimonials - Success Flag", True,
                                  "success=true présent dans la réponse", "testimonials")
                else:
                    self.log_result("Testimonials - Success Flag", False,
                                  f"success={data.get('success', 'missing')}", "testimonials")
                
                # Vérifier structure testimonials
                if "testimonials" in data:
                    testimonials = data["testimonials"]
                    self.log_result("Testimonials - Structure Response", True,
                                  f"Champ 'testimonials' présent avec {len(testimonials)} témoignages", "testimonials")
                    
                    # Vérifier champ count
                    if "count" in data:
                        count = data["count"]
                        if count == len(testimonials):
                            self.log_result("Testimonials - Count Field", True,
                                          f"Count correct: {count}", "testimonials")
                        else:
                            self.log_result("Testimonials - Count Field", False,
                                          f"Count incorrect: {count} vs {len(testimonials)}", "testimonials")
                    
                    # Vérifier timestamp
                    if "timestamp" in data:
                        self.log_result("Testimonials - Timestamp Field", True,
                                      "Timestamp présent dans la réponse", "testimonials")
                    else:
                        self.log_result("Testimonials - Timestamp Field", False,
                                      "Timestamp manquant", "testimonials")
                else:
                    self.log_result("Testimonials - Structure Response", False,
                                  "Champ 'testimonials' manquant", "testimonials")
            else:
                self.log_result("Testimonials - GET Access", False,
                              f"Status {response.status_code}: {response.text[:200]}", "testimonials")
                
        except Exception as e:
            self.log_result("Testimonials - GET Access", False,
                          f"Exception: {str(e)}", "testimonials")
        
        # Test 2: Sécurité
        try:
            url = f"{API_BASE}/admin/testimonials"
            params = {"admin_key": WRONG_ADMIN_KEY}
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 403:
                self.log_result("Testimonials - Security Wrong Key", True,
                              "Status 403 pour mauvaise clé admin", "security")
            else:
                self.log_result("Testimonials - Security Wrong Key", False,
                              f"Status {response.status_code} au lieu de 403", "security")
                
        except Exception as e:
            self.log_result("Testimonials - Security Wrong Key", False,
                          f"Exception: {str(e)}", "security")
    
    def test_admin_key_corrections(self):
        """Test spécifique des corrections de clés admin"""
        print("\n🎯 TEST SPÉCIFIQUE: CORRECTIONS CLÉS ADMIN 2024 → 2025")
        print("-" * 60)
        
        endpoints = [
            ("plans-config", f"{API_BASE}/admin/plans-config"),
            ("promotions", f"{API_BASE}/admin/promotions"),
            ("testimonials", f"{API_BASE}/admin/testimonials")
        ]
        
        for endpoint_name, url in endpoints:
            # Test avec ancienne clé 2024 (doit échouer)
            try:
                params = {"admin_key": "ECOMSIMPLY_ADMIN_2024"}
                response = self.session.get(url, params=params)
                
                if response.status_code == 403:
                    self.log_result(f"Admin Key 2024 Rejected - {endpoint_name}", True,
                                  "Ancienne clé 2024 correctement rejetée", "admin_key_corrections")
                else:
                    self.log_result(f"Admin Key 2024 Rejected - {endpoint_name}", False,
                                  f"Ancienne clé acceptée (Status {response.status_code})", "admin_key_corrections")
            except Exception as e:
                self.log_result(f"Admin Key 2024 Rejected - {endpoint_name}", False,
                              f"Exception: {str(e)}", "admin_key_corrections")
            
            # Test avec nouvelle clé 2025 (doit réussir)
            try:
                params = {"admin_key": "ECOMSIMPLY_ADMIN_2025"}
                response = self.session.get(url, params=params)
                
                if response.status_code == 200:
                    self.log_result(f"Admin Key 2025 Accepted - {endpoint_name}", True,
                                  "Nouvelle clé 2025 correctement acceptée", "admin_key_corrections")
                else:
                    self.log_result(f"Admin Key 2025 Accepted - {endpoint_name}", False,
                                  f"Nouvelle clé rejetée (Status {response.status_code})", "admin_key_corrections")
            except Exception as e:
                self.log_result(f"Admin Key 2025 Accepted - {endpoint_name}", False,
                              f"Exception: {str(e)}", "admin_key_corrections")
    
    def test_timeout_fallbacks(self):
        """Test des timeouts et fallbacks pour éviter les erreurs 502"""
        print("\n🎯 TEST SPÉCIFIQUE: TIMEOUTS ET FALLBACKS ANTI-502")
        print("-" * 60)
        
        endpoints = [
            ("plans-config", f"{API_BASE}/admin/plans-config"),
            ("promotions", f"{API_BASE}/admin/promotions"),
            ("testimonials", f"{API_BASE}/admin/testimonials")
        ]
        
        for endpoint_name, url in endpoints:
            try:
                params = {"admin_key": CORRECT_ADMIN_KEY}
                
                start_time = time.time()
                response = self.session.get(url, params=params, timeout=15)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    self.log_result(f"Timeout Prevention - {endpoint_name}", True,
                                  f"Réponse en {response_time:.2f}s (< 15s)", "timeout_fallbacks")
                elif response.status_code == 502:
                    self.log_result(f"502 Error Prevention - {endpoint_name}", False,
                                  "Erreur 502 détectée - fallback nécessaire", "timeout_fallbacks")
                else:
                    self.log_result(f"Error Handling - {endpoint_name}", True,
                                  f"Status {response.status_code} (pas de 502)", "timeout_fallbacks")
                    
            except requests.exceptions.Timeout:
                self.log_result(f"Timeout Handling - {endpoint_name}", False,
                              "Timeout après 15s - fallback nécessaire", "timeout_fallbacks")
            except Exception as e:
                self.log_result(f"Exception Handling - {endpoint_name}", False,
                              f"Exception: {str(e)}", "timeout_fallbacks")
    
    def run_comprehensive_tests(self):
        """Exécute tous les tests complets"""
        print("🚀 DÉMARRAGE DES TESTS COMPLETS ADMIN DASHBOARD")
        print("=" * 80)
        
        start_time = time.time()
        
        # Exécuter tous les tests
        self.test_plans_config_comprehensive()
        self.test_promotions_comprehensive()
        self.test_testimonials_comprehensive()
        self.test_admin_key_corrections()
        self.test_timeout_fallbacks()
        
        # Calculer les résultats
        total_time = time.time() - start_time
        
        print("\n" + "=" * 80)
        print("📊 RÉSULTATS FINAUX - VALIDATION COMPLÈTE ADMIN DASHBOARD")
        print("=" * 80)
        
        # Grouper les résultats par catégorie
        categories = {}
        for result in self.test_results:
            category = result.get('category', 'other')
            if category not in categories:
                categories[category] = {'passed': 0, 'failed': 0, 'details': []}
            
            if result['success']:
                categories[category]['passed'] += 1
            else:
                categories[category]['failed'] += 1
                categories[category]['details'].append(result)
        
        # Afficher les résultats par catégorie
        for category, stats in categories.items():
            total = stats['passed'] + stats['failed']
            if total > 0:
                success_rate = (stats['passed'] / total) * 100
                status = "✅" if success_rate >= 90 else "⚠️" if success_rate >= 70 else "❌"
                
                print(f"{status} {category.upper()}: {stats['passed']}/{total} tests réussis ({success_rate:.1f}%)")
                
                # Afficher les échecs
                for detail in stats['details']:
                    print(f"    ❌ {detail['test']}: {detail['details']}")
        
        # Résultat global
        if self.total_tests > 0:
            global_success_rate = (self.passed_tests / self.total_tests) * 100
            
            print("\n" + "-" * 80)
            print(f"🎯 RÉSULTAT GLOBAL: {self.passed_tests}/{self.total_tests} tests réussis ({global_success_rate:.1f}%)")
            print(f"⏱️ Temps d'exécution: {total_time:.2f} secondes")
            
            # Évaluation finale
            if global_success_rate >= 95:
                print("🎉 EXCELLENT! Toutes les corrections admin dashboard fonctionnelles")
                final_status = "EXCELLENT"
            elif global_success_rate >= 85:
                print("✅ TRÈS BON! Corrections principales opérationnelles")
                final_status = "TRÈS BON"
            elif global_success_rate >= 70:
                print("⚠️ BON! Corrections partielles, quelques améliorations nécessaires")
                final_status = "BON"
            else:
                print("❌ CRITIQUE! Problèmes majeurs dans les corrections")
                final_status = "CRITIQUE"
        
        print("=" * 80)
        
        return {
            'total_tests': self.total_tests,
            'passed': self.passed_tests,
            'failed': self.total_tests - self.passed_tests,
            'success_rate': global_success_rate if self.total_tests > 0 else 0,
            'execution_time': total_time,
            'final_status': final_status,
            'categories': categories
        }

def main():
    """Fonction principale"""
    tester = ComprehensiveAdminTester()
    results = tester.run_comprehensive_tests()
    
    # Retourner le code de sortie approprié
    if results['success_rate'] >= 80:
        sys.exit(0)  # Succès
    else:
        sys.exit(1)  # Échec

if __name__ == "__main__":
    main()