#!/usr/bin/env python3
"""
Debug the sheet limits issue
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://ecomsimply.com/api"

def debug_sheet_limits():
    print("🔍 Debugging sheet limits...")
    
    # Create test user
    timestamp = int(time.time())
    test_user = {
        "email": f"debug.limits.{timestamp}@test.com",
        "name": "Debug Limits User",
        "password": "TestPassword123!"
    }
    
    session = requests.Session()
    session.timeout = 15
    
    # Register user
    response = session.post(f"{BASE_URL}/auth/register", json=test_user)
    if response.status_code != 200:
        print(f"❌ Registration failed: {response.status_code}")
        return
    
    data = response.json()
    auth_token = data.get("token")
    user_data = data.get("user")
    
    print(f"✅ User created: {user_data.get('name')} with plan: {user_data.get('subscription_plan')}")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Check user stats first
    stats_response = session.get(f"{BASE_URL}/stats", headers=headers)
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print(f"📊 User stats: {stats.get('total_sheets', 0)} total sheets, {stats.get('sheets_this_month', 0)} this month")
    
    # Generate first sheet
    sheet_request = {
        "product_name": "Debug Test Product 1",
        "product_description": "First test product for debugging limits",
        "generate_image": False
    }
    
    print("\n🔄 Generating first sheet...")
    response1 = session.post(f"{BASE_URL}/generate-sheet", json=sheet_request, headers=headers)
    
    print(f"First sheet response: {response1.status_code}")
    if response1.status_code == 200:
        sheet_data = response1.json()
        print(f"✅ First sheet created: {sheet_data.get('id')}")
    else:
        print(f"❌ First sheet failed: {response1.text}")
        return
    
    # Check stats after first sheet
    stats_response = session.get(f"{BASE_URL}/stats", headers=headers)
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print(f"📊 After first sheet: {stats.get('total_sheets', 0)} total sheets, {stats.get('sheets_this_month', 0)} this month")
    
    # Generate second sheet
    sheet_request2 = {
        "product_name": "Debug Test Product 2",
        "product_description": "Second test product for debugging limits",
        "generate_image": False
    }
    
    print("\n🔄 Generating second sheet...")
    response2 = session.post(f"{BASE_URL}/generate-sheet", json=sheet_request2, headers=headers)
    
    print(f"Second sheet response: {response2.status_code}")
    if response2.status_code == 403:
        error_data = response2.json()
        print(f"✅ Second sheet blocked as expected")
        print(f"📋 Error details: {json.dumps(error_data, indent=2)}")
        
        # Check if needs_upgrade flag is present
        if "needs_upgrade" in error_data:
            print(f"🎯 needs_upgrade flag: {error_data['needs_upgrade']}")
        else:
            print("❌ needs_upgrade flag missing from error response")
            
    elif response2.status_code == 200:
        print(f"❌ Second sheet should have been blocked but succeeded")
        sheet_data = response2.json()
        print(f"   Sheet ID: {sheet_data.get('id')}")
    else:
        print(f"❌ Unexpected response: {response2.text}")

if __name__ == "__main__":
    debug_sheet_limits()