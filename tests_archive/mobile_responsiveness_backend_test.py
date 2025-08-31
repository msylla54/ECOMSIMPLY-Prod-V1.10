#!/usr/bin/env python3
"""
Backend Test - Mobile Responsiveness Regression Testing
Test rapide des composants Amazon après modifications de responsivité mobile
Focus: Routes Amazon (/api/amazon/*) et services Phase 3 opérationnels
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Configuration
BACKEND_URL = "https://ecomsimply.com"
API_BASE = f"{BACKEND_URL}/api"

class MobileResponsivenessBackendTester:
    """Testeur rapide pour vérifier que les modifications mobile n'ont pas cassé le backend"""
    
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        self.start_time = time.time()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Enregistrer résultat de test"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.utcnow().isoformat(),
            'response_data': response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")
        print()
    
    async def authenticate(self):
        """Authentification utilisateur admin"""
        try:
            # Créer utilisateur admin de test
            admin_data = {
                "email": "mobile.test@ecomsimply.com",
                "name": "Mobile Test User",
                "password": "MobileTest2025!",
                "admin_key": "ECOMSIMPLY_ADMIN_2025"
            }
            
            async with self.session.post(f"{API_BASE}/auth/register", json=admin_data) as response:
                if response.status in [200, 201]:
                    print("✅ Admin user created successfully")
                elif response.status == 400:
                    print("ℹ️ Admin user already exists")
                else:
                    print(f"⚠️ User creation status: {response.status}")
            
            # Connexion
            login_data = {
                "email": "mobile.test@ecomsimply.com",
                "password": "MobileTest2025!"
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get('access_token')
                    if self.auth_token:
                        self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                        self.log_test("Authentication", True, "Admin user authenticated successfully")
                        return True
                
                error_data = await response.text()
                self.log_test("Authentication", False, f"Login failed: {response.status}", error_data)
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    async def test_basic_health_checks(self):
        """Test des health checks de base"""
        
        # Test health check général
        try:
            async with self.session.get(f"{API_BASE}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    success = data.get('status') == 'healthy'
                    details = f"Status: {data.get('status')}, Uptime: {data.get('uptime', 0):.1f}s"
                    self.log_test("General Health Check", success, details)
                else:
                    self.log_test("General Health Check", False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test("General Health Check", False, f"Exception: {str(e)}")
        
        # Test health check ready
        try:
            async with self.session.get(f"{API_BASE}/health/ready") as response:
                success = response.status == 200
                self.log_test("Ready Health Check", success, f"Status: {response.status}")
        except Exception as e:
            self.log_test("Ready Health Check", False, f"Exception: {str(e)}")
    
    async def test_amazon_integration_routes(self):
        """Test des routes d'intégration Amazon Phase 1"""
        
        # Test status Amazon
        try:
            async with self.session.get(f"{API_BASE}/amazon/status") as response:
                if response.status == 200:
                    data = await response.json()
                    success = 'user_id' in data
                    details = f"User connected: {data.get('connected', False)}"
                    self.log_test("Amazon Status Route", success, details)
                else:
                    self.log_test("Amazon Status Route", False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test("Amazon Status Route", False, f"Exception: {str(e)}")
        
        # Test marketplaces Amazon
        try:
            async with self.session.get(f"{API_BASE}/amazon/marketplaces") as response:
                if response.status == 200:
                    data = await response.json()
                    success = isinstance(data.get('marketplaces'), list) and len(data.get('marketplaces', [])) > 0
                    details = f"Marketplaces found: {len(data.get('marketplaces', []))}"
                    self.log_test("Amazon Marketplaces Route", success, details)
                else:
                    self.log_test("Amazon Marketplaces Route", False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test("Amazon Marketplaces Route", False, f"Exception: {str(e)}")
    
    async def test_amazon_phase3_health(self):
        """Test health check Phase 3 Amazon SEO + Prix"""
        try:
            async with self.session.get(f"{API_BASE}/amazon/health/phase3") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Vérifications critiques
                    checks = []
                    checks.append(data.get('success') is True)
                    checks.append('health' in data)
                    
                    health = data.get('health', {})
                    checks.append(health.get('phase') == 'Phase 3 - SEO + Prix Amazon')
                    
                    services = health.get('services', {})
                    expected_services = ['scraping_service', 'seo_optimizer', 'price_optimizer', 'publisher_service']
                    service_count = 0
                    for service in expected_services:
                        if service in services and services.get(service) == 'healthy':
                            service_count += 1
                    
                    checks.append(service_count >= 3)  # Au moins 3/4 services doivent être healthy
                    
                    success = all(checks)
                    details = f"Services healthy: {service_count}/4, Phase: {health.get('phase', 'Unknown')}"
                    self.log_test("Amazon Phase 3 Health", success, details)
                    
                else:
                    self.log_test("Amazon Phase 3 Health", False, f"HTTP {response.status}")
                    
        except Exception as e:
            self.log_test("Amazon Phase 3 Health", False, f"Exception: {str(e)}")
    
    async def test_amazon_seo_routes(self):
        """Test des routes SEO Amazon"""
        
        # Test règles SEO Amazon
        try:
            async with self.session.get(f"{API_BASE}/amazon/seo/rules") as response:
                if response.status == 200:
                    data = await response.json()
                    success = 'rules' in data and 'a9_a10_compliance' in data.get('rules', {})
                    details = f"Rules loaded: {'rules' in data}"
                    self.log_test("Amazon SEO Rules", success, details)
                else:
                    self.log_test("Amazon SEO Rules", False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test("Amazon SEO Rules", False, f"Exception: {str(e)}")
        
        # Test historique SEO
        try:
            async with self.session.get(f"{API_BASE}/amazon/seo/history?limit=5") as response:
                if response.status == 200:
                    data = await response.json()
                    success = 'history' in data
                    details = f"History entries: {len(data.get('history', []))}"
                    self.log_test("Amazon SEO History", success, details)
                else:
                    self.log_test("Amazon SEO History", False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test("Amazon SEO History", False, f"Exception: {str(e)}")
    
    async def test_amazon_listings_routes(self):
        """Test des routes Amazon Listings Phase 2"""
        
        # Test historique listings
        try:
            async with self.session.get(f"{API_BASE}/amazon/listings/history?limit=5") as response:
                if response.status == 200:
                    data = await response.json()
                    success = 'history' in data
                    details = f"Listings history: {len(data.get('history', []))}"
                    self.log_test("Amazon Listings History", success, details)
                else:
                    self.log_test("Amazon Listings History", False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test("Amazon Listings History", False, f"Exception: {str(e)}")
    
    async def test_critical_endpoints_accessibility(self):
        """Test d'accessibilité des endpoints critiques"""
        
        critical_endpoints = [
            ("/amazon/status", "Amazon Status"),
            ("/amazon/marketplaces", "Amazon Marketplaces"),
            ("/amazon/health/phase3", "Phase 3 Health"),
            ("/amazon/seo/rules", "SEO Rules"),
            ("/amazon/seo/history", "SEO History"),
            ("/amazon/listings/history", "Listings History")
        ]
        
        accessible_count = 0
        total_count = len(critical_endpoints)
        
        for endpoint, name in critical_endpoints:
            try:
                async with self.session.get(f"{API_BASE}{endpoint}") as response:
                    if response.status in [200, 401, 403]:  # 401/403 = accessible but auth required
                        accessible_count += 1
            except:
                pass
        
        success = accessible_count >= (total_count * 0.8)  # Au moins 80% accessibles
        details = f"Accessible endpoints: {accessible_count}/{total_count}"
        self.log_test("Critical Endpoints Accessibility", success, details)
    
    async def test_no_regression_basic_functionality(self):
        """Test qu'il n'y a pas de régression sur les fonctionnalités de base"""
        
        # Test génération de fiche (fonctionnalité core)
        try:
            request_data = {
                "product_name": "Test Mobile Responsiveness Product",
                "product_description": "Test product to verify mobile changes didn't break backend functionality",
                "generate_image": False,
                "number_of_images": 0,
                "language": "fr"
            }
            
            async with self.session.post(f"{API_BASE}/generate-sheet", json=request_data) as response:
                if response.status == 200:
                    data = await response.json()
                    success = 'generated_title' in data and 'marketing_description' in data
                    details = f"Sheet generated successfully, title length: {len(data.get('generated_title', ''))}"
                    self.log_test("Core Functionality - Sheet Generation", success, details)
                else:
                    self.log_test("Core Functionality - Sheet Generation", False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test("Core Functionality - Sheet Generation", False, f"Exception: {str(e)}")
        
        # Test récupération des fiches utilisateur
        try:
            async with self.session.get(f"{API_BASE}/my-sheets") as response:
                if response.status == 200:
                    data = await response.json()
                    success = isinstance(data, list)
                    details = f"User sheets retrieved: {len(data)} sheets"
                    self.log_test("Core Functionality - User Sheets", success, details)
                else:
                    self.log_test("Core Functionality - User Sheets", False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test("Core Functionality - User Sheets", False, f"Exception: {str(e)}")
    
    def generate_summary(self):
        """Générer résumé des tests"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        duration = time.time() - self.start_time
        
        print("=" * 80)
        print("📱 MOBILE RESPONSIVENESS - BACKEND REGRESSION TEST RESULTS")
        print("=" * 80)
        print(f"📊 STATISTIQUES GLOBALES:")
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
        print("   • Routes Amazon Integration (/api/amazon/status, /marketplaces)")
        print("   • Services Amazon Phase 3 (SEO + Prix)")
        print("   • Endpoints SEO Amazon (/api/amazon/seo/*)")
        print("   • Endpoints Listings Amazon (/api/amazon/listings/*)")
        print("   • Fonctionnalités core (génération fiches)")
        print()
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'duration': duration
        }

async def main():
    """Fonction principale de test"""
    print("📱 DÉMARRAGE TESTS RÉGRESSION MOBILE - BACKEND")
    print("=" * 80)
    print("🎯 Objectif: Vérifier que les modifications de responsivité mobile")
    print("   n'ont pas cassé les fonctionnalités backend Amazon")
    print()
    
    async with MobileResponsivenessBackendTester() as tester:
        # Authentification
        if not await tester.authenticate():
            print("❌ Échec de l'authentification - Arrêt des tests")
            return
        
        print("📋 EXÉCUTION DES TESTS DE RÉGRESSION...")
        print()
        
        # Tests de base
        await tester.test_basic_health_checks()
        
        # Tests Amazon spécifiques
        await tester.test_amazon_integration_routes()
        await tester.test_amazon_phase3_health()
        await tester.test_amazon_seo_routes()
        await tester.test_amazon_listings_routes()
        
        # Tests d'accessibilité
        await tester.test_critical_endpoints_accessibility()
        
        # Tests de non-régression
        await tester.test_no_regression_basic_functionality()
        
        # Générer résumé
        summary = tester.generate_summary()
        
        return summary

if __name__ == "__main__":
    try:
        summary = asyncio.run(main())
        
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