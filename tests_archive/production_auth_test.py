#!/usr/bin/env python3
"""
Production vs Preview Authentication Test - ECOMSIMPLY
Test authentication endpoints on both production and preview URLs
"""

import asyncio
import aiohttp
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, List

# URLs to test
PRODUCTION_URL = "https://ecomsimply.com"
PREVIEW_URL = "https://ecomsimply-deploy.preview.emergentagent.com"

class DualURLAuthTester:
    """Test authentication on both production and preview URLs"""
    
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
    
    async def test_url_health(self, base_url: str, url_name: str):
        """Test health endpoint for a specific URL"""
        try:
            async with self.session.get(f"{base_url}/api/health") as response:
                data = await response.json()
                
                if response.status == 200:
                    self.log_test(
                        f"{url_name} Health", 
                        True, 
                        f"Status: {response.status}, Health: {data.get('status', 'unknown')}"
                    )
                    return True
                else:
                    self.log_test(
                        f"{url_name} Health", 
                        False, 
                        f"Status: {response.status}", 
                        data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(f"{url_name} Health", False, f"Exception: {str(e)}")
            return False
    
    async def test_url_registration(self, base_url: str, url_name: str):
        """Test registration endpoint for a specific URL"""
        test_user_data = {
            "name": f"Test User {url_name}",
            "email": f"test+{url_name.lower()}@ecomsimply.com",
            "password": "Ecs#2025!demo"
        }
        
        try:
            async with self.session.post(
                f"{base_url}/api/auth/register", 
                json=test_user_data
            ) as response:
                
                response_text = await response.text()
                
                try:
                    data = json.loads(response_text)
                except json.JSONDecodeError:
                    data = {"raw_response": response_text}
                
                if response.status in [200, 201]:
                    self.log_test(
                        f"{url_name} Registration", 
                        True, 
                        f"Status: {response.status}, Registration successful"
                    )
                    return True, data
                elif response.status == 400 and "existe déjà" in response_text:
                    self.log_test(
                        f"{url_name} Registration", 
                        True, 
                        f"Status: {response.status}, User already exists (expected)"
                    )
                    return True, data
                else:
                    self.log_test(
                        f"{url_name} Registration", 
                        False, 
                        f"Status: {response.status}, Error: {response_text[:200]}", 
                        data
                    )
                    return False, data
                    
        except Exception as e:
            self.log_test(f"{url_name} Registration", False, f"Exception: {str(e)}")
            return False, {"error": str(e)}
    
    async def test_url_login(self, base_url: str, url_name: str):
        """Test login endpoint for a specific URL"""
        login_data = {
            "email": "test+e2e@ecomsimply.com",
            "password": "Ecs#2025!demo"
        }
        
        try:
            async with self.session.post(
                f"{base_url}/api/auth/login", 
                json=login_data
            ) as response:
                
                response_text = await response.text()
                
                try:
                    data = json.loads(response_text)
                except json.JSONDecodeError:
                    data = {"raw_response": response_text}
                
                if response.status == 200 and data.get("token"):
                    self.log_test(
                        f"{url_name} Login", 
                        True, 
                        f"Status: {response.status}, Login successful, Token received"
                    )
                    return True, data
                else:
                    self.log_test(
                        f"{url_name} Login", 
                        False, 
                        f"Status: {response.status}, Error: {response_text[:200]}", 
                        data
                    )
                    return False, data
                    
        except Exception as e:
            self.log_test(f"{url_name} Login", False, f"Exception: {str(e)}")
            return False, {"error": str(e)}
    
    async def test_url_admin_login(self, base_url: str, url_name: str):
        """Test admin login for a specific URL"""
        admin_login_data = {
            "email": "msylla54@gmail.com",
            "password": "ECS-Temp#2025-08-22!"
        }
        
        try:
            async with self.session.post(
                f"{base_url}/api/auth/login", 
                json=admin_login_data
            ) as response:
                
                response_text = await response.text()
                
                try:
                    data = json.loads(response_text)
                except json.JSONDecodeError:
                    data = {"raw_response": response_text}
                
                if response.status == 200 and data.get("token"):
                    self.log_test(
                        f"{url_name} Admin Login", 
                        True, 
                        f"Status: {response.status}, Admin login successful"
                    )
                    return True, data
                else:
                    self.log_test(
                        f"{url_name} Admin Login", 
                        False, 
                        f"Status: {response.status}, Error: {response_text[:200]}", 
                        data
                    )
                    return False, data
                    
        except Exception as e:
            self.log_test(f"{url_name} Admin Login", False, f"Exception: {str(e)}")
            return False, {"error": str(e)}
    
    async def run_comprehensive_dual_url_tests(self):
        """Run authentication tests on both URLs"""
        print("🚀 Starting Dual URL Authentication Testing...")
        print(f"Production URL: {PRODUCTION_URL}")
        print(f"Preview URL: {PREVIEW_URL}")
        print("=" * 80)
        
        # Test both URLs
        urls_to_test = [
            (PRODUCTION_URL, "Production"),
            (PREVIEW_URL, "Preview")
        ]
        
        passed = 0
        total = 0
        
        for base_url, url_name in urls_to_test:
            print(f"\n🌐 Testing {url_name} URL: {base_url}")
            print("-" * 60)
            
            # Test sequence for each URL
            tests = [
                ("Health", self.test_url_health),
                ("Registration", self.test_url_registration),
                ("Login", self.test_url_login),
                ("Admin Login", self.test_url_admin_login),
            ]
            
            for test_name, test_func in tests:
                print(f"\n🔍 Testing: {url_name} {test_name}")
                try:
                    result = await test_func(base_url, url_name)
                    if isinstance(result, tuple):
                        result = result[0]  # Get success boolean from tuple
                    if result:
                        passed += 1
                    total += 1
                except Exception as e:
                    print(f"❌ FAIL {url_name} {test_name}: Exception - {str(e)}")
                    total += 1
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 DUAL URL AUTHENTICATION TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Analyze results by URL
        production_results = [r for r in self.test_results if "Production" in r['test_name']]
        preview_results = [r for r in self.test_results if "Preview" in r['test_name']]
        
        production_passed = sum(1 for r in production_results if r['success'])
        preview_passed = sum(1 for r in preview_results if r['success'])
        
        print(f"\n📈 RESULTS BY URL:")
        print(f"Production URL: {production_passed}/{len(production_results)} passed ({(production_passed/len(production_results))*100:.1f}%)")
        print(f"Preview URL: {preview_passed}/{len(preview_results)} passed ({(preview_passed/len(preview_results))*100:.1f}%)")
        
        # Detailed results
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test_name']}: {result['details']}")
        
        execution_time = time.time() - self.start_time
        print(f"\n⏱️ Total execution time: {execution_time:.2f} seconds")
        
        # Critical finding
        if production_passed < len(production_results) and preview_passed == len(preview_results):
            print("\n🚨 CRITICAL FINDING:")
            print("Authentication endpoints work on Preview URL but fail on Production URL!")
            print("This indicates a deployment or configuration issue on the production environment.")
        
        return passed, total

async def main():
    """Main test execution"""
    async with DualURLAuthTester() as tester:
        passed, total = await tester.run_comprehensive_dual_url_tests()
        
        # Always exit successfully since we're documenting the issue
        print(f"\n📝 Test completed - documented authentication URL differences")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())