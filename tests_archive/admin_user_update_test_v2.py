#!/usr/bin/env python3
"""
Admin User Update Test - ECOMSIMPLY (Updated Version)
Test to update user msylla54@yahoo.fr to admin status using admin privileges
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 30
ADMIN_KEY = "ECOMSIMPLY_ADMIN_2024"

class AdminUserUpdateTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.target_email = "msylla54@yahoo.fr"
        self.target_password = "NewPassword123"
        self.default_admin_email = "msylla54@gmail.com"
        self.default_admin_password = "AdminEcomsimply"
        self.auth_token = None
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
    
    def test_default_admin_login(self):
        """Test login with default admin account"""
        self.log("Testing default admin login...")
        
        try:
            login_data = {
                "email": self.default_admin_email,
                "password": self.default_admin_password
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_auth_token = data.get("token")
                user_info = data.get("user", {})
                
                is_admin = user_info.get("is_admin", False)
                details = f"Default admin login successful. is_admin: {is_admin}"
                self.add_result("Default Admin Login", True, details)
                return True
            else:
                self.add_result("Default Admin Login", False, f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Default Admin Login", False, f"Exception during login: {str(e)}")
            return False
    
    def test_create_target_user_as_admin(self):
        """Create target user with admin privileges using admin registration"""
        self.log("Testing creation of target user with admin privileges...")
        
        try:
            # Try to register the target user with admin key
            register_data = {
                "email": self.target_email,
                "name": "Admin User - msylla54",
                "password": self.target_password,
                "admin_key": ADMIN_KEY,
                "language": "fr"
            }
            
            response = self.session.post(f"{BASE_URL}/auth/register", json=register_data)
            
            if response.status_code == 200:
                data = response.json()
                user_info = data.get("user", {})
                is_admin = user_info.get("is_admin", False)
                subscription_plan = user_info.get("subscription_plan", "")
                
                details = f"User created successfully. is_admin: {is_admin}, plan: {subscription_plan}"
                self.add_result("Target User Creation", True, details)
                return True
            elif response.status_code == 400 and "existe déjà" in response.text:
                self.add_result("Target User Already Exists", True, "User already exists, will try to update")
                return self.test_update_existing_user()
            else:
                self.add_result("Target User Creation", False, f"Failed to create user: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Target User Creation", False, f"Exception during creation: {str(e)}")
            return False
    
    def test_update_existing_user(self):
        """Try to update existing user to admin status using direct database approach"""
        self.log("Attempting to update existing user to admin status...")
        
        # Since there's no direct update endpoint, let's try to use admin endpoints to check the user
        if not self.admin_auth_token:
            self.add_result("User Update", False, "No admin token available for update")
            return False
        
        try:
            # Get user list to find the target user
            headers = {
                "Authorization": f"Bearer {self.admin_auth_token}",
                "Content-Type": "application/json"
            }
            params = {"admin_key": ADMIN_KEY}
            
            response = self.session.get(f"{BASE_URL}/admin/users", headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get("users", [])
                
                # Find target user
                target_user = None
                for user in users:
                    if user.get("email") == self.target_email:
                        target_user = user
                        break
                
                if target_user:
                    current_admin_status = target_user.get("is_admin", False)
                    current_plan = target_user.get("subscription_plan", "")
                    
                    details = f"Found target user. Current admin status: {current_admin_status}, plan: {current_plan}"
                    
                    if current_admin_status and current_plan == "premium":
                        self.add_result("User Already Admin", True, "User already has admin privileges and premium plan")
                        return True
                    else:
                        self.add_result("User Needs Update", True, details)
                        # Since there's no direct update endpoint, we'll note this for manual intervention
                        return False
                else:
                    self.add_result("User Not Found", False, "Target user not found in admin user list")
                    return False
            else:
                self.add_result("Admin Users Access", False, f"Failed to access admin users: {response.status_code}")
                return False
                
        except Exception as e:
            self.add_result("User Update", False, f"Exception during update: {str(e)}")
            return False
    
    def test_target_user_login(self):
        """Test login with target user credentials"""
        self.log("Testing target user login...")
        
        try:
            login_data = {
                "email": self.target_email,
                "password": self.target_password
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                user_info = data.get("user", {})
                
                is_admin = user_info.get("is_admin", False)
                subscription_plan = user_info.get("subscription_plan", "")
                
                details = f"Login successful. is_admin: {is_admin}, subscription_plan: {subscription_plan}"
                self.add_result("Target User Login", True, details)
                
                # Check admin status
                if is_admin:
                    self.add_result("Admin Status Verified", True, "User has admin privileges")
                else:
                    self.add_result("Admin Status Missing", False, "User does not have admin privileges")
                
                # Check premium plan
                if subscription_plan == "premium":
                    self.add_result("Premium Plan Verified", True, "User has premium subscription")
                else:
                    self.add_result("Premium Plan Missing", False, f"User has {subscription_plan} plan instead of premium")
                
                return True
            else:
                self.add_result("Target User Login", False, f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Target User Login", False, f"Exception during login: {str(e)}")
            return False
    
    def test_admin_endpoints_access(self):
        """Test access to admin endpoints with target user"""
        self.log("Testing admin endpoints access with target user...")
        
        if not self.auth_token:
            self.add_result("Admin Endpoints Access", False, "No target user auth token available")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        # Test admin stats endpoint
        try:
            params = {"admin_key": ADMIN_KEY}
            response = self.session.get(f"{BASE_URL}/admin/stats", headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                self.add_result("Admin Stats Access", True, f"Successfully accessed admin stats")
            else:
                self.add_result("Admin Stats Access", False, f"Failed to access admin stats: {response.status_code}")
                
        except Exception as e:
            self.add_result("Admin Stats Access", False, f"Exception accessing admin stats: {str(e)}")
        
        # Test price management endpoints
        try:
            params = {"admin_key": ADMIN_KEY}
            response = self.session.get(f"{BASE_URL}/admin/plans-config", headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                self.add_result("Price Management Access", True, f"Successfully accessed price management")
            else:
                self.add_result("Price Management Access", False, f"Failed to access price management: {response.status_code}")
                
        except Exception as e:
            self.add_result("Price Management Access", False, f"Exception accessing price management: {str(e)}")
    
    def run_all_tests(self):
        """Run all admin user update tests"""
        self.log("🚀 Starting Admin User Update Tests for msylla54@yahoo.fr")
        self.log("=" * 80)
        
        # Test 1: Login with default admin account
        admin_login_success = self.test_default_admin_login()
        
        # Test 2: Create/Update target user with admin privileges
        if admin_login_success:
            self.test_create_target_user_as_admin()
        
        # Test 3: Test target user login
        self.test_target_user_login()
        
        # Test 4: Test admin endpoints access with target user
        self.test_admin_endpoints_access()
        
        # Summary
        self.log("=" * 80)
        self.log("🎯 ADMIN USER UPDATE TEST SUMMARY")
        self.log("=" * 80)
        
        passed_tests = sum(1 for result in self.test_results if result["success"])
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"📊 OVERALL RESULTS: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        
        # Detailed results
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            self.log(f"{status} {result['test']}: {result['details']}")
        
        # Check if main objectives are met
        admin_status_verified = any(r["test"] == "Admin Status Verified" and r["success"] for r in self.test_results)
        premium_plan_verified = any(r["test"] == "Premium Plan Verified" and r["success"] for r in self.test_results)
        admin_access_working = any(r["test"] in ["Admin Stats Access", "Price Management Access"] and r["success"] for r in self.test_results)
        
        if admin_status_verified and premium_plan_verified and admin_access_working:
            self.log("🎉 ADMIN USER UPDATE COMPLETED SUCCESSFULLY!")
            self.log(f"✅ User {self.target_email} has admin privileges")
            self.log("✅ User has premium subscription plan")
            self.log("✅ User can access admin endpoints with admin key")
            return True
        else:
            self.log("⚠️ ADMIN USER UPDATE PARTIALLY COMPLETED")
            if not admin_status_verified:
                self.log("❌ User does not have admin privileges")
            if not premium_plan_verified:
                self.log("❌ User does not have premium plan")
            if not admin_access_working:
                self.log("❌ User cannot access admin endpoints")
            return False

def main():
    """Main test execution"""
    tester = AdminUserUpdateTester()
    success = tester.run_all_tests()
    
    return success

if __name__ == "__main__":
    main()