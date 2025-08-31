#!/usr/bin/env python3
"""
ECOMSIMPLY Focused Backend Testing for Review Request
Tests specific areas mentioned in the review request with detailed analysis
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 30

class FocusedBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        self.admin_token = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def setup_authentication(self):
        """Setup authentication tokens for testing"""
        self.log("🔧 Setting up authentication...")
        
        # Try to login with existing admin user
        admin_login = {
            "email": "msylla54@yahoo.fr",
            "password": "NewPassword123"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json=admin_login)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("token")
                self.auth_token = self.admin_token  # Use admin token for regular tests too
                self.log("✅ Admin authentication successful")
                return True
            else:
                self.log(f"❌ Admin authentication failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Authentication setup failed: {str(e)}", "ERROR")
            return False
    
    def test_advanced_ai_endpoints_detailed(self):
        """Test Advanced AI endpoints with detailed analysis"""
        self.log("🔧 TESTING ADVANCED AI ENDPOINTS (DETAILED)...")
        
        if not self.auth_token:
            self.log("❌ No auth token available", "ERROR")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test Price Optimization (mentioned as working in review)
        self.log("Testing Price Optimization endpoint...")
        price_request = {
            "product_name": "iPhone 16",
            "current_price": 1400,
            "product_cost": 300,
            "competitive_strategy": "premium"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/ai/price-optimization", json=price_request, headers=headers)
            self.log(f"Price Optimization Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Price Optimization working: {json.dumps(data, indent=2)[:200]}...")
            elif response.status_code == 403:
                self.log("⚠️  Price Optimization: Requires premium subscription")
            else:
                self.log(f"❌ Price Optimization failed: {response.text[:200]}")
        except Exception as e:
            self.log(f"❌ Price Optimization error: {str(e)}", "ERROR")
        
        # Test Multilingual Translation (mentioned as working in review)
        self.log("Testing Multilingual Translation endpoint...")
        translation_request = {
            "text": "Bonjour le monde",
            "source_language": "fr",
            "target_languages": ["en"]
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/ai/multilingual-translation", json=translation_request, headers=headers)
            self.log(f"Translation Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Translation working: {json.dumps(data, indent=2)[:200]}...")
            elif response.status_code == 403:
                self.log("⚠️  Translation: Requires premium subscription")
            else:
                self.log(f"❌ Translation failed: {response.text[:200]}")
        except Exception as e:
            self.log(f"❌ Translation error: {str(e)}", "ERROR")
        
        # Test Product Variants (mentioned as working in review)
        self.log("Testing Product Variants endpoint...")
        variants_request = {
            "base_product": "iPhone 16",
            "base_description": "Smartphone premium",
            "number_of_variants": 3,
            "variant_types": ["color", "size"]
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/ai/product-variants", json=variants_request, headers=headers)
            self.log(f"Product Variants Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Product Variants working: {json.dumps(data, indent=2)[:200]}...")
            elif response.status_code == 403:
                self.log("⚠️  Product Variants: Requires premium subscription")
            else:
                self.log(f"❌ Product Variants failed: {response.text[:200]}")
        except Exception as e:
            self.log(f"❌ Product Variants error: {str(e)}", "ERROR")
        
        # Test SEO Analysis
        self.log("Testing SEO Analysis endpoint...")
        seo_request = {
            "product_name": "iPhone 15 Pro",
            "product_description": "Smartphone premium Apple",
            "target_keywords": "iPhone, smartphone, Apple"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/ai/seo-analysis", json=seo_request, headers=headers)
            self.log(f"SEO Analysis Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ SEO Analysis working: {json.dumps(data, indent=2)[:200]}...")
            elif response.status_code == 403:
                self.log("⚠️  SEO Analysis: Requires premium subscription")
            else:
                self.log(f"❌ SEO Analysis failed: {response.text[:200]}")
        except Exception as e:
            self.log(f"❌ SEO Analysis error: {str(e)}", "ERROR")
        
        # Test Competitor Analysis
        self.log("Testing Competitor Analysis endpoint...")
        competitor_request = {
            "product_name": "iPhone 15 Pro",
            "category": "electronics",
            "analysis_depth": "standard"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/ai/competitor-analysis", json=competitor_request, headers=headers)
            self.log(f"Competitor Analysis Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Competitor Analysis working: {json.dumps(data, indent=2)[:200]}...")
            elif response.status_code == 403:
                self.log("⚠️  Competitor Analysis: Requires premium subscription")
            else:
                self.log(f"❌ Competitor Analysis failed: {response.text[:200]}")
        except Exception as e:
            self.log(f"❌ Competitor Analysis error: {str(e)}", "ERROR")
        
        return True
    
    def test_affiliate_system_detailed(self):
        """Test affiliate system APIs with detailed analysis"""
        self.log("🔧 TESTING AFFILIATE SYSTEM (DETAILED)...")
        
        admin_key = "ECOMSIMPLY_ADMIN_2024"
        
        # Test affiliate configuration
        self.log("Testing Affiliate Configuration endpoint...")
        try:
            response = self.session.get(f"{BASE_URL}/admin/affiliate-config?admin_key={admin_key}")
            self.log(f"Affiliate Config Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Affiliate Config working: {json.dumps(data, indent=2)[:300]}...")
            else:
                self.log(f"❌ Affiliate Config failed: {response.text[:200]}")
        except Exception as e:
            self.log(f"❌ Affiliate Config error: {str(e)}", "ERROR")
        
        # Test affiliate management
        self.log("Testing Affiliate Management endpoint...")
        try:
            response = self.session.get(f"{BASE_URL}/admin/affiliates?admin_key={admin_key}")
            self.log(f"Affiliate Management Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Affiliate Management working: Found {len(data)} affiliates")
                if len(data) > 0:
                    self.log(f"Sample affiliate: {json.dumps(data[0], indent=2)[:200]}...")
            else:
                self.log(f"❌ Affiliate Management failed: {response.text[:200]}")
        except Exception as e:
            self.log(f"❌ Affiliate Management error: {str(e)}", "ERROR")
        
        # Test affiliate registration
        self.log("Testing Affiliate Registration endpoint...")
        timestamp = int(time.time())
        affiliate_data = {
            "email": f"test.affiliate{timestamp}@example.com",
            "name": "Test Affiliate",
            "company": "Test Company",
            "website": "https://test.com",
            "motivation": "Testing the affiliate system"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/affiliate/register", json=affiliate_data)
            self.log(f"Affiliate Registration Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Affiliate Registration working: {json.dumps(data, indent=2)[:200]}...")
            else:
                self.log(f"❌ Affiliate Registration failed: {response.text[:200]}")
        except Exception as e:
            self.log(f"❌ Affiliate Registration error: {str(e)}", "ERROR")
        
        return True
    
    def test_admin_panel_detailed(self):
        """Test admin panel APIs with detailed analysis"""
        self.log("🔧 TESTING ADMIN PANEL APIs (DETAILED)...")
        
        if not self.admin_token:
            self.log("❌ No admin token available", "ERROR")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        admin_key = "ECOMSIMPLY_ADMIN_2024"
        
        # Test admin stats
        self.log("Testing Admin Statistics endpoint...")
        try:
            response = self.session.get(f"{BASE_URL}/admin/stats", headers=headers)
            self.log(f"Admin Stats Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Admin Stats working: {json.dumps(data, indent=2)[:300]}...")
            else:
                self.log(f"❌ Admin Stats failed: {response.text[:200]}")
        except Exception as e:
            self.log(f"❌ Admin Stats error: {str(e)}", "ERROR")
        
        # Test price management
        self.log("Testing Price Management endpoint...")
        try:
            response = self.session.get(f"{BASE_URL}/admin/plans-config?admin_key={admin_key}")
            self.log(f"Price Management Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Price Management working: {json.dumps(data, indent=2)[:300]}...")
            else:
                self.log(f"❌ Price Management failed: {response.text[:200]}")
        except Exception as e:
            self.log(f"❌ Price Management error: {str(e)}", "ERROR")
        
        # Test promotion management
        self.log("Testing Promotion Management endpoint...")
        try:
            response = self.session.get(f"{BASE_URL}/admin/promotions?admin_key={admin_key}")
            self.log(f"Promotion Management Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Promotion Management working: {json.dumps(data, indent=2)[:300]}...")
            else:
                self.log(f"❌ Promotion Management failed: {response.text[:200]}")
        except Exception as e:
            self.log(f"❌ Promotion Management error: {str(e)}", "ERROR")
        
        return True
    
    def test_database_objectid_handling(self):
        """Test MongoDB ObjectId serialization specifically"""
        self.log("🔧 TESTING MONGODB OBJECTID HANDLING...")
        
        admin_key = "ECOMSIMPLY_ADMIN_2024"
        
        # Test endpoints that should return MongoDB documents
        endpoints_to_test = [
            f"/admin/affiliates?admin_key={admin_key}",
            f"/admin/users?admin_key={admin_key}",
            f"/admin/activity-logs?admin_key={admin_key}"
        ]
        
        for endpoint in endpoints_to_test:
            self.log(f"Testing ObjectId serialization for: {endpoint}")
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                self.log(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        self.log(f"✅ ObjectId serialization working for {endpoint}")
                        if isinstance(data, list) and len(data) > 0:
                            self.log(f"Sample data structure: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")
                    except json.JSONDecodeError as e:
                        self.log(f"❌ JSON decode error for {endpoint}: {str(e)}", "ERROR")
                elif response.status_code == 403:
                    self.log(f"⚠️  Access denied for {endpoint} (expected for some endpoints)")
                else:
                    self.log(f"❌ Failed for {endpoint}: {response.text[:200]}")
                    
            except Exception as e:
                self.log(f"❌ Error testing {endpoint}: {str(e)}", "ERROR")
        
        return True
    
    def test_payment_integration(self):
        """Test Stripe payment integration"""
        self.log("🔧 TESTING PAYMENT INTEGRATION...")
        
        if not self.auth_token:
            self.log("❌ No auth token available", "ERROR")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test public pricing endpoint
        self.log("Testing Public Pricing endpoint...")
        try:
            response = self.session.get(f"{BASE_URL}/public/plans-pricing")
            self.log(f"Public Pricing Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Public Pricing working: {json.dumps(data, indent=2)[:300]}...")
            else:
                self.log(f"❌ Public Pricing failed: {response.text[:200]}")
        except Exception as e:
            self.log(f"❌ Public Pricing error: {str(e)}", "ERROR")
        
        # Test Stripe checkout creation
        self.log("Testing Stripe Checkout creation...")
        checkout_request = {
            "plan_type": "pro",
            "origin_url": "https://test.com"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/payments/checkout", json=checkout_request, headers=headers)
            self.log(f"Stripe Checkout Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Stripe Checkout working: {json.dumps(data, indent=2)[:300]}...")
            elif response.status_code == 503:
                self.log("⚠️  Stripe Checkout: Service unavailable (expected in test environment)")
            else:
                self.log(f"❌ Stripe Checkout failed: {response.text[:200]}")
        except Exception as e:
            self.log(f"❌ Stripe Checkout error: {str(e)}", "ERROR")
        
        return True
    
    def test_core_functionality_regression(self):
        """Test core functionality to ensure no regressions"""
        self.log("🔧 TESTING CORE FUNCTIONALITY (REGRESSION)...")
        
        if not self.auth_token:
            self.log("❌ No auth token available", "ERROR")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test product sheet generation
        self.log("Testing Product Sheet Generation...")
        sheet_request = {
            "product_name": "Test Product for Regression",
            "product_description": "Testing core functionality",
            "generate_image": True
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=sheet_request, headers=headers)
            self.log(f"Product Sheet Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Product Sheet Generation working")
                self.log(f"Generated title: {data.get('generated_title', 'N/A')}")
                self.log(f"Has image: {'Yes' if data.get('product_image_base64') or data.get('product_images_base64') else 'No'}")
            else:
                self.log(f"❌ Product Sheet Generation failed: {response.text[:200]}")
        except Exception as e:
            self.log(f"❌ Product Sheet Generation error: {str(e)}", "ERROR")
        
        # Test user sheets retrieval
        self.log("Testing User Sheets Retrieval...")
        try:
            response = self.session.get(f"{BASE_URL}/my-sheets", headers=headers)
            self.log(f"User Sheets Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ User Sheets Retrieval working: Found {len(data)} sheets")
            else:
                self.log(f"❌ User Sheets Retrieval failed: {response.text[:200]}")
        except Exception as e:
            self.log(f"❌ User Sheets Retrieval error: {str(e)}", "ERROR")
        
        # Test chatbot
        self.log("Testing Chatbot functionality...")
        chat_request = {"message": "Comment utiliser ECOMSIMPLY ?"}
        
        try:
            response = self.session.post(f"{BASE_URL}/chat", json=chat_request)
            self.log(f"Chatbot Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Chatbot working: {data.get('response', 'N/A')[:100]}...")
            else:
                self.log(f"❌ Chatbot failed: {response.text[:200]}")
        except Exception as e:
            self.log(f"❌ Chatbot error: {str(e)}", "ERROR")
        
        return True
    
    def run_focused_tests(self):
        """Run focused tests based on review request"""
        self.log("🚀 STARTING FOCUSED BACKEND TESTING FOR REVIEW REQUEST...")
        self.log("=" * 80)
        
        start_time = time.time()
        
        # Setup authentication
        if not self.setup_authentication():
            self.log("❌ Cannot proceed without authentication", "ERROR")
            return
        
        # Run focused tests
        self.log("\n" + "=" * 80)
        self.test_core_functionality_regression()
        
        self.log("\n" + "=" * 80)
        self.test_advanced_ai_endpoints_detailed()
        
        self.log("\n" + "=" * 80)
        self.test_admin_panel_detailed()
        
        self.log("\n" + "=" * 80)
        self.test_affiliate_system_detailed()
        
        self.log("\n" + "=" * 80)
        self.test_database_objectid_handling()
        
        self.log("\n" + "=" * 80)
        self.test_payment_integration()
        
        end_time = time.time()
        duration = end_time - start_time
        
        self.log("\n" + "=" * 80)
        self.log("🎯 FOCUSED BACKEND TESTING COMPLETED")
        self.log(f"⏱️  Total testing time: {duration:.2f} seconds")
        self.log("=" * 80)

if __name__ == "__main__":
    tester = FocusedBackendTester()
    tester.run_focused_tests()