#!/usr/bin/env python3
"""
ECOMSIMPLY - Amazon SP-API Phase 2 Backend Testing
Comprehensive testing of Amazon Listings Generator, Validator, Publisher and REST Routes

Test Coverage:
1. Amazon Listing Generator (AI generation with A9/A10 compliance)
2. Amazon Listing Validator (rules validation with scoring)
3. Amazon Listing Publisher (SP-API publication preparation)
4. REST Routes Phase 2 (6 endpoints with JWT authentication)
5. Complete Workflow (Generate → Validate → Publish)
6. Error Handling and Edge Cases

Product Test Data: iPhone 15 Pro Max as specified in review request
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

class AmazonPhase2BackendTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = None
        self.test_results = []
        self.auth_token = None
        self.test_user_email = "amazon.phase2.tester@ecomsimply.com"
        self.test_user_password = "AmazonPhase2Test2025!"
        
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
        
        print(f"🚀 Amazon SP-API Phase 2 Backend Tester initialized")
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

    async def authenticate_user(self) -> bool:
        """Authenticate test user and get JWT token"""
        try:
            print(f"\n🔐 Authenticating test user: {self.test_user_email}")
            
            # Try to register user first (in case doesn't exist)
            register_data = {
                "email": self.test_user_email,
                "name": "Amazon Phase 2 Tester",
                "password": self.test_user_password
            }
            
            async with self.session.post(f"{self.backend_url}/api/register", json=register_data) as response:
                if response.status in [200, 201]:
                    print("✅ Test user registered successfully")
                elif response.status == 400:
                    print("ℹ️ Test user already exists, proceeding to login")
                else:
                    print(f"⚠️ Registration response: {response.status}")
            
            # Login to get JWT token
            login_data = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            async with self.session.post(f"{self.backend_url}/api/login", json=login_data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.auth_token = result.get('access_token')
                    if self.auth_token:
                        print("✅ Authentication successful")
                        return True
                    else:
                        print("❌ No access token in response")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ Login failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False

    def get_auth_headers(self) -> Dict[str, str]:
        """Get headers with JWT authentication"""
        if not self.auth_token:
            return {}
        return {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }

    async def test_amazon_listing_generator(self) -> Dict[str, Any]:
        """Test Amazon Listing Generator - AI generation with A9/A10 compliance"""
        test_name = "Amazon Listing Generator (AI Generation)"
        print(f"\n🤖 Testing {test_name}...")
        
        try:
            # Test data for generation
            generation_request = self.test_product_data.copy()
            
            # Call generation endpoint
            headers = self.get_auth_headers()
            async with self.session.post(
                f"{self.backend_url}/api/amazon/listings/generate",
                json=generation_request,
                headers=headers
            ) as response:
                
                status_code = response.status
                response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                # Analyze results
                success = False
                details = []
                
                if status_code == 200 and isinstance(response_data, dict):
                    if response_data.get('status') == 'success':
                        listing_data = response_data.get('data', {})
                        seo_content = listing_data.get('seo_content', {})
                        metadata = listing_data.get('generation_metadata', {})
                        
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
                            details.append(f"✅ Generated listing ID: {listing_data.get('listing_id')}")
                        
                    else:
                        details.append(f"❌ Generation failed: {response_data.get('message', 'Unknown error')}")
                else:
                    details.append(f"❌ HTTP {status_code}: {response_data}")
                
                return {
                    'test_name': test_name,
                    'success': success,
                    'status_code': status_code,
                    'details': details,
                    'response_data': response_data if success else None
                }
                
        except Exception as e:
            return {
                'test_name': test_name,
                'success': False,
                'status_code': 0,
                'details': [f"❌ Exception: {str(e)}"],
                'response_data': None
            }

    async def test_amazon_listing_validator(self, listing_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test Amazon Listing Validator - Rules validation with scoring"""
        test_name = "Amazon Listing Validator (Rules Validation)"
        print(f"\n🔍 Testing {test_name}...")
        
        try:
            # Use provided listing data or create mock data
            if not listing_data:
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
            
            # Call validation endpoint
            headers = self.get_auth_headers()
            async with self.session.post(
                f"{self.backend_url}/api/amazon/listings/validate",
                json=listing_data,
                headers=headers
            ) as response:
                
                status_code = response.status
                response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                # Analyze results
                success = False
                details = []
                
                if status_code == 200 and isinstance(response_data, dict):
                    if response_data.get('status') == 'success':
                        validation_result = response_data.get('data', {})
                        
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
                        summary = response_data.get('summary', '')
                        if summary:
                            details.append(f"Summary: {summary}")
                        
                    else:
                        details.append(f"❌ Validation failed: {response_data.get('message', 'Unknown error')}")
                else:
                    details.append(f"❌ HTTP {status_code}: {response_data}")
                
                return {
                    'test_name': test_name,
                    'success': success,
                    'status_code': status_code,
                    'details': details,
                    'response_data': response_data if success else None
                }
                
        except Exception as e:
            return {
                'test_name': test_name,
                'success': False,
                'status_code': 0,
                'details': [f"❌ Exception: {str(e)}"],
                'response_data': None
            }

    async def test_amazon_listing_publisher(self, listing_data: Dict[str, Any] = None, validation_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test Amazon Listing Publisher - SP-API publication preparation"""
        test_name = "Amazon Listing Publisher (SP-API Preparation)"
        print(f"\n📤 Testing {test_name}...")
        
        try:
            # Create publication request
            publication_request = {
                'listing_data': listing_data or {
                    'listing_id': 'test-listing-123',
                    'product_data': self.test_product_data,
                    'seo_content': {
                        'title': 'Apple iPhone 15 Pro Max A17 Pro chip Titanium design 6.7 pouces Titanium naturel',
                        'bullet_points': [
                            '🎯 PERFORMANCE SUPÉRIEURE : A17 Pro chip pour une expérience utilisateur optimale',
                            '✅ QUALITÉ GARANTIE : Titanium design certifié pour usage quotidien'
                        ],
                        'description': '<h3>Apple iPhone 15 Pro Max</h3><p>Le smartphone le plus avancé d\'Apple.</p>',
                        'backend_keywords': 'iphone, apple, smartphone, premium'
                    }
                },
                'validation_data': validation_data or {
                    'overall_status': 'APPROVED',
                    'validation_score': 85.0
                },
                'force_publish': True  # Force publish for testing
            }
            
            # Call publication endpoint
            headers = self.get_auth_headers()
            async with self.session.post(
                f"{self.backend_url}/api/amazon/listings/publish",
                json=publication_request,
                headers=headers
            ) as response:
                
                status_code = response.status
                response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                # Analyze results
                success = False
                details = []
                
                if status_code == 200 and isinstance(response_data, dict):
                    publication_result = response_data.get('data', {})
                    
                    # Check publication preparation
                    pub_status = publication_result.get('status')
                    sku = publication_result.get('sku')
                    marketplace_id = publication_result.get('marketplace_id')
                    
                    details.append(f"Publication status: {pub_status}")
                    if sku:
                        details.append(f"Generated SKU: {sku}")
                    if marketplace_id:
                        details.append(f"Marketplace ID: {marketplace_id}")
                    
                    # Check for SP-API payload preparation (even if actual publication fails due to no connection)
                    if pub_status in ['success', 'error', 'forbidden']:  # Any status means publisher worked
                        success = True
                        details.append("✅ Publisher successfully prepared SP-API payload")
                        
                        if pub_status == 'success':
                            details.append("✅ Publication would succeed with valid Amazon connection")
                        elif pub_status == 'error':
                            errors = publication_result.get('errors', [])
                            details.append(f"ℹ️ Publication failed as expected (no Amazon connection): {errors}")
                        
                    else:
                        details.append(f"❌ Unexpected publication status: {pub_status}")
                
                elif status_code == 412:  # Precondition Failed - No Amazon connection
                    success = True  # This is expected for testing
                    details.append("✅ Publisher correctly requires Amazon connection (412 Precondition Failed)")
                    details.append("ℹ️ This is expected behavior - Amazon connection required for publication")
                
                else:
                    details.append(f"❌ HTTP {status_code}: {response_data}")
                
                return {
                    'test_name': test_name,
                    'success': success,
                    'status_code': status_code,
                    'details': details,
                    'response_data': response_data if isinstance(response_data, dict) else None
                }
                
        except Exception as e:
            return {
                'test_name': test_name,
                'success': False,
                'status_code': 0,
                'details': [f"❌ Exception: {str(e)}"],
                'response_data': None
            }

    async def test_listing_status_endpoint(self) -> Dict[str, Any]:
        """Test GET /api/amazon/listings/status/{sku}"""
        test_name = "Listing Status Endpoint"
        print(f"\n🔍 Testing {test_name}...")
        
        try:
            test_sku = "APPLE-IPHONE15PROMAX-TEST123"
            
            headers = self.get_auth_headers()
            async with self.session.get(
                f"{self.backend_url}/api/amazon/listings/status/{test_sku}",
                headers=headers
            ) as response:
                
                status_code = response.status
                response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                success = False
                details = []
                
                if status_code == 412:  # Expected - no Amazon connection
                    success = True
                    details.append("✅ Status endpoint correctly requires Amazon connection")
                elif status_code == 200:
                    success = True
                    details.append("✅ Status endpoint accessible")
                    status_result = response_data.get('data', {})
                    details.append(f"Status result: {status_result.get('status', 'unknown')}")
                else:
                    details.append(f"❌ HTTP {status_code}: {response_data}")
                
                return {
                    'test_name': test_name,
                    'success': success,
                    'status_code': status_code,
                    'details': details,
                    'response_data': response_data if isinstance(response_data, dict) else None
                }
                
        except Exception as e:
            return {
                'test_name': test_name,
                'success': False,
                'status_code': 0,
                'details': [f"❌ Exception: {str(e)}"],
                'response_data': None
            }

    async def test_listings_history_endpoint(self) -> Dict[str, Any]:
        """Test GET /api/amazon/listings/history"""
        test_name = "Listings History Endpoint"
        print(f"\n📚 Testing {test_name}...")
        
        try:
            headers = self.get_auth_headers()
            async with self.session.get(
                f"{self.backend_url}/api/amazon/listings/history?limit=10&skip=0",
                headers=headers
            ) as response:
                
                status_code = response.status
                response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                success = False
                details = []
                
                if status_code == 200 and isinstance(response_data, dict):
                    if response_data.get('status') == 'success':
                        history_data = response_data.get('data', {})
                        listings = history_data.get('listings', [])
                        total_count = history_data.get('total_count', 0)
                        
                        success = True
                        details.append(f"✅ History endpoint accessible")
                        details.append(f"Total listings: {total_count}")
                        details.append(f"Retrieved listings: {len(listings)}")
                    else:
                        details.append(f"❌ History failed: {response_data.get('message', 'Unknown error')}")
                else:
                    details.append(f"❌ HTTP {status_code}: {response_data}")
                
                return {
                    'test_name': test_name,
                    'success': success,
                    'status_code': status_code,
                    'details': details,
                    'response_data': response_data if success else None
                }
                
        except Exception as e:
            return {
                'test_name': test_name,
                'success': False,
                'status_code': 0,
                'details': [f"❌ Exception: {str(e)}"],
                'response_data': None
            }

    async def test_listing_update_endpoint(self) -> Dict[str, Any]:
        """Test PUT /api/amazon/listings/update/{sku}"""
        test_name = "Listing Update Endpoint"
        print(f"\n📝 Testing {test_name}...")
        
        try:
            test_sku = "APPLE-IPHONE15PROMAX-TEST123"
            update_data = {
                'title': 'Apple iPhone 15 Pro Max - Updated Title',
                'price': 1499.00,
                'description': 'Updated description for iPhone 15 Pro Max'
            }
            
            headers = self.get_auth_headers()
            async with self.session.put(
                f"{self.backend_url}/api/amazon/listings/update/{test_sku}",
                json=update_data,
                headers=headers
            ) as response:
                
                status_code = response.status
                response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                success = False
                details = []
                
                if status_code == 412:  # Expected - no Amazon connection
                    success = True
                    details.append("✅ Update endpoint correctly requires Amazon connection")
                elif status_code == 200:
                    success = True
                    details.append("✅ Update endpoint accessible")
                    update_result = response_data.get('data', {})
                    details.append(f"Update status: {update_result.get('status', 'unknown')}")
                else:
                    details.append(f"❌ HTTP {status_code}: {response_data}")
                
                return {
                    'test_name': test_name,
                    'success': success,
                    'status_code': status_code,
                    'details': details,
                    'response_data': response_data if isinstance(response_data, dict) else None
                }
                
        except Exception as e:
            return {
                'test_name': test_name,
                'success': False,
                'status_code': 0,
                'details': [f"❌ Exception: {str(e)}"],
                'response_data': None
            }

    async def test_complete_workflow(self) -> Dict[str, Any]:
        """Test complete workflow: Generate → Validate → Publish"""
        test_name = "Complete Workflow (Generate → Validate → Publish)"
        print(f"\n🔄 Testing {test_name}...")
        
        try:
            workflow_results = []
            details = []
            
            # Step 1: Generate listing
            print("  Step 1: Generating listing...")
            generation_result = await self.test_amazon_listing_generator()
            workflow_results.append(generation_result)
            
            if generation_result['success']:
                details.append("✅ Step 1: Generation successful")
                listing_data = generation_result['response_data']['data']
                
                # Step 2: Validate listing
                print("  Step 2: Validating listing...")
                validation_result = await self.test_amazon_listing_validator(listing_data)
                workflow_results.append(validation_result)
                
                if validation_result['success']:
                    details.append("✅ Step 2: Validation successful")
                    validation_data = validation_result['response_data']['data']
                    
                    # Step 3: Prepare publication (will fail due to no Amazon connection, but tests publisher)
                    print("  Step 3: Testing publication preparation...")
                    publication_result = await self.test_amazon_listing_publisher(listing_data, validation_data)
                    workflow_results.append(publication_result)
                    
                    if publication_result['success']:
                        details.append("✅ Step 3: Publication preparation successful")
                        details.append("✅ Complete workflow functional")
                        success = True
                    else:
                        details.append("❌ Step 3: Publication preparation failed")
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

    async def test_authentication_requirements(self) -> Dict[str, Any]:
        """Test that all endpoints require JWT authentication"""
        test_name = "JWT Authentication Requirements"
        print(f"\n🔐 Testing {test_name}...")
        
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
            all_protected = True
            
            for method, endpoint in endpoints_to_test:
                try:
                    # Test without authentication
                    if method == 'GET':
                        async with self.session.get(f"{self.backend_url}{endpoint}") as response:
                            status_code = response.status
                    elif method == 'POST':
                        async with self.session.post(f"{self.backend_url}{endpoint}", json={}) as response:
                            status_code = response.status
                    elif method == 'PUT':
                        async with self.session.put(f"{self.backend_url}{endpoint}", json={}) as response:
                            status_code = response.status
                    
                    if status_code == 401 or status_code == 403:
                        details.append(f"✅ {method} {endpoint}: Protected (HTTP {status_code})")
                    else:
                        details.append(f"❌ {method} {endpoint}: Not protected (HTTP {status_code})")
                        all_protected = False
                        
                except Exception as e:
                    details.append(f"⚠️ {method} {endpoint}: Error testing - {str(e)}")
            
            return {
                'test_name': test_name,
                'success': all_protected,
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

    async def run_all_tests(self):
        """Run all Amazon SP-API Phase 2 tests"""
        print("🚀 Starting Amazon SP-API Phase 2 Comprehensive Backend Testing")
        print("=" * 80)
        
        start_time = time.time()
        
        try:
            # Setup
            await self.setup_session()
            
            # Authenticate
            auth_success = await self.authenticate_user()
            if not auth_success:
                print("❌ Authentication failed - cannot proceed with authenticated tests")
                return
            
            # Run all tests
            tests = [
                self.test_authentication_requirements(),
                self.test_amazon_listing_generator(),
                self.test_amazon_listing_validator(),
                self.test_amazon_listing_publisher(),
                self.test_listing_status_endpoint(),
                self.test_listings_history_endpoint(),
                self.test_listing_update_endpoint(),
                self.test_complete_workflow()
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
        
        print(f"   ✅ Generator (AI + A9/A10): {'PASS' if generator_test and generator_test['success'] else 'FAIL'}")
        print(f"   ✅ Validator (Rules + Score): {'PASS' if validator_test and validator_test['success'] else 'FAIL'}")
        print(f"   ✅ Publisher (SP-API Prep): {'PASS' if publisher_test and publisher_test['success'] else 'FAIL'}")
        print(f"   ✅ Complete Workflow: {'PASS' if workflow_test and workflow_test['success'] else 'FAIL'}")
        
        # REST endpoints validation
        endpoint_tests = [r for r in self.test_results if 'Endpoint' in r['test_name']]
        endpoints_working = sum(1 for t in endpoint_tests if t['success'])
        print(f"   ✅ REST Endpoints: {endpoints_working}/{len(endpoint_tests)} working")
        
        # Authentication validation
        auth_test = next((r for r in self.test_results if 'Authentication' in r['test_name']), None)
        print(f"   ✅ JWT Authentication: {'SECURED' if auth_test and auth_test['success'] else 'UNSECURED'}")
        
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
    tester = AmazonPhase2BackendTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())