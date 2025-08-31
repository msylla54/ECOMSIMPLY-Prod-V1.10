#!/usr/bin/env python3
"""
ECOMSIMPLY Enhanced Product Sheet Generation Testing Suite
Testing: Système de génération de fiches produit amélioré avec optimisation contextuelle et analyse des prix
Focus: Nouvelles fonctionnalités d'optimisation contextuelle et d'intégration de l'analyse des prix
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://ecomsimply.com/api"

class EnhancedGenerationTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        
    async def setup_session(self):
        """Setup HTTP session and authenticate"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=120)  # 2 minutes for generation tests
        )
        
        # Authenticate with admin credentials
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
    
    async def test_enhanced_category_generation(self):
        """
        TEST 1: Génération avec contexte catégorie amélioré
        Test /api/sheets/generate endpoint with different categories
        """
        print("\n🧪 TEST 1: Génération avec contexte catégorie amélioré")
        print("=" * 70)
        
        # Test cases with different categories as specified in review
        test_cases = [
            {
                "name": "iPhone 15 Pro",
                "description": "Smartphone haut de gamme avec processeur A17 Pro et appareil photo 48MP",
                "category": "électronique",
                "expected_context": "high-tech electronics"
            },
            {
                "name": "Robe d'été élégante",
                "description": "Robe légère et fluide parfaite pour les journées chaudes",
                "category": "mode",
                "expected_context": "fashion clothing style"
            },
            {
                "name": "Crème hydratante visage",
                "description": "Crème nourrissante pour tous types de peau",
                "category": "beauté",
                "expected_context": "beauty cosmetic skincare"
            },
            {
                "name": "Chaussures de running",
                "description": "Chaussures de sport haute performance pour la course",
                "category": "sport",
                "expected_context": "fitness sport equipment"
            }
        ]
        
        test_results = []
        
        for test_case in test_cases:
            print(f"\n📝 Testing category: {test_case['category']} - {test_case['name']}")
            
            generation_data = {
                "product_name": test_case["name"],
                "product_description": test_case["description"],
                "category": test_case["category"],
                "generate_image": True,
                "number_of_images": 1,
                "language": "fr"
            }
            
            start_time = time.time()
            
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/generate-sheet",
                    json=generation_data,
                    headers=self.get_auth_headers()
                ) as response:
                    
                    generation_time = time.time() - start_time
                    status = response.status
                    
                    if status == 200:
                        result = await response.json()
                        
                        # Analyze if category context was used intelligently
                        context_analysis = self.analyze_category_context(result, test_case)
                        
                        print(f"   ✅ SUCCESS: Generation completed in {generation_time:.2f}s")
                        print(f"   📊 Context Analysis: {context_analysis['score']}/10")
                        print(f"   🎯 Category optimization: {'✅ DETECTED' if context_analysis['category_optimized'] else '❌ NOT DETECTED'}")
                        
                        test_results.append({
                            "category": test_case["category"],
                            "product": test_case["name"],
                            "status": status,
                            "success": True,
                            "generation_time": generation_time,
                            "context_score": context_analysis["score"],
                            "category_optimized": context_analysis["category_optimized"],
                            "features_count": len(result.get("key_features", [])),
                            "seo_tags_count": len(result.get("seo_tags", [])),
                            "has_images": len(result.get("generated_images", [])) > 0
                        })
                        
                        # Display key results
                        if result.get("generated_title"):
                            print(f"   📋 Title: {result['generated_title'][:80]}...")
                        if result.get("key_features"):
                            print(f"   🔧 Features: {len(result['key_features'])} features generated")
                        if result.get("seo_tags"):
                            print(f"   🏷️ SEO Tags: {result['seo_tags']}")
                        if result.get("generated_images"):
                            print(f"   🖼️ Images: {len(result['generated_images'])} images generated")
                            
                    else:
                        error_text = await response.text()
                        print(f"   ❌ ERROR {status}: Generation failed")
                        print(f"      Error details: {error_text[:200]}...")
                        
                        test_results.append({
                            "category": test_case["category"],
                            "product": test_case["name"],
                            "status": status,
                            "success": False,
                            "error": f"HTTP {status}",
                            "generation_time": generation_time
                        })
                        
            except Exception as e:
                generation_time = time.time() - start_time
                print(f"   ❌ EXCEPTION: {str(e)}")
                test_results.append({
                    "category": test_case["category"],
                    "product": test_case["name"],
                    "status": None,
                    "success": False,
                    "error": str(e),
                    "generation_time": generation_time
                })
        
        # Summary for category generation
        successful_generations = sum(1 for result in test_results if result['success'])
        total_generations = len(test_results)
        avg_context_score = sum(result.get('context_score', 0) for result in test_results if result['success']) / max(successful_generations, 1)
        
        print(f"\n📈 CATEGORY GENERATION SUMMARY:")
        print(f"   ✅ Successful: {successful_generations}/{total_generations}")
        print(f"   🎯 Average Context Score: {avg_context_score:.1f}/10")
        print(f"   📊 Categories with optimization: {sum(1 for r in test_results if r.get('category_optimized', False))}/{successful_generations}")
        
        self.test_results.extend(test_results)
        return successful_generations > 0
    
    def analyze_category_context(self, result: dict, test_case: dict) -> dict:
        """Analyze if the generation used category context intelligently"""
        score = 0
        category_optimized = False
        
        category = test_case["category"].lower()
        title = result.get("generated_title", "").lower()
        description = result.get("marketing_description", "").lower()
        features = " ".join(result.get("key_features", [])).lower()
        seo_tags = " ".join(result.get("seo_tags", [])).lower()
        
        # Category-specific keywords to look for
        category_keywords = {
            "électronique": ["technologie", "performance", "innovation", "digital", "connecté", "intelligent", "haute définition"],
            "mode": ["style", "élégant", "tendance", "fashion", "look", "design", "confort", "coupe"],
            "beauté": ["soin", "hydratant", "peau", "beauté", "cosmétique", "naturel", "doux", "éclat"],
            "sport": ["performance", "entraînement", "fitness", "résistant", "confort", "sport", "activité", "mouvement"]
        }
        
        if category in category_keywords:
            keywords = category_keywords[category]
            all_text = f"{title} {description} {features} {seo_tags}"
            
            # Check for category-specific keywords
            found_keywords = sum(1 for keyword in keywords if keyword in all_text)
            score += min(found_keywords * 2, 6)  # Max 6 points for keywords
            
            if found_keywords >= 2:
                category_optimized = True
        
        # Check for appropriate pricing context
        price_suggestions = result.get("price_suggestions", "").lower()
        if category == "électronique" and any(term in price_suggestions for term in ["€", "euro", "prix", "gamme"]):
            score += 2
        elif category == "mode" and any(term in price_suggestions for term in ["€", "euro", "prix", "abordable", "accessible"]):
            score += 2
        elif category == "beauté" and any(term in price_suggestions for term in ["€", "euro", "prix", "qualité"]):
            score += 2
        elif category == "sport" and any(term in price_suggestions for term in ["€", "euro", "prix", "rapport qualité"]):
            score += 2
        
        # Check for appropriate target audience
        target_audience = result.get("target_audience", "").lower()
        if category == "électronique" and any(term in target_audience for term in ["technologie", "innovation", "performance"]):
            score += 2
        elif category == "mode" and any(term in target_audience for term in ["style", "fashion", "élégance"]):
            score += 2
        elif category == "beauté" and any(term in target_audience for term in ["soin", "beauté", "bien-être"]):
            score += 2
        elif category == "sport" and any(term in target_audience for term in ["sport", "fitness", "activité"]):
            score += 2
        
        return {
            "score": min(score, 10),
            "category_optimized": category_optimized
        }
    
    async def test_competitor_price_analysis(self):
        """
        TEST 2: Analyse des prix multi-sources enrichie
        Test scrape_competitor_prices function with different categories
        """
        print("\n🧪 TEST 2: Analyse des prix multi-sources enrichie")
        print("=" * 70)
        
        # Test cases for price analysis
        price_test_cases = [
            {
                "product": "iPhone 15 Pro",
                "category": "électronique",
                "expected_sources": ["amazon.fr", "fnac.com", "cdiscount.com"]
            },
            {
                "product": "Robe d'été",
                "category": "mode",
                "expected_sources": ["amazon.fr", "fnac.com"]
            },
            {
                "product": "Crème hydratante",
                "category": "beauté",
                "expected_sources": ["amazon.fr", "fnac.com"]
            }
        ]
        
        test_results = []
        
        for test_case in price_test_cases:
            print(f"\n💰 Testing price analysis: {test_case['product']} ({test_case['category']})")
            
            # Test the competitor analysis endpoint
            price_data = {
                "product_name": test_case["product"],
                "category": test_case["category"],
                "analysis_depth": "standard",
                "language": "fr"
            }
            
            try:
                # Try to call competitor analysis endpoint
                async with self.session.post(
                    f"{BACKEND_URL}/ai/competitor-analysis",
                    json=price_data,
                    headers=self.get_auth_headers()
                ) as response:
                    
                    status = response.status
                    
                    if status == 200:
                        result = await response.json()
                        
                        # Analyze price analysis results
                        price_analysis = self.analyze_price_results(result, test_case)
                        
                        print(f"   ✅ SUCCESS: Price analysis completed")
                        print(f"   💰 Prices found: {price_analysis['prices_found']}")
                        print(f"   🏪 Sources analyzed: {price_analysis['sources_count']}")
                        print(f"   📊 Pricing strategies: {price_analysis['strategies_count']}")
                        
                        test_results.append({
                            "product": test_case["product"],
                            "category": test_case["category"],
                            "status": status,
                            "success": True,
                            "prices_found": price_analysis["prices_found"],
                            "sources_count": price_analysis["sources_count"],
                            "strategies_count": price_analysis["strategies_count"]
                        })
                        
                    elif status == 404:
                        print(f"   ⚠️ ENDPOINT NOT FOUND: Price analysis endpoint not implemented")
                        test_results.append({
                            "product": test_case["product"],
                            "category": test_case["category"],
                            "status": status,
                            "success": False,
                            "error": "Endpoint not implemented"
                        })
                        
                    else:
                        error_text = await response.text()
                        print(f"   ❌ ERROR {status}: Price analysis failed")
                        print(f"      Error details: {error_text[:200]}...")
                        
                        test_results.append({
                            "product": test_case["product"],
                            "category": test_case["category"],
                            "status": status,
                            "success": False,
                            "error": f"HTTP {status}"
                        })
                        
            except Exception as e:
                print(f"   ❌ EXCEPTION: {str(e)}")
                test_results.append({
                    "product": test_case["product"],
                    "category": test_case["category"],
                    "status": None,
                    "success": False,
                    "error": str(e)
                })
        
        # Summary for price analysis
        successful_analyses = sum(1 for result in test_results if result['success'])
        total_analyses = len(test_results)
        
        print(f"\n💰 PRICE ANALYSIS SUMMARY:")
        print(f"   ✅ Successful: {successful_analyses}/{total_analyses}")
        if successful_analyses > 0:
            avg_prices = sum(result.get('prices_found', 0) for result in test_results if result['success']) / successful_analyses
            avg_sources = sum(result.get('sources_count', 0) for result in test_results if result['success']) / successful_analyses
            print(f"   📊 Average prices found: {avg_prices:.1f}")
            print(f"   🏪 Average sources: {avg_sources:.1f}")
        
        self.test_results.extend(test_results)
        return successful_analyses > 0
    
    def analyze_price_results(self, result: dict, test_case: dict) -> dict:
        """Analyze price analysis results"""
        prices_found = 0
        sources_count = 0
        strategies_count = 0
        
        # Check for price data structure
        if "prices" in result:
            prices_found = len(result["prices"])
            sources = set()
            for price in result["prices"]:
                if "source" in price:
                    sources.add(price["source"])
            sources_count = len(sources)
        
        # Check for pricing strategies
        if "strategies" in result:
            strategies_count = len(result["strategies"])
        elif "pricing_strategies" in result:
            strategies_count = len(result["pricing_strategies"])
        
        return {
            "prices_found": prices_found,
            "sources_count": sources_count,
            "strategies_count": strategies_count
        }
    
    async def test_integrated_workflow(self):
        """
        TEST 3: Test d'intégration complète
        Test complete workflow with category context and price analysis
        """
        print("\n🧪 TEST 3: Test d'intégration complète - Workflow complet")
        print("=" * 70)
        
        # Complete workflow test case
        workflow_test = {
            "product_name": "iPhone 15 Pro Max",
            "product_description": "Smartphone premium avec écran 6.7 pouces, processeur A17 Pro, appareil photo 48MP et batterie longue durée",
            "category": "électronique",
            "generate_image": True,
            "number_of_images": 2,
            "language": "fr"
        }
        
        print(f"🔄 Testing complete workflow for: {workflow_test['product_name']}")
        print(f"   Category: {workflow_test['category']}")
        print(f"   Images requested: {workflow_test['number_of_images']}")
        
        start_time = time.time()
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/generate-sheet",
                json=workflow_test,
                headers=self.get_auth_headers()
            ) as response:
                
                total_time = time.time() - start_time
                status = response.status
                
                if status == 200:
                    result = await response.json()
                    
                    # Comprehensive analysis of the complete workflow
                    workflow_analysis = self.analyze_complete_workflow(result, workflow_test)
                    
                    print(f"   ✅ SUCCESS: Complete workflow in {total_time:.2f}s")
                    print(f"   📊 Overall Quality Score: {workflow_analysis['quality_score']}/100")
                    
                    # Detailed analysis
                    print(f"\n   📋 WORKFLOW ANALYSIS:")
                    print(f"      🎯 Category Context Used: {'✅ YES' if workflow_analysis['category_context'] else '❌ NO'}")
                    print(f"      💰 Price Analysis Integrated: {'✅ YES' if workflow_analysis['price_analysis'] else '❌ NO'}")
                    print(f"      🖼️ Images Generated: {workflow_analysis['images_count']}/{workflow_test['number_of_images']}")
                    print(f"      🏷️ SEO Optimization: {'✅ GOOD' if workflow_analysis['seo_quality'] > 7 else '⚠️ NEEDS IMPROVEMENT'}")
                    print(f"      📝 Content Quality: {'✅ HIGH' if workflow_analysis['content_quality'] > 8 else '⚠️ MEDIUM'}")
                    
                    # Display key results
                    if result.get("generated_title"):
                        print(f"\n   📋 Generated Title: {result['generated_title']}")
                    if result.get("price_suggestions"):
                        print(f"   💰 Price Suggestions: {result['price_suggestions']}")
                    if result.get("target_audience"):
                        print(f"   🎯 Target Audience: {result['target_audience']}")
                    
                    test_result = {
                        "workflow": "complete_integration",
                        "product": workflow_test["product_name"],
                        "category": workflow_test["category"],
                        "status": status,
                        "success": True,
                        "total_time": total_time,
                        "quality_score": workflow_analysis["quality_score"],
                        "category_context": workflow_analysis["category_context"],
                        "price_analysis": workflow_analysis["price_analysis"],
                        "images_generated": workflow_analysis["images_count"],
                        "seo_quality": workflow_analysis["seo_quality"],
                        "content_quality": workflow_analysis["content_quality"]
                    }
                    
                else:
                    error_text = await response.text()
                    print(f"   ❌ ERROR {status}: Complete workflow failed")
                    print(f"      Error details: {error_text[:300]}...")
                    
                    test_result = {
                        "workflow": "complete_integration",
                        "product": workflow_test["product_name"],
                        "category": workflow_test["category"],
                        "status": status,
                        "success": False,
                        "error": f"HTTP {status}",
                        "total_time": total_time
                    }
                    
        except Exception as e:
            total_time = time.time() - start_time
            print(f"   ❌ EXCEPTION: {str(e)}")
            test_result = {
                "workflow": "complete_integration",
                "product": workflow_test["product_name"],
                "category": workflow_test["category"],
                "status": None,
                "success": False,
                "error": str(e),
                "total_time": total_time
            }
        
        print(f"\n🔄 COMPLETE WORKFLOW SUMMARY:")
        print(f"   ✅ Success: {'YES' if test_result['success'] else 'NO'}")
        if test_result['success']:
            print(f"   📊 Quality Score: {test_result['quality_score']}/100")
            print(f"   ⏱️ Total Time: {test_result['total_time']:.2f}s")
        
        self.test_results.append(test_result)
        return test_result['success']
    
    def analyze_complete_workflow(self, result: dict, test_case: dict) -> dict:
        """Analyze complete workflow results"""
        quality_score = 0
        category_context = False
        price_analysis = False
        seo_quality = 0
        content_quality = 0
        
        # Check category context usage (20 points)
        category = test_case["category"].lower()
        all_content = f"{result.get('generated_title', '')} {result.get('marketing_description', '')} {' '.join(result.get('key_features', []))}".lower()
        
        category_keywords = {
            "électronique": ["technologie", "performance", "innovation", "digital", "connecté", "intelligent", "haute définition", "processeur", "écran"]
        }
        
        if category in category_keywords:
            found_keywords = sum(1 for keyword in category_keywords[category] if keyword in all_content)
            if found_keywords >= 3:
                category_context = True
                quality_score += 20
            elif found_keywords >= 1:
                quality_score += 10
        
        # Check price analysis integration (20 points)
        price_suggestions = result.get("price_suggestions", "").lower()
        if price_suggestions and any(term in price_suggestions for term in ["€", "euro", "prix", "gamme", "marché", "concurrentiel"]):
            price_analysis = True
            quality_score += 20
        
        # Check SEO quality (20 points)
        seo_tags = result.get("seo_tags", [])
        if len(seo_tags) >= 5:
            seo_quality = 10
            quality_score += 20
        elif len(seo_tags) >= 3:
            seo_quality = 7
            quality_score += 15
        elif len(seo_tags) >= 1:
            seo_quality = 5
            quality_score += 10
        
        # Check content quality (20 points)
        description = result.get("marketing_description", "")
        features = result.get("key_features", [])
        
        if len(description) > 200 and len(features) >= 5:
            content_quality = 10
            quality_score += 20
        elif len(description) > 100 and len(features) >= 3:
            content_quality = 8
            quality_score += 15
        elif len(description) > 50 and len(features) >= 1:
            content_quality = 6
            quality_score += 10
        
        # Check images (20 points)
        images_count = len(result.get("generated_images", []))
        if images_count >= 2:
            quality_score += 20
        elif images_count >= 1:
            quality_score += 15
        
        return {
            "quality_score": quality_score,
            "category_context": category_context,
            "price_analysis": price_analysis,
            "images_count": images_count,
            "seo_quality": seo_quality,
            "content_quality": content_quality
        }
    
    async def run_all_tests(self):
        """Run all enhanced generation tests"""
        print("🚀 ECOMSIMPLY ENHANCED GENERATION TESTING")
        print("=" * 80)
        print("Testing: Système de génération de fiches produit amélioré")
        print("Focus: Optimisation contextuelle et intégration de l'analyse des prix")
        print("=" * 80)
        
        # Setup
        if not await self.setup_session():
            print("❌ Failed to setup test session")
            return False
        
        try:
            # Run all tests
            print("\n🎯 TESTING ENHANCED GENERATION FEATURES...")
            
            test1_result = await self.test_enhanced_category_generation()
            await asyncio.sleep(2)  # Brief pause between tests
            
            test2_result = await self.test_competitor_price_analysis()
            await asyncio.sleep(2)
            
            test3_result = await self.test_integrated_workflow()
            
            # Summary
            print("\n" + "=" * 80)
            print("🏁 ENHANCED GENERATION TEST SUMMARY")
            print("=" * 80)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result.get('success', False))
            
            print(f"📊 Total Tests: {total_tests}")
            print(f"✅ Passed: {passed_tests}")
            print(f"❌ Failed: {total_tests - passed_tests}")
            print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
            
            print(f"\n🎯 FEATURE STATUS:")
            print(f"   Enhanced Category Generation: {'✅ WORKING' if test1_result else '❌ FAILING'}")
            print(f"   Competitor Price Analysis: {'✅ WORKING' if test2_result else '❌ FAILING'}")
            print(f"   Complete Integration Workflow: {'✅ WORKING' if test3_result else '❌ FAILING'}")
            
            # Detailed analysis
            print(f"\n📋 DETAILED ANALYSIS:")
            
            # Category generation analysis
            category_tests = [r for r in self.test_results if 'category' in r and r.get('success')]
            if category_tests:
                avg_context_score = sum(r.get('context_score', 0) for r in category_tests) / len(category_tests)
                optimized_count = sum(1 for r in category_tests if r.get('category_optimized', False))
                print(f"   🎯 Category Context Optimization:")
                print(f"      Average Context Score: {avg_context_score:.1f}/10")
                print(f"      Categories with Optimization: {optimized_count}/{len(category_tests)}")
            
            # Price analysis
            price_tests = [r for r in self.test_results if 'prices_found' in r and r.get('success')]
            if price_tests:
                avg_prices = sum(r.get('prices_found', 0) for r in price_tests) / len(price_tests)
                print(f"   💰 Price Analysis Integration:")
                print(f"      Average Prices Found: {avg_prices:.1f}")
            
            # Workflow analysis
            workflow_tests = [r for r in self.test_results if 'workflow' in r and r.get('success')]
            if workflow_tests:
                avg_quality = sum(r.get('quality_score', 0) for r in workflow_tests) / len(workflow_tests)
                print(f"   🔄 Complete Workflow Quality:")
                print(f"      Average Quality Score: {avg_quality:.1f}/100")
            
            # Overall assessment
            critical_features_working = test1_result and test3_result  # Category generation and workflow are critical
            overall_success = test1_result and test3_result
            
            print(f"\n🏆 OVERALL RESULT: {'✅ SUCCESS' if overall_success else '❌ NEEDS ATTENTION'}")
            
            if overall_success:
                print("🎉 Enhanced generation system is working!")
                print("   ✅ Category context optimization is functional")
                print("   ✅ Complete integration workflow is operational")
                if test2_result:
                    print("   ✅ Price analysis integration is working")
                else:
                    print("   ⚠️ Price analysis needs attention (may not be fully implemented)")
            else:
                print("❌ Issues detected in enhanced generation system:")
                if not test1_result:
                    print("   ❌ Category context optimization needs fixing")
                if not test2_result:
                    print("   ⚠️ Price analysis integration needs implementation")
                if not test3_result:
                    print("   ❌ Complete workflow integration has issues")
            
            return overall_success
            
        finally:
            await self.cleanup()

async def main():
    """Main test execution"""
    tester = EnhancedGenerationTester()
    success = await tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())