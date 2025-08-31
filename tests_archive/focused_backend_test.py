#!/usr/bin/env python3
"""
Focused Backend Testing for remaining issues
"""

import requests
import json
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BACKEND_URL = "https://ecomsimply.com"
API_BASE = f"{BACKEND_URL}/api"

# Test with existing user credentials
TEST_EMAIL = "test_backend_user@example.com"
TEST_PASSWORD = "TestPassword123"

session = requests.Session()
session.verify = False

def test_auth_and_profile():
    """Test authentication and profile access"""
    print("🔐 Testing Authentication and Profile Access...")
    
    # Login
    login_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    response = session.post(f"{API_BASE}/auth/login", json=login_data, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        print(f"✅ Login successful, token: {token[:20]}...")
        
        # Test profile with token
        headers = {'Authorization': f'Bearer {token}'}
        
        # Try different profile endpoints
        for endpoint in ['/user/profile', '/profile', '/me', '/user/me']:
            try:
                response = session.get(f"{API_BASE}{endpoint}", headers=headers, timeout=5)
                print(f"  Profile endpoint {endpoint}: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✅ Profile data: {data.get('email', 'No email')}")
                    break
            except Exception as e:
                print(f"  ❌ Error on {endpoint}: {e}")
        
        # Try stats endpoints
        for endpoint in ['/user/stats', '/stats', '/user/analytics']:
            try:
                response = session.get(f"{API_BASE}{endpoint}", headers=headers, timeout=5)
                print(f"  Stats endpoint {endpoint}: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✅ Stats data: {data}")
                    break
            except Exception as e:
                print(f"  ❌ Error on {endpoint}: {e}")
                
    else:
        print(f"❌ Login failed: {response.status_code}")

def test_pricetruth_detailed():
    """Test PriceTruth with different parameters"""
    print("\n💰 Testing PriceTruth System in Detail...")
    
    # Test different parameter formats
    test_cases = [
        "iPhone 15 Pro",
        "Samsung Galaxy S24",
        "MacBook Pro M3"
    ]
    
    for product in test_cases:
        try:
            # Test with product_name parameter
            response = session.get(f"{API_BASE}/price-truth", 
                                 params={"product_name": product}, 
                                 timeout=10)
            print(f"  Product '{product}': {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"    ✅ Status: {data.get('status')}, Sources: {len(data.get('sources', []))}")
            elif response.status_code == 400:
                error = response.json()
                print(f"    ⚠️ Bad request: {error.get('message', 'Unknown error')}")
            else:
                print(f"    ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"    ❌ Exception: {e}")

def test_product_generation_simple():
    """Test product generation with minimal data"""
    print("\n🤖 Testing Simple Product Generation...")
    
    # Login first
    login_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    response = session.post(f"{API_BASE}/auth/login", json=login_data, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        headers = {'Authorization': f'Bearer {token}'}
        
        # Simple product data
        product_data = {
            "product_name": "Test Product",
            "product_description": "Simple test product for backend testing",
            "generate_image": False,
            "number_of_images": 0,
            "language": "fr"
        }
        
        print("  Sending product generation request...")
        try:
            response = session.post(f"{API_BASE}/generate-sheet", 
                                  json=product_data, 
                                  headers=headers, 
                                  timeout=30)  # Longer timeout for AI
            
            print(f"  Response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Generated title: {data.get('generated_title', 'No title')[:50]}...")
                print(f"  ✅ Features count: {len(data.get('key_features', []))}")
                print(f"  ✅ SEO tags count: {len(data.get('seo_tags', []))}")
            else:
                try:
                    error = response.json()
                    print(f"  ❌ Error: {error}")
                except:
                    print(f"  ❌ Error: {response.text[:200]}")
                    
        except Exception as e:
            print(f"  ❌ Exception: {e}")
    else:
        print("❌ Login failed for product generation test")

if __name__ == "__main__":
    print("🔍 FOCUSED BACKEND TESTING")
    print("=" * 50)
    
    test_auth_and_profile()
    test_pricetruth_detailed()
    test_product_generation_simple()
    
    print("\n✅ Focused testing completed!")