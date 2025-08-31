#!/usr/bin/env python3
"""
CRITICAL BUG FIX VERIFICATION TEST SUITE
Testing the specific fixes mentioned in the review request:

1. target_audience issue: GPT-4 Turbo returns complex objects that need str() conversion
2. number_of_images issue: Validation changed from ge=1 to ge=0 for generate_image=False

URGENT TESTING OBJECTIVES:
- Test product sheet generation immediately 
- Create test user and generate simple product sheet (iPhone 15, Smartphone Apple)
- Verify API returns 200 status (no more 500 errors)
- Confirm sheet is created and saved
- Test with generate_image: false and number_of_images: 0
- Verify GPT-4 Turbo generates content correctly
- Ensure target_audience is converted to string
- Test different product types and verify performance
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 60  # Increased timeout for AI generation

class CriticalBugFixTester:
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
            "email": f"bugfix.test{timestamp}@ecomsimply.fr",
            "name": "Bug Fix Tester",
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
    
    def test_critical_fix_1_simple_product_generation(self):
        """🎯 CRITICAL TEST 1: Test simple product generation (iPhone 15, Smartphone Apple)"""
        self.log("🎯 CRITICAL TEST 1: Testing simple product generation - iPhone 15")
        
        if not self.auth_token:
            self.log_test_result("Critical Fix 1", False, "No auth token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test data as specified in review request
        test_data = {
            "product_name": "iPhone 15",
            "product_description": "Smartphone Apple",
            "generate_image": True,
            "number_of_images": 1,
            "language": "fr"
        }
        
        self.log(f"📝 Test data: {json.dumps(test_data, ensure_ascii=False)}")
        
        try:
            start_time = time.time()
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            generation_time = time.time() - start_time
            
            self.log(f"⏱️ Generation time: {generation_time:.2f} seconds")
            self.log(f"📊 Response status: {response.status_code}")
            
            if response.status_code != 200:
                self.log_test_result("Critical Fix 1", False, f"API returned {response.status_code} instead of 200: {response.text}")
                return False
                
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                self.log_test_result("Critical Fix 1", False, f"Invalid JSON response: {str(e)}")
                return False
                
            # Check if generation was successful
            if not data.get("success", False):
                error_msg = data.get("message", "Unknown error")
                self.log_test_result("Critical Fix 1", False, f"Generation failed: {error_msg}")
                return False
                
            sheet_data = data.get("sheet", {})
            if not sheet_data:
                self.log_test_result("Critical Fix 1", False, "No sheet data in response")
                return False
            
            # CRITICAL CHECK 1: Verify target_audience is a string (not complex object)
            target_audience = sheet_data.get("target_audience")
            if target_audience is None:
                self.log_test_result("Critical Fix 1", False, "target_audience field is missing")
                return False
                
            if not isinstance(target_audience, str):
                self.log_test_result("Critical Fix 1", False, f"target_audience is not a string: {type(target_audience)} - {target_audience}")
                return False
                
            self.log(f"✅ target_audience is properly converted to string: {target_audience[:100]}...")
            
            # CRITICAL CHECK 2: Verify all required fields are present
            required_fields = [
                "id", "user_id", "product_name", "original_description",
                "generated_title", "marketing_description", "key_features",
                "seo_tags", "price_suggestions", "target_audience", "call_to_action"
            ]
            
            missing_fields = [field for field in required_fields if field not in sheet_data]
            if missing_fields:
                self.log_test_result("Critical Fix 1", False, f"Missing required fields: {missing_fields}")
                return False
                
            # CRITICAL CHECK 3: Verify sheet is saved with proper ID
            sheet_id = sheet_data.get("id")
            if not sheet_id or len(sheet_id) < 10:
                self.log_test_result("Critical Fix 1", False, f"Invalid sheet ID: {sheet_id}")
                return False
                
            self.log(f"✅ Sheet created and saved with ID: {sheet_id}")
            
            # Log generated content for verification
            self.log("📊 GENERATED CONTENT VERIFICATION:")
            self.log(f"   Title: {sheet_data.get('generated_title', 'N/A')}")
            self.log(f"   Features count: {len(sheet_data.get('key_features', []))}")
            self.log(f"   SEO tags count: {len(sheet_data.get('seo_tags', []))}")
            self.log(f"   Target audience type: {type(target_audience).__name__}")
            self.log(f"   Generation time: {generation_time:.2f}s")
            
            success_details = f"✅ API returned 200, sheet created with ID {sheet_id}, target_audience properly converted to string, generation time: {generation_time:.2f}s"
            self.log_test_result("Critical Fix 1", True, success_details, sheet_data)
            return True
            
        except Exception as e:
            self.log_test_result("Critical Fix 1", False, f"Exception during generation: {str(e)}")
            return False
    
    def test_critical_fix_2_no_image_generation(self):
        """🎯 CRITICAL TEST 2: Test with generate_image=False and number_of_images=0"""
        self.log("🎯 CRITICAL TEST 2: Testing generate_image=False with number_of_images=0")
        
        if not self.auth_token:
            self.log_test_result("Critical Fix 2", False, "No auth token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test the specific fix: number_of_images validation changed from ge=1 to ge=0
        test_data = {
            "product_name": "MacBook Pro",
            "product_description": "Ordinateur portable Apple haute performance",
            "generate_image": False,  # CRITICAL: No image generation
            "number_of_images": 0,    # CRITICAL: This should now be allowed (was causing validation error)
            "language": "fr"
        }
        
        self.log(f"📝 Test data: {json.dumps(test_data, ensure_ascii=False)}")
        
        try:
            start_time = time.time()
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            generation_time = time.time() - start_time
            
            self.log(f"⏱️ Generation time: {generation_time:.2f} seconds")
            self.log(f"📊 Response status: {response.status_code}")
            
            # CRITICAL: This should NOT return 500 error anymore
            if response.status_code == 500:
                self.log_test_result("Critical Fix 2", False, f"Still getting 500 error - validation fix not working: {response.text}")
                return False
                
            if response.status_code != 200:
                self.log_test_result("Critical Fix 2", False, f"API returned {response.status_code}: {response.text}")
                return False
                
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                self.log_test_result("Critical Fix 2", False, f"Invalid JSON response: {str(e)}")
                return False
                
            if not data.get("success", False):
                error_msg = data.get("message", "Unknown error")
                self.log_test_result("Critical Fix 2", False, f"Generation failed: {error_msg}")
                return False
                
            sheet_data = data.get("sheet", {})
            if not sheet_data:
                self.log_test_result("Critical Fix 2", False, "No sheet data in response")
                return False
            
            # CRITICAL CHECK: Verify target_audience is string (GPT-4 Turbo fix)
            target_audience = sheet_data.get("target_audience")
            if not isinstance(target_audience, str):
                self.log_test_result("Critical Fix 2", False, f"target_audience not converted to string: {type(target_audience)}")
                return False
                
            # CRITICAL CHECK: Verify no images were generated when generate_image=False
            images_base64 = sheet_data.get("product_images_base64", [])
            single_image = sheet_data.get("product_image_base64")
            
            if images_base64 or single_image:
                self.log_test_result("Critical Fix 2", False, "Images were generated despite generate_image=False")
                return False
                
            self.log("✅ No images generated as expected (generate_image=False)")
            self.log(f"✅ target_audience properly converted to string: {target_audience[:100]}...")
            
            # Verify number_of_images_generated is 0
            num_images_generated = sheet_data.get("number_of_images_generated", -1)
            if num_images_generated != 0:
                self.log_test_result("Critical Fix 2", False, f"number_of_images_generated should be 0, got {num_images_generated}")
                return False
                
            success_details = f"✅ Validation fix working: generate_image=False with number_of_images=0 accepted, no 500 error, target_audience converted to string"
            self.log_test_result("Critical Fix 2", True, success_details, sheet_data)
            return True
            
        except Exception as e:
            self.log_test_result("Critical Fix 2", False, f"Exception during generation: {str(e)}")
            return False
    
    def test_critical_fix_3_gpt4_turbo_content_generation(self):
        """🎯 CRITICAL TEST 3: Verify GPT-4 Turbo generates content correctly"""
        self.log("🎯 CRITICAL TEST 3: Testing GPT-4 Turbo content generation quality")
        
        if not self.auth_token:
            self.log_test_result("Critical Fix 3", False, "No auth token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test with a product that should generate quality content
        test_data = {
            "product_name": "AirPods Pro",
            "product_description": "Écouteurs sans fil Apple avec réduction de bruit active",
            "generate_image": False,
            "number_of_images": 0,
            "language": "fr"
        }
        
        try:
            start_time = time.time()
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            generation_time = time.time() - start_time
            
            if response.status_code != 200:
                self.log_test_result("Critical Fix 3", False, f"API returned {response.status_code}")
                return False
                
            data = response.json()
            if not data.get("success", False):
                self.log_test_result("Critical Fix 3", False, f"Generation failed: {data.get('message', 'Unknown error')}")
                return False
                
            sheet_data = data.get("sheet", {})
            
            # CRITICAL CHECK: Verify all content fields are properly generated
            content_checks = {
                "generated_title": sheet_data.get("generated_title", ""),
                "marketing_description": sheet_data.get("marketing_description", ""),
                "key_features": sheet_data.get("key_features", []),
                "seo_tags": sheet_data.get("seo_tags", []),
                "price_suggestions": sheet_data.get("price_suggestions", ""),
                "target_audience": sheet_data.get("target_audience", ""),
                "call_to_action": sheet_data.get("call_to_action", "")
            }
            
            # Check content quality
            quality_issues = []
            
            # Title should be meaningful
            if len(content_checks["generated_title"]) < 10:
                quality_issues.append("Generated title too short")
                
            # Description should be substantial
            if len(content_checks["marketing_description"]) < 100:
                quality_issues.append("Marketing description too short")
                
            # Should have features
            if len(content_checks["key_features"]) < 3:
                quality_issues.append("Too few key features")
                
            # Should have SEO tags
            if len(content_checks["seo_tags"]) < 3:
                quality_issues.append("Too few SEO tags")
                
            # Target audience should be string and meaningful
            if not isinstance(content_checks["target_audience"], str):
                quality_issues.append("target_audience not converted to string")
            elif len(content_checks["target_audience"]) < 20:
                quality_issues.append("target_audience too short")
                
            if quality_issues:
                self.log_test_result("Critical Fix 3", False, f"Content quality issues: {'; '.join(quality_issues)}")
                return False
            
            # Log content analysis
            self.log("📊 CONTENT QUALITY ANALYSIS:")
            self.log(f"   Title length: {len(content_checks['generated_title'])} chars")
            self.log(f"   Description length: {len(content_checks['marketing_description'])} chars")
            self.log(f"   Features count: {len(content_checks['key_features'])}")
            self.log(f"   SEO tags count: {len(content_checks['seo_tags'])}")
            self.log(f"   Target audience length: {len(content_checks['target_audience'])} chars")
            self.log(f"   Generation time: {generation_time:.2f}s")
            
            success_details = f"✅ GPT-4 Turbo generating quality content, all fields properly populated, target_audience converted to string"
            self.log_test_result("Critical Fix 3", True, success_details, content_checks)
            return True
            
        except Exception as e:
            self.log_test_result("Critical Fix 3", False, f"Exception during generation: {str(e)}")
            return False
    
    def test_critical_fix_4_different_product_types(self):
        """🎯 CRITICAL TEST 4: Test different product types for regression"""
        self.log("🎯 CRITICAL TEST 4: Testing different product types for regression")
        
        if not self.auth_token:
            self.log_test_result("Critical Fix 4", False, "No auth token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test different product types to ensure fixes work across categories
        test_products = [
            {
                "name": "Samsung Galaxy S24",
                "description": "Smartphone Android haut de gamme",
                "category": "Electronics"
            },
            {
                "name": "Nike Air Max 270",
                "description": "Chaussures de sport confortables",
                "category": "Fashion"
            },
            {
                "name": "Dyson V15 Detect",
                "description": "Aspirateur sans fil puissant",
                "category": "Home Appliances"
            }
        ]
        
        successful_tests = 0
        
        for product in test_products:
            self.log(f"🧪 Testing {product['name']} ({product['category']})")
            
            test_data = {
                "product_name": product["name"],
                "product_description": product["description"],
                "generate_image": False,
                "number_of_images": 0,
                "language": "fr"
            }
            
            try:
                response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success", False):
                        sheet_data = data.get("sheet", {})
                        target_audience = sheet_data.get("target_audience")
                        
                        # Critical check: target_audience must be string
                        if isinstance(target_audience, str) and len(target_audience) > 10:
                            self.log(f"   ✅ {product['name']}: target_audience properly converted to string")
                            successful_tests += 1
                        else:
                            self.log(f"   ❌ {product['name']}: target_audience issue - {type(target_audience)}")
                    else:
                        self.log(f"   ❌ {product['name']}: Generation failed - {data.get('message', 'Unknown error')}")
                else:
                    self.log(f"   ❌ {product['name']}: API error {response.status_code}")
                    
            except Exception as e:
                self.log(f"   ❌ {product['name']}: Exception - {str(e)}")
                
            time.sleep(1)  # Brief pause between tests
        
        success = successful_tests == len(test_products)
        details = f"Successfully tested {successful_tests}/{len(test_products)} product types"
        self.log_test_result("Critical Fix 4", success, details)
        return success
    
    def test_critical_fix_5_performance_verification(self):
        """🎯 CRITICAL TEST 5: Verify performance is acceptable"""
        self.log("🎯 CRITICAL TEST 5: Testing performance after fixes")
        
        if not self.auth_token:
            self.log_test_result("Critical Fix 5", False, "No auth token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        test_data = {
            "product_name": "Test Performance Product",
            "product_description": "Testing performance after critical bug fixes",
            "generate_image": False,
            "number_of_images": 0,
            "language": "fr"
        }
        
        try:
            start_time = time.time()
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            generation_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success", False):
                    # Performance should be reasonable (under 30 seconds for text-only generation)
                    if generation_time < 30:
                        success_details = f"✅ Performance acceptable: {generation_time:.2f}s for text-only generation"
                        self.log_test_result("Critical Fix 5", True, success_details)
                        return True
                    else:
                        self.log_test_result("Critical Fix 5", False, f"Performance too slow: {generation_time:.2f}s")
                        return False
                else:
                    self.log_test_result("Critical Fix 5", False, f"Generation failed: {data.get('message', 'Unknown error')}")
                    return False
            else:
                self.log_test_result("Critical Fix 5", False, f"API error: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("Critical Fix 5", False, f"Exception: {str(e)}")
            return False
    
    def run_all_critical_tests(self):
        """Run all critical bug fix tests"""
        self.log("🚀 STARTING CRITICAL BUG FIX VERIFICATION TESTS")
        self.log("=" * 80)
        
        # Step 1: Create test user
        if not self.create_test_user():
            self.log("❌ CRITICAL: Cannot proceed without test user", "ERROR")
            return False
        
        # Step 2: Run all critical tests
        tests = [
            ("Critical Fix 1: Simple Product Generation", self.test_critical_fix_1_simple_product_generation),
            ("Critical Fix 2: No Image Generation", self.test_critical_fix_2_no_image_generation),
            ("Critical Fix 3: GPT-4 Turbo Content", self.test_critical_fix_3_gpt4_turbo_content_generation),
            ("Critical Fix 4: Different Product Types", self.test_critical_fix_4_different_product_types),
            ("Critical Fix 5: Performance Verification", self.test_critical_fix_5_performance_verification)
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
        self.log("🏁 CRITICAL BUG FIX TEST SUMMARY")
        self.log("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        self.log(f"📊 Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL CRITICAL BUG FIXES VERIFIED SUCCESSFULLY!")
            self.log("✅ Product sheet generation is working correctly")
            self.log("✅ target_audience conversion to string is working")
            self.log("✅ number_of_images validation allows 0 when generate_image=False")
            self.log("✅ GPT-4 Turbo content generation is functional")
            self.log("✅ System is ready for production use")
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
    tester = CriticalBugFixTester()
    success = tester.run_all_critical_tests()
    
    if success:
        print("\n🎉 CRITICAL BUG FIX VERIFICATION: SUCCESS!")
        exit(0)
    else:
        print("\n❌ CRITICAL BUG FIX VERIFICATION: FAILED!")
        exit(1)

if __name__ == "__main__":
    main()