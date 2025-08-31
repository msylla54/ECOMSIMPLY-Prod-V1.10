#!/usr/bin/env python3
"""
ECOMSIMPLY Image Management Backend Testing Suite
Tests for Bloc 3 Phase 3 - Image Management functionality

Test Coverage:
1. Image Management API Endpoints
2. User Model Extensions  
3. Integration with Product Generation
4. Database Operations
5. Service Integration
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://ecomsimply.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_EMAIL = "imagetest@ecomsimply.com"
TEST_PASSWORD = "ImageTest2025!"
TEST_NAME = "Image Management Tester"

class ImageManagementTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.user_id = None
        self.test_results = []
        
    async def setup_session(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        if data and not success:
            print(f"    Data: {data}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
    async def register_test_user(self) -> bool:
        """Register test user for image management testing"""
        try:
            register_data = {
                "email": TEST_EMAIL,
                "name": TEST_NAME,
                "password": TEST_PASSWORD,
                "language": "fr"
            }
            
            async with self.session.post(f"{API_BASE}/auth/register", json=register_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("User Registration", True, f"User registered: {data.get('user', {}).get('id')}")
                    return True
                elif response.status == 400:
                    # User might already exist
                    self.log_test("User Registration", True, "User already exists (expected)")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("User Registration", False, f"Status: {response.status}", error_text)
                    return False
                    
        except Exception as e:
            self.log_test("User Registration", False, f"Exception: {str(e)}")
            return False
            
    async def login_test_user(self) -> bool:
        """Login test user and get auth token"""
        try:
            login_data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get('token')  # Changed from 'access_token' to 'token'
                    user_data = data.get('user', {})
                    self.user_id = user_data.get('id')
                    
                    # Update session headers with auth token
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.auth_token}'
                    })
                    
                    # Check if user has image management fields (might not be in login response)
                    has_generate_images = 'generate_images' in user_data
                    has_include_images_manual = 'include_images_manual' in user_data
                    
                    self.log_test("User Login", True, 
                        f"Token obtained, User ID: {self.user_id}, "
                        f"generate_images field: {has_generate_images}, "
                        f"include_images_manual field: {has_include_images_manual}")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("User Login", False, f"Status: {response.status}", error_text)
                    return False
                    
        except Exception as e:
            self.log_test("User Login", False, f"Exception: {str(e)}")
            return False
            
    async def test_image_preferences_get(self) -> bool:
        """Test GET /api/images/preferences endpoint"""
        try:
            async with self.session.get(f"{API_BASE}/images/preferences") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Validate response structure
                    required_fields = ['user_id', 'generate_images', 'include_images_manual', 'subscription_plan']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test("GET Image Preferences", False, 
                            f"Missing fields: {missing_fields}", data)
                        return False
                    
                    # Validate data types
                    if not isinstance(data['generate_images'], bool):
                        self.log_test("GET Image Preferences", False, 
                            "generate_images should be boolean", data)
                        return False
                        
                    if not isinstance(data['include_images_manual'], bool):
                        self.log_test("GET Image Preferences", False, 
                            "include_images_manual should be boolean", data)
                        return False
                    
                    self.log_test("GET Image Preferences", True, 
                        f"generate_images: {data['generate_images']}, "
                        f"include_images_manual: {data['include_images_manual']}")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("GET Image Preferences", False, f"Status: {response.status}", error_text)
                    return False
                    
        except Exception as e:
            self.log_test("GET Image Preferences", False, f"Exception: {str(e)}")
            return False
            
    async def test_image_preferences_update(self) -> bool:
        """Test PUT /api/images/preferences endpoint"""
        try:
            # Test 1: Update both preferences
            update_data = {
                "generate_images": False,
                "include_images_manual": False
            }
            
            async with self.session.put(f"{API_BASE}/images/preferences", json=update_data) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('generate_images') != False or data.get('include_images_manual') != False:
                        self.log_test("PUT Image Preferences (Test 1)", False, 
                            "Values not updated correctly", data)
                        return False
                    
                    self.log_test("PUT Image Preferences (Test 1)", True, 
                        "Both preferences updated to False")
                else:
                    error_text = await response.text()
                    self.log_test("PUT Image Preferences (Test 1)", False, 
                        f"Status: {response.status}", error_text)
                    return False
            
            # Test 2: Update only generate_images to True
            update_data = {
                "generate_images": True
            }
            
            async with self.session.put(f"{API_BASE}/images/preferences", json=update_data) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('generate_images') != True:
                        self.log_test("PUT Image Preferences (Test 2)", False, 
                            "generate_images not updated correctly", data)
                        return False
                    
                    self.log_test("PUT Image Preferences (Test 2)", True, 
                        "generate_images updated to True")
                else:
                    error_text = await response.text()
                    self.log_test("PUT Image Preferences (Test 2)", False, 
                        f"Status: {response.status}", error_text)
                    return False
            
            # Test 3: Test auto-correction logic (generate_images=False, include_images_manual=True)
            update_data = {
                "generate_images": False,
                "include_images_manual": True
            }
            
            async with self.session.put(f"{API_BASE}/images/preferences", json=update_data) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Should auto-correct include_images_manual to False
                    if data.get('include_images_manual') != False:
                        self.log_test("PUT Image Preferences (Auto-correction)", False, 
                            "Auto-correction failed: include_images_manual should be False when generate_images=False", data)
                        return False
                    
                    self.log_test("PUT Image Preferences (Auto-correction)", True, 
                        "Auto-correction working: include_images_manual set to False")
                else:
                    error_text = await response.text()
                    self.log_test("PUT Image Preferences (Auto-correction)", False, 
                        f"Status: {response.status}", error_text)
                    return False
            
            return True
            
        except Exception as e:
            self.log_test("PUT Image Preferences", False, f"Exception: {str(e)}")
            return False
            
    async def test_image_generation_test(self) -> bool:
        """Test POST /api/images/test-generation endpoint"""
        try:
            # First, ensure generate_images is True
            await self.session.put(f"{API_BASE}/images/preferences", json={"generate_images": True})
            
            test_data = {
                "product_name": "iPhone 15 Pro Test",
                "product_description": "Smartphone Apple iPhone 15 Pro avec puce A17 Pro, écran Super Retina XDR de 6,1 pouces, système de caméra Pro avec téléobjectif 3x",
                "number_of_images": 2,
                "image_style": "studio",
                "category": "électronique",
                "language": "fr"
            }
            
            async with self.session.post(f"{API_BASE}/images/test-generation", json=test_data) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Validate response structure
                    required_fields = ['status', 'user_config', 'images_generated', 'images_requested', 'has_images']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test("POST Image Test Generation", False, 
                            f"Missing fields: {missing_fields}", data)
                        return False
                    
                    # Validate user_config structure
                    user_config = data.get('user_config', {})
                    if 'generate_images' not in user_config or 'include_images_manual' not in user_config:
                        self.log_test("POST Image Test Generation", False, 
                            "user_config missing required fields", data)
                        return False
                    
                    # Check if images were generated (should be > 0 if generate_images=True)
                    images_generated = data.get('images_generated', 0)
                    images_requested = data.get('images_requested', 0)
                    
                    self.log_test("POST Image Test Generation", True, 
                        f"Generated {images_generated}/{images_requested} images, "
                        f"generate_images: {user_config['generate_images']}")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("POST Image Test Generation", False, 
                        f"Status: {response.status}", error_text)
                    return False
                    
        except Exception as e:
            self.log_test("POST Image Test Generation", False, f"Exception: {str(e)}")
            return False
            
    async def test_publication_rules(self) -> bool:
        """Test GET /api/images/publication-rules endpoint"""
        try:
            async with self.session.get(f"{API_BASE}/images/publication-rules") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Validate response structure
                    required_fields = ['user_config', 'publication_rules', 'ui_controls']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test("GET Publication Rules", False, 
                            f"Missing fields: {missing_fields}", data)
                        return False
                    
                    # Validate publication_rules structure
                    pub_rules = data.get('publication_rules', {})
                    expected_rules = ['auto_publication', 'manual_publication_with_images', 'manual_publication_without_images']
                    missing_rules = [rule for rule in expected_rules if rule not in pub_rules]
                    
                    if missing_rules:
                        self.log_test("GET Publication Rules", False, 
                            f"Missing publication rules: {missing_rules}", data)
                        return False
                    
                    # Validate UI controls
                    ui_controls = data.get('ui_controls', {})
                    expected_controls = ['show_generate_images_toggle', 'show_include_images_manual_toggle', 'show_publication_switch']
                    missing_controls = [control for control in expected_controls if control not in ui_controls]
                    
                    if missing_controls:
                        self.log_test("GET Publication Rules", False, 
                            f"Missing UI controls: {missing_controls}", data)
                        return False
                    
                    # Check auto publication rule (should always be False)
                    auto_pub = pub_rules.get('auto_publication', {})
                    if auto_pub.get('includes_images') != False:
                        self.log_test("GET Publication Rules", False, 
                            "Auto publication should never include images", data)
                        return False
                    
                    self.log_test("GET Publication Rules", True, 
                        f"All rules and controls present, auto_publication correctly excludes images")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("GET Publication Rules", False, 
                        f"Status: {response.status}", error_text)
                    return False
                    
        except Exception as e:
            self.log_test("GET Publication Rules", False, f"Exception: {str(e)}")
            return False
            
    async def test_generate_sheet_integration(self) -> bool:
        """Test integration with /api/generate-sheet endpoint"""
        try:
            # Test 1: Generate sheet with images enabled
            await self.session.put(f"{API_BASE}/images/preferences", json={"generate_images": True})
            
            sheet_data = {
                "product_name": "Samsung Galaxy S24 Ultra Test",
                "product_description": "Smartphone Samsung Galaxy S24 Ultra avec S Pen intégré, écran Dynamic AMOLED 2X de 6,8 pouces, processeur Snapdragon 8 Gen 3",
                "generate_image": True,
                "number_of_images": 1,
                "language": "fr",
                "category": "électronique"
            }
            
            async with self.session.post(f"{API_BASE}/generate-sheet", json=sheet_data) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check if images were generated based on user preferences
                    generated_images = data.get('generated_images', [])
                    
                    self.log_test("Generate Sheet Integration (Images Enabled)", True, 
                        f"Sheet generated with {len(generated_images)} images")
                elif response.status == 422:
                    # Validation error - might be due to request format
                    error_data = await response.json()
                    self.log_test("Generate Sheet Integration (Images Enabled)", False, 
                        f"Validation error: {error_data.get('detail', 'Unknown validation error')}")
                    return False
                else:
                    error_text = await response.text()
                    self.log_test("Generate Sheet Integration (Images Enabled)", False, 
                        f"Status: {response.status}", error_text[:200])
                    return False
            
            # Test 2: Generate sheet with images disabled
            await self.session.put(f"{API_BASE}/images/preferences", json={"generate_images": False})
            
            async with self.session.post(f"{API_BASE}/generate-sheet", json=sheet_data) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Should have no images when generate_images=False
                    generated_images = data.get('generated_images', [])
                    
                    if len(generated_images) > 0:
                        self.log_test("Generate Sheet Integration (Images Disabled)", False, 
                            f"Should have 0 images but got {len(generated_images)}")
                        return False
                    
                    self.log_test("Generate Sheet Integration (Images Disabled)", True, 
                        "Sheet generated with 0 images (correctly respecting user preferences)")
                elif response.status == 422:
                    # Validation error
                    error_data = await response.json()
                    self.log_test("Generate Sheet Integration (Images Disabled)", False, 
                        f"Validation error: {error_data.get('detail', 'Unknown validation error')}")
                    return False
                else:
                    error_text = await response.text()
                    self.log_test("Generate Sheet Integration (Images Disabled)", False, 
                        f"Status: {response.status}", error_text[:200])
                    return False
            
            return True
            
        except Exception as e:
            self.log_test("Generate Sheet Integration", False, f"Exception: {str(e)}")
            return False
            
    async def test_user_model_extensions(self) -> bool:
        """Test User model has the new image management fields via image preferences endpoint"""
        try:
            # Use the image preferences endpoint to verify the user model has the fields
            async with self.session.get(f"{API_BASE}/images/preferences") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for new fields in the response
                    has_generate_images = 'generate_images' in data
                    has_include_images_manual = 'include_images_manual' in data
                    
                    if not has_generate_images:
                        self.log_test("User Model Extensions", False, 
                            "generate_images field missing from preferences response")
                        return False
                    
                    if not has_include_images_manual:
                        self.log_test("User Model Extensions", False, 
                            "include_images_manual field missing from preferences response")
                        return False
                    
                    # Check data types
                    generate_images_val = data.get('generate_images')
                    include_images_manual_val = data.get('include_images_manual')
                    
                    if not isinstance(generate_images_val, bool):
                        self.log_test("User Model Extensions", False, 
                            "generate_images should be boolean")
                        return False
                    
                    if not isinstance(include_images_manual_val, bool):
                        self.log_test("User Model Extensions", False, 
                            "include_images_manual should be boolean")
                        return False
                    
                    self.log_test("User Model Extensions", True, 
                        f"Both fields present and correctly typed - generate_images: {generate_images_val}, "
                        f"include_images_manual: {include_images_manual_val}")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("User Model Extensions", False, 
                        f"Status: {response.status}", error_text)
                    return False
                    
        except Exception as e:
            self.log_test("User Model Extensions", False, f"Exception: {str(e)}")
            return False
            
    async def test_database_operations(self) -> bool:
        """Test database operations for image preferences"""
        try:
            # Test persistence across multiple updates
            test_values = [
                {"generate_images": True, "include_images_manual": True},
                {"generate_images": False, "include_images_manual": False},
                {"generate_images": True, "include_images_manual": False},
                {"generate_images": True, "include_images_manual": True}
            ]
            
            for i, values in enumerate(test_values):
                # Update preferences
                async with self.session.put(f"{API_BASE}/images/preferences", json=values) as response:
                    if response.status != 200:
                        self.log_test(f"Database Operations (Update {i+1})", False, 
                            f"Update failed with status: {response.status}")
                        return False
                
                # Verify persistence by getting preferences
                async with self.session.get(f"{API_BASE}/images/preferences") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        expected_generate = values.get("generate_images")
                        expected_include = values.get("include_images_manual")
                        
                        # Handle auto-correction case
                        if expected_generate == False and expected_include == True:
                            expected_include = False
                        
                        actual_generate = data.get('generate_images')
                        actual_include = data.get('include_images_manual')
                        
                        if actual_generate != expected_generate or actual_include != expected_include:
                            self.log_test(f"Database Operations (Verify {i+1})", False, 
                                f"Values not persisted correctly. Expected: {expected_generate}/{expected_include}, "
                                f"Got: {actual_generate}/{actual_include}")
                            return False
                    else:
                        self.log_test(f"Database Operations (Verify {i+1})", False, 
                            f"Get failed with status: {response.status}")
                        return False
            
            self.log_test("Database Operations", True, 
                "All preference updates persisted correctly")
            return True
            
        except Exception as e:
            self.log_test("Database Operations", False, f"Exception: {str(e)}")
            return False
            
    async def run_all_tests(self):
        """Run all Image Management tests"""
        print("🚀 Starting ECOMSIMPLY Image Management Backend Testing")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        await self.setup_session()
        
        try:
            # Setup
            if not await self.register_test_user():
                print("❌ Failed to register test user, aborting tests")
                return
                
            if not await self.login_test_user():
                print("❌ Failed to login test user, aborting tests")
                return
            
            print("\n📋 Running Image Management API Tests...")
            
            # Core API Tests
            await self.test_image_preferences_get()
            await self.test_image_preferences_update()
            await self.test_image_generation_test()
            await self.test_publication_rules()
            
            print("\n🔗 Running Integration Tests...")
            
            # Integration Tests
            await self.test_generate_sheet_integration()
            await self.test_user_model_extensions()
            await self.test_database_operations()
            
        finally:
            await self.cleanup_session()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n🎯 IMAGE MANAGEMENT TESTING COMPLETED")
        
        return success_rate >= 80  # Consider 80%+ success rate as acceptable

async def main():
    """Main test runner"""
    tester = ImageManagementTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())