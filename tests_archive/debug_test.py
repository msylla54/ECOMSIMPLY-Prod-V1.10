#!/usr/bin/env python3
"""
Debug test to check the exact responses from the API
"""

import requests
import json
import time

BASE_URL = "https://ecomsimply.com/api"

def debug_registration():
    """Debug user registration response"""
    print("🔍 Debugging user registration...")
    
    timestamp = int(time.time())
    test_user = {
        "email": f"debug{timestamp}@example.com",
        "name": "Debug User",
        "password": "DebugPassword123!"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=test_user)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print("User data in response:")
        print(json.dumps(data.get("user", {}), indent=2))
        return data.get("token"), data.get("user")
    
    return None, None

def debug_limit_enforcement(token):
    """Debug free plan limit enforcement"""
    print("\n🔍 Debugging free plan limit enforcement...")
    
    if not token:
        print("No token available")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    sheet_request = {
        "product_name": "Debug Test Product",
        "product_description": "Testing debug",
        "generate_image": False
    }
    
    # First request
    print("First request:")
    response1 = requests.post(f"{BASE_URL}/generate-sheet", json=sheet_request, headers=headers)
    print(f"Status Code: {response1.status_code}")
    print(f"Response: {response1.text[:200]}...")
    
    # Second request
    print("\nSecond request:")
    response2 = requests.post(f"{BASE_URL}/generate-sheet", json=sheet_request, headers=headers)
    print(f"Status Code: {response2.status_code}")
    print(f"Response: {response2.text}")
    
    if response2.status_code == 403:
        try:
            error_data = response2.json()
            print("Error data structure:")
            print(json.dumps(error_data, indent=2))
        except:
            print("Could not parse JSON response")

def main():
    token, user = debug_registration()
    debug_limit_enforcement(token)

if __name__ == "__main__":
    main()