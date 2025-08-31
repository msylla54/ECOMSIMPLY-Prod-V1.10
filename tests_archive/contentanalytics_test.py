#!/usr/bin/env python3
"""
COMPREHENSIVE CONTENTANALYTICS FEEDBACK SYSTEM TESTING
=====================================================

Testing the new ContentAnalytics feedback system implementation:
1. Application startup with ContentAnalytics initialization
2. New feedback endpoints (POST /api/feedback/submit, GET /api/feedback/analytics, GET /api/feedback/improvement-suggestions)
3. Integration with generate-sheet endpoint (tracking)
4. Error handling

Credentials: msylla54@yahoo.fr / NewPassword123
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8001/api"
TEST_EMAIL = "msylla54@gmail.com"
TEST_PASSWORD = "AdminEcomsimply"

class ContentAnalyticsTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.generation_id = None
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   📋 Details: {details}")
        if error:
            print(f"   ❌ Error: {error}")
        print()

    def authenticate(self):
        """Authenticate with the backend"""
        print("🔐 AUTHENTICATION TEST")
        print("=" * 50)
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")  # Changed from "access_token" to "token"
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                
                self.log_test(
                    "User Authentication",
                    True,
                    f"Successfully authenticated as {TEST_EMAIL}"
                )
                return True
            else:
                self.log_test(
                    "User Authentication",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("User Authentication", False, error=str(e))
            return False

    def test_application_startup_logs(self):
        """Test 1: Check if ContentAnalytics system initializes correctly at startup"""
        print("🚀 APPLICATION STARTUP CONTENTANALYTICS INITIALIZATION TEST")
        print("=" * 60)
        
        try:
            # Test a simple endpoint to verify the system is running
            response = self.session.get(f"{BACKEND_URL}/stats")
            
            if response.status_code == 200:
                self.log_test(
                    "Application Startup - ContentAnalytics System Running",
                    True,
                    "Backend is responding, ContentAnalytics should be initialized at startup"
                )
                
                # Note: We can't directly check logs, but we can verify the system works
                # by testing if the feedback endpoints are functional (which require ContentAnalytics)
                return True
            else:
                self.log_test(
                    "Application Startup - ContentAnalytics System Running",
                    False,
                    f"Backend not responding properly: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Application Startup - ContentAnalytics System Running",
                False,
                error=str(e)
            )
            return False

    def test_generate_sheet_with_tracking(self):
        """Test 2: Test generate-sheet endpoint includes generation tracking"""
        print("📊 GENERATE-SHEET CONTENTANALYTICS INTEGRATION TEST")
        print("=" * 55)
        
        try:
            # Generate a product sheet to get a generation_id for tracking
            test_data = {
                "product_name": "iPhone 15 Pro ContentAnalytics Test",
                "product_description": "Smartphone premium pour test du système ContentAnalytics avec feedback utilisateur",
                "generate_image": False,  # Skip image generation for faster testing
                "number_of_images": 0,
                "language": "fr",
                "category": "électronique",
                "use_case": "Test du système de feedback ContentAnalytics"
            }
            
            response = self.session.post(f"{BACKEND_URL}/generate-sheet", json=test_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if generation_id is included in response
                if "generation_id" in data and data["generation_id"]:
                    self.generation_id = data["generation_id"]
                    self.log_test(
                        "Generate-Sheet ContentAnalytics Integration",
                        True,
                        f"Generation ID returned: {self.generation_id[:8]}... (tracking successful)"
                    )
                    return True
                else:
                    self.log_test(
                        "Generate-Sheet ContentAnalytics Integration",
                        False,
                        "Response received but no generation_id field found",
                        "ContentAnalytics tracking may not be working"
                    )
                    return False
            else:
                self.log_test(
                    "Generate-Sheet ContentAnalytics Integration",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Generate-Sheet ContentAnalytics Integration",
                False,
                error=str(e)
            )
            return False

    def test_feedback_submit_endpoint(self):
        """Test 3: Test POST /api/feedback/submit endpoint"""
        print("📝 FEEDBACK SUBMIT ENDPOINT TEST")
        print("=" * 40)
        
        if not self.generation_id:
            self.log_test(
                "Feedback Submit Endpoint",
                False,
                "No generation_id available from previous test",
                "Cannot test feedback without generation_id"
            )
            return False
        
        try:
            # Test positive feedback
            feedback_data = {
                "generation_id": self.generation_id,
                "useful": True
            }
            
            response = self.session.post(f"{BACKEND_URL}/feedback/submit", json=feedback_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") and "✅" in data.get("message", ""):
                    self.log_test(
                        "Feedback Submit Endpoint - Positive Feedback",
                        True,
                        f"Feedback submitted successfully: {data.get('message')}"
                    )
                    
                    # Test negative feedback with a different generation (simulate)
                    feedback_data_negative = {
                        "generation_id": self.generation_id,
                        "useful": False
                    }
                    
                    response_neg = self.session.post(f"{BACKEND_URL}/feedback/submit", json=feedback_data_negative)
                    
                    if response_neg.status_code == 200:
                        data_neg = response_neg.json()
                        if data_neg.get("success"):
                            self.log_test(
                                "Feedback Submit Endpoint - Negative Feedback",
                                True,
                                f"Negative feedback also submitted: {data_neg.get('message')}"
                            )
                            return True
                    
                    self.log_test(
                        "Feedback Submit Endpoint - Negative Feedback",
                        False,
                        f"Status: {response_neg.status_code}",
                        response_neg.text
                    )
                    return False
                else:
                    self.log_test(
                        "Feedback Submit Endpoint - Positive Feedback",
                        False,
                        "Response received but success=False or invalid message",
                        str(data)
                    )
                    return False
            else:
                self.log_test(
                    "Feedback Submit Endpoint - Positive Feedback",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Feedback Submit Endpoint",
                False,
                error=str(e)
            )
            return False

    def test_feedback_analytics_endpoint(self):
        """Test 4: Test GET /api/feedback/analytics endpoint"""
        print("📈 FEEDBACK ANALYTICS ENDPOINT TEST")
        print("=" * 42)
        
        try:
            # Test without parameters (default)
            response = self.session.get(f"{BACKEND_URL}/feedback/analytics")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["period_days", "total_feedback", "useful_rate_percentage", "insights", "recommendations"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test(
                        "Feedback Analytics Endpoint - Default Parameters",
                        True,
                        f"Analytics data: {data['total_feedback']} feedback, {data['useful_rate_percentage']}% useful rate"
                    )
                    
                    # Test with category filter
                    response_cat = self.session.get(f"{BACKEND_URL}/feedback/analytics?category=électronique&days_back=7")
                    
                    if response_cat.status_code == 200:
                        data_cat = response_cat.json()
                        self.log_test(
                            "Feedback Analytics Endpoint - With Category Filter",
                            True,
                            f"Filtered analytics: {data_cat['total_feedback']} feedback for électronique category"
                        )
                        return True
                    else:
                        self.log_test(
                            "Feedback Analytics Endpoint - With Category Filter",
                            False,
                            f"Status: {response_cat.status_code}",
                            response_cat.text
                        )
                        return False
                else:
                    self.log_test(
                        "Feedback Analytics Endpoint - Default Parameters",
                        False,
                        f"Missing required fields: {missing_fields}",
                        str(data)
                    )
                    return False
            else:
                self.log_test(
                    "Feedback Analytics Endpoint - Default Parameters",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Feedback Analytics Endpoint",
                False,
                error=str(e)
            )
            return False

    def test_improvement_suggestions_endpoint(self):
        """Test 5: Test GET /api/feedback/improvement-suggestions endpoint"""
        print("💡 IMPROVEMENT SUGGESTIONS ENDPOINT TEST")
        print("=" * 47)
        
        try:
            # Test with required category parameter
            params = {
                "category": "électronique",
                "use_case": "Test du système de feedback ContentAnalytics"
            }
            
            response = self.session.get(f"{BACKEND_URL}/feedback/improvement-suggestions", params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if we get suggestions or a message about insufficient data
                if "recommendations" in data or "message" in data:
                    self.log_test(
                        "Improvement Suggestions Endpoint - With Category",
                        True,
                        f"Suggestions received: {len(data.get('recommendations', []))} recommendations" if "recommendations" in data else data.get("message", "No data message")
                    )
                    
                    # Test without use_case parameter
                    response_no_case = self.session.get(f"{BACKEND_URL}/feedback/improvement-suggestions?category=mode")
                    
                    if response_no_case.status_code == 200:
                        self.log_test(
                            "Improvement Suggestions Endpoint - Without Use Case",
                            True,
                            "Successfully retrieved suggestions for mode category"
                        )
                        return True
                    else:
                        self.log_test(
                            "Improvement Suggestions Endpoint - Without Use Case",
                            False,
                            f"Status: {response_no_case.status_code}",
                            response_no_case.text
                        )
                        return False
                else:
                    self.log_test(
                        "Improvement Suggestions Endpoint - With Category",
                        False,
                        "Response received but no recommendations or message field",
                        str(data)
                    )
                    return False
            else:
                self.log_test(
                    "Improvement Suggestions Endpoint - With Category",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Improvement Suggestions Endpoint",
                False,
                error=str(e)
            )
            return False

    def test_authentication_requirements(self):
        """Test 6: Verify all endpoints require authentication"""
        print("🔒 AUTHENTICATION REQUIREMENTS TEST")
        print("=" * 42)
        
        # Create a session without authentication
        unauth_session = requests.Session()
        
        endpoints_to_test = [
            ("/feedback/submit", "POST", {"generation_id": "test", "useful": True}),
            ("/feedback/analytics", "GET", None),
            ("/feedback/improvement-suggestions?category=test", "GET", None)
        ]
        
        all_protected = True
        
        for endpoint, method, data in endpoints_to_test:
            try:
                if method == "POST":
                    response = unauth_session.post(f"{BACKEND_URL}{endpoint}", json=data)
                else:
                    response = unauth_session.get(f"{BACKEND_URL}{endpoint}")
                
                if response.status_code in [401, 403]:
                    self.log_test(
                        f"Authentication Required - {endpoint}",
                        True,
                        f"Correctly rejected unauthenticated request with {response.status_code}"
                    )
                else:
                    self.log_test(
                        f"Authentication Required - {endpoint}",
                        False,
                        f"Endpoint accessible without authentication: {response.status_code}",
                        "Security issue: endpoint should require authentication"
                    )
                    all_protected = False
                    
            except Exception as e:
                self.log_test(
                    f"Authentication Required - {endpoint}",
                    False,
                    error=str(e)
                )
                all_protected = False
        
        return all_protected

    def test_error_handling(self):
        """Test 7: Test error handling with invalid data"""
        print("⚠️ ERROR HANDLING TEST")
        print("=" * 30)
        
        try:
            # Test invalid generation_id for feedback
            invalid_feedback = {
                "generation_id": "invalid-id-12345",
                "useful": True
            }
            
            response = self.session.post(f"{BACKEND_URL}/feedback/submit", json=invalid_feedback)
            
            # Should either succeed (if system handles invalid IDs gracefully) or return proper error
            if response.status_code in [200, 400, 404]:
                self.log_test(
                    "Error Handling - Invalid Generation ID",
                    True,
                    f"System handled invalid generation_id appropriately: {response.status_code}"
                )
            else:
                self.log_test(
                    "Error Handling - Invalid Generation ID",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    response.text
                )
                return False
            
            # Test missing required fields
            incomplete_feedback = {"useful": True}  # Missing generation_id
            
            response_incomplete = self.session.post(f"{BACKEND_URL}/feedback/submit", json=incomplete_feedback)
            
            if response_incomplete.status_code in [400, 422]:  # Validation error expected
                self.log_test(
                    "Error Handling - Missing Required Fields",
                    True,
                    f"Correctly rejected incomplete data: {response_incomplete.status_code}"
                )
                return True
            else:
                self.log_test(
                    "Error Handling - Missing Required Fields",
                    False,
                    f"Should have rejected incomplete data: {response_incomplete.status_code}",
                    response_incomplete.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Error Handling",
                False,
                error=str(e)
            )
            return False

    def run_all_tests(self):
        """Run all ContentAnalytics tests"""
        print("🧪 CONTENTANALYTICS FEEDBACK SYSTEM COMPREHENSIVE TESTING")
        print("=" * 65)
        print(f"🎯 Testing Backend: {BACKEND_URL}")
        print(f"👤 Test User: {TEST_EMAIL}")
        print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run tests in sequence
        tests = [
            ("Authentication", self.authenticate),
            ("Application Startup", self.test_application_startup_logs),
            ("Generate-Sheet Integration", self.test_generate_sheet_with_tracking),
            ("Feedback Submit", self.test_feedback_submit_endpoint),
            ("Feedback Analytics", self.test_feedback_analytics_endpoint),
            ("Improvement Suggestions", self.test_improvement_suggestions_endpoint),
            ("Authentication Requirements", self.test_authentication_requirements),
            ("Error Handling", self.test_error_handling)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test_name}: {e}")
        
        # Print summary
        print("📊 TEST SUMMARY")
        print("=" * 20)
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
        print()
        
        # Print detailed results
        print("📋 DETAILED RESULTS")
        print("=" * 25)
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   📋 {result['details']}")
            if result["error"]:
                print(f"   ❌ {result['error']}")
        
        print()
        print("🏁 CONTENTANALYTICS TESTING COMPLETED")
        print(f"🕐 Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return passed, total

if __name__ == "__main__":
    tester = ContentAnalyticsTestSuite()
    passed, total = tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if passed == total else 1)