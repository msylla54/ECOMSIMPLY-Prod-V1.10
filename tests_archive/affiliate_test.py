#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Affiliate Management System
Testing all affiliate endpoints and database operations
"""

import requests
import json
import time
import uuid
from datetime import datetime
import os

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ecomsimply.com')
API_BASE = f"{BACKEND_URL}/api"

# Admin credentials and key
ADMIN_EMAIL = "msylla54@yahoo.fr"
ADMIN_PASSWORD = "NewPassword123"
ADMIN_KEY = "ECOMSIMPLY_ADMIN_2024"

class AffiliateSystemTester:
    def __init__(self):
        self.admin_token = None
        self.test_affiliate_code = None
        self.test_affiliate_id = None
        self.test_user_id = None
        self.test_user_token = None
        self.test_click_id = None
        self.results = []
        
    def log_result(self, test_name, success, details="", response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        if response_data and not success:
            print(f"   Response: {response_data}")
        
        self.results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
        print()

    def authenticate_admin(self):
        """Authenticate as admin user"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            })
            
            print(f"DEBUG: Login response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"DEBUG: Login response data: {data}")
                self.admin_token = data.get("access_token") or data.get("token")
                print(f"DEBUG: Admin token received: {self.admin_token[:20] if self.admin_token else None}...")
                self.log_result("Admin Authentication", True, f"Admin authenticated successfully")
                return True
            else:
                self.log_result("Admin Authentication", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False

    def create_test_user(self):
        """Create a test user for conversion testing"""
        try:
            test_email = f"affiliate_test_{uuid.uuid4().hex[:8]}@test.com"
            response = requests.post(f"{API_BASE}/auth/register", json={
                "email": test_email,
                "name": "Affiliate Test User",
                "password": "TestPassword123"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.test_user_token = data.get("access_token")
                self.test_user_id = data.get("user_id")
                self.log_result("Test User Creation", True, f"Test user created: {test_email}")
                return True
            else:
                self.log_result("Test User Creation", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Test User Creation", False, f"Exception: {str(e)}")
            return False

    def test_affiliate_registration(self):
        """Test affiliate registration endpoint"""
        try:
            test_email = f"affiliate_{uuid.uuid4().hex[:8]}@test.com"
            registration_data = {
                "email": test_email,
                "name": "Test Affiliate",
                "company": "Test Company",
                "website": "https://test-affiliate.com",
                "social_media": {
                    "twitter": "@testaffiliate",
                    "linkedin": "linkedin.com/in/testaffiliate"
                },
                "payment_method": "bank_transfer",
                "payment_details": {
                    "bank_name": "Test Bank",
                    "account_number": "123456789"
                },
                "motivation": "I want to promote this amazing product to my audience"
            }
            
            response = requests.post(f"{API_BASE}/affiliate/register", json=registration_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("affiliate_code"):
                    self.test_affiliate_code = data.get("affiliate_code")
                    self.log_result("Affiliate Registration", True, 
                                  f"Affiliate registered with code: {self.test_affiliate_code}")
                    return True
                else:
                    self.log_result("Affiliate Registration", False, "Missing success or affiliate_code", data)
                    return False
            else:
                self.log_result("Affiliate Registration", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Affiliate Registration", False, f"Exception: {str(e)}")
            return False

    def test_affiliate_registration_duplicate_email(self):
        """Test affiliate registration with duplicate email"""
        try:
            # Use the same email as previous registration
            duplicate_data = {
                "email": f"affiliate_{uuid.uuid4().hex[:8]}@test.com",
                "name": "Duplicate Test",
                "motivation": "Testing duplicate"
            }
            
            # Register first affiliate
            requests.post(f"{API_BASE}/affiliate/register", json=duplicate_data)
            
            # Try to register again with same email
            response = requests.post(f"{API_BASE}/affiliate/register", json=duplicate_data)
            
            if response.status_code == 400:
                self.log_result("Affiliate Registration - Duplicate Email", True, 
                              "Correctly rejected duplicate email")
                return True
            else:
                self.log_result("Affiliate Registration - Duplicate Email", False, 
                              f"Should return 400, got {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Affiliate Registration - Duplicate Email", False, f"Exception: {str(e)}")
            return False

    def test_admin_affiliates_list(self):
        """Test admin affiliates list endpoint"""
        print(f"DEBUG: admin_token = {self.admin_token}")
        if not self.admin_token:
            self.log_result("Admin Affiliates List", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{API_BASE}/admin/affiliates?admin_key={ADMIN_KEY}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "affiliates" in data:
                    affiliates_count = len(data.get("affiliates", []))
                    total_count = data.get("total_count", 0)
                    self.log_result("Admin Affiliates List", True, 
                                  f"Retrieved {affiliates_count} affiliates (total: {total_count})")
                    return True
                else:
                    self.log_result("Admin Affiliates List", False, "Missing success or affiliates", data)
                    return False
            else:
                self.log_result("Admin Affiliates List", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Admin Affiliates List", False, f"Exception: {str(e)}")
            return False

    def approve_test_affiliate(self):
        """Approve the test affiliate for tracking tests"""
        if not self.admin_token or not self.test_affiliate_code:
            self.log_result("Affiliate Approval", False, "Missing admin token or affiliate code")
            return False
            
        try:
            # First get the affiliate ID
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{API_BASE}/admin/affiliates?admin_key={ADMIN_KEY}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                affiliates = data.get("affiliates", [])
                
                # Find our test affiliate
                test_affiliate = None
                for affiliate in affiliates:
                    if affiliate.get("affiliate_code") == self.test_affiliate_code:
                        test_affiliate = affiliate
                        self.test_affiliate_id = affiliate.get("id")
                        break
                
                if test_affiliate:
                    # Approve the affiliate using PUT with query parameters
                    approve_url = f"{API_BASE}/admin/affiliates/{self.test_affiliate_id}/status"
                    approve_params = {
                        "admin_key": ADMIN_KEY,
                        "status": "approved"
                    }
                    
                    approve_response = requests.put(
                        approve_url,
                        params=approve_params,
                        headers=headers
                    )
                    
                    if approve_response.status_code == 200:
                        self.log_result("Affiliate Approval", True, "Test affiliate approved successfully")
                        return True
                    else:
                        self.log_result("Affiliate Approval", False, 
                                      f"Status: {approve_response.status_code}", approve_response.text)
                        return False
                else:
                    self.log_result("Affiliate Approval", False, "Test affiliate not found in admin list")
                    return False
            else:
                self.log_result("Affiliate Approval", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Affiliate Approval", False, f"Exception: {str(e)}")
            return False

    def test_affiliate_tracking(self):
        """Test affiliate click tracking endpoint"""
        if not self.test_affiliate_code:
            self.log_result("Affiliate Tracking", False, "No test affiliate code available")
            return False
            
        try:
            tracking_params = {
                "landing_page": "https://ecomsimply.com/pricing",
                "utm_source": "affiliate",
                "utm_medium": "referral",
                "utm_campaign": "test_campaign"
            }
            
            response = requests.get(
                f"{API_BASE}/affiliate/track/{self.test_affiliate_code}",
                params=tracking_params,
                headers={"User-Agent": "Test Browser", "Referer": "https://test-affiliate.com"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("click_id"):
                    self.test_click_id = data.get("click_id")
                    self.log_result("Affiliate Tracking", True, 
                                  f"Click tracked successfully, ID: {self.test_click_id}")
                    return True
                else:
                    self.log_result("Affiliate Tracking", False, "Missing success or click_id", data)
                    return False
            else:
                self.log_result("Affiliate Tracking", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Affiliate Tracking", False, f"Exception: {str(e)}")
            return False

    def test_affiliate_tracking_invalid_code(self):
        """Test affiliate tracking with invalid code"""
        try:
            response = requests.get(
                f"{API_BASE}/affiliate/track/INVALID123",
                params={"landing_page": "https://ecomsimply.com/pricing"}
            )
            
            if response.status_code == 404:
                self.log_result("Affiliate Tracking - Invalid Code", True, 
                              "Correctly rejected invalid affiliate code")
                return True
            else:
                self.log_result("Affiliate Tracking - Invalid Code", False, 
                              f"Should return 404, got {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Affiliate Tracking - Invalid Code", False, f"Exception: {str(e)}")
            return False

    def test_affiliate_conversion(self):
        """Test affiliate conversion recording"""
        if not self.test_affiliate_code or not self.test_user_id:
            self.log_result("Affiliate Conversion", False, "Missing affiliate code or user ID")
            return False
            
        try:
            conversion_data = {
                "affiliate_code": self.test_affiliate_code,
                "user_id": self.test_user_id,
                "subscription_plan": "pro",
                "subscription_amount": 29.00,
                "click_id": self.test_click_id
            }
            
            response = requests.post(f"{API_BASE}/affiliate/conversion", json=conversion_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("conversion_id"):
                    commission = data.get("commission_amount", 0)
                    self.log_result("Affiliate Conversion", True, 
                                  f"Conversion recorded, commission: €{commission}")
                    return True
                else:
                    self.log_result("Affiliate Conversion", False, "Missing success or conversion_id", data)
                    return False
            else:
                self.log_result("Affiliate Conversion", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Affiliate Conversion", False, f"Exception: {str(e)}")
            return False

    def test_affiliate_conversion_invalid_plan(self):
        """Test affiliate conversion with invalid plan"""
        if not self.test_affiliate_code or not self.test_user_id:
            return False
            
        try:
            conversion_data = {
                "affiliate_code": self.test_affiliate_code,
                "user_id": self.test_user_id,
                "subscription_plan": "invalid_plan",
                "subscription_amount": 29.00
            }
            
            response = requests.post(f"{API_BASE}/affiliate/conversion", json=conversion_data)
            
            if response.status_code == 200:
                data = response.json()
                if not data.get("success"):
                    self.log_result("Affiliate Conversion - Invalid Plan", True, 
                                  "Correctly rejected invalid plan")
                    return True
                else:
                    self.log_result("Affiliate Conversion - Invalid Plan", False, 
                                  "Should reject invalid plan", data)
                    return False
            else:
                self.log_result("Affiliate Conversion - Invalid Plan", False, 
                              f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Affiliate Conversion - Invalid Plan", False, f"Exception: {str(e)}")
            return False

    def test_affiliate_statistics(self):
        """Test affiliate statistics endpoint"""
        if not self.test_affiliate_code:
            self.log_result("Affiliate Statistics", False, "No test affiliate code available")
            return False
            
        try:
            response = requests.get(f"{API_BASE}/affiliate/{self.test_affiliate_code}/stats")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = [
                    "total_clicks", "total_conversions", "conversion_rate", 
                    "total_earnings", "pending_commissions", "paid_commissions",
                    "clicks_this_month", "conversions_this_month", "earnings_this_month",
                    "top_landing_pages", "recent_conversions"
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_result("Affiliate Statistics", True, 
                                  f"Stats: {data['total_clicks']} clicks, {data['total_conversions']} conversions, €{data['total_earnings']} earnings")
                    return True
                else:
                    self.log_result("Affiliate Statistics", False, 
                                  f"Missing fields: {missing_fields}", data)
                    return False
            else:
                self.log_result("Affiliate Statistics", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Affiliate Statistics", False, f"Exception: {str(e)}")
            return False

    def test_affiliate_statistics_invalid_code(self):
        """Test affiliate statistics with invalid code"""
        try:
            response = requests.get(f"{API_BASE}/affiliate/INVALID123/stats")
            
            if response.status_code == 404:
                self.log_result("Affiliate Statistics - Invalid Code", True, 
                              "Correctly rejected invalid affiliate code")
                return True
            else:
                self.log_result("Affiliate Statistics - Invalid Code", False, 
                              f"Should return 404, got {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Affiliate Statistics - Invalid Code", False, f"Exception: {str(e)}")
            return False

    def test_admin_affiliates_list_pagination(self):
        """Test admin affiliates list with pagination"""
        if not self.admin_token:
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(
                f"{API_BASE}/admin/affiliates?admin_key={ADMIN_KEY}&skip=0&limit=10", 
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if "page" in data and "total_pages" in data:
                    self.log_result("Admin Affiliates List - Pagination", True, 
                                  f"Page {data['page']} of {data['total_pages']}")
                    return True
                else:
                    self.log_result("Admin Affiliates List - Pagination", False, 
                                  "Missing pagination info", data)
                    return False
            else:
                self.log_result("Admin Affiliates List - Pagination", False, 
                              f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Admin Affiliates List - Pagination", False, f"Exception: {str(e)}")
            return False

    def test_admin_affiliate_status_update(self):
        """Test admin affiliate status update"""
        if not self.admin_token or not self.test_affiliate_id:
            self.log_result("Admin Affiliate Status Update", False, "Missing admin token or affiliate ID")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Use PUT with query parameters as expected by the API
            update_url = f"{API_BASE}/admin/affiliates/{self.test_affiliate_id}/status"
            update_params = {
                "admin_key": ADMIN_KEY,
                "status": "suspended"
            }
            
            response = requests.put(
                update_url,
                params=update_params,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_result("Admin Affiliate Status Update", True, 
                                  "Status updated to suspended")
                    return True
                else:
                    self.log_result("Admin Affiliate Status Update", False, "Missing success", data)
                    return False
            else:
                self.log_result("Admin Affiliate Status Update", False, 
                              f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Admin Affiliate Status Update", False, f"Exception: {str(e)}")
            return False

    def test_admin_affiliate_detailed_stats(self):
        """Test admin detailed affiliate statistics"""
        if not self.admin_token or not self.test_affiliate_id:
            self.log_result("Admin Affiliate Detailed Stats", False, "Missing admin token or affiliate ID")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(
                f"{API_BASE}/admin/affiliates/{self.test_affiliate_id}/detailed-stats?admin_key={ADMIN_KEY}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "affiliate" in data:
                    clicks_count = len(data.get("clicks", []))
                    conversions_count = len(data.get("conversions", []))
                    commissions_count = len(data.get("commissions", []))
                    self.log_result("Admin Affiliate Detailed Stats", True, 
                                  f"Retrieved detailed stats: {clicks_count} clicks, {conversions_count} conversions, {commissions_count} commissions")
                    return True
                else:
                    self.log_result("Admin Affiliate Detailed Stats", False, 
                                  "Missing success or affiliate data", data)
                    return False
            else:
                self.log_result("Admin Affiliate Detailed Stats", False, 
                              f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Admin Affiliate Detailed Stats", False, f"Exception: {str(e)}")
            return False

    def test_admin_unauthorized_access(self):
        """Test admin endpoints without proper authorization"""
        try:
            # Test without admin token
            response = requests.get(f"{API_BASE}/admin/affiliates?admin_key={ADMIN_KEY}")
            
            if response.status_code in [401, 403]:
                self.log_result("Admin Unauthorized Access - No Token", True, 
                              "Correctly rejected request without token")
            else:
                self.log_result("Admin Unauthorized Access - No Token", False, 
                              f"Should return 401/403, got {response.status_code}")
                return False
            
            # Test with wrong admin key
            if self.admin_token:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                response = requests.get(f"{API_BASE}/admin/affiliates?admin_key=WRONG_KEY", headers=headers)
                
                if response.status_code == 403:
                    self.log_result("Admin Unauthorized Access - Wrong Key", True, 
                                  "Correctly rejected wrong admin key")
                    return True
                else:
                    self.log_result("Admin Unauthorized Access - Wrong Key", False, 
                                  f"Should return 403, got {response.status_code}")
                    return False
            
            return True
                
        except Exception as e:
            self.log_result("Admin Unauthorized Access", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all affiliate system tests"""
        print("🚀 Starting Comprehensive Affiliate Management System Testing")
        print("=" * 70)
        
        # Authentication and setup
        if not self.authenticate_admin():
            print("❌ Cannot proceed without admin authentication")
            return
            
        if not self.create_test_user():
            print("❌ Cannot proceed without test user")
            return
        
        # Test affiliate registration
        self.test_affiliate_registration()
        self.test_affiliate_registration_duplicate_email()
        
        # Test admin endpoints first to get affiliate ID
        self.test_admin_affiliates_list()
        
        # Approve test affiliate for tracking tests
        self.approve_test_affiliate()
        
        # Test affiliate tracking
        self.test_affiliate_tracking()
        self.test_affiliate_tracking_invalid_code()
        
        # Test affiliate conversions
        self.test_affiliate_conversion()
        self.test_affiliate_conversion_invalid_plan()
        
        # Test affiliate statistics
        self.test_affiliate_statistics()
        self.test_affiliate_statistics_invalid_code()
        
        # Test remaining admin endpoints
        self.test_admin_affiliates_list_pagination()
        self.test_admin_affiliate_status_update()
        self.test_admin_affiliate_detailed_stats()
        self.test_admin_unauthorized_access()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("=" * 70)
        print("📊 AFFILIATE MANAGEMENT SYSTEM TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
        else:
            print("🎉 ALL TESTS PASSED!")
        
        print("=" * 70)

if __name__ == "__main__":
    tester = AffiliateSystemTester()
    tester.run_all_tests()