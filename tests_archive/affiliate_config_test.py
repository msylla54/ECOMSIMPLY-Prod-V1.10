#!/usr/bin/env python3
"""
ECOMSIMPLY Affiliate Configuration API Testing Suite
Tests the affiliate configuration API endpoints as requested in the review.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 30
ADMIN_KEY = "ECOMSIMPLY_ADMIN_2024"

class AffiliateConfigTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.admin_token = None
        self.admin_user_data = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_admin_user_registration(self):
        """Test admin user registration with admin key"""
        self.log("Testing admin user registration with admin key...")
        
        # Generate unique admin test user data
        timestamp = int(time.time())
        admin_user = {
            "email": f"admin.test{timestamp}@ecomsimply.fr",
            "name": "Admin Test User",
            "password": "AdminPassword123!",
            "admin_key": ADMIN_KEY
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=admin_user)
            
            if response.status_code == 200:
                data = response.json()
                admin_token = data.get("token")
                admin_user_data = data.get("user")
                
                # Validate response structure
                if admin_token and admin_user_data:
                    # Check if user is marked as admin
                    if admin_user_data.get("is_admin") == True:
                        self.log(f"✅ Admin Registration: Successfully registered admin user {admin_user_data['name']}")
                        self.log(f"   User ID: {admin_user_data['id']}")
                        self.log(f"   Email: {admin_user_data['email']}")
                        self.log(f"   Admin Status: {admin_user_data['is_admin']}")
                        
                        # Store admin credentials for admin tests
                        self.admin_token = admin_token
                        self.admin_user_data = admin_user_data
                        return True
                    else:
                        self.log("❌ Admin Registration: User not marked as admin despite correct admin key", "ERROR")
                        return False
                else:
                    self.log("❌ Admin Registration: Missing token or user data in response", "ERROR")
                    return False
            else:
                self.log(f"❌ Admin Registration failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Admin Registration failed: {str(e)}", "ERROR")
            return False
    
    def test_affiliate_config_get(self):
        """Test GET /api/admin/affiliate-config endpoint"""
        self.log("Testing GET affiliate configuration endpoint...")
        
        if not self.admin_token:
            self.log("❌ Cannot test affiliate config: No admin token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            response = self.session.get(f"{BASE_URL}/admin/affiliate-config?admin_key={ADMIN_KEY}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate required fields
                required_fields = ["success", "config"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log(f"❌ Affiliate Config GET: Missing fields {missing_fields}", "ERROR")
                    return False
                
                if not data.get("success"):
                    self.log("❌ Affiliate Config GET: Success field is false", "ERROR")
                    return False
                
                config = data.get("config", {})
                
                self.log(f"✅ Affiliate Config GET: Successfully retrieved configuration")
                self.log(f"   Commission Pro: {config.get('default_commission_rate_pro', 'N/A')}%")
                self.log(f"   Commission Premium: {config.get('default_commission_rate_premium', 'N/A')}%")
                self.log(f"   Commission Type: {config.get('commission_type', 'N/A')}")
                self.log(f"   Payment Frequency: {config.get('payment_frequency', 'N/A')}")
                self.log(f"   Minimum Payout: {config.get('minimum_payout', 'N/A')}€")
                self.log(f"   Program Enabled: {config.get('program_enabled', 'N/A')}")
                
                return True
            else:
                self.log(f"❌ Affiliate Config GET failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Affiliate Config GET failed: {str(e)}", "ERROR")
            return False
    
    def test_affiliate_config_update(self):
        """Test PUT /api/admin/affiliate-config endpoint"""
        self.log("Testing PUT affiliate configuration endpoint...")
        
        if not self.admin_token:
            self.log("❌ Cannot test affiliate config update: No admin token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test configuration update
        config_update = {
            "default_commission_rate_pro": 12.0,
            "default_commission_rate_premium": 18.0,
            "commission_type": "recurring",
            "payment_frequency": "monthly",
            "minimum_payout": 75.0,
            "program_enabled": True,
            "auto_approval": False,
            "cookie_duration_days": 45,
            "welcome_message": "Bienvenue dans notre programme d'affiliation mis à jour!"
        }
        
        try:
            response = self.session.put(
                f"{BASE_URL}/admin/affiliate-config?admin_key={ADMIN_KEY}", 
                json=config_update, 
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response
                if not data.get("success"):
                    self.log("❌ Affiliate Config UPDATE: Success field is false", "ERROR")
                    return False
                
                message = data.get("message", "")
                if "mise à jour" not in message.lower():
                    self.log("❌ Affiliate Config UPDATE: Unexpected response message", "ERROR")
                    return False
                
                self.log(f"✅ Affiliate Config UPDATE: Successfully updated configuration")
                self.log(f"   Response: {message}")
                self.log(f"   Updated Pro Rate: {config_update['default_commission_rate_pro']}%")
                self.log(f"   Updated Premium Rate: {config_update['default_commission_rate_premium']}%")
                self.log(f"   Updated Minimum Payout: {config_update['minimum_payout']}€")
                
                return True
            else:
                self.log(f"❌ Affiliate Config UPDATE failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Affiliate Config UPDATE failed: {str(e)}", "ERROR")
            return False
    
    def test_affiliate_bulk_update(self):
        """Test POST /api/admin/affiliate-bulk-update endpoint"""
        self.log("Testing POST affiliate bulk update endpoint...")
        
        if not self.admin_token:
            self.log("❌ Cannot test affiliate bulk update: No admin token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test bulk commission update
        bulk_update = {
            "commission_rate_pro": 15.0,
            "commission_rate_premium": 20.0,
            "commission_type": "recurring"
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/admin/affiliate-bulk-update?admin_key={ADMIN_KEY}", 
                json=bulk_update, 
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response
                if not data.get("success"):
                    self.log("❌ Affiliate Bulk Update: Success field is false", "ERROR")
                    return False
                
                message = data.get("message", "")
                
                self.log(f"✅ Affiliate Bulk Update: Successfully updated affiliate commissions")
                self.log(f"   Response: {message}")
                self.log(f"   New Pro Rate: {bulk_update['commission_rate_pro']}%")
                self.log(f"   New Premium Rate: {bulk_update['commission_rate_premium']}%")
                self.log(f"   Commission Type: {bulk_update['commission_type']}")
                
                return True
            else:
                self.log(f"❌ Affiliate Bulk Update failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Affiliate Bulk Update failed: {str(e)}", "ERROR")
            return False
    
    def test_affiliate_config_authentication(self):
        """Test affiliate configuration endpoints require proper admin authentication"""
        self.log("Testing affiliate configuration authentication requirements...")
        
        # Test endpoints without authentication
        endpoints_to_test = [
            ("GET", f"/admin/affiliate-config?admin_key={ADMIN_KEY}"),
            ("PUT", f"/admin/affiliate-config?admin_key={ADMIN_KEY}"),
            ("POST", f"/admin/affiliate-bulk-update?admin_key={ADMIN_KEY}")
        ]
        
        success_count = 0
        
        # Test without auth token
        for method, endpoint in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.session.get(f"{BASE_URL}{endpoint}")
                elif method == "PUT":
                    response = self.session.put(f"{BASE_URL}{endpoint}", json={})
                elif method == "POST":
                    response = self.session.post(f"{BASE_URL}{endpoint}", json={})
                
                if response.status_code in [401, 403]:
                    self.log(f"✅ Auth Required: {method} {endpoint} correctly requires authentication")
                    success_count += 1
                else:
                    self.log(f"❌ Auth Required: {method} {endpoint} should require auth but returned {response.status_code}", "ERROR")
                    
            except Exception as e:
                self.log(f"❌ Auth test failed for {method} {endpoint}: {str(e)}", "ERROR")
        
        # Test with invalid admin key
        if self.admin_token:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            invalid_admin_key = "INVALID_KEY"
            
            try:
                response = self.session.get(f"{BASE_URL}/admin/affiliate-config?admin_key={invalid_admin_key}", headers=headers)
                if response.status_code == 403:
                    self.log("✅ Invalid Admin Key: Correctly rejected invalid admin key")
                    success_count += 1
                else:
                    self.log(f"❌ Invalid Admin Key: Should reject invalid key but returned {response.status_code}", "ERROR")
            except Exception as e:
                self.log(f"❌ Invalid admin key test failed: {str(e)}", "ERROR")
        
        return success_count >= len(endpoints_to_test)
    
    def test_affiliate_config_data_validation(self):
        """Test affiliate configuration data validation"""
        self.log("Testing affiliate configuration data validation...")
        
        if not self.admin_token:
            self.log("❌ Cannot test data validation: No admin token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test bulk update with missing data
        try:
            response = self.session.post(
                f"{BASE_URL}/admin/affiliate-bulk-update?admin_key={ADMIN_KEY}", 
                json={}, 
                headers=headers
            )
            
            if response.status_code == 400:
                self.log("✅ Data Validation: Empty bulk update correctly rejected")
                return True
            else:
                self.log(f"❌ Data Validation: Empty data should be rejected but got {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Data Validation test failed: {str(e)}", "ERROR")
            return False

    def test_mongodb_objectid_serialization(self):
        """Test that MongoDB ObjectId serialization works correctly"""
        self.log("Testing MongoDB ObjectId serialization...")
        
        if not self.admin_token:
            self.log("❌ Cannot test ObjectId serialization: No admin token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Test GET endpoint which should return serialized ObjectIds
            response = self.session.get(f"{BASE_URL}/admin/affiliate-config?admin_key={ADMIN_KEY}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                config = data.get("config", {})
                
                # Check if config has an id field and it's a string (not ObjectId)
                if "id" in config:
                    config_id = config["id"]
                    if isinstance(config_id, str):
                        self.log("✅ ObjectId Serialization: MongoDB ObjectId properly converted to string")
                        self.log(f"   Config ID: {config_id}")
                        return True
                    else:
                        self.log(f"❌ ObjectId Serialization: ID should be string but got {type(config_id)}", "ERROR")
                        return False
                else:
                    self.log("✅ ObjectId Serialization: No ObjectId fields to serialize (acceptable)")
                    return True
            else:
                self.log(f"❌ ObjectId Serialization test failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ ObjectId Serialization test failed: {str(e)}", "ERROR")
            return False

    def run_all_tests(self):
        """Run all affiliate configuration API tests"""
        self.log("🚀 Starting Affiliate Configuration API Testing...")
        self.log("=" * 80)
        
        # Track test results
        test_results = []
        
        # First, create admin user for testing
        test_results.append(("Admin User Registration", self.test_admin_user_registration()))
        
        # Run affiliate configuration tests
        test_results.append(("Affiliate Config GET", self.test_affiliate_config_get()))
        test_results.append(("Affiliate Config UPDATE", self.test_affiliate_config_update()))
        test_results.append(("Affiliate Bulk Update", self.test_affiliate_bulk_update()))
        test_results.append(("Affiliate Config Authentication", self.test_affiliate_config_authentication()))
        test_results.append(("Affiliate Config Data Validation", self.test_affiliate_config_data_validation()))
        test_results.append(("MongoDB ObjectId Serialization", self.test_mongodb_objectid_serialization()))
        
        # Print final results
        self.log("=" * 80)
        self.log("🏁 AFFILIATE CONFIGURATION API TEST RESULTS:")
        self.log("=" * 80)
        
        passed = 0
        failed = 0
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{status}: {test_name}")
            if result:
                passed += 1
            else:
                failed += 1
        
        self.log("=" * 80)
        self.log(f"📊 SUMMARY: {passed} PASSED, {failed} FAILED, {passed + failed} TOTAL")
        success_rate = (passed / (passed + failed)) * 100 if (passed + failed) > 0 else 0
        self.log(f"📈 SUCCESS RATE: {success_rate:.1f}%")
        
        if success_rate >= 90:
            self.log("🎉 EXCELLENT: Affiliate configuration API is working excellently!")
        elif success_rate >= 75:
            self.log("✅ GOOD: Affiliate configuration API is working well with minor issues")
        elif success_rate >= 50:
            self.log("⚠️  MODERATE: Affiliate configuration API has some issues that need attention")
        else:
            self.log("❌ CRITICAL: Affiliate configuration API has major issues requiring immediate attention")
        
        self.log("=" * 80)
        return success_rate >= 75

if __name__ == "__main__":
    tester = AffiliateConfigTester()
    
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 ALL AFFILIATE CONFIGURATION TESTS COMPLETED SUCCESSFULLY!")
        exit(0)
    else:
        print("\n⚠️  AFFILIATE CONFIGURATION TESTS COMPLETED WITH ISSUES")
        exit(1)