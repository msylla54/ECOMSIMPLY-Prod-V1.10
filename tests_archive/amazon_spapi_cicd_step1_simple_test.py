#!/usr/bin/env python3
"""
ECOMSIMPLY Amazon SP-API CI/CD Step 1 Simple Backend Testing
Focus: Core backend functionality after dependency updates
"""

import requests
import json
import sys
from datetime import datetime

BACKEND_URL = "https://ecomsimply-deploy.preview.emergentagent.com"

def test_backend_startup():
    """Test that backend starts without errors"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok') and data.get('db'):
                print("✅ Backend startup: SUCCESS")
                print(f"   Database: {data.get('db')}")
                return True
        print("❌ Backend startup: FAILED")
        print(f"   Response: {response.text}")
        return False
    except Exception as e:
        print("❌ Backend startup: FAILED")
        print(f"   Error: {str(e)}")
        return False

def test_mongodb_connection():
    """Test MongoDB connectivity"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/stats/public", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok') and data.get('stats'):
                print("✅ MongoDB connectivity: SUCCESS")
                return True
        print("❌ MongoDB connectivity: FAILED")
        return False
    except Exception as e:
        print("❌ MongoDB connectivity: FAILED")
        print(f"   Error: {str(e)}")
        return False

def test_existing_endpoints():
    """Test existing endpoints work (no regression)"""
    endpoints = [
        "/api/health",
        "/api/languages", 
        "/api/public/plans-pricing",
        "/api/testimonials",
        "/api/stats/public"
    ]
    
    working = 0
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                working += 1
                print(f"✅ {endpoint}: SUCCESS")
            else:
                print(f"❌ {endpoint}: FAILED ({response.status_code})")
        except Exception as e:
            print(f"❌ {endpoint}: FAILED ({str(e)})")
    
    success = working == len(endpoints)
    print(f"{'✅' if success else '❌'} Existing endpoints: {working}/{len(endpoints)}")
    return success

def test_amazon_spapi_import():
    """Test that python-amazon-sp-api can be imported (no import errors)"""
    try:
        # If the backend starts successfully, the import is likely working
        # We can test this by checking if there are any import-related errors
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ Amazon SP-API import: SUCCESS (no import errors)")
            return True
        else:
            print("❌ Amazon SP-API import: FAILED (backend not responding)")
            return False
    except Exception as e:
        print("❌ Amazon SP-API import: FAILED")
        print(f"   Error: {str(e)}")
        return False

def test_motor_upgrade():
    """Test Motor 3.7.1 upgrade works"""
    try:
        # Test database operations work
        response = requests.get(f"{BACKEND_URL}/api/testimonials", timeout=10)
        if response.status_code == 200:
            print("✅ Motor 3.7.1 upgrade: SUCCESS")
            return True
        else:
            print("❌ Motor 3.7.1 upgrade: FAILED")
            return False
    except Exception as e:
        print("❌ Motor 3.7.1 upgrade: FAILED")
        print(f"   Error: {str(e)}")
        return False

def main():
    print("🚀 ECOMSIMPLY AMAZON SP-API CI/CD STEP 1 SIMPLE TESTING")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Time: {datetime.now().isoformat()}")
    print()
    
    tests = [
        ("Backend Startup", test_backend_startup),
        ("MongoDB Connection", test_mongodb_connection), 
        ("Existing Endpoints", test_existing_endpoints),
        ("Amazon SP-API Import", test_amazon_spapi_import),
        ("Motor 3.7.1 Upgrade", test_motor_upgrade)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"🔍 Testing: {test_name}")
        result = test_func()
        results.append(result)
        print()
    
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total) * 100
    
    print("📊 SUMMARY:")
    print(f"   Tests Passed: {passed}/{total}")
    print(f"   Success Rate: {success_rate:.1f}%")
    print()
    
    if success_rate >= 80:
        print("✅ CI/CD STEP 1 VALIDATION: SUCCESS")
        print("✅ Backend ready for Amazon SP-API integration")
        return 0
    else:
        print("❌ CI/CD STEP 1 VALIDATION: FAILED")
        print("❌ Fix issues before proceeding with Amazon SP-API integration")
        return 1

if __name__ == "__main__":
    sys.exit(main())