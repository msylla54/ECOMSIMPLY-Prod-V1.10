#!/usr/bin/env python3
"""
SEO Error Handling Validation Test
Quick validation test for the error handling fixes in SEO endpoints as requested in review.

Test Objective: Verify that SEO endpoints now return proper 403 responses for free users 
and 200 responses for Pro/Premium users instead of 500 errors.

Focused Test:
1. Create a free user and test GET /api/seo/config (should return 403, not 500)
2. Create an admin user (premium plan) and test GET /api/seo/config (should return 200, not 500)
3. Test one scraping endpoint with admin user: POST /api/seo/scrape/trends (should return 200, not 500)
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 30

class SEOErrorHandlingTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.free_user_token = None
        self.admin_user_token = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def create_free_user(self):
        """Create a free user for testing 403 responses"""
        self.log("Creating free user for 403 testing...")
        
        timestamp = int(time.time())
        free_user = {
            "email": f"free.user{timestamp}@test.fr",
            "name": "Free User Test",
            "password": "TestPassword123!"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=free_user)
            
            if response.status_code == 200:
                data = response.json()
                self.free_user_token = data.get("token")
                user_data = data.get("user")
                
                if self.free_user_token and user_data:
                    self.log(f"✅ Free User Created: {user_data['name']}")
                    self.log(f"   Email: {user_data['email']}")
                    self.log(f"   Plan: {user_data.get('subscription_plan', 'gratuit')}")
                    return True
                else:
                    self.log("❌ Free User Creation: Missing token or user data", "ERROR")
                    return False
            else:
                self.log(f"❌ Free User Creation failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Free User Creation failed: {str(e)}", "ERROR")
            return False
    
    def create_admin_user(self):
        """Create an admin user (premium plan) for testing 200 responses"""
        self.log("Creating admin user (premium plan) for 200 testing...")
        
        timestamp = int(time.time())
        admin_user = {
            "email": f"admin.test{timestamp}@test.fr",
            "name": "Admin Test User",
            "password": "AdminPassword123!",
            "admin_key": "ECOMSIMPLY_ADMIN_2024"  # Admin key for premium access
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=admin_user)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_user_token = data.get("token")
                user_data = data.get("user")
                
                if self.admin_user_token and user_data:
                    self.log(f"✅ Admin User Created: {user_data['name']}")
                    self.log(f"   Email: {user_data['email']}")
                    self.log(f"   Is Admin: {user_data.get('is_admin', False)}")
                    self.log(f"   Plan: {user_data.get('subscription_plan', 'gratuit')}")
                    
                    # Check if admin user has proper premium access
                    if user_data.get('is_admin') == True:
                        self.log("   ✅ Admin privileges confirmed")
                        return True
                    else:
                        self.log("   ⚠️  Admin privileges not set - may affect premium access")
                        return True  # Still proceed with test
                else:
                    self.log("❌ Admin User Creation: Missing token or user data", "ERROR")
                    return False
            else:
                self.log(f"❌ Admin User Creation failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Admin User Creation failed: {str(e)}", "ERROR")
            return False
    
    def test_free_user_seo_config_403(self):
        """Test that free user gets 403 (not 500) for GET /api/seo/config"""
        self.log("Testing FREE USER: GET /api/seo/config (should return 403, not 500)...")
        
        if not self.free_user_token:
            self.log("❌ Cannot test free user SEO config: No free user token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.free_user_token}"}
        
        try:
            response = self.session.get(f"{BASE_URL}/seo/config", headers=headers)
            
            if response.status_code == 403:
                self.log("✅ FREE USER SEO CONFIG: Correctly returns 403 Forbidden")
                self.log("   ✅ Error handling fixed - no more 500 errors")
                
                # Check response content
                try:
                    error_data = response.json()
                    self.log(f"   Response: {error_data.get('detail', 'Access denied')}")
                except:
                    self.log(f"   Response: {response.text}")
                
                return True
            elif response.status_code == 500:
                self.log("❌ FREE USER SEO CONFIG: Still returns 500 Internal Server Error!", "ERROR")
                self.log("   ❌ Error handling bug NOT FIXED", "ERROR")
                self.log(f"   Response: {response.text}")
                return False
            else:
                self.log(f"❌ FREE USER SEO CONFIG: Unexpected status code {response.status_code}", "ERROR")
                self.log(f"   Expected: 403, Got: {response.status_code}")
                self.log(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Free User SEO Config test failed: {str(e)}", "ERROR")
            return False
    
    def test_admin_user_seo_config_200(self):
        """Test that admin user gets 200 (not 500) for GET /api/seo/config"""
        self.log("Testing ADMIN USER: GET /api/seo/config (should return 200, not 500)...")
        
        if not self.admin_user_token:
            self.log("❌ Cannot test admin user SEO config: No admin user token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_user_token}"}
        
        try:
            response = self.session.get(f"{BASE_URL}/seo/config", headers=headers)
            
            if response.status_code == 200:
                self.log("✅ ADMIN USER SEO CONFIG: Correctly returns 200 OK")
                self.log("   ✅ Error handling fixed - no more 500 errors")
                
                # Check response content
                try:
                    config_data = response.json()
                    self.log(f"   ✅ Config retrieved: {len(str(config_data))} chars")
                    
                    # Validate basic config structure
                    if isinstance(config_data, dict):
                        self.log("   ✅ Valid JSON response structure")
                    else:
                        self.log("   ⚠️  Unexpected response structure")
                        
                except Exception as parse_error:
                    self.log(f"   ⚠️  Response parsing issue: {parse_error}")
                
                return True
            elif response.status_code == 500:
                self.log("❌ ADMIN USER SEO CONFIG: Still returns 500 Internal Server Error!", "ERROR")
                self.log("   ❌ Error handling bug NOT FIXED", "ERROR")
                self.log(f"   Response: {response.text}")
                return False
            elif response.status_code == 403:
                self.log("❌ ADMIN USER SEO CONFIG: Returns 403 - Admin user doesn't have premium access!", "ERROR")
                self.log("   ❌ Admin user subscription plan issue", "ERROR")
                self.log(f"   Response: {response.text}")
                return False
            else:
                self.log(f"❌ ADMIN USER SEO CONFIG: Unexpected status code {response.status_code}", "ERROR")
                self.log(f"   Expected: 200, Got: {response.status_code}")
                self.log(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Admin User SEO Config test failed: {str(e)}", "ERROR")
            return False
    
    def test_admin_user_seo_scrape_trends_200(self):
        """Test that admin user gets 200 (not 500) for POST /api/seo/scrape/trends"""
        self.log("Testing ADMIN USER: POST /api/seo/scrape/trends (should return 200, not 500)...")
        
        if not self.admin_user_token:
            self.log("❌ Cannot test admin user SEO scrape: No admin user token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_user_token}"}
        
        # Sample scraping request
        scrape_request = {
            "keywords": ["ecommerce", "product", "marketing"],
            "region": "FR",
            "category": "general"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/seo/scrape/trends", json=scrape_request, headers=headers)
            
            if response.status_code == 200:
                self.log("✅ ADMIN USER SEO SCRAPE TRENDS: Correctly returns 200 OK")
                self.log("   ✅ Error handling fixed - no more 500 errors")
                
                # Check response content
                try:
                    scrape_data = response.json()
                    self.log(f"   ✅ Scrape data retrieved: {len(str(scrape_data))} chars")
                    
                    # Validate basic scrape response structure
                    if isinstance(scrape_data, dict):
                        self.log("   ✅ Valid JSON response structure")
                        
                        # Check for expected fields
                        if "trends" in scrape_data or "keywords" in scrape_data or "status" in scrape_data:
                            self.log("   ✅ Response contains expected SEO data fields")
                        else:
                            self.log("   ⚠️  Response structure may be placeholder")
                    else:
                        self.log("   ⚠️  Unexpected response structure")
                        
                except Exception as parse_error:
                    self.log(f"   ⚠️  Response parsing issue: {parse_error}")
                
                return True
            elif response.status_code == 500:
                self.log("❌ ADMIN USER SEO SCRAPE TRENDS: Still returns 500 Internal Server Error!", "ERROR")
                self.log("   ❌ Error handling bug NOT FIXED", "ERROR")
                self.log(f"   Response: {response.text}")
                return False
            elif response.status_code == 403:
                self.log("❌ ADMIN USER SEO SCRAPE TRENDS: Returns 403 - Admin user doesn't have premium access!", "ERROR")
                self.log("   ❌ Admin user subscription plan issue", "ERROR")
                self.log(f"   Response: {response.text}")
                return False
            else:
                self.log(f"❌ ADMIN USER SEO SCRAPE TRENDS: Unexpected status code {response.status_code}", "ERROR")
                self.log(f"   Expected: 200, Got: {response.status_code}")
                self.log(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Admin User SEO Scrape Trends test failed: {str(e)}", "ERROR")
            return False
    
    def run_focused_seo_error_handling_tests(self):
        """Run the focused SEO error handling validation tests"""
        self.log("🎯 STARTING FOCUSED SEO ERROR HANDLING VALIDATION TESTS")
        self.log("=" * 80)
        
        test_results = []
        
        # Test 1: Create free user
        self.log("\n📋 TEST 1: Create Free User")
        test_results.append(("Create Free User", self.create_free_user()))
        
        # Test 2: Create admin user (premium plan)
        self.log("\n📋 TEST 2: Create Admin User (Premium Plan)")
        test_results.append(("Create Admin User", self.create_admin_user()))
        
        # Test 3: Free user gets 403 for SEO config (not 500)
        self.log("\n📋 TEST 3: Free User SEO Config - Should Return 403 (Not 500)")
        test_results.append(("Free User SEO Config 403", self.test_free_user_seo_config_403()))
        
        # Test 4: Admin user gets 200 for SEO config (not 500)
        self.log("\n📋 TEST 4: Admin User SEO Config - Should Return 200 (Not 500)")
        test_results.append(("Admin User SEO Config 200", self.test_admin_user_seo_config_200()))
        
        # Test 5: Admin user gets 200 for SEO scrape trends (not 500)
        self.log("\n📋 TEST 5: Admin User SEO Scrape Trends - Should Return 200 (Not 500)")
        test_results.append(("Admin User SEO Scrape Trends 200", self.test_admin_user_seo_scrape_trends_200()))
        
        # Summary
        self.log("\n" + "=" * 80)
        self.log("🎯 SEO ERROR HANDLING VALIDATION TEST RESULTS")
        self.log("=" * 80)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{status}: {test_name}")
            if result:
                passed_tests += 1
        
        self.log(f"\n📊 SUMMARY: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL SEO ERROR HANDLING TESTS PASSED!")
            self.log("✅ Free users get 403 Forbidden (not 500 Internal Server Error)")
            self.log("✅ Admin/Premium users get 200 OK (not 500 Internal Server Error)")
            self.log("✅ Error handling is working correctly")
            return True
        else:
            self.log("❌ SOME SEO ERROR HANDLING TESTS FAILED!")
            self.log("⚠️  Error handling fixes may not be complete")
            return False

def main():
    """Main test execution"""
    print("🎯 SEO Error Handling Validation Test")
    print("Quick validation test for the error handling fixes in SEO endpoints")
    print("=" * 80)
    
    tester = SEOErrorHandlingTester()
    success = tester.run_focused_seo_error_handling_tests()
    
    if success:
        print("\n🎉 SEO ERROR HANDLING VALIDATION: SUCCESS!")
        print("The error handling fixes are working correctly.")
    else:
        print("\n❌ SEO ERROR HANDLING VALIDATION: ISSUES FOUND!")
        print("The error handling fixes need further attention.")
    
    return success

if __name__ == "__main__":
    main()