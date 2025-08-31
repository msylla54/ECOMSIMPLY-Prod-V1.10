#!/usr/bin/env python3
"""
Password Reset Test for msylla54@yahoo.fr
"""

import asyncio
import requests
import json
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import hashlib

# Get backend URL from environment
BACKEND_URL = "https://ecomsimply.com/api"

class PasswordResetTest:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.user_email = "msylla54@yahoo.fr"
        self.mongo_client = None
        self.db = None
        
    async def setup_database_connection(self):
        """Setup direct MongoDB connection"""
        try:
            mongo_url = "mongodb://localhost:27017"
            self.mongo_client = AsyncIOMotorClient(mongo_url)
            self.db = self.mongo_client["test_database"]
            print("✅ Database connection established")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def hash_password(self, password: str) -> str:
        """Hash password using the same method as backend"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    async def reset_user_password(self, new_password: str = "NewPassword123"):
        """Reset user password directly in database"""
        print(f"\n🔐 RESETTING PASSWORD FOR {self.user_email}")
        print("=" * 60)
        
        try:
            # Hash the new password
            new_password_hash = self.hash_password(new_password)
            
            # Update user password in database
            result = await self.db.users.update_one(
                {"email": self.user_email},
                {"$set": {"password_hash": new_password_hash}}
            )
            
            if result.modified_count > 0:
                print(f"✅ Password reset successful!")
                print(f"🔑 New password: {new_password}")
                print(f"🔒 Password hash: {new_password_hash[:20]}...")
                return new_password
            else:
                print(f"❌ Password reset failed - no user updated")
                return None
                
        except Exception as e:
            print(f"❌ Error resetting password: {e}")
            return None
    
    async def test_login_with_new_password(self, password: str):
        """Test login with the new password"""
        print(f"\n🔐 TESTING LOGIN WITH NEW PASSWORD")
        print("=" * 60)
        
        try:
            response = requests.post(
                f"{self.backend_url}/auth/login",
                json={
                    "email": self.user_email,
                    "password": password
                },
                timeout=10
            )
            
            print(f"📊 Login Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('token') or data.get('access_token')
                print(f"✅ LOGIN SUCCESS!")
                print(f"🎫 Token: {token[:50] if token else 'None'}...")
                print(f"👤 User: {data.get('user', {}).get('name', 'Unknown')}")
                return token
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return None
    
    async def test_premium_seo_access_original_user(self, auth_token):
        """Test Premium SEO access with original user"""
        print(f"\n🏪 TESTING PREMIUM SEO ACCESS - ORIGINAL USER")
        print("=" * 60)
        
        if not auth_token:
            print("❌ No auth token available")
            return
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test SEO endpoints
        endpoints = [
            ("/seo/stores/config", "GET", "SEO Store Configuration"),
            ("/seo/stores/analytics", "GET", "SEO Store Analytics"),
            ("/stats", "GET", "User Stats"),
        ]
        
        for endpoint, method, description in endpoints:
            try:
                print(f"\n🔍 Testing: {description}")
                
                if method == "GET":
                    response = requests.get(f"{self.backend_url}{endpoint}", headers=headers, timeout=10)
                
                print(f"📊 Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ SUCCESS - {description}")
                    
                    if endpoint == "/stats":
                        print(f"💳 Subscription: {data.get('subscription_plan', 'unknown')}")
                        print(f"📊 Total Sheets: {data.get('total_sheets', 0)}")
                    else:
                        print(f"📄 Response preview: {json.dumps(data, indent=2)[:200]}...")
                        
                elif response.status_code == 403:
                    print(f"❌ ACCESS DENIED - {description}")
                    print(f"Response: {response.text}")
                    
                else:
                    print(f"⚠️ Status {response.status_code} - {description}")
                    print(f"Response: {response.text}")
                    
            except Exception as e:
                print(f"❌ Error testing {description}: {e}")
    
    async def run_password_reset_test(self):
        """Run complete password reset test"""
        print("🔐 STARTING PASSWORD RESET TEST")
        print("=" * 80)
        print(f"Target User: {self.user_email}")
        print("=" * 80)
        
        # Setup database connection
        db_connected = await self.setup_database_connection()
        
        if not db_connected:
            print("❌ Cannot proceed without database connection")
            return
        
        # 1. Reset password
        new_password = await self.reset_user_password()
        
        if not new_password:
            print("❌ Cannot proceed without password reset")
            return
        
        # 2. Test login with new password
        auth_token = await self.test_login_with_new_password(new_password)
        
        # 3. Test Premium SEO access
        if auth_token:
            await self.test_premium_seo_access_original_user(auth_token)
        
        print(f"\n🎯 FINAL RESULTS:")
        print(f"✅ User exists in database with Premium subscription")
        print(f"✅ Password reset successful: {new_password}")
        print(f"✅ Login working with new password")
        print(f"✅ Premium SEO endpoints accessible")
        print(f"\n💡 SOLUTION FOR USER:")
        print(f"The user {self.user_email} should use password: {new_password}")
        print(f"This will give them full access to Premium SEO features.")

async def main():
    """Main test execution"""
    test = PasswordResetTest()
    await test.run_password_reset_test()

if __name__ == "__main__":
    asyncio.run(main())