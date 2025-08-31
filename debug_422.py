#!/usr/bin/env python3
"""
Debug script to investigate 422 errors in GPT-4 Turbo integration
"""

import requests
import json
import time

BASE_URL = "https://ecomsimply.com/api"

def debug_422_error():
    session = requests.Session()
    session.timeout = 30
    
    # Register a test user
    timestamp = int(time.time())
    test_user = {
        "email": f"debug{timestamp}@example.com",
        "name": "Debug User",
        "password": "TestPassword123!"
    }
    
    print("🔍 Registering test user...")
    response = session.post(f"{BASE_URL}/auth/register", json=test_user)
    
    if response.status_code != 200:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return
    
    data = response.json()
    auth_token = data.get("token")
    
    if not auth_token:
        print("❌ No auth token received")
        return
    
    print("✅ User registered successfully")
    
    # Test the generate-sheet endpoint with detailed error logging
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    test_data = {
        "product_name": "iPhone 15 Pro",
        "product_description": "Smartphone haut de gamme avec processeur A17 Pro et appareil photo 48MP",
        "generate_image": True,
        "number_of_images": 1,
        "language": "fr"
    }
    
    print("🔍 Testing generate-sheet endpoint...")
    print(f"📝 Request data: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    response = session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
    
    print(f"📊 Response status: {response.status_code}")
    print(f"📊 Response headers: {dict(response.headers)}")
    
    try:
        response_data = response.json()
        print(f"📊 Response data: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
    except:
        print(f"📊 Response text: {response.text}")
    
    # Also test with minimal data to see if it's a validation issue
    print("\n🔍 Testing with minimal data...")
    minimal_data = {
        "product_name": "Test Product",
        "product_description": "Test description"
    }
    
    response2 = session.post(f"{BASE_URL}/generate-sheet", json=minimal_data, headers=headers)
    print(f"📊 Minimal test status: {response2.status_code}")
    
    try:
        response2_data = response2.json()
        print(f"📊 Minimal test response: {json.dumps(response2_data, ensure_ascii=False, indent=2)}")
    except:
        print(f"📊 Minimal test text: {response2.text}")

if __name__ == "__main__":
    debug_422_error()