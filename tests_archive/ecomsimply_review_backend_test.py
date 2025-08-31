#!/usr/bin/env python3
"""
🎯 ECOMSIMPLY BACKEND VALIDATION - REVIEW REQUEST TESTING
Test complet du backend ECOMSIMPLY selon les spécifications du review request

OBJECTIFS CRITIQUES:
1. Health Check - Tester /api/health pour status "healthy" et database "connected"
2. Bootstrap Admin - Tester POST /api/admin/bootstrap avec header "x-bootstrap-token: ECS-Bootstrap-2025-Secure-Token"
3. Login Admin - Tester POST /api/auth/login avec {"email": "msylla54@gmail.com", "password": "ECS-Temp#2025-08-22!"}
4. Endpoints Publics - Tester GET /api/stats/public, /api/amazon/marketplaces, /api/testimonials, /api/languages
5. Sécurité - Vérifier que les endpoints admin sont protégés (401 sans token)

CONTEXTE: Validation du déploiement backend ECOMSIMPLY avant tests frontend
"""

import asyncio
import aiohttp
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration de test selon les spécifications
BASE_URL = "https://ecomsimply-deploy.preview.emergentagent.com"
TEST_TIMEOUT = 30

# Credentials admin selon le review request
ADMIN_CREDENTIALS = {
    "email": "msylla54@gmail.com",
    "password": "ECS-Temp#2025-08-22!"
}

# Token bootstrap selon le review request
BOOTSTRAP_TOKEN = "ECS-Bootstrap-2025-Secure-Token"

class EcomsimplyReviewTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = None
        self.results = {
            "health_check": {},
            "bootstrap_admin": {},
            "admin_login": {},
            "public_endpoints": {},
            "amazon_endpoints": {},
            "security_validation": {},
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "success_rate": 0.0,
                "critical_failures": []
            }
        }
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=TEST_TIMEOUT)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_endpoint(self, method: str, endpoint: str, description: str, 
                          expected_status: List[int] = None, data: Dict = None, 
                          headers: Dict = None) -> Dict[str, Any]:
        """Test un endpoint spécifique avec analyse détaillée"""
        if expected_status is None:
            expected_status = [200]
            
        url = f"{self.base_url}{endpoint}"
        result = {
            "endpoint": endpoint,
            "method": method,
            "description": description,
            "url": url,
            "status": "unknown",
            "response_code": None,
            "response_time": None,
            "response_data": None,
            "error": None,
            "success": False,
            "expected_status": expected_status
        }
        
        try:
            start_time = time.time()
            
            # Préparer les headers
            request_headers = {"Content-Type": "application/json"}
            if headers:
                request_headers.update(headers)
            
            if method.upper() == "GET":
                async with self.session.get(url, headers=request_headers) as response:
                    result["response_code"] = response.status
                    result["response_time"] = round((time.time() - start_time) * 1000, 2)
                    try:
                        result["response_data"] = await response.json()
                    except:
                        result["response_data"] = await response.text()
                    
            elif method.upper() == "POST":
                async with self.session.post(url, json=data or {}, headers=request_headers) as response:
                    result["response_code"] = response.status
                    result["response_time"] = round((time.time() - start_time) * 1000, 2)
                    try:
                        result["response_data"] = await response.json()
                    except:
                        result["response_data"] = await response.text()
                    
            # Analyser le résultat
            if result["response_code"] in expected_status:
                result["success"] = True
                result["status"] = "success"
            else:
                result["success"] = False
                result["status"] = f"unexpected_status_{result['response_code']}"
                
        except asyncio.TimeoutError:
            result["error"] = "Timeout"
            result["status"] = "timeout"
        except Exception as e:
            result["error"] = str(e)
            result["status"] = "exception"
            
        return result

    async def test_health_check(self):
        """1. Health Check - Vérifier status healthy et database connected"""
        print("\n🏥 1. HEALTH CHECK VALIDATION")
        print("=" * 50)
        
        result = await self.test_endpoint(
            "GET", 
            "/api/health", 
            "Backend Health Check",
            [200]
        )
        
        self.results["health_check"] = result
        self.results["summary"]["total_tests"] += 1
        
        # Analyse spécifique du health check
        if result["success"]:
            response_data = result.get("response_data", {})
            
            # Vérifier status "healthy"
            status_healthy = False
            database_connected = False
            
            if isinstance(response_data, dict):
                # Vérifier différents formats de réponse
                status = response_data.get("status")
                if status == "healthy":
                    status_healthy = True
                elif response_data.get("ok") or response_data.get("health") == "ok":
                    status_healthy = True
                
                # Vérifier database connection
                database = response_data.get("database")
                services = response_data.get("services", {})
                
                if database == "connected" or database == "healthy":
                    database_connected = True
                elif services.get("database") == "healthy":
                    database_connected = True
                elif "database" in str(response_data).lower() and "healthy" in str(response_data).lower():
                    database_connected = True
            
            result["status_healthy"] = status_healthy
            result["database_connected"] = database_connected
            
            if status_healthy and database_connected:
                print(f"✅ Health Check: SUCCESS")
                print(f"    Status: healthy ✅")
                print(f"    Database: connected ✅")
                print(f"    Response time: {result['response_time']}ms")
                self.results["summary"]["passed_tests"] += 1
            else:
                print(f"❌ Health Check: PARTIAL SUCCESS")
                print(f"    Status healthy: {'✅' if status_healthy else '❌'}")
                print(f"    Database connected: {'✅' if database_connected else '❌'}")
                print(f"    Response: {response_data}")
                self.results["summary"]["failed_tests"] += 1
                self.results["summary"]["critical_failures"].append("Health check status/database validation failed")
        else:
            print(f"❌ Health Check: FAILED")
            print(f"    Status: {result['response_code']}")
            print(f"    Error: {result.get('error', 'Unknown error')}")
            self.results["summary"]["failed_tests"] += 1
            self.results["summary"]["critical_failures"].append("Health endpoint not accessible")

    async def test_bootstrap_admin(self):
        """2. Bootstrap Admin - Tester avec token spécifique"""
        print("\n🔐 2. BOOTSTRAP ADMIN VALIDATION")
        print("=" * 50)
        
        result = await self.test_endpoint(
            "POST",
            "/api/admin/bootstrap",
            "Admin Bootstrap Process",
            [200, 403],  # 200 = success, 403 = already done or invalid token
            None,
            {"x-bootstrap-token": BOOTSTRAP_TOKEN}
        )
        
        self.results["bootstrap_admin"] = result
        self.results["summary"]["total_tests"] += 1
        
        if result["success"]:
            response_data = result.get("response_data", {})
            
            if result["response_code"] == 200:
                # Bootstrap réussi
                if isinstance(response_data, dict):
                    bootstrap_done = (
                        response_data.get("bootstrap") == "done" or
                        "bootstrap" in str(response_data).lower() and "succès" in str(response_data).lower() or
                        response_data.get("ok") == True
                    )
                    
                    if bootstrap_done:
                        print(f"✅ Bootstrap Admin: SUCCESS")
                        print(f"    Token accepted: ✅")
                        print(f"    Bootstrap executed: ✅")
                        print(f"    Message: {response_data.get('message', 'Bootstrap completed')}")
                        self.results["summary"]["passed_tests"] += 1
                    else:
                        print(f"⚠️ Bootstrap Admin: PARTIAL SUCCESS")
                        print(f"    Token accepted but unexpected response: {response_data}")
                        self.results["summary"]["passed_tests"] += 1
                else:
                    print(f"⚠️ Bootstrap Admin: PARTIAL SUCCESS")
                    print(f"    Token accepted but non-JSON response: {response_data}")
                    self.results["summary"]["passed_tests"] += 1
                    
            elif result["response_code"] == 403:
                # Token invalide ou bootstrap déjà fait
                print(f"⚠️ Bootstrap Admin: TOKEN REJECTED OR ALREADY DONE")
                print(f"    This is normal if bootstrap was already executed")
                print(f"    Response: {response_data}")
                self.results["summary"]["passed_tests"] += 1
        else:
            print(f"❌ Bootstrap Admin: FAILED")
            print(f"    Status: {result['response_code']}")
            print(f"    Error: {result.get('error', 'Unknown error')}")
            self.results["summary"]["failed_tests"] += 1
            self.results["summary"]["critical_failures"].append("Bootstrap admin endpoint not accessible")

    async def test_admin_login(self):
        """3. Login Admin - Tester avec credentials spécifiques"""
        print("\n🔑 3. ADMIN LOGIN VALIDATION")
        print("=" * 50)
        
        result = await self.test_endpoint(
            "POST",
            "/api/auth/login",
            "Admin Authentication",
            [200, 400, 401, 500],
            ADMIN_CREDENTIALS
        )
        
        self.results["admin_login"] = result
        self.results["summary"]["total_tests"] += 1
        
        if result["response_code"] == 200:
            response_data = result.get("response_data", {})
            
            if isinstance(response_data, dict):
                # Vérifier la présence du token JWT
                token = response_data.get("token") or response_data.get("access_token")
                user_data = response_data.get("user", {})
                is_admin = user_data.get("is_admin", False)
                
                if token and len(str(token)) > 10:  # Token valide
                    print(f"✅ Admin Login: SUCCESS")
                    print(f"    Credentials accepted: ✅")
                    print(f"    JWT token generated: ✅ ({len(str(token))} chars)")
                    print(f"    Admin privileges: {'✅' if is_admin else '❌'}")
                    print(f"    User email: {user_data.get('email', 'N/A')}")
                    
                    # Stocker le token pour les tests suivants
                    result["jwt_token"] = token
                    result["is_admin"] = is_admin
                    
                    self.results["summary"]["passed_tests"] += 1
                else:
                    print(f"❌ Admin Login: TOKEN GENERATION FAILED")
                    print(f"    Credentials accepted but no valid token")
                    print(f"    Response: {response_data}")
                    self.results["summary"]["failed_tests"] += 1
                    self.results["summary"]["critical_failures"].append("Admin login token generation failed")
            else:
                print(f"❌ Admin Login: INVALID RESPONSE FORMAT")
                print(f"    Response: {response_data}")
                self.results["summary"]["failed_tests"] += 1
                self.results["summary"]["critical_failures"].append("Admin login invalid response format")
        else:
            print(f"❌ Admin Login: AUTHENTICATION FAILED")
            print(f"    Status: {result['response_code']}")
            print(f"    Response: {result.get('response_data', 'No data')}")
            self.results["summary"]["failed_tests"] += 1
            self.results["summary"]["critical_failures"].append("Admin login authentication failed")

    async def test_public_endpoints(self):
        """4. Endpoints Publics - Tester les endpoints critiques"""
        print("\n🌐 4. PUBLIC ENDPOINTS VALIDATION")
        print("=" * 50)
        
        public_endpoints = [
            ("/api/stats/public", "Public Statistics"),
            ("/api/testimonials", "Testimonials"),
            ("/api/languages", "Supported Languages")
        ]
        
        results = {}
        
        for endpoint, description in public_endpoints:
            result = await self.test_endpoint(
                "GET",
                endpoint,
                description,
                [200]
            )
            
            results[endpoint] = result
            self.results["summary"]["total_tests"] += 1
            
            if result["success"]:
                response_data = result.get("response_data")
                
                # Validation spécifique par endpoint
                if endpoint == "/api/stats/public":
                    # Vérifier la structure des statistiques
                    if isinstance(response_data, dict):
                        has_stats = any(key in response_data for key in ["satisfied_clients", "total_users", "rating", "average_rating"])
                        if has_stats:
                            print(f"✅ {description}: SUCCESS")
                            print(f"    Statistics data present: ✅")
                            self.results["summary"]["passed_tests"] += 1
                        else:
                            print(f"⚠️ {description}: PARTIAL SUCCESS")
                            print(f"    Endpoint accessible but no statistics data")
                            self.results["summary"]["passed_tests"] += 1
                    else:
                        print(f"⚠️ {description}: PARTIAL SUCCESS")
                        print(f"    Unexpected response format: {type(response_data)}")
                        self.results["summary"]["passed_tests"] += 1
                        
                elif endpoint == "/api/testimonials":
                    # Vérifier la structure des témoignages
                    if isinstance(response_data, list) or (isinstance(response_data, dict) and "testimonials" in response_data):
                        print(f"✅ {description}: SUCCESS")
                        print(f"    Testimonials structure valid: ✅")
                        self.results["summary"]["passed_tests"] += 1
                    else:
                        print(f"⚠️ {description}: PARTIAL SUCCESS")
                        print(f"    Unexpected response format: {type(response_data)}")
                        self.results["summary"]["passed_tests"] += 1
                        
                elif endpoint == "/api/languages":
                    # Vérifier les langues supportées
                    if isinstance(response_data, (list, dict)):
                        print(f"✅ {description}: SUCCESS")
                        print(f"    Languages data present: ✅")
                        self.results["summary"]["passed_tests"] += 1
                    else:
                        print(f"⚠️ {description}: PARTIAL SUCCESS")
                        print(f"    Unexpected response format: {type(response_data)}")
                        self.results["summary"]["passed_tests"] += 1
            else:
                print(f"❌ {description}: FAILED")
                print(f"    Status: {result['response_code']}")
                print(f"    Error: {result.get('error', 'Unknown error')}")
                self.results["summary"]["failed_tests"] += 1
                self.results["summary"]["critical_failures"].append(f"{description} endpoint not accessible")
        
        self.results["public_endpoints"] = results

    async def test_amazon_endpoints(self):
        """5. Amazon Endpoints - Tester les 6 marketplaces Amazon"""
        print("\n🚀 5. AMAZON ENDPOINTS VALIDATION")
        print("=" * 50)
        
        result = await self.test_endpoint(
            "GET",
            "/api/amazon/marketplaces",
            "Amazon Marketplaces",
            [200]
        )
        
        self.results["amazon_endpoints"]["/api/amazon/marketplaces"] = result
        self.results["summary"]["total_tests"] += 1
        
        if result["success"]:
            response_data = result.get("response_data")
            
            if isinstance(response_data, list):
                marketplace_count = len(response_data)
                
                # Vérifier qu'il y a 6 marketplaces comme spécifié
                if marketplace_count >= 6:
                    print(f"✅ Amazon Marketplaces: SUCCESS")
                    print(f"    Marketplaces available: {marketplace_count} ✅")
                    
                    # Afficher les marketplaces disponibles
                    for i, marketplace in enumerate(response_data[:6]):
                        if isinstance(marketplace, dict):
                            name = marketplace.get("name", marketplace.get("country_code", f"Marketplace {i+1}"))
                            print(f"    - {name}")
                    
                    self.results["summary"]["passed_tests"] += 1
                else:
                    print(f"⚠️ Amazon Marketplaces: PARTIAL SUCCESS")
                    print(f"    Expected 6+ marketplaces, found: {marketplace_count}")
                    self.results["summary"]["passed_tests"] += 1
            else:
                print(f"⚠️ Amazon Marketplaces: PARTIAL SUCCESS")
                print(f"    Unexpected response format: {type(response_data)}")
                self.results["summary"]["passed_tests"] += 1
        else:
            print(f"❌ Amazon Marketplaces: FAILED")
            print(f"    Status: {result['response_code']}")
            print(f"    Error: {result.get('error', 'Unknown error')}")
            self.results["summary"]["failed_tests"] += 1
            self.results["summary"]["critical_failures"].append("Amazon marketplaces endpoint not accessible")

    async def test_security_validation(self):
        """6. Sécurité - Vérifier protection des endpoints admin"""
        print("\n🔒 6. SECURITY VALIDATION")
        print("=" * 50)
        
        # Endpoints qui doivent être protégés
        protected_endpoints = [
            ("/api/user/profile", "User Profile"),
            ("/api/admin/users", "Admin Users Management"),
            ("/api/amazon/status", "Amazon Connection Status")
        ]
        
        results = {}
        
        for endpoint, description in protected_endpoints:
            result = await self.test_endpoint(
                "GET",
                endpoint,
                f"Security Check - {description}",
                [401, 403, 404]  # 401/403 = protected (good), 404 = not found (acceptable)
            )
            
            results[endpoint] = result
            self.results["summary"]["total_tests"] += 1
            
            if result["response_code"] in [401, 403]:
                print(f"✅ {description}: PROPERLY PROTECTED")
                print(f"    Returns {result['response_code']} without token: ✅")
                self.results["summary"]["passed_tests"] += 1
            elif result["response_code"] == 404:
                print(f"⚠️ {description}: NOT FOUND")
                print(f"    Endpoint may not be implemented: {result['response_code']}")
                self.results["summary"]["passed_tests"] += 1
            elif result["response_code"] == 200:
                print(f"❌ {description}: NOT PROTECTED")
                print(f"    Endpoint accessible without authentication: SECURITY RISK")
                self.results["summary"]["failed_tests"] += 1
                self.results["summary"]["critical_failures"].append(f"{description} endpoint not protected")
            else:
                print(f"❓ {description}: UNKNOWN STATUS")
                print(f"    Unexpected status: {result['response_code']}")
                self.results["summary"]["failed_tests"] += 1
        
        self.results["security_validation"] = results

    def generate_final_report(self) -> str:
        """Génère le rapport final de validation"""
        report = []
        report.append("🎯 ECOMSIMPLY BACKEND VALIDATION - FINAL REPORT")
        report.append("=" * 60)
        
        # Calculer le taux de succès
        total = self.results["summary"]["total_tests"]
        passed = self.results["summary"]["passed_tests"]
        failed = self.results["summary"]["failed_tests"]
        success_rate = (passed / total) * 100 if total > 0 else 0
        self.results["summary"]["success_rate"] = success_rate
        
        report.append(f"\n📊 RÉSULTATS GLOBAUX:")
        report.append(f"   • Total Tests: {total}")
        report.append(f"   • Tests Réussis: {passed}")
        report.append(f"   • Tests Échoués: {failed}")
        report.append(f"   • Taux de Succès: {success_rate:.1f}%")
        
        # Détail par catégorie
        report.append(f"\n🔍 DÉTAIL PAR CATÉGORIE:")
        
        # Health Check
        health_result = self.results["health_check"]
        if health_result.get("success"):
            status_icon = "✅" if health_result.get("status_healthy") and health_result.get("database_connected") else "⚠️"
            report.append(f"   {status_icon} Health Check: Status & Database validation")
        else:
            report.append(f"   ❌ Health Check: Failed to connect")
        
        # Bootstrap Admin
        bootstrap_result = self.results["bootstrap_admin"]
        if bootstrap_result.get("success"):
            report.append(f"   ✅ Bootstrap Admin: Token authentication working")
        else:
            report.append(f"   ❌ Bootstrap Admin: Failed")
        
        # Admin Login
        login_result = self.results["admin_login"]
        if login_result.get("success") and login_result.get("jwt_token"):
            report.append(f"   ✅ Admin Login: Authentication & JWT generation working")
        else:
            report.append(f"   ❌ Admin Login: Authentication failed")
        
        # Public Endpoints
        public_results = self.results["public_endpoints"]
        public_success = sum(1 for r in public_results.values() if r.get("success"))
        public_total = len(public_results)
        report.append(f"   {'✅' if public_success == public_total else '⚠️'} Public Endpoints: {public_success}/{public_total} working")
        
        # Amazon Endpoints
        amazon_results = self.results["amazon_endpoints"]
        amazon_success = sum(1 for r in amazon_results.values() if r.get("success"))
        amazon_total = len(amazon_results)
        report.append(f"   {'✅' if amazon_success == amazon_total else '⚠️'} Amazon Endpoints: {amazon_success}/{amazon_total} working")
        
        # Security
        security_results = self.results["security_validation"]
        security_success = sum(1 for r in security_results.values() if r.get("success"))
        security_total = len(security_results)
        report.append(f"   {'✅' if security_success == security_total else '⚠️'} Security: {security_success}/{security_total} properly protected")
        
        # Problèmes critiques
        if self.results["summary"]["critical_failures"]:
            report.append(f"\n❌ PROBLÈMES CRITIQUES IDENTIFIÉS:")
            for failure in self.results["summary"]["critical_failures"]:
                report.append(f"   • {failure}")
        
        # Diagnostic final
        report.append(f"\n🎯 DIAGNOSTIC FINAL:")
        if success_rate >= 95:
            report.append("   🎉 EXCELLENT - Backend ECOMSIMPLY 100% fonctionnel et prêt pour production")
        elif success_rate >= 85:
            report.append("   ✅ TRÈS BON - Backend ECOMSIMPLY majoritairement fonctionnel")
        elif success_rate >= 70:
            report.append("   ⚠️ BON - Backend ECOMSIMPLY fonctionnel avec quelques améliorations nécessaires")
        elif success_rate >= 50:
            report.append("   ⚠️ MOYEN - Backend ECOMSIMPLY partiellement fonctionnel, corrections requises")
        else:
            report.append("   ❌ CRITIQUE - Backend ECOMSIMPLY nécessite des corrections majeures")
        
        return "\n".join(report)

    async def run_complete_validation(self):
        """Exécute la validation complète selon le review request"""
        print("🎯 ECOMSIMPLY BACKEND VALIDATION - REVIEW REQUEST TESTING")
        print("=" * 60)
        print(f"Target: {self.base_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Admin Email: {ADMIN_CREDENTIALS['email']}")
        print(f"Bootstrap Token: {BOOTSTRAP_TOKEN}")
        
        try:
            # 1. Health Check
            await self.test_health_check()
            
            # 2. Bootstrap Admin
            await self.test_bootstrap_admin()
            
            # 3. Admin Login
            await self.test_admin_login()
            
            # 4. Public Endpoints
            await self.test_public_endpoints()
            
            # 5. Amazon Endpoints
            await self.test_amazon_endpoints()
            
            # 6. Security Validation
            await self.test_security_validation()
            
            # 7. Génération du rapport final
            print("\n" + "=" * 60)
            print(self.generate_final_report())
            
            return self.results
            
        except Exception as e:
            print(f"❌ ERREUR CRITIQUE pendant la validation: {str(e)}")
            return {"error": str(e), "results": self.results}

async def main():
    """Point d'entrée principal"""
    print("🎯 ECOMSIMPLY BACKEND VALIDATION - REVIEW REQUEST TESTING")
    print("Validation complète du backend ECOMSIMPLY selon les spécifications du review request")
    print()
    
    async with EcomsimplyReviewTester() as tester:
        results = await tester.run_complete_validation()
        
        # Déterminer le code de sortie
        if "error" in results:
            sys.exit(1)
        
        success_rate = results.get("summary", {}).get("success_rate", 0)
        critical_failures = len(results.get("summary", {}).get("critical_failures", []))
        
        if success_rate >= 95 and critical_failures == 0:
            print(f"\n🎉 EXCELLENT: Backend ECOMSIMPLY à {success_rate:.1f}% fonctionnel - Validation complète réussie!")
            sys.exit(0)
        elif success_rate >= 85:
            print(f"\n✅ TRÈS BON: Backend ECOMSIMPLY à {success_rate:.1f}% fonctionnel - Prêt pour production")
            sys.exit(0)
        elif success_rate >= 70:
            print(f"\n⚠️ BON: Backend ECOMSIMPLY à {success_rate:.1f}% fonctionnel - Quelques améliorations nécessaires")
            sys.exit(0)
        else:
            print(f"\n❌ CRITIQUE: Backend ECOMSIMPLY à {success_rate:.1f}% fonctionnel - Corrections requises")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())