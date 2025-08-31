#!/usr/bin/env python3
"""
Detailed Image Generation Analysis
"""

import requests
import json
import time

BASE_URL = "https://ecomsimply.com/api"

def detailed_image_analysis():
    print("🔍 DETAILED IMAGE GENERATION ANALYSIS")
    print("=" * 60)
    
    admin_credentials = {
        "email": "msylla54@gmail.com",
        "password": "AdminEcomsimply"
    }
    
    session = requests.Session()
    session.timeout = 60
    
    # Login
    response = session.post(f"{BASE_URL}/auth/login", json=admin_credentials)
    token = response.json().get("token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test different scenarios
    test_cases = [
        {
            "name": "Single Image Test",
            "data": {
                "product_name": "iPhone 15 Pro",
                "product_description": "Smartphone premium",
                "generate_image": True,
                "number_of_images": 1
            }
        },
        {
            "name": "Multiple Images Test", 
            "data": {
                "product_name": "MacBook Pro",
                "product_description": "Ordinateur portable",
                "generate_image": True,
                "number_of_images": 2
            }
        },
        {
            "name": "No Images Test",
            "data": {
                "product_name": "Test Product",
                "product_description": "Test description",
                "generate_image": False,
                "number_of_images": 0
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 40)
        
        try:
            start_time = time.time()
            response = session.post(f"{BASE_URL}/generate-sheet", json=test_case['data'], headers=headers)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ Request successful ({duration:.2f}s)")
                print(f"📋 Response keys: {list(result.keys())}")
                
                # Check image-related fields
                image_fields = ["generated_images", "product_images_base64", "product_image_base64"]
                
                for field in image_fields:
                    if field in result:
                        value = result[field]
                        if value:
                            if isinstance(value, list):
                                print(f"📸 {field}: {len(value)} items")
                                for j, item in enumerate(value):
                                    if item:
                                        print(f"   Item {j+1}: {len(str(item))} characters")
                                    else:
                                        print(f"   Item {j+1}: Empty")
                            else:
                                print(f"📸 {field}: {len(str(value))} characters")
                        else:
                            print(f"📭 {field}: Empty")
                    else:
                        print(f"❌ {field}: Not found")
                
                # Check generation metadata
                if "generation_time" in result:
                    print(f"⏱️ Generation time: {result['generation_time']}s")
                
                # Check if text generation worked
                if "generated_title" in result and result["generated_title"]:
                    print(f"✅ Text generation: Working")
                    print(f"   Title: {result['generated_title'][:50]}...")
                else:
                    print(f"❌ Text generation: Failed")
                    
            else:
                print(f"❌ Request failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(2)  # Brief pause between tests
    
    print("\n" + "=" * 60)
    print("🔧 DIAGNOSIS:")
    print("If 'generated_images' is consistently empty when generate_image=True,")
    print("then the FAL.ai integration is not working properly.")
    print("This would cause the frontend to show 'Images en cours de génération...'")
    print("indefinitely because no actual image data is returned.")

if __name__ == "__main__":
    detailed_image_analysis()