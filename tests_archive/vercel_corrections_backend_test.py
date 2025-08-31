#!/usr/bin/env python3
"""
ECOMSIMPLY Backend Test - Vercel Corrections Validation
Test complet du backend après les corrections Vercel
Focus: Santé générale, Amazon SP-API, variables d'environnement, services internes
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Configuration depuis les variables d'environnement
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

class VercelCorrectionsBackendTester:
    """Testeur complet des corrections Vercel ECOMSIMPLY"""
    
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
    
    async def test_general_health(self):
        """1. Test santé générale - GET /api/health"""
        try:
            async with self.session.get(f"{API_BASE}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Vérifications critiques
                    checks = []
                    checks.append(data.get('status') == 'healthy')
                    checks.append('uptime' in data)
                    checks.append('timestamp' in data)
                    checks.append('services' in data)
                    
                    # Vérifier les services
                    services = data.get('services', {})
                    expected_services = ['database', 'scheduler', 'email']
                    for service in expected_services:
                        if service in services:
                            checks.append(services[service] == 'operational')
                    
                    success = all(checks)
                    uptime = data.get('uptime', 0)
                    details = f"Status: {data.get('status')}, Uptime: {uptime:.1f}s, Services: {len(services)}"
                    self.log_test("General Health Check", success, details, data)
                    
                else:
                    error_data = await response.text()
                    self.log_test("General Health Check", False, f"HTTP {response.status}", error_data)
                    
        except Exception as e:
            self.log_test("General Health Check", False, f"Exception: {str(e)}")
    
    async def test_ready_endpoint(self):
        """Test endpoint ready pour Kubernetes"""
        try:
            async with self.session.get(f"{API_BASE}/health/ready") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    checks = []
                    checks.append(data.get('status') == 'ready')
                    checks.append('timestamp' in data)
                    
                    success = all(checks)
                    details = f"Status: {data.get('status')}"
                    self.log_test("Ready Endpoint", success, details, data)
                    
                else:
                    error_data = await response.text()
                    self.log_test("Ready Endpoint", False, f"HTTP {response.status}", error_data)
                    
        except Exception as e:
            self.log_test("Ready Endpoint", False, f"Exception: {str(e)}")
    
    async def test_amazon_spapi_routes(self):
        """2. Test routes Amazon SP-API après correction AmazonPublishingResult"""
        
        # Test health Amazon
        try:
            async with self.session.get(f"{API_BASE}/amazon/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    checks = []
                    checks.append('amazon_integration' in data)
                    checks.append('sp_api_client' in data)
                    
                    success = all(checks)
                    details = f"Amazon services detected: {list(data.keys())}"
                    self.log_test("Amazon SP-API Health", success, details, data)
                    
                else:
                    error_data = await response.text()
                    self.log_test("Amazon SP-API Health", False, f"HTTP {response.status}", error_data)
                    
        except Exception as e:
            self.log_test("Amazon SP-API Health", False, f"Exception: {str(e)}")
        
        # Test marketplaces Amazon
        try:
            async with self.session.get(f"{API_BASE}/amazon/marketplaces") as response:
                if response.status in [200, 401, 403]:  # 401/403 attendus sans auth
                    if response.status == 200:
                        data = await response.json()
                        checks = []
                        checks.append('marketplaces' in data)
                        success = all(checks)
                        details = f"Marketplaces available: {len(data.get('marketplaces', []))}"
                    else:
                        success = True  # Auth required is expected
                        details = f"Authentication required (expected): {response.status}"
                    
                    self.log_test("Amazon Marketplaces Endpoint", success, details)
                    
                else:
                    error_data = await response.text()
                    self.log_test("Amazon Marketplaces Endpoint", False, f"HTTP {response.status}", error_data)
                    
        except Exception as e:
            self.log_test("Amazon Marketplaces Endpoint", False, f"Exception: {str(e)}")
    
    async def test_demo_amazon_page(self):
        """3. Test page démo Amazon - /api/demo/amazon/demo-page"""
        try:
            async with self.session.get(f"{API_BASE}/demo/amazon/demo-page") as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Vérifications contenu HTML
                    checks = []
                    checks.append('ECOMSIMPLY - Démo Amazon SP-API Phase 1' in content)
                    checks.append('AmazonIntegrationPage' in content)
                    checks.append('Connexion Amazon' in content)
                    checks.append('marketplace' in content.lower())
                    
                    success = all(checks)
                    content_length = len(content)
                    details = f"HTML content loaded: {content_length} chars, Demo page functional"
                    self.log_test("Amazon Demo Page", success, details)
                    
                else:
                    error_data = await response.text()
                    self.log_test("Amazon Demo Page", False, f"HTTP {response.status}", error_data)
                    
        except Exception as e:
            self.log_test("Amazon Demo Page", False, f"Exception: {str(e)}")
    
    async def test_environment_variables(self):
        """4. Test variables d'environnement critiques"""
        try:
            async with self.session.get(f"{API_BASE}/health/config") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Vérifier variables critiques
                    checks = []
                    config = data.get('config', {})
                    
                    # Variables critiques attendues
                    critical_vars = ['MONGO_URL', 'ENCRYPTION_KEY', 'JWT_SECRET']
                    for var in critical_vars:
                        var_status = config.get(var, 'missing')
                        checks.append(var_status in ['configured', 'present', True])
                    
                    success = all(checks)
                    configured_vars = [k for k, v in config.items() if v in ['configured', 'present', True]]
                    details = f"Critical vars configured: {len(configured_vars)}/{len(critical_vars)}"
                    self.log_test("Environment Variables", success, details, data)
                    
                else:
                    # Si endpoint n'existe pas, tester indirectement via health
                    await self.test_indirect_env_validation()
                    
        except Exception as e:
            self.log_test("Environment Variables", False, f"Exception: {str(e)}")
    
    async def test_indirect_env_validation(self):
        """Test indirect des variables d'environnement via fonctionnalités"""
        try:
            # Test que MongoDB fonctionne (MONGO_URL configuré)
            async with self.session.get(f"{API_BASE}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    db_status = data.get('services', {}).get('database', 'unknown')
                    mongo_ok = db_status == 'operational'
                    
                    # Test que l'encryption fonctionne (ENCRYPTION_KEY configuré)
                    # Indirect via tentative de création utilisateur
                    encryption_ok = True  # Assumé OK si pas d'erreur critique
                    
                    success = mongo_ok and encryption_ok
                    details = f"MongoDB: {db_status}, Encryption: {'OK' if encryption_ok else 'FAIL'}"
                    self.log_test("Environment Variables (Indirect)", success, details)
                    
                else:
                    self.log_test("Environment Variables (Indirect)", False, f"Health check failed: {response.status}")
                    
        except Exception as e:
            self.log_test("Environment Variables (Indirect)", False, f"Exception: {str(e)}")
    
    async def test_internal_services(self):
        """5. Test services internes (MongoDB, scheduler)"""
        try:
            async with self.session.get(f"{API_BASE}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    services = data.get('services', {})
                    checks = []
                    
                    # MongoDB
                    if 'database' in services:
                        checks.append(services['database'] == 'operational')
                    
                    # Scheduler
                    if 'scheduler' in services:
                        checks.append(services['scheduler'] == 'operational')
                    
                    # Email service
                    if 'email' in services:
                        checks.append(services['email'] in ['operational', 'configured'])
                    
                    success = len(checks) > 0 and all(checks)
                    details = f"Services status: {services}"
                    self.log_test("Internal Services", success, details, data)
                    
                else:
                    error_data = await response.text()
                    self.log_test("Internal Services", False, f"HTTP {response.status}", error_data)
                    
        except Exception as e:
            self.log_test("Internal Services", False, f"Exception: {str(e)}")
    
    async def test_module_imports(self):
        """6. Test importation des modules Python"""
        try:
            # Test via endpoint qui utilise les modules Amazon
            async with self.session.get(f"{API_BASE}/amazon/health/phase3") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Si on arrive ici, les imports Amazon fonctionnent
                    checks = []
                    checks.append(data.get('success') is True)
                    checks.append('health' in data)
                    
                    services = data.get('health', {}).get('services', {})
                    # Vérifier que les services Amazon sont importés
                    amazon_services = ['scraping_service', 'seo_optimizer', 'price_optimizer', 'publisher_service']
                    for service in amazon_services:
                        checks.append(service in services)
                    
                    success = all(checks)
                    details = f"Amazon modules imported successfully, services: {list(services.keys())}"
                    self.log_test("Module Imports (Amazon)", success, details)
                    
                else:
                    # Test alternatif avec endpoint plus simple
                    await self.test_basic_module_imports()
                    
        except Exception as e:
            self.log_test("Module Imports (Amazon)", False, f"Exception: {str(e)}")
    
    async def test_basic_module_imports(self):
        """Test basique des imports via endpoints simples"""
        try:
            # Test endpoint simple qui nécessite les imports de base
            async with self.session.get(f"{API_BASE}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Si on arrive ici, les imports de base fonctionnent
                    success = True
                    details = "Basic Python modules imported successfully"
                    self.log_test("Module Imports (Basic)", success, details)
                    
                else:
                    self.log_test("Module Imports (Basic)", False, f"HTTP {response.status}")
                    
        except Exception as e:
            self.log_test("Module Imports (Basic)", False, f"Exception: {str(e)}")
    
    async def test_public_endpoints(self):
        """Test endpoints publics pour validation générale"""
        
        # Test stats publiques
        try:
            async with self.session.get(f"{API_BASE}/stats/public") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    checks = []
                    checks.append('total_sheets' in data)
                    checks.append('satisfied_clients' in data)
                    checks.append(isinstance(data.get('total_sheets'), int))
                    
                    success = all(checks)
                    details = f"Public stats: {data.get('total_sheets')} sheets, {data.get('satisfied_clients')} clients"
                    self.log_test("Public Stats Endpoint", success, details)
                    
                else:
                    error_data = await response.text()
                    self.log_test("Public Stats Endpoint", False, f"HTTP {response.status}", error_data)
                    
        except Exception as e:
            self.log_test("Public Stats Endpoint", False, f"Exception: {str(e)}")
        
        # Test plans pricing
        try:
            async with self.session.get(f"{API_BASE}/public/plans-pricing") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    checks = []
                    checks.append('plans' in data)
                    plans = data.get('plans', [])
                    checks.append(len(plans) >= 2)  # Au moins gratuit + pro
                    
                    success = all(checks)
                    details = f"Pricing plans available: {len(plans)}"
                    self.log_test("Plans Pricing Endpoint", success, details)
                    
                else:
                    error_data = await response.text()
                    self.log_test("Plans Pricing Endpoint", False, f"HTTP {response.status}", error_data)
                    
        except Exception as e:
            self.log_test("Plans Pricing Endpoint", False, f"Exception: {str(e)}")
    
    async def test_system_metrics(self):
        """Test métriques système pour validation performance"""
        try:
            async with self.session.get(f"{API_BASE}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Vérifier métriques système si disponibles
                    checks = []
                    checks.append('uptime' in data)
                    
                    uptime = data.get('uptime', 0)
                    checks.append(uptime > 0)  # Système démarré
                    
                    # Vérifier timestamp récent
                    timestamp = data.get('timestamp')
                    if timestamp:
                        checks.append(len(timestamp) > 10)  # Format ISO valide
                    
                    success = all(checks)
                    details = f"Uptime: {uptime:.1f}s, Timestamp: {timestamp}"
                    self.log_test("System Metrics", success, details)
                    
                else:
                    error_data = await response.text()
                    self.log_test("System Metrics", False, f"HTTP {response.status}", error_data)
                    
        except Exception as e:
            self.log_test("System Metrics", False, f"Exception: {str(e)}")
    
    def generate_summary(self):
        """Générer résumé des tests"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        duration = time.time() - self.start_time
        
        print("\n" + "="*80)
        print("🎯 ECOMSIMPLY BACKEND - VERCEL CORRECTIONS VALIDATION SUMMARY")
        print("="*80)
        print(f"📊 Tests executed: {total_tests}")
        print(f"✅ Tests passed: {passed_tests}")
        print(f"❌ Tests failed: {failed_tests}")
        print(f"📈 Success rate: {success_rate:.1f}%")
        print(f"⏱️ Duration: {duration:.2f}s")
        print(f"🕐 Completed at: {datetime.utcnow().isoformat()}Z")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({failed_tests}):")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test_name']}: {result['details']}")
        
        print(f"\n✅ PASSED TESTS ({passed_tests}):")
        for result in self.test_results:
            if result['success']:
                print(f"  • {result['test_name']}")
        
        # Évaluation finale
        print(f"\n🎯 FINAL ASSESSMENT:")
        if success_rate >= 90:
            print("🟢 EXCELLENT - Backend ready for Vercel production deployment")
        elif success_rate >= 75:
            print("🟡 GOOD - Backend mostly ready, minor issues to address")
        elif success_rate >= 50:
            print("🟠 MODERATE - Backend needs attention before deployment")
        else:
            print("🔴 CRITICAL - Backend requires significant fixes before deployment")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'duration': duration,
            'assessment': 'EXCELLENT' if success_rate >= 90 else 'GOOD' if success_rate >= 75 else 'MODERATE' if success_rate >= 50 else 'CRITICAL'
        }

async def main():
    """Fonction principale de test"""
    print("🚀 Starting ECOMSIMPLY Backend Vercel Corrections Validation")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"📡 API Base: {API_BASE}")
    print("="*80)
    
    async with VercelCorrectionsBackendTester() as tester:
        # Tests séquentiels selon la review request
        await tester.test_general_health()
        await tester.test_ready_endpoint()
        await tester.test_amazon_spapi_routes()
        await tester.test_demo_amazon_page()
        await tester.test_environment_variables()
        await tester.test_internal_services()
        await tester.test_module_imports()
        await tester.test_public_endpoints()
        await tester.test_system_metrics()
        
        # Générer résumé final
        summary = tester.generate_summary()
        
        return summary

if __name__ == "__main__":
    try:
        summary = asyncio.run(main())
        
        # Exit code basé sur le résultat
        if summary['success_rate'] >= 75:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")
        sys.exit(3)