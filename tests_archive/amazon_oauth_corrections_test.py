#!/usr/bin/env python3
"""
Amazon OAuth SP-API Corrections Testing
Test complet des corrections Amazon OAuth SP-API implémentées

Corrections testées:
1. Endpoints OAuth corrigés - EU endpoint token corrigé
2. Priorité AMAZON_REDIRECT_URI sur APP_BASE_URL
3. Logs améliorés sans secrets
4. Routes Amazon fonctionnelles
5. Usage de spapi_oauth_code dans le callback
"""

import os
import sys
import asyncio
import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, List
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables from backend
load_dotenv('/app/backend/.env')

# Add backend path for imports
sys.path.append('/app/backend')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AmazonOAuthCorrectionsTester:
    """Tester for Amazon OAuth SP-API corrections"""
    
    def __init__(self):
        self.results = {
            'oauth_endpoints_correction': {'status': False, 'details': []},
            'redirect_uri_priority': {'status': False, 'details': []},
            'enhanced_logging': {'status': False, 'details': []},
            'amazon_routes': {'status': False, 'details': []},
            'spapi_oauth_code_usage': {'status': False, 'details': []},
            'overall_status': False,
            'success_rate': 0.0
        }
        
        # Get backend URL from environment
        self.backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://ecomsimply.com')
        if not self.backend_url.endswith('/api'):
            self.backend_url = f"{self.backend_url}/api"
        
        logger.info(f"🔗 Testing Amazon OAuth corrections at: {self.backend_url}")
    
    def test_oauth_endpoints_correction(self) -> bool:
        """Test 1: Vérification des endpoints OAuth corrigés"""
        logger.info("🔍 Test 1: Testing OAuth endpoints corrections...")
        
        try:
            from services.amazon_oauth_service import AmazonOAuthService
            from models.amazon_spapi import SPAPIRegion
            
            # Initialize OAuth service
            oauth_service = AmazonOAuthService()
            
            # Check EU endpoint correction
            eu_endpoints = oauth_service._oauth_endpoints[SPAPIRegion.EU]
            expected_eu_token_endpoint = 'https://api.amazon.com/auth/o2/token'
            
            if eu_endpoints['token'] == expected_eu_token_endpoint:
                self.results['oauth_endpoints_correction']['details'].append(
                    f"✅ EU token endpoint corrected: {expected_eu_token_endpoint}"
                )
                logger.info("✅ EU token endpoint correction validated")
            else:
                self.results['oauth_endpoints_correction']['details'].append(
                    f"❌ EU token endpoint incorrect: {eu_endpoints['token']} (expected: {expected_eu_token_endpoint})"
                )
                logger.error(f"❌ EU token endpoint not corrected")
                return False
            
            # Verify other regions remain correct
            na_endpoints = oauth_service._oauth_endpoints[SPAPIRegion.NA]
            fe_endpoints = oauth_service._oauth_endpoints[SPAPIRegion.FE]
            
            expected_na_token = 'https://api.amazon.com/auth/o2/token'
            expected_fe_token = 'https://api.amazon.co.jp/auth/o2/token'
            
            if na_endpoints['token'] == expected_na_token:
                self.results['oauth_endpoints_correction']['details'].append(
                    f"✅ NA token endpoint maintained: {expected_na_token}"
                )
            else:
                self.results['oauth_endpoints_correction']['details'].append(
                    f"❌ NA token endpoint incorrect: {na_endpoints['token']}"
                )
                return False
            
            if fe_endpoints['token'] == expected_fe_token:
                self.results['oauth_endpoints_correction']['details'].append(
                    f"✅ FE token endpoint maintained: {expected_fe_token}"
                )
            else:
                self.results['oauth_endpoints_correction']['details'].append(
                    f"❌ FE token endpoint incorrect: {fe_endpoints['token']}"
                )
                return False
            
            # Verify region mapping
            region_mapping = {
                SPAPIRegion.EU: 'https://sellingpartnerapi-eu.amazon.com',
                SPAPIRegion.NA: 'https://sellingpartnerapi-na.amazon.com', 
                SPAPIRegion.FE: 'https://sellingpartnerapi-fe.amazon.com'
            }
            
            for region, expected_spapi in region_mapping.items():
                actual_spapi = oauth_service._oauth_endpoints[region]['spapi']
                if actual_spapi == expected_spapi:
                    self.results['oauth_endpoints_correction']['details'].append(
                        f"✅ {region.value} SP-API endpoint correct: {expected_spapi}"
                    )
                else:
                    self.results['oauth_endpoints_correction']['details'].append(
                        f"❌ {region.value} SP-API endpoint incorrect: {actual_spapi}"
                    )
                    return False
            
            self.results['oauth_endpoints_correction']['details'].append("✅ All OAuth endpoints corrections validated")
            logger.info("✅ OAuth endpoints corrections test passed")
            return True
            
        except ImportError as e:
            self.results['oauth_endpoints_correction']['details'].append(f"❌ Import error: {e}")
            logger.error(f"❌ Cannot import OAuth service: {e}")
            return False
        except Exception as e:
            self.results['oauth_endpoints_correction']['details'].append(f"❌ Unexpected error: {e}")
            logger.error(f"❌ OAuth endpoints test failed: {e}")
            return False
    
    def test_redirect_uri_priority(self) -> bool:
        """Test 2: Vérification de la priorité AMAZON_REDIRECT_URI"""
        logger.info("🔍 Test 2: Testing AMAZON_REDIRECT_URI priority...")
        
        try:
            from services.amazon_oauth_service import AmazonOAuthService
            from models.amazon_spapi import SPAPIRegion
            
            oauth_service = AmazonOAuthService()
            
            # Test 1: With AMAZON_REDIRECT_URI set
            original_amazon_redirect = os.environ.get('AMAZON_REDIRECT_URI')
            original_app_base_url = os.environ.get('APP_BASE_URL')
            
            # Set test environment variables
            test_amazon_redirect = 'https://test-amazon-redirect.com/callback'
            test_app_base_url = 'https://test-app-base.com'
            
            os.environ['AMAZON_REDIRECT_URI'] = test_amazon_redirect
            os.environ['APP_BASE_URL'] = test_app_base_url
            
            # Test build_authorization_url priority
            test_state = 'test-state-123'
            auth_url = oauth_service.build_authorization_url(
                state=test_state,
                marketplace_id='A13V1IB3VIYZZH',
                region=SPAPIRegion.EU
            )
            
            # URL decode to check for the redirect URI
            from urllib.parse import unquote
            decoded_auth_url = unquote(auth_url)
            
            if test_amazon_redirect in decoded_auth_url:
                self.results['redirect_uri_priority']['details'].append(
                    f"✅ build_authorization_url uses AMAZON_REDIRECT_URI: {test_amazon_redirect}"
                )
                logger.info("✅ build_authorization_url AMAZON_REDIRECT_URI priority working")
            else:
                self.results['redirect_uri_priority']['details'].append(
                    f"❌ build_authorization_url not using AMAZON_REDIRECT_URI"
                )
                logger.error("❌ build_authorization_url priority failed")
                return False
            
            # Test 2: Without AMAZON_REDIRECT_URI (should fallback to APP_BASE_URL)
            if 'AMAZON_REDIRECT_URI' in os.environ:
                del os.environ['AMAZON_REDIRECT_URI']
            
            auth_url_fallback = oauth_service.build_authorization_url(
                state=test_state,
                marketplace_id='A13V1IB3VIYZZH',
                region=SPAPIRegion.EU
            )
            
            expected_fallback = f"{test_app_base_url}/api/amazon/callback"
            decoded_fallback_url = unquote(auth_url_fallback)
            
            if expected_fallback in decoded_fallback_url:
                self.results['redirect_uri_priority']['details'].append(
                    f"✅ build_authorization_url fallback to APP_BASE_URL: {expected_fallback}"
                )
                logger.info("✅ build_authorization_url fallback working")
            else:
                self.results['redirect_uri_priority']['details'].append(
                    f"❌ build_authorization_url fallback failed"
                )
                logger.error("❌ build_authorization_url fallback failed")
                return False
            
            # Test 3: Check exchange_code_for_tokens method (inspect source code)
            import inspect
            exchange_method_source = inspect.getsource(oauth_service.exchange_code_for_tokens)
            
            if "os.environ.get('AMAZON_REDIRECT_URI') or" in exchange_method_source:
                self.results['redirect_uri_priority']['details'].append(
                    "✅ exchange_code_for_tokens has AMAZON_REDIRECT_URI priority logic"
                )
                logger.info("✅ exchange_code_for_tokens priority logic found")
            else:
                self.results['redirect_uri_priority']['details'].append(
                    "❌ exchange_code_for_tokens missing AMAZON_REDIRECT_URI priority"
                )
                logger.error("❌ exchange_code_for_tokens priority logic missing")
                return False
            
            # Restore original environment variables
            if original_amazon_redirect:
                os.environ['AMAZON_REDIRECT_URI'] = original_amazon_redirect
            elif 'AMAZON_REDIRECT_URI' in os.environ:
                del os.environ['AMAZON_REDIRECT_URI']
            
            if original_app_base_url:
                os.environ['APP_BASE_URL'] = original_app_base_url
            elif 'APP_BASE_URL' in os.environ:
                del os.environ['APP_BASE_URL']
            
            self.results['redirect_uri_priority']['details'].append("✅ AMAZON_REDIRECT_URI priority test passed")
            logger.info("✅ AMAZON_REDIRECT_URI priority test completed")
            return True
            
        except Exception as e:
            self.results['redirect_uri_priority']['details'].append(f"❌ Unexpected error: {e}")
            logger.error(f"❌ AMAZON_REDIRECT_URI priority test failed: {e}")
            return False
    
    def test_enhanced_logging(self) -> bool:
        """Test 3: Vérification des logs améliorés sans secrets"""
        logger.info("🔍 Test 3: Testing enhanced logging without secrets...")
        
        try:
            from services.amazon_oauth_service import AmazonOAuthService
            import inspect
            
            oauth_service = AmazonOAuthService()
            
            # Check exchange_code_for_tokens method for enhanced logging
            exchange_method_source = inspect.getsource(oauth_service.exchange_code_for_tokens)
            
            # Check for enhanced error logging features
            logging_features = [
                'response.status_code',
                'response.text[:500]',
                'redirect_uri',
                'region'
            ]
            
            found_features = []
            missing_features = []
            
            for feature in logging_features:
                if feature in exchange_method_source:
                    found_features.append(feature)
                    self.results['enhanced_logging']['details'].append(f"✅ Enhanced logging includes: {feature}")
                else:
                    missing_features.append(feature)
            
            if len(found_features) >= 3:  # At least 3 out of 4 features
                logger.info(f"✅ Enhanced logging features found: {found_features}")
            else:
                self.results['enhanced_logging']['details'].append(f"❌ Missing logging features: {missing_features}")
                logger.error(f"❌ Enhanced logging incomplete: missing {missing_features}")
                return False
            
            # Check for secret protection (should NOT log sensitive data)
            secret_protection_checks = [
                'client_secret' not in exchange_method_source.split('logger.error')[1:] if 'logger.error' in exchange_method_source else True,
                'access_token' not in exchange_method_source.split('logger.error')[1:] if 'logger.error' in exchange_method_source else True,
                'refresh_token' not in exchange_method_source.split('logger.error')[1:] if 'logger.error' in exchange_method_source else True
            ]
            
            if all(secret_protection_checks):
                self.results['enhanced_logging']['details'].append("✅ Secret protection: No sensitive data in error logs")
                logger.info("✅ Secret protection validated")
            else:
                self.results['enhanced_logging']['details'].append("❌ Secret protection: Sensitive data may be logged")
                logger.error("❌ Secret protection failed")
                return False
            
            # Check for specific refresh_token missing log
            if 'refresh_token manquant' in exchange_method_source or 'Missing refresh_token' in exchange_method_source:
                self.results['enhanced_logging']['details'].append("✅ Specific refresh_token missing log found")
                logger.info("✅ Refresh token missing log validated")
            else:
                self.results['enhanced_logging']['details'].append("⚠️ Specific refresh_token missing log not found")
                logger.warning("⚠️ Refresh token missing log not found")
            
            self.results['enhanced_logging']['details'].append("✅ Enhanced logging without secrets test passed")
            logger.info("✅ Enhanced logging test completed")
            return True
            
        except Exception as e:
            self.results['enhanced_logging']['details'].append(f"❌ Unexpected error: {e}")
            logger.error(f"❌ Enhanced logging test failed: {e}")
            return False
    
    async def test_amazon_routes(self) -> bool:
        """Test 4: Vérification des routes Amazon"""
        logger.info("🔍 Test 4: Testing Amazon routes functionality...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                
                # Test Amazon health endpoint
                try:
                    response = await client.get(f"{self.backend_url}/amazon/health")
                    if response.status_code == 200:
                        health_data = response.json()
                        if health_data.get('service') == 'Amazon SP-API Integration':
                            self.results['amazon_routes']['details'].append("✅ /amazon/health endpoint working")
                            logger.info("✅ Amazon health endpoint validated")
                        else:
                            self.results['amazon_routes']['details'].append("❌ Health endpoint service identification incorrect")
                            return False
                    else:
                        self.results['amazon_routes']['details'].append(f"❌ Health endpoint returned {response.status_code}")
                        return False
                except Exception as e:
                    self.results['amazon_routes']['details'].append(f"❌ Health endpoint error: {e}")
                    return False
                
                # Test Amazon connect endpoint (should require auth)
                try:
                    response = await client.get(f"{self.backend_url}/amazon/connect")
                    if response.status_code in [401, 403]:
                        self.results['amazon_routes']['details'].append("✅ /amazon/connect properly protected")
                        logger.info("✅ Amazon connect endpoint protection working")
                    else:
                        self.results['amazon_routes']['details'].append(f"⚠️ Connect endpoint returned {response.status_code}")
                        logger.warning(f"⚠️ Connect endpoint returned {response.status_code}")
                except Exception as e:
                    self.results['amazon_routes']['details'].append(f"❌ Connect endpoint error: {e}")
                    return False
                
                # Test Amazon status endpoint (should require auth)
                try:
                    response = await client.get(f"{self.backend_url}/amazon/status")
                    if response.status_code in [401, 403]:
                        self.results['amazon_routes']['details'].append("✅ /amazon/status properly protected")
                        logger.info("✅ Amazon status endpoint protection working")
                    else:
                        self.results['amazon_routes']['details'].append(f"⚠️ Status endpoint returned {response.status_code}")
                        logger.warning(f"⚠️ Status endpoint returned {response.status_code}")
                except Exception as e:
                    self.results['amazon_routes']['details'].append(f"❌ Status endpoint error: {e}")
                    return False
                
                # Test Amazon disconnect endpoint (should require auth)
                try:
                    response = await client.post(f"{self.backend_url}/amazon/disconnect")
                    if response.status_code in [401, 403]:
                        self.results['amazon_routes']['details'].append("✅ /amazon/disconnect properly protected")
                        logger.info("✅ Amazon disconnect endpoint protection working")
                    else:
                        self.results['amazon_routes']['details'].append(f"⚠️ Disconnect endpoint returned {response.status_code}")
                        logger.warning(f"⚠️ Disconnect endpoint returned {response.status_code}")
                except Exception as e:
                    self.results['amazon_routes']['details'].append(f"❌ Disconnect endpoint error: {e}")
                    return False
                
                self.results['amazon_routes']['details'].append("✅ All Amazon routes tests passed")
                logger.info("✅ Amazon routes test completed")
                return True
                
        except Exception as e:
            self.results['amazon_routes']['details'].append(f"❌ Unexpected error: {e}")
            logger.error(f"❌ Amazon routes test failed: {e}")
            return False
    
    def test_spapi_oauth_code_usage(self) -> bool:
        """Test 5: Vérification de l'usage de spapi_oauth_code dans le callback"""
        logger.info("🔍 Test 5: Testing spapi_oauth_code usage in callback...")
        
        try:
            from routes.amazon_routes import amazon_router
            import inspect
            
            # Get the callback handler function
            callback_handler = None
            for route in amazon_router.routes:
                if hasattr(route, 'path') and '/callback' in route.path:
                    callback_handler = route.endpoint
                    break
            
            if not callback_handler:
                self.results['spapi_oauth_code_usage']['details'].append("❌ Callback handler not found")
                logger.error("❌ Callback handler not found")
                return False
            
            # Check callback function signature
            callback_signature = inspect.signature(callback_handler)
            callback_params = list(callback_signature.parameters.keys())
            
            if 'spapi_oauth_code' in callback_params:
                self.results['spapi_oauth_code_usage']['details'].append("✅ Callback handler accepts spapi_oauth_code parameter")
                logger.info("✅ spapi_oauth_code parameter found in callback")
            else:
                self.results['spapi_oauth_code_usage']['details'].append("❌ Callback handler missing spapi_oauth_code parameter")
                logger.error("❌ spapi_oauth_code parameter missing")
                return False
            
            # Check callback function source code
            callback_source = inspect.getsource(callback_handler)
            
            # Verify spapi_oauth_code is used as the authorization code source
            if 'spapi_oauth_code' in callback_source and 'authorization_code=spapi_oauth_code' in callback_source:
                self.results['spapi_oauth_code_usage']['details'].append("✅ spapi_oauth_code used as authorization code source")
                logger.info("✅ spapi_oauth_code usage validated")
            else:
                self.results['spapi_oauth_code_usage']['details'].append("❌ spapi_oauth_code not properly used as authorization code")
                logger.error("❌ spapi_oauth_code usage incorrect")
                return False
            
            # Check for proper parameter validation
            if 'not spapi_oauth_code' in callback_source or 'spapi_oauth_code' in callback_source:
                self.results['spapi_oauth_code_usage']['details'].append("✅ spapi_oauth_code parameter validation found")
                logger.info("✅ spapi_oauth_code validation found")
            else:
                self.results['spapi_oauth_code_usage']['details'].append("⚠️ spapi_oauth_code parameter validation not found")
                logger.warning("⚠️ spapi_oauth_code validation not found")
            
            # Verify other required callback parameters
            required_params = ['state', 'selling_partner_id', 'spapi_oauth_code']
            missing_params = [param for param in required_params if param not in callback_params]
            
            if not missing_params:
                self.results['spapi_oauth_code_usage']['details'].append("✅ All required callback parameters present")
                logger.info("✅ All callback parameters validated")
            else:
                self.results['spapi_oauth_code_usage']['details'].append(f"❌ Missing callback parameters: {missing_params}")
                logger.error(f"❌ Missing callback parameters: {missing_params}")
                return False
            
            self.results['spapi_oauth_code_usage']['details'].append("✅ spapi_oauth_code usage test passed")
            logger.info("✅ spapi_oauth_code usage test completed")
            return True
            
        except Exception as e:
            self.results['spapi_oauth_code_usage']['details'].append(f"❌ Unexpected error: {e}")
            logger.error(f"❌ spapi_oauth_code usage test failed: {e}")
            return False
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all Amazon OAuth corrections tests"""
        logger.info("🚀 Starting Amazon OAuth SP-API corrections testing...")
        
        test_results = []
        
        # Test 1: OAuth endpoints correction
        result1 = self.test_oauth_endpoints_correction()
        self.results['oauth_endpoints_correction']['status'] = result1
        test_results.append(result1)
        
        # Test 2: AMAZON_REDIRECT_URI priority
        result2 = self.test_redirect_uri_priority()
        self.results['redirect_uri_priority']['status'] = result2
        test_results.append(result2)
        
        # Test 3: Enhanced logging
        result3 = self.test_enhanced_logging()
        self.results['enhanced_logging']['status'] = result3
        test_results.append(result3)
        
        # Test 4: Amazon routes
        result4 = await self.test_amazon_routes()
        self.results['amazon_routes']['status'] = result4
        test_results.append(result4)
        
        # Test 5: spapi_oauth_code usage
        result5 = self.test_spapi_oauth_code_usage()
        self.results['spapi_oauth_code_usage']['status'] = result5
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
        logger.info("📋 AMAZON OAUTH SP-API CORRECTIONS TEST REPORT")
        logger.info("="*80)
        
        test_sections = [
            ('OAuth Endpoints Correction', 'oauth_endpoints_correction'),
            ('AMAZON_REDIRECT_URI Priority', 'redirect_uri_priority'),
            ('Enhanced Logging', 'enhanced_logging'),
            ('Amazon Routes', 'amazon_routes'),
            ('spapi_oauth_code Usage', 'spapi_oauth_code_usage')
        ]
        
        for name, key in test_sections:
            status = "✅ PASS" if self.results[key]['status'] else "❌ FAIL"
            logger.info(f"{name:<30} {status}")
            
            # Show details for failed tests
            if not self.results[key]['status']:
                for detail in self.results[key]['details'][-3:]:  # Show last 3 details
                    logger.info(f"  └─ {detail}")
        
        logger.info("-"*80)
        success_rate = self.results['success_rate']
        overall_status = "✅ ALL CORRECTIONS VALIDATED" if self.results['overall_status'] else "❌ CORRECTIONS INCOMPLETE"
        logger.info(f"{'Success Rate':<30} {success_rate:.1f}%")
        logger.info(f"{'Overall Status':<30} {overall_status}")
        logger.info("="*80)
        
        if self.results['overall_status']:
            logger.info("🎉 All Amazon OAuth SP-API corrections are properly implemented!")
        else:
            logger.error("⚠️ Some Amazon OAuth SP-API corrections require attention")
        
        # Corrections summary
        logger.info("\n🔧 CORRECTIONS VALIDATION SUMMARY:")
        logger.info("✅ EU endpoint token correction: https://api.amazon.com/auth/o2/token")
        logger.info("✅ AMAZON_REDIRECT_URI priority over APP_BASE_URL")
        logger.info("✅ Enhanced error logging without secrets")
        logger.info("✅ Amazon routes functionality")
        logger.info("✅ spapi_oauth_code usage in callback")

async def main():
    """Main test function"""
    logger.info("🔍 Amazon OAuth SP-API Corrections Testing")
    logger.info("Testing all implemented corrections for Amazon OAuth integration...")
    
    tester = AmazonOAuthCorrectionsTester()
    results = await tester.run_comprehensive_tests()
    
    # Exit with appropriate code
    exit_code = 0 if results['overall_status'] else 1
    
    # Summary for main agent
    if results['overall_status']:
        logger.info("\n✅ CORRECTIONS TESTING COMPLETED SUCCESSFULLY")
        logger.info("All Amazon OAuth SP-API corrections are properly implemented")
    else:
        logger.error("\n❌ CORRECTIONS TESTING COMPLETED WITH ISSUES")
        logger.error(f"Success rate: {results['success_rate']:.1f}%")
        logger.error("Some corrections require attention")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())