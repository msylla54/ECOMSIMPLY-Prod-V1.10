#!/usr/bin/env python3
"""
Script de diagnostic et correction pour l'authentification admin en production
"""
import requests
import json
import sys

# Configuration
PRODUCTION_URL = "https://ecomsimply.com"
BOOTSTRAP_TOKEN = "ECS-Bootstrap-2025-Secure-Token"
ADMIN_EMAIL = "msylla54@gmail.com"
ADMIN_PASSWORD = "ECS-Temp#2025-08-22!"

def test_health():
    """Test du health endpoint"""
    try:
        response = requests.get(f"{PRODUCTION_URL}/api/health", timeout=10)
        print(f"🏥 Health check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Database: {data.get('db', 'unknown')}")
            return True
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_admin_bootstrap():
    """Test du bootstrap admin"""
    try:
        headers = {
            "x-bootstrap-token": BOOTSTRAP_TOKEN,
            "Content-Type": "application/json"
        }
        response = requests.post(f"{PRODUCTION_URL}/api/admin/bootstrap", headers=headers, timeout=15)
        print(f"🔧 Bootstrap admin: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Result: {data}")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Bootstrap failed: {e}")
        return False

def test_admin_login():
    """Test du login admin"""
    try:
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        response = requests.post(f"{PRODUCTION_URL}/api/auth/login", json=login_data, timeout=10)
        print(f"🔐 Admin login: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and data.get("token"):
                print(f"   ✅ Login successful - Token length: {len(data['token'])}")
                print(f"   User: {data.get('user', {}).get('email')} (admin: {data.get('user', {}).get('is_admin')})")
                return data.get("token")
            else:
                print(f"   ❌ Invalid response format: {data}")
                return None
        else:
            error_text = response.text
            print(f"   ❌ Login failed: {error_text}")
            return None
            
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return None

def main():
    print("🛠️ DIAGNOSTIC AUTHENTIFICATION ADMIN PRODUCTION")
    print("=" * 60)
    
    # Test 1: Health check
    print("\n1. Test Health Endpoint:")
    health_ok = test_health()
    
    if not health_ok:
        print("❌ Production non accessible, arrêt du diagnostic")
        sys.exit(1)
    
    # Test 2: Bootstrap admin
    print("\n2. Test Bootstrap Admin:")
    bootstrap_ok = test_admin_bootstrap()
    
    # Test 3: Login admin
    print("\n3. Test Login Admin:")
    token = test_admin_login()
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DIAGNOSTIC:")
    print(f"Health: {'✅' if health_ok else '❌'}")
    print(f"Bootstrap: {'✅' if bootstrap_ok else '❌'}")
    print(f"Login: {'✅' if token else '❌'}")
    
    if token:
        print("\n🎉 AUTHENTIFICATION ADMIN FONCTIONNELLE EN PRODUCTION!")
        return True
    else:
        print("\n❌ AUTHENTIFICATION ADMIN ÉCHOUE EN PRODUCTION")
        if bootstrap_ok:
            print("💡 Bootstrap OK mais login échoue - Problème de hash ou logique auth")
        else:
            print("💡 Bootstrap échoue - Problème de token ou config environnement")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)