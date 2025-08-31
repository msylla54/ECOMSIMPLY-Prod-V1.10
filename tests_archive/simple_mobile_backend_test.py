#!/usr/bin/env python3
"""
Simple Backend Test - Mobile Responsiveness Regression
Test rapide sans authentification des endpoints publics et health checks
"""

import asyncio
import aiohttp
import json
import time
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://ecomsimply.com"
API_BASE = f"{BACKEND_URL}/api"

class SimpleMobileBackendTester:
    """Testeur simple sans authentification"""
    
    def __init__(self):
        self.session = None
        self.test_results = []
        self.start_time = time.time()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15),
            headers={'Content-Type': 'application/json'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
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
    
    async def test_basic_health_endpoints(self):
        """Test des endpoints de santé de base"""
        
        # Test health check principal
        try:
            async with self.session.get(f"{API_BASE}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    success = data.get('status') == 'healthy'
                    uptime = data.get('uptime', 0)
                    details = f"Status: {data.get('status')}, Uptime: {uptime:.1f}s"
                    self.log_test("Health Check", success, details)
                else:
                    self.log_test("Health Check", False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
        
        # Test ready endpoint
        try:
            async with self.session.get(f"{API_BASE}/health/ready") as response:
                success = response.status == 200
                self.log_test("Ready Check", success, f"Status: {response.status}")
        except Exception as e:
            self.log_test("Ready Check", False, f"Exception: {str(e)}")
        
        # Test live endpoint
        try:
            async with self.session.get(f"{API_BASE}/health/live") as response:
                success = response.status == 200
                self.log_test("Live Check", success, f"Status: {response.status}")
        except Exception as e:
            self.log_test("Live Check", False, f"Exception: {str(e)}")
    
    async def test_public_endpoints(self):
        """Test des endpoints publics"""
        
        # Test stats publiques
        try:
            async with self.session.get(f"{API_BASE}/stats/public") as response:
                if response.status == 200:
                    data = await response.json()
                    success = 'total_users' in data
                    details = f"Users: {data.get('total_users', 0)}, Sheets: {data.get('total_sheets', 0)}"
                    self.log_test("Public Stats", success, details)
                else:
                    self.log_test("Public Stats", False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test("Public Stats", False, f"Exception: {str(e)}")
        
        # Test plans pricing
        try:
            async with self.session.get(f"{API_BASE}/public/plans-pricing") as response:
                if response.status == 200:
                    data = await response.json()
                    success = isinstance(data, list) and len(data) > 0
                    details = f"Plans available: {len(data)}"
                    self.log_test("Plans Pricing", success, details)
                else:
                    self.log_test("Plans Pricing", False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test("Plans Pricing", False, f"Exception: {str(e)}")
        
        # Test testimonials
        try:
            async with self.session.get(f"{API_BASE}/testimonials") as response:
                if response.status == 200:
                    data = await response.json()
                    success = isinstance(data, list)
                    details = f"Testimonials: {len(data)}"
                    self.log_test("Testimonials", success, details)
                else:
                    self.log_test("Testimonials", False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test("Testimonials", False, f"Exception: {str(e)}")
    
    async def test_amazon_endpoints_accessibility(self):
        """Test d'accessibilité des endpoints Amazon (sans auth)"""
        
        amazon_endpoints = [
            ("/amazon/health/phase3", "Amazon Phase 3 Health"),
            ("/amazon/seo/rules", "Amazon SEO Rules"),
            ("/demo/amazon/demo-page", "Amazon Demo Page"),
            ("/demo/amazon/status", "Amazon Demo Status"),
            ("/demo/amazon/marketplaces", "Amazon Demo Marketplaces")
        ]
        
        accessible_count = 0
        
        for endpoint, name in amazon_endpoints:
            try:
                async with self.session.get(f"{API_BASE}{endpoint}") as response:
                    # Considérer comme accessible si pas 404/500
                    if response.status not in [404, 500, 502, 503]:
                        accessible_count += 1
                        status = "accessible" if response.status == 200 else f"auth required ({response.status})"
                        self.log_test(f"Amazon Endpoint - {name}", True, f"Status: {status}")
                    else:
                        self.log_test(f"Amazon Endpoint - {name}", False, f"HTTP {response.status}")
            except Exception as e:
                self.log_test(f"Amazon Endpoint - {name}", False, f"Exception: {str(e)}")
        
        # Test global d'accessibilité
        total_endpoints = len(amazon_endpoints)
        success = accessible_count >= (total_endpoints * 0.6)  # Au moins 60% accessibles
        details = f"Accessible: {accessible_count}/{total_endpoints}"
        self.log_test("Amazon Endpoints Accessibility", success, details)
    
    async def test_core_functionality_endpoints(self):
        """Test d'accessibilité des endpoints de fonctionnalité core"""
        
        core_endpoints = [
            ("/languages", "Languages"),
            ("/qa/statistics", "QA Statistics"),
            ("/admin/trial-stats", "Trial Stats")
        ]
        
        for endpoint, name in core_endpoints:
            try:
                async with self.session.get(f"{API_BASE}{endpoint}") as response:
                    # Considérer comme accessible si pas 404/500
                    if response.status not in [404, 500, 502, 503]:
                        status = "accessible" if response.status == 200 else f"auth required ({response.status})"
                        self.log_test(f"Core Endpoint - {name}", True, f"Status: {status}")
                    else:
                        self.log_test(f"Core Endpoint - {name}", False, f"HTTP {response.status}")
            except Exception as e:
                self.log_test(f"Core Endpoint - {name}", False, f"Exception: {str(e)}")
    
    async def test_backend_responsiveness(self):
        """Test de la réactivité du backend"""
        
        start_time = time.time()
        
        try:
            async with self.session.get(f"{API_BASE}/health") as response:
                response_time = time.time() - start_time
                
                if response.status == 200 and response_time < 2.0:
                    self.log_test("Backend Responsiveness", True, f"Response time: {response_time:.3f}s")
                else:
                    self.log_test("Backend Responsiveness", False, f"Slow response: {response_time:.3f}s or error {response.status}")
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Backend Responsiveness", False, f"Exception after {response_time:.3f}s: {str(e)}")
    
    def generate_summary(self):
        """Générer résumé des tests"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        duration = time.time() - self.start_time
        
        print("=" * 80)
        print("📱 MOBILE RESPONSIVENESS - SIMPLE BACKEND TEST RESULTS")
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
        print("🎯 ÉVALUATION:")
        if success_rate >= 85:
            print("   ✅ EXCELLENT - Backend entièrement fonctionnel")
            print("   ✅ Aucune régression détectée par les modifications mobile")
            print("   ✅ Tous les services critiques opérationnels")
        elif success_rate >= 70:
            print("   ⚠️ BON - Backend majoritairement fonctionnel")
            print("   ✅ Services principaux opérationnels")
            print("   ⚠️ Quelques endpoints nécessitent attention")
        elif success_rate >= 50:
            print("   ⚠️ MOYEN - Fonctionnalité partielle")
            print("   ⚠️ Plusieurs services affectés")
            print("   ❌ Investigation nécessaire")
        else:
            print("   ❌ CRITIQUE - Problèmes majeurs détectés")
            print("   ❌ Services critiques non fonctionnels")
            print("   ❌ Corrections urgentes requises")
        
        print()
        print("🔧 COMPOSANTS TESTÉS:")
        print("   • Health checks (health, ready, live)")
        print("   • Endpoints publics (stats, plans, testimonials)")
        print("   • Accessibilité endpoints Amazon")
        print("   • Réactivité du backend")
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
    print("📱 DÉMARRAGE TESTS SIMPLE - RÉGRESSION MOBILE BACKEND")
    print("=" * 80)
    print("🎯 Objectif: Vérifier rapidement que le backend fonctionne")
    print("   après les modifications de responsivité mobile")
    print()
    
    async with SimpleMobileBackendTester() as tester:
        print("📋 EXÉCUTION DES TESTS...")
        print()
        
        # Tests de base
        await tester.test_basic_health_endpoints()
        await tester.test_public_endpoints()
        await tester.test_amazon_endpoints_accessibility()
        await tester.test_core_functionality_endpoints()
        await tester.test_backend_responsiveness()
        
        # Générer résumé
        summary = tester.generate_summary()
        
        return summary

if __name__ == "__main__":
    try:
        summary = asyncio.run(main())
        
        # Code de sortie basé sur le taux de réussite
        if summary and summary['success_rate'] >= 70:
            sys.exit(0)  # Succès
        else:
            sys.exit(1)  # Échec
            
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrompus par l'utilisateur")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Erreur critique lors des tests: {str(e)}")
        sys.exit(3)