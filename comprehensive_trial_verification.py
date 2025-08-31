#!/usr/bin/env python3
"""
Comprehensive Trial System Verification
=======================================

This script provides detailed verification of the 7-day free trial system
including user profile updates and transaction verification.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"

def test_complete_trial_flow():
    """Test complete trial flow from registration to profile verification"""
    print("🧪 COMPREHENSIVE TRIAL FLOW TESTING")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'User-Agent': 'ECOMSIMPLY-Trial-Test/1.0'
    })
    
    # Create unique user
    timestamp = int(time.time())
    unique_email = f"comprehensive.trial.{timestamp}@example.com"
    
    print(f"📝 Step 1: Register new user")
    print(f"   Email: {unique_email}")
    
    # 1. Register user
    register_data = {
        "email": unique_email,
        "name": "Comprehensive Trial User",
        "password": "TestPassword123!",
        "language": "fr"
    }
    
    register_response = session.post(f"{BASE_URL}/auth/register", json=register_data)
    
    if register_response.status_code != 200:
        print(f"❌ Registration failed: {register_response.status_code}")
        return False
    
    register_data = register_response.json()
    token = register_data.get('token')
    user_data = register_data.get('user', {})
    
    print(f"✅ User registered successfully")
    print(f"   Initial is_trial_user: {user_data.get('is_trial_user', False)}")
    print(f"   Initial subscription_plan: {user_data.get('subscription_plan', 'N/A')}")
    
    # Set authorization header
    session.headers.update({'Authorization': f'Bearer {token}'})
    
    # 2. Test direct trial registration
    print(f"\n📝 Step 2: Direct trial registration (Pro plan)")
    
    trial_data = {
        "name": "Trial User Pro",
        "email": f"trial.direct.{timestamp}@example.com",
        "password": "TestPassword123!",
        "plan_type": "pro"
    }
    
    trial_response = session.post(f"{BASE_URL}/subscription/trial/register", json=trial_data)
    
    if trial_response.status_code == 200:
        trial_data = trial_response.json()
        trial_info = trial_data.get('trial_info', {})
        trial_user_info = trial_data.get('user', {})
        trial_token = trial_data.get('token')
        
        print(f"✅ Trial registration successful")
        print(f"   Trial user is_trial_user: {trial_user_info.get('is_trial_user', False)}")
        print(f"   Trial subscription_plan: {trial_user_info.get('subscription_plan', 'N/A')}")
        print(f"   Trial plan_type: {trial_info.get('plan_type', 'N/A')}")
        print(f"   Trial days_remaining: {trial_info.get('days_remaining', 0)}")
        
        # 3. Test trial status endpoint
        print(f"\n📝 Step 3: Check trial status")
        
        trial_session = requests.Session()
        trial_session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {trial_token}'
        })
        
        status_response = trial_session.get(f"{BASE_URL}/subscription/trial/status")
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            
            print(f"✅ Trial status retrieved")
            print(f"   has_trial: {status_data.get('has_trial', False)}")
            print(f"   trial_status: {status_data.get('trial_status', 'N/A')}")
            print(f"   plan_type: {status_data.get('plan_type', 'N/A')}")
            print(f"   days_remaining: {status_data.get('days_remaining', 0)}")
            print(f"   trial_end_date: {status_data.get('trial_end_date', 'N/A')}")
            
        else:
            print(f"❌ Trial status failed: {status_response.status_code}")
            print(f"   Response: {status_response.json()}")
        
        # 4. Test user profile endpoint
        print(f"\n📝 Step 4: Check user profile")
        
        profile_response = trial_session.get(f"{BASE_URL}/users/profile")
        
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            
            print(f"✅ User profile retrieved")
            print(f"   is_trial_user: {profile_data.get('is_trial_user', False)}")
            print(f"   subscription_plan: {profile_data.get('subscription_plan', 'N/A')}")
            print(f"   trial_start_date: {profile_data.get('trial_start_date', 'N/A')}")
            print(f"   trial_end_date: {profile_data.get('trial_end_date', 'N/A')}")
            
        else:
            print(f"❌ User profile failed: {profile_response.status_code}")
            print(f"   Response: {profile_response.json()}")
        
    else:
        print(f"❌ Trial registration failed: {trial_response.status_code}")
        print(f"   Response: {trial_response.json()}")
        return False
    
    return True

def test_pricing_configuration():
    """Test pricing configuration to understand why normal checkout is 0€"""
    print("\n🧪 PRICING CONFIGURATION TESTING")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'User-Agent': 'ECOMSIMPLY-Trial-Test/1.0'
    })
    
    # 1. Test public pricing endpoint
    print(f"📝 Step 1: Check public pricing configuration")
    
    pricing_response = session.get(f"{BASE_URL}/public/plans-pricing")
    
    if pricing_response.status_code == 200:
        pricing_data = pricing_response.json()
        
        print(f"✅ Public pricing retrieved")
        
        for plan_name, plan_data in pricing_data.items():
            if isinstance(plan_data, dict):
                price = plan_data.get('price', 'N/A')
                original_price = plan_data.get('original_price', 'N/A')
                promotion_active = plan_data.get('promotion_active', False)
                
                print(f"   {plan_name.upper()}:")
                print(f"     Current Price: {price}€")
                print(f"     Original Price: {original_price}€")
                print(f"     Promotion Active: {promotion_active}")
        
    else:
        print(f"❌ Public pricing failed: {pricing_response.status_code}")
        print(f"   Response: {pricing_response.json()}")
    
    # 2. Test with admin credentials to check admin pricing
    print(f"\n📝 Step 2: Check admin pricing configuration")
    
    # Try to login as admin
    admin_login_data = {
        "email": "msylla54@yahoo.fr",
        "password": "NewPassword123"
    }
    
    admin_response = session.post(f"{BASE_URL}/auth/login", json=admin_login_data)
    
    if admin_response.status_code == 200:
        admin_data = admin_response.json()
        admin_token = admin_data.get('token')
        
        print(f"✅ Admin login successful")
        
        # Check admin pricing config
        admin_pricing_url = f"{BASE_URL}/admin/plans-config?admin_key=ECOMSIMPLY_ADMIN_2024"
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        
        admin_pricing_response = session.get(admin_pricing_url, headers=admin_headers)
        
        if admin_pricing_response.status_code == 200:
            admin_pricing_data = admin_pricing_response.json()
            
            print(f"✅ Admin pricing configuration retrieved")
            
            for plan in admin_pricing_data.get('plans', []):
                plan_name = plan.get('plan_name', 'N/A')
                price = plan.get('price', 'N/A')
                original_price = plan.get('original_price', 'N/A')
                promotion_active = plan.get('promotion_active', False)
                
                print(f"   {plan_name.upper()} (Admin Config):")
                print(f"     Current Price: {price}€")
                print(f"     Original Price: {original_price}€")
                print(f"     Promotion Active: {promotion_active}")
        
        else:
            print(f"❌ Admin pricing config failed: {admin_pricing_response.status_code}")
            print(f"   Response: {admin_pricing_response.json()}")
    
    else:
        print(f"❌ Admin login failed: {admin_response.status_code}")
        print(f"   Response: {admin_response.json()}")

def test_checkout_variations():
    """Test different checkout scenarios"""
    print("\n🧪 CHECKOUT VARIATIONS TESTING")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'User-Agent': 'ECOMSIMPLY-Trial-Test/1.0'
    })
    
    # Create a fresh user for checkout tests
    timestamp = int(time.time())
    unique_email = f"checkout.test.{timestamp}@example.com"
    
    register_data = {
        "email": unique_email,
        "name": "Checkout Test User",
        "password": "TestPassword123!",
        "language": "fr"
    }
    
    register_response = session.post(f"{BASE_URL}/auth/register", json=register_data)
    
    if register_response.status_code != 200:
        print(f"❌ Registration failed: {register_response.status_code}")
        return False
    
    register_data = register_response.json()
    token = register_data.get('token')
    session.headers.update({'Authorization': f'Bearer {token}'})
    
    print(f"✅ Test user registered: {unique_email}")
    
    # Test different checkout scenarios
    scenarios = [
        {
            "name": "Pro Trial (trial_subscription: true)",
            "data": {
                "plan_type": "pro",
                "origin_url": "https://ecomsimply.com/trial",
                "trial_subscription": True
            },
            "expected_amount": 0.0
        },
        {
            "name": "Pro Normal (trial_subscription: false)",
            "data": {
                "plan_type": "pro",
                "origin_url": "https://ecomsimply.com/pricing",
                "trial_subscription": False
            },
            "expected_amount": 29.0
        },
        {
            "name": "Pro Normal (no trial_subscription field)",
            "data": {
                "plan_type": "pro",
                "origin_url": "https://ecomsimply.com/pricing"
            },
            "expected_amount": 29.0
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📝 Scenario {i}: {scenario['name']}")
        
        checkout_response = session.post(f"{BASE_URL}/payments/checkout", json=scenario['data'])
        
        if checkout_response.status_code == 200:
            checkout_data = checkout_response.json()
            session_data = checkout_data.get('session', {})
            amount = session_data.get('amount', 0)
            
            print(f"✅ Checkout successful")
            print(f"   Amount: {amount}€ (Expected: {scenario['expected_amount']}€)")
            
            if amount == scenario['expected_amount']:
                print(f"✅ Amount matches expectation")
            else:
                print(f"❌ Amount mismatch!")
                
        elif checkout_response.status_code == 400:
            # This might be expected for trial scenarios after first trial
            checkout_data = checkout_response.json()
            error_message = checkout_data.get('detail', '')
            
            if "déjà utilisé votre essai gratuit" in error_message:
                print(f"✅ Trial limitation working correctly")
                print(f"   Error: {error_message}")
            else:
                print(f"❌ Unexpected error: {error_message}")
        else:
            print(f"❌ Checkout failed: {checkout_response.status_code}")
            print(f"   Response: {checkout_response.json()}")

def main():
    """Run comprehensive trial verification"""
    print("🚀 COMPREHENSIVE 7-DAY FREE TRIAL SYSTEM VERIFICATION")
    print("=" * 70)
    print(f"Base URL: {BASE_URL}")
    print("=" * 70)
    
    try:
        # Test 1: Complete trial flow
        test_complete_trial_flow()
        
        # Test 2: Pricing configuration
        test_pricing_configuration()
        
        # Test 3: Checkout variations
        test_checkout_variations()
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
    
    print("\n🎯 VERIFICATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()