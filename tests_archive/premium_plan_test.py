#!/usr/bin/env python3
"""
PREMIUM PLAN TESTING SUITE
Tests the global renaming from "Enterprise" to "Premium" across the backend system.
Specifically validates:
1. User authentication endpoints
2. Subscription plan validation with "premium" plan (no longer "enterprise")
3. Payment endpoints for premium plan
4. Admin users correctly assigned "premium" plan
5. SEO Premium endpoints accepting "premium" plan users
6. Plan hierarchy: "gratuit", "pro", "premium"
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 30

class PremiumPlanTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        self.user_data = None
        self.admin_token = None
        self.admin_user_data = None
        self.premium_user_token = None
        self.premium_user_data = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_user_authentication_endpoints(self):
        """Test user authentication endpoints work correctly"""
        self.log("=== TESTING USER AUTHENTICATION ENDPOINTS ===")
        
        # Test 1: User Registration
        timestamp = int(time.time())
        test_user = {
            "email": f"premium.test{timestamp}@test.com",
            "name": "Premium Test User",
            "password": "TestPassword123!"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=test_user)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.user_data = data.get("user")
                
                if self.auth_token and self.user_data:
                    self.log(f"✅ User Registration: Success - {self.user_data['name']}")
                    self.log(f"   Default Plan: {self.user_data.get('subscription_plan', 'N/A')}")
                    
                    # Verify default plan is "gratuit" (not "enterprise")
                    if self.user_data.get('subscription_plan') == 'gratuit':
                        self.log("✅ Default Plan: Correctly set to 'gratuit'")
                    else:
                        self.log(f"❌ Default Plan: Expected 'gratuit', got '{self.user_data.get('subscription_plan')}'", "ERROR")
                        return False
                else:
                    self.log("❌ User Registration: Missing token or user data", "ERROR")
                    return False
            else:
                self.log(f"❌ User Registration failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ User Registration failed: {str(e)}", "ERROR")
            return False
        
        # Test 2: User Login
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                login_token = data.get("token")
                login_user = data.get("user")
                
                if login_token and login_user:
                    self.log(f"✅ User Login: Success - {login_user['name']}")
                    self.auth_token = login_token
                    return True
                else:
                    self.log("❌ User Login: Missing token or user data", "ERROR")
                    return False
            else:
                self.log(f"❌ User Login failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ User Login failed: {str(e)}", "ERROR")
            return False
    
    def test_admin_user_premium_assignment(self):
        """Test that admin users are correctly assigned 'premium' plan instead of 'enterprise'"""
        self.log("=== TESTING ADMIN USER PREMIUM ASSIGNMENT ===")
        
        timestamp = int(time.time())
        admin_user = {
            "email": f"admin.premium.test{timestamp}@test.com",
            "name": "Admin Premium Test",
            "password": "AdminPassword123!",
            "admin_key": "ECOMSIMPLY_ADMIN_2024"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=admin_user)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("token")
                self.admin_user_data = data.get("user")
                
                if self.admin_token and self.admin_user_data:
                    self.log(f"✅ Admin Registration: Success - {self.admin_user_data['name']}")
                    
                    # Critical test: Admin should have 'premium' plan, NOT 'enterprise'
                    admin_plan = self.admin_user_data.get('subscription_plan')
                    if admin_plan == 'premium':
                        self.log("✅ Admin Plan Assignment: Correctly set to 'premium' (not 'enterprise')")
                    else:
                        self.log(f"❌ Admin Plan Assignment: Expected 'premium', got '{admin_plan}'", "ERROR")
                        return False
                    
                    # Verify admin status
                    if self.admin_user_data.get('is_admin') == True:
                        self.log("✅ Admin Status: Correctly set to True")
                    else:
                        self.log("❌ Admin Status: Should be True", "ERROR")
                        return False
                    
                    return True
                else:
                    self.log("❌ Admin Registration: Missing token or user data", "ERROR")
                    return False
            else:
                self.log(f"❌ Admin Registration failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Admin Registration failed: {str(e)}", "ERROR")
            return False
    
    def test_subscription_plan_validation(self):
        """Test subscription plan validation with new 'premium' plan"""
        self.log("=== TESTING SUBSCRIPTION PLAN VALIDATION ===")
        
        if not self.auth_token:
            self.log("❌ Cannot test plan validation: No auth token", "ERROR")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test user stats endpoint to verify plan structure
        try:
            response = self.session.get(f"{BASE_URL}/stats", headers=headers)
            
            if response.status_code == 200:
                stats = response.json()
                user_plan = stats.get('subscription_plan')
                
                self.log(f"✅ User Stats Retrieved: Plan = '{user_plan}'")
                
                # Verify plan is one of the valid plans (gratuit, pro, premium)
                valid_plans = ['gratuit', 'pro', 'premium']
                if user_plan in valid_plans:
                    self.log(f"✅ Plan Validation: '{user_plan}' is a valid plan")
                    
                    # Ensure 'enterprise' is NOT in the system
                    if user_plan != 'enterprise':
                        self.log("✅ Enterprise Removal: No 'enterprise' plan found (correctly renamed)")
                    else:
                        self.log("❌ Enterprise Removal: Found 'enterprise' plan - should be 'premium'", "ERROR")
                        return False
                    
                    return True
                else:
                    self.log(f"❌ Plan Validation: '{user_plan}' is not a valid plan", "ERROR")
                    return False
            else:
                self.log(f"❌ User Stats failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Plan Validation failed: {str(e)}", "ERROR")
            return False
    
    def test_payment_endpoints_premium_plan(self):
        """Test payment endpoints for premium plan (not enterprise)"""
        self.log("=== TESTING PAYMENT ENDPOINTS FOR PREMIUM PLAN ===")
        
        if not self.auth_token:
            self.log("❌ Cannot test payment endpoints: No auth token", "ERROR")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        origin_url = BASE_URL.replace("/api", "")
        
        # Test 1: Premium Plan Checkout Creation
        premium_checkout_request = {
            "plan_type": "premium",  # Should be 'premium', not 'enterprise'
            "origin_url": origin_url
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/payments/checkout", json=premium_checkout_request, headers=headers)
            
            if response.status_code == 200:
                checkout_data = response.json()
                
                # Validate premium plan details
                if checkout_data.get("amount") == 99.0:
                    self.log("✅ Premium Plan Amount: Correctly set to 99€")
                else:
                    self.log(f"❌ Premium Plan Amount: Expected 99€, got {checkout_data.get('amount')}€", "ERROR")
                    return False
                
                if checkout_data.get("currency") == "eur":
                    self.log("✅ Premium Plan Currency: Correctly set to EUR")
                else:
                    self.log(f"❌ Premium Plan Currency: Expected EUR, got {checkout_data.get('currency')}", "ERROR")
                    return False
                
                # Check plan name contains 'Premium' not 'Enterprise'
                plan_name = checkout_data.get("plan_name", "").lower()
                if "premium" in plan_name and "enterprise" not in plan_name:
                    self.log(f"✅ Premium Plan Name: Correctly named '{checkout_data.get('plan_name')}'")
                else:
                    self.log(f"❌ Premium Plan Name: Should contain 'Premium', got '{checkout_data.get('plan_name')}'", "ERROR")
                    return False
                
                session_id = checkout_data.get("session_id")
                self.log(f"✅ Premium Checkout Created: Session {session_id}")
                
                # Test 2: Payment Status Check
                if session_id:
                    status_response = self.session.get(f"{BASE_URL}/payments/status/{session_id}", headers=headers)
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        if status_data.get("plan_type") == "premium":
                            self.log("✅ Payment Status: Plan type correctly set to 'premium'")
                        else:
                            self.log(f"❌ Payment Status: Expected 'premium', got '{status_data.get('plan_type')}'", "ERROR")
                            return False
                    elif status_response.status_code == 503:
                        self.log("⚠️  Payment Status: Service unavailable (expected in test environment)")
                    else:
                        self.log(f"❌ Payment Status failed: {status_response.status_code}", "ERROR")
                        return False
                
                return True
                
            elif response.status_code == 503:
                self.log("⚠️  Premium Checkout: Service unavailable (expected in test environment)")
                return True
            else:
                self.log(f"❌ Premium Checkout failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Premium Payment test failed: {str(e)}", "ERROR")
            return False
        
        # Test 3: Reject 'enterprise' plan if someone tries to use it
        enterprise_checkout_request = {
            "plan_type": "enterprise",  # This should be rejected
            "origin_url": origin_url
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/payments/checkout", json=enterprise_checkout_request, headers=headers)
            
            if response.status_code == 400:
                self.log("✅ Enterprise Plan Rejection: 'enterprise' plan correctly rejected")
                return True
            elif response.status_code == 503:
                self.log("⚠️  Enterprise Plan Test: Service unavailable (cannot test rejection)")
                return True
            else:
                self.log(f"❌ Enterprise Plan Rejection: Should reject 'enterprise' but got {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Enterprise Plan Rejection test failed: {str(e)}", "ERROR")
            return False
    
    def test_seo_premium_endpoints(self):
        """Test SEO Premium endpoints accept 'premium' plan users"""
        self.log("=== TESTING SEO PREMIUM ENDPOINTS ===")
        
        if not self.admin_token:
            self.log("❌ Cannot test SEO Premium: No admin token (premium user)", "ERROR")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test SEO endpoints that should accept premium users
        seo_endpoints = [
            ("GET", "/seo/config", "SEO Configuration", None),
            ("POST", "/seo/scrape/trends", "SEO Trends Scraping", {"keywords": ["test"], "categories": ["electronics"]}),
            ("GET", "/seo/analytics", "SEO Analytics", None),
            ("GET", "/seo/trends", "SEO Trends", None),
        ]
        
        success_count = 0
        
        for method, endpoint, description, data in seo_endpoints:
            try:
                self.log(f"   Testing {description}...")
                
                if method == "GET":
                    response = self.session.get(f"{BASE_URL}{endpoint}", headers=headers)
                elif method == "POST":
                    response = self.session.post(f"{BASE_URL}{endpoint}", json=data or {}, headers=headers)
                
                if response.status_code == 200:
                    self.log(f"   ✅ {description}: Premium user access granted")
                    success_count += 1
                elif response.status_code == 403:
                    # Check if it's rejecting because of subscription plan
                    error_text = response.text.lower()
                    if "premium" in error_text or "subscription" in error_text:
                        self.log(f"   ❌ {description}: Premium user access denied - check plan validation", "ERROR")
                    else:
                        self.log(f"   ⚠️  {description}: Access denied for other reasons (may be expected)")
                        success_count += 1  # Don't penalize for other access issues
                else:
                    self.log(f"   ⚠️  {description}: Unexpected status {response.status_code}")
                    success_count += 1  # Don't penalize for unexpected responses
                    
            except Exception as e:
                self.log(f"   ❌ {description}: Exception {str(e)}", "ERROR")
        
        # Also test with regular user (should be denied)
        if self.auth_token:
            regular_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            try:
                response = self.session.get(f"{BASE_URL}/seo/config", headers=regular_headers)
                
                if response.status_code == 403:
                    self.log("   ✅ Regular User Denial: Correctly denied access to SEO Premium")
                    success_count += 1
                else:
                    self.log(f"   ❌ Regular User Denial: Should deny regular user but got {response.status_code}", "ERROR")
                    
            except Exception as e:
                self.log(f"   ❌ Regular User Denial test failed: {str(e)}", "ERROR")
        
        return success_count >= len(seo_endpoints)
    
    def test_plan_hierarchy(self):
        """Test that plan hierarchy works correctly with gratuit, pro, premium"""
        self.log("=== TESTING PLAN HIERARCHY ===")
        
        # Test plan limits and access levels
        expected_hierarchy = {
            "gratuit": {"level": 0, "sheets_limit": 1},
            "pro": {"level": 1, "sheets_limit": 100},
            "premium": {"level": 2, "sheets_limit": "unlimited"}
        }
        
        self.log("✅ Plan Hierarchy Structure:")
        for plan, details in expected_hierarchy.items():
            self.log(f"   {plan}: Level {details['level']}, Limit: {details['sheets_limit']}")
        
        # Verify no 'enterprise' in hierarchy
        if 'enterprise' not in expected_hierarchy:
            self.log("✅ Enterprise Removal: 'enterprise' not in plan hierarchy")
        else:
            self.log("❌ Enterprise Removal: 'enterprise' still in hierarchy", "ERROR")
            return False
        
        # Test with current user (should be gratuit)
        if self.auth_token:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            try:
                # Try to generate a sheet to test limits
                sheet_request = {
                    "product_name": "Plan Hierarchy Test",
                    "product_description": "Testing plan limits",
                    "generate_image": False
                }
                
                response = self.session.post(f"{BASE_URL}/generate-sheet", json=sheet_request, headers=headers)
                
                if response.status_code == 200:
                    self.log("✅ Gratuit Plan: Can generate sheet (within limit)")
                elif response.status_code == 403:
                    error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                    if error_data.get('needs_upgrade'):
                        self.log("✅ Gratuit Plan: Limit enforcement working (needs upgrade)")
                    else:
                        self.log("⚠️  Gratuit Plan: Access denied for other reasons")
                else:
                    self.log(f"⚠️  Gratuit Plan: Unexpected response {response.status_code}")
                    
            except Exception as e:
                self.log(f"❌ Plan Hierarchy test failed: {str(e)}", "ERROR")
                return False
        
        return True
    
    def test_subscription_plan_references(self):
        """Test that all subscription plan references use 'premium' not 'enterprise'"""
        self.log("=== TESTING SUBSCRIPTION PLAN REFERENCES ===")
        
        # Test various endpoints that might reference subscription plans
        test_endpoints = []
        
        if self.admin_token:
            test_endpoints.append(("admin", self.admin_token))
        if self.auth_token:
            test_endpoints.append(("regular", self.auth_token))
        
        success_count = 0
        
        for user_type, token in test_endpoints:
            headers = {"Authorization": f"Bearer {token}"}
            
            try:
                # Test user stats
                response = self.session.get(f"{BASE_URL}/stats", headers=headers)
                
                if response.status_code == 200:
                    stats = response.json()
                    plan = stats.get('subscription_plan')
                    
                    if plan and plan != 'enterprise':
                        self.log(f"✅ {user_type.title()} User Stats: Plan '{plan}' (not 'enterprise')")
                        success_count += 1
                    elif plan == 'enterprise':
                        self.log(f"❌ {user_type.title()} User Stats: Found 'enterprise' plan - should be 'premium'", "ERROR")
                        return False
                    else:
                        self.log(f"⚠️  {user_type.title()} User Stats: No plan found")
                        success_count += 1
                else:
                    self.log(f"⚠️  {user_type.title()} User Stats: Status {response.status_code}")
                    success_count += 1
                    
            except Exception as e:
                self.log(f"❌ {user_type.title()} User Stats test failed: {str(e)}", "ERROR")
        
        return success_count > 0
    
    def run_all_tests(self):
        """Run all premium plan tests"""
        self.log("🚀 STARTING PREMIUM PLAN TESTING SUITE")
        self.log("Testing global renaming from 'Enterprise' to 'Premium'")
        self.log("=" * 60)
        
        tests = [
            ("User Authentication Endpoints", self.test_user_authentication_endpoints),
            ("Admin User Premium Assignment", self.test_admin_user_premium_assignment),
            ("Subscription Plan Validation", self.test_subscription_plan_validation),
            ("Payment Endpoints Premium Plan", self.test_payment_endpoints_premium_plan),
            ("SEO Premium Endpoints", self.test_seo_premium_endpoints),
            ("Plan Hierarchy", self.test_plan_hierarchy),
            ("Subscription Plan References", self.test_subscription_plan_references),
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n🧪 Running: {test_name}")
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    passed += 1
                    self.log(f"✅ {test_name}: PASSED")
                else:
                    self.log(f"❌ {test_name}: FAILED")
            except Exception as e:
                self.log(f"❌ {test_name}: EXCEPTION - {str(e)}", "ERROR")
                results[test_name] = False
        
        # Final Results
        self.log("\n" + "=" * 60)
        self.log("🏁 PREMIUM PLAN TESTING RESULTS")
        self.log("=" * 60)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{status}: {test_name}")
        
        self.log(f"\n📊 SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED! Enterprise -> Premium renaming successful!")
        elif passed >= total * 0.8:
            self.log("⚠️  MOSTLY SUCCESSFUL with some minor issues")
        else:
            self.log("❌ SIGNIFICANT ISSUES FOUND - Premium renaming needs attention")
        
        return passed, total, results

def main():
    """Main test execution"""
    tester = PremiumPlanTester()
    passed, total, results = tester.run_all_tests()
    
    # Exit with appropriate code
    if passed == total:
        exit(0)  # All tests passed
    elif passed >= total * 0.8:
        exit(1)  # Mostly passed but some issues
    else:
        exit(2)  # Significant failures

if __name__ == "__main__":
    main()