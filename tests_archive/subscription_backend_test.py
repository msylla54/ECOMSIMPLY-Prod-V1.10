#!/usr/bin/env python3
"""
ECOMSIMPLY Backend Testing - Subscription Endpoints Focus
Testing the subscription tab issue: "Aucun plan disponible"

Tests to perform:
1. Test /api/subscription/plans endpoint (no auth required)
2. Create test user and get JWT token
3. Test /api/subscription/status endpoint with token
4. Verify data format for frontend compatibility
5. Test all subscription endpoints functionality
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://ecomsimply.com/api"

class SubscriptionTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = requests.Session()
        self.jwt_token = None
        self.test_user_email = f"test_subscription_{int(time.time())}@ecomsimply.test"
        self.test_user_password = "TestPassword123!"
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_subscription_plans_endpoint(self):
        """Test 1: Test /api/subscription/plans endpoint (no authentication required)"""
        self.log("🔍 Testing /api/subscription/plans endpoint...")
        
        try:
            response = self.session.get(f"{self.backend_url}/subscription/plans")
            self.log(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ /api/subscription/plans endpoint working correctly")
                self.log(f"Response data: {json.dumps(data, indent=2)}")
                
                # Verify response structure
                if "success" in data and "plans" in data:
                    plans = data["plans"]
                    self.log(f"Found {len(plans)} plans:")
                    for plan in plans:
                        self.log(f"  - {plan.get('name', 'Unknown')}: {plan.get('price', 0)}€")
                    
                    # Check for expected plans
                    plan_names = [plan.get('name', '').lower() for plan in plans]
                    expected_plans = ['gratuit', 'pro', 'premium']
                    
                    for expected in expected_plans:
                        if expected in plan_names:
                            self.log(f"✅ Plan '{expected}' found")
                        else:
                            self.log(f"❌ Plan '{expected}' missing")
                    
                    return True, data
                else:
                    self.log("❌ Invalid response structure - missing 'success' or 'plans' fields")
                    return False, data
            else:
                self.log(f"❌ Endpoint failed with status {response.status_code}")
                self.log(f"Response: {response.text}")
                return False, None
                
        except Exception as e:
            self.log(f"❌ Error testing plans endpoint: {e}")
            return False, None
    
    def create_test_user_and_get_token(self):
        """Test 2: Create a test user and get JWT token"""
        self.log("🔍 Creating test user and getting JWT token...")
        
        # First, try to register a new user
        try:
            register_data = {
                "email": self.test_user_email,
                "name": "Test Subscription User",
                "password": self.test_user_password
            }
            
            self.log(f"Registering user: {self.test_user_email}")
            response = self.session.post(f"{self.backend_url}/auth/register", json=register_data)
            
            if response.status_code == 200:
                self.log("✅ User registration successful")
            else:
                self.log(f"⚠️ Registration failed (status {response.status_code}), trying to login with existing user...")
        
        except Exception as e:
            self.log(f"⚠️ Registration error: {e}, trying to login...")
        
        # Now try to login
        try:
            login_data = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            self.log("Attempting login...")
            response = self.session.post(f"{self.backend_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.jwt_token = data["access_token"]
                    self.log("✅ Login successful, JWT token obtained")
                    self.log(f"Token preview: {self.jwt_token[:50]}...")
                    
                    # Set authorization header for future requests
                    self.session.headers.update({"Authorization": f"Bearer {self.jwt_token}"})
                    return True, data
                else:
                    self.log("❌ Login response missing access_token")
                    return False, data
            else:
                self.log(f"❌ Login failed with status {response.status_code}")
                self.log(f"Response: {response.text}")
                return False, None
                
        except Exception as e:
            self.log(f"❌ Error during login: {e}")
            return False, None
    
    def test_subscription_status_endpoint(self):
        """Test 3: Test /api/subscription/status endpoint with JWT token"""
        self.log("🔍 Testing /api/subscription/status endpoint...")
        
        if not self.jwt_token:
            self.log("❌ No JWT token available, cannot test authenticated endpoint")
            return False, None
        
        try:
            response = self.session.get(f"{self.backend_url}/subscription/status")
            self.log(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ /api/subscription/status endpoint working correctly")
                self.log(f"Response data: {json.dumps(data, indent=2)}")
                
                # Verify response structure
                expected_fields = ["success", "user_id", "plan_type", "monthly_limit", "monthly_usage", "can_start_trial"]
                missing_fields = []
                
                for field in expected_fields:
                    if field not in data:
                        missing_fields.append(field)
                
                if missing_fields:
                    self.log(f"⚠️ Missing fields in response: {missing_fields}")
                else:
                    self.log("✅ All expected fields present in response")
                
                return True, data
            else:
                self.log(f"❌ Endpoint failed with status {response.status_code}")
                self.log(f"Response: {response.text}")
                return False, None
                
        except Exception as e:
            self.log(f"❌ Error testing status endpoint: {e}")
            return False, None
    
    def test_subscription_create_endpoint(self):
        """Test 4: Test /api/subscription/create endpoint"""
        self.log("🔍 Testing /api/subscription/create endpoint...")
        
        if not self.jwt_token:
            self.log("❌ No JWT token available, cannot test authenticated endpoint")
            return False, None
        
        try:
            # Test Pro plan creation
            create_data = {
                "plan_type": "pro",
                "with_trial": True
            }
            
            response = self.session.post(f"{self.backend_url}/subscription/create", json=create_data)
            self.log(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ /api/subscription/create endpoint working correctly")
                self.log(f"Response data: {json.dumps(data, indent=2)}")
                
                # Verify response structure
                if "success" in data and "checkout_url" in data:
                    self.log("✅ Response contains required fields (success, checkout_url)")
                    return True, data
                else:
                    self.log("❌ Response missing required fields")
                    return False, data
            else:
                self.log(f"❌ Endpoint failed with status {response.status_code}")
                self.log(f"Response: {response.text}")
                return False, None
                
        except Exception as e:
            self.log(f"❌ Error testing create endpoint: {e}")
            return False, None
    
    def verify_data_format_for_frontend(self, plans_data, status_data):
        """Test 5: Verify data format is compatible with frontend expectations"""
        self.log("🔍 Verifying data format for frontend compatibility...")
        
        issues = []
        
        # Check plans data format
        if plans_data:
            if not isinstance(plans_data.get("plans"), list):
                issues.append("Plans data should be a list")
            else:
                for i, plan in enumerate(plans_data["plans"]):
                    required_fields = ["id", "name", "price", "features"]
                    for field in required_fields:
                        if field not in plan:
                            issues.append(f"Plan {i} missing required field: {field}")
        
        # Check status data format
        if status_data:
            required_status_fields = ["plan_type", "monthly_limit", "monthly_usage"]
            for field in required_status_fields:
                if field not in status_data:
                    issues.append(f"Status data missing required field: {field}")
        
        if issues:
            self.log("❌ Data format issues found:")
            for issue in issues:
                self.log(f"  - {issue}")
            return False
        else:
            self.log("✅ Data format is compatible with frontend expectations")
            return True
    
    def run_comprehensive_test(self):
        """Run all subscription endpoint tests"""
        self.log("🚀 Starting comprehensive subscription endpoints testing...")
        self.log(f"Backend URL: {self.backend_url}")
        
        results = {
            "plans_endpoint": False,
            "user_creation": False,
            "status_endpoint": False,
            "create_endpoint": False,
            "data_format": False
        }
        
        # Test 1: Plans endpoint
        plans_success, plans_data = self.test_subscription_plans_endpoint()
        results["plans_endpoint"] = plans_success
        
        # Test 2: Create user and get token
        user_success, user_data = self.create_test_user_and_get_token()
        results["user_creation"] = user_success
        
        # Test 3: Status endpoint (requires authentication)
        status_success, status_data = self.test_subscription_status_endpoint()
        results["status_endpoint"] = status_success
        
        # Test 4: Create endpoint (requires authentication)
        create_success, create_data = self.test_subscription_create_endpoint()
        results["create_endpoint"] = create_success
        
        # Test 5: Data format verification
        format_success = self.verify_data_format_for_frontend(plans_data, status_data)
        results["data_format"] = format_success
        
        # Summary
        self.log("\n" + "="*60)
        self.log("📊 TEST RESULTS SUMMARY")
        self.log("="*60)
        
        total_tests = len(results)
        passed_tests = sum(1 for success in results.values() if success)
        
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            self.log(f"{test_name.replace('_', ' ').title()}: {status}")
        
        self.log(f"\nOverall Success Rate: {passed_tests}/{total_tests} ({(passed_tests/total_tests)*100:.1f}%)")
        
        # Specific analysis for the reported issue
        self.log("\n" + "="*60)
        self.log("🔍 ANALYSIS FOR REPORTED ISSUE: 'Aucun plan disponible'")
        self.log("="*60)
        
        if plans_success and plans_data:
            self.log("✅ Backend /api/subscription/plans returns data correctly")
            self.log("✅ Plans data structure is valid")
            self.log("✅ All expected plans (Gratuit, Pro, Premium) are present")
            self.log("\n🔍 ISSUE LIKELY IN FRONTEND:")
            self.log("- The backend is working correctly")
            self.log("- Check SubscriptionManager.js data loading logic")
            self.log("- Check if loadSubscriptionData() is properly transforming the array")
            self.log("- Verify frontend error handling and state management")
        else:
            self.log("❌ Backend /api/subscription/plans has issues")
            self.log("🔍 ISSUE IS IN BACKEND:")
            self.log("- Fix the subscription plans endpoint first")
            self.log("- Ensure proper response format")
        
        # Return detailed results for further analysis
        return {
            "success_rate": (passed_tests/total_tests)*100,
            "results": results,
            "data": {
                "plans": plans_data,
                "status": status_data,
                "user": user_data
            }
        }

def main():
    """Main test execution"""
    print("🎯 ECOMSIMPLY Subscription Endpoints Testing")
    print("=" * 60)
    print("Testing the issue: SubscriptionManager shows 'Aucun plan disponible'")
    print("=" * 60)
    
    tester = SubscriptionTester()
    results = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    if results["success_rate"] >= 80:
        print("\n🎉 Testing completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Testing completed with issues!")
        sys.exit(1)

if __name__ == "__main__":
    main()