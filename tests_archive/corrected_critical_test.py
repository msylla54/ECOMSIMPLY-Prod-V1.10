#!/usr/bin/env python3
"""
CORRECTED CRITICAL BUG FIX VERIFICATION TEST SUITE
Based on actual API response structure analysis
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 60

class CorrectedBugFixTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        self.user_data = None
        self.test_results = []
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def log_test_result(self, test_name: str, success: bool, details: str, data: Dict = None):
        """Log test result with details"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "data": data,
            "timestamp": time.strftime("%H:%M:%S")
        }
        self.test_results.append(result)
        self.log(f"{status} {test_name}: {details}")
        
    def create_test_user(self):
        """Create a test user for testing"""
        self.log("🔧 Creating test user for critical bug fix testing...")
        
        timestamp = int(time.time())
        test_user = {
            "email": f"corrected.test{timestamp}@ecomsimply.fr",
            "name": "Corrected Bug Fix Tester",
            "password": "TestPassword123!"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=test_user)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.user_data = data.get("user")
                
                if self.auth_token and self.user_data:
                    self.log_test_result("User Creation", True, f"Test user created: {self.user_data['email']}")
                    return True
                else:
                    self.log_test_result("User Creation", False, "Missing token or user data in response")
                    return False
            else:
                self.log_test_result("User Creation", False, f"Registration failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test_result("User Creation", False, f"Exception: {str(e)}")
            return False
    
    def test_critical_fix_1_api_returns_200(self):
        """🎯 CRITICAL TEST 1: Verify API returns 200 status (no more 500 errors)"""
        self.log("🎯 CRITICAL TEST 1: Testing API returns 200 status - iPhone 15")
        
        if not self.auth_token:
            self.log_test_result("Critical Fix 1", False, "No auth token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        test_data = {
            "product_name": "iPhone 15",
            "product_description": "Smartphone Apple",
            "generate_image": True,
            "number_of_images": 1,
            "language": "fr"
        }
        
        try:
            start_time = time.time()
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            generation_time = time.time() - start_time
            
            self.log(f"⏱️ Generation time: {generation_time:.2f} seconds")
            self.log(f"📊 Response status: {response.status_code}")
            
            # CRITICAL: Should return 200, not 500
            if response.status_code == 500:
                self.log_test_result("Critical Fix 1", False, f"Still getting 500 error - fixes not working: {response.text}")
                return False
                
            if response.status_code != 200:
                self.log_test_result("Critical Fix 1", False, f"API returned {response.status_code}: {response.text}")
                return False
                
            # Try to parse JSON
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                self.log_test_result("Critical Fix 1", False, f"Invalid JSON response: {str(e)}")
                return False
                
            # Check required fields are present
            required_fields = [
                "generated_title", "marketing_description", "key_features",
                "seo_tags", "price_suggestions", "target_audience", "call_to_action"
            ]
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.log_test_result("Critical Fix 1", False, f"Missing required fields: {missing_fields}")
                return False
            
            # CRITICAL CHECK: target_audience should be a string
            target_audience = data.get("target_audience")
            if not isinstance(target_audience, str):
                self.log_test_result("Critical Fix 1", False, f"target_audience is not a string: {type(target_audience)}")
                return False
                
            self.log(f"✅ API returned 200 status")
            self.log(f"✅ All required fields present")
            self.log(f"✅ target_audience is string: {target_audience[:100]}...")
            
            success_details = f"✅ API returned 200, all fields present, target_audience is string, generation time: {generation_time:.2f}s"
            self.log_test_result("Critical Fix 1", True, success_details, data)
            return True
            
        except Exception as e:
            self.log_test_result("Critical Fix 1", False, f"Exception during generation: {str(e)}")
            return False
    
    def test_critical_fix_2_validation_allows_zero_images(self):
        """🎯 CRITICAL TEST 2: Test validation allows number_of_images=0 when generate_image=False"""
        self.log("🎯 CRITICAL TEST 2: Testing validation allows number_of_images=0")
        
        if not self.auth_token:
            self.log_test_result("Critical Fix 2", False, "No auth token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # This combination previously caused validation error
        test_data = {
            "product_name": "MacBook Pro",
            "product_description": "Ordinateur portable Apple haute performance",
            "generate_image": False,  # No image generation
            "number_of_images": 0,    # This should now be allowed (was ge=1, now ge=0)
            "language": "fr"
        }
        
        try:
            start_time = time.time()
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            generation_time = time.time() - start_time
            
            self.log(f"⏱️ Generation time: {generation_time:.2f} seconds")
            self.log(f"📊 Response status: {response.status_code}")
            
            # CRITICAL: Should NOT return 422 validation error anymore
            if response.status_code == 422:
                self.log_test_result("Critical Fix 2", False, f"Still getting 422 validation error - number_of_images validation not fixed: {response.text}")
                return False
                
            if response.status_code != 200:
                self.log_test_result("Critical Fix 2", False, f"API returned {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Verify target_audience is string
            target_audience = data.get("target_audience")
            if not isinstance(target_audience, str):
                self.log_test_result("Critical Fix 2", False, f"target_audience not converted to string: {type(target_audience)}")
                return False
                
            # Verify no images were generated
            generated_images = data.get("generated_images", [])
            if generated_images:
                self.log_test_result("Critical Fix 2", False, "Images were generated despite generate_image=False")
                return False
                
            self.log("✅ Validation accepts number_of_images=0 when generate_image=False")
            self.log("✅ No images generated as expected")
            self.log(f"✅ target_audience properly converted to string")
            
            success_details = f"✅ Validation fix working: number_of_images=0 accepted, no validation error, target_audience is string"
            self.log_test_result("Critical Fix 2", True, success_details, data)
            return True
            
        except Exception as e:
            self.log_test_result("Critical Fix 2", False, f"Exception during generation: {str(e)}")
            return False
    
    def test_critical_fix_3_target_audience_string_conversion(self):
        """🎯 CRITICAL TEST 3: Verify target_audience is always converted to string"""
        self.log("🎯 CRITICAL TEST 3: Testing target_audience string conversion")
        
        if not self.auth_token:
            self.log_test_result("Critical Fix 3", False, "No auth token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test multiple products to ensure consistent string conversion
        test_products = [
            ("AirPods Pro", "Écouteurs sans fil Apple"),
            ("Samsung Galaxy S24", "Smartphone Android premium"),
            ("Nike Air Max", "Chaussures de sport")
        ]
        
        successful_conversions = 0
        
        for product_name, description in test_products:
            self.log(f"🧪 Testing target_audience conversion for: {product_name}")
            
            test_data = {
                "product_name": product_name,
                "product_description": description,
                "generate_image": False,
                "number_of_images": 0,
                "language": "fr"
            }
            
            try:
                response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    target_audience = data.get("target_audience")
                    
                    # CRITICAL CHECK: Must be string
                    if isinstance(target_audience, str):
                        self.log(f"   ✅ {product_name}: target_audience is string ({len(target_audience)} chars)")
                        successful_conversions += 1
                        
                        # Additional check: should not be empty
                        if len(target_audience.strip()) < 10:
                            self.log(f"   ⚠️ {product_name}: target_audience very short: '{target_audience}'")
                    else:
                        self.log(f"   ❌ {product_name}: target_audience is {type(target_audience)}: {target_audience}")
                else:
                    self.log(f"   ❌ {product_name}: API error {response.status_code}")
                    
            except Exception as e:
                self.log(f"   ❌ {product_name}: Exception - {str(e)}")
                
            time.sleep(1)  # Brief pause between tests
        
        success = successful_conversions == len(test_products)
        details = f"target_audience converted to string for {successful_conversions}/{len(test_products)} products"
        self.log_test_result("Critical Fix 3", success, details)
        return success
    
    def test_critical_fix_4_sheet_creation_and_saving(self):
        """🎯 CRITICAL TEST 4: Verify sheet is created and saved properly"""
        self.log("🎯 CRITICAL TEST 4: Testing sheet creation and saving")
        
        if not self.auth_token:
            self.log_test_result("Critical Fix 4", False, "No auth token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Generate a sheet
        test_data = {
            "product_name": "Test Sheet Creation",
            "product_description": "Testing sheet creation and saving functionality",
            "generate_image": False,
            "number_of_images": 0,
            "language": "fr"
        }
        
        try:
            # Generate sheet
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            
            if response.status_code != 200:
                self.log_test_result("Critical Fix 4", False, f"Sheet generation failed: {response.status_code}")
                return False
                
            sheet_data = response.json()
            
            # Verify sheet has all required data
            required_fields = [
                "generated_title", "marketing_description", "key_features",
                "seo_tags", "price_suggestions", "target_audience", "call_to_action"
            ]
            
            missing_fields = [field for field in required_fields if field not in sheet_data]
            if missing_fields:
                self.log_test_result("Critical Fix 4", False, f"Generated sheet missing fields: {missing_fields}")
                return False
            
            # Now try to retrieve user's sheets to verify it was saved
            time.sleep(1)  # Brief pause to ensure saving is complete
            
            response = self.session.get(f"{BASE_URL}/my-sheets", headers=headers)
            
            if response.status_code != 200:
                self.log_test_result("Critical Fix 4", False, f"Failed to retrieve sheets: {response.status_code}")
                return False
                
            user_sheets = response.json()
            
            if not isinstance(user_sheets, list):
                self.log_test_result("Critical Fix 4", False, f"Sheets response is not a list: {type(user_sheets)}")
                return False
                
            # Find our test sheet
            test_sheet_found = False
            for sheet in user_sheets:
                if sheet.get("product_name") == "Test Sheet Creation":
                    test_sheet_found = True
                    self.log(f"✅ Test sheet found in database with ID: {sheet.get('id', 'No ID')}")
                    break
            
            if not test_sheet_found:
                self.log_test_result("Critical Fix 4", False, "Generated sheet not found in user's sheets")
                return False
            
            self.log("✅ Sheet generated successfully")
            self.log("✅ Sheet saved to database")
            self.log("✅ Sheet retrievable via API")
            
            success_details = f"✅ Sheet created, saved, and retrievable. Total user sheets: {len(user_sheets)}"
            self.log_test_result("Critical Fix 4", True, success_details)
            return True
            
        except Exception as e:
            self.log_test_result("Critical Fix 4", False, f"Exception during test: {str(e)}")
            return False
    
    def test_critical_fix_5_performance_acceptable(self):
        """🎯 CRITICAL TEST 5: Verify performance is acceptable after fixes"""
        self.log("🎯 CRITICAL TEST 5: Testing performance after critical fixes")
        
        if not self.auth_token:
            self.log_test_result("Critical Fix 5", False, "No auth token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        test_data = {
            "product_name": "Performance Test Product",
            "product_description": "Testing performance after critical bug fixes implementation",
            "generate_image": False,  # Faster without image generation
            "number_of_images": 0,
            "language": "fr"
        }
        
        try:
            start_time = time.time()
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            generation_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Performance should be reasonable (under 45 seconds for text-only generation)
                if generation_time < 45:
                    self.log(f"✅ Performance acceptable: {generation_time:.2f}s")
                    
                    # Check content quality
                    title_length = len(data.get("generated_title", ""))
                    desc_length = len(data.get("marketing_description", ""))
                    features_count = len(data.get("key_features", []))
                    
                    self.log(f"✅ Content quality: Title {title_length} chars, Description {desc_length} chars, {features_count} features")
                    
                    success_details = f"✅ Performance: {generation_time:.2f}s, Quality: Title {title_length}c, Desc {desc_length}c, {features_count} features"
                    self.log_test_result("Critical Fix 5", True, success_details)
                    return True
                else:
                    self.log_test_result("Critical Fix 5", False, f"Performance too slow: {generation_time:.2f}s (should be <45s)")
                    return False
            else:
                self.log_test_result("Critical Fix 5", False, f"API error: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("Critical Fix 5", False, f"Exception: {str(e)}")
            return False
    
    def run_all_critical_tests(self):
        """Run all critical bug fix tests"""
        self.log("🚀 STARTING CORRECTED CRITICAL BUG FIX VERIFICATION TESTS")
        self.log("=" * 80)
        
        # Step 1: Create test user
        if not self.create_test_user():
            self.log("❌ CRITICAL: Cannot proceed without test user", "ERROR")
            return False
        
        # Step 2: Run all critical tests
        tests = [
            ("Critical Fix 1: API Returns 200", self.test_critical_fix_1_api_returns_200),
            ("Critical Fix 2: Validation Allows Zero Images", self.test_critical_fix_2_validation_allows_zero_images),
            ("Critical Fix 3: Target Audience String Conversion", self.test_critical_fix_3_target_audience_string_conversion),
            ("Critical Fix 4: Sheet Creation and Saving", self.test_critical_fix_4_sheet_creation_and_saving),
            ("Critical Fix 5: Performance Acceptable", self.test_critical_fix_5_performance_acceptable)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n🧪 Running: {test_name}")
            self.log("-" * 60)
            
            try:
                if test_func():
                    passed_tests += 1
                    self.log(f"✅ {test_name}: PASSED")
                else:
                    self.log(f"❌ {test_name}: FAILED")
            except Exception as e:
                self.log(f"❌ {test_name}: EXCEPTION - {str(e)}")
            
            time.sleep(2)  # Brief pause between tests
        
        # Final summary
        self.log("\n" + "=" * 80)
        self.log("🏁 CORRECTED CRITICAL BUG FIX TEST SUMMARY")
        self.log("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        self.log(f"📊 Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL CRITICAL BUG FIXES VERIFIED SUCCESSFULLY!")
            self.log("✅ Product sheet generation working correctly")
            self.log("✅ API returns 200 status (no more 500 errors)")
            self.log("✅ target_audience conversion to string working")
            self.log("✅ number_of_images validation allows 0 when generate_image=False")
            self.log("✅ Sheets are created and saved properly")
            self.log("✅ Performance is acceptable")
            self.log("✅ System ready for production use")
        else:
            self.log("❌ SOME CRITICAL TESTS FAILED!")
            self.log("⚠️ Product sheet generation may still have issues")
            
        # Detailed results
        self.log("\n📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status_icon = "✅" if result["success"] else "❌"
            self.log(f"   {status_icon} {result['test']}: {result['details']}")
        
        return passed_tests == total_tests

def main():
    """Main test execution"""
    tester = CorrectedBugFixTester()
    success = tester.run_all_critical_tests()
    
    if success:
        print("\n🎉 CRITICAL BUG FIX VERIFICATION: SUCCESS!")
        exit(0)
    else:
        print("\n❌ CRITICAL BUG FIX VERIFICATION: FAILED!")
        exit(1)

if __name__ == "__main__":
    main()