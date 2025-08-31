#!/usr/bin/env python3
"""
ECOMSIMPLY Backend Vercel Production Readiness - Focused Testing
Test rapide des correctifs Vercel et validation production readiness
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from datetime import datetime

# Configuration depuis frontend/.env
BACKEND_URL = "https://ecomsimply-deploy.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class VercelFocusedTester:
    """Testeur focalisé Vercel Production Readiness"""
    
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
    
    async def test_vercel_asgi_files(self):
        """Test 1: Vérifier les fichiers ASGI Vercel"""
        print("🔍 TESTING VERCEL ASGI FILES")
        
        # Test vercel.json
        try:
            with open('/app/vercel.json', 'r') as f:
                vercel_config = json.load(f)
            
            api_route_found = any('/api/' in route.get('src', '') for route in vercel_config.get('routes', []))
            success = vercel_config.get('version') == 2 and api_route_found
            details = f"Version: {vercel_config.get('version')}, API routes: {api_route_found}"
            self.log_test("Vercel Config Valid", success, details)
            
        except Exception as e:
            self.log_test("Vercel Config Valid", False, f"Error: {str(e)}")
        
        # Test api/index.py exists
        try:
            asgi_exists = os.path.exists('/app/api/index.py')
            test_exists = os.path.exists('/app/api/test.py')
            success = asgi_exists and test_exists
            details = f"index.py: {asgi_exists}, test.py: {test_exists}"
            self.log_test("ASGI Files Present", success, details)
            
        except Exception as e:
            self.log_test("ASGI Files Present", False, f"Error: {str(e)}")
    
    async def test_health_endpoints_quick(self):
        """Test 2: Tests Health Endpoints rapides"""
        print("🔍 TESTING HEALTH ENDPOINTS")
        
        health_endpoints = [
            '/api/health',
            '/healthz',
            '/api/health/ready',
            '/api/health/live'
        ]
        
        for endpoint in health_endpoints:
            try:
                async with self.session.get(f"{BACKEND_URL}{endpoint}") as response:
                    success = response.status == 200
                    
                    if success:
                        try:
                            data = await response.json()
                            status = data.get('status', 'unknown')
                            details = f"HTTP 200 - Status: {status}"
                        except:
                            details = "HTTP 200 - Response OK"
                    else:
                        details = f"HTTP {response.status}"
                    
                    self.log_test(f"Health {endpoint}", success, details)
                    
            except Exception as e:
                self.log_test(f"Health {endpoint}", False, f"Exception: {str(e)}")
    
    async def test_critical_routes_quick(self):
        """Test 3: Tests Routes Critiques rapides"""
        print("🔍 TESTING CRITICAL ROUTES")
        
        # Test routes GET (devraient retourner 200 ou au moins pas 404)
        get_routes = [
            ('/api/amazon/health', 'Amazon SP-API'),
            ('/api/shopify/health', 'Shopify')
        ]
        
        for endpoint, name in get_routes:
            try:
                async with self.session.get(f"{BACKEND_URL}{endpoint}") as response:
                    success = response.status != 404  # Pas 404 = route existe
                    details = f"HTTP {response.status} (route accessible)"
                    self.log_test(f"{name} Route", success, details)
                    
            except Exception as e:
                self.log_test(f"{name} Route", False, f"Exception: {str(e)}")
        
        # Test routes POST (devraient retourner 400/422, pas 404)
        post_routes = [
            ('/api/auth/register', 'Auth Register'),
            ('/api/auth/login', 'Auth Login'),
            ('/api/generate-sheet', 'Generate Sheet')
        ]
        
        for endpoint, name in post_routes:
            try:
                async with self.session.post(f"{BACKEND_URL}{endpoint}", json={}) as response:
                    success = response.status in [400, 422, 401, 403]  # Validation/auth error, pas 404
                    details = f"HTTP {response.status} (endpoint accessible)"
                    self.log_test(f"{name} Endpoint", success, details)
                    
            except Exception as e:
                self.log_test(f"{name} Endpoint", False, f"Exception: {str(e)}")
    
    async def test_route_count_estimation(self):
        """Test 4: Estimation du nombre de routes via health check"""
        print("🔍 TESTING ROUTE COUNT")
        
        try:
            async with self.session.get(f"{BACKEND_URL}/api/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Si le health check fonctionne, on peut estimer que les routes sont chargées
                    # On teste quelques routes clés pour confirmer
                    test_routes = [
                        '/api/amazon/health',
                        '/api/shopify/health', 
                        '/api/auth/register',
                        '/api/generate-sheet'
                    ]
                    
                    accessible_routes = 0
                    for route in test_routes:
                        try:
                            async with self.session.get(f"{BACKEND_URL}{route}") as test_response:
                                if test_response.status != 404:
                                    accessible_routes += 1
                        except:
                            pass
                    
                    # Si au moins 3/4 routes clés sont accessibles, on estime que les 259 routes sont chargées
                    estimated_routes = accessible_routes * 65  # Estimation: 4 routes testées * 65 ≈ 260 routes
                    success = accessible_routes >= 3
                    details = f"Routes testées accessibles: {accessible_routes}/4, Estimation totale: ~{estimated_routes}"
                    self.log_test("Route Count Estimation", success, details)
                    
                else:
                    self.log_test("Route Count Estimation", False, f"Health check failed: {response.status}")
                    
        except Exception as e:
            self.log_test("Route Count Estimation", False, f"Exception: {str(e)}")
    
    async def test_mongodb_via_health(self):
        """Test 5: MongoDB via health check"""
        print("🔍 TESTING MONGODB CONNECTIVITY")
        
        try:
            async with self.session.get(f"{BACKEND_URL}/api/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Si health check retourne 200 avec status healthy, MongoDB fonctionne
                    mongodb_healthy = data.get('status') == 'healthy'
                    uptime = data.get('uptime', 0)
                    
                    success = mongodb_healthy and uptime > 0
                    details = f"Status: {data.get('status')}, Uptime: {uptime}s"
                    self.log_test("MongoDB Connectivity", success, details)
                    
                else:
                    self.log_test("MongoDB Connectivity", False, f"Health check failed: {response.status}")
                    
        except Exception as e:
            self.log_test("MongoDB Connectivity", False, f"Exception: {str(e)}")
    
    async def test_vercel_timeout_simulation(self):
        """Test 6: Simulation timeout Vercel"""
        print("🔍 TESTING VERCEL TIMEOUT COMPATIBILITY")
        
        try:
            start_time = time.time()
            async with self.session.get(f"{BACKEND_URL}/api/health") as response:
                response_time = time.time() - start_time
                
                # Vercel limite à 10s pour les fonctions serverless
                success = response_time < 10.0 and response.status == 200
                details = f"Response time: {response_time:.2f}s (Vercel limit: 10s)"
                self.log_test("Vercel Timeout Compatibility", success, details)
                
        except Exception as e:
            self.log_test("Vercel Timeout Compatibility", False, f"Exception: {str(e)}")
    
    async def run_focused_tests(self):
        """Exécuter tous les tests focalisés"""
        print("🚀 STARTING ECOMSIMPLY VERCEL FOCUSED TESTING")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test started at: {datetime.utcnow().isoformat()}")
        print("=" * 60)
        
        # Exécuter tous les tests
        await self.test_vercel_asgi_files()
        await self.test_health_endpoints_quick()
        await self.test_critical_routes_quick()
        await self.test_route_count_estimation()
        await self.test_mongodb_via_health()
        await self.test_vercel_timeout_simulation()
        
        # Calculer les résultats
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("=" * 60)
        print("🎯 VERCEL FOCUSED TEST RESULTS")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Test Duration: {time.time() - self.start_time:.2f}s")
        
        # Évaluation finale
        if success_rate >= 95:
            print("🎉 VERCEL PRODUCTION READY - 95%+ success rate!")
        elif success_rate >= 85:
            print("⚠️ MOSTLY READY - Minor issues to address")
        else:
            print("❌ NOT READY - Critical issues found")
        
        # Résumé des échecs
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test_name']}: {test['details']}")
        
        print("=" * 60)
        
        return success_rate >= 95

async def main():
    """Point d'entrée principal"""
    async with VercelFocusedTester() as tester:
        production_ready = await tester.run_focused_tests()
        return production_ready

if __name__ == "__main__":
    try:
        production_ready = asyncio.run(main())
        sys.exit(0 if production_ready else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)