#!/usr/bin/env python3
"""
ECOMSIMPLY Backend Testing Suite - CORRECTED VERSION
Focus: Testing corrections and new category selection feature with correct API response format

CRITICAL FINDINGS FROM INITIAL TESTING:
1. API returns sheet data directly (not wrapped in success/sheet structure)
2. target_audience still returns complex object (fix not working)
3. category field not returned in response (storage issue)
4. number_of_images=0 validation works (no 422 error)
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 45

class CorrectedCategoryTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        self.test_results = []
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def log_test_result(self, test_name: str, success: bool, details: str, data: dict = None):
        """Log test result with details"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "data": data or {},
            "timestamp": time.strftime("%H:%M:%S")
        }
        self.test_results.append(result)
        self.log(f"{status} {test_name}: {details}")
        
    def setup_authentication(self):
        """Setup authentication for testing"""
        self.log("🔐 Setting up authentication...")
        
        # Generate unique test user
        timestamp = int(time.time())
        test_user = {
            "email": f"corrected.test{timestamp}@example.com",
            "name": "Corrected Test User",
            "password": "CorrectedTest123!"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=test_user)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                
                if self.auth_token:
                    self.log_test_result("Authentication Setup", True, f"User registered and authenticated")
                    return True
                else:
                    self.log_test_result("Authentication Setup", False, "Missing token in response")
                    return False
            else:
                self.log_test_result("Authentication Setup", False, f"Registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("Authentication Setup", False, f"Exception: {str(e)}")
            return False
    
    def test_number_of_images_validation_fix(self):
        """🔧 TEST: number_of_images validation fix (ge=0)"""
        self.log("🔧 Testing number_of_images validation fix (ge=0)...")
        
        if not self.auth_token:
            self.log_test_result("Number of Images Validation Fix", False, "No auth token")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test the exact scenario that was failing: generate_image=False, number_of_images=0
        test_data = {
            "product_name": "MacBook Pro M3",
            "product_description": "Ordinateur portable professionnel avec puce M3",
            "generate_image": False,
            "number_of_images": 0,  # This should now be valid (ge=0 instead of ge=1)
            "language": "fr"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            
            if response.status_code == 200:
                # API returns sheet data directly
                sheet_data = response.json()
                
                # Verify no images were generated (as expected)
                product_images = sheet_data.get("generated_images", [])
                
                if len(product_images) == 0:
                    self.log_test_result(
                        "Number of Images Validation Fix", 
                        True, 
                        "number_of_images=0 validation now accepts ge=0 (no 422 error)",
                        {"images_count": len(product_images), "response_status": response.status_code}
                    )
                    return True
                else:
                    self.log_test_result(
                        "Number of Images Validation Fix", 
                        False, 
                        f"Unexpected image generation: {len(product_images)} images"
                    )
                    return False
            elif response.status_code == 422:
                # This would indicate the fix didn't work
                self.log_test_result("Number of Images Validation Fix", False, "Still getting 422 validation error - fix not working")
                return False
            else:
                self.log_test_result("Number of Images Validation Fix", False, f"API call failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("Number of Images Validation Fix", False, f"Exception: {str(e)}")
            return False
    
    def test_target_audience_string_conversion(self):
        """🎯 CRITICAL TEST: GPT-4 Turbo target_audience string conversion fix"""
        self.log("🎯 Testing GPT-4 Turbo target_audience string conversion fix...")
        
        if not self.auth_token:
            self.log_test_result("Target Audience String Conversion", False, "No auth token")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test with a product that would generate complex target_audience object
        test_data = {
            "product_name": "iPhone 15 Pro Max",
            "product_description": "Smartphone premium avec processeur A17 Pro, appareil photo 48MP et écran Super Retina XDR",
            "generate_image": False,
            "number_of_images": 0,
            "language": "fr"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            
            if response.status_code == 200:
                sheet_data = response.json()
                target_audience = sheet_data.get("target_audience")
                
                self.log(f"📊 Target Audience Analysis:")
                self.log(f"   Type: {type(target_audience).__name__}")
                self.log(f"   Content: {str(target_audience)[:200]}...")
                
                # Check if it's a simple string (not a dict-like structure)
                if isinstance(target_audience, str):
                    # Check if it looks like a JSON object (indicates the fix isn't working)
                    if target_audience.strip().startswith('{') and target_audience.strip().endswith('}'):
                        self.log_test_result(
                            "Target Audience String Conversion", 
                            False, 
                            "target_audience is string but contains JSON object - conversion fix not working properly",
                            {"target_audience_type": type(target_audience).__name__, "is_json_like": True}
                        )
                        return False
                    else:
                        self.log_test_result(
                            "Target Audience String Conversion", 
                            True, 
                            f"target_audience correctly converted to simple string: {len(target_audience)} chars",
                            {"target_audience_type": type(target_audience).__name__, "is_json_like": False}
                        )
                        return True
                else:
                    self.log_test_result(
                        "Target Audience String Conversion", 
                        False, 
                        f"target_audience is still {type(target_audience).__name__}, not string",
                        {"target_audience_type": type(target_audience).__name__}
                    )
                    return False
            else:
                self.log_test_result("Target Audience String Conversion", False, f"API call failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("Target Audience String Conversion", False, f"Exception: {str(e)}")
            return False
    
    def test_category_storage_and_influence(self):
        """📱 TEST: Category storage and influence on generation"""
        self.log("📱 Testing category storage and influence on generation...")
        
        if not self.auth_token:
            self.log_test_result("Category Storage and Influence", False, "No auth token")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test with electronics category
        test_data = {
            "product_name": "iPhone 15 Pro",
            "product_description": "Smartphone Apple avec processeur A17 Pro",
            "generate_image": False,
            "number_of_images": 0,
            "language": "fr",
            "category": "électronique"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            
            if response.status_code == 200:
                sheet_data = response.json()
                
                # Check if category is stored/returned
                category_in_response = sheet_data.get("category")
                
                # Analyze content for tech influence
                title = sheet_data.get("generated_title", "").lower()
                description = sheet_data.get("marketing_description", "").lower()
                seo_tags = [tag.lower() for tag in sheet_data.get("seo_tags", [])]
                
                # Check for tech-related content
                tech_indicators = ["technologie", "innovation", "performance", "avancé", "intelligent", "tech", "processeur", "smartphone"]
                has_tech_content = any(indicator in text for text in [title, description] for indicator in tech_indicators)
                has_tech_tags = any(indicator in tag for tag in seo_tags for indicator in tech_indicators)
                
                self.log(f"📊 Category Analysis:")
                self.log(f"   Category in response: {category_in_response}")
                self.log(f"   Tech content detected: {has_tech_content}")
                self.log(f"   Tech SEO tags: {has_tech_tags}")
                self.log(f"   Title: {sheet_data.get('generated_title', 'N/A')}")
                self.log(f"   SEO Tags: {', '.join(sheet_data.get('seo_tags', []))}")
                
                # Determine success
                category_stored = category_in_response == "électronique"
                tech_influence = has_tech_content or has_tech_tags
                
                if category_stored and tech_influence:
                    self.log_test_result(
                        "Category Storage and Influence", 
                        True, 
                        f"Category stored and influenced generation: stored={category_stored}, tech_influence={tech_influence}",
                        {
                            "category_stored": category_stored,
                            "tech_content": has_tech_content,
                            "tech_tags": has_tech_tags,
                            "category_in_response": category_in_response
                        }
                    )
                    return True
                elif not category_stored:
                    self.log_test_result(
                        "Category Storage and Influence", 
                        False, 
                        f"Category not stored in response: expected 'électronique', got {category_in_response}",
                        {"category_in_response": category_in_response}
                    )
                    return False
                else:
                    self.log_test_result(
                        "Category Storage and Influence", 
                        False, 
                        f"Category stored but didn't influence content: tech_content={has_tech_content}, tech_tags={has_tech_tags}"
                    )
                    return False
            else:
                self.log_test_result("Category Storage and Influence", False, f"API call failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("Category Storage and Influence", False, f"Exception: {str(e)}")
            return False
    
    def test_category_comparison(self):
        """📊 TEST: Compare generation with and without category"""
        self.log("📊 Testing generation comparison with and without category...")
        
        if not self.auth_token:
            self.log_test_result("Category Comparison", False, "No auth token")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test same product with and without category
        base_data = {
            "product_name": "T-shirt Premium Coton",
            "product_description": "T-shirt unisexe en coton biologique, coupe moderne",
            "generate_image": False,
            "number_of_images": 0,
            "language": "fr"
        }
        
        try:
            # Test without category
            self.log("   Testing without category...")
            response_no_cat = self.session.post(f"{BASE_URL}/generate-sheet", json=base_data, headers=headers)
            
            if response_no_cat.status_code != 200:
                self.log_test_result("Category Comparison", False, f"No category test failed: {response_no_cat.status_code}")
                return False
            
            sheet_no_cat = response_no_cat.json()
            
            # Test with fashion category
            self.log("   Testing with 'mode' category...")
            cat_data = base_data.copy()
            cat_data["category"] = "mode"
            
            response_with_cat = self.session.post(f"{BASE_URL}/generate-sheet", json=cat_data, headers=headers)
            
            if response_with_cat.status_code != 200:
                self.log_test_result("Category Comparison", False, f"With category test failed: {response_with_cat.status_code}")
                return False
            
            sheet_with_cat = response_with_cat.json()
            
            # Compare results
            no_cat_tags = sheet_no_cat.get("seo_tags", [])
            with_cat_tags = sheet_with_cat.get("seo_tags", [])
            
            no_cat_title = sheet_no_cat.get("generated_title", "")
            with_cat_title = sheet_with_cat.get("generated_title", "")
            
            # Check for fashion indicators in category version
            fashion_indicators = ["style", "tendance", "mode", "fashion", "élégant", "design"]
            has_fashion_influence = any(indicator in with_cat_title.lower() for indicator in fashion_indicators) or \
                                  any(indicator in tag.lower() for tag in with_cat_tags for indicator in fashion_indicators)
            
            self.log(f"📊 Comparison Results:")
            self.log(f"   No category title: {no_cat_title}")
            self.log(f"   With category title: {with_cat_title}")
            self.log(f"   No category tags: {', '.join(no_cat_tags)}")
            self.log(f"   With category tags: {', '.join(with_cat_tags)}")
            self.log(f"   Fashion influence detected: {has_fashion_influence}")
            
            # Success if there's clear difference and fashion influence
            titles_different = no_cat_title != with_cat_title
            tags_different = set(no_cat_tags) != set(with_cat_tags)
            
            if titles_different and has_fashion_influence:
                self.log_test_result(
                    "Category Comparison", 
                    True, 
                    f"Category clearly influences generation: titles_different={titles_different}, fashion_influence={has_fashion_influence}",
                    {
                        "titles_different": titles_different,
                        "tags_different": tags_different,
                        "fashion_influence": has_fashion_influence
                    }
                )
                return True
            else:
                self.log_test_result(
                    "Category Comparison", 
                    False, 
                    f"Category doesn't show clear influence: titles_different={titles_different}, fashion_influence={has_fashion_influence}"
                )
                return False
                
        except Exception as e:
            self.log_test_result("Category Comparison", False, f"Exception: {str(e)}")
            return False
    
    def run_corrected_tests(self):
        """Run corrected tests based on actual API behavior"""
        self.log("🚀 STARTING CORRECTED CATEGORY & GPT-4 TURBO CORRECTIONS TESTING")
        self.log("=" * 80)
        
        tests = [
            ("Authentication Setup", self.setup_authentication),
            ("Number of Images Validation Fix", self.test_number_of_images_validation_fix),
            ("Target Audience String Conversion", self.test_target_audience_string_conversion),
            ("Category Storage and Influence", self.test_category_storage_and_influence),
            ("Category Comparison", self.test_category_comparison)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            self.log(f"\n🧪 Running: {test_name}")
            self.log("-" * 60)
            
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log(f"❌ Test {test_name} crashed: {str(e)}", "ERROR")
                failed += 1
            
            time.sleep(2)  # Brief pause between tests
        
        # Final summary
        self.log("\n" + "=" * 80)
        self.log("🎯 CORRECTED TESTING RESULTS SUMMARY")
        self.log("=" * 80)
        
        total = passed + failed
        success_rate = (passed / total * 100) if total > 0 else 0
        
        self.log(f"📊 OVERALL RESULTS: {passed}/{total} tests passed ({success_rate:.1f}% success rate)")
        
        self.log("\n📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            self.log(f"   {result['status']} {result['test']}: {result['details']}")
        
        self.log("\n🔍 KEY FINDINGS:")
        
        # Analyze key findings
        validation_fix = any(r["test"] == "Number of Images Validation Fix" and r["success"] for r in self.test_results)
        target_audience_fix = any(r["test"] == "Target Audience String Conversion" and r["success"] for r in self.test_results)
        category_feature = any(r["test"] == "Category Storage and Influence" and r["success"] for r in self.test_results)
        category_influence = any(r["test"] == "Category Comparison" and r["success"] for r in self.test_results)
        
        self.log(f"   🔧 number_of_images validation fix (ge=0): {'✅ WORKING' if validation_fix else '❌ BROKEN'}")
        self.log(f"   🎯 GPT-4 Turbo target_audience string fix: {'✅ WORKING' if target_audience_fix else '❌ BROKEN'}")
        self.log(f"   📱 Category storage feature: {'✅ WORKING' if category_feature else '❌ BROKEN'}")
        self.log(f"   📊 Category influences generation: {'✅ CONFIRMED' if category_influence else '❌ NOT DETECTED'}")
        
        return success_rate >= 60

if __name__ == "__main__":
    tester = CorrectedCategoryTester()
    success = tester.run_corrected_tests()
    exit(0 if success else 1)