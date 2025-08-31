#!/usr/bin/env python3
"""
ECOMSIMPLY SEO Premium Testing Suite - Admin User Test
Testing SEO functionality with admin user (premium plan)
"""

import requests
import json
import time
import random
import uuid
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 30

class SEOAdminTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.admin_token = None
        self.admin_user_data = None
        self.test_product_sheet_id = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def create_admin_user(self):
        """Create an admin user for testing SEO features"""
        self.log("Creating admin user for SEO testing...")
        
        # Register admin user with admin key
        admin_data = {
            "email": f"seo_admin_{uuid.uuid4().hex[:8]}@test.com",
            "name": "SEO Admin Tester",
            "password": "SecurePass123!",
            "admin_key": "ECOMSIMPLY_ADMIN_2024",
            "language": "fr"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=admin_data)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("token")
                self.admin_user_data = data.get("user")
                
                self.log("✅ Admin user created successfully")
                self.log(f"   Email: {admin_data['email']}")
                self.log(f"   Is Admin: {self.admin_user_data.get('is_admin', False)}")
                self.log(f"   Subscription: {self.admin_user_data.get('subscription_plan', 'unknown')}")
                self.log(f"   Token: {self.admin_token[:20]}...")
                return True
            else:
                self.log(f"❌ Admin user creation failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Admin user creation failed: {str(e)}", "ERROR")
            return False
    
    def create_test_product_sheet(self):
        """Create a test product sheet for SEO optimization"""
        self.log("Creating test product sheet for SEO testing...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        product_data = {
            "product_name": "Montre Connectée Premium SEO Admin Test",
            "product_description": "Montre intelligente avec GPS, suivi de santé, écran AMOLED et autonomie 7 jours",
            "generate_image": False,  # Skip image generation for faster testing
            "number_of_images": 1,
            "language": "fr"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=product_data, headers=headers)
            if response.status_code == 200:
                data = response.json()
                self.test_product_sheet_id = data.get("id")
                self.log("✅ Test product sheet created successfully")
                self.log(f"   Product Sheet ID: {self.test_product_sheet_id}")
                return True
            else:
                self.log(f"❌ Test product sheet creation failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Test product sheet creation failed: {str(e)}", "ERROR")
            return False
    
    def test_seo_config_get_admin(self):
        """Test GET /api/seo/config endpoint with admin user"""
        self.log("Testing SEO configuration retrieval with admin user...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            response = self.session.get(f"{BASE_URL}/seo/config", headers=headers)
            self.log(f"Response status: {response.status_code}")
            self.log(f"Response body: {response.text[:200]}...")
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ SEO config retrieval successful with admin user")
                self.log(f"   Config keys: {list(data.keys())}")
                return True
            elif response.status_code == 500:
                self.log("❌ SEO config still returns 500 even with admin user", "ERROR")
                self.log("   This confirms the subscription plan validation bug")
                return False
            else:
                self.log(f"❌ SEO config retrieval failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ SEO config retrieval failed: {str(e)}", "ERROR")
            return False
    
    def run_admin_seo_test(self):
        """Run SEO test with admin user"""
        self.log("🚀 Starting SEO Premium Testing with Admin User")
        self.log("=" * 60)
        
        test_results = {}
        
        # Create admin user and test
        test_results["create_admin_user"] = self.create_admin_user()
        test_results["create_test_product"] = self.create_test_product_sheet()
        test_results["seo_config_get_admin"] = self.test_seo_config_get_admin()
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log("📊 ADMIN SEO TESTING SUMMARY")
        self.log("=" * 60)
        
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{status}: {test_name}")
        
        self.log(f"\n🎯 OVERALL RESULT: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        
        return test_results

def main():
    """Main testing function"""
    tester = SEOAdminTester()
    results = tester.run_admin_seo_test()

if __name__ == "__main__":
    main()