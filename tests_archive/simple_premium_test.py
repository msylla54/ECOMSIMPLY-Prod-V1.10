#!/usr/bin/env python3
"""
Simple Premium System Test - Check current implementation
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://ecomsimply.com/api"

async def test_premium_system():
    """Test the premium system with admin user"""
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
        # Authenticate as admin
        auth_data = {
            "email": "msylla54@gmail.com",
            "password": "AdminEcomsimply"
        }
        
        print("🔐 Authenticating...")
        async with session.post(f"{BACKEND_URL}/auth/login", json=auth_data) as response:
            if response.status != 200:
                print(f"❌ Auth failed: {response.status}")
                return
            
            result = await response.json()
            token = result.get("token")
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ Authenticated successfully")
        
        # Test 1: Premium differentiation (content only)
        print("\n🧪 TEST 1: Premium Differentiation (Content Only)")
        test_data = {
            "product_name": "iPhone 15 Pro Max",
            "product_description": "Smartphone premium avec processeur A17 Pro",
            "generate_image": False,
            "number_of_images": 0,
            "category": "électronique"
        }
        
        async with session.post(f"{BACKEND_URL}/generate-sheet", json=test_data, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                features_count = len(result.get("key_features", []))
                seo_count = len(result.get("seo_tags", []))
                print(f"   ✅ Content generated")
                print(f"   📊 Features: {features_count} (Expected: 6 for premium)")
                print(f"   🏷️ SEO Tags: {seo_count} (Expected: 6 for premium)")
                
                if features_count == 6 and seo_count == 6:
                    print("   ✅ PREMIUM DIFFERENTIATION WORKING")
                else:
                    print("   ❌ PREMIUM DIFFERENTIATION NOT WORKING")
            else:
                error = await response.text()
                print(f"   ❌ Error: {response.status} - {error[:200]}")
        
        # Test 2: Image generation
        print("\n🧪 TEST 2: Image Generation")
        image_test_data = {
            "product_name": "MacBook Pro M3",
            "product_description": "Ordinateur portable professionnel",
            "generate_image": True,
            "number_of_images": 1,
            "category": "électronique"
        }
        
        async with session.post(f"{BACKEND_URL}/generate-sheet", json=image_test_data, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                generated_images = result.get("generated_images", [])
                images_count = len(generated_images)
                print(f"   ✅ Generation completed")
                print(f"   🖼️ Images: {images_count}/1 generated")
                
                if images_count > 0:
                    print("   ✅ IMAGE GENERATION WORKING")
                    # Check image quality
                    img_size = len(generated_images[0]) if generated_images else 0
                    print(f"   📊 Image size: {img_size/1024:.1f}KB")
                else:
                    print("   ❌ IMAGE GENERATION NOT WORKING")
            else:
                error = await response.text()
                print(f"   ❌ Error: {response.status} - {error[:200]}")

if __name__ == "__main__":
    asyncio.run(test_premium_system())