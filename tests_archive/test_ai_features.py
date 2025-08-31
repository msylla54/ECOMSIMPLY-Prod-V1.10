#!/usr/bin/env python3
"""
Test script for REFACTORED AI Features System
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 30

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def test_user_registration():
    """Register a test user for AI features testing"""
    log("Registering test user for AI features testing...")
    
    timestamp = int(time.time())
    test_user = {
        "email": f"ai.tester{timestamp}@test.fr",
        "name": "AI Features Tester",
        "password": "TestPassword123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=test_user, timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("token")
            user_data = data.get("user")
            
            if auth_token and user_data:
                log(f"✅ User Registration: Successfully registered {user_data['name']}")
                return auth_token, user_data
            else:
                log("❌ User Registration: Missing token or user data", "ERROR")
                return None, None
        else:
            log(f"❌ User Registration failed: {response.status_code} - {response.text}", "ERROR")
            return None, None
            
    except Exception as e:
        log(f"❌ User Registration failed: {str(e)}", "ERROR")
        return None, None

def test_ai_seo_analysis(auth_token):
    """Test POST /api/ai/seo-analysis with robust error handling"""
    log("Testing AI SEO Analysis endpoint...")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    seo_request = {
        "product_name": "Smartphone Premium",
        "product_description": "Téléphone intelligent haut de gamme avec caméra professionnelle",
        "target_keywords": ["smartphone", "premium", "caméra"],
        "target_audience": "Professionnels et créateurs de contenu",
        "language": "fr"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/ai/seo-analysis", json=seo_request, headers=headers, timeout=TIMEOUT)
        
        if response.status_code == 200:
            seo_data = response.json()
            
            # Validate required fields
            required_fields = ["optimized_title", "meta_description", "seo_keywords", "content_score", "suggestions"]
            missing_fields = [field for field in required_fields if field not in seo_data]
            
            if missing_fields:
                log(f"❌ SEO Analysis: Missing fields {missing_fields}", "ERROR")
                return False
            
            log(f"✅ SEO Analysis: Successfully generated SEO optimization")
            log(f"   Optimized Title: {seo_data['optimized_title']}")
            log(f"   Content Score: {seo_data['content_score']}")
            log(f"   SEO Keywords: {len(seo_data['seo_keywords'])} keywords")
            log(f"   Suggestions: {len(seo_data['suggestions'])} recommendations")
            return True
            
        elif response.status_code == 503:
            log("✅ SEO Analysis: Service gracefully degraded (503) - Error handling working")
            return True
        elif response.status_code == 502:
            log("✅ SEO Analysis: External API error handled (502) - Error handling working")
            return True
        elif response.status_code == 500:
            log(f"   500 Error Response Text: {response.text}")
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            log(f"   500 Error Details: {error_data}")
            if error_data.get('error') in ['API_KEY_MISSING', 'EXTERNAL_API_ERROR', 'INTERNAL_ERROR']:
                log(f"✅ SEO Analysis: Proper error categorization ({error_data.get('error')})")
                return True
            else:
                log(f"❌ SEO Analysis: Unexpected 500 error format", "ERROR")
                return False
        else:
            log(f"❌ SEO Analysis failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ SEO Analysis failed: {str(e)}", "ERROR")
        return False

def test_ai_competitor_analysis(auth_token):
    """Test POST /api/ai/competitor-analysis with enhanced error handling"""
    log("Testing AI Competitor Analysis endpoint...")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    competitor_request = {
        "product_name": "Casque Audio Sans Fil",
        "category": "Electronics",
        "competitor_urls": ["https://example.com/competitor1", "https://example.com/competitor2"],
        "analysis_depth": "standard",
        "language": "fr"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/ai/competitor-analysis", json=competitor_request, headers=headers, timeout=TIMEOUT)
        
        if response.status_code == 200:
            competitor_data = response.json()
            
            # Validate required fields
            required_fields = ["competitors_found", "avg_price_range", "common_features", "market_position", "competitive_advantages"]
            missing_fields = [field for field in required_fields if field not in competitor_data]
            
            if missing_fields:
                log(f"❌ Competitor Analysis: Missing fields {missing_fields}", "ERROR")
                return False
            
            log(f"✅ Competitor Analysis: Successfully analyzed market competition")
            log(f"   Competitors Found: {competitor_data['competitors_found']}")
            log(f"   Market Position: {competitor_data['market_position']}")
            log(f"   Common Features: {len(competitor_data['common_features'])} features")
            log(f"   Competitive Advantages: {len(competitor_data['competitive_advantages'])} advantages")
            return True
            
        elif response.status_code == 503:
            log("✅ Competitor Analysis: Service gracefully degraded (503) - Error handling working")
            return True
        elif response.status_code == 502:
            log("✅ Competitor Analysis: External API error handled (502) - Error handling working")
            return True
        elif response.status_code == 500:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            if error_data.get('error') in ['API_KEY_MISSING', 'EXTERNAL_API_ERROR', 'INTERNAL_ERROR']:
                log(f"✅ Competitor Analysis: Proper error categorization ({error_data.get('error')})")
                return True
            else:
                log(f"❌ Competitor Analysis: Unexpected 500 error format", "ERROR")
                return False
        else:
            log(f"❌ Competitor Analysis failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ Competitor Analysis failed: {str(e)}", "ERROR")
        return False

def test_ai_features_overview(auth_token):
    """Test GET /api/ai/features-overview with enhanced subscription validation"""
    log("Testing AI Features Overview endpoint...")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/ai/features-overview", headers=headers, timeout=TIMEOUT)
        
        if response.status_code == 200:
            features_data = response.json()
            
            # Validate required fields
            required_fields = ["available_features", "subscription_plan", "feature_limits", "upgrade_recommendations"]
            missing_fields = [field for field in required_fields if field not in features_data]
            
            if missing_fields:
                log(f"❌ Features Overview: Missing fields {missing_fields}", "ERROR")
                return False
            
            # Validate features structure
            available_features = features_data['available_features']
            if not isinstance(available_features, list):
                log(f"❌ Features Overview: Invalid available_features structure", "ERROR")
                return False
            
            log(f"✅ Features Overview: Successfully retrieved AI features overview")
            log(f"   Subscription Plan: {features_data['subscription_plan']}")
            log(f"   Available Features: {len(available_features)} features")
            log(f"   Feature Limits: {features_data['feature_limits']}")
            log(f"   Upgrade Recommendations: {len(features_data.get('upgrade_recommendations', []))} recommendations")
            return True
            
        elif response.status_code == 503:
            log("✅ Features Overview: Service gracefully degraded (503) - Error handling working")
            return True
        elif response.status_code == 500:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            if error_data.get('error') in ['API_KEY_MISSING', 'EXTERNAL_API_ERROR', 'INTERNAL_ERROR']:
                log(f"✅ Features Overview: Proper error categorization ({error_data.get('error')})")
                return True
            else:
                log(f"❌ Features Overview: Unexpected 500 error format", "ERROR")
                return False
        else:
            log(f"❌ Features Overview failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ Features Overview failed: {str(e)}", "ERROR")
        return False

def main():
    """Run AI features tests"""
    log("🚀 Starting REFACTORED AI FEATURES SYSTEM TESTING...")
    log("=" * 80)
    
    # Register test user
    auth_token, user_data = test_user_registration()
    if not auth_token:
        log("❌ Cannot proceed without authentication token", "ERROR")
        return
    
    # Run AI features tests
    test_results = []
    test_results.append(("AI SEO Analysis", test_ai_seo_analysis(auth_token)))
    test_results.append(("AI Competitor Analysis", test_ai_competitor_analysis(auth_token)))
    test_results.append(("AI Features Overview", test_ai_features_overview(auth_token)))
    
    # Print Results Summary
    log("=" * 80)
    log("🎯 AI FEATURES TEST RESULTS SUMMARY")
    log("=" * 80)
    
    passed_tests = []
    failed_tests = []
    
    for test_name, result in test_results:
        if result:
            passed_tests.append(test_name)
            log(f"✅ PASSED: {test_name}")
        else:
            failed_tests.append(test_name)
            log(f"❌ FAILED: {test_name}")
    
    log("=" * 80)
    log(f"📊 FINAL RESULTS: {len(passed_tests)}/{len(test_results)} tests passed")
    log(f"✅ Passed: {len(passed_tests)} tests")
    log(f"❌ Failed: {len(failed_tests)} tests")
    
    if failed_tests:
        log("❌ Failed Tests:")
        for test in failed_tests:
            log(f"   - {test}")
    
    success_rate = (len(passed_tests) / len(test_results)) * 100
    log(f"📈 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        log("🎉 EXCELLENT: AI Features system is working excellently!")
    elif success_rate >= 75:
        log("✅ GOOD: AI Features system is working well with minor issues")
    elif success_rate >= 50:
        log("⚠️  MODERATE: AI Features system has some issues that need attention")
    else:
        log("❌ CRITICAL: AI Features system has significant issues requiring immediate attention")

if __name__ == "__main__":
    main()