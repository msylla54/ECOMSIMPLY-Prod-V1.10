#!/usr/bin/env python3
"""
Simple Image Generation Test - Focus on the reported issue
"""

import requests
import json
import time

BASE_URL = "https://ecomsimply.com/api"

def test_image_generation():
    print("🖼️ Testing Image Generation Issue")
    print("=" * 50)
    
    # Test with existing admin user
    admin_credentials = {
        "email": "msylla54@gmail.com",
        "password": "AdminEcomsimply"
    }
    
    session = requests.Session()
    session.timeout = 60
    
    print("1. Logging in as admin user...")
    try:
        response = session.post(f"{BASE_URL}/auth/login", json=admin_credentials)
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            return False
            
        data = response.json()
        token = data.get("token")
        if not token:
            print("❌ No token received")
            return False
            
        print("✅ Login successful")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Test image generation
    print("2. Testing image generation...")
    
    headers = {"Authorization": f"Bearer {token}"}
    test_data = {
        "product_name": "iPhone 15 Pro",
        "product_description": "Smartphone premium avec processeur A17 Pro",
        "generate_image": True,
        "number_of_images": 1
    }
    
    try:
        print("🔄 Sending request...")
        start_time = time.time()
        
        response = session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
        
        duration = time.time() - start_time
        print(f"⏱️ Request took {duration:.2f} seconds")
        
        if response.status_code != 200:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        result = response.json()
        print("✅ Request successful")
        
        # Check for images
        print("3. Checking for image data...")
        
        # Look for image fields
        image_fields = ["product_images_base64", "product_image_base64", "generated_images"]
        images_found = False
        
        for field in image_fields:
            if field in result and result[field]:
                images_found = True
                if isinstance(result[field], list):
                    print(f"✅ Found {len(result[field])} images in '{field}'")
                else:
                    print(f"✅ Found 1 image in '{field}'")
                break
        
        if not images_found:
            print("❌ CRITICAL: NO IMAGES FOUND!")
            print("   This confirms the user's issue:")
            print("   - Text generation works")
            print("   - But no images are generated")
            print("   - Frontend shows 'Images en cours de génération...' forever")
            
            # Show what fields are available
            print(f"   Available fields: {list(result.keys())}")
            return False
        else:
            print("✅ Images generated successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Request error: {e}")
        return False

if __name__ == "__main__":
    success = test_image_generation()
    print("=" * 50)
    if success:
        print("✅ Image generation is working")
    else:
        print("❌ Image generation issue confirmed")