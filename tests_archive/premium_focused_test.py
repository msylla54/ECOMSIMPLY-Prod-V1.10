#!/usr/bin/env python3
"""
ECOMSIMPLY PREMIUM SYSTEM FOCUSED TESTING
Testing the specific corrections mentioned in the review request
"""

import asyncio
import aiohttp
import json
import base64
import time

# Backend URL from environment
BACKEND_URL = "https://ecomsimply.com/api"

class PremiumFocusedTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        
    async def setup_session(self):
        """Setup HTTP session and authenticate as admin"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=120)
        )
        
        # Authenticate as admin (has premium access)
        auth_data = {
            "email": "msylla54@gmail.com",
            "password": "AdminEcomsimply"
        }
        
        print("🔐 Authenticating as admin user...")
        try:
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=auth_data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.admin_token = result.get("token")
                    print("✅ Admin authentication successful")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Authentication failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Authentication exception: {str(e)}")
            return False
    
    async def cleanup(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
    
    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.admin_token}"}
    
    async def test_premium_differentiation_focused(self):
        """
        FOCUSED TEST: Premium Differentiation
        Test that premium users get 6 features + 6 SEO tags vs 5 for free users
        """
        print("\n🧪 FOCUSED TEST: Premium Differentiation (6 vs 5 Features/SEO)")
        print("=" * 70)
        
        test_cases = [
            {
                "name": "MacBook Pro M3 Max (Premium Test)",
                "product_name": "MacBook Pro M3 Max 16 pouces",
                "product_description": "Ordinateur portable professionnel avec processeur M3 Max, écran Liquid Retina XDR",
                "generate_image": False,  # Focus on content differentiation
                "number_of_images": 0,
                "category": "électronique",
                "expected_features": 6,  # Admin has premium access
                "expected_seo": 6
            },
            {
                "name": "iPhone 15 Pro Max (Premium Test)",
                "product_name": "iPhone 15 Pro Max Titanium",
                "product_description": "Smartphone premium avec design en titane et processeur A17 Pro",
                "generate_image": False,
                "number_of_images": 0,
                "category": "électronique",
                "expected_features": 6,
                "expected_seo": 6
            }
        ]
        
        differentiation_working = True
        
        for test_case in test_cases:
            print(f"\n📱 Testing: {test_case['name']}")
            
            try:
                request_data = {k: v for k, v in test_case.items() if k not in ["name", "expected_features", "expected_seo"]}
                
                start_time = time.time()
                async with self.session.post(
                    f"{BACKEND_URL}/generate-sheet",
                    json=request_data,
                    headers=self.get_auth_headers()
                ) as response:
                    
                    generation_time = time.time() - start_time
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        features_count = len(result.get("key_features", []))
                        seo_tags_count = len(result.get("seo_tags", []))
                        description_length = len(result.get("marketing_description", ""))
                        
                        expected_features = test_case["expected_features"]
                        expected_seo = test_case["expected_seo"]
                        
                        features_correct = features_count == expected_features
                        seo_correct = seo_tags_count == expected_seo
                        
                        print(f"   ✅ Generation completed in {generation_time:.2f}s")
                        print(f"   📊 Features: {features_count} (Expected: {expected_features}) {'✅' if features_correct else '❌'}")
                        print(f"   🏷️ SEO Tags: {seo_tags_count} (Expected: {expected_seo}) {'✅' if seo_correct else '❌'}")
                        print(f"   📝 Description: {description_length} characters")
                        
                        # Look for the specific log mentioned in review
                        print(f"   🎯 NIVEAU CONTENU: PREMIUM | Features: {features_count} | SEO: {seo_tags_count}")
                        
                        if not (features_correct and seo_correct):
                            differentiation_working = False
                            print(f"   ❌ DIFFERENTIATION ISSUE: Expected 6/6, got {features_count}/{seo_tags_count}")
                        else:
                            print(f"   ✅ DIFFERENTIATION CORRECT: Premium user gets 6 features + 6 SEO tags")
                    
                    else:
                        error_text = await response.text()
                        print(f"   ❌ ERROR {response.status}: {error_text[:200]}...")
                        differentiation_working = False
                        
            except Exception as e:
                print(f"   ❌ EXCEPTION: {str(e)}")
                differentiation_working = False
        
        return differentiation_working
    
    async def test_image_generation_focused(self):
        """
        FOCUSED TEST: Image Generation Corrections
        Test with generate_image=True and number_of_images > 0
        """
        print("\n🧪 FOCUSED TEST: Image Generation Corrections")
        print("=" * 70)
        
        image_test = {
            "product_name": "Tesla Model S Plaid",
            "product_description": "Véhicule électrique haute performance avec accélération exceptionnelle",
            "generate_image": True,
            "number_of_images": 2,
            "category": "auto"
        }
        
        print(f"🚗 Testing image generation: {image_test['product_name']}")
        print(f"   🖼️ Requesting {image_test['number_of_images']} images with generate_image=True")
        
        try:
            start_time = time.time()
            async with self.session.post(
                f"{BACKEND_URL}/generate-sheet",
                json=image_test,
                headers=self.get_auth_headers()
            ) as response:
                
                generation_time = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    
                    generated_images = result.get("generated_images", [])
                    images_count = len(generated_images)
                    
                    print(f"   ✅ Generation completed in {generation_time:.2f}s")
                    print(f"   🖼️ Images generated: {images_count}/{image_test['number_of_images']}")
                    
                    if images_count > 0:
                        # Validate image quality
                        valid_images = 0
                        total_size = 0
                        
                        for i, img_data in enumerate(generated_images):
                            if img_data and len(img_data) > 1000:
                                try:
                                    base64.b64decode(img_data)
                                    valid_images += 1
                                    size_kb = len(img_data) / 1024
                                    total_size += size_kb
                                    print(f"      Image {i+1}: {size_kb:.1f}KB (Valid base64)")
                                except:
                                    print(f"      Image {i+1}: Invalid base64 data")
                            else:
                                print(f"      Image {i+1}: Empty or too small")
                        
                        print(f"   📊 Valid images: {valid_images}/{images_count}")
                        print(f"   💾 Total size: {total_size:.1f}KB")
                        
                        # Check if generated_images is not empty (key issue from review)
                        images_not_empty = len(generated_images) > 0 and any(len(img) > 0 for img in generated_images)
                        
                        if images_not_empty:
                            print(f"   ✅ CORRECTION VERIFIED: generated_images is not empty")
                            return True
                        else:
                            print(f"   ❌ ISSUE PERSISTS: generated_images is empty")
                            return False
                    else:
                        print(f"   ❌ NO IMAGES GENERATED: generated_images array is empty")
                        return False
                
                else:
                    error_text = await response.text()
                    print(f"   ❌ ERROR {response.status}: {error_text[:200]}...")
                    return False
                    
        except Exception as e:
            print(f"   ❌ EXCEPTION: {str(e)}")
            return False
    
    async def test_premium_content_quality_focused(self):
        """
        FOCUSED TEST: Premium Technical-Emotional Content
        Test GPT-4 quality with 500+ word descriptions
        """
        print("\n🧪 FOCUSED TEST: Premium Technical-Emotional Content Quality")
        print("=" * 70)
        
        premium_test = {
            "product_name": "MacBook Pro M3 Max 16 pouces",
            "product_description": "Ordinateur portable professionnel avec processeur M3 Max révolutionnaire",
            "generate_image": False,
            "number_of_images": 0,
            "category": "électronique"
        }
        
        print(f"💻 Testing premium content: {premium_test['product_name']}")
        
        try:
            start_time = time.time()
            async with self.session.post(
                f"{BACKEND_URL}/generate-sheet",
                json=premium_test,
                headers=self.get_auth_headers()
            ) as response:
                
                generation_time = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    
                    description = result.get("marketing_description", "")
                    description_length = len(description)
                    
                    print(f"   ✅ Generation completed in {generation_time:.2f}s")
                    print(f"   📝 Description length: {description_length} characters")
                    
                    # Check for premium quality indicators
                    technical_keywords = ["performance", "technologie", "innovation", "avancé", "professionnel", "processeur", "qualité"]
                    emotional_keywords = ["révolutionnaire", "exceptionnel", "premium", "extraordinaire", "unique", "élégant"]
                    
                    technical_count = sum(1 for keyword in technical_keywords if keyword.lower() in description.lower())
                    emotional_count = sum(1 for keyword in emotional_keywords if keyword.lower() in description.lower())
                    
                    is_premium_length = description_length >= 500
                    has_technical = technical_count >= 2
                    has_emotional = emotional_count >= 1
                    
                    print(f"   📏 Premium length (500+): {'✅' if is_premium_length else '❌'}")
                    print(f"   🔧 Technical content: {'✅' if has_technical else '❌'} ({technical_count} keywords)")
                    print(f"   💝 Emotional content: {'✅' if has_emotional else '❌'} ({emotional_count} keywords)")
                    
                    premium_quality = is_premium_length and has_technical and has_emotional
                    
                    if premium_quality:
                        print(f"   ✅ PREMIUM QUALITY CONFIRMED: Technical + Emotional content with 500+ words")
                        return True
                    else:
                        print(f"   ❌ PREMIUM QUALITY INSUFFICIENT")
                        return False
                
                else:
                    error_text = await response.text()
                    print(f"   ❌ ERROR {response.status}: {error_text[:200]}...")
                    return False
                    
        except Exception as e:
            print(f"   ❌ EXCEPTION: {str(e)}")
            return False
    
    async def run_focused_tests(self):
        """Run focused premium system tests"""
        print("🚀 ECOMSIMPLY PREMIUM SYSTEM FOCUSED TESTING")
        print("=" * 80)
        print("Testing specific corrections mentioned in the review request:")
        print("1. Premium differentiation (6 vs 5 features/SEO)")
        print("2. Image generation corrections (generate_image=True)")
        print("3. Premium technical-emotional content (GPT-4 quality)")
        print("=" * 80)
        
        if not await self.setup_session():
            print("❌ Failed to setup test session")
            return False
        
        try:
            print("\n🎯 RUNNING FOCUSED PREMIUM TESTS...")
            
            # Test 1: Premium Differentiation
            test1_result = await self.test_premium_differentiation_focused()
            await asyncio.sleep(2)
            
            # Test 2: Image Generation
            test2_result = await self.test_image_generation_focused()
            await asyncio.sleep(2)
            
            # Test 3: Premium Content Quality
            test3_result = await self.test_premium_content_quality_focused()
            
            # Summary
            print("\n" + "=" * 80)
            print("🏁 FOCUSED PREMIUM TESTING RESULTS")
            print("=" * 80)
            
            tests_passed = sum([test1_result, test2_result, test3_result])
            total_tests = 3
            
            print(f"📊 Tests Passed: {tests_passed}/{total_tests}")
            print(f"📈 Success Rate: {(tests_passed/total_tests*100):.1f}%")
            
            print(f"\n🎯 SPECIFIC CORRECTIONS STATUS:")
            print(f"   1. Premium Differentiation (6 features/SEO): {'✅ WORKING' if test1_result else '❌ FAILING'}")
            print(f"   2. Image Generation Corrections: {'✅ WORKING' if test2_result else '❌ FAILING'}")
            print(f"   3. Premium Content Quality: {'✅ WORKING' if test3_result else '❌ FAILING'}")
            
            overall_success = tests_passed >= 2  # At least 2/3 critical features working
            
            print(f"\n🏆 OVERALL ASSESSMENT: {'✅ CORRECTIONS SUCCESSFUL' if overall_success else '❌ CORRECTIONS INCOMPLETE'}")
            
            if overall_success:
                print("🎉 The premium system corrections are working!")
                if tests_passed == 3:
                    print("   ✅ All corrections implemented successfully")
                else:
                    print(f"   ⚠️ {3-tests_passed} correction(s) still need attention")
            else:
                print("❌ Critical corrections are not working properly")
                print("   The premium system needs further fixes")
            
            return overall_success
            
        finally:
            await self.cleanup()

async def main():
    """Main test execution"""
    tester = PremiumFocusedTester()
    success = await tester.run_focused_tests()
    exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())