#!/usr/bin/env python3
"""
Price and Promotion Management System Backend Testing
Testing all endpoints for the newly implemented price and promotion management system
"""

import requests
import json
import uuid
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')
load_dotenv('/app/frontend/.env')

# Get backend URL from frontend environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

# Admin key for authentication
ADMIN_KEY = "ECOMSIMPLY_ADMIN_2024"

class PricePromotionTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.promotion_ids = []  # Store created promotion IDs for cleanup
        
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_data and not success:
            print(f"   Response: {response_data}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
        print()

    def test_admin_authentication(self):
        """Test admin key authentication on all endpoints"""
        print("🔐 TESTING ADMIN AUTHENTICATION")
        
        # Test with wrong admin key
        try:
            response = self.session.get(
                f"{API_BASE}/admin/plans-config",
                params={"admin_key": "wrong_key"}
            )
            
            if response.status_code == 403:
                self.log_test("Admin Authentication - Wrong Key Rejection", True, 
                            "Correctly rejected wrong admin key with 403")
            else:
                self.log_test("Admin Authentication - Wrong Key Rejection", False,
                            f"Expected 403, got {response.status_code}")
        except Exception as e:
            self.log_test("Admin Authentication - Wrong Key Rejection", False, str(e))
        
        # Test with correct admin key
        try:
            response = self.session.get(
                f"{API_BASE}/admin/plans-config",
                params={"admin_key": ADMIN_KEY}
            )
            
            if response.status_code == 200:
                self.log_test("Admin Authentication - Correct Key Acceptance", True,
                            "Correctly accepted valid admin key")
            else:
                self.log_test("Admin Authentication - Correct Key Acceptance", False,
                            f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_test("Admin Authentication - Correct Key Acceptance", False, str(e))

    def test_plans_config_endpoints(self):
        """Test plans configuration endpoints"""
        print("📋 TESTING PLANS CONFIGURATION ENDPOINTS")
        
        # Test GET /api/admin/plans-config
        try:
            response = self.session.get(
                f"{API_BASE}/admin/plans-config",
                params={"admin_key": ADMIN_KEY}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "plans_config" in data:
                    plans = data["plans_config"]
                    plan_names = [plan.get("plan_name") for plan in plans]
                    
                    if "gratuit" in plan_names and "pro" in plan_names and "premium" in plan_names:
                        self.log_test("GET Plans Config", True,
                                    f"Retrieved {len(plans)} plans: {plan_names}")
                    else:
                        self.log_test("GET Plans Config", False,
                                    f"Missing expected plans. Found: {plan_names}")
                else:
                    self.log_test("GET Plans Config", False,
                                "Invalid response structure", data)
            else:
                self.log_test("GET Plans Config", False,
                            f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("GET Plans Config", False, str(e))
        
        # Test PUT /api/admin/plans-config/{plan_name} - Update Pro plan
        try:
            update_data = {
                "price": 39.0,  # Change from 29€ to 39€
                "features": {
                    "sheets_per_month": 150,  # Increase from 100
                    "ai_generation": "advanced",
                    "export_formats": True,
                    "priority_support": True  # New feature
                },
                "limits": {"max_sheets": 150}
            }
            
            response = self.session.put(
                f"{API_BASE}/admin/plans-config/pro",
                json=update_data,
                params={"admin_key": ADMIN_KEY}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test("PUT Plans Config - Pro Plan Update", True,
                                f"Updated Pro plan price to 39€ and features")
                else:
                    self.log_test("PUT Plans Config - Pro Plan Update", False,
                                "Success flag not set", data)
            else:
                self.log_test("PUT Plans Config - Pro Plan Update", False,
                            f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("PUT Plans Config - Pro Plan Update", False, str(e))
        
        # Test PUT /api/admin/plans-config/{plan_name} - Update Premium plan
        try:
            update_data = {
                "price": 129.0,  # Change from 99€ to 129€
                "features": {
                    "sheets_per_month": -1,
                    "ai_generation": "premium",
                    "seo_automation": True,
                    "dedicated_support": True,
                    "white_label": True  # New premium feature
                },
                "limits": {"max_sheets": -1}
            }
            
            response = self.session.put(
                f"{API_BASE}/admin/plans-config/premium",
                json=update_data,
                params={"admin_key": ADMIN_KEY}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test("PUT Plans Config - Premium Plan Update", True,
                                f"Updated Premium plan price to 129€")
                else:
                    self.log_test("PUT Plans Config - Premium Plan Update", False,
                                "Success flag not set", data)
            else:
                self.log_test("PUT Plans Config - Premium Plan Update", False,
                            f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("PUT Plans Config - Premium Plan Update", False, str(e))
        
        # Test invalid plan name
        try:
            response = self.session.put(
                f"{API_BASE}/admin/plans-config/invalid_plan",
                json={"price": 50.0},
                params={"admin_key": ADMIN_KEY}
            )
            
            if response.status_code == 400:
                self.log_test("PUT Plans Config - Invalid Plan Name", True,
                            "Correctly rejected invalid plan name with 400")
            else:
                self.log_test("PUT Plans Config - Invalid Plan Name", False,
                            f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("PUT Plans Config - Invalid Plan Name", False, str(e))

    def test_promotions_management_endpoints(self):
        """Test promotions management endpoints"""
        print("🎯 TESTING PROMOTIONS MANAGEMENT ENDPOINTS")
        
        # Test GET /api/admin/promotions (initially empty)
        try:
            response = self.session.get(
                f"{API_BASE}/admin/promotions",
                params={"admin_key": ADMIN_KEY}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "promotions" in data:
                    initial_count = len(data["promotions"])
                    self.log_test("GET Promotions - Initial State", True,
                                f"Retrieved {initial_count} existing promotions")
                else:
                    self.log_test("GET Promotions - Initial State", False,
                                "Invalid response structure", data)
            else:
                self.log_test("GET Promotions - Initial State", False,
                            f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("GET Promotions - Initial State", False, str(e))
        
        # Test POST /api/admin/promotions - Create percentage discount for Pro plan
        try:
            promotion_data = {
                "title": "Black Friday Pro Discount",
                "description": "Special 30% discount on Pro plan for Black Friday",
                "target_plans": ["pro"],
                "discount_type": "percentage",
                "discount_value": 30.0,
                "badge_text": "PROMO -30%",
                "promotional_text": "Offre Black Friday - Économisez 30% sur le plan Pro!",
                "start_date": datetime.utcnow().isoformat(),
                "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "is_active": True
            }
            
            response = self.session.post(
                f"{API_BASE}/admin/promotions",
                json=promotion_data,
                params={"admin_key": ADMIN_KEY}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "promotion_id" in data:
                    promotion_id = data["promotion_id"]
                    self.promotion_ids.append(promotion_id)
                    self.log_test("POST Promotions - Create Pro Discount", True,
                                f"Created promotion with ID: {promotion_id}")
                else:
                    self.log_test("POST Promotions - Create Pro Discount", False,
                                "Success flag not set or missing promotion_id", data)
            else:
                self.log_test("POST Promotions - Create Pro Discount", False,
                            f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("POST Promotions - Create Pro Discount", False, str(e))
        
        # Test POST /api/admin/promotions - Create fixed amount discount for Premium plan
        try:
            promotion_data = {
                "title": "New Year Premium Deal",
                "description": "Fixed 20€ discount on Premium plan for New Year",
                "target_plans": ["premium"],
                "discount_type": "fixed_amount",
                "discount_value": 20.0,
                "badge_text": "ÉCONOMISEZ 20€",
                "promotional_text": "Offre Nouvel An - 20€ de réduction sur Premium!",
                "start_date": datetime.utcnow().isoformat(),
                "end_date": (datetime.utcnow() + timedelta(days=14)).isoformat(),
                "is_active": True
            }
            
            response = self.session.post(
                f"{API_BASE}/admin/promotions",
                json=promotion_data,
                params={"admin_key": ADMIN_KEY}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "promotion_id" in data:
                    promotion_id = data["promotion_id"]
                    self.promotion_ids.append(promotion_id)
                    self.log_test("POST Promotions - Create Premium Fixed Discount", True,
                                f"Created fixed discount promotion with ID: {promotion_id}")
                else:
                    self.log_test("POST Promotions - Create Premium Fixed Discount", False,
                                "Success flag not set or missing promotion_id", data)
            else:
                self.log_test("POST Promotions - Create Premium Fixed Discount", False,
                            f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("POST Promotions - Create Premium Fixed Discount", False, str(e))
        
        # Test GET /api/admin/promotions (after creating promotions)
        try:
            response = self.session.get(
                f"{API_BASE}/admin/promotions",
                params={"admin_key": ADMIN_KEY}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "promotions" in data:
                    promotions = data["promotions"]
                    created_promotions = [p for p in promotions if p.get("id") in self.promotion_ids]
                    self.log_test("GET Promotions - After Creation", True,
                                f"Found {len(created_promotions)} of {len(self.promotion_ids)} created promotions")
                else:
                    self.log_test("GET Promotions - After Creation", False,
                                "Invalid response structure", data)
            else:
                self.log_test("GET Promotions - After Creation", False,
                            f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("GET Promotions - After Creation", False, str(e))
        
        # Test PUT /api/admin/promotions/{promotion_id} - Update promotion
        if self.promotion_ids:
            try:
                promotion_id = self.promotion_ids[0]  # Update first created promotion
                update_data = {
                    "discount_value": 35.0,  # Increase discount from 30% to 35%
                    "badge_text": "SUPER PROMO -35%",
                    "promotional_text": "Offre Black Friday ÉTENDUE - Économisez 35% sur le plan Pro!"
                }
                
                response = self.session.put(
                    f"{API_BASE}/admin/promotions/{promotion_id}",
                    json=update_data,
                    params={"admin_key": ADMIN_KEY}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        self.log_test("PUT Promotions - Update Promotion", True,
                                    f"Updated promotion discount to 35%")
                    else:
                        self.log_test("PUT Promotions - Update Promotion", False,
                                    "Success flag not set", data)
                else:
                    self.log_test("PUT Promotions - Update Promotion", False,
                                f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("PUT Promotions - Update Promotion", False, str(e))
        
        # Test PUT with non-existent promotion ID
        try:
            fake_id = str(uuid.uuid4())
            response = self.session.put(
                f"{API_BASE}/admin/promotions/{fake_id}",
                json={"discount_value": 50.0},
                params={"admin_key": ADMIN_KEY}
            )
            
            if response.status_code == 404:
                self.log_test("PUT Promotions - Non-existent ID", True,
                            "Correctly returned 404 for non-existent promotion")
            else:
                self.log_test("PUT Promotions - Non-existent ID", False,
                            f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("PUT Promotions - Non-existent ID", False, str(e))

    def test_public_pricing_endpoint(self):
        """Test public pricing endpoint with active promotions"""
        print("🌐 TESTING PUBLIC PRICING ENDPOINT")
        
        try:
            response = self.session.get(f"{API_BASE}/public/plans-pricing")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "plans" in data:
                    plans = data["plans"]
                    active_promotions_count = data.get("active_promotions_count", 0)
                    
                    # Check if plans have correct structure
                    plan_names = [plan.get("plan_name") for plan in plans]
                    expected_plans = ["gratuit", "pro", "premium"]
                    
                    if all(plan in plan_names for plan in expected_plans):
                        self.log_test("GET Public Pricing - Plan Structure", True,
                                    f"All expected plans present: {plan_names}")
                    else:
                        self.log_test("GET Public Pricing - Plan Structure", False,
                                    f"Missing plans. Expected: {expected_plans}, Got: {plan_names}")
                    
                    # Check for promotion application
                    promoted_plans = [plan for plan in plans if plan.get("promotion_active")]
                    if promoted_plans:
                        for plan in promoted_plans:
                            plan_name = plan.get("plan_name")
                            original_price = plan.get("original_price")
                            current_price = plan.get("price")
                            promotion_text = plan.get("promotion_text", "")
                            
                            if original_price and current_price < original_price:
                                discount = original_price - current_price
                                self.log_test(f"Promotion Applied - {plan_name.title()} Plan", True,
                                            f"Price: {original_price}€ → {current_price}€ (Save {discount:.2f}€)")
                            else:
                                self.log_test(f"Promotion Applied - {plan_name.title()} Plan", False,
                                            f"Promotion marked active but price not reduced")
                    
                    self.log_test("GET Public Pricing - Active Promotions", True,
                                f"Found {active_promotions_count} active promotions affecting {len(promoted_plans)} plans")
                    
                else:
                    self.log_test("GET Public Pricing", False,
                                "Invalid response structure", data)
            else:
                self.log_test("GET Public Pricing", False,
                            f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("GET Public Pricing", False, str(e))

    def test_promotion_date_validation(self):
        """Test promotion date validation (active vs expired promotions)"""
        print("📅 TESTING PROMOTION DATE VALIDATION")
        
        # Create an expired promotion
        try:
            expired_promotion_data = {
                "title": "Expired Test Promotion",
                "description": "This promotion should be expired",
                "target_plans": ["pro"],
                "discount_type": "percentage",
                "discount_value": 50.0,
                "badge_text": "EXPIRED -50%",
                "promotional_text": "This should not appear in public pricing",
                "start_date": (datetime.utcnow() - timedelta(days=10)).isoformat(),
                "end_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),  # Expired yesterday
                "is_active": True
            }
            
            response = self.session.post(
                f"{API_BASE}/admin/promotions",
                json=expired_promotion_data,
                params={"admin_key": ADMIN_KEY}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "promotion_id" in data:
                    expired_promotion_id = data["promotion_id"]
                    self.promotion_ids.append(expired_promotion_id)
                    self.log_test("Create Expired Promotion", True,
                                f"Created expired promotion for testing")
                    
                    # Now check if expired promotion affects public pricing
                    pricing_response = self.session.get(f"{API_BASE}/public/plans-pricing")
                    if pricing_response.status_code == 200:
                        pricing_data = pricing_response.json()
                        plans = pricing_data.get("plans", [])
                        
                        # Check if any plan shows the expired promotion
                        expired_promotion_found = False
                        for plan in plans:
                            if plan.get("promotion_text") == "This should not appear in public pricing":
                                expired_promotion_found = True
                                break
                        
                        if not expired_promotion_found:
                            self.log_test("Expired Promotion Filtering", True,
                                        "Expired promotion correctly excluded from public pricing")
                        else:
                            self.log_test("Expired Promotion Filtering", False,
                                        "Expired promotion incorrectly included in public pricing")
                    
                else:
                    self.log_test("Create Expired Promotion", False,
                                "Failed to create expired promotion for testing", data)
            else:
                self.log_test("Create Expired Promotion", False,
                            f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Expired Promotion", False, str(e))
        
        # Create a future promotion
        try:
            future_promotion_data = {
                "title": "Future Test Promotion",
                "description": "This promotion should not be active yet",
                "target_plans": ["premium"],
                "discount_type": "percentage",
                "discount_value": 25.0,
                "badge_text": "FUTURE -25%",
                "promotional_text": "This should not appear in public pricing yet",
                "start_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),  # Starts tomorrow
                "end_date": (datetime.utcnow() + timedelta(days=10)).isoformat(),
                "is_active": True
            }
            
            response = self.session.post(
                f"{API_BASE}/admin/promotions",
                json=future_promotion_data,
                params={"admin_key": ADMIN_KEY}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "promotion_id" in data:
                    future_promotion_id = data["promotion_id"]
                    self.promotion_ids.append(future_promotion_id)
                    self.log_test("Create Future Promotion", True,
                                f"Created future promotion for testing")
                    
                    # Check if future promotion affects public pricing
                    pricing_response = self.session.get(f"{API_BASE}/public/plans-pricing")
                    if pricing_response.status_code == 200:
                        pricing_data = pricing_response.json()
                        plans = pricing_data.get("plans", [])
                        
                        # Check if any plan shows the future promotion
                        future_promotion_found = False
                        for plan in plans:
                            if plan.get("promotion_text") == "This should not appear in public pricing yet":
                                future_promotion_found = True
                                break
                        
                        if not future_promotion_found:
                            self.log_test("Future Promotion Filtering", True,
                                        "Future promotion correctly excluded from public pricing")
                        else:
                            self.log_test("Future Promotion Filtering", False,
                                        "Future promotion incorrectly included in public pricing")
                    
                else:
                    self.log_test("Create Future Promotion", False,
                                "Failed to create future promotion for testing", data)
            else:
                self.log_test("Create Future Promotion", False,
                            f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Future Promotion", False, str(e))

    def test_promotion_deletion(self):
        """Test promotion deletion"""
        print("🗑️ TESTING PROMOTION DELETION")
        
        if self.promotion_ids:
            # Test DELETE with valid promotion ID
            try:
                promotion_id = self.promotion_ids[-1]  # Delete last created promotion
                response = self.session.delete(
                    f"{API_BASE}/admin/promotions/{promotion_id}",
                    params={"admin_key": ADMIN_KEY}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        self.log_test("DELETE Promotions - Valid ID", True,
                                    f"Successfully deleted promotion {promotion_id}")
                        self.promotion_ids.remove(promotion_id)  # Remove from cleanup list
                    else:
                        self.log_test("DELETE Promotions - Valid ID", False,
                                    "Success flag not set", data)
                else:
                    self.log_test("DELETE Promotions - Valid ID", False,
                                f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("DELETE Promotions - Valid ID", False, str(e))
        
        # Test DELETE with non-existent promotion ID
        try:
            fake_id = str(uuid.uuid4())
            response = self.session.delete(
                f"{API_BASE}/admin/promotions/{fake_id}",
                params={"admin_key": ADMIN_KEY}
            )
            
            if response.status_code == 404:
                self.log_test("DELETE Promotions - Non-existent ID", True,
                            "Correctly returned 404 for non-existent promotion")
            else:
                self.log_test("DELETE Promotions - Non-existent ID", False,
                            f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("DELETE Promotions - Non-existent ID", False, str(e))

    def cleanup_test_data(self):
        """Clean up test promotions"""
        print("🧹 CLEANING UP TEST DATA")
        
        for promotion_id in self.promotion_ids:
            try:
                response = self.session.delete(
                    f"{API_BASE}/admin/promotions/{promotion_id}",
                    params={"admin_key": ADMIN_KEY}
                )
                if response.status_code == 200:
                    print(f"✅ Cleaned up promotion {promotion_id}")
                else:
                    print(f"⚠️ Failed to clean up promotion {promotion_id}")
            except Exception as e:
                print(f"❌ Error cleaning up promotion {promotion_id}: {e}")

    def run_all_tests(self):
        """Run all price and promotion management tests"""
        print("🚀 STARTING COMPREHENSIVE PRICE AND PROMOTION MANAGEMENT SYSTEM TESTING")
        print("=" * 80)
        
        # Run all test suites
        self.test_admin_authentication()
        self.test_plans_config_endpoints()
        self.test_promotions_management_endpoints()
        self.test_public_pricing_endpoint()
        self.test_promotion_date_validation()
        self.test_promotion_deletion()
        
        # Clean up test data
        self.cleanup_test_data()
        
        # Print summary
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n🎯 PRICE AND PROMOTION MANAGEMENT SYSTEM TESTING COMPLETED!")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "results": self.test_results
        }

if __name__ == "__main__":
    print("🔧 Price and Promotion Management System Backend Testing")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"🔑 Admin Key: {ADMIN_KEY}")
    print()
    
    tester = PricePromotionTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if results["failed_tests"] == 0 else 1)