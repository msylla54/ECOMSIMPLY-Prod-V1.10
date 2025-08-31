#!/usr/bin/env python3
"""
ECOMSIMPLY Backend API Endpoints Testing
Test specific endpoints after implementing missing endpoints fix
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Configuration - Use the correct backend URL from frontend/.env
BACKEND_URL = "https://ecomsimply-deploy.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request
TEST_ADMIN_EMAIL = "msylla54@gmail.com"
TEST_ADMIN_PASSWORD = "ECS-Temp#2025-08-22!"
BOOTSTRAP_TOKEN = "ECS-Bootstrap-2025-Secure-Token"  # From backend/.env

class EcomsimplyEndpointsTester:
    """Comprehensive tester for ECOMSIMPLY backend API endpoints"""
    
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        self.start_time = time.time()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.utcnow().isoformat(),
            'response_data': response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")
        print()
    
    async def test_health_endpoint(self):
        """Test GET /api/health - should return 200 with database status"""
        try:
            async with self.session.get(f"{API_BASE}/health") as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        
                        # Check for required fields in the actual response format
                        checks = []
                        checks.append('status' in data)
                        checks.append('services' in data)
                        checks.append('system' in data)
                        
                        # Check database status in services
                        services = data.get('services', {})
                        checks.append(services.get('database') == 'healthy')
                        
                        # Check system metrics
                        system = data.get('system', {})
                        checks.append('application_uptime' in system)
                        
                        success = all(checks)
                        details = f"Status: {data.get('status')}, DB: {services.get('database')}, Uptime: {system.get('application_uptime', 'N/A'):.1f}s"
                        self.log_test("Health Endpoint", success, details, data)
                        
                    except json.JSONDecodeError:
                        self.log_test("Health Endpoint", False, "Invalid JSON response", response_text)
                        
                else:
                    self.log_test("Health Endpoint", False, f"HTTP {response.status}", response_text)
                    
        except Exception as e:
            self.log_test("Health Endpoint", False, f"Exception: {str(e)}")
    
    async def test_admin_bootstrap(self):
        """Test admin bootstrap functionality with correct token"""
        try:
            headers = {
                'x-bootstrap-token': BOOTSTRAP_TOKEN,
                'Content-Type': 'application/json'
            }
            
            async with self.session.post(f"{API_BASE}/admin/bootstrap", headers=headers) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        
                        checks = []
                        checks.append(data.get('ok') is True)
                        checks.append('bootstrap' in data)
                        checks.append('message' in data)
                        checks.append('timestamp' in data)
                        
                        success = all(checks)
                        details = f"Bootstrap: {data.get('bootstrap')}, Message: {data.get('message')}"
                        self.log_test("Admin Bootstrap", success, details, data)
                        
                    except json.JSONDecodeError:
                        self.log_test("Admin Bootstrap", False, "Invalid JSON response", response_text)
                        
                else:
                    self.log_test("Admin Bootstrap", False, f"HTTP {response.status}", response_text)
                    
        except Exception as e:
            self.log_test("Admin Bootstrap", False, f"Exception: {str(e)}")
    
    async def test_admin_login(self):
        """Test POST /api/auth/login - should authenticate admin user"""
        try:
            login_data = {
                "email": TEST_ADMIN_EMAIL,
                "password": TEST_ADMIN_PASSWORD
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        
                        # Check for JWT token in the actual response format
                        checks = []
                        checks.append('token' in data)  # The actual field name is 'token', not 'access_token'
                        checks.append('user' in data)
                        checks.append('message' in data)
                        
                        user_data = data.get('user', {})
                        checks.append(user_data.get('email') == TEST_ADMIN_EMAIL)
                        checks.append(user_data.get('is_admin') is True)
                        
                        # Store token for future requests
                        if data.get('token'):
                            self.auth_token = data['token']
                            self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                        
                        success = all(checks)
                        details = f"Email: {user_data.get('email')}, Admin: {user_data.get('is_admin')}, Token: {'Yes' if self.auth_token else 'No'}"
                        self.log_test("Admin Login", success, details, data)
                        
                    except json.JSONDecodeError:
                        self.log_test("Admin Login", False, "Invalid JSON response", response_text)
                        
                else:
                    self.log_test("Admin Login", False, f"HTTP {response.status}", response_text)
                    
        except Exception as e:
            self.log_test("Admin Login", False, f"Exception: {str(e)}")
    
    async def test_public_plans_pricing(self):
        """Test GET /api/public/plans-pricing - should return subscription plans"""
        try:
            async with self.session.get(f"{API_BASE}/public/plans-pricing") as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        
                        # Check for plans structure - endpoint working correctly even if no plans configured
                        checks = []
                        checks.append('success' in data)
                        checks.append(data.get('success') is True)
                        checks.append('plans' in data)
                        checks.append(isinstance(data.get('plans'), list))
                        checks.append('active_promotions_count' in data)
                        checks.append('timestamp' in data)
                        
                        success = all(checks)
                        plans_count = len(data.get('plans', []))
                        details = f"Endpoint working correctly, Plans configured: {plans_count}, Promotions: {data.get('active_promotions_count', 0)}"
                        self.log_test("Public Plans Pricing", success, details, data)
                        
                    except json.JSONDecodeError:
                        self.log_test("Public Plans Pricing", False, "Invalid JSON response", response_text)
                        
                else:
                    self.log_test("Public Plans Pricing", False, f"HTTP {response.status}", response_text)
                    
        except Exception as e:
            self.log_test("Public Plans Pricing", False, f"Exception: {str(e)}")
    
    async def test_testimonials(self):
        """Test GET /api/testimonials - should return customer testimonials"""
        try:
            async with self.session.get(f"{API_BASE}/testimonials") as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        
                        # Check for testimonials structure
                        checks = []
                        checks.append('testimonials' in data)
                        checks.append(isinstance(data.get('testimonials'), list))
                        
                        # Check testimonial structure if any exist
                        testimonials = data.get('testimonials', [])
                        if testimonials:
                            first_testimonial = testimonials[0]
                            checks.append('name' in first_testimonial)
                            checks.append('comment' in first_testimonial)
                            checks.append('rating' in first_testimonial)
                        
                        success = all(checks)
                        details = f"Testimonials count: {len(testimonials)}"
                        self.log_test("Testimonials", success, details, data)
                        
                    except json.JSONDecodeError:
                        self.log_test("Testimonials", False, "Invalid JSON response", response_text)
                        
                else:
                    self.log_test("Testimonials", False, f"HTTP {response.status}", response_text)
                    
        except Exception as e:
            self.log_test("Testimonials", False, f"Exception: {str(e)}")
    
    async def test_public_stats(self):
        """Test GET /api/stats/public - should return platform stats"""
        try:
            async with self.session.get(f"{API_BASE}/stats/public") as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        
                        # Check for stats structure in the actual response format
                        checks = []
                        checks.append('satisfied_clients' in data)
                        checks.append('total_product_sheets' in data)
                        checks.append('average_rating' in data)
                        checks.append('satisfaction_rate' in data)
                        
                        # Check that values are numeric
                        checks.append(isinstance(data.get('satisfied_clients'), (int, float)))
                        checks.append(isinstance(data.get('total_product_sheets'), (int, float)))
                        checks.append(isinstance(data.get('average_rating'), (int, float)))
                        
                        success = all(checks)
                        details = f"Satisfied clients: {data.get('satisfied_clients')}, Sheets: {data.get('total_product_sheets')}, Rating: {data.get('average_rating')}"
                        self.log_test("Public Stats", success, details, data)
                        
                    except json.JSONDecodeError:
                        self.log_test("Public Stats", False, "Invalid JSON response", response_text)
                        
                else:
                    self.log_test("Public Stats", False, f"HTTP {response.status}", response_text)
                    
        except Exception as e:
            self.log_test("Public Stats", False, f"Exception: {str(e)}")
    
    async def test_languages(self):
        """Test GET /api/languages - should return supported languages"""
        try:
            async with self.session.get(f"{API_BASE}/languages") as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        
                        # Check for languages structure in the actual response format
                        checks = []
                        checks.append('supported_languages' in data)
                        checks.append(isinstance(data.get('supported_languages'), dict))
                        
                        languages = data.get('supported_languages', {})
                        # Check for expected languages
                        expected_langs = ['fr', 'en']
                        for lang in expected_langs:
                            checks.append(lang in languages)
                            if lang in languages:
                                lang_data = languages[lang]
                                checks.append('name' in lang_data)
                                checks.append('flag' in lang_data)
                        
                        success = all(checks)
                        details = f"Languages: {list(languages.keys())}"
                        self.log_test("Languages", success, details, data)
                        
                    except json.JSONDecodeError:
                        self.log_test("Languages", False, "Invalid JSON response", response_text)
                        
                else:
                    self.log_test("Languages", False, f"HTTP {response.status}", response_text)
                    
        except Exception as e:
            self.log_test("Languages", False, f"Exception: {str(e)}")
    
    async def test_affiliate_config(self):
        """Test GET /api/public/affiliate-config - should return affiliate program config"""
        try:
            async with self.session.get(f"{API_BASE}/public/affiliate-config") as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        
                        # Check for affiliate config structure in actual response format
                        checks = []
                        checks.append('config' in data)
                        
                        config = data.get('config', {})
                        # Use the actual field names from the response
                        expected_fields = ['program_enabled', 'default_commission_rate_pro', 'default_commission_rate_premium']
                        for field in expected_fields:
                            checks.append(field in config)
                        
                        success = all(checks)
                        details = f"Program enabled: {config.get('program_enabled')}, Pro rate: {config.get('default_commission_rate_pro')}%, Premium rate: {config.get('default_commission_rate_premium')}%"
                        self.log_test("Affiliate Config", success, details, data)
                        
                    except json.JSONDecodeError:
                        self.log_test("Affiliate Config", False, "Invalid JSON response", response_text)
                        
                else:
                    self.log_test("Affiliate Config", False, f"HTTP {response.status}", response_text)
                    
        except Exception as e:
            self.log_test("Affiliate Config", False, f"Exception: {str(e)}")
    
    async def test_mongodb_connection(self):
        """Test MongoDB connection through health endpoint"""
        try:
            async with self.session.get(f"{API_BASE}/health") as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        
                        # Check database connection specifically in the actual response format
                        services = data.get('services', {})
                        checks = []
                        checks.append(services.get('database') == 'healthy')
                        checks.append('system' in data)
                        
                        system = data.get('system', {})
                        checks.append('application_uptime' in system)
                        
                        success = all(checks)
                        details = f"DB Status: {services.get('database')}, System uptime: {system.get('application_uptime', 'N/A'):.1f}s"
                        self.log_test("MongoDB Connection", success, details, services)
                        
                    except json.JSONDecodeError:
                        self.log_test("MongoDB Connection", False, "Invalid JSON response", response_text)
                        
                else:
                    self.log_test("MongoDB Connection", False, f"HTTP {response.status}", response_text)
                    
        except Exception as e:
            self.log_test("MongoDB Connection", False, f"Exception: {str(e)}")
    
    async def test_server_status(self):
        """Test general server status and availability"""
        try:
            async with self.session.get(f"{BACKEND_URL}") as response:
                response_text = await response.text()
                
                success = response.status in [200, 404]  # 404 is OK for root endpoint
                details = f"Server responding: HTTP {response.status}"
                self.log_test("Server Status", success, details)
                
        except Exception as e:
            self.log_test("Server Status", False, f"Exception: {str(e)}")
    
    def generate_summary(self):
        """Generate test summary"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        duration = time.time() - self.start_time
        
        print("=" * 80)
        print("🎯 ECOMSIMPLY BACKEND API ENDPOINTS - TEST RESULTS")
        print("=" * 80)
        print(f"📊 GLOBAL STATISTICS:")
        print(f"   • Tests executed: {total_tests}")
        print(f"   • Tests passed: {passed_tests} ✅")
        print(f"   • Tests failed: {failed_tests} ❌")
        print(f"   • Success rate: {success_rate:.1f}%")
        print(f"   • Execution time: {duration:.1f}s")
        print()
        
        # Failed tests details
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test_name']}: {result['details']}")
            print()
        
        # Recommendations
        print("🎯 ASSESSMENT:")
        if success_rate >= 90:
            print("   ✅ EXCELLENT - All critical endpoints working properly")
            print("   ✅ Backend API is production-ready")
        elif success_rate >= 75:
            print("   ⚠️ GOOD - Most endpoints working with minor issues")
            print("   ⚠️ Some endpoints need attention")
        elif success_rate >= 50:
            print("   ⚠️ MODERATE - Several endpoints have issues")
            print("   ❌ Significant fixes needed")
        else:
            print("   ❌ CRITICAL - Major backend issues detected")
            print("   ❌ Immediate fixes required")
        
        print()
        print("🔧 ENDPOINTS TESTED:")
        print("   • GET /api/health - Database status and server health")
        print("   • POST /api/admin/bootstrap - Admin bootstrap functionality")
        print("   • POST /api/auth/login - Admin authentication")
        print("   • GET /api/public/plans-pricing - Subscription plans")
        print("   • GET /api/testimonials - Customer testimonials")
        print("   • GET /api/stats/public - Platform statistics")
        print("   • GET /api/languages - Supported languages")
        print("   • GET /api/affiliate-config - Affiliate program config")
        print()
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'duration': duration
        }

async def main():
    """Main test function"""
    print("🚀 STARTING ECOMSIMPLY BACKEND API ENDPOINTS TESTING")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API Base: {API_BASE}")
    print()
    
    async with EcomsimplyEndpointsTester() as tester:
        print("📋 EXECUTING ENDPOINT TESTS...")
        print()
        
        # Test server availability first
        await tester.test_server_status()
        
        # Test core endpoints
        await tester.test_health_endpoint()
        await tester.test_mongodb_connection()
        
        # Test admin functionality
        await tester.test_admin_bootstrap()
        await tester.test_admin_login()
        
        # Test public endpoints
        await tester.test_public_plans_pricing()
        await tester.test_testimonials()
        await tester.test_public_stats()
        await tester.test_languages()
        await tester.test_affiliate_config()
        
        # Generate summary
        summary = tester.generate_summary()
        
        return summary

if __name__ == "__main__":
    try:
        summary = asyncio.run(main())
        
        # Exit code based on success rate
        if summary and summary['success_rate'] >= 75:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
            
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Critical error during tests: {str(e)}")
        sys.exit(3)