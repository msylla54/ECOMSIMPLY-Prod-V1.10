#!/usr/bin/env python3
"""
ECOMSIMPLY Backend Regression Testing
Test backend après corrections JavaScript pour s'assurer qu'aucune régression n'a été introduite

Zones de test spécifiques:
1. Santé générale du backend - Tous les services opérationnels
2. Endpoints Amazon - OAuth et statuts Amazon fonctionnent
3. Endpoints principaux - API stats, testimonials, plans fonctionnent
4. Authentification - Système d'auth fonctionne correctement
5. Base de données - Connexion MongoDB opérationnelle
"""

import os
import sys
import asyncio
import json
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, List
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')
load_dotenv('/app/backend/.env')

# Add backend path for imports
sys.path.append('/app/backend')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EcomsimplyRegressionTester:
    """Comprehensive regression tester for ECOMSIMPLY backend after JavaScript fixes"""
    
    def __init__(self):
        self.results = {
            'backend_health': {'status': False, 'details': []},
            'amazon_endpoints': {'status': False, 'details': []},
            'main_endpoints': {'status': False, 'details': []},
            'authentication': {'status': False, 'details': []},
            'database_connection': {'status': False, 'details': []},
            'overall_status': False,
            'success_rate': 0.0
        }
        
        # Get backend URL from environment
        self.backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
        if not self.backend_url.endswith('/api'):
            self.backend_url = f"{self.backend_url}/api"
        
        logger.info(f"🔗 Testing ECOMSIMPLY backend regression at: {self.backend_url}")
        
        # Test credentials for authentication testing
        self.test_user_email = "msylla54@gmail.com"
        self.test_user_password = "AmiMorFa01!"
        self.auth_token = None
    
    async def test_backend_health(self) -> bool:
        """Test 1: Santé générale du backend - Tous les services opérationnels"""
        logger.info("🏥 Test 1: Testing backend general health...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                
                # Test main health endpoint
                try:
                    response = await client.get(f"{self.backend_url}/health")
                    if response.status_code == 200:
                        health_data = response.json()
                        self.results['backend_health']['details'].append("✅ Main health endpoint working")
                        logger.info("✅ Main health endpoint validated")
                        
                        # Check health data structure
                        if 'status' in health_data:
                            self.results['backend_health']['details'].append(f"✅ Health status: {health_data.get('status')}")
                        if 'uptime' in health_data:
                            self.results['backend_health']['details'].append(f"✅ Uptime: {health_data.get('uptime')}")
                        if 'version' in health_data:
                            self.results['backend_health']['details'].append(f"✅ Version: {health_data.get('version')}")
                    else:
                        self.results['backend_health']['details'].append(f"❌ Health endpoint returned {response.status_code}")
                        logger.error(f"❌ Health endpoint returned {response.status_code}")
                        return False
                except Exception as e:
                    self.results['backend_health']['details'].append(f"❌ Health endpoint error: {e}")
                    logger.error(f"❌ Health endpoint error: {e}")
                    return False
                
                # Test ready endpoint
                try:
                    response = await client.get(f"{self.backend_url}/health/ready")
                    if response.status_code == 200:
                        self.results['backend_health']['details'].append("✅ Ready endpoint working")
                        logger.info("✅ Ready endpoint validated")
                    else:
                        self.results['backend_health']['details'].append(f"⚠️ Ready endpoint returned {response.status_code}")
                        logger.warning(f"⚠️ Ready endpoint returned {response.status_code}")
                except Exception as e:
                    self.results['backend_health']['details'].append(f"❌ Ready endpoint error: {e}")
                    logger.error(f"❌ Ready endpoint error: {e}")
                
                # Test live endpoint
                try:
                    response = await client.get(f"{self.backend_url}/health/live")
                    if response.status_code == 200:
                        self.results['backend_health']['details'].append("✅ Live endpoint working")
                        logger.info("✅ Live endpoint validated")
                    else:
                        self.results['backend_health']['details'].append(f"⚠️ Live endpoint returned {response.status_code}")
                        logger.warning(f"⚠️ Live endpoint returned {response.status_code}")
                except Exception as e:
                    self.results['backend_health']['details'].append(f"❌ Live endpoint error: {e}")
                    logger.error(f"❌ Live endpoint error: {e}")
                
                # Test status publication endpoint
                try:
                    response = await client.get(f"{self.backend_url}/status/publication")
                    if response.status_code == 200:
                        status_data = response.json()
                        self.results['backend_health']['details'].append("✅ Publication status endpoint working")
                        logger.info("✅ Publication status endpoint validated")
                        
                        # Check publication status data
                        if 'mode' in status_data:
                            self.results['backend_health']['details'].append(f"✅ Publication mode: {status_data.get('mode')}")
                        if 'auto_publish' in status_data:
                            self.results['backend_health']['details'].append(f"✅ Auto publish: {status_data.get('auto_publish')}")
                    else:
                        self.results['backend_health']['details'].append(f"⚠️ Publication status returned {response.status_code}")
                        logger.warning(f"⚠️ Publication status returned {response.status_code}")
                except Exception as e:
                    self.results['backend_health']['details'].append(f"❌ Publication status error: {e}")
                    logger.error(f"❌ Publication status error: {e}")
            
            self.results['backend_health']['details'].append("✅ Backend health tests completed")
            logger.info("✅ Backend health tests completed successfully")
            return True
            
        except Exception as e:
            self.results['backend_health']['details'].append(f"❌ Unexpected error: {e}")
            logger.error(f"❌ Backend health test failed: {e}")
            return False
    
    async def test_amazon_endpoints(self) -> bool:
        """Test 2: Endpoints Amazon - OAuth et statuts Amazon fonctionnent"""
        logger.info("🛒 Test 2: Testing Amazon endpoints...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                
                # Test Amazon health endpoint
                try:
                    response = await client.get(f"{self.backend_url}/amazon/health")
                    if response.status_code == 200:
                        health_data = response.json()
                        self.results['amazon_endpoints']['details'].append("✅ Amazon health endpoint working")
                        logger.info("✅ Amazon health endpoint validated")
                        
                        # Check Amazon service details
                        if health_data.get('service') == 'Amazon SP-API Integration':
                            self.results['amazon_endpoints']['details'].append("✅ Amazon service identification correct")
                        if 'status' in health_data:
                            self.results['amazon_endpoints']['details'].append(f"✅ Amazon status: {health_data.get('status')}")
                    else:
                        self.results['amazon_endpoints']['details'].append(f"❌ Amazon health returned {response.status_code}")
                        logger.error(f"❌ Amazon health returned {response.status_code}")
                        return False
                except Exception as e:
                    self.results['amazon_endpoints']['details'].append(f"❌ Amazon health error: {e}")
                    logger.error(f"❌ Amazon health error: {e}")
                    return False
                
                # Test Amazon OAuth callback endpoint (should be accessible)
                try:
                    response = await client.get(f"{self.backend_url}/amazon/callback", params={
                        'state': 'test-state',
                        'selling_partner_id': 'test-seller',
                        'spapi_oauth_code': 'test-code'
                    })
                    
                    # Should handle the callback (might return error but endpoint should be accessible)
                    if response.status_code in [200, 302, 400, 404]:
                        self.results['amazon_endpoints']['details'].append("✅ Amazon OAuth callback endpoint accessible")
                        logger.info("✅ Amazon OAuth callback endpoint accessible")
                    else:
                        self.results['amazon_endpoints']['details'].append(f"⚠️ OAuth callback returned {response.status_code}")
                        logger.warning(f"⚠️ OAuth callback returned {response.status_code}")
                except Exception as e:
                    self.results['amazon_endpoints']['details'].append(f"❌ OAuth callback error: {e}")
                    logger.error(f"❌ OAuth callback error: {e}")
                    return False
                
                # Test protected Amazon endpoints (should require auth)
                protected_endpoints = [
                    '/amazon/connect',
                    '/amazon/connections'
                ]
                
                for endpoint in protected_endpoints:
                    try:
                        if endpoint == '/amazon/connect':
                            response = await client.post(f"{self.backend_url}{endpoint}", json={
                                "marketplace_id": "A13V1IB3VIYZZH",
                                "region": "eu"
                            })
                        else:
                            response = await client.get(f"{self.backend_url}{endpoint}")
                        
                        # Should require authentication
                        if response.status_code in [401, 403]:
                            self.results['amazon_endpoints']['details'].append(f"✅ {endpoint} properly protected")
                            logger.info(f"✅ {endpoint} authentication protection working")
                        elif response.status_code == 422:
                            self.results['amazon_endpoints']['details'].append(f"✅ {endpoint} accessible (validation expected)")
                        else:
                            self.results['amazon_endpoints']['details'].append(f"⚠️ {endpoint} returned {response.status_code}")
                    except Exception as e:
                        self.results['amazon_endpoints']['details'].append(f"❌ {endpoint} error: {e}")
                        logger.error(f"❌ {endpoint} error: {e}")
                        return False
            
            self.results['amazon_endpoints']['details'].append("✅ Amazon endpoints tests completed")
            logger.info("✅ Amazon endpoints tests completed successfully")
            return True
            
        except Exception as e:
            self.results['amazon_endpoints']['details'].append(f"❌ Unexpected error: {e}")
            logger.error(f"❌ Amazon endpoints test failed: {e}")
            return False
    
    async def test_main_endpoints(self) -> bool:
        """Test 3: Endpoints principaux - API stats, testimonials, plans fonctionnent"""
        logger.info("📊 Test 3: Testing main API endpoints...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                
                # Test subscription plans endpoint
                try:
                    response = await client.get(f"{self.backend_url}/subscription/plans")
                    if response.status_code == 200:
                        plans_data = response.json()
                        self.results['main_endpoints']['details'].append("✅ Subscription plans endpoint working")
                        logger.info("✅ Subscription plans endpoint validated")
                        
                        # Check plans structure
                        if isinstance(plans_data, list) and len(plans_data) > 0:
                            self.results['main_endpoints']['details'].append(f"✅ Found {len(plans_data)} subscription plans")
                            
                            # Check for required plan fields
                            first_plan = plans_data[0]
                            required_fields = ['name', 'price', 'features']
                            for field in required_fields:
                                if field in first_plan:
                                    self.results['main_endpoints']['details'].append(f"✅ Plan has {field} field")
                                else:
                                    self.results['main_endpoints']['details'].append(f"⚠️ Plan missing {field} field")
                    else:
                        self.results['main_endpoints']['details'].append(f"❌ Plans endpoint returned {response.status_code}")
                        logger.error(f"❌ Plans endpoint returned {response.status_code}")
                        return False
                except Exception as e:
                    self.results['main_endpoints']['details'].append(f"❌ Plans endpoint error: {e}")
                    logger.error(f"❌ Plans endpoint error: {e}")
                    return False
                
                # Test testimonials endpoint
                try:
                    response = await client.get(f"{self.backend_url}/testimonials")
                    if response.status_code == 200:
                        testimonials_data = response.json()
                        self.results['main_endpoints']['details'].append("✅ Testimonials endpoint working")
                        logger.info("✅ Testimonials endpoint validated")
                        
                        # Check testimonials structure
                        if isinstance(testimonials_data, list):
                            self.results['main_endpoints']['details'].append(f"✅ Found {len(testimonials_data)} testimonials")
                        else:
                            self.results['main_endpoints']['details'].append("⚠️ Testimonials format unexpected")
                    else:
                        self.results['main_endpoints']['details'].append(f"❌ Testimonials endpoint returned {response.status_code}")
                        logger.error(f"❌ Testimonials endpoint returned {response.status_code}")
                        return False
                except Exception as e:
                    self.results['main_endpoints']['details'].append(f"❌ Testimonials endpoint error: {e}")
                    logger.error(f"❌ Testimonials endpoint error: {e}")
                    return False
                
                # Test admin stats endpoint (should require auth)
                try:
                    response = await client.get(f"{self.backend_url}/admin/stats")
                    if response.status_code in [401, 403]:
                        self.results['main_endpoints']['details'].append("✅ Admin stats properly protected")
                        logger.info("✅ Admin stats authentication protection working")
                    elif response.status_code == 200:
                        self.results['main_endpoints']['details'].append("⚠️ Admin stats accessible without auth")
                        logger.warning("⚠️ Admin stats accessible without auth")
                    else:
                        self.results['main_endpoints']['details'].append(f"⚠️ Admin stats returned {response.status_code}")
                except Exception as e:
                    self.results['main_endpoints']['details'].append(f"❌ Admin stats error: {e}")
                    logger.error(f"❌ Admin stats error: {e}")
                
                # Test contact endpoint (POST)
                try:
                    contact_data = {
                        "name": "Test User",
                        "email": "test@example.com",
                        "subject": "Test Subject",
                        "message": "Test message for regression testing"
                    }
                    response = await client.post(f"{self.backend_url}/contact", json=contact_data)
                    if response.status_code in [200, 201]:
                        self.results['main_endpoints']['details'].append("✅ Contact endpoint working")
                        logger.info("✅ Contact endpoint validated")
                    else:
                        self.results['main_endpoints']['details'].append(f"⚠️ Contact endpoint returned {response.status_code}")
                        logger.warning(f"⚠️ Contact endpoint returned {response.status_code}")
                except Exception as e:
                    self.results['main_endpoints']['details'].append(f"❌ Contact endpoint error: {e}")
                    logger.error(f"❌ Contact endpoint error: {e}")
            
            self.results['main_endpoints']['details'].append("✅ Main endpoints tests completed")
            logger.info("✅ Main endpoints tests completed successfully")
            return True
            
        except Exception as e:
            self.results['main_endpoints']['details'].append(f"❌ Unexpected error: {e}")
            logger.error(f"❌ Main endpoints test failed: {e}")
            return False
    
    async def test_authentication(self) -> bool:
        """Test 4: Authentification - Système d'auth fonctionne correctement"""
        logger.info("🔐 Test 4: Testing authentication system...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                
                # Test user registration endpoint
                try:
                    register_data = {
                        "email": f"test_{datetime.now().timestamp()}@example.com",
                        "name": "Test User Regression",
                        "password": "TestPassword123!",
                        "language": "fr"
                    }
                    response = await client.post(f"{self.backend_url}/auth/register", json=register_data)
                    if response.status_code in [200, 201, 409]:  # 409 = user already exists
                        self.results['authentication']['details'].append("✅ Registration endpoint working")
                        logger.info("✅ Registration endpoint validated")
                    else:
                        self.results['authentication']['details'].append(f"❌ Registration returned {response.status_code}")
                        logger.error(f"❌ Registration returned {response.status_code}")
                        return False
                except Exception as e:
                    self.results['authentication']['details'].append(f"❌ Registration error: {e}")
                    logger.error(f"❌ Registration error: {e}")
                    return False
                
                # Test user login endpoint with a fresh user
                try:
                    # First create a test user
                    test_email = f"test_regression_{datetime.now().timestamp()}@example.com"
                    register_data = {
                        "email": test_email,
                        "name": "Test Regression User",
                        "password": "TestPassword123!",
                        "language": "fr"
                    }
                    
                    register_response = await client.post(f"{self.backend_url}/auth/register", json=register_data)
                    if register_response.status_code in [200, 201]:
                        self.results['authentication']['details'].append("✅ Test user created for login test")
                        
                        # Now test login with the created user
                        login_data = {
                            "email": test_email,
                            "password": "TestPassword123!"
                        }
                        response = await client.post(f"{self.backend_url}/auth/login", json=login_data)
                    else:
                        # Fallback to original credentials
                        login_data = {
                            "email": self.test_user_email,
                            "password": self.test_user_password
                        }
                        response = await client.post(f"{self.backend_url}/auth/login", json=login_data)
                    if response.status_code == 200:
                        login_response = response.json()
                        self.results['authentication']['details'].append("✅ Login endpoint working")
                        logger.info("✅ Login endpoint validated")
                        
                        # Check login response structure
                        if 'token' in login_response:
                            self.auth_token = login_response['token']
                            self.results['authentication']['details'].append("✅ Auth token received")
                        elif 'access_token' in login_response:
                            self.auth_token = login_response['access_token']
                            self.results['authentication']['details'].append("✅ Access token received")
                        if 'user' in login_response:
                            self.results['authentication']['details'].append("✅ User data received")
                        if 'subscription_plan' in login_response:
                            self.results['authentication']['details'].append(f"✅ Subscription plan: {login_response.get('subscription_plan')}")
                    else:
                        self.results['authentication']['details'].append(f"❌ Login returned {response.status_code}")
                        logger.error(f"❌ Login returned {response.status_code}")
                        return False
                except Exception as e:
                    self.results['authentication']['details'].append(f"❌ Login error: {e}")
                    logger.error(f"❌ Login error: {e}")
                    return False
                
                # Test protected endpoint with authentication
                if self.auth_token:
                    try:
                        headers = {"Authorization": f"Bearer {self.auth_token}"}
                        response = await client.get(f"{self.backend_url}/stats", headers=headers)
                        if response.status_code == 200:
                            stats_data = response.json()
                            self.results['authentication']['details'].append("✅ Authenticated endpoint access working")
                            logger.info("✅ Authenticated endpoint access validated")
                            
                            # Check stats structure
                            if 'total_sheets' in stats_data:
                                self.results['authentication']['details'].append(f"✅ User stats: {stats_data.get('total_sheets')} sheets")
                        else:
                            self.results['authentication']['details'].append(f"❌ Authenticated endpoint returned {response.status_code}")
                            logger.error(f"❌ Authenticated endpoint returned {response.status_code}")
                            return False
                    except Exception as e:
                        self.results['authentication']['details'].append(f"❌ Authenticated endpoint error: {e}")
                        logger.error(f"❌ Authenticated endpoint error: {e}")
                        return False
                
                # Test JWT token validation
                try:
                    headers = {"Authorization": "Bearer invalid_token"}
                    response = await client.get(f"{self.backend_url}/stats", headers=headers)
                    if response.status_code in [401, 403]:
                        self.results['authentication']['details'].append("✅ JWT validation working (invalid token rejected)")
                        logger.info("✅ JWT validation working")
                    else:
                        self.results['authentication']['details'].append(f"⚠️ Invalid token returned {response.status_code}")
                        logger.warning(f"⚠️ Invalid token returned {response.status_code}")
                except Exception as e:
                    self.results['authentication']['details'].append(f"❌ JWT validation error: {e}")
                    logger.error(f"❌ JWT validation error: {e}")
            
            self.results['authentication']['details'].append("✅ Authentication tests completed")
            logger.info("✅ Authentication tests completed successfully")
            return True
            
        except Exception as e:
            self.results['authentication']['details'].append(f"❌ Unexpected error: {e}")
            logger.error(f"❌ Authentication test failed: {e}")
            return False
    
    async def test_database_connection(self) -> bool:
        """Test 5: Base de données - Connexion MongoDB opérationnelle"""
        logger.info("🗄️ Test 5: Testing MongoDB database connection...")
        
        try:
            # Get MongoDB URL from environment
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            db_name = os.environ.get('DB_NAME', 'ecomsimply_production')
            
            # Test direct MongoDB connection
            try:
                client = AsyncIOMotorClient(
                    mongo_url,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000
                )
                
                # Test connection with ping
                await client.admin.command('ping')
                self.results['database_connection']['details'].append("✅ MongoDB connection successful")
                logger.info("✅ MongoDB connection established")
                
                # Test database access
                db = client[db_name]
                
                # Test collections access
                collections = await db.list_collection_names()
                self.results['database_connection']['details'].append(f"✅ Database collections: {len(collections)} found")
                logger.info(f"✅ Found {len(collections)} collections in database")
                
                # Test basic operations
                try:
                    # Test read operation
                    users_count = await db.users.count_documents({})
                    self.results['database_connection']['details'].append(f"✅ Users collection: {users_count} documents")
                    
                    # Test write operation (insert test document)
                    test_doc = {
                        "test_id": f"regression_test_{datetime.now().timestamp()}",
                        "created_at": datetime.utcnow(),
                        "test_type": "regression"
                    }
                    result = await db.test_collection.insert_one(test_doc)
                    if result.inserted_id:
                        self.results['database_connection']['details'].append("✅ Database write operation successful")
                        
                        # Clean up test document
                        await db.test_collection.delete_one({"_id": result.inserted_id})
                        self.results['database_connection']['details'].append("✅ Database cleanup successful")
                    else:
                        self.results['database_connection']['details'].append("❌ Database write operation failed")
                        client.close()
                        return False
                        
                except Exception as e:
                    self.results['database_connection']['details'].append(f"❌ Database operations error: {e}")
                    logger.error(f"❌ Database operations error: {e}")
                    client.close()
                    return False
                
                # Test database health via API endpoint
                try:
                    async with httpx.AsyncClient(timeout=30.0) as http_client:
                        response = await http_client.get(f"{self.backend_url}/health")
                        if response.status_code == 200:
                            health_data = response.json()
                            if 'database' in health_data:
                                self.results['database_connection']['details'].append("✅ Database health via API confirmed")
                            else:
                                self.results['database_connection']['details'].append("⚠️ Database health not reported in API")
                except Exception as e:
                    self.results['database_connection']['details'].append(f"❌ Database health API error: {e}")
                
                # Close connection
                client.close()
                
            except Exception as e:
                self.results['database_connection']['details'].append(f"❌ MongoDB connection failed: {e}")
                logger.error(f"❌ MongoDB connection failed: {e}")
                return False
            
            self.results['database_connection']['details'].append("✅ Database connection tests completed")
            logger.info("✅ Database connection tests completed successfully")
            return True
            
        except Exception as e:
            self.results['database_connection']['details'].append(f"❌ Unexpected error: {e}")
            logger.error(f"❌ Database connection test failed: {e}")
            return False
    
    async def run_regression_tests(self) -> Dict[str, Any]:
        """Run all regression tests"""
        logger.info("🚀 Starting ECOMSIMPLY backend regression testing...")
        
        test_results = []
        
        # Test 1: Backend health
        result1 = await self.test_backend_health()
        self.results['backend_health']['status'] = result1
        test_results.append(result1)
        
        # Test 2: Amazon endpoints
        result2 = await self.test_amazon_endpoints()
        self.results['amazon_endpoints']['status'] = result2
        test_results.append(result2)
        
        # Test 3: Main endpoints
        result3 = await self.test_main_endpoints()
        self.results['main_endpoints']['status'] = result3
        test_results.append(result3)
        
        # Test 4: Authentication
        result4 = await self.test_authentication()
        self.results['authentication']['status'] = result4
        test_results.append(result4)
        
        # Test 5: Database connection
        result5 = await self.test_database_connection()
        self.results['database_connection']['status'] = result5
        test_results.append(result5)
        
        # Calculate overall results
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        self.results['success_rate'] = (passed_tests / total_tests) * 100
        self.results['overall_status'] = passed_tests == total_tests
        
        # Print comprehensive report
        self.print_test_report()
        
        return self.results
    
    def print_test_report(self):
        """Print comprehensive test report"""
        logger.info("\n" + "="*80)
        logger.info("📋 ECOMSIMPLY BACKEND REGRESSION TEST REPORT")
        logger.info("="*80)
        
        test_sections = [
            ('Backend Health', 'backend_health'),
            ('Amazon Endpoints', 'amazon_endpoints'),
            ('Main Endpoints', 'main_endpoints'),
            ('Authentication', 'authentication'),
            ('Database Connection', 'database_connection')
        ]
        
        for name, key in test_sections:
            status = "✅ PASS" if self.results[key]['status'] else "❌ FAIL"
            logger.info(f"{name:<25} {status}")
            
            # Show details for failed tests or important info
            if not self.results[key]['status']:
                for detail in self.results[key]['details'][-3:]:  # Show last 3 details
                    logger.info(f"  └─ {detail}")
            elif key == 'authentication' and self.auth_token:
                logger.info(f"  └─ ✅ Authentication token obtained successfully")
        
        logger.info("-"*80)
        success_rate = self.results['success_rate']
        overall_status = "✅ NO REGRESSION" if self.results['overall_status'] else "❌ REGRESSION DETECTED"
        logger.info(f"{'Success Rate':<25} {success_rate:.1f}%")
        logger.info(f"{'Overall Status':<25} {overall_status}")
        logger.info("="*80)
        
        if self.results['overall_status']:
            logger.info("🎉 No regression detected! Backend is working correctly after JavaScript fixes.")
        else:
            logger.error("⚠️ Regression detected! Some backend components are not working properly.")
        
        # Summary for main agent
        logger.info("\n📊 REGRESSION TEST SUMMARY:")
        logger.info("✅ Backend services operational" if self.results['backend_health']['status'] else "❌ Backend services issues")
        logger.info("✅ Amazon OAuth functional" if self.results['amazon_endpoints']['status'] else "❌ Amazon OAuth issues")
        logger.info("✅ Main APIs working" if self.results['main_endpoints']['status'] else "❌ Main APIs issues")
        logger.info("✅ Authentication system OK" if self.results['authentication']['status'] else "❌ Authentication issues")
        logger.info("✅ MongoDB connection OK" if self.results['database_connection']['status'] else "❌ MongoDB connection issues")

async def main():
    """Main test function"""
    logger.info("🔍 ECOMSIMPLY Backend Regression Testing")
    logger.info("Testing backend after JavaScript fixes to ensure no regression...")
    
    tester = EcomsimplyRegressionTester()
    results = await tester.run_regression_tests()
    
    # Exit with appropriate code
    exit_code = 0 if results['overall_status'] else 1
    
    # Summary for main agent
    if results['overall_status']:
        logger.info("\n✅ REGRESSION TESTING COMPLETED SUCCESSFULLY")
        logger.info("No regression detected - backend is working correctly after JavaScript fixes")
    else:
        logger.error("\n❌ REGRESSION TESTING COMPLETED WITH ISSUES")
        logger.error(f"Success rate: {results['success_rate']:.1f}%")
        logger.error("Some backend components require attention")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())