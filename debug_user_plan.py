#!/usr/bin/env python3
"""
Debug User Plan - Check admin user subscription plan
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://ecomsimply.com/api"

async def debug_user_plan():
    """Debug the admin user's subscription plan"""
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        # Authenticate as admin
        auth_data = {
            "email": "msylla54@gmail.com",
            "password": "AdminEcomsimply"
        }
        
        print("🔐 Authenticating...")
        async with session.post(f"{BACKEND_URL}/auth/login", json=auth_data) as response:
            if response.status != 200:
                print(f"❌ Auth failed: {response.status}")
                return
            
            result = await response.json()
            token = result.get("token")
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ Authenticated successfully")
            
            # Get user info
            user_info = result.get("user", {})
            print(f"\n👤 USER INFO:")
            print(f"   Email: {user_info.get('email', 'N/A')}")
            print(f"   Name: {user_info.get('name', 'N/A')}")
            print(f"   Subscription Plan: {user_info.get('subscription_plan', 'N/A')}")
            print(f"   Is Admin: {user_info.get('is_admin', 'N/A')}")
        
        # Get user stats to confirm plan
        print("\n📊 Getting user stats...")
        async with session.get(f"{BACKEND_URL}/stats", headers=headers) as response:
            if response.status == 200:
                stats = await response.json()
                print(f"   Subscription Plan from stats: {stats.get('subscription_plan', 'N/A')}")
            else:
                print(f"   ❌ Stats error: {response.status}")

if __name__ == "__main__":
    asyncio.run(debug_user_plan())