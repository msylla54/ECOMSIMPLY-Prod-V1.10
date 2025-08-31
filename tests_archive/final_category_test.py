#!/usr/bin/env python3
"""
FINAL CATEGORY CORRECTIONS TESTING
==================================

Testing the specific corrections mentioned in the review request:
1. Category field added to ProductSheetRequest model
2. GPT-4 Turbo prompt clarification for target_audience as simple text
3. Category influence on SEO targeting and content generation
4. Custom category functionality
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"

class FinalCategoryTest:
    def __init__(self):
        self.auth_token = None
        self.test_results = []
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def authenticate(self):
        """Authenticate test user"""
        self.log("🔐 Setting up authentication...")
        
        # Try login first
        login_data = {
            "email": "final.test@example.com",
            "password": "FinalTest123!"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                self.auth_token = result.get("token")
                self.log(f"✅ User logged in successfully")
                return True
            else:
                # Try registration
                register_data = {
                    "email": "final.test@example.com",
                    "name": "Final Test User",
                    "password": "FinalTest123!"
                }
                response = requests.post(f"{BASE_URL}/auth/register", json=register_data, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    self.auth_token = result.get("token")
                    self.log(f"✅ User registered successfully")
                    return True
                else:
                    self.log(f"❌ Authentication failed: {response.status_code}")
                    return False
        except Exception as e:
            self.log(f"❌ Authentication error: {e}")
            return False
    
    def generate_sheet(self, product_name, description, category=None):
        """Generate product sheet with optional category"""
        request_data = {
            "product_name": product_name,
            "product_description": description,
            "generate_image": False,
            "number_of_images": 0,
            "language": "fr"
        }
        
        if category:
            request_data["category"] = category
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/generate-sheet", json=request_data, headers=headers, timeout=60)
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_category_storage(self):
        """Test 1: Category Storage and Response"""
        self.log("\n🧪 TEST 1: CATEGORY STORAGE AND RESPONSE")
        self.log("="*50)
        
        test_cases = [
            ("iPhone 15 Pro", "Smartphone haut de gamme avec processeur A17 Pro", "électronique"),
            ("T-shirt Premium", "T-shirt en coton bio de qualité supérieure", "mode"),
            ("Produit Custom", "Description de test pour catégorie personnalisée", "custom category here")
        ]
        
        results = []
        
        for product, description, category in test_cases:
            self.log(f"🔍 Testing: {product} with category '{category}'")
            
            result = self.generate_sheet(product, description, category)
            
            if result["success"]:
                data = result["data"]
                response_category = data.get("category")
                
                # Check if category is stored and returned
                category_stored = response_category is not None and response_category != ""
                
                test_result = {
                    "product": product,
                    "requested_category": category,
                    "response_category": response_category,
                    "category_stored": category_stored,
                    "success": category_stored
                }
                
                if category_stored:
                    self.log(f"✅ Category stored: {response_category}")
                else:
                    self.log(f"❌ Category NOT stored - Response: {response_category}")
                
                results.append(test_result)
            else:
                self.log(f"❌ Generation failed: {result['error']}")
                results.append({"product": product, "success": False, "error": result["error"]})
        
        success_count = sum(1 for r in results if r.get("success", False))
        self.log(f"\n📊 CATEGORY STORAGE RESULTS: {success_count}/{len(test_cases)} successful")
        
        self.test_results.append({
            "test_name": "Category Storage",
            "success_rate": success_count / len(test_cases) * 100,
            "details": results
        })
        
        return results
    
    def test_target_audience_format(self):
        """Test 2: Target Audience Format"""
        self.log("\n🧪 TEST 2: TARGET AUDIENCE FORMAT")
        self.log("="*50)
        
        test_cases = [
            ("MacBook Pro", "Ordinateur portable professionnel haute performance", "électronique"),
            ("Robe Élégante", "Robe de soirée en soie naturelle", "mode")
        ]
        
        results = []
        
        for product, description, category in test_cases:
            self.log(f"🔍 Testing: {product}")
            
            result = self.generate_sheet(product, description, category)
            
            if result["success"]:
                data = result["data"]
                target_audience = data.get("target_audience", "")
                
                # Check if target_audience is simple text (not JSON)
                is_simple_text = True
                is_json_like = False
                
                # Check for JSON-like structures
                if "{" in target_audience and "}" in target_audience:
                    is_json_like = True
                    is_simple_text = False
                
                try:
                    # Try to parse as JSON
                    parsed = json.loads(target_audience)
                    if isinstance(parsed, (dict, list)):
                        is_json_like = True
                        is_simple_text = False
                except:
                    pass  # Good - it's not JSON
                
                test_result = {
                    "product": product,
                    "target_audience": target_audience[:100] + "..." if len(target_audience) > 100 else target_audience,
                    "is_simple_text": is_simple_text,
                    "is_json_like": is_json_like,
                    "success": is_simple_text
                }
                
                if is_simple_text:
                    self.log(f"✅ Target audience is simple text")
                else:
                    self.log(f"❌ Target audience appears to be JSON-like")
                
                results.append(test_result)
            else:
                self.log(f"❌ Generation failed: {result['error']}")
                results.append({"product": product, "success": False, "error": result["error"]})
        
        success_count = sum(1 for r in results if r.get("success", False))
        self.log(f"\n📊 TARGET AUDIENCE FORMAT RESULTS: {success_count}/{len(test_cases)} successful")
        
        self.test_results.append({
            "test_name": "Target Audience Format",
            "success_rate": success_count / len(test_cases) * 100,
            "details": results
        })
        
        return results
    
    def test_category_influence(self):
        """Test 3: Category Influence on Content"""
        self.log("\n🧪 TEST 3: CATEGORY INFLUENCE ON CONTENT")
        self.log("="*50)
        
        product = "iPhone 15 Pro"
        description = "Smartphone haut de gamme avec processeur A17 Pro et appareil photo 48MP"
        
        self.log("🔍 Generating WITHOUT category...")
        result_without = self.generate_sheet(product, description, None)
        
        self.log("🔍 Generating WITH electronics category...")
        result_with = self.generate_sheet(product, description, "électronique")
        
        if result_without["success"] and result_with["success"]:
            data_without = result_without["data"]
            data_with = result_with["data"]
            
            # Compare key fields
            differences = {
                "title": data_without.get("generated_title") != data_with.get("generated_title"),
                "description": data_without.get("marketing_description") != data_with.get("marketing_description"),
                "seo_tags": set(data_without.get("seo_tags", [])) != set(data_with.get("seo_tags", [])),
                "features": data_without.get("key_features") != data_with.get("key_features"),
                "target_audience": data_without.get("target_audience") != data_with.get("target_audience")
            }
            
            differences_count = sum(differences.values())
            
            self.log(f"📊 Differences found: {differences_count}/5 fields")
            self.log(f"🔍 Title different: {'✅' if differences['title'] else '❌'}")
            self.log(f"🔍 SEO tags different: {'✅' if differences['seo_tags'] else '❌'}")
            self.log(f"🔍 Target audience different: {'✅' if differences['target_audience'] else '❌'}")
            
            # Show specific differences
            self.log(f"\n📋 WITHOUT category - Title: {data_without.get('generated_title', '')}")
            self.log(f"📋 WITH category - Title: {data_with.get('generated_title', '')}")
            self.log(f"🏷️ WITHOUT category - SEO: {data_without.get('seo_tags', [])}")
            self.log(f"🏷️ WITH category - SEO: {data_with.get('seo_tags', [])}")
            
            # Category influence is successful if at least 3 fields are different
            influence_success = differences_count >= 3
            
            test_result = {
                "differences_count": differences_count,
                "total_fields": 5,
                "success": influence_success,
                "details": differences
            }
            
            if influence_success:
                self.log(f"✅ Category clearly influences content generation")
            else:
                self.log(f"❌ Category influence not significant enough")
        else:
            self.log(f"❌ Comparison failed - generation errors")
            test_result = {"success": False, "error": "Generation failed"}
        
        self.test_results.append({
            "test_name": "Category Influence",
            "success_rate": 100 if test_result.get("success", False) else 0,
            "details": test_result
        })
        
        return test_result
    
    def test_custom_category(self):
        """Test 4: Custom Category Functionality"""
        self.log("\n🧪 TEST 4: CUSTOM CATEGORY FUNCTIONALITY")
        self.log("="*50)
        
        custom_categories = [
            "produits bio et naturels",
            "équipement sportif professionnel",
            "gadgets technologiques innovants"
        ]
        
        results = []
        
        for category in custom_categories:
            self.log(f"🔍 Testing custom category: {category}")
            
            result = self.generate_sheet("Produit Test", f"Produit de test pour {category}", category)
            
            if result["success"]:
                data = result["data"]
                
                # Check if content reflects the custom category
                title = data.get("generated_title", "").lower()
                seo_tags = [tag.lower() for tag in data.get("seo_tags", [])]
                
                # Look for category-related keywords
                category_words = category.lower().split()
                content_text = f"{title} {' '.join(seo_tags)}"
                
                keyword_matches = sum(1 for word in category_words if word in content_text)
                adaptation_score = keyword_matches / len(category_words) * 100 if category_words else 0
                
                test_result = {
                    "category": category,
                    "keyword_matches": keyword_matches,
                    "total_keywords": len(category_words),
                    "adaptation_score": adaptation_score,
                    "success": adaptation_score > 25,  # At least 25% keyword match
                    "title": data.get("generated_title", "")
                }
                
                if test_result["success"]:
                    self.log(f"✅ Custom category adapted (score: {adaptation_score:.1f}%)")
                else:
                    self.log(f"❌ Custom category poorly adapted (score: {adaptation_score:.1f}%)")
                
                results.append(test_result)
            else:
                self.log(f"❌ Generation failed: {result['error']}")
                results.append({"category": category, "success": False, "error": result["error"]})
        
        success_count = sum(1 for r in results if r.get("success", False))
        self.log(f"\n📊 CUSTOM CATEGORY RESULTS: {success_count}/{len(custom_categories)} successful")
        
        self.test_results.append({
            "test_name": "Custom Category",
            "success_rate": success_count / len(custom_categories) * 100,
            "details": results
        })
        
        return results
    
    def print_final_summary(self):
        """Print final test summary"""
        self.log("\n" + "="*60)
        self.log("🎯 FINAL CATEGORY CORRECTIONS TEST SUMMARY")
        self.log("="*60)
        
        if not self.test_results:
            self.log("❌ No tests completed")
            return
        
        overall_success = sum(r["success_rate"] for r in self.test_results) / len(self.test_results)
        
        self.log(f"\n📊 OVERALL SUCCESS RATE: {overall_success:.1f}%")
        
        self.log(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success_rate"] >= 80 else "⚠️" if result["success_rate"] >= 50 else "❌"
            self.log(f"{status} {result['test_name']}: {result['success_rate']:.1f}%")
        
        # Evaluate success criteria from review request
        self.log(f"\n🎯 SUCCESS CRITERIA EVALUATION:")
        
        criteria_results = []
        
        # Criterion 1: Category storage
        category_test = next((r for r in self.test_results if "Category Storage" in r["test_name"]), None)
        if category_test and category_test["success_rate"] >= 80:
            self.log("✅ Category field storage and response working")
            criteria_results.append(True)
        else:
            self.log("❌ Category field storage and response failing")
            criteria_results.append(False)
        
        # Criterion 2: Target audience format
        audience_test = next((r for r in self.test_results if "Target Audience" in r["test_name"]), None)
        if audience_test and audience_test["success_rate"] >= 80:
            self.log("✅ Target audience is simple text (not JSON)")
            criteria_results.append(True)
        else:
            self.log("❌ Target audience still JSON format")
            criteria_results.append(False)
        
        # Criterion 3: Category influence
        influence_test = next((r for r in self.test_results if "Category Influence" in r["test_name"]), None)
        if influence_test and influence_test["success_rate"] >= 80:
            self.log("✅ Category clearly influences SEO and content")
            criteria_results.append(True)
        else:
            self.log("❌ Category influence not significant")
            criteria_results.append(False)
        
        # Criterion 4: Custom categories
        custom_test = next((r for r in self.test_results if "Custom Category" in r["test_name"]), None)
        if custom_test and custom_test["success_rate"] >= 80:
            self.log("✅ Custom category functionality working")
            criteria_results.append(True)
        else:
            self.log("❌ Custom category functionality failing")
            criteria_results.append(False)
        
        success_criteria_met = sum(criteria_results)
        self.log(f"\n🏆 SUCCESS CRITERIA MET: {success_criteria_met}/4")
        
        if success_criteria_met == 4:
            self.log("🎉 ALL CORRECTIONS SUCCESSFULLY IMPLEMENTED!")
        elif success_criteria_met >= 3:
            self.log("⚠️ Most corrections working, minor issues remain")
        else:
            self.log("❌ CRITICAL ISSUES - Major corrections still needed")
        
        return overall_success, success_criteria_met
    
    def run_all_tests(self):
        """Run all category correction tests"""
        self.log("🚀 STARTING FINAL CATEGORY CORRECTIONS TESTING")
        self.log("="*60)
        
        # Authentication
        if not self.authenticate():
            self.log("❌ Authentication failed - cannot proceed")
            return
        
        # Run all tests
        try:
            self.test_category_storage()
            self.test_target_audience_format()
            self.test_category_influence()
            self.test_custom_category()
            
            # Final summary
            overall_success, criteria_met = self.print_final_summary()
            
            return overall_success, criteria_met
            
        except Exception as e:
            self.log(f"❌ Test execution error: {e}")
            return 0, 0

def main():
    """Main test execution"""
    tester = FinalCategoryTest()
    overall_success, criteria_met = tester.run_all_tests()
    
    # Return exit code based on results
    if criteria_met >= 3:
        exit(0)  # Success
    else:
        exit(1)  # Failure

if __name__ == "__main__":
    main()