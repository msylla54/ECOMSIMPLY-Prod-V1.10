#!/usr/bin/env python3
"""
Migration 0003: Seed Languages from hardcoded data to MongoDB
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

async def seed_languages():
    """Seed languages collection with hardcoded data"""
    
    # MongoDB connection
    MONGO_URL = os.getenv("MONGO_URL")
    if not MONGO_URL:
        raise Exception("MONGO_URL environment variable is required")
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client["ecomsimply_production"]
    
    print("🔄 Migration 0003: Seeding Languages...")
    
    # Hardcoded languages from server.py
    languages_data = [
        {
            "_id": "lang_fr",
            "code": "fr",
            "name": "Français",
            "flag": "🇫🇷", 
            "default": True,
            "active": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": "lang_en",
            "code": "en",
            "name": "English",
            "flag": "🇺🇸",
            "default": False,
            "active": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": "lang_es",
            "code": "es", 
            "name": "Español",
            "flag": "🇪🇸",
            "default": False,
            "active": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": "lang_de",
            "code": "de",
            "name": "Deutsch",
            "flag": "🇩🇪",
            "default": False, 
            "active": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    # Create indexes
    try:
        await db["languages"].create_index([("code", 1)], unique=True)
        await db["languages"].create_index([("default", 1), ("active", 1)])
        print("✅ Created indexes: languages.code (unique) + default/active")
    except Exception as e:
        print(f"ℹ️  Indexes already exist or error: {e}")
    
    # Seed languages
    inserted_count = 0
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for language in languages_data:
        try:
            # Upsert by _id (idempotent)
            result = await db["languages"].update_one(
                {"_id": language["_id"]},
                {"$setOnInsert": language},
                upsert=True
            )
            
            if result.upserted_id:
                inserted_count += 1
                print(f"✅ Inserted language: {language['name']} ({language['code']})")
            else:
                skipped_count += 1
                print(f"⏭️  Skipped existing language: {language['name']}")
                
        except DuplicateKeyError:
            skipped_count += 1
            print(f"⏭️  Duplicate language: {language['name']}")
        except Exception as e:
            error_count += 1
            print(f"❌ Error inserting language {language['name']}: {e}")
    
    # Summary
    total_count = await db["languages"].count_documents({})
    
    print(f"""
📊 Migration 0003 Results:
   - Inserted: {inserted_count}
   - Updated: {updated_count}
   - Skipped: {skipped_count}
   - Errors: {error_count}
   - Total languages in DB: {total_count}
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
    
    asyncio.run(seed_languages())