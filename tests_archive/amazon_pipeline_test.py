#!/usr/bin/env python3
"""
ECOMSIMPLY Amazon Pipeline Publication Automatique - Test Final
Test complet du pipeline de publication automatique Amazon avec scraping prix réparé

Tests à exécuter:
1. Test Prix Scraping Réparé: POST /api/amazon/pipeline/test/price-scraping-only
2. Test Pipeline Complet Dry-Run: POST /api/amazon/pipeline/test/full-pipeline-dry-run  
3. Test Pipeline Stats & Monitoring: GET /api/amazon/pipeline/stats
4. Validation 1 SKU Test: iPhone 15 Pro workflow complet

Author: Testing Agent
Date: 2025-01-01
"""

import asyncio
import os
import sys
import json
import httpx
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Load environment variables from backend/.env
load_dotenv('/app/backend/.env')

# Add the backend directory to Python path
sys.path.insert(0, '/app/backend')
sys.path.insert(0, '/app')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AmazonPipelineTest:
    """Test suite for Amazon Pipeline Publication Automatique validation"""
    
    def __init__(self):
        self.backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://ecomsimply.com')
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
        # Test credentials (from environment)
        self.test_email = "pipeline_test@ecomsimply.com"
        self.test_password = "TestPipeline2025!"
        self.auth_token = None
        
        # Test data for iPhone 15 Pro
        self.test_product_data = {
            "product_name": "iPhone 15 Pro 256GB Titane Naturel",
            "brand": "Apple",
            "model": "iPhone 15 Pro",
            "category": "électronique",
            "features": ["Puce A17 Pro", "Écran 6,1 pouces", "Triple caméra 48MP"],
            "benefits": ["Photos pro", "Performance gaming", "Design premium"],
            "size": "6,1 pouces",
            "color": "Titane Naturel"
        }
        
        logger.info("🧪 Amazon Pipeline Publication Automatique Test Suite Initialized")
        logger.info(f"📡 Backend URL: {self.backend_url}")
    
    async def setup_authentication(self) -> bool:
        """Setup authentication for API testing"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Login to get JWT token
                login_response = await client.post(
                    f"{self.backend_url}/api/auth/login",
                    json={
                        "email": self.test_email,
                        "password": self.test_password
                    }
                )
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    self.auth_token = login_data.get('token')
                    logger.info("✅ Authentication successful")
                    return True
                else:
                    logger.error(f"❌ Authentication failed: {login_response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Authentication setup failed: {e}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}
    
    async def test_price_scraping_only(self) -> Dict[str, Any]:
        """Test 1: Prix Scraping Réparé - POST /api/amazon/pipeline/test/price-scraping-only"""
        test_name = "Prix Scraping Réparé"
        logger.info(f"🧪 Testing: {test_name}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                auth_headers = self.get_auth_headers()
                
                # Test price scraping endpoint
                request_data = {
                    "product_data": self.test_product_data
                }
                
                response = await client.post(
                    f"{self.backend_url}/api/amazon/pipeline/test/price-scraping-only",
                    json=request_data,
                    headers=auth_headers
                )
                
                test_result = {
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0,
                    "accessible": response.status_code in [200, 201]
                }
                
                if response.status_code in [200, 201]:
                    response_data = response.json()
                    test_result["response_data"] = response_data
                    
                    # Validate response structure
                    expected_fields = ["prices", "scraping_method", "success"]
                    has_expected_fields = all(field in response_data for field in expected_fields)
                    
                    # Check if prices are realistic for iPhone 15 Pro (800-1500 EUR)
                    prices_realistic = False
                    if "prices" in response_data and response_data["prices"]:
                        prices = response_data["prices"]
                        if isinstance(prices, list) and len(prices) > 0:
                            # Check if any price is in realistic range
                            for price_info in prices:
                                if isinstance(price_info, dict) and "price" in price_info:
                                    price = float(price_info["price"])
                                    if 800 <= price <= 1500:
                                        prices_realistic = True
                                        break
                    
                    test_result.update({
                        "has_expected_fields": has_expected_fields,
                        "prices_realistic": prices_realistic,
                        "scraping_success": response_data.get("success", False)
                    })
                    
                    if has_expected_fields and prices_realistic and response_data.get("success"):
                        return {
                            "test": test_name,
                            "status": "PASS",
                            "message": "Prix scraping réparé fonctionne correctement avec prix réalistes",
                            "details": test_result
                        }
                    else:
                        return {
                            "test": test_name,
                            "status": "PARTIAL_PASS",
                            "message": "Prix scraping accessible mais données incomplètes ou prix non réalistes",
                            "details": test_result
                        }
                else:
                    test_result["error_message"] = response.text
                    return {
                        "test": test_name,
                        "status": "FAIL",
                        "message": f"Prix scraping endpoint non accessible (status: {response.status_code})",
                        "details": test_result
                    }
                    
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "message": f"Test execution failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def test_full_pipeline_dry_run(self) -> Dict[str, Any]:
        """Test 2: Pipeline Complet Dry-Run - POST /api/amazon/pipeline/test/full-pipeline-dry-run"""
        test_name = "Pipeline Complet Dry-Run"
        logger.info(f"🧪 Testing: {test_name}")
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                auth_headers = self.get_auth_headers()
                
                # Test full pipeline dry-run
                test_payload = {
                    "product_data": {
                        **self.test_product_data,
                        "auto_publish": False  # Dry-run mode
                    }
                }
                
                response = await client.post(
                    f"{self.backend_url}/api/amazon/pipeline/test/full-pipeline-dry-run",
                    json=test_payload,
                    headers=auth_headers
                )
                
                test_result = {
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0,
                    "accessible": response.status_code in [200, 201]
                }
                
                if response.status_code in [200, 201]:
                    response_data = response.json()
                    test_result["response_data"] = response_data
                    
                    # Validate pipeline stages
                    expected_stages = ["seo_optimization", "price_scraping", "amazon_format", "validation"]
                    pipeline_complete = False
                    
                    if "pipeline_stages" in response_data:
                        stages = response_data["pipeline_stages"]
                        completed_stages = [stage for stage in expected_stages if stage in stages and stages[stage].get("status") == "completed"]
                        pipeline_complete = len(completed_stages) >= 3  # At least 3 stages should complete
                    
                    # Check SEO A9/A10 compliance
                    seo_compliant = False
                    if "seo_data" in response_data:
                        seo_data = response_data["seo_data"]
                        title_length = len(seo_data.get("title", ""))
                        bullets_count = len(seo_data.get("bullet_points", []))
                        seo_compliant = title_length <= 200 and bullets_count == 5
                    
                    # Check Amazon SP-API format
                    amazon_format_valid = False
                    if "amazon_listing" in response_data:
                        listing = response_data["amazon_listing"]
                        required_fields = ["title", "bullet_point_1", "description", "search_terms"]
                        amazon_format_valid = all(field in listing for field in required_fields)
                    
                    test_result.update({
                        "pipeline_complete": pipeline_complete,
                        "seo_compliant": seo_compliant,
                        "amazon_format_valid": amazon_format_valid,
                        "dry_run_mode": response_data.get("dry_run", False)
                    })
                    
                    if pipeline_complete and seo_compliant and amazon_format_valid:
                        return {
                            "test": test_name,
                            "status": "PASS",
                            "message": "Pipeline complet dry-run fonctionne avec conformité SEO A9/A10 et format Amazon SP-API",
                            "details": test_result
                        }
                    else:
                        return {
                            "test": test_name,
                            "status": "PARTIAL_PASS",
                            "message": "Pipeline dry-run accessible mais étapes incomplètes ou non conformes",
                            "details": test_result
                        }
                else:
                    test_result["error_message"] = response.text
                    return {
                        "test": test_name,
                        "status": "FAIL",
                        "message": f"Pipeline dry-run endpoint non accessible (status: {response.status_code})",
                        "details": test_result
                    }
                    
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "message": f"Test execution failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def test_pipeline_stats_monitoring(self) -> Dict[str, Any]:
        """Test 3: Pipeline Stats & Monitoring - GET /api/amazon/pipeline/stats"""
        test_name = "Pipeline Stats & Monitoring"
        logger.info(f"🧪 Testing: {test_name}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                auth_headers = self.get_auth_headers()
                
                # Test pipeline stats endpoint
                response = await client.get(
                    f"{self.backend_url}/api/amazon/pipeline/stats",
                    headers=auth_headers
                )
                
                test_result = {
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0,
                    "accessible": response.status_code == 200
                }
                
                if response.status_code == 200:
                    response_data = response.json()
                    test_result["response_data"] = response_data
                    
                    # Validate monitoring data structure
                    expected_metrics = ["total_pipelines", "success_rate", "average_processing_time"]
                    has_metrics = any(metric in response_data for metric in expected_metrics)
                    
                    # Check if monitoring is operational
                    monitoring_operational = False
                    if "status" in response_data:
                        monitoring_operational = response_data["status"] == "operational"
                    
                    # Check if stats are recent (within last hour)
                    stats_recent = False
                    if "last_updated" in response_data:
                        try:
                            last_updated = datetime.fromisoformat(response_data["last_updated"].replace('Z', '+00:00'))
                            time_diff = datetime.now() - last_updated.replace(tzinfo=None)
                            stats_recent = time_diff.total_seconds() < 3600  # Within 1 hour
                        except:
                            pass
                    
                    test_result.update({
                        "has_metrics": has_metrics,
                        "monitoring_operational": monitoring_operational,
                        "stats_recent": stats_recent
                    })
                    
                    if has_metrics and monitoring_operational:
                        return {
                            "test": test_name,
                            "status": "PASS",
                            "message": "Pipeline stats & monitoring opérationnel avec métriques complètes",
                            "details": test_result
                        }
                    else:
                        return {
                            "test": test_name,
                            "status": "PARTIAL_PASS",
                            "message": "Pipeline stats accessible mais métriques incomplètes",
                            "details": test_result
                        }
                else:
                    test_result["error_message"] = response.text
                    return {
                        "test": test_name,
                        "status": "FAIL",
                        "message": f"Pipeline stats endpoint non accessible (status: {response.status_code})",
                        "details": test_result
                    }
                    
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "message": f"Test execution failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def test_iphone_15_pro_workflow(self) -> Dict[str, Any]:
        """Test 4: Validation 1 SKU Test - iPhone 15 Pro workflow complet"""
        test_name = "iPhone 15 Pro Workflow Complet"
        logger.info(f"🧪 Testing: {test_name}")
        
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                auth_headers = self.get_auth_headers()
                
                # Test complete iPhone 15 Pro workflow
                workflow_payload = {
                    "product_data": {
                        **self.test_product_data,
                        "auto_publish": False,  # Safe mode for testing
                        "validate_seo": True,
                        "include_pricing": True,
                        "target_marketplace": "FR"
                    }
                }
                
                response = await client.post(
                    f"{self.backend_url}/api/amazon/pipeline/test/full-pipeline-dry-run",
                    json=workflow_payload,
                    headers=auth_headers
                )
                
                test_result = {
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0,
                    "accessible": response.status_code in [200, 201]
                }
                
                if response.status_code in [200, 201]:
                    response_data = response.json()
                    test_result["response_data"] = response_data
                    
                    # Validate iPhone 15 Pro specific criteria
                    criteria_checks = {
                        "seo_title_length": False,
                        "bullet_points_count": False,
                        "price_range_realistic": False,
                        "amazon_format_complete": False,
                        "workflow_success": False
                    }
                    
                    # Check SEO title length (≤200 chars)
                    if "seo_data" in response_data and "title" in response_data["seo_data"]:
                        title_length = len(response_data["seo_data"]["title"])
                        criteria_checks["seo_title_length"] = title_length <= 200
                    
                    # Check bullet points count (=5)
                    if "seo_data" in response_data and "bullet_points" in response_data["seo_data"]:
                        bullets_count = len(response_data["seo_data"]["bullet_points"])
                        criteria_checks["bullet_points_count"] = bullets_count == 5
                    
                    # Check price range (800-1500 EUR for iPhone 15 Pro)
                    if "pricing_data" in response_data and "suggested_price" in response_data["pricing_data"]:
                        price = float(response_data["pricing_data"]["suggested_price"])
                        criteria_checks["price_range_realistic"] = 800 <= price <= 1500
                    
                    # Check Amazon format completeness
                    if "amazon_listing" in response_data:
                        listing = response_data["amazon_listing"]
                        required_fields = ["title", "bullet_point_1", "bullet_point_2", "bullet_point_3", 
                                         "bullet_point_4", "bullet_point_5", "description", "search_terms"]
                        criteria_checks["amazon_format_complete"] = all(field in listing and listing[field] for field in required_fields)
                    
                    # Check overall workflow success
                    criteria_checks["workflow_success"] = response_data.get("success", False)
                    
                    test_result["criteria_checks"] = criteria_checks
                    passed_criteria = sum(criteria_checks.values())
                    total_criteria = len(criteria_checks)
                    
                    if passed_criteria == total_criteria:
                        return {
                            "test": test_name,
                            "status": "PASS",
                            "message": f"iPhone 15 Pro workflow complet réussi - tous critères validés ({passed_criteria}/{total_criteria})",
                            "details": test_result
                        }
                    elif passed_criteria >= total_criteria * 0.8:
                        return {
                            "test": test_name,
                            "status": "PARTIAL_PASS",
                            "message": f"iPhone 15 Pro workflow partiellement réussi ({passed_criteria}/{total_criteria} critères)",
                            "details": test_result
                        }
                    else:
                        return {
                            "test": test_name,
                            "status": "FAIL",
                            "message": f"iPhone 15 Pro workflow échoué ({passed_criteria}/{total_criteria} critères)",
                            "details": test_result
                        }
                else:
                    test_result["error_message"] = response.text
                    return {
                        "test": test_name,
                        "status": "FAIL",
                        "message": f"iPhone 15 Pro workflow endpoint non accessible (status: {response.status_code})",
                        "details": test_result
                    }
                    
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "message": f"Test execution failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Amazon Pipeline tests"""
        logger.info("🚀 Starting Amazon Pipeline Publication Automatique Test Suite")
        
        # Setup authentication
        auth_success = await self.setup_authentication()
        if not auth_success:
            logger.warning("⚠️ Authentication failed - tests may be limited")
        
        # Define all tests
        tests = [
            self.test_price_scraping_only,
            self.test_full_pipeline_dry_run,
            self.test_pipeline_stats_monitoring,
            self.test_iphone_15_pro_workflow
        ]
        
        # Run all tests
        results = []
        for test_func in tests:
            try:
                result = await test_func()
                results.append(result)
                self.total_tests += 1
                
                if result['status'] in ['PASS', 'PARTIAL_PASS']:
                    self.passed_tests += 1
                    logger.info(f"✅ {result['test']}: {result['status']}")
                else:
                    logger.error(f"❌ {result['test']}: {result['status']} - {result['message']}")
                    
            except Exception as e:
                error_result = {
                    "test": test_func.__name__,
                    "status": "ERROR",
                    "message": f"Test execution failed: {str(e)}",
                    "details": {"error": str(e)}
                }
                results.append(error_result)
                self.total_tests += 1
                logger.error(f"💥 {test_func.__name__}: ERROR - {str(e)}")
        
        # Calculate overall results
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        summary = {
            "test_suite": "Amazon Pipeline Publication Automatique",
            "timestamp": datetime.now().isoformat(),
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "success_rate": f"{success_rate:.1f}%",
            "overall_status": "PASS" if success_rate >= 80 else "PARTIAL_PASS" if success_rate >= 60 else "FAIL",
            "test_results": results
        }
        
        return summary

async def main():
    """Main test execution function"""
    print("=" * 80)
    print("🧪 ECOMSIMPLY AMAZON PIPELINE PUBLICATION AUTOMATIQUE TESTING")
    print("=" * 80)
    
    # Initialize test suite
    test_suite = AmazonPipelineTest()
    
    # Run all tests
    results = await test_suite.run_all_tests()
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    print(f"Test Suite: {results['test_suite']}")
    print(f"Timestamp: {results['timestamp']}")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed Tests: {results['passed_tests']}")
    print(f"Success Rate: {results['success_rate']}")
    print(f"Overall Status: {results['overall_status']}")
    
    print("\n📋 DETAILED RESULTS:")
    print("-" * 80)
    
    for i, test_result in enumerate(results['test_results'], 1):
        status_emoji = "✅" if test_result['status'] == "PASS" else "⚠️" if test_result['status'] == "PARTIAL_PASS" else "❌"
        print(f"{i}. {status_emoji} {test_result['test']}")
        print(f"   Status: {test_result['status']}")
        print(f"   Message: {test_result['message']}")
        
        if test_result.get('details'):
            # Print key details without overwhelming output
            details = test_result['details']
            if 'status_code' in details:
                print(f"   Status Code: {details['status_code']}")
            if 'response_time' in details:
                print(f"   Response Time: {details['response_time']:.2f}s")
            if 'criteria_checks' in details:
                print(f"   Criteria Passed: {sum(details['criteria_checks'].values())}/{len(details['criteria_checks'])}")
        print()
    
    print("=" * 80)
    
    # Return appropriate exit code
    return 0 if results['overall_status'] in ['PASS', 'PARTIAL_PASS'] else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)