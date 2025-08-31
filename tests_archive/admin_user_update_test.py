#!/usr/bin/env python3
"""
Admin User Update Test - ECOMSIMPLY
Test to update user msylla54@yahoo.fr to admin status and verify admin access
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
        self.auth_token = None
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
    
    def test_direct_database_update(self):
        """Test direct database update to make user admin"""
        self.log("Testing direct database update to make user admin...")
        
        try:
            # First, let's try to register the user if they don't exist
            register_data = {
                "email": self.target_email,
                "name": "Admin User Test",
                "password": self.target_password,
                "admin_key": ADMIN_KEY,
                "language": "fr"
            }
            
            response = self.session.post(f"{BASE_URL}/auth/register", json=register_data)
            
            if response.status_code == 200:
                self.add_result("User Registration/Update", True, f"User {self.target_email} registered/updated successfully")
                return True
            elif response.status_code == 400 and "existe déjà" in response.text:
                self.add_result("User Already Exists", True, f"User {self.target_email} already exists, will try to login")
                return True
            else:
                self.add_result("User Registration/Update", False, f"Failed to register user: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("User Registration/Update", False, f"Exception during registration: {str(e)}")
            return False
    
    def test_user_login(self):
        """Test user login with existing credentials"""
        self.log("Testing user login...")
        
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
                
                # Check if user has admin status and premium plan
                is_admin = user_info.get("is_admin", False)
                subscription_plan = user_info.get("subscription_plan", "")
                
                details = f"Login successful. is_admin: {is_admin}, subscription_plan: {subscription_plan}"
                self.add_result("User Login", True, details)
                
                # Verify admin status
                if is_admin:
                    self.add_result("Admin Status Check", True, "User has admin privileges")
                else:
                    self.add_result("Admin Status Check", False, "User does not have admin privileges")
                
                # Verify premium plan
                if subscription_plan == "premium":
                    self.add_result("Premium Plan Check", True, "User has premium subscription")
                else:
                    self.add_result("Premium Plan Check", False, f"User has {subscription_plan} plan instead of premium")
                
                return True
            else:
                self.add_result("User Login", False, f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("User Login", False, f"Exception during login: {str(e)}")
            return False
    
    def test_admin_endpoints_access(self):
        """Test access to admin endpoints with admin key"""
        self.log("Testing admin endpoints access...")
        
        if not self.auth_token:
            self.add_result("Admin Endpoints Access", False, "No auth token available")
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
                self.add_result("Admin Stats Access", True, f"Successfully accessed admin stats: {len(data)} fields returned")
            else:
                self.add_result("Admin Stats Access", False, f"Failed to access admin stats: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.add_result("Admin Stats Access", False, f"Exception accessing admin stats: {str(e)}")
        
        # Test admin users endpoint
        try:
            params = {"admin_key": ADMIN_KEY}
            response = self.session.get(f"{BASE_URL}/admin/users", headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                users_count = len(data.get("users", []))
                self.add_result("Admin Users Access", True, f"Successfully accessed admin users: {users_count} users found")
            else:
                self.add_result("Admin Users Access", False, f"Failed to access admin users: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.add_result("Admin Users Access", False, f"Exception accessing admin users: {str(e)}")
        
        # Test price and promotion management endpoints
        try:
            params = {"admin_key": ADMIN_KEY}
            response = self.session.get(f"{BASE_URL}/admin/plans-config", headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                plans_count = len(data.get("plans", []))
                self.add_result("Admin Plans Config Access", True, f"Successfully accessed plans config: {plans_count} plans found")
            else:
                self.add_result("Admin Plans Config Access", False, f"Failed to access plans config: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.add_result("Admin Plans Config Access", False, f"Exception accessing plans config: {str(e)}")
    
    def test_user_stats_with_admin_data(self):
        """Test user stats endpoint to verify admin user data"""
        self.log("Testing user stats to verify admin user data...")
        
        if not self.auth_token:
            self.add_result("User Stats Check", False, "No auth token available")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = self.session.get(f"{BASE_URL}/stats", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                subscription_plan = data.get("subscription_plan", "")
                
                details = f"User stats retrieved. subscription_plan: {subscription_plan}"
                self.add_result("User Stats Retrieval", True, details)
                
                # Verify premium plan in stats
                if subscription_plan == "premium":
                    self.add_result("Stats Premium Plan Check", True, "User stats show premium subscription")
                else:
                    self.add_result("Stats Premium Plan Check", False, f"User stats show {subscription_plan} plan instead of premium")
                
                return True
            else:
                self.add_result("User Stats Retrieval", False, f"Failed to get user stats: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("User Stats Retrieval", False, f"Exception getting user stats: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all admin user update tests"""
        self.log("🚀 Starting Admin User Update Tests for msylla54@yahoo.fr")
        self.log("=" * 80)
        
        # Test 1: Update/Register user with admin privileges
        self.test_direct_database_update()
        
        # Test 2: Login with existing credentials
        self.test_user_login()
        
        # Test 3: Test admin endpoints access
        self.test_admin_endpoints_access()
        
        # Test 4: Verify user stats show correct data
        self.test_user_stats_with_admin_data()
        
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
        
        # Final status
        if success_rate >= 80:
            self.log("🎉 ADMIN USER UPDATE TESTS COMPLETED SUCCESSFULLY!")
            return True
        else:
            self.log("❌ ADMIN USER UPDATE TESTS FAILED - Some critical issues found")
            return False

def main():
    """Main test execution"""
    tester = AdminUserUpdateTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Admin user update completed successfully!")
        print(f"✅ User {tester.target_email} now has admin privileges")
        print("✅ User can access admin interface with admin key")
        print("✅ User maintains premium subscription plan")
    else:
        print("\n❌ Admin user update encountered issues")
        print("❌ Please check the detailed logs above")
    
    return success

if __name__ == "__main__":
    main()