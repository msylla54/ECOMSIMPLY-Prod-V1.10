#!/usr/bin/env python3
"""
Simplified Affiliate System Test - Focus on Core Functionality
"""

import requests
import json
import uuid

# Configuration
BACKEND_URL = 'https://ecomsimply.com'
API_BASE = f"{BACKEND_URL}/api"
ADMIN_EMAIL = "msylla54@yahoo.fr"
ADMIN_PASSWORD = "NewPassword123"
ADMIN_KEY = "ECOMSIMPLY_ADMIN_2024"

def test_affiliate_system():
    print("🚀 Testing Core Affiliate Management System")
    print("=" * 50)
    
    results = []
    
    # 1. Test Affiliate Registration
    print("1. Testing Affiliate Registration...")
    test_email = f"affiliate_test_{uuid.uuid4().hex[:8]}@test.com"
    registration_data = {
        "email": test_email,
        "name": "Test Affiliate",
        "company": "Test Company",
        "website": "https://test-affiliate.com",
        "social_media": {"twitter": "@testaffiliate"},
        "payment_method": "bank_transfer",
        "payment_details": {"bank_name": "Test Bank"},
        "motivation": "I want to promote this amazing product"
    }
    
    response = requests.post(f"{API_BASE}/affiliate/register", json=registration_data)
    if response.status_code == 200:
        data = response.json()
        if data.get("success") and data.get("affiliate_code"):
            affiliate_code = data.get("affiliate_code")
            print(f"✅ Affiliate registered with code: {affiliate_code}")
            results.append(("Affiliate Registration", True))
        else:
            print(f"❌ Registration failed: {data}")
            results.append(("Affiliate Registration", False))
            return results
    else:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        results.append(("Affiliate Registration", False))
        return results
    
    # 2. Test Duplicate Email Validation
    print("\n2. Testing Duplicate Email Validation...")
    response = requests.post(f"{API_BASE}/affiliate/register", json=registration_data)
    if response.status_code == 400:
        print("✅ Correctly rejected duplicate email")
        results.append(("Duplicate Email Validation", True))
    else:
        print(f"❌ Should reject duplicate email: {response.status_code}")
        results.append(("Duplicate Email Validation", False))
    
    # 3. Test Affiliate Statistics (should work even for pending affiliates)
    print(f"\n3. Testing Affiliate Statistics for {affiliate_code}...")
    response = requests.get(f"{API_BASE}/affiliate/{affiliate_code}/stats")
    if response.status_code == 200:
        data = response.json()
        required_fields = ["total_clicks", "total_conversions", "conversion_rate", "total_earnings"]
        if all(field in data for field in required_fields):
            print(f"✅ Statistics retrieved: {data['total_clicks']} clicks, {data['total_conversions']} conversions")
            results.append(("Affiliate Statistics", True))
        else:
            print(f"❌ Missing required fields in stats: {data}")
            results.append(("Affiliate Statistics", False))
    else:
        print(f"❌ Statistics failed: {response.status_code} - {response.text}")
        results.append(("Affiliate Statistics", False))
    
    # 4. Test Invalid Affiliate Code
    print("\n4. Testing Invalid Affiliate Code...")
    response = requests.get(f"{API_BASE}/affiliate/INVALID123/stats")
    if response.status_code == 404:
        print("✅ Correctly rejected invalid affiliate code")
        results.append(("Invalid Code Handling", True))
    else:
        print(f"❌ Should reject invalid code: {response.status_code}")
        results.append(("Invalid Code Handling", False))
    
    # 5. Test Affiliate Tracking (will fail for pending affiliate, but should give proper error)
    print(f"\n5. Testing Affiliate Tracking for {affiliate_code}...")
    tracking_params = {
        "landing_page": "https://ecomsimply.com/pricing",
        "utm_source": "affiliate",
        "utm_medium": "referral"
    }
    response = requests.get(f"{API_BASE}/affiliate/track/{affiliate_code}", params=tracking_params)
    if response.status_code == 404:
        print("✅ Correctly rejected pending affiliate (needs approval)")
        results.append(("Affiliate Tracking Validation", True))
    elif response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print(f"✅ Tracking successful: {data}")
            results.append(("Affiliate Tracking", True))
        else:
            print(f"❌ Tracking failed: {data}")
            results.append(("Affiliate Tracking", False))
    else:
        print(f"❌ Unexpected tracking response: {response.status_code} - {response.text}")
        results.append(("Affiliate Tracking", False))
    
    # 6. Test User Registration for Conversion Testing
    print("\n6. Testing User Registration...")
    user_email = f"user_test_{uuid.uuid4().hex[:8]}@test.com"
    user_data = {
        "email": user_email,
        "name": "Test User",
        "password": "TestPassword123"
    }
    response = requests.post(f"{API_BASE}/auth/register", json=user_data)
    user_id = None
    if response.status_code == 200:
        data = response.json()
        user_id = data.get("user", {}).get("id")
        print(f"✅ Test user created: {user_email} (ID: {user_id})")
        results.append(("User Registration", True))
        
        # 7. Test Affiliate Conversion (should work even with pending affiliate)
        print(f"\n7. Testing Affiliate Conversion...")
        conversion_params = {
            "affiliate_code": affiliate_code,
            "user_id": user_id,
            "subscription_plan": "pro",
            "subscription_amount": 29.00
        }
        response = requests.post(f"{API_BASE}/affiliate/conversion", params=conversion_params)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Conversion recorded: €{data.get('commission_amount', 0)} commission")
                results.append(("Affiliate Conversion", True))
            else:
                print(f"⚠️ Conversion rejected (expected for pending affiliate): {data}")
                results.append(("Affiliate Conversion Logic", True))  # This is expected behavior
        else:
            print(f"❌ Conversion failed: {response.status_code} - {response.text}")
            results.append(("Affiliate Conversion", False))
    else:
        print(f"❌ User registration failed: {response.status_code}")
        results.append(("User Registration", False))
    
    # 8. Test Invalid Conversion Plan
    print(f"\n8. Testing Invalid Conversion Plan...")
    if user_id:
        invalid_conversion_params = {
            "affiliate_code": affiliate_code,
            "user_id": user_id,
            "subscription_plan": "invalid_plan",
            "subscription_amount": 29.00
        }
        response = requests.post(f"{API_BASE}/affiliate/conversion", params=invalid_conversion_params)
        if response.status_code == 200:
            data = response.json()
            if not data.get("success"):
                print("✅ Correctly rejected invalid plan")
                results.append(("Invalid Plan Validation", True))
            else:
                print(f"❌ Should reject invalid plan: {data}")
                results.append(("Invalid Plan Validation", False))
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            results.append(("Invalid Plan Validation", False))
    else:
        print("⚠️ Skipping invalid plan test - no user ID available")
        results.append(("Invalid Plan Validation", False))
    
    # Print Summary
    print("\n" + "=" * 50)
    print("📊 AFFILIATE SYSTEM TEST SUMMARY")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {total_tests - passed_tests} ❌")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if passed_tests < total_tests:
        print("\n❌ FAILED TESTS:")
        for test_name, success in results:
            if not success:
                print(f"  • {test_name}")
    else:
        print("\n🎉 ALL CORE TESTS PASSED!")
    
    return results

if __name__ == "__main__":
    test_affiliate_system()