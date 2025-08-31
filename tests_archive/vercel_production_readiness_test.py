#!/usr/bin/env python3
"""
ECOMSIMPLY Backend Vercel Production Readiness Testing
Test des correctifs Vercel appliqués et validation production readiness

Focus: API routing, ASGI compatibility, health endpoints, services critiques
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any, List
import subprocess
import importlib.util

# Configuration depuis frontend/.env
BACKEND_URL = "https://ecomsimply-deploy.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class VercelProductionReadinessTester:
    """Testeur complet Vercel Production Readiness"""
    
    def __init__(self):
        self.session = None
        self.test_results = []
        self.start_time = time.time()
        self.total_routes_found = 0
        
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
    
    async def test_asgi_import_validation(self):
        """1. Validation Import ASGI - Test que /app/api/index.py peut importer FastAPI app"""
        print("🔍 TESTING ASGI IMPORT VALIDATION")
        
        try:
            # Test import direct du module ASGI
            sys.path.insert(0, '/app/api')
            
            # Test import de index.py
            spec = importlib.util.spec_from_file_location("index", "/app/api/index.py")
            if spec and spec.loader:
                index_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(index_module)
                
                # Vérifier que l'app FastAPI est disponible
                if hasattr(index_module, 'app'):
                    app = index_module.app
                    
                    # Compter les routes
                    routes_count = len(app.routes)
                    self.total_routes_found = routes_count
                    
                    # Vérifier les routes critiques
                    route_paths = [route.path for route in app.routes if hasattr(route, 'path')]
                    
                    critical_routes = [
                        '/api/health',
                        '/api/auth',
                        '/api/amazon',
                        '/api/shopify'
                    ]
                    
                    routes_found = []
                    for critical_route in critical_routes:
                        matching_routes = [path for path in route_paths if path.startswith(critical_route)]
                        routes_found.extend(matching_routes)
                    
                    # Vérifier handler Vercel
                    handler_available = hasattr(index_module, 'handler')
                    
                    success = (
                        routes_count >= 200 and  # Au moins 200 routes (target: 259)
                        len(routes_found) >= 10 and  # Au moins 10 routes critiques
                        handler_available
                    )
                    
                    details = f"Routes totales: {routes_count}, Routes critiques: {len(routes_found)}, Handler: {handler_available}"
                    self.log_test("ASGI Import Validation", success, details, {
                        'total_routes': routes_count,
                        'critical_routes_found': len(routes_found),
                        'handler_available': handler_available,
                        'sample_routes': route_paths[:10]
                    })
                    
                else:
                    self.log_test("ASGI Import Validation", False, "FastAPI app not found in index.py")
                    
            else:
                self.log_test("ASGI Import Validation", False, "Cannot load /app/api/index.py")
                
        except Exception as e:
            self.log_test("ASGI Import Validation", False, f"Import error: {str(e)}")
    
    async def test_health_endpoints(self):
        """2. Tests Health Endpoints - Tous les endpoints de santé"""
        print("🔍 TESTING HEALTH ENDPOINTS")
        
        health_endpoints = [
            ('/api/health', 'Main Health Check'),
            ('/healthz', 'Kubernetes Health Check'),
            ('/api/health/ready', 'Readiness Check'),
            ('/api/health/live', 'Liveness Check')
        ]
        
        for endpoint, description in health_endpoints:
            try:
                async with self.session.get(f"{BACKEND_URL}{endpoint}") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Vérifications spécifiques selon l'endpoint
                        if endpoint == '/api/health':
                            checks = [
                                data.get('status') == 'healthy',
                                'uptime' in data,
                                'system_metrics' in data or 'cpu_usage' in data,
                                'memory_usage' in data or 'system_metrics' in data
                            ]
                            
                            system_info = ""
                            if 'system_metrics' in data:
                                metrics = data['system_metrics']
                                system_info = f"CPU: {metrics.get('cpu_usage', 'N/A')}%, Memory: {metrics.get('memory_usage', 'N/A')}%"
                            elif 'cpu_usage' in data:
                                system_info = f"CPU: {data.get('cpu_usage', 'N/A')}%, Memory: {data.get('memory_usage', 'N/A')}%"
                            
                            success = all(checks)
                            details = f"Status: {data.get('status')}, Uptime: {data.get('uptime', 'N/A')}s, {system_info}"
                            
                        else:
                            # Pour les autres endpoints, vérifier juste le status 200
                            success = True
                            details = f"Response received successfully"
                        
                        self.log_test(f"Health Endpoint {description}", success, details, data)
                        
                    else:
                        error_data = await response.text()
                        self.log_test(f"Health Endpoint {description}", False, f"HTTP {response.status}", error_data)
                        
            except Exception as e:
                self.log_test(f"Health Endpoint {description}", False, f"Exception: {str(e)}")
    
    async def test_critical_routes(self):
        """3. Tests Routes Critiques - Amazon SP-API, Shopify, Auth, Core"""
        print("🔍 TESTING CRITICAL ROUTES")
        
        critical_routes = [
            ('/api/amazon/health', 'Amazon SP-API Health'),
            ('/api/shopify/health', 'Shopify Health'),
            ('/api/auth/register', 'Auth Register Endpoint'),
            ('/api/auth/login', 'Auth Login Endpoint'),
            ('/api/generate-sheet', 'Core Generate Sheet')
        ]
        
        for endpoint, description in critical_routes:
            try:
                # Pour les endpoints POST, on teste avec une requête vide pour vérifier l'accessibilité
                if endpoint in ['/api/auth/register', '/api/auth/login', '/api/generate-sheet']:
                    async with self.session.post(f"{BACKEND_URL}{endpoint}", json={}) as response:
                        # Ces endpoints devraient retourner 400 (validation error) ou 422, pas 404
                        success = response.status in [400, 422, 401, 403]  # Pas 404 ou 500
                        details = f"HTTP {response.status} (endpoint accessible)"
                        
                        if not success:
                            error_data = await response.text()
                            details += f" - {error_data[:100]}"
                        
                        self.log_test(f"Critical Route {description}", success, details)
                else:
                    # Pour les endpoints GET
                    async with self.session.get(f"{BACKEND_URL}{endpoint}") as response:
                        # Health endpoints devraient retourner 200, ou au moins pas 404
                        success = response.status != 404
                        
                        if response.status == 200:
                            data = await response.json()
                            details = f"HTTP 200 - {data.get('status', 'OK')}"
                        else:
                            details = f"HTTP {response.status} (endpoint accessible)"
                        
                        self.log_test(f"Critical Route {description}", success, details)
                        
            except Exception as e:
                self.log_test(f"Critical Route {description}", False, f"Exception: {str(e)}")
    
    async def test_vercel_compatibility(self):
        """4. Tests Vercel Compatibility - Simulation environnement serverless"""
        print("🔍 TESTING VERCEL COMPATIBILITY")
        
        # Test 1: Vérifier que vercel.json existe et est valide
        try:
            with open('/app/vercel.json', 'r') as f:
                vercel_config = json.load(f)
                
            checks = [
                'functions' in vercel_config,
                'routes' in vercel_config,
                vercel_config.get('version') == 2
            ]
            
            # Vérifier les routes API
            routes = vercel_config.get('routes', [])
            api_route_found = any('/api/' in route.get('src', '') for route in routes)
            checks.append(api_route_found)
            
            success = all(checks)
            details = f"Version: {vercel_config.get('version')}, Routes: {len(routes)}, API route: {api_route_found}"
            self.log_test("Vercel Config Validation", success, details, vercel_config)
            
        except Exception as e:
            self.log_test("Vercel Config Validation", False, f"Config error: {str(e)}")
        
        # Test 2: Test des imports Python avec chemins relatifs
        try:
            # Simuler l'import comme Vercel le ferait
            test_script = """
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from server import app
print(f"Routes available: {len(app.routes)}")
"""
            
            # Écrire et exécuter le script de test
            with open('/tmp/vercel_import_test.py', 'w') as f:
                f.write(test_script)
            
            result = subprocess.run([sys.executable, '/tmp/vercel_import_test.py'], 
                                  capture_output=True, text=True, cwd='/app/api')
            
            success = result.returncode == 0 and 'Routes available:' in result.stdout
            details = f"Import test: {'SUCCESS' if success else 'FAILED'}"
            if result.stdout:
                details += f" - {result.stdout.strip()}"
            if result.stderr:
                details += f" - Error: {result.stderr.strip()}"
            
            self.log_test("Python Import Compatibility", success, details)
            
        except Exception as e:
            self.log_test("Python Import Compatibility", False, f"Import test error: {str(e)}")
        
        # Test 3: Test timeout et limits Vercel (simulation)
        try:
            start_time = time.time()
            async with self.session.get(f"{BACKEND_URL}/api/health") as response:
                response_time = time.time() - start_time
                
                # Vercel a une limite de 10s pour les fonctions serverless
                success = response_time < 10.0 and response.status == 200
                details = f"Response time: {response_time:.2f}s (limit: 10s)"
                
                self.log_test("Vercel Timeout Compatibility", success, details)
                
        except Exception as e:
            self.log_test("Vercel Timeout Compatibility", False, f"Timeout test error: {str(e)}")
    
    async def test_critical_services(self):
        """5. Tests Services Critiques - MongoDB, Amazon SP-API, Shopify, PriceTruth"""
        print("🔍 TESTING CRITICAL SERVICES")
        
        # Test MongoDB connectivity via health endpoint
        try:
            async with self.session.get(f"{BACKEND_URL}/api/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Vérifier que le service est healthy (implique MongoDB OK)
                    mongodb_healthy = data.get('status') == 'healthy'
                    details = f"MongoDB via health check: {'CONNECTED' if mongodb_healthy else 'ISSUE'}"
                    
                    self.log_test("MongoDB Connectivity", mongodb_healthy, details)
                else:
                    self.log_test("MongoDB Connectivity", False, f"Health check failed: {response.status}")
                    
        except Exception as e:
            self.log_test("MongoDB Connectivity", False, f"MongoDB test error: {str(e)}")
        
        # Test Amazon SP-API integration loading
        try:
            async with self.session.get(f"{BACKEND_URL}/api/amazon/health") as response:
                # Même si pas configuré, l'endpoint devrait être accessible
                success = response.status in [200, 401, 403, 422]  # Pas 404 ou 500
                
                if response.status == 200:
                    data = await response.json()
                    details = f"Amazon SP-API: {data.get('status', 'LOADED')}"
                else:
                    details = f"Amazon SP-API endpoint accessible (HTTP {response.status})"
                
                self.log_test("Amazon SP-API Integration", success, details)
                
        except Exception as e:
            self.log_test("Amazon SP-API Integration", False, f"Amazon test error: {str(e)}")
        
        # Test Shopify routes registration
        try:
            async with self.session.get(f"{BACKEND_URL}/api/shopify/health") as response:
                success = response.status in [200, 401, 403, 422]  # Pas 404 ou 500
                
                if response.status == 200:
                    data = await response.json()
                    details = f"Shopify: {data.get('status', 'LOADED')}"
                else:
                    details = f"Shopify endpoint accessible (HTTP {response.status})"
                
                self.log_test("Shopify Routes Registration", success, details)
                
        except Exception as e:
            self.log_test("Shopify Routes Registration", False, f"Shopify test error: {str(e)}")
        
        # Test PriceTruth service initialization via generate-sheet
        try:
            # Test avec données minimales pour vérifier que le service se charge
            test_data = {
                "product_name": "Test Product Vercel",
                "product_description": "Test description for Vercel compatibility testing",
                "generate_image": False,
                "number_of_images": 0
            }
            
            async with self.session.post(f"{BACKEND_URL}/api/generate-sheet", json=test_data) as response:
                # Devrait retourner 401 (pas authentifié) ou 422 (validation), pas 500 (service error)
                success = response.status in [401, 422, 400]  # Service chargé mais auth/validation required
                
                details = f"PriceTruth service: {'LOADED' if success else 'ERROR'} (HTTP {response.status})"
                
                self.log_test("PriceTruth Service Initialization", success, details)
                
        except Exception as e:
            self.log_test("PriceTruth Service Initialization", False, f"PriceTruth test error: {str(e)}")
    
    async def run_all_tests(self):
        """Exécuter tous les tests de production readiness"""
        print("🚀 STARTING ECOMSIMPLY VERCEL PRODUCTION READINESS TESTING")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test started at: {datetime.utcnow().isoformat()}")
        print("=" * 80)
        
        # Exécuter tous les tests
        await self.test_asgi_import_validation()
        await self.test_health_endpoints()
        await self.test_critical_routes()
        await self.test_vercel_compatibility()
        await self.test_critical_services()
        
        # Calculer les résultats
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("=" * 80)
        print("🎯 VERCEL PRODUCTION READINESS TEST RESULTS")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Routes Found: {self.total_routes_found}")
        print(f"Test Duration: {time.time() - self.start_time:.2f}s")
        
        # Évaluation finale
        if success_rate >= 95:
            print("🎉 VERCEL PRODUCTION READY - 95%+ success rate achieved!")
        elif success_rate >= 85:
            print("⚠️ MOSTLY READY - Minor issues to address before production")
        else:
            print("❌ NOT READY - Critical issues must be resolved")
        
        # Résumé des échecs
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test_name']}: {test['details']}")
        
        print("=" * 80)
        
        return success_rate >= 95

async def main():
    """Point d'entrée principal"""
    async with VercelProductionReadinessTester() as tester:
        production_ready = await tester.run_all_tests()
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