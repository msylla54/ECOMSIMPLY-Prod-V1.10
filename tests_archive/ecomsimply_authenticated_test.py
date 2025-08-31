#!/usr/bin/env python3
"""
ECOMSIMPLY Authenticated Backend Testing
Test with proper authentication to verify generate-sheet and other protected endpoints
"""

import asyncio
import aiohttp
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Test configuration
BACKEND_URL = "https://ecomsimply.com"
API_BASE = f"{BACKEND_URL}/api"

class AuthenticatedBackendTester:
    """Authenticated tester for ECOMSIMPLY backend"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "tests": {},
            "summary": {"total": 0, "passed": 0, "failed": 0, "warnings": 0}
        }
        self.session = None
        self.auth_token = None
    
    async def setup(self):
        """Setup test environment"""
        print("🚀 ECOMSIMPLY Authenticated Backend Testing")
        print("=" * 60)
        
        # Create aiohttp session
        timeout = aiohttp.ClientTimeout(total=60)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
        print(f"📡 Backend URL: {BACKEND_URL}")
        print(f"🔗 API Base: {API_BASE}")
        print()
    
    async def cleanup(self):
        """Cleanup test resources"""
        if self.session:
            await self.session.close()
    
    def log_test_result(self, test_name: str, status: str, message: str, details: Dict = None):
        """Log test result"""
        self.results["tests"][test_name] = {
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.results["summary"]["total"] += 1
        if status == "passed":
            self.results["summary"]["passed"] += 1
            print(f"✅ {test_name}: {message}")
        elif status == "warning":
            self.results["summary"]["warnings"] += 1
            print(f"⚠️  {test_name}: {message}")
        else:
            self.results["summary"]["failed"] += 1
            print(f"❌ {test_name}: {message}")
    
    async def test_user_authentication(self):
        """Test user authentication with test credentials"""
        test_name = "User Authentication"
        
        try:
            # Try to authenticate with test user
            auth_data = {
                "email": "test_user_3d_hero@ecomsimply.test",
                "password": "TestPassword123"
            }
            
            # First try to register the test user
            register_url = f"{API_BASE}/auth/register"
            register_data = {
                "email": auth_data["email"],
                "name": "Test User 3D Hero",
                "password": auth_data["password"]
            }
            
            async with self.session.post(register_url, json=register_data) as response:
                register_status = response.status
                if response.content_type == 'application/json':
                    register_response = await response.json()
                else:
                    register_response = await response.text()
            
            # Now try to login
            login_url = f"{API_BASE}/auth/login"
            async with self.session.post(login_url, json=auth_data) as response:
                login_status = response.status
                if response.content_type == 'application/json':
                    login_response = await response.json()
                else:
                    login_response = await response.text()
            
            details = {
                "register_status": register_status,
                "login_status": login_status,
                "register_response": str(register_response)[:200],
                "login_response": str(login_response)[:200]
            }
            
            # Check if we got a token
            if login_status == 200 and isinstance(login_response, dict) and "token" in login_response:
                self.auth_token = login_response["token"]
                self.log_test_result(test_name, "passed", "Authentication successful - token obtained", details)
            elif login_status in [400, 409]:  # User might already exist
                # Try with existing credentials
                existing_creds = {
                    "email": "msylla54@yahoo.fr",
                    "password": "NewPassword123"
                }
                
                async with self.session.post(login_url, json=existing_creds) as response:
                    status_code = response.status
                    if response.content_type == 'application/json':
                        response_data = await response.json()
                    else:
                        response_data = await response.text()
                
                if status_code == 200 and isinstance(response_data, dict) and "token" in response_data:
                    self.auth_token = response_data["token"]
                    details["existing_user_login"] = {"status": status_code, "success": True}
                    self.log_test_result(test_name, "passed", "Authentication successful with existing user", details)
                else:
                    details["existing_user_login"] = {"status": status_code, "response": str(response_data)[:200]}
                    self.log_test_result(test_name, "failed", "Authentication failed with both new and existing users", details)
            else:
                self.log_test_result(test_name, "failed", f"Authentication failed - status {login_status}", details)
        
        except Exception as e:
            self.log_test_result(test_name, "failed", f"Error during authentication: {str(e)}")
    
    async def test_authenticated_generate_sheet(self):
        """Test generate-sheet endpoint with authentication"""
        test_name = "Authenticated Generate Sheet"
        
        if not self.auth_token:
            self.log_test_result(test_name, "failed", "No authentication token available")
            return
        
        try:
            # Test data for product sheet generation
            test_data = {
                "product_name": "iPhone 15 Pro Test Authentifié",
                "product_description": "Smartphone premium avec processeur A17 Pro et design en titane. Test authentifié après ajout des composants 3D Hero.",
                "generate_image": True,
                "number_of_images": 1,
                "language": "fr",
                "category": "électronique",
                "use_case": "Test authentifié de régression",
                "image_style": "studio"
            }
            
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            url = f"{API_BASE}/generate-sheet"
            start_time = time.time()
            
            async with self.session.post(url, json=test_data, headers=headers) as response:
                response_time = time.time() - start_time
                status_code = response.status
                
                if response.content_type == 'application/json':
                    response_data = await response.json()
                else:
                    response_data = await response.text()
                
                details = {
                    "status_code": status_code,
                    "response_time": round(response_time, 2),
                    "request_data": test_data,
                    "has_auth_token": bool(self.auth_token)
                }
                
                if status_code == 200 and isinstance(response_data, dict):
                    # Verify response structure
                    required_fields = ["generated_title", "marketing_description", "key_features", "seo_tags"]
                    missing_fields = [field for field in required_fields if field not in response_data]
                    
                    details.update({
                        "response_structure": {
                            "has_title": "generated_title" in response_data,
                            "has_description": "marketing_description" in response_data,
                            "has_features": "key_features" in response_data,
                            "has_seo_tags": "seo_tags" in response_data,
                            "has_images": "generated_images" in response_data,
                            "missing_fields": missing_fields
                        },
                        "content_quality": {
                            "title_length": len(response_data.get("generated_title", "")),
                            "description_length": len(response_data.get("marketing_description", "")),
                            "features_count": len(response_data.get("key_features", [])),
                            "seo_tags_count": len(response_data.get("seo_tags", [])),
                            "images_count": len(response_data.get("generated_images", []))
                        }
                    })
                    
                    if not missing_fields:
                        self.log_test_result(test_name, "passed", f"Authenticated generate sheet working ({response_time:.1f}s)", details)
                    else:
                        self.log_test_result(test_name, "warning", f"Generate sheet working but missing fields: {missing_fields}", details)
                else:
                    details["response_data"] = str(response_data)[:500]
                    self.log_test_result(test_name, "failed", f"Authenticated generate sheet failed with status {status_code}", details)
        
        except Exception as e:
            self.log_test_result(test_name, "failed", f"Error testing authenticated generate sheet: {str(e)}")
    
    async def test_subscription_with_auth(self):
        """Test subscription endpoints with authentication"""
        test_name = "Authenticated Subscription Endpoints"
        
        if not self.auth_token:
            self.log_test_result(test_name, "failed", "No authentication token available")
            return
        
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            # Test subscription-related endpoints with auth
            subscription_endpoints = [
                {"endpoint": "/subscription/plans", "method": "GET", "critical": True},
                {"endpoint": "/subscription/trial-eligibility", "method": "GET", "critical": True},
                {"endpoint": "/subscription/status", "method": "GET", "critical": False}
            ]
            
            subscription_results = {}
            working_endpoints = 0
            critical_failures = 0
            
            for endpoint_info in subscription_endpoints:
                endpoint = endpoint_info["endpoint"]
                method = endpoint_info["method"]
                is_critical = endpoint_info["critical"]
                
                try:
                    url = f"{API_BASE}{endpoint}"
                    
                    if method == "GET":
                        async with self.session.get(url, headers=headers) as response:
                            status_code = response.status
                            
                            if response.content_type == 'application/json':
                                response_data = await response.json()
                            else:
                                response_data = await response.text()
                    
                    subscription_results[endpoint] = {
                        "status_code": status_code,
                        "working": status_code == 200,
                        "response": str(response_data)[:200] if isinstance(response_data, str) else response_data
                    }
                    
                    if status_code == 200:
                        working_endpoints += 1
                    elif is_critical:
                        critical_failures += 1
                
                except Exception as e:
                    subscription_results[endpoint] = {
                        "status_code": None,
                        "working": False,
                        "error": str(e)
                    }
                    if is_critical:
                        critical_failures += 1
            
            details = {
                "tested_endpoints": len(subscription_endpoints),
                "working_endpoints": working_endpoints,
                "critical_failures": critical_failures,
                "subscription_results": subscription_results,
                "has_auth_token": bool(self.auth_token)
            }
            
            if critical_failures == 0 and working_endpoints >= len(subscription_endpoints) * 0.8:
                self.log_test_result(test_name, "passed", f"Authenticated subscription endpoints working ({working_endpoints}/{len(subscription_endpoints)})", details)
            elif critical_failures <= 1:
                self.log_test_result(test_name, "warning", f"Some authenticated subscription endpoints issues ({working_endpoints}/{len(subscription_endpoints)})", details)
            else:
                self.log_test_result(test_name, "failed", f"Critical authenticated subscription endpoints failing ({critical_failures} critical failures)", details)
        
        except Exception as e:
            self.log_test_result(test_name, "failed", f"Error testing authenticated subscription endpoints: {str(e)}")
    
    async def test_stripe_integration(self):
        """Test Stripe integration endpoints"""
        test_name = "Stripe Integration"
        
        try:
            # Test Stripe-related endpoints
            stripe_endpoints = [
                {"endpoint": "/subscription/webhook", "method": "POST", "expect_status": [400, 405, 422]},
                {"endpoint": "/subscription/create", "method": "POST", "expect_status": [400, 401, 422]},
                {"endpoint": "/subscription/plans", "method": "GET", "expect_status": [200]}
            ]
            
            stripe_results = {}
            working_endpoints = 0
            
            for endpoint_info in stripe_endpoints:
                endpoint = endpoint_info["endpoint"]
                method = endpoint_info["method"]
                expected_statuses = endpoint_info["expect_status"]
                
                try:
                    url = f"{API_BASE}{endpoint}"
                    
                    if method == "GET":
                        async with self.session.get(url) as response:
                            status_code = response.status
                    elif method == "POST":
                        # Send empty POST to test endpoint existence
                        async with self.session.post(url, json={}) as response:
                            status_code = response.status
                    
                    stripe_results[endpoint] = {
                        "status_code": status_code,
                        "working": status_code in expected_statuses,
                        "expected_statuses": expected_statuses
                    }
                    
                    if status_code in expected_statuses:
                        working_endpoints += 1
                
                except Exception as e:
                    stripe_results[endpoint] = {
                        "status_code": None,
                        "working": False,
                        "error": str(e)
                    }
            
            details = {
                "tested_endpoints": len(stripe_endpoints),
                "working_endpoints": working_endpoints,
                "stripe_results": stripe_results
            }
            
            if working_endpoints == len(stripe_endpoints):
                self.log_test_result(test_name, "passed", f"Stripe integration working ({working_endpoints}/{len(stripe_endpoints)} endpoints)", details)
            elif working_endpoints >= len(stripe_endpoints) * 0.7:
                self.log_test_result(test_name, "warning", f"Stripe integration mostly working ({working_endpoints}/{len(stripe_endpoints)} endpoints)", details)
            else:
                self.log_test_result(test_name, "failed", f"Stripe integration issues ({working_endpoints}/{len(stripe_endpoints)} endpoints working)", details)
        
        except Exception as e:
            self.log_test_result(test_name, "failed", f"Error testing Stripe integration: {str(e)}")
    
    async def run_all_tests(self):
        """Run all authenticated backend tests"""
        await self.setup()
        
        try:
            # Run tests in sequence
            await self.test_user_authentication()
            await self.test_authenticated_generate_sheet()
            await self.test_subscription_with_auth()
            await self.test_stripe_integration()
            
            # Print summary
            self.print_final_summary()
            
        finally:
            await self.cleanup()
    
    def print_final_summary(self):
        """Print final test summary"""
        summary = self.results["summary"]
        
        print(f"\n{'='*60}")
        print("📊 AUTHENTICATED BACKEND TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {summary['total']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"⚠️  Warnings: {summary['warnings']}")
        
        success_rate = (summary['passed'] / summary['total']) * 100 if summary['total'] > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Overall assessment
        if summary['failed'] == 0:
            print(f"\n✅ OVERALL RESULT: Authenticated backend functionality working correctly")
        elif summary['failed'] <= 1:
            print(f"\n⚠️  OVERALL RESULT: Authenticated backend mostly working with minor issues")
        else:
            print(f"\n❌ OVERALL RESULT: Authenticated backend has significant issues")
        
        print(f"\n🕐 Test completed at: {datetime.utcnow().isoformat()}Z")

async def main():
    """Main test execution"""
    tester = AuthenticatedBackendTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())