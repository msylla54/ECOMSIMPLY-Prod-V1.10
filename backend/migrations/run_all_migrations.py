#!/usr/bin/env python3
"""
Run All Migrations Script
Executes all migration scripts in order and provides summary report
"""

import os
import sys
import asyncio
from datetime import datetime

# Import all migration modules using importlib for numeric module names
import importlib.util

def import_migration_module(module_name, file_path):
    """Import migration module by file path"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import migration functions
migration_0001 = import_migration_module("migration_0001", os.path.join(os.path.dirname(__file__), "0001_seed_testimonials.py"))
migration_0002 = import_migration_module("migration_0002", os.path.join(os.path.dirname(__file__), "0002_seed_subscription_plans.py"))
migration_0003 = import_migration_module("migration_0003", os.path.join(os.path.dirname(__file__), "0003_seed_languages.py"))
migration_0004 = import_migration_module("migration_0004", os.path.join(os.path.dirname(__file__), "0004_seed_public_stats.py"))
migration_0005 = import_migration_module("migration_0005", os.path.join(os.path.dirname(__file__), "0005_seed_affiliate_config.py"))
migration_0006 = import_migration_module("migration_0006", os.path.join(os.path.dirname(__file__), "0006_create_empty_collections.py"))

async def run_all_migrations():
    """Run all migrations in sequence"""
    
    print("🚀 ECOMSIMPLY - Running All Migrations to MongoDB Atlas")
    print("=" * 60)
    print(f"Started at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("")
    
    # Check environment
    MONGO_URL = os.getenv("MONGO_URL")
    if not MONGO_URL:
        print("❌ ERROR: MONGO_URL environment variable is required")
        print("Please set MONGO_URL and try again.")
        return
    
    print(f"🔗 MongoDB URL: {MONGO_URL.split('@')[1] if '@' in MONGO_URL else 'localhost'}")
    print("")
    
    # Migration sequence
    migrations = [
        ("0001", "Testimonials", migration_0001.seed_testimonials),
        ("0002", "Subscription Plans", migration_0002.seed_subscription_plans), 
        ("0003", "Languages", migration_0003.seed_languages),
        ("0004", "Public Stats", migration_0004.seed_public_stats),
        ("0005", "Affiliate Config", migration_0005.seed_affiliate_config),
        ("0006", "Empty Collections", migration_0006.create_empty_collections)
    ]
    
    results = {}
    total_inserted = 0
    total_updated = 0
    total_skipped = 0
    total_errors = 0
    
    # Run each migration
    for migration_id, name, migration_func in migrations:
        try:
            print(f"🔄 Running Migration {migration_id}: {name}")
            result = await migration_func()
            results[migration_id] = {"name": name, "success": True, "result": result}
            
            # Aggregate counts (handle different result structures)
            if "inserted" in result:
                total_inserted += result.get("inserted", 0)
                total_updated += result.get("updated", 0) 
                total_skipped += result.get("skipped", 0)
                total_errors += result.get("errors", 0)
            
            print(f"✅ Migration {migration_id} completed successfully")
            print("")
            
        except Exception as e:
            print(f"❌ Migration {migration_id} failed: {str(e)}")
            results[migration_id] = {"name": name, "success": False, "error": str(e)}
            total_errors += 1
            print("")
    
    # Final summary report
    print("=" * 60)
    print("📊 MIGRATION SUMMARY REPORT")
    print("=" * 60)
    
    successful = 0
    failed = 0
    
    for migration_id, result in results.items():
        status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
        print(f"Migration {migration_id} ({result['name']}): {status}")
        if result["success"]:
            successful += 1
        else:
            failed += 1
            print(f"   Error: {result.get('error', 'Unknown error')}")
    
    print("")
    print(f"📈 OVERALL STATISTICS:")
    print(f"   - Successful migrations: {successful}/{len(migrations)}")
    print(f"   - Failed migrations: {failed}/{len(migrations)}")
    print(f"   - Total documents inserted: {total_inserted}")
    print(f"   - Total documents updated: {total_updated}")
    print(f"   - Total documents skipped: {total_skipped}")
    print(f"   - Total errors encountered: {total_errors}")
    print("")
    
    if failed == 0:
        print("🎉 ALL MIGRATIONS COMPLETED SUCCESSFULLY!")
        print("✅ MongoDB Atlas is now ready for ECOMSIMPLY production use.")
    else:
        print(f"⚠️  {failed} migration(s) failed. Please review errors above.")
        return False
    
    print("")
    print(f"Completed at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    return True

if __name__ == "__main__":
    # Load environment
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    success = asyncio.run(run_all_migrations())
    sys.exit(0 if success else 1)