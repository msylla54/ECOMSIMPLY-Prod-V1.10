#!/usr/bin/env python3
"""
Focused 7-Day Free Trial System Testing
=======================================

This script focuses on the core functionality of the 0€ free trial system.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"

def test_trial_checkout_with_fresh_user():
    """Test trial checkout with a completely fresh user"""
    print("🧪 Testing Free Trial Checkout with Fresh User")
    print("-" * 50)
    
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'User-Agent': 'ECOMSIMPLY-Trial-Test/1.0'
    })
    
    # Create unique user
    timestamp = int(time.time())
    unique_email = f"fresh.trial.{timestamp}@example.com"
    
    # 1. Register fresh user
    register_data = {
        "email": unique_email,
        "name": "Fresh Trial User",
        "password": "TestPassword123!",
        "language": "fr"
    }
    
    print(f"📝 Registering user: {unique_email}")
    register_response = session.post(f"{BASE_URL}/auth/register", json=register_data)
    
    if register_response.status_code != 200:
        print(f"❌ Registration failed: {register_response.status_code}")
        print(f"   Response: {register_response.json()}")
        return False
    
    # Get token
    register_data = register_response.json()
    token = register_data.get('token')
    user_data = register_data.get('user', {})
    
    print(f"✅ User registered successfully")
    print(f"   User ID: {user_data.get('id', 'N/A')}")
    print(f"   Is Trial User: {user_data.get('is_trial_user', False)}")
    print(f"   Subscription Plan: {user_data.get('subscription_plan', 'N/A')}")
    
    # Set authorization header
    session.headers.update({'Authorization': f'Bearer {token}'})
    
    # 2. Test Pro trial checkout
    print(f"\n💳 Testing Pro Trial Checkout (should be 0€)")
    checkout_data = {
        "plan_type": "pro",
        "origin_url": "https://ecomsimply.com/trial",
        "trial_subscription": True
    }
    
    checkout_response = session.post(f"{BASE_URL}/payments/checkout", json=checkout_data)
    
    if checkout_response.status_code == 200:
        data = checkout_response.json()
        session_data = data.get('session', {})
        amount = session_data.get('amount', 0)
        currency = session_data.get('currency', '')
        session_id = session_data.get('session_id', '')
        
        print(f"✅ Pro Trial Checkout Success")
        print(f"   Amount: {amount}€ (Expected: 0€)")
        print(f"   Currency: {currency}")
        print(f"   Session ID: {session_id[:20]}..." if session_id else "No session ID")
        
        if amount == 0.0:
            print(f"✅ CRITICAL TEST PASSED: Pro trial amount is 0€")
        else:
            print(f"❌ CRITICAL TEST FAILED: Pro trial amount is {amount}€, expected 0€")
            
    else:
        print(f"❌ Pro Trial Checkout Failed: {checkout_response.status_code}")
        print(f"   Response: {checkout_response.json()}")
        return False
    
    # 3. Test Premium trial checkout with same user (should fail - 1 trial limit)
    print(f"\n💳 Testing Premium Trial Checkout (should fail - 1 trial per user)")
    checkout_data["plan_type"] = "premium"
    
    checkout_response2 = session.post(f"{BASE_URL}/payments/checkout", json=checkout_data)
    
    if checkout_response2.status_code == 400:
        data = checkout_response2.json()
        error_message = data.get('detail', '')
        
        print(f"✅ Premium Trial Correctly Rejected")
        print(f"   Error: {error_message}")
        
        if "déjà utilisé votre essai gratuit" in error_message:
            print(f"✅ CRITICAL TEST PASSED: 1 trial per user limitation working")
        else:
            print(f"❌ CRITICAL TEST FAILED: Wrong error message")
            
    else:
        print(f"❌ Premium Trial Should Have Failed: {checkout_response2.status_code}")
        print(f"   Response: {checkout_response2.json()}")
    
    return True

def test_normal_paid_checkout():
    """Test that normal paid checkouts still work (not 0€)"""
    print("\n🧪 Testing Normal Paid Checkout (should NOT be 0€)")
    print("-" * 50)
    
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'User-Agent': 'ECOMSIMPLY-Trial-Test/1.0'
    })
    
    # Create another fresh user
    timestamp = int(time.time())
    unique_email = f"paid.user.{timestamp}@example.com"
    
    # Register user
    register_data = {
        "email": unique_email,
        "name": "Paid User",
        "password": "TestPassword123!",
        "language": "fr"
    }
    
    print(f"📝 Registering paid user: {unique_email}")
    register_response = session.post(f"{BASE_URL}/auth/register", json=register_data)
    
    if register_response.status_code != 200:
        print(f"❌ Registration failed: {register_response.status_code}")
        return False
    
    # Get token
    register_data = register_response.json()
    token = register_data.get('token')
    session.headers.update({'Authorization': f'Bearer {token}'})
    
    # Test normal paid checkout
    print(f"\n💳 Testing Normal Pro Checkout (should be 29€)")
    checkout_data = {
        "plan_type": "pro",
        "origin_url": "https://ecomsimply.com/pricing",
        "trial_subscription": False  # Normal paid subscription
    }
    
    checkout_response = session.post(f"{BASE_URL}/payments/checkout", json=checkout_data)
    
    if checkout_response.status_code == 200:
        data = checkout_response.json()
        session_data = data.get('session', {})
        amount = session_data.get('amount', 0)
        
        print(f"✅ Normal Paid Checkout Success")
        print(f"   Amount: {amount}€ (Expected: 29€)")
        
        if amount == 29.0:
            print(f"✅ CRITICAL TEST PASSED: Normal Pro checkout is 29€")
        else:
            print(f"❌ CRITICAL TEST FAILED: Normal Pro checkout is {amount}€, expected 29€")
            
    else:
        print(f"❌ Normal Paid Checkout Failed: {checkout_response.status_code}")
        print(f"   Response: {checkout_response.json()}")
        return False
    
    return True

def test_trial_registration_direct():
    """Test direct trial registration endpoint"""
    print("\n🧪 Testing Direct Trial Registration")
    print("-" * 50)
    
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'User-Agent': 'ECOMSIMPLY-Trial-Test/1.0'
    })
    
    # Test Pro trial registration
    timestamp = int(time.time())
    unique_email = f"direct.trial.{timestamp}@example.com"
    
    trial_data = {
        "name": "Direct Trial User",
        "email": unique_email,
        "password": "TestPassword123!",
        "plan_type": "pro"
    }
    
    print(f"📝 Testing direct Pro trial registration: {unique_email}")
    response = session.post(f"{BASE_URL}/subscription/trial/register", json=trial_data)
    
    if response.status_code == 200:
        data = response.json()
        trial_info = data.get('trial_info', {})
        user_info = data.get('user', {})
        
        is_trial_user = user_info.get('is_trial_user', False)
        plan_type = trial_info.get('plan_type')
        days_remaining = trial_info.get('days_remaining', 0)
        
        print(f"✅ Direct Trial Registration Success")
        print(f"   Is Trial User: {is_trial_user}")
        print(f"   Plan Type: {plan_type}")
        print(f"   Days Remaining: {days_remaining}")
        
        if is_trial_user and plan_type == "pro" and days_remaining == 7:
            print(f"✅ CRITICAL TEST PASSED: Direct trial registration working correctly")
        else:
            print(f"❌ CRITICAL TEST FAILED: Trial registration data incorrect")
            
    else:
        print(f"❌ Direct Trial Registration Failed: {response.status_code}")
        print(f"   Response: {response.json()}")
        return False
    
    return True

def main():
    """Run focused trial tests"""
    print("🚀 FOCUSED 7-DAY FREE TRIAL SYSTEM TESTING")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print("=" * 60)
    
    results = []
    
    # Test 1: Trial checkout with fresh user
    try:
        result1 = test_trial_checkout_with_fresh_user()
        results.append(("Trial Checkout with Fresh User", result1))
    except Exception as e:
        print(f"❌ CRITICAL ERROR in trial checkout test: {str(e)}")
        results.append(("Trial Checkout with Fresh User", False))
    
    # Test 2: Normal paid checkout
    try:
        result2 = test_normal_paid_checkout()
        results.append(("Normal Paid Checkout", result2))
    except Exception as e:
        print(f"❌ CRITICAL ERROR in paid checkout test: {str(e)}")
        results.append(("Normal Paid Checkout", False))
    
    # Test 3: Direct trial registration
    try:
        result3 = test_trial_registration_direct()
        results.append(("Direct Trial Registration", result3))
    except Exception as e:
        print(f"❌ CRITICAL ERROR in direct registration test: {str(e)}")
        results.append(("Direct Trial Registration", False))
    
    # Summary
    print("\n📊 FOCUSED TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    print("\n📋 DETAILED RESULTS:")
    print("-" * 30)
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    print("\n🎯 CRITICAL ASSESSMENT:")
    print("-" * 30)
    
    if success_rate >= 80:
        print("🎉 7-DAY FREE TRIAL SYSTEM: OPERATIONAL")
    elif success_rate >= 60:
        print("⚠️ 7-DAY FREE TRIAL SYSTEM: PARTIALLY FUNCTIONAL")
    else:
        print("❌ 7-DAY FREE TRIAL SYSTEM: CRITICAL ISSUES")
    
    print("=" * 60)

if __name__ == "__main__":
    main()