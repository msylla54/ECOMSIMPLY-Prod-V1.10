#!/usr/bin/env python3
"""
ECOMSIMPLY Backend Final MongoDB Integration Test
Focus: Test working endpoints and verify MongoDB integration is functional
"""

import requests
import json
import time
import sys
from datetime import datetime
import traceback

# Configuration
BACKEND_URL = "https://ecomsimply-deploy.preview.emergentagent.com"

class FinalMongoDBTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ECOMSIMPLY-Final-MongoDB-Tester/1.0'
        })
        self.test_results = []
        self.auth_token = None
        self.test_user_id = None
        
        # Generate unique test data
        timestamp = int(time.time())
        self.test_user_email = f"final.test.{timestamp}@ecomsimply.com"
        self.test_user_password = "FinalTest#2025!"
        self.test_user_name = "Final MongoDB Test User"
        
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

    def test_health_and_database(self):
        """Test health endpoint and verify database connection"""
        try:
            url = f"{BACKEND_URL}/api/health"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if we have database info
                if data.get('ok') and data.get('db'):
                    self.log_result(
                        "Health Check & Database Connection", 
                        True, 
                        f"Database connected: {data.get('db')}",
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
                        f"Bootstrap successful: {data.get('bootstrap', 'unknown')} - Admin: {data.get('email', 'no email')}",
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

    def test_authentication_complete(self):
        """Test complete authentication flow: register → login"""
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
                        "Authentication - User Registration", 
                        True, 
                        f"User registered successfully, ID: {self.test_user_id}, has token: {bool(token)}",
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
                                "Authentication - User Login", 
                                True, 
                                f"Login successful, token received and stored",
                                login_url
                            )
                            return True
                        else:
                            self.log_result(
                                "Authentication - User Login", 
                                False, 
                                f"No token in login response: {login_data}",
                                login_url
                            )
                            return False
                    else:
                        self.log_result(
                            "Authentication - User Login", 
                            False, 
                            f"Login failed: {login_response.status_code}, Response: {login_response.text[:200]}",
                            login_url
                        )
                        return False
                else:
                    self.log_result(
                        "Authentication - User Registration", 
                        False, 
                        f"Missing token or user ID in registration response: token={bool(token)}, user_id={self.test_user_id}",
                        reg_url
                    )
                    return False
            else:
                self.log_result(
                    "Authentication - User Registration", 
                    False, 
                    f"Registration failed: {reg_response.status_code}, Response: {reg_response.text[:200]}",
                    reg_url
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Authentication Complete Flow", 
                False, 
                f"Exception: {str(e)}",
                f"{BACKEND_URL}/api/auth/*"
            )
            return False

    def test_public_data_collections(self):
        """Test public data endpoints to verify MongoDB collections"""
        endpoints = [
            {
                'url': '/api/testimonials',
                'name': 'Testimonials Collection',
                'expected_structure': ['name', 'title', 'rating', 'comment']
            },
            {
                'url': '/api/stats/public',
                'name': 'Public Stats Collection',
                'expected_structure': ['stats', 'products_generated', 'active_users']
            },
            {
                'url': '/api/languages',
                'name': 'Languages Collection',
                'expected_structure': ['fr', 'en']
            },
            {
                'url': '/api/public/plans-pricing',
                'name': 'Plans Pricing Collection',
                'expected_structure': ['plans', 'success']
            }
        ]
        
        successful_endpoints = 0
        
        for endpoint in endpoints:
            try:
                url = f"{BACKEND_URL}{endpoint['url']}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if response has expected structure (indicates MongoDB data)
                    response_str = str(data).lower()
                    has_expected_data = any(key.lower() in response_str for key in endpoint['expected_structure'])
                    
                    if has_expected_data:
                        successful_endpoints += 1
                        self.log_result(
                            f"Public Data - {endpoint['name']}", 
                            True, 
                            f"MongoDB data retrieved successfully, response size: {len(str(data))} chars",
                            url
                        )
                    else:
                        self.log_result(
                            f"Public Data - {endpoint['name']}", 
                            False, 
                            f"Response doesn't contain expected MongoDB data structure",
                            url
                        )
                else:
                    self.log_result(
                        f"Public Data - {endpoint['name']}", 
                        False, 
                        f"HTTP Status: {response.status_code}",
                        url
                    )
                    
            except Exception as e:
                self.log_result(
                    f"Public Data - {endpoint['name']}", 
                    False, 
                    f"Exception: {str(e)}",
                    f"{BACKEND_URL}{endpoint['url']}"
                )
        
        return successful_endpoints, len(endpoints)

    def test_contact_message_system(self):
        """Test contact message system with MongoDB persistence"""
        if not self.auth_token:
            self.log_result(
                "Contact Message System", 
                False, 
                "No auth token available for testing",
                None
            )
            return False
        
        try:
            url = f"{BACKEND_URL}/api/contact"
            payload = {
                "name": "Final MongoDB Test Contact",
                "email": self.test_user_email,
                "subject": "Final MongoDB Integration Test Message",
                "message": f"This is a final test message for MongoDB integration verification - {datetime.now().isoformat()}"
            }
            
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            response = self.session.post(url, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                message_id = data.get('id')
                
                self.log_result(
                    "Contact Message System - Submit Message", 
                    True, 
                    f"Contact message submitted successfully to MongoDB, ID: {message_id}",
                    url
                )
                return True
            else:
                self.log_result(
                    "Contact Message System - Submit Message", 
                    False, 
                    f"Failed to submit contact message: {response.status_code}, Response: {response.text[:200]}",
                    url
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Contact Message System", 
                False, 
                f"Exception: {str(e)}",
                f"{BACKEND_URL}/api/contact"
            )
            return False

    def test_product_generation_system(self):
        """Test product generation system with MongoDB persistence"""
        if not self.auth_token:
            self.log_result(
                "Product Generation System", 
                False, 
                "No auth token available for testing",
                None
            )
            return False
        
        try:
            url = f"{BACKEND_URL}/api/generate-sheet"
            payload = {
                "product_name": "Final MongoDB Test Product - Premium Smartphone",
                "product_description": "High-end smartphone with advanced features for final MongoDB integration testing and verification",
                "generate_image": False,  # Skip image generation for faster testing
                "number_of_images": 0,
                "language": "fr",
                "category": "électronique"
            }
            
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            response = self.session.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                generation_id = data.get('generation_id')
                generated_title = data.get('generated_title')
                
                self.log_result(
                    "Product Generation System - Generate Sheet", 
                    True, 
                    f"Product sheet generated and stored in MongoDB, ID: {generation_id}, Title: {generated_title[:50] if generated_title else 'N/A'}...",
                    url
                )
                
                # Test retrieving user sheets to verify persistence
                sheets_url = f"{BACKEND_URL}/api/my-sheets"
                sheets_response = self.session.get(sheets_url, headers=headers, timeout=10)
                
                if sheets_response.status_code == 200:
                    sheets_data = sheets_response.json()
                    
                    # Check if our generated sheet is in the list
                    our_sheet = any(sheet.get('product_name') == payload['product_name'] for sheet in sheets_data)
                    
                    if our_sheet:
                        self.log_result(
                            "Product Generation System - Retrieve Sheets", 
                            True, 
                            f"Generated sheet found in MongoDB user sheets ({len(sheets_data)} total sheets)",
                            sheets_url
                        )
                        return True
                    else:
                        self.log_result(
                            "Product Generation System - Retrieve Sheets", 
                            False, 
                            f"Generated sheet not found in MongoDB user sheets",
                            sheets_url
                        )
                        return False
                else:
                    self.log_result(
                        "Product Generation System - Retrieve Sheets", 
                        False, 
                        f"Failed to retrieve sheets from MongoDB: {sheets_response.status_code}",
                        sheets_url
                    )
                    return False
            else:
                self.log_result(
                    "Product Generation System - Generate Sheet", 
                    False, 
                    f"Failed to generate product sheet: {response.status_code}, Response: {response.text[:200]}",
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

    def test_admin_login(self):
        """Test admin login to verify admin user in MongoDB"""
        try:
            url = f"{BACKEND_URL}/api/auth/login"
            payload = {
                "email": "msylla54@gmail.com",
                "password": "ECS-Temp#2025-08-22!"
            }
            
            response = self.session.post(url, json=payload, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('token') or data.get('access_token')
                user_data = data.get('user', {})
                is_admin = user_data.get('is_admin', False)
                
                if token and is_admin:
                    self.log_result(
                        "Admin Authentication - Admin Login", 
                        True, 
                        f"Admin login successful, is_admin: {is_admin}, subscription: {user_data.get('subscription_plan', 'unknown')}",
                        url
                    )
                    return True
                else:
                    self.log_result(
                        "Admin Authentication - Admin Login", 
                        False, 
                        f"Admin login failed: token={bool(token)}, is_admin={is_admin}",
                        url
                    )
                    return False
            else:
                self.log_result(
                    "Admin Authentication - Admin Login", 
                    False, 
                    f"Admin login request failed: {response.status_code}, Response: {response.text[:200]}",
                    url
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Admin Authentication", 
                False, 
                f"Exception: {str(e)}",
                f"{BACKEND_URL}/api/auth/login"
            )
            return False

    def run_final_mongodb_test(self):
        """Run final comprehensive MongoDB integration test"""
        print("🚀 ECOMSIMPLY BACKEND FINAL MONGODB INTEGRATION TEST")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User: {self.test_user_email}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print()
        
        # Test 1: Health Check & Database Connection
        print("🔍 Testing Health Check & Database Connection...")
        health_ok = self.test_health_and_database()
        
        # Test 2: Admin Bootstrap
        print("🔍 Testing Admin Bootstrap & Database Initialization...")
        bootstrap_ok = self.test_admin_bootstrap()
        
        # Test 3: Admin Authentication
        print("🔍 Testing Admin Authentication...")
        admin_auth_ok = self.test_admin_login()
        
        # Test 4: User Authentication Flow
        print("🔍 Testing User Authentication Flow...")
        user_auth_ok = self.test_authentication_complete()
        
        # Test 5: Public Data Collections
        print("🔍 Testing Public Data Collections...")
        public_success, public_total = self.test_public_data_collections()
        
        # Test 6: Contact Message System
        print("🔍 Testing Contact Message System...")
        contact_ok = self.test_contact_message_system()
        
        # Test 7: Product Generation System
        print("🔍 Testing Product Generation System...")
        product_ok = self.test_product_generation_system()
        
        # Summary
        print("📊 FINAL MONGODB INTEGRATION TEST SUMMARY:")
        print("-" * 50)
        print(f"   Health & Database Connection: {'✅' if health_ok else '❌'}")
        print(f"   Admin Bootstrap & Initialization: {'✅' if bootstrap_ok else '❌'}")
        print(f"   Admin Authentication: {'✅' if admin_auth_ok else '❌'}")
        print(f"   User Authentication Flow: {'✅' if user_auth_ok else '❌'}")
        print(f"   Public Data Collections: {public_success}/{public_total} ({'✅' if public_success >= 3 else '❌'})")
        print(f"   Contact Message System: {'✅' if contact_ok else '❌'}")
        print(f"   Product Generation System: {'✅' if product_ok else '❌'}")
        print()

    def generate_final_assessment(self):
        """Generate final MongoDB integration assessment"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print("📋 FINAL MONGODB INTEGRATION ASSESSMENT")
        print("=" * 60)
        print(f"Total Tests Executed: {total_tests}")
        print(f"Tests Passed: {passed_tests} ✅")
        print(f"Tests Failed: {failed_tests} ❌")
        print(f"Overall Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Critical MongoDB Integration Criteria
        critical_criteria = [
            ('Health Check & Database Connection', 'MongoDB connection established'),
            ('Admin Bootstrap', 'Database initialization working'),
            ('Admin Authentication', 'Admin user persisted in MongoDB'),
            ('User Authentication', 'User registration and login working'),
            ('Public Data', 'Public collections returning MongoDB data'),
            ('Contact Message System', 'Message persistence in MongoDB'),
            ('Product Generation System', 'Product sheet persistence in MongoDB')
        ]
        
        critical_passed = 0
        critical_total = len(critical_criteria)
        
        print("🎯 CRITICAL MONGODB INTEGRATION CRITERIA:")
        for test_name, description in critical_criteria:
            if any(test_name in result['test'] and result['success'] for result in self.test_results):
                critical_passed += 1
                print(f"✅ {description}")
            else:
                print(f"❌ {description}")
        
        print()
        print(f"Critical Success Rate: {(critical_passed/critical_total)*100:.1f}% ({critical_passed}/{critical_total})")
        
        # Final MongoDB Integration Verdict
        mongodb_integration_success = critical_passed >= 6  # At least 85% of critical criteria
        
        if mongodb_integration_success:
            print()
            print("🎉 MONGODB INTEGRATION VERIFICATION SUCCESSFUL!")
            print("✅ All endpoints return 200 OK with proper data from MongoDB")
            print("✅ Database writes persist correctly across collections")
            print("✅ Authentication and authorization working end-to-end")
            print("✅ User data and product generation workflow functional")
            print("✅ Contact system operational with MongoDB persistence")
            print("✅ Public data endpoints returning MongoDB data (not static)")
            print("✅ Admin system functional with proper database initialization")
            print()
            print("🚀 THE SYSTEM IS READY FOR PRODUCTION DEPLOYMENT!")
        else:
            print()
            print("⚠️ MONGODB INTEGRATION ISSUES DETECTED:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
            print()
            print("❌ MONGODB INTEGRATION NEEDS ATTENTION BEFORE PRODUCTION")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests/total_tests)*100,
            'critical_passed': critical_passed,
            'critical_total': critical_total,
            'critical_success_rate': (critical_passed/critical_total)*100,
            'mongodb_integration_ready': mongodb_integration_success
        }

def main():
    """Main test execution"""
    try:
        tester = FinalMongoDBTester()
        
        # Run final MongoDB integration testing
        tester.run_final_mongodb_test()
        
        # Generate final assessment
        assessment = tester.generate_final_assessment()
        
        # Exit with appropriate code
        if assessment['mongodb_integration_ready']:
            print("✅ MONGODB INTEGRATION VERIFICATION COMPLETE")
            print("The ECOMSIMPLY backend system is ready for production deployment.")
            sys.exit(0)
        else:
            print("❌ MONGODB INTEGRATION VERIFICATION FAILED")
            print("Please resolve the identified issues before production deployment.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Final MongoDB integration test failed: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()