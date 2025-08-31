#!/usr/bin/env python3
"""
Admin User Deletion Testing Suite
Testing the newly implemented admin user deletion functionality
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BACKEND_URL = "https://ecomsimply.com/api"
ADMIN_KEY = "ECOMSIMPLY_ADMIN_2024"

class AdminUserDeletionTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_user_email = None
        self.test_user_id = None
        self.test_results = []
        
    async def setup_session(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results"""
        status = "✅ PASSED" if success else "❌ FAILED"
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
        
    async def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None, params: Dict = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        try:
            url = f"{BACKEND_URL}{endpoint}"
            
            if method.upper() == "GET":
                async with self.session.get(url, headers=headers, params=params) as response:
                    response_data = await response.json()
                    return response.status < 400, response_data, response.status
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, headers=headers, params=params) as response:
                    response_data = await response.json()
                    return response.status < 400, response_data, response.status
            elif method.upper() == "DELETE":
                async with self.session.delete(url, headers=headers, params=params) as response:
                    response_data = await response.json()
                    return response.status < 400, response_data, response.status
            else:
                return False, {"error": f"Unsupported method: {method}"}, 400
                
        except Exception as e:
            return False, {"error": str(e)}, 500
            
    async def create_admin_user(self) -> bool:
        """Create admin user for testing"""
        print("🔧 Setting up admin user...")
        
        # Try the default admin account first
        default_admin = {
            "email": "msylla54@gmail.com",
            "password": "AdminEcomsimply"
        }
        
        success, login_response, status = await self.make_request("POST", "/auth/login", default_admin)
        if success and ("access_token" in login_response or "token" in login_response):
            self.admin_token = login_response.get("access_token") or login_response.get("token")
            self.log_test("Admin Login (Default)", True, "Admin token obtained from default admin")
            return True
        
        # Try our test admin account
        admin_data = {
            "email": "admin_deletion_test@test.com",
            "name": "Admin Deletion Tester",
            "password": "AdminTest123!",
            "admin_key": ADMIN_KEY
        }
        
        # Try to login first
        login_data = {
            "email": admin_data["email"],
            "password": admin_data["password"]
        }
        
        success, login_response, status = await self.make_request("POST", "/auth/login", login_data)
        if success and ("access_token" in login_response or "token" in login_response):
            self.admin_token = login_response.get("access_token") or login_response.get("token")
            self.log_test("Admin Login (Test Account)", True, "Admin token obtained from test admin")
            return True
        
        # Create a new admin with unique email
        import time
        unique_email = f"admin_test_{int(time.time())}@test.com"
        admin_data["email"] = unique_email
        
        success, response, status = await self.make_request("POST", "/auth/register", admin_data)
        
        if success:
            self.log_test("Admin User Creation", True, f"Admin user created successfully: {unique_email}")
            
            # Login to get token
            login_data["email"] = unique_email
            success, login_response, status = await self.make_request("POST", "/auth/login", login_data)
            if success and ("access_token" in login_response or "token" in login_response):
                self.admin_token = login_response.get("access_token") or login_response.get("token")
                self.log_test("Admin Login", True, "Admin token obtained")
                return True
            else:
                self.log_test("Admin Login", False, "Failed to get admin token", login_response)
                return False
        else:
            self.log_test("Admin User Setup", False, "Failed to create admin user", response)
            return False
                
    async def create_test_user(self) -> bool:
        """Create a test user to be deleted"""
        print("👤 Creating test user for deletion...")
        
        self.test_user_email = f"test_user_deletion_{int(datetime.now().timestamp())}@test.com"
        
        user_data = {
            "email": self.test_user_email,
            "name": "Test User For Deletion",
            "password": "TestUser123!"
        }
        
        success, response, status = await self.make_request("POST", "/auth/register", user_data)
        
        if success:
            self.log_test("Test User Creation", True, f"Test user created: {self.test_user_email}")
            
            # Login to get user ID and create some data
            login_data = {
                "email": self.test_user_email,
                "password": user_data["password"]
            }
            
            success, login_response, status = await self.make_request("POST", "/auth/login", login_data)
            if success and ("access_token" in login_response or "token" in login_response):
                user_token = login_response.get("access_token") or login_response.get("token")
                
                # Create some product sheets for this user
                await self.create_test_data_for_user(user_token)
                return True
            else:
                self.log_test("Test User Login", False, "Failed to login test user", login_response)
                return False
        else:
            self.log_test("Test User Creation", False, "Failed to create test user", response)
            return False
            
    async def create_test_data_for_user(self, user_token: str):
        """Create test data for the user to verify deletion"""
        print("📊 Creating test data for user...")
        
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Create product sheets
        for i in range(3):
            sheet_data = {
                "product_name": f"Test Product {i+1}",
                "product_description": f"Description for test product {i+1}",
                "generate_image": False,
                "number_of_images": 1
            }
            
            success, response, status = await self.make_request("POST", "/generate-sheet", sheet_data, headers)
            if success:
                print(f"   ✅ Created product sheet {i+1}")
            else:
                print(f"   ❌ Failed to create product sheet {i+1}")
                
        # Create chat messages
        chat_data = {"message": "Test chat message for deletion testing"}
        success, response, status = await self.make_request("POST", "/chat", chat_data, headers)
        if success:
            print("   ✅ Created chat message")
        else:
            print("   ❌ Failed to create chat message")
            
    async def test_admin_authentication_required(self):
        """Test that admin authentication is required for deletion endpoints"""
        print("🔐 Testing admin authentication requirements...")
        
        # Test DELETE endpoint without admin key
        success, response, status = await self.make_request("DELETE", f"/admin/delete-user/{self.test_user_email}")
        
        if not success and status == 403:
            self.log_test("DELETE Endpoint - No Admin Key", True, "Correctly rejected request without admin key")
        else:
            self.log_test("DELETE Endpoint - No Admin Key", False, "Should have rejected request without admin key", response)
            
        # Test DELETE endpoint with wrong admin key
        params = {"admin_key": "wrong_key"}
        success, response, status = await self.make_request("DELETE", f"/admin/delete-user/{self.test_user_email}", params=params)
        
        if not success and status == 403:
            self.log_test("DELETE Endpoint - Wrong Admin Key", True, "Correctly rejected request with wrong admin key")
        else:
            self.log_test("DELETE Endpoint - Wrong Admin Key", False, "Should have rejected request with wrong admin key", response)
            
        # Test POST endpoint without admin key
        post_data = {"email": self.test_user_email}
        success, response, status = await self.make_request("POST", "/admin/delete-user-by-email", post_data)
        
        if not success and (status == 400 or status == 403):
            self.log_test("POST Endpoint - No Admin Key", True, "Correctly rejected request without admin key")
        else:
            self.log_test("POST Endpoint - No Admin Key", False, "Should have rejected request without admin key", response)
            
        # Test POST endpoint with wrong admin key
        post_data = {"email": self.test_user_email, "admin_key": "wrong_key"}
        success, response, status = await self.make_request("POST", "/admin/delete-user-by-email", post_data)
        
        if not success and status == 403:
            self.log_test("POST Endpoint - Wrong Admin Key", True, "Correctly rejected request with wrong admin key")
        else:
            self.log_test("POST Endpoint - Wrong Admin Key", False, "Should have rejected request with wrong admin key", response)
            
    async def test_user_not_found(self):
        """Test deletion of non-existent user"""
        print("🔍 Testing deletion of non-existent user...")
        
        fake_email = "nonexistent_user@test.com"
        
        # Test DELETE endpoint
        params = {"admin_key": ADMIN_KEY}
        success, response, status = await self.make_request("DELETE", f"/admin/delete-user/{fake_email}", params=params)
        
        if not success and status == 404:
            self.log_test("DELETE Non-existent User", True, "Correctly returned 404 for non-existent user")
        else:
            self.log_test("DELETE Non-existent User", False, "Should have returned 404 for non-existent user", response)
            
        # Test POST endpoint
        post_data = {"email": fake_email, "admin_key": ADMIN_KEY}
        success, response, status = await self.make_request("POST", "/admin/delete-user-by-email", post_data)
        
        if not success and status == 404:
            self.log_test("POST Non-existent User", True, "Correctly returned 404 for non-existent user")
        else:
            self.log_test("POST Non-existent User", False, "Should have returned 404 for non-existent user", response)
            
    async def test_user_deletion_delete_endpoint(self):
        """Test user deletion via DELETE endpoint"""
        print("🗑️ Testing user deletion via DELETE endpoint...")
        
        params = {"admin_key": ADMIN_KEY}
        success, response, status = await self.make_request("DELETE", f"/admin/delete-user/{self.test_user_email}", params=params)
        
        if success:
            # Verify response structure
            required_fields = ["success", "message", "deleted_user", "deletion_summary", "total_records_deleted", "deleted_at"]
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                self.log_test("DELETE Endpoint - Response Structure", True, f"All required fields present: {required_fields}")
                
                # Verify deletion summary
                deletion_summary = response.get("deletion_summary", {})
                total_deleted = response.get("total_records_deleted", 0)
                
                if total_deleted > 0:
                    self.log_test("DELETE Endpoint - Data Deletion", True, f"Successfully deleted {total_deleted} records: {deletion_summary}")
                else:
                    self.log_test("DELETE Endpoint - Data Deletion", False, "No records were deleted", response)
                    
                # Verify user info
                deleted_user = response.get("deleted_user", {})
                if deleted_user.get("email") == self.test_user_email:
                    self.log_test("DELETE Endpoint - User Info", True, f"Correct user deleted: {deleted_user}")
                else:
                    self.log_test("DELETE Endpoint - User Info", False, "Incorrect user info in response", deleted_user)
                    
            else:
                self.log_test("DELETE Endpoint - Response Structure", False, f"Missing fields: {missing_fields}", response)
        else:
            self.log_test("DELETE Endpoint - User Deletion", False, f"Failed to delete user (Status: {status})", response)
            
    async def test_user_deletion_post_endpoint(self):
        """Test user deletion via POST endpoint"""
        print("📮 Testing user deletion via POST endpoint...")
        
        # Create another test user for POST endpoint testing
        test_email_2 = f"test_user_deletion_post_{int(datetime.now().timestamp())}@test.com"
        
        user_data = {
            "email": test_email_2,
            "name": "Test User For POST Deletion",
            "password": "TestUser123!"
        }
        
        success, response, status = await self.make_request("POST", "/auth/register", user_data)
        
        if not success:
            self.log_test("POST Endpoint - Test User Creation", False, "Failed to create test user for POST endpoint", response)
            return
            
        # Test POST deletion
        post_data = {"email": test_email_2, "admin_key": ADMIN_KEY}
        success, response, status = await self.make_request("POST", "/admin/delete-user-by-email", post_data)
        
        if success:
            # Verify response structure (should be same as DELETE endpoint)
            required_fields = ["success", "message", "deleted_user", "deletion_summary", "total_records_deleted", "deleted_at"]
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                self.log_test("POST Endpoint - Response Structure", True, f"All required fields present: {required_fields}")
                
                # Verify user info
                deleted_user = response.get("deleted_user", {})
                if deleted_user.get("email") == test_email_2:
                    self.log_test("POST Endpoint - User Deletion", True, f"Successfully deleted user via POST: {deleted_user}")
                else:
                    self.log_test("POST Endpoint - User Deletion", False, "Incorrect user info in response", deleted_user)
                    
            else:
                self.log_test("POST Endpoint - Response Structure", False, f"Missing fields: {missing_fields}", response)
        else:
            self.log_test("POST Endpoint - User Deletion", False, f"Failed to delete user via POST (Status: {status})", response)
            
    async def test_user_data_cleanup(self):
        """Test that user data is properly cleaned up after deletion"""
        print("🧹 Testing user data cleanup after deletion...")
        
        # Create a new test user with data
        cleanup_test_email = f"cleanup_test_{int(datetime.now().timestamp())}@test.com"
        
        user_data = {
            "email": cleanup_test_email,
            "name": "Cleanup Test User",
            "password": "TestUser123!"
        }
        
        success, response, status = await self.make_request("POST", "/auth/register", user_data)
        
        if not success:
            self.log_test("Data Cleanup - Test User Creation", False, "Failed to create test user for cleanup testing", response)
            return
            
        # Login and create data
        login_data = {
            "email": cleanup_test_email,
            "password": user_data["password"]
        }
        
        success, login_response, status = await self.make_request("POST", "/auth/login", login_data)
        if not success:
            self.log_test("Data Cleanup - Test User Login", False, "Failed to login test user", login_response)
            return
            
        user_token = login_response.get("access_token") or login_response.get("token")
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Create product sheets
        sheets_created = 0
        for i in range(2):
            sheet_data = {
                "product_name": f"Cleanup Test Product {i+1}",
                "product_description": f"Description for cleanup test product {i+1}",
                "generate_image": False,
                "number_of_images": 1
            }
            
            success, response, status = await self.make_request("POST", "/generate-sheet", sheet_data, headers)
            if success:
                sheets_created += 1
                
        # Create chat message
        chat_data = {"message": "Cleanup test chat message"}
        success, response, status = await self.make_request("POST", "/chat", chat_data, headers)
        chat_created = success
        
        print(f"   📊 Created {sheets_created} product sheets and {'1' if chat_created else '0'} chat messages")
        
        # Now delete the user
        post_data = {"email": cleanup_test_email, "admin_key": ADMIN_KEY}
        success, delete_response, status = await self.make_request("POST", "/admin/delete-user-by-email", post_data)
        
        if success:
            deletion_summary = delete_response.get("deletion_summary", {})
            total_deleted = delete_response.get("total_records_deleted", 0)
            
            # Verify that data was actually deleted
            expected_deletions = {
                "product_sheets": sheets_created,
                "user_account": 1
            }
            
            cleanup_success = True
            cleanup_details = []
            
            for data_type, expected_count in expected_deletions.items():
                actual_count = deletion_summary.get(data_type, 0)
                if actual_count >= expected_count:
                    cleanup_details.append(f"{data_type}: {actual_count} deleted")
                else:
                    cleanup_success = False
                    cleanup_details.append(f"{data_type}: expected {expected_count}, got {actual_count}")
                    
            if cleanup_success:
                self.log_test("Data Cleanup - Verification", True, f"Data properly cleaned up: {', '.join(cleanup_details)}")
            else:
                self.log_test("Data Cleanup - Verification", False, f"Data cleanup issues: {', '.join(cleanup_details)}", deletion_summary)
                
            # Verify total count
            if total_deleted > 0:
                self.log_test("Data Cleanup - Total Count", True, f"Total {total_deleted} records deleted")
            else:
                self.log_test("Data Cleanup - Total Count", False, "No records were deleted", delete_response)
                
        else:
            self.log_test("Data Cleanup - User Deletion", False, "Failed to delete user for cleanup testing", delete_response)
            
    async def test_activity_logging(self):
        """Test that user deletion is properly logged"""
        print("📝 Testing activity logging for user deletion...")
        
        # Create a test user for logging verification
        logging_test_email = f"logging_test_{int(datetime.now().timestamp())}@test.com"
        
        user_data = {
            "email": logging_test_email,
            "name": "Logging Test User",
            "password": "TestUser123!"
        }
        
        success, response, status = await self.make_request("POST", "/auth/register", user_data)
        
        if not success:
            self.log_test("Activity Logging - Test User Creation", False, "Failed to create test user for logging", response)
            return
            
        # Delete the user
        post_data = {"email": logging_test_email, "admin_key": ADMIN_KEY}
        success, delete_response, status = await self.make_request("POST", "/admin/delete-user-by-email", post_data)
        
        if success:
            # Check if deletion was logged (response should contain deletion info)
            required_log_fields = ["deleted_user", "deletion_summary", "deleted_at"]
            missing_fields = [field for field in required_log_fields if field not in delete_response]
            
            if not missing_fields:
                self.log_test("Activity Logging - Response Logging", True, "Deletion properly logged in response")
                
                # Verify log details
                deleted_user = delete_response.get("deleted_user", {})
                if deleted_user.get("email") == logging_test_email:
                    self.log_test("Activity Logging - User Details", True, "Correct user details logged")
                else:
                    self.log_test("Activity Logging - User Details", False, "Incorrect user details in log", deleted_user)
                    
                # Verify timestamp
                deleted_at = delete_response.get("deleted_at")
                if deleted_at:
                    self.log_test("Activity Logging - Timestamp", True, f"Deletion timestamp recorded: {deleted_at}")
                else:
                    self.log_test("Activity Logging - Timestamp", False, "No deletion timestamp recorded")
                    
            else:
                self.log_test("Activity Logging - Response Logging", False, f"Missing log fields: {missing_fields}", delete_response)
        else:
            self.log_test("Activity Logging - User Deletion", False, "Failed to delete user for logging test", delete_response)
            
    async def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("🔍 Testing edge cases and error handling...")
        
        # Test POST endpoint with missing email
        post_data = {"admin_key": ADMIN_KEY}
        success, response, status = await self.make_request("POST", "/admin/delete-user-by-email", post_data)
        
        if not success and status == 400:
            self.log_test("Edge Case - Missing Email", True, "Correctly handled missing email")
        else:
            self.log_test("Edge Case - Missing Email", False, "Should have returned 400 for missing email", response)
            
        # Test POST endpoint with empty email
        post_data = {"email": "", "admin_key": ADMIN_KEY}
        success, response, status = await self.make_request("POST", "/admin/delete-user-by-email", post_data)
        
        if not success:
            self.log_test("Edge Case - Empty Email", True, "Correctly handled empty email")
        else:
            self.log_test("Edge Case - Empty Email", False, "Should have rejected empty email", response)
            
        # Test POST endpoint with invalid email format
        post_data = {"email": "invalid-email", "admin_key": ADMIN_KEY}
        success, response, status = await self.make_request("POST", "/admin/delete-user-by-email", post_data)
        
        if not success and status == 404:
            self.log_test("Edge Case - Invalid Email Format", True, "Correctly handled invalid email format")
        else:
            self.log_test("Edge Case - Invalid Email Format", False, "Should have handled invalid email format", response)
            
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("🎯 ADMIN USER DELETION TESTING SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
                    
        print("\n" + "="*80)
        
        return passed_tests, failed_tests, total_tests
        
    async def run_all_tests(self):
        """Run all admin user deletion tests"""
        print("🚀 Starting Admin User Deletion Testing...")
        print("="*80)
        
        try:
            await self.setup_session()
            
            # Setup phase
            if not await self.create_admin_user():
                print("❌ Failed to setup admin user. Aborting tests.")
                return 0, 1, 1
                
            if not await self.create_test_user():
                print("❌ Failed to create test user. Aborting tests.")
                return 0, 1, 1
                
            # Test phases
            await self.test_admin_authentication_required()
            await self.test_user_not_found()
            await self.test_user_deletion_delete_endpoint()
            await self.test_user_deletion_post_endpoint()
            await self.test_user_data_cleanup()
            await self.test_activity_logging()
            await self.test_edge_cases()
            
            # Summary
            passed, failed, total = self.print_summary()
            
            return passed, failed, total
            
        except Exception as e:
            print(f"❌ Critical error during testing: {e}")
            return 0, 1, 1
        finally:
            await self.cleanup_session()

async def main():
    """Main test execution"""
    tester = AdminUserDeletionTester()
    passed, failed, total = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    asyncio.run(main())