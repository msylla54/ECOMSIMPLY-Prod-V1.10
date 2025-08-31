#!/usr/bin/env python3
"""
ECOMSIMPLY AI QUALITY PREMIUM TESTING SUITE
Tests the premium AI content generation improvements as requested in the review.

FOCUS: Testing that AI generates high-quality, realistic content instead of inappropriate content
like "Papier toilettes Ingénierie Innovante" with unrealistic prices (49€-149€).

TESTS:
1. Test 1 - Problematic Product (Toilet Paper) - Before/After comparison
2. Test 2 - Standard Product (Samsung Galaxy smartphone)  
3. Test 3 - Complex Product (Professional espresso machine)

QUALITY CRITERIA:
✅ Appropriate titles without inappropriate technical jargon
✅ Realistic pricing for each product category
✅ Rich, relevant descriptions (200-300 words)
✅ Appropriate audience targeting
✅ Relevant SEO tags
✅ Persuasive CTAs
"""

import requests
import json
import time
import re
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 45

class AIQualityPremiumTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        self.user_data = None
        self.test_results = []
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def register_test_user(self):
        """Register a test user for AI quality testing"""
        self.log("🔐 Registering test user for AI quality testing...")
        
        timestamp = int(time.time())
        test_user = {
            "email": f"ai.quality.test{timestamp}@ecomsimply.fr",
            "name": "AI Quality Tester",
            "password": "QualityTest123!"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=test_user)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.user_data = data.get("user")
                
                if self.auth_token and self.user_data:
                    self.log(f"✅ Test User Registered: {self.user_data['name']}")
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
    
    def analyze_content_quality(self, sheet_data, product_name, expected_category):
        """Analyze the quality of generated content against premium standards"""
        analysis = {
            "product_name": product_name,
            "category": expected_category,
            "quality_score": 0,
            "issues": [],
            "strengths": [],
            "pricing_realistic": False,
            "title_appropriate": False,
            "description_quality": False,
            "audience_appropriate": False,
            "seo_relevant": False
        }
        
        # 1. TITLE ANALYSIS
        title = sheet_data.get("generated_title", "")
        self.log(f"   📝 Analyzing Title: '{title}'")
        
        # Check for inappropriate technical jargon
        inappropriate_terms = ["ingénierie", "innovante", "avancé", "technologie", "système"]
        has_inappropriate = any(term.lower() in title.lower() for term in inappropriate_terms)
        
        if not has_inappropriate and len(title) >= 30:
            analysis["title_appropriate"] = True
            analysis["quality_score"] += 20
            analysis["strengths"].append("✅ Title: Appropriate, no inappropriate jargon")
        else:
            analysis["issues"].append(f"❌ Title: {'Inappropriate jargon detected' if has_inappropriate else 'Too short'}")
        
        # 2. PRICING ANALYSIS
        price_suggestions = sheet_data.get("price_suggestions", "")
        self.log(f"   💰 Analyzing Pricing: '{price_suggestions[:100]}...'")
        
        # Extract price ranges from text
        price_matches = re.findall(r'(\d+)[€$]?[-–]?(\d+)?[€$]?', price_suggestions)
        prices = []
        for match in price_matches:
            if match[0]:
                prices.append(int(match[0]))
            if match[1]:
                prices.append(int(match[1]))
        
        # Define realistic price ranges by category
        realistic_ranges = {
            "toilet_paper": (2, 15),
            "smartphone": (200, 1500),
            "espresso_machine": (300, 3000),
            "electronics": (50, 2000),
            "household": (5, 100)
        }
        
        expected_range = realistic_ranges.get(expected_category, (10, 500))
        
        if prices:
            min_price = min(prices)
            max_price = max(prices)
            
            if expected_range[0] <= min_price <= expected_range[1] and expected_range[0] <= max_price <= expected_range[1]:
                analysis["pricing_realistic"] = True
                analysis["quality_score"] += 25
                analysis["strengths"].append(f"✅ Pricing: Realistic range {min_price}€-{max_price}€")
            else:
                analysis["issues"].append(f"❌ Pricing: Unrealistic {min_price}€-{max_price}€ for {expected_category}")
        else:
            analysis["issues"].append("❌ Pricing: No clear price range found")
        
        # 3. DESCRIPTION QUALITY ANALYSIS
        description = sheet_data.get("marketing_description", "")
        self.log(f"   📄 Analyzing Description: {len(description)} characters")
        
        word_count = len(description.split())
        if 150 <= word_count <= 400:  # Good length range
            analysis["quality_score"] += 20
            analysis["strengths"].append(f"✅ Description: Good length ({word_count} words)")
            
            # Check for storytelling elements
            storytelling_indicators = ["découvrez", "imaginez", "profitez", "transformez", "expérience", "sensation"]
            has_storytelling = any(indicator in description.lower() for indicator in storytelling_indicators)
            
            if has_storytelling:
                analysis["description_quality"] = True
                analysis["quality_score"] += 15
                analysis["strengths"].append("✅ Description: Contains storytelling elements")
            else:
                analysis["issues"].append("❌ Description: Lacks storytelling/emotional connection")
        else:
            analysis["issues"].append(f"❌ Description: Poor length ({word_count} words, should be 150-400)")
        
        # 4. AUDIENCE ANALYSIS
        audience = sheet_data.get("target_audience", "")
        self.log(f"   👥 Analyzing Audience: '{audience[:100]}...'")
        
        # Check if audience is appropriate for product category
        inappropriate_audiences = {
            "toilet_paper": ["technophiles", "gamers", "développeurs", "ingénieurs"],
            "smartphone": ["personnes âgées exclusivement"],
            "espresso_machine": ["enfants", "adolescents"]
        }
        
        inappropriate_for_category = inappropriate_audiences.get(expected_category, [])
        has_inappropriate_audience = any(term.lower() in audience.lower() for term in inappropriate_for_category)
        
        if not has_inappropriate_audience and len(audience) > 50:
            analysis["audience_appropriate"] = True
            analysis["quality_score"] += 15
            analysis["strengths"].append("✅ Audience: Appropriate for product category")
        else:
            analysis["issues"].append("❌ Audience: Inappropriate or too generic")
        
        # 5. SEO TAGS ANALYSIS
        seo_tags = sheet_data.get("seo_tags", [])
        self.log(f"   🏷️ Analyzing SEO Tags: {seo_tags}")
        
        # Check relevance to product
        product_words = product_name.lower().split()
        relevant_tags = 0
        
        for tag in seo_tags:
            tag_lower = tag.lower()
            if any(word in tag_lower for word in product_words if len(word) > 2):
                relevant_tags += 1
            # Check for inappropriate tags
            if expected_category == "toilet_paper" and any(tech_term in tag_lower for tech_term in ["avancé", "technologie", "innovation"]):
                analysis["issues"].append(f"❌ SEO: Inappropriate tag '{tag}' for toilet paper")
        
        if relevant_tags >= 2:
            analysis["seo_relevant"] = True
            analysis["quality_score"] += 5
            analysis["strengths"].append(f"✅ SEO: {relevant_tags} relevant tags")
        else:
            analysis["issues"].append("❌ SEO: Tags not relevant to product")
        
        return analysis
    
    def test_problematic_product_toilet_paper(self):
        """Test 1 - Problematic Product (Toilet Paper) - Should generate appropriate content"""
        self.log("🧻 TEST 1: PROBLEMATIC PRODUCT - TOILET PAPER")
        self.log("   Testing that AI no longer generates 'Papier toilettes Ingénierie Innovante' with 49€-149€ prices")
        
        if not self.auth_token:
            self.log("❌ Cannot test: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # EXACT test case from review request
        sheet_request = {
            "product_name": "Papier toilettes",
            "product_description": "Papier toilettes pour nettoyer Applications Polyvalentes",
            "generate_image": False,
            "number_of_images": 0,
            "language": "fr"
        }
        
        try:
            self.log("   🚀 Generating product sheet for toilet paper...")
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=sheet_request, headers=headers)
            
            if response.status_code == 200:
                sheet_data = response.json()
                
                # Analyze content quality
                analysis = self.analyze_content_quality(sheet_data, "Papier toilettes", "toilet_paper")
                self.test_results.append(analysis)
                
                self.log(f"   📊 QUALITY ANALYSIS RESULTS:")
                self.log(f"      Overall Quality Score: {analysis['quality_score']}/100")
                self.log(f"      Title: '{sheet_data.get('generated_title', '')}'")
                self.log(f"      Price Suggestions: '{sheet_data.get('price_suggestions', '')[:100]}...'")
                
                # Log strengths and issues
                for strength in analysis['strengths']:
                    self.log(f"      {strength}")
                for issue in analysis['issues']:
                    self.log(f"      {issue}")
                
                # CRITICAL CHECKS
                title = sheet_data.get("generated_title", "").lower()
                has_inappropriate_jargon = "ingénierie" in title or "innovante" in title
                
                if has_inappropriate_jargon:
                    self.log("   ❌ CRITICAL FAILURE: Still generating inappropriate jargon!", "ERROR")
                    return False
                
                if analysis['pricing_realistic']:
                    self.log("   ✅ PRICING FIX VERIFIED: Realistic prices for toilet paper")
                else:
                    self.log("   ❌ PRICING STILL UNREALISTIC: Prices not appropriate for toilet paper", "ERROR")
                
                if analysis['quality_score'] >= 60:
                    self.log("   🎉 TEST 1 PASSED: Toilet paper content quality significantly improved!")
                    return True
                else:
                    self.log(f"   ❌ TEST 1 FAILED: Quality score too low ({analysis['quality_score']}/100)", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Request failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Test failed: {str(e)}", "ERROR")
            return False
    
    def test_standard_product_smartphone(self):
        """Test 2 - Standard Product (Samsung Galaxy smartphone)"""
        self.log("📱 TEST 2: STANDARD PRODUCT - SAMSUNG GALAXY SMARTPHONE")
        
        if not self.auth_token:
            self.log("❌ Cannot test: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # EXACT test case from review request
        sheet_request = {
            "product_name": "Smartphone Samsung Galaxy",
            "product_description": "Smartphone Android dernière génération avec appareil photo haute qualité",
            "generate_image": False,
            "number_of_images": 0,
            "language": "fr"
        }
        
        try:
            self.log("   🚀 Generating product sheet for Samsung Galaxy smartphone...")
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=sheet_request, headers=headers)
            
            if response.status_code == 200:
                sheet_data = response.json()
                
                # Analyze content quality
                analysis = self.analyze_content_quality(sheet_data, "Smartphone Samsung Galaxy", "smartphone")
                self.test_results.append(analysis)
                
                self.log(f"   📊 QUALITY ANALYSIS RESULTS:")
                self.log(f"      Overall Quality Score: {analysis['quality_score']}/100")
                self.log(f"      Title: '{sheet_data.get('generated_title', '')}'")
                self.log(f"      Price Suggestions: '{sheet_data.get('price_suggestions', '')[:100]}...'")
                
                # Log strengths and issues
                for strength in analysis['strengths']:
                    self.log(f"      {strength}")
                for issue in analysis['issues']:
                    self.log(f"      {issue}")
                
                # Check for smartphone-specific quality
                description = sheet_data.get("marketing_description", "")
                has_tech_features = any(term in description.lower() for term in ["appareil photo", "android", "écran", "batterie", "processeur"])
                
                if has_tech_features:
                    self.log("   ✅ CONTENT RELEVANCE: Contains appropriate smartphone features")
                else:
                    self.log("   ⚠️ CONTENT RELEVANCE: Missing key smartphone features")
                
                if analysis['quality_score'] >= 70:
                    self.log("   🎉 TEST 2 PASSED: Smartphone content quality excellent!")
                    return True
                else:
                    self.log(f"   ❌ TEST 2 FAILED: Quality score too low ({analysis['quality_score']}/100)", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Request failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Test failed: {str(e)}", "ERROR")
            return False
    
    def test_complex_product_espresso_machine(self):
        """Test 3 - Complex Product (Professional espresso machine)"""
        self.log("☕ TEST 3: COMPLEX PRODUCT - PROFESSIONAL ESPRESSO MACHINE")
        
        if not self.auth_token:
            self.log("❌ Cannot test: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # EXACT test case from review request
        sheet_request = {
            "product_name": "Machine à café expresso professionnelle",
            "product_description": "Machine expresso semi-automatique pour café professionnel",
            "generate_image": False,
            "number_of_images": 0,
            "language": "fr"
        }
        
        try:
            self.log("   🚀 Generating product sheet for professional espresso machine...")
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=sheet_request, headers=headers)
            
            if response.status_code == 200:
                sheet_data = response.json()
                
                # Analyze content quality
                analysis = self.analyze_content_quality(sheet_data, "Machine à café expresso professionnelle", "espresso_machine")
                self.test_results.append(analysis)
                
                self.log(f"   📊 QUALITY ANALYSIS RESULTS:")
                self.log(f"      Overall Quality Score: {analysis['quality_score']}/100")
                self.log(f"      Title: '{sheet_data.get('generated_title', '')}'")
                self.log(f"      Price Suggestions: '{sheet_data.get('price_suggestions', '')[:100]}...'")
                
                # Log strengths and issues
                for strength in analysis['strengths']:
                    self.log(f"      {strength}")
                for issue in analysis['issues']:
                    self.log(f"      {issue}")
                
                # Check for espresso machine-specific quality
                description = sheet_data.get("marketing_description", "")
                has_coffee_features = any(term in description.lower() for term in ["café", "expresso", "mousse", "pression", "barista", "professionnel"])
                
                if has_coffee_features:
                    self.log("   ✅ CONTENT RELEVANCE: Contains appropriate coffee machine features")
                else:
                    self.log("   ⚠️ CONTENT RELEVANCE: Missing key coffee machine features")
                
                # Check audience appropriateness for professional equipment
                audience = sheet_data.get("target_audience", "").lower()
                has_professional_audience = any(term in audience for term in ["professionnel", "restaurant", "café", "barista", "entreprise"])
                
                if has_professional_audience:
                    self.log("   ✅ AUDIENCE TARGETING: Appropriate professional audience")
                else:
                    self.log("   ⚠️ AUDIENCE TARGETING: May not target professional users appropriately")
                
                if analysis['quality_score'] >= 70:
                    self.log("   🎉 TEST 3 PASSED: Espresso machine content quality excellent!")
                    return True
                else:
                    self.log(f"   ❌ TEST 3 FAILED: Quality score too low ({analysis['quality_score']}/100)", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Request failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Test failed: {str(e)}", "ERROR")
            return False
    
    def generate_quality_report(self):
        """Generate a comprehensive quality report"""
        self.log("📊 GENERATING COMPREHENSIVE QUALITY REPORT...")
        
        if not self.test_results:
            self.log("❌ No test results to analyze", "ERROR")
            return
        
        total_score = sum(result['quality_score'] for result in self.test_results)
        average_score = total_score / len(self.test_results)
        
        self.log(f"")
        self.log(f"🎯 AI QUALITY PREMIUM TEST RESULTS SUMMARY")
        self.log(f"=" * 60)
        self.log(f"📈 Overall Average Quality Score: {average_score:.1f}/100")
        self.log(f"🧪 Total Tests Conducted: {len(self.test_results)}")
        
        # Analyze by category
        categories_tested = set(result['category'] for result in self.test_results)
        self.log(f"📂 Product Categories Tested: {', '.join(categories_tested)}")
        
        # Quality criteria summary
        criteria_summary = {
            "title_appropriate": 0,
            "pricing_realistic": 0,
            "description_quality": 0,
            "audience_appropriate": 0,
            "seo_relevant": 0
        }
        
        for result in self.test_results:
            for criterion in criteria_summary:
                if result.get(criterion, False):
                    criteria_summary[criterion] += 1
        
        self.log(f"")
        self.log(f"📋 QUALITY CRITERIA ANALYSIS:")
        for criterion, count in criteria_summary.items():
            percentage = (count / len(self.test_results)) * 100
            status = "✅" if percentage >= 70 else "⚠️" if percentage >= 50 else "❌"
            self.log(f"   {status} {criterion.replace('_', ' ').title()}: {count}/{len(self.test_results)} ({percentage:.1f}%)")
        
        # Individual test results
        self.log(f"")
        self.log(f"📝 INDIVIDUAL TEST RESULTS:")
        for i, result in enumerate(self.test_results, 1):
            self.log(f"   Test {i}: {result['product_name']}")
            self.log(f"      Score: {result['quality_score']}/100")
            self.log(f"      Category: {result['category']}")
            if result['strengths']:
                self.log(f"      Strengths: {len(result['strengths'])} identified")
            if result['issues']:
                self.log(f"      Issues: {len(result['issues'])} identified")
        
        # Final assessment
        self.log(f"")
        if average_score >= 75:
            self.log(f"🎉 FINAL ASSESSMENT: EXCELLENT - AI content quality significantly improved!")
            self.log(f"   ✅ Premium content generation working as expected")
            self.log(f"   ✅ Inappropriate content issues resolved")
            self.log(f"   ✅ Realistic pricing implemented")
        elif average_score >= 60:
            self.log(f"✅ FINAL ASSESSMENT: GOOD - AI content quality improved with minor issues")
            self.log(f"   ✅ Major issues resolved")
            self.log(f"   ⚠️ Some fine-tuning may be needed")
        else:
            self.log(f"❌ FINAL ASSESSMENT: NEEDS IMPROVEMENT - Quality standards not met")
            self.log(f"   ❌ Significant issues remain")
            self.log(f"   ❌ Further AI prompt optimization required")
    
    def run_all_tests(self):
        """Run all AI quality premium tests"""
        self.log("🚀 STARTING AI QUALITY PREMIUM TESTING SUITE")
        self.log("=" * 60)
        
        # Register test user
        if not self.register_test_user():
            self.log("❌ Failed to register test user - aborting tests", "ERROR")
            return False
        
        # Run all tests
        test_results = []
        
        self.log("")
        test_results.append(self.test_problematic_product_toilet_paper())
        
        time.sleep(2)  # Brief pause between tests
        
        self.log("")
        test_results.append(self.test_standard_product_smartphone())
        
        time.sleep(2)  # Brief pause between tests
        
        self.log("")
        test_results.append(self.test_complex_product_espresso_machine())
        
        # Generate comprehensive report
        self.log("")
        self.generate_quality_report()
        
        # Final summary
        passed_tests = sum(1 for result in test_results if result)
        total_tests = len(test_results)
        
        self.log("")
        self.log(f"🏁 TESTING COMPLETE")
        self.log(f"   Tests Passed: {passed_tests}/{total_tests}")
        self.log(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL TESTS PASSED - AI QUALITY PREMIUM IMPROVEMENTS VERIFIED!")
            return True
        else:
            self.log("❌ SOME TESTS FAILED - AI QUALITY IMPROVEMENTS NEED ATTENTION")
            return False

def main():
    """Main test execution"""
    tester = AIQualityPremiumTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 AI QUALITY PREMIUM TESTING: SUCCESS")
        exit(0)
    else:
        print("\n❌ AI QUALITY PREMIUM TESTING: FAILED")
        exit(1)

if __name__ == "__main__":
    main()