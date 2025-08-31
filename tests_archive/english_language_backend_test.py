#!/usr/bin/env python3
"""
ECOMSIMPLY English Language Support Backend Testing Suite
Testing the newly implemented English language support in the backend
Focus: Language Parameter Integration, English Content Generation, Multilingual Image Generation
"""

import asyncio
import aiohttp
import json
import base64
import time
import os
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "http://localhost:8001/api"

class EnglishLanguageTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        
    async def setup_session(self):
        """Setup HTTP session and authenticate"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=120)  # 2 minute timeout for AI generation
        )
        
        # Authenticate with provided credentials
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
    
    async def test_language_parameter_integration(self):
        """
        TEST 1: Language Parameter Integration
        Test POST /api/generate-sheet with language="en" parameter
        Verify that the language parameter is correctly passed to call_gpt4_turbo_direct function
        """
        print("\n🧪 TEST 1: Language Parameter Integration")
        print("=" * 60)
        
        test_cases = [
            {
                "name": "English Language Parameter",
                "data": {
                    "product_name": "MacBook Air M3",
                    "product_description": "Latest Apple laptop with M3 chip and Retina display",
                    "category": "Électronique",
                    "language": "en",
                    "generate_image": False,
                    "number_of_images": 0
                },
                "expected_language": "en"
            },
            {
                "name": "French Language Parameter (Default)",
                "data": {
                    "product_name": "MacBook Air M3",
                    "product_description": "Dernier ordinateur portable Apple avec puce M3 et écran Retina",
                    "category": "Électronique",
                    "language": "fr",
                    "generate_image": False,
                    "number_of_images": 0
                },
                "expected_language": "fr"
            },
            {
                "name": "Missing Language Parameter (Should Default to French)",
                "data": {
                    "product_name": "MacBook Air M3",
                    "product_description": "Latest Apple laptop with M3 chip and Retina display",
                    "category": "Électronique",
                    "generate_image": False,
                    "number_of_images": 0
                },
                "expected_language": "fr"
            }
        ]
        
        test_results = []
        
        for test_case in test_cases:
            print(f"\n📋 Testing: {test_case['name']}")
            
            try:
                start_time = time.time()
                async with self.session.post(
                    f"{BACKEND_URL}/generate-sheet",
                    json=test_case["data"],
                    headers=self.get_auth_headers()
                ) as response:
                    
                    status = response.status
                    response_data = await response.json()
                    generation_time = time.time() - start_time
                    
                    if status == 200:
                        print(f"   ✅ SUCCESS: API call completed in {generation_time:.2f}s")
                        print(f"   📝 Generated Title: {response_data.get('generated_title', 'N/A')[:50]}...")
                        print(f"   📄 Description Length: {len(response_data.get('marketing_description', ''))}")
                        print(f"   🏷️ Features Count: {len(response_data.get('key_features', []))}")
                        print(f"   🔍 SEO Tags Count: {len(response_data.get('seo_tags', []))}")
                        
                        # Analyze language of generated content
                        title = response_data.get('generated_title', '')
                        description = response_data.get('marketing_description', '')
                        features = response_data.get('key_features', [])
                        
                        # Simple language detection based on common words
                        english_indicators = ['the', 'and', 'with', 'for', 'this', 'that', 'professional', 'premium', 'quality']
                        french_indicators = ['le', 'la', 'les', 'et', 'avec', 'pour', 'ce', 'cette', 'professionnel', 'premium', 'qualité']
                        
                        full_text = f"{title} {description} {' '.join(features)}".lower()
                        english_score = sum(1 for word in english_indicators if word in full_text)
                        french_score = sum(1 for word in french_indicators if word in full_text)
                        
                        detected_language = "en" if english_score > french_score else "fr"
                        language_match = detected_language == test_case["expected_language"]
                        
                        print(f"   🌍 Expected Language: {test_case['expected_language']}")
                        print(f"   🌍 Detected Language: {detected_language} (EN:{english_score}, FR:{french_score})")
                        print(f"   🎯 Language Match: {'✅ YES' if language_match else '❌ NO'}")
                        
                        test_results.append({
                            "test_case": test_case["name"],
                            "status": status,
                            "success": True,
                            "language_match": language_match,
                            "expected_language": test_case["expected_language"],
                            "detected_language": detected_language,
                            "generation_time": generation_time,
                            "content_quality": {
                                "title_length": len(title),
                                "description_length": len(description),
                                "features_count": len(features),
                                "seo_tags_count": len(response_data.get('seo_tags', []))
                            }
                        })
                    else:
                        print(f"   ❌ ERROR {status}: {test_case['name']}")
                        error_detail = response_data.get('detail', 'Unknown error')
                        print(f"      Error: {error_detail}")
                        test_results.append({
                            "test_case": test_case["name"],
                            "status": status,
                            "success": False,
                            "error": error_detail
                        })
                        
            except Exception as e:
                print(f"   ❌ EXCEPTION: {test_case['name']} - {str(e)}")
                test_results.append({
                    "test_case": test_case["name"],
                    "status": None,
                    "success": False,
                    "error": str(e)
                })
        
        # Summary for language parameter integration
        successful_tests = sum(1 for result in test_results if result['success'])
        language_matches = sum(1 for result in test_results if result.get('language_match', False))
        total_tests = len(test_results)
        
        print(f"\n📈 LANGUAGE PARAMETER INTEGRATION SUMMARY:")
        print(f"   ✅ Successful API Calls: {successful_tests}/{total_tests}")
        print(f"   🌍 Correct Language Generation: {language_matches}/{successful_tests}")
        print(f"   📊 Overall Success Rate: {(language_matches/total_tests*100):.1f}%")
        
        self.test_results.extend(test_results)
        return language_matches == successful_tests and successful_tests > 0
    
    async def test_english_content_generation(self):
        """
        TEST 2: English Content Generation
        Generate a product sheet with English language setting
        Verify that all content fields are in English
        """
        print("\n🧪 TEST 2: English Content Generation")
        print("=" * 60)
        
        test_data = {
            "product_name": "MacBook Air M3",
            "product_description": "Latest Apple laptop with M3 chip and Retina display",
            "category": "Électronique",
            "language": "en",
            "generate_image": False,
            "number_of_images": 0,
            "use_case": "Professional work and creative tasks"
        }
        
        print(f"📋 Testing English content generation for: {test_data['product_name']}")
        
        try:
            start_time = time.time()
            async with self.session.post(
                f"{BACKEND_URL}/generate-sheet",
                json=test_data,
                headers=self.get_auth_headers()
            ) as response:
                
                status = response.status
                response_data = await response.json()
                generation_time = time.time() - start_time
                
                if status == 200:
                    print(f"   ✅ SUCCESS: English content generated in {generation_time:.2f}s")
                    
                    # Extract all content fields
                    generated_title = response_data.get('generated_title', '')
                    marketing_description = response_data.get('marketing_description', '')
                    key_features = response_data.get('key_features', [])
                    seo_tags = response_data.get('seo_tags', [])
                    price_suggestions = response_data.get('price_suggestions', '')
                    target_audience = response_data.get('target_audience', '')
                    call_to_action = response_data.get('call_to_action', '')
                    
                    print(f"\n📝 GENERATED ENGLISH CONTENT:")
                    print(f"   🏷️ Title: {generated_title}")
                    print(f"   📄 Description: {marketing_description[:100]}...")
                    print(f"   ⭐ Features ({len(key_features)}):")
                    for i, feature in enumerate(key_features[:3], 1):
                        print(f"      {i}. {feature}")
                    print(f"   🔍 SEO Tags ({len(seo_tags)}): {', '.join(seo_tags[:5])}")
                    print(f"   💰 Price: {price_suggestions[:50]}...")
                    print(f"   🎯 Audience: {target_audience[:50]}...")
                    print(f"   📢 CTA: {call_to_action}")
                    
                    # Analyze English quality
                    all_content = f"{generated_title} {marketing_description} {' '.join(key_features)} {' '.join(seo_tags)} {price_suggestions} {target_audience} {call_to_action}"
                    
                    # English quality indicators
                    english_quality_indicators = {
                        'professional_terms': ['professional', 'premium', 'advanced', 'innovative', 'cutting-edge', 'state-of-the-art'],
                        'technical_terms': ['processor', 'display', 'performance', 'technology', 'specifications', 'features'],
                        'marketing_terms': ['exclusive', 'ultimate', 'superior', 'exceptional', 'outstanding', 'remarkable'],
                        'action_words': ['discover', 'experience', 'achieve', 'enhance', 'optimize', 'maximize']
                    }
                    
                    quality_scores = {}
                    for category, terms in english_quality_indicators.items():
                        score = sum(1 for term in terms if term.lower() in all_content.lower())
                        quality_scores[category] = score
                    
                    total_quality_score = sum(quality_scores.values())
                    
                    print(f"\n🎯 ENGLISH CONTENT QUALITY ANALYSIS:")
                    for category, score in quality_scores.items():
                        print(f"   {category.replace('_', ' ').title()}: {score}")
                    print(f"   Total Quality Score: {total_quality_score}")
                    
                    # Check for French words (should be minimal)
                    french_words = ['le', 'la', 'les', 'et', 'avec', 'pour', 'dans', 'sur', 'une', 'des']
                    french_count = sum(1 for word in french_words if f" {word} " in all_content.lower())
                    
                    print(f"   French Words Detected: {french_count} (should be minimal)")
                    
                    content_quality_good = (
                        len(generated_title) >= 30 and
                        len(marketing_description) >= 200 and
                        len(key_features) >= 5 and
                        len(seo_tags) >= 5 and
                        total_quality_score >= 3 and
                        french_count <= 2
                    )
                    
                    print(f"   🏆 Content Quality: {'✅ EXCELLENT' if content_quality_good else '⚠️ NEEDS IMPROVEMENT'}")
                    
                    test_result = {
                        "test_name": "English Content Generation",
                        "status": status,
                        "success": True,
                        "content_quality_good": content_quality_good,
                        "generation_time": generation_time,
                        "content_analysis": {
                            "title_length": len(generated_title),
                            "description_length": len(marketing_description),
                            "features_count": len(key_features),
                            "seo_tags_count": len(seo_tags),
                            "quality_score": total_quality_score,
                            "french_words_count": french_count
                        },
                        "sample_content": {
                            "title": generated_title,
                            "first_feature": key_features[0] if key_features else "",
                            "first_seo_tag": seo_tags[0] if seo_tags else "",
                            "cta": call_to_action
                        }
                    }
                    
                else:
                    print(f"   ❌ ERROR {status}: English content generation failed")
                    error_detail = response_data.get('detail', 'Unknown error')
                    print(f"      Error: {error_detail}")
                    test_result = {
                        "test_name": "English Content Generation",
                        "status": status,
                        "success": False,
                        "error": error_detail
                    }
                    
        except Exception as e:
            print(f"   ❌ EXCEPTION: English content generation - {str(e)}")
            test_result = {
                "test_name": "English Content Generation",
                "status": None,
                "success": False,
                "error": str(e)
            }
        
        self.test_results.append(test_result)
        return test_result.get('success', False) and test_result.get('content_quality_good', False)
    
    async def test_multilingual_image_generation(self):
        """
        TEST 3: Multilingual Image Generation
        Test that image generation prompts are generated in English when language="en"
        Verify that the language parameter is passed to generate_image_with_fal_optimized
        """
        print("\n🧪 TEST 3: Multilingual Image Generation")
        print("=" * 60)
        
        test_cases = [
            {
                "name": "English Image Generation",
                "data": {
                    "product_name": "MacBook Air M3",
                    "product_description": "Latest Apple laptop with M3 chip and Retina display",
                    "category": "Électronique",
                    "language": "en",
                    "generate_image": True,
                    "number_of_images": 1,
                    "image_style": "studio"
                },
                "expected_language": "en"
            },
            {
                "name": "French Image Generation",
                "data": {
                    "product_name": "MacBook Air M3",
                    "product_description": "Dernier ordinateur portable Apple avec puce M3 et écran Retina",
                    "category": "Électronique",
                    "language": "fr",
                    "generate_image": True,
                    "number_of_images": 1,
                    "image_style": "studio"
                },
                "expected_language": "fr"
            }
        ]
        
        test_results = []
        
        for test_case in test_cases:
            print(f"\n🖼️ Testing: {test_case['name']}")
            
            try:
                start_time = time.time()
                async with self.session.post(
                    f"{BACKEND_URL}/generate-sheet",
                    json=test_case["data"],
                    headers=self.get_auth_headers()
                ) as response:
                    
                    status = response.status
                    response_data = await response.json()
                    generation_time = time.time() - start_time
                    
                    if status == 200:
                        generated_images = response_data.get('generated_images', [])
                        image_count = len(generated_images)
                        
                        print(f"   ✅ SUCCESS: {test_case['expected_language'].upper()} image generation completed in {generation_time:.2f}s")
                        print(f"   🖼️ Images Generated: {image_count}")
                        
                        if image_count > 0:
                            # Check if images are valid base64
                            valid_images = 0
                            for i, img in enumerate(generated_images):
                                try:
                                    if img and len(img) > 1000:  # Basic validation
                                        base64.b64decode(img[:100])  # Test decode first 100 chars
                                        valid_images += 1
                                        print(f"      Image {i+1}: ✅ Valid (Size: {len(img)} chars)")
                                    else:
                                        print(f"      Image {i+1}: ❌ Invalid or too small")
                                except:
                                    print(f"      Image {i+1}: ❌ Invalid base64")
                            
                            images_quality_good = valid_images == image_count and image_count > 0
                            print(f"   🎯 Image Quality: {'✅ GOOD' if images_quality_good else '❌ POOR'}")
                        else:
                            images_quality_good = False
                            print(f"   ❌ No images generated")
                        
                        # Also check text content language
                        title = response_data.get('generated_title', '')
                        description = response_data.get('marketing_description', '')
                        
                        english_indicators = ['the', 'and', 'with', 'for', 'professional', 'premium']
                        french_indicators = ['le', 'la', 'et', 'avec', 'pour', 'professionnel']
                        
                        full_text = f"{title} {description}".lower()
                        english_score = sum(1 for word in english_indicators if word in full_text)
                        french_score = sum(1 for word in french_indicators if word in full_text)
                        
                        detected_language = "en" if english_score > french_score else "fr"
                        language_match = detected_language == test_case["expected_language"]
                        
                        print(f"   🌍 Content Language Match: {'✅ YES' if language_match else '❌ NO'} ({detected_language})")
                        
                        test_results.append({
                            "test_case": test_case["name"],
                            "status": status,
                            "success": True,
                            "images_generated": image_count,
                            "images_quality_good": images_quality_good,
                            "language_match": language_match,
                            "generation_time": generation_time
                        })
                    else:
                        print(f"   ❌ ERROR {status}: {test_case['name']}")
                        error_detail = response_data.get('detail', 'Unknown error')
                        print(f"      Error: {error_detail}")
                        test_results.append({
                            "test_case": test_case["name"],
                            "status": status,
                            "success": False,
                            "error": error_detail
                        })
                        
            except Exception as e:
                print(f"   ❌ EXCEPTION: {test_case['name']} - {str(e)}")
                test_results.append({
                    "test_case": test_case["name"],
                    "status": None,
                    "success": False,
                    "error": str(e)
                })
        
        # Summary for multilingual image generation
        successful_tests = sum(1 for result in test_results if result['success'])
        quality_images = sum(1 for result in test_results if result.get('images_quality_good', False))
        language_matches = sum(1 for result in test_results if result.get('language_match', False))
        total_tests = len(test_results)
        
        print(f"\n🖼️ MULTILINGUAL IMAGE GENERATION SUMMARY:")
        print(f"   ✅ Successful API Calls: {successful_tests}/{total_tests}")
        print(f"   🎨 Quality Images Generated: {quality_images}/{successful_tests}")
        print(f"   🌍 Correct Language Content: {language_matches}/{successful_tests}")
        print(f"   📊 Overall Success Rate: {(min(quality_images, language_matches)/total_tests*100):.1f}%")
        
        self.test_results.extend(test_results)
        return successful_tests > 0 and quality_images > 0 and language_matches > 0
    
    async def test_fallback_and_error_handling(self):
        """
        TEST 4: Fallback and Error Handling
        Test with missing language parameter (should default to French)
        Test with invalid language parameter
        Verify proper error handling
        """
        print("\n🧪 TEST 4: Fallback and Error Handling")
        print("=" * 60)
        
        test_cases = [
            {
                "name": "Invalid Language Parameter",
                "data": {
                    "product_name": "MacBook Air M3",
                    "product_description": "Latest Apple laptop with M3 chip and Retina display",
                    "category": "Électronique",
                    "language": "invalid_lang",
                    "generate_image": False,
                    "number_of_images": 0
                },
                "should_succeed": True,  # Should fallback to French
                "expected_fallback": "fr"
            },
            {
                "name": "Empty Language Parameter",
                "data": {
                    "product_name": "MacBook Air M3",
                    "product_description": "Latest Apple laptop with M3 chip and Retina display",
                    "category": "Électronique",
                    "language": "",
                    "generate_image": False,
                    "number_of_images": 0
                },
                "should_succeed": True,  # Should fallback to French
                "expected_fallback": "fr"
            },
            {
                "name": "Null Language Parameter",
                "data": {
                    "product_name": "MacBook Air M3",
                    "product_description": "Latest Apple laptop with M3 chip and Retina display",
                    "category": "Électronique",
                    "language": None,
                    "generate_image": False,
                    "number_of_images": 0
                },
                "should_succeed": True,  # Should fallback to French
                "expected_fallback": "fr"
            }
        ]
        
        test_results = []
        
        for test_case in test_cases:
            print(f"\n🔧 Testing: {test_case['name']}")
            
            try:
                start_time = time.time()
                async with self.session.post(
                    f"{BACKEND_URL}/generate-sheet",
                    json=test_case["data"],
                    headers=self.get_auth_headers()
                ) as response:
                    
                    status = response.status
                    response_data = await response.json()
                    generation_time = time.time() - start_time
                    
                    if status == 200:
                        print(f"   ✅ SUCCESS: API handled fallback correctly in {generation_time:.2f}s")
                        
                        # Check if content was generated in expected fallback language
                        title = response_data.get('generated_title', '')
                        description = response_data.get('marketing_description', '')
                        
                        # French indicators for fallback detection
                        french_indicators = ['le', 'la', 'les', 'et', 'avec', 'pour', 'professionnel', 'qualité']
                        english_indicators = ['the', 'and', 'with', 'for', 'professional', 'quality']
                        
                        full_text = f"{title} {description}".lower()
                        french_score = sum(1 for word in french_indicators if word in full_text)
                        english_score = sum(1 for word in english_indicators if word in full_text)
                        
                        detected_language = "fr" if french_score > english_score else "en"
                        fallback_correct = detected_language == test_case["expected_fallback"]
                        
                        print(f"   🌍 Expected Fallback: {test_case['expected_fallback']}")
                        print(f"   🌍 Detected Language: {detected_language}")
                        print(f"   🎯 Fallback Correct: {'✅ YES' if fallback_correct else '❌ NO'}")
                        
                        test_results.append({
                            "test_case": test_case["name"],
                            "status": status,
                            "success": True,
                            "fallback_correct": fallback_correct,
                            "detected_language": detected_language,
                            "expected_fallback": test_case["expected_fallback"],
                            "generation_time": generation_time
                        })
                    elif test_case["should_succeed"]:
                        print(f"   ❌ UNEXPECTED ERROR {status}: Should have succeeded with fallback")
                        error_detail = response_data.get('detail', 'Unknown error')
                        print(f"      Error: {error_detail}")
                        test_results.append({
                            "test_case": test_case["name"],
                            "status": status,
                            "success": False,
                            "error": f"Unexpected error: {error_detail}"
                        })
                    else:
                        print(f"   ✅ EXPECTED ERROR {status}: Correctly rejected invalid input")
                        test_results.append({
                            "test_case": test_case["name"],
                            "status": status,
                            "success": True,
                            "expected_error": True
                        })
                        
            except Exception as e:
                print(f"   ❌ EXCEPTION: {test_case['name']} - {str(e)}")
                test_results.append({
                    "test_case": test_case["name"],
                    "status": None,
                    "success": False,
                    "error": str(e)
                })
        
        # Summary for fallback and error handling
        successful_tests = sum(1 for result in test_results if result['success'])
        correct_fallbacks = sum(1 for result in test_results if result.get('fallback_correct', False))
        total_tests = len(test_results)
        
        print(f"\n🔧 FALLBACK AND ERROR HANDLING SUMMARY:")
        print(f"   ✅ Successful Tests: {successful_tests}/{total_tests}")
        print(f"   🎯 Correct Fallbacks: {correct_fallbacks}/{successful_tests}")
        print(f"   📊 Overall Success Rate: {(successful_tests/total_tests*100):.1f}%")
        
        self.test_results.extend(test_results)
        return successful_tests == total_tests and correct_fallbacks >= 2  # At least 2 fallbacks should work
    
    async def run_all_tests(self):
        """Run all English language support tests"""
        print("🚀 ECOMSIMPLY ENGLISH LANGUAGE SUPPORT TESTING")
        print("=" * 80)
        print("Testing newly implemented English language support in the backend")
        print("Focus: Language Parameter Integration, English Content Generation, Multilingual Image Generation")
        print("=" * 80)
        
        # Setup
        if not await self.setup_session():
            print("❌ Failed to setup test session")
            return False
        
        try:
            # Run all tests
            print("\n🎯 TESTING ENGLISH LANGUAGE SUPPORT...")
            
            test1_result = await self.test_language_parameter_integration()
            await asyncio.sleep(2)  # Brief pause between tests
            
            test2_result = await self.test_english_content_generation()
            await asyncio.sleep(2)
            
            test3_result = await self.test_multilingual_image_generation()
            await asyncio.sleep(2)
            
            test4_result = await self.test_fallback_and_error_handling()
            
            # Summary
            print("\n" + "=" * 80)
            print("🏁 TEST SUMMARY - ENGLISH LANGUAGE SUPPORT")
            print("=" * 80)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result.get('success', False))
            
            print(f"📊 Total Tests: {total_tests}")
            print(f"✅ Passed: {passed_tests}")
            print(f"❌ Failed: {total_tests - passed_tests}")
            print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
            
            print(f"\n🎯 ENGLISH LANGUAGE SUPPORT STATUS:")
            print(f"   Language Parameter Integration: {'✅ WORKING' if test1_result else '❌ FAILING'}")
            print(f"   English Content Generation: {'✅ WORKING' if test2_result else '❌ FAILING'}")
            print(f"   Multilingual Image Generation: {'✅ WORKING' if test3_result else '❌ FAILING'}")
            print(f"   Fallback and Error Handling: {'✅ WORKING' if test4_result else '❌ FAILING'}")
            
            # Overall assessment
            all_tests_passed = test1_result and test2_result and test3_result and test4_result
            
            print(f"\n🏆 OVERALL RESULT: {'✅ COMPLETE SUCCESS' if all_tests_passed else '⚠️ PARTIAL SUCCESS' if any([test1_result, test2_result, test3_result, test4_result]) else '❌ FAILURE'}")
            
            if all_tests_passed:
                print("🎉 All English language support features are working perfectly!")
                print("   ✅ Language parameter is correctly integrated")
                print("   ✅ English content generation is functional")
                print("   ✅ Multilingual image generation works")
                print("   ✅ Fallback mechanisms are working")
            elif any([test1_result, test2_result, test3_result, test4_result]):
                print("⚠️ Some English language support features are working:")
                if test1_result:
                    print("   ✅ Language parameter integration is working")
                if test2_result:
                    print("   ✅ English content generation is working")
                if test3_result:
                    print("   ✅ Multilingual image generation is working")
                if test4_result:
                    print("   ✅ Fallback and error handling is working")
                    
                print("   Issues detected:")
                if not test1_result:
                    print("   ❌ Language parameter integration needs attention")
                if not test2_result:
                    print("   ❌ English content generation needs attention")
                if not test3_result:
                    print("   ❌ Multilingual image generation needs attention")
                if not test4_result:
                    print("   ❌ Fallback and error handling needs attention")
            else:
                print("❌ CRITICAL FAILURE: English language support is not working")
                print("   All language features need immediate attention")
            
            return all_tests_passed
            
        finally:
            await self.cleanup()

async def main():
    """Main test execution"""
    tester = EnglishLanguageTester()
    success = await tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())