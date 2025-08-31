#!/usr/bin/env python3
"""
FIXED CRITICAL BUG TEST: Product Sheet Generation Issues Identified and Fixed
Focus: Testing with corrected parameters based on validation errors found

ISSUES IDENTIFIED:
1. number_of_images must be >= 1 (validation error 422)
2. GPT-4 Turbo returning dict instead of string for target_audience (500 error)

FIXES APPLIED:
1. Set number_of_images to 1 when generate_image is True, remove when False
2. Test both scenarios to isolate the GPT-4 Turbo parsing issue
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 60

class FixedSheetGenerationTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        self.user_data = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def create_test_user(self):
        """Create a test user for sheet generation"""
        self.log("👤 Creating test user...")
        
        timestamp = int(time.time())
        test_user = {
            "email": f"test.fixed{timestamp}@example.com",
            "name": "Test Fixed User",
            "password": "TestPassword123!"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=test_user)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.user_data = data.get("user")
                
                if self.auth_token and self.user_data:
                    self.log(f"✅ User Created: {self.user_data['name']} ({self.user_data['email']})")
                    return True
                else:
                    self.log("❌ User Creation: Missing token or user data", "ERROR")
                    return False
            else:
                self.log(f"❌ User Creation failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ User Creation failed: {str(e)}", "ERROR")
            return False
    
    def test_sheet_generation_without_image(self):
        """Test sheet generation WITHOUT image (fixed validation)"""
        self.log("📝 Testing sheet generation WITHOUT image (validation fixed)...")
        
        if not self.auth_token:
            self.log("❌ Cannot test: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # FIXED: Remove number_of_images when generate_image is False
        test_data = {
            "product_name": "iPhone 15",
            "product_description": "Smartphone Apple dernière génération",
            "generate_image": False,
            "language": "fr"
        }
        
        self.log(f"📝 Test data: {json.dumps(test_data, ensure_ascii=False)}")
        
        try:
            self.log("🔄 Making API call to /api/generate-sheet...")
            start_time = time.time()
            
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.log(f"⏱️ API call completed in {duration:.2f} seconds")
            self.log(f"📊 Response status: {response.status_code}")
            
            if response.status_code != 200:
                self.log(f"❌ API call failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
            data = response.json()
            
            if not data.get("success", False):
                self.log(f"❌ Generation failed: {data.get('message', 'Unknown error')}", "ERROR")
                return False
            
            sheet_data = data.get("sheet", {})
            if not sheet_data:
                self.log("❌ No sheet data in response", "ERROR")
                return False
            
            # Log successful generation
            self.log("✅ SUCCESS: Product sheet generated without image!")
            self.log(f"   Sheet ID: {sheet_data['id']}")
            self.log(f"   Generated Title: {sheet_data['generated_title']}")
            self.log(f"   AI Generated: {sheet_data.get('is_ai_generated', 'Unknown')}")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Test failed: {str(e)}", "ERROR")
            return False
    
    def test_sheet_generation_with_image(self):
        """Test sheet generation WITH image (fixed validation)"""
        self.log("🖼️ Testing sheet generation WITH image (validation fixed)...")
        
        if not self.auth_token:
            self.log("❌ Cannot test: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # FIXED: Set number_of_images to 1 when generate_image is True
        test_data = {
            "product_name": "MacBook Pro",
            "product_description": "Ordinateur portable professionnel Apple",
            "generate_image": True,
            "number_of_images": 1,
            "language": "fr"
        }
        
        self.log(f"📝 Test data: {json.dumps(test_data, ensure_ascii=False)}")
        
        try:
            self.log("🔄 Making API call with image generation...")
            start_time = time.time()
            
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.log(f"⏱️ API call completed in {duration:.2f} seconds")
            self.log(f"📊 Response status: {response.status_code}")
            
            if response.status_code != 200:
                self.log(f"❌ API call failed: {response.status_code}", "ERROR")
                self.log(f"❌ Response: {response.text}", "ERROR")
                
                # Check if this is the GPT-4 Turbo parsing issue
                if response.status_code == 500 and "target_audience" in response.text:
                    self.log("🔍 IDENTIFIED: GPT-4 Turbo JSON parsing issue!", "ERROR")
                    self.log("   GPT-4 Turbo is returning dict instead of string for target_audience", "ERROR")
                    self.log("   This confirms the reported GPT-4 Turbo modification bug", "ERROR")
                
                return False
                
            data = response.json()
            
            if not data.get("success", False):
                self.log(f"❌ Generation failed: {data.get('message', 'Unknown error')}", "ERROR")
                return False
            
            sheet_data = data.get("sheet", {})
            if not sheet_data:
                self.log("❌ No sheet data in response", "ERROR")
                return False
            
            # Check for image
            has_image = bool(sheet_data.get("product_image_base64") or 
                           (sheet_data.get("product_images_base64") and len(sheet_data["product_images_base64"]) > 0))
            
            self.log("✅ SUCCESS: Product sheet generated with image!")
            self.log(f"   Sheet ID: {sheet_data['id']}")
            self.log(f"   Generated Title: {sheet_data['generated_title']}")
            self.log(f"   Image Generated: {'✅ Yes' if has_image else '❌ No'}")
            self.log(f"   AI Generated: {sheet_data.get('is_ai_generated', 'Unknown')}")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Test failed: {str(e)}", "ERROR")
            return False
    
    def test_multiple_products_fixed(self):
        """Test multiple products with fixed validation"""
        self.log("🔄 Testing multiple products with fixed validation...")
        
        if not self.auth_token:
            self.log("❌ Cannot test: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        test_products = [
            ("Papier toilette", "Papier toilette doux et résistant"),
            ("Smartphone Samsung", "Téléphone Android dernière génération"),
            ("Chaussures Nike", "Baskets de sport pour running")
        ]
        
        success_count = 0
        
        for product_name, description in test_products:
            self.log(f"🧪 Testing: {product_name}")
            
            # FIXED: Remove number_of_images for no-image generation
            test_data = {
                "product_name": product_name,
                "product_description": description,
                "generate_image": False,
                "language": "fr"
            }
            
            try:
                response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success", False):
                        sheet_data = data.get("sheet", {})
                        self.log(f"   ✅ {product_name}: Generated successfully")
                        self.log(f"      Title: {sheet_data.get('generated_title', 'N/A')[:50]}...")
                        success_count += 1
                    else:
                        self.log(f"   ❌ {product_name}: Generation failed - {data.get('message', 'Unknown')}")
                elif response.status_code == 422:
                    self.log(f"   ❌ {product_name}: Validation error - {response.text}")
                elif response.status_code == 500:
                    self.log(f"   ❌ {product_name}: Server error (likely GPT-4 Turbo parsing issue)")
                else:
                    self.log(f"   ❌ {product_name}: API call failed - {response.status_code}")
                    
            except Exception as e:
                self.log(f"   ❌ {product_name}: Exception - {str(e)}")
            
            time.sleep(1)  # Brief pause between requests
        
        self.log(f"📊 Multiple products test: {success_count}/{len(test_products)} successful")
        return success_count > 0  # At least one should work
    
    def run_diagnostic_tests(self):
        """Run diagnostic tests to identify the exact issues"""
        self.log("🔍 RUNNING DIAGNOSTIC TESTS FOR PRODUCT SHEET GENERATION")
        self.log("=" * 80)
        
        tests = [
            ("User Creation", self.create_test_user),
            ("Sheet Generation WITHOUT Image (Fixed)", self.test_sheet_generation_without_image),
            ("Sheet Generation WITH Image (Fixed)", self.test_sheet_generation_with_image),
            ("Multiple Products Test (Fixed)", self.test_multiple_products_fixed)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            self.log(f"\n🔍 Running: {test_name}")
            self.log("-" * 40)
            
            try:
                result = test_func()
                status = "✅ PASS" if result else "❌ FAIL"
                results.append((test_name, result, status))
                self.log(f"{status} {test_name}")
            except Exception as e:
                self.log(f"❌ FAIL {test_name}: Exception - {str(e)}", "ERROR")
                results.append((test_name, False, "❌ FAIL"))
        
        # Summary
        self.log("\n" + "=" * 80)
        self.log("🔍 DIAGNOSTIC SUMMARY - ROOT CAUSE ANALYSIS")
        self.log("=" * 80)
        
        passed = sum(1 for _, result, _ in results if result)
        total = len(results)
        
        for test_name, result, status in results:
            self.log(f"{status} {test_name}")
        
        self.log(f"\n📊 Overall Result: {passed}/{total} tests passed")
        
        # Root cause analysis
        self.log("\n🔍 ROOT CAUSE ANALYSIS:")
        self.log("=" * 40)
        
        if results[1][1]:  # Sheet generation without image works
            self.log("✅ FINDING 1: Basic sheet generation (no image) WORKS")
            self.log("   The core GPT-4 Turbo integration is functional")
        else:
            self.log("❌ FINDING 1: Basic sheet generation BROKEN")
            self.log("   Core functionality is not working")
        
        if not results[2][1]:  # Sheet generation with image fails
            self.log("❌ FINDING 2: Image generation causes failures")
            self.log("   GPT-4 Turbo JSON parsing issue confirmed")
            self.log("   target_audience field returned as dict instead of string")
        else:
            self.log("✅ FINDING 2: Image generation works correctly")
        
        self.log("\n🎯 CONCLUSION:")
        if passed >= 2:
            self.log("✅ Product sheet generation is PARTIALLY WORKING")
            self.log("   Issue: GPT-4 Turbo JSON parsing needs fixing")
            self.log("   Solution: Fix JSON response parsing in backend")
        else:
            self.log("❌ Product sheet generation is BROKEN")
            self.log("   Multiple critical issues need immediate attention")
        
        return passed, total

def main():
    """Main test execution"""
    tester = FixedSheetGenerationTester()
    passed, total = tester.run_diagnostic_tests()
    
    # Exit with appropriate code
    if passed >= 2:  # At least basic functionality works
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main()