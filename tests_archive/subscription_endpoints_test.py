#!/usr/bin/env python3
"""
ECOMSIMPLY Subscription Endpoints Testing
Focus: Testing subscription endpoints causing frontend errors
- GET /api/subscription/plans
- GET /api/subscription/status  
- GET /api/subscription/incomplete
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime

# Get backend URL from frontend .env
BACKEND_URL = "https://ecomsimply.com"

print("🧪 ECOMSIMPLY SUBSCRIPTION ENDPOINTS TESTING")
print("=" * 60)
print(f"🌐 Backend URL: {BACKEND_URL}")
print("=" * 60)

class SubscriptionEndpointsTester:
    """Tester for subscription endpoints causing frontend errors"""
    
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = {
            'plans_endpoint': {'passed': 0, 'failed': 0, 'details': []},
            'status_endpoint': {'passed': 0, 'failed': 0, 'details': []},
            'incomplete_endpoint': {'passed': 0, 'failed': 0, 'details': []},
            'authentication': {'passed': 0, 'failed': 0, 'details': []}
        }
        self.auth_token = None
        self.demo_user_email = "demo@ecomsimply.com"
        self.demo_user_password = "demo123"
    
    def log_test(self, component: str, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {test_name}")
        if details:
            print(f"    → {details}")
        
        if success:
            self.test_results[component]['passed'] += 1
        else:
            self.test_results[component]['failed'] += 1
        
        self.test_results[component]['details'].append({
            'test': test_name,
            'success': success,
            'details': details
        })
    
    async def authenticate_demo_user(self, session):
        """Authenticate with demo user credentials"""
        print("\n🔐 AUTHENTICATION TESTING")
        print("-" * 40)
        
        try:
            # Try to login with demo credentials
            login_data = {
                "email": self.demo_user_email,
                "password": self.demo_user_password
            }
            
            async with session.post(f"{self.backend_url}/api/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'access_token' in data:
                        self.auth_token = data['access_token']
                        self.log_test('authentication', 'Demo user login', True, 
                                    f"Token obtained: {self.auth_token[:20]}...")
                        return True
                    else:
                        self.log_test('authentication', 'Demo user login', False, 
                                    "No access_token in response")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test('authentication', 'Demo user login', False, 
                                f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test('authentication', 'Demo user login', False, f"Exception: {str(e)}")
            return False
    
    async def test_plans_endpoint(self, session):
        """Test GET /api/subscription/plans endpoint"""
        print("\n📋 TESTING PLANS ENDPOINT")
        print("-" * 40)
        
        try:
            # Test without authentication first
            async with session.get(f"{self.backend_url}/api/subscription/plans") as response:
                status_code = response.status
                
                if status_code == 200:
                    data = await response.json()
                    
                    # Check if response contains plans data
                    success = 'plans' in data or isinstance(data, list)
                    self.log_test('plans_endpoint', 'Endpoint accessibility (no auth)', success,
                                f"Status: {status_code}, Has plans data: {success}")
                    
                    if success:
                        # Check data structure
                        plans_data = data.get('plans', data) if 'plans' in data else data
                        
                        if isinstance(plans_data, list):
                            success = len(plans_data) > 0
                            self.log_test('plans_endpoint', 'Plans array not empty', success,
                                        f"Found {len(plans_data)} plans")
                            
                            # Check plan structure
                            if plans_data:
                                first_plan = plans_data[0]
                                required_fields = ['plan_name', 'price', 'currency']
                                has_required = all(field in first_plan for field in required_fields)
                                self.log_test('plans_endpoint', 'Plan structure validation', has_required,
                                            f"Required fields present: {has_required}")
                                
                                # Log plan details
                                for plan in plans_data:
                                    plan_name = plan.get('plan_name', 'Unknown')
                                    price = plan.get('price', 'N/A')
                                    currency = plan.get('currency', 'N/A')
                                    print(f"    📦 Plan: {plan_name} - {price} {currency}")
                        else:
                            success = isinstance(plans_data, dict) and len(plans_data) > 0
                            self.log_test('plans_endpoint', 'Plans object structure', success,
                                        f"Plans data type: {type(plans_data)}")
                    
                elif status_code == 401:
                    self.log_test('plans_endpoint', 'Authentication required', True,
                                f"Status: {status_code} - Authentication required")
                else:
                    error_text = await response.text()
                    self.log_test('plans_endpoint', 'Endpoint response', False,
                                f"Status: {status_code}, Error: {error_text}")
                    
        except Exception as e:
            self.log_test('plans_endpoint', 'Plans endpoint test', False, f"Exception: {str(e)}")
    
    async def test_status_endpoint(self, session):
        """Test GET /api/subscription/status endpoint"""
        print("\n📊 TESTING STATUS ENDPOINT")
        print("-" * 40)
        
        try:
            # Test without authentication
            async with session.get(f"{self.backend_url}/api/subscription/status") as response:
                status_code = response.status
                
                if status_code == 401:
                    self.log_test('status_endpoint', 'Authentication required (no auth)', True,
                                f"Status: {status_code} - Correctly requires authentication")
                elif status_code == 200:
                    self.log_test('status_endpoint', 'Accessible without auth', True,
                                f"Status: {status_code} - No authentication required")
                else:
                    error_text = await response.text()
                    self.log_test('status_endpoint', 'Endpoint response (no auth)', False,
                                f"Status: {status_code}, Error: {error_text}")
            
            # Test with authentication if we have a token
            if self.auth_token:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                async with session.get(f"{self.backend_url}/api/subscription/status", headers=headers) as response:
                    status_code = response.status
                    
                    if status_code == 200:
                        data = await response.json()
                        
                        # Check response structure
                        expected_fields = ['subscription_plan', 'status']
                        has_expected = any(field in data for field in expected_fields)
                        self.log_test('status_endpoint', 'Authenticated access', True,
                                    f"Status: {status_code}, Has subscription data: {has_expected}")
                        
                        if has_expected:
                            plan = data.get('subscription_plan', 'N/A')
                            status = data.get('status', 'N/A')
                            print(f"    📋 User Plan: {plan}")
                            print(f"    📊 Status: {status}")
                    else:
                        error_text = await response.text()
                        self.log_test('status_endpoint', 'Authenticated access', False,
                                    f"Status: {status_code}, Error: {error_text}")
            else:
                self.log_test('status_endpoint', 'Authenticated test skipped', False,
                            "No authentication token available")
                    
        except Exception as e:
            self.log_test('status_endpoint', 'Status endpoint test', False, f"Exception: {str(e)}")
    
    async def test_incomplete_endpoint(self, session):
        """Test GET /api/subscription/incomplete endpoint"""
        print("\n⏳ TESTING INCOMPLETE ENDPOINT")
        print("-" * 40)
        
        try:
            # Test without authentication
            async with session.get(f"{self.backend_url}/api/subscription/incomplete") as response:
                status_code = response.status
                
                if status_code == 404:
                    self.log_test('incomplete_endpoint', 'Endpoint existence', False,
                                f"Status: {status_code} - Endpoint does not exist")
                elif status_code == 401:
                    self.log_test('incomplete_endpoint', 'Authentication required (no auth)', True,
                                f"Status: {status_code} - Correctly requires authentication")
                elif status_code == 200:
                    data = await response.json()
                    self.log_test('incomplete_endpoint', 'Endpoint accessible (no auth)', True,
                                f"Status: {status_code}, Response: {type(data)}")
                else:
                    error_text = await response.text()
                    self.log_test('incomplete_endpoint', 'Endpoint response (no auth)', False,
                                f"Status: {status_code}, Error: {error_text}")
            
            # Test with authentication if we have a token
            if self.auth_token:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                async with session.get(f"{self.backend_url}/api/subscription/incomplete", headers=headers) as response:
                    status_code = response.status
                    
                    if status_code == 404:
                        self.log_test('incomplete_endpoint', 'Endpoint existence (authenticated)', False,
                                    f"Status: {status_code} - Endpoint does not exist")
                    elif status_code == 200:
                        data = await response.json()
                        self.log_test('incomplete_endpoint', 'Authenticated access', True,
                                    f"Status: {status_code}, Response type: {type(data)}")
                        
                        # Check if it returns incomplete subscriptions data
                        if isinstance(data, list):
                            print(f"    📋 Found {len(data)} incomplete subscriptions")
                        elif isinstance(data, dict):
                            print(f"    📋 Response keys: {list(data.keys())}")
                    else:
                        error_text = await response.text()
                        self.log_test('incomplete_endpoint', 'Authenticated access', False,
                                    f"Status: {status_code}, Error: {error_text}")
            else:
                self.log_test('incomplete_endpoint', 'Authenticated test skipped', False,
                            "No authentication token available")
                    
        except Exception as e:
            self.log_test('incomplete_endpoint', 'Incomplete endpoint test', False, f"Exception: {str(e)}")
    
    async def test_backend_health(self, session):
        """Test basic backend connectivity"""
        print("\n🏥 TESTING BACKEND HEALTH")
        print("-" * 40)
        
        try:
            # Test basic health endpoint
            async with session.get(f"{self.backend_url}/api/health") as response:
                if response.status == 200:
                    self.log_test('authentication', 'Backend connectivity', True,
                                f"Health endpoint accessible: {response.status}")
                else:
                    self.log_test('authentication', 'Backend connectivity', False,
                                f"Health endpoint status: {response.status}")
        except Exception as e:
            self.log_test('authentication', 'Backend connectivity', False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all subscription endpoint tests"""
        print("🚀 Starting subscription endpoints testing...")
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Test backend health first
            await self.test_backend_health(session)
            
            # Try to authenticate
            auth_success = await self.authenticate_demo_user(session)
            
            # Test all subscription endpoints
            await self.test_plans_endpoint(session)
            await self.test_status_endpoint(session)
            await self.test_incomplete_endpoint(session)
        
        # Print final summary
        self.print_final_summary()
    
    def print_final_summary(self):
        """Print final test summary"""
        print("\n" + "=" * 60)
        print("📊 SUBSCRIPTION ENDPOINTS TEST SUMMARY")
        print("=" * 60)
        
        total_passed = 0
        total_failed = 0
        
        for component, results in self.test_results.items():
            passed = results['passed']
            failed = results['failed']
            total = passed + failed
            
            if total > 0:
                success_rate = (passed / total) * 100
                status = "✅" if failed == 0 else "⚠️" if success_rate >= 70 else "❌"
                
                print(f"{status} {component.upper()}: {passed}/{total} tests passed ({success_rate:.1f}%)")
                
                # Show failed tests
                if failed > 0:
                    failed_tests = [detail for detail in results['details'] if not detail['success']]
                    for test in failed_tests:
                        print(f"    ❌ {test['test']}: {test['details']}")
                
                total_passed += passed
                total_failed += failed
        
        print("-" * 60)
        overall_total = total_passed + total_failed
        overall_success_rate = (total_passed / overall_total) * 100 if overall_total > 0 else 0
        
        print(f"🎯 OVERALL RESULT: {total_passed}/{overall_total} tests passed ({overall_success_rate:.1f}%)")
        
        print("\n🔍 ENDPOINTS TESTED:")
        print("  📋 GET /api/subscription/plans - Plan data structure")
        print("  📊 GET /api/subscription/status - User subscription data")
        print("  ⏳ GET /api/subscription/incomplete - Incomplete subscriptions")
        
        print("\n💡 FRONTEND ERROR ANALYSIS:")
        if total_failed > 0:
            print("  ❌ Issues found that could cause frontend errors:")
            for component, results in self.test_results.items():
                failed_tests = [detail for detail in results['details'] if not detail['success']]
                for test in failed_tests:
                    print(f"    • {test['test']}: {test['details']}")
        else:
            print("  ✅ All endpoints working correctly - frontend error may be elsewhere")
        
        print(f"\n⏱️ Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    """Main entry point"""
    tester = SubscriptionEndpointsTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())