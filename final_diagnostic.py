#!/usr/bin/env python3
"""
Diagnostic final pour identifier l'état exact de la production
"""
import requests
import time

def comprehensive_test():
    print("🔍 DIAGNOSTIC FINAL PRODUCTION")
    print("=" * 50)
    
    base_url = "https://ecomsimply.com"
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        print(f"✅ Health: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health: {e}")
    
    # Test 2: Bootstrap avec différents tokens
    tokens = [
        "ECS-Bootstrap-2025-Secure-Token",
        "bootstrap-token",
        "admin-bootstrap",
        ""
    ]
    
    for token in tokens:
        try:
            headers = {"x-bootstrap-token": token, "Content-Type": "application/json"}
            response = requests.post(f"{base_url}/api/admin/bootstrap", 
                                   headers=headers, timeout=5)
            print(f"Bootstrap '{token[:10]}...': {response.status_code} - {response.text[:100]}")
            
            if response.status_code == 200:
                return True
        except Exception as e:
            print(f"Bootstrap '{token[:10]}...': ERROR - {e}")
    
    # Test 3: Login avec différents passwords
    passwords = [
        "ECS-Permanent#2025!",
        "ECS-Temp#2025-08-22!",
        "admin",
        "password"
    ]
    
    for password in passwords:
        try:
            data = {"email": "msylla54@gmail.com", "password": password}
            response = requests.post(f"{base_url}/api/auth/login", json=data, timeout=5)
            print(f"Login '{password[:15]}...': {response.status_code} - {response.text[:100]}")
            
            if response.status_code == 200:
                return True
        except Exception as e:
            print(f"Login '{password[:15]}...': ERROR - {e}")
    
    # Test 4: Endpoints disponibles
    endpoints = [
        "/api/debug/env",
        "/api/emergency/create-admin",
        "/api/admin/users",
        "/api/stats/public"
    ]
    
    print("\n🔍 ENDPOINTS DISPONIBLES:")
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            print(f"{endpoint}: {response.status_code}")
        except Exception as e:
            print(f"{endpoint}: ERROR - {e}")
    
    return False

if __name__ == "__main__":
    success = comprehensive_test()
    print(f"\n🎯 Résultat: {'✅ SUCCÈS' if success else '❌ ÉCHEC'}")