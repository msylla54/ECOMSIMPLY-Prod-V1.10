#!/usr/bin/env python3
"""
Migration 0006: Create Empty Collections for new features
Creates collections and indexes for messages, ai_sessions, ai_events, product_generations
Idempotent script - safe to run multiple times
"""

import os
import sys
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# Add backend to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def create_empty_collections():
    """Create empty collections with proper indexes"""
    
    # MongoDB connection
    MONGO_URL = os.getenv("MONGO_URL")
    if not MONGO_URL:
        raise Exception("MONGO_URL environment variable is required")
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client["ecomsimply_production"]
    
    print("🔄 Migration 0006: Creating Empty Collections...")
    
    collections_created = 0
    indexes_created = 0
    errors = 0
    
    # Define collections and their indexes
    collections_config = {
        "messages": [
            {"index": [("userId", 1), ("created_at", -1)]},
            {"index": [("source", 1), ("status", 1)]},
            {"index": [("email", 1)]}
        ],
        "ai_sessions": [
            {"index": [("userId", 1), ("created_at", -1)]},
            {"index": [("sessionType", 1), ("created_at", -1)]},
            {"index": [("created_at", 1)], "expireAfterSeconds": 2592000}  # 30 days TTL
        ],
        "ai_events": [
            {"index": [("sessionId", 1), ("created_at", 1)]},
            {"index": [("role", 1), ("created_at", -1)]},
            {"index": [("created_at", 1)], "expireAfterSeconds": 2592000}  # 30 days TTL
        ],
        "product_generations": [
            {"index": [("userId", 1), ("created_at", -1)]},
            {"index": [("status", 1), ("created_at", -1)]},
            {"index": [("created_at", -1)]}
        ]
    }
    
    # Create collections and indexes
    for collection_name, indexes in collections_config.items():
        try:
            # Create collection (will be created automatically on first insert, but we ensure it exists)
            collection = db[collection_name]
            
            # Insert and immediately delete a dummy document to create the collection
            dummy_doc = await collection.insert_one({"_temp": True})
            await collection.delete_one({"_id": dummy_doc.inserted_id})
            
            collections_created += 1
            print(f"✅ Created collection: {collection_name}")
            
            # Create indexes
            for index_config in indexes:
                try:
                    if "expireAfterSeconds" in index_config:
                        # TTL index
                        await collection.create_index(
                            index_config["index"],
                            expireAfterSeconds=index_config["expireAfterSeconds"]
                        )
                        print(f"   ⏰ Created TTL index: {collection_name}.{index_config['index']} (TTL: {index_config['expireAfterSeconds']}s)")
                    else:
                        # Regular index
                        await collection.create_index(index_config["index"])
                        print(f"   📑 Created index: {collection_name}.{index_config['index']}")
                    indexes_created += 1
                    
                except Exception as e:
                    if "already exists" in str(e):
                        print(f"   ℹ️  Index already exists: {collection_name}.{index_config['index']}")
                    else:
                        errors += 1
                        print(f"   ❌ Error creating index {collection_name}.{index_config['index']}: {e}")
                        
        except Exception as e:
            errors += 1
            print(f"❌ Error creating collection {collection_name}: {e}")
    
    # Update users collection with last_login_at field support
    try:
        users_collection = db["users"]
        
        # Ensure users.email index exists (should already exist)
        await users_collection.create_index([("email", 1)], unique=True)
        print("✅ Ensured users.email unique index exists")
        
        # Add compound index for performance
        await users_collection.create_index([("isActive", 1), ("created_at", -1)])
        print("✅ Created users compound index: isActive + created_at")
        
        indexes_created += 2
        
    except Exception as e:
        if "already exists" in str(e):
            print("ℹ️  Users indexes already exist")
        else:
            errors += 1
            print(f"❌ Error updating users collection: {e}")
    
    # Summary
    print(f"""
📊 Migration 0006 Results:
   - Collections created: {collections_created}
   - Indexes created: {indexes_created}
   - Errors: {errors}
   
📋 Collections now available:
   - messages (contact/support system)
   - ai_sessions (AI conversation tracking)  
   - ai_events (AI conversation events)
   - product_generations (product creation history)
   - users (enhanced with performance indexes)
""")
    
    client.close()
    return {
        "collections_created": collections_created,
        "indexes_created": indexes_created,
        "errors": errors
    }

if __name__ == "__main__":
    # Load environment
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    asyncio.run(create_empty_collections())