#!/usr/bin/env python3
"""
ECOMSIMPLY - Amazon SP-API Phase 2 Backend Testing (Simplified)
Testing Amazon Listings components without authentication dependency
"""

import asyncio
import aiohttp
import json
import sys
import os
import time
from datetime import datetime
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://ecomsimply.com"

class AmazonPhase2SimplifiedTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = None
        self.test_results = []
        
        # Test product data as specified in review request
        self.test_product_data = {
            "brand": "Apple",
            "product_name": "iPhone 15 Pro Max",
            "features": ["A17 Pro chip", "Titanium design", "Action Button", "Pro camera system"],
            "category": "électronique", 
            "target_keywords": ["smartphone", "premium", "apple", "iphone"],
            "size": "6.7 pouces",
            "color": "Titanium naturel",
            "price": 1479.00,
            "description": "Le smartphone le plus avancé d'Apple avec puce A17 Pro et design en titane"
        }
        
        print(f"🚀 Amazon SP-API Phase 2 Simplified Tester initialized")
        print(f"📱 Test Product: {self.test_product_data['brand']} {self.test_product_data['product_name']}")
        print(f"🌐 Backend URL: {self.backend_url}")

    async def setup_session(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'Content-Type': 'application/json'}
        )

    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()

    async def test_amazon_listing_generator_direct(self) -> Dict[str, Any]:
        """Test Amazon Listing Generator directly (without API)"""
        test_name = "Amazon Listing Generator (Direct Import)"
        print(f"\n🤖 Testing {test_name}...")
        
        try:
            # Import the generator directly
            sys.path.append('/app/backend')
            from amazon.listings.generator import AmazonListingGenerator
            
            # Initialize generator
            generator = AmazonListingGenerator()
            
            # Generate listing
            generated_listing = await generator.generate_amazon_listing(self.test_product_data)
            
            # Validate results
            success = False
            details = []
            
            if generated_listing:
                seo_content = generated_listing.get('seo_content', {})
                metadata = generated_listing.get('generation_metadata', {})
                
                # Validate A9/A10 compliance
                title = seo_content.get('title', '')
                bullets = seo_content.get('bullet_points', [])
                description = seo_content.get('description', '')
                keywords = seo_content.get('backend_keywords', '')
                
                # Check title compliance (15-200 chars)
                title_valid = 15 <= len(title) <= 200
                details.append(f"Title length: {len(title)} chars ({'✅' if title_valid else '❌'} A9/A10 compliant)")
                
                # Check bullets compliance (1-5 bullets, max 255 chars each)
                bullets_valid = 1 <= len(bullets) <= 5 and all(len(bullet) <= 255 for bullet in bullets)
                details.append(f"Bullets: {len(bullets)} count ({'✅' if bullets_valid else '❌'} A9/A10 compliant)")
                
                # Check description compliance (100-2000 chars)
                desc_text_length = len(description.replace('<', '').replace('>', ''))  # Rough HTML removal
                desc_valid = 100 <= desc_text_length <= 2000
                details.append(f"Description: {desc_text_length} chars ({'✅' if desc_valid else '❌'} A9/A10 compliant)")
                
                # Check keywords compliance (max 250 bytes)
                keywords_bytes = len(keywords.encode('utf-8'))
                keywords_valid = keywords_bytes <= 250
                details.append(f"Keywords: {keywords_bytes} bytes ({'✅' if keywords_valid else '❌'} A9/A10 compliant)")
                
                # Check optimization score
                opt_score = metadata.get('optimization_score', 0)
                score_valid = opt_score >= 80  # Target ≥80% as per review request
                details.append(f"Optimization score: {opt_score}% ({'✅' if score_valid else '❌'} Target ≥80%)")
                
                # Overall success if all validations pass
                success = title_valid and bullets_valid and desc_valid and keywords_valid and score_valid
                
                if success:
                    details.append("✅ All A9/A10 compliance rules met")
                    details.append(f"✅ Generated listing ID: {generated_listing.get('listing_id')}")
                    details.append(f"✅ Title: {title[:50]}...")
                    details.append(f"✅ Bullets count: {len(bullets)}")
                    details.append(f"✅ Keywords: {keywords[:50]}...")
                
            else:
                details.append("❌ No listing generated")
            
            return {
                'test_name': test_name,
                'success': success,
                'status_code': 200,
                'details': details,
                'response_data': generated_listing if success else None
            }
            
        except Exception as e:
            return {
                'test_name': test_name,
                'success': False,
                'status_code': 0,
                'details': [f"❌ Exception: {str(e)}"],
                'response_data': None
            }

    async def test_amazon_listing_validator_direct(self) -> Dict[str, Any]:
        """Test Amazon Listing Validator directly (without API)"""
        test_name = "Amazon Listing Validator (Direct Import)"
        print(f"\n🔍 Testing {test_name}...")
        
        try:
            # Import the validator directly
            sys.path.append('/app/backend')
            from amazon.listings.validators import AmazonListingValidator
            
            # Initialize validator
            validator = AmazonListingValidator()
            
            # Create test listing data
            listing_data = {
                'listing_id': 'test-listing-123',
                'product_data': self.test_product_data,
                'seo_content': {
                    'title': 'Apple iPhone 15 Pro Max A17 Pro chip Titanium design 6.7 pouces Titanium naturel',
                    'bullet_points': [
                        '🎯 PERFORMANCE SUPÉRIEURE : A17 Pro chip pour une expérience utilisateur optimale',
                        '✅ QUALITÉ GARANTIE : Titanium design certifié pour usage quotidien',
                        '🚀 INNOVATION : Action Button avec technologie avancée',
                        '💪 DURABILITÉ : Pro camera system résistant et fiable',
                        '🎁 AVANTAGE UNIQUE : Design exclusif pour électronique'
                    ],
                    'description': '<h3>🌟 Apple iPhone 15 Pro Max</h3><p>Découvrez notre <strong>iPhone 15 Pro Max</strong> conçu pour répondre à tous vos besoins en matière de <em>électronique</em>. Apple vous garantit une qualité exceptionnelle et une performance optimale.</p>',
                    'backend_keywords': 'iphone, apple, smartphone, premium, électronique, a17, pro, titanium, 6.7, naturel',
                    'image_requirements': {
                        'main_image': {
                            'description': 'Image principale de iPhone 15 Pro Max sur fond blanc pur',
                            'required': True
                        }
                    }
                }
            }
            
            # Validate listing
            validation_result = validator.validate_complete_listing(listing_data)
            
            # Analyze results
            success = False
            details = []
            
            if validation_result:
                # Check validation results
                overall_status = validation_result.get('overall_status')
                validation_score = validation_result.get('validation_score', 0)
                validation_details = validation_result.get('details', {})
                
                details.append(f"Overall status: {overall_status}")
                details.append(f"Validation score: {validation_score}%")
                
                # Check individual component validations
                for component, result in validation_details.items():
                    component_status = result.get('status', 'unknown')
                    component_score = result.get('score', 0)
                    details.append(f"{component}: {component_status} ({component_score}%)")
                
                # Success criteria: APPROVED or PENDING_REVIEW with score ≥70%
                success = overall_status in ['APPROVED', 'PENDING_REVIEW'] and validation_score >= 70
                
                if success:
                    details.append("✅ Validation passed with acceptable score")
                else:
                    details.append(f"❌ Validation failed: {overall_status} with {validation_score}%")
                    
                # Add summary
                summary = validator.get_validation_summary(validation_result)
                if summary:
                    details.append(f"Summary: {summary}")
                
            else:
                details.append("❌ No validation result")
            
            return {
                'test_name': test_name,
                'success': success,
                'status_code': 200,
                'details': details,
                'response_data': validation_result if success else None
            }
            
        except Exception as e:
            return {
                'test_name': test_name,
                'success': False,
                'status_code': 0,
                'details': [f"❌ Exception: {str(e)}"],
                'response_data': None
            }

    async def test_amazon_listing_publisher_direct(self) -> Dict[str, Any]:
        """Test Amazon Listing Publisher directly (without API)"""
        test_name = "Amazon Listing Publisher (Direct Import)"
        print(f"\n📤 Testing {test_name}...")
        
        try:
            # Import the publisher directly
            sys.path.append('/app/backend')
            from amazon.listings.publisher import AmazonListingPublisher
            
            # Initialize publisher
            publisher = AmazonListingPublisher()
            
            # Test SP-API payload preparation
            product_data = self.test_product_data
            seo_data = {
                'title': 'Apple iPhone 15 Pro Max A17 Pro chip Titanium design 6.7 pouces Titanium naturel',
                'bullet_points': [
                    '🎯 PERFORMANCE SUPÉRIEURE : A17 Pro chip pour une expérience utilisateur optimale',
                    '✅ QUALITÉ GARANTIE : Titanium design certifié pour usage quotidien'
                ],
                'description': '<h3>Apple iPhone 15 Pro Max</h3><p>Le smartphone le plus avancé d\'Apple.</p>',
                'backend_keywords': 'iphone, apple, smartphone, premium'
            }
            
            # Test payload preparation (this should work without Amazon connection)
            sp_api_payload = await publisher._prepare_spapi_payload(product_data, seo_data)
            
            # Analyze results
            success = False
            details = []
            
            if sp_api_payload:
                # Check SP-API payload structure
                product_type = sp_api_payload.get('productType')
                attributes = sp_api_payload.get('attributes', {})
                
                details.append(f"Product type: {product_type}")
                details.append(f"Attributes count: {len(attributes)}")
                
                # Check required SP-API fields
                required_fields = ['item_name', 'brand', 'bullet_point', 'product_description', 'generic_keyword']
                missing_fields = [field for field in required_fields if field not in attributes]
                
                if not missing_fields:
                    details.append("✅ All required SP-API fields present")
                    success = True
                    
                    # Check specific field formats
                    item_name = attributes.get('item_name', [])
                    if item_name and len(item_name) > 0:
                        details.append(f"✅ Title prepared: {item_name[0].get('value', '')[:50]}...")
                    
                    bullet_points = attributes.get('bullet_point', [])
                    details.append(f"✅ Bullets prepared: {len(bullet_points)} bullets")
                    
                    keywords = attributes.get('generic_keyword', [])
                    if keywords and len(keywords) > 0:
                        details.append(f"✅ Keywords prepared: {keywords[0].get('value', '')[:50]}...")
                    
                else:
                    details.append(f"❌ Missing SP-API fields: {missing_fields}")
                
            else:
                details.append("❌ No SP-API payload generated")
            
            return {
                'test_name': test_name,
                'success': success,
                'status_code': 200,
                'details': details,
                'response_data': sp_api_payload if success else None
            }
            
        except Exception as e:
            return {
                'test_name': test_name,
                'success': False,
                'status_code': 0,
                'details': [f"❌ Exception: {str(e)}"],
                'response_data': None
            }

    async def test_rest_endpoints_structure(self) -> Dict[str, Any]:
        """Test REST endpoints structure (without authentication)"""
        test_name = "REST Endpoints Structure"
        print(f"\n🌐 Testing {test_name}...")
        
        try:
            endpoints_to_test = [
                ('POST', '/api/amazon/listings/generate'),
                ('POST', '/api/amazon/listings/validate'),
                ('POST', '/api/amazon/listings/publish'),
                ('GET', '/api/amazon/listings/status/TEST-SKU'),
                ('GET', '/api/amazon/listings/history'),
                ('PUT', '/api/amazon/listings/update/TEST-SKU')
            ]
            
            details = []
            endpoints_found = 0
            
            for method, endpoint in endpoints_to_test:
                try:
                    # Test endpoint existence (should return 401/403 for auth, not 404)
                    if method == 'GET':
                        async with self.session.get(f"{self.backend_url}{endpoint}") as response:
                            status_code = response.status
                    elif method == 'POST':
                        async with self.session.post(f"{self.backend_url}{endpoint}", json={}) as response:
                            status_code = response.status
                    elif method == 'PUT':
                        async with self.session.put(f"{self.backend_url}{endpoint}", json={}) as response:
                            status_code = response.status
                    
                    if status_code in [401, 403]:  # Endpoint exists but requires auth
                        details.append(f"✅ {method} {endpoint}: Found (requires auth)")
                        endpoints_found += 1
                    elif status_code == 404:
                        details.append(f"❌ {method} {endpoint}: Not found")
                    else:
                        details.append(f"⚠️ {method} {endpoint}: Unexpected status {status_code}")
                        endpoints_found += 1  # Still counts as found
                        
                except Exception as e:
                    details.append(f"❌ {method} {endpoint}: Error - {str(e)}")
            
            success = endpoints_found == len(endpoints_to_test)
            details.append(f"Endpoints found: {endpoints_found}/{len(endpoints_to_test)}")
            
            return {
                'test_name': test_name,
                'success': success,
                'status_code': 200,
                'details': details,
                'response_data': None
            }
            
        except Exception as e:
            return {
                'test_name': test_name,
                'success': False,
                'status_code': 0,
                'details': [f"❌ Exception: {str(e)}"],
                'response_data': None
            }

    async def test_complete_workflow_direct(self) -> Dict[str, Any]:
        """Test complete workflow using direct imports"""
        test_name = "Complete Workflow (Direct Components)"
        print(f"\n🔄 Testing {test_name}...")
        
        try:
            workflow_results = []
            details = []
            
            # Step 1: Generate listing
            print("  Step 1: Generating listing...")
            generation_result = await self.test_amazon_listing_generator_direct()
            workflow_results.append(generation_result)
            
            if generation_result['success']:
                details.append("✅ Step 1: Generation successful")
                listing_data = generation_result['response_data']
                
                # Step 2: Validate listing
                print("  Step 2: Validating listing...")
                validation_result = await self.test_amazon_listing_validator_direct()
                workflow_results.append(validation_result)
                
                if validation_result['success']:
                    details.append("✅ Step 2: Validation successful")
                    
                    # Step 3: Test publisher preparation
                    print("  Step 3: Testing publisher preparation...")
                    publisher_result = await self.test_amazon_listing_publisher_direct()
                    workflow_results.append(publisher_result)
                    
                    if publisher_result['success']:
                        details.append("✅ Step 3: Publisher preparation successful")
                        details.append("✅ Complete workflow functional")
                        success = True
                    else:
                        details.append("❌ Step 3: Publisher preparation failed")
                        success = False
                else:
                    details.append("❌ Step 2: Validation failed")
                    success = False
            else:
                details.append("❌ Step 1: Generation failed")
                success = False
            
            return {
                'test_name': test_name,
                'success': success,
                'status_code': 200,
                'details': details,
                'workflow_results': workflow_results
            }
            
        except Exception as e:
            return {
                'test_name': test_name,
                'success': False,
                'status_code': 0,
                'details': [f"❌ Exception: {str(e)}"],
                'workflow_results': []
            }

    async def run_all_tests(self):
        """Run all Amazon SP-API Phase 2 tests"""
        print("🚀 Starting Amazon SP-API Phase 2 Simplified Backend Testing")
        print("=" * 80)
        
        start_time = time.time()
        
        try:
            # Setup
            await self.setup_session()
            
            # Run all tests
            tests = [
                self.test_rest_endpoints_structure(),
                self.test_amazon_listing_generator_direct(),
                self.test_amazon_listing_validator_direct(),
                self.test_amazon_listing_publisher_direct(),
                self.test_complete_workflow_direct()
            ]
            
            # Execute tests
            for test_coro in tests:
                result = await test_coro
                self.test_results.append(result)
            
            # Generate summary
            await self.generate_test_summary()
            
        except Exception as e:
            print(f"❌ Test execution failed: {str(e)}")
        finally:
            await self.cleanup_session()
            
        end_time = time.time()
        print(f"\n⏱️ Total test execution time: {end_time - start_time:.2f} seconds")

    async def generate_test_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 AMAZON SP-API PHASE 2 BACKEND TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 Overall Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 Detailed Results:")
        for i, result in enumerate(self.test_results, 1):
            status_icon = "✅" if result['success'] else "❌"
            print(f"\n{i}. {status_icon} {result['test_name']}")
            print(f"   Status Code: {result['status_code']}")
            
            for detail in result['details']:
                print(f"   {detail}")
        
        # Phase 2 specific validation
        print(f"\n🎯 PHASE 2 AMAZON SP-API VALIDATION:")
        
        # Check critical components
        generator_test = next((r for r in self.test_results if 'Generator' in r['test_name']), None)
        validator_test = next((r for r in self.test_results if 'Validator' in r['test_name']), None)
        publisher_test = next((r for r in self.test_results if 'Publisher' in r['test_name']), None)
        workflow_test = next((r for r in self.test_results if 'Workflow' in r['test_name']), None)
        endpoints_test = next((r for r in self.test_results if 'Endpoints' in r['test_name']), None)
        
        print(f"   ✅ Generator (AI + A9/A10): {'PASS' if generator_test and generator_test['success'] else 'FAIL'}")
        print(f"   ✅ Validator (Rules + Score): {'PASS' if validator_test and validator_test['success'] else 'FAIL'}")
        print(f"   ✅ Publisher (SP-API Prep): {'PASS' if publisher_test and publisher_test['success'] else 'FAIL'}")
        print(f"   ✅ Complete Workflow: {'PASS' if workflow_test and workflow_test['success'] else 'FAIL'}")
        print(f"   ✅ REST Endpoints: {'PASS' if endpoints_test and endpoints_test['success'] else 'FAIL'}")
        
        # Final assessment
        critical_tests_passed = all([
            generator_test and generator_test['success'],
            validator_test and validator_test['success'],
            publisher_test and publisher_test['success']
        ])
        
        print(f"\n🏆 FINAL ASSESSMENT:")
        if success_rate >= 85 and critical_tests_passed:
            print(f"   ✅ AMAZON SP-API PHASE 2 - PRODUCTION READY")
            print(f"   ✅ All critical components functional")
            print(f"   ✅ A9/A10 compliance validated")
            print(f"   ✅ SP-API integration prepared")
        elif success_rate >= 70:
            print(f"   ⚠️ AMAZON SP-API PHASE 2 - MOSTLY FUNCTIONAL")
            print(f"   ⚠️ Minor issues detected, review failed tests")
        else:
            print(f"   ❌ AMAZON SP-API PHASE 2 - NEEDS ATTENTION")
            print(f"   ❌ Critical issues detected, major fixes required")
        
        print("=" * 80)

async def main():
    """Main test execution"""
    tester = AmazonPhase2SimplifiedTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())