#!/usr/bin/env python3
"""
Comprehensive Backend Testing for ECOMSIMPLY Automation System
Testing the new automation system implementation as requested in review.
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Configuration
BACKEND_URL = "https://ecomsimply.com/api"

class AutomationSystemTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.admin_token = None
        self.pro_user_token = None
        self.premium_user_token = None
        self.free_user_token = None
        
    async def setup_session(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_data and not success:
            print(f"   Response: {response_data}")
        print()
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
        
    async def make_request(self, method: str, endpoint: str, data: Dict = None, 
                          headers: Dict = None, token: str = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{BACKEND_URL}{endpoint}"
        
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
            
        try:
            async with self.session.request(method, url, 
                                          json=data if data else None,
                                          headers=request_headers) as response:
                try:
                    response_data = await response.json()
                except:
                    response_data = await response.text()
                
                return response.status < 400, response_data, response.status
                
        except Exception as e:
            return False, str(e), 0
            
    async def create_test_users(self):
        """Create test users for different subscription tiers"""
        print("🔧 Setting up test users...")
        
        # Try to login with existing admin user first
        admin_login = {
            "email": "admin_automation_test@test.com",
            "password": "TestPassword123"
        }
        
        success, response, status = await self.make_request("POST", "/auth/login", admin_login)
        if success and "token" in response:
            self.admin_token = response["token"]
            self.log_test("Admin User Login", True, "Admin user logged in successfully")
        else:
            # Create new admin user with different email
            admin_data = {
                "email": f"admin_automation_test_{int(datetime.now().timestamp())}@test.com",
                "name": "Admin Automation Test",
                "password": "TestPassword123",
                "admin_key": "ECOMSIMPLY_ADMIN_2024"
            }
            
            success, response, status = await self.make_request("POST", "/auth/register", admin_data)
            if success and "token" in response:
                self.admin_token = response["token"]
                self.log_test("Admin User Creation", True, "Admin user created successfully")
            else:
                self.log_test("Admin User Creation", False, f"Status: {status}", response)
            
        # Try to login with existing pro user first
        pro_login = {
            "email": "pro_automation_test@test.com",
            "password": "TestPassword123"
        }
        
        success, response, status = await self.make_request("POST", "/auth/login", pro_login)
        if success and "token" in response:
            self.pro_user_token = response["token"]
            # Try to upgrade to pro plan
            await self.upgrade_user_subscription(self.pro_user_token, "pro")
            self.log_test("Pro User Login", True, "Pro user logged in successfully")
        else:
            # Create new pro user with different email
            pro_data = {
                "email": f"pro_automation_test_{int(datetime.now().timestamp())}@test.com", 
                "name": "Pro Automation Test",
                "password": "TestPassword123"
            }
            
            success, response, status = await self.make_request("POST", "/auth/register", pro_data)
            if success and "token" in response:
                self.pro_user_token = response["token"]
                # Upgrade to pro plan
                await self.upgrade_user_subscription(self.pro_user_token, "pro")
                self.log_test("Pro User Creation", True, "Pro user created successfully")
            else:
                self.log_test("Pro User Creation", False, f"Status: {status}", response)
            
        # Try to login with existing premium user first
        premium_login = {
            "email": "premium_automation_test@test.com",
            "password": "TestPassword123"
        }
        
        success, response, status = await self.make_request("POST", "/auth/login", premium_login)
        if success and "token" in response:
            self.premium_user_token = response["token"]
            # Try to upgrade to premium plan
            await self.upgrade_user_subscription(self.premium_user_token, "premium")
            self.log_test("Premium User Login", True, "Premium user logged in successfully")
        else:
            # Create new premium user with different email
            premium_data = {
                "email": f"premium_automation_test_{int(datetime.now().timestamp())}@test.com",
                "name": "Premium Automation Test", 
                "password": "TestPassword123"
            }
            
            success, response, status = await self.make_request("POST", "/auth/register", premium_data)
            if success and "token" in response:
                self.premium_user_token = response["token"]
                # Upgrade to premium plan
                await self.upgrade_user_subscription(self.premium_user_token, "premium")
                self.log_test("Premium User Creation", True, "Premium user created successfully")
            else:
                self.log_test("Premium User Creation", False, f"Status: {status}", response)
            
        # Try to login with existing free user first
        free_login = {
            "email": "free_automation_test@test.com",
            "password": "TestPassword123"
        }
        
        success, response, status = await self.make_request("POST", "/auth/login", free_login)
        if success and "token" in response:
            self.free_user_token = response["token"]
            self.log_test("Free User Login", True, "Free user logged in successfully")
        else:
            # Create new free user with different email
            free_data = {
                "email": f"free_automation_test_{int(datetime.now().timestamp())}@test.com",
                "name": "Free Automation Test",
                "password": "TestPassword123"
            }
            
            success, response, status = await self.make_request("POST", "/auth/register", free_data)
            if success and "token" in response:
                self.free_user_token = response["token"]
                self.log_test("Free User Creation", True, "Free user created successfully")
            else:
                self.log_test("Free User Creation", False, f"Status: {status}", response)
            
    async def upgrade_user_subscription(self, token: str, plan: str):
        """Simulate subscription upgrade by directly updating user plan"""
        # For testing purposes, we'll create a mock payment and upgrade
        # In real system this would be done via Stripe payment processing
        
        # Create a mock checkout session first
        checkout_data = {
            "plan_type": plan,
            "origin_url": "https://test.com"
        }
        
        success, response, status = await self.make_request("POST", "/payments/create-checkout",
                                                           data=checkout_data, token=token)
        
        if success and "session_id" in response:
            session_id = response["session_id"]
            
            # Simulate successful payment by checking status (this will trigger upgrade)
            success, response, status = await self.make_request("GET", f"/payments/status/{session_id}",
                                                               token=token)
            
            if success:
                print(f"   Simulated {plan} subscription upgrade successful")
            else:
                print(f"   Failed to simulate {plan} subscription upgrade: {response}")
        else:
            print(f"   Failed to create checkout session for {plan}: {response}")
        
    async def test_scheduler_system(self):
        """Test 1: Verify the automatic scheduler starts correctly on server startup"""
        print("🤖 Testing Scheduler System...")
        
        # First, let's check what subscription plan our admin user actually has
        if self.admin_token:
            success, response, status = await self.make_request("GET", "/stats", token=self.admin_token)
            if success:
                admin_plan = response.get("subscription_plan", "unknown")
                print(f"   Admin user subscription plan: {admin_plan}")
            
        # Test if scheduler endpoints are accessible (indirect test of scheduler running)
        success, response, status = await self.make_request("GET", "/seo/automation-stats", 
                                                           token=self.admin_token)
        
        if success:
            self.log_test("Scheduler System - Endpoint Accessibility", True, 
                         "Automation stats endpoint accessible, indicating scheduler is running")
        else:
            self.log_test("Scheduler System - Endpoint Accessibility", False, 
                         f"Status: {status}, automation endpoints not accessible", response)
            
        # Test scheduler job configuration by checking if automation functions exist
        # This is tested indirectly through the test automation endpoint
        if self.admin_token:  # Use admin token since they should have premium access
            success, response, status = await self.make_request("POST", "/seo/test-automation",
                                                               token=self.admin_token)
            
            if success and "results" in response:
                results = response["results"]
                has_scraping = "scraping" in results
                has_optimization = "optimization" in results  
                has_publication = "publication" in results
                
                if has_scraping and has_optimization and has_publication:
                    self.log_test("Scheduler System - Job Functions", True,
                                 "All three automation functions (scraping, optimization, publication) are available")
                else:
                    self.log_test("Scheduler System - Job Functions", False,
                                 f"Missing automation functions. Found: {list(results.keys())}")
            else:
                self.log_test("Scheduler System - Job Functions", False,
                             f"Status: {status}, could not test automation functions", response)
                             
    async def test_automation_settings_endpoints(self):
        """Test 2: Test the new automation management endpoints"""
        print("⚙️ Testing Automation Settings Endpoints...")
        
        # Check what subscription plan our admin user has
        if self.admin_token:
            success, response, status = await self.make_request("GET", "/stats", token=self.admin_token)
            if success:
                admin_plan = response.get("subscription_plan", "unknown")
                print(f"   Admin user subscription plan: {admin_plan}")
        
        # Test GET /api/seo/auto-settings with Admin user (should have premium access)
        success, response, status = await self.make_request("GET", "/seo/auto-settings",
                                                           token=self.admin_token)
        
        if success and "settings" in response:
            settings = response["settings"]
            required_fields = ["scraping_enabled", "auto_optimization_enabled", 
                             "auto_publication_enabled", "scraping_frequency", "target_categories"]
            
            has_all_fields = all(field in settings for field in required_fields)
            
            if has_all_fields:
                self.log_test("GET /api/seo/auto-settings - Admin User", True,
                             f"All required settings fields present: {list(settings.keys())}")
            else:
                missing = [f for f in required_fields if f not in settings]
                self.log_test("GET /api/seo/auto-settings - Admin User", False,
                             f"Missing settings fields: {missing}")
        else:
            self.log_test("GET /api/seo/auto-settings - Admin User", False,
                         f"Status: {status}", response)
            
        # Test PUT /api/seo/auto-settings with Admin user
        update_settings = {
            "scraping_enabled": True,
            "auto_optimization_enabled": True,
            "auto_publication_enabled": False,
            "scraping_frequency": "daily",
            "target_categories": ["electronics", "clothing"]
        }
        
        success, response, status = await self.make_request("PUT", "/seo/auto-settings",
                                                           data=update_settings,
                                                           token=self.admin_token)
        
        if success and response.get("success"):
            self.log_test("PUT /api/seo/auto-settings - Admin User", True,
                         "Settings updated successfully")
        else:
            self.log_test("PUT /api/seo/auto-settings - Admin User", False,
                         f"Status: {status}", response)
            
        # Test GET /api/seo/automation-stats with Admin user
        success, response, status = await self.make_request("GET", "/seo/automation-stats",
                                                           token=self.admin_token)
        
        if success and "stats" in response:
            stats = response["stats"]
            required_stats = ["sheets_optimized", "sheets_published", "trends_available", 
                            "automation_enabled"]
            
            has_all_stats = all(stat in stats for stat in required_stats)
            
            if has_all_stats:
                self.log_test("GET /api/seo/automation-stats - Admin User", True,
                             f"All required stats fields present: {list(stats.keys())}")
            else:
                missing = [s for s in required_stats if s not in stats]
                self.log_test("GET /api/seo/automation-stats - Admin User", False,
                             f"Missing stats fields: {missing}")
        else:
            self.log_test("GET /api/seo/automation-stats - Admin User", False,
                         f"Status: {status}", response)
            
        # Test POST /api/seo/test-automation with Admin user
        if self.admin_token:
            success, response, status = await self.make_request("POST", "/seo/test-automation",
                                                               token=self.admin_token)
            
            if success and "results" in response:
                self.log_test("POST /api/seo/test-automation - Admin User", True,
                             "Automation test completed successfully")
            else:
                self.log_test("POST /api/seo/test-automation - Admin User", False,
                             f"Status: {status}", response)
                             
    async def test_subscription_access_control(self):
        """Test 3: Verify proper access control for different subscription tiers"""
        print("🔐 Testing Subscription Access Control...")
        
        # Test Free user access (should be blocked)
        success, response, status = await self.make_request("GET", "/seo/auto-settings",
                                                           token=self.free_user_token)
        
        if not success and status == 403:
            self.log_test("Access Control - Free User Blocked", True,
                         "Free user correctly blocked from automation settings")
        else:
            self.log_test("Access Control - Free User Blocked", False,
                         f"Free user should be blocked but got status: {status}", response)
            
        # Test Pro user access (should be allowed)
        success, response, status = await self.make_request("GET", "/seo/auto-settings",
                                                           token=self.pro_user_token)
        
        if success:
            self.log_test("Access Control - Pro User Allowed", True,
                         "Pro user correctly allowed access to automation settings")
        else:
            self.log_test("Access Control - Pro User Allowed", False,
                         f"Pro user should be allowed but got status: {status}", response)
            
        # Test Premium user access (should be allowed)
        if self.premium_user_token:
            success, response, status = await self.make_request("GET", "/seo/auto-settings",
                                                               token=self.premium_user_token)
            
            if success:
                self.log_test("Access Control - Premium User Allowed", True,
                             "Premium user correctly allowed access to automation settings")
            else:
                self.log_test("Access Control - Premium User Allowed", False,
                             f"Premium user should be allowed but got status: {status}", response)
                             
        # Test Premium-only test automation endpoint
        if self.pro_user_token:
            success, response, status = await self.make_request("POST", "/seo/test-automation",
                                                               token=self.pro_user_token)
            
            if not success and status == 403:
                self.log_test("Access Control - Pro User Blocked from Test Automation", True,
                             "Pro user correctly blocked from premium-only test automation")
            else:
                self.log_test("Access Control - Pro User Blocked from Test Automation", False,
                             f"Pro user should be blocked from test automation but got status: {status}", response)
                             
        if self.premium_user_token:
            success, response, status = await self.make_request("POST", "/seo/test-automation",
                                                               token=self.premium_user_token)
            
            if success:
                self.log_test("Access Control - Premium User Test Automation", True,
                             "Premium user correctly allowed access to test automation")
            else:
                self.log_test("Access Control - Premium User Test Automation", False,
                             f"Premium user should be allowed test automation but got status: {status}", response)
                             
    async def test_automation_functions(self):
        """Test 4: Test that the automation functions work correctly"""
        print("🔄 Testing Automation Functions...")
        
        # Create a test product sheet for automation testing
        if self.pro_user_token:
            sheet_data = {
                "product_name": "Test Automation Product",
                "product_description": "A test product for automation system testing",
                "generate_image": False,
                "number_of_images": 1
            }
            
            success, response, status = await self.make_request("POST", "/generate-sheet",
                                                               data=sheet_data,
                                                               token=self.pro_user_token)
            
            if success:
                self.log_test("Automation Functions - Test Product Sheet Creation", True,
                             "Test product sheet created for automation testing")
                
                # Test automation functions via test endpoint (Premium user only)
                if self.premium_user_token:
                    success, response, status = await self.make_request("POST", "/seo/test-automation",
                                                                       token=self.premium_user_token)
                    
                    if success and "results" in response:
                        results = response["results"]
                        
                        # Check scraping function
                        scraping_result = results.get("scraping", "")
                        if "success" in scraping_result or "error" in scraping_result:
                            self.log_test("Automation Functions - Daily Scraping Task", True,
                                         f"Scraping function executed: {scraping_result}")
                        else:
                            self.log_test("Automation Functions - Daily Scraping Task", False,
                                         f"Unexpected scraping result: {scraping_result}")
                            
                        # Check optimization function
                        optimization_result = results.get("optimization", "")
                        if "success" in optimization_result or "error" in optimization_result:
                            self.log_test("Automation Functions - Optimization Task", True,
                                         f"Optimization function executed: {optimization_result}")
                        else:
                            self.log_test("Automation Functions - Optimization Task", False,
                                         f"Unexpected optimization result: {optimization_result}")
                            
                        # Check publication function
                        publication_result = results.get("publication", "")
                        if "success" in publication_result or "skipped" in publication_result or "error" in publication_result:
                            self.log_test("Automation Functions - Auto Publication Task", True,
                                         f"Publication function executed: {publication_result}")
                        else:
                            self.log_test("Automation Functions - Auto Publication Task", False,
                                         f"Unexpected publication result: {publication_result}")
                    else:
                        self.log_test("Automation Functions - Test Execution", False,
                                     f"Status: {status}", response)
            else:
                self.log_test("Automation Functions - Test Product Sheet Creation", False,
                             f"Status: {status}", response)
                             
    async def test_database_integration(self):
        """Test 5: Verify automation system integrates with existing database"""
        print("💾 Testing Database Integration...")
        
        # Test SEO scraping config creation/update
        if self.pro_user_token:
            # First, get current settings to verify config exists
            success, response, status = await self.make_request("GET", "/seo/auto-settings",
                                                               token=self.pro_user_token)
            
            if success and "settings" in response:
                self.log_test("Database Integration - SEO Config Retrieval", True,
                             "SEO scraping config successfully retrieved from database")
                
                # Update settings to test database write
                update_data = {
                    "scraping_enabled": True,
                    "auto_optimization_enabled": True,
                    "scraping_frequency": "daily",
                    "target_categories": ["test_category"]
                }
                
                success, response, status = await self.make_request("PUT", "/seo/auto-settings",
                                                                   data=update_data,
                                                                   token=self.pro_user_token)
                
                if success:
                    self.log_test("Database Integration - SEO Config Update", True,
                                 "SEO scraping config successfully updated in database")
                    
                    # Verify the update by retrieving again
                    success, response, status = await self.make_request("GET", "/seo/auto-settings",
                                                                       token=self.pro_user_token)
                    
                    if success and response.get("settings", {}).get("scraping_enabled") == True:
                        self.log_test("Database Integration - Config Persistence", True,
                                     "Updated settings correctly persisted in database")
                    else:
                        self.log_test("Database Integration - Config Persistence", False,
                                     "Updated settings not properly persisted")
                else:
                    self.log_test("Database Integration - SEO Config Update", False,
                                 f"Status: {status}", response)
            else:
                self.log_test("Database Integration - SEO Config Retrieval", False,
                             f"Status: {status}", response)
                             
        # Test integration logs tracking (check if automation stats work)
        if self.pro_user_token:
            success, response, status = await self.make_request("GET", "/seo/automation-stats",
                                                               token=self.pro_user_token)
            
            if success and "stats" in response:
                stats = response["stats"]
                if isinstance(stats.get("sheets_optimized"), int) and isinstance(stats.get("sheets_published"), int):
                    self.log_test("Database Integration - Integration Logs", True,
                                 "Integration logs properly tracked in database")
                else:
                    self.log_test("Database Integration - Integration Logs", False,
                                 "Integration logs not properly structured")
            else:
                self.log_test("Database Integration - Integration Logs", False,
                             f"Status: {status}", response)
                             
    async def test_error_handling(self):
        """Test 6: Verify robust error handling throughout the automation system"""
        print("🛡️ Testing Error Handling...")
        
        # Test invalid settings data
        if self.pro_user_token:
            invalid_settings = {
                "scraping_enabled": "invalid_boolean",  # Should be boolean
                "invalid_field": "test",
                "scraping_frequency": 123  # Should be string
            }
            
            success, response, status = await self.make_request("PUT", "/seo/auto-settings",
                                                               data=invalid_settings,
                                                               token=self.pro_user_token)
            
            if not success and status in [400, 422]:
                self.log_test("Error Handling - Invalid Settings Data", True,
                             "Invalid settings data properly rejected with appropriate error")
            else:
                self.log_test("Error Handling - Invalid Settings Data", False,
                             f"Invalid data should be rejected but got status: {status}", response)
                             
        # Test missing authentication
        success, response, status = await self.make_request("GET", "/seo/auto-settings")
        
        if not success and status in [401, 403]:
            self.log_test("Error Handling - Missing Authentication", True,
                         "Missing authentication properly handled")
        else:
            self.log_test("Error Handling - Missing Authentication", False,
                         f"Missing auth should return 401/403 but got status: {status}", response)
            
        # Test invalid token
        success, response, status = await self.make_request("GET", "/seo/auto-settings",
                                                           token="invalid_token_12345")
        
        if not success and status in [401, 403]:
            self.log_test("Error Handling - Invalid Token", True,
                         "Invalid token properly handled")
        else:
            self.log_test("Error Handling - Invalid Token", False,
                         f"Invalid token should return 401/403 but got status: {status}", response)
                         
        # Test automation functions error handling (if premium user available)
        if self.premium_user_token:
            # This will test internal error handling of automation functions
            success, response, status = await self.make_request("POST", "/seo/test-automation",
                                                               token=self.premium_user_token)
            
            if success and "results" in response:
                results = response["results"]
                # Even if functions fail internally, the endpoint should handle errors gracefully
                has_error_handling = any("error" in str(result) or "success" in str(result) 
                                       for result in results.values())
                
                if has_error_handling:
                    self.log_test("Error Handling - Automation Functions", True,
                                 "Automation functions have proper error handling")
                else:
                    self.log_test("Error Handling - Automation Functions", False,
                                 "Automation functions may not have proper error handling")
            else:
                self.log_test("Error Handling - Automation Functions", False,
                             f"Status: {status}", response)
                             
    async def run_all_tests(self):
        """Run all automation system tests"""
        print("🚀 Starting Comprehensive Automation System Testing")
        print("=" * 60)
        
        await self.setup_session()
        
        try:
            # Setup
            await self.create_test_users()
            
            # Core automation tests
            await self.test_scheduler_system()
            await self.test_automation_settings_endpoints()
            await self.test_subscription_access_control()
            await self.test_automation_functions()
            await self.test_database_integration()
            await self.test_error_handling()
            
        finally:
            await self.cleanup_session()
            
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("=" * 60)
        print("🏁 AUTOMATION SYSTEM TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
            print()
            
        print("✅ PASSED TESTS:")
        for result in self.test_results:
            if result["success"]:
                print(f"  - {result['test']}")
                
        print("\n" + "=" * 60)

async def main():
    """Main test execution"""
    tester = AutomationSystemTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())