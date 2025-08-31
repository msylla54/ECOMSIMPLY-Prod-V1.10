#!/usr/bin/env python3
"""
ECOMSIMPLY AI Quality Test - Focus on Review Request
Test the exact issue: toilet paper generating inappropriate technical content
"""

import requests
import json
import time
import re
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TEST_USER_EMAIL = "ai.quality.test@example.com"
TEST_USER_PASSWORD = "TestPassword123"

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def test_user_setup():
    """Setup test user"""
    session = requests.Session()
    
    # Register user
    register_data = {
        "email": TEST_USER_EMAIL,
        "name": "AI Quality Tester",
        "password": TEST_USER_PASSWORD
    }
    
    try:
        response = session.post(f"{BASE_URL}/auth/register", json=register_data)
        log(f"Registration response: {response.status_code}")
    except Exception as e:
        log(f"Registration error: {e}")
    
    # Login
    login_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    try:
        response = session.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            if token:
                session.headers.update({"Authorization": f"Bearer {token}"})
                log("✅ User authentication successful")
                return session
            else:
                log("❌ No token received")
                return None
        else:
            log(f"❌ Login failed: {response.status_code}")
            return None
    except Exception as e:
        log(f"❌ Login error: {e}")
        return None

def analyze_toilet_paper_content(sheet_data):
    """Analyze toilet paper content for quality issues"""
    issues = []
    score = 100
    
    title = sheet_data.get("generated_title", "").lower()
    description = sheet_data.get("marketing_description", "").lower()
    features = [f.lower() for f in sheet_data.get("key_features", [])]
    tags = [t.lower() for t in sheet_data.get("seo_tags", [])]
    price_text = sheet_data.get("price_suggestions", "").lower()
    audience = sheet_data.get("target_audience", "").lower()
    
    log("📊 ANALYZING GENERATED CONTENT:")
    log(f"   Title: {sheet_data.get('generated_title', 'N/A')}")
    log(f"   Price: {sheet_data.get('price_suggestions', 'N/A')}")
    log(f"   Tags: {', '.join(sheet_data.get('seo_tags', []))}")
    log(f"   Audience: {sheet_data.get('target_audience', 'N/A')[:100]}...")
    
    # Check for inappropriate technical jargon
    inappropriate_terms = [
        "ingénierie", "innovante", "technologie", "avancé", "moderne",
        "engineering", "innovative", "technology", "advanced", "modern",
        "applications polyvalentes", "expérience utilisateur"
    ]
    
    for term in inappropriate_terms:
        if any(term in text for text in [title, description] + features):
            issues.append(f"❌ Inappropriate technical term '{term}' found")
            score -= 20
            
    # Check pricing (should be 2€-25€ range as per review)
    price_numbers = re.findall(r'(\d+)€', price_text)
    if price_numbers:
        max_price = max(int(p) for p in price_numbers)
        if max_price > 30:
            issues.append(f"❌ Unrealistic pricing for toilet paper: {max_price}€ (should be ≤25€)")
            score -= 25
        else:
            log(f"✅ Realistic toilet paper pricing detected: max {max_price}€")
            
    # Check for inappropriate tags
    inappropriate_tags = ["#avancé", "#moderne", "#technologie", "#advanced", "#modern", "#technology"]
    for tag in tags:
        if any(inappropriate in tag for inappropriate in inappropriate_tags):
            issues.append(f"❌ Inappropriate tag for toilet paper: {tag}")
            score -= 15
            
    # Check audience targeting
    inappropriate_audience_terms = ["technophiles", "tech", "technologie", "technology", "consommateurs tech"]
    if any(term in audience for term in inappropriate_audience_terms):
        issues.append("❌ Inappropriate tech audience targeting for toilet paper")
        score -= 20
    
    return issues, score

def test_toilet_paper_generation(session):
    """Test the critical toilet paper generation case"""
    log("🧻 TESTING TOILET PAPER GENERATION (EXACT CASE FROM REVIEW)")
    
    # This is the EXACT test case from the review request
    test_data = {
        "product_name": "Papier toilettes",
        "product_description": "Papier toilettes pour nettoyer Applications Polyvalentes",
        "generate_image": False,
        "number_of_images": 0,
        "language": "fr"
    }
    
    log(f"📝 Test data: {json.dumps(test_data, ensure_ascii=False)}")
    
    try:
        response = session.post(f"{BASE_URL}/generate-sheet", json=test_data)
        
        if response.status_code != 200:
            log(f"❌ API call failed: {response.status_code}")
            try:
                error_data = response.json()
                log(f"❌ Error details: {error_data}")
            except:
                log(f"❌ Response text: {response.text}")
            return False
            
        data = response.json()
        
        if not data.get("success"):
            log(f"❌ Generation failed: {data.get('message', 'Unknown error')}")
            return False
            
        sheet_data = data.get("sheet", {})
        
        # Analyze content quality
        issues, score = analyze_toilet_paper_content(sheet_data)
        
        log(f"\n📊 QUALITY ANALYSIS RESULTS:")
        log(f"   Quality Score: {score}/100")
        
        if issues:
            log("❌ QUALITY ISSUES DETECTED:")
            for issue in issues:
                log(f"   {issue}")
            return False
        else:
            log("✅ QUALITY CHECK PASSED: No inappropriate content detected")
            log("✅ AI fix is working correctly!")
            return True
            
    except Exception as e:
        log(f"❌ Exception during test: {str(e)}")
        return False

def main():
    """Main test execution"""
    log("🚀 STARTING ECOMSIMPLY AI QUALITY TEST")
    log("=" * 60)
    log("FOCUS: AI Content Generation Quality Fix Verification")
    log("ISSUE: Toilet paper generating inappropriate technical content")
    log("EXPECTED: Realistic, appropriate content for basic products")
    log("=" * 60)
    
    # Setup user
    log("\n👤 SETTING UP TEST USER")
    session = test_user_setup()
    if not session:
        log("❌ Cannot proceed without authentication")
        return False
    
    # Test toilet paper generation
    log("\n🎯 CRITICAL TEST: TOILET PAPER CONTENT GENERATION")
    success = test_toilet_paper_generation(session)
    
    # Final assessment
    log("\n" + "=" * 60)
    log("🎯 FINAL ASSESSMENT FOR REVIEW:")
    if success:
        log("✅ TOILET PAPER GENERATION: AI quality fix is WORKING CORRECTLY")
        log("   ✅ No inappropriate technical jargon detected")
        log("   ✅ Pricing appears realistic for the product category")
        log("   ✅ SEO tags and audience targeting are appropriate")
        log("   ✅ The reported issue has been RESOLVED")
        log("\n🎉 AI QUALITY TEST COMPLETED SUCCESSFULLY!")
        return True
    else:
        log("❌ TOILET PAPER GENERATION: AI quality issues STILL PRESENT")
        log("   ❌ The reported fix may not be fully implemented")
        log("   ❌ Manual review of AI prompts is recommended")
        log("   ❌ The issue from the review request is NOT resolved")
        log("\n❌ AI QUALITY TEST FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)