#!/usr/bin/env python3
"""
URGENT IMAGE GENERATION DIAGNOSTIC TEST
Focus: Diagnose why images show "Images en cours de génération..." but never appear
"""

import requests
import json
import time
import base64
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 45

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def test_image_generation_issue():
    """Test the exact image generation issue reported by user"""
    log("🚨 URGENT: Testing image generation issue")
    log("Issue: Images show 'Images en cours de génération...' but never appear")
    
    session = requests.Session()
    session.timeout = TIMEOUT
    
    # Create test user
    log("1. Creating test user...")
    timestamp = int(time.time())
    user_data = {
        "email": f"urgent.test.{timestamp}@example.com",
        "name": "Urgent Test User",
        "password": "TestPassword123!"
    }
    
    try:
        response = session.post(f"{BASE_URL}/auth/register", json=user_data)
        if response.status_code != 200:
            log(f"❌ User creation failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
        data = response.json()
        auth_token = data.get("token")
        if not auth_token:
            log("❌ No auth token received", "ERROR")
            return False
            
        log(f"✅ User created: {data.get('user', {}).get('email', 'Unknown')}")
        
    except Exception as e:
        log(f"❌ User creation exception: {str(e)}", "ERROR")
        return False
    
    # Test image generation
    log("2. Testing image generation with generate_image=true and number_of_images=1...")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    test_data = {
        "product_name": "iPhone 15 Pro",
        "product_description": "Smartphone premium avec processeur A17 Pro",
        "generate_image": True,
        "number_of_images": 1,
        "language": "fr"
    }
    
    try:
        log("🔄 Sending image generation request...")
        start_time = time.time()
        
        response = session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
        
        generation_time = time.time() - start_time
        log(f"⏱️ Request completed in {generation_time:.2f} seconds")
        
        if response.status_code != 200:
            log(f"❌ API request failed: {response.status_code}", "ERROR")
            log(f"Response: {response.text}", "ERROR")
            return False
            
        result = response.json()
        log("✅ API request successful")
        
        # Check response structure
        log("3. Analyzing response structure...")
        
        # Look for different possible response formats
        sheet_data = None
        if "sheet" in result:
            sheet_data = result["sheet"]
            log("📋 Found 'sheet' in response")
        elif "product_name" in result:
            sheet_data = result
            log("📋 Response is direct sheet data")
        else:
            log("❌ No recognizable sheet data in response", "ERROR")
            log(f"Response keys: {list(result.keys())}")
            return False
        
        # Check for image fields
        log("4. Checking for image data...")
        
        image_fields = [
            "product_images_base64",
            "product_image_base64", 
            "generated_images",
            "images"
        ]
        
        images_found = []
        for field in image_fields:
            if field in sheet_data:
                value = sheet_data[field]
                if value:
                    if isinstance(value, list):
                        images_found.extend(value)
                        log(f"📸 Found {len(value)} images in '{field}'")
                    else:
                        images_found.append(value)
                        log(f"📸 Found 1 image in '{field}'")
                else:
                    log(f"📭 Field '{field}' exists but is empty")
            else:
                log(f"📭 Field '{field}' not found")
        
        # Analyze results
        log("5. CRITICAL ANALYSIS:")
        
        if not images_found:
            log("❌ ISSUE CONFIRMED: NO IMAGES GENERATED!")
            log("   This matches the user report exactly:")
            log("   - API request succeeds")
            log("   - Sheet data is generated")
            log("   - But NO image data is present")
            log("   - Frontend would show 'Images en cours de génération...' indefinitely")
            
            # Check if FAL.ai integration is working
            log("6. Checking FAL.ai integration status...")
            
            # Look for error indicators in response
            if "error" in result:
                log(f"❌ Error in response: {result['error']}")
            
            if "message" in result:
                log(f"📝 Message: {result['message']}")
            
            # Check generation metadata
            if "generation_time" in sheet_data:
                log(f"⏱️ Generation time: {sheet_data['generation_time']}s")
            
            if "is_ai_generated" in sheet_data:
                log(f"🤖 AI generated: {sheet_data['is_ai_generated']}")
            
            log("")
            log("🔧 DIAGNOSIS:")
            log("   The backend API is working for text generation")
            log("   But the image generation component is failing")
            log("   Possible causes:")
            log("   - FAL_KEY not properly configured")
            log("   - FAL.ai API connectivity issues")
            log("   - generate_image_with_fal_optimized() function failing")
            log("   - asyncio.gather not working for image generation")
            
            return False
            
        else:
            log(f"✅ SUCCESS: {len(images_found)} images generated!")
            
            # Validate image quality
            valid_images = 0
            for i, image_data in enumerate(images_found):
                try:
                    decoded = base64.b64decode(image_data)
                    size = len(decoded)
                    
                    if size > 50000:  # >50KB suggests high-quality FAL.ai image
                        log(f"   Image {i+1}: HIGH QUALITY FAL.ai image ({size} bytes)")
                        valid_images += 1
                    elif size > 1000:  # >1KB suggests valid image
                        log(f"   Image {i+1}: Standard quality image ({size} bytes)")
                        valid_images += 1
                    else:
                        log(f"   Image {i+1}: Suspiciously small ({size} bytes)")
                        
                except Exception as e:
                    log(f"   Image {i+1}: Invalid base64 - {str(e)}")
            
            if valid_images > 0:
                log(f"✅ CONCLUSION: Image generation is working ({valid_images} valid images)")
                log("   The user issue may be intermittent or frontend-related")
                return True
            else:
                log("❌ CONCLUSION: Images generated but all are invalid")
                return False
        
    except Exception as e:
        log(f"❌ Image generation test exception: {str(e)}", "ERROR")
        return False

def main():
    print("🚨 URGENT IMAGE GENERATION DIAGNOSTIC")
    print("=" * 60)
    print("Testing: Images show 'Images en cours de génération...' but never appear")
    print("=" * 60)
    
    success = test_image_generation_issue()
    
    print("=" * 60)
    if success:
        print("✅ Image generation appears to be working")
        print("   Issue may be frontend-related or intermittent")
    else:
        print("❌ CRITICAL ISSUE CONFIRMED")
        print("   Image generation is not working properly")
        print("   Backend investigation required")
    print("=" * 60)

if __name__ == "__main__":
    main()