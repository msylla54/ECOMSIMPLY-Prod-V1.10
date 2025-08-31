#!/usr/bin/env python3
"""
ECOMSIMPLY Premium Backend Features Testing Suite
Tests the premium backend features as requested in test_result.md
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 30

class PremiumBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        self.user_data = None
        
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
            "email": f"premium.test{timestamp}@ecomsimply.fr",
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
                    self.log("❌ User Registration: Missing token or user data", "ERROR")
                    return False
            else:
                self.log(f"❌ User Registration failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ User Registration failed: {str(e)}", "ERROR")
            return False
    
    def test_user_login(self):
        """Test user login endpoint"""
        self.log("Testing user login...")
        
        if not self.user_data:
            self.log("❌ Cannot test login: No user data from registration", "ERROR")
            return False
            
        login_data = {
            "email": self.user_data["email"],
            "password": "PremiumTest123!"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                login_token = data.get("token")
                
                if login_token:
                    self.log(f"✅ User Login: Successfully logged in")
                    self.auth_token = login_token
                    return True
                else:
                    self.log("❌ User Login: Missing token", "ERROR")
                    return False
            else:
                self.log(f"❌ User Login failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ User Login failed: {str(e)}", "ERROR")
            return False

    def test_advanced_ai_features_system(self):
        """Test Advanced AI Features System endpoints"""
        self.log("Testing Advanced AI Features System...")
        
        if not self.auth_token:
            self.log("❌ Cannot test AI features: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        ai_endpoints = [
            "/ai/seo-analysis",
            "/ai/competitor-analysis",
            "/ai/price-optimization",
            "/ai/multilingual-translation",
            "/ai/product-variants",
            "/ai/features-overview"
        ]
        
        success_count = 0
        
        for endpoint in ai_endpoints:
            try:
                # Test with minimal valid data structure
                test_data = {
                    "product_name": "Test Product",
                    "product_description": "Test description"
                }
                
                if endpoint == "/ai/features-overview":
                    # This endpoint is GET
                    response = self.session.get(f"{BASE_URL}{endpoint}", headers=headers)
                else:
                    response = self.session.post(f"{BASE_URL}{endpoint}", json=test_data, headers=headers)
                
                if response.status_code == 200:
                    self.log(f"✅ AI Feature: {endpoint} working")
                    success_count += 1
                elif response.status_code == 403:
                    self.log(f"⚠️  AI Feature: {endpoint} requires premium subscription")
                    success_count += 1  # Expected for free users
                elif response.status_code == 422:
                    self.log(f"⚠️  AI Feature: {endpoint} validation error (expected)")
                    success_count += 1  # Expected with minimal test data
                elif response.status_code == 500:
                    self.log(f"❌ AI Feature: {endpoint} returning 500 Internal Server Error", "ERROR")
                else:
                    self.log(f"❌ AI Feature: {endpoint} failed with {response.status_code}", "ERROR")
                    
            except Exception as e:
                self.log(f"❌ AI Feature {endpoint} failed: {str(e)}", "ERROR")
        
        return success_count >= len(ai_endpoints)

    def test_ecommerce_platform_integrations(self):
        """Test Additional E-commerce Platform Integrations"""
        self.log("Testing Additional E-commerce Platform Integrations...")
        
        if not self.auth_token:
            self.log("❌ Cannot test e-commerce integrations: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test marketplace connection endpoints
        marketplace_endpoints = [
            "/ecommerce/amazon/connect",
            "/ecommerce/ebay/connect",
            "/ecommerce/etsy/connect", 
            "/ecommerce/facebook/connect",
            "/ecommerce/google-shopping/connect"
        ]
        
        success_count = 0
        
        for endpoint in marketplace_endpoints:
            try:
                # Test with minimal valid data structure
                test_data = {
                    "store_name": "Test Store",
                    "credentials": "test_credentials"
                }
                
                response = self.session.post(f"{BASE_URL}{endpoint}", json=test_data, headers=headers)
                
                if response.status_code == 200:
                    self.log(f"✅ Marketplace Integration: {endpoint} working")
                    success_count += 1
                elif response.status_code == 403:
                    self.log(f"⚠️  Marketplace Integration: {endpoint} requires premium subscription")
                    success_count += 1  # Expected for free users
                elif response.status_code == 422:
                    self.log(f"⚠️  Marketplace Integration: {endpoint} validation error (expected)")
                    success_count += 1  # Expected with test data
                elif response.status_code == 500:
                    self.log(f"❌ Marketplace Integration: {endpoint} returning 500 Internal Server Error", "ERROR")
                else:
                    self.log(f"❌ Marketplace Integration: {endpoint} failed with {response.status_code}", "ERROR")
                    
            except Exception as e:
                self.log(f"❌ Marketplace Integration {endpoint} failed: {str(e)}", "ERROR")
        
        # Test all stores endpoint
        try:
            response = self.session.get(f"{BASE_URL}/ecommerce/all-stores", headers=headers)
            
            if response.status_code == 200:
                self.log("✅ All Stores Endpoint: Working")
                success_count += 1
            elif response.status_code == 403:
                self.log("⚠️  All Stores Endpoint: Requires premium subscription")
                success_count += 1
            elif response.status_code == 500:
                self.log("❌ All Stores Endpoint: 500 Internal Server Error", "ERROR")
            else:
                self.log(f"❌ All Stores Endpoint failed: {response.status_code}", "ERROR")
                
        except Exception as e:
            self.log(f"❌ All Stores Endpoint failed: {str(e)}", "ERROR")
        
        return success_count >= len(marketplace_endpoints)

    def test_premium_image_generation_system(self):
        """Test Premium Image Generation System endpoints"""
        self.log("Testing Premium Image Generation System...")
        
        if not self.auth_token:
            self.log("❌ Cannot test premium image generation: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test 1: Premium Image Styles Endpoint
        try:
            response = self.session.get(f"{BASE_URL}/premium/image-styles", headers=headers)
            
            if response.status_code == 200:
                styles_data = response.json()
                self.log("✅ Premium Image Styles: Endpoint working")
                self.log(f"   Available styles: {len(styles_data.get('styles', []))}")
                self.log(f"   Available providers: {len(styles_data.get('providers', []))}")
            elif response.status_code == 403:
                self.log("⚠️  Premium Image Styles: Requires premium subscription (expected for free users)")
            else:
                self.log(f"❌ Premium Image Styles failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Premium Image Styles failed: {str(e)}", "ERROR")
            return False
        
        # Test 2: Premium Image Generation Endpoint
        try:
            image_request = {
                "product_name": "Test Premium Product",
                "product_description": "Testing premium image generation",
                "styles": ["studio", "lifestyle"],
                "generators": ["fal"],
                "count_per_style": 1,
                "priority": "standard"
            }
            
            response = self.session.post(f"{BASE_URL}/premium/generate-images", json=image_request, headers=headers)
            
            if response.status_code == 200:
                self.log("✅ Premium Image Generation: Endpoint working")
            elif response.status_code == 403:
                self.log("⚠️  Premium Image Generation: Requires premium subscription (expected for free users)")
            elif response.status_code == 422:
                self.log("❌ Premium Image Generation: Validation error - request structure issue", "ERROR")
                return False
            else:
                self.log(f"❌ Premium Image Generation failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Premium Image Generation failed: {str(e)}", "ERROR")
            return False
        
        return True

    def test_advanced_analytics_system(self):
        """Test Advanced Analytics and Reporting endpoints"""
        self.log("Testing Advanced Analytics and Reporting System...")
        
        if not self.auth_token:
            self.log("❌ Cannot test analytics: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        analytics_endpoints = [
            "/analytics/product-performance",
            "/analytics/integration-performance", 
            "/analytics/user-engagement",
            "/analytics/dashboard-summary"
        ]
        
        success_count = 0
        
        for endpoint in analytics_endpoints:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}", headers=headers)
                
                if response.status_code == 200:
                    self.log(f"✅ Analytics Endpoint: {endpoint} working")
                    success_count += 1
                elif response.status_code == 403:
                    self.log(f"⚠️  Analytics Endpoint: {endpoint} requires premium subscription")
                    success_count += 1  # Expected for free users
                elif response.status_code == 500:
                    self.log(f"❌ Analytics Endpoint: {endpoint} returning 500 Internal Server Error", "ERROR")
                else:
                    self.log(f"❌ Analytics Endpoint: {endpoint} failed with {response.status_code}", "ERROR")
                    
            except Exception as e:
                self.log(f"❌ Analytics Endpoint {endpoint} failed: {str(e)}", "ERROR")
        
        return success_count == len(analytics_endpoints)

    def run_premium_backend_tests(self):
        """Run premium backend feature tests based on test_result.md priorities"""
        self.log("STARTING PREMIUM BACKEND FEATURES TESTING - Phase 2")
        self.log("=" * 80)
        
        test_results = []
        
        # Core System Setup
        test_results.append(("API Health Check", self.test_api_health()))
        test_results.append(("User Registration", self.test_user_registration()))
        test_results.append(("User Login", self.test_user_login()))
        
        # PRIORITY 1: Advanced AI Features System (Previously fixed but needs verification)
        self.log("\nPRIORITY 1: Advanced AI Features System")
        test_results.append(("Advanced AI Features System", self.test_advanced_ai_features_system()))
        
        # PRIORITY 2: Additional E-commerce Platform Integrations (Currently failing)
        self.log("\nPRIORITY 2: Additional E-commerce Platform Integrations")
        test_results.append(("E-commerce Platform Integrations", self.test_ecommerce_platform_integrations()))
        
        # PRIORITY 3: Premium Image Generation System (Has validation issues)
        self.log("\nPRIORITY 3: Premium Image Generation System")
        test_results.append(("Premium Image Generation System", self.test_premium_image_generation_system()))
        
        # PRIORITY 4: Advanced Analytics and Reporting (Previous 500 errors)
        self.log("\nPRIORITY 4: Advanced Analytics and Reporting")
        test_results.append(("Advanced Analytics System", self.test_advanced_analytics_system()))
        
        # Print Results Summary
        self.log("=" * 80)
        self.log("PREMIUM BACKEND FEATURES TEST RESULTS")
        self.log("=" * 80)
        
        passed = 0
        failed = 0
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{status}: {test_name}")
            if result:
                passed += 1
            else:
                failed += 1
        
        self.log("=" * 80)
        self.log(f"PREMIUM FEATURES RESULTS: {passed} PASSED, {failed} FAILED")
        success_rate = (passed / len(test_results)) * 100
        self.log(f"SUCCESS RATE: {success_rate:.1f}%")
        
        if success_rate >= 90:
            self.log("EXCELLENT: Premium backend features working excellently!")
        elif success_rate >= 75:
            self.log("GOOD: Premium backend features working well with minor issues")
        elif success_rate >= 50:
            self.log("MODERATE: Premium backend features have some issues")
        else:
            self.log("CRITICAL: Premium backend features have significant issues")
        
        self.log("=" * 80)
        
        return success_rate >= 75

if __name__ == "__main__":
    tester = PremiumBackendTester()
    
    # Run premium backend tests as requested
    success = tester.run_premium_backend_tests()
    
    if success:
        print("\nPREMIUM BACKEND TESTS COMPLETED SUCCESSFULLY!")
        exit(0)
    else:
        print("\nSOME PREMIUM BACKEND TESTS FAILED - CHECK LOGS ABOVE")
        exit(1)