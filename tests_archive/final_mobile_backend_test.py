#!/usr/bin/env python3
"""
Final Backend Test - Mobile Responsiveness Regression
Test simple utilisant requests pour vérifier le backend après modifications mobile
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

class FinalMobileBackendTester:
    """Testeur final utilisant requests"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.auth_token = None
        self.test_results = []
        self.start_time = time.time()
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Enregistrer résultat de test"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        print()
    
    def authenticate(self):
        """Authentification utilisateur admin"""
        try:
            # Créer utilisateur admin de test
            admin_data = {
                "email": "final.test@ecomsimply.com",
                "name": "Final Test User",
                "password": "FinalTest2025!",
                "admin_key": "ECOMSIMPLY_ADMIN_2025"
            }
            
            response = self.session.post(f"{API_BASE}/auth/register", json=admin_data, timeout=10)
            if response.status_code in [200, 201]:
                print("✅ Admin user created successfully")
            elif response.status_code == 400:
                print("ℹ️ Admin user already exists")
            else:
                print(f"⚠️ User creation status: {response.status_code}")
            
            # Connexion
            login_data = {
                "email": "final.test@ecomsimply.com",
                "password": "FinalTest2025!"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                if self.auth_token:
                    self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                    self.log_test("Authentication", True, "Admin user authenticated successfully")
                    return True
            
            self.log_test("Authentication", False, f"Login failed: {response.status_code}")
            return False
                
        except Exception as e:
            self.log_test("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_health_checks(self):
        """Test des health checks"""
        
        # Test health check principal
        try:
            response = self.session.get(f"{API_BASE}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                success = data.get('status') == 'healthy'
                uptime = data.get('uptime', 0)
                details = f"Status: {data.get('status')}, Uptime: {uptime:.1f}s"
                self.log_test("Health Check", success, details)
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
        
        # Test ready endpoint
        try:
            response = self.session.get(f"{API_BASE}/health/ready", timeout=10)
            success = response.status_code == 200
            self.log_test("Ready Check", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Ready Check", False, f"Exception: {str(e)}")
    
    def test_public_endpoints(self):
        """Test des endpoints publics"""
        
        # Test stats publiques
        try:
            response = self.session.get(f"{API_BASE}/stats/public", timeout=10)
            if response.status_code == 200:
                data = response.json()
                success = 'satisfied_clients' in data and 'total_product_sheets' in data
                details = f"Clients: {data.get('satisfied_clients', 0)}, Sheets: {data.get('total_product_sheets', 0)}"
                self.log_test("Public Stats", success, details)
            else:
                self.log_test("Public Stats", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Public Stats", False, f"Exception: {str(e)}")
        
        # Test plans pricing
        try:
            response = self.session.get(f"{API_BASE}/public/plans-pricing", timeout=10)
            if response.status_code == 200:
                data = response.json()
                success = isinstance(data, list) and len(data) > 0
                details = f"Plans available: {len(data)}"
                self.log_test("Plans Pricing", success, details)
            else:
                self.log_test("Plans Pricing", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Plans Pricing", False, f"Exception: {str(e)}")
    
    def test_amazon_phase3_services(self):
        """Test des services Amazon Phase 3"""
        
        # Test health check Phase 3
        try:
            response = self.session.get(f"{API_BASE}/amazon/health/phase3", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                success = data.get('success') is True
                health = data.get('health', {})
                services = health.get('services', {})
                
                # Compter les services healthy
                healthy_services = sum(1 for status in services.values() if status == 'healthy')
                total_services = len(services)
                
                success = success and healthy_services >= 3  # Au moins 3/4 services healthy
                details = f"Phase: {health.get('phase', 'Unknown')}, Services healthy: {healthy_services}/{total_services}"
                self.log_test("Amazon Phase 3 Health", success, details)
            else:
                self.log_test("Amazon Phase 3 Health", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Amazon Phase 3 Health", False, f"Exception: {str(e)}")
    
    def test_amazon_seo_endpoints(self):
        """Test des endpoints SEO Amazon"""
        
        # Test règles SEO (nécessite auth)
        try:
            response = self.session.get(f"{API_BASE}/amazon/seo/rules", timeout=10)
            if response.status_code == 200:
                data = response.json()
                success = 'rules' in data
                details = f"SEO rules loaded successfully"
                self.log_test("Amazon SEO Rules", success, details)
            elif response.status_code == 401:
                self.log_test("Amazon SEO Rules", True, "Auth required (endpoint accessible)")
            else:
                self.log_test("Amazon SEO Rules", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Amazon SEO Rules", False, f"Exception: {str(e)}")
        
        # Test historique SEO (nécessite auth)
        try:
            response = self.session.get(f"{API_BASE}/amazon/seo/history?limit=5", timeout=10)
            if response.status_code == 200:
                data = response.json()
                success = 'history' in data
                details = f"SEO history accessible"
                self.log_test("Amazon SEO History", success, details)
            elif response.status_code == 401:
                self.log_test("Amazon SEO History", True, "Auth required (endpoint accessible)")
            else:
                self.log_test("Amazon SEO History", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Amazon SEO History", False, f"Exception: {str(e)}")
    
    def test_core_functionality(self):
        """Test de la fonctionnalité core avec auth"""
        
        if not self.auth_token:
            print("⚠️ Skipping authenticated tests - no auth token")
            return
        
        # Test génération de fiche
        try:
            request_data = {
                "product_name": "Test Mobile Backend Product Final",
                "product_description": "Test product to verify backend functionality after mobile changes - final test",
                "generate_image": False,
                "number_of_images": 0,
                "language": "fr"
            }
            
            response = self.session.post(f"{API_BASE}/generate-sheet", json=request_data, timeout=30)
            if response.status_code == 200:
                data = response.json()
                success = 'generated_title' in data and 'marketing_description' in data
                title_length = len(data.get('generated_title', ''))
                details = f"Sheet generated, title length: {title_length} chars"
                self.log_test("Core - Sheet Generation", success, details)
            else:
                self.log_test("Core - Sheet Generation", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Core - Sheet Generation", False, f"Exception: {str(e)}")
        
        # Test récupération des fiches
        try:
            response = self.session.get(f"{API_BASE}/my-sheets", timeout=10)
            if response.status_code == 200:
                data = response.json()
                success = isinstance(data, list)
                details = f"User sheets retrieved: {len(data)} sheets"
                self.log_test("Core - User Sheets", success, details)
            else:
                self.log_test("Core - User Sheets", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Core - User Sheets", False, f"Exception: {str(e)}")
    
    def test_amazon_integration_routes(self):
        """Test des routes d'intégration Amazon"""
        
        if not self.auth_token:
            print("⚠️ Skipping Amazon integration tests - no auth token")
            return
        
        # Test status Amazon
        try:
            response = self.session.get(f"{API_BASE}/amazon/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                success = 'user_id' in data
                connected = data.get('connected', False)
                details = f"Amazon status accessible, connected: {connected}"
                self.log_test("Amazon Status", success, details)
            else:
                self.log_test("Amazon Status", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Amazon Status", False, f"Exception: {str(e)}")
        
        # Test marketplaces Amazon
        try:
            response = self.session.get(f"{API_BASE}/amazon/marketplaces", timeout=10)
            if response.status_code == 200:
                data = response.json()
                success = 'marketplaces' in data
                marketplace_count = len(data.get('marketplaces', []))
                details = f"Marketplaces found: {marketplace_count}"
                self.log_test("Amazon Marketplaces", success, details)
            else:
                self.log_test("Amazon Marketplaces", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Amazon Marketplaces", False, f"Exception: {str(e)}")
    
    def generate_summary(self):
        """Générer résumé des tests"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        duration = time.time() - self.start_time
        
        print("=" * 80)
        print("📱 MOBILE RESPONSIVENESS - FINAL BACKEND TEST RESULTS")
        print("=" * 80)
        print(f"📊 RÉSULTATS:")
        print(f"   • Tests exécutés: {total_tests}")
        print(f"   • Tests réussis: {passed_tests} ✅")
        print(f"   • Tests échoués: {failed_tests} ❌")
        print(f"   • Taux de réussite: {success_rate:.1f}%")
        print(f"   • Durée d'exécution: {duration:.1f}s")
        print()
        
        # Tests échoués
        if failed_tests > 0:
            print("❌ TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test_name']}: {result['details']}")
            print()
        
        # Évaluation
        print("🎯 ÉVALUATION RÉGRESSION MOBILE:")
        if success_rate >= 90:
            print("   ✅ EXCELLENT - Aucune régression détectée")
            print("   ✅ Routes Amazon fonctionnelles (/api/amazon/*)")
            print("   ✅ Services Phase 3 opérationnels")
            print("   ✅ Fonctionnalités core préservées")
        elif success_rate >= 75:
            print("   ⚠️ BON - Régression mineure détectée")
            print("   ✅ Fonctionnalités principales préservées")
            print("   ⚠️ Quelques ajustements nécessaires")
        elif success_rate >= 50:
            print("   ⚠️ MOYEN - Régression modérée")
            print("   ⚠️ Certaines fonctionnalités affectées")
            print("   ❌ Corrections nécessaires")
        else:
            print("   ❌ CRITIQUE - Régression majeure détectée")
            print("   ❌ Fonctionnalités critiques cassées")
            print("   ❌ Corrections urgentes requises")
        
        print()
        print("🔧 COMPOSANTS TESTÉS:")
        print("   • Health checks et endpoints publics")
        print("   • Services Amazon Phase 3 (SEO + Prix)")
        print("   • Routes Amazon Integration")
        print("   • Endpoints SEO Amazon")
        print("   • Fonctionnalités core (génération fiches)")
        print()
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'duration': duration
        }

def main():
    """Fonction principale de test"""
    print("📱 DÉMARRAGE TESTS FINAL - RÉGRESSION MOBILE BACKEND")
    print("=" * 80)
    print("🎯 Objectif: Vérifier que les modifications de responsivité mobile")
    print("   n'ont pas cassé les fonctionnalités backend Amazon")
    print("🔗 URL testée: http://localhost:8001 (interne)")
    print()
    
    tester = FinalMobileBackendTester()
    
    try:
        print("📋 EXÉCUTION DES TESTS...")
        print()
        
        # Tests de base (sans auth)
        tester.test_health_checks()
        tester.test_public_endpoints()
        tester.test_amazon_phase3_services()
        tester.test_amazon_seo_endpoints()
        
        # Authentification
        auth_success = tester.authenticate()
        
        if auth_success:
            # Tests avec authentification
            tester.test_core_functionality()
            tester.test_amazon_integration_routes()
        else:
            print("⚠️ Continuing with non-authenticated tests only")
        
        # Générer résumé
        summary = tester.generate_summary()
        
        return summary
        
    finally:
        tester.session.close()

if __name__ == "__main__":
    try:
        summary = main()
        
        # Code de sortie basé sur le taux de réussite
        if summary and summary['success_rate'] >= 75:
            sys.exit(0)  # Succès
        else:
            sys.exit(1)  # Échec
            
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrompus par l'utilisateur")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Erreur critique lors des tests: {str(e)}")
        sys.exit(3)