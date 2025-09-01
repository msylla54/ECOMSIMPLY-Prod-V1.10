#!/usr/bin/env python3
"""
Test Production Database Access
Vérifie l'accès à la base de production et son état
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def test_production_db():
    """
    Teste l'accès à la base de production
    """
    try:
        # URL de production fournie par l'utilisateur
        prod_url = "mongodb+srv://ecomsimply-app:xIP7EfOXhODZdp0k@ecomsimply.xagju9s.mongodb.net"
        
        print(f"🔍 === TEST BASE PRODUCTION ===")
        print(f"Timestamp : {datetime.utcnow().isoformat()}")
        print()
        
        # Test base dev actuelle
        print("📋 Test ecomsimply_production :")
        client_dev = AsyncIOMotorClient(prod_url + "/ecomsimply_production?retryWrites=true&w=majority")
        db_dev = client_dev["ecomsimply_production"]
        await client_dev.admin.command('ping')
        
        collections_dev = await db_dev.list_collection_names()
        total_docs_dev = 0
        
        for coll_name in collections_dev:
            count = await db_dev[coll_name].count_documents({})
            total_docs_dev += count
            print(f"  - {coll_name}: {count} documents")
        
        print(f"✅ ecomsimply_production : {len(collections_dev)} collections, {total_docs_dev} documents")
        client_dev.close()
        
        # Test base prod cible
        print("\n📋 Test ecomsimply_production :")
        client_prod = AsyncIOMotorClient(prod_url + "/ecomsimply_production?retryWrites=true&w=majority")
        db_prod = client_prod["ecomsimply_production"]
        await client_prod.admin.command('ping')
        
        collections_prod = await db_prod.list_collection_names()
        total_docs_prod = 0
        
        for coll_name in collections_prod:
            count = await db_prod[coll_name].count_documents({})
            total_docs_prod += count
            print(f"  - {coll_name}: {count} documents")
        
        print(f"✅ ecomsimply_production : {len(collections_prod)} collections, {total_docs_prod} documents")
        client_prod.close()
        
        return {
            "dev": {"collections": len(collections_dev), "documents": total_docs_dev},
            "prod": {"collections": len(collections_prod), "documents": total_docs_prod}
        }
        
    except Exception as e:
        print(f"❌ Erreur test production : {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    result = asyncio.run(test_production_db())
    print(f"\n📊 Résultat : {result}")