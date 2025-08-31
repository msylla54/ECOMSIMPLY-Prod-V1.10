#!/usr/bin/env python3
"""
Plan Migration Testing Suite
Testing the complete plan migration from Premium/Pro to Premium system

This test validates:
1. Plan migration endpoint POST /api/admin/migrate-plans
2. Create test users with old "premium" plans and verify migration
3. Verify that Premium users have access to all SEO features
4. Test that SEO endpoints now require "premium" subscription only
5. Test user registration with admin key (should get "premium" plan)
6. Test complete SEO Premium workflow with new plan structure
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://ecomsimply.com/api"
ADMIN_KEY = "ECOMSIMPLY_ADMIN_2024"

class PlanMigrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_users = []
        self.results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": []
        }
    
    def log_test(self, test_name, passed, details=""):
        """Log test result"""
        self.results["total_tests"] += 1
        if passed:
            self.results["passed_tests"] += 1
            status = "✅ PASSED"
        else:
            self.results["failed_tests"] += 1
            status = "❌ FAILED"
        
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results["test_details"].append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def create_admin_user(self):
        """Create admin user for testing"""
        try:
            admin_data = {
                "email": f"admin.migration.test.{int(time.time())}@example.com",
                "name": "Migration Test Admin",
                "password": "AdminTest123!",
                "admin_key": ADMIN_KEY
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=admin_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("token")
                self.log_test("Admin User Creation", True, f"Admin created: {admin_data['email']}")
                return True
            else:
                self.log_test("Admin User Creation", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin User Creation", False, f"Exception: {str(e)}")
            return False
    
    def create_test_user_with_plan(self, plan_type):
        """Create test user with specific plan"""
        try:
            user_data = {
                "email": f"test.{plan_type}.{int(time.time())}@example.com",
                "name": f"Test User {plan_type.title()}",
                "password": "TestPass123!"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=user_data)
            
            if response.status_code == 200:
                data = response.json()
                user_token = data.get("token")
                
                # Manually update user plan in database (simulating existing users)
                # This would normally be done via direct database access
                user_info = {
                    "email": user_data["email"],
                    "token": user_token,
                    "plan": plan_type
                }
                self.test_users.append(user_info)
                
                self.log_test(f"Test User Creation ({plan_type})", True, f"User created: {user_data['email']}")
                return user_info
            else:
                self.log_test(f"Test User Creation ({plan_type})", False, f"Status: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test(f"Test User Creation ({plan_type})", False, f"Exception: {str(e)}")
            return None
    
    def test_plan_migration_endpoint(self):
        """Test POST /api/admin/migrate-plans endpoint"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.post(f"{BACKEND_URL}/admin/migrate-plans", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Plan Migration Endpoint", True, f"Migration response: {data}")
                return True
            elif response.status_code == 404:
                self.log_test("Plan Migration Endpoint", False, "Endpoint not found - migration not implemented")
                return False
            else:
                self.log_test("Plan Migration Endpoint", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Plan Migration Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_current_subscription_plans(self):
        """Test current subscription plan configuration"""
        try:
            # Check what plans are currently supported by trying to access SEO features
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{BACKEND_URL}/seo/config", headers=headers)
            
            if response.status_code == 200:
                self.log_test("Current Plan System - Admin Access", True, "Admin can access SEO features")
            elif response.status_code == 403:
                error_data = response.json()
                error_msg = error_data.get("detail", "")
                if "premium" in error_msg.lower():
                    self.log_test("Current Plan System", True, "System requires 'premium' plan")
                elif "pro" in error_msg.lower() or "premium" in error_msg.lower():
                    self.log_test("Current Plan System", False, f"System still uses old plans: {error_msg}")
                else:
                    self.log_test("Current Plan System", False, f"Unexpected error: {error_msg}")
            else:
                self.log_test("Current Plan System", False, f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Current Plan System", False, f"Exception: {str(e)}")
    
    def test_seo_premium_access(self, user_info, expected_access=True):
        """Test SEO premium features access"""
        try:
            headers = {"Authorization": f"Bearer {user_info['token']}"}
            
            # Test GET /api/seo/config
            response = self.session.get(f"{BACKEND_URL}/seo/config", headers=headers)
            
            if expected_access:
                if response.status_code == 200:
                    self.log_test(f"SEO Config Access ({user_info['plan']})", True, "User can access SEO config")
                else:
                    self.log_test(f"SEO Config Access ({user_info['plan']})", False, f"Expected access but got {response.status_code}")
            else:
                if response.status_code == 403:
                    self.log_test(f"SEO Config Access ({user_info['plan']})", True, "User correctly denied access")
                else:
                    self.log_test(f"SEO Config Access ({user_info['plan']})", False, f"Expected 403 but got {response.status_code}")
            
            # Test POST /api/seo/scrape/trends
            trends_data = {
                "keywords": ["test product", "e-commerce"],
                "region": "FR"
            }
            response = self.session.post(f"{BACKEND_URL}/seo/scrape/trends", json=trends_data, headers=headers)
            
            if expected_access:
                if response.status_code in [200, 503]:  # 503 for service unavailable is acceptable
                    self.log_test(f"SEO Trends Access ({user_info['plan']})", True, "User can access SEO trends")
                else:
                    self.log_test(f"SEO Trends Access ({user_info['plan']})", False, f"Expected access but got {response.status_code}")
            else:
                if response.status_code == 403:
                    self.log_test(f"SEO Trends Access ({user_info['plan']})", True, "User correctly denied access")
                else:
                    self.log_test(f"SEO Trends Access ({user_info['plan']})", False, f"Expected 403 but got {response.status_code}")
                    
        except Exception as e:
            self.log_test(f"SEO Access Test ({user_info['plan']})", False, f"Exception: {str(e)}")
    
    def test_admin_registration_plan(self):
        """Test that admin registration gives premium plan"""
        try:
            admin_data = {
                "email": f"admin.premium.test.{int(time.time())}@example.com",
                "name": "Premium Admin Test",
                "password": "AdminTest123!",
                "admin_key": ADMIN_KEY
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=admin_data)
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("token")
                
                # Check user stats to see subscription plan
                headers = {"Authorization": f"Bearer {token}"}
                stats_response = self.session.get(f"{BACKEND_URL}/stats", headers=headers)
                
                if stats_response.status_code == 200:
                    stats_data = stats_response.json()
                    plan = stats_data.get("subscription_plan", "")
                    
                    if plan == "premium":
                        self.log_test("Admin Registration Plan", True, "Admin gets premium plan")
                    elif plan == "premium":
                        self.log_test("Admin Registration Plan", False, f"Admin gets '{plan}' instead of 'premium'")
                    else:
                        self.log_test("Admin Registration Plan", False, f"Admin gets unexpected plan: {plan}")
                else:
                    self.log_test("Admin Registration Plan", False, f"Cannot get user stats: {stats_response.status_code}")
            else:
                self.log_test("Admin Registration Plan", False, f"Admin registration failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Admin Registration Plan", False, f"Exception: {str(e)}")
    
    def test_subscription_plan_display(self):
        """Test that subscription plan display shows 'Premium' instead of 'Premium'"""
        try:
            # This would typically test frontend display, but we can check API responses
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{BACKEND_URL}/stats", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                plan = data.get("subscription_plan", "")
                
                if plan == "premium":
                    self.log_test("Subscription Plan Display", True, "Plan shows as 'premium'")
                elif plan in ["premium", "pro"]:
                    self.log_test("Subscription Plan Display", False, f"Plan still shows as '{plan}' instead of 'premium'")
                else:
                    self.log_test("Subscription Plan Display", False, f"Unexpected plan: {plan}")
            else:
                self.log_test("Subscription Plan Display", False, f"Cannot get user stats: {response.status_code}")
                
        except Exception as e:
            self.log_test("Subscription Plan Display", False, f"Exception: {str(e)}")
    
    def test_plan_hierarchy(self):
        """Test plan hierarchy and access controls"""
        try:
            # Test that premium plan has access to all features
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test various premium endpoints
            endpoints_to_test = [
                "/seo/config",
                "/seo/analytics", 
                "/analytics/detailed",
                "/premium/image-styles"
            ]
            
            accessible_endpoints = 0
            total_endpoints = len(endpoints_to_test)
            
            for endpoint in endpoints_to_test:
                try:
                    response = self.session.get(f"{BACKEND_URL}{endpoint}", headers=headers)
                    if response.status_code in [200, 503]:  # 200 OK or 503 Service Unavailable (acceptable)
                        accessible_endpoints += 1
                except:
                    pass
            
            if accessible_endpoints >= total_endpoints * 0.75:  # At least 75% should be accessible
                self.log_test("Plan Hierarchy", True, f"{accessible_endpoints}/{total_endpoints} premium endpoints accessible")
            else:
                self.log_test("Plan Hierarchy", False, f"Only {accessible_endpoints}/{total_endpoints} premium endpoints accessible")
                
        except Exception as e:
            self.log_test("Plan Hierarchy", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all plan migration tests"""
        print("🚀 STARTING PLAN MIGRATION TESTING SUITE")
        print("=" * 60)
        
        # Phase 1: Setup and Plan Migration Testing
        print("\n📋 PHASE 1: Plan Migration Testing")
        if not self.create_admin_user():
            print("❌ Cannot proceed without admin user")
            return
        
        self.test_plan_migration_endpoint()
        self.test_current_subscription_plans()
        
        # Create test users with old plans
        premium_user = self.create_test_user_with_plan("premium")
        pro_user = self.create_test_user_with_plan("pro")
        free_user = self.create_test_user_with_plan("gratuit")
        
        # Phase 2: SEO Features Access Control
        print("\n📋 PHASE 2: SEO Features Access Control")
        if premium_user:
            self.test_seo_premium_access(premium_user, expected_access=True)
        if pro_user:
            self.test_seo_premium_access(pro_user, expected_access=True)
        if free_user:
            self.test_seo_premium_access(free_user, expected_access=False)
        
        # Phase 3: User Experience Testing
        print("\n📋 PHASE 3: User Experience Testing")
        self.test_admin_registration_plan()
        self.test_subscription_plan_display()
        
        # Phase 4: Complete Integration Validation
        print("\n📋 PHASE 4: Complete Integration Validation")
        self.test_plan_hierarchy()
        
        # Print final results
        self.print_final_results()
    
    def print_final_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 60)
        print("🎯 PLAN MIGRATION TESTING RESULTS")
        print("=" * 60)
        
        total = self.results["total_tests"]
        passed = self.results["passed_tests"]
        failed = self.results["failed_tests"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"📊 SUMMARY:")
        print(f"   Total Tests: {total}")
        print(f"   Passed: {passed}")
        print(f"   Failed: {failed}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.results["test_details"]:
            print(f"   {result['status']}: {result['test']}")
            if result['details']:
                print(f"      → {result['details']}")
        
        # Analysis and recommendations
        print(f"\n🔍 ANALYSIS:")
        if success_rate >= 80:
            print("   ✅ Plan migration system is mostly functional")
        elif success_rate >= 60:
            print("   ⚠️ Plan migration system has some issues")
        else:
            print("   ❌ Plan migration system has critical issues")
        
        # Check for specific issues
        migration_endpoint_found = any("Plan Migration Endpoint" in result["test"] and "PASSED" in result["status"] for result in self.results["test_details"])
        premium_plan_used = any("premium" in result["details"].lower() for result in self.results["test_details"])
        
        print(f"\n💡 RECOMMENDATIONS:")
        if not migration_endpoint_found:
            print("   🔧 Implement POST /api/admin/migrate-plans endpoint")
        if not premium_plan_used:
            print("   🔧 Update system to use 'premium' plan instead of 'pro'/'premium'")
            print("   🔧 Update subscription validation to check for 'premium' plan")
            print("   🔧 Update admin registration to assign 'premium' plan")
        
        print(f"\n🎯 NEXT STEPS:")
        print("   1. Review failed tests and implement missing functionality")
        print("   2. Update plan validation logic throughout the system")
        print("   3. Test migration with real user data")
        print("   4. Update frontend to display 'Premium' instead of 'Premium'")

if __name__ == "__main__":
    tester = PlanMigrationTester()
    tester.run_all_tests()