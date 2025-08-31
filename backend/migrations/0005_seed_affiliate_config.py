#!/usr/bin/env python3
"""
Migration 0005: Seed Affiliate Config from hardcoded data to MongoDB
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

async def seed_affiliate_config():
    """Seed affiliate_config collection with hardcoded data"""
    
    # MongoDB connection
    MONGO_URL = os.getenv("MONGO_URL")
    if not MONGO_URL:
        raise Exception("MONGO_URL environment variable is required")
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client["ecomsimply_production"]
    
    print("🔄 Migration 0005: Seeding Affiliate Config...")
    
    # Hardcoded affiliate config from server.py
    config_data = {
        "_id": "affiliate_config_default",
        "commission_rate": 30.0,
        "cookie_duration": 30,
        "minimum_payout": 100.0,
        "payment_methods": ["PayPal", "Virement bancaire"],
        "tracking_enabled": True,
        "custom_links": True,
        "benefits": [
            "Commission de 30% sur chaque vente",
            "Cookie de suivi de 30 jours", 
            "Paiement minimum de 100€",
            "Dashboard temps réel",
            "Support marketing dédié"
        ],
        "created_at": datetime.utcnow()
    }
    
    # Create indexes
    try:
        await db["affiliate_config"].create_index([("commission_rate", 1)])
        print("✅ Created index: affiliate_config.commission_rate")
    except Exception as e:
        print(f"ℹ️  Index already exists or error: {e}")
    
    # Seed config
    inserted_count = 0
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        # Upsert by _id (idempotent)
        result = await db["affiliate_config"].update_one(
            {"_id": config_data["_id"]},
            {"$setOnInsert": config_data},
            upsert=True
        )
        
        if result.upserted_id:
            inserted_count += 1
            print(f"✅ Inserted affiliate config: {config_data['commission_rate']}% commission")
        else:
            skipped_count += 1
            print(f"⏭️  Skipped existing affiliate config")
            
    except DuplicateKeyError:
        skipped_count += 1
        print(f"⏭️  Duplicate affiliate config")
    except Exception as e:
        error_count += 1
        print(f"❌ Error inserting affiliate config: {e}")
    
    # Summary
    total_count = await db["affiliate_config"].count_documents({})
    
    print(f"""
📊 Migration 0005 Results:
   - Inserted: {inserted_count}
   - Updated: {updated_count}
   - Skipped: {skipped_count}
   - Errors: {error_count}
   - Total configs in DB: {total_count}
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
    
    asyncio.run(seed_affiliate_config())