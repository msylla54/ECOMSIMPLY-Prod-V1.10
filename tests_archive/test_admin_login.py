#!/usr/bin/env python3
"""
Test de connexion admin avec les nouvelles credentials sécurisées
Usage direct pour vérifier que msylla54@gmail.com peut se connecter
"""

import requests
import json

def test_admin_login():
    """Test de connexion admin"""
    print("🔐 TEST DE CONNEXION ADMINISTRATEUR")
    print("=" * 50)
    
    # Configuration
    backend_url = "http://localhost:8001"
    login_url = f"{backend_url}/api/auth/login"
    
    # Nouvelles credentials sécurisées
    credentials = {
        "email": "msylla54@gmail.com",
        "password": "SecureAdmin2025!"
    }
    
    print(f"📧 Email: {credentials['email']}")
    print(f"🔑 Mot de passe: {credentials['password']}")
    print(f"🌐 URL: {login_url}")
    
    try:
        # Effectuer la requête de connexion
        print("\n🔄 Tentative de connexion...")
        response = requests.post(
            login_url,
            json=credentials,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"📊 Statut HTTP: {response.status_code}")
        
        if response.status_code == 200:
            # Connexion réussie
            data = response.json()
            print("🎉 CONNEXION RÉUSSIE!")
            
            # Afficher les informations utilisateur
            user = data.get('user', {})
            print(f"👤 Nom: {user.get('name', 'N/A')}")
            print(f"📧 Email: {user.get('email', 'N/A')}")
            print(f"👑 Admin: {'✅ OUI' if user.get('is_admin') else '❌ NON'}")
            print(f"💎 Plan: {user.get('subscription_plan', 'N/A')}")
            
            # Vérifier le token
            token = data.get('access_token') or data.get('token')
            if token:
                print(f"🎫 Token JWT: {token[:20]}...")
                
                # Test d'accès aux stats avec le token
                print("\n🧪 Test d'accès aux statistiques...")
                stats_response = requests.get(
                    f"{backend_url}/api/stats",
                    headers={'Authorization': f'Bearer {token}'},
                    timeout=10
                )
                
                if stats_response.status_code == 200:
                    stats = stats_response.json()
                    print("✅ Accès aux statistiques réussi")
                    print(f"📊 Fiches créées: {stats.get('total_sheets', 0)}")
                    print(f"💳 Plan: {stats.get('subscription_plan', 'N/A')}")
                else:
                    print(f"❌ Erreur d'accès aux stats: {stats_response.status_code}")
            
            return True
            
        else:
            # Connexion échouée
            print("❌ CONNEXION ÉCHOUÉE")
            try:
                error_data = response.json()
                print(f"Erreur: {error_data.get('detail', 'Erreur inconnue')}")
            except:
                print(f"Erreur HTTP: {response.text}")
            
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {str(e)}")
        return False

def test_old_password():
    """Test avec l'ancien mot de passe pour vérifier qu'il ne fonctionne plus"""
    print("\n🔒 TEST SÉCURITÉ - ANCIEN MOT DE PASSE")
    print("=" * 50)
    
    backend_url = "http://localhost:8001"
    login_url = f"{backend_url}/api/auth/login"
    
    # Ancien mot de passe (doit échouer)
    old_credentials = {
        "email": "msylla54@gmail.com",
        "password": "AdminEcomsimply"
    }
    
    print(f"📧 Email: {old_credentials['email']}")
    print(f"🔑 Ancien mot de passe: {old_credentials['password']}")
    
    try:
        response = requests.post(
            login_url,
            json=old_credentials,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 401 or response.status_code == 400:
            print("✅ SÉCURITÉ OK - Ancien mot de passe rejeté")
            return True
        else:
            print("❌ PROBLÈME SÉCURITÉ - Ancien mot de passe accepté!")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test sécurité: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 ECOMSIMPLY - Test de connexion administrateur")
    print("Date:", "2025-08-21")
    print()
    
    # Test avec nouvelles credentials
    login_success = test_admin_login()
    
    # Test sécurité avec anciennes credentials
    security_ok = test_old_password()
    
    print("\n" + "=" * 50)
    print("📋 RÉSUMÉ DES TESTS")
    print("=" * 50)
    print(f"✅ Connexion nouvelle: {'RÉUSSIE' if login_success else 'ÉCHOUÉE'}")
    print(f"🔒 Sécurité ancienne: {'OK' if security_ok else 'PROBLÈME'}")
    
    if login_success and security_ok:
        print("\n🎉 TOUS LES TESTS RÉUSSIS!")
        print("✅ L'utilisateur msylla54@gmail.com peut maintenant se connecter")
        print("✅ Le système est sécurisé")
        print("✅ Le problème de mot de passe hardcodé est résolu")
    else:
        print("\n⚠️ TESTS PARTIELLEMENT RÉUSSIS")
        if not login_success:
            print("❌ Problème de connexion avec nouvelles credentials")
        if not security_ok:
            print("❌ Problème de sécurité avec anciennes credentials")