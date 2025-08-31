#!/usr/bin/env python3
"""
Bootstrap Admin & Sécurité - ECOMSIMPLY
Lance le bootstrap admin et valide la sécurité
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
from pathlib import Path

# Configuration
ADMIN_EMAIL = "msylla54@gmail.com"
ADMIN_PASSWORD = "ECS-Temp#2025-08-22!"
BOOTSTRAP_TOKEN = "ECS-Bootstrap-2025-Secure-Token"

class AdminBootstrapService:
    def __init__(self):
        # Lire les URLs depuis les fichiers de configuration
        self.backend_direct_url = self.get_backend_url()
        self.frontend_proxy_url = "https://ecomsimply.com"
        self.session = None
        
    def get_backend_url(self):
        """Récupère l'URL du backend"""
        # Essayer de lire depuis le fichier Railway
        railway_file = Path("/app/ecomsimply-deploy/RAILWAY_BACKEND_URL.txt")
        if railway_file.exists():
            railway_url = railway_file.read_text().strip()
            return f"https://{railway_url}"
        
        # Essayer depuis DNS configuré
        dns_config_file = Path("/app/ecomsimply-deploy/DNS_CONFIG.json")
        if dns_config_file.exists():
            try:
                with open(dns_config_file) as f:
                    dns_config = json.load(f)
                    return f"https://{dns_config['domain']}"
            except:
                pass
        
        # URL par défaut si DNS configuré
        return "https://api.ecomsimply.com"
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "ECOMSIMPLY-Bootstrap/1.0"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_backend_health(self, url):
        """Test health check backend"""
        try:
            async with self.session.get(f"{url}/api/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Backend accessible: {url}")
                    print(f"   Status: {data.get('status', 'unknown')}")
                    print(f"   Database: {data.get('database', 'unknown')}")
                    return True, data
                else:
                    print(f"❌ Backend inaccessible: {resp.status}")
                    return False, None
        except Exception as e:
            print(f"❌ Erreur connexion backend: {e}")
            return False, None
    
    async def bootstrap_admin(self, backend_url):
        """Lance le bootstrap admin"""
        print("🔧 Bootstrap Admin...")
        
        try:
            headers = {"x-bootstrap-token": BOOTSTRAP_TOKEN}
            async with self.session.post(
                f"{backend_url}/api/admin/bootstrap",
                headers=headers
            ) as resp:
                data = await resp.json()
                
                if resp.status == 200:
                    bootstrap_status = data.get('bootstrap', 'unknown')
                    print(f"✅ Bootstrap Admin: {bootstrap_status}")
                    
                    if bootstrap_status == "exists":
                        print("   ℹ️  Admin déjà existant (idempotent)")
                    elif bootstrap_status == "done":
                        print("   🎉 Admin créé avec succès")
                    
                    return True, data
                else:
                    print(f"❌ Bootstrap échoué: {resp.status}")
                    print(f"   Erreur: {data}")
                    return False, data
                    
        except Exception as e:
            print(f"❌ Erreur bootstrap: {e}")
            return False, None
    
    async def test_admin_login(self, backend_url):
        """Test connexion admin"""
        print("🔑 Test Login Admin...")
        
        try:
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            async with self.session.post(
                f"{backend_url}/api/auth/login",
                json=login_data
            ) as resp:
                data = await resp.json()
                
                if resp.status == 200 and "access_token" in data:
                    token = data["access_token"]
                    user_data = data.get("user", {})
                    print(f"✅ Login Admin réussi")
                    print(f"   Email: {user_data.get('email', 'N/A')}")
                    print(f"   Role: {user_data.get('role', 'N/A')}")
                    print(f"   Token: {token[:20]}...")
                    
                    return True, token
                else:
                    print(f"❌ Login échoué: {resp.status}")
                    print(f"   Erreur: {data}")
                    return False, None
                    
        except Exception as e:
            print(f"❌ Erreur login: {e}")
            return False, None
    
    async def check_emergency_routes(self, backend_url):
        """Vérifie et signale les routes d'urgence"""
        print("🚨 Vérification routes d'urgence...")
        
        emergency_routes = [
            "/api/emergency/admin",
            "/api/debug/admin", 
            "/api/test/admin",
            "/api/admin/debug"
        ]
        
        found_routes = []
        
        for route in emergency_routes:
            try:
                async with self.session.get(f"{backend_url}{route}") as resp:
                    if resp.status != 404:  # Route existe
                        found_routes.append((route, resp.status))
            except:
                pass  # Route n'existe pas ou erreur réseau
        
        if found_routes:
            print("⚠️ Routes d'urgence trouvées:")
            for route, status in found_routes:
                print(f"   • {route} → {status}")
            print("   💡 Recommandation: Désactiver en production")
            return found_routes
        else:
            print("✅ Aucune route d'urgence détectée")
            return []
    
    async def test_proxy_frontend(self):
        """Test proxy Vercel frontend"""
        print("🔄 Test Proxy Frontend...")
        
        try:
            # Test health via proxy
            async with self.session.get(f"{self.frontend_proxy_url}/api/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Proxy frontend fonctionnel")
                    print(f"   Status: {data.get('status', 'unknown')}")
                    return True
                else:
                    print(f"❌ Proxy frontend échoué: {resp.status}")
                    return False
        except Exception as e:
            print(f"❌ Erreur proxy frontend: {e}")
            return False
    
    async def validate_security(self, backend_url, admin_token):
        """Validation sécurité générale"""
        print("🔒 Validation Sécurité...")
        
        security_checks = []
        
        # Test 1: Headers sécurité
        try:
            async with self.session.get(f"{backend_url}/api/health") as resp:
                headers = resp.headers
                
                # Vérifier headers de sécurité importants
                security_headers = [
                    "Access-Control-Allow-Origin",
                    "Content-Type"
                ]
                
                for header in security_headers:
                    if header in headers:
                        security_checks.append(f"✅ {header}: {headers[header]}")
                    else:
                        security_checks.append(f"⚠️ {header}: manquant")
                        
        except Exception as e:
            security_checks.append(f"❌ Erreur test headers: {e}")
        
        # Test 2: Endpoints admin protégés
        if admin_token:
            try:
                # Test sans token
                async with self.session.get(f"{backend_url}/api/admin/users") as resp:
                    if resp.status == 401:
                        security_checks.append("✅ Endpoints admin protégés (401 sans token)")
                    else:
                        security_checks.append(f"⚠️ Endpoints admin non protégés: {resp.status}")
            except:
                security_checks.append("⚠️ Impossible de tester protection endpoints")
        
        print("📋 Résultats sécurité:")
        for check in security_checks:
            print(f"   {check}")
        
        return security_checks
    
    async def run_complete_bootstrap(self):
        """Exécute le bootstrap complet"""
        print("🚀 BOOTSTRAP ADMIN & SÉCURITÉ - ECOMSIMPLY")
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Backend: {self.backend_direct_url}")
        print(f"🌐 Frontend: {self.frontend_proxy_url}")
        print("=" * 60)
        
        results = {
            "backend_health": False,
            "bootstrap_admin": False,
            "admin_login": False,
            "proxy_frontend": False,
            "emergency_routes": [],
            "security_checks": [],
            "admin_token": None
        }
        
        # 1. Test santé backend
        print("\n🔍 PHASE 1: Test Backend")
        health_ok, health_data = await self.test_backend_health(self.backend_direct_url)
        results["backend_health"] = health_ok
        
        if not health_ok:
            print("❌ Backend inaccessible - Arrêt du bootstrap")
            return results
        
        # 2. Bootstrap admin
        print("\n🔍 PHASE 2: Bootstrap Admin")
        bootstrap_ok, bootstrap_data = await self.bootstrap_admin(self.backend_direct_url)
        results["bootstrap_admin"] = bootstrap_ok
        
        # 3. Test login admin
        print("\n🔍 PHASE 3: Login Admin")
        login_ok, admin_token = await self.test_admin_login(self.backend_direct_url)
        results["admin_login"] = login_ok
        results["admin_token"] = admin_token
        
        # 4. Test proxy frontend
        print("\n🔍 PHASE 4: Proxy Frontend")
        proxy_ok = await self.test_proxy_frontend()
        results["proxy_frontend"] = proxy_ok
        
        # 5. Vérification routes d'urgence
        print("\n🔍 PHASE 5: Routes d'Urgence")
        emergency_routes = await self.check_emergency_routes(self.backend_direct_url)
        results["emergency_routes"] = emergency_routes
        
        # 6. Validation sécurité
        print("\n🔍 PHASE 6: Sécurité")
        security_checks = await self.validate_security(self.backend_direct_url, admin_token)
        results["security_checks"] = security_checks
        
        # Résultats finaux
        print("\n" + "=" * 60)
        print("📊 RÉSULTATS BOOTSTRAP")
        
        success_count = sum([
            results["backend_health"],
            results["bootstrap_admin"], 
            results["admin_login"],
            results["proxy_frontend"]
        ])
        
        print(f"✅ Tests réussis: {success_count}/4")
        
        if success_count >= 3:
            print("🎉 ✅ BOOTSTRAP ADMIN RÉUSSI")
            status = "SUCCESS"
        else:
            print("❌ 🔴 BOOTSTRAP ADMIN ÉCHOUÉ")
            status = "FAILED"
        
        # Sauvegarde rapport
        bootstrap_report = {
            "timestamp": datetime.now().isoformat(),
            "backend_url": self.backend_direct_url,
            "frontend_url": self.frontend_proxy_url,
            "results": results,
            "status": status,
            "success_rate": (success_count / 4) * 100
        }
        
        with open("/app/ecomsimply-deploy/BOOTSTRAP_REPORT.json", "w") as f:
            json.dump(bootstrap_report, f, indent=2)
        
        print(f"\n📋 Rapport sauvegardé: BOOTSTRAP_REPORT.json")
        
        return results

async def main():
    """Point d'entrée principal"""
    async with AdminBootstrapService() as service:
        try:
            results = await service.run_complete_bootstrap()
            
            # Code de sortie selon succès
            success = all([
                results["backend_health"],
                results["bootstrap_admin"],
                results["admin_login"]
            ])
            
            sys.exit(0 if success else 1)
            
        except Exception as e:
            print(f"❌ Erreur critique bootstrap: {e}")
            sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())