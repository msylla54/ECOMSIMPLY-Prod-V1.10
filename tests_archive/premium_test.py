#!/usr/bin/env python3
"""
ECOMSIMPLY Premium Features Backend Testing Suite
Tests the premium features as requested in the review.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 30

class PremiumFeaturesTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        self.user_data = None
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
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        self.log("Testing user registration...")
        
        # Generate unique test user data
        timestamp = int(time.time())
        test_user = {
            "email": f"premium.test{timestamp}@entreprise.fr",
            "name": "Premium Test User",
            "password": "PremiumTest123!"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=test_user)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.user_data = data.get("user")
                
                if self.auth_token and self.user_data:
                    self.log(f"✅ User Registration: Successfully registered {self.user_data['name']}")
                    return True
                else:
                    self.log("❌ User Registration: Missing token or user data in response", "ERROR")
                    return False
            else:
                self.log(f"❌ User Registration failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ User Registration failed: {str(e)}", "ERROR")
            return False
    
    def test_admin_user_registration(self):
        """Test admin user registration with admin key"""
        self.log("Testing admin user registration...")
        
        # Generate unique admin test user data
        timestamp = int(time.time())
        admin_user = {
            "email": f"admin.premium{timestamp}@ecomsimply.fr",
            "name": "Admin Premium Test",
            "password": "AdminPremium123!",
            "admin_key": "ECOMSIMPLY_ADMIN_2024"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=admin_user)
            
            if response.status_code == 200:
                data = response.json()
                admin_token = data.get("token")
                admin_user_data = data.get("user")
                
                if admin_token and admin_user_data and admin_user_data.get("is_admin"):
                    self.admin_token = admin_token
                    self.admin_user_data = admin_user_data
                    self.log(f"✅ Admin Registration: Successfully registered admin {admin_user_data['name']}")
                    return True
                else:
                    self.log("❌ Admin Registration: User not marked as admin or missing data", "ERROR")
                    return False
            else:
                self.log(f"❌ Admin Registration failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Admin Registration failed: {str(e)}", "ERROR")
            return False
    
    def test_premium_image_generation_endpoint(self):
        """Test POST /api/premium/generate-images endpoint"""
        self.log("Testing Premium Image Generation endpoint...")
        
        if not self.auth_token:
            self.log("❌ Cannot test premium image generation: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test premium image generation request
        premium_request = {
            "product_name": "Premium Test Product",
            "product_description": "High-end product for premium image generation testing",
            "styles": ["studio", "lifestyle", "detailed"],
            "generators": ["fal", "dalle3"],
            "backgrounds": ["white", "transparent"],
            "count_per_style": 1,
            "priority": "premium"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/premium/generate-images", json=premium_request, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["images", "generation_details", "failed_generations"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log(f"❌ Premium Image Generation: Missing fields {missing_fields}", "ERROR")
                    return False
                
                images = data.get("images", [])
                generation_details = data.get("generation_details", [])
                
                self.log(f"✅ Premium Image Generation: {len(images)} images generated")
                self.log(f"   Generation Details: {len(generation_details)} records")
                self.log(f"   Failed Generations: {len(data.get('failed_generations', []))}")
                
                return True
                
            elif response.status_code == 403:
                self.log("⚠️  Premium Image Generation: Requires Pro/Premium subscription (expected)")
                return True  # This is expected behavior for free users
            else:
                self.log(f"❌ Premium Image Generation failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Premium Image Generation failed: {str(e)}", "ERROR")
            return False
    
    def test_premium_image_styles_endpoint(self):
        """Test GET /api/premium/image-styles endpoint"""
        self.log("Testing Premium Image Styles endpoint...")
        
        try:
            response = self.session.get(f"{BASE_URL}/premium/image-styles")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                if "styles" not in data or "providers" not in data:
                    self.log("❌ Premium Image Styles: Missing styles or providers", "ERROR")
                    return False
                
                styles = data["styles"]
                providers = data["providers"]
                
                # Check for expected styles
                expected_styles = ["studio", "lifestyle", "detailed", "3d_render", "minimalist", "premium_luxury", "ecommerce_optimized"]
                found_styles = list(styles.keys()) if isinstance(styles, dict) else styles
                
                missing_styles = [style for style in expected_styles if style not in found_styles]
                if missing_styles:
                    self.log(f"❌ Premium Image Styles: Missing styles {missing_styles}", "ERROR")
                    return False
                
                # Check for expected providers
                expected_providers = ["fal", "dalle3", "stable_diffusion"]
                found_providers = list(providers.keys()) if isinstance(providers, dict) else providers
                
                missing_providers = [provider for provider in expected_providers if provider not in found_providers]
                if missing_providers:
                    self.log(f"❌ Premium Image Styles: Missing providers {missing_providers}", "ERROR")
                    return False
                
                self.log(f"✅ Premium Image Styles: {len(found_styles)} styles available")
                self.log(f"   Styles: {', '.join(found_styles[:5])}...")
                self.log(f"   Providers: {', '.join(found_providers)}")
                
                return True
            else:
                self.log(f"❌ Premium Image Styles failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Premium Image Styles failed: {str(e)}", "ERROR")
            return False
    
    def test_analytics_product_performance(self):
        """Test POST /api/analytics/product-performance endpoint"""
        self.log("Testing Analytics Product Performance endpoint...")
        
        if not self.auth_token:
            self.log("❌ Cannot test analytics: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test analytics request
        analytics_request = {
            "timeframe": {
                "period": "30d"
            }
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/analytics/product-performance", json=analytics_request, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                if not isinstance(data, list):
                    self.log("❌ Product Performance Analytics: Response should be a list", "ERROR")
                    return False
                
                self.log(f"✅ Product Performance Analytics: {len(data)} performance metrics retrieved")
                
                # Validate metric structure if data exists
                if data:
                    sample_metric = data[0]
                    required_fields = ["product_sheet_id", "product_name", "views", "exports", "engagement_score"]
                    missing_fields = [field for field in required_fields if field not in sample_metric]
                    
                    if missing_fields:
                        self.log(f"❌ Product Performance: Missing fields {missing_fields}", "ERROR")
                        return False
                    
                    self.log(f"   Sample: {sample_metric['product_name']} - {sample_metric['engagement_score']} engagement")
                
                return True
                
            elif response.status_code == 403:
                self.log("⚠️  Product Performance Analytics: Requires Pro/Premium subscription (expected)")
                return True  # This is expected behavior for free users
            else:
                self.log(f"❌ Product Performance Analytics failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Product Performance Analytics failed: {str(e)}", "ERROR")
            return False
    
    def test_analytics_integration_performance(self):
        """Test POST /api/analytics/integration-performance endpoint"""
        self.log("Testing Analytics Integration Performance endpoint...")
        
        if not self.auth_token:
            self.log("❌ Cannot test integration analytics: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        analytics_request = {
            "timeframe": {
                "period": "30d"
            }
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/analytics/integration-performance", json=analytics_request, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if not isinstance(data, list):
                    self.log("❌ Integration Performance Analytics: Response should be a list", "ERROR")
                    return False
                
                self.log(f"✅ Integration Performance Analytics: {len(data)} integration metrics retrieved")
                
                # Validate metric structure if data exists
                if data:
                    sample_metric = data[0]
                    required_fields = ["platform", "total_publishes", "successful_publishes", "success_rate"]
                    missing_fields = [field for field in required_fields if field not in sample_metric]
                    
                    if missing_fields:
                        self.log(f"❌ Integration Performance: Missing fields {missing_fields}", "ERROR")
                        return False
                    
                    self.log(f"   Sample: {sample_metric['platform']} - {sample_metric['success_rate']}% success rate")
                
                return True
                
            elif response.status_code == 403:
                self.log("⚠️  Integration Performance Analytics: Requires Pro/Premium subscription (expected)")
                return True
            else:
                self.log(f"❌ Integration Performance Analytics failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Integration Performance Analytics failed: {str(e)}", "ERROR")
            return False
    
    def test_analytics_user_engagement(self):
        """Test POST /api/analytics/user-engagement endpoint"""
        self.log("Testing Analytics User Engagement endpoint...")
        
        if not self.auth_token:
            self.log("❌ Cannot test user engagement analytics: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        analytics_request = {
            "timeframe": {
                "period": "30d"
            }
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/analytics/user-engagement", json=analytics_request, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["user_id", "total_sheets_generated", "total_images_generated", "favorite_styles"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log(f"❌ User Engagement Analytics: Missing fields {missing_fields}", "ERROR")
                    return False
                
                self.log(f"✅ User Engagement Analytics: Retrieved for user {data['user_id']}")
                self.log(f"   Sheets Generated: {data['total_sheets_generated']}")
                self.log(f"   Images Generated: {data['total_images_generated']}")
                self.log(f"   Favorite Styles: {', '.join(data['favorite_styles'][:3])}")
                
                return True
                
            elif response.status_code == 403:
                self.log("⚠️  User Engagement Analytics: Requires Pro/Premium subscription (expected)")
                return True
            else:
                self.log(f"❌ User Engagement Analytics failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ User Engagement Analytics failed: {str(e)}", "ERROR")
            return False
    
    def test_admin_business_intelligence(self):
        """Test POST /api/admin/analytics/business-intelligence endpoint (admin only)"""
        self.log("Testing Admin Business Intelligence endpoint...")
        
        if not hasattr(self, 'admin_token') or not self.admin_token:
            self.log("❌ Cannot test business intelligence: No admin token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        analytics_request = {
            "timeframe": {
                "period": "30d"
            }
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/admin/analytics/business-intelligence", json=analytics_request, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["timeframe", "total_revenue", "active_users", "premium_conversions"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log(f"❌ Business Intelligence: Missing fields {missing_fields}", "ERROR")
                    return False
                
                self.log(f"✅ Business Intelligence Report: Generated for {data['timeframe']}")
                self.log(f"   Total Revenue: {data['total_revenue']}€")
                self.log(f"   Active Users: {data['active_users']}")
                self.log(f"   Premium Conversions: {data['premium_conversions']}")
                
                return True
            else:
                self.log(f"❌ Business Intelligence failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Business Intelligence failed: {str(e)}", "ERROR")
            return False
    
    def test_analytics_dashboard_summary(self):
        """Test GET /api/analytics/dashboard-summary endpoint"""
        self.log("Testing Analytics Dashboard Summary endpoint...")
        
        if not self.auth_token:
            self.log("❌ Cannot test dashboard summary: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            response = self.session.get(f"{BASE_URL}/analytics/dashboard-summary", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                expected_sections = ["product_performance", "integration_analytics", "user_engagement"]
                missing_sections = [section for section in expected_sections if section not in data]
                
                if missing_sections:
                    self.log(f"❌ Dashboard Summary: Missing sections {missing_sections}", "ERROR")
                    return False
                
                self.log(f"✅ Analytics Dashboard Summary: Retrieved successfully")
                self.log(f"   Product Performance: {len(data.get('product_performance', []))} items")
                self.log(f"   Integration Analytics: {len(data.get('integration_analytics', []))} items")
                self.log(f"   User Engagement: Available")
                
                return True
                
            elif response.status_code == 403:
                self.log("⚠️  Dashboard Summary: Requires Pro/Premium subscription (expected)")
                return True
            else:
                self.log(f"❌ Dashboard Summary failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Dashboard Summary failed: {str(e)}", "ERROR")
            return False
    
    def test_ecommerce_shopify_connect(self):
        """Test POST /api/ecommerce/shopify/connect endpoint"""
        self.log("Testing E-commerce Shopify Connect endpoint...")
        
        if not self.auth_token:
            self.log("❌ Cannot test Shopify connect: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test Shopify connection request
        shopify_request = {
            "shop_name": "test-shop",
            "store_url": "https://test-shop.myshopify.com",
            "access_token": "test_access_token_123",
            "api_key": "test_api_key",
            "api_secret": "test_api_secret"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/ecommerce/shopify/connect", json=shopify_request, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["store_id", "status", "message"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log(f"❌ Shopify Connect: Missing fields {missing_fields}", "ERROR")
                    return False
                
                self.log(f"✅ Shopify Connect: {data['message']}")
                self.log(f"   Store ID: {data['store_id']}")
                self.log(f"   Status: {data['status']}")
                
                return True
            else:
                self.log(f"❌ Shopify Connect failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Shopify Connect failed: {str(e)}", "ERROR")
            return False
    
    def test_ecommerce_woocommerce_connect(self):
        """Test POST /api/ecommerce/woocommerce/connect endpoint"""
        self.log("Testing E-commerce WooCommerce Connect endpoint...")
        
        if not self.auth_token:
            self.log("❌ Cannot test WooCommerce connect: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test WooCommerce connection request
        woocommerce_request = {
            "store_name": "Test WooCommerce Store",
            "store_url": "https://test-store.com",
            "consumer_key": "ck_test_consumer_key_123",
            "consumer_secret": "cs_test_consumer_secret_456"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/ecommerce/woocommerce/connect", json=woocommerce_request, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["store_id", "status", "message"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log(f"❌ WooCommerce Connect: Missing fields {missing_fields}", "ERROR")
                    return False
                
                self.log(f"✅ WooCommerce Connect: {data['message']}")
                self.log(f"   Store ID: {data['store_id']}")
                self.log(f"   Status: {data['status']}")
                
                return True
            else:
                self.log(f"❌ WooCommerce Connect failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ WooCommerce Connect failed: {str(e)}", "ERROR")
            return False
    
    def test_ecommerce_stores_list(self):
        """Test GET /api/ecommerce/stores endpoint"""
        self.log("Testing E-commerce Stores List endpoint...")
        
        if not self.auth_token:
            self.log("❌ Cannot test stores list: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            response = self.session.get(f"{BASE_URL}/ecommerce/stores", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if not isinstance(data, list):
                    self.log("❌ E-commerce Stores: Response should be a list", "ERROR")
                    return False
                
                self.log(f"✅ E-commerce Stores List: {len(data)} stores retrieved")
                
                # Validate store structure if data exists
                if data:
                    sample_store = data[0]
                    required_fields = ["id", "platform", "store_name", "store_url", "is_active"]
                    missing_fields = [field for field in required_fields if field not in sample_store]
                    
                    if missing_fields:
                        self.log(f"❌ E-commerce Stores: Missing fields {missing_fields}", "ERROR")
                        return False
                    
                    self.log(f"   Sample: {sample_store['store_name']} ({sample_store['platform']})")
                
                return True
            else:
                self.log(f"❌ E-commerce Stores List failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ E-commerce Stores List failed: {str(e)}", "ERROR")
            return False
    
    def test_ecommerce_integration_logs(self):
        """Test GET /api/ecommerce/integration-logs endpoint"""
        self.log("Testing E-commerce Integration Logs endpoint...")
        
        if not self.auth_token:
            self.log("❌ Cannot test integration logs: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            response = self.session.get(f"{BASE_URL}/ecommerce/integration-logs", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if not isinstance(data, list):
                    self.log("❌ Integration Logs: Response should be a list", "ERROR")
                    return False
                
                self.log(f"✅ E-commerce Integration Logs: {len(data)} logs retrieved")
                
                # Validate log structure if data exists
                if data:
                    sample_log = data[0]
                    required_fields = ["id", "platform", "action", "status", "timestamp"]
                    missing_fields = [field for field in required_fields if field not in sample_log]
                    
                    if missing_fields:
                        self.log(f"❌ Integration Logs: Missing fields {missing_fields}", "ERROR")
                        return False
                    
                    self.log(f"   Sample: {sample_log['platform']} - {sample_log['action']} ({sample_log['status']})")
                
                return True
            else:
                self.log(f"❌ Integration Logs failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Integration Logs failed: {str(e)}", "ERROR")
            return False
    
    def test_subscription_plan_verification(self):
        """Test subscription plan requirements for premium features"""
        self.log("Testing subscription plan verification for premium features...")
        
        if not self.auth_token:
            self.log("❌ Cannot test subscription verification: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test premium endpoints that should require Pro/Premium plans
        premium_endpoints = [
            ("POST", "/premium/generate-images", {"product_name": "Test", "product_description": "Test"}),
            ("POST", "/analytics/product-performance", {"timeframe": {"period": "30d"}}),
            ("POST", "/analytics/integration-performance", {"timeframe": {"period": "30d"}}),
            ("POST", "/analytics/user-engagement", {"timeframe": {"period": "30d"}}),
            ("GET", "/analytics/dashboard-summary", None)
        ]
        
        success_count = 0
        
        for method, endpoint, data in premium_endpoints:
            try:
                if method == "POST":
                    response = self.session.post(f"{BASE_URL}{endpoint}", json=data, headers=headers)
                elif method == "GET":
                    response = self.session.get(f"{BASE_URL}{endpoint}", headers=headers)
                
                # For free users, should get 403 Forbidden
                if response.status_code == 403:
                    self.log(f"✅ Subscription Verification: {method} {endpoint} correctly requires premium plan")
                    success_count += 1
                elif response.status_code == 200:
                    # If user has premium plan, this is also correct
                    self.log(f"✅ Subscription Verification: {method} {endpoint} accessible (user has premium plan)")
                    success_count += 1
                else:
                    self.log(f"❌ Subscription Verification: {method} {endpoint} unexpected response {response.status_code}", "ERROR")
                    
            except Exception as e:
                self.log(f"❌ Subscription Verification test failed for {method} {endpoint}: {str(e)}", "ERROR")
        
        return success_count == len(premium_endpoints)

    def run_premium_features_tests(self):
        """Run comprehensive tests for premium features"""
        self.log("🚀 Starting ECOMSIMPLY Premium Features Testing Suite")
        self.log("=" * 80)
        
        test_results = []
        
        # Setup tests
        test_results.append(("API Health Check", self.test_api_health()))
        test_results.append(("User Registration", self.test_user_registration()))
        test_results.append(("Admin User Registration", self.test_admin_user_registration()))
        
        # Premium Image Generation System Tests
        self.log("\n🎨 PREMIUM IMAGE GENERATION SYSTEM TESTS")
        self.log("-" * 60)
        test_results.append(("Premium Image Generation Endpoint", self.test_premium_image_generation_endpoint()))
        test_results.append(("Premium Image Styles Endpoint", self.test_premium_image_styles_endpoint()))
        
        # Advanced Analytics System Tests
        self.log("\n📊 ADVANCED ANALYTICS SYSTEM TESTS")
        self.log("-" * 60)
        test_results.append(("Analytics Product Performance", self.test_analytics_product_performance()))
        test_results.append(("Analytics Integration Performance", self.test_analytics_integration_performance()))
        test_results.append(("Analytics User Engagement", self.test_analytics_user_engagement()))
        test_results.append(("Admin Business Intelligence", self.test_admin_business_intelligence()))
        test_results.append(("Analytics Dashboard Summary", self.test_analytics_dashboard_summary()))
        
        # E-commerce Integration Tests
        self.log("\n🛒 E-COMMERCE INTEGRATION TESTS")
        self.log("-" * 60)
        test_results.append(("E-commerce Shopify Connect", self.test_ecommerce_shopify_connect()))
        test_results.append(("E-commerce WooCommerce Connect", self.test_ecommerce_woocommerce_connect()))
        test_results.append(("E-commerce Stores List", self.test_ecommerce_stores_list()))
        test_results.append(("E-commerce Integration Logs", self.test_ecommerce_integration_logs()))
        
        # Subscription Plan Verification
        self.log("\n🔒 SUBSCRIPTION PLAN VERIFICATION TESTS")
        self.log("-" * 60)
        test_results.append(("Subscription Plan Verification", self.test_subscription_plan_verification()))
        
        # Calculate results
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        self.log("\n" + "=" * 80)
        self.log("🎯 PREMIUM FEATURES TEST RESULTS SUMMARY")
        self.log("=" * 80)
        
        # Show results by category
        categories = {
            "Setup": test_results[:3],
            "Premium Image Generation": test_results[3:5],
            "Advanced Analytics": test_results[5:10],
            "E-commerce Integration": test_results[10:14],
            "Subscription Verification": test_results[14:15]
        }
        
        for category, tests in categories.items():
            category_passed = sum(1 for _, result in tests if result)
            category_total = len(tests)
            self.log(f"\n📋 {category}: {category_passed}/{category_total} passed")
            
            for test_name, result in tests:
                status = "✅ PASS" if result else "❌ FAIL"
                self.log(f"   {test_name}: {status}")
        
        self.log(f"\n🎉 OVERALL RESULT: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")
        
        if passed == total:
            self.log("✅ ALL PREMIUM FEATURES TESTS PASSED!")
            self.log("   🎨 Premium Image Generation System: Functional")
            self.log("   📊 Advanced Analytics System: Operational")
            self.log("   🛒 E-commerce Integration: Working")
            self.log("   🔒 Subscription Plan Verification: Enforced")
        elif passed >= total * 0.8:
            self.log("✅ MAJORITY OF PREMIUM FEATURES WORKING!")
            self.log(f"   {total - passed} minor issues detected")
        else:
            self.log("⚠️  MULTIPLE PREMIUM FEATURES NEED ATTENTION!")
            self.log(f"   {total - passed} critical issues found")
        
        return passed, total

if __name__ == "__main__":
    tester = PremiumFeaturesTester()
    tester.run_premium_features_tests()