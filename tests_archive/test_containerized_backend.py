#!/usr/bin/env python3
"""
Tests E2E pour validation du backend conteneurisé ECOMSIMPLY
Après migration de api/index.py vers backend conteneur Railway/Fly.io
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
from typing import Dict, Any

# URLs de test
BACKEND_DIRECT_URL = "https://api.ecomsimply.com"
FRONTEND_PROXY_URL = "https://ecomsimply.com"

# Configuration admin
ADMIN_EMAIL = "msylla54@gmail.com"
ADMIN_PASSWORD = "ECS-Temp#2025-08-22!"
BOOTSTRAP_TOKEN = "ECS-Bootstrap-2025-Secure-Token"

class ContainerizedBackendTester:
    def __init__(self):
        self.session = None
        self.results = {
            "backend_direct": {},
            "frontend_proxy": {},
            "summary": {}
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "ECOMSIMPLY-E2E-Test/1.0"}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_backend_direct(self) -> Dict[str, Any]:
        """Tests directs sur le backend conteneur"""
        print("🔍 PHASE 1: Tests Backend Direct")
        results = {}
        
        # Test 1.1: Health Check
        try:
            async with self.session.get(f"{BACKEND_DIRECT_URL}/api/health") as resp:
                health_data = await resp.json()
                results["health_check"] = {
                    "status": resp.status,
                    "success": resp.status == 200,
                    "data": health_data
                }
                print(f"✅ Health Check: {resp.status}")
        except Exception as e:
            results["health_check"] = {"success": False, "error": str(e)}
            print(f"❌ Health Check: {e}")
        
        # Test 1.2: Bootstrap Admin
        try:
            headers = {"x-bootstrap-token": BOOTSTRAP_TOKEN}
            async with self.session.post(
                f"{BACKEND_DIRECT_URL}/api/admin/bootstrap", 
                headers=headers
            ) as resp:
                bootstrap_data = await resp.json()
                results["bootstrap"] = {
                    "status": resp.status,
                    "success": resp.status == 200,
                    "data": bootstrap_data
                }
                print(f"✅ Bootstrap: {resp.status} - {bootstrap_data.get('bootstrap', 'unknown')}")
        except Exception as e:
            results["bootstrap"] = {"success": False, "error": str(e)}
            print(f"❌ Bootstrap: {e}")
        
        # Test 1.3: Login Admin  
        try:
            login_data = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
            async with self.session.post(
                f"{BACKEND_DIRECT_URL}/api/auth/login",
                json=login_data
            ) as resp:
                auth_data = await resp.json()
                results["login"] = {
                    "status": resp.status,
                    "success": resp.status == 200,
                    "has_token": "access_token" in auth_data,
                    "data": auth_data
                }
                print(f"✅ Login: {resp.status} - Token: {'✅' if 'access_token' in auth_data else '❌'}")
        except Exception as e:
            results["login"] = {"success": False, "error": str(e)}
            print(f"❌ Login: {e}")
        
        # Test 1.4: Endpoints Publics
        public_endpoints = [
            "/api/stats/public",
            "/api/amazon/marketplaces", 
            "/api/testimonials",
            "/api/languages"
        ]
        
        results["public_endpoints"] = {}
        for endpoint in public_endpoints:
            try:
                async with self.session.get(f"{BACKEND_DIRECT_URL}{endpoint}") as resp:
                    data = await resp.json()
                    results["public_endpoints"][endpoint] = {
                        "status": resp.status,
                        "success": resp.status == 200,
                        "data_type": type(data).__name__,
                        "has_data": bool(data)
                    }
                    print(f"✅ {endpoint}: {resp.status}")
            except Exception as e:
                results["public_endpoints"][endpoint] = {"success": False, "error": str(e)}
                print(f"❌ {endpoint}: {e}")
        
        return results
    
    async def test_frontend_proxy(self) -> Dict[str, Any]:
        """Tests via proxy Vercel"""
        print("\n🔍 PHASE 2: Tests Frontend Proxy")
        results = {}
        
        # Test 2.1: Health via proxy
        try:
            async with self.session.get(f"{FRONTEND_PROXY_URL}/api/health") as resp:
                health_data = await resp.json()
                results["proxy_health"] = {
                    "status": resp.status,
                    "success": resp.status == 200,
                    "data": health_data
                }
                print(f"✅ Proxy Health: {resp.status}")
        except Exception as e:
            results["proxy_health"] = {"success": False, "error": str(e)}
            print(f"❌ Proxy Health: {e}")
        
        # Test 2.2: Login via proxy
        try:
            login_data = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
            async with self.session.post(
                f"{FRONTEND_PROXY_URL}/api/auth/login",
                json=login_data
            ) as resp:
                auth_data = await resp.json()
                results["proxy_login"] = {
                    "status": resp.status,
                    "success": resp.status == 200,
                    "has_token": "access_token" in auth_data
                }
                print(f"✅ Proxy Login: {resp.status}")
        except Exception as e:
            results["proxy_login"] = {"success": False, "error": str(e)}
            print(f"❌ Proxy Login: {e}")
        
        # Test 2.3: Endpoints publics via proxy
        proxy_endpoints = ["/api/stats/public", "/api/amazon/marketplaces"]
        results["proxy_endpoints"] = {}
        
        for endpoint in proxy_endpoints:
            try:
                async with self.session.get(f"{FRONTEND_PROXY_URL}{endpoint}") as resp:
                    data = await resp.json()
                    results["proxy_endpoints"][endpoint] = {
                        "status": resp.status,
                        "success": resp.status == 200
                    }
                    print(f"✅ Proxy {endpoint}: {resp.status}")
            except Exception as e:
                results["proxy_endpoints"][endpoint] = {"success": False, "error": str(e)}
                print(f"❌ Proxy {endpoint}: {e}")
        
        return results
    
    def calculate_success_rate(self, results: Dict[str, Any]) -> float:
        """Calcule le taux de succès global"""
        total_tests = 0
        successful_tests = 0
        
        def count_recursive(data):
            nonlocal total_tests, successful_tests
            if isinstance(data, dict):
                if "success" in data:
                    total_tests += 1
                    if data["success"]:
                        successful_tests += 1
                else:
                    for value in data.values():
                        count_recursive(value)
        
        count_recursive(results)
        return (successful_tests / total_tests * 100) if total_tests > 0 else 0
    
    async def run_all_tests(self):
        """Exécute tous les tests"""
        print("🚀 TESTS E2E BACKEND CONTENEURISÉ ECOMSIMPLY")
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Phase 1: Backend direct
        self.results["backend_direct"] = await self.test_backend_direct()
        
        # Phase 2: Frontend proxy  
        self.results["frontend_proxy"] = await self.test_frontend_proxy()
        
        # Calculs finaux
        backend_success = self.calculate_success_rate(self.results["backend_direct"])
        proxy_success = self.calculate_success_rate(self.results["frontend_proxy"])
        global_success = self.calculate_success_rate(self.results)
        
        self.results["summary"] = {
            "backend_direct_success_rate": backend_success,
            "frontend_proxy_success_rate": proxy_success,
            "global_success_rate": global_success,
            "test_date": datetime.now().isoformat(),
            "backend_url": BACKEND_DIRECT_URL,
            "frontend_url": FRONTEND_PROXY_URL
        }
        
        # Affichage résultats
        print("\n" + "=" * 60)
        print("📊 RÉSULTATS FINAUX")
        print(f"Backend Direct: {backend_success:.1f}% de succès")
        print(f"Frontend Proxy: {proxy_success:.1f}% de succès")
        print(f"Global: {global_success:.1f}% de succès")
        
        if global_success >= 90:
            print("🎉 ✅ MIGRATION BACKEND CONTENEUR RÉUSSIE!")
        elif global_success >= 70:
            print("⚠️ 🟡 MIGRATION PARTIELLEMENT RÉUSSIE - Corrections mineures needed")
        else:
            print("❌ 🔴 MIGRATION ÉCHOUÉE - Corrections majeures required")
        
        return self.results

async def main():
    """Point d'entrée principal"""
    async with ContainerizedBackendTester() as tester:
        try:
            results = await tester.run_all_tests()
            
            # Sauvegarde résultats
            with open("containerized_backend_test_results.json", "w") as f:
                json.dump(results, f, indent=2)
            
            print(f"\n📋 Résultats sauvegardés: containerized_backend_test_results.json")
            
            # Code de sortie selon succès
            success_rate = results["summary"]["global_success_rate"]
            sys.exit(0 if success_rate >= 90 else 1)
            
        except Exception as e:
            print(f"❌ Erreur critique: {e}")
            sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())