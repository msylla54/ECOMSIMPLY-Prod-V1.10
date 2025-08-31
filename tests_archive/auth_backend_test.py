#!/usr/bin/env python3
"""
Authentication Backend Test - ECOMSIMPLY
Focused test for authentication endpoints server errors
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Configuration - Use production URL from frontend/.env
BACKEND_URL = "https://ecomsimply-deploy.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class AuthenticationTester:
    """Focused tester for authentication endpoints"""
    
    def __init__(self):
        self.session = None
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
        print(f"{status} {test_name}: {details}")
        
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
    
    async def test_health_endpoint(self):
        """Test basic health endpoint"""
        try:
            async with self.session.get(f"{API_BASE}/health") as response:
                data = await response.json()
                
                if response.status == 200:
                    self.log_test(
                        "Health Endpoint", 
                        True, 
                        f"Status: {response.status}, Health: {data.get('status', 'unknown')}"
                    )
                    return True
                else:
                    self.log_test(
                        "Health Endpoint", 
                        False, 
                        f"Status: {response.status}", 
                        data
                    )
                    return False
                    
        except Exception as e:
            self.log_test("Health Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def test_registration_endpoint(self):
        """Test user registration endpoint with real data"""
        test_user_data = {
            "name": "Test User E2E",
            "email": "test+e2e@ecomsimply.com",
            "password": "Ecs#2025!demo"
        }
        
        try:
            async with self.session.post(
                f"{API_BASE}/auth/register", 
                json=test_user_data
            ) as response:
                
                # Get response text first to handle both JSON and text responses
                response_text = await response.text()
                
                try:
                    data = json.loads(response_text)
                except json.JSONDecodeError:
                    data = {"raw_response": response_text}
                
                if response.status == 200 or response.status == 201:
                    self.log_test(
                        "Registration Endpoint", 
                        True, 
                        f"Status: {response.status}, User registered successfully"
                    )
                    return True, data
                else:
                    self.log_test(
                        "Registration Endpoint", 
                        False, 
                        f"Status: {response.status}, Error: {response_text[:200]}", 
                        data
                    )
                    return False, data
                    
        except Exception as e:
            self.log_test("Registration Endpoint", False, f"Exception: {str(e)}")
            return False, {"error": str(e)}
    
    async def test_login_endpoint(self):
        """Test user login endpoint"""
        login_data = {
            "email": "test+e2e@ecomsimply.com",
            "password": "Ecs#2025!demo"
        }
        
        try:
            async with self.session.post(
                f"{API_BASE}/auth/login", 
                json=login_data
            ) as response:
                
                response_text = await response.text()
                
                try:
                    data = json.loads(response_text)
                except json.JSONDecodeError:
                    data = {"raw_response": response_text}
                
                if response.status == 200:
                    self.log_test(
                        "Login Endpoint", 
                        True, 
                        f"Status: {response.status}, Login successful"
                    )
                    return True, data
                else:
                    self.log_test(
                        "Login Endpoint", 
                        False, 
                        f"Status: {response.status}, Error: {response_text[:200]}", 
                        data
                    )
                    return False, data
                    
        except Exception as e:
            self.log_test("Login Endpoint", False, f"Exception: {str(e)}")
            return False, {"error": str(e)}
    
    async def test_admin_login(self):
        """Test admin login with known credentials"""
        admin_login_data = {
            "email": "msylla54@gmail.com",
            "password": "ECS-Temp#2025-08-22!"
        }
        
        try:
            async with self.session.post(
                f"{API_BASE}/auth/login", 
                json=admin_login_data
            ) as response:
                
                response_text = await response.text()
                
                try:
                    data = json.loads(response_text)
                except json.JSONDecodeError:
                    data = {"raw_response": response_text}
                
                if response.status == 200:
                    self.log_test(
                        "Admin Login", 
                        True, 
                        f"Status: {response.status}, Admin login successful"
                    )
                    return True, data
                else:
                    self.log_test(
                        "Admin Login", 
                        False, 
                        f"Status: {response.status}, Error: {response_text[:200]}", 
                        data
                    )
                    return False, data
                    
        except Exception as e:
            self.log_test("Admin Login", False, f"Exception: {str(e)}")
            return False, {"error": str(e)}
    
    async def test_mongodb_connection(self):
        """Test MongoDB connection via health endpoint"""
        try:
            async with self.session.get(f"{API_BASE}/health") as response:
                data = await response.json()
                
                # Check if database status is included in health response
                db_status = data.get('database', {}).get('status', 'unknown')
                
                if db_status == 'healthy':
                    self.log_test(
                        "MongoDB Connection", 
                        True, 
                        f"Database status: {db_status}"
                    )
                    return True
                else:
                    self.log_test(
                        "MongoDB Connection", 
                        False, 
                        f"Database status: {db_status}", 
                        data
                    )
                    return False
                    
        except Exception as e:
            self.log_test("MongoDB Connection", False, f"Exception: {str(e)}")
            return False
    
    async def test_bcrypt_jwt_dependencies(self):
        """Test if bcrypt and JWT dependencies are working by checking endpoints"""
        try:
            # Test with invalid credentials to see if bcrypt is working
            invalid_login = {
                "email": "nonexistent@test.com",
                "password": "wrongpassword"
            }
            
            async with self.session.post(
                f"{API_BASE}/auth/login", 
                json=invalid_login
            ) as response:
                
                response_text = await response.text()
                
                # If we get a proper error response (not 500), bcrypt/JWT are likely working
                if response.status in [400, 401, 404]:
                    self.log_test(
                        "Bcrypt/JWT Dependencies", 
                        True, 
                        f"Dependencies working - proper error response: {response.status}"
                    )
                    return True
                elif response.status == 500:
                    self.log_test(
                        "Bcrypt/JWT Dependencies", 
                        False, 
                        f"Server error suggests dependency issues: {response_text[:200]}"
                    )
                    return False
                else:
                    self.log_test(
                        "Bcrypt/JWT Dependencies", 
                        True, 
                        f"Unexpected but non-500 response: {response.status}"
                    )
                    return True
                    
        except Exception as e:
            self.log_test("Bcrypt/JWT Dependencies", False, f"Exception: {str(e)}")
            return False
    
    async def test_bootstrap_endpoint(self):
        """Test admin bootstrap endpoint"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'x-bootstrap-token': 'ECS-Bootstrap-2025-Secure-Token'
            }
            
            async with self.session.post(
                f"{API_BASE}/admin/bootstrap",
                headers=headers
            ) as response:
                
                response_text = await response.text()
                
                try:
                    data = json.loads(response_text)
                except json.JSONDecodeError:
                    data = {"raw_response": response_text}
                
                if response.status == 200:
                    self.log_test(
                        "Bootstrap Endpoint", 
                        True, 
                        f"Status: {response.status}, Bootstrap successful"
                    )
                    return True
                else:
                    self.log_test(
                        "Bootstrap Endpoint", 
                        False, 
                        f"Status: {response.status}, Error: {response_text[:200]}", 
                        data
                    )
                    return False
                    
        except Exception as e:
            self.log_test("Bootstrap Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def run_comprehensive_auth_tests(self):
        """Run all authentication tests"""
        print("🚀 Starting Comprehensive Authentication Testing...")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print("=" * 60)
        
        # Test sequence
        tests = [
            ("Health Check", self.test_health_endpoint),
            ("MongoDB Connection", self.test_mongodb_connection),
            ("Bcrypt/JWT Dependencies", self.test_bcrypt_jwt_dependencies),
            ("Bootstrap Endpoint", self.test_bootstrap_endpoint),
            ("Admin Login", self.test_admin_login),
            ("User Registration", self.test_registration_endpoint),
            ("User Login", self.test_login_endpoint),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Testing: {test_name}")
            try:
                result = await test_func()
                if result:
                    passed += 1
            except Exception as e:
                print(f"❌ FAIL {test_name}: Exception - {str(e)}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 AUTHENTICATION TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Detailed results
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test_name']}: {result['details']}")
        
        execution_time = time.time() - self.start_time
        print(f"\n⏱️ Total execution time: {execution_time:.2f} seconds")
        
        return passed, total

async def main():
    """Main test execution"""
    async with AuthenticationTester() as tester:
        passed, total = await tester.run_comprehensive_auth_tests()
        
        # Exit with appropriate code
        if passed == total:
            print("\n🎉 All authentication tests passed!")
            sys.exit(0)
        else:
            print(f"\n⚠️ {total - passed} authentication tests failed!")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())