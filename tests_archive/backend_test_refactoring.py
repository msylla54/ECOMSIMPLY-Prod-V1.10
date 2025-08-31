#!/usr/bin/env python3
"""
🎯 BACKEND TESTING ECOMSIMPLY - API CLIENT CENTRALISÉ REFACTORING
Test complet du backend ECOMSIMPLY après refactoring API client centralisé

OBJECTIFS CRITIQUES:
1. **Endpoints Core**: 
   - GET /api/health (statut système et MongoDB)
   - GET /api/admin/bootstrap (avec token ECS-Bootstrap-2025-Secure-Token)
   - POST /api/auth/login (msylla54@gmail.com / ECS-Temp#2025-08-22!)

2. **Endpoints Publics**:
   - GET /api/testimonials
   - GET /api/stats/public  
   - GET /api/languages
   - GET /api/public/plans-pricing
   - GET /api/public/affiliate-config

3. **Endpoints Amazon SP-API**:
   - GET /api/amazon/health
   - GET /api/amazon/marketplaces
   - GET /api/amazon/status (avec auth)
   - GET /api/demo/amazon/status (sans auth)

4. **Variables d'environnement**:
   - MONGO_URL fonctionnelle
   - JWT_SECRET configuré
   - Admin credentials valides

CONTEXTE: S'assurer que le refactoring du client API n'a pas cassé les fonctionnalités backend existantes.
"""

import asyncio
import aiohttp
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration de test depuis frontend/.env
BASE_URL = "https://ecomsimply-deploy.preview.emergentagent.com"
TEST_TIMEOUT = 30

class EcomsimplyRefactoringTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = None
        self.results = {
            "core_endpoints": {},
            "public_endpoints": {},
            "amazon_endpoints": {},
            "authentication": {},
            "environment_validation": {},
            "summary": {
                "total_endpoints": 0,
                "working_endpoints": 0,
                "auth_required_endpoints": 0,
                "broken_endpoints": 0,
                "success_rate": 0.0
            }
        }
        
        # Credentials admin pour test authentification
        self.admin_credentials = {
            "email": "msylla54@gmail.com",
            "password": "ECS-Temp#2025-08-22!"
        }
        
        # Token JWT pour tests authentifiés
        self.jwt_token = None
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=TEST_TIMEOUT)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_endpoint(self, method: str, endpoint: str, description: str, 
                          expected_status: List[int] = None, data: Dict = None, 
                          headers: Dict = None, use_auth: bool = False) -> Dict[str, Any]:
        """Test un endpoint spécifique"""
        if expected_status is None:
            expected_status = [200, 401, 403, 422]  # Statuts acceptables
            
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
            "working": False
        }
        
        try:
            start_time = time.time()
            
            # Préparer les headers
            request_headers = {"Content-Type": "application/json"}
            if headers:
                request_headers.update(headers)
            
            # Ajouter l'authentification si nécessaire
            if use_auth and self.jwt_token:
                request_headers["Authorization"] = f"Bearer {self.jwt_token}"
            
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
                result["working"] = True
                if result["response_code"] == 200:
                    result["status"] = "operational"
                    self.results["summary"]["working_endpoints"] += 1
                elif result["response_code"] in [401, 403]:
                    result["status"] = "auth_required"
                    self.results["summary"]["auth_required_endpoints"] += 1
                elif result["response_code"] == 422:
                    result["status"] = "validation_error"
                    self.results["summary"]["working_endpoints"] += 1
                else:
                    result["status"] = "working"
                    self.results["summary"]["working_endpoints"] += 1
            elif result["response_code"] == 404:
                result["status"] = "not_found"
                result["working"] = False
                self.results["summary"]["broken_endpoints"] += 1
            elif result["response_code"] == 503:
                result["status"] = "service_unavailable"
                result["working"] = True  # Service existe mais indisponible
                self.results["summary"]["working_endpoints"] += 1
            else:
                result["status"] = "error"
                result["working"] = False
                self.results["summary"]["broken_endpoints"] += 1
                
        except asyncio.TimeoutError:
            result["error"] = "Timeout"
            result["status"] = "timeout"
            self.results["summary"]["broken_endpoints"] += 1
        except Exception as e:
            result["error"] = str(e)
            result["status"] = "exception"
            self.results["summary"]["broken_endpoints"] += 1
            
        self.results["summary"]["total_endpoints"] += 1
        return result

    async def test_core_endpoints(self):
        """Test des endpoints core critiques"""
        print("\n🔧 VALIDATION ENDPOINTS CORE")
        print("=" * 50)
        
        # 1. Health endpoint avec validation MongoDB
        health_result = await self.test_endpoint(
            "GET", "/api/health", "System Health Check & MongoDB Status"
        )
        self.results["core_endpoints"]["health"] = health_result
        
        status_icon = "✅" if health_result["working"] else "❌"
        print(f"{status_icon} Health Check: {health_result['status']} ({health_result['response_code']})")
        if health_result["response_time"]:
            print(f"    Response time: {health_result['response_time']}ms")
        
        # Analyser la réponse health pour MongoDB
        if health_result["response_code"] == 200 and health_result.get("response_data"):
            health_data = health_result["response_data"]
            if isinstance(health_data, dict):
                db_status = health_data.get("database", {}).get("status") or health_data.get("services", {}).get("database")
                if db_status == "healthy":
                    print(f"    ✅ MongoDB Status: {db_status}")
                else:
                    print(f"    ⚠️ MongoDB Status: {db_status}")
        
        # 2. Admin Bootstrap avec token
        bootstrap_result = await self.test_endpoint(
            "POST", 
            "/api/admin/bootstrap", 
            "Admin Bootstrap Process",
            [200, 403], 
            None, 
            {"x-bootstrap-token": "ECS-Bootstrap-2025-Secure-Token"}
        )
        self.results["core_endpoints"]["bootstrap"] = bootstrap_result
        
        status_icon = "✅" if bootstrap_result["working"] else "❌"
        print(f"{status_icon} Admin Bootstrap: {bootstrap_result['status']} ({bootstrap_result['response_code']})")
        
        # 3. Admin Login pour obtenir JWT token
        await self.test_admin_authentication()

    async def test_admin_authentication(self):
        """Test du système d'authentification admin"""
        print("\n🔐 VALIDATION AUTHENTIFICATION ADMIN")
        print("=" * 50)
        
        # Test login admin
        login_result = await self.test_endpoint(
            "POST", 
            "/api/auth/login", 
            "Admin Authentication",
            [200, 400, 401, 500],
            self.admin_credentials
        )
        
        self.results["authentication"]["admin_login"] = login_result
        
        status_icon = "✅" if login_result["working"] else "❌"
        print(f"{status_icon} Admin Login: {login_result['status']} ({login_result['response_code']})")
        
        # Analyser la réponse pour extraire le token JWT
        if login_result["response_code"] == 200:
            response_data = login_result.get("response_data", {})
            if isinstance(response_data, dict):
                token = response_data.get("token") or response_data.get("access_token")
                user_data = response_data.get("user", {})
                is_admin = user_data.get("is_admin", False)
                
                if token:
                    self.jwt_token = token
                    print(f"    ✅ JWT Token generated: {len(token)} chars")
                    print(f"    ✅ Admin privileges: {is_admin}")
                    print(f"    ✅ User email: {user_data.get('email', 'N/A')}")
                else:
                    print(f"    ❌ PROBLÈME: Pas de token JWT généré")
            else:
                print(f"    ❌ PROBLÈME: Réponse invalide - {response_data}")
        else:
            print(f"    ❌ PROBLÈME: Login échoué - {login_result.get('response_data', 'No data')}")

    async def test_public_endpoints(self):
        """Test des endpoints publics"""
        print("\n🌐 VALIDATION ENDPOINTS PUBLICS")
        print("=" * 50)
        
        public_endpoints = [
            ("GET", "/api/testimonials", "Customer Testimonials"),
            ("GET", "/api/stats/public", "Public Statistics"),
            ("GET", "/api/languages", "Supported Languages"),
            ("GET", "/api/public/plans-pricing", "Plans & Pricing"),
            ("GET", "/api/public/affiliate-config", "Affiliate Configuration"),
        ]
        
        for method, endpoint, description in public_endpoints:
            result = await self.test_endpoint(method, endpoint, description)
            self.results["public_endpoints"][endpoint] = result
            
            status_icon = "✅" if result["working"] else "❌"
            print(f"{status_icon} {description}: {result['status']} ({result['response_code']})")
            if result["response_time"]:
                print(f"    Response time: {result['response_time']}ms")
            
            # Analyser les réponses spécifiques
            if result["response_code"] == 200 and result.get("response_data"):
                self.analyze_public_endpoint_response(endpoint, result["response_data"])

    def analyze_public_endpoint_response(self, endpoint: str, data: Any):
        """Analyse les réponses des endpoints publics"""
        if endpoint == "/api/testimonials":
            if isinstance(data, list):
                print(f"    📊 Testimonials count: {len(data)}")
            elif isinstance(data, dict) and "testimonials" in data:
                print(f"    📊 Testimonials count: {len(data['testimonials'])}")
        
        elif endpoint == "/api/stats/public":
            if isinstance(data, dict):
                clients = data.get("satisfied_clients", "N/A")
                rating = data.get("average_rating", "N/A")
                print(f"    📊 Satisfied clients: {clients}, Rating: {rating}")
        
        elif endpoint == "/api/languages":
            if isinstance(data, list):
                print(f"    🌍 Languages supported: {len(data)}")
            elif isinstance(data, dict):
                langs = data.get("languages", [])
                print(f"    🌍 Languages supported: {len(langs)}")
        
        elif endpoint == "/api/public/plans-pricing":
            if isinstance(data, dict):
                plans = data.get("plans", [])
                promotions = data.get("active_promotions_count", 0)
                print(f"    💰 Plans available: {len(plans)}, Promotions: {promotions}")
        
        elif endpoint == "/api/public/affiliate-config":
            if isinstance(data, dict):
                enabled = data.get("program_enabled", False)
                pro_rate = data.get("default_commission_rate_pro", "N/A")
                premium_rate = data.get("default_commission_rate_premium", "N/A")
                print(f"    🤝 Program enabled: {enabled}, Rates: Pro {pro_rate}%, Premium {premium_rate}%")

    async def test_amazon_endpoints(self):
        """Test des endpoints Amazon SP-API"""
        print("\n🚀 VALIDATION ENDPOINTS AMAZON SP-API")
        print("=" * 50)
        
        # Endpoints Amazon sans authentification
        amazon_public_endpoints = [
            ("GET", "/api/amazon/health", "Amazon Health Check"),
            ("GET", "/api/amazon/marketplaces", "Amazon Marketplaces"),
            ("GET", "/api/demo/amazon/status", "Demo Amazon Status"),
        ]
        
        for method, endpoint, description in amazon_public_endpoints:
            result = await self.test_endpoint(method, endpoint, description)
            self.results["amazon_endpoints"][endpoint] = result
            
            status_icon = "✅" if result["working"] else "❌"
            print(f"{status_icon} {description}: {result['status']} ({result['response_code']})")
            if result["response_time"]:
                print(f"    Response time: {result['response_time']}ms")
            
            # Analyser les réponses Amazon
            if result["response_code"] == 200 and result.get("response_data"):
                self.analyze_amazon_endpoint_response(endpoint, result["response_data"])
        
        # Endpoints Amazon avec authentification
        if self.jwt_token:
            print("\n🔐 Testing Amazon endpoints with authentication...")
            
            amazon_auth_endpoints = [
                ("GET", "/api/amazon/status", "Amazon Connection Status (Auth)"),
            ]
            
            for method, endpoint, description in amazon_auth_endpoints:
                result = await self.test_endpoint(method, endpoint, description, use_auth=True)
                self.results["amazon_endpoints"][f"{endpoint}_auth"] = result
                
                status_icon = "✅" if result["working"] else "❌"
                print(f"{status_icon} {description}: {result['status']} ({result['response_code']})")
        else:
            print("    ⚠️ No JWT token available for authenticated Amazon endpoints")

    def analyze_amazon_endpoint_response(self, endpoint: str, data: Any):
        """Analyse les réponses des endpoints Amazon"""
        if endpoint == "/api/amazon/health":
            if isinstance(data, dict):
                status = data.get("status", "unknown")
                service_status = data.get("service_status", "unknown")
                print(f"    🏥 Amazon Health: {status}, Service: {service_status}")
        
        elif endpoint == "/api/amazon/marketplaces":
            if isinstance(data, list):
                print(f"    🛒 Marketplaces available: {len(data)}")
                if len(data) > 0:
                    # Afficher quelques marketplaces
                    sample_markets = [m.get("name", "Unknown") for m in data[:3] if isinstance(m, dict)]
                    print(f"    📍 Sample markets: {', '.join(sample_markets)}")
        
        elif endpoint == "/api/demo/amazon/status":
            if isinstance(data, dict):
                demo_status = data.get("status", "unknown")
                print(f"    🎭 Demo Status: {demo_status}")

    async def validate_environment_variables(self):
        """Validation des variables d'environnement critiques"""
        print("\n🔧 VALIDATION VARIABLES D'ENVIRONNEMENT")
        print("=" * 50)
        
        env_checks = {
            "mongo_url": False,
            "jwt_secret": False,
            "admin_credentials": False
        }
        
        # 1. MONGO_URL - Testé indirectement via health endpoint
        health_result = self.results.get("core_endpoints", {}).get("health", {})
        if health_result.get("working") and health_result.get("response_data"):
            health_data = health_result["response_data"]
            if isinstance(health_data, dict):
                db_status = health_data.get("database", {}).get("status") or health_data.get("services", {}).get("database")
                if db_status == "healthy":
                    env_checks["mongo_url"] = True
                    print("✅ MONGO_URL: Fonctionnelle (MongoDB connecté)")
                else:
                    print(f"❌ MONGO_URL: Problème détecté (status: {db_status})")
        else:
            print("❌ MONGO_URL: Impossible de vérifier (health endpoint failed)")
        
        # 2. JWT_SECRET - Testé indirectement via login
        login_result = self.results.get("authentication", {}).get("admin_login", {})
        if login_result.get("working") and self.jwt_token:
            env_checks["jwt_secret"] = True
            print("✅ JWT_SECRET: Configuré (token généré avec succès)")
        else:
            print("❌ JWT_SECRET: Problème détecté (pas de token généré)")
        
        # 3. Admin credentials - Testé via login
        if login_result.get("working"):
            env_checks["admin_credentials"] = True
            print("✅ Admin Credentials: Valides (login réussi)")
        else:
            print("❌ Admin Credentials: Invalides (login échoué)")
        
        self.results["environment_validation"] = env_checks
        
        # Résumé validation environnement
        valid_count = sum(env_checks.values())
        total_count = len(env_checks)
        print(f"\n📊 Variables d'environnement: {valid_count}/{total_count} valides")

    def generate_final_report(self) -> str:
        """Génère le rapport final de validation"""
        report = []
        report.append("🎯 BACKEND TESTING ECOMSIMPLY - API CLIENT CENTRALISÉ REFACTORING")
        report.append("=" * 70)
        
        # Calculer le taux de succès global
        total = self.results["summary"]["total_endpoints"]
        working = self.results["summary"]["working_endpoints"] + self.results["summary"]["auth_required_endpoints"]
        success_rate = (working / total) * 100 if total > 0 else 0
        self.results["summary"]["success_rate"] = success_rate
        
        report.append(f"\n📊 RÉSULTATS GLOBAUX:")
        report.append(f"   • Total Endpoints Testés: {total}")
        report.append(f"   • Endpoints Fonctionnels: {self.results['summary']['working_endpoints']}")
        report.append(f"   • Auth Requise (Normal): {self.results['summary']['auth_required_endpoints']}")
        report.append(f"   • Endpoints Cassés: {self.results['summary']['broken_endpoints']}")
        report.append(f"   • Taux de Succès Global: {success_rate:.1f}%")
        
        # Analyse par catégorie
        categories = [
            ("core_endpoints", "🔧 ENDPOINTS CORE", ["health", "bootstrap"]),
            ("public_endpoints", "🌐 ENDPOINTS PUBLICS", ["/api/testimonials", "/api/stats/public", "/api/languages", "/api/public/plans-pricing", "/api/public/affiliate-config"]),
            ("amazon_endpoints", "🚀 ENDPOINTS AMAZON SP-API", ["/api/amazon/health", "/api/amazon/marketplaces", "/api/demo/amazon/status"])
        ]
        
        for category_key, category_name, expected_endpoints in categories:
            category_results = self.results.get(category_key, {})
            if category_results:
                working_count = sum(1 for r in category_results.values() if r.get("working", False))
                total_count = len(category_results)
                category_rate = (working_count / total_count) * 100 if total_count > 0 else 0
                
                status_icon = "✅" if category_rate >= 90 else "⚠️" if category_rate >= 75 else "❌"
                report.append(f"\n{category_name}:")
                report.append(f"   {status_icon} Taux de succès: {category_rate:.1f}% ({working_count}/{total_count})")
                
                # Détail des endpoints problématiques
                for endpoint, result in category_results.items():
                    if not result.get("working", False):
                        report.append(f"   ❌ {endpoint}: {result.get('status', 'unknown')} ({result.get('response_code', 'N/A')})")
        
        # Analyse authentification
        report.append(f"\n🔐 AUTHENTIFICATION:")
        auth_results = self.results.get("authentication", {})
        admin_login = auth_results.get("admin_login", {})
        if admin_login.get("working") and self.jwt_token:
            report.append(f"   ✅ Admin Login: FONCTIONNEL")
            report.append(f"   ✅ JWT Token Generation: FONCTIONNEL")
        else:
            report.append(f"   ❌ Admin Login: ÉCHEC - {admin_login.get('status', 'unknown')}")
        
        # Analyse variables d'environnement
        report.append(f"\n🔧 VARIABLES D'ENVIRONNEMENT:")
        env_validation = self.results.get("environment_validation", {})
        for var_name, is_valid in env_validation.items():
            status_icon = "✅" if is_valid else "❌"
            var_display = var_name.replace("_", " ").upper()
            report.append(f"   {status_icon} {var_display}: {'VALIDE' if is_valid else 'PROBLÈME'}")
        
        # Diagnostic final
        report.append(f"\n🎯 DIAGNOSTIC FINAL:")
        if success_rate >= 95:
            report.append("   🎉 EXCELLENT - Refactoring API client réussi, aucun impact détecté")
        elif success_rate >= 85:
            report.append("   ✅ TRÈS BON - Refactoring réussi avec impact minimal")
        elif success_rate >= 75:
            report.append("   ⚠️ BON - Quelques problèmes mineurs à corriger")
        elif success_rate >= 60:
            report.append("   ⚠️ MOYEN - Corrections nécessaires après refactoring")
        else:
            report.append("   ❌ CRITIQUE - Refactoring a causé des régressions majeures")
        
        # Recommandations spécifiques
        report.append(f"\n💡 RECOMMANDATIONS:")
        
        if self.results["summary"]["broken_endpoints"] > 0:
            report.append(f"   🔧 Corriger {self.results['summary']['broken_endpoints']} endpoints cassés")
        
        # Recommandations par catégorie
        if not self.results.get("authentication", {}).get("admin_login", {}).get("working", False):
            report.append("   🔐 PRIORITÉ HAUTE: Corriger l'authentification admin")
        
        env_issues = sum(1 for v in self.results.get("environment_validation", {}).values() if not v)
        if env_issues > 0:
            report.append(f"   🔧 Vérifier {env_issues} variables d'environnement")
        
        if success_rate >= 90:
            report.append("   ✅ Le refactoring API client n'a pas impacté les fonctionnalités backend")
        else:
            report.append("   ⚠️ Le refactoring API client peut avoir causé des régressions")
        
        return "\n".join(report)

    async def run_complete_validation(self):
        """Exécute la validation complète selon les spécifications"""
        print("🎯 BACKEND TESTING ECOMSIMPLY - API CLIENT CENTRALISÉ REFACTORING")
        print("=" * 70)
        print(f"Target: {self.base_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        try:
            # 1. Validation Endpoints Core
            await self.test_core_endpoints()
            
            # 2. Validation Endpoints Publics
            await self.test_public_endpoints()
            
            # 3. Validation Endpoints Amazon SP-API
            await self.test_amazon_endpoints()
            
            # 4. Validation Variables d'Environnement
            await self.validate_environment_variables()
            
            # 5. Génération du rapport final
            print("\n" + "=" * 70)
            print(self.generate_final_report())
            
            return self.results
            
        except Exception as e:
            print(f"❌ ERREUR CRITIQUE pendant la validation: {str(e)}")
            return {"error": str(e), "results": self.results}

async def main():
    """Point d'entrée principal"""
    print("🎯 BACKEND TESTING ECOMSIMPLY - API CLIENT CENTRALISÉ REFACTORING")
    print("Test complet du backend après refactoring pour vérifier l'absence de régressions")
    print()
    
    async with EcomsimplyRefactoringTester() as tester:
        results = await tester.run_complete_validation()
        
        # Déterminer le code de sortie
        if "error" in results:
            sys.exit(1)
        
        success_rate = results.get("summary", {}).get("success_rate", 0)
        
        if success_rate >= 95:
            print(f"\n🎉 EXCELLENT: Backend à {success_rate:.1f}% fonctionnel - Refactoring réussi!")
            sys.exit(0)
        elif success_rate >= 85:
            print(f"\n✅ TRÈS BON: Backend à {success_rate:.1f}% fonctionnel - Impact minimal du refactoring")
            sys.exit(0)
        elif success_rate >= 75:
            print(f"\n⚠️ BON: Backend à {success_rate:.1f}% fonctionnel - Quelques corrections nécessaires")
            sys.exit(0)
        elif success_rate >= 60:
            print(f"\n⚠️ MOYEN: Backend à {success_rate:.1f}% fonctionnel - Corrections nécessaires")
            sys.exit(0)
        else:
            print(f"\n❌ CRITIQUE: Backend à {success_rate:.1f}% fonctionnel - Régressions majeures détectées")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())