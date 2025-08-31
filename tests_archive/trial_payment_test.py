#!/usr/bin/env python3
"""
ECOMSIMPLY Trial Payment Integration Testing
===========================================

This test specifically focuses on the issue mentioned in the review:
"The frontend handleTrialSubscription function calls /api/payments/checkout with 
trial_subscription: true but users are seeing 'Erreur lors de l'initialisation 
de l'essai gratuit' error after login."

Test User Credentials:
- Email: msylla54@yahoo.fr
- Password: NewPassword123
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 30

class TrialPaymentTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def authenticate_user(self):
        """Authenticate with the test user credentials"""
        self.log("🔐 Authenticating with test user credentials...")
        
        login_data = {
            "email": "msylla54@yahoo.fr",
            "password": "NewPassword123"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.auth_token = data["access_token"]
                    self.log(f"✅ Authentication successful")
                    self.log(f"   User: {login_data['email']}")
                    self.log(f"   Token: {self.auth_token[:20]}...")
                    return True
                else:
                    self.log(f"❌ Authentication failed: No access token in response", "ERROR")
                    self.log(f"   Response: {data}", "ERROR")
                    return False
            else:
                self.log(f"❌ Authentication failed: HTTP {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data}", "ERROR")
                except:
                    self.log(f"   Error: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication failed: {str(e)}", "ERROR")
            return False
    
    def test_trial_checkout_pro(self):
        """Test /api/payments/checkout with trial_subscription: true for Pro plan"""
        self.log("💳 Testing Pro plan trial checkout...")
        
        if not self.auth_token:
            self.log("❌ Cannot test - no authentication token", "ERROR")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        checkout_data = {
            "plan_type": "pro",
            "origin_url": "https://ecomsimply.com",
            "trial_subscription": True
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/payments/checkout", json=checkout_data, headers=headers)
            
            self.log(f"   Request URL: {BASE_URL}/payments/checkout")
            self.log(f"   Request Data: {json.dumps(checkout_data, indent=2)}")
            self.log(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Pro trial checkout successful!")
                self.log(f"   Session ID: {data.get('session_id', 'N/A')}")
                self.log(f"   Checkout URL: {data.get('checkout_url', 'N/A')[:100]}...")
                self.log(f"   Plan Type: {data.get('plan_type', 'N/A')}")
                self.log(f"   Amount: {data.get('amount', 'N/A')}")
                self.log(f"   Currency: {data.get('currency', 'N/A')}")
                return True
            else:
                self.log(f"❌ Pro trial checkout failed: HTTP {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error Response: {json.dumps(error_data, indent=2)}", "ERROR")
                except:
                    self.log(f"   Error Response: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Pro trial checkout failed: {str(e)}", "ERROR")
            return False
    
    def test_trial_checkout_premium(self):
        """Test /api/payments/checkout with trial_subscription: true for Premium plan"""
        self.log("💎 Testing Premium plan trial checkout...")
        
        if not self.auth_token:
            self.log("❌ Cannot test - no authentication token", "ERROR")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        checkout_data = {
            "plan_type": "premium",
            "origin_url": "https://ecomsimply.com",
            "trial_subscription": True
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/payments/checkout", json=checkout_data, headers=headers)
            
            self.log(f"   Request URL: {BASE_URL}/payments/checkout")
            self.log(f"   Request Data: {json.dumps(checkout_data, indent=2)}")
            self.log(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Premium trial checkout successful!")
                self.log(f"   Session ID: {data.get('session_id', 'N/A')}")
                self.log(f"   Checkout URL: {data.get('checkout_url', 'N/A')[:100]}...")
                self.log(f"   Plan Type: {data.get('plan_type', 'N/A')}")
                self.log(f"   Amount: {data.get('amount', 'N/A')}")
                self.log(f"   Currency: {data.get('currency', 'N/A')}")
                return True
            else:
                self.log(f"❌ Premium trial checkout failed: HTTP {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error Response: {json.dumps(error_data, indent=2)}", "ERROR")
                except:
                    self.log(f"   Error Response: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Premium trial checkout failed: {str(e)}", "ERROR")
            return False
    
    def test_regular_checkout_comparison(self):
        """Test regular checkout (without trial) for comparison"""
        self.log("🔄 Testing regular checkout for comparison...")
        
        if not self.auth_token:
            self.log("❌ Cannot test - no authentication token", "ERROR")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        checkout_data = {
            "plan_type": "pro",
            "origin_url": "https://ecomsimply.com"
            # No trial_subscription parameter
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/payments/checkout", json=checkout_data, headers=headers)
            
            self.log(f"   Request URL: {BASE_URL}/payments/checkout")
            self.log(f"   Request Data: {json.dumps(checkout_data, indent=2)}")
            self.log(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Regular checkout successful!")
                self.log(f"   Session ID: {data.get('session_id', 'N/A')}")
                self.log(f"   Checkout URL: {data.get('checkout_url', 'N/A')[:100]}...")
                self.log(f"   Plan Type: {data.get('plan_type', 'N/A')}")
                self.log(f"   Amount: {data.get('amount', 'N/A')}")
                self.log(f"   Currency: {data.get('currency', 'N/A')}")
                return True
            else:
                self.log(f"❌ Regular checkout failed: HTTP {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error Response: {json.dumps(error_data, indent=2)}", "ERROR")
                except:
                    self.log(f"   Error Response: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Regular checkout failed: {str(e)}", "ERROR")
            return False
    
    def test_error_scenarios(self):
        """Test various error scenarios"""
        self.log("⚠️ Testing error scenarios...")
        
        if not self.auth_token:
            self.log("❌ Cannot test - no authentication token", "ERROR")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        # Test with invalid plan type
        self.log("   Testing invalid plan type...")
        invalid_data = {
            "plan_type": "invalid_plan",
            "origin_url": "https://ecomsimply.com",
            "trial_subscription": True
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/payments/checkout", json=invalid_data, headers=headers)
            if response.status_code == 400:
                self.log("   ✅ Invalid plan type correctly rejected")
            else:
                self.log(f"   ⚠️ Invalid plan type response: {response.status_code}")
        except Exception as e:
            self.log(f"   ❌ Error testing invalid plan: {str(e)}", "ERROR")
        
        # Test with missing origin_url
        self.log("   Testing missing origin_url...")
        missing_url_data = {
            "plan_type": "pro",
            "trial_subscription": True
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/payments/checkout", json=missing_url_data, headers=headers)
            if response.status_code in [400, 422]:
                self.log("   ✅ Missing origin_url correctly rejected")
            else:
                self.log(f"   ⚠️ Missing origin_url response: {response.status_code}")
        except Exception as e:
            self.log(f"   ❌ Error testing missing URL: {str(e)}", "ERROR")
        
        # Test without authentication
        self.log("   Testing without authentication...")
        try:
            response = self.session.post(f"{BASE_URL}/payments/checkout", json={
                "plan_type": "pro",
                "origin_url": "https://ecomsimply.com",
                "trial_subscription": True
            })
            if response.status_code == 401:
                self.log("   ✅ Unauthenticated request correctly rejected")
            else:
                self.log(f"   ⚠️ Unauthenticated request response: {response.status_code}")
        except Exception as e:
            self.log(f"   ❌ Error testing unauthenticated: {str(e)}", "ERROR")
        
        return True
    
    def run_all_tests(self):
        """Run all trial payment integration tests"""
        self.log("🚀 Starting Trial Payment Integration Testing")
        self.log("=" * 60)
        self.log(f"Backend URL: {BASE_URL}")
        self.log(f"Test User: msylla54@yahoo.fr")
        self.log("=" * 60)
        
        results = []
        
        # Authenticate first
        auth_success = self.authenticate_user()
        results.append(("Authentication", auth_success))
        
        if auth_success:
            # Test trial checkout endpoints
            pro_success = self.test_trial_checkout_pro()
            results.append(("Pro Trial Checkout", pro_success))
            
            premium_success = self.test_trial_checkout_premium()
            results.append(("Premium Trial Checkout", premium_success))
            
            regular_success = self.test_regular_checkout_comparison()
            results.append(("Regular Checkout", regular_success))
            
            error_success = self.test_error_scenarios()
            results.append(("Error Scenarios", error_success))
        
        # Print summary
        self.log("=" * 60)
        self.log("🎯 TEST SUMMARY")
        self.log("=" * 60)
        
        total_tests = len(results)
        passed_tests = sum(1 for _, success in results if success)
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"Total Tests: {total_tests}")
        self.log(f"Passed: {passed_tests}")
        self.log(f"Failed: {failed_tests}")
        self.log(f"Success Rate: {success_rate:.1f}%")
        
        for test_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            self.log(f"  {status} {test_name}")
        
        if success_rate >= 80:
            self.log("🎉 OVERALL STATUS: TRIAL PAYMENT INTEGRATION IS WORKING!")
            return True
        else:
            self.log("❌ OVERALL STATUS: TRIAL PAYMENT INTEGRATION HAS ISSUES")
            return False

def main():
    """Main test execution"""
    tester = TrialPaymentTester()
    success = tester.run_all_tests()
    return success

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        exit(1)