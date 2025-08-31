#!/usr/bin/env python3
"""
Subscription Validation Deep Dive Test
Understanding the current subscription validation logic
"""

import requests
import json
import time

BACKEND_URL = "https://ecomsimply.com/api"
ADMIN_KEY = "ECOMSIMPLY_ADMIN_2024"

def test_subscription_validation():
    """Test current subscription validation logic"""
    
    # Create users with different plans
    users = {}
    
    # Create admin user (should get premium)
    admin_data = {
        "email": f"admin.validation.{int(time.time())}@example.com",
        "name": "Validation Admin",
        "password": "AdminTest123!",
        "admin_key": ADMIN_KEY
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/register", json=admin_data)
    if response.status_code == 200:
        data = response.json()
        users["admin"] = {
            "token": data["token"],
            "email": admin_data["email"]
        }
        print(f"✅ Admin user created: {admin_data['email']}")
    
    # Create regular user (should get gratuit)
    regular_data = {
        "email": f"regular.validation.{int(time.time())}@example.com",
        "name": "Regular User",
        "password": "RegularTest123!"
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/register", json=regular_data)
    if response.status_code == 200:
        data = response.json()
        users["regular"] = {
            "token": data["token"],
            "email": regular_data["email"]
        }
        print(f"✅ Regular user created: {regular_data['email']}")
    
    # Test each user's subscription plan and SEO access
    for user_type, user_info in users.items():
        print(f"\n🔍 Testing {user_type} user: {user_info['email']}")
        
        headers = {"Authorization": f"Bearer {user_info['token']}"}
        
        # Get user stats to see subscription plan
        stats_response = requests.get(f"{BACKEND_URL}/stats", headers=headers)
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            plan = stats_data.get("subscription_plan", "unknown")
            print(f"   📋 Subscription Plan: {plan}")
        else:
            print(f"   ❌ Cannot get stats: {stats_response.status_code}")
            continue
        
        # Test SEO config access
        seo_response = requests.get(f"{BACKEND_URL}/seo/config", headers=headers)
        print(f"   🔧 SEO Config Access: {seo_response.status_code}")
        if seo_response.status_code == 403:
            error_data = seo_response.json()
            error_msg = error_data.get("detail", "")
            print(f"      Error: {error_msg}")
        elif seo_response.status_code == 200:
            print(f"      ✅ Access granted")
        
        # Test SEO trends access
        trends_data = {"keywords": ["test"], "region": "FR"}
        trends_response = requests.post(f"{BACKEND_URL}/seo/scrape/trends", json=trends_data, headers=headers)
        print(f"   📈 SEO Trends Access: {trends_response.status_code}")
        if trends_response.status_code == 403:
            error_data = trends_response.json()
            error_msg = error_data.get("detail", "")
            print(f"      Error: {error_msg}")
        elif trends_response.status_code in [200, 503]:
            print(f"      ✅ Access granted")

if __name__ == "__main__":
    test_subscription_validation()