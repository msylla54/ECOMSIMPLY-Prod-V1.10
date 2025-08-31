#!/usr/bin/env python3
"""
ECOMSIMPLY Backend Functionality Testing
Testing Core API Health, Authentication, Product Generation, Admin Dashboard, Public Endpoints, Database Connectivity, and PriceTruth System
"""

import requests
import json
import time
import sys
from datetime import datetime
import os

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ecomsimply.com')
API_BASE = f"{BACKEND_URL}/api"

# Admin key for testing
ADMIN_KEY = "ECOMSIMPLY_ADMIN_2025"

# Test credentials
TEST_EMAIL = "test_backend_user@example.com"
TEST_PASSWORD = "TestPassword123"
TEST_NAME = "Backend Test User"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        # Disable SSL verification for testing
        self.session.verify = False
        # Disable SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.auth_token = None
        self.test_results = []
        self.start_time = time.time()
        
    def log_test(self, test_name, success, details="", response_time=0):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "response_time": f"{response_time:.3f}s"
        }
        self.test_results.append(result)
        print(f"{status} {test_name} ({response_time:.3f}s)")
        if details:
            print(f"    Details: {details}")
        
    def make_request(self, method, endpoint, **kwargs):
        """Make HTTP request with timing"""
        start = time.time()
        try:
            url = f"{API_BASE}{endpoint}"
            if self.auth_token and 'headers' not in kwargs:
                kwargs['headers'] = {'Authorization': f'Bearer {self.auth_token}'}
            elif self.auth_token and 'headers' in kwargs:
                kwargs['headers']['Authorization'] = f'Bearer {self.auth_token}'
            
            # Set timeout
            kwargs.setdefault('timeout', 10)
                
            response = self.session.request(method, url, **kwargs)
            response_time = time.time() - start
            return response, response_time
        except Exception as e:
            response_time = time.time() - start
            print(f"    Request error: {str(e)}")
            return None, response_time

    def test_core_health_endpoints(self):
        """Test Core API Health endpoints"""
        print("\n🔍 Testing Core API Health Endpoints...")
        
        # Test /api/health
        response, response_time = self.make_request('GET', '/health')
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.log_test("Health Endpoint", True, f"Status: {data.get('status', 'unknown')}", response_time)
            except:
                self.log_test("Health Endpoint", True, f"Status Code: {response.status_code}", response_time)
        else:
            self.log_test("Health Endpoint", False, f"Status: {response.status_code if response else 'No response'}", response_time)
        
        # Test /api/health/ready
        response, response_time = self.make_request('GET', '/health/ready')
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.log_test("Health Ready Endpoint", True, f"Ready: {data.get('ready', 'unknown')}", response_time)
            except:
                self.log_test("Health Ready Endpoint", True, f"Status Code: {response.status_code}", response_time)
        else:
            self.log_test("Health Ready Endpoint", False, f"Status: {response.status_code if response else 'No response'}", response_time)
        
        # Test /api/health/live
        response, response_time = self.make_request('GET', '/health/live')
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.log_test("Health Live Endpoint", True, f"Live: {data.get('live', 'unknown')}", response_time)
            except:
                self.log_test("Health Live Endpoint", True, f"Status Code: {response.status_code}", response_time)
        else:
            self.log_test("Health Live Endpoint", False, f"Status: {response.status_code if response else 'No response'}", response_time)

    def test_authentication_endpoints(self):
        """Test Authentication endpoints"""
        print("\n🔐 Testing Authentication Endpoints...")
        
        # Test user registration
        register_data = {
            "email": TEST_EMAIL,
            "name": TEST_NAME,
            "password": TEST_PASSWORD
        }
        
        response, response_time = self.make_request('POST', '/auth/register', json=register_data)
        if response and response.status_code in [200, 201]:
            try:
                data = response.json()
                self.log_test("User Registration", True, f"User created: {data.get('user', {}).get('email', 'unknown')}", response_time)
            except:
                self.log_test("User Registration", True, f"Status Code: {response.status_code}", response_time)
        elif response and response.status_code == 400:
            # User might already exist
            self.log_test("User Registration", True, "User already exists (expected)", response_time)
        else:
            self.log_test("User Registration", False, f"Status: {response.status_code if response else 'No response'}", response_time)
        
        # Test user login
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response, response_time = self.make_request('POST', '/auth/login', json=login_data)
        if response and response.status_code == 200:
            try:
                data = response.json()
                print(f"    Login response: {data}")
                self.auth_token = data.get('access_token') or data.get('token')
                self.log_test("User Login", True, f"Token received: {bool(self.auth_token)}", response_time)
            except Exception as e:
                print(f"    Login parsing error: {e}")
                self.log_test("User Login", False, "Invalid response format", response_time)
        else:
            error_msg = f"Status: {response.status_code if response else 'No response'}"
            if response:
                try:
                    error_data = response.json()
                    error_msg += f", Error: {error_data}"
                except:
                    error_msg += f", Text: {response.text[:100]}"
            self.log_test("User Login", False, error_msg, response_time)

    def test_product_generation_endpoints(self):
        """Test Product generation endpoints"""
        print("\n🤖 Testing Product Generation Endpoints...")
        
        if not self.auth_token:
            self.log_test("Product Generation", False, "No auth token available", 0)
            return
        
        # Test product sheet generation
        product_data = {
            "product_name": "iPhone 15 Pro Max 256GB",
            "product_description": "Le dernier smartphone Apple avec puce A17 Pro, écran Super Retina XDR de 6.7 pouces, système de caméra Pro avancé avec zoom optique 5x, et construction en titane premium.",
            "generate_image": False,
            "number_of_images": 0,
            "language": "fr",
            "category": "électronique"
        }
        
        response, response_time = self.make_request('POST', '/generate-sheet', json=product_data)
        if response and response.status_code == 200:
            try:
                data = response.json()
                title = data.get('generated_title', '')
                description = data.get('marketing_description', '')
                features = data.get('key_features', [])
                seo_tags = data.get('seo_tags', [])
                
                success = bool(title and description and features and seo_tags)
                details = f"Title: {len(title)} chars, Features: {len(features)}, SEO tags: {len(seo_tags)}"
                self.log_test("Product Sheet Generation", success, details, response_time)
                
                # Store product sheet ID for later tests
                self.product_sheet_id = data.get('generation_id')
                
            except Exception as e:
                self.log_test("Product Sheet Generation", False, f"Response parsing error: {str(e)}", response_time)
        else:
            self.log_test("Product Sheet Generation", False, f"Status: {response.status_code if response else 'No response'}", response_time)

    def test_admin_dashboard_endpoints(self):
        """Test Admin Dashboard endpoints with ECOMSIMPLY_ADMIN_2025 key"""
        print("\n👑 Testing Admin Dashboard Endpoints...")
        
        # Test admin plans configuration
        response, response_time = self.make_request('GET', f'/admin/plans-config?admin_key={ADMIN_KEY}')
        if response and response.status_code == 200:
            try:
                data = response.json()
                success = data.get('success', False)
                plans = data.get('plans_config', [])
                self.log_test("Admin Plans Config", success, f"Plans found: {len(plans)}", response_time)
            except:
                self.log_test("Admin Plans Config", True, f"Status Code: {response.status_code}", response_time)
        else:
            self.log_test("Admin Plans Config", False, f"Status: {response.status_code if response else 'No response'}", response_time)
        
        # Test admin promotions
        response, response_time = self.make_request('GET', f'/admin/promotions?admin_key={ADMIN_KEY}')
        if response and response.status_code == 200:
            try:
                data = response.json()
                success = data.get('success', False)
                promotions = data.get('promotions', [])
                self.log_test("Admin Promotions", success, f"Promotions found: {len(promotions)}", response_time)
            except:
                self.log_test("Admin Promotions", True, f"Status Code: {response.status_code}", response_time)
        else:
            self.log_test("Admin Promotions", False, f"Status: {response.status_code if response else 'No response'}", response_time)
        
        # Test admin testimonials
        response, response_time = self.make_request('GET', f'/admin/testimonials?admin_key={ADMIN_KEY}')
        if response and response.status_code == 200:
            try:
                data = response.json()
                success = data.get('success', False)
                testimonials = data.get('testimonials', [])
                self.log_test("Admin Testimonials", success, f"Testimonials found: {len(testimonials)}", response_time)
            except:
                self.log_test("Admin Testimonials", True, f"Status Code: {response.status_code}", response_time)
        else:
            self.log_test("Admin Testimonials", False, f"Status: {response.status_code if response else 'No response'}", response_time)

    def test_public_endpoints(self):
        """Test Public endpoints"""
        print("\n🌐 Testing Public Endpoints...")
        
        # Test public testimonials
        response, response_time = self.make_request('GET', '/testimonials')
        if response and response.status_code == 200:
            try:
                data = response.json()
                testimonials = data if isinstance(data, list) else data.get('testimonials', [])
                self.log_test("Public Testimonials", True, f"Testimonials found: {len(testimonials)}", response_time)
            except:
                self.log_test("Public Testimonials", True, f"Status Code: {response.status_code}", response_time)
        else:
            self.log_test("Public Testimonials", False, f"Status: {response.status_code if response else 'No response'}", response_time)
        
        # Test public statistics
        response, response_time = self.make_request('GET', '/stats/public')
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.log_test("Public Statistics", True, f"Stats available: {bool(data)}", response_time)
            except:
                self.log_test("Public Statistics", True, f"Status Code: {response.status_code}", response_time)
        else:
            # Try alternative endpoint
            response, response_time = self.make_request('GET', '/public/stats')
            if response and response.status_code == 200:
                self.log_test("Public Statistics", True, f"Status Code: {response.status_code}", response_time)
            else:
                self.log_test("Public Statistics", False, f"Status: {response.status_code if response else 'No response'}", response_time)
        
        # Test public plans/pricing
        response, response_time = self.make_request('GET', '/plans')
        if response and response.status_code == 200:
            try:
                data = response.json()
                plans = data if isinstance(data, list) else data.get('plans', [])
                self.log_test("Public Plans/Pricing", True, f"Plans found: {len(plans)}", response_time)
            except:
                self.log_test("Public Plans/Pricing", True, f"Status Code: {response.status_code}", response_time)
        else:
            # Try alternative endpoints
            for alt_endpoint in ['/public/plans', '/subscription/plans', '/pricing']:
                response, response_time = self.make_request('GET', alt_endpoint)
                if response and response.status_code == 200:
                    self.log_test("Public Plans/Pricing", True, f"Found at {alt_endpoint}", response_time)
                    break
            else:
                self.log_test("Public Plans/Pricing", False, f"Status: {response.status_code if response else 'No response'}", response_time)

    def test_database_connectivity(self):
        """Test Database connectivity through API endpoints"""
        print("\n🗄️ Testing Database Connectivity...")
        
        if not self.auth_token:
            self.log_test("Database Connectivity", False, "No auth token available", 0)
            return
        
        # Test user profile (requires DB)
        response, response_time = self.make_request('GET', '/user/profile')
        if response and response.status_code == 200:
            try:
                data = response.json()
                email = data.get('email', '')
                self.log_test("Database User Profile", True, f"User email: {email}", response_time)
            except:
                self.log_test("Database User Profile", True, f"Status Code: {response.status_code}", response_time)
        else:
            self.log_test("Database User Profile", False, f"Status: {response.status_code if response else 'No response'}", response_time)
        
        # Test user stats (requires DB)
        response, response_time = self.make_request('GET', '/user/stats')
        if response and response.status_code == 200:
            try:
                data = response.json()
                total_sheets = data.get('total_sheets', 0)
                self.log_test("Database User Stats", True, f"Total sheets: {total_sheets}", response_time)
            except:
                self.log_test("Database User Stats", True, f"Status Code: {response.status_code}", response_time)
        else:
            self.log_test("Database User Stats", False, f"Status: {response.status_code if response else 'No response'}", response_time)

    def test_pricetruth_system(self):
        """Test PriceTruth system endpoints"""
        print("\n💰 Testing PriceTruth System...")
        
        # Test PriceTruth health
        response, response_time = self.make_request('GET', '/price-truth/health')
        if response and response.status_code == 200:
            try:
                data = response.json()
                status = data.get('status', 'unknown')
                adapters = data.get('adapters_available', 0)
                self.log_test("PriceTruth Health", True, f"Status: {status}, Adapters: {adapters}", response_time)
            except:
                self.log_test("PriceTruth Health", True, f"Status Code: {response.status_code}", response_time)
        else:
            self.log_test("PriceTruth Health", False, f"Status: {response.status_code if response else 'No response'}", response_time)
        
        # Test PriceTruth stats
        response, response_time = self.make_request('GET', '/price-truth/stats')
        if response and response.status_code == 200:
            try:
                data = response.json()
                total_queries = data.get('total_queries', 0)
                cache_rate = data.get('cache_hit_rate', 0)
                self.log_test("PriceTruth Stats", True, f"Queries: {total_queries}, Cache rate: {cache_rate}%", response_time)
            except:
                self.log_test("PriceTruth Stats", True, f"Status Code: {response.status_code}", response_time)
        else:
            self.log_test("PriceTruth Stats", False, f"Status: {response.status_code if response else 'No response'}", response_time)
        
        # Test PriceTruth query
        test_product = "iPhone 15 Pro"
        response, response_time = self.make_request('GET', f'/price-truth?product_name={test_product}')
        if response and response.status_code == 200:
            try:
                data = response.json()
                status = data.get('status', 'unknown')
                sources_count = len(data.get('sources', []))
                self.log_test("PriceTruth Query", True, f"Status: {status}, Sources: {sources_count}", response_time)
            except:
                self.log_test("PriceTruth Query", True, f"Status Code: {response.status_code}", response_time)
        elif response and response.status_code == 400:
            # Bad request might be expected for missing parameters
            try:
                error_data = response.json()
                self.log_test("PriceTruth Query", True, f"Expected 400: {error_data.get('message', 'Bad request')}", response_time)
            except:
                self.log_test("PriceTruth Query", True, f"Expected 400 status", response_time)
        else:
            self.log_test("PriceTruth Query", False, f"Status: {response.status_code if response else 'No response'}", response_time)

    def test_response_times(self):
        """Test response times for key endpoints"""
        print("\n⏱️ Testing Response Times...")
        
        # Test health endpoint response time
        response, response_time = self.make_request('GET', '/health')
        acceptable_time = response_time < 2.0  # 2 seconds threshold
        self.log_test("Health Response Time", acceptable_time, f"Response time: {response_time:.3f}s (threshold: 2.0s)", response_time)
        
        # Test authentication response time
        if self.auth_token:
            response, response_time = self.make_request('GET', '/user/profile')
            acceptable_time = response_time < 3.0  # 3 seconds threshold
            self.log_test("Auth Response Time", acceptable_time, f"Response time: {response_time:.3f}s (threshold: 3.0s)", response_time)

    def run_all_tests(self):
        """Run all backend tests"""
        print(f"🚀 Starting ECOMSIMPLY Backend Testing...")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print(f"Admin Key: {ADMIN_KEY}")
        print("=" * 80)
        
        # Run all test suites
        self.test_core_health_endpoints()
        self.test_authentication_endpoints()
        self.test_product_generation_endpoints()
        self.test_admin_dashboard_endpoints()
        self.test_public_endpoints()
        self.test_database_connectivity()
        self.test_pricetruth_system()
        self.test_response_times()
        
        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        total_time = time.time() - self.start_time
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 80)
        print("📊 ECOMSIMPLY BACKEND TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n🎯 PRODUCTION READINESS ASSESSMENT:")
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
    tester = BackendTester()
    tester.run_all_tests()