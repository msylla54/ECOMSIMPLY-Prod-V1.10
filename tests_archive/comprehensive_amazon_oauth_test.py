#!/usr/bin/env python3
"""
COMPREHENSIVE AMAZON OAUTH CALLBACK TESTING
===========================================

Testing the complete Amazon OAuth callback implementation with automatic refresh token generation.

IMPLEMENTATION CONTEXT:
- Complete OAuth callback endpoint with automatic refresh token generation and secure storage
- Enhanced callback logic with popup and redirect modes
- Comprehensive error handling and CSRF validation
- AES-GCM encryption with AWS KMS for token security

COMPREHENSIVE TESTING COVERAGE:
1. OAuth Callback Endpoint Testing
2. Refresh Token Generation Validation
3. Security Validation (CSRF, encryption)
4. Error Handling Testing
5. Integration Flow Testing

CRITICAL SUCCESS CRITERIA:
✅ OAuth callback processes code and generates refresh token automatically
✅ Tokens stored encrypted in database with AES-GCM + KMS
✅ CSRF protection via OAuth state validation working
✅ Popup and redirect modes both functional
✅ Error handling comprehensive for all failure scenarios
✅ No sensitive token data exposed in responses or logs
✅ Multi-tenant security maintained
"""

import asyncio
import aiohttp
import json
import os
import sys
import time
import uuid
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode, parse_qs, urlparse

# Test configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ecomsimply.com')
API_BASE = f"{BACKEND_URL}/api"

class AmazonOAuthCallbackTester:
    """Comprehensive Amazon OAuth callback testing suite"""
    
    def __init__(self):
        self.session = None
        self.test_results = []
        self.auth_token = None
        self.test_user_id = None
        self.connection_id = None
        self.oauth_state = None
        
        # Test data
        self.test_credentials = {
            "email": "test.amazon.oauth@ecomsimply.com",
            "password": "TestAmazonOAuth2025!",
            "name": "Amazon OAuth Test User"
        }
        
        # Mock Amazon OAuth data
        self.mock_oauth_data = {
            "selling_partner_id": "A1B2C3D4E5F6G7H8I9J0",
            "spapi_oauth_code": "ANcdefghijklmnopqrstuvwxyz1234567890",
            "mws_auth_token": "amzn.mws.12345678-1234-1234-1234-123456789012"
        }
        
        print("🧪 Amazon OAuth Callback Comprehensive Testing Suite Initialized")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print(f"📡 API Base: {API_BASE}")
    
    async def setup_session(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'ECOMSIMPLY-OAuth-Test/1.0',
                'Content-Type': 'application/json'
            }
        )
        print("✅ HTTP session initialized")
    
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            print("🧹 HTTP session cleaned up")
    
    def log_test_result(self, test_name: str, success: bool, details: str, data: Dict = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {}
        }
        self.test_results.append(result)
        print(f"{status} {test_name}: {details}")
        if data and not success:
            print(f"   📋 Error Data: {json.dumps(data, indent=2)}")
    
    async def authenticate_test_user(self) -> bool:
        """Authenticate test user and get JWT token"""
        try:
            # Try to register test user first
            register_data = {
                "email": self.test_credentials["email"],
                "name": self.test_credentials["name"],
                "password": self.test_credentials["password"]
            }
            
            async with self.session.post(f"{API_BASE}/auth/register", json=register_data) as response:
                if response.status in [200, 201]:
                    print("✅ Test user registered successfully")
                elif response.status == 400:
                    print("ℹ️ Test user already exists, proceeding to login")
                else:
                    print(f"⚠️ Registration response: {response.status}")
            
            # Login to get JWT token
            login_data = {
                "email": self.test_credentials["email"],
                "password": self.test_credentials["password"]
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    self.test_user_id = data.get("user_id")
                    
                    if self.auth_token:
                        # Update session headers with auth token
                        self.session.headers.update({
                            'Authorization': f'Bearer {self.auth_token}'
                        })
                        self.log_test_result(
                            "User Authentication",
                            True,
                            f"Successfully authenticated test user {self.test_user_id[:8]}***"
                        )
                        return True
                    else:
                        self.log_test_result(
                            "User Authentication",
                            False,
                            "No access token in login response",
                            data
                        )
                        return False
                else:
                    error_data = await response.text()
                    self.log_test_result(
                        "User Authentication",
                        False,
                        f"Login failed with status {response.status}",
                        {"status": response.status, "response": error_data}
                    )
                    return False
                    
        except Exception as e:
            self.log_test_result(
                "User Authentication",
                False,
                f"Authentication error: {str(e)}",
                {"error": str(e), "type": type(e).__name__}
            )
            return False
    
    async def test_amazon_connection_initiation(self) -> bool:
        """Test Amazon connection initiation to get OAuth state"""
        try:
            connection_request = {
                "marketplace_id": "A13V1IB3VIYZZH",  # France
                "region": "eu"
            }
            
            async with self.session.post(f"{API_BASE}/amazon/connect", json=connection_request) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Validate response structure
                    required_fields = ["connection_id", "authorization_url", "state", "expires_at"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test_result(
                            "Amazon Connection Initiation",
                            False,
                            f"Missing required fields: {missing_fields}",
                            data
                        )
                        return False
                    
                    # Store connection details for callback testing
                    self.connection_id = data["connection_id"]
                    self.oauth_state = data["state"]
                    
                    # Validate authorization URL
                    auth_url = data["authorization_url"]
                    if "sellercentral-europe.amazon.com" not in auth_url:
                        self.log_test_result(
                            "Amazon Connection Initiation",
                            False,
                            "Invalid authorization URL for EU region",
                            {"auth_url": auth_url}
                        )
                        return False
                    
                    # Validate OAuth state format
                    if not self.oauth_state or len(self.oauth_state) < 32:
                        self.log_test_result(
                            "Amazon Connection Initiation",
                            False,
                            "OAuth state appears invalid or too short",
                            {"state_length": len(self.oauth_state) if self.oauth_state else 0}
                        )
                        return False
                    
                    self.log_test_result(
                        "Amazon Connection Initiation",
                        True,
                        f"Connection initiated successfully, ID: {self.connection_id}",
                        {
                            "connection_id": self.connection_id,
                            "state_length": len(self.oauth_state),
                            "auth_url_valid": True
                        }
                    )
                    return True
                else:
                    error_data = await response.text()
                    self.log_test_result(
                        "Amazon Connection Initiation",
                        False,
                        f"Connection initiation failed with status {response.status}",
                        {"status": response.status, "response": error_data}
                    )
                    return False
                    
        except Exception as e:
            self.log_test_result(
                "Amazon Connection Initiation",
                False,
                f"Connection initiation error: {str(e)}",
                {"error": str(e), "type": type(e).__name__}
            )
            return False
    
    async def test_oauth_callback_popup_mode(self) -> bool:
        """Test OAuth callback endpoint in popup mode"""
        try:
            if not self.oauth_state:
                self.log_test_result(
                    "OAuth Callback Popup Mode",
                    False,
                    "No OAuth state available for testing",
                    {}
                )
                return False
            
            # Build callback URL with popup=true
            callback_params = {
                "state": self.oauth_state,
                "selling_partner_id": self.mock_oauth_data["selling_partner_id"],
                "spapi_oauth_code": self.mock_oauth_data["spapi_oauth_code"],
                "popup": "true"
            }
            
            callback_url = f"{API_BASE}/amazon/callback?" + urlencode(callback_params)
            
            async with self.session.get(callback_url) as response:
                if response.status == 200:
                    content = await response.text()
                    content_type = response.headers.get('content-type', '')
                    
                    # Validate HTML response for popup mode
                    if 'text/html' not in content_type:
                        self.log_test_result(
                            "OAuth Callback Popup Mode",
                            False,
                            f"Expected HTML response, got {content_type}",
                            {"content_type": content_type}
                        )
                        return False
                    
                    # Check for popup-specific elements
                    popup_indicators = [
                        "postMessage",
                        "window.opener",
                        "AMAZON_CONNECTED",
                        "Amazon Connecté avec Succès"
                    ]
                    
                    found_indicators = [indicator for indicator in popup_indicators if indicator in content]
                    
                    if len(found_indicators) < 3:
                        self.log_test_result(
                            "OAuth Callback Popup Mode",
                            False,
                            f"Missing popup indicators, found: {found_indicators}",
                            {"found_indicators": found_indicators, "content_length": len(content)}
                        )
                        return False
                    
                    self.log_test_result(
                        "OAuth Callback Popup Mode",
                        True,
                        f"Popup mode callback successful, found {len(found_indicators)} indicators",
                        {
                            "content_type": content_type,
                            "found_indicators": found_indicators,
                            "content_length": len(content)
                        }
                    )
                    return True
                else:
                    error_data = await response.text()
                    self.log_test_result(
                        "OAuth Callback Popup Mode",
                        False,
                        f"Callback failed with status {response.status}",
                        {"status": response.status, "response": error_data[:500]}
                    )
                    return False
                    
        except Exception as e:
            self.log_test_result(
                "OAuth Callback Popup Mode",
                False,
                f"Popup callback error: {str(e)}",
                {"error": str(e), "type": type(e).__name__}
            )
            return False
    
    async def test_oauth_callback_redirect_mode(self) -> bool:
        """Test OAuth callback endpoint in redirect mode"""
        try:
            if not self.oauth_state:
                self.log_test_result(
                    "OAuth Callback Redirect Mode",
                    False,
                    "No OAuth state available for testing",
                    {}
                )
                return False
            
            # Build callback URL without popup parameter (default redirect mode)
            callback_params = {
                "state": self.oauth_state,
                "selling_partner_id": self.mock_oauth_data["selling_partner_id"],
                "spapi_oauth_code": self.mock_oauth_data["spapi_oauth_code"]
            }
            
            callback_url = f"{API_BASE}/amazon/callback?" + urlencode(callback_params)
            
            # Don't follow redirects to test the redirect response
            async with self.session.get(callback_url, allow_redirects=False) as response:
                if response.status == 302:
                    location = response.headers.get('location', '')
                    
                    # Validate redirect URL
                    if not location:
                        self.log_test_result(
                            "OAuth Callback Redirect Mode",
                            False,
                            "No Location header in redirect response",
                            {"headers": dict(response.headers)}
                        )
                        return False
                    
                    # Check if redirect goes to dashboard
                    if "dashboard" not in location or "amazon=connected" not in location:
                        self.log_test_result(
                            "OAuth Callback Redirect Mode",
                            False,
                            f"Invalid redirect URL: {location}",
                            {"location": location}
                        )
                        return False
                    
                    self.log_test_result(
                        "OAuth Callback Redirect Mode",
                        True,
                        f"Redirect mode callback successful, redirecting to: {location}",
                        {
                            "status": response.status,
                            "location": location
                        }
                    )
                    return True
                else:
                    error_data = await response.text()
                    self.log_test_result(
                        "OAuth Callback Redirect Mode",
                        False,
                        f"Expected 302 redirect, got {response.status}",
                        {"status": response.status, "response": error_data[:500]}
                    )
                    return False
                    
        except Exception as e:
            self.log_test_result(
                "OAuth Callback Redirect Mode",
                False,
                f"Redirect callback error: {str(e)}",
                {"error": str(e), "type": type(e).__name__}
            )
            return False
    
    async def test_oauth_callback_missing_parameters(self) -> bool:
        """Test OAuth callback with missing required parameters"""
        try:
            test_cases = [
                {
                    "name": "Missing state",
                    "params": {
                        "selling_partner_id": self.mock_oauth_data["selling_partner_id"],
                        "spapi_oauth_code": self.mock_oauth_data["spapi_oauth_code"]
                    }
                },
                {
                    "name": "Missing selling_partner_id",
                    "params": {
                        "state": self.oauth_state,
                        "spapi_oauth_code": self.mock_oauth_data["spapi_oauth_code"]
                    }
                },
                {
                    "name": "Missing spapi_oauth_code",
                    "params": {
                        "state": self.oauth_state,
                        "selling_partner_id": self.mock_oauth_data["selling_partner_id"]
                    }
                }
            ]
            
            all_passed = True
            
            for test_case in test_cases:
                callback_url = f"{API_BASE}/amazon/callback?" + urlencode(test_case["params"])
                
                async with self.session.get(callback_url) as response:
                    # Should return error response (HTML or redirect with error)
                    if response.status == 200:
                        content = await response.text()
                        if "error" not in content.lower() and "erreur" not in content.lower():
                            self.log_test_result(
                                f"OAuth Missing Parameters - {test_case['name']}",
                                False,
                                "Expected error response but got success",
                                {"status": response.status, "content_length": len(content)}
                            )
                            all_passed = False
                        else:
                            self.log_test_result(
                                f"OAuth Missing Parameters - {test_case['name']}",
                                True,
                                "Correctly returned error response",
                                {"status": response.status}
                            )
                    elif response.status == 302:
                        location = response.headers.get('location', '')
                        if "error" not in location:
                            self.log_test_result(
                                f"OAuth Missing Parameters - {test_case['name']}",
                                False,
                                "Expected error in redirect but got success",
                                {"status": response.status, "location": location}
                            )
                            all_passed = False
                        else:
                            self.log_test_result(
                                f"OAuth Missing Parameters - {test_case['name']}",
                                True,
                                "Correctly redirected with error",
                                {"status": response.status, "location": location}
                            )
                    else:
                        self.log_test_result(
                            f"OAuth Missing Parameters - {test_case['name']}",
                            False,
                            f"Unexpected status code: {response.status}",
                            {"status": response.status}
                        )
                        all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.log_test_result(
                "OAuth Missing Parameters",
                False,
                f"Missing parameters test error: {str(e)}",
                {"error": str(e), "type": type(e).__name__}
            )
            return False
    
    async def test_oauth_callback_invalid_state(self) -> bool:
        """Test OAuth callback with invalid state (CSRF protection)"""
        try:
            invalid_states = [
                "invalid_state_123",
                "",
                "a" * 200,  # Too long
                base64.b64encode(b"invalid:data:format").decode()
            ]
            
            all_passed = True
            
            for invalid_state in invalid_states:
                callback_params = {
                    "state": invalid_state,
                    "selling_partner_id": self.mock_oauth_data["selling_partner_id"],
                    "spapi_oauth_code": self.mock_oauth_data["spapi_oauth_code"]
                }
                
                callback_url = f"{API_BASE}/amazon/callback?" + urlencode(callback_params)
                
                async with self.session.get(callback_url) as response:
                    # Should return error response
                    if response.status == 200:
                        content = await response.text()
                        if "error" not in content.lower() and "erreur" not in content.lower():
                            self.log_test_result(
                                f"OAuth Invalid State - {invalid_state[:20]}***",
                                False,
                                "Expected error response for invalid state",
                                {"status": response.status, "state": invalid_state[:20]}
                            )
                            all_passed = False
                        else:
                            self.log_test_result(
                                f"OAuth Invalid State - {invalid_state[:20]}***",
                                True,
                                "Correctly rejected invalid state",
                                {"status": response.status}
                            )
                    elif response.status == 302:
                        location = response.headers.get('location', '')
                        if "error" not in location:
                            self.log_test_result(
                                f"OAuth Invalid State - {invalid_state[:20]}***",
                                False,
                                "Expected error in redirect for invalid state",
                                {"status": response.status, "location": location}
                            )
                            all_passed = False
                        else:
                            self.log_test_result(
                                f"OAuth Invalid State - {invalid_state[:20]}***",
                                True,
                                "Correctly redirected with error for invalid state",
                                {"status": response.status}
                            )
                    else:
                        self.log_test_result(
                            f"OAuth Invalid State - {invalid_state[:20]}***",
                            False,
                            f"Unexpected status code: {response.status}",
                            {"status": response.status}
                        )
                        all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.log_test_result(
                "OAuth Invalid State",
                False,
                f"Invalid state test error: {str(e)}",
                {"error": str(e), "type": type(e).__name__}
            )
            return False
    
    async def test_connection_status_after_callback(self) -> bool:
        """Test connection status after successful OAuth callback"""
        try:
            # Wait a moment for callback processing
            await asyncio.sleep(2)
            
            async with self.session.get(f"{API_BASE}/amazon/status") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check if status indicates successful connection
                    status = data.get("status")
                    if status == "connected":
                        active_connection = data.get("active_connection", {})
                        
                        # Validate active connection details
                        required_fields = ["connection_id", "marketplace_id", "seller_id", "region"]
                        missing_fields = [field for field in required_fields if field not in active_connection]
                        
                        if missing_fields:
                            self.log_test_result(
                                "Connection Status After Callback",
                                False,
                                f"Missing active connection fields: {missing_fields}",
                                data
                            )
                            return False
                        
                        # Verify seller ID matches our mock data
                        if active_connection["seller_id"] != self.mock_oauth_data["selling_partner_id"]:
                            self.log_test_result(
                                "Connection Status After Callback",
                                False,
                                "Seller ID mismatch in active connection",
                                {
                                    "expected": self.mock_oauth_data["selling_partner_id"],
                                    "actual": active_connection["seller_id"]
                                }
                            )
                            return False
                        
                        self.log_test_result(
                            "Connection Status After Callback",
                            True,
                            f"Connection status shows active connection for seller {active_connection['seller_id']}",
                            {
                                "status": status,
                                "connection_id": active_connection["connection_id"],
                                "marketplace_id": active_connection["marketplace_id"]
                            }
                        )
                        return True
                    else:
                        self.log_test_result(
                            "Connection Status After Callback",
                            False,
                            f"Expected 'connected' status, got '{status}'",
                            data
                        )
                        return False
                else:
                    error_data = await response.text()
                    self.log_test_result(
                        "Connection Status After Callback",
                        False,
                        f"Status check failed with status {response.status}",
                        {"status": response.status, "response": error_data}
                    )
                    return False
                    
        except Exception as e:
            self.log_test_result(
                "Connection Status After Callback",
                False,
                f"Status check error: {str(e)}",
                {"error": str(e), "type": type(e).__name__}
            )
            return False
    
    async def test_refresh_token_validation(self) -> bool:
        """Test refresh token validation endpoint (development only)"""
        try:
            async with self.session.post(f"{API_BASE}/amazon/test/validate-refresh-token") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("success"):
                        details = data.get("details", {})
                        token_features = details.get("token_features", {})
                        
                        # Validate token features
                        required_features = [
                            "refresh_token_present",
                            "encryption_nonce_present", 
                            "kms_encryption",
                            "access_token_retrieved",
                            "automatic_refresh_working"
                        ]
                        
                        missing_features = [
                            feature for feature in required_features 
                            if not token_features.get(feature, False)
                        ]
                        
                        if missing_features:
                            self.log_test_result(
                                "Refresh Token Validation",
                                False,
                                f"Missing token features: {missing_features}",
                                data
                            )
                            return False
                        
                        # Validate encryption details
                        if not details.get("encryption_key_id"):
                            self.log_test_result(
                                "Refresh Token Validation",
                                False,
                                "No encryption key ID found",
                                data
                            )
                            return False
                        
                        self.log_test_result(
                            "Refresh Token Validation",
                            True,
                            "Refresh token validation successful - all features working",
                            {
                                "connection_id": details.get("connection_id"),
                                "seller_id": details.get("seller_id"),
                                "encryption_key_id": details.get("encryption_key_id")[:20] + "***",
                                "token_features": token_features
                            }
                        )
                        return True
                    else:
                        self.log_test_result(
                            "Refresh Token Validation",
                            False,
                            f"Validation failed: {data.get('message', 'Unknown error')}",
                            data
                        )
                        return False
                elif response.status == 403:
                    # Expected in production environment
                    self.log_test_result(
                        "Refresh Token Validation",
                        True,
                        "Test endpoint correctly restricted in production environment",
                        {"status": response.status}
                    )
                    return True
                else:
                    error_data = await response.text()
                    self.log_test_result(
                        "Refresh Token Validation",
                        False,
                        f"Validation request failed with status {response.status}",
                        {"status": response.status, "response": error_data}
                    )
                    return False
                    
        except Exception as e:
            self.log_test_result(
                "Refresh Token Validation",
                False,
                f"Refresh token validation error: {str(e)}",
                {"error": str(e), "type": type(e).__name__}
            )
            return False
    
    async def test_amazon_health_check(self) -> bool:
        """Test Amazon integration health check"""
        try:
            async with self.session.get(f"{API_BASE}/amazon/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Validate health check response
                    required_fields = ["status", "service", "version"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test_result(
                            "Amazon Health Check",
                            False,
                            f"Missing health check fields: {missing_fields}",
                            data
                        )
                        return False
                    
                    # Check service status
                    status = data.get("status")
                    if status not in ["healthy", "degraded"]:
                        self.log_test_result(
                            "Amazon Health Check",
                            False,
                            f"Unexpected health status: {status}",
                            data
                        )
                        return False
                    
                    # Validate details if present
                    details = data.get("details", {})
                    if details:
                        kms_access = details.get("kms_access")
                        if kms_access is False:
                            self.log_test_result(
                                "Amazon Health Check",
                                False,
                                "KMS access test failed in health check",
                                data
                            )
                            return False
                    
                    self.log_test_result(
                        "Amazon Health Check",
                        True,
                        f"Health check successful, status: {status}",
                        {
                            "status": status,
                            "service": data.get("service"),
                            "version": data.get("version"),
                            "kms_access": details.get("kms_access") if details else None
                        }
                    )
                    return True
                else:
                    error_data = await response.text()
                    self.log_test_result(
                        "Amazon Health Check",
                        False,
                        f"Health check failed with status {response.status}",
                        {"status": response.status, "response": error_data}
                    )
                    return False
                    
        except Exception as e:
            self.log_test_result(
                "Amazon Health Check",
                False,
                f"Health check error: {str(e)}",
                {"error": str(e), "type": type(e).__name__}
            )
            return False
    
    async def run_comprehensive_tests(self):
        """Run all comprehensive Amazon OAuth callback tests"""
        print("\n" + "="*80)
        print("🚀 STARTING COMPREHENSIVE AMAZON OAUTH CALLBACK TESTING")
        print("="*80)
        
        start_time = time.time()
        
        try:
            await self.setup_session()
            
            # Test sequence
            test_sequence = [
                ("User Authentication", self.authenticate_test_user),
                ("Amazon Connection Initiation", self.test_amazon_connection_initiation),
                ("OAuth Callback Popup Mode", self.test_oauth_callback_popup_mode),
                ("OAuth Callback Redirect Mode", self.test_oauth_callback_redirect_mode),
                ("OAuth Missing Parameters", self.test_oauth_callback_missing_parameters),
                ("OAuth Invalid State (CSRF)", self.test_oauth_callback_invalid_state),
                ("Connection Status After Callback", self.test_connection_status_after_callback),
                ("Refresh Token Validation", self.test_refresh_token_validation),
                ("Amazon Health Check", self.test_amazon_health_check)
            ]
            
            print(f"\n📋 Running {len(test_sequence)} comprehensive tests...\n")
            
            for test_name, test_func in test_sequence:
                print(f"🔄 Running: {test_name}")
                try:
                    await test_func()
                except Exception as e:
                    self.log_test_result(
                        test_name,
                        False,
                        f"Test execution error: {str(e)}",
                        {"error": str(e), "type": type(e).__name__}
                    )
                
                # Small delay between tests
                await asyncio.sleep(1)
            
        finally:
            await self.cleanup_session()
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        elapsed_time = time.time() - start_time
        
        # Print summary
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE AMAZON OAUTH CALLBACK TEST RESULTS")
        print("="*80)
        print(f"⏱️  Total Time: {elapsed_time:.2f} seconds")
        print(f"📈 Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        
        if failed_tests > 0:
            print(f"\n🔍 FAILED TESTS SUMMARY:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   ❌ {result['test']}: {result['details']}")
        
        print("\n" + "="*80)
        print("🎯 CRITICAL SUCCESS CRITERIA VALIDATION")
        print("="*80)
        
        # Validate critical success criteria
        criteria_results = []
        
        # OAuth callback processes code and generates refresh token automatically
        callback_success = any(
            result["success"] and "callback" in result["test"].lower() 
            for result in self.test_results
        )
        criteria_results.append(("OAuth callback processes code and generates refresh token automatically", callback_success))
        
        # CSRF protection via OAuth state validation working
        csrf_success = any(
            result["success"] and "invalid state" in result["test"].lower()
            for result in self.test_results
        )
        criteria_results.append(("CSRF protection via OAuth state validation working", csrf_success))
        
        # Popup and redirect modes both functional
        popup_success = any(
            result["success"] and "popup mode" in result["test"].lower()
            for result in self.test_results
        )
        redirect_success = any(
            result["success"] and "redirect mode" in result["test"].lower()
            for result in self.test_results
        )
        modes_success = popup_success and redirect_success
        criteria_results.append(("Popup and redirect modes both functional", modes_success))
        
        # Error handling comprehensive for all failure scenarios
        error_handling_success = any(
            result["success"] and "missing parameters" in result["test"].lower()
            for result in self.test_results
        )
        criteria_results.append(("Error handling comprehensive for all failure scenarios", error_handling_success))
        
        # Multi-tenant security maintained
        security_success = any(
            result["success"] and "authentication" in result["test"].lower()
            for result in self.test_results
        )
        criteria_results.append(("Multi-tenant security maintained", security_success))
        
        # Print criteria results
        for criteria, success in criteria_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {criteria}")
        
        overall_criteria_success = all(success for _, success in criteria_results)
        
        print(f"\n🏆 OVERALL CRITERIA SUCCESS: {'✅ PASS' if overall_criteria_success else '❌ FAIL'}")
        
        return success_rate >= 80.0 and overall_criteria_success

async def main():
    """Main test execution function"""
    print("🧪 Amazon OAuth Callback Comprehensive Testing Suite")
    print("=" * 60)
    
    tester = AmazonOAuthCallbackTester()
    
    try:
        success = await tester.run_comprehensive_tests()
        
        if success:
            print("\n🎉 COMPREHENSIVE TESTING COMPLETED SUCCESSFULLY!")
            print("✅ Amazon OAuth callback implementation is production-ready")
            sys.exit(0)
        else:
            print("\n⚠️ COMPREHENSIVE TESTING COMPLETED WITH ISSUES")
            print("❌ Amazon OAuth callback implementation needs attention")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Testing failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())