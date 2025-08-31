#!/usr/bin/env python3
"""
Focused Bootstrap and API Testing for ECOMSIMPLY
"""

import asyncio
import aiohttp
import json
import hashlib

BACKEND_URL = "https://ecomsimply.com"
API_BASE = f"{BACKEND_URL}/api"

async def test_bootstrap_and_apis():
    """Test bootstrap functionality and main APIs"""
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        
        print("🚀 Testing ECOMSIMPLY Backend - Bootstrap & APIs")
        print("=" * 60)
        
        # Test 1: Health endpoint
        print("\n1. Testing Health Endpoint...")
        try:
            async with session.get(f"{API_BASE}/health") as response:
                data = await response.json()
                print(f"   Status: {response.status}")
                print(f"   Database: {data.get('database', {}).get('status', 'unknown')}")
                print(f"   Uptime: {data.get('uptime', 0)}s")
                if response.status == 200:
                    print("   ✅ Health endpoint working")
                else:
                    print("   ❌ Health endpoint failed")
        except Exception as e:
            print(f"   ❌ Health endpoint error: {e}")
        
        # Test 2: Bootstrap with correct token
        print("\n2. Testing Bootstrap with Correct Token...")
        try:
            headers = {
                'Content-Type': 'application/json',
                'x-bootstrap-token': 'ECS-Bootstrap-2025-Secure-Token'
            }
            
            async with session.post(f"{API_BASE}/admin/bootstrap", headers=headers, json={}) as response:
                data = await response.json()
                print(f"   Status: {response.status}")
                print(f"   Response: {json.dumps(data, indent=2)}")
                
                if response.status == 200:
                    print("   ✅ Bootstrap successful!")
                else:
                    print("   ❌ Bootstrap failed")
                    
        except Exception as e:
            print(f"   ❌ Bootstrap error: {e}")
        
        # Test 3: Admin login
        print("\n3. Testing Admin Login...")
        try:
            # First, let's hash the password properly
            import bcrypt
            password = "ECS-Temp#2025-08-22!"
            
            # Try login
            login_data = {
                "email": "msylla54@gmail.com",
                "password": password
            }
            
            async with session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                data = await response.json()
                print(f"   Status: {response.status}")
                
                if response.status == 200:
                    print("   ✅ Admin login successful!")
                    print(f"   User ID: {data.get('user', {}).get('id', 'unknown')}")
                    auth_token = data.get('access_token')
                    if auth_token:
                        print("   ✅ Auth token received")
                else:
                    print("   ❌ Admin login failed")
                    print(f"   Error: {data.get('detail', 'Unknown error')}")
                    
        except Exception as e:
            print(f"   ❌ Admin login error: {e}")
        
        # Test 4: Main API endpoints
        print("\n4. Testing Main API Endpoints...")
        endpoints = [
            ("/testimonials", "Testimonials"),
            ("/stats/public", "Public Stats"),
            ("/public/plans-pricing", "Plans Pricing")
        ]
        
        for endpoint, name in endpoints:
            try:
                async with session.get(f"{API_BASE}{endpoint}") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ {name}: Working (Status: {response.status})")
                    else:
                        print(f"   ❌ {name}: Failed (Status: {response.status})")
            except Exception as e:
                print(f"   ❌ {name}: Error - {e}")
        
        # Test 5: Database operations check
        print("\n5. Testing Database Operations...")
        try:
            async with session.get(f"{API_BASE}/stats/public") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Database operations working")
                    print(f"   Stats: {json.dumps(data, indent=2)}")
                else:
                    print(f"   ❌ Database operations failed: {response.status}")
        except Exception as e:
            print(f"   ❌ Database operations error: {e}")
        
        print("\n" + "=" * 60)
        print("🏁 Testing completed!")

if __name__ == "__main__":
    asyncio.run(test_bootstrap_and_apis())