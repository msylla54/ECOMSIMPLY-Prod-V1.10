#!/usr/bin/env python3
"""
Detailed Per-Store SEO Configuration Testing
Get detailed responses from the implemented endpoints
"""

import requests
import json
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ecomsimply.com')
API_BASE = f"{BACKEND_URL}/api"

def create_admin_user():
    """Create admin user and return token"""
    try:
        payload = {
            "email": f"detailed_admin_{int(datetime.now().timestamp())}@test.com",
            "name": "Detailed Admin Test",
            "password": "AdminPassword123",
            "admin_key": "ECOMSIMPLY_ADMIN_2024"
        }
        
        response = requests.post(f"{API_BASE}/auth/register", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            print(f"✅ Admin user created successfully")
            return token
        else:
            print(f"❌ Admin user creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception creating admin user: {str(e)}")
        return None

def test_per_store_endpoints_detailed(admin_token):
    """Test per-store SEO endpoints with detailed responses"""
    print("\n🔍 DETAILED PER-STORE SEO ENDPOINT TESTING")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test GET /api/seo/stores/config
    print("\n1. Testing GET /api/seo/stores/config")
    print("-" * 40)
    try:
        response = requests.get(f"{BACKEND_URL}/api/seo/stores/config", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        try:
            data = response.json()
            print(f"Response Data: {json.dumps(data, indent=2)}")
        except:
            print(f"Response Text: {response.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")
    
    # Test GET /api/seo/stores/analytics
    print("\n2. Testing GET /api/seo/stores/analytics")
    print("-" * 40)
    try:
        response = requests.get(f"{BACKEND_URL}/api/seo/stores/analytics", headers=headers)
        print(f"Status Code: {response.status_code}")
        try:
            data = response.json()
            print(f"Response Data: {json.dumps(data, indent=2)}")
        except:
            print(f"Response Text: {response.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")
    
    # Test PUT /api/seo/stores/{store_id}/config
    print("\n3. Testing PUT /api/seo/stores/test-store-123/config")
    print("-" * 40)
    try:
        test_config = {
            "scraping_enabled": True,
            "scraping_frequency": "daily",
            "target_keywords": ["electronics", "smartphone"],
            "target_categories": ["tech"],
            "competitor_urls": ["https://example.com"],
            "auto_optimization_enabled": True,
            "auto_publication_enabled": False,
            "confidence_threshold": 0.7,
            "geographic_focus": ["FR"]
        }
        response = requests.put(f"{BACKEND_URL}/api/seo/stores/test-store-123/config", 
                               json=test_config, headers=headers)
        print(f"Status Code: {response.status_code}")
        try:
            data = response.json()
            print(f"Response Data: {json.dumps(data, indent=2)}")
        except:
            print(f"Response Text: {response.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")
    
    # Test POST /api/seo/stores/{store_id}/test-scraping
    print("\n4. Testing POST /api/seo/stores/test-store-123/test-scraping")
    print("-" * 40)
    try:
        response = requests.post(f"{BACKEND_URL}/api/seo/stores/test-store-123/test-scraping", 
                                json={}, headers=headers)
        print(f"Status Code: {response.status_code}")
        try:
            data = response.json()
            print(f"Response Data: {json.dumps(data, indent=2)}")
        except:
            print(f"Response Text: {response.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")

def test_existing_seo_endpoints(admin_token):
    """Test existing SEO endpoints to understand the current system"""
    print("\n🔍 EXISTING SEO ENDPOINTS ANALYSIS")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    endpoints = [
        ("GET", "/api/seo/config"),
        ("GET", "/api/seo/auto-settings"),
        ("GET", "/api/seo/analytics"),
        ("POST", "/api/seo/test-automation")
    ]
    
    for method, endpoint in endpoints:
        print(f"\n{method} {endpoint}")
        print("-" * 40)
        try:
            if method == "GET":
                response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers)
            elif method == "POST":
                response = requests.post(f"{BACKEND_URL}{endpoint}", json={}, headers=headers)
            
            print(f"Status Code: {response.status_code}")
            try:
                data = response.json()
                print(f"Response Data: {json.dumps(data, indent=2)}")
            except:
                print(f"Response Text: {response.text}")
        except Exception as e:
            print(f"Exception: {str(e)}")

def main():
    print("🚀 DETAILED PER-STORE SEO CONFIGURATION ANALYSIS")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 80)
    
    # Create admin user
    admin_token = create_admin_user()
    
    if not admin_token:
        print("❌ Cannot proceed without admin token")
        return
    
    # Test per-store endpoints
    test_per_store_endpoints_detailed(admin_token)
    
    # Test existing SEO endpoints
    test_existing_seo_endpoints(admin_token)
    
    print("\n🎯 ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()