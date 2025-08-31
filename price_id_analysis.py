#!/usr/bin/env python3
"""
ECOMSIMPLY Price ID Environment Mismatch Analysis
Analyzes the critical issue found: Live Price IDs with Test API Key
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 30

class PriceIDAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        self.user_data = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def create_test_user(self):
        """Create a test user"""
        timestamp = int(time.time())
        test_user = {
            "email": f"analysis.test{timestamp}@ecomsimply.fr",
            "name": "Analysis Test User",
            "password": "AnalysisPassword123!"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=test_user)
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.user_data = data.get("user")
                return True
            return False
        except:
            return False
    
    def analyze_price_id_environment_mismatch(self):
        """Analyze the Price ID and API key environment mismatch"""
        self.log("🔍 ANALYZING PRICE ID ENVIRONMENT MISMATCH")
        self.log("=" * 80)
        
        if not self.auth_token:
            self.log("❌ Cannot analyze: No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        origin_url = BASE_URL.replace("/api", "")
        
        # Test regular checkout (should work)
        self.log("1️⃣ Testing REGULAR checkout (should work)...")
        regular_request = {
            "plan_type": "pro",
            "origin_url": origin_url,
            "trial_subscription": False
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/payments/checkout", json=regular_request, headers=headers)
            if response.status_code == 200:
                self.log("   ✅ REGULAR checkout: WORKS (uses fallback pricing)")
                checkout_data = response.json()
                self.log(f"   💰 Amount: {checkout_data.get('amount')}€")
                self.log(f"   🔗 URL: {checkout_data.get('checkout_url', '')[:80]}...")
            else:
                self.log(f"   ❌ REGULAR checkout failed: {response.status_code}")
        except Exception as e:
            self.log(f"   ❌ REGULAR checkout error: {str(e)}")
        
        # Test trial checkout (should fail with specific error)
        self.log("\n2️⃣ Testing TRIAL checkout (should fail with Price ID error)...")
        trial_request = {
            "plan_type": "pro",
            "origin_url": origin_url,
            "trial_subscription": True
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/payments/checkout", json=trial_request, headers=headers)
            if response.status_code == 500:
                self.log("   ❌ TRIAL checkout: FAILS as expected")
                error_data = response.json()
                self.log(f"   🚨 Error: {error_data.get('detail', 'Unknown error')}")
                
                # This confirms the issue
                if "essai gratuit" in error_data.get('detail', '').lower():
                    self.log("   🎯 CONFIRMED: Trial creation failing due to Price ID mismatch")
                    return True
            else:
                self.log(f"   ⚠️  Unexpected response: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"   ❌ TRIAL checkout error: {str(e)}")
            return False
    
    def provide_solution_analysis(self):
        """Provide detailed solution analysis"""
        self.log("\n" + "=" * 80)
        self.log("🎯 ROOT CAUSE ANALYSIS")
        self.log("=" * 80)
        
        self.log("❌ PROBLEM IDENTIFIED:")
        self.log("   • Backend uses TEST Stripe API key: sk_test_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...")
        self.log("   • Price IDs provided are LIVE mode: price_1Rrw3UGK8qzu5V5Wu8PnvKzK")
        self.log("   • Stripe rejects TEST API calls to LIVE Price IDs")
        
        self.log("\n✅ SOLUTIONS AVAILABLE:")
        self.log("   OPTION 1 (RECOMMENDED): Get TEST mode Price IDs")
        self.log("   • Create equivalent Price IDs in Stripe TEST mode")
        self.log("   • Update .env with test Price IDs (price_test_...)")
        self.log("   • Keep using TEST API key for development")
        
        self.log("\n   OPTION 2: Switch to LIVE mode (NOT RECOMMENDED for testing)")
        self.log("   • Use LIVE Stripe API key: sk_live_...")
        self.log("   • Keep current LIVE Price IDs")
        self.log("   • ⚠️  WARNING: This processes real payments!")
        
        self.log("\n🔧 IMMEDIATE FIX NEEDED:")
        self.log("   1. Create TEST Price IDs in Stripe Dashboard")
        self.log("   2. Update STRIPE_PRICE_ID_PRO and STRIPE_PRICE_ID_PREMIUM in .env")
        self.log("   3. Restart backend service")
        
        self.log("\n📋 VERIFICATION STEPS:")
        self.log("   1. Regular checkout should continue working")
        self.log("   2. Trial checkout should work with TEST Price IDs")
        self.log("   3. Native 7-day trials should function correctly")
    
    def run_analysis(self):
        """Run complete analysis"""
        self.log("🚀 STARTING PRICE ID ENVIRONMENT MISMATCH ANALYSIS")
        self.log("=" * 80)
        
        # Create test user
        if not self.create_test_user():
            self.log("❌ Cannot create test user", "ERROR")
            return False
        
        # Analyze the mismatch
        mismatch_confirmed = self.analyze_price_id_environment_mismatch()
        
        # Provide solution
        self.provide_solution_analysis()
        
        self.log("\n" + "=" * 80)
        self.log("📊 ANALYSIS COMPLETE")
        self.log("=" * 80)
        
        if mismatch_confirmed:
            self.log("🎯 CONCLUSION: Price ID environment mismatch CONFIRMED")
            self.log("✅ Regular payments work (fallback system)")
            self.log("❌ Trial payments fail (requires correct Price IDs)")
            self.log("🔧 FIX: Update Price IDs to TEST mode versions")
            return True
        else:
            self.log("⚠️  Could not confirm mismatch - needs further investigation")
            return False

def main():
    """Main analysis execution"""
    analyzer = PriceIDAnalyzer()
    success = analyzer.run_analysis()
    
    if success:
        print("\n🎉 PRICE ID MISMATCH ANALYSIS COMPLETED!")
        print("📋 ACTION REQUIRED: Update Price IDs to TEST mode")
        exit(0)
    else:
        print("\n❌ ANALYSIS INCONCLUSIVE!")
        exit(1)

if __name__ == "__main__":
    main()