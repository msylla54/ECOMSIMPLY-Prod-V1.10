#!/usr/bin/env python3
"""
Check admin user subscription plan
"""

import requests
import json

BASE_URL = "https://ecomsimply.com/api"

# Create admin user
admin_data = {
    "email": "debug_admin@test.com",
    "name": "Debug Admin",
    "password": "SecurePass123!",
    "admin_key": "ECOMSIMPLY_ADMIN_2024",
    "language": "fr"
}

response = requests.post(f"{BASE_URL}/auth/register", json=admin_data)
if response.status_code == 200:
    data = response.json()
    token = data.get("token")
    user = data.get("user")
    
    print(f"Admin user created:")
    print(f"  Email: {user.get('email')}")
    print(f"  Is Admin: {user.get('is_admin')}")
    print(f"  Subscription Plan: {user.get('subscription_plan')}")
    
    # Get user stats to see subscription plan
    headers = {"Authorization": f"Bearer {token}"}
    stats_response = requests.get(f"{BASE_URL}/stats", headers=headers)
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print(f"  Stats Subscription Plan: {stats.get('subscription_plan')}")
    else:
        print(f"  Stats request failed: {stats_response.status_code}")
else:
    print(f"Admin user creation failed: {response.status_code} - {response.text}")