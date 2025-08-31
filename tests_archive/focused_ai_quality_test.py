#!/usr/bin/env python3
"""
FOCUSED AI QUALITY TESTING - Premium Content Generation
Tests the specific improvements mentioned in the review request.
"""

import requests
import json
import time
import re
from datetime import datetime

BASE_URL = "https://ecomsimply.com/api"

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def register_user():
    """Register a test user"""
    timestamp = int(time.time())
    user_data = {
        "email": f"test.ai.quality{timestamp}@example.com",
        "name": "AI Quality Tester",
        "password": "TestPassword123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data, timeout=30)
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            if token:
                log(f"✅ User registered successfully")
                return token
        log(f"❌ Registration failed: {response.status_code}", "ERROR")
        return None
    except Exception as e:
        log(f"❌ Registration error: {str(e)}", "ERROR")
        return None

def test_product_sheet_quality(token, product_name, product_description, expected_category):
    """Test product sheet generation quality"""
    log(f"🧪 Testing: {product_name}")
    
    headers = {"Authorization": f"Bearer {token}"}
    request_data = {
        "product_name": product_name,
        "product_description": product_description,
        "generate_image": False,
        "number_of_images": 1,
        "language": "fr"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generate-sheet", json=request_data, headers=headers, timeout=45)
        
        if response.status_code == 200:
            sheet_data = response.json()
            
            # Extract key fields
            title = sheet_data.get("generated_title", "")
            description = sheet_data.get("marketing_description", "")
            price_suggestions = sheet_data.get("price_suggestions", "")
            target_audience = sheet_data.get("target_audience", "")
            seo_tags = sheet_data.get("seo_tags", [])
            
            log(f"   📝 Title: {title}")
            log(f"   💰 Price: {price_suggestions[:100]}...")
            log(f"   👥 Audience: {target_audience[:100]}...")
            log(f"   🏷️ SEO Tags: {seo_tags}")
            
            # Quality analysis
            issues = []
            strengths = []
            
            # 1. Check for inappropriate jargon (main issue from review)
            inappropriate_terms = ["ingénierie", "innovante", "avancé", "technologie avancée"]
            has_inappropriate = any(term.lower() in title.lower() for term in inappropriate_terms)
            
            if has_inappropriate:
                issues.append("❌ Title contains inappropriate technical jargon")
            else:
                strengths.append("✅ Title appropriate, no inappropriate jargon")
            
            # 2. Check pricing realism
            price_numbers = re.findall(r'(\d+)[€$]', price_suggestions)
            prices = [int(p) for p in price_numbers if p.isdigit()]
            
            realistic_ranges = {
                "toilet_paper": (2, 20),
                "smartphone": (200, 1500),
                "espresso_machine": (300, 3000)
            }
            
            expected_range = realistic_ranges.get(expected_category, (10, 500))
            
            if prices:
                min_price = min(prices)
                max_price = max(prices)
                
                if expected_range[0] <= min_price <= expected_range[1] and expected_range[0] <= max_price <= expected_range[1]:
                    strengths.append(f"✅ Realistic pricing: {min_price}€-{max_price}€")
                else:
                    issues.append(f"❌ Unrealistic pricing: {min_price}€-{max_price}€ for {expected_category}")
            else:
                issues.append("❌ No clear pricing found")
            
            # 3. Check description quality
            word_count = len(description.split())
            if 150 <= word_count <= 400:
                strengths.append(f"✅ Good description length: {word_count} words")
            else:
                issues.append(f"❌ Poor description length: {word_count} words")
            
            # 4. Check audience appropriateness
            if expected_category == "toilet_paper":
                inappropriate_audiences = ["technophiles", "gamers", "développeurs"]
                has_inappropriate_audience = any(term.lower() in target_audience.lower() for term in inappropriate_audiences)
                if has_inappropriate_audience:
                    issues.append("❌ Inappropriate audience for toilet paper")
                else:
                    strengths.append("✅ Appropriate audience for toilet paper")
            
            # Log results
            for strength in strengths:
                log(f"   {strength}")
            for issue in issues:
                log(f"   {issue}")
            
            # Calculate score
            total_checks = len(strengths) + len(issues)
            score = (len(strengths) / total_checks * 100) if total_checks > 0 else 0
            log(f"   📊 Quality Score: {score:.1f}%")
            
            return score >= 70, score
            
        else:
            log(f"❌ Request failed: {response.status_code} - {response.text}", "ERROR")
            return False, 0
            
    except Exception as e:
        log(f"❌ Test error: {str(e)}", "ERROR")
        return False, 0

def main():
    log("🚀 AI QUALITY PREMIUM TESTING - FOCUSED")
    log("=" * 50)
    
    # Register user
    token = register_user()
    if not token:
        log("❌ Cannot proceed without authentication", "ERROR")
        return False
    
    # Test cases from review request
    test_cases = [
        ("Papier toilettes", "Papier toilettes pour nettoyer Applications Polyvalentes", "toilet_paper"),
        ("Smartphone Samsung Galaxy", "Smartphone Android dernière génération avec appareil photo haute qualité", "smartphone"),
        ("Machine à café expresso professionnelle", "Machine expresso semi-automatique pour café professionnel", "espresso_machine")
    ]
    
    results = []
    
    for product_name, description, category in test_cases:
        log("")
        success, score = test_product_sheet_quality(token, product_name, description, category)
        results.append((product_name, success, score))
        time.sleep(2)  # Brief pause between tests
    
    # Summary
    log("")
    log("📊 FINAL RESULTS SUMMARY")
    log("=" * 30)
    
    passed = 0
    total_score = 0
    
    for product_name, success, score in results:
        status = "✅ PASS" if success else "❌ FAIL"
        log(f"{status} {product_name}: {score:.1f}%")
        if success:
            passed += 1
        total_score += score
    
    average_score = total_score / len(results)
    success_rate = (passed / len(results)) * 100
    
    log("")
    log(f"🎯 Overall Results:")
    log(f"   Tests Passed: {passed}/{len(results)} ({success_rate:.1f}%)")
    log(f"   Average Quality Score: {average_score:.1f}%")
    
    if passed == len(results) and average_score >= 70:
        log("🎉 ALL TESTS PASSED - AI QUALITY IMPROVEMENTS VERIFIED!")
        return True
    else:
        log("❌ SOME TESTS FAILED - AI QUALITY NEEDS ATTENTION")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)