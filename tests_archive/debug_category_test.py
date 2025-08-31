#!/usr/bin/env python3
"""
Debug Category Test - Simple test to identify the issue
"""

import requests
import json
import time

# Configuration
BASE_URL = "https://ecomsimply.com/api"

def test_simple_generation():
    """Test simple product sheet generation"""
    
    # First, register/login a test user
    print("🔐 Setting up authentication...")
    
    # Try to register
    register_data = {
        "email": "debug.test@example.com",
        "name": "Debug Test User",
        "password": "DebugTest123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            auth_token = result.get("access_token")
            print(f"✅ User registered successfully")
            print(f"🔑 Token: {auth_token[:20]}..." if auth_token else "❌ No token received")
        else:
            # Try login instead
            login_data = {
                "email": "debug.test@example.com",
                "password": "DebugTest123!"
            }
            response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                print(f"📄 Login response: {result}")
                auth_token = result.get("access_token") or result.get("token")
                print(f"✅ User logged in successfully")
                print(f"🔑 Token: {auth_token[:20]}..." if auth_token else "❌ No token received")
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return
    
    if not auth_token:
        print("❌ No authentication token received")
        return
    
    # Test simple generation without category
    print("\n🧪 Testing simple generation without category...")
    
    generation_data = {
        "product_name": "Test Product",
        "product_description": "Simple test product description",
        "generate_image": False,
        "number_of_images": 0,
        "language": "fr"
    }
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    try:
        print("📤 Sending generation request...")
        response = requests.post(f"{BASE_URL}/generate-sheet", json=generation_data, headers=headers, timeout=60)
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Generation successful!")
            print(f"📋 Title: {result.get('generated_title', 'N/A')}")
            print(f"🏷️ Category: {result.get('category', 'N/A')}")
            print(f"👥 Target Audience: {result.get('target_audience', 'N/A')[:100]}...")
        else:
            print(f"❌ Generation failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Generation error: {e}")
    
    # Test generation WITH category
    print("\n🧪 Testing generation WITH category...")
    
    generation_data_with_category = {
        "product_name": "iPhone 15 Pro",
        "product_description": "Smartphone haut de gamme avec processeur A17 Pro",
        "generate_image": False,
        "number_of_images": 0,
        "language": "fr",
        "category": "électronique"
    }
    
    try:
        print("📤 Sending generation request with category...")
        response = requests.post(f"{BASE_URL}/generate-sheet", json=generation_data_with_category, headers=headers, timeout=60)
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Generation with category successful!")
            print(f"📋 Title: {result.get('generated_title', 'N/A')}")
            print(f"🏷️ Category: {result.get('category', 'N/A')}")
            print(f"👥 Target Audience: {result.get('target_audience', 'N/A')[:100]}...")
            print(f"🏷️ SEO Tags: {result.get('seo_tags', [])}")
        else:
            print(f"❌ Generation with category failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Generation with category error: {e}")

if __name__ == "__main__":
    test_simple_generation()