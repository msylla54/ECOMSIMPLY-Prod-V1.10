#!/usr/bin/env python3
"""
Simple Mock Publication Test - Debug Authentication
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BACKEND_URL = "https://ecomsimply.com/api"

async def test_auth_and_publication():
    """Test simple d'authentification et publication"""
    
    async with aiohttp.ClientSession() as session:
        # 1. Créer utilisateur
        user_email = f"test_debug_{int(datetime.now().timestamp())}@test.com"
        user_password = "TestDebug123!"
        
        print(f"🔧 Création utilisateur: {user_email}")
        
        register_data = {
            "email": user_email,
            "name": "Test Debug User",
            "password": user_password
        }
        
        async with session.post(f"{BACKEND_URL}/auth/register", json=register_data) as response:
            print(f"📝 Register status: {response.status}")
            if response.status == 200:
                result = await response.json()
                print(f"📝 Register response: {json.dumps(result, indent=2)}")
                token = result.get("token") or result.get("access_token")
                if token:
                    print(f"✅ Token obtenu via register: {token[:20]}...")
                else:
                    print("⚠️ Pas de token dans register, tentative login...")
                    
                    # Essayer login
                    login_data = {"email": user_email, "password": user_password}
                    async with session.post(f"{BACKEND_URL}/auth/login", json=login_data) as login_response:
                        print(f"📝 Login status: {login_response.status}")
                        if login_response.status == 200:
                            login_result = await login_response.json()
                            print(f"📝 Login response: {json.dumps(login_result, indent=2)}")
                            token = login_result.get("token") or login_result.get("access_token")
                            if token:
                                print(f"✅ Token obtenu via login: {token[:20]}...")
                            else:
                                print("❌ Pas de token dans login")
                                return
                        else:
                            print(f"❌ Login failed: {await login_response.text()}")
                            return
            else:
                print(f"❌ Register failed: {await response.text()}")
                return
        
        # 2. Test status publication (sans auth)
        print(f"\n🔧 Test status publication")
        async with session.get(f"{BACKEND_URL}/status/publication") as response:
            print(f"📝 Status publication: {response.status}")
            if response.status == 200:
                result = await response.json()
                print(f"✅ Status OK - Mode mock: {result.get('status', {}).get('mock_mode', 'unknown')}")
                print(f"✅ Auto publish: {result.get('status', {}).get('auto_publish', 'unknown')}")
            else:
                print(f"❌ Status failed: {await response.text()}")
        
        # 3. Test génération avec auth
        if token:
            print(f"\n🔧 Test génération avec token")
            headers = {"Authorization": f"Bearer {token}"}
            
            request_data = {
                "product_name": "iPhone 15 Pro Test",
                "product_description": "Test simple pour debug auth",
                "category": "Electronics",
                "generate_image": False,
                "number_of_images": 0,
                "language": "fr"
            }
            
            async with session.post(
                f"{BACKEND_URL}/generate-sheet",
                json=request_data,
                headers=headers
            ) as response:
                print(f"📝 Generate sheet status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Génération réussie!")
                    print(f"   - Titre: {result.get('generated_title', 'N/A')[:50]}...")
                    print(f"   - Auto publish: {result.get('auto_publish_enabled', 'N/A')}")
                    print(f"   - Publications: {len(result.get('publication_results', []))}")
                    
                    # Analyser les résultats de publication
                    pub_results = result.get('publication_results', [])
                    if pub_results:
                        successful = [p for p in pub_results if p.get('success')]
                        print(f"   - Publications réussies: {len(successful)}/{len(pub_results)}")
                        for pub in successful:
                            print(f"     * {pub.get('platform')}: {pub.get('mode')} mode")
                    else:
                        print("   - Aucun résultat de publication")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ Generate sheet failed: {response.status}")
                    print(f"   Error: {error_text}")
        
        # 4. Test historique publications
        print(f"\n🔧 Test historique publications")
        async with session.get(f"{BACKEND_URL}/publications/history?limit=10") as response:
            print(f"📝 Publications history status: {response.status}")
            if response.status == 200:
                result = await response.json()
                publications = result.get('publications', [])
                print(f"✅ Historique OK - {len(publications)} publications trouvées")
                if publications:
                    for pub in publications[:3]:  # Afficher les 3 premières
                        print(f"   - {pub.get('platform')}: {pub.get('product_name')} ({pub.get('status')})")
            else:
                print(f"❌ History failed: {await response.text()}")

if __name__ == "__main__":
    asyncio.run(test_auth_and_publication())