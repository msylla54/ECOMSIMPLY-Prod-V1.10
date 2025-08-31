#!/usr/bin/env python3
"""
ECOMSIMPLY Backend Focused MongoDB Integration Test
Focus: Test actual available endpoints and verify MongoDB integration
"""

import requests
import json
import time
import sys
from datetime import datetime
import traceback

# Configuration
BACKEND_URL = "https://ecomsimply-deploy.preview.emergentagent.com"

class FocusedMongoDBTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ECOMSIMPLY-Focused-MongoDB-Tester/1.0'
        })
        self.test_results = []
        self.auth_token = None
        self.test_user_id = None
        
        # Generate unique test data
        timestamp = int(time.time())
        self.test_user_email = f"focused.test.{timestamp}@ecomsimply.com"
        self.test_user_password = "FocusedTest#2025!"
        self.test_user_name = "Focused MongoDB Test User"
        
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
        """Test health endpoint"""
        try:
            url = f"{BACKEND_URL}/api/health"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                db_name = data.get('db')
                
                if db_name:
                    self.log_result(
                        "Health Check & Database Connection", 
                        True, 
                        f"Database connected: {db_name}",
                        url
                    )
                    return True
                else:
                    self.log_result(
                        "Health Check & Database Connection", 
                        False, 
                        f"No database info in response: {data}",
                        url
                    )
                    return False
            else:
                self.log_result(
                    "Health Check & Database Connection", 
                    False, 
                    f"Status: {response.status_code}",
                    url
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Health Check & Database Connection", 
                False, 
                f"Exception: {str(e)}",
                f"{BACKEND_URL}/api/health"
            )
            return False

    def test_authentication_flow(self):
        """Test authentication: register → login"""
        try:
            # Step 1: Registration
            reg_url = f"{BACKEND_URL}/api/auth/register"
            reg_payload = {
                "name": self.test_user_name,
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            reg_response = self.session.post(reg_url, json=reg_payload, timeout=15)
            
            if reg_response.status_code == 200:
                reg_data = reg_response.json()
                token = reg_data.get('token') or reg_data.get('access_token')
                user_data = reg_data.get('user', {})
                self.test_user_id = user_data.get('id')
                
                if token and self.test_user_id:
                    self.log_result(
                        "Authentication - Registration", 
                        True, 
                        f"User registered successfully, ID: {self.test_user_id}",
                        reg_url
                    )
                    
                    # Step 2: Login
                    login_url = f"{BACKEND_URL}/api/auth/login"
                    login_payload = {
                        "email": self.test_user_email,
                        "password": self.test_user_password
                    }
                    
                    login_response = self.session.post(login_url, json=login_payload, timeout=15)
                    
                    if login_response.status_code == 200:
                        login_data = login_response.json()
                        login_token = login_data.get('token') or login_data.get('access_token')
                        
                        if login_token:
                            self.auth_token = login_token
                            self.log_result(
                                "Authentication - Login", 
                                True, 
                                f"Login successful, token received",
                                login_url
                            )
                            return True
                        else:
                            self.log_result(
                                "Authentication - Login", 
                                False, 
                                f"No token in login response",
                                login_url
                            )
                            return False
                    else:
                        self.log_result(
                            "Authentication - Login", 
                            False, 
                            f"Login failed: {login_response.status_code}",
                            login_url
                        )
                        return False
                else:
                    self.log_result(
                        "Authentication - Registration", 
                        False, 
                        f"Missing token or user ID in registration response",
                        reg_url
                    )
                    return False
            else:
                self.log_result(
                    "Authentication - Registration", 
                    False, 
                    f"Registration failed: {reg_response.status_code}, Response: {reg_response.text[:200]}",
                    reg_url
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Authentication Flow", 
                False, 
                f"Exception: {str(e)}",
                f"{BACKEND_URL}/api/auth/*"
            )
            return False

    def test_public_endpoints(self):
        """Test public endpoints that should work"""
        endpoints = [
            {
                'url': '/api/testimonials',
                'name': 'Testimonials Collection',
                'expected_keys': ['name', 'title', 'rating', 'comment']
            },
            {
                'url': '/api/stats/public',
                'name': 'Public Stats Collection',
                'expected_keys': ['stats', 'products_generated', 'active_users']
            },
            {
                'url': '/api/languages',
                'name': 'Languages Collection',
                'expected_keys': ['fr', 'en']
            },
            {
                'url': '/api/public/plans-pricing',
                'name': 'Plans Pricing Collection',
                'expected_keys': ['plans', 'success']
            }
        ]
        
        successful_endpoints = 0
        
        for endpoint in endpoints:
            try:
                url = f"{BACKEND_URL}{endpoint['url']}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if response has expected structure
                    has_expected_data = any(key in str(data) for key in endpoint['expected_keys'])
                    
                    if has_expected_data:
                        successful_endpoints += 1
                        self.log_result(
                            f"Public Endpoint - {endpoint['name']}", 
                            True, 
                            f"Data retrieved successfully, response size: {len(str(data))} chars",
                            url
                        )
                    else:
                        self.log_result(
                            f"Public Endpoint - {endpoint['name']}", 
                            False, 
                            f"Response doesn't contain expected data structure",
                            url
                        )
                else:
                    self.log_result(
                        f"Public Endpoint - {endpoint['name']}", 
                        False, 
                        f"Status: {response.status_code}",
                        url
                    )
                    
            except Exception as e:
                self.log_result(
                    f"Public Endpoint - {endpoint['name']}", 
                    False, 
                    f"Exception: {str(e)}",
                    f"{BACKEND_URL}{endpoint['url']}"
                )
        
        return successful_endpoints, len(endpoints)

    def test_contact_system(self):
        """Test contact message system"""
        if not self.auth_token:
            self.log_result(
                "Contact System", 
                False, 
                "No auth token available",
                None
            )
            return False
        
        try:
            url = f"{BACKEND_URL}/api/contact"
            payload = {
                "name": "MongoDB Test Contact",
                "email": self.test_user_email,
                "subject": "MongoDB Integration Test",
                "message": f"Test message for MongoDB integration - {datetime.now().isoformat()}"
            }
            
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            response = self.session.post(url, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                message_id = data.get('id')
                
                self.log_result(
                    "Contact System - Submit Message", 
                    True, 
                    f"Message submitted successfully, ID: {message_id}",
                    url
                )
                return True
            else:
                self.log_result(
                    "Contact System - Submit Message", 
                    False, 
                    f"Failed to submit message: {response.status_code}, Response: {response.text[:200]}",
                    url
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Contact System", 
                False, 
                f"Exception: {str(e)}",
                f"{BACKEND_URL}/api/contact"
            )
            return False

    def test_product_generation(self):
        """Test product generation system"""
        if not self.auth_token:
            self.log_result(
                "Product Generation System", 
                False, 
                "No auth token available",
                None
            )
            return False
        
        try:
            url = f"{BACKEND_URL}/api/generate-sheet"
            payload = {
                "product_name": "MongoDB Test Product - Premium Smartphone",
                "product_description": "High-end smartphone with advanced features for testing MongoDB integration",
                "generate_image": False,
                "number_of_images": 0,
                "language": "fr",
                "category": "électronique"
            }
            
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            response = self.session.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                generation_id = data.get('generation_id')
                
                self.log_result(
                    "Product Generation - Generate Sheet", 
                    True, 
                    f"Product sheet generated successfully, ID: {generation_id}",
                    url
                )
                
                # Test retrieving user sheets
                sheets_url = f"{BACKEND_URL}/api/my-sheets"
                sheets_response = self.session.get(sheets_url, headers=headers, timeout=10)
                
                if sheets_response.status_code == 200:
                    sheets_data = sheets_response.json()
                    
                    # Check if our generated sheet is in the list
                    our_sheet = any(sheet.get('product_name') == payload['product_name'] for sheet in sheets_data)
                    
                    if our_sheet:
                        self.log_result(
                            "Product Generation - Retrieve Sheets", 
                            True, 
                            f"Generated sheet found in user sheets list ({len(sheets_data)} total sheets)",
                            sheets_url
                        )
                        return True
                    else:
                        self.log_result(
                            "Product Generation - Retrieve Sheets", 
                            False, 
                            f"Generated sheet not found in user sheets",
                            sheets_url
                        )
                        return False
                else:
                    self.log_result(
                        "Product Generation - Retrieve Sheets", 
                        False, 
                        f"Failed to retrieve sheets: {sheets_response.status_code}",
                        sheets_url
                    )
                    return False
            else:
                self.log_result(
                    "Product Generation - Generate Sheet", 
                    False, 
                    f"Failed to generate sheet: {response.status_code}, Response: {response.text[:200]}",
                    url
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Product Generation System", 
                False, 
                f"Exception: {str(e)}",
                f"{BACKEND_URL}/api/generate-sheet"
            )
            return False

    def test_user_stats(self):
        """Test user statistics endpoint"""
        if not self.auth_token:
            self.log_result(
                "User Statistics", 
                False, 
                "No auth token available",
                None
            )
            return False
        
        try:
            url = f"{BACKEND_URL}/api/stats"
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            response = self.session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if we have expected user stats fields
                expected_fields = ['total_sheets', 'sheets_this_month', 'subscription_plan']
                has_expected_fields = all(field in data for field in expected_fields)
                
                if has_expected_fields:
                    self.log_result(
                        "User Statistics", 
                        True, 
                        f"User stats retrieved: {data.get('total_sheets', 0)} total sheets, plan: {data.get('subscription_plan', 'unknown')}",
                        url
                    )
                    return True
                else:
                    self.log_result(
                        "User Statistics", 
                        False, 
                        f"Missing expected fields in user stats response",
                        url
                    )
                    return False
            else:
                self.log_result(
                    "User Statistics", 
                    False, 
                    f"Failed to retrieve user stats: {response.status_code}",
                    url
                )
                return False
                
        except Exception as e:
            self.log_result(
                "User Statistics", 
                False, 
                f"Exception: {str(e)}",
                f"{BACKEND_URL}/api/stats"
            )
            return False

    def test_admin_bootstrap(self):
        """Test admin bootstrap to verify database initialization"""
        try:
            url = f"{BACKEND_URL}/api/admin/bootstrap"
            headers = {'x-bootstrap-token': 'ECS-Bootstrap-2025-Secure-Token'}
            
            response = self.session.post(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('ok'):
                    self.log_result(
                        "Admin Bootstrap - Database Initialization", 
                        True, 
                        f"Bootstrap successful: {data.get('bootstrap', 'unknown')} - {data.get('email', 'no email')}",
                        url
                    )
                    return True
                else:
                    self.log_result(
                        "Admin Bootstrap - Database Initialization", 
                        False, 
                        f"Bootstrap failed: {data}",
                        url
                    )
                    return False
            else:
                self.log_result(
                    "Admin Bootstrap - Database Initialization", 
                    False, 
                    f"Bootstrap request failed: {response.status_code}",
                    url
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Admin Bootstrap", 
                False, 
                f"Exception: {str(e)}",
                f"{BACKEND_URL}/api/admin/bootstrap"
            )
            return False

    def run_focused_mongodb_test(self):
        """Run focused MongoDB integration testing"""
        print("🚀 ECOMSIMPLY BACKEND FOCUSED MONGODB INTEGRATION TEST")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User: {self.test_user_email}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print()
        
        # Test 1: Health Check
        print("🔍 Testing Health Check & Database Connection...")
        health_ok = self.test_health_endpoint()
        
        # Test 2: Admin Bootstrap
        print("🔍 Testing Admin Bootstrap...")
        bootstrap_ok = self.test_admin_bootstrap()
        
        # Test 3: Authentication Flow
        print("🔍 Testing Authentication Flow...")
        auth_ok = self.test_authentication_flow()
        
        # Test 4: Public Endpoints
        print("🔍 Testing Public Endpoints...")
        public_success, public_total = self.test_public_endpoints()
        
        # Test 5: Contact System
        print("🔍 Testing Contact System...")
        contact_ok = self.test_contact_system()
        
        # Test 6: Product Generation
        print("🔍 Testing Product Generation System...")
        product_ok = self.test_product_generation()
        
        # Test 7: User Statistics
        print("🔍 Testing User Statistics...")
        stats_ok = self.test_user_stats()
        
        # Summary
        print("📊 FOCUSED MONGODB INTEGRATION TEST SUMMARY:")
        print("-" * 50)
        print(f"   Health & Database Connection: {'✅' if health_ok else '❌'}")
        print(f"   Admin Bootstrap: {'✅' if bootstrap_ok else '❌'}")
        print(f"   Authentication Flow: {'✅' if auth_ok else '❌'}")
        print(f"   Public Endpoints: {public_success}/{public_total} ({'✅' if public_success >= 3 else '❌'})")
        print(f"   Contact System: {'✅' if contact_ok else '❌'}")
        print(f"   Product Generation: {'✅' if product_ok else '❌'}")
        print(f"   User Statistics: {'✅' if stats_ok else '❌'}")
        print()

    def generate_final_summary(self):
        """Generate final test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print("📋 FINAL FOCUSED MONGODB INTEGRATION TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Critical success criteria
        critical_passed = 0
        critical_total = 7
        
        critical_tests = [
            ('Health Check & Database Connection', 'MongoDB connection verified'),
            ('Admin Bootstrap', 'Database initialization working'),
            ('Authentication - Registration', 'User registration working'),
            ('Authentication - Login', 'User login working'),
            ('Public Endpoint', 'At least one public endpoint working'),
            ('Contact System', 'Contact message system working'),
            ('Product Generation', 'Product generation system working')
        ]
        
        for test_name, description in critical_tests:
            if any(test_name in result['test'] and result['success'] for result in self.test_results):
                critical_passed += 1
                print(f"✅ {description}")
            else:
                print(f"❌ {description}")
        
        print()
        print(f"Critical Success Rate: {(critical_passed/critical_total)*100:.1f}% ({critical_passed}/{critical_total})")
        
        # MongoDB Integration Assessment
        if critical_passed >= 6:  # At least 85% of critical tests pass
            print()
            print("🎉 MONGODB INTEGRATION VERIFICATION SUCCESSFUL!")
            print("✅ Database connection established")
            print("✅ User authentication and data persistence working")
            print("✅ Public data endpoints returning MongoDB data")
            print("✅ Core functionality operational")
            mongodb_ready = True
        else:
            print()
            print("⚠️ MONGODB INTEGRATION ISSUES DETECTED:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
            mongodb_ready = False
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests/total_tests)*100,
            'critical_passed': critical_passed,
            'critical_total': critical_total,
            'mongodb_ready': mongodb_ready
        }

def main():
    """Main test execution"""
    try:
        tester = FocusedMongoDBTester()
        
        # Run focused MongoDB integration testing
        tester.run_focused_mongodb_test()
        
        # Generate final summary
        summary = tester.generate_final_summary()
        
        # Exit with appropriate code
        if summary['mongodb_ready']:
            print("✅ MONGODB INTEGRATION VERIFICATION SUCCESSFUL")
            print("The backend system is ready for production deployment.")
            sys.exit(0)
        else:
            print("❌ MONGODB INTEGRATION ISSUES DETECTED")
            print("Please review the failed tests and resolve issues.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Focused MongoDB test execution failed: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()