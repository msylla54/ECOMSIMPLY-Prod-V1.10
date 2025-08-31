#!/usr/bin/env python3
"""
ECOMSIMPLY Backend Testing After 3D Hero Components Addition
Test suite to verify all existing functionalities work correctly after frontend 3D changes
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

class EcomsimplyBackendTester:
    """Comprehensive tester for ECOMSIMPLY backend after 3D Hero components addition"""
    
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
        print("🚀 ECOMSIMPLY Backend Testing After 3D Hero Components")
        print("=" * 70)
        
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
    
    async def test_server_health(self):
        """Test 1: Verify server is running and responding on port 8001"""
        test_name = "Server Health Check"
        
        try:
            # Test basic health endpoints
            health_endpoints = [
                "/health",
                "/health/ready", 
                "/health/live"
            ]
            
            health_results = {}
            working_endpoints = 0
            
            for endpoint in health_endpoints:
                try:
                    url = f"{API_BASE}{endpoint}"
                    start_time = time.time()
                    async with self.session.get(url) as response:
                        response_time = time.time() - start_time
                        status_code = response.status
                        
                        if response.content_type == 'application/json':
                            response_data = await response.json()
                        else:
                            response_data = await response.text()
                        
                        health_results[endpoint] = {
                            "status_code": status_code,
                            "response_time": round(response_time * 1000, 2),
                            "working": status_code == 200,
                            "response": response_data
                        }
                        
                        if status_code == 200:
                            working_endpoints += 1
                
                except Exception as e:
                    health_results[endpoint] = {
                        "status_code": None,
                        "working": False,
                        "error": str(e)
                    }
            
            details = {
                "tested_endpoints": len(health_endpoints),
                "working_endpoints": working_endpoints,
                "health_results": health_results
            }
            
            if working_endpoints == len(health_endpoints):
                self.log_test_result(test_name, "passed", f"Server healthy - all {working_endpoints} endpoints responding", details)
            elif working_endpoints > 0:
                self.log_test_result(test_name, "warning", f"Server partially healthy - {working_endpoints}/{len(health_endpoints)} endpoints working", details)
            else:
                self.log_test_result(test_name, "failed", "Server not responding to health checks", details)
        
        except Exception as e:
            self.log_test_result(test_name, "failed", f"Error testing server health: {str(e)}")
    
    async def test_generate_sheet_endpoint(self):
        """Test 2: Verify /api/generate-sheet endpoint functionality"""
        test_name = "Generate Sheet Endpoint"
        
        try:
            # Test data for product sheet generation
            test_data = {
                "product_name": "iPhone 15 Pro Test 3D Hero",
                "product_description": "Smartphone premium avec processeur A17 Pro, appareil photo 48MP et design en titane. Test après ajout des composants 3D Hero.",
                "generate_image": True,
                "number_of_images": 1,
                "language": "fr",
                "category": "électronique",
                "use_case": "Test de régression après 3D Hero",
                "image_style": "studio"
            }
            
            url = f"{API_BASE}/generate-sheet"
            start_time = time.time()
            
            async with self.session.post(url, json=test_data) as response:
                response_time = time.time() - start_time
                status_code = response.status
                
                if response.content_type == 'application/json':
                    response_data = await response.json()
                else:
                    response_data = await response.text()
                
                details = {
                    "status_code": status_code,
                    "response_time": round(response_time, 2),
                    "request_data": test_data
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
                        self.log_test_result(test_name, "passed", f"Generate sheet working correctly ({response_time:.1f}s)", details)
                    else:
                        self.log_test_result(test_name, "warning", f"Generate sheet working but missing fields: {missing_fields}", details)
                else:
                    details["response_data"] = str(response_data)[:500]
                    self.log_test_result(test_name, "failed", f"Generate sheet failed with status {status_code}", details)
        
        except Exception as e:
            self.log_test_result(test_name, "failed", f"Error testing generate sheet: {str(e)}")
    
    async def test_subscription_endpoints(self):
        """Test 3: Verify subscription endpoints functionality"""
        test_name = "Subscription Endpoints"
        
        try:
            # Test subscription-related endpoints
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
                        async with self.session.get(url) as response:
                            status_code = response.status
                            
                            if response.content_type == 'application/json':
                                response_data = await response.json()
                            else:
                                response_data = await response.text()
                    
                    subscription_results[endpoint] = {
                        "status_code": status_code,
                        "working": status_code in [200, 401, 403],  # 401/403 are acceptable for auth-required endpoints
                        "response": str(response_data)[:200] if isinstance(response_data, str) else response_data
                    }
                    
                    if status_code in [200, 401, 403]:
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
                "subscription_results": subscription_results
            }
            
            if critical_failures == 0 and working_endpoints >= len(subscription_endpoints) * 0.8:
                self.log_test_result(test_name, "passed", f"Subscription endpoints working ({working_endpoints}/{len(subscription_endpoints)})", details)
            elif critical_failures <= 1:
                self.log_test_result(test_name, "warning", f"Some subscription endpoints issues ({working_endpoints}/{len(subscription_endpoints)})", details)
            else:
                self.log_test_result(test_name, "failed", f"Critical subscription endpoints failing ({critical_failures} critical failures)", details)
        
        except Exception as e:
            self.log_test_result(test_name, "failed", f"Error testing subscription endpoints: {str(e)}")
    
    async def test_stripe_webhooks(self):
        """Test 4: Verify Stripe webhook endpoint accessibility"""
        test_name = "Stripe Webhooks"
        
        try:
            # Test webhook endpoint accessibility (should return 400/405 for GET requests, but endpoint should exist)
            webhook_url = f"{API_BASE}/subscription/webhook"
            
            async with self.session.get(webhook_url) as response:
                status_code = response.status
                
                if response.content_type == 'application/json':
                    response_data = await response.json()
                else:
                    response_data = await response.text()
            
            details = {
                "webhook_url": webhook_url,
                "status_code": status_code,
                "response": str(response_data)[:200]
            }
            
            # Webhook endpoints typically return 400/405 for GET requests, which means they exist
            if status_code in [400, 405, 422]:  # Bad request, method not allowed, or unprocessable entity
                self.log_test_result(test_name, "passed", "Stripe webhook endpoint accessible and responding", details)
            elif status_code == 404:
                self.log_test_result(test_name, "failed", "Stripe webhook endpoint not found", details)
            else:
                self.log_test_result(test_name, "warning", f"Stripe webhook endpoint responding with status {status_code}", details)
        
        except Exception as e:
            self.log_test_result(test_name, "failed", f"Error testing Stripe webhooks: {str(e)}")
    
    async def test_existing_services_regression(self):
        """Test 5: Verify no regression in existing services (GPT, image generation, etc.)"""
        test_name = "Existing Services Regression"
        
        try:
            # Test various service endpoints to ensure no regression
            service_endpoints = [
                {"endpoint": "/status/publication", "name": "Publication Service"},
                {"endpoint": "/publications/history", "name": "Publication History"},
                {"endpoint": "/health", "name": "Health Service"},
                {"endpoint": "/subscription/plans", "name": "Subscription Plans"}
            ]
            
            service_results = {}
            working_services = 0
            
            for service_info in service_endpoints:
                endpoint = service_info["endpoint"]
                service_name = service_info["name"]
                
                try:
                    url = f"{API_BASE}{endpoint}"
                    start_time = time.time()
                    
                    async with self.session.get(url) as response:
                        response_time = time.time() - start_time
                        status_code = response.status
                        
                        if response.content_type == 'application/json':
                            response_data = await response.json()
                        else:
                            response_data = await response.text()
                    
                    service_results[service_name] = {
                        "endpoint": endpoint,
                        "status_code": status_code,
                        "response_time": round(response_time * 1000, 2),
                        "working": status_code in [200, 401, 403],
                        "response_size": len(str(response_data))
                    }
                    
                    if status_code in [200, 401, 403]:
                        working_services += 1
                
                except Exception as e:
                    service_results[service_name] = {
                        "endpoint": endpoint,
                        "status_code": None,
                        "working": False,
                        "error": str(e)
                    }
            
            details = {
                "tested_services": len(service_endpoints),
                "working_services": working_services,
                "service_results": service_results
            }
            
            if working_services == len(service_endpoints):
                self.log_test_result(test_name, "passed", f"No regression detected - all {working_services} services working", details)
            elif working_services >= len(service_endpoints) * 0.8:
                self.log_test_result(test_name, "warning", f"Minor regression - {working_services}/{len(service_endpoints)} services working", details)
            else:
                self.log_test_result(test_name, "failed", f"Significant regression - only {working_services}/{len(service_endpoints)} services working", details)
        
        except Exception as e:
            self.log_test_result(test_name, "failed", f"Error testing service regression: {str(e)}")
    
    async def test_api_response_times(self):
        """Test 6: Verify API response times are acceptable"""
        test_name = "API Response Times"
        
        try:
            # Test response times for critical endpoints
            critical_endpoints = [
                "/health",
                "/subscription/plans",
                "/status/publication"
            ]
            
            response_times = {}
            slow_endpoints = []
            
            for endpoint in critical_endpoints:
                try:
                    url = f"{API_BASE}{endpoint}"
                    start_time = time.time()
                    
                    async with self.session.get(url) as response:
                        response_time = time.time() - start_time
                        status_code = response.status
                    
                    response_times[endpoint] = {
                        "response_time_ms": round(response_time * 1000, 2),
                        "status_code": status_code,
                        "acceptable": response_time < 5.0  # 5 seconds threshold
                    }
                    
                    if response_time >= 5.0:
                        slow_endpoints.append(endpoint)
                
                except Exception as e:
                    response_times[endpoint] = {
                        "response_time_ms": None,
                        "error": str(e),
                        "acceptable": False
                    }
                    slow_endpoints.append(endpoint)
            
            avg_response_time = sum(
                rt["response_time_ms"] for rt in response_times.values() 
                if rt["response_time_ms"] is not None
            ) / len([rt for rt in response_times.values() if rt["response_time_ms"] is not None])
            
            details = {
                "tested_endpoints": len(critical_endpoints),
                "slow_endpoints": slow_endpoints,
                "average_response_time_ms": round(avg_response_time, 2),
                "response_times": response_times
            }
            
            if not slow_endpoints:
                self.log_test_result(test_name, "passed", f"All endpoints responding quickly (avg: {avg_response_time:.0f}ms)", details)
            elif len(slow_endpoints) <= 1:
                self.log_test_result(test_name, "warning", f"Some slow endpoints detected: {slow_endpoints}", details)
            else:
                self.log_test_result(test_name, "failed", f"Multiple slow endpoints: {slow_endpoints}", details)
        
        except Exception as e:
            self.log_test_result(test_name, "failed", f"Error testing response times: {str(e)}")
    
    async def test_cors_and_headers(self):
        """Test 7: Verify CORS and security headers are properly configured"""
        test_name = "CORS and Security Headers"
        
        try:
            # Test CORS configuration
            url = f"{API_BASE}/health"
            
            async with self.session.get(url) as response:
                headers = dict(response.headers)
                status_code = response.status
            
            # Check for important headers
            cors_headers = {
                "access-control-allow-origin": headers.get("access-control-allow-origin"),
                "access-control-allow-methods": headers.get("access-control-allow-methods"),
                "access-control-allow-headers": headers.get("access-control-allow-headers")
            }
            
            security_headers = {
                "content-type": headers.get("content-type"),
                "server": headers.get("server", "Not disclosed")
            }
            
            details = {
                "status_code": status_code,
                "cors_headers": cors_headers,
                "security_headers": security_headers,
                "total_headers": len(headers)
            }
            
            # Check if CORS is properly configured
            has_cors = any(cors_headers.values())
            has_content_type = "content-type" in headers
            
            if has_cors and has_content_type:
                self.log_test_result(test_name, "passed", "CORS and headers properly configured", details)
            elif has_content_type:
                self.log_test_result(test_name, "warning", "Basic headers present, CORS may need configuration", details)
            else:
                self.log_test_result(test_name, "failed", "Missing important headers", details)
        
        except Exception as e:
            self.log_test_result(test_name, "failed", f"Error testing CORS and headers: {str(e)}")
    
    async def run_all_tests(self):
        """Run all backend tests"""
        await self.setup()
        
        try:
            # Run all tests in sequence
            await self.test_server_health()
            await self.test_generate_sheet_endpoint()
            await self.test_subscription_endpoints()
            await self.test_stripe_webhooks()
            await self.test_existing_services_regression()
            await self.test_api_response_times()
            await self.test_cors_and_headers()
            
            # Print summary
            self.print_final_summary()
            
        finally:
            await self.cleanup()
    
    def print_final_summary(self):
        """Print final test summary"""
        summary = self.results["summary"]
        
        print(f"\n{'='*70}")
        print("📊 ECOMSIMPLY BACKEND TEST SUMMARY (After 3D Hero Components)")
        print(f"{'='*70}")
        print(f"Total Tests: {summary['total']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"⚠️  Warnings: {summary['warnings']}")
        
        success_rate = (summary['passed'] / summary['total']) * 100 if summary['total'] > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Overall assessment
        if summary['failed'] == 0:
            print(f"\n✅ OVERALL RESULT: Backend is stable after 3D Hero components addition")
            print("🎯 All existing functionalities are working correctly")
        elif summary['failed'] <= 2:
            print(f"\n⚠️  OVERALL RESULT: Backend mostly stable with minor issues")
            print("🔧 Some functionalities may need attention")
        else:
            print(f"\n❌ OVERALL RESULT: Backend has significant issues after 3D Hero changes")
            print("🚨 Multiple functionalities are affected")
        
        print(f"\n🕐 Test completed at: {datetime.utcnow().isoformat()}Z")
        
        # Specific recommendations
        print(f"\n📋 RECOMMENDATIONS:")
        if summary['failed'] == 0 and summary['warnings'] == 0:
            print("• No issues detected - backend is ready for production")
        else:
            print("• Review failed tests and address critical issues")
            print("• Monitor response times and performance")
            print("• Verify all subscription and payment flows")

async def main():
    """Main test execution"""
    tester = EcomsimplyBackendTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())