#!/usr/bin/env python3
"""
Migration 0001: Seed Testimonials from hardcoded data to MongoDB
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

async def seed_testimonials():
    """Seed testimonials collection with hardcoded data"""
    
    # MongoDB connection
    MONGO_URL = os.getenv("MONGO_URL")
    if not MONGO_URL:
        raise Exception("MONGO_URL environment variable is required")
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client["ecomsimply_production"]
    
    print("🔄 Migration 0001: Seeding Testimonials...")
    
    # Hardcoded testimonials from server.py
    testimonials_data = [
        {
            "_id": "testimonial_marie_dubois",
            "authorName": "Marie Dubois",
            "authorRole": "Boutique Mode Paris", 
            "content": "ECOMSIMPLY a révolutionné notre processus de création de fiches produits. Nous gagnons 80% de temps sur la rédaction!",
            "rating": 5,
            "avatarUrl": "/assets/testimonials/marie.jpg",
            "published": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": "testimonial_thomas_martin",
            "authorName": "Thomas Martin",
            "authorRole": "TechStore Online",
            "content": "L'IA d'ECOMSIMPLY génère des descriptions parfaitement optimisées pour le SEO. Nos ventes ont augmenté de 45%.",
            "rating": 5,
            "avatarUrl": "/assets/testimonials/thomas.jpg",
            "published": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": "testimonial_sophie_laurent",
            "authorName": "Sophie Laurent",
            "authorRole": "Cosmétiques Bio",
            "content": "Interface intuitive et résultats impressionnants. Je recommande vivement ECOMSIMPLY à tous les e-commerçants.",
            "rating": 5,
            "avatarUrl": "/assets/testimonials/sophie.jpg", 
            "published": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    # Create indexes
    try:
        await db["testimonials"].create_index([("published", 1), ("created_at", -1)])
        print("✅ Created index: testimonials.published + created_at")
    except Exception as e:
        print(f"ℹ️  Index already exists or error: {e}")
    
    # Seed testimonials
    inserted_count = 0
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for testimonial in testimonials_data:
        try:
            # Upsert by _id (idempotent)
            result = await db["testimonials"].update_one(
                {"_id": testimonial["_id"]},
                {"$setOnInsert": testimonial},
                upsert=True
            )
            
            if result.upserted_id:
                inserted_count += 1
                print(f"✅ Inserted testimonial: {testimonial['authorName']}")
            else:
                skipped_count += 1
                print(f"⏭️  Skipped existing testimonial: {testimonial['authorName']}")
                
        except DuplicateKeyError:
            skipped_count += 1
            print(f"⏭️  Duplicate testimonial: {testimonial['authorName']}")
        except Exception as e:
            error_count += 1
            print(f"❌ Error inserting testimonial {testimonial['authorName']}: {e}")
    
    # Summary
    total_count = await db["testimonials"].count_documents({})
    
    print(f"""
📊 Migration 0001 Results:
   - Inserted: {inserted_count}
   - Updated: {updated_count} 
   - Skipped: {skipped_count}
   - Errors: {error_count}
   - Total testimonials in DB: {total_count}
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
    
    asyncio.run(seed_testimonials())