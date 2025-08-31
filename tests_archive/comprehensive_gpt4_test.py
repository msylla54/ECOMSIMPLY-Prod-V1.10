#!/usr/bin/env python3
"""
COMPREHENSIVE GPT-4 TURBO INTEGRATION TEST
Focus: Verify if GPT-4 Turbo is actually working or if system is using fallback

CRITICAL FINDINGS FROM DEBUG:
1. API works but returns GENERIC FALLBACK content
2. Content shows classic fallback phrases like "produit d'exception qui répond à vos attentes"
3. This indicates GPT-4 Turbo integration is NOT working properly
4. number_of_images must be >= 1 (validation constraint)

TEST OBJECTIVES:
1. Confirm GPT-4 Turbo is NOT working (using fallback)
2. Test different product types to verify fallback behavior
3. Measure generation times (should be faster for fallback)
4. Validate API response structure
5. Document the exact issue for the main agent
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 60

class ComprehensiveGPT4Tester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        self.user_data = None
        self.test_results = []
        self.fallback_indicators = [
            "produit d'exception qui répond à vos attentes",
            "qualité premium garantie",
            "design soigné et fonctionnel", 
            "performance optimale",
            "satisfaction client assurée",
            "prix sur demande - contactez-nous pour un devis personnalisé"
        ]
        
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
    
    def setup_test_user(self):
        """Create and authenticate a test user"""
        self.log("🔧 Setting up test user...")
        
        timestamp = int(time.time())
        test_user = {
            "email": f"gpt4comprehensive{timestamp}@example.com",
            "name": "GPT-4 Comprehensive Tester",
            "password": "TestPassword123!"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=test_user)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.user_data = data.get("user")
                
                if self.auth_token and self.user_data:
                    self.log(f"✅ Test user created: {self.user_data['name']}")
                    return True
                else:
                    self.log("❌ User registration: Missing token or user data", "ERROR")
                    return False
            else:
                self.log(f"❌ User registration failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ User setup failed: {str(e)}", "ERROR")
            return False
    
    def analyze_content_for_fallback(self, sheet_data: Dict[str, Any], product_name: str) -> Dict[str, Any]:
        """Analyze content to determine if it's fallback or GPT-4 generated"""
        analysis = {
            "is_fallback": False,
            "fallback_score": 0,
            "gpt4_indicators": 0,
            "fallback_phrases_found": [],
            "content_quality": "unknown",
            "product_specificity": 0
        }
        
        title = sheet_data.get("generated_title", "").lower()
        description = sheet_data.get("marketing_description", "").lower()
        features = [f.lower() for f in sheet_data.get("key_features", [])]
        price_text = sheet_data.get("price_suggestions", "").lower()
        
        all_content = title + " " + description + " " + " ".join(features) + " " + price_text
        
        # Check for fallback indicators
        for indicator in self.fallback_indicators:
            if indicator.lower() in all_content:
                analysis["fallback_phrases_found"].append(indicator)
                analysis["fallback_score"] += 20
        
        # Check for product-specific content
        product_words = product_name.lower().split()
        for word in product_words:
            if len(word) > 3 and word in all_content:
                analysis["product_specificity"] += 1
        
        # Determine if it's fallback
        analysis["is_fallback"] = analysis["fallback_score"] > 40 or len(analysis["fallback_phrases_found"]) >= 2
        
        # Assess content quality
        if analysis["is_fallback"]:
            analysis["content_quality"] = "fallback_generic"
        elif len(description) > 300 and analysis["product_specificity"] > 2:
            analysis["content_quality"] = "gpt4_likely"
        else:
            analysis["content_quality"] = "uncertain"
        
        return analysis
    
    def test_iphone_generation(self):
        """Test iPhone 15 Pro generation to check for GPT-4 vs fallback"""
        self.log("📱 TESTING: iPhone 15 Pro generation")
        
        if not self.auth_token:
            self.log_test_result("iPhone Generation", False, "No auth token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        test_data = {
            "product_name": "iPhone 15 Pro",
            "product_description": "Smartphone haut de gamme avec processeur A17 Pro et appareil photo 48MP",
            "generate_image": True,  # Must be True to avoid 422 error
            "number_of_images": 1,   # Must be >= 1
            "language": "fr"
        }
        
        start_time = time.time()
        
        try:
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            generation_time = time.time() - start_time
            
            if response.status_code != 200:
                self.log_test_result("iPhone Generation", False, f"API call failed: {response.status_code}")
                return False
                
            data = response.json()
            
            # Analyze the content
            analysis = self.analyze_content_for_fallback(data, "iPhone 15 Pro")
            
            # Log detailed analysis
            self.log("📊 IPHONE CONTENT ANALYSIS:")
            self.log(f"   Title: {data.get('generated_title', 'N/A')}")
            self.log(f"   Description: {data.get('marketing_description', 'N/A')[:100]}...")
            self.log(f"   Generation Time: {generation_time:.2f}s")
            self.log(f"   Is Fallback: {analysis['is_fallback']}")
            self.log(f"   Fallback Score: {analysis['fallback_score']}/100")
            self.log(f"   Fallback Phrases: {analysis['fallback_phrases_found']}")
            self.log(f"   Content Quality: {analysis['content_quality']}")
            
            # Determine success (we expect this to be fallback based on debug results)
            is_using_fallback = analysis["is_fallback"]
            success = True  # Test passes if we can detect the issue
            
            details = f"Fallback detected: {is_using_fallback} | Quality: {analysis['content_quality']} | Time: {generation_time:.2f}s"
            
            self.log_test_result("iPhone Generation", success, details, {
                "generation_time": generation_time,
                "is_fallback": is_using_fallback,
                "analysis": analysis,
                "content": data
            })
            
            return success
            
        except Exception as e:
            generation_time = time.time() - start_time
            self.log_test_result("iPhone Generation", False, f"Exception: {str(e)}")
            return False
    
    def test_multiple_products(self):
        """Test multiple products to confirm fallback behavior"""
        self.log("🎯 TESTING: Multiple products for fallback confirmation")
        
        if not self.auth_token:
            self.log_test_result("Multiple Products", False, "No auth token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        test_products = [
            ("MacBook Pro M3", "Ordinateur portable professionnel avec puce M3"),
            ("AirPods Pro", "Écouteurs sans fil avec réduction de bruit"),
            ("Papier toilette premium", "Papier toilette doux et résistant")
        ]
        
        fallback_count = 0
        successful_tests = 0
        generation_times = []
        
        for product_name, description in test_products:
            test_data = {
                "product_name": product_name,
                "product_description": description,
                "generate_image": True,
                "number_of_images": 1,
                "language": "fr"
            }
            
            start_time = time.time()
            
            try:
                response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
                generation_time = time.time() - start_time
                generation_times.append(generation_time)
                
                if response.status_code == 200:
                    data = response.json()
                    analysis = self.analyze_content_for_fallback(data, product_name)
                    
                    if analysis["is_fallback"]:
                        fallback_count += 1
                    
                    successful_tests += 1
                    
                    self.log(f"   ✅ {product_name}: {generation_time:.2f}s | Fallback: {analysis['is_fallback']}")
                else:
                    self.log(f"   ❌ {product_name}: API error {response.status_code}")
                    
            except Exception as e:
                generation_time = time.time() - start_time
                generation_times.append(generation_time)
                self.log(f"   ❌ {product_name}: Exception - {str(e)}")
            
            time.sleep(2)  # Pause between requests
        
        # Analyze results
        if successful_tests > 0:
            avg_time = sum(generation_times) / len(generation_times)
            fallback_percentage = (fallback_count / successful_tests) * 100
            
            # If most/all are fallback, GPT-4 Turbo is not working
            gpt4_not_working = fallback_percentage >= 80
            
            success = True  # Test passes if we can identify the issue
            details = f"Fallback rate: {fallback_percentage:.1f}% ({fallback_count}/{successful_tests}) | Avg time: {avg_time:.2f}s | GPT-4 issue: {gpt4_not_working}"
            
            self.log_test_result("Multiple Products", success, details, {
                "fallback_count": fallback_count,
                "successful_tests": successful_tests,
                "fallback_percentage": fallback_percentage,
                "avg_generation_time": avg_time,
                "gpt4_turbo_not_working": gpt4_not_working
            })
            
            return success
        else:
            self.log_test_result("Multiple Products", False, "No successful tests")
            return False
    
    def test_api_response_structure(self):
        """Test that API response structure is correct"""
        self.log("🔍 TESTING: API response structure validation")
        
        if not self.auth_token:
            self.log_test_result("API Response Structure", False, "No auth token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        test_data = {
            "product_name": "Test Product",
            "product_description": "Test description",
            "generate_image": True,
            "number_of_images": 1,
            "language": "fr"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            
            if response.status_code != 200:
                self.log_test_result("API Response Structure", False, f"API call failed: {response.status_code}")
                return False
                
            data = response.json()
            
            # Check required fields from ProductSheetResponse model
            required_fields = [
                "generated_title",
                "marketing_description",
                "key_features", 
                "seo_tags",
                "price_suggestions",
                "target_audience",
                "call_to_action",
                "generated_images",
                "generation_time"
            ]
            
            missing_fields = []
            field_types_correct = True
            
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
                else:
                    value = data[field]
                    if field in ["key_features", "seo_tags", "generated_images"]:
                        if not isinstance(value, list):
                            field_types_correct = False
                    elif field == "generation_time":
                        if not isinstance(value, (int, float)):
                            field_types_correct = False
                    else:
                        if not isinstance(value, str):
                            field_types_correct = False
            
            success = len(missing_fields) == 0 and field_types_correct
            details = f"Missing fields: {len(missing_fields)} | Correct types: {field_types_correct}"
            
            if missing_fields:
                details += f" | Missing: {', '.join(missing_fields)}"
            
            self.log_test_result("API Response Structure", success, details, {
                "missing_fields": missing_fields,
                "field_types_correct": field_types_correct,
                "response_data": data
            })
            
            return success
            
        except Exception as e:
            self.log_test_result("API Response Structure", False, f"Exception: {str(e)}")
            return False
    
    def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        self.log("🚀 STARTING COMPREHENSIVE GPT-4 TURBO INTEGRATION ANALYSIS")
        self.log("=" * 80)
        
        # Setup
        if not self.setup_test_user():
            self.log("❌ CRITICAL: Cannot proceed without test user", "ERROR")
            return False
        
        # Run tests
        tests = [
            ("iPhone Generation Analysis", self.test_iphone_generation),
            ("Multiple Products Analysis", self.test_multiple_products),
            ("API Response Structure", self.test_api_response_structure)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n🧪 Running: {test_name}")
            self.log("-" * 50)
            
            try:
                if test_func():
                    passed_tests += 1
                    self.log(f"✅ {test_name} COMPLETED")
                else:
                    self.log(f"❌ {test_name} FAILED")
            except Exception as e:
                self.log(f"❌ {test_name} EXCEPTION: {str(e)}", "ERROR")
            
            time.sleep(2)
        
        # Analysis and Summary
        self.log("\n" + "=" * 80)
        self.log("🎯 COMPREHENSIVE GPT-4 TURBO ANALYSIS RESULTS")
        self.log("=" * 80)
        
        # Analyze all test results to determine GPT-4 Turbo status
        fallback_evidence = []
        gpt4_evidence = []
        
        for result in self.test_results:
            if result.get("data"):
                data = result["data"]
                if data.get("is_fallback"):
                    fallback_evidence.append(result["test"])
                if data.get("gpt4_turbo_not_working"):
                    fallback_evidence.append(f"{result['test']} (high fallback rate)")
        
        # Final determination
        gpt4_turbo_working = len(fallback_evidence) == 0
        
        self.log(f"📊 Tests Completed: {passed_tests}/{total_tests}")
        self.log(f"📊 Fallback Evidence: {len(fallback_evidence)} indicators")
        
        if not gpt4_turbo_working:
            self.log("\n❌ CRITICAL FINDING: GPT-4 TURBO IS NOT WORKING")
            self.log("🔍 Evidence of fallback system usage:")
            for evidence in fallback_evidence:
                self.log(f"   • {evidence}")
            
            self.log("\n🎯 ROOT CAUSE ANALYSIS:")
            self.log("   • API endpoint works but returns generic fallback content")
            self.log("   • Content contains classic fallback phrases")
            self.log("   • call_gpt4_turbo_direct function is likely not being called")
            self.log("   • System is using generate_intelligent_fallback_content instead")
            
            self.log("\n🔧 RECOMMENDED ACTIONS:")
            self.log("   1. Check OpenAI API key configuration")
            self.log("   2. Verify call_gpt4_turbo_direct function is being invoked")
            self.log("   3. Check for errors in GPT-4 Turbo integration")
            self.log("   4. Ensure duplicate function removal didn't break the integration")
            
        else:
            self.log("\n✅ GPT-4 TURBO APPEARS TO BE WORKING")
            
        return gpt4_turbo_working

def main():
    """Main test execution"""
    tester = ComprehensiveGPT4Tester()
    
    print("🎯 COMPREHENSIVE GPT-4 TURBO INTEGRATION ANALYSIS")
    print("Investigating whether GPT-4 Turbo is working or using fallback")
    print("=" * 80)
    
    working = tester.run_comprehensive_tests()
    
    if not working:
        print("\n❌ GPT-4 TURBO INTEGRATION IS NOT WORKING - USING FALLBACK SYSTEM")
        exit(1)
    else:
        print("\n✅ GPT-4 TURBO INTEGRATION IS WORKING CORRECTLY")
        exit(0)

if __name__ == "__main__":
    main()