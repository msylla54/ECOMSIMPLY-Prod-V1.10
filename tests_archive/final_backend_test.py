#!/usr/bin/env python3
"""
Final Comprehensive ECOMSIMPLY Backend Test
Based on actual endpoint analysis
"""

import requests
import json
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BACKEND_URL = "https://ecomsimply.com"
API_BASE = f"{BACKEND_URL}/api"
ADMIN_KEY = "ECOMSIMPLY_ADMIN_2025"

# Test credentials
TEST_EMAIL = "final_test_user@example.com"
TEST_PASSWORD = "TestPassword123"
TEST_NAME = "Final Test User"

class FinalBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.auth_token = None
        self.results = {"passed": 0, "failed": 0, "tests": []}
        
    def log_result(self, test_name, success, details="", response_time=0):
        status = "✅ PASS" if success else "❌ FAIL"
        self.results["tests"].append({
            "name": test_name,
            "success": success,
            "details": details,
            "time": response_time
        })
        if success:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1
        print(f"{status} {test_name} ({response_time:.3f}s)")
        if details:
            print(f"    {details}")

    def test_core_health_endpoints(self):
        """Test Core API Health endpoints"""
        print("\n🔍 CORE API HEALTH ENDPOINTS")
        
        endpoints = [
            ("/health", "Health Check"),
            ("/health/ready", "Health Ready"),
            ("/health/live", "Health Live")
        ]
        
        for endpoint, name in endpoints:
            start = time.time()
            try:
                response = self.session.get(f"{API_BASE}{endpoint}", timeout=5)
                response_time = time.time() - start
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        status = data.get('status', 'healthy')
                        self.log_result(name, True, f"Status: {status}", response_time)
                    except:
                        self.log_result(name, True, f"HTTP 200", response_time)
                else:
                    self.log_result(name, False, f"HTTP {response.status_code}", response_time)
            except Exception as e:
                response_time = time.time() - start
                self.log_result(name, False, f"Error: {str(e)}", response_time)

    def test_authentication_system(self):
        """Test Authentication system"""
        print("\n🔐 AUTHENTICATION SYSTEM")
        
        # Test registration
        start = time.time()
        register_data = {
            "email": TEST_EMAIL,
            "name": TEST_NAME,
            "password": TEST_PASSWORD
        }
        
        try:
            response = self.session.post(f"{API_BASE}/auth/register", json=register_data, timeout=10)
            response_time = time.time() - start
            
            if response.status_code in [200, 201]:
                self.log_result("User Registration", True, "User created successfully", response_time)
            elif response.status_code == 400:
                self.log_result("User Registration", True, "User already exists (expected)", response_time)
            else:
                self.log_result("User Registration", False, f"HTTP {response.status_code}", response_time)
        except Exception as e:
            response_time = time.time() - start
            self.log_result("User Registration", False, f"Error: {str(e)}", response_time)
        
        # Test login
        start = time.time()
        login_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
        
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data, timeout=10)
            response_time = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('token')
                self.log_result("User Login", True, f"Token received: {bool(self.auth_token)}", response_time)
            else:
                self.log_result("User Login", False, f"HTTP {response.status_code}", response_time)
        except Exception as e:
            response_time = time.time() - start
            self.log_result("User Login", False, f"Error: {str(e)}", response_time)

    def test_product_generation(self):
        """Test Product generation"""
        print("\n🤖 PRODUCT GENERATION")
        
        if not self.auth_token:
            self.log_result("Product Generation", False, "No auth token available", 0)
            return
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        product_data = {
            "product_name": "Samsung Galaxy S24 Ultra",
            "product_description": "Smartphone premium avec écran Dynamic AMOLED 6.8 pouces, processeur Snapdragon 8 Gen 3, système de caméra quadruple 200MP, et S Pen intégré.",
            "generate_image": False,
            "number_of_images": 0,
            "language": "fr",
            "category": "électronique"
        }
        
        start = time.time()
        try:
            response = self.session.post(f"{API_BASE}/generate-sheet", 
                                       json=product_data, 
                                       headers=headers, 
                                       timeout=45)
            response_time = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                title = data.get('generated_title', '')
                features = data.get('key_features', [])
                seo_tags = data.get('seo_tags', [])
                
                success = bool(title and len(features) >= 3 and len(seo_tags) >= 5)
                details = f"Title: {len(title)} chars, Features: {len(features)}, SEO: {len(seo_tags)}"
                self.log_result("Product Generation", success, details, response_time)
            else:
                self.log_result("Product Generation", False, f"HTTP {response.status_code}", response_time)
        except Exception as e:
            response_time = time.time() - start
            self.log_result("Product Generation", False, f"Error: {str(e)}", response_time)

    def test_admin_dashboard(self):
        """Test Admin Dashboard endpoints"""
        print("\n👑 ADMIN DASHBOARD ENDPOINTS")
        
        admin_endpoints = [
            (f"/admin/plans-config?admin_key={ADMIN_KEY}", "Plans Configuration"),
            (f"/admin/promotions?admin_key={ADMIN_KEY}", "Promotions Management"),
            (f"/admin/testimonials?admin_key={ADMIN_KEY}", "Testimonials Management")
        ]
        
        for endpoint, name in admin_endpoints:
            start = time.time()
            try:
                response = self.session.get(f"{API_BASE}{endpoint}", timeout=10)
                response_time = time.time() - start
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        success = data.get('success', False)
                        if 'plans' in endpoint:
                            count = len(data.get('plans_config', []))
                        elif 'promotions' in endpoint:
                            count = len(data.get('promotions', []))
                        else:
                            count = len(data.get('testimonials', []))
                        
                        self.log_result(name, success, f"Items found: {count}", response_time)
                    except:
                        self.log_result(name, True, f"HTTP 200", response_time)
                else:
                    self.log_result(name, False, f"HTTP {response.status_code}", response_time)
            except Exception as e:
                response_time = time.time() - start
                self.log_result(name, False, f"Error: {str(e)}", response_time)

    def test_public_endpoints(self):
        """Test Public endpoints"""
        print("\n🌐 PUBLIC ENDPOINTS")
        
        public_endpoints = [
            ("/testimonials", "Public Testimonials"),
            ("/stats/public", "Public Statistics"),
            ("/subscription/plans", "Public Plans/Pricing")
        ]
        
        for endpoint, name in public_endpoints:
            start = time.time()
            try:
                response = self.session.get(f"{API_BASE}{endpoint}", timeout=10)
                response_time = time.time() - start
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            count = len(data)
                        elif isinstance(data, dict):
                            count = len(data.get('testimonials', data.get('plans', [])))
                        else:
                            count = 1
                        self.log_result(name, True, f"Data items: {count}", response_time)
                    except:
                        self.log_result(name, True, f"HTTP 200", response_time)
                else:
                    self.log_result(name, False, f"HTTP {response.status_code}", response_time)
            except Exception as e:
                response_time = time.time() - start
                self.log_result(name, False, f"Error: {str(e)}", response_time)

    def test_database_connectivity(self):
        """Test Database connectivity"""
        print("\n🗄️ DATABASE CONNECTIVITY")
        
        if not self.auth_token:
            self.log_result("Database Connectivity", False, "No auth token available", 0)
            return
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        # Test user stats (actual endpoint from server.py)
        start = time.time()
        try:
            response = self.session.get(f"{API_BASE}/stats", headers=headers, timeout=10)
            response_time = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                total_sheets = data.get('total_sheets', 0)
                plan = data.get('subscription_plan', 'unknown')
                self.log_result("User Stats", True, f"Sheets: {total_sheets}, Plan: {plan}", response_time)
            else:
                self.log_result("User Stats", False, f"HTTP {response.status_code}", response_time)
        except Exception as e:
            response_time = time.time() - start
            self.log_result("User Stats", False, f"Error: {str(e)}", response_time)

    def test_pricetruth_system(self):
        """Test PriceTruth system"""
        print("\n💰 PRICETRUTH SYSTEM")
        
        # Test health endpoint
        start = time.time()
        try:
            response = self.session.get(f"{API_BASE}/price-truth/health", timeout=10)
            response_time = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                adapters = data.get('adapters_available', 0)
                self.log_result("PriceTruth Health", True, f"Status: {status}, Adapters: {adapters}", response_time)
            else:
                self.log_result("PriceTruth Health", False, f"HTTP {response.status_code}", response_time)
        except Exception as e:
            response_time = time.time() - start
            self.log_result("PriceTruth Health", False, f"Error: {str(e)}", response_time)
        
        # Test stats endpoint
        start = time.time()
        try:
            response = self.session.get(f"{API_BASE}/price-truth/stats", timeout=10)
            response_time = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                queries = data.get('total_queries', 0)
                cache_rate = data.get('cache_hit_rate', 0)
                self.log_result("PriceTruth Stats", True, f"Queries: {queries}, Cache: {cache_rate}%", response_time)
            else:
                self.log_result("PriceTruth Stats", False, f"HTTP {response.status_code}", response_time)
        except Exception as e:
            response_time = time.time() - start
            self.log_result("PriceTruth Stats", False, f"Error: {str(e)}", response_time)
        
        # Test price query with correct parameter
        start = time.time()
        try:
            response = self.session.get(f"{API_BASE}/price-truth?q=iPhone 15 Pro", timeout=15)
            response_time = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                sources = len(data.get('sources', []))
                self.log_result("PriceTruth Query", True, f"Status: {status}, Sources: {sources}", response_time)
            else:
                self.log_result("PriceTruth Query", False, f"HTTP {response.status_code}", response_time)
        except Exception as e:
            response_time = time.time() - start
            self.log_result("PriceTruth Query", False, f"Error: {str(e)}", response_time)

    def test_response_times(self):
        """Test response times"""
        print("\n⏱️ RESPONSE TIMES")
        
        # Test health endpoint response time
        start = time.time()
        try:
            response = self.session.get(f"{API_BASE}/health", timeout=5)
            response_time = time.time() - start
            acceptable = response_time < 2.0
            self.log_result("Health Response Time", acceptable, 
                          f"{response_time:.3f}s (threshold: 2.0s)", response_time)
        except Exception as e:
            response_time = time.time() - start
            self.log_result("Health Response Time", False, f"Error: {str(e)}", response_time)

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 ECOMSIMPLY FINAL BACKEND TESTING")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Key: {ADMIN_KEY}")
        print("=" * 80)
        
        self.test_core_health_endpoints()
        self.test_authentication_system()
        self.test_product_generation()
        self.test_admin_dashboard()
        self.test_public_endpoints()
        self.test_database_connectivity()
        self.test_pricetruth_system()
        self.test_response_times()
        
        self.generate_summary()

    def generate_summary(self):
        """Generate final summary"""
        total = self.results["passed"] + self.results["failed"]
        success_rate = (self.results["passed"] / total * 100) if total > 0 else 0
        
        print("\n" + "=" * 80)
        print("📊 FINAL BACKEND TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total}")
        print(f"Passed: {self.results['passed']} ✅")
        print(f"Failed: {self.results['failed']} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.results["failed"] > 0:
            print("\n❌ FAILED TESTS:")
            for test in self.results["tests"]:
                if not test["success"]:
                    print(f"  - {test['name']}: {test['details']}")
        
        print(f"\n🎯 PRODUCTION READINESS:")
        if success_rate >= 90:
            print("✅ EXCELLENT - System is production-ready")
        elif success_rate >= 80:
            print("⚠️ GOOD - Minor issues need attention")
        elif success_rate >= 70:
            print("⚠️ ACCEPTABLE - Several issues need fixing")
        else:
            print("❌ CRITICAL - Major issues prevent production deployment")
        
        print("=" * 80)

if __name__ == "__main__":
    tester = FinalBackendTester()
    tester.run_all_tests()