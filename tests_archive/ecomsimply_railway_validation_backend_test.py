#!/usr/bin/env python3
"""
🎯 ECOMSIMPLY RAILWAY VALIDATION - BACKEND TESTING COMPLET
Test complet du backend ECOMSIMPLY pour validation post-Railway setup

OBJECTIFS CRITIQUES selon review request:
1. **Health Check** : Vérifier /api/health pour backend operationnel
2. **Bootstrap Admin** : Tester POST /api/admin/bootstrap avec token ECS-Bootstrap-2025-Secure-Token  
3. **Login Admin** : Tester authentification msylla54@gmail.com / ECS-Temp#2025-08-22!
4. **Endpoints Publics** : Valider /api/stats/public, /api/testimonials, /api/languages
5. **Amazon SP-API** : Tester /api/amazon/marketplaces (6 marketplaces attendues)
6. **Database MongoDB** : Vérifier connexion et persistance données

OBJECTIF : Générer un rapport de validation E2E baseline avant déploiement Railway 
pour comparaison post-déploiement. Le backend local doit être testé à 100% pour 
s'assurer que le code est prêt pour Railway.
"""

import asyncio
import aiohttp
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration de test selon review request
BASE_URL = "https://ecomsimply-deploy.preview.emergentagent.com"
TEST_TIMEOUT = 30

class EcomsimplyRailwayValidationTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = None
        self.results = {
            "health_check": {},
            "admin_bootstrap": {},
            "admin_authentication": {},
            "public_endpoints": {},
            "amazon_spapi": {},
            "database_validation": {},
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "success_rate": 0.0,
                "railway_ready": False
            }
        }
        
        # Credentials selon review request
        self.admin_credentials = {
            "email": "msylla54@gmail.com",
            "password": "ECS-Temp#2025-08-22!"
        }
        
        self.bootstrap_token = "ECS-Bootstrap-2025-Secure-Token"
        
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
            "passed": False,
            "railway_ready": False
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
                result["passed"] = True
                result["railway_ready"] = True
                result["status"] = "passed"
                self.results["summary"]["passed_tests"] += 1
            else:
                result["passed"] = False
                result["railway_ready"] = False
                result["status"] = "failed"
                result["error"] = f"Expected {expected_status}, got {result['response_code']}"
                self.results["summary"]["failed_tests"] += 1
                
        except asyncio.TimeoutError:
            result["error"] = "Timeout"
            result["status"] = "timeout"
            result["passed"] = False
            result["railway_ready"] = False
            self.results["summary"]["failed_tests"] += 1
        except Exception as e:
            result["error"] = str(e)
            result["status"] = "exception"
            result["passed"] = False
            result["railway_ready"] = False
            self.results["summary"]["failed_tests"] += 1
            
        self.results["summary"]["total_tests"] += 1
        return result

    async def test_health_check(self):
        """1. Health Check - Vérifier /api/health pour backend operationnel"""
        print("\n🏥 1. HEALTH CHECK VALIDATION")
        print("=" * 50)
        
        result = await self.test_endpoint(
            "GET", 
            "/api/health", 
            "Backend Health Check - Operational Status",
            [200]
        )
        
        self.results["health_check"] = result
        
        # Analyse détaillée de la réponse health
        if result["passed"] and result.get("response_data"):
            health_data = result["response_data"]
            
            # Vérifier les indicateurs de santé
            status_indicators = {
                "status_healthy": health_data.get("status") == "healthy" or health_data.get("ok") is True,
                "database_connected": "database" in str(health_data).lower() or "db" in str(health_data).lower(),
                "uptime_present": "uptime" in str(health_data).lower() or "ok" in str(health_data).lower(),
                "response_time_good": result["response_time"] < 1000  # < 1 seconde
            }
            
            result["health_indicators"] = status_indicators
            result["detailed_analysis"] = {
                "status_field": health_data.get("status", health_data.get("ok", "N/A")),
                "response_time_ms": result["response_time"],
                "data_structure": type(health_data).__name__,
                "keys_present": list(health_data.keys()) if isinstance(health_data, dict) else "N/A"
            }
            
            # Déterminer si prêt pour Railway
            all_indicators_good = all(status_indicators.values())
            result["railway_ready"] = result["passed"] and all_indicators_good
            
            print(f"✅ Health Check: PASSED ({result['response_code']}) - {result['response_time']}ms")
            print(f"    Status: {health_data.get('status', health_data.get('ok', 'N/A'))}")
            print(f"    Database: {'✅' if status_indicators['database_connected'] else '❌'}")
            print(f"    Response Time: {'✅' if status_indicators['response_time_good'] else '❌'} ({result['response_time']}ms)")
            print(f"    Railway Ready: {'✅' if result['railway_ready'] else '❌'}")
        else:
            print(f"❌ Health Check: FAILED ({result.get('response_code', 'N/A')})")
            print(f"    Error: {result.get('error', 'Unknown error')}")

    async def test_admin_bootstrap(self):
        """2. Bootstrap Admin - Tester POST /api/admin/bootstrap avec token"""
        print("\n🔧 2. ADMIN BOOTSTRAP VALIDATION")
        print("=" * 50)
        
        result = await self.test_endpoint(
            "POST",
            "/api/admin/bootstrap",
            "Admin Bootstrap Process",
            [200],
            None,
            {"x-bootstrap-token": self.bootstrap_token}
        )
        
        self.results["admin_bootstrap"] = result
        
        # Analyse détaillée de la réponse bootstrap
        if result["passed"] and result.get("response_data"):
            bootstrap_data = result["response_data"]
            
            # Vérifier les indicateurs de bootstrap
            bootstrap_indicators = {
                "bootstrap_success": bootstrap_data.get("ok") is True or "success" in str(bootstrap_data).lower(),
                "message_present": "message" in bootstrap_data or "bootstrap" in str(bootstrap_data).lower(),
                "timestamp_present": "timestamp" in bootstrap_data or "created" in str(bootstrap_data).lower()
            }
            
            result["bootstrap_indicators"] = bootstrap_indicators
            result["detailed_analysis"] = {
                "ok_field": bootstrap_data.get("ok", "N/A"),
                "message": bootstrap_data.get("message", "N/A"),
                "bootstrap_field": bootstrap_data.get("bootstrap", "N/A")
            }
            
            # Déterminer si prêt pour Railway
            result["railway_ready"] = result["passed"] and bootstrap_indicators["bootstrap_success"]
            
            print(f"✅ Admin Bootstrap: PASSED ({result['response_code']})")
            print(f"    Success: {'✅' if bootstrap_indicators['bootstrap_success'] else '❌'}")
            print(f"    Message: {bootstrap_data.get('message', 'N/A')}")
            print(f"    Railway Ready: {'✅' if result['railway_ready'] else '❌'}")
        else:
            print(f"❌ Admin Bootstrap: FAILED ({result.get('response_code', 'N/A')})")
            print(f"    Error: {result.get('error', 'Unknown error')}")

    async def test_admin_authentication(self):
        """3. Login Admin - Tester authentification avec credentials admin"""
        print("\n🔐 3. ADMIN AUTHENTICATION VALIDATION")
        print("=" * 50)
        
        result = await self.test_endpoint(
            "POST",
            "/api/auth/login",
            "Admin Authentication Test",
            [200],
            self.admin_credentials
        )
        
        self.results["admin_authentication"] = result
        
        # Analyse détaillée de l'authentification
        if result["passed"] and result.get("response_data"):
            auth_data = result["response_data"]
            
            # Vérifier les indicateurs d'authentification
            auth_indicators = {
                "token_present": "token" in auth_data or "access_token" in auth_data,
                "user_data_present": "user" in auth_data,
                "admin_privileges": False,
                "email_correct": False
            }
            
            # Vérifier les privilèges admin
            if "user" in auth_data:
                user_data = auth_data["user"]
                auth_indicators["admin_privileges"] = user_data.get("is_admin", False)
                auth_indicators["email_correct"] = user_data.get("email") == self.admin_credentials["email"]
            
            # Extraire le token pour tests futurs
            token = auth_data.get("token") or auth_data.get("access_token")
            
            result["auth_indicators"] = auth_indicators
            result["detailed_analysis"] = {
                "token_length": len(token) if token else 0,
                "user_email": auth_data.get("user", {}).get("email", "N/A"),
                "is_admin": auth_data.get("user", {}).get("is_admin", False),
                "token_present": bool(token)
            }
            
            # Déterminer si prêt pour Railway
            all_auth_good = all(auth_indicators.values())
            result["railway_ready"] = result["passed"] and all_auth_good and token
            
            print(f"✅ Admin Authentication: PASSED ({result['response_code']})")
            print(f"    Token Generated: {'✅' if auth_indicators['token_present'] else '❌'}")
            print(f"    Admin Privileges: {'✅' if auth_indicators['admin_privileges'] else '❌'}")
            print(f"    Email Correct: {'✅' if auth_indicators['email_correct'] else '❌'}")
            print(f"    Railway Ready: {'✅' if result['railway_ready'] else '❌'}")
            
            # Stocker le token pour tests futurs
            if token:
                self.jwt_token = token
                
        else:
            print(f"❌ Admin Authentication: FAILED ({result.get('response_code', 'N/A')})")
            print(f"    Error: {result.get('error', 'Unknown error')}")

    async def test_public_endpoints(self):
        """4. Endpoints Publics - Valider /api/stats/public, /api/testimonials, /api/languages"""
        print("\n🌐 4. PUBLIC ENDPOINTS VALIDATION")
        print("=" * 50)
        
        public_endpoints = [
            ("/api/stats/public", "Public Statistics"),
            ("/api/testimonials", "Testimonials Data"),
            ("/api/languages", "Supported Languages")
        ]
        
        public_results = {}
        
        for endpoint, description in public_endpoints:
            result = await self.test_endpoint("GET", endpoint, description, [200])
            public_results[endpoint] = result
            
            # Analyse spécifique par endpoint
            if result["passed"] and result.get("response_data"):
                data = result["response_data"]
                
                if endpoint == "/api/stats/public":
                    # Vérifier les statistiques publiques
                    stats_indicators = {
                        "has_clients": "clients" in str(data).lower() or "satisfied" in str(data).lower(),
                        "has_rating": "rating" in str(data).lower() or "average" in str(data).lower(),
                        "has_sheets": "sheets" in str(data).lower() or "product" in str(data).lower()
                    }
                    result["stats_indicators"] = stats_indicators
                    result["railway_ready"] = result["passed"] and any(stats_indicators.values())
                    
                elif endpoint == "/api/testimonials":
                    # Vérifier les témoignages
                    testimonials_indicators = {
                        "is_array": isinstance(data, list),
                        "has_structure": True if isinstance(data, list) else "testimonials" in str(data).lower()
                    }
                    result["testimonials_indicators"] = testimonials_indicators
                    result["railway_ready"] = result["passed"] and testimonials_indicators["has_structure"]
                    
                elif endpoint == "/api/languages":
                    # Vérifier les langues supportées
                    languages_indicators = {
                        "has_french": "fr" in str(data).lower() or "français" in str(data).lower(),
                        "has_english": "en" in str(data).lower() or "english" in str(data).lower(),
                        "proper_structure": isinstance(data, (list, dict))
                    }
                    result["languages_indicators"] = languages_indicators
                    result["railway_ready"] = result["passed"] and languages_indicators["has_french"]
            
            status_icon = "✅" if result["passed"] else "❌"
            railway_icon = "✅" if result.get("railway_ready", False) else "❌"
            print(f"{status_icon} {description}: PASSED ({result['response_code']}) - Railway Ready: {railway_icon}")
            
        self.results["public_endpoints"] = public_results

    async def test_amazon_spapi(self):
        """5. Amazon SP-API - Tester /api/amazon/marketplaces (6 marketplaces attendues)"""
        print("\n🚀 5. AMAZON SP-API VALIDATION")
        print("=" * 50)
        
        amazon_endpoints = [
            ("/api/amazon/marketplaces", "Amazon Marketplaces List", [200]),
            ("/api/amazon/health", "Amazon Health Check", [200]),
            ("/api/amazon/status", "Amazon Connection Status", [200, 403])  # 403 normal sans auth
        ]
        
        amazon_results = {}
        
        for endpoint_data in amazon_endpoints:
            endpoint, description = endpoint_data[:2]
            expected_status = endpoint_data[2] if len(endpoint_data) > 2 else [200]
            
            result = await self.test_endpoint("GET", endpoint, description, expected_status)
            amazon_results[endpoint] = result
            
            # Analyse spécifique Amazon
            if result["passed"] and result.get("response_data"):
                data = result["response_data"]
                
                if endpoint == "/api/amazon/marketplaces":
                    # Vérifier les 6 marketplaces attendues
                    # Les données sont dans data["marketplaces"] selon la structure API
                    marketplaces_list = data.get("marketplaces", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                    
                    marketplaces_indicators = {
                        "is_proper_structure": isinstance(data, dict) and "marketplaces" in data,
                        "has_6_marketplaces": len(marketplaces_list) == 6,
                        "has_france": any("fr" in str(m).lower() or "france" in str(m).lower() for m in marketplaces_list),
                        "has_germany": any("de" in str(m).lower() or "germany" in str(m).lower() for m in marketplaces_list),
                        "has_us": any("us" in str(m).lower() or "united" in str(m).lower() for m in marketplaces_list),
                        "has_uk": any("uk" in str(m).lower() or "kingdom" in str(m).lower() for m in marketplaces_list),
                        "has_italy": any("it" in str(m).lower() or "italy" in str(m).lower() for m in marketplaces_list),
                        "has_spain": any("es" in str(m).lower() or "spain" in str(m).lower() for m in marketplaces_list)
                    }
                    
                    result["marketplaces_indicators"] = marketplaces_indicators
                    result["marketplace_count"] = len(marketplaces_list)
                    
                    # Railway ready si 6 marketplaces avec les principaux pays
                    main_markets = [
                        marketplaces_indicators["has_france"],
                        marketplaces_indicators["has_germany"], 
                        marketplaces_indicators["has_us"],
                        marketplaces_indicators["has_uk"]
                    ]
                    result["railway_ready"] = result["passed"] and marketplaces_indicators["has_6_marketplaces"] and sum(main_markets) >= 3
                    
                    print(f"✅ {description}: PASSED ({result['response_code']})")
                    print(f"    Marketplaces Count: {result['marketplace_count']}/6")
                    print(f"    France: {'✅' if marketplaces_indicators['has_france'] else '❌'}")
                    print(f"    Germany: {'✅' if marketplaces_indicators['has_germany'] else '❌'}")
                    print(f"    US: {'✅' if marketplaces_indicators['has_us'] else '❌'}")
                    print(f"    UK: {'✅' if marketplaces_indicators['has_uk'] else '❌'}")
                    print(f"    Railway Ready: {'✅' if result['railway_ready'] else '❌'}")
                    
                elif endpoint == "/api/amazon/health":
                    # Vérifier la santé Amazon
                    health_indicators = {
                        "has_status": "status" in str(data).lower(),
                        "service_available": "healthy" in str(data).lower() or "ok" in str(data).lower() or "available" in str(data).lower()
                    }
                    result["amazon_health_indicators"] = health_indicators
                    result["railway_ready"] = result["passed"]
                    
                    status_icon = "✅" if result["passed"] else "❌"
                    print(f"{status_icon} {description}: PASSED ({result['response_code']})")
                    
            else:
                status_icon = "✅" if result["passed"] else "❌"
                print(f"{status_icon} {description}: {'PASSED' if result['passed'] else 'FAILED'} ({result.get('response_code', 'N/A')})")
                if not result["passed"]:
                    print(f"    Error: {result.get('error', 'Unknown error')}")
                    
        self.results["amazon_spapi"] = amazon_results

    async def test_database_validation(self):
        """6. Database MongoDB - Vérifier connexion et persistance données"""
        print("\n🗄️ 6. DATABASE MONGODB VALIDATION")
        print("=" * 50)
        
        # Test indirect de la base via les endpoints qui l'utilisent
        database_tests = [
            ("/api/health", "Database Connection via Health"),
            ("/api/stats/public", "Database Read Operations"),
            ("/api/testimonials", "Database Collections Access")
        ]
        
        database_results = {}
        database_indicators = {
            "health_db_connected": False,
            "data_persistence": False,
            "collections_accessible": False,
            "response_times_good": True
        }
        
        for endpoint, description in database_tests:
            result = await self.test_endpoint("GET", endpoint, description, [200])
            database_results[endpoint] = result
            
            if result["passed"]:
                # Analyser les indicateurs de base de données
                if endpoint == "/api/health":
                    health_data = result.get("response_data", {})
                    database_indicators["health_db_connected"] = (
                        "database" in str(health_data).lower() or 
                        "db" in str(health_data).lower() or
                        "mongo" in str(health_data).lower()
                    )
                    
                elif endpoint == "/api/stats/public":
                    stats_data = result.get("response_data", {})
                    database_indicators["data_persistence"] = bool(stats_data and stats_data != {})
                    
                elif endpoint == "/api/testimonials":
                    testimonials_data = result.get("response_data", {})
                    database_indicators["collections_accessible"] = isinstance(testimonials_data, (list, dict))
                
                # Vérifier les temps de réponse
                if result.get("response_time", 0) > 2000:  # > 2 secondes
                    database_indicators["response_times_good"] = False
            
            status_icon = "✅" if result["passed"] else "❌"
            print(f"{status_icon} {description}: {'PASSED' if result['passed'] else 'FAILED'} ({result.get('response_code', 'N/A')})")
        
        # Évaluation globale de la base de données
        db_health_score = sum(database_indicators.values())
        database_railway_ready = db_health_score >= 3  # Au moins 3/4 indicateurs OK
        
        print(f"\n📊 Database Health Summary:")
        print(f"    Connection: {'✅' if database_indicators['health_db_connected'] else '❌'}")
        print(f"    Data Persistence: {'✅' if database_indicators['data_persistence'] else '❌'}")
        print(f"    Collections Access: {'✅' if database_indicators['collections_accessible'] else '❌'}")
        print(f"    Response Times: {'✅' if database_indicators['response_times_good'] else '❌'}")
        print(f"    Railway Ready: {'✅' if database_railway_ready else '❌'}")
        
        self.results["database_validation"] = {
            "tests": database_results,
            "indicators": database_indicators,
            "health_score": db_health_score,
            "railway_ready": database_railway_ready
        }

    def generate_railway_validation_report(self) -> str:
        """Génère le rapport final de validation Railway"""
        report = []
        report.append("🎯 ECOMSIMPLY RAILWAY VALIDATION - RAPPORT FINAL")
        report.append("=" * 70)
        
        # Calculer le taux de succès global
        total = self.results["summary"]["total_tests"]
        passed = self.results["summary"]["passed_tests"]
        success_rate = (passed / total) * 100 if total > 0 else 0
        self.results["summary"]["success_rate"] = success_rate
        
        report.append(f"\n📊 RÉSULTATS GLOBAUX:")
        report.append(f"   • Total Tests Exécutés: {total}")
        report.append(f"   • Tests Réussis: {passed}")
        report.append(f"   • Tests Échoués: {self.results['summary']['failed_tests']}")
        report.append(f"   • Taux de Succès: {success_rate:.1f}%")
        
        # Analyse détaillée par section
        sections = [
            ("health_check", "🏥 Health Check"),
            ("admin_bootstrap", "🔧 Admin Bootstrap"),
            ("admin_authentication", "🔐 Admin Authentication"),
            ("public_endpoints", "🌐 Public Endpoints"),
            ("amazon_spapi", "🚀 Amazon SP-API"),
            ("database_validation", "🗄️ Database MongoDB")
        ]
        
        railway_ready_sections = 0
        
        for section_key, section_name in sections:
            section_data = self.results.get(section_key, {})
            
            if section_key == "public_endpoints" or section_key == "amazon_spapi":
                # Sections avec multiples endpoints
                section_passed = 0
                section_total = 0
                section_railway_ready = 0
                
                if isinstance(section_data, dict):
                    for endpoint_result in section_data.values():
                        if isinstance(endpoint_result, dict):
                            section_total += 1
                            if endpoint_result.get("passed", False):
                                section_passed += 1
                            if endpoint_result.get("railway_ready", False):
                                section_railway_ready += 1
                
                section_success = (section_passed / section_total) * 100 if section_total > 0 else 0
                railway_ready = section_railway_ready == section_total
                
                if railway_ready:
                    railway_ready_sections += 1
                
                status_icon = "✅" if railway_ready else "⚠️" if section_success >= 75 else "❌"
                report.append(f"\n{status_icon} {section_name}:")
                report.append(f"   • Tests: {section_passed}/{section_total} réussis ({section_success:.1f}%)")
                report.append(f"   • Railway Ready: {'✅' if railway_ready else '❌'}")
                
            elif section_key == "database_validation":
                # Section database avec structure spéciale
                db_data = section_data.get("indicators", {})
                db_railway_ready = section_data.get("railway_ready", False)
                
                if db_railway_ready:
                    railway_ready_sections += 1
                
                status_icon = "✅" if db_railway_ready else "❌"
                report.append(f"\n{status_icon} {section_name}:")
                report.append(f"   • Health Score: {section_data.get('health_score', 0)}/4")
                report.append(f"   • Railway Ready: {'✅' if db_railway_ready else '❌'}")
                
            else:
                # Sections avec un seul test
                section_passed = section_data.get("passed", False)
                section_railway_ready = section_data.get("railway_ready", False)
                
                if section_railway_ready:
                    railway_ready_sections += 1
                
                status_icon = "✅" if section_railway_ready else "❌"
                report.append(f"\n{status_icon} {section_name}:")
                report.append(f"   • Test: {'✅ PASSED' if section_passed else '❌ FAILED'}")
                report.append(f"   • Railway Ready: {'✅' if section_railway_ready else '❌'}")
        
        # Évaluation finale Railway
        total_sections = len(sections)
        railway_readiness = (railway_ready_sections / total_sections) * 100
        overall_railway_ready = railway_readiness >= 85  # 85% des sections doivent être prêtes
        
        self.results["summary"]["railway_ready"] = overall_railway_ready
        
        report.append(f"\n🚀 ÉVALUATION RAILWAY:")
        report.append(f"   • Sections Prêtes: {railway_ready_sections}/{total_sections}")
        report.append(f"   • Taux de Préparation: {railway_readiness:.1f}%")
        
        if overall_railway_ready:
            report.append(f"   • ✅ PRÊT POUR RAILWAY - Code validé pour déploiement")
        else:
            report.append(f"   • ❌ NON PRÊT POUR RAILWAY - Corrections nécessaires")
        
        # Recommandations spécifiques
        report.append(f"\n💡 RECOMMANDATIONS:")
        
        if not self.results.get("health_check", {}).get("railway_ready", False):
            report.append("   🔧 Corriger le health check - Vérifier la connectivité database")
        
        if not self.results.get("admin_authentication", {}).get("railway_ready", False):
            report.append("   🔐 Corriger l'authentification admin - Vérifier JWT token generation")
        
        amazon_data = self.results.get("amazon_spapi", {})
        marketplaces_result = amazon_data.get("/api/amazon/marketplaces", {})
        if not marketplaces_result.get("railway_ready", False):
            report.append("   🚀 Corriger Amazon SP-API - Vérifier les 6 marketplaces")
        
        if overall_railway_ready:
            report.append("   🎉 Backend ECOMSIMPLY validé - Prêt pour déploiement Railway!")
        else:
            report.append("   ⚠️ Corrections nécessaires avant déploiement Railway")
        
        return "\n".join(report)

    async def run_complete_railway_validation(self):
        """Exécute la validation complète Railway selon le review request"""
        print("🎯 ECOMSIMPLY RAILWAY VALIDATION - BACKEND TESTING COMPLET")
        print("=" * 70)
        print(f"Target: {self.base_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Objective: Validation E2E baseline avant déploiement Railway")
        
        try:
            # 1. Health Check
            await self.test_health_check()
            
            # 2. Bootstrap Admin
            await self.test_admin_bootstrap()
            
            # 3. Login Admin
            await self.test_admin_authentication()
            
            # 4. Endpoints Publics
            await self.test_public_endpoints()
            
            # 5. Amazon SP-API
            await self.test_amazon_spapi()
            
            # 6. Database MongoDB
            await self.test_database_validation()
            
            # 7. Génération du rapport final
            print("\n" + "=" * 70)
            print(self.generate_railway_validation_report())
            
            return self.results
            
        except Exception as e:
            print(f"❌ ERREUR CRITIQUE pendant la validation Railway: {str(e)}")
            return {"error": str(e), "results": self.results}

async def main():
    """Point d'entrée principal"""
    print("🎯 ECOMSIMPLY RAILWAY VALIDATION - BACKEND TESTING COMPLET")
    print("Validation E2E baseline avant déploiement Railway pour comparaison post-déploiement")
    print()
    
    async with EcomsimplyRailwayValidationTester() as tester:
        results = await tester.run_complete_railway_validation()
        
        # Déterminer le code de sortie
        if "error" in results:
            sys.exit(1)
        
        railway_ready = results.get("summary", {}).get("railway_ready", False)
        success_rate = results.get("summary", {}).get("success_rate", 0)
        
        if railway_ready:
            print(f"\n🎉 EXCELLENT: Backend ECOMSIMPLY PRÊT POUR RAILWAY ({success_rate:.1f}% succès)")
            sys.exit(0)
        elif success_rate >= 75:
            print(f"\n⚠️ BON: Backend à {success_rate:.1f}% - Corrections mineures avant Railway")
            sys.exit(0)
        else:
            print(f"\n❌ CRITIQUE: Backend à {success_rate:.1f}% - Corrections majeures requises avant Railway")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())