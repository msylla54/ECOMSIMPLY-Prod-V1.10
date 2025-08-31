#!/usr/bin/env python3
"""
Category Issue Test - Focus on the specific category storage issue
"""

import requests
import json

# Configuration
BASE_URL = "https://ecomsimply.com/api"

def test_category_issue():
    """Test the category storage issue with admin user"""
    
    print("🔐 Authenticating as admin user...")
    
    # Login as admin user (has premium plan)
    login_data = {
        "email": "msylla54@gmail.com",
        "password": "AdminEcomsimply"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            auth_token = result.get("token")
            user_info = result.get("user", {})
            print(f"✅ Admin logged in successfully")
            print(f"📋 Plan: {user_info.get('subscription_plan', 'unknown')}")
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return
    
    # Test generation WITH category
    print("\n🧪 Testing generation WITH category...")
    
    generation_data = {
        "product_name": "iPhone 15 Pro",
        "product_description": "Smartphone haut de gamme avec processeur A17 Pro et appareil photo 48MP",
        "generate_image": False,
        "number_of_images": 0,
        "language": "fr",
        "category": "électronique"
    }
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    print(f"📤 Sending request with category: {generation_data['category']}")
    
    try:
        response = requests.post(f"{BASE_URL}/generate-sheet", json=generation_data, headers=headers, timeout=60)
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Generation successful!")
            
            # Check category field
            response_category = result.get("category")
            print(f"\n🔍 CATEGORY ANALYSIS:")
            print(f"📤 Requested category: {generation_data['category']}")
            print(f"📥 Response category: {response_category}")
            print(f"🏷️ Category stored: {'✅ YES' if response_category else '❌ NO'}")
            
            # Check target_audience format
            target_audience = result.get("target_audience", "")
            print(f"\n🔍 TARGET AUDIENCE ANALYSIS:")
            print(f"📝 Target audience: {target_audience[:150]}...")
            print(f"📊 Length: {len(target_audience)} characters")
            
            # Check if it's JSON-like
            is_json_like = "{" in target_audience and "}" in target_audience
            print(f"🔍 JSON-like format: {'❌ YES' if is_json_like else '✅ NO'}")
            
            # Show other fields for comparison
            print(f"\n📋 OTHER FIELDS:")
            print(f"🏷️ Title: {result.get('generated_title', 'N/A')}")
            print(f"🏷️ SEO Tags: {result.get('seo_tags', [])}")
            
            # Summary
            print(f"\n🎯 ISSUE SUMMARY:")
            if not response_category:
                print("❌ CRITICAL: Category field is NOT being stored/returned")
                print("   This confirms the issue mentioned in the review request")
            else:
                print("✅ Category field is working correctly")
            
            if is_json_like:
                print("❌ CRITICAL: Target audience is still JSON-like format")
                print("   The GPT-4 Turbo prompt fix is not working properly")
            else:
                print("✅ Target audience is simple text format")
                
        else:
            print(f"❌ Generation failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Generation error: {e}")

if __name__ == "__main__":
    test_category_issue()