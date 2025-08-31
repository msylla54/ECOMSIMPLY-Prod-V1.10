#!/usr/bin/env python3
"""
Migration 0004: Seed Public Stats from hardcoded data to MongoDB
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

async def seed_public_stats():
    """Seed stats_public collection with hardcoded data"""
    
    # MongoDB connection
    MONGO_URL = os.getenv("MONGO_URL")
    if not MONGO_URL:
        raise Exception("MONGO_URL environment variable is required")
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client["ecomsimply_production"]
    
    print("🔄 Migration 0004: Seeding Public Stats...")
    
    # Hardcoded stats from server.py
    stats_data = [
        {
            "_id": "stat_products_generated",
            "key": "products_generated",
            "value": 125000,
            "category": "performance",
            "display_name": "Produits Générés",
            "format_type": "number",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "_id": "stat_active_users", 
            "key": "active_users",
            "value": 2500,
            "category": "performance",
            "display_name": "Utilisateurs Actifs",
            "format_type": "number",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "_id": "stat_time_saved_hours",
            "key": "time_saved_hours", 
            "value": 50000,
            "category": "performance",
            "display_name": "Heures Économisées",
            "format_type": "number",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "_id": "stat_conversion_improvement",
            "key": "conversion_improvement",
            "value": "45%",
            "category": "performance",
            "display_name": "Amélioration Conversion",
            "format_type": "percentage",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "_id": "stat_seo_score_average",
            "key": "seo_score_average",
            "value": 92,
            "category": "performance",
            "display_name": "Score SEO Moyen",
            "format_type": "number",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    # Create indexes
    try:
        await db["stats_public"].create_index([("key", 1)], unique=True)
        await db["stats_public"].create_index([("category", 1), ("updated_at", -1)])
        print("✅ Created indexes: stats_public.key (unique) + category/updated_at")
    except Exception as e:
        print(f"ℹ️  Indexes already exist or error: {e}")
    
    # Seed stats
    inserted_count = 0
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for stat in stats_data:
        try:
            # Upsert by _id (idempotent)
            result = await db["stats_public"].update_one(
                {"_id": stat["_id"]},
                {"$setOnInsert": stat},
                upsert=True
            )
            
            if result.upserted_id:
                inserted_count += 1
                print(f"✅ Inserted stat: {stat['display_name']} = {stat['value']}")
            else:
                skipped_count += 1
                print(f"⏭️  Skipped existing stat: {stat['display_name']}")
                
        except DuplicateKeyError:
            skipped_count += 1
            print(f"⏭️  Duplicate stat: {stat['display_name']}")
        except Exception as e:
            error_count += 1
            print(f"❌ Error inserting stat {stat['display_name']}: {e}")
    
    # Summary
    total_count = await db["stats_public"].count_documents({})
    
    print(f"""
📊 Migration 0004 Results:
   - Inserted: {inserted_count}
   - Updated: {updated_count}
   - Skipped: {skipped_count}
   - Errors: {error_count}
   - Total stats in DB: {total_count}
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
    
    asyncio.run(seed_public_stats())