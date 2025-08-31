#!/usr/bin/env python3
"""
Debug GPT-4 Call - Check if GPT-4 is working or falling back
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://ecomsimply.com/api"

async def debug_gpt4_call():
    """Debug the GPT-4 call to see if it's working"""
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
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
        
        # Test with detailed logging
        print("\n🧪 Testing GPT-4 call with detailed response...")
        test_data = {
            "product_name": "iPhone 15 Pro Max Test",
            "product_description": "Smartphone premium test pour debug GPT-4",
            "generate_image": False,
            "number_of_images": 0,
            "category": "électronique"
        }
        
        async with session.post(f"{BACKEND_URL}/generate-sheet", json=test_data, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                
                print(f"   ✅ Response received")
                print(f"   📝 Title: {result.get('generated_title', 'N/A')[:100]}...")
                print(f"   📊 Features count: {len(result.get('key_features', []))}")
                print(f"   🏷️ SEO tags count: {len(result.get('seo_tags', []))}")
                print(f"   📏 Description length: {len(result.get('marketing_description', ''))}")
                
                # Check if it's using fallback content
                features = result.get('key_features', [])
                if features and "Qualité premium certifiée et garantie" in features:
                    print("   ⚠️ USING FALLBACK CONTENT - GPT-4 call failed")
                else:
                    print("   ✅ USING GPT-4 CONTENT - GPT-4 call succeeded")
                
                # Print actual features and SEO tags
                print(f"\n   📋 Features:")
                for i, feature in enumerate(features, 1):
                    print(f"      {i}. {feature}")
                
                seo_tags = result.get('seo_tags', [])
                print(f"\n   🏷️ SEO Tags:")
                for i, tag in enumerate(seo_tags, 1):
                    print(f"      {i}. {tag}")
                    
            else:
                error = await response.text()
                print(f"   ❌ Error: {response.status} - {error[:500]}")

if __name__ == "__main__":
    asyncio.run(debug_gpt4_call())