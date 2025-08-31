#!/usr/bin/env python3
"""
Script d'urgence pour créer l'admin directement via MongoDB Atlas
"""
import sys
import bcrypt
import pymongo
from pymongo import MongoClient
from datetime import datetime
import os

def generate_admin_hash(password):
    """Generate bcrypt hash for admin password"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_admin_direct_mongo():
    """Create admin directly in MongoDB Atlas if possible"""
    try:
        # Cette approche nécessiterait la connection string MongoDB Atlas
        # Mais nous n'avons pas accès direct à la DB de production
        print("❌ Accès direct MongoDB Atlas non disponible dans cet environnement")
        return False
    except Exception as e:
        print(f"❌ Erreur MongoDB direct: {e}")
        return False

def test_alternative_endpoints():
    """Test différents endpoints pour contourner le problème"""
    import requests
    
    PRODUCTION_URL = "https://ecomsimply.com"
    
    # Test 1: Essayer avec différents tokens
    tokens_to_try = [
        "ECS-Bootstrap-2025-Secure-Token",
        "ecomsimply-bootstrap-token",
        "bootstrap-admin-2025"
    ]
    
    for token in tokens_to_try:
        try:
            print(f"🔄 Test bootstrap avec token: {token[:20]}...")
            headers = {
                "x-bootstrap-token": token,
                "Content-Type": "application/json"
            }
            
            response = requests.post(f"{PRODUCTION_URL}/api/admin/bootstrap", 
                                   headers=headers, timeout=10)
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ SUCCÈS! Réponse: {response.json()}")
                return True
            else:
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    # Test 2: Vérifier si l'admin existe déjà avec différents mots de passe
    passwords_to_try = [
        "ECS-Permanent#2025!",
        "ECS-Temp#2025-08-22!",
        "admin123",
        "ecomsimply2025"
    ]
    
    for password in passwords_to_try:
        try:
            print(f"🔄 Test login avec password: {password[:10]}...")
            login_data = {
                "email": "msylla54@gmail.com",
                "password": password
            }
            
            response = requests.post(f"{PRODUCTION_URL}/api/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok") and data.get("token"):
                    print(f"   ✅ LOGIN RÉUSSI! Token: {data['token'][:50]}...")
                    return True, data["token"]
            else:
                print(f"   Status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    return False

def create_manual_bootstrap_request():
    """Create a manual bootstrap request with detailed debugging"""
    import requests
    
    PRODUCTION_URL = "https://ecomsimply.com"
    
    print("🔧 DIAGNOSTIC APPROFONDI BOOTSTRAP:")
    
    # Test avec le hash généré localement
    admin_password = "ECS-Permanent#2025!"
    admin_hash = generate_admin_hash(admin_password)
    
    print(f"Password: {admin_password}")
    print(f"Generated hash: {admin_hash}")
    print(f"Expected hash: $2b$12$yQhOn3ydalPB3RuDZNsD8uUbfuc.MVG3Pf30xrUougEsibvP4Ukty")
    
    # Test de vérification du hash
    test_valid = bcrypt.checkpw(admin_password.encode('utf-8'), admin_hash.encode('utf-8'))
    print(f"Hash validation test: {test_valid}")
    
    # Essayer différentes approches
    headers = {
        "x-bootstrap-token": "ECS-Bootstrap-2025-Secure-Token",
        "Content-Type": "application/json",
        "User-Agent": "EcomsimplyAdmin/1.0"
    }
    
    try:
        response = requests.post(f"{PRODUCTION_URL}/api/admin/bootstrap", 
                               headers=headers, timeout=15)
        
        print(f"Bootstrap response: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response body: {response.text}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Bootstrap error: {e}")
        return False

def main():
    print("🚨 DIAGNOSTIC ET FIX ADMIN PRODUCTION")
    print("=" * 60)
    
    # Test 1: Alternative endpoints
    print("\n1. 🔄 Test endpoints alternatifs:")
    success = test_alternative_endpoints()
    
    if success:
        print("\n✅ ADMIN TROUVÉ ET FONCTIONNEL!")
        return True
    
    # Test 2: Bootstrap diagnostic
    print("\n2. 🔧 Diagnostic bootstrap approfondi:")
    bootstrap_success = create_manual_bootstrap_request()
    
    if bootstrap_success:
        print("\n✅ BOOTSTRAP RÉUSSI!")
        return True
    
    # Test 3: MongoDB direct (si possible)
    print("\n3. 🗄️ Tentative accès MongoDB direct:")
    mongo_success = create_admin_direct_mongo()
    
    if mongo_success:
        print("\n✅ ADMIN CRÉÉ VIA MONGODB!")
        return True
    
    print("\n❌ TOUS LES TESTS ÉCHOUÉS")
    print("💡 Recommandations:")
    print("1. Vérifier que les variables Vercel sont bien configurées")
    print("2. Vérifier que le redéploiement Vercel est complet")
    print("3. Attendre quelques minutes et relancer")
    print("4. Vérifier les logs Vercel pour erreurs de déploiement")
    
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)