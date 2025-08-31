#!/usr/bin/env python3
"""
Test rapide pour vérifier le problème de la page démo
"""

import requests

def test_demo_page():
    """Test de la page démo sur différents serveurs"""
    print("🧪 TEST PAGE DÉMO - DIAGNOSTIC")
    print("=" * 40)
    
    # Test 1: API Backend health
    try:
        response = requests.get("http://localhost:8001/api/health", timeout=5)
        print(f"✅ Backend API: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend API: {str(e)}")
    
    # Test 2: API Demo routes
    try:
        response = requests.get("http://localhost:8001/api/demo/amazon/status", timeout=5)
        print(f"✅ Demo API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Demo data: {data.get('status', 'N/A')}")
    except Exception as e:
        print(f"❌ Demo API: {str(e)}")
    
    # Test 3: Production site
    try:
        response = requests.get("https://ecomsimply.com/demo", timeout=10)
        print(f"📊 Production demo: {response.status_code}")
        if response.status_code == 404:
            print("   ⚠️ 404 confirmé - problème de configuration serveur")
        elif response.status_code == 200:
            if "PremiumDemo" in response.text:
                print("   ✅ Page demo fonctionne")
            else:
                print("   ⚠️ Page chargée mais contenu incorrect")
    except Exception as e:
        print(f"❌ Production demo: {str(e)}")
    
    # Test 4: Autres routes production
    test_routes = ["/", "/api/health"]
    for route in test_routes:
        try:
            response = requests.get(f"https://ecomsimply.com{route}", timeout=5)
            print(f"📊 Production {route}: {response.status_code}")
        except Exception as e:
            print(f"❌ Production {route}: {str(e)}")

if __name__ == "__main__":
    test_demo_page()