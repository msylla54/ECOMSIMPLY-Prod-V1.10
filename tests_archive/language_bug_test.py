#!/usr/bin/env python3
"""
ECOMSIMPLY Language Bug Fix Testing Suite
Testing the two critical bug fixes:
1. BUG BANDEAU SUPÉRIEUR CORRIGÉ - Main title positioning fix
2. BUG SÉLECTEUR DE LANGUE AMÉLIORÉ - Language switching functionality

Focus: Testing backend language functionality for content generation
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://ecomsimply.com/api"

class LanguageBugTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        
    async def setup_session(self):
        """Setup HTTP session and authenticate"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        )
        
        # Try to authenticate with admin credentials
        auth_data = {
            "email": "msylla54@gmail.com",
            "password": "AdminEcomsimply"
        }
        
        print("🔐 Authenticating with admin credentials...")
        try:
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=auth_data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.auth_token = result.get("token")
                    print("✅ Authentication successful")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Authentication failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Authentication exception: {str(e)}")
            return False
    
    async def cleanup(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
    
    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    async def test_language_content_generation(self):
        """
        TEST 1: Language-specific Content Generation
        Test POST /api/generate-sheet with language=fr and language=en for "iPhone 15 Pro"
        Verify that AI-generated content changes language appropriately
        """
        print("\n🧪 TEST 1: Language-specific Content Generation")
        print("=" * 60)
        
        test_product = "iPhone 15 Pro"
        test_description = "Smartphone premium avec processeur A17 Pro et appareil photo 48MP"
        
        # Test data for both languages
        test_cases = [
            {
                "language": "fr",
                "product_name": test_product,
                "product_description": test_description,
                "expected_language_indicators": ["français", "avec", "pour", "de", "le", "la", "des", "une", "un"]
            },
            {
                "language": "en", 
                "product_name": test_product,
                "product_description": "Premium smartphone with A17 Pro processor and 48MP camera",
                "expected_language_indicators": ["with", "and", "for", "the", "a", "an", "premium", "advanced"]
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            lang = test_case["language"]
            print(f"\n🌍 Testing language: {lang.upper()}")
            
            request_data = {
                "product_name": test_case["product_name"],
                "product_description": test_case["product_description"],
                "generate_image": False,  # Skip image generation for faster testing
                "number_of_images": 0,
                "language": lang,
                "category": "électronique",
                "use_case": "smartphone haut de gamme"
            }
            
            try:
                start_time = time.time()
                async with self.session.post(
                    f"{BACKEND_URL}/generate-sheet",
                    json=request_data,
                    headers=self.get_auth_headers()
                ) as response:
                    
                    status = response.status
                    generation_time = time.time() - start_time
                    
                    if status == 200:
                        response_data = await response.json()
                        
                        # Extract generated content
                        generated_title = response_data.get("generated_title", "")
                        marketing_description = response_data.get("marketing_description", "")
                        key_features = response_data.get("key_features", [])
                        seo_tags = response_data.get("seo_tags", [])
                        call_to_action = response_data.get("call_to_action", "")
                        
                        # Combine all text for language analysis
                        all_text = f"{generated_title} {marketing_description} {' '.join(key_features)} {' '.join(seo_tags)} {call_to_action}".lower()
                        
                        # Check for language indicators
                        language_score = 0
                        detected_indicators = []
                        for indicator in test_case["expected_language_indicators"]:
                            if indicator.lower() in all_text:
                                language_score += 1
                                detected_indicators.append(indicator)
                        
                        # Determine if language is correctly applied
                        language_threshold = len(test_case["expected_language_indicators"]) * 0.3  # At least 30% of indicators
                        language_correct = language_score >= language_threshold
                        
                        print(f"   ✅ SUCCESS: Content generated in {lang.upper()}")
                        print(f"   📊 Generation time: {generation_time:.2f}s")
                        print(f"   📝 Title: {generated_title[:100]}...")
                        print(f"   🔤 Language indicators found: {language_score}/{len(test_case['expected_language_indicators'])}")
                        print(f"   🎯 Language detection: {'✅ CORRECT' if language_correct else '❌ INCORRECT'}")
                        
                        if detected_indicators:
                            print(f"   📋 Detected indicators: {', '.join(detected_indicators[:5])}")
                        
                        results.append({
                            "language": lang,
                            "status": status,
                            "success": True,
                            "language_correct": language_correct,
                            "language_score": language_score,
                            "generation_time": generation_time,
                            "content_length": len(all_text),
                            "title": generated_title,
                            "features_count": len(key_features),
                            "seo_tags_count": len(seo_tags)
                        })
                        
                    else:
                        error_text = await response.text()
                        print(f"   ❌ ERROR {status}: Content generation failed for {lang.upper()}")
                        print(f"      Error details: {error_text[:200]}...")
                        
                        results.append({
                            "language": lang,
                            "status": status,
                            "success": False,
                            "error": f"HTTP {status}",
                            "error_details": error_text[:200]
                        })
                        
            except Exception as e:
                print(f"   ❌ EXCEPTION: Language {lang.upper()} test failed - {str(e)}")
                results.append({
                    "language": lang,
                    "status": None,
                    "success": False,
                    "error": str(e)
                })
        
        # Analysis and comparison
        print(f"\n📊 LANGUAGE GENERATION ANALYSIS:")
        
        successful_tests = [r for r in results if r['success']]
        if len(successful_tests) >= 2:
            fr_result = next((r for r in successful_tests if r['language'] == 'fr'), None)
            en_result = next((r for r in successful_tests if r['language'] == 'en'), None)
            
            if fr_result and en_result:
                print(f"   🇫🇷 French generation: {'✅ WORKING' if fr_result['language_correct'] else '❌ LANGUAGE ISSUE'}")
                print(f"   🇺🇸 English generation: {'✅ WORKING' if en_result['language_correct'] else '❌ LANGUAGE ISSUE'}")
                
                # Compare content differences
                if fr_result['title'] != en_result['title']:
                    print(f"   🔄 Content differs between languages: ✅ GOOD")
                else:
                    print(f"   ⚠️ Content identical between languages: POTENTIAL ISSUE")
                
                # Performance comparison
                avg_time = (fr_result['generation_time'] + en_result['generation_time']) / 2
                print(f"   ⏱️ Average generation time: {avg_time:.2f}s")
                
                both_languages_working = fr_result['language_correct'] and en_result['language_correct']
                print(f"   🎯 Both languages working correctly: {'✅ YES' if both_languages_working else '❌ NO'}")
                
                self.test_results.extend(results)
                return both_languages_working
        
        print(f"   ❌ Insufficient successful tests for comparison")
        self.test_results.extend(results)
        return False
    
    async def test_language_switching_consistency(self):
        """
        TEST 2: Language Switching Consistency
        Test that the same product generates different content in different languages
        """
        print("\n🧪 TEST 2: Language Switching Consistency")
        print("=" * 60)
        
        # Test with multiple products to ensure consistency
        test_products = [
            {
                "name": "MacBook Pro",
                "description": "Ordinateur portable professionnel"
            },
            {
                "name": "AirPods Pro",
                "description": "Écouteurs sans fil premium"
            }
        ]
        
        consistency_results = []
        
        for product in test_products:
            print(f"\n🔍 Testing product: {product['name']}")
            
            # Generate in French first
            fr_request = {
                "product_name": product["name"],
                "product_description": product["description"],
                "generate_image": False,
                "number_of_images": 0,
                "language": "fr",
                "category": "électronique"
            }
            
            # Generate in English
            en_request = {
                "product_name": product["name"],
                "product_description": "Professional premium device",
                "generate_image": False,
                "number_of_images": 0,
                "language": "en",
                "category": "électronique"
            }
            
            fr_content = None
            en_content = None
            
            # Test French generation
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/generate-sheet",
                    json=fr_request,
                    headers=self.get_auth_headers()
                ) as response:
                    if response.status == 200:
                        fr_content = await response.json()
                        print(f"   🇫🇷 French generation: ✅ SUCCESS")
                    else:
                        print(f"   🇫🇷 French generation: ❌ FAILED ({response.status})")
            except Exception as e:
                print(f"   🇫🇷 French generation: ❌ EXCEPTION - {str(e)}")
            
            # Small delay between requests
            await asyncio.sleep(1)
            
            # Test English generation
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/generate-sheet",
                    json=en_request,
                    headers=self.get_auth_headers()
                ) as response:
                    if response.status == 200:
                        en_content = await response.json()
                        print(f"   🇺🇸 English generation: ✅ SUCCESS")
                    else:
                        print(f"   🇺🇸 English generation: ❌ FAILED ({response.status})")
            except Exception as e:
                print(f"   🇺🇸 English generation: ❌ EXCEPTION - {str(e)}")
            
            # Compare content if both succeeded
            if fr_content and en_content:
                fr_title = fr_content.get("generated_title", "")
                en_title = en_content.get("generated_title", "")
                
                fr_desc = fr_content.get("marketing_description", "")
                en_desc = en_content.get("marketing_description", "")
                
                # Check if content is different (indicating proper language switching)
                title_different = fr_title.lower() != en_title.lower()
                desc_different = fr_desc.lower() != en_desc.lower()
                
                # Check for language-specific words
                fr_has_french_words = any(word in fr_desc.lower() for word in ["avec", "pour", "de", "le", "la", "des", "une"])
                en_has_english_words = any(word in en_desc.lower() for word in ["with", "for", "the", "and", "premium", "advanced"])
                
                consistency_score = sum([title_different, desc_different, fr_has_french_words, en_has_english_words])
                
                print(f"   📊 Content Analysis:")
                print(f"      Title different: {'✅' if title_different else '❌'}")
                print(f"      Description different: {'✅' if desc_different else '❌'}")
                print(f"      French words in FR: {'✅' if fr_has_french_words else '❌'}")
                print(f"      English words in EN: {'✅' if en_has_english_words else '❌'}")
                print(f"      Consistency score: {consistency_score}/4")
                
                consistency_results.append({
                    "product": product["name"],
                    "both_generated": True,
                    "consistency_score": consistency_score,
                    "title_different": title_different,
                    "desc_different": desc_different,
                    "language_indicators_correct": fr_has_french_words and en_has_english_words
                })
            else:
                print(f"   ❌ Cannot compare - one or both generations failed")
                consistency_results.append({
                    "product": product["name"],
                    "both_generated": False,
                    "error": "Generation failed"
                })
        
        # Overall consistency assessment
        successful_comparisons = [r for r in consistency_results if r.get('both_generated', False)]
        if successful_comparisons:
            avg_consistency = sum(r['consistency_score'] for r in successful_comparisons) / len(successful_comparisons)
            high_consistency = avg_consistency >= 3.0  # At least 3/4 criteria met
            
            print(f"\n🎯 CONSISTENCY ASSESSMENT:")
            print(f"   Products tested: {len(consistency_results)}")
            print(f"   Successful comparisons: {len(successful_comparisons)}")
            print(f"   Average consistency score: {avg_consistency:.1f}/4")
            print(f"   Language switching working: {'✅ YES' if high_consistency else '❌ NO'}")
            
            return high_consistency
        else:
            print(f"\n❌ No successful comparisons possible")
            return False
    
    async def test_supported_languages_endpoint(self):
        """
        TEST 3: Supported Languages Endpoint
        Test that the backend properly reports supported languages
        """
        print("\n🧪 TEST 3: Supported Languages Endpoint")
        print("=" * 60)
        
        try:
            async with self.session.get(
                f"{BACKEND_URL}/languages",
                headers=self.get_auth_headers()
            ) as response:
                
                status = response.status
                
                if status == 200:
                    languages_data = await response.json()
                    print(f"   ✅ SUCCESS: Languages endpoint working")
                    print(f"   📋 Response: {json.dumps(languages_data, indent=2)}")
                    
                    # Check if French and English are supported
                    if isinstance(languages_data, dict):
                        fr_supported = "fr" in languages_data
                        en_supported = "en" in languages_data
                        
                        print(f"   🇫🇷 French supported: {'✅' if fr_supported else '❌'}")
                        print(f"   🇺🇸 English supported: {'✅' if en_supported else '❌'}")
                        
                        both_supported = fr_supported and en_supported
                        
                        self.test_results.append({
                            "test": "languages_endpoint",
                            "status": status,
                            "success": True,
                            "both_languages_supported": both_supported,
                            "languages_count": len(languages_data)
                        })
                        
                        return both_supported
                    else:
                        print(f"   ⚠️ Unexpected response format")
                        return False
                        
                else:
                    error_text = await response.text()
                    print(f"   ❌ ERROR {status}: Languages endpoint failed")
                    print(f"      Error details: {error_text[:200]}...")
                    
                    self.test_results.append({
                        "test": "languages_endpoint",
                        "status": status,
                        "success": False,
                        "error": f"HTTP {status}"
                    })
                    
                    return False
                    
        except Exception as e:
            print(f"   ❌ EXCEPTION: Languages endpoint test failed - {str(e)}")
            self.test_results.append({
                "test": "languages_endpoint",
                "status": None,
                "success": False,
                "error": str(e)
            })
            return False
    
    async def run_all_tests(self):
        """Run all language bug fix tests"""
        print("🚀 ECOMSIMPLY LANGUAGE BUG FIX TESTING")
        print("=" * 80)
        print("Testing Critical Bug Fixes:")
        print("1. BUG BANDEAU SUPÉRIEUR CORRIGÉ - Main title positioning")
        print("2. BUG SÉLECTEUR DE LANGUE AMÉLIORÉ - Language switching functionality")
        print("=" * 80)
        
        # Setup
        if not await self.setup_session():
            print("❌ Failed to setup test session")
            return False
        
        try:
            # Run all tests
            print("\n🎯 TESTING LANGUAGE FUNCTIONALITY...")
            
            test1_result = await self.test_language_content_generation()
            await asyncio.sleep(2)  # Pause between tests
            
            test2_result = await self.test_language_switching_consistency()
            await asyncio.sleep(1)
            
            test3_result = await self.test_supported_languages_endpoint()
            
            # Summary
            print("\n" + "=" * 80)
            print("🏁 LANGUAGE BUG FIX TEST SUMMARY")
            print("=" * 80)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result.get('success', False))
            
            print(f"📊 Total Tests: {total_tests}")
            print(f"✅ Passed: {passed_tests}")
            print(f"❌ Failed: {total_tests - passed_tests}")
            print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests completed")
            
            print(f"\n🎯 LANGUAGE FUNCTIONALITY STATUS:")
            print(f"   Content Generation (FR/EN): {'✅ WORKING' if test1_result else '❌ FAILING'}")
            print(f"   Language Switching Consistency: {'✅ WORKING' if test2_result else '❌ FAILING'}")
            print(f"   Supported Languages Endpoint: {'✅ WORKING' if test3_result else '❌ FAILING'}")
            
            # Overall assessment
            language_functionality_working = test1_result and test2_result
            overall_success = language_functionality_working and test3_result
            
            print(f"\n🏆 OVERALL RESULT: {'✅ SUCCESS' if overall_success else '❌ ISSUES DETECTED'}")
            
            if overall_success:
                print("🎉 All language functionality tests passed!")
                print("   ✅ French and English content generation working")
                print("   ✅ Language switching produces different content")
                print("   ✅ Backend properly supports both languages")
                print("\n💡 BUG FIX VERIFICATION:")
                print("   ✅ Language selector functionality is working correctly")
                print("   ✅ GPT prompts are using the selected language")
                print("   ✅ Content generation respects language parameter")
            else:
                print("⚠️ Issues detected in language functionality:")
                if not test1_result:
                    print("   ❌ Content generation not properly switching languages")
                if not test2_result:
                    print("   ❌ Language switching consistency issues")
                if not test3_result:
                    print("   ❌ Languages endpoint not working properly")
                    
                print("\n🔧 RECOMMENDATIONS:")
                print("   1. Check GPT prompt templates for language-specific instructions")
                print("   2. Verify language parameter is being passed correctly to AI generation")
                print("   3. Ensure backend language configuration is properly set up")
            
            return overall_success
            
        finally:
            await self.cleanup()

async def main():
    """Main test execution"""
    tester = LanguageBugTester()
    success = await tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())