#!/usr/bin/env python3
"""
Detailed GPT-4 Turbo Integration Analysis
This script analyzes whether GPT-4 Turbo is actually being used or if the system is falling back
"""

import requests
import json
import time
import re

BASE_URL = "https://ecomsimply.com/api"

def analyze_gpt4_turbo_usage():
    session = requests.Session()
    session.timeout = 45
    
    # Register a test user
    timestamp = int(time.time())
    test_user = {
        "email": f"gpt4analysis{timestamp}@example.com",
        "name": "GPT-4 Analysis User",
        "password": "TestPassword123!"
    }
    
    print("🔍 Registering test user for GPT-4 Turbo analysis...")
    response = session.post(f"{BASE_URL}/auth/register", json=test_user)
    
    if response.status_code != 200:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return
    
    data = response.json()
    auth_token = data.get("token")
    
    if not auth_token:
        print("❌ No auth token received")
        return
    
    print("✅ User registered successfully")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test multiple different products to see if we get varied, intelligent responses
    test_products = [
        {
            "name": "iPhone 15 Pro",
            "description": "Smartphone haut de gamme avec processeur A17 Pro et appareil photo 48MP",
            "expected_ai_indicators": ["a17 pro", "processeur", "appareil photo", "48mp", "smartphone"]
        },
        {
            "name": "Papier toilette premium",
            "description": "Papier toilette doux et résistant pour usage domestique",
            "expected_ai_indicators": ["doux", "résistant", "domestique", "hygiène", "confort"]
        },
        {
            "name": "Machine à café expresso",
            "description": "Machine à café automatique avec broyeur intégré",
            "expected_ai_indicators": ["expresso", "broyeur", "automatique", "café", "machine"]
        }
    ]
    
    results = []
    
    for i, product in enumerate(test_products):
        print(f"\n🧪 Test {i+1}/3: Analyzing {product['name']}")
        
        test_data = {
            "product_name": product["name"],
            "product_description": product["description"],
            "generate_image": False,  # Focus on text generation
            "number_of_images": 0,
            "language": "fr"
        }
        
        start_time = time.time()
        response = session.post(f"{BASE_URL}/generate-sheet", json=test_data, headers=headers)
        generation_time = time.time() - start_time
        
        if response.status_code == 200:
            response_data = response.json()
            
            analysis = analyze_response_quality(product, response_data, generation_time)
            results.append(analysis)
            
            print(f"   ⏱️ Generation time: {generation_time:.2f}s")
            print(f"   🎯 AI Quality Score: {analysis['ai_quality_score']}/100")
            print(f"   📝 Title: {response_data.get('generated_title', 'N/A')[:60]}...")
            print(f"   🔍 AI Indicators: {analysis['ai_indicators_found']}/{analysis['ai_indicators_total']}")
            
            if analysis['likely_gpt4_turbo']:
                print(f"   ✅ Likely using GPT-4 Turbo")
            else:
                print(f"   ❌ Likely using fallback system")
                print(f"   🔍 Reasons: {', '.join(analysis['fallback_indicators'])}")
        else:
            print(f"   ❌ Request failed: {response.status_code}")
            results.append({"likely_gpt4_turbo": False, "ai_quality_score": 0})
        
        time.sleep(2)  # Pause between requests
    
    # Overall analysis
    print("\n" + "="*80)
    print("🎯 GPT-4 TURBO INTEGRATION ANALYSIS SUMMARY")
    print("="*80)
    
    gpt4_turbo_count = sum(1 for r in results if r['likely_gpt4_turbo'])
    avg_quality_score = sum(r['ai_quality_score'] for r in results) / len(results) if results else 0
    
    print(f"📊 Tests using GPT-4 Turbo: {gpt4_turbo_count}/{len(results)}")
    print(f"📊 Average AI Quality Score: {avg_quality_score:.1f}/100")
    
    if gpt4_turbo_count >= 2:
        print("✅ GPT-4 TURBO STATUS: WORKING CORRECTLY")
        print("   The system is successfully using GPT-4 Turbo for content generation")
    elif gpt4_turbo_count == 1:
        print("⚠️ GPT-4 TURBO STATUS: PARTIALLY WORKING")
        print("   The system sometimes uses GPT-4 Turbo but may fall back frequently")
    else:
        print("❌ GPT-4 TURBO STATUS: NOT WORKING")
        print("   The system appears to be using fallback content generation only")
        print("   Possible issues:")
        print("   - OpenAI API key not configured or invalid")
        print("   - GPT-4 Turbo model not accessible")
        print("   - Network connectivity issues")
        print("   - Rate limiting or quota exceeded")
    
    # Specific recommendations
    print("\n🔧 RECOMMENDATIONS:")
    if avg_quality_score < 50:
        print("   1. Check OpenAI API key configuration in backend/.env")
        print("   2. Verify GPT-4 Turbo model access in OpenAI account")
        print("   3. Check backend logs for API errors")
    elif gpt4_turbo_count < len(results):
        print("   1. Monitor for intermittent API failures")
        print("   2. Consider implementing retry logic for failed API calls")
        print("   3. Check rate limiting settings")
    else:
        print("   ✅ GPT-4 Turbo integration is working well!")
    
    return gpt4_turbo_count >= 2

def analyze_response_quality(product, response_data, generation_time):
    """Analyze if the response likely came from GPT-4 Turbo or fallback system"""
    
    analysis = {
        "likely_gpt4_turbo": True,
        "ai_quality_score": 100,
        "ai_indicators_found": 0,
        "ai_indicators_total": 0,
        "fallback_indicators": []
    }
    
    title = response_data.get("generated_title", "").lower()
    description = response_data.get("marketing_description", "").lower()
    features = [f.lower() for f in response_data.get("key_features", [])]
    tags = [t.lower() for t in response_data.get("seo_tags", [])]
    price_text = response_data.get("price_suggestions", "").lower()
    
    # Check for fallback system indicators
    fallback_phrases = [
        "produit d'exception qui répond à vos attentes",
        "conçu avec soin et attention aux détails",
        "qualité supérieure et son design réfléchi",
        "prix sur demande - contactez-nous",
        "consommateurs exigeants recherchant qualité",
        "découvrez l'excellence - commandez maintenant"
    ]
    
    fallback_count = 0
    for phrase in fallback_phrases:
        if phrase in description or phrase in title or phrase in price_text:
            fallback_count += 1
            analysis["fallback_indicators"].append(f"Generic phrase: '{phrase[:30]}...'")
    
    if fallback_count >= 3:
        analysis["likely_gpt4_turbo"] = False
        analysis["ai_quality_score"] -= 40
    
    # Check for product-specific content
    expected_indicators = product.get("expected_ai_indicators", [])
    analysis["ai_indicators_total"] = len(expected_indicators)
    
    for indicator in expected_indicators:
        if any(indicator in text for text in [title, description] + features + tags):
            analysis["ai_indicators_found"] += 1
    
    if analysis["ai_indicators_found"] < len(expected_indicators) * 0.3:  # Less than 30% relevance
        analysis["likely_gpt4_turbo"] = False
        analysis["ai_quality_score"] -= 30
        analysis["fallback_indicators"].append("Low product relevance")
    
    # Check for generic features
    generic_features = [
        "qualité premium garantie",
        "design soigné et fonctionnel", 
        "performance optimale",
        "durabilité exceptionnelle",
        "satisfaction client assurée"
    ]
    
    generic_feature_count = sum(1 for feature in features if any(generic in feature for generic in generic_features))
    if generic_feature_count >= 4:  # Most features are generic
        analysis["likely_gpt4_turbo"] = False
        analysis["ai_quality_score"] -= 25
        analysis["fallback_indicators"].append("Generic features detected")
    
    # Check generation time (GPT-4 Turbo should take reasonable time)
    if generation_time < 5:  # Too fast for real AI
        analysis["ai_quality_score"] -= 15
        analysis["fallback_indicators"].append("Generation too fast for AI")
    elif generation_time > 35:  # Too slow
        analysis["ai_quality_score"] -= 10
        analysis["fallback_indicators"].append("Generation very slow")
    
    # Check for content variety and intelligence
    word_count = len(description.split())
    if word_count < 50:  # Too short
        analysis["ai_quality_score"] -= 20
        analysis["fallback_indicators"].append("Description too short")
    
    return analysis

if __name__ == "__main__":
    success = analyze_gpt4_turbo_usage()
    exit(0 if success else 1)