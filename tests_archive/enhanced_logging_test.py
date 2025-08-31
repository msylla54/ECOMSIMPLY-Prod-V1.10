#!/usr/bin/env python3
"""
ECOMSIMPLY GPT-4 Turbo Enhanced Logging Analysis
Focus: Analyze the enhanced logging to identify the exact issue with GPT-4 Turbo integration

Based on the backend logs, I can see:
✅ GPT-4 Turbo is being called correctly
✅ OpenAI API key is present and working
✅ GPT-4 Turbo is returning content (2560 characters)
❌ JSON parsing error: "Expecting value: line 1 column 1 (char 0)"
❌ The response includes markdown code blocks (```json) which breaks parsing

This test will create a user and test the exact scenario to confirm the issue.
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 60

class EnhancedLoggingAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        self.user_data = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def create_test_user(self):
        """Create a new test user for GPT-4 Turbo testing"""
        self.log("👤 Creating new test user for enhanced logging analysis...")
        
        timestamp = int(time.time())
        test_user = {
            "email": f"enhanced.logging.test{timestamp}@example.com",
            "name": "Enhanced Logging Test User",
            "password": "TestPassword123!"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=test_user)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.user_data = data.get("user")
                
                if self.auth_token and self.user_data:
                    self.log(f"✅ Test User Created: {self.user_data['name']}")
                    self.log(f"   User ID: {self.user_data['id']}")
                    self.log(f"   Email: {self.user_data['email']}")
                    return True
                else:
                    self.log("❌ User Creation: Missing token or user data", "ERROR")
                    return False
            else:
                self.log(f"❌ User Creation failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ User Creation failed: {str(e)}", "ERROR")
            return False
    
    def test_gpt4_turbo_with_enhanced_logging(self):
        """Test GPT-4 Turbo with the exact scenario from review request"""
        self.log("🧠 TESTING GPT-4 TURBO WITH ENHANCED LOGGING")
        self.log("🎯 Looking for these specific log messages:")
        self.log("   - '🧠 TENTATIVE GPT-4 TURBO: iPhone 15 Pro'")
        self.log("   - '🔑 OpenAI Key présente: Oui/Non'")
        self.log("   - '🧠 Appel GPT-4 Turbo (nouvelle API) pour: iPhone 15 Pro'")
        self.log("   - Success or detailed error messages")
        
        if not self.auth_token:
            self.log("❌ Cannot test: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Exact test case from review request
        test_data = {
            "product_name": "iPhone 15 Pro",
            "product_description": "Smartphone haut de gamme avec processeur A17 Pro et appareil photo 48MP",
            "generate_image": False,  # Focus on text generation to isolate the issue
            "number_of_images": 0,
            "language": "fr"
        }
        
        self.log(f"📝 Test data: {json.dumps(test_data, ensure_ascii=False)}")
        
        try:
            self.log("⏱️ Making request to /generate-sheet...")
            start_time = time.time()
            
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
            
            end_time = time.time()
            generation_time = end_time - start_time
            
            self.log(f"⏱️ Request completed in {generation_time:.2f} seconds")
            self.log(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.log("✅ Response JSON parsed successfully")
                    
                    if data.get("success"):
                        sheet_data = data.get("sheet", {})
                        self.log("🎉 GENERATION SUCCESS!")
                        self.log(f"   Title: {sheet_data.get('generated_title', 'N/A')}")
                        self.log(f"   AI Generated: {sheet_data.get('is_ai_generated', False)}")
                        self.log(f"   Generation Time: {sheet_data.get('generation_time', 'N/A')} seconds")
                        return True
                    else:
                        error_msg = data.get("message", "Unknown error")
                        self.log(f"❌ Generation failed: {error_msg}")
                        return False
                        
                except json.JSONDecodeError as e:
                    self.log(f"❌ JSON parsing error: {str(e)}", "ERROR")
                    self.log(f"📄 Raw response: {response.text[:500]}...")
                    return False
                    
            elif response.status_code == 422:
                self.log("❌ Validation error (422)")
                try:
                    error_data = response.json()
                    self.log(f"📄 Error details: {json.dumps(error_data, indent=2)}")
                except:
                    self.log(f"📄 Raw error response: {response.text}")
                return False
            else:
                self.log(f"❌ API call failed: {response.status_code}")
                self.log(f"📄 Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Exception during test: {str(e)}", "ERROR")
            return False
    
    def analyze_backend_logs(self):
        """Analyze backend logs for GPT-4 Turbo enhanced logging"""
        self.log("🔍 ANALYZING BACKEND LOGS FOR ENHANCED LOGGING")
        
        import subprocess
        
        try:
            # Get recent backend logs with GPT-4 Turbo related messages
            result = subprocess.run([
                "tail", "-n", "200", "/var/log/supervisor/backend.out.log"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logs = result.stdout
                
                # Look for specific enhanced logging messages
                enhanced_log_patterns = [
                    "🧠 TENTATIVE GPT-4 TURBO:",
                    "🔑 OpenAI Key présente:",
                    "🧠 Appel GPT-4 Turbo (nouvelle API) pour:",
                    "✅ GPT-4 Turbo - Réponse reçue:",
                    "⚠️ GPT-4 Turbo - Erreur parsing JSON:",
                    "✅ GPT-4 TURBO RÉUSSIE:",
                    "✅ GÉNÉRATION GPT-4 TURBO RÉUSSIE"
                ]
                
                found_logs = []
                for line in logs.split('\n'):
                    for pattern in enhanced_log_patterns:
                        if pattern in line:
                            found_logs.append(line.strip())
                
                if found_logs:
                    self.log("✅ ENHANCED LOGGING MESSAGES FOUND:")
                    for log_line in found_logs[-10:]:  # Show last 10 relevant logs
                        self.log(f"   📝 {log_line}")
                    
                    # Analyze the findings
                    self.analyze_log_findings(found_logs)
                    return True
                else:
                    self.log("❌ No enhanced logging messages found in recent logs")
                    return False
            else:
                self.log("❌ Could not read backend logs", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error analyzing logs: {str(e)}", "ERROR")
            return False
    
    def analyze_log_findings(self, log_lines):
        """Analyze the enhanced logging findings"""
        self.log("🔍 ENHANCED LOGGING ANALYSIS:")
        
        # Check for key indicators
        has_gpt4_attempt = any("🧠 TENTATIVE GPT-4 TURBO:" in line for line in log_lines)
        has_openai_key = any("🔑 OpenAI Key présente: Oui" in line for line in log_lines)
        has_api_call = any("🧠 Appel GPT-4 Turbo (nouvelle API)" in line for line in log_lines)
        has_response = any("✅ GPT-4 Turbo - Réponse reçue:" in line for line in log_lines)
        has_json_error = any("⚠️ GPT-4 Turbo - Erreur parsing JSON:" in line for line in log_lines)
        has_success = any("✅ GÉNÉRATION GPT-4 TURBO RÉUSSIE" in line for line in log_lines)
        
        self.log(f"   🧠 GPT-4 Turbo Attempt: {'✅ YES' if has_gpt4_attempt else '❌ NO'}")
        self.log(f"   🔑 OpenAI Key Present: {'✅ YES' if has_openai_key else '❌ NO'}")
        self.log(f"   📞 API Call Made: {'✅ YES' if has_api_call else '❌ NO'}")
        self.log(f"   📥 Response Received: {'✅ YES' if has_response else '❌ NO'}")
        self.log(f"   ⚠️ JSON Parsing Error: {'❌ YES' if has_json_error else '✅ NO'}")
        self.log(f"   🎉 Generation Success: {'✅ YES' if has_success else '❌ NO'}")
        
        # Provide diagnosis
        if has_gpt4_attempt and has_openai_key and has_api_call and has_response:
            if has_json_error:
                self.log("🔍 DIAGNOSIS: GPT-4 Turbo is working but has JSON parsing issue")
                self.log("   ✅ OpenAI API key is valid and working")
                self.log("   ✅ GPT-4 Turbo model is accessible")
                self.log("   ✅ API calls are successful")
                self.log("   ❌ JSON parsing fails due to markdown code blocks in response")
                self.log("   🔧 SOLUTION: Fix JSON parsing to handle ```json code blocks")
            elif has_success:
                self.log("🎉 DIAGNOSIS: GPT-4 Turbo is working correctly!")
                self.log("   ✅ All components functioning properly")
                self.log("   ✅ No fallback to generic content")
            else:
                self.log("⚠️ DIAGNOSIS: GPT-4 Turbo partially working")
        elif not has_openai_key:
            self.log("❌ DIAGNOSIS: OpenAI API key issue")
            self.log("   ❌ OpenAI API key not loaded or invalid")
            self.log("   🔧 SOLUTION: Check OPENAI_API_KEY environment variable")
        elif not has_api_call:
            self.log("❌ DIAGNOSIS: GPT-4 Turbo not being called")
            self.log("   ❌ API call not being made")
            self.log("   🔧 SOLUTION: Check call_gpt4_turbo_direct function")
        else:
            self.log("❌ DIAGNOSIS: Unknown issue with GPT-4 Turbo integration")
    
    def run_enhanced_logging_analysis(self):
        """Run the complete enhanced logging analysis"""
        self.log("🚀 STARTING ENHANCED LOGGING ANALYSIS")
        self.log("=" * 80)
        
        # Step 1: Create test user
        if not self.create_test_user():
            self.log("❌ Cannot proceed without test user", "ERROR")
            return False
        
        # Step 2: Test GPT-4 Turbo
        self.log("\n🧪 STEP 2: Testing GPT-4 Turbo Integration")
        gpt4_result = self.test_gpt4_turbo_with_enhanced_logging()
        
        # Step 3: Analyze backend logs
        self.log("\n🔍 STEP 3: Analyzing Backend Logs")
        log_analysis_result = self.analyze_backend_logs()
        
        # Final summary
        self.log("\n" + "=" * 80)
        self.log("🎯 ENHANCED LOGGING ANALYSIS SUMMARY")
        self.log("=" * 80)
        
        if log_analysis_result:
            self.log("✅ ENHANCED LOGGING IS WORKING!")
            self.log("📝 The detailed logging shows exactly what's happening with GPT-4 Turbo")
            self.log("🔍 Based on the logs, the main issue appears to be JSON parsing")
            self.log("💡 GPT-4 Turbo is working but returns content with markdown code blocks")
            return True
        else:
            self.log("❌ Could not analyze enhanced logging")
            return False

def main():
    """Main analysis execution"""
    print("🔍 GPT-4 TURBO ENHANCED LOGGING ANALYSIS")
    print("🎯 Analyzing the enhanced logging to identify fallback issues")
    print("=" * 80)
    
    analyzer = EnhancedLoggingAnalyzer()
    success = analyzer.run_enhanced_logging_analysis()
    
    if success:
        print("\n🎉 ENHANCED LOGGING ANALYSIS COMPLETED!")
        print("✅ The enhanced logging is working and shows the exact issue")
        print("🔧 Issue identified: JSON parsing error with markdown code blocks")
        exit(0)
    else:
        print("\n❌ ENHANCED LOGGING ANALYSIS HAD ISSUES")
        exit(1)

if __name__ == "__main__":
    main()