#!/usr/bin/env python3
"""
CRITICAL BUG TEST: Product Sheet Generation Failure
Focus: Testing the exact issue reported - product sheet generation completely broken after GPT-4 Turbo modifications

CRITICAL ISSUE REPORTED:
- User reports that product sheet generation is not working at all
- No sheets are being generated after GPT-4 Turbo modifications
- Need to test /api/generate-sheet endpoint specifically
- Need to identify exact error causing complete failure
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 60  # Increased timeout for generation

class CriticalSheetGenerationTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        self.user_data = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_api_health(self):
        """Test if the API is accessible"""
        self.log("🔍 Testing API health check...")
        try:
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ API Health Check: {data.get('message', 'OK')}")
                return True
            else:
                self.log(f"❌ API Health Check failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ API Health Check failed: {str(e)}", "ERROR")
            return False
    
    def create_test_user(self):
        """Create a test user for sheet generation"""
        self.log("👤 Creating test user...")
        
        timestamp = int(time.time())
        test_user = {
            "email": f"test.generation{timestamp}@example.com",
            "name": "Test Generation User",
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
                    self.log(f"   User ID: {self.user_data['id']}")
                    self.log(f"   Subscription: {self.user_data.get('subscription_plan', 'gratuit')}")
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
    
    def test_critical_sheet_generation(self):
        """🚨 CRITICAL TEST: Test the exact product sheet generation issue"""
        self.log("🚨 CRITICAL TEST: Testing product sheet generation...")
        
        if not self.auth_token:
            self.log("❌ Cannot test sheet generation: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test with a simple product first
        test_data = {
            "product_name": "iPhone 15",
            "product_description": "Smartphone Apple dernière génération",
            "generate_image": False,  # Start without image to isolate the issue
            "number_of_images": 0,
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
            
            # Log response headers for debugging
            self.log(f"📋 Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                self.log(f"❌ CRITICAL FAILURE: API call failed with status {response.status_code}", "ERROR")
                self.log(f"❌ Response text: {response.text}", "ERROR")
                
                # Try to parse error details
                try:
                    error_data = response.json()
                    self.log(f"❌ Error details: {json.dumps(error_data, indent=2)}", "ERROR")
                except:
                    self.log("❌ Could not parse error response as JSON", "ERROR")
                
                return False
                
            # Parse response
            try:
                data = response.json()
                self.log(f"📄 Response data keys: {list(data.keys())}")
                
                # Check if generation was successful
                if not data.get("success", False):
                    self.log(f"❌ CRITICAL FAILURE: Generation failed - {data.get('message', 'Unknown error')}", "ERROR")
                    self.log(f"❌ Full response: {json.dumps(data, indent=2)}", "ERROR")
                    return False
                
                # Check if sheet data exists
                sheet_data = data.get("sheet")
                if not sheet_data:
                    self.log("❌ CRITICAL FAILURE: No sheet data in response", "ERROR")
                    self.log(f"❌ Full response: {json.dumps(data, indent=2)}", "ERROR")
                    return False
                
                # Validate sheet structure
                required_fields = [
                    "id", "user_id", "product_name", "original_description",
                    "generated_title", "marketing_description", "key_features",
                    "seo_tags", "price_suggestions", "target_audience", "call_to_action"
                ]
                
                missing_fields = [field for field in required_fields if field not in sheet_data]
                if missing_fields:
                    self.log(f"❌ CRITICAL FAILURE: Missing required fields: {missing_fields}", "ERROR")
                    self.log(f"❌ Available fields: {list(sheet_data.keys())}", "ERROR")
                    return False
                
                # Log successful generation details
                self.log("✅ CRITICAL SUCCESS: Product sheet generated successfully!")
                self.log(f"   Sheet ID: {sheet_data['id']}")
                self.log(f"   Product Name: {sheet_data['product_name']}")
                self.log(f"   Generated Title: {sheet_data['generated_title']}")
                self.log(f"   Marketing Description Length: {len(sheet_data['marketing_description'])} chars")
                self.log(f"   Key Features Count: {len(sheet_data['key_features'])}")
                self.log(f"   SEO Tags Count: {len(sheet_data['seo_tags'])}")
                self.log(f"   AI Generated: {sheet_data.get('is_ai_generated', 'Unknown')}")
                self.log(f"   Generation Time: {sheet_data.get('generation_time', 'Unknown')} seconds")
                
                # Log sample content for verification
                self.log("📋 Generated Content Sample:")
                self.log(f"   Title: {sheet_data['generated_title']}")
                self.log(f"   Description: {sheet_data['marketing_description'][:200]}...")
                self.log(f"   Features: {', '.join(sheet_data['key_features'][:3])}...")
                self.log(f"   SEO Tags: {', '.join(sheet_data['seo_tags'])}")
                self.log(f"   Price: {sheet_data['price_suggestions']}")
                self.log(f"   Target Audience: {sheet_data['target_audience'][:100]}...")
                self.log(f"   CTA: {sheet_data['call_to_action']}")
                
                return True
                
            except json.JSONDecodeError as e:
                self.log(f"❌ CRITICAL FAILURE: Could not parse response JSON: {str(e)}", "ERROR")
                self.log(f"❌ Raw response: {response.text[:500]}...", "ERROR")
                return False
                
        except requests.exceptions.Timeout:
            self.log("❌ CRITICAL FAILURE: Request timed out", "ERROR")
            return False
        except requests.exceptions.ConnectionError as e:
            self.log(f"❌ CRITICAL FAILURE: Connection error: {str(e)}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ CRITICAL FAILURE: Unexpected error: {str(e)}", "ERROR")
            import traceback
            self.log(f"❌ Traceback: {traceback.format_exc()}", "ERROR")
            return False
    
    def test_with_image_generation(self):
        """Test sheet generation WITH image generation"""
        self.log("🖼️ Testing sheet generation WITH image generation...")
        
        if not self.auth_token:
            self.log("❌ Cannot test with image: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        test_data = {
            "product_name": "MacBook Pro",
            "product_description": "Ordinateur portable professionnel Apple",
            "generate_image": True,
            "number_of_images": 1,
            "language": "fr"
        }
        
        try:
            self.log("🔄 Making API call with image generation...")
            start_time = time.time()
            
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.log(f"⏱️ API call with image completed in {duration:.2f} seconds")
            
            if response.status_code != 200:
                self.log(f"❌ Image generation test failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
            data = response.json()
            
            if not data.get("success", False):
                self.log(f"❌ Image generation failed: {data.get('message', 'Unknown error')}", "ERROR")
                return False
            
            sheet_data = data.get("sheet", {})
            
            # Check for image data
            has_image = bool(sheet_data.get("product_image_base64") or 
                           (sheet_data.get("product_images_base64") and len(sheet_data["product_images_base64"]) > 0))
            
            if has_image:
                self.log("✅ Image generation successful!")
                image_data = sheet_data.get("product_image_base64") or sheet_data.get("product_images_base64", [None])[0]
                if image_data:
                    self.log(f"   Image data length: {len(image_data)} characters")
                    # Validate base64 format
                    try:
                        import base64
                        decoded = base64.b64decode(image_data)
                        self.log(f"   Decoded image size: {len(decoded)} bytes")
                    except Exception as e:
                        self.log(f"   ⚠️ Image data validation failed: {str(e)}")
            else:
                self.log("⚠️ No image generated (may be using fallback system)")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Image generation test failed: {str(e)}", "ERROR")
            return False
    
    def test_different_products(self):
        """Test generation with different product types"""
        self.log("🔄 Testing generation with different product types...")
        
        if not self.auth_token:
            self.log("❌ Cannot test different products: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        test_products = [
            ("Papier toilette", "Papier toilette doux et résistant"),
            ("Smartphone Samsung", "Téléphone Android dernière génération"),
            ("Chaussures Nike", "Baskets de sport pour running"),
            ("Livre de cuisine", "Recettes françaises traditionnelles")
        ]
        
        success_count = 0
        
        for product_name, description in test_products:
            self.log(f"🧪 Testing: {product_name}")
            
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
                    if data.get("success", False):
                        sheet_data = data.get("sheet", {})
                        self.log(f"   ✅ {product_name}: Generated successfully")
                        self.log(f"      Title: {sheet_data.get('generated_title', 'N/A')[:50]}...")
                        success_count += 1
                    else:
                        self.log(f"   ❌ {product_name}: Generation failed - {data.get('message', 'Unknown')}")
                else:
                    self.log(f"   ❌ {product_name}: API call failed - {response.status_code}")
                    
            except Exception as e:
                self.log(f"   ❌ {product_name}: Exception - {str(e)}")
            
            time.sleep(1)  # Brief pause between requests
        
        self.log(f"📊 Product variety test: {success_count}/{len(test_products)} successful")
        return success_count == len(test_products)
    
    def run_critical_tests(self):
        """Run all critical tests to diagnose the issue"""
        self.log("🚨 STARTING CRITICAL PRODUCT SHEET GENERATION DIAGNOSTIC")
        self.log("=" * 80)
        
        tests = [
            ("API Health Check", self.test_api_health),
            ("User Creation", self.create_test_user),
            ("Critical Sheet Generation", self.test_critical_sheet_generation),
            ("Sheet Generation with Image", self.test_with_image_generation),
            ("Different Product Types", self.test_different_products)
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
        self.log("🚨 CRITICAL DIAGNOSTIC SUMMARY")
        self.log("=" * 80)
        
        passed = sum(1 for _, result, _ in results if result)
        total = len(results)
        
        for test_name, result, status in results:
            self.log(f"{status} {test_name}")
        
        self.log(f"\n📊 Overall Result: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("✅ CONCLUSION: Product sheet generation is WORKING correctly")
            self.log("   The reported issue may have been resolved or was intermittent")
        elif passed == 0:
            self.log("❌ CONCLUSION: Product sheet generation is COMPLETELY BROKEN")
            self.log("   This confirms the critical issue reported by the user")
        else:
            self.log("⚠️ CONCLUSION: Product sheet generation has PARTIAL ISSUES")
            self.log("   Some functionality works, but there are specific problems")
        
        return passed, total

def main():
    """Main test execution"""
    tester = CriticalSheetGenerationTester()
    passed, total = tester.run_critical_tests()
    
    # Exit with appropriate code
    if passed == total:
        exit(0)  # All tests passed
    else:
        exit(1)  # Some tests failed

if __name__ == "__main__":
    main()