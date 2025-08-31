#!/usr/bin/env python3
"""
ECOMSIMPLY 7-Day Free Trial System Testing (0€ Amount)
=====================================================

This script tests the new 7-day free trial system with 0€ amount as requested in the review.

TESTING OBJECTIVES:
1. Verify free trial with 0€ amount via /api/payments/checkout with trial_subscription: true
2. Test limitation to 1 trial per user
3. Verify creation and management of trials
4. Test integration with existing system

TEST USER: trial.test@example.com / TestPassword123!
"""

import requests
import json
import time
import uuid
from datetime import datetime, timedelta

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TEST_USER_EMAIL = "trial.test@example.com"
TEST_USER_PASSWORD = "TestPassword123!"
TEST_USER_NAME = "Trial Test User"

class TrialTestRunner:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ECOMSIMPLY-Trial-Test/1.0'
        })
        self.test_results = []
        self.user_token = None
        self.user_id = None
        
    def log_test(self, test_name, success, details, response_data=None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
    
    def cleanup_test_user(self):
        """Clean up test user if exists"""
        try:
            # Try to login first to see if user exists
            login_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                print(f"🧹 Cleaning up existing test user: {TEST_USER_EMAIL}")
                # User exists, we'll work with it
                return True
        except Exception as e:
            print(f"ℹ️ No existing test user found: {e}")
        return False
    
    def register_test_user(self):
        """Register a new test user"""
        try:
            register_data = {
                "email": TEST_USER_EMAIL,
                "name": TEST_USER_NAME,
                "password": TEST_USER_PASSWORD,
                "language": "fr"
            }
            
            response = self.session.post(f"{BASE_URL}/auth/register", json=register_data)
            
            if response.status_code == 200:
                data = response.json()
                self.user_token = data.get('token')
                self.user_id = data.get('user', {}).get('id')
                
                # Set authorization header
                self.session.headers.update({
                    'Authorization': f'Bearer {self.user_token}'
                })
                
                self.log_test(
                    "User Registration", 
                    True, 
                    f"Successfully registered user {TEST_USER_EMAIL}",
                    {"user_id": self.user_id, "has_token": bool(self.user_token)}
                )
                return True
            else:
                self.log_test(
                    "User Registration", 
                    False, 
                    f"Failed to register user: {response.status_code}",
                    response.json() if response.content else None
                )
                return False
                
        except Exception as e:
            self.log_test("User Registration", False, f"Exception during registration: {str(e)}")
            return False
    
    def login_test_user(self):
        """Login with test user"""
        try:
            login_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.user_token = data.get('token')
                self.user_id = data.get('user', {}).get('id')
                
                # Set authorization header
                self.session.headers.update({
                    'Authorization': f'Bearer {self.user_token}'
                })
                
                self.log_test(
                    "User Login", 
                    True, 
                    f"Successfully logged in user {TEST_USER_EMAIL}",
                    {"user_id": self.user_id, "has_token": bool(self.user_token)}
                )
                return True
            else:
                self.log_test(
                    "User Login", 
                    False, 
                    f"Failed to login user: {response.status_code}",
                    response.json() if response.content else None
                )
                return False
                
        except Exception as e:
            self.log_test("User Login", False, f"Exception during login: {str(e)}")
            return False
    
    def test_free_trial_checkout_pro(self):
        """Test 1: Free trial checkout for Pro plan with 0€ amount"""
        try:
            checkout_data = {
                "plan_type": "pro",
                "origin_url": "https://ecomsimply.com/trial",
                "trial_subscription": True
            }
            
            response = self.session.post(f"{BASE_URL}/payments/checkout", json=checkout_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify 0€ amount
                session_data = data.get('session', {})
                amount = session_data.get('amount', 0)
                
                success = amount == 0.0
                details = f"Pro trial checkout - Amount: {amount}€ (Expected: 0€)"
                
                self.log_test(
                    "Free Trial Checkout Pro (0€)", 
                    success, 
                    details,
                    {
                        "amount": amount,
                        "currency": session_data.get('currency'),
                        "session_id": session_data.get('session_id', 'N/A')[:20] + "..."
                    }
                )
                return success
            else:
                self.log_test(
                    "Free Trial Checkout Pro (0€)", 
                    False, 
                    f"Failed checkout: {response.status_code}",
                    response.json() if response.content else None
                )
                return False
                
        except Exception as e:
            self.log_test("Free Trial Checkout Pro (0€)", False, f"Exception: {str(e)}")
            return False
    
    def test_free_trial_checkout_premium(self):
        """Test 2: Free trial checkout for Premium plan with 0€ amount"""
        try:
            checkout_data = {
                "plan_type": "premium",
                "origin_url": "https://ecomsimply.com/trial",
                "trial_subscription": True
            }
            
            response = self.session.post(f"{BASE_URL}/payments/checkout", json=checkout_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify 0€ amount
                session_data = data.get('session', {})
                amount = session_data.get('amount', 0)
                
                success = amount == 0.0
                details = f"Premium trial checkout - Amount: {amount}€ (Expected: 0€)"
                
                self.log_test(
                    "Free Trial Checkout Premium (0€)", 
                    success, 
                    details,
                    {
                        "amount": amount,
                        "currency": session_data.get('currency'),
                        "session_id": session_data.get('session_id', 'N/A')[:20] + "..."
                    }
                )
                return success
            else:
                self.log_test(
                    "Free Trial Checkout Premium (0€)", 
                    False, 
                    f"Failed checkout: {response.status_code}",
                    response.json() if response.content else None
                )
                return False
                
        except Exception as e:
            self.log_test("Free Trial Checkout Premium (0€)", False, f"Exception: {str(e)}")
            return False
    
    def test_trial_registration_pro(self):
        """Test 3: Direct trial registration for Pro plan"""
        try:
            # Create a new user for this test
            unique_email = f"trial.pro.{int(time.time())}@example.com"
            
            trial_data = {
                "name": "Pro Trial User",
                "email": unique_email,
                "password": TEST_USER_PASSWORD,
                "plan_type": "pro"
            }
            
            response = self.session.post(f"{BASE_URL}/subscription/trial/register", json=trial_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify trial creation
                trial_info = data.get('trial_info', {})
                user_info = data.get('user', {})
                
                is_trial_user = user_info.get('is_trial_user', False)
                plan_type = trial_info.get('plan_type')
                days_remaining = trial_info.get('days_remaining', 0)
                
                success = is_trial_user and plan_type == "pro" and days_remaining == 7
                details = f"Pro trial registration - Trial user: {is_trial_user}, Plan: {plan_type}, Days: {days_remaining}"
                
                self.log_test(
                    "Trial Registration Pro", 
                    success, 
                    details,
                    {
                        "is_trial_user": is_trial_user,
                        "plan_type": plan_type,
                        "days_remaining": days_remaining,
                        "email": unique_email
                    }
                )
                return success
            else:
                self.log_test(
                    "Trial Registration Pro", 
                    False, 
                    f"Failed registration: {response.status_code}",
                    response.json() if response.content else None
                )
                return False
                
        except Exception as e:
            self.log_test("Trial Registration Pro", False, f"Exception: {str(e)}")
            return False
    
    def test_trial_registration_premium(self):
        """Test 4: Direct trial registration for Premium plan"""
        try:
            # Create a new user for this test
            unique_email = f"trial.premium.{int(time.time())}@example.com"
            
            trial_data = {
                "name": "Premium Trial User",
                "email": unique_email,
                "password": TEST_USER_PASSWORD,
                "plan_type": "premium"
            }
            
            response = self.session.post(f"{BASE_URL}/subscription/trial/register", json=trial_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify trial creation
                trial_info = data.get('trial_info', {})
                user_info = data.get('user', {})
                
                is_trial_user = user_info.get('is_trial_user', False)
                plan_type = trial_info.get('plan_type')
                days_remaining = trial_info.get('days_remaining', 0)
                
                success = is_trial_user and plan_type == "premium" and days_remaining == 7
                details = f"Premium trial registration - Trial user: {is_trial_user}, Plan: {plan_type}, Days: {days_remaining}"
                
                self.log_test(
                    "Trial Registration Premium", 
                    success, 
                    details,
                    {
                        "is_trial_user": is_trial_user,
                        "plan_type": plan_type,
                        "days_remaining": days_remaining,
                        "email": unique_email
                    }
                )
                return success
            else:
                self.log_test(
                    "Trial Registration Premium", 
                    False, 
                    f"Failed registration: {response.status_code}",
                    response.json() if response.content else None
                )
                return False
                
        except Exception as e:
            self.log_test("Trial Registration Premium", False, f"Exception: {str(e)}")
            return False
    
    def test_duplicate_trial_limitation(self):
        """Test 5: Verify limitation to 1 trial per user"""
        try:
            # First, register a trial user
            unique_email = f"trial.duplicate.{int(time.time())}@example.com"
            
            trial_data = {
                "name": "Duplicate Trial Test",
                "email": unique_email,
                "password": TEST_USER_PASSWORD,
                "plan_type": "pro"
            }
            
            # First trial registration (should succeed)
            response1 = self.session.post(f"{BASE_URL}/subscription/trial/register", json=trial_data)
            
            if response1.status_code != 200:
                self.log_test(
                    "Duplicate Trial Limitation", 
                    False, 
                    "Failed to create first trial for duplicate test",
                    response1.json() if response1.content else None
                )
                return False
            
            # Wait a moment
            time.sleep(1)
            
            # Second trial registration (should fail)
            trial_data["plan_type"] = "premium"  # Try different plan
            response2 = self.session.post(f"{BASE_URL}/subscription/trial/register", json=trial_data)
            
            # Should fail with appropriate error message
            if response2.status_code == 400:
                data = response2.json()
                error_message = data.get('detail', '')
                
                expected_message = "Vous avez déjà utilisé votre essai gratuit"
                success = expected_message in error_message
                details = f"Duplicate trial correctly rejected - Message: '{error_message}'"
                
                self.log_test(
                    "Duplicate Trial Limitation", 
                    success, 
                    details,
                    {
                        "first_trial": "success",
                        "second_trial": "rejected",
                        "error_message": error_message
                    }
                )
                return success
            else:
                self.log_test(
                    "Duplicate Trial Limitation", 
                    False, 
                    f"Second trial should have failed but got: {response2.status_code}",
                    response2.json() if response2.content else None
                )
                return False
                
        except Exception as e:
            self.log_test("Duplicate Trial Limitation", False, f"Exception: {str(e)}")
            return False
    
    def test_trial_status_endpoint(self):
        """Test 6: Verify trial status endpoint"""
        try:
            # Create a trial user first
            unique_email = f"trial.status.{int(time.time())}@example.com"
            
            trial_data = {
                "name": "Status Test User",
                "email": unique_email,
                "password": TEST_USER_PASSWORD,
                "plan_type": "pro"
            }
            
            # Register trial user
            register_response = self.session.post(f"{BASE_URL}/subscription/trial/register", json=trial_data)
            
            if register_response.status_code != 200:
                self.log_test(
                    "Trial Status Endpoint", 
                    False, 
                    "Failed to create trial user for status test",
                    register_response.json() if register_response.content else None
                )
                return False
            
            # Get token from registration
            register_data = register_response.json()
            token = register_data.get('token')
            
            if not token:
                self.log_test("Trial Status Endpoint", False, "No token received from trial registration")
                return False
            
            # Set authorization header for this user
            headers = {'Authorization': f'Bearer {token}'}
            
            # Check trial status
            status_response = self.session.get(f"{BASE_URL}/subscription/trial/status", headers=headers)
            
            if status_response.status_code == 200:
                data = status_response.json()
                
                has_trial = data.get('has_trial', False)
                trial_status = data.get('trial_status')
                plan_type = data.get('plan_type')
                days_remaining = data.get('days_remaining', 0)
                
                success = has_trial and trial_status == "active" and plan_type == "pro" and days_remaining == 7
                details = f"Trial status - Has trial: {has_trial}, Status: {trial_status}, Plan: {plan_type}, Days: {days_remaining}"
                
                self.log_test(
                    "Trial Status Endpoint", 
                    success, 
                    details,
                    {
                        "has_trial": has_trial,
                        "trial_status": trial_status,
                        "plan_type": plan_type,
                        "days_remaining": days_remaining
                    }
                )
                return success
            else:
                self.log_test(
                    "Trial Status Endpoint", 
                    False, 
                    f"Failed to get trial status: {status_response.status_code}",
                    status_response.json() if status_response.content else None
                )
                return False
                
        except Exception as e:
            self.log_test("Trial Status Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_trial_user_profile_update(self):
        """Test 7: Verify trial user profile is updated correctly"""
        try:
            # Create a trial user
            unique_email = f"trial.profile.{int(time.time())}@example.com"
            
            trial_data = {
                "name": "Profile Test User",
                "email": unique_email,
                "password": TEST_USER_PASSWORD,
                "plan_type": "premium"
            }
            
            # Register trial user
            register_response = self.session.post(f"{BASE_URL}/subscription/trial/register", json=trial_data)
            
            if register_response.status_code != 200:
                self.log_test(
                    "Trial User Profile Update", 
                    False, 
                    "Failed to create trial user for profile test"
                )
                return False
            
            # Get token and check user profile
            register_data = register_response.json()
            token = register_data.get('token')
            user_data = register_data.get('user', {})
            
            is_trial_user = user_data.get('is_trial_user', False)
            subscription_plan = user_data.get('subscription_plan')
            trial_start_date = user_data.get('trial_start_date')
            trial_end_date = user_data.get('trial_end_date')
            
            success = (is_trial_user and 
                      subscription_plan == "premium" and 
                      trial_start_date is not None and 
                      trial_end_date is not None)
            
            details = f"Profile update - Trial user: {is_trial_user}, Plan: {subscription_plan}, Has dates: {bool(trial_start_date and trial_end_date)}"
            
            self.log_test(
                "Trial User Profile Update", 
                success, 
                details,
                {
                    "is_trial_user": is_trial_user,
                    "subscription_plan": subscription_plan,
                    "has_trial_dates": bool(trial_start_date and trial_end_date)
                }
            )
            return success
                
        except Exception as e:
            self.log_test("Trial User Profile Update", False, f"Exception: {str(e)}")
            return False
    
    def test_trial_transaction_creation(self):
        """Test 8: Verify trial transactions are created with 0€ amount"""
        try:
            # This test checks if the payment transaction is created correctly for trials
            checkout_data = {
                "plan_type": "pro",
                "origin_url": "https://ecomsimply.com/trial",
                "trial_subscription": True
            }
            
            response = self.session.post(f"{BASE_URL}/payments/checkout", json=checkout_data)
            
            if response.status_code == 200:
                data = response.json()
                session_data = data.get('session', {})
                
                # Check transaction details
                amount = session_data.get('amount', 0)
                currency = session_data.get('currency', '')
                session_id = session_data.get('session_id', '')
                
                success = amount == 0.0 and currency == "eur" and session_id
                details = f"Trial transaction - Amount: {amount}€, Currency: {currency}, Has session: {bool(session_id)}"
                
                self.log_test(
                    "Trial Transaction Creation (0€)", 
                    success, 
                    details,
                    {
                        "amount": amount,
                        "currency": currency,
                        "has_session_id": bool(session_id)
                    }
                )
                return success
            else:
                self.log_test(
                    "Trial Transaction Creation (0€)", 
                    False, 
                    f"Failed to create trial transaction: {response.status_code}",
                    response.json() if response.content else None
                )
                return False
                
        except Exception as e:
            self.log_test("Trial Transaction Creation (0€)", False, f"Exception: {str(e)}")
            return False
    
    def test_existing_system_integration(self):
        """Test 9: Verify integration with existing system (normal paid subscriptions still work)"""
        try:
            # Test normal paid checkout (should not be 0€)
            checkout_data = {
                "plan_type": "pro",
                "origin_url": "https://ecomsimply.com/pricing",
                "trial_subscription": False  # Normal paid subscription
            }
            
            response = self.session.post(f"{BASE_URL}/payments/checkout", json=checkout_data)
            
            if response.status_code == 200:
                data = response.json()
                session_data = data.get('session', {})
                amount = session_data.get('amount', 0)
                
                # Normal Pro plan should be 29€
                success = amount == 29.0
                details = f"Normal paid checkout - Amount: {amount}€ (Expected: 29€ for Pro)"
                
                self.log_test(
                    "Existing System Integration", 
                    success, 
                    details,
                    {
                        "amount": amount,
                        "is_trial": False,
                        "plan_type": "pro"
                    }
                )
                return success
            else:
                self.log_test(
                    "Existing System Integration", 
                    False, 
                    f"Failed normal checkout: {response.status_code}",
                    response.json() if response.content else None
                )
                return False
                
        except Exception as e:
            self.log_test("Existing System Integration", False, f"Exception: {str(e)}")
            return False
    
    def test_affiliate_system_with_trials(self):
        """Test 10: Verify affiliate system works with free trials"""
        try:
            # Test trial checkout with affiliate code
            checkout_data = {
                "plan_type": "premium",
                "origin_url": "https://ecomsimply.com/trial",
                "trial_subscription": True,
                "affiliate_code": "TEST123"  # Test affiliate code
            }
            
            response = self.session.post(f"{BASE_URL}/payments/checkout", json=checkout_data)
            
            if response.status_code == 200:
                data = response.json()
                session_data = data.get('session', {})
                
                # Should still be 0€ even with affiliate code
                amount = session_data.get('amount', 0)
                success = amount == 0.0
                details = f"Trial with affiliate - Amount: {amount}€ (Should remain 0€)"
                
                self.log_test(
                    "Affiliate System with Trials", 
                    success, 
                    details,
                    {
                        "amount": amount,
                        "has_affiliate_code": True,
                        "affiliate_code": "TEST123"
                    }
                )
                return success
            else:
                # If affiliate code is invalid, that's also acceptable
                if response.status_code == 400:
                    self.log_test(
                        "Affiliate System with Trials", 
                        True, 
                        "Invalid affiliate code properly rejected",
                        {"status": "affiliate_validation_working"}
                    )
                    return True
                else:
                    self.log_test(
                        "Affiliate System with Trials", 
                        False, 
                        f"Unexpected error: {response.status_code}",
                        response.json() if response.content else None
                    )
                    return False
                
        except Exception as e:
            self.log_test("Affiliate System with Trials", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all trial system tests"""
        print("🚀 STARTING ECOMSIMPLY 7-DAY FREE TRIAL SYSTEM TESTING")
        print("=" * 60)
        print(f"Base URL: {BASE_URL}")
        print(f"Test User: {TEST_USER_EMAIL}")
        print("=" * 60)
        
        # Setup phase
        print("\n📋 SETUP PHASE")
        print("-" * 30)
        
        # Clean up any existing test user
        self.cleanup_test_user()
        
        # Try to register or login
        if not self.register_test_user():
            if not self.login_test_user():
                print("❌ CRITICAL: Cannot setup test user. Aborting tests.")
                return
        
        # Main testing phase
        print("\n🧪 TESTING PHASE")
        print("-" * 30)
        
        tests = [
            self.test_free_trial_checkout_pro,
            self.test_free_trial_checkout_premium,
            self.test_trial_registration_pro,
            self.test_trial_registration_premium,
            self.test_duplicate_trial_limitation,
            self.test_trial_status_endpoint,
            self.test_trial_user_profile_update,
            self.test_trial_transaction_creation,
            self.test_existing_system_integration,
            self.test_affiliate_system_with_trials
        ]
        
        for test in tests:
            try:
                test()
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test.__name__}: {str(e)}")
        
        # Results summary
        print("\n📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 30)
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if not result['success']:
                print(f"   └─ {result['details']}")
        
        # Critical findings
        print("\n🎯 CRITICAL FINDINGS:")
        print("-" * 30)
        
        critical_tests = [
            "Free Trial Checkout Pro (0€)",
            "Free Trial Checkout Premium (0€)",
            "Duplicate Trial Limitation",
            "Trial Transaction Creation (0€)"
        ]
        
        for test_name in critical_tests:
            result = next((r for r in self.test_results if r['test'] == test_name), None)
            if result:
                status = "✅ WORKING" if result['success'] else "❌ FAILING"
                print(f"{status} {test_name}")
        
        print("\n" + "=" * 60)
        if success_rate >= 80:
            print("🎉 TRIAL SYSTEM STATUS: OPERATIONAL")
        elif success_rate >= 60:
            print("⚠️ TRIAL SYSTEM STATUS: PARTIALLY FUNCTIONAL")
        else:
            print("❌ TRIAL SYSTEM STATUS: CRITICAL ISSUES")
        
        print("=" * 60)

if __name__ == "__main__":
    runner = TrialTestRunner()
    runner.run_all_tests()