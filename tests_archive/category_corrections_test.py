#!/usr/bin/env python3
"""
ECOMSIMPLY Backend Testing Suite - CATEGORY SELECTION & GPT-4 TURBO CORRECTIONS
Focus: Testing corrections and new category selection feature as requested in review

CRITICAL TEST OBJECTIVES FROM REVIEW REQUEST:
1. ✅ GPT-4 Turbo Bug Fix: target_audience string conversion + number_of_images validation (ge=0)
2. ✅ New Category Selection Feature: Frontend + Backend integration
3. ✅ Category Influence on GPT-4 Turbo Content Generation
4. ✅ Category Database Storage and Retrieval
5. ✅ Custom Category Testing ("custom")

TESTING SCENARIOS:
- iPhone 15 with category "électronique" → tech tags, tech-savvy audience
- T-shirt with category "mode" → fashion tags, style-conscious audience  
- Custom category "innovation" → adaptation of prompt
- Generation WITHOUT category (regression test)
"""

import requests
import json
import time
import random
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 45  # Increased timeout for GPT-4 Turbo processing

class CategoryCorrectionsTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        self.user_data = None
        self.test_results = []
        self.generated_sheets = []
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def log_test_result(self, test_name: str, success: bool, details: str, data: Dict = None):
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
        
    def test_api_health(self):
        """Test if the API is accessible"""
        self.log("🔍 Testing API health check...")
        try:
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                self.log_test_result("API Health Check", True, f"API accessible: {data.get('message', 'OK')}")
                return True
            else:
                self.log_test_result("API Health Check", False, f"API returned {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("API Health Check", False, f"Exception: {str(e)}")
            return False
    
    def test_user_registration_and_login(self):
        """Test user registration and login for testing"""
        self.log("👤 Testing user registration and login...")
        
        # Generate unique test user
        timestamp = int(time.time())
        test_user = {
            "email": f"category.test{timestamp}@example.com",
            "name": "Category Test User",
            "password": "CategoryTest123!"
        }
        
        try:
            # Register user
            response = self.session.post(f"{BASE_URL}/auth/register", json=test_user)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.user_data = data.get("user")
                
                if self.auth_token and self.user_data:
                    self.log_test_result("User Registration", True, f"User registered: {self.user_data['name']}")
                    
                    # Test login
                    login_data = {
                        "email": test_user["email"],
                        "password": test_user["password"]
                    }
                    
                    login_response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
                    if login_response.status_code == 200:
                        login_data = login_response.json()
                        self.auth_token = login_data.get("token")  # Update with login token
                        self.log_test_result("User Login", True, "Login successful")
                        return True
                    else:
                        self.log_test_result("User Login", False, f"Login failed: {login_response.status_code}")
                        return False
                else:
                    self.log_test_result("User Registration", False, "Missing token or user data")
                    return False
            else:
                self.log_test_result("User Registration", False, f"Registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("User Registration/Login", False, f"Exception: {str(e)}")
            return False
    
    def test_gpt4_turbo_target_audience_fix(self):
        """🎯 CRITICAL TEST: GPT-4 Turbo target_audience string conversion fix"""
        self.log("🎯 CRITICAL TEST: Testing GPT-4 Turbo target_audience string conversion fix...")
        
        if not self.auth_token:
            self.log_test_result("GPT-4 Turbo Target Audience Fix", False, "No auth token")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test with a product that would generate complex target_audience object
        test_data = {
            "product_name": "iPhone 15 Pro Max",
            "product_description": "Smartphone premium avec processeur A17 Pro, appareil photo 48MP et écran Super Retina XDR",
            "generate_image": False,
            "number_of_images": 0,  # Test the ge=0 validation fix
            "language": "fr",
            "category": "électronique"  # Test category integration
        }
        
        try:
            self.log("📝 Testing GPT-4 Turbo with complex product that previously caused target_audience dict error...")
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    sheet_data = data.get("sheet", {})
                    target_audience = sheet_data.get("target_audience")
                    
                    # CRITICAL: target_audience must be a string, not a dict
                    if isinstance(target_audience, str):
                        self.log_test_result(
                            "GPT-4 Turbo Target Audience Fix", 
                            True, 
                            f"target_audience correctly converted to string: {len(target_audience)} chars",
                            {"target_audience_type": type(target_audience).__name__, "target_audience_preview": target_audience[:100]}
                        )
                        
                        # Store for further analysis
                        self.generated_sheets.append({
                            "test": "target_audience_fix",
                            "sheet_data": sheet_data,
                            "category": "électronique"
                        })
                        
                        return True
                    else:
                        self.log_test_result(
                            "GPT-4 Turbo Target Audience Fix", 
                            False, 
                            f"target_audience is still {type(target_audience).__name__}, not string",
                            {"target_audience_type": type(target_audience).__name__, "target_audience_value": str(target_audience)}
                        )
                        return False
                else:
                    self.log_test_result("GPT-4 Turbo Target Audience Fix", False, f"Generation failed: {data.get('message', 'Unknown error')}")
                    return False
            else:
                self.log_test_result("GPT-4 Turbo Target Audience Fix", False, f"API call failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("GPT-4 Turbo Target Audience Fix", False, f"Exception: {str(e)}")
            return False
    
    def test_number_of_images_validation_fix(self):
        """🔧 CRITICAL TEST: number_of_images validation fix (ge=0)"""
        self.log("🔧 CRITICAL TEST: Testing number_of_images validation fix (ge=0)...")
        
        if not self.auth_token:
            self.log_test_result("Number of Images Validation Fix", False, "No auth token")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test the exact scenario that was failing: generate_image=False, number_of_images=0
        test_data = {
            "product_name": "MacBook Pro M3",
            "product_description": "Ordinateur portable professionnel avec puce M3",
            "generate_image": False,  # No image generation
            "number_of_images": 0,    # This should now be valid (ge=0 instead of ge=1)
            "language": "fr",
            "category": "électronique"
        }
        
        try:
            self.log("📝 Testing number_of_images=0 with generate_image=False (previously caused 422 validation error)...")
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    sheet_data = data.get("sheet", {})
                    
                    # Verify no images were generated (as expected)
                    product_images = sheet_data.get("product_images_base64", [])
                    number_generated = sheet_data.get("number_of_images_generated", 0)
                    
                    if number_generated == 0 and len(product_images) == 0:
                        self.log_test_result(
                            "Number of Images Validation Fix", 
                            True, 
                            "number_of_images=0 validation now accepts ge=0 (no 422 error)",
                            {"number_of_images_generated": number_generated, "images_count": len(product_images)}
                        )
                        return True
                    else:
                        self.log_test_result(
                            "Number of Images Validation Fix", 
                            False, 
                            f"Unexpected image generation: {number_generated} generated, {len(product_images)} in array"
                        )
                        return False
                else:
                    self.log_test_result("Number of Images Validation Fix", False, f"Generation failed: {data.get('message', 'Unknown error')}")
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
    
    def test_category_selection_electronics(self):
        """📱 TEST: Category selection - Electronics (iPhone with électronique category)"""
        self.log("📱 Testing category selection: iPhone 15 with 'électronique' category...")
        
        if not self.auth_token:
            self.log_test_result("Category Selection - Electronics", False, "No auth token")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        test_data = {
            "product_name": "iPhone 15 Pro",
            "product_description": "Smartphone Apple avec processeur A17 Pro et appareil photo 48MP",
            "generate_image": False,
            "number_of_images": 0,
            "language": "fr",
            "category": "électronique"  # NEW FEATURE: Category selection
        }
        
        try:
            self.log("📝 Testing iPhone with électronique category - should generate tech-focused content...")
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    sheet_data = data.get("sheet", {})
                    
                    # Analyze if category influenced the generation
                    title = sheet_data.get("generated_title", "").lower()
                    description = sheet_data.get("marketing_description", "").lower()
                    seo_tags = [tag.lower() for tag in sheet_data.get("seo_tags", [])]
                    target_audience = sheet_data.get("target_audience", "").lower()
                    category_stored = sheet_data.get("category")  # Check if category is stored
                    
                    # Check for tech-related content (should be present for electronics)
                    tech_indicators = ["technologie", "innovation", "performance", "avancé", "intelligent", "numérique", "tech"]
                    has_tech_content = any(indicator in text for text in [title, description, target_audience] for indicator in tech_indicators)
                    
                    # Check SEO tags for tech relevance
                    tech_tags = any(indicator in tag for tag in seo_tags for indicator in tech_indicators)
                    
                    # Check if category is stored in database
                    category_stored_correctly = category_stored == "électronique"
                    
                    self.log(f"📊 CATEGORY ANALYSIS:")
                    self.log(f"   Category stored: {category_stored}")
                    self.log(f"   Title: {sheet_data.get('generated_title', 'N/A')}")
                    self.log(f"   Tech content detected: {has_tech_content}")
                    self.log(f"   Tech SEO tags: {tech_tags}")
                    self.log(f"   SEO Tags: {', '.join(sheet_data.get('seo_tags', []))}")
                    self.log(f"   Target Audience: {target_audience[:100]}...")
                    
                    # Success criteria: category stored + tech-focused content
                    success = category_stored_correctly and (has_tech_content or tech_tags)
                    
                    if success:
                        self.log_test_result(
                            "Category Selection - Electronics", 
                            True, 
                            f"Category 'électronique' influenced generation: tech content={has_tech_content}, tech tags={tech_tags}",
                            {
                                "category_stored": category_stored,
                                "tech_content": has_tech_content,
                                "tech_tags": tech_tags,
                                "seo_tags": sheet_data.get("seo_tags", [])
                            }
                        )
                        
                        # Store for comparison
                        self.generated_sheets.append({
                            "test": "category_electronics",
                            "sheet_data": sheet_data,
                            "category": "électronique",
                            "analysis": {
                                "tech_content": has_tech_content,
                                "tech_tags": tech_tags
                            }
                        })
                        
                        return True
                    else:
                        self.log_test_result(
                            "Category Selection - Electronics", 
                            False, 
                            f"Category not properly stored or didn't influence content: stored={category_stored_correctly}, tech_content={has_tech_content}"
                        )
                        return False
                else:
                    self.log_test_result("Category Selection - Electronics", False, f"Generation failed: {data.get('message', 'Unknown error')}")
                    return False
            else:
                self.log_test_result("Category Selection - Electronics", False, f"API call failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("Category Selection - Electronics", False, f"Exception: {str(e)}")
            return False
    
    def test_category_selection_fashion(self):
        """👕 TEST: Category selection - Fashion (T-shirt with mode category)"""
        self.log("👕 Testing category selection: T-shirt with 'mode' category...")
        
        if not self.auth_token:
            self.log_test_result("Category Selection - Fashion", False, "No auth token")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        test_data = {
            "product_name": "T-shirt Premium Coton Bio",
            "product_description": "T-shirt unisexe en coton biologique, coupe moderne et confortable",
            "generate_image": False,
            "number_of_images": 0,
            "language": "fr",
            "category": "mode"  # NEW FEATURE: Fashion category
        }
        
        try:
            self.log("📝 Testing T-shirt with mode category - should generate fashion-focused content...")
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    sheet_data = data.get("sheet", {})
                    
                    # Analyze if category influenced the generation
                    title = sheet_data.get("generated_title", "").lower()
                    description = sheet_data.get("marketing_description", "").lower()
                    seo_tags = [tag.lower() for tag in sheet_data.get("seo_tags", [])]
                    target_audience = sheet_data.get("target_audience", "").lower()
                    category_stored = sheet_data.get("category")
                    
                    # Check for fashion-related content
                    fashion_indicators = ["style", "tendance", "élégant", "fashion", "look", "design", "esthétique", "chic", "moderne"]
                    has_fashion_content = any(indicator in text for text in [title, description, target_audience] for indicator in fashion_indicators)
                    
                    # Check SEO tags for fashion relevance
                    fashion_tags = any(indicator in tag for tag in seo_tags for indicator in fashion_indicators)
                    
                    # Check if category is stored
                    category_stored_correctly = category_stored == "mode"
                    
                    self.log(f"📊 FASHION CATEGORY ANALYSIS:")
                    self.log(f"   Category stored: {category_stored}")
                    self.log(f"   Title: {sheet_data.get('generated_title', 'N/A')}")
                    self.log(f"   Fashion content detected: {has_fashion_content}")
                    self.log(f"   Fashion SEO tags: {fashion_tags}")
                    self.log(f"   SEO Tags: {', '.join(sheet_data.get('seo_tags', []))}")
                    self.log(f"   Target Audience: {target_audience[:100]}...")
                    
                    # Success criteria: category stored + fashion-focused content
                    success = category_stored_correctly and (has_fashion_content or fashion_tags)
                    
                    if success:
                        self.log_test_result(
                            "Category Selection - Fashion", 
                            True, 
                            f"Category 'mode' influenced generation: fashion content={has_fashion_content}, fashion tags={fashion_tags}",
                            {
                                "category_stored": category_stored,
                                "fashion_content": has_fashion_content,
                                "fashion_tags": fashion_tags,
                                "seo_tags": sheet_data.get("seo_tags", [])
                            }
                        )
                        
                        # Store for comparison
                        self.generated_sheets.append({
                            "test": "category_fashion",
                            "sheet_data": sheet_data,
                            "category": "mode",
                            "analysis": {
                                "fashion_content": has_fashion_content,
                                "fashion_tags": fashion_tags
                            }
                        })
                        
                        return True
                    else:
                        self.log_test_result(
                            "Category Selection - Fashion", 
                            False, 
                            f"Category not properly stored or didn't influence content: stored={category_stored_correctly}, fashion_content={has_fashion_content}"
                        )
                        return False
                else:
                    self.log_test_result("Category Selection - Fashion", False, f"Generation failed: {data.get('message', 'Unknown error')}")
                    return False
            else:
                self.log_test_result("Category Selection - Fashion", False, f"API call failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("Category Selection - Fashion", False, f"Exception: {str(e)}")
            return False
    
    def test_custom_category_innovation(self):
        """🚀 TEST: Custom category - Innovation"""
        self.log("🚀 Testing custom category: 'innovation'...")
        
        if not self.auth_token:
            self.log_test_result("Custom Category - Innovation", False, "No auth token")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        test_data = {
            "product_name": "Drone Autonome AI",
            "product_description": "Drone intelligent avec intelligence artificielle pour navigation autonome",
            "generate_image": False,
            "number_of_images": 0,
            "language": "fr",
            "category": "innovation"  # CUSTOM CATEGORY
        }
        
        try:
            self.log("📝 Testing custom category 'innovation' - should adapt prompt accordingly...")
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    sheet_data = data.get("sheet", {})
                    
                    # Analyze if custom category influenced the generation
                    title = sheet_data.get("generated_title", "").lower()
                    description = sheet_data.get("marketing_description", "").lower()
                    seo_tags = [tag.lower() for tag in sheet_data.get("seo_tags", [])]
                    target_audience = sheet_data.get("target_audience", "").lower()
                    category_stored = sheet_data.get("category")
                    
                    # Check for innovation-related content
                    innovation_indicators = ["innovation", "révolutionnaire", "pionnier", "avancé", "futur", "intelligent", "breakthrough", "cutting-edge"]
                    has_innovation_content = any(indicator in text for text in [title, description, target_audience] for indicator in innovation_indicators)
                    
                    # Check SEO tags for innovation relevance
                    innovation_tags = any(indicator in tag for tag in seo_tags for indicator in innovation_indicators)
                    
                    # Check if custom category is stored
                    category_stored_correctly = category_stored == "innovation"
                    
                    self.log(f"📊 INNOVATION CATEGORY ANALYSIS:")
                    self.log(f"   Category stored: {category_stored}")
                    self.log(f"   Title: {sheet_data.get('generated_title', 'N/A')}")
                    self.log(f"   Innovation content detected: {has_innovation_content}")
                    self.log(f"   Innovation SEO tags: {innovation_tags}")
                    self.log(f"   SEO Tags: {', '.join(sheet_data.get('seo_tags', []))}")
                    self.log(f"   Target Audience: {target_audience[:100]}...")
                    
                    # Success criteria: category stored + innovation-focused content
                    success = category_stored_correctly and (has_innovation_content or innovation_tags)
                    
                    if success:
                        self.log_test_result(
                            "Custom Category - Innovation", 
                            True, 
                            f"Custom category 'innovation' influenced generation: innovation content={has_innovation_content}, innovation tags={innovation_tags}",
                            {
                                "category_stored": category_stored,
                                "innovation_content": has_innovation_content,
                                "innovation_tags": innovation_tags,
                                "seo_tags": sheet_data.get("seo_tags", [])
                            }
                        )
                        
                        # Store for comparison
                        self.generated_sheets.append({
                            "test": "custom_category_innovation",
                            "sheet_data": sheet_data,
                            "category": "innovation",
                            "analysis": {
                                "innovation_content": has_innovation_content,
                                "innovation_tags": innovation_tags
                            }
                        })
                        
                        return True
                    else:
                        self.log_test_result(
                            "Custom Category - Innovation", 
                            False, 
                            f"Custom category not properly stored or didn't influence content: stored={category_stored_correctly}, innovation_content={has_innovation_content}"
                        )
                        return False
                else:
                    self.log_test_result("Custom Category - Innovation", False, f"Generation failed: {data.get('message', 'Unknown error')}")
                    return False
            else:
                self.log_test_result("Custom Category - Innovation", False, f"API call failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("Custom Category - Innovation", False, f"Exception: {str(e)}")
            return False
    
    def test_generation_without_category_regression(self):
        """🔄 REGRESSION TEST: Generation without category (should still work)"""
        self.log("🔄 REGRESSION TEST: Testing generation WITHOUT category...")
        
        if not self.auth_token:
            self.log_test_result("Generation Without Category", False, "No auth token")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        test_data = {
            "product_name": "Casque Audio Bluetooth",
            "product_description": "Casque sans fil avec réduction de bruit active",
            "generate_image": False,
            "number_of_images": 0,
            "language": "fr"
            # NO CATEGORY - regression test
        }
        
        try:
            self.log("📝 Testing generation without category - should work as before...")
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    sheet_data = data.get("sheet", {})
                    
                    # Verify basic generation works
                    required_fields = ["generated_title", "marketing_description", "key_features", "seo_tags", "target_audience"]
                    missing_fields = [field for field in required_fields if not sheet_data.get(field)]
                    
                    if not missing_fields:
                        # Check that category is None or empty (as expected)
                        category_stored = sheet_data.get("category")
                        category_is_none = category_stored is None or category_stored == ""
                        
                        self.log(f"📊 NO CATEGORY ANALYSIS:")
                        self.log(f"   Category stored: {category_stored}")
                        self.log(f"   Title: {sheet_data.get('generated_title', 'N/A')}")
                        self.log(f"   All required fields present: {len(missing_fields) == 0}")
                        
                        if category_is_none:
                            self.log_test_result(
                                "Generation Without Category", 
                                True, 
                                "Generation works without category, no regression detected",
                                {
                                    "category_stored": category_stored,
                                    "required_fields_present": len(missing_fields) == 0,
                                    "title": sheet_data.get("generated_title", "")
                                }
                            )
                            
                            # Store for comparison
                            self.generated_sheets.append({
                                "test": "no_category_regression",
                                "sheet_data": sheet_data,
                                "category": None
                            })
                            
                            return True
                        else:
                            self.log_test_result(
                                "Generation Without Category", 
                                False, 
                                f"Category should be None but got: {category_stored}"
                            )
                            return False
                    else:
                        self.log_test_result(
                            "Generation Without Category", 
                            False, 
                            f"Missing required fields: {missing_fields}"
                        )
                        return False
                else:
                    self.log_test_result("Generation Without Category", False, f"Generation failed: {data.get('message', 'Unknown error')}")
                    return False
            else:
                self.log_test_result("Generation Without Category", False, f"API call failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("Generation Without Category", False, f"Exception: {str(e)}")
            return False
    
    def test_category_comparison_analysis(self):
        """📊 ANALYSIS: Compare generation results with and without categories"""
        self.log("📊 ANALYSIS: Comparing generation results with and without categories...")
        
        if len(self.generated_sheets) < 2:
            self.log_test_result("Category Comparison Analysis", False, "Not enough generated sheets for comparison")
            return False
        
        try:
            # Find sheets with and without categories
            category_sheets = [sheet for sheet in self.generated_sheets if sheet.get("category")]
            no_category_sheets = [sheet for sheet in self.generated_sheets if not sheet.get("category")]
            
            if not category_sheets or not no_category_sheets:
                self.log_test_result("Category Comparison Analysis", False, "Missing sheets with or without categories for comparison")
                return False
            
            self.log("📊 CATEGORY COMPARISON ANALYSIS:")
            
            # Analyze category influence
            category_influences = []
            
            for sheet in category_sheets:
                category = sheet.get("category")
                analysis = sheet.get("analysis", {})
                sheet_data = sheet.get("sheet_data", {})
                
                # Count category-specific indicators
                seo_tags = sheet_data.get("seo_tags", [])
                target_audience = sheet_data.get("target_audience", "")
                
                influence_score = 0
                if analysis.get("tech_content"): influence_score += 1
                if analysis.get("tech_tags"): influence_score += 1
                if analysis.get("fashion_content"): influence_score += 1
                if analysis.get("fashion_tags"): influence_score += 1
                if analysis.get("innovation_content"): influence_score += 1
                if analysis.get("innovation_tags"): influence_score += 1
                
                category_influences.append({
                    "category": category,
                    "influence_score": influence_score,
                    "seo_tags_count": len(seo_tags),
                    "audience_length": len(target_audience)
                })
                
                self.log(f"   {category}: influence_score={influence_score}, seo_tags={len(seo_tags)}, audience_chars={len(target_audience)}")
            
            # Calculate average influence
            avg_influence = sum(ci["influence_score"] for ci in category_influences) / len(category_influences)
            avg_seo_tags = sum(ci["seo_tags_count"] for ci in category_influences) / len(category_influences)
            
            # Compare with no-category sheets
            no_category_sheet = no_category_sheets[0]
            no_cat_data = no_category_sheet.get("sheet_data", {})
            no_cat_seo_tags = len(no_cat_data.get("seo_tags", []))
            no_cat_audience = len(no_cat_data.get("target_audience", ""))
            
            self.log(f"   No Category: seo_tags={no_cat_seo_tags}, audience_chars={no_cat_audience}")
            self.log(f"   Average with categories: influence={avg_influence:.1f}, seo_tags={avg_seo_tags:.1f}")
            
            # Success if categories show clear influence
            success = avg_influence > 0 and len(category_influences) >= 2
            
            if success:
                self.log_test_result(
                    "Category Comparison Analysis", 
                    True, 
                    f"Categories clearly influence generation: avg_influence={avg_influence:.1f}, tested_categories={len(category_influences)}",
                    {
                        "category_influences": category_influences,
                        "avg_influence_score": avg_influence,
                        "avg_seo_tags_with_category": avg_seo_tags,
                        "seo_tags_without_category": no_cat_seo_tags
                    }
                )
                return True
            else:
                self.log_test_result(
                    "Category Comparison Analysis", 
                    False, 
                    f"Categories don't show clear influence: avg_influence={avg_influence:.1f}"
                )
                return False
                
        except Exception as e:
            self.log_test_result("Category Comparison Analysis", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all category and corrections tests"""
        self.log("🚀 STARTING CATEGORY SELECTION & GPT-4 TURBO CORRECTIONS TESTING")
        self.log("=" * 80)
        
        tests = [
            ("API Health Check", self.test_api_health),
            ("User Registration & Login", self.test_user_registration_and_login),
            ("GPT-4 Turbo Target Audience Fix", self.test_gpt4_turbo_target_audience_fix),
            ("Number of Images Validation Fix", self.test_number_of_images_validation_fix),
            ("Category Selection - Electronics", self.test_category_selection_electronics),
            ("Category Selection - Fashion", self.test_category_selection_fashion),
            ("Custom Category - Innovation", self.test_custom_category_innovation),
            ("Generation Without Category (Regression)", self.test_generation_without_category_regression),
            ("Category Comparison Analysis", self.test_category_comparison_analysis)
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
            
            time.sleep(1)  # Brief pause between tests
        
        # Final summary
        self.log("\n" + "=" * 80)
        self.log("🎯 CATEGORY SELECTION & GPT-4 TURBO CORRECTIONS TEST SUMMARY")
        self.log("=" * 80)
        
        total = passed + failed
        success_rate = (passed / total * 100) if total > 0 else 0
        
        self.log(f"📊 OVERALL RESULTS: {passed}/{total} tests passed ({success_rate:.1f}% success rate)")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED! Category selection and GPT-4 Turbo corrections working perfectly!")
        elif success_rate >= 80:
            self.log("✅ MOSTLY SUCCESSFUL! Minor issues detected but core functionality working.")
        elif success_rate >= 60:
            self.log("⚠️  PARTIAL SUCCESS! Some issues need attention.")
        else:
            self.log("❌ CRITICAL ISSUES! Major problems detected.")
        
        self.log("\n📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            self.log(f"   {result['status']} {result['test']}: {result['details']}")
        
        self.log("\n🔍 KEY FINDINGS:")
        
        # Analyze key findings
        gpt4_fix_working = any(r["test"] == "GPT-4 Turbo Target Audience Fix" and r["success"] for r in self.test_results)
        validation_fix_working = any(r["test"] == "Number of Images Validation Fix" and r["success"] for r in self.test_results)
        category_working = any("Category Selection" in r["test"] and r["success"] for r in self.test_results)
        regression_ok = any(r["test"] == "Generation Without Category (Regression)" and r["success"] for r in self.test_results)
        
        self.log(f"   🎯 GPT-4 Turbo target_audience fix: {'✅ WORKING' if gpt4_fix_working else '❌ BROKEN'}")
        self.log(f"   🔧 number_of_images validation fix: {'✅ WORKING' if validation_fix_working else '❌ BROKEN'}")
        self.log(f"   📱 Category selection feature: {'✅ WORKING' if category_working else '❌ BROKEN'}")
        self.log(f"   🔄 No regression in existing functionality: {'✅ CONFIRMED' if regression_ok else '❌ REGRESSION DETECTED'}")
        
        if len(self.generated_sheets) > 0:
            self.log(f"\n📝 Generated {len(self.generated_sheets)} test sheets for analysis")
            for sheet in self.generated_sheets:
                test_name = sheet.get("test", "unknown")
                category = sheet.get("category", "none")
                self.log(f"   - {test_name}: category={category}")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = CategoryCorrectionsTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)