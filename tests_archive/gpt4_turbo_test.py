#!/usr/bin/env python3
"""
ECOMSIMPLY GPT-4 Turbo Integration Testing Suite - ENHANCED LOGGING FOCUS
Focus: Testing GPT-4 Turbo with Enhanced Logging to Identify Fallback Issues

This test suite specifically addresses the review request to test the GPT-4 Turbo integration
with detailed logging to identify why it's falling back to generic content.

CRITICAL TEST OBJECTIVES FROM REVIEW REQUEST:
1. Test GPT-4 Turbo with enhanced logging by creating new test user
2. Check backend logs for detailed error messages
3. Identify specific error causing fallback to generic content
4. Verify if OpenAI API key is being loaded correctly
5. Test with "iPhone 15 Pro" product specifically
6. Look for specific log messages mentioned in review:
   - "🧠 TENTATIVE GPT-4 TURBO: iPhone 15 Pro"
   - "🔑 OpenAI Key présente: Oui/Non"
   - "🧠 Appel GPT-4 Turbo (nouvelle API) pour: iPhone 15 Pro"
   - Either success or detailed error messages

EXPECTED ERROR INVESTIGATION:
- Check if it's an OpenAI API authentication error
- Check if it's a model access error (GPT-4 Turbo not available)
- Check if it's a network connectivity issue
- Check if it's a JSON parsing error
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 45  # Extended timeout for GPT-4 Turbo calls

class GPT4TurboTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        self.user_data = None
        self.test_results = []
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def log_test_result(self, test_name: str, success: bool, details: str, data: Dict = None):
        """Log test result with details"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "data": data,
            "timestamp": time.strftime("%H:%M:%S")
        }
        self.test_results.append(result)
        self.log(f"{status} {test_name}: {details}")
    
    def test_api_health(self):
        """Test if the API is accessible"""
        self.log("🔍 Testing API health check...")
        try:
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                self.log_test_result("API Health Check", True, f"API accessible: {data.get('message', 'OK')}")
                return True
            else:
                self.log_test_result("API Health Check", False, f"API returned status {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("API Health Check", False, f"API connection failed: {str(e)}")
            return False
    
    def test_user_registration_and_login(self):
        """Test user registration and login for authentication"""
        self.log("👤 Testing user registration and login...")
        
        # Generate unique test user
        timestamp = int(time.time())
        test_user = {
            "email": f"gpt4test{timestamp}@example.com",
            "name": "GPT-4 Test User",
            "password": "TestPassword123!"
        }
        
        try:
            # Register user
            response = self.session.post(f"{BASE_URL}/auth/register", json=test_user)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.user_data = data.get("user")
                
                if self.auth_token and self.user_data:
                    self.log_test_result("User Registration", True, f"User registered: {self.user_data['name']}")
                    return True
                else:
                    self.log_test_result("User Registration", False, "Missing token or user data in response")
                    return False
            else:
                self.log_test_result("User Registration", False, f"Registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("User Registration", False, f"Registration exception: {str(e)}")
            return False
    
    def test_gpt4_turbo_product_sheet_generation(self):
        """🎯 MAIN TEST: Test GPT-4 Turbo integration for product sheet generation"""
        self.log("🧠 CRITICAL TEST: Testing GPT-4 Turbo integration for product sheet generation")
        
        if not self.auth_token:
            self.log_test_result("GPT-4 Turbo Generation", False, "No authentication token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test with iPhone 15 Pro as requested in review
        test_data = {
            "product_name": "iPhone 15 Pro",
            "product_description": "Smartphone haut de gamme avec processeur A17 Pro et appareil photo 48MP",
            "generate_image": True,
            "number_of_images": 1,
            "language": "fr"
        }
        
        self.log(f"📝 Test data: {json.dumps(test_data, ensure_ascii=False)}")
        
        try:
            # Record start time to measure generation time
            start_time = time.time()
            
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            
            # Record end time
            end_time = time.time()
            generation_time = end_time - start_time
            
            self.log(f"⏱️ Generation time: {generation_time:.2f} seconds")
            
            if response.status_code != 200:
                self.log_test_result("GPT-4 Turbo Generation", False, f"API call failed: {response.status_code} - {response.text}")
                return False
                
            data = response.json()
            
            # Check if generation was successful
            if not data.get("success", False):
                self.log_test_result("GPT-4 Turbo Generation", False, f"Generation failed: {data.get('message', 'Unknown error')}")
                return False
                
            sheet_data = data.get("sheet", {})
            
            # Validate all required fields are present
            required_fields = [
                "generated_title", "marketing_description", "key_features",
                "seo_tags", "price_suggestions", "target_audience", "call_to_action"
            ]
            
            missing_fields = [field for field in required_fields if not sheet_data.get(field)]
            if missing_fields:
                self.log_test_result("GPT-4 Turbo Generation", False, f"Missing required fields: {missing_fields}")
                return False
            
            # Log generated content for analysis
            self.log("📊 GENERATED CONTENT ANALYSIS:")
            self.log(f"   Title: {sheet_data.get('generated_title', 'N/A')}")
            self.log(f"   Description Length: {len(sheet_data.get('marketing_description', ''))} characters")
            self.log(f"   Features Count: {len(sheet_data.get('key_features', []))}")
            self.log(f"   SEO Tags Count: {len(sheet_data.get('seo_tags', []))}")
            self.log(f"   Price Suggestions: {sheet_data.get('price_suggestions', 'N/A')}")
            self.log(f"   Target Audience: {sheet_data.get('target_audience', 'N/A')[:100]}...")
            self.log(f"   Call to Action: {sheet_data.get('call_to_action', 'N/A')}")
            
            # Check if AI generation flag is set (indicates real AI was used)
            is_ai_generated = sheet_data.get("is_ai_generated", False)
            self.log(f"   AI Generated Flag: {is_ai_generated}")
            
            # Check generation time (should be under 30 seconds as per requirements)
            generation_time_from_response = sheet_data.get("generation_time", generation_time)
            time_acceptable = generation_time_from_response < 30
            
            self.log(f"   Generation Time: {generation_time_from_response:.2f}s (Acceptable: {time_acceptable})")
            
            # Validate content quality for iPhone 15 Pro
            content_quality = self.validate_iphone_content_quality(sheet_data)
            
            # Determine overall success
            success = (
                len(missing_fields) == 0 and
                is_ai_generated and
                time_acceptable and
                content_quality["overall_quality"]
            )
            
            details = f"Fields: ✅ Complete | AI Generated: {'✅' if is_ai_generated else '❌'} | Time: {generation_time_from_response:.2f}s | Quality: {'✅' if content_quality['overall_quality'] else '❌'}"
            
            if content_quality["issues"]:
                details += f" | Issues: {'; '.join(content_quality['issues'])}"
            
            self.log_test_result("GPT-4 Turbo Generation", success, details, {
                "generation_time": generation_time_from_response,
                "is_ai_generated": is_ai_generated,
                "content_quality": content_quality,
                "sheet_data": sheet_data
            })
            
            return success
            
        except Exception as e:
            self.log_test_result("GPT-4 Turbo Generation", False, f"Exception: {str(e)}")
            return False
    
    def validate_iphone_content_quality(self, sheet_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content quality specifically for iPhone 15 Pro"""
        quality_analysis = {
            "overall_quality": True,
            "issues": [],
            "scores": {}
        }
        
        title = sheet_data.get("generated_title", "").lower()
        description = sheet_data.get("marketing_description", "").lower()
        features = [f.lower() for f in sheet_data.get("key_features", [])]
        tags = [t.lower() for t in sheet_data.get("seo_tags", [])]
        price_text = sheet_data.get("price_suggestions", "").lower()
        
        # Check if title is appropriate for iPhone
        if "iphone" not in title:
            quality_analysis["issues"].append("Title should mention iPhone")
            quality_analysis["overall_quality"] = False
        
        # Check if description is substantial (should be 200+ words as per prompt)
        word_count = len(description.split())
        if word_count < 100:  # Minimum acceptable
            quality_analysis["issues"].append(f"Description too short: {word_count} words")
            quality_analysis["overall_quality"] = False
        
        quality_analysis["scores"]["description_word_count"] = word_count
        
        # Check if features are relevant to smartphones
        smartphone_terms = ["processeur", "appareil photo", "écran", "batterie", "stockage", "camera", "processor", "screen", "battery", "storage"]
        relevant_features = sum(1 for feature in features if any(term in feature for term in smartphone_terms))
        
        if relevant_features < 2:
            quality_analysis["issues"].append("Features should be more relevant to smartphones")
            quality_analysis["overall_quality"] = False
        
        quality_analysis["scores"]["relevant_features"] = relevant_features
        
        # Check pricing (iPhone should be in premium range)
        import re
        price_numbers = re.findall(r'(\d+)€', price_text)
        if price_numbers:
            max_price = max(int(p) for p in price_numbers)
            if max_price < 500:  # iPhone should be premium priced
                quality_analysis["issues"].append(f"iPhone pricing seems too low: {max_price}€")
                quality_analysis["overall_quality"] = False
            quality_analysis["scores"]["max_price"] = max_price
        
        # Check if SEO tags are relevant
        tech_terms = ["iphone", "smartphone", "apple", "mobile", "téléphone", "tech"]
        relevant_tags = sum(1 for tag in tags if any(term in tag for term in tech_terms))
        
        if relevant_tags < 2:
            quality_analysis["issues"].append("SEO tags should be more relevant to iPhone/smartphones")
            quality_analysis["overall_quality"] = False
        
        quality_analysis["scores"]["relevant_tags"] = relevant_tags
        
        return quality_analysis
    
    def test_backend_service_status(self):
        """Test backend service status and configuration"""
        self.log("🔧 Testing backend service status...")
        
        try:
            # Test basic API endpoints to verify services are running
            endpoints_to_test = [
                ("/", "GET", None),
            ]
            
            all_services_ok = True
            
            for endpoint, method, data in endpoints_to_test:
                try:
                    if method == "GET":
                        response = self.session.get(f"{BASE_URL}{endpoint}")
                    elif method == "POST":
                        response = self.session.post(f"{BASE_URL}{endpoint}", json=data)
                    
                    if response.status_code in [200, 401, 403]:  # 401/403 are OK for protected endpoints
                        self.log(f"   ✅ {endpoint}: Service responding (status {response.status_code})")
                    else:
                        self.log(f"   ❌ {endpoint}: Service issue (status {response.status_code})")
                        all_services_ok = False
                        
                except Exception as e:
                    self.log(f"   ❌ {endpoint}: Service error - {str(e)}")
                    all_services_ok = False
            
            self.log_test_result("Backend Service Status", all_services_ok, 
                               "All services responding" if all_services_ok else "Some services have issues")
            return all_services_ok
            
        except Exception as e:
            self.log_test_result("Backend Service Status", False, f"Service check failed: {str(e)}")
            return False
    
    def test_openai_api_key_configuration(self):
        """Test OpenAI API key configuration by attempting generation"""
        self.log("🔑 Testing OpenAI API key configuration...")
        
        if not self.auth_token:
            self.log_test_result("OpenAI API Key Config", False, "No authentication token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Simple test to see if OpenAI integration works
        test_data = {
            "product_name": "Test Product",
            "product_description": "Simple test for API key validation",
            "generate_image": False,  # Focus on text generation only
            "number_of_images": 0,
            "language": "fr"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success", False):
                    sheet_data = data.get("sheet", {})
                    is_ai_generated = sheet_data.get("is_ai_generated", False)
                    
                    if is_ai_generated:
                        self.log_test_result("OpenAI API Key Config", True, "OpenAI API key working correctly")
                        return True
                    else:
                        self.log_test_result("OpenAI API Key Config", False, "API key may be missing - using fallback")
                        return False
                else:
                    self.log_test_result("OpenAI API Key Config", False, f"Generation failed: {data.get('message', 'Unknown error')}")
                    return False
            else:
                self.log_test_result("OpenAI API Key Config", False, f"API call failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("OpenAI API Key Config", False, f"Exception: {str(e)}")
            return False
    
    def test_multiple_product_types(self):
        """Test GPT-4 Turbo with different product types to verify versatility"""
        self.log("🎯 Testing GPT-4 Turbo with multiple product types...")
        
        if not self.auth_token:
            self.log_test_result("Multiple Product Types", False, "No authentication token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        test_products = [
            {
                "name": "MacBook Pro M3",
                "description": "Ordinateur portable professionnel avec puce M3 et écran Retina",
                "expected_price_range": (1500, 3000)
            },
            {
                "name": "AirPods Pro",
                "description": "Écouteurs sans fil avec réduction de bruit active",
                "expected_price_range": (200, 400)
            },
            {
                "name": "Apple Watch Series 9",
                "description": "Montre connectée avec GPS et suivi de santé",
                "expected_price_range": (300, 800)
            }
        ]
        
        successful_generations = 0
        
        for product in test_products:
            test_data = {
                "product_name": product["name"],
                "product_description": product["description"],
                "generate_image": False,  # Focus on text generation
                "number_of_images": 0,
                "language": "fr"
            }
            
            try:
                start_time = time.time()
                response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
                generation_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success", False):
                        sheet_data = data.get("sheet", {})
                        is_ai_generated = sheet_data.get("is_ai_generated", False)
                        
                        # Quick quality check
                        title = sheet_data.get("generated_title", "")
                        description = sheet_data.get("marketing_description", "")
                        
                        if is_ai_generated and len(title) > 0 and len(description) > 100:
                            successful_generations += 1
                            self.log(f"   ✅ {product['name']}: Generated successfully ({generation_time:.2f}s)")
                        else:
                            self.log(f"   ❌ {product['name']}: Quality issues or not AI generated")
                    else:
                        self.log(f"   ❌ {product['name']}: Generation failed")
                else:
                    self.log(f"   ❌ {product['name']}: API call failed ({response.status_code})")
                    
                time.sleep(1)  # Brief pause between requests
                
            except Exception as e:
                self.log(f"   ❌ {product['name']}: Exception - {str(e)}")
        
        success = successful_generations >= 2  # At least 2 out of 3 should work
        self.log_test_result("Multiple Product Types", success, 
                           f"{successful_generations}/{len(test_products)} products generated successfully")
        return success
    
    def run_comprehensive_gpt4_turbo_tests(self):
        """Run all GPT-4 Turbo integration tests"""
        self.log("🚀 Starting Comprehensive GPT-4 Turbo Integration Tests")
        self.log("=" * 80)
        
        test_functions = [
            self.test_api_health,
            self.test_backend_service_status,
            self.test_user_registration_and_login,
            self.test_openai_api_key_configuration,
            self.test_gpt4_turbo_product_sheet_generation,
            self.test_multiple_product_types,
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_func in test_functions:
            try:
                if test_func():
                    passed_tests += 1
                time.sleep(1)  # Brief pause between tests
            except Exception as e:
                self.log(f"❌ Test {test_func.__name__} failed with exception: {str(e)}", "ERROR")
        
        # Print summary
        self.log("=" * 80)
        self.log("🎯 GPT-4 TURBO INTEGRATION TEST SUMMARY")
        self.log("=" * 80)
        
        for result in self.test_results:
            self.log(f"{result['status']} {result['test']}: {result['details']}")
        
        self.log("=" * 80)
        success_rate = (passed_tests / total_tests) * 100
        self.log(f"📊 OVERALL RESULT: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            self.log("🎉 GPT-4 TURBO INTEGRATION: WORKING CORRECTLY", "SUCCESS")
        elif success_rate >= 60:
            self.log("⚠️ GPT-4 TURBO INTEGRATION: PARTIALLY WORKING", "WARNING")
        else:
            self.log("❌ GPT-4 TURBO INTEGRATION: CRITICAL ISSUES", "ERROR")
        
        return success_rate >= 80

def main():
    """Main test execution"""
    tester = GPT4TurboTester()
    success = tester.run_comprehensive_gpt4_turbo_tests()
    
    if success:
        print("\n✅ GPT-4 Turbo integration is working correctly!")
        exit(0)
    else:
        print("\n❌ GPT-4 Turbo integration has issues that need attention!")
        exit(1)

if __name__ == "__main__":
    main()