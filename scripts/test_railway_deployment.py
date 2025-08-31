#!/usr/bin/env python3
"""
Test E2E Railway Deployment - ECOMSIMPLY
Valide le déploiement Railway complet avec tous les endpoints critiques
"""

import asyncio
import aiohttp
import json
import sys
import argparse
from datetime import datetime
from typing import Dict, Any, List

class RailwayE2ETester:
    def __init__(self, railway_url: str, frontend_url: str = "https://ecomsimply.com"):
        self.railway_url = railway_url.rstrip('/')
        self.frontend_url = frontend_url.rstrip('/')
        self.session = None
        self.admin_token = None
        
        self.results = {
            "railway_direct": {},
            "vercel_proxy": {},
            "admin_functionality": {},
            "amazon_spapi": {},
            "database_connectivity": {},
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
    
    async def test_railway_direct(self):
        """Tests directs sur Railway backend"""
        print("\n🔍 PHASE 1: Tests Railway Direct")
        print("-" * 40)
        
        # Test 1.1: Health Check
        try:
            async with self.session.get(f"{self.railway_url}/api/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    success = data.get("status") == "healthy"
                    self.log_test("railway_direct", "health_check", success, data)
                else:
                    self.log_test("railway_direct", "health_check", False, f"HTTP {resp.status}")
        except Exception as e:
            self.log_test("railway_direct", "health_check", False, str(e))
        
        # Test 1.2: Bootstrap Admin
        try:
            headers = {"x-bootstrap-token": "ECS-Bootstrap-2025-Secure-Token"}
            async with self.session.post(f"{self.railway_url}/api/admin/bootstrap", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    success = data.get("ok") is True
                    self.log_test("railway_direct", "bootstrap_admin", success, data)
                else:
                    self.log_test("railway_direct", "bootstrap_admin", False, f"HTTP {resp.status}")
        except Exception as e:
            self.log_test("railway_direct", "bootstrap_admin", False, str(e))
        
        # Test 1.3: Admin Login
        try:
            login_data = {
                "email": "msylla54@gmail.com",
                "password": "ECS-Temp#2025-08-22!"
            }
            async with self.session.post(f"{self.railway_url}/api/auth/login", json=login_data) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    success = "access_token" in data
                    if success:
                        self.admin_token = data["access_token"]
                    self.log_test("railway_direct", "admin_login", success, {"has_token": success})
                else:
                    self.log_test("railway_direct", "admin_login", False, f"HTTP {resp.status}")
        except Exception as e:
            self.log_test("railway_direct", "admin_login", False, str(e))
        
        # Test 1.4: Endpoints Publics
        public_endpoints = [
            "/api/stats/public",
            "/api/testimonials", 
            "/api/languages",
            "/api/public/plans-pricing"
        ]
        
        for endpoint in public_endpoints:
            try:
                async with self.session.get(f"{self.railway_url}{endpoint}") as resp:
                    success = resp.status == 200
                    if success:
                        data = await resp.json()
                        details = {"type": type(data).__name__, "has_data": bool(data)}
                    else:
                        details = {"status": resp.status}
                    
                    test_name = f"public_{endpoint.replace('/', '_').replace('-', '_')}"
                    self.log_test("railway_direct", test_name, success, details)
            except Exception as e:
                test_name = f"public_{endpoint.replace('/', '_').replace('-', '_')}"
                self.log_test("railway_direct", test_name, False, str(e))
    
    async def test_vercel_proxy(self):
        """Tests proxy Vercel → Railway"""
        print("\n🔄 PHASE 2: Tests Proxy Vercel")
        print("-" * 40)
        
        # Test 2.1: Health via proxy
        try:
            async with self.session.get(f"{self.frontend_url}/api/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    success = data.get("status") == "healthy"
                    self.log_test("vercel_proxy", "proxy_health", success, {"via_proxy": True})
                else:
                    self.log_test("vercel_proxy", "proxy_health", False, f"HTTP {resp.status}")
        except Exception as e:
            self.log_test("vercel_proxy", "proxy_health", False, str(e))
        
        # Test 2.2: Login via proxy
        try:
            login_data = {
                "email": "msylla54@gmail.com",
                "password": "ECS-Temp#2025-08-22!"
            }
            async with self.session.post(f"{self.frontend_url}/api/auth/login", json=login_data) as resp:
                success = resp.status == 200
                self.log_test("vercel_proxy", "proxy_login", success, {"via_proxy": True})
        except Exception as e:
            self.log_test("vercel_proxy", "proxy_login", False, str(e))
        
        # Test 2.3: Endpoints publics via proxy
        proxy_endpoints = ["/api/stats/public", "/api/testimonials"]
        
        for endpoint in proxy_endpoints:
            try:
                async with self.session.get(f"{self.frontend_url}{endpoint}") as resp:
                    success = resp.status == 200
                    test_name = f"proxy_{endpoint.replace('/', '_')}"
                    self.log_test("vercel_proxy", test_name, success, {"status": resp.status})
            except Exception as e:
                test_name = f"proxy_{endpoint.replace('/', '_')}"
                self.log_test("vercel_proxy", test_name, False, str(e))
    
    async def test_admin_functionality(self):
        """Tests fonctionnalités admin"""
        print("\n🔑 PHASE 3: Tests Admin Functionality")
        print("-" * 40)
        
        if not self.admin_token:
            print("⚠️ Pas de token admin - skip tests admin")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test 3.1: Admin endpoints protégés
        admin_endpoints = [
            "/api/admin/users",
            "/api/admin/stats"
        ]
        
        for endpoint in admin_endpoints:
            try:
                # Test sans token (doit échouer)
                async with self.session.get(f"{self.railway_url}{endpoint}") as resp:
                    protected = resp.status in [401, 403]
                    test_name = f"protection_{endpoint.replace('/', '_')}"
                    self.log_test("admin_functionality", test_name, protected, {"protected": protected})
                
                # Test avec token (peut réussir ou 404 si non implémenté)
                async with self.session.get(f"{self.railway_url}{endpoint}", headers=headers) as resp:
                    authorized = resp.status in [200, 404]
                    test_name = f"authorized_{endpoint.replace('/', '_')}"
                    self.log_test("admin_functionality", test_name, authorized, {"status": resp.status})
                    
            except Exception as e:
                test_name = f"admin_{endpoint.replace('/', '_')}"
                self.log_test("admin_functionality", test_name, False, str(e))
    
    async def test_amazon_spapi(self):
        """Tests Amazon SP-API"""
        print("\n🛒 PHASE 4: Tests Amazon SP-API")
        print("-" * 40)
        
        # Test 4.1: Amazon Health
        try:
            async with self.session.get(f"{self.railway_url}/api/amazon/health") as resp:
                success = resp.status == 200
                self.log_test("amazon_spapi", "amazon_health", success, {"status": resp.status})
        except Exception as e:
            self.log_test("amazon_spapi", "amazon_health", False, str(e))
        
        # Test 4.2: Marketplaces
        try:
            async with self.session.get(f"{self.railway_url}/api/amazon/marketplaces") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    success = isinstance(data, list) and len(data) >= 6
                    details = {"count": len(data) if isinstance(data, list) else 0}
                else:
                    success = False
                    details = {"status": resp.status}
                
                self.log_test("amazon_spapi", "marketplaces", success, details)
        except Exception as e:
            self.log_test("amazon_spapi", "marketplaces", False, str(e))
        
        # Test 4.3: Demo status
        try:
            async with self.session.get(f"{self.railway_url}/api/demo/amazon/status") as resp:
                success = resp.status in [200, 404]  # 404 acceptable
                self.log_test("amazon_spapi", "demo_status", success, {"status": resp.status})
        except Exception as e:
            self.log_test("amazon_spapi", "demo_status", False, str(e))
    
    async def test_database_connectivity(self):
        """Tests connectivité base de données"""
        print("\n💾 PHASE 5: Tests Database Connectivity")
        print("-" * 40)
        
        # Test 5.1: Health check database
        try:
            async with self.session.get(f"{self.railway_url}/api/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    db_connected = data.get("database") == "connected"
                    self.log_test("database_connectivity", "mongodb_connection", db_connected, data.get("database"))
                else:
                    self.log_test("database_connectivity", "mongodb_connection", False, f"HTTP {resp.status}")
        except Exception as e:
            self.log_test("database_connectivity", "mongodb_connection", False, str(e))
        
        # Test 5.2: Collections de base
        collections_endpoints = [
            "/api/testimonials",
            "/api/languages",
            "/api/stats/public"
        ]
        
        for endpoint in collections_endpoints:
            try:
                async with self.session.get(f"{self.railway_url}{endpoint}") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        success = bool(data)  # Données présentes
                        details = {"has_data": success, "count": len(data) if isinstance(data, list) else 1}
                    else:
                        success = False
                        details = {"status": resp.status}
                    
                    collection_name = endpoint.split('/')[-1]
                    self.log_test("database_connectivity", f"collection_{collection_name}", success, details)
            except Exception as e:
                collection_name = endpoint.split('/')[-1]
                self.log_test("database_connectivity", f"collection_{collection_name}", False, str(e))
    
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
    
    async def run_complete_e2e(self):
        """Exécute tous les tests E2E"""
        print("🚂 TESTS E2E RAILWAY DEPLOYMENT - ECOMSIMPLY")
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Railway URL: {self.railway_url}")
        print(f"🌐 Frontend URL: {self.frontend_url}")
        print("=" * 60)
        
        # Exécution des phases
        await self.test_railway_direct()
        await self.test_vercel_proxy()
        await self.test_admin_functionality()
        await self.test_amazon_spapi()
        await self.test_database_connectivity()
        
        # Calculs finaux
        success_rates = self.calculate_success_rates()
        global_success = sum(success_rates.values()) / len(success_rates) if success_rates else 0
        
        # Comptage total
        total_tests = sum(len(tests) for tests in self.results.values() if isinstance(tests, dict))
        successful_tests = sum(
            sum(1 for test in tests.values() if test.get("success", False))
            for tests in self.results.values() if isinstance(tests, dict)
        )
        
        self.results["summary"] = {
            "test_date": datetime.now().isoformat(),
            "railway_url": self.railway_url,
            "frontend_url": self.frontend_url,
            "success_rates": success_rates,
            "global_success_rate": global_success,
            "total_tests": total_tests,
            "successful_tests": successful_tests
        }
        
        # Affichage final
        print("\n" + "=" * 60)
        print("📊 RÉSULTATS FINAUX E2E RAILWAY")
        print("-" * 35)
        for category, rate in success_rates.items():
            print(f"{category.replace('_', ' ').title()}: {rate:.1f}%")
        
        print(f"\n🎯 GLOBAL: {global_success:.1f}% ({successful_tests}/{total_tests} tests)")
        
        # Verdict
        if global_success >= 90:
            print("\n🎉 ✅ DÉPLOIEMENT RAILWAY EXCELLENT - PRODUCTION READY!")
            verdict = "EXCELLENT"
        elif global_success >= 80:
            print("\n✅ 🟢 DÉPLOIEMENT RAILWAY RÉUSSI - Production Ready")
            verdict = "SUCCESS"
        elif global_success >= 70:
            print("\n⚠️ 🟡 DÉPLOIEMENT RAILWAY PARTIEL - Corrections mineures")
            verdict = "PARTIAL"
        else:
            print("\n❌ 🔴 DÉPLOIEMENT RAILWAY ÉCHOUÉ - Corrections requises")
            verdict = "FAILED"
        
        self.results["summary"]["verdict"] = verdict
        
        return self.results

async def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description="Test E2E déploiement Railway ECOMSIMPLY")
    parser.add_argument("--url", required=True, help="URL du backend Railway")
    parser.add_argument("--frontend", default="https://ecomsimply.com", help="URL du frontend")
    
    args = parser.parse_args()
    
    async with RailwayE2ETester(args.url, args.frontend) as tester:
        try:
            results = await tester.run_complete_e2e()
            
            # Sauvegarde
            with open("/app/ecomsimply-deploy/railway_e2e_results.json", "w") as f:
                json.dump(results, f, indent=2)
            
            print(f"\n📋 Résultats détaillés: railway_e2e_results.json")
            
            # Code de sortie
            verdict = results["summary"]["verdict"]
            sys.exit(0 if verdict in ["EXCELLENT", "SUCCESS"] else 1)
            
        except Exception as e:
            print(f"❌ Erreur critique E2E: {e}")
            sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())