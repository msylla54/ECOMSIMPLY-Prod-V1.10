#!/usr/bin/env python3
"""
MongoDB Database Inventory Script
Génère un inventaire complet de la base de données actuelle
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

async def inventory_database():
    """
    Effectue un inventaire complet de la base de données MongoDB
    """
    try:
        # Configuration depuis les variables d'environnement
        mongo_url = os.getenv("MONGO_URL")
        db_name = os.getenv("DB_NAME", "ecomsimply_production")
        
        if not mongo_url:
            # Fallback vers URL de production pour test
            mongo_url = "mongodb+srv://ecomsimply-app:xIP7EfOXhODZdp0k@ecomsimply.xagju9s.mongodb.net"
            db_name = "ecomsimply_production"
        
        print(f"🔍 === INVENTAIRE BASE DE DONNÉES ===")
        print(f"Connexion : {mongo_url[:50]}...")
        print(f"Base de données : {db_name}")
        print(f"Timestamp : {datetime.utcnow().isoformat()}")
        print()
        
        # Connexion MongoDB
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=10000)
        db = client[db_name]
        
        # Test de connexion
        await client.admin.command('ping')
        print("✅ Connexion MongoDB réussie")
        
        # Inventaire des collections
        collection_names = await db.list_collection_names()
        print(f"📋 Collections trouvées : {len(collection_names)}")
        
        inventory = {
            "database": db_name,
            "timestamp": datetime.utcnow().isoformat(),
            "connection_test": "success",
            "collections": {},
            "summary": {
                "total_collections": len(collection_names),
                "total_documents": 0,
                "total_indexes": 0
            }
        }
        
        # Analyse détaillée par collection
        for collection_name in sorted(collection_names):
            print(f"\n📁 Analyse collection : {collection_name}")
            
            collection = db[collection_name]
            
            # Compter documents
            doc_count = await collection.count_documents({})
            
            # Lister les index
            indexes = []
            async for index in collection.list_indexes():
                indexes.append({
                    "name": index.get("name"),
                    "key": index.get("key"),
                    "unique": index.get("unique", False)
                })
            
            # Échantillon de documents (premiers 2)
            sample_docs = []
            async for doc in collection.find({}).limit(2):
                # Masquer les champs sensibles
                safe_doc = {}
                for key, value in doc.items():
                    if key in ["password", "passwordHash", "password_hash", "token", "secret"]:
                        safe_doc[key] = "***MASKED***"
                    elif key == "_id":
                        safe_doc[key] = str(value)
                    else:
                        safe_doc[key] = value
                sample_docs.append(safe_doc)
            
            collection_info = {
                "document_count": doc_count,
                "indexes": indexes,
                "sample_documents": sample_docs
            }
            
            inventory["collections"][collection_name] = collection_info
            inventory["summary"]["total_documents"] += doc_count
            inventory["summary"]["total_indexes"] += len(indexes)
            
            print(f"   📊 Documents : {doc_count}")
            print(f"   🔍 Index : {len(indexes)}")
            
        # Fermer connexion
        client.close()
        
        print(f"\n📈 === RÉSUMÉ INVENTAIRE ===")
        print(f"Collections : {inventory['summary']['total_collections']}")
        print(f"Documents totaux : {inventory['summary']['total_documents']}")
        print(f"Index totaux : {inventory['summary']['total_indexes']}")
        
        return inventory
        
    except Exception as e:
        print(f"❌ Erreur inventaire : {str(e)}")
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

async def main():
    inventory = await inventory_database()
    
    # Sauvegarder en JSON
    output_file = "diag/db_inventory.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Inventaire sauvegardé : {output_file}")
    
    # Générer rapport Markdown
    md_file = "diag/db_inventory.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(f"# 📊 INVENTAIRE BASE DE DONNÉES - {inventory.get('database', 'unknown')}\n\n")
        f.write(f"**Date** : {inventory.get('timestamp', 'unknown')}\n")
        f.write(f"**Base** : `{inventory.get('database', 'unknown')}`\n")
        f.write(f"**Status** : {'✅ Connecté' if inventory.get('connection_test') == 'success' else '❌ Erreur'}\n\n")
        
        if "summary" in inventory:
            f.write("## 📈 Résumé\n\n")
            f.write(f"- **Collections** : {inventory['summary']['total_collections']}\n")
            f.write(f"- **Documents totaux** : {inventory['summary']['total_documents']}\n")
            f.write(f"- **Index totaux** : {inventory['summary']['total_indexes']}\n\n")
        
        if "collections" in inventory:
            f.write("## 📋 Détail Collections\n\n")
            f.write("| Collection | Documents | Index | Unique Index |\n")
            f.write("|------------|-----------|-------|-------------|\n")
            
            for coll_name, coll_info in inventory["collections"].items():
                unique_count = sum(1 for idx in coll_info["indexes"] if idx.get("unique", False))
                f.write(f"| `{coll_name}` | {coll_info['document_count']} | {len(coll_info['indexes'])} | {unique_count} |\n")
        
        f.write(f"\n---\n*Généré le {datetime.utcnow().isoformat()}*\n")
    
    print(f"✅ Rapport Markdown généré : {md_file}")

if __name__ == "__main__":
    asyncio.run(main())