#!/usr/bin/env python3
"""
Script pour forcer la création de l'admin en production via bootstrap
"""
import requests
import time
import sys

PRODUCTION_URL = "https://ecomsimply.com"
BOOTSTRAP_TOKEN = "ECS-Bootstrap-2025-Secure-Token"

def test_bootstrap_force():
    """Force bootstrap même si health est en erreur"""
    try:
        print("🔧 Tentative bootstrap admin (ignore health check)...")
        headers = {
            "x-bootstrap-token": BOOTSTRAP_TOKEN,
            "Content-Type": "application/json"
        }
        
        response = requests.post(f"{PRODUCTION_URL}/api/admin/bootstrap", headers=headers, timeout=20)
        print(f"Bootstrap response: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            return True
        else:
            print(f"❌ Bootstrap failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Bootstrap error: {e}")
        return False

def test_login_after_bootstrap():
    """Test login après bootstrap"""
    try:
        login_data = {
            "email": "msylla54@gmail.com",
            "password": "ECS-Temp#2025-08-22!"
        }
        response = requests.post(f"{PRODUCTION_URL}/api/auth/login", json=login_data, timeout=15)
        print(f"Login test: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and data.get("token"):
                print(f"✅ LOGIN SUCCESS! Token length: {len(data['token'])}")
                return True
        
        print(f"❌ Login failed: {response.text}")
        return False
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False

def main():
    print("🛠️ FORCE ADMIN CREATION - PRODUCTION")
    print("=" * 50)
    
    # Tentative 1: Bootstrap direct
    print("\n1. Bootstrap admin (ignore health status):")
    bootstrap_ok = test_bootstrap_force()
    
    if bootstrap_ok:
        print("\n2. Test login après bootstrap:")
        login_ok = test_login_after_bootstrap()
        
        if login_ok:
            print("\n🎉 SUCCÈS! Authentification admin fonctionnelle en production!")
            return True
    
    # Tentative 2: Retry après délai
    print("\n⏳ Retry après 30s...")
    time.sleep(30)
    
    print("\n3. Retry bootstrap:")
    bootstrap_ok = test_bootstrap_force()
    
    if bootstrap_ok:
        print("\n4. Retry login:")
        login_ok = test_login_after_bootstrap()
        
        if login_ok:
            print("\n🎉 SUCCÈS après retry! Authentification admin fonctionnelle!")
            return True
    
    print("\n❌ Échec création admin - problème plus profond en production")
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)