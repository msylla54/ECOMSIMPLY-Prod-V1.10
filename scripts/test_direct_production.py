#!/usr/bin/env python3
"""
Test Direct Production Database Connection
Teste la connexion directe à ecomsimply_production
"""

import os
import sys
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

async def test_production_direct():
    """
    Test connexion directe à la base production avec credentials réels
    """
    try:
        # URL production complète
        prod_url = "mongodb+srv://ecomsimply-app:xIP7EfOXhODZdp0k@ecomsimply.xagju9s.mongodb.net/ecomsimply_production?retryWrites=true&w=majority&appName=EcomSimply"
        
        print(f"🔄 === TEST CONNEXION PRODUCTION DIRECTE ===")
        print(f"Timestamp : {datetime.utcnow().isoformat()}")
        print(f"Base cible : ecomsimply_production")
        print()
        
        # Connexion MongoDB
        client = AsyncIOMotorClient(prod_url, serverSelectionTimeoutMS=10000)
        db = client["ecomsimply_production"]
        
        # Test ping
        await client.admin.command('ping')
        print("✅ Connexion MongoDB réussie")
        
        # Test collections
        collections = await db.list_collection_names()
        print(f"📋 Collections : {len(collections)}")
        
        total_docs = 0
        for coll_name in sorted(collections):
            count = await db[coll_name].count_documents({})
            total_docs += count
            print(f"  • {coll_name}: {count} documents")
        
        print(f"📊 Total documents : {total_docs}")
        
        # Test spécifique users
        users_count = 0
        if "users" in collections:
            users_count = await db.users.count_documents({})
            users_sample = []
            async for user in db.users.find({}, {"email": 1, "name": 1, "is_admin": 1}).limit(3):
                users_sample.append({
                    "email": user.get("email", "unknown"),
                    "name": user.get("name", "unknown"), 
                    "is_admin": user.get("is_admin", False)
                })
            
            print(f"👥 Échantillon utilisateurs :")
            for user in users_sample:
                admin_flag = " (ADMIN)" if user["is_admin"] else ""
                print(f"  • {user['email']} - {user['name']}{admin_flag}")
        
        # Test index email unique
        print(f"\n🔍 Test contrainte unique email...")
        try:
            # Essayer d'insérer un utilisateur test
            test_user = {
                "email": "test-production-validation@example.com",
                "name": "Test Production",
                "password_hash": "test123"
            }
            
            await db.users.insert_one(test_user)
            print("  ✅ Insert test réussi")
            
            # Tenter duplicate (doit échouer)
            try:
                await db.users.insert_one(test_user.copy())
                print("  ❌ ERREUR: Duplicate autorisé (problème index unique)")
            except Exception as e:
                if "duplicate" in str(e).lower():
                    print("  ✅ Contrainte unique email validée")
                else:
                    print(f"  ⚠️ Erreur inattendue: {e}")
            
            # Nettoyer
            await db.users.delete_many({"email": "test-production-validation@example.com"})
            print("  🧹 Nettoyage effectué")
            
        except Exception as e:
            print(f"  ❌ Erreur test contrainte: {e}")
        
        # Préparer résultat avant fermeture
        result = {
            "success": True,
            "collections": len(collections),
            "documents": total_docs,
            "users_count": users_count
        }
        
        client.close()
        return result
        
    except Exception as e:
        print(f"❌ Erreur connexion production: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = asyncio.run(test_production_direct())
    if result["success"]:
        print(f"\n🎉 Test production réussi !")
        print(f"📊 {result['collections']} collections, {result['documents']} documents")
    else:
        print(f"\n❌ Test production échoué: {result.get('error', 'unknown')}")
        exit(1)