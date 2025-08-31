#!/usr/bin/env python3
"""
Debug test to see the actual API response
"""

import requests
import json
import time

BASE_URL = "https://ecomsimply.com/api"

def debug_api_response():
    # Create user
    timestamp = int(time.time())
    test_user = {
        "email": f"debug.test{timestamp}@ecomsimply.fr",
        "name": "Debug Tester",
        "password": "TestPassword123!"
    }
    
    print("Creating user...")
    response = requests.post(f"{BASE_URL}/auth/register", json=test_user)
    print(f"Registration status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("token")
        print(f"Token received: {bool(token)}")
        
        if token:
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test simple generation
            test_data = {
                "product_name": "iPhone 15",
                "product_description": "Smartphone Apple",
                "generate_image": False,
                "number_of_images": 0,
                "language": "fr"
            }
            
            print("\nTesting product generation...")
            print(f"Request data: {json.dumps(test_data, ensure_ascii=False)}")
            
            response = requests.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            try:
                response_data = response.json()
                print(f"Response JSON: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                
                # Check specific fields
                if "success" in response_data:
                    print(f"Success field: {response_data['success']}")
                if "message" in response_data:
                    print(f"Message field: {response_data['message']}")
                if "sheet" in response_data:
                    sheet = response_data["sheet"]
                    print(f"Sheet data present: {bool(sheet)}")
                    if sheet and "target_audience" in sheet:
                        ta = sheet["target_audience"]
                        print(f"Target audience type: {type(ta)}")
                        print(f"Target audience value: {ta}")
                        
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                print(f"Raw response: {response.text}")
    else:
        print(f"Registration failed: {response.text}")

if __name__ == "__main__":
    debug_api_response()