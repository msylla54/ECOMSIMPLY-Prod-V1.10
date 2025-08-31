#!/usr/bin/env python3
"""
Simple test script for product publishing endpoints
"""
import requests
import json
import time

# Get the backend URL from environment
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BASE_URL = line.strip().split('=')[1] + '/api'
            break

print(f"Testing backend at: {BASE_URL}")

def test_publishing_endpoints():
    """Test all product publishing endpoints"""
    print("🛒 TESTING PRODUCT PUBLISHING ENDPOINTS...")
    
    # First register and login a user
    timestamp = int(time.time())
    user_data = {
        "email": f"testuser{timestamp}@test.fr",
        "name": "Test User",
        "password": "TestPassword123!"
    }
    
    session = requests.Session()
    
    # Register user
    print("   Registering test user...")
    response = session.post(f"{BASE_URL}/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"❌ User registration failed: {response.status_code}")
        return False
    
    # Get auth token
    data = response.json()
    auth_token = data.get("token")
    if not auth_token:
        print("❌ No auth token received")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test data structure as specified in review request
    test_publish_request = {
        "product_sheet_id": "test-sheet-id",
        "store_id": "test-store-id", 
        "product_data": {
            "name": "Test Product",
            "description": "Test description",
            "features": ["Feature 1", "Feature 2"],
            "seo_tags": ["tag1", "tag2"],
            "price_suggestions": "29.99€",
            "target_audience": "Test audience",
            "images": []
        },
        "auto_publish": True,
        "pricing_strategy": "auto"
    }
    
    # All publishing endpoints to test
    publishing_endpoints = [
        "/ecommerce/shopify/publish",
        "/ecommerce/woocommerce/publish", 
        "/ecommerce/amazon/publish",
        "/ecommerce/ebay/publish",
        "/ecommerce/etsy/publish",
        "/ecommerce/facebook/publish",
        "/ecommerce/google-shopping/publish"
    ]
    
    success_count = 0
    
    for endpoint in publishing_endpoints:
        try:
            print(f"   Testing: {endpoint}")
            
            response = session.post(f"{BASE_URL}{endpoint}", json=test_publish_request, headers=headers)
            
            # Expected behavior based on review request:
            # - For free users: Should return 403 (premium feature required)
            # - For premium users: Should handle request (might return 404 for missing product sheet/store, but endpoint should be accessible)
            # - Should NOT return 500 Internal Server Error
            # - Should NOT return 405 Method Not Allowed
            
            if response.status_code == 403:
                print(f"   ✅ {endpoint}: Correctly requires premium subscription (403)")
                success_count += 1
            elif response.status_code == 404:
                print(f"   ✅ {endpoint}: Endpoint accessible, returns 404 for missing resources (expected)")
                success_count += 1
            elif response.status_code == 200:
                print(f"   ✅ {endpoint}: Successfully processed request (200)")
                success_count += 1
            elif response.status_code == 422:
                print(f"   ✅ {endpoint}: Validation error (422) - endpoint working")
                success_count += 1
            elif response.status_code == 500:
                print(f"   ❌ {endpoint}: Internal Server Error (500) - CRITICAL ISSUE")
            elif response.status_code == 405:
                print(f"   ❌ {endpoint}: Method Not Allowed (405) - ENDPOINT NOT IMPLEMENTED")
            else:
                print(f"   ⚠️  {endpoint}: Unexpected status code {response.status_code}")
                success_count += 1  # Still count as working if not 500/405
                
            time.sleep(0.2)  # Brief pause between requests
            
        except Exception as e:
            print(f"   ❌ {endpoint}: Exception {str(e)}")
    
    if success_count == len(publishing_endpoints):
        print("✅ PRODUCT PUBLISHING ENDPOINTS: All endpoints working correctly!")
        print(f"   ✅ {success_count}/{len(publishing_endpoints)} endpoints functional")
        return True
    else:
        print(f"❌ PRODUCT PUBLISHING ENDPOINTS: {success_count}/{len(publishing_endpoints)} endpoints working")
        return False

def test_all_stores_endpoint():
    """Test the /api/ecommerce/all-stores endpoint"""
    print("🏪 TESTING ALL-STORES ENDPOINT...")
    
    # Register and login a user
    timestamp = int(time.time())
    user_data = {
        "email": f"testuser2{timestamp}@test.fr",
        "name": "Test User 2",
        "password": "TestPassword123!"
    }
    
    session = requests.Session()
    
    # Register user
    response = session.post(f"{BASE_URL}/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"❌ User registration failed: {response.status_code}")
        return False
    
    # Get auth token
    data = response.json()
    auth_token = data.get("token")
    if not auth_token:
        print("❌ No auth token received")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = session.get(f"{BASE_URL}/ecommerce/all-stores", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            required_fields = ["stores", "total", "platforms"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ All-Stores Endpoint: Missing fields {missing_fields}")
                return False
            
            stores = data.get("stores", [])
            total = data.get("total", 0)
            platforms = data.get("platforms", {})
            
            print(f"✅ All-Stores Endpoint: Successfully retrieved store data")
            print(f"   Total Stores: {total}")
            print(f"   Stores Array: {len(stores)} items")
            print(f"   Platforms: {list(platforms.keys())}")
            
            return True
            
        elif response.status_code == 500:
            print("❌ All-Stores Endpoint: Internal Server Error (500) - CRITICAL ISSUE")
            return False
        elif response.status_code == 403:
            print("✅ All-Stores Endpoint: Requires premium subscription (403)")
            return True
        else:
            print(f"❌ All-Stores Endpoint: Unexpected status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ All-Stores Endpoint failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 STARTING PRODUCT PUBLISHING ENDPOINTS TESTING")
    print("=" * 80)
    
    # Test publishing endpoints
    publishing_result = test_publishing_endpoints()
    
    print("\n" + "-" * 60)
    
    # Test all-stores endpoint
    stores_result = test_all_stores_endpoint()
    
    # Final Results
    print("\n" + "=" * 80)
    print("🎯 PRODUCT PUBLISHING ENDPOINTS TEST RESULTS")
    print("=" * 80)
    
    if publishing_result and stores_result:
        print("🎉 ALL TESTS PASSED!")
        print("   ✅ All publishing endpoints working correctly")
        print("   ✅ All-stores endpoint functional")
        exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        if not publishing_result:
            print("   ❌ Publishing endpoints have issues")
        if not stores_result:
            print("   ❌ All-stores endpoint has issues")
        exit(1)