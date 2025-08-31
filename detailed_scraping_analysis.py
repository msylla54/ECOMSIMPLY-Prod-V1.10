#!/usr/bin/env python3
"""
ECOMSIMPLY Detailed Scraping Data Analysis
Analyzes the actual scraped data to verify it's real and not mock
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 60

# Test credentials for Premium user
TEST_EMAIL = "msylla54@yahoo.fr"
TEST_PASSWORD = "NewPassword123"

def authenticate():
    """Authenticate and return session with token"""
    session = requests.Session()
    session.timeout = TIMEOUT
    
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    response = session.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        auth_token = data.get("token")
        
        session.headers.update({
            "Authorization": f"Bearer {auth_token}"
        })
        
        print(f"✅ Authenticated as {TEST_EMAIL}")
        return session
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        return None

def analyze_scraping_data():
    """Analyze the actual scraped data"""
    session = authenticate()
    if not session:
        return
    
    print("\n🔍 ANALYZING REAL SCRAPING DATA")
    print("=" * 60)
    
    # Test Google Trends scraping
    print("\n📈 Testing Google Trends Scraping...")
    trends_response = session.post(f"{BASE_URL}/seo/scrape/trends")
    
    if trends_response.status_code == 200:
        trends_data = trends_response.json()
        print(f"✅ Google Trends Response:")
        print(json.dumps(trends_data, indent=2))
        
        # Analyze the data
        trends_count = trends_data.get("trends_count", 0)
        categories = trends_data.get("categories", [])
        message = trends_data.get("message", "")
        
        print(f"\n📊 Analysis:")
        print(f"   - Trends scraped: {trends_count}")
        print(f"   - Categories processed: {len(categories)} - {categories}")
        print(f"   - Message: {message}")
        
        # Check for real data indicators
        if "fallback" in message.lower():
            print("   ⚠️ Using fallback data (real libraries may not be available)")
        elif "scraped" in message.lower():
            print("   ✅ Real scraping appears to be working")
        
    else:
        print(f"❌ Google Trends failed: {trends_response.status_code} - {trends_response.text}")
    
    # Test Competitor scraping
    print("\n🏪 Testing Competitor Scraping...")
    competitors_response = session.post(f"{BASE_URL}/seo/scrape/competitors")
    
    if competitors_response.status_code == 200:
        competitors_data = competitors_response.json()
        print(f"✅ Competitor Scraping Response:")
        print(json.dumps(competitors_data, indent=2))
        
        # Analyze the data
        competitors_count = competitors_data.get("competitors_count", 0)
        categories = competitors_data.get("categories", [])
        message = competitors_data.get("message", "")
        
        print(f"\n📊 Analysis:")
        print(f"   - Competitors scraped: {competitors_count}")
        print(f"   - Categories processed: {len(categories)} - {categories}")
        print(f"   - Message: {message}")
        
        # Check for real data indicators
        if "fallback" in message.lower():
            print("   ⚠️ Using fallback data (real libraries may not be available)")
        elif "scraped" in message.lower():
            print("   ✅ Real scraping appears to be working")
        
    else:
        print(f"❌ Competitor scraping failed: {competitors_response.status_code} - {competitors_response.text}")
    
    # Test if we can create some product sheets to have categories for scraping
    print("\n📝 Creating test product sheet to generate categories...")
    
    product_data = {
        "product_name": "iPhone 16 Pro",
        "product_description": "Smartphone premium avec processeur A18 Pro et appareil photo 48MP",
        "generate_image": False,
        "language": "fr"
    }
    
    sheet_response = session.post(f"{BASE_URL}/product-sheets/generate", json=product_data)
    
    if sheet_response.status_code == 200:
        print("✅ Created test product sheet")
        
        # Now test scraping again with real categories
        print("\n🔄 Re-testing scraping with real product categories...")
        
        trends_response2 = session.post(f"{BASE_URL}/seo/scrape/trends")
        if trends_response2.status_code == 200:
            trends_data2 = trends_response2.json()
            print(f"✅ Second Google Trends test:")
            print(json.dumps(trends_data2, indent=2))
        
        competitors_response2 = session.post(f"{BASE_URL}/seo/scrape/competitors")
        if competitors_response2.status_code == 200:
            competitors_data2 = competitors_response2.json()
            print(f"✅ Second Competitor test:")
            print(json.dumps(competitors_data2, indent=2))
    
    else:
        print(f"⚠️ Could not create test product sheet: {sheet_response.status_code}")
    
    print("\n" + "=" * 60)
    print("🎯 SCRAPING DATA ANALYSIS COMPLETE")

if __name__ == "__main__":
    analyze_scraping_data()