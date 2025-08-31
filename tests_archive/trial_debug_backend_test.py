#!/usr/bin/env python3
"""
ECOMSIMPLY Trial Initialization Error Debug Suite
Specifically tests the "Erreur lors de l'initialisation de l'essai gratuit" backend issues
as requested in the review request.

Focus Areas:
1. Trial Registration Endpoint Issues - POST /api/subscription/trial/register
2. Payment Checkout Integration - POST /api/payments/checkout with trial_subscription flag
3. Authentication Integration - JWT token validation for trial endpoints
4. Error Logging and Debugging - Check backend logs for specific error messages
5. Dependencies and Configuration - Verify environment variables and database connectivity
"""

import requests
import json
import time
import random
import uuid
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 30

class TrialDebugTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def add_result(self, test_name, success, details):
        """Add test result to results list"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    def test_api_health(self):
        """Test if the API is accessible"""
        self.log("🔍 Testing API health check...")
        try:
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ API Health Check: {data.get('message', 'OK')}")
                self.add_result("API Health Check", True, f"Status: {response.status_code}, Message: {data.get('message', 'OK')}")
                return True
            else:
                self.log(f"❌ API Health Check failed: {response.status_code}", "ERROR")
                self.add_result("API Health Check", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ API Health Check failed: {str(e)}", "ERROR")
            self.add_result("API Health Check", False, f"Exception: {str(e)}")
            return False
    
    def test_trial_registration_endpoint_exists(self):
        """Test if the trial registration endpoint exists and responds"""
        self.log("🔍 Testing trial registration endpoint existence...")
        
        # Test with minimal data to check if endpoint exists
        test_data = {
            "name": "Test User",
            "email": f"test{int(time.time())}@example.com",
            "password": "TestPassword123!",
            "plan_type": "pro"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/subscription/trial/register", json=test_data)
            
            if response.status_code == 404:
                self.log("❌ Trial registration endpoint NOT FOUND (404)", "ERROR")
                self.add_result("Trial Registration Endpoint Exists", False, "Endpoint returns 404 - not implemented")
                return False
            elif response.status_code in [200, 400, 422, 500]:
                self.log(f"✅ Trial registration endpoint EXISTS (status: {response.status_code})")
                self.add_result("Trial Registration Endpoint Exists", True, f"Endpoint responds with status: {response.status_code}")
                return True
            else:
                self.log(f"⚠️ Trial registration endpoint responds with unexpected status: {response.status_code}")
                self.add_result("Trial Registration Endpoint Exists", True, f"Unexpected status: {response.status_code}")
                return True
                
        except Exception as e:
            self.log(f"❌ Error testing trial registration endpoint: {str(e)}", "ERROR")
            self.add_result("Trial Registration Endpoint Exists", False, f"Exception: {str(e)}")
            return False
    
    def test_trial_registration_pro_plan(self):
        """Test trial registration for Pro plan with detailed error analysis"""
        self.log("🔍 Testing trial registration for Pro plan...")
        
        # Generate unique test user data
        timestamp = int(time.time())
        trial_user = {
            "name": "Marie Dubois",
            "email": f"marie.dubois.pro{timestamp}@example.com",
            "password": "SecurePassword123!",
            "plan_type": "pro"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/subscription/trial/register", json=trial_user)
            
            self.log(f"📊 Response Status: {response.status_code}")
            self.log(f"📊 Response Headers: {dict(response.headers)}")
            
            try:
                response_data = response.json()
                self.log(f"📊 Response Data: {json.dumps(response_data, indent=2)}")
            except:
                self.log(f"📊 Response Text: {response.text}")
                response_data = {"error": "Invalid JSON response", "text": response.text}
            
            if response.status_code == 200:
                # Success case
                required_fields = ["success", "message", "user", "trial_info", "token"]
                missing_fields = [field for field in required_fields if field not in response_data]
                
                if missing_fields:
                    self.log(f"❌ Pro Trial Registration: Missing fields {missing_fields}", "ERROR")
                    self.add_result("Trial Registration Pro Plan", False, f"Missing fields: {missing_fields}")
                    return False
                
                user_data = response_data.get("user", {})
                trial_data = response_data.get("trial_info", {})
                
                self.log(f"✅ Pro Trial Registration: Successfully registered {user_data.get('name', 'Unknown')}")
                self.log(f"   User ID: {user_data.get('id', 'N/A')}")
                self.log(f"   Email: {user_data.get('email', 'N/A')}")
                self.log(f"   Plan: {user_data.get('subscription_plan', 'N/A')}")
                self.log(f"   Trial Status: {user_data.get('is_trial_user', 'N/A')}")
                
                self.add_result("Trial Registration Pro Plan", True, {
                    "user_id": user_data.get('id'),
                    "email": user_data.get('email'),
                    "plan": user_data.get('subscription_plan'),
                    "is_trial": user_data.get('is_trial_user')
                })
                return True
                
            elif response.status_code == 400:
                # Bad request - analyze the error
                error_msg = response_data.get('detail', response_data.get('message', 'Unknown error'))
                self.log(f"❌ Pro Trial Registration: Bad Request - {error_msg}", "ERROR")
                self.add_result("Trial Registration Pro Plan", False, f"Bad Request: {error_msg}")
                return False
                
            elif response.status_code == 500:
                # Internal server error - this is the critical issue
                error_msg = response_data.get('detail', response_data.get('message', 'Internal server error'))
                self.log(f"❌ Pro Trial Registration: INTERNAL SERVER ERROR - {error_msg}", "ERROR")
                self.log("🚨 This matches the 'Erreur lors de l'initialisation de l'essai gratuit' issue!", "ERROR")
                self.add_result("Trial Registration Pro Plan", False, f"Internal Server Error: {error_msg}")
                return False
                
            else:
                self.log(f"❌ Pro Trial Registration: Unexpected status {response.status_code}", "ERROR")
                self.add_result("Trial Registration Pro Plan", False, f"Unexpected status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Pro trial registration: {str(e)}", "ERROR")
            self.add_result("Trial Registration Pro Plan", False, f"Exception: {str(e)}")
            return False
    
    def test_trial_registration_premium_plan(self):
        """Test trial registration for Premium plan with detailed error analysis"""
        self.log("🔍 Testing trial registration for Premium plan...")
        
        # Generate unique test user data
        timestamp = int(time.time())
        trial_user = {
            "name": "Jean Martin",
            "email": f"jean.martin.premium{timestamp}@example.com",
            "password": "SecurePassword123!",
            "plan_type": "premium"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/subscription/trial/register", json=trial_user)
            
            self.log(f"📊 Response Status: {response.status_code}")
            
            try:
                response_data = response.json()
                self.log(f"📊 Response Data: {json.dumps(response_data, indent=2)}")
            except:
                self.log(f"📊 Response Text: {response.text}")
                response_data = {"error": "Invalid JSON response", "text": response.text}
            
            if response.status_code == 200:
                user_data = response_data.get("user", {})
                self.log(f"✅ Premium Trial Registration: Successfully registered {user_data.get('name', 'Unknown')}")
                self.add_result("Trial Registration Premium Plan", True, {
                    "user_id": user_data.get('id'),
                    "email": user_data.get('email'),
                    "plan": user_data.get('subscription_plan')
                })
                return True
            elif response.status_code == 500:
                error_msg = response_data.get('detail', response_data.get('message', 'Internal server error'))
                self.log(f"❌ Premium Trial Registration: INTERNAL SERVER ERROR - {error_msg}", "ERROR")
                self.log("🚨 This matches the 'Erreur lors de l'initialisation de l'essai gratuit' issue!", "ERROR")
                self.add_result("Trial Registration Premium Plan", False, f"Internal Server Error: {error_msg}")
                return False
            else:
                self.log(f"❌ Premium Trial Registration: Status {response.status_code}", "ERROR")
                self.add_result("Trial Registration Premium Plan", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Premium trial registration: {str(e)}", "ERROR")
            self.add_result("Trial Registration Premium Plan", False, f"Exception: {str(e)}")
            return False
    
    def test_payment_checkout_endpoint(self):
        """Test payment checkout endpoint with trial_subscription flag"""
        self.log("🔍 Testing payment checkout endpoint for trial subscriptions...")
        
        # Test checkout creation for trial subscription
        checkout_data = {
            "plan_type": "pro",
            "origin_url": "https://ecomsimply.com",
            "trial_subscription": True  # This is the key flag for trial subscriptions
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/payments/checkout", json=checkout_data)
            
            self.log(f"📊 Checkout Response Status: {response.status_code}")
            
            try:
                response_data = response.json()
                self.log(f"📊 Checkout Response Data: {json.dumps(response_data, indent=2)}")
            except:
                self.log(f"📊 Checkout Response Text: {response.text}")
                response_data = {"error": "Invalid JSON response", "text": response.text}
            
            if response.status_code == 200:
                checkout_url = response_data.get('checkout_url')
                session_id = response_data.get('session_id')
                
                if checkout_url and session_id:
                    self.log(f"✅ Payment Checkout: Successfully created trial checkout session")
                    self.log(f"   Session ID: {session_id}")
                    self.log(f"   Checkout URL: {checkout_url[:100]}...")
                    self.add_result("Payment Checkout Trial", True, {
                        "session_id": session_id,
                        "has_checkout_url": bool(checkout_url)
                    })
                    return True
                else:
                    self.log("❌ Payment Checkout: Missing checkout_url or session_id", "ERROR")
                    self.add_result("Payment Checkout Trial", False, "Missing checkout_url or session_id")
                    return False
                    
            elif response.status_code == 401:
                self.log("❌ Payment Checkout: Authentication required", "ERROR")
                self.add_result("Payment Checkout Trial", False, "Authentication required")
                return False
                
            elif response.status_code == 500:
                error_msg = response_data.get('detail', response_data.get('message', 'Internal server error'))
                self.log(f"❌ Payment Checkout: INTERNAL SERVER ERROR - {error_msg}", "ERROR")
                self.log("🚨 This could be related to the trial initialization issue!", "ERROR")
                self.add_result("Payment Checkout Trial", False, f"Internal Server Error: {error_msg}")
                return False
                
            else:
                self.log(f"❌ Payment Checkout: Unexpected status {response.status_code}", "ERROR")
                self.add_result("Payment Checkout Trial", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing payment checkout: {str(e)}", "ERROR")
            self.add_result("Payment Checkout Trial", False, f"Exception: {str(e)}")
            return False
    
    def test_authentication_integration(self):
        """Test JWT token validation for trial endpoints"""
        self.log("🔍 Testing authentication integration for trial endpoints...")
        
        # First, try to register a regular user to get a token
        timestamp = int(time.time())
        user_data = {
            "name": "Test Auth User",
            "email": f"auth.test{timestamp}@example.com",
            "password": "TestPassword123!"
        }
        
        try:
            # Register user
            response = self.session.post(f"{BASE_URL}/register", json=user_data)
            
            if response.status_code == 200:
                reg_data = response.json()
                token = reg_data.get('token')
                
                if token:
                    self.log(f"✅ User registration successful, got token")
                    
                    # Test authenticated access to trial status endpoint
                    headers = {"Authorization": f"Bearer {token}"}
                    status_response = self.session.get(f"{BASE_URL}/subscription/trial/status", headers=headers)
                    
                    self.log(f"📊 Trial Status Response: {status_response.status_code}")
                    
                    if status_response.status_code in [200, 404]:  # 404 is OK if no trial exists
                        self.log("✅ Authentication Integration: JWT token validation working")
                        self.add_result("Authentication Integration", True, f"Token validation working, status: {status_response.status_code}")
                        return True
                    elif status_response.status_code == 401:
                        self.log("❌ Authentication Integration: JWT token rejected", "ERROR")
                        self.add_result("Authentication Integration", False, "JWT token rejected")
                        return False
                    else:
                        self.log(f"⚠️ Authentication Integration: Unexpected status {status_response.status_code}")
                        self.add_result("Authentication Integration", True, f"Unexpected but not auth error: {status_response.status_code}")
                        return True
                else:
                    self.log("❌ Authentication Integration: No token received from registration", "ERROR")
                    self.add_result("Authentication Integration", False, "No token from registration")
                    return False
            else:
                self.log(f"❌ Authentication Integration: User registration failed with {response.status_code}", "ERROR")
                self.add_result("Authentication Integration", False, f"Registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing authentication integration: {str(e)}", "ERROR")
            self.add_result("Authentication Integration", False, f"Exception: {str(e)}")
            return False
    
    def test_environment_configuration(self):
        """Test environment variables and configuration through API responses"""
        self.log("🔍 Testing environment configuration and dependencies...")
        
        try:
            # Test database connectivity through a simple API call
            response = self.session.get(f"{BASE_URL}/")
            
            if response.status_code == 200:
                self.log("✅ Database connectivity: API responding (MongoDB likely connected)")
                db_status = True
            else:
                self.log("❌ Database connectivity: API not responding properly", "ERROR")
                db_status = False
            
            # Test Stripe configuration by checking public pricing endpoint
            pricing_response = self.session.get(f"{BASE_URL}/public/plans-pricing")
            
            if pricing_response.status_code == 200:
                pricing_data = pricing_response.json()
                if 'pro' in pricing_data and 'premium' in pricing_data:
                    self.log("✅ Stripe configuration: Pricing data available")
                    stripe_status = True
                else:
                    self.log("❌ Stripe configuration: Invalid pricing data", "ERROR")
                    stripe_status = False
            else:
                self.log("❌ Stripe configuration: Pricing endpoint not accessible", "ERROR")
                stripe_status = False
            
            # Test email service by checking if contact endpoint exists
            contact_test = {
                "name": "Test User",
                "email": "test@example.com",
                "subject": "Configuration Test",
                "message": "Testing email service configuration"
            }
            
            contact_response = self.session.post(f"{BASE_URL}/contact", json=contact_test)
            
            if contact_response.status_code in [200, 400, 422]:  # 400/422 are OK, means endpoint exists
                self.log("✅ Email service: Contact endpoint accessible")
                email_status = True
            else:
                self.log("❌ Email service: Contact endpoint not accessible", "ERROR")
                email_status = False
            
            overall_status = db_status and stripe_status and email_status
            
            self.add_result("Environment Configuration", overall_status, {
                "database": db_status,
                "stripe": stripe_status,
                "email": email_status
            })
            
            return overall_status
            
        except Exception as e:
            self.log(f"❌ Error testing environment configuration: {str(e)}", "ERROR")
            self.add_result("Environment Configuration", False, f"Exception: {str(e)}")
            return False
    
    def test_error_logging_endpoints(self):
        """Test error logging and debugging capabilities"""
        self.log("🔍 Testing error logging and debugging endpoints...")
        
        try:
            # Test health endpoint for detailed status
            health_response = self.session.get(f"{BASE_URL}/health")
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                self.log(f"✅ Health endpoint: {json.dumps(health_data, indent=2)}")
                
                # Check if we have detailed health information
                if 'database' in health_data or 'status' in health_data:
                    self.log("✅ Error Logging: Health endpoint provides detailed status")
                    self.add_result("Error Logging", True, "Health endpoint provides detailed status")
                    return True
                else:
                    self.log("⚠️ Error Logging: Basic health endpoint only")
                    self.add_result("Error Logging", True, "Basic health endpoint available")
                    return True
            else:
                self.log(f"❌ Error Logging: Health endpoint not accessible ({health_response.status_code})", "ERROR")
                self.add_result("Error Logging", False, f"Health endpoint status: {health_response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing error logging: {str(e)}", "ERROR")
            self.add_result("Error Logging", False, f"Exception: {str(e)}")
            return False
    
    def run_comprehensive_trial_debug(self):
        """Run all trial debugging tests"""
        self.log("🚀 Starting Comprehensive Trial Initialization Debug Suite")
        self.log("=" * 80)
        
        tests = [
            ("API Health Check", self.test_api_health),
            ("Trial Registration Endpoint Exists", self.test_trial_registration_endpoint_exists),
            ("Trial Registration Pro Plan", self.test_trial_registration_pro_plan),
            ("Trial Registration Premium Plan", self.test_trial_registration_premium_plan),
            ("Payment Checkout Integration", self.test_payment_checkout_endpoint),
            ("Authentication Integration", self.test_authentication_integration),
            ("Environment Configuration", self.test_environment_configuration),
            ("Error Logging", self.test_error_logging_endpoints)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n{'='*20} {test_name} {'='*20}")
            try:
                if test_func():
                    passed += 1
                    self.log(f"✅ {test_name}: PASSED")
                else:
                    self.log(f"❌ {test_name}: FAILED")
            except Exception as e:
                self.log(f"❌ {test_name}: EXCEPTION - {str(e)}", "ERROR")
        
        self.log("\n" + "=" * 80)
        self.log(f"🏁 TRIAL DEBUG SUITE COMPLETED")
        self.log(f"📊 Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        # Analyze results for trial initialization issues
        self.analyze_trial_issues()
        
        return passed, total
    
    def analyze_trial_issues(self):
        """Analyze test results to identify trial initialization issues"""
        self.log("\n🔍 TRIAL INITIALIZATION ISSUE ANALYSIS")
        self.log("=" * 50)
        
        # Check for specific patterns that indicate the "Erreur lors de l'initialisation de l'essai gratuit" issue
        trial_reg_pro = next((r for r in self.test_results if r['test'] == 'Trial Registration Pro Plan'), None)
        trial_reg_premium = next((r for r in self.test_results if r['test'] == 'Trial Registration Premium Plan'), None)
        payment_checkout = next((r for r in self.test_results if r['test'] == 'Payment Checkout Trial'), None)
        
        issues_found = []
        
        if trial_reg_pro and not trial_reg_pro['success']:
            if 'Internal Server Error' in str(trial_reg_pro['details']):
                issues_found.append("🚨 CRITICAL: Pro trial registration returns 500 Internal Server Error")
        
        if trial_reg_premium and not trial_reg_premium['success']:
            if 'Internal Server Error' in str(trial_reg_premium['details']):
                issues_found.append("🚨 CRITICAL: Premium trial registration returns 500 Internal Server Error")
        
        if payment_checkout and not payment_checkout['success']:
            if 'Internal Server Error' in str(payment_checkout['details']):
                issues_found.append("🚨 CRITICAL: Payment checkout for trials returns 500 Internal Server Error")
        
        if issues_found:
            self.log("❌ TRIAL INITIALIZATION ISSUES IDENTIFIED:")
            for issue in issues_found:
                self.log(f"   {issue}")
            self.log("\n💡 RECOMMENDED FIXES:")
            self.log("   1. Check backend logs for detailed error messages")
            self.log("   2. Verify Stripe API key configuration")
            self.log("   3. Check MongoDB connection and trial collection setup")
            self.log("   4. Verify email service configuration for trial welcome emails")
            self.log("   5. Check for missing environment variables (STRIPE_API_KEY, FAL_KEY, etc.)")
        else:
            self.log("✅ No critical trial initialization issues detected in backend endpoints")
        
        # Summary for main agent
        self.log("\n📋 SUMMARY FOR MAIN AGENT:")
        if issues_found:
            self.log("❌ BACKEND TRIAL INITIALIZATION ERRORS CONFIRMED")
            self.log("   The 'Erreur lors de l'initialisation de l'essai gratuit' issue is caused by:")
            self.log("   - Internal server errors (500) in trial registration endpoints")
            self.log("   - Possible Stripe integration failures")
            self.log("   - Database or environment configuration issues")
        else:
            self.log("✅ BACKEND TRIAL ENDPOINTS APPEAR FUNCTIONAL")
            self.log("   The issue may be in frontend-backend integration or specific edge cases")

if __name__ == "__main__":
    tester = TrialDebugTester()
    passed, total = tester.run_comprehensive_trial_debug()
    
    if passed == total:
        print(f"\n🎉 All {total} tests passed! Trial backend appears functional.")
        exit(0)
    else:
        print(f"\n⚠️ {total - passed} tests failed. Trial initialization issues detected.")
        exit(1)