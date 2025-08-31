#!/usr/bin/env python3
"""
Tests E2E Complets - ECOMSIMPLY Railway Deployment
Valide le workflow complet après déploiement Railway + DNS Vercel
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
from typing import Dict, Any, List

# URLs finales
FRONTEND_URL = "https://ecomsimply.com"
BACKEND_DIRECT_URL = "https://api.ecomsimply.com"

# Configuration Admin
ADMIN_EMAIL = "msylla54@gmail.com"
ADMIN_PASSWORD = "ECS-Temp#2025-08-22!"
BOOTSTRAP_TOKEN = "ECS-Bootstrap-2025-Secure-Token"

class RailwayE2ETester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.results = {
            "backend_direct": {},
            "frontend_proxy": {},
            "e2e_workflow": {},
            "summary": {}
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "ECOMSIMPLY-Railway-E2E/1.0"}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, category: str, test_name: str, success: bool, details: Any = None):
        """Log standardisé des tests"""
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        
        if category not in self.results:
            self.results[category] = {}
        
        self.results[category][test_name] = {
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
    
    async def test_backend_direct(self) -> Dict[str, bool]:
        """Tests backend direct api.ecomsimply.com"""
        print("\n🔍 PHASE 1: Backend Direct (api.ecomsimply.com)")
        print("-" * 50)
        
        tests = {}
        
        # Test 1.1: Health Check
        try:
            async with self.session.get(f"{BACKEND_DIRECT_URL}/api/health") as resp:
                data = await resp.json()
                success = resp.status == 200 and data.get("status") == "healthy"
                self.log_test("backend_direct", "health_check", success, data)
                tests["health"] = success
        except Exception as e:
            self.log_test("backend_direct", "health_check", False, str(e))
            tests["health"] = False
        
        # Test 1.2: Bootstrap Admin
        try:
            headers = {"x-bootstrap-token": BOOTSTRAP_TOKEN}
            async with self.session.post(f"{BACKEND_DIRECT_URL}/api/admin/bootstrap", headers=headers) as resp:
                data = await resp.json()
                success = resp.status == 200
                self.log_test("backend_direct", "bootstrap_admin", success, data)
                tests["bootstrap"] = success
        except Exception as e:
            self.log_test("backend_direct", "bootstrap_admin", False, str(e))
            tests["bootstrap"] = False
        
        # Test 1.3: Admin Login
        try:
            login_data = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
            async with self.session.post(f"{BACKEND_DIRECT_URL}/api/auth/login", json=login_data) as resp:
                data = await resp.json()
                success = resp.status == 200 and "access_token" in data
                if success:
                    self.admin_token = data["access_token"]
                self.log_test("backend_direct", "admin_login", success, {"has_token": success})
                tests["login"] = success
        except Exception as e:
            self.log_test("backend_direct", "admin_login", False, str(e))
            tests["login"] = False
        
        # Test 1.4: Endpoints Publics
        public_endpoints = [
            "/api/stats/public",
            "/api/amazon/marketplaces",
            "/api/testimonials",
            "/api/languages"
        ]
        
        public_success = 0
        for endpoint in public_endpoints:
            try:
                async with self.session.get(f"{BACKEND_DIRECT_URL}{endpoint}") as resp:
                    success = resp.status == 200
                    if success:
                        public_success += 1
                        data = await resp.json()
                        self.log_test("backend_direct", f"public{endpoint.replace('/', '_')}", True, type(data).__name__)
                    else:
                        self.log_test("backend_direct", f"public{endpoint.replace('/', '_')}", False, resp.status)
            except Exception as e:
                self.log_test("backend_direct", f"public{endpoint.replace('/', '_')}", False, str(e))
        
        tests["public_endpoints"] = public_success >= 2
        
        return tests
    
    async def test_frontend_proxy(self) -> Dict[str, bool]:
        """Tests frontend proxy via Vercel"""
        print("\n🔍 PHASE 2: Frontend Proxy (ecomsimply.com)")
        print("-" * 50)
        
        tests = {}
        
        # Test 2.1: Proxy Health Check
        try:
            async with self.session.get(f"{FRONTEND_URL}/api/health") as resp:
                data = await resp.json()
                success = resp.status == 200 and data.get("status") == "healthy"
                self.log_test("frontend_proxy", "proxy_health", success, data)
                tests["proxy_health"] = success
        except Exception as e:
            self.log_test("frontend_proxy", "proxy_health", False, str(e))
            tests["proxy_health"] = False
        
        # Test 2.2: Proxy Login
        try:
            login_data = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
            async with self.session.post(f"{FRONTEND_URL}/api/auth/login", json=login_data) as resp:
                data = await resp.json()
                success = resp.status == 200 and "access_token" in data
                self.log_test("frontend_proxy", "proxy_login", success, {"has_token": success})
                tests["proxy_login"] = success
        except Exception as e:
            self.log_test("frontend_proxy", "proxy_login", False, str(e))
            tests["proxy_login"] = False
        
        # Test 2.3: Proxy Public Endpoints
        proxy_endpoints = ["/api/stats/public", "/api/amazon/marketplaces"]
        proxy_success = 0
        
        for endpoint in proxy_endpoints:
            try:
                async with self.session.get(f"{FRONTEND_URL}{endpoint}") as resp:
                    success = resp.status == 200
                    if success:
                        proxy_success += 1
                    self.log_test("frontend_proxy", f"proxy{endpoint.replace('/', '_')}", success, resp.status)
            except Exception as e:
                self.log_test("frontend_proxy", f"proxy{endpoint.replace('/', '_')}", False, str(e))
        
        tests["proxy_endpoints"] = proxy_success >= 1
        
        # Test 2.4: CORS Headers
        try:
            headers = {"Origin": FRONTEND_URL}
            async with self.session.get(f"{FRONTEND_URL}/api/stats/public", headers=headers) as resp:
                success = resp.status == 200
                cors_headers = {
                    "access-control-allow-origin": resp.headers.get("access-control-allow-origin"),
                    "access-control-allow-methods": resp.headers.get("access-control-allow-methods")
                }
                self.log_test("frontend_proxy", "cors_headers", success, cors_headers)
                tests["cors"] = success
        except Exception as e:
            self.log_test("frontend_proxy", "cors_headers", False, str(e))
            tests["cors"] = False
        
        return tests
    
    async def test_amazon_integration(self) -> Dict[str, bool]:
        """Tests spécifiques Amazon SP-API"""
        print("\n🔍 PHASE 3: Amazon SP-API Integration")
        print("-" * 50)
        
        tests = {}
        
        # Test 3.1: Amazon Marketplaces
        try:
            async with self.session.get(f"{BACKEND_DIRECT_URL}/api/amazon/marketplaces") as resp:
                data = await resp.json()
                success = resp.status == 200 and isinstance(data, list) and len(data) >= 6
                self.log_test("e2e_workflow", "amazon_marketplaces", success, {"count": len(data) if isinstance(data, list) else 0})
                tests["marketplaces"] = success
        except Exception as e:
            self.log_test("e2e_workflow", "amazon_marketplaces", False, str(e))
            tests["marketplaces"] = False
        
        # Test 3.2: Amazon Connection Status (si admin token disponible)
        if self.admin_token:
            try:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                async with self.session.get(f"{BACKEND_DIRECT_URL}/api/amazon/connections", headers=headers) as resp:
                    success = resp.status in [200, 404]  # 404 acceptable si pas de connexions
                    data = await resp.json() if resp.status == 200 else {"status": resp.status}
                    self.log_test("e2e_workflow", "amazon_connections", success, data)
                    tests["connections"] = success
            except Exception as e:
                self.log_test("e2e_workflow", "amazon_connections", False, str(e))
                tests["connections"] = False
        else:
            tests["connections"] = False
        
        # Test 3.3: Amazon Public Stats
        try:
            async with self.session.get(f"{BACKEND_DIRECT_URL}/api/amazon/stats/public") as resp:
                success = resp.status in [200, 404]  # Peut ne pas exister
                self.log_test("e2e_workflow", "amazon_public_stats", success, resp.status)
                tests["public_stats"] = success
        except Exception as e:
            self.log_test("e2e_workflow", "amazon_public_stats", False, str(e))
            tests["public_stats"] = False
        
        return tests
    
    async def test_complete_workflow(self) -> Dict[str, bool]:
        """Test workflow E2E complet"""
        print("\n🔍 PHASE 4: Workflow E2E Complet")
        print("-" * 50)
        
        tests = {}
        
        # Test 4.1: Frontend Loading (basique)
        try:
            async with self.session.get(FRONTEND_URL) as resp:
                success = resp.status == 200
                content_type = resp.headers.get("content-type", "")
                is_html = "text/html" in content_type
                self.log_test("e2e_workflow", "frontend_loading", success and is_html, {
                    "status": resp.status,
                    "content_type": content_type
                })
                tests["frontend"] = success and is_html
        except Exception as e:
            self.log_test("e2e_workflow", "frontend_loading", False, str(e))
            tests["frontend"] = False
        
        # Test 4.2: Database Connection (via health check)
        try:
            async with self.session.get(f"{BACKEND_DIRECT_URL}/api/health") as resp:
                data = await resp.json()
                db_connected = data.get("database") == "connected"
                self.log_test("e2e_workflow", "database_connection", db_connected, data.get("database"))
                tests["database"] = db_connected
        except Exception as e:
            self.log_test("e2e_workflow", "database_connection", False, str(e))
            tests["database"] = False
        
        # Test 4.3: Critical API Endpoints
        critical_endpoints = [
            "/api/health",
            "/api/stats/public",
            "/api/amazon/marketplaces"
        ]
        
        critical_success = 0
        for endpoint in critical_endpoints:
            try:
                async with self.session.get(f"{BACKEND_DIRECT_URL}{endpoint}") as resp:
                    if resp.status == 200:
                        critical_success += 1
            except:
                pass
        
        tests["critical_apis"] = critical_success >= 2
        self.log_test("e2e_workflow", "critical_apis", tests["critical_apis"], f"{critical_success}/3 OK")
        
        return tests
    
    def calculate_success_rates(self) -> Dict[str, float]:
        """Calcule les taux de succès par catégorie"""
        rates = {}
        
        for category, tests in self.results.items():
            if category == "summary":
                continue
                
            if tests:
                total = len(tests)
                successful = sum(1 for test in tests.values() if test.get("success", False))
                rates[category] = (successful / total) * 100 if total > 0 else 0
        
        return rates
    
    async def run_all_tests(self):
        """Exécute tous les tests E2E"""
        print("🚀 TESTS E2E RAILWAY DEPLOYMENT - ECOMSIMPLY")
        print(f"📍 Frontend: {FRONTEND_URL}")
        print(f"📍 Backend: {BACKEND_DIRECT_URL}")
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Exécution des phases de test
        backend_tests = await self.test_backend_direct()
        proxy_tests = await self.test_frontend_proxy()
        amazon_tests = await self.test_amazon_integration()
        workflow_tests = await self.test_complete_workflow()
        
        # Calculs finaux
        success_rates = self.calculate_success_rates()
        global_success = sum(success_rates.values()) / len(success_rates) if success_rates else 0
        
        self.results["summary"] = {
            "test_date": datetime.now().isoformat(),
            "frontend_url": FRONTEND_URL,
            "backend_url": BACKEND_DIRECT_URL,
            "success_rates": success_rates,
            "global_success_rate": global_success,
            "backend_direct_tests": len(self.results.get("backend_direct", {})),
            "frontend_proxy_tests": len(self.results.get("frontend_proxy", {})),
            "e2e_workflow_tests": len(self.results.get("e2e_workflow", {}))
        }
        
        # Affichage final
        print("\n" + "=" * 70)
        print("📊 RÉSULTATS FINAUX E2E")
        print("-" * 30)
        for category, rate in success_rates.items():
            print(f"{category.replace('_', ' ').title()}: {rate:.1f}%")
        print(f"\n🎯 GLOBAL: {global_success:.1f}%")
        
        # Verdict final
        if global_success >= 90:
            print("\n🎉 ✅ DÉPLOIEMENT RAILWAY RÉUSSI - PRODUCTION READY!")
            verdict = "SUCCESS"
        elif global_success >= 75:
            print("\n⚠️ 🟡 DÉPLOIEMENT PARTIELLEMENT RÉUSSI - Corrections mineures")
            verdict = "PARTIAL"
        else:
            print("\n❌ 🔴 DÉPLOIEMENT ÉCHOUÉ - Corrections majeures requises")
            verdict = "FAILED"
        
        self.results["summary"]["verdict"] = verdict
        
        return self.results

async def main():
    """Point d'entrée principal"""
    
    async with RailwayE2ETester() as tester:
        try:
            results = await tester.run_all_tests()
            
            # Sauvegarde résultats
            with open("railway_e2e_results.json", "w") as f:
                json.dump(results, f, indent=2)
            
            print(f"\n📋 Résultats détaillés: railway_e2e_results.json")
            
            # Code de sortie
            verdict = results["summary"]["verdict"]
            sys.exit(0 if verdict == "SUCCESS" else 1)
            
        except Exception as e:
            print(f"❌ Erreur critique E2E: {e}")
            sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())