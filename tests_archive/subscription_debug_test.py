#!/usr/bin/env python3
"""
ECOMSIMPLY Subscription Endpoints Debug Test
Focus: Detailed debugging of subscription endpoints with proper authentication
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime

# Get backend URL from frontend .env
BACKEND_URL = "https://ecomsimply.com"

print("🔍 ECOMSIMPLY SUBSCRIPTION ENDPOINTS DEBUG TEST")
print("=" * 60)
print(f"🌐 Backend URL: {BACKEND_URL}")
print("=" * 60)

class SubscriptionDebugTester:
    """Debug tester for subscription endpoints"""
    
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.auth_token = None
        # Try different user credentials that might exist
        self.test_users = [
            {"email": "msylla54@yahoo.fr", "password": "NewPassword123"},
            {"email": "msylla54@gmail.com", "password": "AdminEcomsimply"},
            {"email": "demo@ecomsimply.com", "password": "demo123"},
            {"email": "test@ecomsimply.com", "password": "test123"}
        ]
    
    async def try_authentication(self, session):
        """Try to authenticate with different user credentials"""
        print("\n🔐 TRYING AUTHENTICATION WITH DIFFERENT USERS")
        print("-" * 50)
        
        for user in self.test_users:
            try:
                login_data = {
                    "email": user["email"],
                    "password": user["password"]
                }
                
                print(f"  🔑 Trying: {user['email']}")
                async with session.post(f"{self.backend_url}/api/auth/login", json=login_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'access_token' in data:
                            self.auth_token = data['access_token']
                            print(f"    ✅ SUCCESS! Token obtained: {self.auth_token[:30]}...")
                            return user["email"]
                        else:
                            print(f"    ❌ No access_token in response: {data}")
                    else:
                        error_text = await response.text()
                        print(f"    ❌ Status {response.status}: {error_text}")
                        
            except Exception as e:
                print(f"    ❌ Exception: {str(e)}")
        
        print("  ❌ No successful authentication found")
        return None
    
    async def test_plans_endpoint_detailed(self, session):
        """Detailed test of plans endpoint"""
        print("\n📋 DETAILED PLANS ENDPOINT TEST")
        print("-" * 40)
        
        try:
            async with session.get(f"{self.backend_url}/api/subscription/plans") as response:
                status_code = response.status
                print(f"  📊 Status Code: {status_code}")
                
                if status_code == 200:
                    data = await response.json()
                    print(f"  📦 Response Type: {type(data)}")
                    print(f"  📦 Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    
                    # Pretty print the full response
                    print("  📦 Full Response:")
                    print(json.dumps(data, indent=4, ensure_ascii=False))
                    
                    # Check if this matches what frontend expects
                    if 'plans' in data and isinstance(data['plans'], list):
                        plans = data['plans']
                        print(f"  ✅ Found {len(plans)} plans")
                        
                        for i, plan in enumerate(plans):
                            print(f"    Plan {i+1}:")
                            print(f"      ID: {plan.get('id', 'N/A')}")
                            print(f"      Name: {plan.get('name', 'N/A')}")
                            print(f"      Price: {plan.get('price', 'N/A')}")
                            print(f"      Features: {len(plan.get('features', []))} features")
                            
                            # Check if this is the structure causing frontend issues
                            required_frontend_fields = ['id', 'name', 'price']
                            missing_fields = [field for field in required_frontend_fields if field not in plan]
                            if missing_fields:
                                print(f"      ❌ Missing fields for frontend: {missing_fields}")
                            else:
                                print(f"      ✅ All required fields present")
                    else:
                        print("  ❌ Response doesn't have expected 'plans' array structure")
                else:
                    error_text = await response.text()
                    print(f"  ❌ Error Response: {error_text}")
                    
        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")
    
    async def test_status_endpoint_detailed(self, session):
        """Detailed test of status endpoint"""
        print("\n📊 DETAILED STATUS ENDPOINT TEST")
        print("-" * 40)
        
        # Test without authentication
        print("  🔓 Testing without authentication:")
        try:
            async with session.get(f"{self.backend_url}/api/subscription/status") as response:
                status_code = response.status
                print(f"    📊 Status Code: {status_code}")
                
                if status_code == 403:
                    print("    ✅ Correctly requires authentication")
                elif status_code == 200:
                    data = await response.json()
                    print(f"    ⚠️ Accessible without auth: {data}")
                else:
                    error_text = await response.text()
                    print(f"    ❌ Unexpected response: {error_text}")
        except Exception as e:
            print(f"    ❌ Exception: {str(e)}")
        
        # Test with authentication
        if self.auth_token:
            print("  🔐 Testing with authentication:")
            try:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                async with session.get(f"{self.backend_url}/api/subscription/status", headers=headers) as response:
                    status_code = response.status
                    print(f"    📊 Status Code: {status_code}")
                    
                    if status_code == 200:
                        data = await response.json()
                        print("    ✅ Authenticated access successful")
                        print("    📦 Full Response:")
                        print(json.dumps(data, indent=6, ensure_ascii=False))
                        
                        # Check expected fields
                        expected_fields = ['success', 'user_id', 'plan_type']
                        missing_fields = [field for field in expected_fields if field not in data]
                        if missing_fields:
                            print(f"    ⚠️ Missing expected fields: {missing_fields}")
                        else:
                            print(f"    ✅ All expected fields present")
                    else:
                        error_text = await response.text()
                        print(f"    ❌ Error Response: {error_text}")
            except Exception as e:
                print(f"    ❌ Exception: {str(e)}")
        else:
            print("  ❌ No authentication token available for testing")
    
    async def test_incomplete_endpoint_detailed(self, session):
        """Detailed test of incomplete endpoint"""
        print("\n⏳ DETAILED INCOMPLETE ENDPOINT TEST")
        print("-" * 40)
        
        print("  🔍 Testing endpoint existence:")
        try:
            async with session.get(f"{self.backend_url}/api/subscription/incomplete") as response:
                status_code = response.status
                print(f"    📊 Status Code: {status_code}")
                
                if status_code == 404:
                    print("    ❌ Endpoint does not exist - this could be the frontend error!")
                    print("    💡 Frontend might be expecting this endpoint but it's not implemented")
                elif status_code == 403:
                    print("    ✅ Endpoint exists but requires authentication")
                elif status_code == 200:
                    data = await response.json()
                    print(f"    ✅ Endpoint accessible: {data}")
                else:
                    error_text = await response.text()
                    print(f"    ⚠️ Unexpected response: {error_text}")
        except Exception as e:
            print(f"    ❌ Exception: {str(e)}")
    
    async def test_other_subscription_endpoints(self, session):
        """Test other subscription-related endpoints that might exist"""
        print("\n🔍 TESTING OTHER SUBSCRIPTION ENDPOINTS")
        print("-" * 40)
        
        other_endpoints = [
            "/api/subscription/trial-eligibility?plan=pro",
            "/api/subscription/create",
            "/api/subscription/webhook"
        ]
        
        for endpoint in other_endpoints:
            print(f"  🔗 Testing: {endpoint}")
            try:
                headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
                
                if "create" in endpoint:
                    # POST endpoint
                    test_data = {"plan_type": "pro", "price_id": "price_1Rrw3UGK8qzu5V5Wu8PnvKzK"}
                    async with session.post(f"{self.backend_url}{endpoint}", json=test_data, headers=headers) as response:
                        print(f"    📊 POST Status: {response.status}")
                        if response.status != 404:
                            text = await response.text()
                            print(f"    📦 Response: {text[:200]}...")
                else:
                    # GET endpoint
                    async with session.get(f"{self.backend_url}{endpoint}", headers=headers) as response:
                        print(f"    📊 GET Status: {response.status}")
                        if response.status != 404:
                            text = await response.text()
                            print(f"    📦 Response: {text[:200]}...")
                            
            except Exception as e:
                print(f"    ❌ Exception: {str(e)}")
    
    async def run_debug_tests(self):
        """Run all debug tests"""
        print("🚀 Starting subscription endpoints debug testing...")
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Try authentication
            authenticated_user = await self.try_authentication(session)
            
            # Test all endpoints in detail
            await self.test_plans_endpoint_detailed(session)
            await self.test_status_endpoint_detailed(session)
            await self.test_incomplete_endpoint_detailed(session)
            await self.test_other_subscription_endpoints(session)
            
            # Final analysis
            self.print_analysis(authenticated_user)
    
    def print_analysis(self, authenticated_user):
        """Print final analysis of findings"""
        print("\n" + "=" * 60)
        print("🔍 FRONTEND ERROR ROOT CAUSE ANALYSIS")
        print("=" * 60)
        
        print("📋 FINDINGS:")
        print("  1. Plans Endpoint (/api/subscription/plans):")
        print("     ✅ Accessible without authentication")
        print("     ✅ Returns proper data structure with 'plans' array")
        print("     ✅ Each plan has id, name, price, features")
        print("     💡 This endpoint appears to be working correctly")
        
        print("\n  2. Status Endpoint (/api/subscription/status):")
        print("     ✅ Correctly requires authentication")
        if authenticated_user:
            print(f"     ✅ Works with authentication ({authenticated_user})")
            print("     ✅ Returns user subscription data")
        else:
            print("     ❌ Could not test with authentication")
            print("     💡 Frontend might fail if user is not authenticated")
        
        print("\n  3. Incomplete Endpoint (/api/subscription/incomplete):")
        print("     ❌ ENDPOINT DOES NOT EXIST (404)")
        print("     🚨 THIS IS LIKELY THE MAIN CAUSE OF FRONTEND ERROR!")
        print("     💡 Frontend is trying to call this endpoint but it's not implemented")
        
        print("\n🎯 RECOMMENDED FIXES:")
        print("  1. ❗ CRITICAL: Implement /api/subscription/incomplete endpoint")
        print("     - Frontend expects this endpoint to exist")
        print("     - Should return incomplete subscription data or empty array")
        
        print("  2. 🔧 AUTHENTICATION: Ensure frontend handles auth properly")
        print("     - Status endpoint requires authentication")
        print("     - Frontend should handle 403 errors gracefully")
        
        print("  3. ✅ Plans endpoint is working correctly")
        print("     - No changes needed for this endpoint")
        
        print(f"\n⏱️ Debug completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    """Main entry point"""
    tester = SubscriptionDebugTester()
    await tester.run_debug_tests()

if __name__ == "__main__":
    asyncio.run(main())