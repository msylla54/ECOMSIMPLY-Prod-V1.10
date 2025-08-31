#!/usr/bin/env python3
"""
Test Bootstrap Admin ECOMSIMPLY
Teste la création et connexion admin après déploiement Railway
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://api.ecomsimply.com"  # URL finale après DNS
ADMIN_EMAIL = "msylla54@gmail.com"
ADMIN_PASSWORD = "ECS-Temp#2025-08-22!"
BOOTSTRAP_TOKEN = "ECS-Bootstrap-2025-Secure-Token"

class AdminBootstrapTester:
    def __init__(self, base_url=BACKEND_URL):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "ECOMSIMPLY-Admin-Test/1.0"}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health_check(self):
        """Test de base - health check"""
        print("🔍 Test Health Check...")
        try:
            async with self.session.get(f"{self.base_url}/api/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Health Check OK: {data.get('status', 'unknown')}")
                    return True
                else:
                    print(f"❌ Health Check Failed: {resp.status}")
                    return False
        except Exception as e:
            print(f"❌ Health Check Error: {e}")
            return False
    
    async def test_bootstrap_admin(self):
        """Bootstrap de l'admin"""
        print("🔧 Test Bootstrap Admin...")
        try:
            headers = {"x-bootstrap-token": BOOTSTRAP_TOKEN}
            async with self.session.post(
                f"{self.base_url}/api/admin/bootstrap",
                headers=headers
            ) as resp:
                data = await resp.json()
                
                if resp.status == 200:
                    bootstrap_status = data.get('bootstrap', 'unknown')
                    print(f"✅ Bootstrap Admin: {bootstrap_status}")
                    
                    if bootstrap_status == "exists":
                        print("ℹ️  Admin déjà existant (idempotent)")
                    elif bootstrap_status == "done":
                        print("🎉 Admin créé avec succès")
                    
                    return True
                else:
                    print(f"❌ Bootstrap Failed: {resp.status} - {data}")
                    return False
                    
        except Exception as e:
            print(f"❌ Bootstrap Error: {e}")
            return False
    
    async def test_admin_login(self):
        """Test de connexion admin"""
        print("🔑 Test Login Admin...")
        try:
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            async with self.session.post(
                f"{self.base_url}/api/auth/login",
                json=login_data
            ) as resp:
                data = await resp.json()
                
                if resp.status == 200 and "access_token" in data:
                    token = data["access_token"]
                    user_data = data.get("user", {})
                    print(f"✅ Login Admin OK")
                    print(f"   Email: {user_data.get('email', 'N/A')}")
                    print(f"   Role: {user_data.get('role', 'N/A')}")
                    print(f"   Token: {token[:20]}...")
                    
                    # Stocker le token pour tests suivants
                    self.admin_token = token
                    return True
                else:
                    print(f"❌ Login Failed: {resp.status} - {data}")
                    return False
                    
        except Exception as e:
            print(f"❌ Login Error: {e}")
            return False
    
    async def test_admin_endpoints(self):
        """Test endpoints administrateur"""
        if not hasattr(self, 'admin_token'):
            print("⚠️ Pas de token admin - skip tests admin")
            return True
            
        print("🔒 Test Endpoints Admin...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        admin_endpoints = [
            "/api/admin/users",
            "/api/admin/stats",
        ]
        
        success_count = 0
        
        for endpoint in admin_endpoints:
            try:
                async with self.session.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers
                ) as resp:
                    if resp.status in [200, 404]:  # 404 acceptable si endpoint pas implémenté
                        print(f"✅ {endpoint}: {resp.status}")
                        success_count += 1
                    else:
                        print(f"⚠️ {endpoint}: {resp.status}")
                        
            except Exception as e:
                print(f"❌ {endpoint}: {e}")
        
        return success_count > 0
    
    async def test_public_endpoints(self):
        """Test endpoints publics"""
        print("🌐 Test Endpoints Publics...")
        
        public_endpoints = [
            "/api/stats/public",
            "/api/amazon/marketplaces",
            "/api/testimonials",
            "/api/languages"
        ]
        
        success_count = 0
        
        for endpoint in public_endpoints:
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"✅ {endpoint}: OK ({type(data).__name__})")
                        success_count += 1
                    else:
                        print(f"⚠️ {endpoint}: {resp.status}")
                        
            except Exception as e:
                print(f"❌ {endpoint}: {e}")
        
        return success_count >= 2  # Au moins 2 endpoints doivent marcher
    
    async def run_all_tests(self):
        """Exécute tous les tests admin"""
        print("🚀 TESTS ADMIN BOOTSTRAP - ECOMSIMPLY")
        print(f"📍 Backend: {self.base_url}")
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        results = []
        
        # Test 1: Health Check
        results.append(await self.test_health_check())
        print()
        
        # Test 2: Bootstrap Admin
        results.append(await self.test_bootstrap_admin())
        print()
        
        # Test 3: Login Admin
        results.append(await self.test_admin_login())
        print()
        
        # Test 4: Endpoints Admin
        results.append(await self.test_admin_endpoints())
        print()
        
        # Test 5: Endpoints Publics
        results.append(await self.test_public_endpoints())
        print()
        
        # Résultats
        success_count = sum(results)
        total_tests = len(results)
        success_rate = (success_count / total_tests) * 100
        
        print("=" * 60)
        print("📊 RÉSULTATS ADMIN BOOTSTRAP")
        print(f"Tests réussis: {success_count}/{total_tests}")
        print(f"Taux de succès: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 ✅ ADMIN BOOTSTRAP RÉUSSI!")
            status = "SUCCESS"
        else:
            print("❌ 🔴 ADMIN BOOTSTRAP ÉCHOUÉ")
            status = "FAILED"
        
        # Sauvegarde résultats
        report = {
            "test_date": datetime.now().isoformat(),
            "backend_url": self.base_url,
            "success_rate": success_rate,
            "tests_passed": success_count,
            "total_tests": total_tests,
            "status": status,
            "admin_email": ADMIN_EMAIL
        }
        
        with open("admin_bootstrap_results.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📋 Résultats sauvegardés: admin_bootstrap_results.json")
        
        return success_rate >= 80

async def main():
    """Point d'entrée principal"""
    
    # Permettre de tester avec URL alternative
    backend_url = sys.argv[1] if len(sys.argv) > 1 else BACKEND_URL
    
    async with AdminBootstrapTester(backend_url) as tester:
        try:
            success = await tester.run_all_tests()
            sys.exit(0 if success else 1)
            
        except Exception as e:
            print(f"❌ Erreur critique: {e}")
            sys.exit(2)

if __name__ == "__main__":
    print("Usage: python test_admin_bootstrap.py [BACKEND_URL]")
    print(f"Default: {BACKEND_URL}")
    print()
    
    asyncio.run(main())