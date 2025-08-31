#!/usr/bin/env python3
"""
ECOMSIMPLY Amazon Backend Regression Test - Post UI Refactoring
==============================================================

Test suite to verify Amazon SP-API endpoints remain functional after UI refactoring.
Tests all Amazon endpoints, data consistency, multi-tenant security, and non-regression.

Author: Testing Agent
Date: 2025-01-01
"""

import requests
import json
import jwt
import time
from datetime import datetime

# Configuration - Use localhost since external URL has 502 issues
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_EMAIL = "msylla54@gmail.com"
TEST_PASSWORD = "AmiMorFa01!"

class AmazonBackendRegressionTest:
    """Test suite for Amazon integration after UI refactoring"""
    
    def __init__(self):
        self.auth_token = None
        self.user_id = None
        self.test_results = {}
        
    def authenticate(self):
        """Authenticate test user and get JWT token"""
        print("🔐 Authenticating test user...")
        
        try:
            login_data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            response = requests.post(f"{API_BASE}/auth/login", json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                
                # Decode JWT to get user_id
                if self.auth_token:
                    payload = jwt.decode(self.auth_token, options={"verify_signature": False})
                    self.user_id = payload.get("user_id")
                    
                print(f"✅ Authentication successful - User ID: {self.user_id}")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
            
    def get_auth_headers(self):
        """Get authorization headers for API requests"""
        if not self.auth_token:
            raise Exception("No authentication token available")
        return {"Authorization": f"Bearer {self.auth_token}"}
        
    def test_amazon_endpoints(self):
        """Test all Amazon SP-API endpoints functionality"""
        print("\n🔍 Testing Amazon SP-API Endpoints...")
        
        results = {}
        
        # Test 1: GET /api/amazon/connect (OAuth URL generation)
        print("  Testing GET /api/amazon/connect...")
        try:
            headers = self.get_auth_headers()
            response = requests.get(f"{API_BASE}/amazon/connect", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "authorization_url" in data and "connection_id" in data:
                    results["connect_endpoint"] = {
                        "status": "PASS",
                        "details": "OAuth URL generation working correctly",
                        "response_fields": list(data.keys())
                    }
                    print("    ✅ PASS - OAuth URL generation working")
                else:
                    results["connect_endpoint"] = {
                        "status": "FAIL",
                        "details": "Missing required fields in response"
                    }
                    print("    ❌ FAIL - Missing required fields")
            else:
                results["connect_endpoint"] = {
                    "status": "FAIL",
                    "details": f"HTTP {response.status_code}: {response.text}"
                }
                print(f"    ❌ FAIL - HTTP {response.status_code}")
        except Exception as e:
            results["connect_endpoint"] = {
                "status": "ERROR",
                "details": f"Exception: {str(e)}"
            }
            print(f"    🔥 ERROR - {str(e)}")
            
        # Test 2: GET /api/amazon/status (Connection status)
        print("  Testing GET /api/amazon/status...")
        try:
            headers = self.get_auth_headers()
            response = requests.get(f"{API_BASE}/amazon/status", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                valid_statuses = ["none", "connected", "revoked", "pending"]
                if "status" in data and data["status"] in valid_statuses:
                    results["status_endpoint"] = {
                        "status": "PASS",
                        "details": f"Status endpoint working - Status: {data['status']}",
                        "current_status": data["status"],
                        "connections_count": data.get("connections_count", 0)
                    }
                    print(f"    ✅ PASS - Status: {data['status']}, Connections: {data.get('connections_count', 0)}")
                else:
                    results["status_endpoint"] = {
                        "status": "FAIL",
                        "details": "Invalid status response format"
                    }
                    print("    ❌ FAIL - Invalid response format")
            else:
                results["status_endpoint"] = {
                    "status": "FAIL",
                    "details": f"HTTP {response.status_code}: {response.text}"
                }
                print(f"    ❌ FAIL - HTTP {response.status_code}")
        except Exception as e:
            results["status_endpoint"] = {
                "status": "ERROR",
                "details": f"Exception: {str(e)}"
            }
            print(f"    🔥 ERROR - {str(e)}")
            
        # Test 3: POST /api/amazon/disconnect (Disconnect all connections)
        print("  Testing POST /api/amazon/disconnect...")
        try:
            headers = self.get_auth_headers()
            response = requests.post(f"{API_BASE}/amazon/disconnect", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "status" in data and "disconnected_count" in data:
                    results["disconnect_endpoint"] = {
                        "status": "PASS",
                        "details": f"Disconnect endpoint working - {data['disconnected_count']} connections processed",
                        "disconnected_count": data["disconnected_count"],
                        "response_status": data["status"]
                    }
                    print(f"    ✅ PASS - Disconnected {data['disconnected_count']} connections")
                else:
                    results["disconnect_endpoint"] = {
                        "status": "FAIL",
                        "details": "Invalid disconnect response format"
                    }
                    print("    ❌ FAIL - Invalid response format")
            else:
                results["disconnect_endpoint"] = {
                    "status": "FAIL",
                    "details": f"HTTP {response.status_code}: {response.text}"
                }
                print(f"    ❌ FAIL - HTTP {response.status_code}")
        except Exception as e:
            results["disconnect_endpoint"] = {
                "status": "ERROR",
                "details": f"Exception: {str(e)}"
            }
            print(f"    🔥 ERROR - {str(e)}")
            
        # Test 4: GET /api/amazon/callback (OAuth callback accessibility)
        print("  Testing GET /api/amazon/callback...")
        try:
            response = requests.get(f"{API_BASE}/amazon/callback", timeout=10)
            # Should return 400 for missing parameters, not 404 or 500
            if response.status_code == 400:
                results["callback_endpoint"] = {
                    "status": "PASS",
                    "details": "Callback endpoint accessible and validates parameters correctly"
                }
                print("    ✅ PASS - Callback endpoint accessible")
            elif response.status_code == 404:
                results["callback_endpoint"] = {
                    "status": "FAIL",
                    "details": "Callback endpoint not found (404)"
                }
                print("    ❌ FAIL - Endpoint not found")
            else:
                results["callback_endpoint"] = {
                    "status": "PARTIAL",
                    "details": f"Callback endpoint accessible but unexpected status: {response.status_code}"
                }
                print(f"    ⚠️ PARTIAL - Unexpected status {response.status_code}")
        except Exception as e:
            results["callback_endpoint"] = {
                "status": "ERROR",
                "details": f"Exception: {str(e)}"
            }
            print(f"    🔥 ERROR - {str(e)}")
            
        # Test 5: GET /api/amazon/health (Health check)
        print("  Testing GET /api/amazon/health...")
        try:
            response = requests.get(f"{API_BASE}/amazon/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "status" in data and "service" in data:
                    results["health_endpoint"] = {
                        "status": "PASS",
                        "details": f"Health endpoint working - Service status: {data['status']}",
                        "service_status": data["status"],
                        "service_name": data.get("service", "Unknown")
                    }
                    print(f"    ✅ PASS - Service status: {data['status']}")
                else:
                    results["health_endpoint"] = {
                        "status": "FAIL",
                        "details": "Invalid health response format"
                    }
                    print("    ❌ FAIL - Invalid response format")
            else:
                results["health_endpoint"] = {
                    "status": "FAIL",
                    "details": f"HTTP {response.status_code}: {response.text}"
                }
                print(f"    ❌ FAIL - HTTP {response.status_code}")
        except Exception as e:
            results["health_endpoint"] = {
                "status": "ERROR",
                "details": f"Exception: {str(e)}"
            }
            print(f"    🔥 ERROR - {str(e)}")
            
        self.test_results["amazon_endpoints"] = results
        
        # Calculate success rate
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result["status"] == "PASS")
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n📊 Amazon Endpoints: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
        
    def test_security_validation(self):
        """Test multi-tenant security with JWT authentication"""
        print("\n🔍 Testing Security Validation...")
        
        results = {}
        
        # Test 1: Verify JWT authentication required
        print("  Testing JWT authentication requirement...")
        try:
            response = requests.get(f"{API_BASE}/amazon/status", timeout=10)
            if response.status_code in [401, 403]:
                results["jwt_required"] = {
                    "status": "PASS",
                    "details": f"Authentication properly required (HTTP {response.status_code})"
                }
                print(f"    ✅ PASS - Auth required (HTTP {response.status_code})")
            elif response.status_code == 200:
                results["jwt_required"] = {
                    "status": "FAIL",
                    "details": "Endpoint accessible without authentication - security vulnerability"
                }
                print("    ❌ FAIL - No auth required (security issue)")
            else:
                results["jwt_required"] = {
                    "status": "PARTIAL",
                    "details": f"Unexpected response without auth: HTTP {response.status_code}"
                }
                print(f"    ⚠️ PARTIAL - Unexpected status {response.status_code}")
        except Exception as e:
            results["jwt_required"] = {
                "status": "ERROR",
                "details": f"Exception: {str(e)}"
            }
            print(f"    🔥 ERROR - {str(e)}")
            
        # Test 2: Verify no sensitive data leakage
        print("  Testing for sensitive data leakage...")
        try:
            headers = self.get_auth_headers()
            response = requests.get(f"{API_BASE}/amazon/status", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                response_text = json.dumps(data).lower()
                
                # Check for sensitive data patterns
                sensitive_patterns = [
                    "refresh_token", "access_token", "client_secret", 
                    "encrypted_refresh_token", "token_encryption_nonce",
                    "password", "secret", "key"
                ]
                
                found_sensitive = [pattern for pattern in sensitive_patterns if pattern in response_text]
                
                if not found_sensitive:
                    results["no_data_leakage"] = {
                        "status": "PASS",
                        "details": "No sensitive data detected in response"
                    }
                    print("    ✅ PASS - No sensitive data leaked")
                else:
                    results["no_data_leakage"] = {
                        "status": "FAIL",
                        "details": f"Sensitive data patterns found: {found_sensitive}"
                    }
                    print(f"    ❌ FAIL - Sensitive data found: {found_sensitive}")
            else:
                results["no_data_leakage"] = {
                    "status": "SKIP",
                    "details": f"Could not test data leakage: HTTP {response.status_code}"
                }
                print(f"    ⏭️ SKIP - Could not test (HTTP {response.status_code})")
        except Exception as e:
            results["no_data_leakage"] = {
                "status": "ERROR",
                "details": f"Exception: {str(e)}"
            }
            print(f"    🔥 ERROR - {str(e)}")
            
        self.test_results["security_validation"] = results
        
        # Calculate success rate
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result["status"] == "PASS")
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n📊 Security Validation: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
        
    def test_non_regression(self):
        """Test non-regression of other application endpoints"""
        print("\n🔍 Testing Non-Regression...")
        
        results = {}
        
        # Test 1: Main health endpoint
        print("  Testing main health endpoint...")
        try:
            response = requests.get(f"{API_BASE}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "status" in data:
                    results["main_health"] = {
                        "status": "PASS",
                        "details": f"Main health endpoint working - Status: {data['status']}"
                    }
                    print(f"    ✅ PASS - Health status: {data['status']}")
                else:
                    results["main_health"] = {
                        "status": "FAIL",
                        "details": "Invalid health response format"
                    }
                    print("    ❌ FAIL - Invalid response format")
            else:
                results["main_health"] = {
                    "status": "FAIL",
                    "details": f"Health endpoint failed: HTTP {response.status_code}"
                }
                print(f"    ❌ FAIL - HTTP {response.status_code}")
        except Exception as e:
            results["main_health"] = {
                "status": "ERROR",
                "details": f"Exception: {str(e)}"
            }
            print(f"    🔥 ERROR - {str(e)}")
            
        # Test 2: Authentication endpoints
        print("  Testing authentication endpoints...")
        try:
            login_data = {"email": "test@example.com", "password": "invalid"}
            response = requests.post(f"{API_BASE}/auth/login", json=login_data, timeout=10)
            # Should return 401 for invalid credentials, not 500 or 404
            if response.status_code == 401:
                results["auth_endpoints"] = {
                    "status": "PASS",
                    "details": "Authentication endpoints working correctly"
                }
                print("    ✅ PASS - Auth endpoints working")
            elif response.status_code == 404:
                results["auth_endpoints"] = {
                    "status": "FAIL",
                    "details": "Authentication endpoint not found"
                }
                print("    ❌ FAIL - Auth endpoint not found")
            else:
                results["auth_endpoints"] = {
                    "status": "PARTIAL",
                    "details": f"Auth endpoint accessible but unexpected status: {response.status_code}"
                }
                print(f"    ⚠️ PARTIAL - Unexpected status {response.status_code}")
        except Exception as e:
            results["auth_endpoints"] = {
                "status": "ERROR",
                "details": f"Exception: {str(e)}"
            }
            print(f"    🔥 ERROR - {str(e)}")
            
        # Test 3: Subscription endpoints
        print("  Testing subscription endpoints...")
        try:
            response = requests.get(f"{API_BASE}/subscription/plans", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    results["subscription_endpoints"] = {
                        "status": "PASS",
                        "details": f"Subscription endpoints working - {len(data)} plans available"
                    }
                    print(f"    ✅ PASS - {len(data)} subscription plans available")
                else:
                    results["subscription_endpoints"] = {
                        "status": "FAIL",
                        "details": "Invalid subscription plans response"
                    }
                    print("    ❌ FAIL - Invalid plans response")
            else:
                results["subscription_endpoints"] = {
                    "status": "FAIL",
                    "details": f"Subscription endpoint failed: HTTP {response.status_code}"
                }
                print(f"    ❌ FAIL - HTTP {response.status_code}")
        except Exception as e:
            results["subscription_endpoints"] = {
                "status": "ERROR",
                "details": f"Exception: {str(e)}"
            }
            print(f"    🔥 ERROR - {str(e)}")
            
        self.test_results["non_regression"] = results
        
        # Calculate success rate
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result["status"] == "PASS")
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n📊 Non-Regression: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
        
    def calculate_overall_results(self):
        """Calculate overall test results"""
        all_results = []
        
        for category, tests in self.test_results.items():
            for test_name, result in tests.items():
                all_results.append(result["status"])
                
        if not all_results:
            return {"overall_status": "NO_TESTS", "summary": {}}
            
        total_tests = len(all_results)
        passed_tests = sum(1 for status in all_results if status == "PASS")
        failed_tests = sum(1 for status in all_results if status == "FAIL")
        error_tests = sum(1 for status in all_results if status == "ERROR")
        partial_tests = sum(1 for status in all_results if status == "PARTIAL")
        
        success_rate = (passed_tests / total_tests) * 100
        
        if success_rate >= 90:
            overall_status = "EXCELLENT"
        elif success_rate >= 75:
            overall_status = "GOOD"
        elif success_rate >= 50:
            overall_status = "PARTIAL"
        else:
            overall_status = "POOR"
            
        return {
            "overall_status": overall_status,
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": error_tests,
                "partial": partial_tests,
                "success_rate": round(success_rate, 1)
            }
        }
        
    def print_detailed_results(self):
        """Print detailed test results"""
        print("\n" + "="*80)
        print("🎯 ECOMSIMPLY AMAZON UI REFACTORING BACKEND TEST RESULTS")
        print("="*80)
        
        for category, tests in self.test_results.items():
            print(f"\n📋 {category.replace('_', ' ').title()}:")
            print("-" * 50)
            
            for test_name, result in tests.items():
                status_icon = {
                    "PASS": "✅",
                    "FAIL": "❌", 
                    "ERROR": "🔥",
                    "PARTIAL": "⚠️",
                    "SKIP": "⏭️"
                }.get(result["status"], "❓")
                
                print(f"{status_icon} {test_name}: {result['status']}")
                print(f"   Details: {result['details']}")
                
                # Print additional info if available
                for key, value in result.items():
                    if key not in ["status", "details"]:
                        print(f"   {key}: {value}")
                        
        # Print overall summary
        overall_results = self.calculate_overall_results()
        if "summary" in overall_results:
            summary = overall_results["summary"]
            print(f"\n📊 OVERALL SUMMARY:")
            print("-" * 50)
            print(f"Total Tests: {summary['total_tests']}")
            print(f"✅ Passed: {summary['passed']}")
            print(f"❌ Failed: {summary['failed']}")
            print(f"🔥 Errors: {summary['errors']}")
            print(f"⚠️ Partial: {summary['partial']}")
            print(f"📈 Success Rate: {summary['success_rate']}%")
            print(f"🎯 Overall Status: {overall_results['overall_status']}")
            
        return overall_results
        
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Amazon UI Refactoring Backend Regression Test...")
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"👤 Test User: {TEST_EMAIL}")
        
        # Authenticate
        if not self.authenticate():
            print("❌ Cannot proceed without authentication")
            return {"overall_status": "AUTH_FAILED"}
            
        # Run all test suites
        self.test_amazon_endpoints()
        self.test_security_validation()
        self.test_non_regression()
        
        # Print detailed results
        overall_results = self.print_detailed_results()
        
        return overall_results

def main():
    """Main test execution"""
    test_suite = AmazonBackendRegressionTest()
    results = test_suite.run_all_tests()
    
    print(f"\n🏁 Test execution completed with status: {results.get('overall_status', 'UNKNOWN')}")
    
    # Return appropriate exit code
    if results.get("overall_status") in ["EXCELLENT", "GOOD"]:
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)