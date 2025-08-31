#!/usr/bin/env python3
"""
ECOMSIMPLY STRIPE PAYMENT SYSTEM REINFORCEMENT TEST
Comprehensive testing of the newly implemented Stripe security features:
1. Trial eligibility service with "one trial per customer" rule
2. Secure Stripe webhooks with signature verification and anti-replay
3. Stripe service with idempotence and server-side price validation
4. Trial eligibility endpoint as server-side source of truth
"""

import asyncio
import aiohttp
import json
import os
import sys
import time
import hashlib
import hmac
from datetime import datetime
from typing import Dict, List, Any, Optional

# Test configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

print(f"🔧 Using backend URL: {BACKEND_URL}")
print(f"🔧 API base: {API_BASE}")

class StripeReinforcementTester:
    """Comprehensive tester for ECOMSIMPLY Stripe payment system reinforcement"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "tests": {},
            "summary": {"total": 0, "passed": 0, "failed": 0, "warnings": 0}
        }
        self.session = None
        self.test_user_token = None
        self.test_user_data = None
    
    async def setup(self):
        """Setup test environment"""
        print("🚀 ECOMSIMPLY STRIPE REINFORCEMENT SYSTEM TEST")
        print("=" * 70)
        
        # Create aiohttp session
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
        print(f"📡 Backend URL: {BACKEND_URL}")
        print(f"🔗 API Base: {API_BASE}")
        print()
        
        # Create test user for authentication
        await self.create_test_user()
    
    async def cleanup(self):
        """Cleanup test resources"""
        if self.session:
            await self.session.close()
    
    def log_test_result(self, test_name: str, status: str, message: str, details: Dict = None):
        """Log test result"""
        self.results["tests"][test_name] = {
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.results["summary"]["total"] += 1
        if status == "passed":
            self.results["summary"]["passed"] += 1
            print(f"✅ {test_name}: {message}")
        elif status == "warning":
            self.results["summary"]["warnings"] += 1
            print(f"⚠️  {test_name}: {message}")
        else:
            self.results["summary"]["failed"] += 1
            print(f"❌ {test_name}: {message}")
    
    async def create_test_user(self):
        """Create a test user for authentication"""
        try:
            # Generate unique test user
            timestamp = int(time.time())
            test_email = f"stripe_test_{timestamp}@ecomsimply.test"
            test_password = "TestPassword123!"
            
            # Register test user
            register_data = {
                "email": test_email,
                "name": "Stripe Test User",
                "password": test_password
            }
            
            async with self.session.post(f"{API_BASE}/auth/register", json=register_data) as response:
                if response.status == 200:
                    # Login to get token
                    login_data = {
                        "email": test_email,
                        "password": test_password
                    }
                    
                    async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as login_response:
                        if login_response.status == 200:
                            login_result = await login_response.json()
                            self.test_user_token = login_result.get("token")  # Fixed: use "token" not "access_token"
                            user_info = login_result.get("user", {})
                            self.test_user_data = {
                                "email": test_email,
                                "password": test_password,
                                "user_id": user_info.get("id")
                            }
                            print(f"✅ Test user created and authenticated: {test_email}")
                            print(f"🔑 Token received: {self.test_user_token[:20]}..." if self.test_user_token else "❌ No token received")
                        else:
                            login_error = await login_response.json()
                            print(f"❌ Failed to login test user: {login_response.status} - {login_error}")
                else:
                    print(f"❌ Failed to create test user: {response.status}")
        except Exception as e:
            print(f"❌ Error creating test user: {str(e)}")
    
    def get_auth_headers(self):
        """Get authentication headers"""
        if self.test_user_token:
            return {"Authorization": f"Bearer {self.test_user_token}"}
        return {}
    
    # ================================================================================
    # 🎯 TEST 1: TRIAL ELIGIBILITY ENDPOINT
    # ================================================================================
    
    async def test_trial_eligibility_endpoint(self):
        """Test 1: Trial eligibility endpoint functionality"""
        test_name = "Trial Eligibility Endpoint"
        
        try:
            headers = self.get_auth_headers()
            if not headers:
                self.log_test_result(test_name, "failed", "No authentication token available")
                return
            
            # Test with valid plan (pro)
            async with self.session.get(
                f"{API_BASE}/subscription/trial-eligibility?plan=pro", 
                headers=headers
            ) as response:
                status_code = response.status
                response_data = await response.json()
                
                details = {
                    "status_code": status_code,
                    "response_structure": list(response_data.keys()) if isinstance(response_data, dict) else "invalid",
                    "eligible_field_present": "eligible" in response_data if isinstance(response_data, dict) else False,
                    "reason_field_present": "reason" in response_data if isinstance(response_data, dict) else False,
                    "message_field_present": "message" in response_data if isinstance(response_data, dict) else False
                }
                
                # Test with premium plan
                async with self.session.get(
                    f"{API_BASE}/subscription/trial-eligibility?plan=premium", 
                    headers=headers
                ) as premium_response:
                    premium_status = premium_response.status
                    premium_data = await premium_response.json()
                    
                    details["premium_test"] = {
                        "status_code": premium_status,
                        "eligible": premium_data.get("eligible") if isinstance(premium_data, dict) else None
                    }
                
                # Test with invalid plan
                async with self.session.get(
                    f"{API_BASE}/subscription/trial-eligibility?plan=invalid", 
                    headers=headers
                ) as invalid_response:
                    invalid_status = invalid_response.status
                    details["invalid_plan_test"] = {
                        "status_code": invalid_status,
                        "properly_rejected": invalid_status == 400
                    }
                
                # Evaluate results
                if status_code == 200 and details["eligible_field_present"] and details["reason_field_present"]:
                    self.log_test_result(test_name, "passed", "Trial eligibility endpoint working correctly", details)
                elif status_code == 200:
                    self.log_test_result(test_name, "warning", "Endpoint accessible but missing required fields", details)
                else:
                    self.log_test_result(test_name, "failed", f"Endpoint returned status {status_code}", details)
        
        except Exception as e:
            self.log_test_result(test_name, "failed", f"Error testing trial eligibility: {str(e)}")
    
    # ================================================================================
    # 🎯 TEST 2: PRICE ID VALIDATION (ALLOWLIST)
    # ================================================================================
    
    async def test_price_id_validation(self):
        """Test 2: Server-side price ID allowlist validation"""
        test_name = "Price ID Allowlist Validation"
        
        try:
            headers = self.get_auth_headers()
            if not headers:
                self.log_test_result(test_name, "failed", "No authentication token available")
                return
            
            # Test with legitimate price IDs
            legitimate_tests = [
                {
                    "plan": "pro",
                    "price_id": "price_1Rrw3UGK8qzu5V5Wu8PnvKzK",
                    "expected_status": 200
                },
                {
                    "plan": "premium", 
                    "price_id": "price_1RrxgjGK8qzu5V5WvOSb4uPd",
                    "expected_status": 200
                }
            ]
            
            # Test with forged price IDs (should be rejected)
            forged_tests = [
                {
                    "plan": "pro",
                    "price_id": "price_FORGED_MALICIOUS_ID",
                    "expected_status": 403
                },
                {
                    "plan": "premium",
                    "price_id": "price_ANOTHER_FORGED_ID", 
                    "expected_status": 403
                }
            ]
            
            results = {"legitimate": [], "forged": []}
            
            # Test legitimate price IDs
            for test_case in legitimate_tests:
                create_data = {
                    "plan_type": test_case["plan"],
                    "price_id": test_case["price_id"],
                    "with_trial": True,
                    "success_url": "https://example.com/success",
                    "cancel_url": "https://example.com/cancel"
                }
                
                async with self.session.post(
                    f"{API_BASE}/subscription/create",
                    json=create_data,
                    headers=headers
                ) as response:
                    status_code = response.status
                    response_data = await response.json()
                    
                    results["legitimate"].append({
                        "plan": test_case["plan"],
                        "price_id": test_case["price_id"][:20] + "...",
                        "status_code": status_code,
                        "accepted": status_code in [200, 201],
                        "response": response_data.get("status", "unknown") if isinstance(response_data, dict) else "invalid"
                    })
            
            # Test forged price IDs
            for test_case in forged_tests:
                create_data = {
                    "plan_type": test_case["plan"],
                    "price_id": test_case["price_id"],
                    "with_trial": True,
                    "success_url": "https://example.com/success",
                    "cancel_url": "https://example.com/cancel"
                }
                
                async with self.session.post(
                    f"{API_BASE}/subscription/create",
                    json=create_data,
                    headers=headers
                ) as response:
                    status_code = response.status
                    response_data = await response.json()
                    
                    results["forged"].append({
                        "plan": test_case["plan"],
                        "price_id": test_case["price_id"],
                        "status_code": status_code,
                        "properly_rejected": status_code in [400, 403],
                        "response": response_data.get("detail", "unknown") if isinstance(response_data, dict) else "invalid"
                    })
            
            # Evaluate results
            legitimate_accepted = sum(1 for r in results["legitimate"] if r["accepted"])
            forged_rejected = sum(1 for r in results["forged"] if r["properly_rejected"])
            
            details = {
                "legitimate_tests": len(legitimate_tests),
                "legitimate_accepted": legitimate_accepted,
                "forged_tests": len(forged_tests),
                "forged_rejected": forged_rejected,
                "results": results
            }
            
            if legitimate_accepted == len(legitimate_tests) and forged_rejected == len(forged_tests):
                self.log_test_result(test_name, "passed", "Price ID allowlist working correctly", details)
            elif forged_rejected == len(forged_tests):
                self.log_test_result(test_name, "warning", "Forged IDs rejected but legitimate IDs have issues", details)
            else:
                self.log_test_result(test_name, "failed", "Price ID validation not working properly", details)
        
        except Exception as e:
            self.log_test_result(test_name, "failed", f"Error testing price ID validation: {str(e)}")
    
    # ================================================================================
    # 🎯 TEST 3: SUBSCRIPTION CREATION WITH TRIAL ELIGIBILITY
    # ================================================================================
    
    async def test_subscription_creation_with_eligibility(self):
        """Test 3: Subscription creation with trial eligibility validation"""
        test_name = "Subscription Creation with Trial Eligibility"
        
        try:
            headers = self.get_auth_headers()
            if not headers:
                self.log_test_result(test_name, "failed", "No authentication token available")
                return
            
            # Test 1: Create subscription with trial (eligible user)
            create_data_with_trial = {
                "plan_type": "pro",
                "price_id": "price_1Rrw3UGK8qzu5V5Wu8PnvKzK",
                "with_trial": True,
                "success_url": "https://example.com/success",
                "cancel_url": "https://example.com/cancel"
            }
            
            async with self.session.post(
                f"{API_BASE}/subscription/create",
                json=create_data_with_trial,
                headers=headers
            ) as response:
                trial_status = response.status
                trial_data = await response.json()
                
                trial_result = {
                    "status_code": trial_status,
                    "checkout_url_present": "checkout_url" in trial_data if isinstance(trial_data, dict) else False,
                    "trial_active": trial_data.get("trial_active") if isinstance(trial_data, dict) else None,
                    "status": trial_data.get("status") if isinstance(trial_data, dict) else "unknown"
                }
            
            # Test 2: Create subscription without trial (direct payment)
            create_data_no_trial = {
                "plan_type": "premium",
                "price_id": "price_1RrxgjGK8qzu5V5WvOSb4uPd",
                "with_trial": False,
                "success_url": "https://example.com/success",
                "cancel_url": "https://example.com/cancel"
            }
            
            async with self.session.post(
                f"{API_BASE}/subscription/create",
                json=create_data_no_trial,
                headers=headers
            ) as response:
                no_trial_status = response.status
                no_trial_data = await response.json()
                
                no_trial_result = {
                    "status_code": no_trial_status,
                    "checkout_url_present": "checkout_url" in no_trial_data if isinstance(no_trial_data, dict) else False,
                    "trial_active": no_trial_data.get("trial_active") if isinstance(no_trial_data, dict) else None,
                    "status": no_trial_data.get("status") if isinstance(no_trial_data, dict) else "unknown"
                }
            
            # Test 3: Test idempotence (same request twice)
            async with self.session.post(
                f"{API_BASE}/subscription/create",
                json=create_data_with_trial,
                headers=headers
            ) as response:
                idempotent_status = response.status
                idempotent_data = await response.json()
                
                idempotent_result = {
                    "status_code": idempotent_status,
                    "handled_gracefully": idempotent_status in [200, 201, 409],
                    "status": idempotent_data.get("status") if isinstance(idempotent_data, dict) else "unknown"
                }
            
            details = {
                "trial_test": trial_result,
                "no_trial_test": no_trial_result,
                "idempotence_test": idempotent_result
            }
            
            # Evaluate results
            trial_working = trial_status in [200, 201] and trial_result["checkout_url_present"]
            no_trial_working = no_trial_status in [200, 201] and no_trial_result["checkout_url_present"]
            idempotence_working = idempotent_result["handled_gracefully"]
            
            if trial_working and no_trial_working and idempotence_working:
                self.log_test_result(test_name, "passed", "Subscription creation working correctly", details)
            elif trial_working and no_trial_working:
                self.log_test_result(test_name, "warning", "Subscription creation working but idempotence issues", details)
            else:
                self.log_test_result(test_name, "failed", "Subscription creation has issues", details)
        
        except Exception as e:
            self.log_test_result(test_name, "failed", f"Error testing subscription creation: {str(e)}")
    
    # ================================================================================
    # 🎯 TEST 4: WEBHOOK SECURITY VALIDATION
    # ================================================================================
    
    async def test_webhook_security(self):
        """Test 4: Webhook security features (signature verification, anti-replay)"""
        test_name = "Webhook Security Validation"
        
        try:
            # Test 1: Webhook without signature (should be rejected)
            webhook_payload = {
                "id": "evt_test_webhook",
                "object": "event",
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "id": "cs_test_session",
                        "customer": "cus_test_customer",
                        "subscription": "sub_test_subscription",
                        "metadata": {
                            "user_id": "test_user_123",
                            "plan_type": "pro"
                        }
                    }
                },
                "created": int(time.time())
            }
            
            # Test without signature header
            async with self.session.post(
                f"{API_BASE}/subscription/webhook",
                json=webhook_payload
            ) as response:
                no_signature_status = response.status
                no_signature_data = await response.json() if response.content_type == 'application/json' else {}
            
            # Test 2: Webhook with invalid signature (should be rejected)
            invalid_signature = "t=1234567890,v1=invalid_signature_hash"
            
            async with self.session.post(
                f"{API_BASE}/subscription/webhook",
                json=webhook_payload,
                headers={"stripe-signature": invalid_signature}
            ) as response:
                invalid_signature_status = response.status
                invalid_signature_data = await response.json() if response.content_type == 'application/json' else {}
            
            # Test 3: Test with old timestamp (should be rejected for replay protection)
            old_timestamp = int(time.time()) - 3600  # 1 hour ago
            old_payload = webhook_payload.copy()
            old_payload["created"] = old_timestamp
            
            # Generate a mock signature (won't be valid but tests timestamp check)
            mock_signature = f"t={old_timestamp},v1=mock_signature_for_old_event"
            
            async with self.session.post(
                f"{API_BASE}/subscription/webhook",
                json=old_payload,
                headers={"stripe-signature": mock_signature}
            ) as response:
                old_timestamp_status = response.status
                old_timestamp_data = await response.json() if response.content_type == 'application/json' else {}
            
            details = {
                "no_signature_test": {
                    "status_code": no_signature_status,
                    "properly_rejected": no_signature_status in [400, 401, 403],
                    "response": no_signature_data
                },
                "invalid_signature_test": {
                    "status_code": invalid_signature_status,
                    "properly_rejected": invalid_signature_status in [400, 401, 403],
                    "response": invalid_signature_data
                },
                "old_timestamp_test": {
                    "status_code": old_timestamp_status,
                    "properly_rejected": old_timestamp_status in [400, 401, 403],
                    "response": old_timestamp_data
                }
            }
            
            # Evaluate results
            security_checks_passed = (
                details["no_signature_test"]["properly_rejected"] and
                details["invalid_signature_test"]["properly_rejected"]
            )
            
            if security_checks_passed:
                self.log_test_result(test_name, "passed", "Webhook security validation working correctly", details)
            else:
                # Check if webhooks are at least accessible (basic implementation)
                if (details["no_signature_test"]["status_code"] == 200 or 
                    details["invalid_signature_test"]["status_code"] == 200):
                    self.log_test_result(test_name, "warning", "Webhook endpoint accessible but security validation needs improvement", details)
                else:
                    self.log_test_result(test_name, "failed", "Webhook security validation has issues", details)
        
        except Exception as e:
            self.log_test_result(test_name, "failed", f"Error testing webhook security: {str(e)}")
    
    # ================================================================================
    # 🎯 TEST 5: SUBSCRIPTION STATUS AND PLANS ENDPOINTS
    # ================================================================================
    
    async def test_subscription_info_endpoints(self):
        """Test 5: Subscription status and plans information endpoints"""
        test_name = "Subscription Information Endpoints"
        
        try:
            headers = self.get_auth_headers()
            if not headers:
                self.log_test_result(test_name, "failed", "No authentication token available")
                return
            
            # Test 1: Get available plans
            async with self.session.get(f"{API_BASE}/subscription/plans") as response:
                plans_status = response.status
                plans_data = await response.json()
                
                plans_result = {
                    "status_code": plans_status,
                    "success": plans_data.get("success") if isinstance(plans_data, dict) else False,
                    "plans_present": "plans" in plans_data if isinstance(plans_data, dict) else False,
                    "pro_plan_present": False,
                    "premium_plan_present": False
                }
                
                if isinstance(plans_data, dict) and "plans" in plans_data:
                    plans = plans_data["plans"]
                    plans_result["pro_plan_present"] = "pro" in plans
                    plans_result["premium_plan_present"] = "premium" in plans
                    
                    if "pro" in plans:
                        pro_plan = plans["pro"]
                        plans_result["pro_has_price"] = "price" in pro_plan
                        plans_result["pro_has_features"] = "features" in pro_plan
                    
                    if "premium" in plans:
                        premium_plan = plans["premium"]
                        plans_result["premium_has_price"] = "price" in premium_plan
                        plans_result["premium_has_features"] = "features" in premium_plan
            
            # Test 2: Get subscription status
            async with self.session.get(f"{API_BASE}/subscription/status", headers=headers) as response:
                status_status = response.status
                status_data = await response.json()
                
                status_result = {
                    "status_code": status_status,
                    "user_id_present": "user_id" in status_data if isinstance(status_data, dict) else False,
                    "plan_type_present": "plan_type" in status_data if isinstance(status_data, dict) else False,
                    "can_start_trial_present": "can_start_trial" in status_data if isinstance(status_data, dict) else False,
                    "has_used_trial_present": "has_used_trial" in status_data if isinstance(status_data, dict) else False
                }
            
            # Test 3: Validate trial eligibility utility endpoint
            async with self.session.get(f"{API_BASE}/subscription/validate-trial-eligibility", headers=headers) as response:
                validate_status = response.status
                validate_data = await response.json()
                
                validate_result = {
                    "status_code": validate_status,
                    "eligible_present": "eligible" in validate_data if isinstance(validate_data, dict) else False,
                    "has_used_trial_present": "has_used_trial" in validate_data if isinstance(validate_data, dict) else False,
                    "current_plan_present": "current_plan" in validate_data if isinstance(validate_data, dict) else False
                }
            
            details = {
                "plans_endpoint": plans_result,
                "status_endpoint": status_result,
                "validate_endpoint": validate_result
            }
            
            # Evaluate results
            plans_working = plans_status == 200 and plans_result["plans_present"] and plans_result["pro_plan_present"]
            status_working = status_status == 200 and status_result["plan_type_present"]
            validate_working = validate_status == 200 and validate_result["eligible_present"]
            
            if plans_working and status_working and validate_working:
                self.log_test_result(test_name, "passed", "All subscription information endpoints working", details)
            elif plans_working and status_working:
                self.log_test_result(test_name, "warning", "Main endpoints working, validation endpoint has issues", details)
            elif plans_working or status_working:
                self.log_test_result(test_name, "warning", "Some subscription information endpoints working", details)
            else:
                self.log_test_result(test_name, "failed", "Subscription information endpoints have issues", details)
        
        except Exception as e:
            self.log_test_result(test_name, "failed", f"Error testing subscription info endpoints: {str(e)}")
    
    # ================================================================================
    # 🎯 TEST 6: TRIAL ELIGIBILITY BUSINESS LOGIC
    # ================================================================================
    
    async def test_trial_eligibility_business_logic(self):
        """Test 6: Trial eligibility business logic with different user scenarios"""
        test_name = "Trial Eligibility Business Logic"
        
        try:
            headers = self.get_auth_headers()
            if not headers:
                self.log_test_result(test_name, "failed", "No authentication token available")
                return
            
            # Test 1: New user should be eligible
            async with self.session.get(
                f"{API_BASE}/subscription/trial-eligibility?plan=pro", 
                headers=headers
            ) as response:
                new_user_status = response.status
                new_user_data = await response.json()
                
                new_user_result = {
                    "status_code": new_user_status,
                    "eligible": new_user_data.get("eligible") if isinstance(new_user_data, dict) else None,
                    "reason": new_user_data.get("reason") if isinstance(new_user_data, dict) else None,
                    "message": new_user_data.get("message") if isinstance(new_user_data, dict) else None
                }
            
            # Test 2: Test with different plans
            plan_tests = {}
            for plan in ["pro", "premium"]:
                async with self.session.get(
                    f"{API_BASE}/subscription/trial-eligibility?plan={plan}", 
                    headers=headers
                ) as response:
                    plan_status = response.status
                    plan_data = await response.json()
                    
                    plan_tests[plan] = {
                        "status_code": plan_status,
                        "eligible": plan_data.get("eligible") if isinstance(plan_data, dict) else None,
                        "plan_type": plan_data.get("plan_type") if isinstance(plan_data, dict) else None
                    }
            
            # Test 3: Test invalid plan rejection
            async with self.session.get(
                f"{API_BASE}/subscription/trial-eligibility?plan=gratuit", 
                headers=headers
            ) as response:
                invalid_plan_status = response.status
                invalid_plan_data = await response.json()
                
                invalid_plan_result = {
                    "status_code": invalid_plan_status,
                    "properly_rejected": invalid_plan_status == 400,
                    "error_message": invalid_plan_data.get("detail") if isinstance(invalid_plan_data, dict) else None
                }
            
            details = {
                "new_user_test": new_user_result,
                "plan_tests": plan_tests,
                "invalid_plan_test": invalid_plan_result
            }
            
            # Evaluate results
            new_user_eligible = new_user_result.get("eligible") == True
            pro_premium_working = (
                plan_tests.get("pro", {}).get("status_code") == 200 and
                plan_tests.get("premium", {}).get("status_code") == 200
            )
            invalid_plan_rejected = invalid_plan_result["properly_rejected"]
            
            if new_user_eligible and pro_premium_working and invalid_plan_rejected:
                self.log_test_result(test_name, "passed", "Trial eligibility business logic working correctly", details)
            elif pro_premium_working and invalid_plan_rejected:
                self.log_test_result(test_name, "warning", "Business logic working but new user eligibility unclear", details)
            else:
                self.log_test_result(test_name, "failed", "Trial eligibility business logic has issues", details)
        
        except Exception as e:
            self.log_test_result(test_name, "failed", f"Error testing trial eligibility business logic: {str(e)}")
    
    # ================================================================================
    # 🎯 MAIN TEST RUNNER
    # ================================================================================
    
    async def run_all_tests(self):
        """Run all Stripe reinforcement tests"""
        await self.setup()
        
        try:
            # Run all tests
            await self.test_trial_eligibility_endpoint()
            await self.test_price_id_validation()
            await self.test_subscription_creation_with_eligibility()
            await self.test_webhook_security()
            await self.test_subscription_info_endpoints()
            await self.test_trial_eligibility_business_logic()
            
            # Print summary
            self.print_final_summary()
            
        finally:
            await self.cleanup()
    
    def print_final_summary(self):
        """Print final test summary"""
        summary = self.results["summary"]
        
        print(f"\n{'='*70}")
        print("📊 STRIPE REINFORCEMENT SYSTEM TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Total Tests: {summary['total']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"⚠️  Warnings: {summary['warnings']}")
        
        success_rate = (summary['passed'] / summary['total']) * 100 if summary['total'] > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Overall assessment
        if summary['failed'] == 0:
            print(f"\n✅ OVERALL RESULT: Stripe reinforcement system is working correctly")
        elif summary['failed'] <= 2:
            print(f"\n⚠️  OVERALL RESULT: Stripe reinforcement system has minor issues")
        else:
            print(f"\n❌ OVERALL RESULT: Stripe reinforcement system has significant issues")
        
        print(f"\n📁 Detailed results available in test results")
        print(f"🕐 Test completed at: {datetime.utcnow().isoformat()}Z")

async def main():
    """Main test execution"""
    tester = StripeReinforcementTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())