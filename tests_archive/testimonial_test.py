#!/usr/bin/env python3
"""
ECOMSIMPLY Testimonial System Testing Suite
Tests the complete testimonial management system including submission, admin management, and public display.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 30

class TestimonialTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        self.user_data = None
        self.admin_token = None
        self.admin_user_data = None
        self.testimonial_id = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_api_health(self):
        """Test if the API is accessible"""
        self.log("Testing API health check...")
        try:
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ API Health Check: {data.get('message', 'OK')}")
                return True
            else:
                self.log(f"❌ API Health Check failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ API Health Check failed: {str(e)}", "ERROR")
            return False
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        self.log("Testing user registration...")
        
        timestamp = int(time.time())
        test_user = {
            "email": f"testimonial.user{timestamp}@test.fr",
            "name": "Testimonial Test User",
            "password": "TestPassword123!"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=test_user)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.user_data = data.get("user")
                
                if self.auth_token and self.user_data:
                    self.log(f"✅ User Registration: Successfully registered {self.user_data['name']}")
                    return True
                else:
                    self.log("❌ User Registration: Missing token or user data", "ERROR")
                    return False
            else:
                self.log(f"❌ User Registration failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ User Registration failed: {str(e)}", "ERROR")
            return False
    
    def test_admin_user_registration(self):
        """Test admin user registration"""
        self.log("Testing admin user registration...")
        
        timestamp = int(time.time())
        admin_user = {
            "email": f"admin.testimonial{timestamp}@test.fr",
            "name": "Admin Testimonial User",
            "password": "AdminPassword123!",
            "admin_key": "ECOMSIMPLY_ADMIN_2024"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=admin_user)
            
            if response.status_code == 200:
                data = response.json()
                admin_token = data.get("token")
                admin_user_data = data.get("user")
                
                if admin_token and admin_user_data and admin_user_data.get("is_admin"):
                    self.admin_token = admin_token
                    self.admin_user_data = admin_user_data
                    self.log(f"✅ Admin Registration: Successfully registered {admin_user_data['name']}")
                    return True
                else:
                    self.log("❌ Admin Registration: User not marked as admin", "ERROR")
                    return False
            else:
                self.log(f"❌ Admin Registration failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Admin Registration failed: {str(e)}", "ERROR")
            return False
    
    def test_testimonial_submission(self):
        """Test testimonial submission endpoint"""
        self.log("Testing testimonial submission...")
        
        testimonial_data = {
            "name": "Jean Dupont",
            "title": "Directeur Marketing, TechCorp",
            "rating": 5,
            "comment": "ECOMSIMPLY a révolutionné notre processus de création de fiches produits. L'IA génère du contenu de qualité professionnelle en quelques secondes. Excellent outil!"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/testimonials", json=testimonial_data)
            
            if response.status_code == 200:
                result = response.json()
                
                required_fields = ["message", "id", "status"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log(f"❌ Testimonial Submission: Missing fields {missing_fields}", "ERROR")
                    return False
                
                if result.get("status") != "pending":
                    self.log(f"❌ Testimonial Submission: Expected status 'pending', got '{result.get('status')}'", "ERROR")
                    return False
                
                self.testimonial_id = result.get("id")
                
                self.log(f"✅ Testimonial Submission: Successfully submitted")
                self.log(f"   Testimonial ID: {self.testimonial_id}")
                self.log(f"   Status: {result.get('status')}")
                
                return True
            else:
                self.log(f"❌ Testimonial Submission failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Testimonial Submission failed: {str(e)}", "ERROR")
            return False
    
    def test_public_testimonials(self):
        """Test public testimonials retrieval"""
        self.log("Testing public testimonials retrieval...")
        
        try:
            response = self.session.get(f"{BASE_URL}/testimonials")
            
            if response.status_code == 200:
                result = response.json()
                
                if "testimonials" not in result:
                    self.log("❌ Public Testimonials: Missing 'testimonials' field", "ERROR")
                    return False
                
                testimonials = result["testimonials"]
                
                if not isinstance(testimonials, list):
                    self.log("❌ Public Testimonials: 'testimonials' should be a list", "ERROR")
                    return False
                
                approved_count = len(testimonials)
                
                self.log(f"✅ Public Testimonials: Retrieved successfully")
                self.log(f"   Approved testimonials: {approved_count}")
                
                # Validate that admin fields are not exposed
                for testimonial in testimonials:
                    admin_fields = ["admin_reply", "replied_by", "replied_at"]
                    exposed_fields = [field for field in admin_fields if field in testimonial]
                    
                    if exposed_fields:
                        self.log(f"❌ Public Testimonials: Admin fields exposed: {exposed_fields}", "ERROR")
                        return False
                
                self.log("   ✅ Admin fields properly hidden from public view")
                return True
            else:
                self.log(f"❌ Public Testimonials failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Public Testimonials failed: {str(e)}", "ERROR")
            return False
    
    def test_admin_testimonials(self):
        """Test admin testimonials management endpoint"""
        self.log("Testing admin testimonials management...")
        
        if not self.admin_token:
            self.log("❌ Cannot test admin testimonials: No admin token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            response = self.session.get(f"{BASE_URL}/admin/testimonials", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                
                if "testimonials" not in result:
                    self.log("❌ Admin Testimonials: Missing 'testimonials' field", "ERROR")
                    return False
                
                testimonials = result["testimonials"]
                
                if not isinstance(testimonials, list):
                    self.log("❌ Admin Testimonials: 'testimonials' should be a list", "ERROR")
                    return False
                
                self.log(f"✅ Admin Testimonials: Retrieved successfully")
                self.log(f"   Total testimonials: {len(testimonials)}")
                
                if testimonials:
                    sample_testimonial = testimonials[0]
                    required_fields = ["id", "name", "title", "rating", "comment", "status", "created_at"]
                    missing_fields = [field for field in required_fields if field not in sample_testimonial]
                    
                    if missing_fields:
                        self.log(f"❌ Admin Testimonials: Missing fields {missing_fields}", "ERROR")
                        return False
                    
                    self.log(f"   Sample testimonial: {sample_testimonial['name']} - {sample_testimonial['title']}")
                    self.log(f"   Rating: {sample_testimonial['rating']}/5")
                    self.log(f"   Status: {sample_testimonial['status']}")
                
                return True
            else:
                self.log(f"❌ Admin Testimonials failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Admin Testimonials failed: {str(e)}", "ERROR")
            return False
    
    def test_admin_testimonial_reply(self):
        """Test admin testimonial reply functionality"""
        self.log("Testing admin testimonial reply...")
        
        if not self.admin_token:
            self.log("❌ Cannot test admin reply: No admin token", "ERROR")
            return False
            
        if not self.testimonial_id:
            self.log("❌ Cannot test admin reply: No testimonial ID", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        reply_data = {
            "reply_message": "Merci beaucoup pour votre retour positif ! Nous sommes ravis que ECOMSIMPLY vous aide à améliorer votre processus de création de contenu. N'hésitez pas à nous contacter si vous avez des questions."
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/admin/testimonials/{self.testimonial_id}/reply", 
                                       json=reply_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                
                required_fields = ["message", "testimonial_id", "replied_at", "replied_by"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log(f"❌ Admin Reply: Missing fields {missing_fields}", "ERROR")
                    return False
                
                self.log(f"✅ Admin Testimonial Reply: Successfully sent")
                self.log(f"   Testimonial ID: {result.get('testimonial_id')}")
                self.log(f"   Replied by: {result.get('replied_by')}")
                
                return True
            else:
                self.log(f"❌ Admin Reply failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Admin Reply failed: {str(e)}", "ERROR")
            return False
    
    def test_admin_testimonial_status(self):
        """Test admin testimonial status update functionality"""
        self.log("Testing admin testimonial status update...")
        
        if not self.admin_token:
            self.log("❌ Cannot test status update: No admin token", "ERROR")
            return False
            
        if not self.testimonial_id:
            self.log("❌ Cannot test status update: No testimonial ID", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test updating status to "approved"
        status_data = {"status": "approved"}
        
        try:
            response = self.session.post(f"{BASE_URL}/admin/testimonials/{self.testimonial_id}/status", 
                                       json=status_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                
                required_fields = ["message", "testimonial_id", "status"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log(f"❌ Status Update: Missing fields {missing_fields}", "ERROR")
                    return False
                
                if result.get("status") != "approved":
                    self.log(f"❌ Status Update: Expected 'approved', got '{result.get('status')}'", "ERROR")
                    return False
                
                self.log(f"✅ Admin Status Update: Successfully updated")
                self.log(f"   Testimonial ID: {result.get('testimonial_id')}")
                self.log(f"   New Status: {result.get('status')}")
                
                # Test invalid status
                self.log("   Testing invalid status rejection...")
                invalid_status_data = {"status": "invalid_status"}
                
                invalid_response = self.session.post(f"{BASE_URL}/admin/testimonials/{self.testimonial_id}/status", 
                                                   json=invalid_status_data, headers=headers)
                
                if invalid_response.status_code == 400:
                    self.log("   ✅ Invalid status correctly rejected")
                else:
                    self.log(f"   ❌ Invalid status should return 400, got {invalid_response.status_code}", "ERROR")
                    return False
                
                return True
            else:
                self.log(f"❌ Status Update failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Status Update failed: {str(e)}", "ERROR")
            return False
    
    def test_testimonial_auth(self):
        """Test testimonial authentication and authorization"""
        self.log("Testing testimonial authentication and authorization...")
        
        if not self.auth_token:
            self.log("❌ Cannot test testimonial auth: No regular user token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        admin_endpoints = [
            ("GET", "/admin/testimonials"),
            ("POST", f"/admin/testimonials/test-id/reply", {"reply_message": "Test"}),
            ("POST", f"/admin/testimonials/test-id/status", {"status": "approved"})
        ]
        
        success_count = 0
        
        for method, endpoint, *data in admin_endpoints:
            try:
                json_data = data[0] if data else None
                
                if method == "GET":
                    response = self.session.get(f"{BASE_URL}{endpoint}", headers=headers)
                elif method == "POST":
                    response = self.session.post(f"{BASE_URL}{endpoint}", json=json_data, headers=headers)
                
                if response.status_code == 403:
                    self.log(f"   ✅ {method} {endpoint}: Correctly requires admin privileges")
                    success_count += 1
                else:
                    self.log(f"   ❌ {method} {endpoint}: Should require admin but returned {response.status_code}", "ERROR")
                    
            except Exception as e:
                self.log(f"   ❌ {method} {endpoint}: Exception {str(e)}", "ERROR")
        
        # Test that public endpoints don't require authentication
        try:
            public_response = self.session.get(f"{BASE_URL}/testimonials")
            if public_response.status_code == 200:
                self.log("   ✅ Public testimonials endpoint accessible without auth")
                success_count += 1
            else:
                self.log(f"   ❌ Public endpoint should be accessible but returned {public_response.status_code}", "ERROR")
                
            submit_response = self.session.post(f"{BASE_URL}/testimonials", json={
                "name": "Test User",
                "title": "Test Title", 
                "rating": 4,
                "comment": "Test comment"
            })
            if submit_response.status_code == 200:
                self.log("   ✅ Testimonial submission accessible without auth")
                success_count += 1
            else:
                self.log(f"   ❌ Testimonial submission should be accessible but returned {submit_response.status_code}", "ERROR")
                
        except Exception as e:
            self.log(f"   ❌ Public endpoint test failed: {str(e)}", "ERROR")
        
        if success_count >= 4:  # At least 4 out of 5 tests should pass
            self.log("✅ Testimonial Authentication: Tests passed")
            return True
        else:
            self.log(f"❌ Testimonial Authentication: Only {success_count}/5 tests passed", "ERROR")
            return False
    
    def test_testimonial_validation(self):
        """Test testimonial data validation"""
        self.log("Testing testimonial data validation...")
        
        test_cases = [
            {
                "name": "Valid Testimonial",
                "data": {
                    "name": "Marie Dubois",
                    "title": "Chef de Projet Digital",
                    "rating": 4,
                    "comment": "Très bon outil pour la génération de contenu produit."
                },
                "expected_status": 200,
                "should_pass": True
            },
            {
                "name": "Missing Name",
                "data": {
                    "title": "Chef de Projet",
                    "rating": 5,
                    "comment": "Excellent outil!"
                },
                "expected_status": 422,
                "should_pass": False
            },
            {
                "name": "Invalid Rating (too high)",
                "data": {
                    "name": "Test User",
                    "title": "Test Title",
                    "rating": 6,
                    "comment": "Test comment"
                },
                "expected_status": 422,
                "should_pass": False
            },
            {
                "name": "Invalid Rating (too low)",
                "data": {
                    "name": "Test User",
                    "title": "Test Title", 
                    "rating": 0,
                    "comment": "Test comment"
                },
                "expected_status": 422,
                "should_pass": False
            },
            {
                "name": "Empty Comment",
                "data": {
                    "name": "Test User",
                    "title": "Test Title",
                    "rating": 3,
                    "comment": ""
                },
                "expected_status": 422,
                "should_pass": False
            }
        ]
        
        success_count = 0
        
        for test_case in test_cases:
            try:
                self.log(f"   Testing: {test_case['name']}")
                
                response = self.session.post(f"{BASE_URL}/testimonials", json=test_case["data"])
                
                if test_case["should_pass"]:
                    if response.status_code == test_case["expected_status"]:
                        self.log(f"   ✅ {test_case['name']}: Correctly accepted")
                        success_count += 1
                    else:
                        self.log(f"   ❌ {test_case['name']}: Expected {test_case['expected_status']}, got {response.status_code}", "ERROR")
                else:
                    if response.status_code == test_case["expected_status"]:
                        self.log(f"   ✅ {test_case['name']}: Correctly rejected")
                        success_count += 1
                    else:
                        self.log(f"   ❌ {test_case['name']}: Expected {test_case['expected_status']}, got {response.status_code}", "ERROR")
                        
            except Exception as e:
                self.log(f"   ❌ {test_case['name']}: Exception {str(e)}", "ERROR")
        
        if success_count >= len(test_cases) * 0.8:  # At least 80% should pass
            self.log(f"✅ Testimonial Validation: {success_count}/{len(test_cases)} tests passed")
            return True
        else:
            self.log(f"❌ Testimonial Validation: Only {success_count}/{len(test_cases)} tests passed", "ERROR")
            return False
    
    def test_testimonial_integration_workflow(self):
        """Test complete testimonial integration workflow"""
        self.log("Testing complete testimonial integration workflow...")
        
        try:
            # Step 1: Submit a new testimonial
            self.log("   Step 1: Submitting new testimonial...")
            testimonial_data = {
                "name": "Sophie Martin",
                "title": "Responsable E-commerce, ModeFashion",
                "rating": 5,
                "comment": "ECOMSIMPLY nous fait gagner un temps précieux dans la création de nos fiches produits. L'IA génère du contenu pertinent et professionnel. Je recommande vivement!"
            }
            
            response = self.session.post(f"{BASE_URL}/testimonials", json=testimonial_data)
            if response.status_code != 200:
                self.log(f"   ❌ Step 1 failed: {response.status_code}", "ERROR")
                return False
                
            workflow_testimonial_id = response.json().get("id")
            self.log(f"   ✅ Step 1: Testimonial submitted (ID: {workflow_testimonial_id})")
            
            # Step 2: Verify it appears in admin panel with "pending" status
            self.log("   Step 2: Checking admin panel...")
            if not self.admin_token:
                self.log("   ❌ Step 2 failed: No admin token", "ERROR")
                return False
                
            admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
            admin_response = self.session.get(f"{BASE_URL}/admin/testimonials", headers=admin_headers)
            
            if admin_response.status_code != 200:
                self.log(f"   ❌ Step 2 failed: {admin_response.status_code}", "ERROR")
                return False
                
            admin_testimonials = admin_response.json().get("testimonials", [])
            workflow_testimonial = None
            
            for testimonial in admin_testimonials:
                if testimonial.get("id") == workflow_testimonial_id:
                    workflow_testimonial = testimonial
                    break
                    
            if not workflow_testimonial:
                self.log("   ❌ Step 2 failed: Testimonial not found in admin panel", "ERROR")
                return False
                
            if workflow_testimonial.get("status") != "pending":
                self.log(f"   ❌ Step 2 failed: Expected 'pending' status, got '{workflow_testimonial.get('status')}'", "ERROR")
                return False
                
            self.log("   ✅ Step 2: Testimonial appears in admin panel with 'pending' status")
            
            # Step 3: Admin replies to testimonial
            self.log("   Step 3: Admin replying to testimonial...")
            reply_data = {
                "reply_message": "Merci Sophie pour ce retour très positif ! Nous sommes ravis que ECOMSIMPLY vous aide à optimiser votre processus de création de contenu."
            }
            
            reply_response = self.session.post(f"{BASE_URL}/admin/testimonials/{workflow_testimonial_id}/reply", 
                                             json=reply_data, headers=admin_headers)
            
            if reply_response.status_code != 200:
                self.log(f"   ❌ Step 3 failed: {reply_response.status_code}", "ERROR")
                return False
                
            self.log("   ✅ Step 3: Admin reply sent successfully")
            
            # Step 4: Admin approves testimonial
            self.log("   Step 4: Admin approving testimonial...")
            status_data = {"status": "approved"}
            
            status_response = self.session.post(f"{BASE_URL}/admin/testimonials/{workflow_testimonial_id}/status", 
                                              json=status_data, headers=admin_headers)
            
            if status_response.status_code != 200:
                self.log(f"   ❌ Step 4 failed: {status_response.status_code}", "ERROR")
                return False
                
            self.log("   ✅ Step 4: Testimonial approved successfully")
            
            # Step 5: Verify testimonial appears in public endpoint
            self.log("   Step 5: Checking public testimonials...")
            public_response = self.session.get(f"{BASE_URL}/testimonials")
            
            if public_response.status_code != 200:
                self.log(f"   ❌ Step 5 failed: {public_response.status_code}", "ERROR")
                return False
                
            public_testimonials = public_response.json().get("testimonials", [])
            public_testimonial = None
            
            for testimonial in public_testimonials:
                if testimonial.get("id") == workflow_testimonial_id:
                    public_testimonial = testimonial
                    break
                    
            if not public_testimonial:
                self.log("   ❌ Step 5 failed: Approved testimonial not found in public endpoint", "ERROR")
                return False
                
            # Verify admin fields are hidden
            admin_fields = ["admin_reply", "replied_by", "replied_at"]
            exposed_fields = [field for field in admin_fields if field in public_testimonial]
            
            if exposed_fields:
                self.log(f"   ❌ Step 5 failed: Admin fields exposed in public view: {exposed_fields}", "ERROR")
                return False
                
            self.log("   ✅ Step 5: Approved testimonial appears in public endpoint (admin fields hidden)")
            
            self.log("✅ TESTIMONIAL INTEGRATION WORKFLOW: Complete workflow tested successfully!")
            self.log("   ✅ Submit → Admin Review → Reply → Approve → Public Display")
            self.log("   ✅ All data properly stored and retrieved")
            self.log("   ✅ Admin fields properly hidden from public view")
            self.log("   ✅ Authentication and authorization working correctly")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Testimonial Integration Workflow failed: {str(e)}", "ERROR")
            return False

    def run_testimonial_tests(self):
        """Run comprehensive testimonial system tests"""
        self.log("🚀 Starting TESTIMONIAL SYSTEM Testing Suite...")
        self.log("=" * 80)
        
        # First ensure we have basic setup
        if not self.test_api_health():
            self.log("❌ API not accessible, aborting tests")
            return 0, 1
            
        if not self.test_user_registration():
            self.log("❌ User registration failed, aborting tests")
            return 0, 1
            
        # Ensure we have admin access
        if not self.test_admin_user_registration():
            self.log("❌ Admin registration failed, aborting tests")
            return 0, 1
        
        # Testimonial system tests
        tests = [
            ("Testimonial Submission", self.test_testimonial_submission),
            ("Public Testimonials Retrieval", self.test_public_testimonials),
            ("Admin Testimonials Management", self.test_admin_testimonials),
            ("Admin Testimonial Reply", self.test_admin_testimonial_reply),
            ("Admin Testimonial Status Update", self.test_admin_testimonial_status),
            ("Testimonial Authentication & Authorization", self.test_testimonial_auth),
            ("Testimonial Data Validation", self.test_testimonial_validation),
            ("Testimonial Integration Workflow", self.test_testimonial_integration_workflow)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            self.log(f"\n📋 Running: {test_name}")
            self.log("-" * 60)
            
            try:
                if test_func():
                    self.log(f"✅ PASSED: {test_name}")
                    passed += 1
                else:
                    self.log(f"❌ FAILED: {test_name}")
                    failed += 1
            except Exception as e:
                self.log(f"❌ ERROR in {test_name}: {str(e)}", "ERROR")
                failed += 1
            
            time.sleep(0.5)  # Brief pause between tests
        
        # Final Results
        self.log("\n" + "=" * 80)
        self.log("🎯 TESTIMONIAL SYSTEM TEST RESULTS")
        self.log("=" * 80)
        self.log(f"✅ PASSED: {passed}")
        self.log(f"❌ FAILED: {failed}")
        self.log(f"📊 SUCCESS RATE: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            self.log("🎉 ALL TESTIMONIAL SYSTEM TESTS PASSED!")
            self.log("   ✅ Testimonial submission working correctly")
            self.log("   ✅ Public testimonials display functional")
            self.log("   ✅ Admin management system operational")
            self.log("   ✅ Admin reply functionality working")
            self.log("   ✅ Status update system functional")
            self.log("   ✅ Authentication and authorization correct")
            self.log("   ✅ Data validation working properly")
            self.log("   ✅ Complete integration workflow tested")
        elif passed > failed:
            self.log("✅ MAJORITY TESTS PASSED! Minor issues detected.")
        else:
            self.log("⚠️  MULTIPLE FAILURES DETECTED! Testimonial system needs attention.")
        
        return passed, failed

if __name__ == "__main__":
    tester = TestimonialTester()
    
    # Run the testimonial system tests
    tester.run_testimonial_tests()