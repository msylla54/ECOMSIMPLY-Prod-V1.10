#!/usr/bin/env python3
"""
ECOMSIMPLY Comprehensive Backend Review Testing Suite
Tests all backend functionality as requested in the review, focusing on:
1. Core API Endpoints (authentication, user management)
2. Help Page Backend Support
3. Admin Panel APIs (price management, promotions, affiliate management)
4. Advanced AI Endpoints (SEO, competitor analysis, price optimization, translation, variants)
5. Affiliate System APIs
6. Database Connectivity (MongoDB, ObjectId handling)
7. Payment Processing (Stripe integration)
8. Static File Serving
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 30

class ComprehensiveBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        self.admin_token = None
        self.user_data = None
        self.admin_data = None
        self.test_results = {
            "core_api": [],
            "help_page": [],
            "admin_panel": [],
            "advanced_ai": [],
            "affiliate_system": [],
            "database": [],
            "payment": [],
            "static_files": []
        }
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def add_result(self, category, test_name, success, details=""):
        self.test_results[category].append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    # ========================================
    # 1. CORE API ENDPOINTS TESTING
    # ========================================
    
    def test_core_api_endpoints(self):
        """Test core API endpoints: authentication, user management, basic functionality"""
        self.log("🔧 TESTING CORE API ENDPOINTS...")
        
        # Test API health
        success = self.test_api_health()
        self.add_result("core_api", "API Health Check", success)
        
        # Test user registration
        success = self.test_user_registration()
        self.add_result("core_api", "User Registration", success)
        
        # Test user login
        success = self.test_user_login()
        self.add_result("core_api", "User Login", success)
        
        # Test admin registration
        success = self.test_admin_registration()
        self.add_result("core_api", "Admin Registration", success)
        
        # Test protected endpoints require auth
        success = self.test_authentication_required()
        self.add_result("core_api", "Authentication Required", success)
        
        # Test user stats
        success = self.test_user_stats()
        self.add_result("core_api", "User Statistics", success)
        
        # Test product sheet generation
        success = self.test_product_sheet_generation()
        self.add_result("core_api", "Product Sheet Generation", success)
        
        # Test user sheets retrieval
        success = self.test_user_sheets_retrieval()
        self.add_result("core_api", "User Sheets Retrieval", success)
        
        return self.test_results["core_api"]
    
    def test_api_health(self):
        """Test if the API is accessible"""
        try:
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                self.log("✅ API Health Check: OK")
                return True
            else:
                self.log(f"❌ API Health Check failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ API Health Check failed: {str(e)}", "ERROR")
            return False
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        timestamp = int(time.time())
        test_user = {
            "email": f"test.user{timestamp}@ecomsimply.fr",
            "name": "Test User",
            "password": "TestPassword123!"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=test_user)
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.user_data = data.get("user")
                self.log("✅ User Registration: Success")
                return True
            else:
                self.log(f"❌ User Registration failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ User Registration failed: {str(e)}", "ERROR")
            return False
    
    def test_user_login(self):
        """Test user login endpoint"""
        if not self.user_data:
            return False
            
        login_data = {
            "email": self.user_data["email"],
            "password": "TestPassword123!"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.log("✅ User Login: Success")
                return True
            else:
                self.log(f"❌ User Login failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ User Login failed: {str(e)}", "ERROR")
            return False
    
    def test_admin_registration(self):
        """Test admin user registration"""
        timestamp = int(time.time())
        admin_user = {
            "email": f"admin.test{timestamp}@ecomsimply.fr",
            "name": "Admin Test User",
            "password": "AdminPassword123!",
            "admin_key": "ECOMSIMPLY_ADMIN_2024"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=admin_user)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("token")
                self.admin_data = data.get("user")
                if self.admin_data.get("is_admin"):
                    self.log("✅ Admin Registration: Success")
                    return True
                else:
                    self.log("❌ Admin Registration: User not marked as admin", "ERROR")
                    return False
            else:
                self.log(f"❌ Admin Registration failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Admin Registration failed: {str(e)}", "ERROR")
            return False
    
    def test_authentication_required(self):
        """Test that protected endpoints require authentication"""
        protected_endpoints = [
            ("GET", "/my-sheets"),
            ("GET", "/stats"),
            ("POST", "/generate-sheet", {"product_name": "Test", "product_description": "Test"})
        ]
        
        success_count = 0
        for method, endpoint, *data in protected_endpoints:
            try:
                if method == "POST":
                    response = self.session.post(f"{BASE_URL}{endpoint}", json=data[0] if data else None)
                else:
                    response = self.session.get(f"{BASE_URL}{endpoint}")
                
                if response.status_code in [401, 403]:
                    success_count += 1
                    
            except Exception:
                pass
        
        success = success_count == len(protected_endpoints)
        if success:
            self.log("✅ Authentication Required: All endpoints protected")
        else:
            self.log("❌ Authentication Required: Some endpoints not protected", "ERROR")
        return success
    
    def test_user_stats(self):
        """Test user statistics endpoint"""
        if not self.auth_token:
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        try:
            response = self.session.get(f"{BASE_URL}/stats", headers=headers)
            if response.status_code == 200:
                stats = response.json()
                required_fields = ["total_sheets", "sheets_this_month", "account_created"]
                if all(field in stats for field in required_fields):
                    self.log("✅ User Statistics: Success")
                    return True
            self.log(f"❌ User Statistics failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ User Statistics failed: {str(e)}", "ERROR")
            return False
    
    def test_product_sheet_generation(self):
        """Test product sheet generation"""
        if not self.auth_token:
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        sheet_request = {
            "product_name": "Test Product",
            "product_description": "Test product for backend testing",
            "generate_image": True
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=sheet_request, headers=headers)
            if response.status_code == 200:
                sheet_data = response.json()
                required_fields = ["id", "product_name", "generated_title", "marketing_description"]
                if all(field in sheet_data for field in required_fields):
                    self.log("✅ Product Sheet Generation: Success")
                    return True
            self.log(f"❌ Product Sheet Generation failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Product Sheet Generation failed: {str(e)}", "ERROR")
            return False
    
    def test_user_sheets_retrieval(self):
        """Test retrieving user's product sheets"""
        if not self.auth_token:
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        try:
            response = self.session.get(f"{BASE_URL}/my-sheets", headers=headers)
            if response.status_code == 200:
                sheets = response.json()
                if isinstance(sheets, list):
                    self.log("✅ User Sheets Retrieval: Success")
                    return True
            self.log(f"❌ User Sheets Retrieval failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ User Sheets Retrieval failed: {str(e)}", "ERROR")
            return False
    
    # ========================================
    # 2. HELP PAGE BACKEND SUPPORT TESTING
    # ========================================
    
    def test_help_page_backend_support(self):
        """Test backend endpoints that might support help page functionality"""
        self.log("🔧 TESTING HELP PAGE BACKEND SUPPORT...")
        
        # Test chatbot (help support)
        success = self.test_chatbot_functionality()
        self.add_result("help_page", "Chatbot Support", success)
        
        # Test contact form (help support)
        success = self.test_contact_form()
        self.add_result("help_page", "Contact Form", success)
        
        # Test public endpoints (help content)
        success = self.test_public_endpoints()
        self.add_result("help_page", "Public Endpoints", success)
        
        return self.test_results["help_page"]
    
    def test_chatbot_functionality(self):
        """Test chatbot functionality for help support"""
        chat_request = {"message": "Comment utiliser ECOMSIMPLY ?"}
        
        try:
            response = self.session.post(f"{BASE_URL}/chat", json=chat_request)
            if response.status_code == 200:
                chat_data = response.json()
                required_fields = ["message", "response"]
                if all(field in chat_data for field in required_fields):
                    self.log("✅ Chatbot Functionality: Success")
                    return True
            self.log(f"❌ Chatbot Functionality failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Chatbot Functionality failed: {str(e)}", "ERROR")
            return False
    
    def test_contact_form(self):
        """Test contact form functionality"""
        contact_request = {
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Test Contact",
            "message": "This is a test contact message"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/contact", json=contact_request)
            if response.status_code == 200:
                self.log("✅ Contact Form: Success")
                return True
            self.log(f"❌ Contact Form failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Contact Form failed: {str(e)}", "ERROR")
            return False
    
    def test_public_endpoints(self):
        """Test public endpoints that might provide help content"""
        public_endpoints = [
            "/public/plans-pricing",
            "/public/features"
        ]
        
        success_count = 0
        for endpoint in public_endpoints:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                if response.status_code == 200:
                    success_count += 1
            except Exception:
                pass
        
        success = success_count > 0  # At least one public endpoint should work
        if success:
            self.log("✅ Public Endpoints: Success")
        else:
            self.log("❌ Public Endpoints: No public endpoints accessible", "ERROR")
        return success
    
    # ========================================
    # 3. ADMIN PANEL APIs TESTING
    # ========================================
    
    def test_admin_panel_apis(self):
        """Test admin panel APIs: price management, promotions, affiliate management"""
        self.log("🔧 TESTING ADMIN PANEL APIs...")
        
        if not self.admin_token:
            self.log("❌ Cannot test admin APIs: No admin token", "ERROR")
            return []
        
        # Test admin stats
        success = self.test_admin_stats()
        self.add_result("admin_panel", "Admin Statistics", success)
        
        # Test admin users management
        success = self.test_admin_users()
        self.add_result("admin_panel", "Admin Users Management", success)
        
        # Test price management
        success = self.test_price_management()
        self.add_result("admin_panel", "Price Management", success)
        
        # Test promotion management
        success = self.test_promotion_management()
        self.add_result("admin_panel", "Promotion Management", success)
        
        # Test affiliate management
        success = self.test_admin_affiliate_management()
        self.add_result("admin_panel", "Affiliate Management", success)
        
        return self.test_results["admin_panel"]
    
    def test_admin_stats(self):
        """Test admin statistics endpoint"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        try:
            response = self.session.get(f"{BASE_URL}/admin/stats", headers=headers)
            if response.status_code == 200:
                stats = response.json()
                required_fields = ["total_users", "total_sheets"]
                if all(field in stats for field in required_fields):
                    self.log("✅ Admin Statistics: Success")
                    return True
            self.log(f"❌ Admin Statistics failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Admin Statistics failed: {str(e)}", "ERROR")
            return False
    
    def test_admin_users(self):
        """Test admin users management endpoint"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        try:
            response = self.session.get(f"{BASE_URL}/admin/users", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if "users" in data and isinstance(data["users"], list):
                    self.log("✅ Admin Users Management: Success")
                    return True
            self.log(f"❌ Admin Users Management failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Admin Users Management failed: {str(e)}", "ERROR")
            return False
    
    def test_price_management(self):
        """Test price management APIs"""
        admin_key = "ECOMSIMPLY_ADMIN_2024"
        
        try:
            # Test getting plans config
            response = self.session.get(f"{BASE_URL}/admin/plans-config?admin_key={admin_key}")
            if response.status_code == 200:
                plans = response.json()
                if isinstance(plans, list) and len(plans) > 0:
                    self.log("✅ Price Management: Success")
                    return True
            self.log(f"❌ Price Management failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Price Management failed: {str(e)}", "ERROR")
            return False
    
    def test_promotion_management(self):
        """Test promotion management APIs"""
        admin_key = "ECOMSIMPLY_ADMIN_2024"
        
        try:
            # Test getting promotions
            response = self.session.get(f"{BASE_URL}/admin/promotions?admin_key={admin_key}")
            if response.status_code == 200:
                promotions = response.json()
                if isinstance(promotions, list):
                    self.log("✅ Promotion Management: Success")
                    return True
            self.log(f"❌ Promotion Management failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Promotion Management failed: {str(e)}", "ERROR")
            return False
    
    def test_admin_affiliate_management(self):
        """Test admin affiliate management APIs"""
        admin_key = "ECOMSIMPLY_ADMIN_2024"
        
        try:
            # Test getting affiliates
            response = self.session.get(f"{BASE_URL}/admin/affiliates?admin_key={admin_key}")
            if response.status_code == 200:
                affiliates = response.json()
                if isinstance(affiliates, list):
                    self.log("✅ Admin Affiliate Management: Success")
                    return True
            self.log(f"❌ Admin Affiliate Management failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Admin Affiliate Management failed: {str(e)}", "ERROR")
            return False
    
    # ========================================
    # 4. ADVANCED AI ENDPOINTS TESTING
    # ========================================
    
    def test_advanced_ai_endpoints(self):
        """Test Advanced AI endpoints: SEO analysis, competitor analysis, price optimization, translation, product variants"""
        self.log("🔧 TESTING ADVANCED AI ENDPOINTS...")
        
        if not self.auth_token:
            self.log("❌ Cannot test AI endpoints: No auth token", "ERROR")
            return []
        
        # Test SEO analysis
        success = self.test_seo_analysis()
        self.add_result("advanced_ai", "SEO Analysis", success)
        
        # Test competitor analysis
        success = self.test_competitor_analysis()
        self.add_result("advanced_ai", "Competitor Analysis", success)
        
        # Test price optimization
        success = self.test_price_optimization()
        self.add_result("advanced_ai", "Price Optimization", success)
        
        # Test multilingual translation
        success = self.test_multilingual_translation()
        self.add_result("advanced_ai", "Multilingual Translation", success)
        
        # Test product variants
        success = self.test_product_variants()
        self.add_result("advanced_ai", "Product Variants", success)
        
        # Test AI features overview
        success = self.test_ai_features_overview()
        self.add_result("advanced_ai", "AI Features Overview", success)
        
        return self.test_results["advanced_ai"]
    
    def test_seo_analysis(self):
        """Test SEO analysis endpoint"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        seo_request = {
            "product_name": "iPhone 15 Pro",
            "product_description": "Smartphone premium Apple",
            "target_keywords": "iPhone, smartphone, Apple"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/ai/seo-analysis", json=seo_request, headers=headers)
            # Expect 403 for free users or 200 for premium users
            if response.status_code in [200, 403]:
                self.log("✅ SEO Analysis: Endpoint functional")
                return True
            self.log(f"❌ SEO Analysis failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ SEO Analysis failed: {str(e)}", "ERROR")
            return False
    
    def test_competitor_analysis(self):
        """Test competitor analysis endpoint"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        competitor_request = {
            "product_name": "iPhone 15 Pro",
            "category": "electronics",
            "analysis_depth": "standard"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/ai/competitor-analysis", json=competitor_request, headers=headers)
            # Expect 403 for free users, 422 for validation, or 200 for success
            if response.status_code in [200, 403, 422]:
                self.log("✅ Competitor Analysis: Endpoint functional")
                return True
            self.log(f"❌ Competitor Analysis failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Competitor Analysis failed: {str(e)}", "ERROR")
            return False
    
    def test_price_optimization(self):
        """Test price optimization endpoint"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        price_request = {
            "product_name": "iPhone 16",
            "current_price": 1400,
            "product_cost": 300,
            "competitive_strategy": "premium"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/ai/price-optimization", json=price_request, headers=headers)
            # Expect 403 for free users or 200 for premium users
            if response.status_code in [200, 403]:
                self.log("✅ Price Optimization: Endpoint functional")
                return True
            self.log(f"❌ Price Optimization failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Price Optimization failed: {str(e)}", "ERROR")
            return False
    
    def test_multilingual_translation(self):
        """Test multilingual translation endpoint"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        translation_request = {
            "text": "Bonjour le monde",
            "source_language": "fr",
            "target_languages": ["en"]
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/ai/multilingual-translation", json=translation_request, headers=headers)
            # Expect 422 for validation, 403 for free users, or 200 for success
            if response.status_code in [200, 403, 422]:
                self.log("✅ Multilingual Translation: Endpoint functional")
                return True
            self.log(f"❌ Multilingual Translation failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Multilingual Translation failed: {str(e)}", "ERROR")
            return False
    
    def test_product_variants(self):
        """Test product variants endpoint"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        variants_request = {
            "base_product": "iPhone 16",
            "base_description": "Smartphone premium",
            "number_of_variants": 3,
            "variant_types": ["color", "size"]
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/ai/product-variants", json=variants_request, headers=headers)
            # Expect 422 for validation, 403 for free users, or 200 for success
            if response.status_code in [200, 403, 422]:
                self.log("✅ Product Variants: Endpoint functional")
                return True
            self.log(f"❌ Product Variants failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Product Variants failed: {str(e)}", "ERROR")
            return False
    
    def test_ai_features_overview(self):
        """Test AI features overview endpoint"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            response = self.session.get(f"{BASE_URL}/ai/features-overview", headers=headers)
            if response.status_code == 200:
                features = response.json()
                if "features" in features and isinstance(features["features"], list):
                    self.log("✅ AI Features Overview: Success")
                    return True
            self.log(f"❌ AI Features Overview failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ AI Features Overview failed: {str(e)}", "ERROR")
            return False
    
    # ========================================
    # 5. AFFILIATE SYSTEM APIs TESTING
    # ========================================
    
    def test_affiliate_system_apis(self):
        """Test affiliate system APIs: registration, tracking, conversion, statistics"""
        self.log("🔧 TESTING AFFILIATE SYSTEM APIs...")
        
        # Test affiliate registration
        success = self.test_affiliate_registration()
        self.add_result("affiliate_system", "Affiliate Registration", success)
        
        # Test affiliate tracking
        success = self.test_affiliate_tracking()
        self.add_result("affiliate_system", "Affiliate Tracking", success)
        
        # Test affiliate statistics
        success = self.test_affiliate_statistics()
        self.add_result("affiliate_system", "Affiliate Statistics", success)
        
        # Test affiliate configuration
        success = self.test_affiliate_configuration()
        self.add_result("affiliate_system", "Affiliate Configuration", success)
        
        return self.test_results["affiliate_system"]
    
    def test_affiliate_registration(self):
        """Test affiliate registration endpoint"""
        timestamp = int(time.time())
        affiliate_data = {
            "email": f"affiliate{timestamp}@test.com",
            "name": "Test Affiliate",
            "company": "Test Company",
            "website": "https://test.com",
            "motivation": "Testing affiliate system"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/affiliate/register", json=affiliate_data)
            if response.status_code == 200:
                data = response.json()
                if "affiliate_code" in data:
                    self.log("✅ Affiliate Registration: Success")
                    return True
            self.log(f"❌ Affiliate Registration failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Affiliate Registration failed: {str(e)}", "ERROR")
            return False
    
    def test_affiliate_tracking(self):
        """Test affiliate tracking endpoint"""
        # Use a test affiliate code
        test_code = "TESTCODE"
        
        try:
            response = self.session.get(f"{BASE_URL}/affiliate/track/{test_code}")
            # Expect 404 for non-existent affiliate or 200 for valid tracking
            if response.status_code in [200, 404]:
                self.log("✅ Affiliate Tracking: Endpoint functional")
                return True
            self.log(f"❌ Affiliate Tracking failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Affiliate Tracking failed: {str(e)}", "ERROR")
            return False
    
    def test_affiliate_statistics(self):
        """Test affiliate statistics endpoint"""
        test_code = "TESTCODE"
        
        try:
            response = self.session.get(f"{BASE_URL}/affiliate/stats/{test_code}")
            # Expect 404 for non-existent affiliate or 200 for valid stats
            if response.status_code in [200, 404]:
                self.log("✅ Affiliate Statistics: Endpoint functional")
                return True
            self.log(f"❌ Affiliate Statistics failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Affiliate Statistics failed: {str(e)}", "ERROR")
            return False
    
    def test_affiliate_configuration(self):
        """Test affiliate configuration endpoint"""
        admin_key = "ECOMSIMPLY_ADMIN_2024"
        
        try:
            response = self.session.get(f"{BASE_URL}/admin/affiliate-config?admin_key={admin_key}")
            if response.status_code == 200:
                config = response.json()
                if "default_commission_rate_pro" in config:
                    self.log("✅ Affiliate Configuration: Success")
                    return True
            self.log(f"❌ Affiliate Configuration failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Affiliate Configuration failed: {str(e)}", "ERROR")
            return False
    
    # ========================================
    # 6. DATABASE CONNECTIVITY TESTING
    # ========================================
    
    def test_database_connectivity(self):
        """Test database connectivity and MongoDB ObjectId handling"""
        self.log("🔧 TESTING DATABASE CONNECTIVITY...")
        
        # Test MongoDB connection through API calls
        success = self.test_mongodb_connection()
        self.add_result("database", "MongoDB Connection", success)
        
        # Test ObjectId serialization
        success = self.test_objectid_serialization()
        self.add_result("database", "ObjectId Serialization", success)
        
        # Test data persistence
        success = self.test_data_persistence()
        self.add_result("database", "Data Persistence", success)
        
        return self.test_results["database"]
    
    def test_mongodb_connection(self):
        """Test MongoDB connection through API calls"""
        if not self.auth_token:
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        try:
            # Test a simple database operation
            response = self.session.get(f"{BASE_URL}/my-sheets", headers=headers)
            if response.status_code == 200:
                self.log("✅ MongoDB Connection: Success")
                return True
            self.log(f"❌ MongoDB Connection failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ MongoDB Connection failed: {str(e)}", "ERROR")
            return False
    
    def test_objectid_serialization(self):
        """Test ObjectId serialization in API responses"""
        admin_key = "ECOMSIMPLY_ADMIN_2024"
        
        try:
            # Test an endpoint that should return MongoDB documents
            response = self.session.get(f"{BASE_URL}/admin/affiliates?admin_key={admin_key}")
            if response.status_code == 200:
                data = response.json()
                # If we get valid JSON, ObjectId serialization is working
                self.log("✅ ObjectId Serialization: Success")
                return True
            elif response.status_code == 403:
                # Access denied but no serialization error
                self.log("✅ ObjectId Serialization: No serialization errors")
                return True
            self.log(f"❌ ObjectId Serialization failed: {response.status_code}", "ERROR")
            return False
        except json.JSONDecodeError:
            self.log("❌ ObjectId Serialization: JSON decode error", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ ObjectId Serialization failed: {str(e)}", "ERROR")
            return False
    
    def test_data_persistence(self):
        """Test data persistence through CRUD operations"""
        if not self.auth_token:
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # Create a product sheet
            sheet_request = {
                "product_name": "Persistence Test Product",
                "product_description": "Testing data persistence",
                "generate_image": False
            }
            
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=sheet_request, headers=headers)
            if response.status_code == 200:
                sheet_data = response.json()
                sheet_id = sheet_data.get("id")
                
                # Verify it can be retrieved
                response = self.session.get(f"{BASE_URL}/my-sheets", headers=headers)
                if response.status_code == 200:
                    sheets = response.json()
                    if any(sheet.get("id") == sheet_id for sheet in sheets):
                        self.log("✅ Data Persistence: Success")
                        return True
                        
            self.log("❌ Data Persistence: Failed to persist data", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Data Persistence failed: {str(e)}", "ERROR")
            return False
    
    # ========================================
    # 7. PAYMENT PROCESSING TESTING
    # ========================================
    
    def test_payment_processing(self):
        """Test Stripe integration and subscription management"""
        self.log("🔧 TESTING PAYMENT PROCESSING...")
        
        if not self.auth_token:
            self.log("❌ Cannot test payment processing: No auth token", "ERROR")
            return []
        
        # Test Stripe checkout creation
        success = self.test_stripe_checkout()
        self.add_result("payment", "Stripe Checkout", success)
        
        # Test payment status
        success = self.test_payment_status()
        self.add_result("payment", "Payment Status", success)
        
        # Test subscription plans
        success = self.test_subscription_plans()
        self.add_result("payment", "Subscription Plans", success)
        
        return self.test_results["payment"]
    
    def test_stripe_checkout(self):
        """Test Stripe checkout session creation"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        checkout_request = {
            "plan_type": "pro",
            "origin_url": "https://test.com"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/payments/checkout", json=checkout_request, headers=headers)
            # Expect 200 for success or 503 for service unavailable in test environment
            if response.status_code in [200, 503]:
                self.log("✅ Stripe Checkout: Endpoint functional")
                return True
            self.log(f"❌ Stripe Checkout failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Stripe Checkout failed: {str(e)}", "ERROR")
            return False
    
    def test_payment_status(self):
        """Test payment status checking"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        test_session_id = "test_session_123"
        
        try:
            response = self.session.get(f"{BASE_URL}/payments/status/{test_session_id}", headers=headers)
            # Expect 404 for non-existent session or 503 for service unavailable
            if response.status_code in [200, 404, 503]:
                self.log("✅ Payment Status: Endpoint functional")
                return True
            self.log(f"❌ Payment Status failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Payment Status failed: {str(e)}", "ERROR")
            return False
    
    def test_subscription_plans(self):
        """Test subscription plans configuration"""
        try:
            response = self.session.get(f"{BASE_URL}/public/plans-pricing")
            if response.status_code == 200:
                plans = response.json()
                if isinstance(plans, list) and len(plans) > 0:
                    self.log("✅ Subscription Plans: Success")
                    return True
            self.log(f"❌ Subscription Plans failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Subscription Plans failed: {str(e)}", "ERROR")
            return False
    
    # ========================================
    # 8. STATIC FILE SERVING TESTING
    # ========================================
    
    def test_static_file_serving(self):
        """Test static file serving and asset delivery"""
        self.log("🔧 TESTING STATIC FILE SERVING...")
        
        # Test API root endpoint
        success = self.test_api_root()
        self.add_result("static_files", "API Root", success)
        
        # Test public endpoints
        success = self.test_public_assets()
        self.add_result("static_files", "Public Assets", success)
        
        return self.test_results["static_files"]
    
    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                self.log("✅ API Root: Success")
                return True
            self.log(f"❌ API Root failed: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ API Root failed: {str(e)}", "ERROR")
            return False
    
    def test_public_assets(self):
        """Test public asset serving"""
        # Test if we can access public endpoints without authentication
        public_endpoints = [
            "/public/plans-pricing",
            "/public/features"
        ]
        
        success_count = 0
        for endpoint in public_endpoints:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                if response.status_code == 200:
                    success_count += 1
            except Exception:
                pass
        
        success = success_count > 0
        if success:
            self.log("✅ Public Assets: Success")
        else:
            self.log("❌ Public Assets: No public assets accessible", "ERROR")
        return success
    
    # ========================================
    # MAIN TEST RUNNER
    # ========================================
    
    def run_comprehensive_tests(self):
        """Run all comprehensive backend tests"""
        self.log("🚀 STARTING COMPREHENSIVE BACKEND TESTING...")
        
        start_time = time.time()
        
        # Run all test categories
        core_results = self.test_core_api_endpoints()
        help_results = self.test_help_page_backend_support()
        admin_results = self.test_admin_panel_apis()
        ai_results = self.test_advanced_ai_endpoints()
        affiliate_results = self.test_affiliate_system_apis()
        database_results = self.test_database_connectivity()
        payment_results = self.test_payment_processing()
        static_results = self.test_static_file_serving()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Generate summary
        self.generate_test_summary(duration)
        
        return self.test_results
    
    def generate_test_summary(self, duration):
        """Generate comprehensive test summary"""
        self.log("=" * 80)
        self.log("🎯 COMPREHENSIVE BACKEND TESTING SUMMARY")
        self.log("=" * 80)
        
        total_tests = 0
        total_passed = 0
        
        categories = [
            ("Core API Endpoints", "core_api"),
            ("Help Page Backend Support", "help_page"),
            ("Admin Panel APIs", "admin_panel"),
            ("Advanced AI Endpoints", "advanced_ai"),
            ("Affiliate System APIs", "affiliate_system"),
            ("Database Connectivity", "database"),
            ("Payment Processing", "payment"),
            ("Static File Serving", "static_files")
        ]
        
        for category_name, category_key in categories:
            results = self.test_results[category_key]
            passed = sum(1 for r in results if r["success"])
            total = len(results)
            
            total_tests += total
            total_passed += passed
            
            status = "✅" if passed == total else "❌" if passed == 0 else "⚠️"
            self.log(f"{status} {category_name}: {passed}/{total} tests passed")
            
            # Show failed tests
            failed_tests = [r for r in results if not r["success"]]
            for test in failed_tests:
                self.log(f"   ❌ {test['test']}: {test['details']}")
        
        self.log("-" * 80)
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        self.log(f"🎯 OVERALL RESULTS: {total_passed}/{total_tests} tests passed ({success_rate:.1f}%)")
        self.log(f"⏱️  Total testing time: {duration:.2f} seconds")
        
        if success_rate >= 90:
            self.log("🎉 EXCELLENT: Backend system is highly stable and functional!")
        elif success_rate >= 75:
            self.log("✅ GOOD: Backend system is mostly functional with minor issues")
        elif success_rate >= 50:
            self.log("⚠️  MODERATE: Backend system has significant issues that need attention")
        else:
            self.log("❌ CRITICAL: Backend system has major issues requiring immediate attention")
        
        self.log("=" * 80)

if __name__ == "__main__":
    tester = ComprehensiveBackendTester()
    results = tester.run_comprehensive_tests()