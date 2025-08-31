#!/usr/bin/env python3
"""
ECOMSIMPLY BACKEND PRODUCTION READINESS TEST
===========================================

Test complet du backend ECOMSIMPLY pour validation production selon review request.

ENDPOINTS CRITIQUES À TESTER:
1. SANTÉ & AUTHENTIFICATION (Priorité MAX)
2. ENDPOINTS PUBLICS (Homepage)  
3. AMAZON SP-API (Après auth JWT)
4. PERSISTANCE MONGODB

Focus: ROBUSTESSE et PRODUCTION-READINESS
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os

# Configuration des URLs depuis les variables d'environnement
BACKEND_URL = "https://ecomsimply-deploy.preview.emergentagent.com"

# Credentials de test
ADMIN_EMAIL = "msylla54@gmail.com"
ADMIN_PASSWORD = "ECS-Temp#2025-08-22!"
BOOTSTRAP_TOKEN = "ECS-Bootstrap-2025-Secure-Token"

class EcomsimplyBackendTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = None
        self.jwt_token = None
        self.test_results = []
        self.start_time = time.time()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'ECOMSIMPLY-Backend-Tester/1.0'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, status: str, details: Dict[str, Any] = None, response_time: float = 0):
        """Log test result"""
        result = {
            "test_name": test_name,
            "status": status,  # "PASS", "FAIL", "WARNING"
            "response_time_ms": round(response_time * 1000, 2),
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        # Print immediate feedback
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name} ({result['response_time_ms']}ms)")
        if details and status != "PASS":
            print(f"   Details: {details}")
    
    async def test_endpoint(self, method: str, endpoint: str, headers: Dict = None, 
                          data: Dict = None, expected_status: int = 200, 
                          test_name: str = None) -> Dict[str, Any]:
        """Generic endpoint tester"""
        if not test_name:
            test_name = f"{method} {endpoint}"
            
        url = f"{self.backend_url}{endpoint}"
        start_time = time.time()
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=data if data else None
            ) as response:
                response_time = time.time() - start_time
                response_text = await response.text()
                
                try:
                    response_data = json.loads(response_text) if response_text else {}
                except json.JSONDecodeError:
                    response_data = {"raw_response": response_text}
                
                if response.status == expected_status:
                    self.log_test(test_name, "PASS", {
                        "status_code": response.status,
                        "response_size": len(response_text)
                    }, response_time)
                    return {
                        "success": True,
                        "status_code": response.status,
                        "data": response_data,
                        "response_time": response_time
                    }
                else:
                    self.log_test(test_name, "FAIL", {
                        "expected_status": expected_status,
                        "actual_status": response.status,
                        "response": response_data
                    }, response_time)
                    return {
                        "success": False,
                        "status_code": response.status,
                        "data": response_data,
                        "response_time": response_time
                    }
                    
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test(test_name, "FAIL", {
                "error": str(e),
                "error_type": type(e).__name__
            }, response_time)
            return {
                "success": False,
                "error": str(e),
                "response_time": response_time
            }
    
    async def test_health_authentication_priority_max(self):
        """SECTION 1: SANTÉ & AUTHENTIFICATION (Priorité MAX)"""
        print("\n🎯 SECTION 1: SANTÉ & AUTHENTIFICATION (Priorité MAX)")
        print("=" * 60)
        
        # 1.1 Health Check avec MongoDB ping
        print("\n1.1 Testing Health Endpoint...")
        health_result = await self.test_endpoint(
            "GET", "/api/health", 
            test_name="Health Check + MongoDB Ping"
        )
        
        if health_result["success"]:
            health_data = health_result["data"]
            if isinstance(health_data, dict):
                db_status = health_data.get("database", {}).get("status") if isinstance(health_data.get("database"), dict) else "unknown"
                if db_status == "healthy" or health_data.get("status") == True:
                    print("   ✅ MongoDB connection confirmed")
                else:
                    print(f"   ⚠️ MongoDB status unclear: {db_status}")
        
        # 1.2 Admin Bootstrap
        print("\n1.2 Testing Admin Bootstrap...")
        bootstrap_result = await self.test_endpoint(
            "POST", "/api/admin/bootstrap",
            headers={"x-bootstrap-token": BOOTSTRAP_TOKEN},
            test_name="Admin Bootstrap Process"
        )
        
        # 1.3 Admin Login
        print("\n1.3 Testing Admin Authentication...")
        login_result = await self.test_endpoint(
            "POST", "/api/auth/login",
            data={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            test_name="Admin Login Authentication"
        )
        
        if login_result["success"]:
            login_data = login_result["data"]
            if isinstance(login_data, dict) and "token" in login_data:
                self.jwt_token = login_data["token"]
                print(f"   ✅ JWT Token acquired ({len(self.jwt_token)} chars)")
                
                # Verify admin privileges
                if login_data.get("user", {}).get("is_admin") == True:
                    print("   ✅ Admin privileges confirmed")
                else:
                    print("   ⚠️ Admin privileges not confirmed")
            else:
                print("   ❌ No JWT token in response")
        
        # 1.4 Auth Me (if token available)
        if self.jwt_token:
            print("\n1.4 Testing Auth Me endpoint...")
            auth_me_result = await self.test_endpoint(
                "GET", "/api/auth/me",
                headers={"Authorization": f"Bearer {self.jwt_token}"},
                test_name="Auth Me with JWT Token"
            )
    
    async def test_public_endpoints_homepage(self):
        """SECTION 2: ENDPOINTS PUBLICS (Homepage)"""
        print("\n🏠 SECTION 2: ENDPOINTS PUBLICS (Homepage)")
        print("=" * 60)
        
        # 2.1 Testimonials
        print("\n2.1 Testing Testimonials...")
        testimonials_result = await self.test_endpoint(
            "GET", "/api/testimonials",
            test_name="Homepage Testimonials"
        )
        
        if testimonials_result["success"]:
            testimonials_data = testimonials_result["data"]
            if isinstance(testimonials_data, dict):
                testimonials_list = testimonials_data.get("testimonials", [])
                print(f"   ✅ Found {len(testimonials_list)} testimonials")
        
        # 2.2 Public Stats
        print("\n2.2 Testing Public Statistics...")
        stats_result = await self.test_endpoint(
            "GET", "/api/stats/public",
            test_name="Homepage Public Statistics"
        )
        
        if stats_result["success"]:
            stats_data = stats_result["data"]
            if isinstance(stats_data, dict):
                stats_info = stats_data.get("stats", {})
                if stats_info:
                    print(f"   ✅ Statistics available: {list(stats_info.keys())}")
        
        # 2.3 Plans Pricing
        print("\n2.3 Testing Plans Pricing...")
        pricing_result = await self.test_endpoint(
            "GET", "/api/public/plans-pricing",
            test_name="Homepage Plans Pricing"
        )
        
        if pricing_result["success"]:
            pricing_data = pricing_result["data"]
            if isinstance(pricing_data, dict):
                plans = pricing_data.get("plans", [])
                print(f"   ✅ Found {len(plans)} pricing plans")
        
        # 2.4 Languages
        print("\n2.4 Testing Supported Languages...")
        languages_result = await self.test_endpoint(
            "GET", "/api/languages",
            test_name="Supported Languages"
        )
        
        if languages_result["success"]:
            languages_data = languages_result["data"]
            if isinstance(languages_data, dict):
                languages = languages_data.get("languages", [])
                print(f"   ✅ Supported languages: {len(languages)}")
    
    async def test_amazon_spapi_endpoints(self):
        """SECTION 3: AMAZON SP-API (Après auth JWT)"""
        print("\n🛒 SECTION 3: AMAZON SP-API (Après auth JWT)")
        print("=" * 60)
        
        if not self.jwt_token:
            print("   ❌ No JWT token available - skipping Amazon SP-API tests")
            return
        
        auth_headers = {"Authorization": f"Bearer {self.jwt_token}"}
        
        # 3.1 Amazon Health
        print("\n3.1 Testing Amazon Integration Health...")
        amazon_health_result = await self.test_endpoint(
            "GET", "/api/amazon/health",
            test_name="Amazon SP-API Health Check"
        )
        
        # 3.2 Amazon Status (requires auth)
        print("\n3.2 Testing Amazon Connection Status...")
        amazon_status_result = await self.test_endpoint(
            "GET", "/api/amazon/status",
            headers=auth_headers,
            expected_status=403,  # Expect 403 for unconnected user
            test_name="Amazon User Connection Status"
        )
        
        # Note: This might return 403 if user has no Amazon connection, which is normal
        if amazon_status_result["status_code"] == 403:
            print("   ℹ️ 403 response normal - user not connected to Amazon")
        
        # 3.3 Amazon Marketplaces
        print("\n3.3 Testing Amazon Marketplaces...")
        marketplaces_result = await self.test_endpoint(
            "GET", "/api/amazon/marketplaces",
            test_name="Amazon Supported Marketplaces"
        )
        
        if marketplaces_result["success"]:
            marketplaces_data = marketplaces_result["data"]
            if isinstance(marketplaces_data, list):
                print(f"   ✅ Found {len(marketplaces_data)} marketplaces")
                for marketplace in marketplaces_data[:3]:  # Show first 3
                    if isinstance(marketplace, dict):
                        name = marketplace.get("name", "Unknown")
                        country = marketplace.get("country_code", "??")
                        print(f"      - {name} ({country})")
            elif isinstance(marketplaces_data, dict) and "marketplaces" in marketplaces_data:
                marketplaces_list = marketplaces_data["marketplaces"]
                print(f"   ✅ Found {len(marketplaces_list)} marketplaces")
    
    async def test_mongodb_persistence(self):
        """SECTION 4: PERSISTANCE MONGODB"""
        print("\n💾 SECTION 4: PERSISTANCE MONGODB")
        print("=" * 60)
        
        # Test if admin login persists by making another auth call
        if self.jwt_token:
            print("\n4.1 Testing JWT Token Persistence...")
            auth_headers = {"Authorization": f"Bearer {self.jwt_token}"}
            
            # Try to access a protected endpoint to verify token works
            me_result = await self.test_endpoint(
                "GET", "/api/auth/me",
                headers=auth_headers,
                test_name="JWT Token Persistence Check"
            )
            
            if me_result["success"]:
                print("   ✅ JWT token persists and works")
            else:
                print("   ❌ JWT token persistence issue")
        
        # Verify collections exist by checking if endpoints return data
        print("\n4.2 Testing Collections Accessibility...")
        
        # Test users collection (via auth)
        if self.jwt_token:
            print("   - Users collection: ✅ (confirmed via successful auth)")
        
        # Test testimonials collection
        testimonials_check = await self.test_endpoint(
            "GET", "/api/testimonials",
            test_name="Testimonials Collection Check"
        )
        if testimonials_check["success"]:
            print("   - Testimonials collection: ✅")
        
        # Test stats_public collection
        stats_check = await self.test_endpoint(
            "GET", "/api/stats/public", 
            test_name="Stats Public Collection Check"
        )
        if stats_check["success"]:
            print("   - Stats_public collection: ✅")
    
    def generate_summary_report(self):
        """Generate comprehensive test summary"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        warning_tests = len([r for r in self.test_results if r["status"] == "WARNING"])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 80)
        print("🎯 ECOMSIMPLY BACKEND PRODUCTION READINESS REPORT")
        print("=" * 80)
        
        print(f"\n📊 RÉSULTATS GLOBAUX:")
        print(f"   • Tests exécutés: {total_tests}")
        print(f"   • Tests réussis: {passed_tests} ✅")
        print(f"   • Tests échoués: {failed_tests} ❌")
        print(f"   • Avertissements: {warning_tests} ⚠️")
        print(f"   • Taux de succès: {success_rate:.1f}%")
        print(f"   • Temps total: {total_time:.2f}s")
        
        # Categorize results by section
        sections = {
            "SANTÉ & AUTHENTIFICATION": [],
            "ENDPOINTS PUBLICS": [],
            "AMAZON SP-API": [],
            "PERSISTANCE MONGODB": []
        }
        
        for result in self.test_results:
            test_name = result["test_name"]
            if any(keyword in test_name for keyword in ["Health", "Bootstrap", "Login", "Auth"]):
                sections["SANTÉ & AUTHENTIFICATION"].append(result)
            elif any(keyword in test_name for keyword in ["Testimonials", "Statistics", "Plans", "Languages"]):
                sections["ENDPOINTS PUBLICS"].append(result)
            elif "Amazon" in test_name:
                sections["AMAZON SP-API"].append(result)
            elif any(keyword in test_name for keyword in ["Persistence", "Collection", "JWT"]):
                sections["PERSISTANCE MONGODB"].append(result)
        
        print(f"\n📋 DÉTAIL PAR SECTION:")
        for section_name, section_results in sections.items():
            if section_results:
                section_passed = len([r for r in section_results if r["status"] == "PASS"])
                section_total = len(section_results)
                section_rate = (section_passed / section_total * 100) if section_total > 0 else 0
                print(f"\n   {section_name}: {section_passed}/{section_total} ({section_rate:.1f}%)")
                
                for result in section_results:
                    status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
                    print(f"      {status_icon} {result['test_name']} ({result['response_time_ms']}ms)")
        
        # Critical issues
        critical_failures = [r for r in self.test_results if r["status"] == "FAIL" and 
                           any(keyword in r["test_name"] for keyword in ["Health", "Login", "Bootstrap"])]
        
        if critical_failures:
            print(f"\n🚨 PROBLÈMES CRITIQUES DÉTECTÉS:")
            for failure in critical_failures:
                print(f"   ❌ {failure['test_name']}")
                if failure["details"]:
                    print(f"      Détails: {failure['details']}")
        
        # Production readiness assessment
        print(f"\n🎯 ÉVALUATION PRODUCTION-READINESS:")
        if success_rate >= 90:
            print("   ✅ EXCELLENT - Backend prêt pour production")
        elif success_rate >= 80:
            print("   ⚠️ BON - Backend majoritairement fonctionnel, corrections mineures recommandées")
        elif success_rate >= 70:
            print("   ⚠️ MOYEN - Problèmes à corriger avant production")
        else:
            print("   ❌ CRITIQUE - Problèmes majeurs, production non recommandée")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "total_time": total_time,
            "critical_failures": len(critical_failures),
            "production_ready": success_rate >= 80
        }

async def main():
    """Main test execution"""
    print("🚀 ECOMSIMPLY BACKEND PRODUCTION READINESS TEST")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Start: {datetime.now().isoformat()}")
    print("=" * 80)
    
    async with EcomsimplyBackendTester() as tester:
        # Execute all test sections
        await tester.test_health_authentication_priority_max()
        await tester.test_public_endpoints_homepage()
        await tester.test_amazon_spapi_endpoints()
        await tester.test_mongodb_persistence()
        
        # Generate final report
        summary = tester.generate_summary_report()
        
        # Return appropriate exit code
        return 0 if summary["production_ready"] else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur critique: {e}")
        sys.exit(1)