#!/usr/bin/env python3
"""
Advanced AI Backend API Testing Suite
Tests the Advanced AI endpoints that are returning 500 errors:
- POST /api/ai/seo-analysis
- POST /api/ai/competitor-analysis  
- GET /api/seo/config
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 30

class AdvancedAITester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.admin_token = None
        self.admin_user_data = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_admin_login(self):
        """Login as admin user to test premium AI features"""
        self.log("Testing admin login for Advanced AI features...")
        
        # Use the admin credentials from the review request
        login_data = {
            "email": "msylla54@yahoo.fr",
            "password": "NewPassword123"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("token")
                self.admin_user_data = data.get("user")
                
                if self.admin_token and self.admin_user_data:
                    self.log(f"✅ Admin Login: Successfully logged in as {self.admin_user_data['name']}")
                    self.log(f"   User ID: {self.admin_user_data['id']}")
                    self.log(f"   Email: {self.admin_user_data['email']}")
                    self.log(f"   Subscription Plan: {self.admin_user_data.get('subscription_plan', 'N/A')}")
                    self.log(f"   Is Admin: {self.admin_user_data.get('is_admin', False)}")
                    return True
                else:
                    self.log("❌ Admin Login: Missing token or user data in response", "ERROR")
                    return False
            else:
                self.log(f"❌ Admin Login failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Admin Login failed: {str(e)}", "ERROR")
            return False
    
    def test_seo_analysis_endpoint(self):
        """Test POST /api/ai/seo-analysis endpoint with iPhone 15 Pro data"""
        self.log("Testing SEO Analysis endpoint...")
        
        if not self.admin_token:
            self.log("❌ Cannot test SEO analysis: No admin token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test data from review request
        seo_request = {
            "product_name": "iPhone 15 Pro",
            "product_description": "Smartphone haut de gamme avec processeur A17 Pro",
            "target_keywords": ["iPhone", "smartphone", "Apple"],
            "target_audience": "Consommateurs premium",
            "language": "fr"
        }
        
        try:
            self.log("   Sending SEO analysis request...")
            self.log(f"   Product: {seo_request['product_name']}")
            self.log(f"   Keywords: {seo_request['target_keywords']}")
            
            response = self.session.post(f"{BASE_URL}/ai/seo-analysis", json=seo_request, headers=headers)
            
            self.log(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                if "success" in data and "seo_analysis" in data:
                    seo_analysis = data["seo_analysis"]
                    
                    # Check required fields
                    required_fields = ["optimized_title", "meta_description", "seo_keywords", "content_score", "suggestions"]
                    missing_fields = [field for field in required_fields if field not in seo_analysis]
                    
                    if missing_fields:
                        self.log(f"❌ SEO Analysis: Missing fields {missing_fields}", "ERROR")
                        return False
                    
                    self.log("✅ SEO Analysis: Successfully completed!")
                    self.log(f"   Optimized Title: {seo_analysis['optimized_title']}")
                    self.log(f"   Meta Description: {seo_analysis['meta_description'][:100]}...")
                    self.log(f"   SEO Keywords: {seo_analysis['seo_keywords']}")
                    self.log(f"   Content Score: {seo_analysis['content_score']}")
                    self.log(f"   Suggestions Count: {len(seo_analysis['suggestions'])}")
                    return True
                else:
                    self.log(f"❌ SEO Analysis: Invalid response structure - {data}", "ERROR")
                    return False
                    
            elif response.status_code == 500:
                self.log("❌ SEO Analysis: 500 Internal Server Error - CRITICAL ISSUE!", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error Details: {error_data}", "ERROR")
                except:
                    self.log(f"   Raw Error: {response.text}", "ERROR")
                return False
            elif response.status_code == 403:
                self.log("❌ SEO Analysis: 403 Forbidden - Subscription access issue", "ERROR")
                return False
            else:
                self.log(f"❌ SEO Analysis failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ SEO Analysis failed: {str(e)}", "ERROR")
            return False
    
    def test_competitor_analysis_endpoint(self):
        """Test POST /api/ai/competitor-analysis endpoint with iPhone 15 Pro data"""
        self.log("Testing Competitor Analysis endpoint...")
        
        if not self.admin_token:
            self.log("❌ Cannot test competitor analysis: No admin token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test data from review request
        competitor_request = {
            "product_name": "iPhone 15 Pro",
            "category": "électronique",
            "analysis_depth": "standard",
            "language": "fr"
        }
        
        try:
            self.log("   Sending competitor analysis request...")
            self.log(f"   Product: {competitor_request['product_name']}")
            self.log(f"   Category: {competitor_request['category']}")
            self.log(f"   Analysis Depth: {competitor_request['analysis_depth']}")
            
            response = self.session.post(f"{BASE_URL}/ai/competitor-analysis", json=competitor_request, headers=headers)
            
            self.log(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                if "success" in data and "competitor_analysis" in data:
                    analysis = data["competitor_analysis"]
                    
                    # Check required fields
                    required_fields = ["competitors_found", "avg_price_range", "common_features", "market_position", "competitive_advantages"]
                    missing_fields = [field for field in required_fields if field not in analysis]
                    
                    if missing_fields:
                        self.log(f"❌ Competitor Analysis: Missing fields {missing_fields}", "ERROR")
                        return False
                    
                    self.log("✅ Competitor Analysis: Successfully completed!")
                    self.log(f"   Competitors Found: {analysis['competitors_found']}")
                    self.log(f"   Price Range: {analysis['avg_price_range']}")
                    self.log(f"   Market Position: {analysis['market_position']}")
                    self.log(f"   Common Features: {analysis['common_features']}")
                    self.log(f"   Competitive Advantages: {analysis['competitive_advantages']}")
                    return True
                else:
                    self.log(f"❌ Competitor Analysis: Invalid response structure - {data}", "ERROR")
                    return False
                    
            elif response.status_code == 500:
                self.log("❌ Competitor Analysis: 500 Internal Server Error - CRITICAL ISSUE!", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error Details: {error_data}", "ERROR")
                except:
                    self.log(f"   Raw Error: {response.text}", "ERROR")
                return False
            elif response.status_code == 403:
                self.log("❌ Competitor Analysis: 403 Forbidden - Subscription access issue", "ERROR")
                return False
            else:
                self.log(f"❌ Competitor Analysis failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Competitor Analysis failed: {str(e)}", "ERROR")
            return False
    
    def test_seo_config_endpoint(self):
        """Test GET /api/seo/config endpoint"""
        self.log("Testing SEO Configuration endpoint...")
        
        if not self.admin_token:
            self.log("❌ Cannot test SEO config: No admin token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            self.log("   Sending SEO config request...")
            
            response = self.session.get(f"{BASE_URL}/seo/config", headers=headers)
            
            self.log(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                if "success" in data and "config" in data:
                    config = data["config"]
                    
                    self.log("✅ SEO Config: Successfully retrieved!")
                    self.log(f"   Config Keys: {list(config.keys()) if isinstance(config, dict) else 'Not a dict'}")
                    
                    # Check for common config fields
                    expected_fields = ["scraping_enabled", "scraping_frequency", "target_platforms"]
                    found_fields = [field for field in expected_fields if field in config]
                    self.log(f"   Expected Fields Found: {found_fields}")
                    
                    return True
                else:
                    self.log(f"❌ SEO Config: Invalid response structure - {data}", "ERROR")
                    return False
                    
            elif response.status_code == 500:
                self.log("❌ SEO Config: 500 Internal Server Error - CRITICAL ISSUE!", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error Details: {error_data}", "ERROR")
                except:
                    self.log(f"   Raw Error: {response.text}", "ERROR")
                return False
            elif response.status_code == 403:
                self.log("❌ SEO Config: 403 Forbidden - Premium subscription required", "ERROR")
                return False
            else:
                self.log(f"❌ SEO Config failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ SEO Config failed: {str(e)}", "ERROR")
            return False
    
    def test_openai_api_key_availability(self):
        """Test if OpenAI API key is working by checking error messages"""
        self.log("Testing OpenAI API key availability...")
        
        if not self.admin_token:
            self.log("❌ Cannot test OpenAI key: No admin token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Try a simple SEO analysis to see if we get API key errors
        simple_request = {
            "product_name": "Test Product",
            "product_description": "Simple test",
            "target_keywords": ["test"],
            "language": "fr"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/ai/seo-analysis", json=simple_request, headers=headers)
            
            if response.status_code == 503:
                self.log("❌ OpenAI API Key: Service unavailable - API configuration issue", "ERROR")
                return False
            elif response.status_code == 502:
                self.log("❌ OpenAI API Key: External service error", "ERROR")
                return False
            elif response.status_code == 200:
                self.log("✅ OpenAI API Key: Working correctly")
                return True
            elif response.status_code == 500:
                # Check if it's an ObjectId serialization error vs API key error
                try:
                    error_data = response.json()
                    error_msg = str(error_data).lower()
                    if "objectid" in error_msg or "not iterable" in error_msg:
                        self.log("❌ OpenAI API Key: MongoDB ObjectId serialization error detected", "ERROR")
                        return False
                    elif "api" in error_msg or "key" in error_msg:
                        self.log("❌ OpenAI API Key: API key issue detected", "ERROR")
                        return False
                    else:
                        self.log("❌ OpenAI API Key: Unknown 500 error", "ERROR")
                        return False
                except:
                    self.log("❌ OpenAI API Key: 500 error with unparseable response", "ERROR")
                    return False
            else:
                self.log(f"⚠️  OpenAI API Key: Unexpected response {response.status_code}")
                return True  # Not necessarily a key issue
                
        except Exception as e:
            self.log(f"❌ OpenAI API Key test failed: {str(e)}", "ERROR")
            return False
    
    def test_mongodb_objectid_serialization(self):
        """Test if MongoDB ObjectId serialization is working correctly"""
        self.log("Testing MongoDB ObjectId serialization...")
        
        if not self.admin_token:
            self.log("❌ Cannot test ObjectId serialization: No admin token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test SEO config first as it's simpler
        try:
            response = self.session.get(f"{BASE_URL}/seo/config", headers=headers)
            
            if response.status_code == 500:
                try:
                    error_data = response.json()
                    error_msg = str(error_data).lower()
                    if "objectid" in error_msg or "not iterable" in error_msg or "not json serializable" in error_msg:
                        self.log("❌ MongoDB ObjectId Serialization: CRITICAL ERROR DETECTED!", "ERROR")
                        self.log("   The convert_objectid_to_str() function is not working properly", "ERROR")
                        self.log(f"   Error details: {error_data}", "ERROR")
                        return False
                except:
                    self.log("❌ MongoDB ObjectId Serialization: 500 error suggests serialization issue", "ERROR")
                    return False
            elif response.status_code == 200:
                self.log("✅ MongoDB ObjectId Serialization: Working correctly")
                return True
            elif response.status_code == 403:
                self.log("⚠️  MongoDB ObjectId Serialization: Cannot test due to subscription restrictions")
                return True  # Not a serialization issue
            else:
                self.log(f"⚠️  MongoDB ObjectId Serialization: Unexpected response {response.status_code}")
                return True  # Not necessarily a serialization issue
                
        except Exception as e:
            self.log(f"❌ MongoDB ObjectId Serialization test failed: {str(e)}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Run all Advanced AI backend tests"""
        self.log("=" * 80)
        self.log("STARTING ADVANCED AI BACKEND TESTING")
        self.log("=" * 80)
        
        test_results = {}
        
        # Test 1: Admin Login
        test_results["admin_login"] = self.test_admin_login()
        
        if not test_results["admin_login"]:
            self.log("❌ Cannot continue testing without admin login", "ERROR")
            return test_results
        
        # Test 2: MongoDB ObjectId Serialization
        test_results["objectid_serialization"] = self.test_mongodb_objectid_serialization()
        
        # Test 3: OpenAI API Key
        test_results["openai_api_key"] = self.test_openai_api_key_availability()
        
        # Test 4: SEO Config Endpoint
        test_results["seo_config"] = self.test_seo_config_endpoint()
        
        # Test 5: SEO Analysis Endpoint
        test_results["seo_analysis"] = self.test_seo_analysis_endpoint()
        
        # Test 6: Competitor Analysis Endpoint
        test_results["competitor_analysis"] = self.test_competitor_analysis_endpoint()
        
        # Summary
        self.log("=" * 80)
        self.log("ADVANCED AI BACKEND TEST RESULTS")
        self.log("=" * 80)
        
        passed = sum(1 for result in test_results.values() if result)
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{status} {test_name.replace('_', ' ').title()}")
        
        self.log("=" * 80)
        self.log(f"OVERALL RESULT: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 ALL ADVANCED AI TESTS PASSED!")
        else:
            self.log("❌ SOME ADVANCED AI TESTS FAILED - CRITICAL ISSUES DETECTED")
            
            # Provide specific guidance based on failures
            if not test_results.get("objectid_serialization", True):
                self.log("🔧 FIX NEEDED: MongoDB ObjectId serialization in Advanced AI endpoints")
            if not test_results.get("openai_api_key", True):
                self.log("🔧 FIX NEEDED: OpenAI API key configuration or availability")
            if not test_results.get("seo_config", True):
                self.log("🔧 FIX NEEDED: SEO configuration endpoint implementation")
            if not test_results.get("seo_analysis", True):
                self.log("🔧 FIX NEEDED: SEO analysis endpoint implementation")
            if not test_results.get("competitor_analysis", True):
                self.log("🔧 FIX NEEDED: Competitor analysis endpoint implementation")
        
        self.log("=" * 80)
        
        return test_results

if __name__ == "__main__":
    tester = AdvancedAITester()
    results = tester.run_all_tests()