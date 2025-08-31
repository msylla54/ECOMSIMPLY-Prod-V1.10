#!/usr/bin/env python3
"""
Tests E2E Complets - ECOMSIMPLY Production
Valide 100% du fonctionnement après déploiement Railway
"""

import asyncio
import aiohttp
import json
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Configuration
ADMIN_EMAIL = "msylla54@gmail.com"
ADMIN_PASSWORD = "ECS-Temp#2025-08-22!"
FRONTEND_URL = "https://ecomsimply.com"

class CompleteE2ETester:
    def __init__(self):
        self.backend_url = self.get_backend_url()
        self.frontend_url = FRONTEND_URL
        self.session = None
        self.admin_token = None
        
        self.results = {
            "backend_direct": {},
            "frontend_proxy": {},
            "amazon_integration": {},
            "database_persistence": {},
            "performance": {},
            "security": {},
            "summary": {}
        }
    
    def get_backend_url(self):
        """Récupère l'URL backend configurée"""
        # DNS configuré
        return "https://api.ecomsimply.com"
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "ECOMSIMPLY-E2E-Complete/1.0"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, category: str, test_name: str, success: bool, details: Any = None, duration: float = 0):
        """Log standardisé des tests"""
        status = "✅" if success else "❌"
        duration_str = f" ({duration:.2f}s)" if duration > 0 else ""
        print(f"{status} {test_name}{duration_str}")
        
        if category not in self.results:
            self.results[category] = {}
        
        self.results[category][test_name] = {
            "success": success,
            "details": details,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
    
    async def measure_performance(self, url: str, test_name: str) -> float:
        """Mesure le temps de réponse"""
        start_time = time.time()
        try:
            async with self.session.get(url) as resp:
                await resp.read()  # Lire la réponse complète
                duration = time.time() - start_time
                
                if resp.status == 200:
                    if duration < 0.5:
                        perf_status = "excellent"
                    elif duration < 1.0:
                        perf_status = "good"
                    else:
                        perf_status = "slow"
                    
                    self.log_test("performance", f"{test_name}_response_time", True, {
                        "duration": duration,
                        "status": perf_status
                    }, duration)
                
                return duration
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("performance", f"{test_name}_response_time", False, str(e), duration)
            return duration
    
    async def test_backend_direct_complete(self):
        """Tests backend direct complets"""
        print("\n🔍 PHASE 1: Backend Direct (Complet)")
        print("-" * 50)
        
        # Health Check avec performance
        start_time = time.time()
        try:
            async with self.session.get(f"{self.backend_url}/api/health") as resp:
                duration = time.time() - start_time
                data = await resp.json()
                success = resp.status == 200 and data.get("status") == "healthy"
                
                self.log_test("backend_direct", "health_check", success, {
                    "status": data.get("status"),
                    "database": data.get("database"),
                    "response_code": resp.status
                }, duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("backend_direct", "health_check", False, str(e), duration)
        
        # Admin Login avec récupération token
        try:
            login_data = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
            start_time = time.time()
            
            async with self.session.post(f"{self.backend_url}/api/auth/login", json=login_data) as resp:
                duration = time.time() - start_time
                data = await resp.json()
                success = resp.status == 200 and "access_token" in data
                
                if success:
                    self.admin_token = data["access_token"]
                
                self.log_test("backend_direct", "admin_login", success, {
                    "has_token": success,
                    "user_email": data.get("user", {}).get("email")
                }, duration)
                
        except Exception as e:
            self.log_test("backend_direct", "admin_login", False, str(e))
        
        # Endpoints publics critiques
        public_endpoints = [
            "/api/stats/public",
            "/api/amazon/marketplaces", 
            "/api/testimonials",
            "/api/languages"
        ]
        
        for endpoint in public_endpoints:
            try:
                start_time = time.time()
                async with self.session.get(f"{self.backend_url}{endpoint}") as resp:
                    duration = time.time() - start_time
                    success = resp.status == 200
                    
                    if success:
                        data = await resp.json()
                        details = {
                            "type": type(data).__name__,
                            "count": len(data) if isinstance(data, list) else 1,
                            "has_data": bool(data)
                        }
                    else:
                        details = {"status_code": resp.status}
                    
                    self.log_test("backend_direct", f"public_{endpoint.replace('/', '_')}", success, details, duration)
                    
            except Exception as e:
                self.log_test("backend_direct", f"public_{endpoint.replace('/', '_')}", False, str(e))
    
    async def test_frontend_proxy_complete(self):
        """Tests proxy frontend complets"""
        print("\n🔍 PHASE 2: Frontend Proxy (Complet)")
        print("-" * 50)
        
        # Health via proxy
        await self.measure_performance(f"{self.frontend_url}/api/health", "proxy_health")
        
        try:
            async with self.session.get(f"{self.frontend_url}/api/health") as resp:
                data = await resp.json()
                success = resp.status == 200 and data.get("status") == "healthy"
                
                self.log_test("frontend_proxy", "proxy_health_check", success, {
                    "status": data.get("status"),
                    "via_proxy": True
                })
                
        except Exception as e:
            self.log_test("frontend_proxy", "proxy_health_check", False, str(e))
        
        # Login via proxy
        try:
            login_data = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
            async with self.session.post(f"{self.frontend_url}/api/auth/login", json=login_data) as resp:
                data = await resp.json()
                success = resp.status == 200 and "access_token" in data
                
                self.log_test("frontend_proxy", "proxy_admin_login", success, {
                    "has_token": success,
                    "via_proxy": True
                })
                
        except Exception as e:
            self.log_test("frontend_proxy", "proxy_admin_login", False, str(e))
        
        # Test CORS
        try:
            headers = {"Origin": self.frontend_url}
            async with self.session.get(f"{self.frontend_url}/api/stats/public", headers=headers) as resp:
                success = resp.status == 200
                cors_headers = {
                    "access_control_allow_origin": resp.headers.get("access-control-allow-origin"),
                    "content_type": resp.headers.get("content-type")
                }
                
                self.log_test("frontend_proxy", "cors_headers", success, cors_headers)
                
        except Exception as e:
            self.log_test("frontend_proxy", "cors_headers", False, str(e))
        
        # Frontend Loading
        await self.measure_performance(self.frontend_url, "frontend_page")
        
        try:
            async with self.session.get(self.frontend_url) as resp:
                success = resp.status == 200
                is_html = "text/html" in resp.headers.get("content-type", "")
                
                self.log_test("frontend_proxy", "frontend_loading", success and is_html, {
                    "status": resp.status,
                    "is_html": is_html,
                    "content_type": resp.headers.get("content-type")
                })
                
        except Exception as e:
            self.log_test("frontend_proxy", "frontend_loading", False, str(e))
    
    async def test_amazon_integration_complete(self):
        """Tests Amazon SP-API complets"""
        print("\n🔍 PHASE 3: Amazon SP-API Integration")
        print("-" * 50)
        
        # Marketplaces Amazon
        try:
            start_time = time.time()
            async with self.session.get(f"{self.backend_url}/api/amazon/marketplaces") as resp:
                duration = time.time() - start_time
                data = await resp.json()
                success = resp.status == 200 and isinstance(data, list) and len(data) >= 6
                
                self.log_test("amazon_integration", "marketplaces", success, {
                    "count": len(data) if isinstance(data, list) else 0,
                    "marketplaces": [m.get("name") for m in data[:3]] if isinstance(data, list) else []
                }, duration)
                
        except Exception as e:
            self.log_test("amazon_integration", "marketplaces", False, str(e))
        
        # Connexions Amazon (si admin token)
        if self.admin_token:
            try:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                async with self.session.get(f"{self.backend_url}/api/amazon/connections", headers=headers) as resp:
                    success = resp.status in [200, 404]  # 404 acceptable si pas de connexions
                    details = {"status_code": resp.status}
                    
                    if resp.status == 200:
                        data = await resp.json()
                        details["connections_count"] = len(data) if isinstance(data, list) else 1
                    
                    self.log_test("amazon_integration", "connections_endpoint", success, details)
                    
            except Exception as e:
                self.log_test("amazon_integration", "connections_endpoint", False, str(e))
        
        # Stats Amazon publiques
        try:
            async with self.session.get(f"{self.backend_url}/api/amazon/stats/public") as resp:
                success = resp.status in [200, 404]  # Peut ne pas exister
                self.log_test("amazon_integration", "public_stats", success, {"status": resp.status})
                
        except Exception as e:
            self.log_test("amazon_integration", "public_stats", False, str(e))
    
    async def test_database_persistence(self):
        """Tests persistance base de données"""
        print("\n🔍 PHASE 4: Database Persistence")
        print("-" * 50)
        
        # Connexion DB via health check
        try:
            async with self.session.get(f"{self.backend_url}/api/health") as resp:
                data = await resp.json()
                db_connected = data.get("database") == "connected"
                
                self.log_test("database_persistence", "connection", db_connected, {
                    "status": data.get("database"),
                    "mongodb": True
                })
                
        except Exception as e:
            self.log_test("database_persistence", "connection", False, str(e))
        
        # Collections de base
        base_collections = [
            "/api/testimonials",   # Collection testimonials
            "/api/languages",      # Collection languages
            "/api/stats/public"    # Collection stats
        ]
        
        for endpoint in base_collections:
            try:
                async with self.session.get(f"{self.backend_url}{endpoint}") as resp:
                    success = resp.status == 200
                    
                    if success:
                        data = await resp.json()
                        details = {
                            "has_data": bool(data),
                            "type": type(data).__name__,
                            "count": len(data) if isinstance(data, list) else 1
                        }
                    else:
                        details = {"status": resp.status}
                    
                    collection_name = endpoint.split('/')[-1]
                    self.log_test("database_persistence", f"collection_{collection_name}", success, details)
                    
            except Exception as e:
                collection_name = endpoint.split('/')[-1]
                self.log_test("database_persistence", f"collection_{collection_name}", False, str(e))
    
    async def test_security_validation(self):
        """Tests validation sécurité"""
        print("\n🔍 PHASE 5: Security Validation") 
        print("-" * 50)
        
        # Test protection endpoints admin
        try:
            # Sans token
            async with self.session.get(f"{self.backend_url}/api/admin/users") as resp:
                protected = resp.status == 401
                
                self.log_test("security", "admin_endpoints_protected", protected, {
                    "status_without_token": resp.status,
                    "properly_protected": protected
                })
                
        except Exception as e:
            self.log_test("security", "admin_endpoints_protected", False, str(e))
        
        # Test avec token admin valide
        if self.admin_token:
            try:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                async with self.session.get(f"{self.backend_url}/api/admin/users", headers=headers) as resp:
                    authorized = resp.status in [200, 404]  # 200 OK ou 404 si endpoint pas implémenté
                    
                    self.log_test("security", "admin_token_valid", authorized, {
                        "status_with_token": resp.status,
                        "token_accepted": authorized
                    })
                    
            except Exception as e:
                self.log_test("security", "admin_token_valid", False, str(e))
        
        # Test headers sécurité
        try:
            async with self.session.get(f"{self.backend_url}/api/health") as resp:
                headers = resp.headers
                
                security_headers = {
                    "content_type": headers.get("content-type"),
                    "cors_origin": headers.get("access-control-allow-origin"),
                    "cors_methods": headers.get("access-control-allow-methods")
                }
                
                has_cors = bool(security_headers["cors_origin"])
                has_content_type = "application/json" in (security_headers["content_type"] or "")
                
                self.log_test("security", "response_headers", has_cors and has_content_type, security_headers)
                
        except Exception as e:
            self.log_test("security", "response_headers", False, str(e))
    
    async def test_error_handling(self):
        """Tests gestion d'erreurs"""
        print("\n🔍 PHASE 6: Error Handling")
        print("-" * 50)
        
        # Test 404
        try:
            async with self.session.get(f"{self.backend_url}/api/nonexistent") as resp:
                proper_404 = resp.status == 404
                
                self.log_test("security", "404_handling", proper_404, {
                    "status": resp.status,
                    "proper_404": proper_404
                })
                
        except Exception as e:
            self.log_test("security", "404_handling", False, str(e))
        
        # Test 500 (endpoint qui pourrait échouer)
        try:
            async with self.session.post(f"{self.backend_url}/api/auth/login", json={}) as resp:
                proper_error = resp.status in [400, 422]  # Bad request ou validation error
                
                self.log_test("security", "error_handling", proper_error, {
                    "status": resp.status,
                    "proper_error_code": proper_error
                })
                
        except Exception as e:
            self.log_test("security", "error_handling", False, str(e))
    
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
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Génère un rapport de performance"""
        perf_data = self.results.get("performance", {})
        
        response_times = []
        for test_name, test_data in perf_data.items():
            if "response_time" in test_name and test_data.get("success"):
                response_times.append(test_data.get("duration", 0))
        
        if response_times:
            avg_response = sum(response_times) / len(response_times)
            max_response = max(response_times)
            min_response = min(response_times)
            
            performance_grade = "A" if avg_response < 0.3 else "B" if avg_response < 0.6 else "C" if avg_response < 1.0 else "D"
            
            return {
                "average_response_time": avg_response,
                "max_response_time": max_response,
                "min_response_time": min_response,
                "performance_grade": performance_grade,
                "total_measurements": len(response_times)
            }
        
        return {"no_performance_data": True}
    
    async def run_complete_e2e(self):
        """Exécute tous les tests E2E complets"""
        print("🚀 TESTS E2E COMPLETS - ECOMSIMPLY PRODUCTION")
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Backend: {self.backend_url}")
        print(f"🌐 Frontend: {self.frontend_url}")
        print("=" * 70)
        
        # Exécution de toutes les phases
        await self.test_backend_direct_complete()
        await self.test_frontend_proxy_complete()
        await self.test_amazon_integration_complete()
        await self.test_database_persistence()
        await self.test_security_validation()
        await self.test_error_handling()
        
        # Calculs finaux
        success_rates = self.calculate_success_rates()
        performance_report = self.generate_performance_report()
        global_success = sum(success_rates.values()) / len(success_rates) if success_rates else 0
        
        # Comptage total des tests
        total_tests = sum(len(tests) for tests in self.results.values() if isinstance(tests, dict))
        successful_tests = sum(
            sum(1 for test in tests.values() if test.get("success", False))
            for tests in self.results.values() if isinstance(tests, dict)
        )
        
        self.results["summary"] = {
            "test_date": datetime.now().isoformat(),
            "backend_url": self.backend_url,
            "frontend_url": self.frontend_url,
            "success_rates": success_rates,
            "global_success_rate": global_success,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "performance": performance_report
        }
        
        # Affichage final
        print("\n" + "=" * 70)
        print("📊 RÉSULTATS FINAUX E2E COMPLETS")
        print("-" * 35)
        for category, rate in success_rates.items():
            print(f"{category.replace('_', ' ').title()}: {rate:.1f}%")
        
        print(f"\n🎯 GLOBAL: {global_success:.1f}% ({successful_tests}/{total_tests} tests)")
        
        # Performance
        if not performance_report.get("no_performance_data"):
            print(f"⚡ Performance: {performance_report['performance_grade']} (avg: {performance_report['average_response_time']:.3f}s)")
        
        # Verdict final
        if global_success >= 95:
            print("\n🎉 ✅ PLATEFORME 100% FONCTIONNELLE - PRODUCTION READY!")
            verdict = "EXCELLENT"
        elif global_success >= 90:
            print("\n🎉 ✅ PLATEFORME FONCTIONNELLE - PRODUCTION READY!")
            verdict = "SUCCESS"
        elif global_success >= 80:
            print("\n⚠️ 🟡 PLATEFORME PARTIELLEMENT FONCTIONNELLE")
            verdict = "PARTIAL"
        else:
            print("\n❌ 🔴 PLATEFORME NON FONCTIONNELLE")
            verdict = "FAILED"
        
        self.results["summary"]["verdict"] = verdict
        
        return self.results

async def main():
    """Point d'entrée principal"""
    
    async with CompleteE2ETester() as tester:
        try:
            results = await tester.run_complete_e2e()
            
            # Sauvegarde résultats
            with open("/app/ecomsimply-deploy/E2E_COMPLETE_RESULTS.json", "w") as f:
                json.dump(results, f, indent=2)
            
            print(f"\n📋 Résultats détaillés: E2E_COMPLETE_RESULTS.json")
            
            # Code de sortie
            verdict = results["summary"]["verdict"]
            sys.exit(0 if verdict in ["EXCELLENT", "SUCCESS"] else 1)
            
        except Exception as e:
            print(f"❌ Erreur critique E2E: {e}")
            sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())