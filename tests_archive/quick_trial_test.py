#!/usr/bin/env python3
"""
Quick Trial Test - Test endpoints with shorter timeouts
"""

import requests
import json
import time
from datetime import datetime
import threading

# Configuration
BASE_URL = "https://ecomsimply.com/api"

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_with_timeout(func, timeout=30):
    """Run a function with a timeout"""
    result = [None]
    exception = [None]
    
    def target():
        try:
            result[0] = func()
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout)
    
    if thread.is_alive():
        log(f"❌ Function timed out after {timeout} seconds")
        return None
    
    if exception[0]:
        log(f"❌ Function failed: {exception[0]}")
        return None
        
    return result[0]

def register_trial():
    """Register a trial user"""
    timestamp = int(time.time())
    trial_data = {
        "name": "Quick Test User",
        "email": f"quicktest{timestamp}@test.fr",
        "password": "TestPassword123!",
        "plan_type": "pro"
    }
    
    log("Attempting trial registration...")
    response = requests.post(f"{BASE_URL}/subscription/trial/register", 
                           json=trial_data, timeout=25)
    
    log(f"Registration response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        log("✅ Trial registration successful!")
        return data.get('token'), data
    else:
        log(f"❌ Registration failed: {response.text[:200]}")
        return None, None

def test_status(token):
    """Test trial status"""
    if not token:
        return False
        
    log("Testing trial status...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/subscription/trial/status", 
                          headers=headers, timeout=10)
    
    log(f"Status response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        log(f"✅ Status: {data.get('trial_status')} - {data.get('days_remaining')} days left")
        return True
    else:
        log(f"❌ Status failed: {response.text[:200]}")
        return False

def main():
    log("=== QUICK TRIAL SUBSCRIPTION TEST ===")
    
    # Test registration with timeout
    log("Testing trial registration (with 30s timeout)...")
    result = test_with_timeout(register_trial, 30)
    
    if result:
        token, data = result
        log("Registration completed successfully!")
        
        # Test status
        status_ok = test_status(token)
        
        log("=== RESULTS ===")
        log(f"Registration: ✅ SUCCESS")
        log(f"Status: {'✅ SUCCESS' if status_ok else '❌ FAILED'}")
    else:
        log("=== RESULTS ===")
        log("Registration: ❌ FAILED (timeout or error)")
        log("Status: ❌ SKIPPED")

if __name__ == "__main__":
    main()