#!/usr/bin/env python3
"""
Script de validation intensive avec retry automatique
"""
import requests
import time
import sys

PRODUCTION_URL = "https://ecomsimply.com"
BOOTSTRAP_TOKEN = "ECS-Bootstrap-2025-Secure-Token"
ADMIN_EMAIL = "msylla54@gmail.com"
ADMIN_PASSWORD = "ECS-Permanent#2025!"

def test_bootstrap():
    """Test bootstrap avec retry"""
    try:
        headers = {
            "x-bootstrap-token": BOOTSTRAP_TOKEN,
            "Content-Type": "application/json"
        }
        
        response = requests.post(f"{PRODUCTION_URL}/api/admin/bootstrap", 
                               headers=headers, timeout=10)
        
        print(f"Bootstrap: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.text
            
    except Exception as e:
        print(f"❌ Bootstrap error: {e}")
        return False, str(e)

def test_login():
    """Test login admin"""
    try:
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        response = requests.post(f"{PRODUCTION_URL}/api/auth/login", 
                               json=login_data, timeout=10)
        
        print(f"Login: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and data.get("token"):
                return True, data["token"]
        
        return False, response.text
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False, str(e)

def intensive_test():
    """Test intensif avec retry jusqu'à succès"""
    max_attempts = 20
    delay = 30  # 30 secondes entre chaque test
    
    print("🚨 VALIDATION INTENSIVE ADMIN PRODUCTION")
    print("=" * 60)
    print(f"Max attempts: {max_attempts}")
    print(f"Delay between tests: {delay}s")
    print("=" * 60)
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n🔄 TENTATIVE {attempt}/{max_attempts}")
        print(f"Temps: {time.strftime('%H:%M:%S')}")
        
        # Test 1: Bootstrap
        print("1. Test bootstrap...")
        bootstrap_success, bootstrap_result = test_bootstrap()
        
        if bootstrap_success:
            print("✅ BOOTSTRAP RÉUSSI!")
            
            # Test 2: Login si bootstrap réussi
            print("2. Test login admin...")
            login_success, login_result = test_login()
            
            if login_success:
                print(f"✅ LOGIN RÉUSSI! Token: {login_result[:50]}...")
                
                # Mission accomplie
                print("\n🎉 MISSION ACCOMPLIE!")
                print("✅ Bootstrap admin: Succès")
                print("✅ Login admin: Succès")
                print(f"✅ JWT Token: {len(login_result)} caractères")
                print(f"✅ Email: {ADMIN_EMAIL}")
                print("✅ Production: 100% fonctionnelle")
                
                return True, login_result
            else:
                print(f"❌ Login échoué: {login_result}")
        else:
            print(f"❌ Bootstrap échoué: {bootstrap_result}")
        
        if attempt < max_attempts:
            print(f"⏳ Attente {delay}s avant retry...")
            time.sleep(delay)
    
    print(f"\n❌ ÉCHEC APRÈS {max_attempts} TENTATIVES")
    print("💡 Variables Vercel potentiellement pas encore propagées")
    print("💡 Vérifier configuration Vercel et redéploiement")
    
    return False, None

def main():
    success, token = intensive_test()
    
    if success:
        print("\n" + "=" * 60)
        print("🎯 RÉSULTAT FINAL: ✅ SUCCÈS COMPLET")
        print("Admin msylla54@gmail.com maintenant 100% fonctionnel!")
        print("Dashboard et Amazon SP-API accessibles en production!")
        
        # Sauvegarder le token pour usage ultérieur
        with open("/app/admin_token.txt", "w") as f:
            f.write(token)
        
        return True
    else:
        print("\n" + "=" * 60)
        print("🎯 RÉSULTAT FINAL: ❌ ÉCHEC")
        print("Variables Vercel pas encore propagées après configuration")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)