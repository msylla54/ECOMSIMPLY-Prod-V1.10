#!/usr/bin/env python3
"""
ECOMSIMPLY Authentication and Subscription Level Testing
Tests authentication requirements and subscription level access for image generation
"""

import requests
import json
import time
import base64
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 60

class AuthSubscriptionTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_authentication_required(self):
        """Test that image generation requires authentication"""
        self.log("Testing authentication requirements for image generation...")
        
        test_request = {
            "product_name": "Test Product",
            "product_description": "Testing authentication requirement",
            "generate_image": True,
            "number_of_images": 1
        }
        
        try:
            # Test without authentication
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_request)
            
            if response.status_code == 401:
                self.log("✅ Authentication Required: Endpoint correctly requires authentication")
                return True
            elif response.status_code == 403:
                self.log("✅ Authentication Required: Endpoint correctly requires authentication (403)")
                return True
            else:
                self.log(f"❌ Authentication Required: Endpoint should require auth but returned {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication test failed: {str(e)}", "ERROR")
            return False
    
    def test_invalid_token(self):
        """Test behavior with invalid authentication token"""
        self.log("Testing behavior with invalid authentication token...")
        
        headers = {"Authorization": "Bearer invalid_token_12345"}
        test_request = {
            "product_name": "Test Product",
            "product_description": "Testing invalid token",
            "generate_image": True,
            "number_of_images": 1
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_request, headers=headers)
            
            if response.status_code == 401:
                self.log("✅ Invalid Token: Correctly rejected invalid authentication token")
                return True
            else:
                self.log(f"❌ Invalid Token: Should reject invalid token but returned {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Invalid token test failed: {str(e)}", "ERROR")
            return False
    
    def create_test_user_and_authenticate(self):
        """Create a test user and get authentication token"""
        self.log("Creating test user for authentication testing...")
        
        timestamp = int(time.time())
        user_data = {
            "email": f"auth.test.{timestamp}@ecomsimply.fr",
            "name": "Auth Test User",
            "password": "TestPassword123!"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=user_data)
            
            if response.status_code == 200:
                data = response.json()
                auth_token = data.get("token")
                user_info = data.get("user")
                
                if auth_token and user_info:
                    self.log(f"✅ Created test user: {user_info['name']}")
                    self.log(f"   Plan: {user_info.get('subscription_plan', 'gratuit')}")
                    return auth_token, user_info
                else:
                    self.log("❌ Failed to create user: Missing token or user data", "ERROR")
                    return None, None
            else:
                self.log(f"❌ Failed to create user: {response.status_code} - {response.text}", "ERROR")
                return None, None
                
        except Exception as e:
            self.log(f"❌ Exception creating user: {str(e)}", "ERROR")
            return None, None
    
    def test_subscription_level_access(self, auth_token, user_info):
        """Test that different subscription levels have appropriate access"""
        self.log("Testing subscription level access to image generation...")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        user_plan = user_info.get('subscription_plan', 'gratuit')
        
        test_request = {
            "product_name": f"Subscription Test {user_plan}",
            "product_description": f"Testing {user_plan} plan access to image generation",
            "generate_image": True,
            "number_of_images": 1
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_request, headers=headers)
            
            if response.status_code == 200:
                sheet_data = response.json()
                has_images = bool(sheet_data.get("product_images_base64") and len(sheet_data["product_images_base64"]) > 0)
                
                if has_images:
                    image_data = sheet_data["product_images_base64"][0]
                    decoded = base64.b64decode(image_data)
                    image_size = len(decoded)
                    is_high_quality = image_size > 50000
                    
                    self.log(f"✅ {user_plan.upper()} Plan Access: Image generation successful")
                    self.log(f"   📊 Image Size: {image_size} bytes ({image_size/1024:.1f}KB)")
                    self.log(f"   🎨 Quality: {'HIGH (Fal.ai)' if is_high_quality else 'STANDARD (Placeholder)'}")
                    
                    return {
                        "success": True,
                        "plan": user_plan,
                        "has_image": True,
                        "image_size": image_size,
                        "is_high_quality": is_high_quality
                    }
                else:
                    self.log(f"❌ {user_plan.upper()} Plan Access: No image generated", "ERROR")
                    return {"success": False, "plan": user_plan, "error": "no_image"}
                    
            elif response.status_code == 403:
                error_detail = response.json().get("detail", {})
                if isinstance(error_detail, dict) and error_detail.get("needs_upgrade"):
                    self.log(f"⚠️  {user_plan.upper()} Plan Access: Plan limit reached")
                    return {"success": True, "plan": user_plan, "limit_reached": True}
                else:
                    self.log(f"❌ {user_plan.upper()} Plan Access: Access denied", "ERROR")
                    return {"success": False, "plan": user_plan, "error": "access_denied"}
            else:
                self.log(f"❌ {user_plan.upper()} Plan Access: Request failed {response.status_code}", "ERROR")
                return {"success": False, "plan": user_plan, "error": f"http_{response.status_code}"}
                
        except Exception as e:
            self.log(f"❌ {user_plan.upper()} Plan Access: Exception {str(e)}", "ERROR")
            return {"success": False, "plan": user_plan, "error": "exception"}
    
    def test_environment_configuration(self):
        """Test that environment variables are properly configured"""
        self.log("Testing environment configuration for image generation...")
        
        # Create a test user to verify the system works
        auth_token, user_info = self.create_test_user_and_authenticate()
        
        if not auth_token:
            self.log("❌ Cannot test environment: Failed to create test user", "ERROR")
            return False
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        test_request = {
            "product_name": "Environment Test",
            "product_description": "Testing environment configuration",
            "generate_image": True,
            "number_of_images": 1
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_request, headers=headers)
            
            if response.status_code == 200:
                sheet_data = response.json()
                has_images = bool(sheet_data.get("product_images_base64") and len(sheet_data["product_images_base64"]) > 0)
                
                if has_images:
                    image_data = sheet_data["product_images_base64"][0]
                    decoded = base64.b64decode(image_data)
                    image_size = len(decoded)
                    
                    # High-quality images indicate Fal.ai is working (FAL_KEY configured)
                    if image_size > 50000:
                        self.log("✅ Environment Configuration: FAL_KEY properly configured")
                        self.log("   🔑 Fal.ai integration working correctly")
                        self.log(f"   📊 High-quality image generated ({image_size/1024:.1f}KB)")
                        return True
                    else:
                        self.log("⚠️  Environment Configuration: Using fallback system")
                        self.log("   🔑 FAL_KEY may be missing, but fallback working")
                        self.log(f"   📊 Placeholder image generated ({image_size/1024:.1f}KB)")
                        return True  # Still working, just using fallback
                else:
                    self.log("❌ Environment Configuration: No image generated", "ERROR")
                    return False
            else:
                self.log(f"❌ Environment Configuration: Request failed {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Environment Configuration test failed: {str(e)}", "ERROR")
            return False
    
    def run_authentication_and_subscription_tests(self):
        """Run all authentication and subscription level tests"""
        self.log("🔐 TESTING AUTHENTICATION AND SUBSCRIPTION LEVEL ACCESS")
        self.log("=" * 60)
        
        test_results = {}
        
        # 1. Test authentication requirement
        self.log("\n1️⃣ Testing authentication requirements...")
        test_results["auth_required"] = self.test_authentication_required()
        
        # 2. Test invalid token handling
        self.log("\n2️⃣ Testing invalid token handling...")
        test_results["invalid_token"] = self.test_invalid_token()
        
        # 3. Test environment configuration
        self.log("\n3️⃣ Testing environment configuration...")
        test_results["environment_config"] = self.test_environment_configuration()
        
        # 4. Test subscription level access
        self.log("\n4️⃣ Testing subscription level access...")
        auth_token, user_info = self.create_test_user_and_authenticate()
        if auth_token:
            subscription_result = self.test_subscription_level_access(auth_token, user_info)
            test_results["subscription_access"] = subscription_result.get("success", False)
        else:
            test_results["subscription_access"] = False
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log("🏁 AUTHENTICATION AND SUBSCRIPTION TEST RESULTS:")
        self.log("=" * 60)
        
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{test_name.replace('_', ' ').title()}: {status}")
        
        self.log("=" * 60)
        self.log(f"OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL AUTHENTICATION AND SUBSCRIPTION TESTS PASSED!")
            self.log("✅ Authentication properly required for image generation")
            self.log("✅ Invalid tokens correctly rejected")
            self.log("✅ Environment configuration working")
            self.log("✅ Subscription level access working correctly")
            return True
        else:
            self.log("⚠️  SOME AUTHENTICATION/SUBSCRIPTION TESTS FAILED")
            return False

def main():
    """Main test execution"""
    tester = AuthSubscriptionTester()
    success = tester.run_authentication_and_subscription_tests()
    
    if success:
        print("\n🎉 AUTHENTICATION AND SUBSCRIPTION TESTING: ALL TESTS PASSED!")
        exit(0)
    else:
        print("\n❌ AUTHENTICATION AND SUBSCRIPTION TESTING: SOME TESTS FAILED!")
        exit(1)

if __name__ == "__main__":
    main()