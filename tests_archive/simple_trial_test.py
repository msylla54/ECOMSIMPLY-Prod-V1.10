#!/usr/bin/env python3
"""
Simple Trial Subscription System Test
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def test_trial_registration():
    """Test trial registration endpoint"""
    log("Testing trial registration with Pro plan...")
    
    timestamp = int(time.time())
    trial_data = {
        "name": "Jean Dupont Test",
        "email": f"jean.test{timestamp}@test.fr",
        "password": "TestPassword123!",
        "plan_type": "pro",
        "affiliate_code": None
    }
    
    try:
        response = requests.post(f"{BASE_URL}/subscription/trial/register", 
                               json=trial_data, timeout=10)
        
        log(f"Response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            log("✅ Trial registration successful!")
            log(f"User: {data.get('user', {}).get('name', 'Unknown')}")
            log(f"Plan: {data.get('trial', {}).get('plan_type', 'Unknown')}")
            return data.get('token'), data.get('user', {}).get('id')
        else:
            log(f"❌ Trial registration failed: {response.text}")
            return None, None
            
    except Exception as e:
        log(f"❌ Trial registration error: {str(e)}")
        return None, None

def test_trial_status(token):
    """Test trial status endpoint"""
    if not token:
        log("❌ No token available for status test")
        return False
        
    log("Testing trial status endpoint...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/subscription/trial/status", 
                              headers=headers, timeout=10)
        
        log(f"Response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            log("✅ Trial status retrieved successfully!")
            log(f"Has trial: {data.get('has_trial')}")
            log(f"Status: {data.get('trial_status')}")
            log(f"Plan: {data.get('plan_type')}")
            log(f"Days remaining: {data.get('days_remaining')}")
            return True
        else:
            log(f"❌ Trial status failed: {response.text}")
            return False
            
    except Exception as e:
        log(f"❌ Trial status error: {str(e)}")
        return False

def test_trial_cancellation(token):
    """Test trial cancellation endpoint"""
    if not token:
        log("❌ No token available for cancellation test")
        return False
        
    log("Testing trial cancellation...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/subscription/trial/cancel", 
                               headers=headers, timeout=10)
        
        log(f"Response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            log("✅ Trial cancellation successful!")
            log(f"Message: {data.get('message')}")
            log(f"Downgraded to: {data.get('downgraded_to')}")
            return True
        else:
            log(f"❌ Trial cancellation failed: {response.text}")
            return False
            
    except Exception as e:
        log(f"❌ Trial cancellation error: {str(e)}")
        return False

def main():
    log("=" * 50)
    log("SIMPLE TRIAL SUBSCRIPTION TESTS")
    log("=" * 50)
    
    # Test 1: Trial Registration
    token, user_id = test_trial_registration()
    
    # Test 2: Trial Status
    status_success = test_trial_status(token)
    
    # Test 3: Trial Cancellation
    cancel_success = test_trial_cancellation(token)
    
    # Summary
    log("=" * 50)
    log("TEST RESULTS:")
    log(f"Registration: {'✅ PASSED' if token else '❌ FAILED'}")
    log(f"Status: {'✅ PASSED' if status_success else '❌ FAILED'}")
    log(f"Cancellation: {'✅ PASSED' if cancel_success else '❌ FAILED'}")
    log("=" * 50)

if __name__ == "__main__":
    main()