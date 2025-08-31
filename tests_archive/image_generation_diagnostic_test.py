#!/usr/bin/env python3
"""
ECOMSIMPLY IMAGE GENERATION DIAGNOSTIC TEST
==========================================

URGENT MISSION: Diagnose the exact root cause of the image display issue
reported in the review request:

PROBLEM IDENTIFIED:
- ✅ Backend generates images perfectly (5/5 success in logs)  
- ❌ Frontend doesn't display them ("Images en cours de génération..." stays stuck)

SPECIFIC TESTS:
1. Test with "Philips Série 7000" (exact user case)
2. Examine exact JSON response structure
3. Verify base64 image data format
4. Check if generated_images array contains data
5. Validate frontend compatibility

This test will provide the exact diagnosis needed for the main agent.
"""

import asyncio
import aiohttp
import json
import base64
import time
import sys
import os
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://ecomsimply.com/api"

class ImageGenerationDiagnostic:
    def __init__(self):
        self.session = None
        self.auth_token = None
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    async def authenticate_admin(self) -> bool:
        """Authenticate with admin credentials"""
        try:
            print("🔐 Authenticating with admin credentials...")
            
            login_data = {
                "email": "msylla54@gmail.com", 
                "password": "AdminEcomsimply"
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("token")
                    print(f"✅ Admin authentication successful")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Admin authentication failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
            
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }

    async def test_philips_serie_7000_case(self):
        """Test the exact user case: Philips Série 7000"""
        print("\n🎯 DIAGNOSTIC TEST: Philips Série 7000 (Exact User Case)")
        print("=" * 70)
        
        # Exact test case from user report
        request_data = {
            "product_name": "Philips Série 7000",
            "product_description": "Rasoir électrique premium avec technologie de coupe avancée",
            "generate_image": True,
            "number_of_images": 1,
            "language": "fr"
        }
        
        print(f"📤 Sending request to /api/generate-sheet")
        print(f"   Product: {request_data['product_name']}")
        print(f"   Description: {request_data['product_description']}")
        print(f"   Generate Image: {request_data['generate_image']}")
        print(f"   Number of Images: {request_data['number_of_images']}")
        print(f"   Language: {request_data['language']}")
        
        start_time = time.time()
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/generate-sheet",
                json=request_data,
                headers=self.get_auth_headers()
            ) as response:
                
                end_time = time.time()
                generation_time = end_time - start_time
                
                print(f"\n📥 RESPONSE ANALYSIS")
                print(f"   Status Code: {response.status}")
                print(f"   Generation Time: {generation_time:.2f} seconds")
                
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"\n🔍 JSON RESPONSE STRUCTURE ANALYSIS:")
                    print(f"   Response Keys: {list(data.keys())}")
                    
                    # Check each key in detail
                    for key, value in data.items():
                        if key == "generated_images":
                            print(f"   📸 {key}: {type(value)} with {len(value) if isinstance(value, list) else 'N/A'} items")
                            if isinstance(value, list) and len(value) > 0:
                                first_image = value[0]
                                if isinstance(first_image, str):
                                    print(f"      - Image 1 Type: string")
                                    print(f"      - Image 1 Length: {len(first_image)} characters")
                                    print(f"      - Image 1 Size: {len(first_image) / 1024:.1f}KB")
                                    
                                    # Test base64 validity
                                    try:
                                        decoded = base64.b64decode(first_image)
                                        print(f"      - Base64 Valid: ✅ YES")
                                        print(f"      - Decoded Size: {len(decoded)} bytes")
                                        
                                        # Check if it looks like image data
                                        if len(decoded) > 1000:  # Substantial image data
                                            print(f"      - Image Data Quality: ✅ SUBSTANTIAL ({len(decoded)} bytes)")
                                        else:
                                            print(f"      - Image Data Quality: ⚠️ SMALL ({len(decoded)} bytes)")
                                            
                                    except Exception as e:
                                        print(f"      - Base64 Valid: ❌ NO - {e}")
                                else:
                                    print(f"      - Image 1 Type: {type(first_image)} (NOT STRING)")
                            else:
                                print(f"      - ❌ CRITICAL: generated_images is empty!")
                                print(f"      - This confirms the frontend issue!")
                        elif key == "generation_time":
                            print(f"   ⏱️ {key}: {value} seconds")
                        elif isinstance(value, str):
                            preview = value[:100] + "..." if len(value) > 100 else value
                            print(f"   📝 {key}: {preview}")
                        elif isinstance(value, list):
                            print(f"   📋 {key}: {type(value)} with {len(value)} items")
                        else:
                            print(f"   🔧 {key}: {type(value)} = {value}")
                    
                    # CRITICAL DIAGNOSIS
                    print(f"\n🚨 CRITICAL DIAGNOSIS:")
                    generated_images = data.get("generated_images", [])
                    
                    if len(generated_images) == 0:
                        print(f"   ❌ ROOT CAUSE CONFIRMED: generated_images array is EMPTY")
                        print(f"   ❌ This explains why frontend shows 'Images en cours de génération...'")
                        print(f"   ❌ Backend is NOT calling FAL.ai image generation functions")
                        print(f"   🔧 SOLUTION NEEDED: Fix /api/generate-sheet endpoint to call image generation")
                    elif len(generated_images) > 0:
                        first_image = generated_images[0]
                        if isinstance(first_image, str) and len(first_image) > 1000:
                            print(f"   ✅ IMAGES GENERATED: Backend is working correctly!")
                            print(f"   ✅ Image data present and substantial")
                            print(f"   🔍 Frontend issue may be in parsing or display logic")
                        else:
                            print(f"   ⚠️ IMAGES PRESENT BUT SUSPICIOUS: Data too small or wrong format")
                            print(f"   🔍 May be placeholder or fallback data")
                    
                    # Check text generation
                    if data.get("generated_title"):
                        print(f"   ✅ TEXT GENERATION: Working correctly")
                        print(f"      Title: {data.get('generated_title', '')[:50]}...")
                    else:
                        print(f"   ❌ TEXT GENERATION: Also failing")
                        
                else:
                    error_text = await response.text()
                    print(f"   ❌ REQUEST FAILED: {response.status}")
                    print(f"   Error: {error_text}")
                    
        except Exception as e:
            print(f"❌ DIAGNOSTIC EXCEPTION: {e}")
            import traceback
            print(f"Stack trace: {traceback.format_exc()}")

    async def test_backend_logs_analysis(self):
        """Analyze what the backend logs show vs actual response"""
        print("\n🔍 BACKEND LOGS vs ACTUAL RESPONSE ANALYSIS")
        print("=" * 70)
        
        print("📋 According to troubleshoot_agent:")
        print("   - Backend logs show '5/5 success' for image generation")
        print("   - This suggests FAL.ai is being called successfully")
        print("   - But frontend doesn't receive the images")
        
        print("\n🧪 Testing to verify this discrepancy...")
        
        # Test with a simple product
        request_data = {
            "product_name": "iPhone 15 Pro",
            "product_description": "Smartphone premium avec processeur A17 Pro",
            "generate_image": True,
            "number_of_images": 1,
            "language": "fr"
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/generate-sheet",
                json=request_data,
                headers=self.get_auth_headers()
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    generated_images = data.get("generated_images", [])
                    
                    print(f"\n📊 VERIFICATION RESULTS:")
                    print(f"   Response Status: {response.status} (Success)")
                    print(f"   Generated Images Count: {len(generated_images)}")
                    
                    if len(generated_images) > 0:
                        print(f"   ✅ CONTRADICTION RESOLVED: Images ARE being returned!")
                        print(f"   🔍 The issue may have been fixed already")
                        print(f"   🔍 Or the issue is intermittent")
                        
                        # Analyze the image data
                        first_image = generated_images[0]
                        if isinstance(first_image, str):
                            try:
                                base64.b64decode(first_image)
                                size_kb = len(first_image) / 1024
                                print(f"   📸 Image Analysis:")
                                print(f"      - Format: Valid base64 string")
                                print(f"      - Size: {size_kb:.1f}KB")
                                print(f"      - Quality: {'High (FAL.ai)' if size_kb > 10 else 'Low (fallback)'}")
                            except:
                                print(f"   ❌ Image data is invalid base64")
                    else:
                        print(f"   ❌ ISSUE CONFIRMED: No images in response")
                        print(f"   🚨 Backend logs may be misleading")
                        print(f"   🚨 FAL.ai may not be called despite logs")
                        
                else:
                    print(f"   ❌ Request failed: {response.status}")
                    
        except Exception as e:
            print(f"❌ Analysis exception: {e}")

    async def test_multiple_scenarios(self):
        """Test multiple scenarios to identify patterns"""
        print("\n🧪 MULTIPLE SCENARIOS PATTERN ANALYSIS")
        print("=" * 70)
        
        test_cases = [
            {
                "name": "Electronics (Smartphone)",
                "product_name": "Samsung Galaxy S24",
                "product_description": "Smartphone Android avec IA intégrée"
            },
            {
                "name": "Home Appliance (Rasoir)",
                "product_name": "Philips Série 7000", 
                "product_description": "Rasoir électrique premium avec technologie de coupe avancée"
            },
            {
                "name": "Fashion (Chaussures)",
                "product_name": "Nike Air Max 270",
                "product_description": "Chaussures de sport avec technologie Air Max"
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📱 Test {i}: {test_case['name']}")
            
            request_data = {
                "product_name": test_case["product_name"],
                "product_description": test_case["product_description"],
                "generate_image": True,
                "number_of_images": 1,
                "language": "fr"
            }
            
            try:
                start_time = time.time()
                
                async with self.session.post(
                    f"{BACKEND_URL}/generate-sheet",
                    json=request_data,
                    headers=self.get_auth_headers()
                ) as response:
                    
                    end_time = time.time()
                    generation_time = end_time - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        generated_images = data.get("generated_images", [])
                        
                        result = {
                            "name": test_case["name"],
                            "product": test_case["product_name"],
                            "status": "success",
                            "images_count": len(generated_images),
                            "generation_time": generation_time,
                            "has_text": bool(data.get("generated_title")),
                            "image_size_kb": len(generated_images[0]) / 1024 if generated_images else 0
                        }
                        
                        print(f"   Status: ✅ Success")
                        print(f"   Images: {len(generated_images)}")
                        print(f"   Time: {generation_time:.1f}s")
                        print(f"   Size: {result['image_size_kb']:.1f}KB")
                        
                    else:
                        result = {
                            "name": test_case["name"],
                            "product": test_case["product_name"],
                            "status": "failed",
                            "error": response.status
                        }
                        print(f"   Status: ❌ Failed ({response.status})")
                        
                    results.append(result)
                    
            except Exception as e:
                print(f"   Status: ❌ Exception - {e}")
                results.append({
                    "name": test_case["name"],
                    "product": test_case["product_name"],
                    "status": "exception",
                    "error": str(e)
                })
        
        # Analyze patterns
        print(f"\n📊 PATTERN ANALYSIS:")
        successful_tests = [r for r in results if r.get("status") == "success"]
        failed_tests = [r for r in results if r.get("status") != "success"]
        
        print(f"   Successful Tests: {len(successful_tests)}/{len(results)}")
        
        if successful_tests:
            images_generated = [r for r in successful_tests if r.get("images_count", 0) > 0]
            print(f"   Tests with Images: {len(images_generated)}/{len(successful_tests)}")
            
            if images_generated:
                avg_size = sum(r.get("image_size_kb", 0) for r in images_generated) / len(images_generated)
                avg_time = sum(r.get("generation_time", 0) for r in images_generated) / len(images_generated)
                print(f"   Average Image Size: {avg_size:.1f}KB")
                print(f"   Average Generation Time: {avg_time:.1f}s")
                
                if avg_size > 10:
                    print(f"   🎉 CONCLUSION: FAL.ai integration is WORKING!")
                    print(f"   🔍 Frontend issue may be in display logic")
                else:
                    print(f"   ⚠️ CONCLUSION: Images too small - may be fallback data")
            else:
                print(f"   ❌ CONCLUSION: No images generated in any test")
                print(f"   🚨 FAL.ai integration is NOT working")
        
        return results

    async def run_diagnostic(self):
        """Run complete diagnostic"""
        print("🚀 ECOMSIMPLY IMAGE GENERATION DIAGNOSTIC")
        print("=" * 80)
        print("Diagnosing: Backend generates images but frontend doesn't display them")
        print("=" * 80)
        
        await self.setup_session()
        
        try:
            # Authenticate first
            if not await self.authenticate_admin():
                print("❌ Cannot proceed without authentication")
                return
                
            # Run diagnostic tests
            await self.test_philips_serie_7000_case()
            await self.test_backend_logs_analysis()
            results = await self.test_multiple_scenarios()
            
            # Final diagnosis
            print("\n" + "=" * 80)
            print("🎯 FINAL DIAGNOSTIC CONCLUSION")
            print("=" * 80)
            
            successful_with_images = [r for r in results if r.get("status") == "success" and r.get("images_count", 0) > 0]
            
            if len(successful_with_images) == len(results):
                print("✅ DIAGNOSIS: Image generation is WORKING correctly!")
                print("🔍 The issue may be:")
                print("   1. Frontend parsing/display logic")
                print("   2. Intermittent issue that's now resolved")
                print("   3. Specific to certain products/conditions")
                print("\n🔧 RECOMMENDATION: Check frontend image display code")
                
            elif len(successful_with_images) > 0:
                print("⚠️ DIAGNOSIS: Image generation is PARTIALLY working")
                print(f"   Working: {len(successful_with_images)}/{len(results)} cases")
                print("🔍 The issue may be:")
                print("   1. Intermittent FAL.ai API issues")
                print("   2. Product-specific generation problems")
                print("   3. Rate limiting or quota issues")
                print("\n🔧 RECOMMENDATION: Investigate FAL.ai integration stability")
                
            else:
                print("❌ DIAGNOSIS: Image generation is NOT working!")
                print("🚨 CRITICAL ISSUE CONFIRMED:")
                print("   - Backend endpoint not calling FAL.ai functions")
                print("   - generated_images array consistently empty")
                print("   - This explains 'Images en cours de génération...' stuck state")
                print("\n🔧 URGENT FIX NEEDED: Repair /api/generate-sheet endpoint")
                
        finally:
            await self.cleanup_session()

async def main():
    """Main diagnostic execution"""
    diagnostic = ImageGenerationDiagnostic()
    await diagnostic.run_diagnostic()

if __name__ == "__main__":
    asyncio.run(main())