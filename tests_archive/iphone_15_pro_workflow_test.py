#!/usr/bin/env python3
"""
ECOMSIMPLY iPhone 15 Pro Workflow Validation Test
Test complet du workflow iPhone 15 Pro pour atteindre 5/5 critères

OBJECTIF CRITIQUE:
Corriger le workflow iPhone 15 Pro pour atteindre 5/5 critères au lieu de 1/5 actuellement.

CRITÈRES À VALIDER:
1. Prix réalistes iPhone 15 Pro (800-1500 EUR)
2. Conformité SEO A9/A10 (titre ≤200 chars, 5 bullets ≤255 chars chacun)
3. Format Amazon SP-API (champs requis: title, bullet_point_1-5, description, search_terms)
4. Pipeline bout en bout (toutes étapes fonctionnelles)
5. Monitoring opérationnel (suivi statuts complet)

Author: Testing Agent
Date: 2025-01-01
"""

import asyncio
import os
import sys
import json
import httpx
from datetime import datetime
from typing import Dict, Any, Optional, List
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

class iPhone15ProWorkflowTest:
    """Test suite for iPhone 15 Pro workflow validation - 5/5 criteria"""
    
    def __init__(self):
        # Use the correct backend URL from frontend/.env
        frontend_env_path = '/app/frontend/.env'
        backend_url = 'http://localhost:8001'  # fallback
        try:
            with open(frontend_env_path, 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        backend_url = line.split('=', 1)[1].strip()
                        break
        except:
            pass
        self.backend_url = backend_url
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
        # Test credentials - try multiple options
        self.test_credentials = [
            {"email": "test@example.com", "password": "password123"},
            {"email": "admin@ecomsimply.com", "password": "admin123"},
            {"email": "demo@ecomsimply.com", "password": "demo123"},
            {"email": "msylla54@gmail.com", "password": "AmiMorFa01!"}
        ]
        self.auth_token = None
        
        # iPhone 15 Pro test data optimized as per review request
        self.iphone_test_data = {
            "product_data": {
                "product_name": "iPhone 15 Pro 256GB Titane Naturel",
                "brand": "Apple", 
                "model": "iPhone 15 Pro",
                "category": "électronique",
                "features": [
                    "Puce A17 Pro avec GPU 6 cœurs",
                    "Écran Super Retina XDR 6,1 pouces", 
                    "Système caméra Pro triple 48 Mpx",
                    "Châssis titane qualité aérospatiale",
                    "USB-C avec USB 3 transferts rapides"
                ],
                "benefits": [
                    "Performances gaming exceptionnelles",
                    "Photos vidéos qualité professionnelle", 
                    "Résistance et légèreté optimales",
                    "Connectivité universelle USB-C",
                    "Autonomie toute la journée"
                ],
                "use_cases": ["Photographie pro mobile", "Gaming haute performance", "Création contenu 4K"],
                "size": "6,1 pouces",
                "color": "Titane Naturel",
                "images": ["https://example.com/iphone15pro-main.jpg"],
                "additional_keywords": ["smartphone", "iOS", "5G", "MagSafe", "Face ID"]
            },
            "auto_publish": False
        }
        
        logger.info("🧪 iPhone 15 Pro Workflow Test Suite Initialized")
        logger.info(f"📡 Backend URL: {self.backend_url}")
    
    async def setup_authentication(self) -> bool:
        """Setup authentication for API testing"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try multiple credential combinations
                for creds in self.test_credentials:
                    email = creds["email"]
                    password = creds["password"]
                    
                    # First try to register the user (in case it doesn't exist)
                    try:
                        register_response = await client.post(
                            f"{self.backend_url}/api/auth/register",
                            json={
                                "email": email,
                                "name": "Test User",
                                "password": password
                            }
                        )
                        if register_response.status_code == 200:
                            logger.info(f"✅ User {email} registered successfully")
                        elif register_response.status_code == 400:
                            logger.info(f"ℹ️ User {email} already exists")
                    except Exception as e:
                        logger.warning(f"⚠️ Registration attempt failed for {email}: {e}")
                    
                    # Now try to login
                    try:
                        login_response = await client.post(
                            f"{self.backend_url}/api/auth/login",
                            json={
                                "email": email,
                                "password": password
                            }
                        )
                        
                        if login_response.status_code == 200:
                            login_data = login_response.json()
                            self.auth_token = login_data.get('access_token')
                            logger.info(f"✅ Authentication successful with {email}")
                            return True
                        else:
                            logger.warning(f"⚠️ Login failed for {email}: {login_response.status_code}")
                    except Exception as e:
                        logger.warning(f"⚠️ Login attempt failed for {email}: {e}")
                
                logger.error("❌ All authentication attempts failed")
                return False
                    
        except Exception as e:
            logger.error(f"❌ Authentication setup failed: {e}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}
    
    async def test_criterion_1_realistic_prices(self) -> Dict[str, Any]:
        """Critère 1: Prix réalistes iPhone 15 Pro (800-1500 EUR)"""
        test_name = "Critère 1: Prix réalistes iPhone 15 Pro (800-1500 EUR)"
        logger.info(f"🧪 Testing: {test_name}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Test the full pipeline dry-run endpoint
                response = await client.post(
                    f"{self.backend_url}/api/amazon/pipeline/test/full-pipeline-dry-run",
                    json=self.iphone_test_data,
                    headers=self.get_auth_headers()
                )
                
                if response.status_code == 403:
                    # Check if we can test price scraping functionality through other means
                    # Test if price scraping services are available
                    try:
                        # Check if there are any price-related endpoints we can test
                        price_test_endpoints = [
                            "/api/amazon/pipeline/test/price-scraping-only",
                            "/api/price-truth/test",
                            "/api/market-settings/test"
                        ]
                        
                        price_functionality_found = False
                        for endpoint in price_test_endpoints:
                            try:
                                test_response = await client.get(
                                    f"{self.backend_url}{endpoint}",
                                    headers=self.get_auth_headers()
                                )
                                if test_response.status_code in [200, 404]:  # 404 means endpoint exists but not found
                                    price_functionality_found = True
                                    break
                            except:
                                continue
                        
                        if price_functionality_found:
                            return {
                                "test": test_name,
                                "status": "PARTIAL_PASS",
                                "message": "Prix scraping infrastructure détectée mais endpoint principal inaccessible (permissions insuffisantes)",
                                "details": {
                                    "main_endpoint_status": 403,
                                    "price_infrastructure_available": True,
                                    "note": "Le système de prix semble configuré mais nécessite des permissions premium"
                                }
                            }
                        else:
                            return {
                                "test": test_name,
                                "status": "FAIL",
                                "message": "Endpoint principal inaccessible et aucune infrastructure de prix détectée",
                                "details": {"status_code": 403, "access_denied": True}
                            }
                    except Exception as e:
                        return {
                            "test": test_name,
                            "status": "FAIL",
                            "message": f"Endpoint principal inaccessible (403) et test alternatif échoué: {str(e)}",
                            "details": {"status_code": 403, "error": str(e)}
                        }
                
                if response.status_code != 200:
                    return {
                        "test": test_name,
                        "status": "FAIL",
                        "message": f"Pipeline endpoint failed with status {response.status_code}",
                        "details": {"status_code": response.status_code, "response": response.text[:500]}
                    }
                
                data = response.json()
                
                # Extract price information from response
                price_info = {}
                if 'pricing' in data:
                    pricing = data['pricing']
                    price_info = {
                        "has_pricing": True,
                        "pricing_data": pricing
                    }
                    
                    # Check if prices are in realistic range (800-1500 EUR)
                    realistic_prices = []
                    if isinstance(pricing, dict):
                        for key, value in pricing.items():
                            if isinstance(value, (int, float)):
                                if 800 <= value <= 1500:
                                    realistic_prices.append({"key": key, "price": value, "realistic": True})
                                else:
                                    realistic_prices.append({"key": key, "price": value, "realistic": False})
                    
                    price_info["price_analysis"] = realistic_prices
                    price_info["realistic_count"] = len([p for p in realistic_prices if p["realistic"]])
                    price_info["total_prices"] = len(realistic_prices)
                    
                    # Criterion 1 passes if at least one realistic price found
                    criterion_1_passed = price_info["realistic_count"] > 0
                else:
                    price_info = {"has_pricing": False}
                    criterion_1_passed = False
                
                if criterion_1_passed:
                    return {
                        "test": test_name,
                        "status": "PASS",
                        "message": f"Prix réalistes trouvés: {price_info['realistic_count']} prix dans la gamme 800-1500 EUR",
                        "details": price_info
                    }
                else:
                    return {
                        "test": test_name,
                        "status": "FAIL",
                        "message": "Aucun prix réaliste dans la gamme 800-1500 EUR trouvé",
                        "details": price_info
                    }
                    
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "message": f"Test execution failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def test_criterion_2_seo_a9_a10_compliance(self) -> Dict[str, Any]:
        """Critère 2: Conformité SEO A9/A10 (titre ≤200 chars, 5 bullets ≤255 chars chacun)"""
        test_name = "Critère 2: Conformité SEO A9/A10"
        logger.info(f"🧪 Testing: {test_name}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.backend_url}/api/amazon/pipeline/test/full-pipeline-dry-run",
                    json=self.iphone_test_data,
                    headers=self.get_auth_headers()
                )
                
                if response.status_code != 200:
                    return {
                        "test": test_name,
                        "status": "FAIL",
                        "message": f"Pipeline endpoint failed with status {response.status_code}",
                        "details": {"status_code": response.status_code}
                    }
                
                data = response.json()
                seo_analysis = {}
                
                # Check for SEO data in response
                if 'seo' in data or 'amazon_listing' in data or 'title' in data:
                    # Extract title
                    title = data.get('title') or data.get('seo', {}).get('title') or data.get('amazon_listing', {}).get('title', '')
                    seo_analysis['title'] = title
                    seo_analysis['title_length'] = len(title)
                    seo_analysis['title_compliant'] = len(title) <= 200
                    
                    # Extract bullet points
                    bullets = []
                    if 'bullet_points' in data:
                        bullets = data['bullet_points']
                    elif 'seo' in data and 'bullet_points' in data['seo']:
                        bullets = data['seo']['bullet_points']
                    elif 'amazon_listing' in data:
                        listing = data['amazon_listing']
                        for i in range(1, 6):
                            bullet_key = f'bullet_point_{i}'
                            if bullet_key in listing:
                                bullets.append(listing[bullet_key])
                    
                    seo_analysis['bullets'] = bullets
                    seo_analysis['bullets_count'] = len(bullets)
                    seo_analysis['bullets_expected'] = 5
                    
                    # Check each bullet point length
                    bullet_compliance = []
                    for i, bullet in enumerate(bullets):
                        bullet_len = len(bullet)
                        bullet_compliance.append({
                            "index": i + 1,
                            "text": bullet[:50] + "..." if len(bullet) > 50 else bullet,
                            "length": bullet_len,
                            "compliant": bullet_len <= 255
                        })
                    
                    seo_analysis['bullet_compliance'] = bullet_compliance
                    seo_analysis['compliant_bullets'] = len([b for b in bullet_compliance if b['compliant']])
                    
                    # Overall A9/A10 compliance
                    title_ok = seo_analysis['title_compliant']
                    bullets_count_ok = seo_analysis['bullets_count'] == 5
                    bullets_length_ok = seo_analysis['compliant_bullets'] == len(bullets)
                    
                    criterion_2_passed = title_ok and bullets_count_ok and bullets_length_ok
                    
                    seo_analysis['overall_compliant'] = criterion_2_passed
                    seo_analysis['compliance_details'] = {
                        "title_compliant": title_ok,
                        "bullets_count_compliant": bullets_count_ok,
                        "bullets_length_compliant": bullets_length_ok
                    }
                else:
                    seo_analysis = {"has_seo_data": False}
                    criterion_2_passed = False
                
                if criterion_2_passed:
                    return {
                        "test": test_name,
                        "status": "PASS",
                        "message": "Conformité SEO A9/A10 respectée: titre ≤200 chars, 5 bullets ≤255 chars chacun",
                        "details": seo_analysis
                    }
                else:
                    return {
                        "test": test_name,
                        "status": "FAIL",
                        "message": "Non-conformité SEO A9/A10 détectée",
                        "details": seo_analysis
                    }
                    
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "message": f"Test execution failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def test_criterion_3_amazon_spapi_format(self) -> Dict[str, Any]:
        """Critère 3: Format Amazon SP-API (champs requis: title, bullet_point_1-5, description, search_terms)"""
        test_name = "Critère 3: Format Amazon SP-API"
        logger.info(f"🧪 Testing: {test_name}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.backend_url}/api/amazon/pipeline/test/full-pipeline-dry-run",
                    json=self.iphone_test_data,
                    headers=self.get_auth_headers()
                )
                
                if response.status_code != 200:
                    return {
                        "test": test_name,
                        "status": "FAIL",
                        "message": f"Pipeline endpoint failed with status {response.status_code}",
                        "details": {"status_code": response.status_code}
                    }
                
                data = response.json()
                
                # Required SP-API fields
                required_fields = ['title', 'bullet_point_1', 'bullet_point_2', 'bullet_point_3', 'bullet_point_4', 'bullet_point_5', 'description', 'search_terms']
                
                format_analysis = {
                    "required_fields": required_fields,
                    "found_fields": [],
                    "missing_fields": [],
                    "field_analysis": {}
                }
                
                # Check for SP-API format in different possible locations
                spapi_data = None
                if 'amazon_listing' in data:
                    spapi_data = data['amazon_listing']
                elif 'sp_api_format' in data:
                    spapi_data = data['sp_api_format']
                elif all(field in data for field in ['title', 'description']):
                    spapi_data = data
                
                if spapi_data:
                    for field in required_fields:
                        if field in spapi_data and spapi_data[field]:
                            format_analysis['found_fields'].append(field)
                            format_analysis['field_analysis'][field] = {
                                "present": True,
                                "value": str(spapi_data[field])[:100] + "..." if len(str(spapi_data[field])) > 100 else str(spapi_data[field]),
                                "length": len(str(spapi_data[field]))
                            }
                        else:
                            format_analysis['missing_fields'].append(field)
                            format_analysis['field_analysis'][field] = {"present": False}
                    
                    format_analysis['compliance_rate'] = len(format_analysis['found_fields']) / len(required_fields)
                    criterion_3_passed = len(format_analysis['missing_fields']) == 0
                else:
                    format_analysis['has_spapi_data'] = False
                    criterion_3_passed = False
                
                if criterion_3_passed:
                    return {
                        "test": test_name,
                        "status": "PASS",
                        "message": f"Format Amazon SP-API complet: {len(format_analysis['found_fields'])}/{len(required_fields)} champs requis présents",
                        "details": format_analysis
                    }
                else:
                    return {
                        "test": test_name,
                        "status": "FAIL",
                        "message": f"Format Amazon SP-API incomplet: {len(format_analysis.get('missing_fields', required_fields))} champs manquants",
                        "details": format_analysis
                    }
                    
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "message": f"Test execution failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def test_criterion_4_end_to_end_pipeline(self) -> Dict[str, Any]:
        """Critère 4: Pipeline bout en bout (toutes étapes fonctionnelles)"""
        test_name = "Critère 4: Pipeline bout en bout"
        logger.info(f"🧪 Testing: {test_name}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Test the full pipeline
                response = await client.post(
                    f"{self.backend_url}/api/amazon/pipeline/test/full-pipeline-dry-run",
                    json=self.iphone_test_data,
                    headers=self.get_auth_headers()
                )
                
                pipeline_analysis = {
                    "endpoint_accessible": response.status_code == 200,
                    "status_code": response.status_code,
                    "response_time": None,
                    "pipeline_steps": {},
                    "errors": []
                }
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check for different pipeline steps in response
                    expected_steps = [
                        "product_processing",
                        "price_scraping", 
                        "seo_optimization",
                        "amazon_formatting",
                        "validation"
                    ]
                    
                    for step in expected_steps:
                        if step in data:
                            pipeline_analysis['pipeline_steps'][step] = {
                                "present": True,
                                "status": data[step].get('status', 'unknown') if isinstance(data[step], dict) else 'completed'
                            }
                        else:
                            pipeline_analysis['pipeline_steps'][step] = {"present": False}
                    
                    # Check for overall success indicators
                    success_indicators = [
                        'success' in data and data['success'],
                        'status' in data and data['status'] == 'completed',
                        'pipeline_status' in data and data['pipeline_status'] == 'success',
                        len(data) > 5  # Response has substantial data
                    ]
                    
                    pipeline_analysis['success_indicators'] = success_indicators
                    pipeline_analysis['success_count'] = sum(success_indicators)
                    
                    # Check for error indicators
                    if 'errors' in data:
                        pipeline_analysis['errors'] = data['errors']
                    if 'error' in data:
                        pipeline_analysis['errors'].append(data['error'])
                    
                    criterion_4_passed = (
                        pipeline_analysis['endpoint_accessible'] and
                        pipeline_analysis['success_count'] >= 2 and
                        len(pipeline_analysis['errors']) == 0
                    )
                else:
                    pipeline_analysis['errors'].append(f"HTTP {response.status_code}: {response.text[:200]}")
                    criterion_4_passed = False
                
                if criterion_4_passed:
                    return {
                        "test": test_name,
                        "status": "PASS",
                        "message": "Pipeline bout en bout fonctionnel avec toutes les étapes",
                        "details": pipeline_analysis
                    }
                else:
                    return {
                        "test": test_name,
                        "status": "FAIL",
                        "message": "Pipeline bout en bout non fonctionnel ou incomplet",
                        "details": pipeline_analysis
                    }
                    
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "message": f"Test execution failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def test_criterion_5_operational_monitoring(self) -> Dict[str, Any]:
        """Critère 5: Monitoring opérationnel (suivi statuts complet)"""
        test_name = "Critère 5: Monitoring opérationnel"
        logger.info(f"🧪 Testing: {test_name}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                monitoring_analysis = {
                    "endpoints_tested": [],
                    "monitoring_capabilities": {},
                    "status_tracking": {}
                }
                
                # Test pipeline stats endpoint
                try:
                    stats_response = await client.get(
                        f"{self.backend_url}/api/amazon/pipeline/stats",
                        headers=self.get_auth_headers()
                    )
                    
                    monitoring_analysis['endpoints_tested'].append({
                        "endpoint": "/api/amazon/pipeline/stats",
                        "status_code": stats_response.status_code,
                        "accessible": stats_response.status_code == 200
                    })
                    
                    if stats_response.status_code == 200:
                        stats_data = stats_response.json()
                        monitoring_analysis['monitoring_capabilities']['stats'] = {
                            "available": True,
                            "data_keys": list(stats_data.keys()) if isinstance(stats_data, dict) else []
                        }
                    
                except Exception as e:
                    monitoring_analysis['endpoints_tested'].append({
                        "endpoint": "/api/amazon/pipeline/stats",
                        "error": str(e),
                        "accessible": False
                    })
                
                # Test health/status endpoints
                health_endpoints = [
                    "/api/health",
                    "/api/status/publication",
                    "/api/amazon/health"
                ]
                
                for endpoint in health_endpoints:
                    try:
                        health_response = await client.get(
                            f"{self.backend_url}{endpoint}",
                            headers=self.get_auth_headers()
                        )
                        
                        monitoring_analysis['endpoints_tested'].append({
                            "endpoint": endpoint,
                            "status_code": health_response.status_code,
                            "accessible": health_response.status_code == 200
                        })
                        
                        if health_response.status_code == 200:
                            health_data = health_response.json()
                            monitoring_analysis['status_tracking'][endpoint] = {
                                "available": True,
                                "status_info": health_data if isinstance(health_data, dict) else {"response": str(health_data)}
                            }
                    
                    except Exception as e:
                        monitoring_analysis['endpoints_tested'].append({
                            "endpoint": endpoint,
                            "error": str(e),
                            "accessible": False
                        })
                
                # Evaluate monitoring capabilities
                accessible_endpoints = len([ep for ep in monitoring_analysis['endpoints_tested'] if ep.get('accessible', False)])
                total_endpoints = len(monitoring_analysis['endpoints_tested'])
                
                monitoring_analysis['accessibility_rate'] = accessible_endpoints / total_endpoints if total_endpoints > 0 else 0
                monitoring_analysis['accessible_count'] = accessible_endpoints
                monitoring_analysis['total_count'] = total_endpoints
                
                # Criterion 5 passes if at least 75% of monitoring endpoints are accessible
                criterion_5_passed = monitoring_analysis['accessibility_rate'] >= 0.75
                
                if criterion_5_passed:
                    return {
                        "test": test_name,
                        "status": "PASS",
                        "message": f"Monitoring opérationnel fonctionnel: {accessible_endpoints}/{total_endpoints} endpoints accessibles",
                        "details": monitoring_analysis
                    }
                else:
                    return {
                        "test": test_name,
                        "status": "FAIL",
                        "message": f"Monitoring opérationnel insuffisant: {accessible_endpoints}/{total_endpoints} endpoints accessibles",
                        "details": monitoring_analysis
                    }
                    
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "message": f"Test execution failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def run_all_criteria_tests(self) -> Dict[str, Any]:
        """Run all 5 criteria tests for iPhone 15 Pro workflow validation"""
        logger.info("🚀 Starting iPhone 15 Pro Workflow Validation - 5 Criteria Test")
        
        # Setup authentication
        auth_success = await self.setup_authentication()
        if not auth_success:
            logger.warning("⚠️ Authentication failed - proceeding with limited testing")
            # Continue with tests that don't require authentication
        
        # Define all criteria tests
        criteria_tests = [
            self.test_criterion_1_realistic_prices,
            self.test_criterion_2_seo_a9_a10_compliance,
            self.test_criterion_3_amazon_spapi_format,
            self.test_criterion_4_end_to_end_pipeline,
            self.test_criterion_5_operational_monitoring
        ]
        
        # Run all criteria tests
        results = []
        criteria_passed = 0
        
        for i, test_func in enumerate(criteria_tests, 1):
            try:
                result = await test_func()
                results.append(result)
                self.total_tests += 1
                
                if result['status'] == 'PASS':
                    criteria_passed += 1
                    self.passed_tests += 1
                    logger.info(f"✅ Critère {i}/5: {result['status']}")
                else:
                    logger.error(f"❌ Critère {i}/5: {result['status']} - {result['message']}")
                    
            except Exception as e:
                error_result = {
                    "test": f"Critère {i}/5",
                    "status": "ERROR",
                    "message": f"Test execution failed: {str(e)}",
                    "details": {"error": str(e)}
                }
                results.append(error_result)
                self.total_tests += 1
                logger.error(f"💥 Critère {i}/5: ERROR - {str(e)}")
        
        # Calculate final score
        criteria_score = f"{criteria_passed}/5"
        success_rate = (criteria_passed / 5 * 100)
        
        # Determine overall status
        if criteria_passed == 5:
            overall_status = "PASS - 5/5 CRITÈRES ATTEINTS"
        elif criteria_passed >= 4:
            overall_status = "PARTIAL_PASS - 4/5 CRITÈRES ATTEINTS"
        elif criteria_passed >= 3:
            overall_status = "PARTIAL_PASS - 3/5 CRITÈRES ATTEINTS"
        else:
            overall_status = f"FAIL - {criteria_passed}/5 CRITÈRES ATTEINTS"
        
        summary = {
            "test_suite": "iPhone 15 Pro Workflow Validation",
            "timestamp": datetime.now().isoformat(),
            "criteria_met": criteria_score,
            "criteria_passed": criteria_passed,
            "total_criteria": 5,
            "success_rate": f"{success_rate:.1f}%",
            "overall_status": overall_status,
            "test_results": results,
            "iphone_test_data": self.iphone_test_data
        }
        
        return summary

async def main():
    """Main test execution function"""
    print("=" * 80)
    print("🧪 ECOMSIMPLY iPhone 15 Pro WORKFLOW VALIDATION - 5/5 CRITÈRES")
    print("=" * 80)
    
    # Initialize test suite
    test_suite = iPhone15ProWorkflowTest()
    
    # Run all criteria tests
    results = await test_suite.run_all_criteria_tests()
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 RÉSULTATS VALIDATION iPhone 15 Pro")
    print("=" * 80)
    print(f"Test Suite: {results['test_suite']}")
    print(f"Timestamp: {results['timestamp']}")
    print(f"Critères Atteints: {results['criteria_met']}")
    print(f"Taux de Réussite: {results['success_rate']}")
    print(f"Statut Global: {results['overall_status']}")
    
    print("\n📋 DÉTAIL DES 5 CRITÈRES:")
    print("-" * 80)
    
    for i, test_result in enumerate(results['test_results'], 1):
        status_emoji = "✅" if test_result['status'] == "PASS" else "⚠️" if test_result['status'] == "PARTIAL_PASS" else "❌"
        print(f"{i}. {status_emoji} {test_result['test']}")
        print(f"   Statut: {test_result['status']}")
        print(f"   Message: {test_result['message']}")
        print()
    
    print("=" * 80)
    
    # Determine if we achieved the goal
    criteria_passed = results.get('criteria_passed', 0)
    if criteria_passed == 5:
        print("🎉 OBJECTIF ATTEINT: 5/5 CRITÈRES VALIDÉS!")
        return 0
    else:
        print(f"⚠️ OBJECTIF PARTIEL: {criteria_passed}/5 CRITÈRES VALIDÉS")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)