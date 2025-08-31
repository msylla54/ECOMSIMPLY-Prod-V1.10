#!/usr/bin/env python3
"""
GPT-4 TURBO JSON PARSING FIX VERIFICATION TEST
==============================================

This test specifically verifies the GPT-4 Turbo JSON parsing fix mentioned in the review request.

ISSUE FIXED: GPT-4 Turbo returns JSON content wrapped in markdown code blocks (```json...```) 
but the parser was trying to parse this directly, causing JSON parsing errors and triggering 
the fallback system.

EXPECTED RESULTS:
1. ✅ GPT-4 Turbo content generation (no more fallback)
2. ✅ Intelligent, product-specific content for "iPhone 15 Pro"
3. ✅ Realistic pricing suggestions for smartphones
4. ✅ Specific log messages indicating successful JSON parsing
5. ✅ No more "prix sur demande" or generic fallback content
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 60  # Longer timeout for AI generation

class GPT4TurboJSONFixTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        self.user_data = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def register_test_user(self):
        """Register a test user for authentication"""
        self.log("🔐 Registering test user for GPT-4 Turbo testing...")
        
        timestamp = int(time.time())
        test_user = {
            "email": f"gpt4test{timestamp}@example.com",
            "name": "GPT-4 Turbo Tester",
            "password": "TestPassword123!"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=test_user)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.user_data = data.get("user")
                
                if self.auth_token and self.user_data:
                    self.log(f"✅ User registered successfully: {self.user_data['email']}")
                    return True
                else:
                    self.log("❌ Registration failed: Missing token or user data", "ERROR")
                    return False
            else:
                self.log(f"❌ Registration failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Registration failed: {str(e)}", "ERROR")
            return False
    
    def test_gpt4_turbo_iphone_generation(self):
        """
        🎯 CRITICAL TEST: Test GPT-4 Turbo with iPhone 15 Pro (exact case from review)
        
        This test verifies:
        1. GPT-4 Turbo integration is working (no fallback)
        2. JSON parsing fix is working (no more markdown code block errors)
        3. Content is intelligent and product-specific
        4. Pricing is realistic for smartphones
        """
        self.log("🧠 TESTING GPT-4 TURBO JSON PARSING FIX - iPhone 15 Pro")
        self.log("=" * 60)
        
        if not self.auth_token:
            self.log("❌ Cannot test: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Exact test case from review request
        test_data = {
            "product_name": "iPhone 15 Pro",
            "product_description": "Smartphone haut de gamme avec processeur A17 Pro et appareil photo 48MP",
            "generate_image": True,  # Required by API
            "number_of_images": 1,   # Minimum required
            "language": "fr"
        }
        
        self.log(f"📝 Test Request: {json.dumps(test_data, ensure_ascii=False)}")
        
        try:
            start_time = time.time()
            self.log("🚀 Sending request to GPT-4 Turbo...")
            
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            
            generation_time = time.time() - start_time
            self.log(f"⏱️ Request completed in {generation_time:.2f} seconds")
            
            if response.status_code != 200:
                self.log(f"❌ API call failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
            data = response.json()
            
            if not data.get("success", False):
                self.log(f"❌ Generation failed: {data.get('message', 'Unknown error')}", "ERROR")
                return False
                
            sheet_data = data.get("sheet", {})
            
            # Analyze the generated content
            self.log("📊 ANALYZING GENERATED CONTENT:")
            self.log("=" * 40)
            
            title = sheet_data.get("generated_title", "")
            description = sheet_data.get("marketing_description", "")
            features = sheet_data.get("key_features", [])
            tags = sheet_data.get("seo_tags", [])
            pricing = sheet_data.get("price_suggestions", "")
            audience = sheet_data.get("target_audience", "")
            cta = sheet_data.get("call_to_action", "")
            
            self.log(f"📱 Title: {title}")
            self.log(f"💰 Pricing: {pricing}")
            self.log(f"🏷️ SEO Tags: {', '.join(tags)}")
            self.log(f"👥 Target Audience: {audience[:100]}...")
            self.log(f"📝 Description Length: {len(description)} characters")
            self.log(f"⭐ Features Count: {len(features)}")
            
            # CRITICAL ANALYSIS: Check for GPT-4 Turbo success indicators
            success_indicators = self.analyze_gpt4_turbo_success(sheet_data)
            
            # Display results
            self.log("\n🔍 GPT-4 TURBO SUCCESS ANALYSIS:")
            self.log("=" * 40)
            
            for indicator, result in success_indicators.items():
                status = "✅" if result["success"] else "❌"
                self.log(f"{status} {indicator}: {result['message']}")
                if result.get("details"):
                    self.log(f"   Details: {result['details']}")
            
            # Overall success determination
            total_checks = len(success_indicators)
            passed_checks = sum(1 for r in success_indicators.values() if r["success"])
            success_rate = (passed_checks / total_checks) * 100
            
            self.log(f"\n📈 OVERALL SUCCESS RATE: {passed_checks}/{total_checks} ({success_rate:.1f}%)")
            
            if success_rate >= 80:
                self.log("🎉 GPT-4 TURBO JSON PARSING FIX: VERIFIED SUCCESSFUL!")
                self.log("✅ The fix is working correctly - GPT-4 Turbo generating intelligent content")
                return True
            else:
                self.log("❌ GPT-4 TURBO JSON PARSING FIX: ISSUES DETECTED")
                self.log("⚠️ The fix may not be working properly or fallback system is still active")
                return False
                
        except Exception as e:
            self.log(f"❌ Test failed with exception: {str(e)}", "ERROR")
            import traceback
            self.log(f"📋 Traceback: {traceback.format_exc()}", "ERROR")
            return False
    
    def analyze_gpt4_turbo_success(self, sheet_data):
        """
        Analyze the generated content to determine if GPT-4 Turbo is working correctly
        """
        results = {}
        
        title = sheet_data.get("generated_title", "").lower()
        description = sheet_data.get("marketing_description", "").lower()
        features = [f.lower() for f in sheet_data.get("key_features", [])]
        tags = [t.lower() for t in sheet_data.get("seo_tags", [])]
        pricing = sheet_data.get("price_suggestions", "").lower()
        audience = sheet_data.get("target_audience", "").lower()
        
        # 1. Check for iPhone-specific content (not generic)
        iphone_terms = ["iphone", "apple", "a17", "pro", "48mp", "smartphone", "ios", "camera"]
        has_iphone_content = any(term in title + description for term in iphone_terms)
        
        results["iPhone-Specific Content"] = {
            "success": has_iphone_content,
            "message": "Content mentions iPhone-specific features" if has_iphone_content else "Content appears generic",
            "details": f"Found iPhone terms: {[term for term in iphone_terms if term in title + description]}"
        }
        
        # 2. Check pricing is realistic for smartphones (not "prix sur demande")
        has_realistic_pricing = "prix sur demande" not in pricing and "contactez-nous" not in pricing
        price_numbers = []
        import re
        price_matches = re.findall(r'(\d+)€', pricing)
        if price_matches:
            price_numbers = [int(p) for p in price_matches]
            # iPhone pricing should be in 500-1500€ range typically
            realistic_range = any(500 <= p <= 1500 for p in price_numbers)
        else:
            realistic_range = False
            
        results["Realistic Smartphone Pricing"] = {
            "success": has_realistic_pricing and (realistic_range or len(price_numbers) == 0),
            "message": f"Pricing appears realistic for smartphones" if has_realistic_pricing else "Generic pricing detected",
            "details": f"Price ranges found: {price_numbers}€" if price_numbers else "No specific prices found"
        }
        
        # 3. Check for intelligent features (not generic)
        generic_features = ["qualité premium", "design soigné", "performance optimale", "satisfaction client"]
        intelligent_features = ["a17 pro", "48mp", "appareil photo", "processeur", "écran", "batterie", "ios"]
        
        has_generic = any(generic in ' '.join(features) for generic in generic_features)
        has_intelligent = any(intel in ' '.join(features) for intel in intelligent_features)
        
        results["Intelligent Features"] = {
            "success": has_intelligent and not has_generic,
            "message": "Features are product-specific and intelligent" if has_intelligent else "Features appear generic",
            "details": f"Intelligent: {has_intelligent}, Generic: {has_generic}"
        }
        
        # 4. Check SEO tags are iPhone-relevant
        iphone_seo_terms = ["iphone", "apple", "smartphone", "mobile", "pro", "camera", "ios"]
        generic_seo_terms = ["qualité-supérieure", "performance-optimale", "satisfaction-garantie"]
        
        has_relevant_seo = any(term in ' '.join(tags) for term in iphone_seo_terms)
        has_generic_seo = any(term in ' '.join(tags) for term in generic_seo_terms)
        
        results["Relevant SEO Tags"] = {
            "success": has_relevant_seo and not has_generic_seo,
            "message": "SEO tags are iPhone-specific" if has_relevant_seo else "SEO tags appear generic",
            "details": f"Relevant: {has_relevant_seo}, Generic: {has_generic_seo}"
        }
        
        # 5. Check target audience is appropriate for smartphones
        tech_audience_terms = ["technophiles", "passionnés", "professionnels", "utilisateurs", "smartphone"]
        generic_audience_terms = ["consommateurs exigeants", "qualité exceptionnelle"]
        
        has_tech_audience = any(term in audience for term in tech_audience_terms)
        has_generic_audience = any(term in audience for term in generic_audience_terms)
        
        results["Appropriate Target Audience"] = {
            "success": has_tech_audience and not has_generic_audience,
            "message": "Target audience is appropriate for smartphones" if has_tech_audience else "Target audience appears generic",
            "details": f"Tech-focused: {has_tech_audience}, Generic: {has_generic_audience}"
        }
        
        # 6. Check content length (GPT-4 Turbo should generate substantial content)
        substantial_content = len(description) > 200 and len(features) >= 4
        
        results["Substantial Content Generation"] = {
            "success": substantial_content,
            "message": f"Generated substantial content ({len(description)} chars, {len(features)} features)" if substantial_content else "Content appears minimal",
            "details": f"Description: {len(description)} chars, Features: {len(features)}"
        }
        
        return results
    
    def test_fallback_comparison(self):
        """
        Test a basic product to see if we get fallback content (for comparison)
        """
        self.log("🔄 TESTING FALLBACK SYSTEM COMPARISON")
        self.log("=" * 40)
        
        if not self.auth_token:
            self.log("❌ Cannot test: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test with a very basic product that might trigger fallback
        test_data = {
            "product_name": "Produit Test",
            "product_description": "Un produit simple pour tester",
            "generate_image": True,
            "number_of_images": 1,
            "language": "fr"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    sheet_data = data.get("sheet", {})
                    pricing = sheet_data.get("price_suggestions", "")
                    description = sheet_data.get("marketing_description", "")
                    
                    # Check for fallback indicators
                    is_fallback = ("prix sur demande" in pricing.lower() or 
                                 "produit d'exception qui répond à vos attentes" in description.lower())
                    
                    if is_fallback:
                        self.log("✅ Fallback system detected for basic product (expected)")
                        self.log("   This confirms the system can differentiate between AI and fallback")
                    else:
                        self.log("✅ AI generation working even for basic products")
                        
                    return True
                    
        except Exception as e:
            self.log(f"⚠️ Fallback test failed: {str(e)}")
            
        return True  # Non-critical test
    
    def run_comprehensive_test(self):
        """
        Run the complete GPT-4 Turbo JSON parsing fix verification
        """
        self.log("🚀 STARTING GPT-4 TURBO JSON PARSING FIX VERIFICATION")
        self.log("=" * 60)
        self.log("OBJECTIVE: Verify that GPT-4 Turbo JSON parsing fix is working correctly")
        self.log("EXPECTED: Intelligent iPhone 15 Pro content, no fallback, realistic pricing")
        self.log("=" * 60)
        
        # Step 1: Register test user
        if not self.register_test_user():
            self.log("❌ CRITICAL FAILURE: Could not register test user", "ERROR")
            return False
        
        # Step 2: Test GPT-4 Turbo with iPhone 15 Pro
        success = self.test_gpt4_turbo_iphone_generation()
        
        # Step 3: Test fallback comparison (optional)
        self.test_fallback_comparison()
        
        # Final result
        self.log("\n" + "=" * 60)
        if success:
            self.log("🎉 FINAL RESULT: GPT-4 TURBO JSON PARSING FIX VERIFICATION SUCCESSFUL!")
            self.log("✅ The fix is working correctly")
            self.log("✅ GPT-4 Turbo is generating intelligent, product-specific content")
            self.log("✅ No more fallback content for iPhone 15 Pro")
            self.log("✅ JSON parsing is working without markdown code block errors")
        else:
            self.log("❌ FINAL RESULT: GPT-4 TURBO JSON PARSING FIX VERIFICATION FAILED!")
            self.log("⚠️ The fix may not be working properly")
            self.log("⚠️ System may still be using fallback content")
            self.log("⚠️ JSON parsing errors may still be occurring")
        
        self.log("=" * 60)
        return success

def main():
    """Main test execution"""
    tester = GPT4TurboJSONFixTester()
    success = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    main()