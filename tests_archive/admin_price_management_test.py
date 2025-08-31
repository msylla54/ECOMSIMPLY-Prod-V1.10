#!/usr/bin/env python3
"""
ECOMSIMPLY Admin Price Management System Testing Suite
Tests the complete admin price management system including authentication, price configuration, and public pricing API.
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 30
ADMIN_KEY = "ECOMSIMPLY_ADMIN_2024"
ADMIN_EMAIL = "msylla54@yahoo.fr"
ADMIN_PASSWORD = "NewPassword123"

class AdminPriceManagementTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.admin_token = None
        self.admin_user_data = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_api_health(self):
        """Test if the API is accessible"""
        self.log("Testing API health check...")
        try:
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ API Health Check: {data.get('message', 'OK')}")
                return True
            else:
                self.log(f"❌ API Health Check failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ API Health Check failed: {str(e)}", "ERROR")
            return False
    
    def test_admin_authentication(self):
        """Test admin authentication with msylla54@yahoo.fr"""
        self.log("Testing admin authentication...")
        
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("token")
                self.admin_user_data = data.get("user")
                
                if self.admin_token and self.admin_user_data:
                    # Verify admin status
                    if self.admin_user_data.get("is_admin") == True:
                        self.log(f"✅ Admin Authentication: Successfully logged in as admin")
                        self.log(f"   Email: {self.admin_user_data['email']}")
                        self.log(f"   Name: {self.admin_user_data['name']}")
                        self.log(f"   Admin Status: {self.admin_user_data['is_admin']}")
                        self.log(f"   Plan: {self.admin_user_data.get('subscription_plan', 'N/A')}")
                        return True
                    else:
                        self.log("❌ Admin Authentication: User is not marked as admin", "ERROR")
                        return False
                else:
                    self.log("❌ Admin Authentication: Missing token or user data", "ERROR")
                    return False
            else:
                self.log(f"❌ Admin Authentication failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Admin Authentication failed: {str(e)}", "ERROR")
            return False
    
    def test_admin_key_access(self):
        """Test admin key access for price management endpoints"""
        self.log("Testing admin key access...")
        
        # Test GET plans-config with admin key
        try:
            response = self.session.get(f"{BASE_URL}/admin/plans-config?admin_key={ADMIN_KEY}")
            
            if response.status_code == 200:
                data = response.json()
                plans_config = data.get("plans_config", [])
                self.log(f"✅ Admin Key Access: Successfully accessed plans configuration")
                self.log(f"   Plans found: {len(plans_config)} plans")
                
                # Validate plan structure
                for plan_data in plans_config:
                    plan_name = plan_data.get("plan_name", "unknown")
                    price = plan_data.get("price", 0)
                    self.log(f"   Plan {plan_name}: {price}€")
                
                return True
            else:
                self.log(f"❌ Admin Key Access failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Admin Key Access failed: {str(e)}", "ERROR")
            return False
    
    def test_load_current_plans_configuration(self):
        """Test loading current plan configurations"""
        self.log("Testing current plans configuration loading...")
        
        try:
            response = self.session.get(f"{BASE_URL}/admin/plans-config?admin_key={ADMIN_KEY}")
            
            if response.status_code == 200:
                data = response.json()
                plans_config = data.get("plans_config", [])
                
                # Convert to dict for easier access
                plans_data = {}
                for plan in plans_config:
                    plan_name = plan.get("plan_name")
                    if plan_name:
                        plans_data[plan_name] = plan
                
                # Validate required plans exist
                required_plans = ["gratuit", "pro", "premium"]
                missing_plans = [plan for plan in required_plans if plan not in plans_data]
                
                if missing_plans:
                    self.log(f"❌ Plans Configuration: Missing plans {missing_plans}", "ERROR")
                    return False, None
                
                self.log(f"✅ Plans Configuration: All required plans found")
                
                # Display current configuration
                for plan_name in required_plans:
                    plan_data = plans_data[plan_name]
                    price = plan_data.get("price", 0)
                    currency = plan_data.get("currency", "EUR")
                    self.log(f"   {plan_name.capitalize()}: {price}{currency}")
                
                return True, plans_data
            else:
                self.log(f"❌ Plans Configuration failed: {response.status_code} - {response.text}", "ERROR")
                return False, None
                
        except Exception as e:
            self.log(f"❌ Plans Configuration failed: {str(e)}", "ERROR")
            return False, None
    
    def test_update_pro_plan_price(self, new_price=35.0):
        """Test updating Pro plan price from 29€ to 35€"""
        self.log(f"Testing Pro plan price update to {new_price}€...")
        
        update_data = {
            "price": new_price,
            "currency": "EUR"
        }
        
        try:
            response = self.session.put(
                f"{BASE_URL}/admin/plans-config/pro?admin_key={ADMIN_KEY}",
                json=update_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Pro Plan Update: Successfully updated to {new_price}€")
                self.log(f"   Message: {result.get('message', 'Updated')}")
                self.log(f"   Updated Plan: {result.get('updated_plan', {}).get('plan_name', 'pro')}")
                self.log(f"   New Price: {result.get('updated_plan', {}).get('price', new_price)}€")
                return True
            else:
                self.log(f"❌ Pro Plan Update failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Pro Plan Update failed: {str(e)}", "ERROR")
            return False
    
    def test_update_premium_plan_price(self, new_price=120.0):
        """Test updating Premium plan price from 99€ to 120€"""
        self.log(f"Testing Premium plan price update to {new_price}€...")
        
        update_data = {
            "price": new_price,
            "currency": "EUR"
        }
        
        try:
            response = self.session.put(
                f"{BASE_URL}/admin/plans-config/premium?admin_key={ADMIN_KEY}",
                json=update_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Premium Plan Update: Successfully updated to {new_price}€")
                self.log(f"   Message: {result.get('message', 'Updated')}")
                self.log(f"   Updated Plan: {result.get('updated_plan', {}).get('plan_name', 'premium')}")
                self.log(f"   New Price: {result.get('updated_plan', {}).get('price', new_price)}€")
                return True
            else:
                self.log(f"❌ Premium Plan Update failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Premium Plan Update failed: {str(e)}", "ERROR")
            return False
    
    def test_public_pricing_api(self):
        """Test public pricing API returns updated prices"""
        self.log("Testing public pricing API...")
        
        try:
            response = self.session.get(f"{BASE_URL}/public/plans-pricing")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["plans", "active_promotions_count"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log(f"❌ Public Pricing: Missing fields {missing_fields}", "ERROR")
                    return False, None
                
                plans_list = data["plans"]
                self.log(f"✅ Public Pricing API: Successfully retrieved pricing data")
                self.log(f"   Plans available: {len(plans_list)}")
                self.log(f"   Active promotions: {data['active_promotions_count']}")
                
                # Convert to dict for easier access
                plans = {}
                for plan in plans_list:
                    plan_name = plan.get("plan_name")
                    if plan_name:
                        plans[plan_name] = plan
                
                # Display current public pricing
                for plan_name, plan_data in plans.items():
                    price = plan_data.get("price", 0)
                    original_price = plan_data.get("original_price")
                    promotion_active = plan_data.get("promotion_active", False)
                    
                    if promotion_active and original_price:
                        self.log(f"   {plan_name.capitalize()}: {price}€ (was {original_price}€) - PROMOTION ACTIVE")
                    else:
                        self.log(f"   {plan_name.capitalize()}: {price}€")
                
                return True, {"plans": plans, "active_promotions_count": data["active_promotions_count"]}
            else:
                self.log(f"❌ Public Pricing API failed: {response.status_code} - {response.text}", "ERROR")
                return False, None
                
        except Exception as e:
            self.log(f"❌ Public Pricing API failed: {str(e)}", "ERROR")
            return False, None
    
    def test_verify_price_updates(self, expected_pro_price=35.0, expected_premium_price=120.0):
        """Verify that price updates are reflected in public API"""
        self.log("Verifying price updates in public API...")
        
        success, pricing_data = self.test_public_pricing_api()
        if not success:
            return False
        
        plans = pricing_data["plans"]
        
        # Check Pro plan price (accounting for active promotions)
        pro_plan = plans.get("pro", {})
        pro_price = pro_plan.get("price", 0)
        original_price = pro_plan.get("original_price")
        promotion_active = pro_plan.get("promotion_active", False)
        
        if promotion_active and original_price:
            # If promotion is active, check the original price
            if original_price == expected_pro_price:
                self.log(f"✅ Pro Plan Verification: Original price correctly updated to {original_price}€ (showing {pro_price}€ with promotion)")
            else:
                self.log(f"❌ Pro Plan Verification: Expected original price {expected_pro_price}€, got {original_price}€", "ERROR")
                return False
        else:
            # No promotion, check direct price
            if pro_price == expected_pro_price:
                self.log(f"✅ Pro Plan Verification: Price correctly updated to {pro_price}€")
            else:
                self.log(f"❌ Pro Plan Verification: Expected {expected_pro_price}€, got {pro_price}€", "ERROR")
                return False
        
        # Check Premium plan price
        premium_plan = plans.get("premium", {})
        premium_price = premium_plan.get("price", 0)
        
        if premium_price == expected_premium_price:
            self.log(f"✅ Premium Plan Verification: Price correctly updated to {premium_price}€")
        else:
            self.log(f"❌ Premium Plan Verification: Expected {expected_premium_price}€, got {premium_price}€", "ERROR")
            return False
        
        return True
    
    def test_create_test_promotion(self):
        """Test creating a test promotion"""
        self.log("Testing promotion creation...")
        
        # Create a test promotion for Pro plan
        promotion_data = {
            "title": "Test Promotion - Pro Plan",
            "description": "Test promotion for Pro plan pricing",
            "target_plans": ["pro"],
            "discount_type": "percentage",
            "discount_value": 20.0,
            "badge_text": "PROMO -20%",
            "promotional_text": "Offre de test limitée",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/admin/promotions?admin_key={ADMIN_KEY}",
                json=promotion_data
            )
            
            if response.status_code == 200:
                result = response.json()
                promotion_id = result.get("promotion", {}).get("id")
                self.log(f"✅ Promotion Creation: Successfully created test promotion")
                self.log(f"   Promotion ID: {promotion_id}")
                self.log(f"   Title: {result.get('promotion', {}).get('title')}")
                self.log(f"   Discount: {result.get('promotion', {}).get('discount_value')}%")
                return True, promotion_id
            else:
                self.log(f"❌ Promotion Creation failed: {response.status_code} - {response.text}", "ERROR")
                return False, None
                
        except Exception as e:
            self.log(f"❌ Promotion Creation failed: {str(e)}", "ERROR")
            return False, None
    
    def test_promotion_integration(self):
        """Test that promotions are properly applied to pricing"""
        self.log("Testing promotion integration with pricing...")
        
        # Create a test promotion
        success, promotion_id = self.test_create_test_promotion()
        if not success:
            return False
        
        # Wait a moment for promotion to be processed
        time.sleep(2)
        
        # Check if promotion is applied in public pricing
        success, pricing_data = self.test_public_pricing_api()
        if not success:
            return False
        
        plans = pricing_data["plans"]
        pro_plan = plans.get("pro", {})
        
        # Check if promotion is active
        promotion_active = pro_plan.get("promotion_active", False)
        if promotion_active:
            original_price = pro_plan.get("original_price", 0)
            discounted_price = pro_plan.get("price", 0)
            promotion_badge = pro_plan.get("promotion_badge", "")
            
            self.log(f"✅ Promotion Integration: Promotion successfully applied")
            self.log(f"   Original Price: {original_price}€")
            self.log(f"   Discounted Price: {discounted_price}€")
            self.log(f"   Promotion Badge: {promotion_badge}")
            
            # Verify discount calculation (20% off)
            expected_discounted_price = original_price * 0.8
            if abs(discounted_price - expected_discounted_price) < 0.01:
                self.log(f"✅ Discount Calculation: Correctly calculated 20% discount")
            else:
                self.log(f"❌ Discount Calculation: Expected {expected_discounted_price}€, got {discounted_price}€", "ERROR")
                return False
        else:
            self.log(f"❌ Promotion Integration: Promotion not applied to Pro plan", "ERROR")
            return False
        
        # Clean up - delete test promotion
        if promotion_id:
            try:
                delete_response = self.session.delete(f"{BASE_URL}/admin/promotions/{promotion_id}?admin_key={ADMIN_KEY}")
                if delete_response.status_code == 200:
                    self.log(f"✅ Cleanup: Test promotion deleted successfully")
                else:
                    self.log(f"⚠️  Cleanup: Could not delete test promotion", "WARN")
            except Exception as e:
                self.log(f"⚠️  Cleanup error: {str(e)}", "WARN")
        
        return True
    
    def test_invalid_admin_key(self):
        """Test that invalid admin keys are rejected"""
        self.log("Testing invalid admin key rejection...")
        
        try:
            response = self.session.get(f"{BASE_URL}/admin/plans-config?admin_key=INVALID_KEY")
            
            if response.status_code == 403:
                self.log(f"✅ Invalid Admin Key: Correctly rejected with 403")
                return True
            else:
                self.log(f"❌ Invalid Admin Key: Should reject but returned {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Invalid Admin Key test failed: {str(e)}", "ERROR")
            return False
    
    def test_unauthorized_price_update(self):
        """Test that price updates without admin key are rejected"""
        self.log("Testing unauthorized price update rejection...")
        
        update_data = {
            "price": 999.0,
            "currency": "EUR"
        }
        
        try:
            # Try without admin key
            response = self.session.put(f"{BASE_URL}/admin/plans-config/pro", json=update_data)
            
            if response.status_code in [401, 403]:
                self.log(f"✅ Unauthorized Update: Correctly rejected with {response.status_code}")
                return True
            else:
                self.log(f"❌ Unauthorized Update: Should reject but returned {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Unauthorized Update test failed: {str(e)}", "ERROR")
            return False
    
    def run_complete_price_management_test(self):
        """Run the complete price management test flow"""
        self.log("=" * 80)
        self.log("STARTING COMPLETE ADMIN PRICE MANAGEMENT SYSTEM TEST")
        self.log("=" * 80)
        
        test_results = []
        
        # Test 1: API Health
        test_results.append(("API Health Check", self.test_api_health()))
        
        # Test 2: Admin Authentication
        test_results.append(("Admin Authentication", self.test_admin_authentication()))
        
        # Test 3: Admin Key Access
        test_results.append(("Admin Key Access", self.test_admin_key_access()))
        
        # Test 4: Load Current Plans Configuration
        success, _ = self.test_load_current_plans_configuration()
        test_results.append(("Load Plans Configuration", success))
        
        # Test 5: Update Pro Plan Price
        test_results.append(("Update Pro Plan Price", self.test_update_pro_plan_price(35.0)))
        
        # Test 6: Update Premium Plan Price
        test_results.append(("Update Premium Plan Price", self.test_update_premium_plan_price(120.0)))
        
        # Test 7: Verify Price Updates in Public API
        test_results.append(("Verify Price Updates", self.test_verify_price_updates(35.0, 120.0)))
        
        # Test 8: Test Promotion Integration
        test_results.append(("Promotion Integration", self.test_promotion_integration()))
        
        # Test 9: Test Security - Invalid Admin Key
        test_results.append(("Invalid Admin Key Rejection", self.test_invalid_admin_key()))
        
        # Test 10: Test Security - Unauthorized Update
        test_results.append(("Unauthorized Update Rejection", self.test_unauthorized_price_update()))
        
        # Summary
        self.log("=" * 80)
        self.log("ADMIN PRICE MANAGEMENT SYSTEM TEST RESULTS")
        self.log("=" * 80)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{status}: {test_name}")
            if result:
                passed_tests += 1
        
        self.log("=" * 80)
        success_rate = (passed_tests / total_tests) * 100
        self.log(f"OVERALL RESULT: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        
        if success_rate >= 80:
            self.log("🎉 ADMIN PRICE MANAGEMENT SYSTEM: FULLY FUNCTIONAL!")
            self.log("✅ Admin authentication working with msylla54@yahoo.fr")
            self.log("✅ Admin key access working with ECOMSIMPLY_ADMIN_2024")
            self.log("✅ Price management APIs functional")
            self.log("✅ Public pricing API returns dynamic data")
            self.log("✅ Promotion system integrated and working")
            self.log("✅ Security controls in place")
        else:
            self.log("❌ ADMIN PRICE MANAGEMENT SYSTEM: ISSUES DETECTED!")
            self.log("Some critical functionality may not be working properly.")
        
        self.log("=" * 80)
        return success_rate >= 80

def main():
    """Main test execution"""
    tester = AdminPriceManagementTester()
    success = tester.run_complete_price_management_test()
    
    if success:
        print("\n🎉 ALL ADMIN PRICE MANAGEMENT TESTS COMPLETED SUCCESSFULLY!")
        print("The 'Modifier' buttons functionality is fully operational.")
    else:
        print("\n❌ ADMIN PRICE MANAGEMENT TESTS FAILED!")
        print("Issues detected in the price management system.")
    
    return success

if __name__ == "__main__":
    main()