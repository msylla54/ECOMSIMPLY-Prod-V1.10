#!/usr/bin/env python3
"""
Debug GPT-4 Turbo Integration Issues
Focus: Investigate the 422 errors and understand what's happening
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 60

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def setup_test_user():
    """Create and authenticate a test user"""
    session = requests.Session()
    session.timeout = TIMEOUT
    
    # Generate unique test user
    timestamp = int(time.time())
    test_user = {
        "email": f"debugtest{timestamp}@example.com",
        "name": "Debug Test User",
        "password": "TestPassword123!"
    }
    
    try:
        # Register user
        response = session.post(f"{BASE_URL}/auth/register", json=test_user)
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("token")
            user_data = data.get("user")
            
            if auth_token and user_data:
                log(f"✅ Test user created: {user_data['name']}")
                return session, auth_token, user_data
            else:
                log("❌ User registration: Missing token or user data", "ERROR")
                return None, None, None
        else:
            log(f"❌ User registration failed: {response.status_code} - {response.text}", "ERROR")
            return None, None, None
            
    except Exception as e:
        log(f"❌ User setup failed: {str(e)}", "ERROR")
        return None, None, None

def debug_generate_sheet_endpoint():
    """Debug the generate-sheet endpoint with detailed error analysis"""
    log("🔍 DEBUGGING /api/generate-sheet endpoint")
    
    session, auth_token, user_data = setup_test_user()
    if not auth_token:
        log("❌ Cannot debug without auth token", "ERROR")
        return
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test with minimal data first
    minimal_data = {
        "product_name": "iPhone 15 Pro",
        "product_description": "Smartphone haut de gamme"
    }
    
    log("📝 Testing with minimal data...")
    log(f"   Data: {json.dumps(minimal_data, ensure_ascii=False)}")
    
    try:
        response = session.post(f"{BASE_URL}/generate-sheet", json=minimal_data, headers=headers)
        
        log(f"📊 Response Status: {response.status_code}")
        log(f"📊 Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            log(f"📊 Response Data: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        except:
            log(f"📊 Response Text: {response.text}")
            
    except Exception as e:
        log(f"❌ Request failed: {str(e)}", "ERROR")
    
    # Test with full data
    log("\n📝 Testing with full data...")
    full_data = {
        "product_name": "iPhone 15 Pro",
        "product_description": "Smartphone haut de gamme avec processeur A17 Pro et appareil photo 48MP",
        "generate_image": False,  # Disable image to focus on text
        "number_of_images": 0,
        "language": "fr"
    }
    
    log(f"   Data: {json.dumps(full_data, ensure_ascii=False)}")
    
    try:
        response = session.post(f"{BASE_URL}/generate-sheet", json=full_data, headers=headers)
        
        log(f"📊 Response Status: {response.status_code}")
        
        try:
            response_data = response.json()
            log(f"📊 Response Data: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            
            # If successful, analyze the response
            if response.status_code == 200 and response_data.get("success"):
                sheet_data = response_data.get("sheet", {})
                log("\n✅ SUCCESS! Analyzing generated content...")
                log(f"   Title: {sheet_data.get('generated_title', 'N/A')}")
                log(f"   Description length: {len(sheet_data.get('marketing_description', ''))}")
                log(f"   Features count: {len(sheet_data.get('key_features', []))}")
                log(f"   SEO tags count: {len(sheet_data.get('seo_tags', []))}")
                log(f"   Generation time: {response_data.get('generation_time', 'N/A')}")
                
                # Check if it looks like GPT-4 Turbo content
                description = sheet_data.get('marketing_description', '')
                if len(description) > 200 and 'iPhone' in description:
                    log("🎯 Content appears to be GPT-4 Turbo generated (detailed and product-specific)")
                else:
                    log("⚠️ Content may be fallback (short or generic)")
                    
        except:
            log(f"📊 Response Text: {response.text}")
            
    except Exception as e:
        log(f"❌ Request failed: {str(e)}", "ERROR")

def test_user_limits():
    """Test if user limits are causing the 422 errors"""
    log("\n🔍 TESTING User Limits")
    
    session, auth_token, user_data = setup_test_user()
    if not auth_token:
        return
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Check user stats to see current usage
        response = session.get(f"{BASE_URL}/stats", headers=headers)
        
        if response.status_code == 200:
            stats = response.json()
            log(f"📊 User Stats: {json.dumps(stats, ensure_ascii=False, indent=2)}")
            
            # Check subscription plan
            plan = user_data.get('subscription_plan', 'unknown')
            log(f"📊 Subscription Plan: {plan}")
            
            if plan == 'gratuit':
                log("⚠️ User is on free plan - may have limits")
            
        else:
            log(f"❌ Stats request failed: {response.status_code}")
            
    except Exception as e:
        log(f"❌ Stats check failed: {str(e)}", "ERROR")

def main():
    log("🚀 DEBUGGING GPT-4 TURBO INTEGRATION ISSUES")
    log("=" * 80)
    
    debug_generate_sheet_endpoint()
    test_user_limits()
    
    log("\n" + "=" * 80)
    log("🎯 DEBUG COMPLETE")

if __name__ == "__main__":
    main()