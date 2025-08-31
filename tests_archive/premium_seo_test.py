#!/usr/bin/env python3
"""
Premium SEO Access Test - Testing with working credentials
"""

import asyncio
import requests
import json
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://ecomsimply.com/api"

class PremiumSEOAccessTest:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        
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
    
    async def get_premium_auth_token(self):
        """Get auth token for premium user"""
        print("🔐 GETTING PREMIUM AUTH TOKEN")
        print("=" * 50)
        
        # Use the test premium user we created
        test_email = "test_premium_user@test.com"
        test_password = "TestPremium123"
        
        try:
            response = requests.post(
                f"{self.backend_url}/auth/login",
                json={
                    "email": test_email,
                    "password": test_password
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('token') or data.get('access_token')  # Try both field names
                print(f"✅ Premium auth token obtained: {token[:50] if token else 'None'}...")
                if token:
                    self.log_result("Premium Auth Token", True, "Successfully obtained auth token")
                    return token
                else:
                    print("❌ No token in response")
                    print(f"Response data: {data}")
                    self.log_result("Premium Auth Token", False, "No token in response")
                    return None
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(f"Response: {response.text}")
                self.log_result("Premium Auth Token", False, f"Login failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting auth token: {e}")
            self.log_result("Premium Auth Token", False, f"Error: {str(e)}")
            return None
    
    async def test_seo_stores_endpoints(self, auth_token):
        """Test all SEO stores endpoints"""
        print("\n🏪 TESTING SEO STORES ENDPOINTS")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test endpoints
        endpoints = [
            ("/seo/stores/config", "GET", "SEO Store Configuration List"),
            ("/seo/stores/analytics", "GET", "SEO Store Analytics"),
        ]
        
        for endpoint, method, description in endpoints:
            try:
                print(f"\n🔍 Testing: {description}")
                print(f"📡 {method} {endpoint}")
                
                if method == "GET":
                    response = requests.get(f"{self.backend_url}{endpoint}", headers=headers, timeout=10)
                
                print(f"📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ SUCCESS - {description}")
                    print(f"📄 Response preview: {json.dumps(data, indent=2)[:300]}...")
                    self.log_result(f"SEO Endpoint - {description}", True, f"Status: {response.status_code}")
                    
                elif response.status_code == 403:
                    print(f"❌ ACCESS DENIED - {description}")
                    print(f"🚫 Response: {response.text}")
                    self.log_result(f"SEO Endpoint - {description}", False, "Access denied (403)")
                    
                elif response.status_code == 401:
                    print(f"❌ UNAUTHORIZED - {description}")
                    print(f"🔐 Response: {response.text}")
                    self.log_result(f"SEO Endpoint - {description}", False, "Unauthorized (401)")
                    
                else:
                    print(f"⚠️ UNEXPECTED STATUS - {description}")
                    print(f"📄 Response: {response.text}")
                    self.log_result(f"SEO Endpoint - {description}", False, f"Status: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ ERROR testing {description}: {e}")
                self.log_result(f"SEO Endpoint - {description}", False, f"Request error: {str(e)}")
    
    async def test_user_stats_endpoint(self, auth_token):
        """Test user stats to verify premium status"""
        print("\n👤 TESTING USER STATS (Premium Verification)")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        try:
            response = requests.get(f"{self.backend_url}/stats", headers=headers, timeout=10)
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                subscription_plan = data.get('subscription_plan', 'unknown')
                print(f"✅ User Stats Retrieved")
                print(f"💳 Subscription Plan: {subscription_plan}")
                print(f"📊 Total Sheets: {data.get('total_sheets', 0)}")
                print(f"📅 Account Created: {data.get('account_created', 'unknown')}")
                
                is_premium = subscription_plan.lower() == 'premium'
                self.log_result(
                    "User Stats - Premium Verification", 
                    is_premium, 
                    f"Plan: {subscription_plan}, Is Premium: {is_premium}"
                )
            else:
                print(f"❌ Failed to get user stats: {response.status_code}")
                print(f"Response: {response.text}")
                self.log_result("User Stats - Premium Verification", False, f"Failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error getting user stats: {e}")
            self.log_result("User Stats - Premium Verification", False, f"Error: {str(e)}")
    
    async def test_create_seo_store_config(self, auth_token):
        """Test creating SEO store configuration"""
        print("\n⚙️ TESTING SEO STORE CONFIG CREATION")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First, let's try to create a test store connection
        print("🏪 Creating test WooCommerce store...")
        
        store_data = {
            "store_name": "Test Premium Store",
            "store_url": "https://test-premium-store.com",
            "consumer_key": "test_key_123",
            "consumer_secret": "test_secret_456"
        }
        
        try:
            # Create WooCommerce store
            store_response = requests.post(
                f"{self.backend_url}/ecommerce/woocommerce/connect",
                json=store_data,
                headers=headers,
                timeout=10
            )
            
            print(f"📊 Store Creation Status: {store_response.status_code}")
            
            if store_response.status_code == 200:
                store_result = store_response.json()
                store_id = store_result.get('store_id')
                print(f"✅ Test store created with ID: {store_id}")
                
                # Now try to create SEO config for this store
                if store_id:
                    print(f"⚙️ Creating SEO config for store {store_id}...")
                    
                    seo_config_data = {
                        "scraping_enabled": True,
                        "scraping_frequency": "daily",
                        "target_keywords": ["premium", "quality", "best"],
                        "target_categories": ["electronics", "fashion"],
                        "competitor_urls": ["https://competitor1.com", "https://competitor2.com"],
                        "auto_optimization_enabled": True,
                        "auto_publication_enabled": False,
                        "confidence_threshold": 0.8,
                        "geographic_focus": ["FR", "EU"],
                        "price_monitoring_enabled": True,
                        "content_optimization_enabled": True,
                        "keyword_tracking_enabled": True
                    }
                    
                    config_response = requests.put(
                        f"{self.backend_url}/seo/stores/{store_id}/config",
                        json=seo_config_data,
                        headers=headers,
                        timeout=10
                    )
                    
                    print(f"📊 SEO Config Status: {config_response.status_code}")
                    
                    if config_response.status_code == 200:
                        print(f"✅ SEO configuration created successfully")
                        self.log_result("SEO Store Config Creation", True, "Successfully created SEO config")
                    else:
                        print(f"❌ SEO config creation failed: {config_response.status_code}")
                        print(f"Response: {config_response.text}")
                        self.log_result("SEO Store Config Creation", False, f"Failed: {config_response.status_code}")
                else:
                    print(f"❌ No store ID returned")
                    self.log_result("SEO Store Config Creation", False, "No store ID returned")
            else:
                print(f"❌ Store creation failed: {store_response.status_code}")
                print(f"Response: {store_response.text}")
                self.log_result("SEO Store Config Creation", False, f"Store creation failed: {store_response.status_code}")
                
        except Exception as e:
            print(f"❌ Error in SEO config creation: {e}")
            self.log_result("SEO Store Config Creation", False, f"Error: {str(e)}")
    
    async def run_premium_seo_tests(self):
        """Run all Premium SEO access tests"""
        print("🏪 STARTING PREMIUM SEO ACCESS TESTS")
        print("=" * 80)
        print(f"Backend URL: {self.backend_url}")
        print("=" * 80)
        
        # 1. Get premium auth token
        auth_token = await self.get_premium_auth_token()
        
        if not auth_token:
            print("❌ Cannot proceed without auth token")
            return
        
        print(f"🎫 Using auth token: {auth_token[:50]}...")
        
        # 2. Verify premium status
        await self.test_user_stats_endpoint(auth_token)
        
        # 3. Test SEO stores endpoints
        await self.test_seo_stores_endpoints(auth_token)
        
        # 4. Test creating SEO store config
        await self.test_create_seo_store_config(auth_token)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🎯 PREMIUM SEO ACCESS TEST SUMMARY")
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

async def main():
    """Main test execution"""
    test = PremiumSEOAccessTest()
    await test.run_premium_seo_tests()

if __name__ == "__main__":
    asyncio.run(main())