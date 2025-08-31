#!/usr/bin/env python3
"""
Quick API test to verify concurrent image generation
"""

import requests
import time
import json

# Configuration
BACKEND_URL = "https://ecomsimply.com/api"
TEST_EMAIL = "msylla54@gmail.com"
TEST_PASSWORD = "AdminEcomsimply"

def authenticate():
    """Get JWT token"""
    login_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json().get("token")
    return None

def test_concurrent_generation():
    """Test concurrent image generation"""
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test with 3 images
    print("🧪 Testing concurrent generation with 3 images...")
    
    request_data = {
        "product_name": "Quick Test Product",
        "product_description": "Testing concurrent image generation performance",
        "generate_image": True,
        "number_of_images": 3,
        "language": "fr"
    }
    
    start_time = time.time()
    response = requests.post(f"{BACKEND_URL}/generate-sheet", json=request_data, headers=headers)
    end_time = time.time()
    
    if response.status_code == 200:
        data = response.json()
        generation_time = data.get("generation_time", end_time - start_time)
        images_generated = data.get("number_of_images_generated", 0)
        
        print(f"✅ Success!")
        print(f"⏱️  Generation time: {generation_time:.2f}s")
        print(f"🖼️  Images generated: {images_generated}")
        print(f"📊 Performance: {'🚀 GOOD' if generation_time < 60 else '⚠️ SLOW'}")
        
        # Check if we have the expected fields
        if "product_images_base64" in data:
            print(f"🖼️  Image data present: {len(data['product_images_base64'])} images")
        
        return True
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    test_concurrent_generation()