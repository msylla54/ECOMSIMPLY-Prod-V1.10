#!/usr/bin/env python3
# ================================================================================
# MIGRATION SIMPLE VERS PREMIUM UNIQUEMENT
# ================================================================================

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def migrate_to_premium():
    """Migration simplifiée vers Premium uniquement"""
    
    # Configuration
    MONGO_URL = "mongodb://localhost:27017/ecomsimply_production"
    
    try:
        print("🔗 Connexion à MongoDB...")
        client = AsyncIOMotorClient(MONGO_URL)
        db = client.ecomsimply_production
        
        # Test de connexion
        await db.command("ping")
        print("✅ Connexion réussie!")
        
        # Statistiques avant migration
        print("\n📊 ÉTAT AVANT MIGRATION:")
        pipeline = [{"$group": {"_id": "$subscription_plan", "count": {"$sum": 1}}}]
        async for result in db.users.aggregate(pipeline):
            print(f"   Plan {result['_id']}: {result['count']} utilisateurs")
        
        total_before = await db.users.count_documents({})
        print(f"   Total: {total_before} utilisateurs")
        
        # Migration - Mettre tous les utilisateurs en Premium
        print("\n🚀 MIGRATION EN COURS...")
        
        # Utilisateurs non-Premium à migrer
        non_premium_count = await db.users.count_documents({
            "subscription_plan": {"$ne": "premium"}
        })
        
        if non_premium_count == 0:
            print("✅ Tous les utilisateurs sont déjà en Premium!")
            return True
        
        print(f"📋 {non_premium_count} utilisateurs à migrer vers Premium")
        
        # Migration en lot
        update_result = await db.users.update_many(
            {"subscription_plan": {"$ne": "premium"}},
            {"$set": {
                "subscription_plan": "premium",
                "subscription_status": "trialing",
                "has_used_trial": False,
                "generate_images": True,
                "include_images_manual": True,
                "monthly_sheets_limit": float('inf'),
                "migration_date": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }}
        )
        
        print(f"✅ Migration terminée - {update_result.modified_count} utilisateurs mis à jour")
        
        # Statistiques après migration
        print("\n📊 ÉTAT APRÈS MIGRATION:")
        async for result in db.users.aggregate(pipeline):
            print(f"   Plan {result['_id']}: {result['count']} utilisateurs")
        
        total_after = await db.users.count_documents({})
        premium_count = await db.users.count_documents({"subscription_plan": "premium"})
        
        print(f"   Total: {total_after} utilisateurs")
        print(f"   Premium: {premium_count} utilisateurs")
        
        # Validation
        if premium_count == total_after:
            print("\n✅ MIGRATION RÉUSSIE! Tous les utilisateurs sont maintenant en Premium")
            
            # Nettoyer les anciens plans dans subscription_plans si la collection existe
            try:
                await db.subscription_plans.update_many(
                    {"plan_id": {"$in": ["gratuit", "free", "pro"]}},
                    {"$set": {"active": False, "archived_at": datetime.utcnow()}}
                )
                print("🧹 Anciens plans archivés")
            except:
                print("ℹ️ Collection subscription_plans n'existe pas encore")
                
            return True
        else:
            print(f"❌ PROBLÈME: {total_after - premium_count} utilisateurs ne sont pas en Premium")
            return False
        
    except Exception as e:
        print(f"❌ Erreur migration: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    print("🚀 MIGRATION VERS PREMIUM UNIQUEMENT")
    print("=" * 50)
    
    success = asyncio.run(migrate_to_premium())
    
    if success:
        print("\n🎉 MIGRATION TERMINÉE AVEC SUCCÈS!")
        print("💡 Tous les utilisateurs ont maintenant le plan Premium avec essai 3 jours disponible")
    else:
        print("\n❌ MIGRATION ÉCHOUÉE!")