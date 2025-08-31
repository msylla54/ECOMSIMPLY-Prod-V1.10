#!/usr/bin/env python3
"""
ECOMSIMPLY Authentication System Verification Test
Focus: Comprehensive verification of authentication fixes after critical issues resolution
Review Request: Verify signup/login issues have been resolved after fixes
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

class AuthVerificationTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ECOMSIMPLY-Auth-Verification/1.0'
        })
        self.test_results = []
        # Use unique test data for each run
        self.test_user_email = f"authtest+{int(time.time())}@ecomsimply.com"
        self.test_user_password = "SecureTest#2025!"
        self.test_user_name = "Auth Verification User"
        self.jwt_token = None
        
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

    def test_health_endpoint(self):
        """Test /api/health endpoint for overall backend health"""
        try:
            url = f"{BACKEND_URL}/api/health"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Check for healthy status indicators
                if (data.get('status') == 'healthy' or 
                    data.get('ok') == True or 
                    'healthy' in str(data).lower()):
                    self.log_result(
                        "Backend Health Check", 
                        True, 
                        f"Backend healthy: {data}",
                        url
                    )
                    return True
                else:
                    self.log_result(
                        "Backend Health Check", 
                        False, 
                        f"Backend unhealthy: {data}",
                        url
                    )
                    return False
            else:
                self.log_result(
                    "Backend Health Check", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}",
                    url
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Backend Health Check", 
                False, 
                f"Exception: {str(e)}",
                f"{BACKEND_URL}/api/health"
            )
            return False

    def test_registration_flow(self):
        """Test complete registration flow with real data"""
        try:
            url = f"{BACKEND_URL}/api/auth/register"
            payload = {
                "name": self.test_user_name,
                "email": self.test_user_email,
                "password": self.test_user_password,
                "language": "fr"
            }
            
            response = self.session.post(url, json=payload, timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check for server errors in successful response
                    if 'detail' in data and 'erreur' in data.get('detail', '').lower():
                        self.log_result(
                            "User Registration Flow", 
                            False, 
                            f"Server error in registration: {data['detail']}",
                            url
                        )
                        return False, None
                    
                    # Check for successful registration with token
                    if 'token' in data or 'access_token' in data:
                        token = data.get('token') or data.get('access_token')
                        user_data = data.get('user', {})
                        
                        if token and token != 'null':
                            self.log_result(
                                "User Registration Flow", 
                                True, 
                                f"Registration successful - User: {user_data.get('email')}, Token length: {len(str(token))}",
                                url
                            )
                            return True, token
                        else:
                            self.log_result(
                                "User Registration Flow", 
                                False, 
                                f"Invalid token received: {token}",
                                url
                            )
                            return False, None
                    else:
                        self.log_result(
                            "User Registration Flow", 
                            False, 
                            f"No token in registration response: {data}",
                            url
                        )
                        return False, None
                        
                except json.JSONDecodeError:
                    self.log_result(
                        "User Registration Flow", 
                        False, 
                        f"Invalid JSON in registration response: {response.text[:200]}",
                        url
                    )
                    return False, None
            else:
                self.log_result(
                    "User Registration Flow", 
                    False, 
                    f"Registration failed - Status: {response.status_code}, Response: {response.text[:300]}",
                    url
                )
                return False, None
                
        except Exception as e:
            self.log_result(
                "User Registration Flow", 
                False, 
                f"Registration exception: {str(e)}",
                f"{BACKEND_URL}/api/auth/register"
            )
            return False, None

    def test_login_flow(self):
        """Test login flow with registered user"""
        try:
            url = f"{BACKEND_URL}/api/auth/login"
            payload = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            response = self.session.post(url, json=payload, timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check for server errors
                    if 'detail' in data and 'erreur' in data.get('detail', '').lower():
                        self.log_result(
                            "User Login Flow", 
                            False, 
                            f"Server error in login: {data['detail']}",
                            url
                        )
                        return False, None
                    
                    # Check for successful login
                    if 'token' in data or 'access_token' in data:
                        token = data.get('token') or data.get('access_token')
                        user_data = data.get('user', {})
                        
                        if token and token != 'null':
                            self.jwt_token = token  # Store for /me endpoint test
                            self.log_result(
                                "User Login Flow", 
                                True, 
                                f"Login successful - User: {user_data.get('email')}, Token valid: {bool(token)}",
                                url
                            )
                            return True, token
                        else:
                            self.log_result(
                                "User Login Flow", 
                                False, 
                                f"Invalid token in login: {token}",
                                url
                            )
                            return False, None
                    else:
                        self.log_result(
                            "User Login Flow", 
                            False, 
                            f"No token in login response: {data}",
                            url
                        )
                        return False, None
                        
                except json.JSONDecodeError:
                    self.log_result(
                        "User Login Flow", 
                        False, 
                        f"Invalid JSON in login response: {response.text[:200]}",
                        url
                    )
                    return False, None
            else:
                self.log_result(
                    "User Login Flow", 
                    False, 
                    f"Login failed - Status: {response.status_code}, Response: {response.text[:300]}",
                    url
                )
                return False, None
                
        except Exception as e:
            self.log_result(
                "User Login Flow", 
                False, 
                f"Login exception: {str(e)}",
                f"{BACKEND_URL}/api/auth/login"
            )
            return False, None

    def test_me_endpoint(self):
        """Test /api/auth/me endpoint with JWT token validation"""
        if not self.jwt_token:
            self.log_result(
                "Token Validation (/api/auth/me)", 
                False, 
                "No JWT token available for testing",
                f"{BACKEND_URL}/api/auth/me"
            )
            return False
            
        try:
            url = f"{BACKEND_URL}/api/auth/me"
            headers = {
                'Authorization': f'Bearer {self.jwt_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check for user data in response
                    if 'email' in data or 'user' in data:
                        user_email = data.get('email') or data.get('user', {}).get('email')
                        user_id = data.get('id') or data.get('user', {}).get('id')
                        
                        if user_email == self.test_user_email:
                            self.log_result(
                                "Token Validation (/api/auth/me)", 
                                True, 
                                f"Token valid - User: {user_email}, ID: {user_id}",
                                url
                            )
                            return True
                        else:
                            self.log_result(
                                "Token Validation (/api/auth/me)", 
                                False, 
                                f"Token valid but wrong user - Expected: {self.test_user_email}, Got: {user_email}",
                                url
                            )
                            return False
                    else:
                        self.log_result(
                            "Token Validation (/api/auth/me)", 
                            False, 
                            f"No user data in /me response: {data}",
                            url
                        )
                        return False
                        
                except json.JSONDecodeError:
                    self.log_result(
                        "Token Validation (/api/auth/me)", 
                        False, 
                        f"Invalid JSON in /me response: {response.text[:200]}",
                        url
                    )
                    return False
            elif response.status_code == 401:
                self.log_result(
                    "Token Validation (/api/auth/me)", 
                    False, 
                    f"Token rejected (401): {response.text[:200]}",
                    url
                )
                return False
            elif response.status_code == 404:
                self.log_result(
                    "Token Validation (/api/auth/me)", 
                    False, 
                    "/api/auth/me endpoint not found (404) - Critical issue!",
                    url
                )
                return False
            else:
                self.log_result(
                    "Token Validation (/api/auth/me)", 
                    False, 
                    f"Unexpected status: {response.status_code}, Response: {response.text[:200]}",
                    url
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Token Validation (/api/auth/me)", 
                False, 
                f"/me endpoint exception: {str(e)}",
                f"{BACKEND_URL}/api/auth/me"
            )
            return False

    def test_error_handling(self):
        """Test error handling scenarios"""
        error_tests = []
        
        # Test 1: Duplicate email registration
        try:
            url = f"{BACKEND_URL}/api/auth/register"
            payload = {
                "name": "Duplicate User",
                "email": self.test_user_email,  # Same email as before
                "password": "AnotherPassword123!"
            }
            
            response = self.session.post(url, json=payload, timeout=10)
            
            if response.status_code == 409:  # Conflict - expected for duplicate
                error_tests.append(("Duplicate Email Registration", True, "Correctly returned 409 for duplicate email"))
            elif response.status_code == 400:  # Bad request also acceptable
                error_tests.append(("Duplicate Email Registration", True, "Correctly returned 400 for duplicate email"))
            else:
                error_tests.append(("Duplicate Email Registration", False, f"Unexpected status {response.status_code} for duplicate email"))
                
        except Exception as e:
            error_tests.append(("Duplicate Email Registration", False, f"Exception: {str(e)}"))
        
        # Test 2: Invalid credentials login
        try:
            url = f"{BACKEND_URL}/api/auth/login"
            payload = {
                "email": self.test_user_email,
                "password": "WrongPassword123!"
            }
            
            response = self.session.post(url, json=payload, timeout=10)
            
            if response.status_code == 401:  # Unauthorized - expected
                error_tests.append(("Invalid Credentials Login", True, "Correctly returned 401 for invalid credentials"))
            else:
                error_tests.append(("Invalid Credentials Login", False, f"Unexpected status {response.status_code} for invalid credentials"))
                
        except Exception as e:
            error_tests.append(("Invalid Credentials Login", False, f"Exception: {str(e)}"))
        
        # Test 3: Invalid token for /me endpoint
        try:
            url = f"{BACKEND_URL}/api/auth/me"
            headers = {
                'Authorization': 'Bearer invalid_token_12345',
                'Content-Type': 'application/json'
            }
            
            response = self.session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 401:  # Unauthorized - expected
                error_tests.append(("Invalid Token /me", True, "Correctly returned 401 for invalid token"))
            else:
                error_tests.append(("Invalid Token /me", False, f"Unexpected status {response.status_code} for invalid token"))
                
        except Exception as e:
            error_tests.append(("Invalid Token /me", False, f"Exception: {str(e)}"))
        
        # Test 4: Missing required fields
        try:
            url = f"{BACKEND_URL}/api/auth/register"
            payload = {
                "name": "Incomplete User"
                # Missing email and password
            }
            
            response = self.session.post(url, json=payload, timeout=10)
            
            if response.status_code == 422:  # Validation error - expected
                error_tests.append(("Missing Required Fields", True, "Correctly returned 422 for missing fields"))
            elif response.status_code == 400:  # Bad request also acceptable
                error_tests.append(("Missing Required Fields", True, "Correctly returned 400 for missing fields"))
            else:
                error_tests.append(("Missing Required Fields", False, f"Unexpected status {response.status_code} for missing fields"))
                
        except Exception as e:
            error_tests.append(("Missing Required Fields", False, f"Exception: {str(e)}"))
        
        # Log all error handling test results
        for test_name, success, details in error_tests:
            self.log_result(f"Error Handling - {test_name}", success, details)
        
        return error_tests

    def test_database_persistence(self):
        """Test that user data is properly persisted in MongoDB"""
        # This is tested implicitly by the login after registration
        # If login works after registration, database persistence is working
        
        # Additional test: Try to register same user again (should fail due to unique constraint)
        try:
            url = f"{BACKEND_URL}/api/auth/register"
            payload = {
                "name": "Same User Again",
                "email": self.test_user_email,
                "password": "DifferentPassword123!"
            }
            
            response = self.session.post(url, json=payload, timeout=10)
            
            # Should fail due to unique email constraint
            if response.status_code in [409, 400]:
                self.log_result(
                    "Database Persistence Verification", 
                    True, 
                    f"Database correctly enforces unique email constraint (Status: {response.status_code})",
                    url
                )
                return True
            else:
                self.log_result(
                    "Database Persistence Verification", 
                    False, 
                    f"Database may not be enforcing constraints properly (Status: {response.status_code})",
                    url
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Database Persistence Verification", 
                False, 
                f"Database persistence test exception: {str(e)}",
                f"{BACKEND_URL}/api/auth/register"
            )
            return False

    def run_comprehensive_verification(self):
        """Run comprehensive authentication verification"""
        print("🚀 ECOMSIMPLY AUTHENTICATION SYSTEM VERIFICATION")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User: {self.test_user_email}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print()
        
        # Step 1: Backend Health Check
        print("🔍 STEP 1: Backend Health Verification")
        print("-" * 40)
        health_ok = self.test_health_endpoint()
        
        # Step 2: Authentication Endpoints Full Flow
        print("🔍 STEP 2: Authentication Endpoints Full Flow")
        print("-" * 40)
        reg_success, reg_token = self.test_registration_flow()
        
        if reg_success:
            login_success, login_token = self.test_login_flow()
            
            if login_success:
                me_success = self.test_me_endpoint()
            else:
                me_success = False
        else:
            login_success = False
            me_success = False
        
        # Step 3: Error Handling Verification
        print("🔍 STEP 3: Error Handling Verification")
        print("-" * 40)
        error_tests = self.test_error_handling()
        error_success_count = sum(1 for _, success, _ in error_tests if success)
        
        # Step 4: Database Persistence Verification
        print("🔍 STEP 4: Database Persistence Verification")
        print("-" * 40)
        db_persistence_ok = self.test_database_persistence()
        
        # Summary
        print("📊 VERIFICATION SUMMARY")
        print("=" * 40)
        print(f"✅ Backend Health: {'PASS' if health_ok else 'FAIL'}")
        print(f"✅ User Registration: {'PASS' if reg_success else 'FAIL'}")
        print(f"✅ User Login: {'PASS' if login_success else 'FAIL'}")
        print(f"✅ Token Validation (/me): {'PASS' if me_success else 'FAIL'}")
        print(f"✅ Error Handling: {error_success_count}/{len(error_tests)} PASS")
        print(f"✅ Database Persistence: {'PASS' if db_persistence_ok else 'FAIL'}")
        print()
        
        # Critical Success Criteria Check
        critical_criteria = [
            ("Registration → Login → Profile Flow", reg_success and login_success and me_success),
            ("No 404 errors on /api/auth/me", me_success),
            ("Proper error handling", error_success_count >= 3),
            ("JWT tokens work correctly", login_success and me_success),
            ("Database persistence", db_persistence_ok)
        ]
        
        print("🎯 CRITICAL SUCCESS CRITERIA")
        print("=" * 40)
        all_critical_passed = True
        for criteria, passed in critical_criteria:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} {criteria}")
            if not passed:
                all_critical_passed = False
        
        return all_critical_passed

    def generate_final_summary(self):
        """Generate final test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print("\n📋 FINAL VERIFICATION SUMMARY")
        print("=" * 50)
        print(f"Total Tests Executed: {total_tests}")
        print(f"Tests Passed: {passed_tests} ✅")
        print(f"Tests Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Identify critical failures
        auth_failures = [r for r in self.test_results if not r['success'] and 
                        ('Registration' in r['test'] or 'Login' in r['test'] or 'Token' in r['test'])]
        
        if auth_failures:
            print("🚨 CRITICAL AUTHENTICATION FAILURES:")
            for failure in auth_failures:
                print(f"   - {failure['test']}: {failure['details']}")
            print()
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests/total_tests)*100,
            'auth_failures': len(auth_failures),
            'critical_issues': len(auth_failures) > 0
        }

def main():
    """Main verification execution"""
    try:
        tester = AuthVerificationTester()
        
        # Run comprehensive verification
        all_critical_passed = tester.run_comprehensive_verification()
        
        # Generate final summary
        summary = tester.generate_final_summary()
        
        # Final assessment
        if all_critical_passed and summary['auth_failures'] == 0:
            print("🎉 AUTHENTICATION SYSTEM VERIFICATION SUCCESSFUL!")
            print("All critical authentication issues have been resolved.")
            print("The frontend signup/login modal issues can now be resolved.")
            sys.exit(0)
        elif summary['auth_failures'] == 0:
            print("✅ Authentication core functionality working")
            print("Some minor issues detected but authentication flow is operational")
            sys.exit(0)
        else:
            print("🚨 CRITICAL AUTHENTICATION ISSUES STILL PRESENT")
            print("Authentication fixes need further investigation")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Verification execution failed: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()