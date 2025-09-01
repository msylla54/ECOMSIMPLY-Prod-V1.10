#!/usr/bin/env python3
"""
Vérification des index en production
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_production_indexes():
    try:
        prod_url = "mongodb+srv://ecomsimply-app:xIP7EfOXhODZdp0k@ecomsimply.xagju9s.mongodb.net/ecomsimply_production"
        client = AsyncIOMotorClient(prod_url)
        db = client["ecomsimply_production"]
        
        print("🔍 === VÉRIFICATION INDEX PRODUCTION ===")
        
        # Vérifier index users (critique pour auth)
        if "users" in await db.list_collection_names():
            print("\n📋 Collection 'users' :")
            users_collection = db["users"]
            
            async for index in users_collection.list_indexes():
                index_name = index.get("name", "unknown")
                index_key = index.get("key", {})
                is_unique = index.get("unique", False)
                
                print(f"  - {index_name}: {index_key} {'(UNIQUE)' if is_unique else ''}")
                
                # Vérifier index email unique
                if "email" in index_key and is_unique:
                    print("    ✅ Index email unique détecté")
        
        # Test insertion duplicate pour valider contrainte unique
        print("\n🧪 Test contrainte unique email :")
        try:
            test_user = {
                "email": "test-duplicate@example.com",
                "name": "Test Duplicate"
            }
            
            # Insérer une première fois
            await db.users.insert_one(test_user.copy())
            print("  ✅ Premier insert réussi")
            
            # Essayer d'insérer le même email (doit échouer)
            try:
                await db.users.insert_one(test_user.copy())
                print("  ❌ ERREUR: Duplicate autorisé (index unique manquant)")
            except Exception as e:
                if "duplicate" in str(e).lower():
                    print("  ✅ Contrainte unique fonctionnelle")
                else:
                    print(f"  ⚠️ Erreur inattendue : {e}")
            
            # Nettoyer le test
            await db.users.delete_many({"email": "test-duplicate@example.com"})
            print("  🧹 Données de test nettoyées")
            
        except Exception as e:
            print(f"  ❌ Erreur test contrainte : {e}")
        
        client.close()
        print("\n✅ Vérification index terminée")
        
    except Exception as e:
        print(f"❌ Erreur vérification index : {e}")

if __name__ == "__main__":
    asyncio.run(check_production_indexes())