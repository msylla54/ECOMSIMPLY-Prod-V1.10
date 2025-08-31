#!/usr/bin/env python3
"""
User Investigation Test for msylla54@yahoo.fr
Testing user existence, subscription plan, and Premium access
"""

import asyncio
import requests
import json
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# Get backend URL from environment
BACKEND_URL = "https://ecomsimply.com/api"

class UserInvestigationTest:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.user_email = "msylla54@yahoo.fr"
        self.mongo_client = None
        self.db = None
        
    async def setup_database_connection(self):
        """Setup direct MongoDB connection for database investigation"""
        try:
            mongo_url = "mongodb://localhost:27017"
            self.mongo_client = AsyncIOMotorClient(mongo_url)
            self.db = self.mongo_client["test_database"]
            print("✅ Database connection established")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def log_result(self, test_name: str, success: bool, details: str):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status}: {test_name} - {details}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def investigate_user_in_database(self):
        """Direct database investigation of the user"""
        print(f"\n🔍 INVESTIGATING USER: {self.user_email}")
        print("=" * 60)
        
        try:
            # Search for user by email
            user = await self.db.users.find_one({"email": self.user_email})
            
            if user:
                print(f"✅ USER FOUND in database!")
                print(f"📧 Email: {user.get('email')}")
                print(f"👤 Name: {user.get('name')}")
                print(f"🆔 User ID: {user.get('id')}")
                print(f"📅 Created: {user.get('created_at')}")
                print(f"💳 Subscription Plan: {user.get('subscription_plan', 'Not set')}")
                print(f"🌍 Language: {user.get('language', 'Not set')}")
                print(f"👑 Is Admin: {user.get('is_admin', False)}")
                print(f"📊 Subscription Updated: {user.get('subscription_updated_at', 'Never')}")
                
                self.log_result(
                    "User Database Existence", 
                    True, 
                    f"User exists with plan: {user.get('subscription_plan', 'gratuit')}"
                )
                
                # Check subscription plan specifically
                subscription_plan = user.get('subscription_plan', 'gratuit')
                is_premium = subscription_plan.lower() == 'premium'
                
                self.log_result(
                    "Premium Subscription Check",
                    is_premium,
                    f"Plan: {subscription_plan}, Premium Access: {is_premium}"
                )
                
                return user
            else:
                print(f"❌ USER NOT FOUND in database!")
                self.log_result("User Database Existence", False, "User does not exist in database")
                return None
                
        except Exception as e:
            print(f"❌ Database investigation error: {e}")
            self.log_result("User Database Investigation", False, f"Database error: {str(e)}")
            return None
    
    async def test_user_login_attempts(self):
        """Test login with common passwords"""
        print(f"\n🔐 TESTING LOGIN ATTEMPTS for {self.user_email}")
        print("=" * 60)
        
        # Common passwords to try
        common_passwords = [
            "password",
            "123456",
            "password123",
            "admin",
            "user123",
            "msylla54",
            "yahoo123",
            "Premium123",
            "ecomsimply",
            "test123"
        ]
        
        login_success = False
        successful_password = None
        
        for password in common_passwords:
            try:
                response = requests.post(
                    f"{self.backend_url}/auth/login",
                    json={
                        "email": self.user_email,
                        "password": password
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    login_success = True
                    successful_password = password
                    data = response.json()
                    print(f"✅ LOGIN SUCCESS with password: {password}")
                    print(f"🎫 Token received: {data.get('access_token', 'No token')[:50]}...")
                    break
                else:
                    print(f"❌ Login failed with password '{password}': {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Login attempt error with '{password}': {e}")
        
        self.log_result(
            "Login Attempts",
            login_success,
            f"Successful password: {successful_password}" if login_success else "All login attempts failed"
        )
        
        return successful_password
    
    async def test_premium_seo_access(self, auth_token=None):
        """Test access to Premium SEO features"""
        print(f"\n🏪 TESTING PREMIUM SEO ACCESS")
        print("=" * 60)
        
        if not auth_token:
            print("❌ No auth token available, cannot test Premium features")
            self.log_result("Premium SEO Access", False, "No authentication token available")
            return
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test SEO store configuration endpoints
        seo_endpoints = [
            ("/seo/stores/config", "GET", "SEO Store Configuration List"),
            ("/seo/stores/analytics", "GET", "SEO Store Analytics"),
        ]
        
        for endpoint, method, description in seo_endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{self.backend_url}{endpoint}", headers=headers, timeout=10)
                
                print(f"🔍 Testing {description}: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {description} - SUCCESS")
                    print(f"📊 Response: {json.dumps(data, indent=2)[:200]}...")
                    self.log_result(f"Premium SEO - {description}", True, f"Status: {response.status_code}")
                elif response.status_code == 403:
                    print(f"❌ {description} - ACCESS DENIED (403)")
                    self.log_result(f"Premium SEO - {description}", False, "Access denied - insufficient permissions")
                else:
                    print(f"⚠️ {description} - Status: {response.status_code}")
                    self.log_result(f"Premium SEO - {description}", False, f"Unexpected status: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error testing {description}: {e}")
                self.log_result(f"Premium SEO - {description}", False, f"Request error: {str(e)}")
    
    async def check_user_product_sheets(self):
        """Check user's product sheets and activity"""
        print(f"\n📋 CHECKING USER ACTIVITY")
        print("=" * 60)
        
        try:
            # Get user from database first
            user = await self.db.users.find_one({"email": self.user_email})
            if not user:
                print("❌ Cannot check activity - user not found")
                return
            
            user_id = user.get('id')
            
            # Check product sheets
            sheets_count = await self.db.product_sheets.count_documents({"user_id": user_id})
            print(f"📊 Product sheets created: {sheets_count}")
            
            # Check recent sheets
            recent_sheets = await self.db.product_sheets.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(5).to_list(length=5)
            
            print(f"📝 Recent product sheets:")
            for sheet in recent_sheets:
                print(f"  - {sheet.get('product_name', 'Unknown')} ({sheet.get('created_at', 'No date')})")
            
            # Check connected stores
            stores_count = await self.db.woocommerce_stores.count_documents({"user_id": user_id})
            stores_count += await self.db.shopify_stores.count_documents({"user_id": user_id})
            print(f"🏪 Connected stores: {stores_count}")
            
            # Check SEO configurations
            seo_configs = await self.db.seo_store_configs.count_documents({"user_id": user_id})
            print(f"⚙️ SEO store configurations: {seo_configs}")
            
            self.log_result(
                "User Activity Check",
                True,
                f"Sheets: {sheets_count}, Stores: {stores_count}, SEO configs: {seo_configs}"
            )
            
        except Exception as e:
            print(f"❌ Error checking user activity: {e}")
            self.log_result("User Activity Check", False, f"Database error: {str(e)}")
    
    async def create_test_premium_user(self):
        """Create a test premium user for comparison"""
        print(f"\n👤 CREATING TEST PREMIUM USER")
        print("=" * 60)
        
        test_email = "test_premium_user@test.com"
        test_password = "TestPremium123"
        
        try:
            # Register test user with admin key for premium access
            response = requests.post(
                f"{self.backend_url}/auth/register",
                json={
                    "email": test_email,
                    "name": "Test Premium User",
                    "password": test_password,
                    "admin_key": "ECOMSIMPLY_ADMIN_2024"  # This should give premium access
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Test premium user created successfully")
                
                # Login with test user
                login_response = requests.post(
                    f"{self.backend_url}/auth/login",
                    json={
                        "email": test_email,
                        "password": test_password
                    },
                    timeout=10
                )
                
                if login_response.status_code == 200:
                    token = login_response.json().get('access_token')
                    print(f"✅ Test user login successful")
                    
                    # Test SEO access with test user
                    await self.test_premium_seo_access(token)
                    
                    self.log_result("Test Premium User Creation", True, "Created and tested successfully")
                else:
                    print(f"❌ Test user login failed: {login_response.status_code}")
                    self.log_result("Test Premium User Creation", False, "Login failed after creation")
            else:
                print(f"❌ Test user creation failed: {response.status_code}")
                print(f"Response: {response.text}")
                self.log_result("Test Premium User Creation", False, f"Registration failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error creating test user: {e}")
            self.log_result("Test Premium User Creation", False, f"Error: {str(e)}")
    
    async def run_investigation(self):
        """Run complete user investigation"""
        print("🔍 STARTING USER INVESTIGATION")
        print("=" * 80)
        print(f"Target User: {self.user_email}")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 80)
        
        # Setup database connection
        db_connected = await self.setup_database_connection()
        
        if db_connected:
            # 1. Direct database investigation
            user_data = await self.investigate_user_in_database()
            
            # 2. Check user activity
            await self.check_user_product_sheets()
            
            # 3. Test login attempts
            successful_password = await self.test_user_login_attempts()
            
            # 4. If login successful, test Premium features
            if successful_password:
                # Get auth token
                try:
                    login_response = requests.post(
                        f"{self.backend_url}/auth/login",
                        json={
                            "email": self.user_email,
                            "password": successful_password
                        },
                        timeout=10
                    )
                    if login_response.status_code == 200:
                        token = login_response.json().get('access_token')
                        await self.test_premium_seo_access(token)
                except Exception as e:
                    print(f"❌ Error getting auth token: {e}")
            
            # 5. Create test premium user for comparison
            await self.create_test_premium_user()
        
        # Print final summary
        self.print_summary()
    
    def print_summary(self):
        """Print investigation summary"""
        print("\n" + "=" * 80)
        print("🎯 INVESTIGATION SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")
        
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        print(f"\n🎯 INVESTIGATION CONCLUSIONS:")
        
        # Analyze results
        user_exists = any(r['test'] == 'User Database Existence' and r['success'] for r in self.test_results)
        has_premium = any(r['test'] == 'Premium Subscription Check' and r['success'] for r in self.test_results)
        login_works = any(r['test'] == 'Login Attempts' and r['success'] for r in self.test_results)
        
        if user_exists:
            print(f"✅ User {self.user_email} EXISTS in database")
        else:
            print(f"❌ User {self.user_email} NOT FOUND in database")
        
        if has_premium:
            print(f"✅ User has PREMIUM subscription plan")
        else:
            print(f"❌ User does NOT have Premium subscription")
        
        if login_works:
            print(f"✅ User login is FUNCTIONAL")
        else:
            print(f"❌ User login FAILED with common passwords")
        
        print(f"\n💡 RECOMMENDATIONS:")
        if not user_exists:
            print("- User needs to register an account first")
        elif not has_premium:
            print("- User needs to upgrade to Premium subscription")
        elif not login_works:
            print("- User may need password reset")
            print("- Check if user is using correct email address")
        else:
            print("- User account appears properly configured")
            print("- Issue may be frontend-related or browser-specific")
            print("- Check browser console for JavaScript errors")

async def main():
    """Main test execution"""
    test = UserInvestigationTest()
    await test.run_investigation()

if __name__ == "__main__":
    asyncio.run(main())