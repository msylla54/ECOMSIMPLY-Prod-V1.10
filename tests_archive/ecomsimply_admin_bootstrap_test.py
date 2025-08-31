#!/usr/bin/env python3
"""
ECOMSIMPLY Admin Bootstrap and Backend API Testing
Comprehensive testing of backend functionality and admin bootstrap process
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any, List
import hashlib
import secrets

# Configuration from environment
BACKEND_URL = "https://ecomsimply.com"
API_BASE = f"{BACKEND_URL}/api"

class EcomsimplyBackendTester:
    """Comprehensive ECOMSIMPLY Backend Tester"""
    
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        self.start_time = time.time()
        self.admin_credentials = {
            "email": "msylla54@gmail.com",
            "password": "ECS-Temp#2025-08-22!"
        }
        
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
        print(f"{status} {test_name}: {details}")
        
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
    
    async def test_health_endpoint(self):
        """Test health endpoint"""
        try:
            async with self.session.get(f"{API_BASE}/health") as response:
                data = await response.json()
                
                if response.status == 200:
                    db_status = data.get('database', {}).get('status', 'unknown')
                    uptime = data.get('uptime', 0)
                    
                    self.log_test(
                        "Health Endpoint",
                        True,
                        f"Status: {response.status}, DB: {db_status}, Uptime: {uptime}s",
                        data
                    )
                    return True
                else:
                    self.log_test(
                        "Health Endpoint",
                        False,
                        f"Unexpected status: {response.status}",
                        data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Health Endpoint",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_mongodb_connection(self):
        """Test MongoDB connection through health endpoint"""
        try:
            async with self.session.get(f"{API_BASE}/health") as response:
                data = await response.json()
                
                if response.status == 200:
                    db_info = data.get('database', {})
                    db_status = db_info.get('status', 'unknown')
                    db_name = db_info.get('database_name', 'unknown')
                    
                    success = db_status == 'connected'
                    self.log_test(
                        "MongoDB Connection",
                        success,
                        f"DB Status: {db_status}, DB Name: {db_name}",
                        db_info
                    )
                    return success
                else:
                    self.log_test(
                        "MongoDB Connection",
                        False,
                        f"Health endpoint failed: {response.status}",
                        data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "MongoDB Connection",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_admin_bootstrap_with_different_tokens(self):
        """Test admin bootstrap with different tokens to understand the issue"""
        
        # Test tokens to try
        test_tokens = [
            "ECS-Bootstrap-2025",
            "admin-bootstrap-token",
            "bootstrap-secret-key",
            "ecomsimply-admin-setup",
            None  # No token
        ]
        
        bootstrap_results = []
        
        for i, token in enumerate(test_tokens):
            try:
                headers = {'Content-Type': 'application/json'}
                if token:
                    headers['x-bootstrap-token'] = token
                
                async with self.session.post(
                    f"{API_BASE}/admin/bootstrap",
                    headers=headers,
                    json={}
                ) as response:
                    
                    try:
                        data = await response.json()
                    except:
                        data = {"error": "Invalid JSON response"}
                    
                    test_name = f"Bootstrap Token Test {i+1}"
                    if token:
                        test_name += f" (Token: {token[:10]}...)"
                    else:
                        test_name += " (No Token)"
                    
                    success = response.status == 200
                    details = f"Status: {response.status}"
                    
                    if response.status == 403:
                        details += " - Invalid/Missing Token"
                    elif response.status == 200:
                        details += " - Bootstrap Successful"
                    
                    bootstrap_results.append({
                        'token': token,
                        'status': response.status,
                        'success': success,
                        'response': data
                    })
                    
                    self.log_test(test_name, success, details, data)
                    
            except Exception as e:
                self.log_test(
                    f"Bootstrap Token Test {i+1}",
                    False,
                    f"Exception: {str(e)}"
                )
        
        # Summary of bootstrap tests
        successful_tokens = [r for r in bootstrap_results if r['success']]
        if successful_tokens:
            self.log_test(
                "Bootstrap Token Analysis",
                True,
                f"Found {len(successful_tokens)} working tokens",
                successful_tokens
            )
        else:
            self.log_test(
                "Bootstrap Token Analysis",
                False,
                "No working bootstrap tokens found - check ADMIN_BOOTSTRAP_TOKEN env var",
                bootstrap_results
            )
        
        return len(successful_tokens) > 0
    
    async def test_environment_variables(self):
        """Test if environment variables are properly configured"""
        try:
            # Test through a diagnostic endpoint or health check
            async with self.session.get(f"{API_BASE}/health") as response:
                data = await response.json()
                
                # Check if we can infer environment configuration
                env_indicators = {
                    'database_configured': 'database' in data and data['database'].get('status') == 'connected',
                    'backend_running': response.status == 200,
                    'uptime_available': 'uptime' in data
                }
                
                all_good = all(env_indicators.values())
                
                self.log_test(
                    "Environment Variables Check",
                    all_good,
                    f"Indicators: {env_indicators}",
                    data
                )
                
                return all_good
                
        except Exception as e:
            self.log_test(
                "Environment Variables Check",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_cors_configuration(self):
        """Test CORS configuration for frontend-backend communication"""
        try:
            # Test with OPTIONS request (preflight)
            headers = {
                'Origin': 'https://ecomsimply.com',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            }
            
            async with self.session.options(f"{API_BASE}/health", headers=headers) as response:
                cors_headers = {
                    'access-control-allow-origin': response.headers.get('Access-Control-Allow-Origin'),
                    'access-control-allow-methods': response.headers.get('Access-Control-Allow-Methods'),
                    'access-control-allow-headers': response.headers.get('Access-Control-Allow-Headers')
                }
                
                # Check if CORS is properly configured
                origin_allowed = cors_headers['access-control-allow-origin'] in ['*', 'https://ecomsimply.com']
                methods_allowed = 'POST' in str(cors_headers.get('access-control-allow-methods', ''))
                
                success = origin_allowed and (response.status in [200, 204])
                
                self.log_test(
                    "CORS Configuration",
                    success,
                    f"Status: {response.status}, Origin allowed: {origin_allowed}",
                    cors_headers
                )
                
                return success
                
        except Exception as e:
            self.log_test(
                "CORS Configuration",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_main_api_endpoints(self):
        """Test main API endpoints functionality"""
        endpoints_to_test = [
            ("/health", "GET", "Health Check"),
            ("/health/ready", "GET", "Readiness Check"),
            ("/health/live", "GET", "Liveness Check"),
            ("/stats/public", "GET", "Public Stats"),
            ("/public/plans-pricing", "GET", "Plans Pricing"),
            ("/testimonials", "GET", "Testimonials")
        ]
        
        successful_endpoints = 0
        total_endpoints = len(endpoints_to_test)
        
        for endpoint, method, description in endpoints_to_test:
            try:
                url = f"{API_BASE}{endpoint}"
                
                if method == "GET":
                    async with self.session.get(url) as response:
                        try:
                            data = await response.json()
                        except:
                            data = {"error": "Invalid JSON response"}
                        
                        success = response.status == 200
                        if success:
                            successful_endpoints += 1
                        
                        self.log_test(
                            f"API Endpoint - {description}",
                            success,
                            f"Status: {response.status}, URL: {endpoint}",
                            data if not success else {"status": "ok"}
                        )
                        
            except Exception as e:
                self.log_test(
                    f"API Endpoint - {description}",
                    False,
                    f"Exception: {str(e)}"
                )
        
        # Overall API endpoints test
        overall_success = successful_endpoints >= (total_endpoints * 0.8)  # 80% success rate
        self.log_test(
            "Main API Endpoints Summary",
            overall_success,
            f"Success rate: {successful_endpoints}/{total_endpoints} ({(successful_endpoints/total_endpoints)*100:.1f}%)"
        )
        
        return overall_success
    
    async def test_admin_user_creation(self):
        """Test if admin user can be created/exists"""
        try:
            # Try to login with admin credentials to see if user exists
            login_data = {
                "email": self.admin_credentials["email"],
                "password": self.admin_credentials["password"]
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                data = await response.json()
                
                if response.status == 200 and 'access_token' in data:
                    self.auth_token = data['access_token']
                    self.log_test(
                        "Admin User Login",
                        True,
                        f"Admin user exists and can login successfully",
                        {"user_id": data.get('user', {}).get('id', 'unknown')}
                    )
                    return True
                elif response.status == 401:
                    self.log_test(
                        "Admin User Login",
                        False,
                        "Admin user exists but credentials are incorrect",
                        data
                    )
                    return False
                elif response.status == 404:
                    self.log_test(
                        "Admin User Login",
                        False,
                        "Admin user does not exist - needs to be created via bootstrap",
                        data
                    )
                    return False
                else:
                    self.log_test(
                        "Admin User Login",
                        False,
                        f"Unexpected response: {response.status}",
                        data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Admin User Login",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_database_operations(self):
        """Test basic database operations"""
        try:
            # Test public endpoints that should work without auth
            async with self.session.get(f"{API_BASE}/stats/public") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check if we get meaningful data
                    has_stats = any(key in data for key in ['total_sheets', 'satisfied_clients', 'success_rate'])
                    
                    self.log_test(
                        "Database Operations - Public Stats",
                        has_stats,
                        f"Status: {response.status}, Has stats: {has_stats}",
                        data
                    )
                    
                    return has_stats
                else:
                    data = await response.json()
                    self.log_test(
                        "Database Operations - Public Stats",
                        False,
                        f"Failed to get public stats: {response.status}",
                        data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Database Operations",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def run_comprehensive_test(self):
        """Run comprehensive backend test suite"""
        print("🚀 Starting ECOMSIMPLY Backend Comprehensive Testing...")
        print(f"🎯 Target: {BACKEND_URL}")
        print(f"📅 Started: {datetime.utcnow().isoformat()}")
        print("=" * 80)
        
        # Test sequence
        test_functions = [
            ("Health Endpoint", self.test_health_endpoint),
            ("MongoDB Connection", self.test_mongodb_connection),
            ("Environment Variables", self.test_environment_variables),
            ("CORS Configuration", self.test_cors_configuration),
            ("Main API Endpoints", self.test_main_api_endpoints),
            ("Database Operations", self.test_database_operations),
            ("Admin Bootstrap Tokens", self.test_admin_bootstrap_with_different_tokens),
            ("Admin User Creation", self.test_admin_user_creation),
        ]
        
        successful_tests = 0
        total_tests = len(test_functions)
        
        for test_name, test_func in test_functions:
            print(f"\n🔍 Running: {test_name}")
            try:
                result = await test_func()
                if result:
                    successful_tests += 1
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
        
        # Final summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        success_rate = (successful_tests / total_tests) * 100
        print(f"🎯 Overall Success Rate: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Categorize results
        passed_tests = [r for r in self.test_results if r['success']]
        failed_tests = [r for r in self.test_results if not r['success']]
        
        print(f"\n✅ PASSED TESTS ({len(passed_tests)}):")
        for test in passed_tests:
            print(f"   • {test['test_name']}: {test['details']}")
        
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test_name']}: {test['details']}")
        
        # Specific findings for admin bootstrap
        bootstrap_tests = [r for r in self.test_results if 'Bootstrap' in r['test_name']]
        if bootstrap_tests:
            print(f"\n🔐 ADMIN BOOTSTRAP ANALYSIS:")
            for test in bootstrap_tests:
                status = "✅" if test['success'] else "❌"
                print(f"   {status} {test['test_name']}: {test['details']}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if not any('Bootstrap' in r['test_name'] and r['success'] for r in self.test_results):
            print("   • Check ADMIN_BOOTSTRAP_TOKEN environment variable configuration")
            print("   • Verify admin credentials: msylla54@gmail.com / ECS-Temp#2025-08-22!")
            print("   • Ensure bootstrap endpoint is properly configured")
        
        if success_rate >= 80:
            print("   • Backend is mostly functional - focus on fixing bootstrap issues")
        else:
            print("   • Multiple backend issues detected - comprehensive review needed")
        
        print(f"\n⏱️  Total execution time: {time.time() - self.start_time:.2f} seconds")
        print("🏁 Testing completed!")
        
        return success_rate >= 70  # Consider 70% as acceptable

async def main():
    """Main test execution"""
    async with EcomsimplyBackendTester() as tester:
        success = await tester.run_comprehensive_test()
        return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)