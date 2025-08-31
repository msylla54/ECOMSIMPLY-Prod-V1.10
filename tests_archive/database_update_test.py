#!/usr/bin/env python3
"""
Database Direct Update Test - ECOMSIMPLY
Direct database update to make user msylla54@yahoo.fr an admin
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 30
ADMIN_KEY = "ECOMSIMPLY_ADMIN_2024"

class DatabaseUpdateTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.target_email = "msylla54@yahoo.fr"
        self.target_password = "NewPassword123"
        self.default_admin_email = "msylla54@gmail.com"
        self.default_admin_password = "AdminEcomsimply"
        self.admin_auth_token = None
        self.test_results = []
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def add_result(self, test_name, success, details=""):
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        status = "✅ PASSED" if success else "❌ FAILED"
        self.log(f"{status}: {test_name} - {details}")
    
    def test_admin_login(self):
        """Login with admin account"""
        self.log("Testing admin login...")
        
        try:
            login_data = {
                "email": self.default_admin_email,
                "password": self.default_admin_password
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_auth_token = data.get("token")
                self.add_result("Admin Login", True, "Successfully logged in as admin")
                return True
            else:
                self.add_result("Admin Login", False, f"Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.add_result("Admin Login", False, f"Exception: {str(e)}")
            return False
    
    def test_check_target_user(self):
        """Check current status of target user"""
        self.log("Checking target user status...")
        
        if not self.admin_auth_token:
            self.add_result("User Status Check", False, "No admin token")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.admin_auth_token}",
                "Content-Type": "application/json"
            }
            params = {"admin_key": ADMIN_KEY}
            
            response = self.session.get(f"{BASE_URL}/admin/users", headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get("users", [])
                
                target_user = None
                for user in users:
                    if user.get("email") == self.target_email:
                        target_user = user
                        break
                
                if target_user:
                    is_admin = target_user.get("is_admin", False)
                    plan = target_user.get("subscription_plan", "")
                    user_id = target_user.get("id", "")
                    
                    details = f"Found user. ID: {user_id}, is_admin: {is_admin}, plan: {plan}"
                    self.add_result("Target User Found", True, details)
                    
                    # Store user info for potential update
                    self.target_user_id = user_id
                    self.current_admin_status = is_admin
                    self.current_plan = plan
                    
                    return True
                else:
                    self.add_result("Target User Not Found", False, "User not found in database")
                    return False
            else:
                self.add_result("User Status Check", False, f"Failed to get users: {response.status_code}")
                return False
                
        except Exception as e:
            self.add_result("User Status Check", False, f"Exception: {str(e)}")
            return False
    
    def test_delete_and_recreate_user(self):
        """Delete existing user and recreate with admin privileges"""
        self.log("Attempting to delete and recreate user with admin privileges...")
        
        if not self.admin_auth_token or not hasattr(self, 'target_user_id'):
            self.add_result("User Recreation", False, "Missing admin token or user ID")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.admin_auth_token}",
                "Content-Type": "application/json"
            }
            
            # Step 1: Delete existing user
            params = {"admin_key": ADMIN_KEY}
            delete_response = self.session.delete(
                f"{BASE_URL}/admin/delete-user/{self.target_email}", 
                headers=headers, 
                params=params
            )
            
            if delete_response.status_code == 200:
                self.add_result("User Deletion", True, "Successfully deleted existing user")
                
                # Step 2: Wait a moment for database consistency
                time.sleep(2)
                
                # Step 3: Recreate user with admin privileges
                register_data = {
                    "email": self.target_email,
                    "name": "Admin User - msylla54",
                    "password": self.target_password,
                    "admin_key": ADMIN_KEY,
                    "language": "fr"
                }
                
                register_response = self.session.post(f"{BASE_URL}/auth/register", json=register_data)
                
                if register_response.status_code == 200:
                    data = register_response.json()
                    user_info = data.get("user", {})
                    is_admin = user_info.get("is_admin", False)
                    plan = user_info.get("subscription_plan", "")
                    
                    details = f"User recreated successfully. is_admin: {is_admin}, plan: {plan}"
                    self.add_result("User Recreation", True, details)
                    return True
                else:
                    self.add_result("User Recreation", False, f"Failed to recreate user: {register_response.status_code}")
                    return False
            else:
                self.add_result("User Deletion", False, f"Failed to delete user: {delete_response.status_code}")
                return False
                
        except Exception as e:
            self.add_result("User Recreation", False, f"Exception: {str(e)}")
            return False
    
    def test_final_verification(self):
        """Final verification that user can login and access admin features"""
        self.log("Final verification of admin user setup...")
        
        try:
            # Test login
            login_data = {
                "email": self.target_email,
                "password": self.target_password
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                auth_token = data.get("token")
                user_info = data.get("user", {})
                
                is_admin = user_info.get("is_admin", False)
                plan = user_info.get("subscription_plan", "")
                
                details = f"Login successful. is_admin: {is_admin}, plan: {plan}"
                self.add_result("Final Login Test", True, details)
                
                # Test admin endpoint access
                if auth_token:
                    headers = {
                        "Authorization": f"Bearer {auth_token}",
                        "Content-Type": "application/json"
                    }
                    params = {"admin_key": ADMIN_KEY}
                    
                    admin_response = self.session.get(f"{BASE_URL}/admin/stats", headers=headers, params=params)
                    
                    if admin_response.status_code == 200:
                        self.add_result("Admin Access Test", True, "Successfully accessed admin endpoints")
                    else:
                        self.add_result("Admin Access Test", False, f"Failed to access admin endpoints: {admin_response.status_code}")
                
                return is_admin and plan == "premium"
            else:
                self.add_result("Final Login Test", False, f"Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.add_result("Final Login Test", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all database update tests"""
        self.log("🚀 Starting Database Update Tests for msylla54@yahoo.fr")
        self.log("=" * 80)
        
        # Test 1: Admin login
        if not self.test_admin_login():
            self.log("❌ Cannot proceed without admin access")
            return False
        
        # Test 2: Check target user status
        if not self.test_check_target_user():
            self.log("❌ Cannot find target user")
            return False
        
        # Test 3: Delete and recreate user with admin privileges
        if not self.test_delete_and_recreate_user():
            self.log("❌ Failed to recreate user with admin privileges")
            return False
        
        # Test 4: Final verification
        success = self.test_final_verification()
        
        # Summary
        self.log("=" * 80)
        self.log("🎯 DATABASE UPDATE TEST SUMMARY")
        self.log("=" * 80)
        
        passed_tests = sum(1 for result in self.test_results if result["success"])
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"📊 OVERALL RESULTS: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        
        # Detailed results
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            self.log(f"{status} {result['test']}: {result['details']}")
        
        if success:
            self.log("🎉 ADMIN USER UPDATE COMPLETED SUCCESSFULLY!")
            self.log(f"✅ User {self.target_email} now has admin privileges")
            self.log("✅ User can login with credentials: msylla54@yahoo.fr / NewPassword123")
            self.log("✅ User has premium subscription plan")
            self.log("✅ User can access admin endpoints with admin key ECOMSIMPLY_ADMIN_2024")
        else:
            self.log("❌ ADMIN USER UPDATE FAILED")
        
        return success

def main():
    """Main test execution"""
    tester = DatabaseUpdateTester()
    success = tester.run_all_tests()
    return success

if __name__ == "__main__":
    main()