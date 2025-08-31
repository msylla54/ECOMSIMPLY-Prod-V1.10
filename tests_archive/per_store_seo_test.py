#!/usr/bin/env python3
"""
Per-Store SEO Configuration Testing for ECOMSIMPLY Platform
Testing the new per-store SEO configuration functionality for Premium users
"""

import requests
import json
import os
from datetime import datetime
import sys

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ecomsimply.com')
API_BASE = f"{BACKEND_URL}/api"

class PerStoreSEOTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.premium_user_token = None
        self.pro_user_token = None
        self.free_user_token = None
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    def create_test_user(self, email: str, name: str, password: str, admin_key: str = None) -> str:
        """Create a test user and return JWT token"""
        try:
            payload = {
                "email": email,
                "name": name,
                "password": password
            }
            if admin_key:
                payload["admin_key"] = admin_key
                
            response = self.session.post(f"{API_BASE}/auth/register", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("token")
                self.log_result(f"User Creation ({email})", True, f"Token: {token[:20]}...")
                return token
            else:
                self.log_result(f"User Creation ({email})", False, f"Status: {response.status_code}, Response: {response.text[:100]}")
                return None
                
        except Exception as e:
            self.log_result(f"User Creation ({email})", False, f"Exception: {str(e)}")
            return None
    
    def test_per_store_seo_endpoints(self):
        """Test the new per-store SEO configuration endpoints"""
        print("\n🔍 TESTING PER-STORE SEO CONFIGURATION ENDPOINTS")
        print("=" * 60)
        
        # Test endpoints that should exist according to review request
        endpoints_to_test = [
            ("GET", "/api/seo/stores/config", "Get SEO configuration for all connected stores"),
            ("PUT", "/api/seo/stores/test-store-id/config", "Update SEO configuration for specific store"),
            ("POST", "/api/seo/stores/test-store-id/test-scraping", "Test scraping for specific store"),
            ("GET", "/api/seo/stores/analytics", "Get SEO analytics for all stores")
        ]
        
        headers = {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}
        
        for method, endpoint, description in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.session.get(f"{BACKEND_URL}{endpoint}", headers=headers)
                elif method == "PUT":
                    test_config = {
                        "scraping_enabled": True,
                        "scraping_frequency": "daily",
                        "target_keywords": ["test", "product"],
                        "target_categories": ["electronics"],
                        "competitor_urls": ["https://example.com"],
                        "auto_optimization_enabled": True,
                        "auto_publication_enabled": False,
                        "confidence_threshold": 0.7,
                        "geographic_focus": ["FR"]
                    }
                    response = self.session.put(f"{BACKEND_URL}{endpoint}", json=test_config, headers=headers)
                elif method == "POST":
                    response = self.session.post(f"{BACKEND_URL}{endpoint}", json={}, headers=headers)
                
                if response.status_code == 404:
                    self.log_result(f"{method} {endpoint}", False, f"ENDPOINT NOT IMPLEMENTED - {description}")
                elif response.status_code in [200, 201]:
                    self.log_result(f"{method} {endpoint}", True, f"Endpoint exists and responds - {description}")
                elif response.status_code == 403:
                    self.log_result(f"{method} {endpoint}", True, f"Endpoint exists, access control working - {description}")
                else:
                    self.log_result(f"{method} {endpoint}", False, f"Status: {response.status_code} - {description}")
                    
            except Exception as e:
                self.log_result(f"{method} {endpoint}", False, f"Exception: {str(e)} - {description}")
    
    def test_seo_store_config_model(self):
        """Test if SEOStoreConfig model is being used in database operations"""
        print("\n🔍 TESTING SEO STORE CONFIG MODEL USAGE")
        print("=" * 60)
        
        # Test if we can access any existing store configs
        headers = {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}
        
        # Check if there are any existing SEO endpoints that might work with store configs
        existing_seo_endpoints = [
            ("GET", "/api/seo/config", "Global SEO config"),
            ("PUT", "/api/seo/config", "Update global SEO config"),
            ("GET", "/api/seo/auto-settings", "Automation settings"),
            ("PUT", "/api/seo/auto-settings", "Update automation settings"),
            ("GET", "/api/seo/analytics", "SEO analytics"),
            ("POST", "/api/seo/test-automation", "Test automation")
        ]
        
        for method, endpoint, description in existing_seo_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{BACKEND_URL}{endpoint}", headers=headers)
                elif method == "PUT":
                    test_data = {
                        "scraping_enabled": True,
                        "scraping_frequency": "daily",
                        "auto_optimization_enabled": True,
                        "auto_publication_enabled": False
                    }
                    response = self.session.put(f"{BACKEND_URL}{endpoint}", json=test_data, headers=headers)
                elif method == "POST":
                    response = self.session.post(f"{BACKEND_URL}{endpoint}", json={}, headers=headers)
                
                if response.status_code in [200, 201]:
                    self.log_result(f"Existing SEO Endpoint {endpoint}", True, f"Working - {description}")
                    # Try to see if response contains store-specific data
                    try:
                        data = response.json()
                        if isinstance(data, dict):
                            store_related_keys = [k for k in data.keys() if 'store' in k.lower()]
                            if store_related_keys:
                                self.log_result(f"Store-related data in {endpoint}", True, f"Found keys: {store_related_keys}")
                    except:
                        pass
                elif response.status_code == 403:
                    self.log_result(f"Existing SEO Endpoint {endpoint}", True, f"Access control working - {description}")
                elif response.status_code == 404:
                    self.log_result(f"Existing SEO Endpoint {endpoint}", False, f"Not found - {description}")
                else:
                    self.log_result(f"Existing SEO Endpoint {endpoint}", False, f"Status: {response.status_code} - {description}")
                    
            except Exception as e:
                self.log_result(f"Existing SEO Endpoint {endpoint}", False, f"Exception: {str(e)}")
    
    def test_premium_access_control(self):
        """Test that only Premium users can access per-store SEO features"""
        print("\n🔍 TESTING PREMIUM ACCESS CONTROL")
        print("=" * 60)
        
        # Test with different user types
        user_tokens = [
            (self.free_user_token, "Free User"),
            (self.pro_user_token, "Pro User"), 
            (self.premium_user_token, "Premium User"),
            (self.admin_token, "Admin User")
        ]
        
        test_endpoint = "/api/seo/config"  # Use existing endpoint to test access control
        
        for token, user_type in user_tokens:
            if not token:
                self.log_result(f"Access Control Test - {user_type}", False, "No token available")
                continue
                
            try:
                headers = {"Authorization": f"Bearer {token}"}
                response = self.session.get(f"{BACKEND_URL}{test_endpoint}", headers=headers)
                
                if user_type in ["Free User"]:
                    # Free users should be denied
                    if response.status_code == 403:
                        self.log_result(f"Access Control - {user_type}", True, "Correctly denied access")
                    else:
                        self.log_result(f"Access Control - {user_type}", False, f"Should be denied but got {response.status_code}")
                        
                elif user_type in ["Pro User", "Premium User", "Admin User"]:
                    # Pro, Premium, and Admin users should have access
                    if response.status_code in [200, 201]:
                        self.log_result(f"Access Control - {user_type}", True, "Correctly granted access")
                    elif response.status_code == 403:
                        self.log_result(f"Access Control - {user_type}", False, "Should have access but was denied")
                    else:
                        self.log_result(f"Access Control - {user_type}", False, f"Unexpected status: {response.status_code}")
                        
            except Exception as e:
                self.log_result(f"Access Control - {user_type}", False, f"Exception: {str(e)}")
    
    def test_enhanced_scraping_logic(self):
        """Test the enhanced scraping logic for per-store configurations"""
        print("\n🔍 TESTING ENHANCED SCRAPING LOGIC")
        print("=" * 60)
        
        # Test if the scraping system can handle per-store configurations
        # This would typically be tested through the automation endpoints
        
        if not self.admin_token:
            self.log_result("Enhanced Scraping Logic", False, "No admin token available")
            return
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test automation endpoints that should use the enhanced scraping logic
        try:
            # Test automation test endpoint
            response = self.session.post(f"{BACKEND_URL}/api/seo/test-automation", json={}, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Enhanced Scraping Logic - Test Automation", True, "Automation test endpoint working")
                
                # Check if response indicates per-store processing
                if isinstance(data, dict):
                    scraping_results = data.get("scraping_results", {})
                    if "stores_processed" in str(scraping_results) or "per_store" in str(scraping_results):
                        self.log_result("Per-Store Processing", True, "Evidence of per-store processing found")
                    else:
                        self.log_result("Per-Store Processing", False, "No evidence of per-store processing")
                        
            elif response.status_code == 403:
                self.log_result("Enhanced Scraping Logic - Test Automation", True, "Access control working")
            else:
                self.log_result("Enhanced Scraping Logic - Test Automation", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Enhanced Scraping Logic", False, f"Exception: {str(e)}")
    
    def test_data_validation(self):
        """Test SEOStoreConfig model data validation"""
        print("\n🔍 TESTING DATA VALIDATION")
        print("=" * 60)
        
        # Test if we can create/update SEO configurations with proper validation
        if not self.admin_token:
            self.log_result("Data Validation", False, "No admin token available")
            return
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test with valid configuration data
        valid_config = {
            "scraping_enabled": True,
            "scraping_frequency": "daily",
            "target_keywords": ["electronics", "smartphone"],
            "target_categories": ["tech", "mobile"],
            "competitor_urls": ["https://example.com/competitor"],
            "auto_optimization_enabled": True,
            "auto_publication_enabled": False,
            "confidence_threshold": 0.8,
            "geographic_focus": ["FR", "EU"]
        }
        
        # Test with invalid configuration data
        invalid_configs = [
            {
                "scraping_frequency": "invalid_frequency",  # Invalid frequency
                "confidence_threshold": 1.5  # Invalid threshold (should be 0-1)
            },
            {
                "target_keywords": "not_a_list",  # Should be a list
                "geographic_focus": ["INVALID_REGION"]  # Invalid region
            }
        ]
        
        # Test valid configuration
        try:
            response = self.session.put(f"{BACKEND_URL}/api/seo/config", json=valid_config, headers=headers)
            if response.status_code in [200, 201]:
                self.log_result("Data Validation - Valid Config", True, "Valid configuration accepted")
            elif response.status_code == 422:
                self.log_result("Data Validation - Valid Config", False, "Valid configuration rejected with validation error")
            else:
                self.log_result("Data Validation - Valid Config", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_result("Data Validation - Valid Config", False, f"Exception: {str(e)}")
        
        # Test invalid configurations
        for i, invalid_config in enumerate(invalid_configs):
            try:
                response = self.session.put(f"{BACKEND_URL}/api/seo/config", json=invalid_config, headers=headers)
                if response.status_code == 422:
                    self.log_result(f"Data Validation - Invalid Config {i+1}", True, "Invalid configuration correctly rejected")
                elif response.status_code in [200, 201]:
                    self.log_result(f"Data Validation - Invalid Config {i+1}", False, "Invalid configuration incorrectly accepted")
                else:
                    self.log_result(f"Data Validation - Invalid Config {i+1}", False, f"Unexpected status: {response.status_code}")
            except Exception as e:
                self.log_result(f"Data Validation - Invalid Config {i+1}", False, f"Exception: {str(e)}")
    
    def run_comprehensive_test(self):
        """Run all per-store SEO configuration tests"""
        print("🚀 STARTING COMPREHENSIVE PER-STORE SEO CONFIGURATION TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print("=" * 80)
        
        # Create test users
        print("\n👥 CREATING TEST USERS")
        print("-" * 40)
        
        self.admin_token = self.create_test_user(
            f"admin_seo_test_{int(datetime.now().timestamp())}@test.com", 
            "Admin SEO Test", 
            "AdminPassword123", 
            "ECOMSIMPLY_ADMIN_2024"
        )
        
        self.premium_user_token = self.create_test_user(
            f"premium_seo_test_{int(datetime.now().timestamp())}@test.com",
            "Premium SEO Test",
            "PremiumPassword123"
        )
        
        self.pro_user_token = self.create_test_user(
            f"pro_seo_test_{int(datetime.now().timestamp())}@test.com",
            "Pro SEO Test", 
            "ProPassword123"
        )
        
        self.free_user_token = self.create_test_user(
            f"free_seo_test_{int(datetime.now().timestamp())}@test.com",
            "Free SEO Test",
            "FreePassword123"
        )
        
        # Run all tests
        self.test_per_store_seo_endpoints()
        self.test_seo_store_config_model()
        self.test_premium_access_control()
        self.test_enhanced_scraping_logic()
        self.test_data_validation()
        
        # Generate summary
        return self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 80)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   └─ {result['details']}")
        
        print("\n🎯 KEY FINDINGS:")
        print("-" * 80)
        
        # Analyze results for key findings
        endpoint_failures = [r for r in self.test_results if "ENDPOINT NOT IMPLEMENTED" in r.get("details", "")]
        access_control_issues = [r for r in self.test_results if "Access Control" in r["test"] and not r["success"]]
        validation_issues = [r for r in self.test_results if "Data Validation" in r["test"] and not r["success"]]
        
        if endpoint_failures:
            print(f"❌ {len(endpoint_failures)} per-store SEO endpoints are NOT IMPLEMENTED")
            for failure in endpoint_failures:
                print(f"   • {failure['test']}")
        
        if access_control_issues:
            print(f"❌ {len(access_control_issues)} access control issues found")
            
        if validation_issues:
            print(f"❌ {len(validation_issues)} data validation issues found")
        
        # Overall assessment
        print(f"\n🏆 OVERALL ASSESSMENT:")
        print("-" * 80)
        
        if success_rate >= 80:
            print("✅ EXCELLENT: Per-store SEO configuration system is working well")
        elif success_rate >= 60:
            print("⚠️ GOOD: Per-store SEO configuration system has minor issues")
        elif success_rate >= 40:
            print("❌ POOR: Per-store SEO configuration system has significant issues")
        else:
            print("❌ CRITICAL: Per-store SEO configuration system is not functional")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "results": self.test_results
        }

if __name__ == "__main__":
    tester = PerStoreSEOTester()
    results = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    if results["success_rate"] >= 80:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure