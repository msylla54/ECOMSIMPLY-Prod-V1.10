#!/usr/bin/env python3
"""
Migration 0002: Seed Subscription Plans from hardcoded data to MongoDB
Idempotent script - safe to run multiple times
"""

import os
import sys
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError

# Add backend to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def seed_subscription_plans():
    """Seed subscription_plans collection with hardcoded data"""
    
    # MongoDB connection
    MONGO_URL = os.getenv("MONGO_URL")
    if not MONGO_URL:
        raise Exception("MONGO_URL environment variable is required")
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client["ecomsimply_production"]
    
    print("🔄 Migration 0002: Seeding Subscription Plans...")
    
    # Hardcoded plans from server.py
    plans_data = [
        {
            "_id": "plan_starter",
            "plan_id": "starter",
            "name": "Starter",
            "price": 29.0,
            "currency": "EUR",
            "period": "month",
            "features": [
                "Jusqu'à 50 produits/mois",
                "Génération IA des fiches produits",
                "Optimisation SEO de base", 
                "Support email"
            ],
            "active": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": "plan_pro",
            "plan_id": "pro",
            "name": "Pro", 
            "price": 79.0,
            "currency": "EUR",
            "period": "month",
            "features": [
                "Jusqu'à 200 produits/mois",
                "Génération IA avancée",
                "Optimisation SEO Premium",
                "A/B Testing",
                "Support prioritaire"
            ],
            "active": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": "plan_enterprise", 
            "plan_id": "enterprise",
            "name": "Enterprise",
            "price": 199.0,
            "currency": "EUR",
            "period": "month",
            "features": [
                "Produits illimités",
                "IA personnalisée", 
                "Intégrations sur mesure",
                "Manager dédié",
                "SLA 99.9%"
            ],
            "active": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    # Create indexes
    try:
        await db["subscription_plans"].create_index([("plan_id", 1)], unique=True)
        await db["subscription_plans"].create_index([("active", 1), ("price", 1)])
        print("✅ Created indexes: subscription_plans.plan_id (unique) + active/price")
    except Exception as e:
        print(f"ℹ️  Indexes already exist or error: {e}")
    
    # Seed plans
    inserted_count = 0
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for plan in plans_data:
        try:
            # Upsert by _id (idempotent)
            result = await db["subscription_plans"].update_one(
                {"_id": plan["_id"]},
                {"$setOnInsert": plan},
                upsert=True
            )
            
            if result.upserted_id:
                inserted_count += 1
                print(f"✅ Inserted plan: {plan['name']} (€{plan['price']})")
            else:
                skipped_count += 1
                print(f"⏭️  Skipped existing plan: {plan['name']}")
                
        except DuplicateKeyError:
            skipped_count += 1
            print(f"⏭️  Duplicate plan: {plan['name']}")
        except Exception as e:
            error_count += 1
            print(f"❌ Error inserting plan {plan['name']}: {e}")
    
    # Summary
    total_count = await db["subscription_plans"].count_documents({})
    
    print(f"""
📊 Migration 0002 Results:
   - Inserted: {inserted_count}
   - Updated: {updated_count}
   - Skipped: {skipped_count}
   - Errors: {error_count}
   - Total plans in DB: {total_count}
""")
    
    client.close()
    return {
        "inserted": inserted_count,
        "updated": updated_count,
        "skipped": skipped_count,
        "errors": error_count,
        "total": total_count
    }

if __name__ == "__main__":
    # Load environment
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    asyncio.run(seed_subscription_plans())