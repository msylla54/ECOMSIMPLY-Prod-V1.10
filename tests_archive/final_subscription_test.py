#!/usr/bin/env python3
"""
ECOMSIMPLY Final Subscription Test with Proper Authentication
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://ecomsimply.com"

async def test_with_proper_auth():
    """Test subscription endpoints with proper authentication"""
    print("🎯 FINAL SUBSCRIPTION TEST WITH AUTHENTICATION")
    print("=" * 50)
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Authenticate with correct credentials
        login_data = {
            "email": "msylla54@gmail.com",
            "password": "AdminEcomsimply"
        }
        
        print("🔐 Authenticating...")
        async with session.post(f"{BACKEND_URL}/api/auth/login", json=login_data) as response:
            if response.status == 200:
                data = await response.json()
                # Use 'token' field, not 'access_token'
                auth_token = data.get('token')
                print(f"  ✅ Authentication successful")
                print(f"  🔑 Token: {auth_token[:30]}...")
                
                # Test status endpoint with proper auth
                print("\n📊 Testing status endpoint with authentication...")
                headers = {"Authorization": f"Bearer {auth_token}"}
                async with session.get(f"{BACKEND_URL}/api/subscription/status", headers=headers) as status_response:
                    if status_response.status == 200:
                        status_data = await status_response.json()
                        print(f"  ✅ Status endpoint working!")
                        print(f"  📦 Response: {json.dumps(status_data, indent=2)}")
                    else:
                        error_text = await status_response.text()
                        print(f"  ❌ Status endpoint failed: {status_response.status} - {error_text}")
                
                # Test incomplete endpoint with auth
                print("\n⏳ Testing incomplete endpoint with authentication...")
                async with session.get(f"{BACKEND_URL}/api/subscription/incomplete", headers=headers) as incomplete_response:
                    if incomplete_response.status == 404:
                        print(f"  ❌ CONFIRMED: /api/subscription/incomplete does NOT exist (404)")
                        print(f"  🚨 This is the ROOT CAUSE of frontend error!")
                    elif incomplete_response.status == 200:
                        incomplete_data = await incomplete_response.json()
                        print(f"  ✅ Incomplete endpoint working!")
                        print(f"  📦 Response: {json.dumps(incomplete_data, indent=2)}")
                    else:
                        error_text = await incomplete_response.text()
                        print(f"  ❌ Incomplete endpoint error: {incomplete_response.status} - {error_text}")
            else:
                print(f"  ❌ Authentication failed: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_with_proper_auth())