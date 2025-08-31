#!/usr/bin/env python3
"""
ECOMSIMPLY Authentication System Comprehensive Testing
Focus: Complete authentication flow testing including database operations
Review Request: Test signup/login endpoints, database connectivity, error scenarios
"""

import requests
import json
import time
import sys
from datetime import datetime
import traceback
import uuid

# Configuration from environment files
BACKEND_URL = "https://ecomsimply-deploy.preview.emergentagent.com"
PRODUCTION_URL = "https://ecomsimply.com"

class ComprehensiveAuthTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ECOMSIMPLY-Comprehensive-Auth-Tester/1.0'
        })
        self.test_results = []
        self.unique_id = str(uuid.uuid4())[:8]
        self.test_user_email = f"test+auth+{int(time.time())}+{self.unique_id}@ecomsimply.com"
        self.test_user_password = "Ecs#2025!demo"
        self.test_user_name = "E2E Auth Test User"
        
    def log_result(self, test_name, success, details, url_tested=None):
        """Log test result with structured information"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'url': url_tested,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if url_tested:
            print(f"    URL: {url_tested}")
        print(f"    Details: {details}")
        print()

    def test_health_endpoint(self, base_url):
        """Test health endpoint to verify backend connectivity"""
        try:
            url = f"{base_url}/api/health"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Check for database connectivity in health response
                db_status = "unknown"
                if 'services' in data and 'database' in data['services']:
                    db_status = data['services']['database']
                elif 'db' in data:
                    db_status = "connected" if data['db'] else "disconnected"
                
                self.log_result(
                    f"Health Check ({base_url})", 
                    True, 
                    f"Status: {response.status_code}, DB Status: {db_status}, Response: {data}",
                    url
                )
                return True, db_status
            else:
                self.log_result(
                    f"Health Check ({base_url})", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}",
                    url
                )
                return False, "unknown"
                
        except Exception as e:
            self.log_result(
                f"Health Check ({base_url})", 
                False, 
                f"Exception: {str(e)}",
                f"{base_url}/api/health"
            )
            return False, "error"

    def test_registration_valid_data(self, base_url):
        """Test user registration with valid data"""
        try:
            url = f"{base_url}/api/auth/register"
            payload = {
                "name": self.test_user_name,
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            response = self.session.post(url, json=payload, timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check for error messages in successful response
                    if 'detail' in data and 'erreur' in data['detail'].lower():
                        self.log_result(
                            f"Registration Valid Data ({base_url})", 
                            False, 
                            f"Server error in response: {data['detail']}",
                            url
                        )
                        return False, None
                    
                    # Check for successful registration indicators
                    if 'token' in data or 'access_token' in data or 'user' in data:
                        token = data.get('token') or data.get('access_token')
                        user_data = data.get('user', {})
                        self.log_result(
                            f"Registration Valid Data ({base_url})", 
                            True, 
                            f"Registration successful, token: {bool(token)}, user_id: {user_data.get('id', 'N/A')}",
                            url
                        )
                        return True, token
                    else:
                        self.log_result(
                            f"Registration Valid Data ({base_url})", 
                            False, 
                            f"No token in response: {data}",
                            url
                        )
                        return False, None
                        
                except json.JSONDecodeError:
                    self.log_result(
                        f"Registration Valid Data ({base_url})", 
                        False, 
                        f"Invalid JSON response: {response.text[:200]}",
                        url
                    )
                    return False, None
            else:
                self.log_result(
                    f"Registration Valid Data ({base_url})", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}",
                    url
                )
                return False, None
                
        except Exception as e:
            self.log_result(
                f"Registration Valid Data ({base_url})", 
                False, 
                f"Exception: {str(e)}",
                f"{base_url}/api/auth/register"
            )
            return False, None

    def test_registration_duplicate_email(self, base_url):
        """Test registration with duplicate email (should return 409)"""
        try:
            url = f"{base_url}/api/auth/register"
            payload = {
                "name": "Duplicate User",
                "email": self.test_user_email,  # Same email as previous registration
                "password": "AnotherPassword123!"
            }
            
            response = self.session.post(url, json=payload, timeout=15)
            
            # Should return 409 Conflict or 400 Bad Request for duplicate email
            if response.status_code in [409, 400]:
                try:
                    data = response.json()
                    self.log_result(
                        f"Registration Duplicate Email ({base_url})", 
                        True, 
                        f"Correctly rejected duplicate email with status {response.status_code}: {data}",
                        url
                    )
                    return True
                except json.JSONDecodeError:
                    self.log_result(
                        f"Registration Duplicate Email ({base_url})", 
                        True, 
                        f"Correctly rejected duplicate email with status {response.status_code}",
                        url
                    )
                    return True
            elif response.status_code == 500:
                # Server error might indicate database issues
                self.log_result(
                    f"Registration Duplicate Email ({base_url})", 
                    False, 
                    f"Server error (500) instead of proper duplicate handling: {response.text[:200]}",
                    url
                )
                return False
            else:
                self.log_result(
                    f"Registration Duplicate Email ({base_url})", 
                    False, 
                    f"Unexpected status {response.status_code} for duplicate email: {response.text[:200]}",
                    url
                )
                return False
                
        except Exception as e:
            self.log_result(
                f"Registration Duplicate Email ({base_url})", 
                False, 
                f"Exception: {str(e)}",
                f"{base_url}/api/auth/register"
            )
            return False

    def test_login_valid_credentials(self, base_url):
        """Test login with valid credentials"""
        try:
            url = f"{base_url}/api/auth/login"
            payload = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            response = self.session.post(url, json=payload, timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check for error messages in successful response
                    if 'detail' in data and 'erreur' in data['detail'].lower():
                        self.log_result(
                            f"Login Valid Credentials ({base_url})", 
                            False, 
                            f"Server error in response: {data['detail']}",
                            url
                        )
                        return False, None
                    
                    # Check for successful login indicators
                    if 'token' in data or 'access_token' in data:
                        token = data.get('token') or data.get('access_token')
                        if token and token != 'null' and token is not None:
                            user_data = data.get('user', {})
                            self.log_result(
                                f"Login Valid Credentials ({base_url})", 
                                True, 
                                f"Login successful, valid token received, user_id: {user_data.get('id', 'N/A')}",
                                url
                            )
                            return True, token
                        else:
                            self.log_result(
                                f"Login Valid Credentials ({base_url})", 
                                False, 
                                f"Null or invalid token received: {token}",
                                url
                            )
                            return False, None
                    else:
                        self.log_result(
                            f"Login Valid Credentials ({base_url})", 
                            False, 
                            f"No token in response: {data}",
                            url
                        )
                        return False, None
                        
                except json.JSONDecodeError:
                    self.log_result(
                        f"Login Valid Credentials ({base_url})", 
                        False, 
                        f"Invalid JSON response: {response.text[:200]}",
                        url
                    )
                    return False, None
            else:
                self.log_result(
                    f"Login Valid Credentials ({base_url})", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}",
                    url
                )
                return False, None
                
        except Exception as e:
            self.log_result(
                f"Login Valid Credentials ({base_url})", 
                False, 
                f"Exception: {str(e)}",
                f"{base_url}/api/auth/login"
            )
            return False, None

    def test_login_invalid_credentials(self, base_url):
        """Test login with invalid credentials (should return 401)"""
        try:
            url = f"{base_url}/api/auth/login"
            payload = {
                "email": self.test_user_email,
                "password": "WrongPassword123!"
            }
            
            response = self.session.post(url, json=payload, timeout=15)
            
            # Should return 401 Unauthorized for invalid credentials
            if response.status_code == 401:
                try:
                    data = response.json()
                    self.log_result(
                        f"Login Invalid Credentials ({base_url})", 
                        True, 
                        f"Correctly rejected invalid credentials with 401: {data}",
                        url
                    )
                    return True
                except json.JSONDecodeError:
                    self.log_result(
                        f"Login Invalid Credentials ({base_url})", 
                        True, 
                        f"Correctly rejected invalid credentials with 401",
                        url
                    )
                    return True
            elif response.status_code == 500:
                # Server error might indicate authentication system issues
                self.log_result(
                    f"Login Invalid Credentials ({base_url})", 
                    False, 
                    f"Server error (500) instead of proper 401: {response.text[:200]}",
                    url
                )
                return False
            else:
                self.log_result(
                    f"Login Invalid Credentials ({base_url})", 
                    False, 
                    f"Unexpected status {response.status_code} for invalid credentials: {response.text[:200]}",
                    url
                )
                return False
                
        except Exception as e:
            self.log_result(
                f"Login Invalid Credentials ({base_url})", 
                False, 
                f"Exception: {str(e)}",
                f"{base_url}/api/auth/login"
            )
            return False

    def test_token_validation(self, base_url, token):
        """Test token validation with /api/auth/me endpoint"""
        if not token:
            self.log_result(
                f"Token Validation ({base_url})", 
                False, 
                "No token available for validation",
                f"{base_url}/api/auth/me"
            )
            return False
            
        try:
            url = f"{base_url}/api/auth/me"
            headers = {"Authorization": f"Bearer {token}"}
            
            response = self.session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    user_data = data.get('user', data)  # Handle different response formats
                    self.log_result(
                        f"Token Validation ({base_url})", 
                        True, 
                        f"Token valid, user: {user_data.get('email', 'N/A')}, id: {user_data.get('id', 'N/A')}",
                        url
                    )
                    return True
                except json.JSONDecodeError:
                    self.log_result(
                        f"Token Validation ({base_url})", 
                        False, 
                        f"Invalid JSON response: {response.text[:200]}",
                        url
                    )
                    return False
            elif response.status_code == 401:
                self.log_result(
                    f"Token Validation ({base_url})", 
                    False, 
                    f"Token rejected as invalid (401): {response.text[:200]}",
                    url
                )
                return False
            else:
                self.log_result(
                    f"Token Validation ({base_url})", 
                    False, 
                    f"Unexpected status {response.status_code}: {response.text[:200]}",
                    url
                )
                return False
                
        except Exception as e:
            self.log_result(
                f"Token Validation ({base_url})", 
                False, 
                f"Exception: {str(e)}",
                f"{base_url}/api/auth/me"
            )
            return False

    def test_missing_required_fields(self, base_url):
        """Test registration with missing required fields (should return 422)"""
        test_cases = [
            {"name": "Test User"},  # Missing email and password
            {"email": "test@example.com"},  # Missing name and password
            {"password": "password123"},  # Missing name and email
            {}  # Missing all fields
        ]
        
        results = []
        for i, payload in enumerate(test_cases):
            try:
                url = f"{base_url}/api/auth/register"
                response = self.session.post(url, json=payload, timeout=10)
                
                # Should return 422 Unprocessable Entity for missing fields
                if response.status_code == 422:
                    try:
                        data = response.json()
                        self.log_result(
                            f"Missing Fields Test {i+1} ({base_url})", 
                            True, 
                            f"Correctly rejected missing fields with 422: {data.get('detail', 'Validation error')}",
                            url
                        )
                        results.append(True)
                    except json.JSONDecodeError:
                        self.log_result(
                            f"Missing Fields Test {i+1} ({base_url})", 
                            True, 
                            f"Correctly rejected missing fields with 422",
                            url
                        )
                        results.append(True)
                else:
                    self.log_result(
                        f"Missing Fields Test {i+1} ({base_url})", 
                        False, 
                        f"Unexpected status {response.status_code} for missing fields: {response.text[:200]}",
                        url
                    )
                    results.append(False)
                    
            except Exception as e:
                self.log_result(
                    f"Missing Fields Test {i+1} ({base_url})", 
                    False, 
                    f"Exception: {str(e)}",
                    f"{base_url}/api/auth/register"
                )
                results.append(False)
        
        return all(results)

    def test_cors_and_headers(self, base_url):
        """Test CORS and header handling"""
        try:
            url = f"{base_url}/api/health"
            
            # Test with custom headers
            headers = {
                'Origin': 'https://ecomsimply.com',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            }
            
            response = self.session.options(url, headers=headers, timeout=10)
            
            # Check CORS headers in response
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            has_cors = any(cors_headers.values())
            
            self.log_result(
                f"CORS Headers Test ({base_url})", 
                has_cors, 
                f"CORS headers present: {has_cors}, Headers: {cors_headers}",
                url
            )
            return has_cors
            
        except Exception as e:
            self.log_result(
                f"CORS Headers Test ({base_url})", 
                False, 
                f"Exception: {str(e)}",
                f"{base_url}/api/health"
            )
            return False

    def run_comprehensive_test(self):
        """Run comprehensive authentication testing"""
        print("🚀 ECOMSIMPLY AUTHENTICATION SYSTEM COMPREHENSIVE TESTING")
        print("=" * 70)
        print(f"Test User: {self.test_user_email}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print()
        
        # Test both preview and production URLs
        urls_to_test = [
            ("Preview URL", BACKEND_URL),
            ("Production URL", PRODUCTION_URL)
        ]
        
        for url_name, base_url in urls_to_test:
            print(f"🔍 Testing {url_name}: {base_url}")
            print("-" * 50)
            
            # 1. Test health endpoint and database connectivity
            health_ok, db_status = self.test_health_endpoint(base_url)
            
            # 2. Test CORS and headers
            cors_ok = self.test_cors_and_headers(base_url)
            
            # 3. Test registration with valid data
            reg_success, reg_token = self.test_registration_valid_data(base_url)
            
            # 4. Test registration with duplicate email
            duplicate_handled = self.test_registration_duplicate_email(base_url)
            
            # 5. Test login with valid credentials
            login_success, login_token = self.test_login_valid_credentials(base_url)
            
            # 6. Test login with invalid credentials
            invalid_login_handled = self.test_login_invalid_credentials(base_url)
            
            # 7. Test token validation
            token_to_test = reg_token or login_token
            token_valid = self.test_token_validation(base_url, token_to_test)
            
            # 8. Test missing required fields
            missing_fields_handled = self.test_missing_required_fields(base_url)
            
            print(f"📊 {url_name} Summary:")
            print(f"   Health & DB: {'✅' if health_ok else '❌'} (DB: {db_status})")
            print(f"   CORS Headers: {'✅' if cors_ok else '❌'}")
            print(f"   Registration: {'✅' if reg_success else '❌'}")
            print(f"   Duplicate Email Handling: {'✅' if duplicate_handled else '❌'}")
            print(f"   Login: {'✅' if login_success else '❌'}")
            print(f"   Invalid Login Handling: {'✅' if invalid_login_handled else '❌'}")
            print(f"   Token Validation: {'✅' if token_valid else '❌'}")
            print(f"   Missing Fields Handling: {'✅' if missing_fields_handled else '❌'}")
            print()

    def generate_summary(self):
        """Generate comprehensive test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print("📋 COMPREHENSIVE TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Analyze failures by URL
        preview_failures = [r for r in self.test_results if not r['success'] and BACKEND_URL in str(r.get('url', ''))]
        production_failures = [r for r in self.test_results if not r['success'] and PRODUCTION_URL in str(r.get('url', ''))]
        
        print("🔍 FAILURE ANALYSIS:")
        print(f"Preview URL failures: {len(preview_failures)}")
        print(f"Production URL failures: {len(production_failures)}")
        print()
        
        if production_failures:
            print("❌ PRODUCTION ISSUES IDENTIFIED:")
            for failure in production_failures:
                print(f"   - {failure['test']}: {failure['details']}")
            print()
        
        # Critical authentication failures
        auth_failures = [r for r in self.test_results if not r['success'] and 
                        ('Registration' in r['test'] or 'Login' in r['test'] or 'Token' in r['test'])]
        
        if auth_failures:
            print("🚨 CRITICAL AUTHENTICATION FAILURES:")
            for failure in auth_failures:
                print(f"   - {failure['test']}: {failure['details']}")
            print()
        
        # Database connectivity issues
        db_failures = [r for r in self.test_results if not r['success'] and 'Health' in r['test']]
        if db_failures:
            print("🗄️ DATABASE CONNECTIVITY ISSUES:")
            for failure in db_failures:
                print(f"   - {failure['test']}: {failure['details']}")
            print()
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests/total_tests)*100,
            'preview_failures': len(preview_failures),
            'production_failures': len(production_failures),
            'auth_failures': len(auth_failures),
            'db_failures': len(db_failures),
            'critical_issues': len(auth_failures) > 0 or len(db_failures) > 0
        }

def main():
    """Main test execution"""
    try:
        tester = ComprehensiveAuthTester()
        
        # Run comprehensive authentication testing
        tester.run_comprehensive_test()
        
        # Generate summary and analysis
        summary = tester.generate_summary()
        
        # Final recommendations
        print("🎯 RECOMMENDATIONS:")
        if summary['production_failures'] > 0:
            print("   - Investigate production deployment configuration")
            print("   - Check database connectivity in production environment")
            print("   - Verify environment variables are properly set")
        if summary['auth_failures'] > 0:
            print("   - Review authentication system implementation")
            print("   - Check JWT token generation and validation")
            print("   - Verify password hashing and bcrypt configuration")
        if summary['db_failures'] > 0:
            print("   - Check MongoDB connection string and credentials")
            print("   - Verify database server availability")
            print("   - Review database initialization and bootstrap process")
        
        if summary['critical_issues']:
            print("\n🚨 CRITICAL ISSUES DETECTED - IMMEDIATE ATTENTION REQUIRED")
            sys.exit(1)
        elif summary['failed_tests'] > 0:
            print("\n⚠️ Some tests failed but no critical issues detected")
            sys.exit(1)
        else:
            print("\n✅ All authentication tests passed successfully")
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()