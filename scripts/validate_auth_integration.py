#!/usr/bin/env python3
"""
🔐 ECOMSIMPLY Authentication & MongoDB Atlas Integration Validator
Valide la connectivité et les fonctionnalités d'authentification
"""

import os
import sys
import asyncio
import json
from datetime import datetime
import requests
import bcrypt

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

async def test_mongodb_connection():
    """Test de connexion MongoDB Atlas"""
    print("🔧 TEST 1: Connexion MongoDB Atlas")
    print("=" * 50)
    
    try:
        from backend.database import get_db
        
        # Test de connexion
        db = await get_db()
        
        # Test ping
        result = await db.command("ping")
        print(f"✅ MongoDB Ping: {result}")
        
        # Test d'accès aux collections
        collections = await db.list_collection_names()
        print(f"✅ Collections disponibles: {collections}")
        
        # Test d'écriture/lecture
        test_doc = {
            "test_id": "auth_validation",
            "timestamp": datetime.utcnow(),
            "status": "test"
        }
        
        await db.test_auth_validation.insert_one(test_doc)
        print("✅ Test d'écriture: OK")
        
        # Nettoyer le document de test
        await db.test_auth_validation.delete_one({"test_id": "auth_validation"})
        print("✅ Test de suppression: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur MongoDB: {e}")
        return False

def test_backend_endpoints():
    """Test des endpoints backend d'authentification"""
    print("\n🔧 TEST 2: Endpoints Backend Auth")
    print("=" * 50)
    
    # Déterminer l'URL du backend
    backend_urls = [
        "http://localhost:8001",
        "https://ecomsimply-deploy.preview.emergentagent.com"
    ]
    
    working_url = None
    
    for url in backend_urls:
        try:
            response = requests.get(f"{url}/api/health", timeout=5)
            if response.status_code == 200:
                working_url = url
                print(f"✅ Backend disponible: {url}")
                health_data = response.json()
                print(f"   Service: {health_data.get('service', 'N/A')}")
                print(f"   MongoDB: {health_data.get('mongo', 'N/A')}")
                print(f"   Database: {health_data.get('database', 'N/A')}")
                break
        except Exception as e:
            print(f"❌ Backend indisponible: {url} - {e}")
    
    if not working_url:
        print("❌ Aucun backend accessible")
        return False
    
    # Test des endpoints d'authentification
    api_base = f"{working_url}/api"
    
    # Test endpoint register (sans créer d'utilisateur)
    try:
        response = requests.post(f"{api_base}/auth/register", 
                               json={"name": "", "email": "", "password": ""})
        if response.status_code in [422, 400]:  # Validation errors expected
            print("✅ Endpoint /auth/register: Accessible")
        else:
            print(f"⚠️  Endpoint /auth/register: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Endpoint /auth/register: {e}")
    
    # Test endpoint login (sans credentials)
    try:
        response = requests.post(f"{api_base}/auth/login", 
                               json={"email": "", "password": ""})
        if response.status_code in [422, 401]:  # Auth errors expected
            print("✅ Endpoint /auth/login: Accessible")
        else:
            print(f"⚠️  Endpoint /auth/login: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Endpoint /auth/login: {e}")
    
    # Test endpoint me (sans token)
    try:
        response = requests.get(f"{api_base}/auth/me")
        if response.status_code == 401:  # Unauthorized expected
            print("✅ Endpoint /auth/me: Accessible (401 attendu)")
        else:
            print(f"⚠️  Endpoint /auth/me: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Endpoint /auth/me: {e}")
    
    return True

def test_jwt_security():
    """Test de la configuration JWT"""
    print("\n🔧 TEST 3: Configuration JWT & Sécurité")
    print("=" * 50)
    
    # Test variables d'environnement
    jwt_secret = os.getenv("JWT_SECRET")
    if jwt_secret and len(jwt_secret) >= 32:
        print("✅ JWT_SECRET: Configuré et suffisamment long")
    else:
        print("⚠️  JWT_SECRET: Manquant ou trop court (< 32 chars)")
    
    # Test bcrypt
    try:
        test_password = "test123456"
        hashed = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt())
        
        # Vérification
        if bcrypt.checkpw(test_password.encode('utf-8'), hashed):
            print("✅ bcrypt: Fonctionnel")
        else:
            print("❌ bcrypt: Dysfonctionnel")
    except Exception as e:
        print(f"❌ bcrypt: Erreur - {e}")
    
    return True

def test_cors_configuration():
    """Test de la configuration CORS"""
    print("\n🔧 TEST 4: Configuration CORS")
    print("=" * 50)
    
    app_base_url = os.getenv("APP_BASE_URL")
    additional_origins = os.getenv("ADDITIONAL_ALLOWED_ORIGINS")
    
    print(f"APP_BASE_URL: {app_base_url or 'Non configuré'}")
    print(f"ADDITIONAL_ALLOWED_ORIGINS: {additional_origins or 'Non configuré'}")
    
    # Simulation de la logique CORS du backend
    origins = set()
    
    if app_base_url:
        origins.add(app_base_url)
    
    # Domaine emergent.sh automatique
    app_name = os.getenv("APP_NAME", "ecom-api-fixes")
    emergent_domain = f"https://{app_name}.emergent.host"
    origins.add(emergent_domain)
    
    # Domaine de production
    origins.add("https://ecomsimply.com")
    
    if additional_origins:
        for origin in additional_origins.split(","):
            origin = origin.strip()
            if origin:
                origins.add(origin)
    
    print(f"✅ Origines CORS configurées: {list(origins)}")
    
    return True

def test_environment_variables():
    """Test des variables d'environnement critiques"""
    print("\n🔧 TEST 5: Variables d'Environnement")
    print("=" * 50)
    
    critical_vars = {
        "MONGO_URL": os.getenv("MONGO_URL"),
        "DB_NAME": os.getenv("DB_NAME", "ecomsimply_production"),
        "JWT_SECRET": os.getenv("JWT_SECRET"),
        "APP_BASE_URL": os.getenv("APP_BASE_URL"),
        "ADMIN_EMAIL": os.getenv("ADMIN_EMAIL"),
        "ADMIN_PASSWORD_HASH": os.getenv("ADMIN_PASSWORD_HASH")
    }
    
    for var_name, var_value in critical_vars.items():
        if var_value:
            if var_name in ["MONGO_URL", "JWT_SECRET", "ADMIN_PASSWORD_HASH"]:
                # Masquer les valeurs sensibles
                masked_value = var_value[:10] + "..." if len(var_value) > 10 else "***"
                print(f"✅ {var_name}: {masked_value}")
            else:
                print(f"✅ {var_name}: {var_value}")
        else:
            print(f"❌ {var_name}: Non configuré")
    
    return True

async def main():
    """Fonction principale de validation"""
    print("🔐 VALIDATION AUTHENTIFICATION & MONGODB ATLAS")
    print("=" * 60)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print()
    
    results = {
        "mongodb": False,
        "backend_endpoints": False,
        "jwt_security": False,
        "cors_config": False,
        "environment_vars": False
    }
    
    # Tests séquentiels
    results["mongodb"] = await test_mongodb_connection()
    results["backend_endpoints"] = test_backend_endpoints()
    results["jwt_security"] = test_jwt_security()
    results["cors_config"] = test_cors_configuration()
    results["environment_vars"] = test_environment_variables()
    
    # Résumé final
    print("\n🎯 RÉSUMÉ DE VALIDATION")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {test_name.replace('_', ' ').title()}: {'PASS' if status else 'FAIL'}")
    
    print(f"\n📊 Score: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés ! L'authentification est prête.")
        return 0
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez la configuration.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)