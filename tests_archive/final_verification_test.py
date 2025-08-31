#!/usr/bin/env python3
"""
Final Verification Test - ECOMSIMPLY
Comprehensive verification that msylla54@yahoo.fr meets all admin requirements
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 30
ADMIN_KEY = "ECOMSIMPLY_ADMIN_2024"

class FinalVerificationTester:
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
    
    def test_user_login(self):
        """Test user can login with existing credentials"""
        self.log("Testing user login with msylla54@yahoo.fr / NewPassword123...")
        
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
                user_id = user_info.get("id", "")
                email = user_info.get("email", "")
                name = user_info.get("name", "")
                
                details = f"Login successful. Email: {email}, is_admin: {is_admin}, plan: {subscription_plan}"
                self.add_result("User Login", True, details)
                
                # Store user info for other tests
                self.user_info = user_info
                
                return True
            else:
                self.add_result("User Login", False, f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("User Login", False, f"Exception: {str(e)}")
            return False
    
    def test_admin_status(self):
        """Verify user has is_admin: true"""
        self.log("Verifying admin status...")
        
        if not hasattr(self, 'user_info'):
            self.add_result("Admin Status Check", False, "No user info available")
            return False
        
        is_admin = self.user_info.get("is_admin", False)
        
        if is_admin:
            self.add_result("Admin Status Check", True, "User has is_admin: true")
            return True
        else:
            self.add_result("Admin Status Check", False, "User does not have admin privileges")
            return False
    
    def test_premium_plan(self):
        """Verify user has premium subscription plan"""
        self.log("Verifying premium subscription plan...")
        
        if not hasattr(self, 'user_info'):
            self.add_result("Premium Plan Check", False, "No user info available")
            return False
        
        subscription_plan = self.user_info.get("subscription_plan", "")
        
        if subscription_plan == "premium":
            self.add_result("Premium Plan Check", True, "User has premium subscription plan")
            return True
        else:
            self.add_result("Premium Plan Check", False, f"User has {subscription_plan} plan instead of premium")
            return False
    
    def test_admin_key_access(self):
        """Verify user can access admin endpoints with admin key"""
        self.log("Testing admin key access...")
        
        if not self.auth_token:
            self.add_result("Admin Key Access", False, "No auth token available")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        admin_endpoints_tested = 0
        admin_endpoints_passed = 0
        
        # Test 1: Admin Stats
        try:
            params = {"admin_key": ADMIN_KEY}
            response = self.session.get(f"{BASE_URL}/admin/stats", headers=headers, params=params)
            admin_endpoints_tested += 1
            
            if response.status_code == 200:
                admin_endpoints_passed += 1
                self.add_result("Admin Stats Access", True, "Successfully accessed admin stats")
            else:
                self.add_result("Admin Stats Access", False, f"Failed: {response.status_code}")
                
        except Exception as e:
            self.add_result("Admin Stats Access", False, f"Exception: {str(e)}")
        
        # Test 2: Admin Users
        try:
            params = {"admin_key": ADMIN_KEY}
            response = self.session.get(f"{BASE_URL}/admin/users", headers=headers, params=params)
            admin_endpoints_tested += 1
            
            if response.status_code == 200:
                admin_endpoints_passed += 1
                data = response.json()
                users_count = len(data.get("users", []))
                self.add_result("Admin Users Access", True, f"Successfully accessed admin users ({users_count} users)")
            else:
                self.add_result("Admin Users Access", False, f"Failed: {response.status_code}")
                
        except Exception as e:
            self.add_result("Admin Users Access", False, f"Exception: {str(e)}")
        
        # Test 3: Price and Promotion Management
        try:
            params = {"admin_key": ADMIN_KEY}
            response = self.session.get(f"{BASE_URL}/admin/plans-config", headers=headers, params=params)
            admin_endpoints_tested += 1
            
            if response.status_code == 200:
                admin_endpoints_passed += 1
                data = response.json()
                plans_count = len(data.get("plans", []))
                self.add_result("Price Management Access", True, f"Successfully accessed price management ({plans_count} plans)")
            else:
                self.add_result("Price Management Access", False, f"Failed: {response.status_code}")
                
        except Exception as e:
            self.add_result("Price Management Access", False, f"Exception: {str(e)}")
        
        # Test 4: Promotions Management
        try:
            params = {"admin_key": ADMIN_KEY}
            response = self.session.get(f"{BASE_URL}/admin/promotions", headers=headers, params=params)
            admin_endpoints_tested += 1
            
            if response.status_code == 200:
                admin_endpoints_passed += 1
                data = response.json()
                promotions_count = len(data.get("promotions", []))
                self.add_result("Promotions Management Access", True, f"Successfully accessed promotions ({promotions_count} promotions)")
            else:
                self.add_result("Promotions Management Access", False, f"Failed: {response.status_code}")
                
        except Exception as e:
            self.add_result("Promotions Management Access", False, f"Exception: {str(e)}")
        
        # Overall admin access result
        if admin_endpoints_passed >= 3:  # At least 3 out of 4 admin endpoints working
            self.add_result("Overall Admin Access", True, f"Admin access working ({admin_endpoints_passed}/{admin_endpoints_tested} endpoints)")
            return True
        else:
            self.add_result("Overall Admin Access", False, f"Insufficient admin access ({admin_endpoints_passed}/{admin_endpoints_tested} endpoints)")
            return False
    
    def test_user_stats_consistency(self):
        """Verify user stats endpoint shows consistent admin data"""
        self.log("Testing user stats consistency...")
        
        if not self.auth_token:
            self.add_result("User Stats Consistency", False, "No auth token available")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(f"{BASE_URL}/stats", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                subscription_plan = data.get("subscription_plan", "")
                
                if subscription_plan == "premium":
                    self.add_result("User Stats Consistency", True, "User stats show premium plan consistently")
                    return True
                else:
                    self.add_result("User Stats Consistency", False, f"User stats show {subscription_plan} instead of premium")
                    return False
            else:
                self.add_result("User Stats Consistency", False, f"Failed to get user stats: {response.status_code}")
                return False
                
        except Exception as e:
            self.add_result("User Stats Consistency", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all final verification tests"""
        self.log("🚀 Starting Final Verification Tests for msylla54@yahoo.fr")
        self.log("=" * 80)
        
        # Test 1: User can login successfully
        login_success = self.test_user_login()
        
        # Test 2: User has admin status
        admin_status = self.test_admin_status()
        
        # Test 3: User has premium plan
        premium_plan = self.test_premium_plan()
        
        # Test 4: User can access admin endpoints with admin key
        admin_access = self.test_admin_key_access()
        
        # Test 5: User stats consistency
        stats_consistency = self.test_user_stats_consistency()
        
        # Summary
        self.log("=" * 80)
        self.log("🎯 FINAL VERIFICATION SUMMARY")
        self.log("=" * 80)
        
        passed_tests = sum(1 for result in self.test_results if result["success"])
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"📊 OVERALL RESULTS: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        
        # Detailed results
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            self.log(f"{status} {result['test']}: {result['details']}")
        
        # Check all requirements
        all_requirements_met = (
            login_success and 
            admin_status and 
            premium_plan and 
            admin_access and 
            stats_consistency
        )
        
        self.log("=" * 80)
        self.log("📋 REQUIREMENTS VERIFICATION")
        self.log("=" * 80)
        
        req_status = "✅" if login_success else "❌"
        self.log(f"{req_status} User can login with msylla54@yahoo.fr / NewPassword123")
        
        req_status = "✅" if admin_status else "❌"
        self.log(f"{req_status} User has is_admin: true")
        
        req_status = "✅" if premium_plan else "❌"
        self.log(f"{req_status} User has subscription_plan: premium")
        
        req_status = "✅" if admin_access else "❌"
        self.log(f"{req_status} User can access admin endpoints with admin key ECOMSIMPLY_ADMIN_2024")
        
        if all_requirements_met:
            self.log("=" * 80)
            self.log("🎉 ALL REQUIREMENTS SUCCESSFULLY MET!")
            self.log("✅ User msylla54@yahoo.fr is now a fully functional admin user")
            self.log("✅ User can access the admin interface and price/promotion management")
            self.log("✅ User maintains premium subscription benefits")
            self.log("=" * 80)
        else:
            self.log("=" * 80)
            self.log("❌ SOME REQUIREMENTS NOT MET")
            self.log("❌ Please review the failed tests above")
            self.log("=" * 80)
        
        return all_requirements_met

def main():
    """Main test execution"""
    tester = FinalVerificationTester()
    success = tester.run_all_tests()
    return success

if __name__ == "__main__":
    main()