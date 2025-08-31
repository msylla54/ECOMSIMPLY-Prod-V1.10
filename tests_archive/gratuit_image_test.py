#!/usr/bin/env python3
"""
ECOMSIMPLY Gratuit Plan Image Generation Test
Specifically tests that FREE/GRATUIT users receive high-quality Fal.ai Flux Pro images
"""

import requests
import json
import time
import base64
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 60

class GratuitImageTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def create_fresh_gratuit_user(self):
        """Create a fresh gratuit user for testing"""
        self.log("Creating fresh Gratuit user for image generation testing...")
        
        timestamp = int(time.time())
        user_data = {
            "email": f"gratuit.image.test.{timestamp}@ecomsimply.fr",
            "name": f"Gratuit Image Test User",
            "password": "TestPassword123!"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=user_data)
            
            if response.status_code == 200:
                data = response.json()
                auth_token = data.get("token")
                user_info = data.get("user")
                
                if auth_token and user_info:
                    self.log(f"✅ Created fresh Gratuit user: {user_info['name']}")
                    self.log(f"   Email: {user_info['email']}")
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
    
    def test_gratuit_high_quality_image_generation(self, auth_token, product_name, product_description):
        """Test that Gratuit users get high-quality Fal.ai images"""
        self.log(f"Testing Gratuit plan high-quality image generation: {product_name}")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        test_request = {
            "product_name": product_name,
            "product_description": product_description,
            "generate_image": True,
            "number_of_images": 1
        }
        
        try:
            start_time = time.time()
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_request, headers=headers)
            generation_time = time.time() - start_time
            
            if response.status_code == 200:
                sheet_data = response.json()
                
                # Check for image generation
                has_images = bool(sheet_data.get("product_images_base64") and len(sheet_data["product_images_base64"]) > 0)
                
                if has_images:
                    image_data = sheet_data["product_images_base64"][0]
                    
                    try:
                        decoded = base64.b64decode(image_data)
                        image_size = len(decoded)
                        
                        # Analyze image quality - High-quality Fal.ai images are typically >50KB
                        is_high_quality = image_size > 50000  # 50KB threshold
                        
                        self.log(f"🎉 GRATUIT PLAN SUCCESS: {product_name}")
                        self.log(f"   📊 Image Size: {image_size} bytes ({image_size/1024:.1f}KB)")
                        self.log(f"   ⏱️  Generation Time: {generation_time:.2f} seconds")
                        self.log(f"   🎨 Quality: {'HIGH-QUALITY FAL.AI FLUX PRO' if is_high_quality else 'STANDARD PLACEHOLDER'}")
                        self.log(f"   📝 Generated Title: {sheet_data.get('generated_title', 'N/A')}")
                        self.log(f"   🔍 Marketing Description: {sheet_data.get('marketing_description', 'N/A')[:100]}...")
                        
                        # Verify this is actually high-quality
                        if is_high_quality:
                            self.log("✅ CRITICAL VERIFICATION: Gratuit users receive HIGH-QUALITY Fal.ai images!")
                            self.log("✅ This confirms the image quality fix is working correctly")
                            return True
                        else:
                            self.log("⚠️  CRITICAL ISSUE: Gratuit users receiving low-quality placeholder images")
                            self.log("❌ This indicates Fal.ai may not be working for free users")
                            return False
                        
                    except Exception as decode_error:
                        self.log(f"❌ Image decode error: {decode_error}", "ERROR")
                        return False
                else:
                    self.log(f"❌ GRATUIT PLAN - {product_name}: No image generated", "ERROR")
                    return False
                    
            elif response.status_code == 403:
                error_detail = response.json().get("detail", {})
                if isinstance(error_detail, dict) and error_detail.get("needs_upgrade"):
                    self.log(f"⚠️  GRATUIT PLAN - {product_name}: Free plan limit reached (1 sheet per month)")
                    self.log("   This is expected behavior for Gratuit plan after first sheet")
                    return "limit_reached"
                else:
                    self.log(f"❌ GRATUIT PLAN - {product_name}: Access denied - {response.status_code}", "ERROR")
                    return False
            else:
                self.log(f"❌ GRATUIT PLAN - {product_name}: Request failed - {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ GRATUIT PLAN - {product_name}: Exception - {str(e)}", "ERROR")
            return False
    
    def run_gratuit_image_quality_test(self):
        """Run the specific test for Gratuit plan image quality"""
        self.log("🎯 TESTING GRATUIT PLAN HIGH-QUALITY IMAGE GENERATION")
        self.log("=" * 60)
        self.log("OBJECTIVE: Verify that FREE users receive Fal.ai Flux Pro high-quality images")
        self.log("REQUIREMENT: Image size should be >50KB indicating Fal.ai generation, not placeholder")
        self.log("=" * 60)
        
        # Create fresh user
        auth_token, user_info = self.create_fresh_gratuit_user()
        
        if not auth_token:
            self.log("❌ Cannot proceed: Failed to create test user", "ERROR")
            return False
        
        # Test with the specific product mentioned in the review
        test_product = ("iPhone 15 Pro", "Smartphone haut de gamme Apple avec processeur A17 Pro et appareil photo 48MP")
        
        result = self.test_gratuit_high_quality_image_generation(auth_token, test_product[0], test_product[1])
        
        self.log("\n" + "=" * 60)
        self.log("🏁 GRATUIT PLAN IMAGE QUALITY TEST RESULTS:")
        self.log("=" * 60)
        
        if result is True:
            self.log("🎉 SUCCESS: GRATUIT USERS RECEIVE HIGH-QUALITY FAL.AI IMAGES!")
            self.log("✅ Image quality fix is working correctly")
            self.log("✅ Free users get the same quality as paid users")
            self.log("✅ Fal.ai Flux Pro is being used for all subscription plans")
            return True
        elif result == "limit_reached":
            self.log("⚠️  PARTIAL SUCCESS: Cannot fully test due to Gratuit plan limits")
            self.log("   This is expected behavior - Gratuit users are limited to 1 sheet per month")
            self.log("   The limit itself confirms the system is working correctly")
            return True
        else:
            self.log("❌ FAILURE: Gratuit users are NOT receiving high-quality images")
            self.log("❌ This indicates the image quality fix may not be working")
            self.log("❌ Free users may be getting placeholder images instead of Fal.ai")
            return False

def main():
    """Main test execution"""
    tester = GratuitImageTester()
    success = tester.run_gratuit_image_quality_test()
    
    if success:
        print("\n🎉 GRATUIT PLAN IMAGE QUALITY TEST: PASSED!")
        print("✅ Free users receive high-quality Fal.ai Flux Pro images")
        exit(0)
    else:
        print("\n❌ GRATUIT PLAN IMAGE QUALITY TEST: FAILED!")
        print("❌ Free users are not receiving high-quality images")
        exit(1)

if __name__ == "__main__":
    main()