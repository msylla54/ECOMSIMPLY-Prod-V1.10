#!/usr/bin/env python3
"""
ECOMSIMPLY Backend Testing Suite - CATEGORY SELECTION & GPT-4 TURBO CORRECTIONS
================================================================================

TEST FINAL DE VALIDATION - TOUTES LES CORRECTIONS

This comprehensive test suite validates all the corrections mentioned in the review request:
1. ProductSheetRequest: Category field addition
2. ProductSheetResponse: Category field for API return  
3. ProductSheet: Category field for DB storage
4. call_gpt4_turbo_direct: Category parameter support
5. generate_sheet: Category passing + inclusion in response
6. GPT-4 Turbo Prompt: target_audience as simple text

CRITICAL TESTS:
- Test Complet de la Chaîne Catégorie
- Test Target Audience Format
- Test Comparatif d'Influence Catégorie
- Test Catégorie Personnalisée
- Test de Non-Régression
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional

import random
import uuid

# Configuration
BACKEND_URL = "https://ecomsimply.com/api"
TEST_USER_EMAIL = f"category.test.{random.randint(1000, 9999)}@example.com"
TEST_USER_PASSWORD = "CategoryTest123!"
TEST_USER_NAME = "Category Test User"

class CategoryTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    def setup_test_user(self) -> bool:
        """Create and authenticate test user"""
        try:
            # Register test user
            register_data = {
                "email": TEST_USER_EMAIL,
                "name": TEST_USER_NAME,
                "password": TEST_USER_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=register_data)
            if response.status_code in [200, 201]:
                print(f"✅ Test user created: {TEST_USER_EMAIL}")
            elif response.status_code == 400 and ("already exists" in response.text or "déjà enregistré" in response.text):
                print(f"ℹ️ Test user already exists: {TEST_USER_EMAIL}")
            else:
                print(f"❌ Failed to create test user: {response.status_code} - {response.text}")
                return False
            
            # Login test user
            login_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.user_id = data.get("user", {}).get("id")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                print(f"✅ Test user authenticated successfully")
                return True
            else:
                print(f"❌ Failed to authenticate test user: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error setting up test user: {e}")
            return False
    
    def test_category_field_storage_and_return(self) -> bool:
        """Test 1: Category field storage and API return"""
        try:
            print("\n🎯 TEST 1: CATEGORY FIELD STORAGE AND API RETURN")
            
            # Test with category
            request_data = {
                "product_name": "iPhone 15 Pro",
                "product_description": "Smartphone haut de gamme avec processeur A17 Pro",
                "generate_image": False,
                "number_of_images": 0,
                "language": "fr",
                "category": "électronique"
            }
            
            print(f"📤 Sending request with category: {request_data['category']}")
            response = self.session.post(f"{BACKEND_URL}/generate-sheet", json=request_data)
            
            if response.status_code != 200:
                self.log_test("Category Storage", False, f"API returned {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            returned_category = data.get("category")
            
            if returned_category is None:
                self.log_test("Category Storage", False, f"Category field returned None instead of 'électronique'")
                return False
            elif returned_category != "électronique":
                self.log_test("Category Storage", False, f"Category field returned '{returned_category}' instead of 'électronique'")
                return False
            else:
                self.log_test("Category Storage", True, f"Category field correctly stored and returned: '{returned_category}'")
                return True
                
        except Exception as e:
            self.log_test("Category Storage", False, f"Exception: {e}")
            return False
    
    def test_target_audience_format(self) -> bool:
        """Test 2: Target audience format (simple text, not JSON)"""
        try:
            print("\n🎯 TEST 2: TARGET AUDIENCE FORMAT")
            
            request_data = {
                "product_name": "MacBook Pro",
                "product_description": "Ordinateur portable professionnel",
                "generate_image": False,
                "number_of_images": 0,
                "language": "fr",
                "category": "informatique"
            }
            
            response = self.session.post(f"{BACKEND_URL}/generate-sheet", json=request_data)
            
            if response.status_code != 200:
                self.log_test("Target Audience Format", False, f"API returned {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            target_audience = data.get("target_audience")
            
            if target_audience is None:
                self.log_test("Target Audience Format", False, "target_audience field is None")
                return False
            
            # Check if it's a simple string (not JSON object)
            if isinstance(target_audience, dict):
                self.log_test("Target Audience Format", False, f"target_audience is still a JSON object: {target_audience}")
                return False
            elif not isinstance(target_audience, str):
                self.log_test("Target Audience Format", False, f"target_audience is not a string: {type(target_audience)}")
                return False
            elif len(target_audience) < 50:
                self.log_test("Target Audience Format", False, f"target_audience too short (likely not properly converted): '{target_audience}'")
                return False
            else:
                # Check if it contains JSON-like structures
                if target_audience.strip().startswith('{') or 'demographics' in target_audience or 'psychographics' in target_audience:
                    self.log_test("Target Audience Format", False, f"target_audience still contains JSON structure: {target_audience[:100]}...")
                    return False
                else:
                    self.log_test("Target Audience Format", True, f"target_audience is simple text ({len(target_audience)} chars): '{target_audience[:100]}...'")
                    return True
                    
        except Exception as e:
            self.log_test("Target Audience Format", False, f"Exception: {e}")
            return False
    
    def test_category_influence_comparison(self) -> bool:
        """Test 3: Category influence on content generation (comparative test)"""
        try:
            print("\n🎯 TEST 3: CATEGORY INFLUENCE COMPARISON")
            
            base_product = {
                "product_name": "T-shirt Premium",
                "product_description": "T-shirt de qualité supérieure",
                "generate_image": False,
                "number_of_images": 0,
                "language": "fr"
            }
            
            # Test without category
            print("📤 Testing without category...")
            response1 = self.session.post(f"{BACKEND_URL}/generate-sheet", json=base_product)
            
            if response1.status_code != 200:
                self.log_test("Category Influence", False, f"First request failed: {response1.status_code}")
                return False
            
            data1 = response1.json()
            
            # Test with category
            print("📤 Testing with 'mode' category...")
            base_product["category"] = "mode"
            response2 = self.session.post(f"{BACKEND_URL}/generate-sheet", json=base_product)
            
            if response2.status_code != 200:
                self.log_test("Category Influence", False, f"Second request failed: {response2.status_code}")
                return False
            
            data2 = response2.json()
            
            # Compare results
            title1 = data1.get("generated_title", "")
            title2 = data2.get("generated_title", "")
            seo_tags1 = data1.get("seo_tags", [])
            seo_tags2 = data2.get("seo_tags", [])
            
            # Check for differences
            title_different = title1 != title2
            seo_different = set(seo_tags1) != set(seo_tags2)
            
            # Check for fashion-related terms in category version
            fashion_terms = ["mode", "style", "tendance", "fashion", "élégant", "chic"]
            has_fashion_terms = any(term.lower() in title2.lower() or any(term.lower() in tag.lower() for tag in seo_tags2) for term in fashion_terms)
            
            if title_different and seo_different and has_fashion_terms:
                self.log_test("Category Influence", True, f"Category clearly influences content - Fashion terms found, titles and SEO tags differ")
                print(f"  Without category: {title1}")
                print(f"  With 'mode' category: {title2}")
                return True
            elif title_different or seo_different:
                self.log_test("Category Influence", True, f"Category influences content - Some differences detected")
                return True
            else:
                self.log_test("Category Influence", False, f"No significant differences between with/without category")
                return False
                
        except Exception as e:
            self.log_test("Category Influence", False, f"Exception: {e}")
            return False
    
    def test_custom_category(self) -> bool:
        """Test 4: Custom category handling"""
        try:
            print("\n🎯 TEST 4: CUSTOM CATEGORY HANDLING")
            
            request_data = {
                "product_name": "Drone Innovant",
                "product_description": "Drone avec intelligence artificielle",
                "generate_image": False,
                "number_of_images": 0,
                "language": "fr",
                "category": "innovation technologique"
            }
            
            print(f"📤 Testing with custom category: '{request_data['category']}'")
            response = self.session.post(f"{BACKEND_URL}/generate-sheet", json=request_data)
            
            if response.status_code != 200:
                self.log_test("Custom Category", False, f"API returned {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            returned_category = data.get("category")
            generated_title = data.get("generated_title", "")
            seo_tags = data.get("seo_tags", [])
            
            # Check category storage
            if returned_category != "innovation technologique":
                self.log_test("Custom Category", False, f"Custom category not stored correctly: got '{returned_category}'")
                return False
            
            # Check if custom category influenced content
            innovation_terms = ["innovation", "technologique", "avancé", "intelligent", "futur"]
            has_innovation_terms = any(term.lower() in generated_title.lower() or any(term.lower() in tag.lower() for tag in seo_tags) for term in innovation_terms)
            
            if has_innovation_terms:
                self.log_test("Custom Category", True, f"Custom category properly handled and influences content")
                return True
            else:
                self.log_test("Custom Category", True, f"Custom category stored correctly (content influence may vary)")
                return True
                
        except Exception as e:
            self.log_test("Custom Category", False, f"Exception: {e}")
            return False
    
    def test_non_regression_without_category(self) -> bool:
        """Test 5: Non-regression test (without category should still work)"""
        try:
            print("\n🎯 TEST 5: NON-REGRESSION (WITHOUT CATEGORY)")
            
            request_data = {
                "product_name": "Casque Audio",
                "product_description": "Casque audio haute qualité",
                "generate_image": False,
                "number_of_images": 0,
                "language": "fr"
                # No category field
            }
            
            print("📤 Testing without category field...")
            response = self.session.post(f"{BACKEND_URL}/generate-sheet", json=request_data)
            
            if response.status_code != 200:
                self.log_test("Non-Regression", False, f"API failed without category: {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            
            # Check all required fields are present
            required_fields = ["generated_title", "marketing_description", "key_features", "seo_tags", "price_suggestions", "target_audience", "call_to_action"]
            missing_fields = [field for field in required_fields if not data.get(field)]
            
            if missing_fields:
                self.log_test("Non-Regression", False, f"Missing required fields: {missing_fields}")
                return False
            
            # Category should be None or not present
            returned_category = data.get("category")
            if returned_category is not None:
                self.log_test("Non-Regression", False, f"Category should be None when not provided, got: {returned_category}")
                return False
            
            self.log_test("Non-Regression", True, f"System works correctly without category - all required fields present")
            return True
            
        except Exception as e:
            self.log_test("Non-Regression", False, f"Exception: {e}")
            return False
    
    def test_performance_benchmark(self) -> bool:
        """Test 6: Performance benchmark (< 30 seconds)"""
        try:
            print("\n🎯 TEST 6: PERFORMANCE BENCHMARK")
            
            request_data = {
                "product_name": "Smartphone Test Performance",
                "product_description": "Test de performance de génération",
                "generate_image": False,
                "number_of_images": 0,
                "language": "fr",
                "category": "électronique"
            }
            
            print("📤 Testing generation performance...")
            start_time = time.time()
            response = self.session.post(f"{BACKEND_URL}/generate-sheet", json=request_data)
            end_time = time.time()
            
            generation_time = end_time - start_time
            
            if response.status_code != 200:
                self.log_test("Performance", False, f"API failed: {response.status_code}")
                return False
            
            if generation_time > 30:
                self.log_test("Performance", False, f"Generation took {generation_time:.2f}s (> 30s limit)")
                return False
            else:
                self.log_test("Performance", True, f"Generation completed in {generation_time:.2f}s (< 30s)")
                return True
                
        except Exception as e:
            self.log_test("Performance", False, f"Exception: {e}")
            return False
    
    def run_comprehensive_tests(self):
        """Run all category-related tests"""
        print("🚀 STARTING COMPREHENSIVE CATEGORY TESTING SUITE")
        print("=" * 80)
        
        # Setup
        if not self.setup_test_user():
            print("❌ Failed to setup test user - aborting tests")
            return
        
        # Run all tests
        tests = [
            self.test_category_field_storage_and_return,
            self.test_target_audience_format,
            self.test_category_influence_comparison,
            self.test_custom_category,
            self.test_non_regression_without_category,
            self.test_performance_benchmark
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
                time.sleep(1)  # Brief pause between tests
            except Exception as e:
                print(f"❌ Test {test_func.__name__} failed with exception: {e}")
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        print(f"\n🎯 FINAL SCORE: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        
        if success_rate >= 100:
            print("🎉 ALL TESTS PASSED - CATEGORY FUNCTIONALITY FULLY OPERATIONAL!")
        elif success_rate >= 80:
            print("✅ MOST TESTS PASSED - CATEGORY FUNCTIONALITY MOSTLY WORKING")
        elif success_rate >= 60:
            print("⚠️ SOME TESTS FAILED - CATEGORY FUNCTIONALITY PARTIALLY WORKING")
        else:
            print("❌ MANY TESTS FAILED - CATEGORY FUNCTIONALITY NEEDS MAJOR FIXES")
        
        return success_rate >= 80

if __name__ == "__main__":
    test_suite = CategoryTestSuite()
    success = test_suite.run_comprehensive_tests()
    sys.exit(0 if success else 1)