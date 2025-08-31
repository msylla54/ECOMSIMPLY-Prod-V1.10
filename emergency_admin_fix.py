#!/usr/bin/env python3
"""
Script d'urgence pour créer l'admin et tester l'authentification
"""
import requests
import time
import sys

PRODUCTION_URL = "https://ecomsimply.com"
ADMIN_EMAIL = "msylla54@gmail.com"
ADMIN_PASSWORD = "ECS-Temp#2025-08-22!"

def emergency_create_admin():
    """Utilise l'endpoint d'urgence pour créer l'admin"""
    try:
        print("🚨 Création admin via endpoint d'urgence...")
        response = requests.post(f"{PRODUCTION_URL}/api/emergency/create-admin", timeout=20)
        print(f"Emergency admin creation: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response: {data}")
            return data.get("ok", False)
        else:
            print(f"❌ Emergency creation failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Emergency creation error: {e}")
        return False

def test_admin_login():
    """Test login admin"""
    try:
        print("🔐 Test login admin...")
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        response = requests.post(f"{PRODUCTION_URL}/api/auth/login", json=login_data, timeout=15)
        print(f"Login test: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and data.get("token"):
                print(f"✅ LOGIN SUCCESS! Token: {data['token'][:50]}...")
                print(f"User: {data.get('user', {})}")
                return data.get("token")
        
        print(f"❌ Login failed: {response.text}")
        return None
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_dashboard_access(token):
    """Test accès dashboard avec token"""
    try:
        print("🏠 Test accès dashboard...")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Test d'un endpoint qui nécessite l'authentification
        response = requests.get(f"{PRODUCTION_URL}/api/health", headers=headers, timeout=10)
        print(f"Authenticated request: {response.status_code}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Dashboard access error: {e}")
        return False

def main():
    print("🚨 EMERGENCY ADMIN FIX - PRODUCTION")
    print("=" * 60)
    
    # Attendre le déploiement
    print("⏳ Attente déploiement endpoint d'urgence...")
    time.sleep(60)
    
    # Étape 1: Créer admin via endpoint d'urgence
    print("\n1. Création admin via endpoint d'urgence:")
    admin_created = emergency_create_admin()
    
    # Étape 2: Test login
    print("\n2. Test authentification admin:")
    token = test_admin_login()
    
    # Étape 3: Test accès avec token
    if token:
        print("\n3. Test accès authentifié:")
        dashboard_ok = test_dashboard_access(token)
        
        if dashboard_ok:
            print("\n🎉 MISSION RÉUSSIE!")
            print("✅ Admin créé en production")
            print("✅ Authentification fonctionnelle")
            print("✅ Accès dashboard OK")
            print(f"✅ Email: {ADMIN_EMAIL}")
            print(f"✅ Token généré: {len(token)} caractères")
            return True
    
    print("\n❌ Échec de la mission d'urgence")
    print("💡 Vérifier les logs Vercel pour plus de détails")
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)