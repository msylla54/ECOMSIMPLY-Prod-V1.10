#!/usr/bin/env python3
"""
Test des endpoints avec base production directe
Simule ce qui se passera après la bascule emergent.sh
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

async def test_production_endpoints():
    """
    Test simulation des endpoints avec base production
    """
    try:
        prod_url = "mongodb+srv://ecomsimply-app:xIP7EfOXhODZdp0k@ecomsimply.xagju9s.mongodb.net/ecomsimply_production?retryWrites=true&w=majority&appName=EcomSimply"
        
        print(f"🧪 === SIMULATION ENDPOINTS PRODUCTION ===")
        print(f"Timestamp : {datetime.utcnow().isoformat()}")
        print()
        
        client = AsyncIOMotorClient(prod_url, serverSelectionTimeoutMS=10000)
        db = client["ecomsimply_production"]
        
        await client.admin.command('ping')
        print("✅ Connexion production OK")
        
        # Simulation endpoint /api/public/plans-pricing
        print("\n📋 Test: /api/public/plans-pricing")
        plans = await db.subscription_plans.find({"active": True}, {"_id": 0}).to_list(length=None)
        print(f"  ✅ Plans trouvés: {len(plans)}")
        for plan in plans:
            print(f"    • {plan.get('name', 'Unknown')}: {plan.get('price', 0)}€")
        
        # Simulation endpoint /api/testimonials  
        print("\n📋 Test: /api/testimonials")
        testimonials = await db.testimonials.find({"published": True}, {"_id": 0}).to_list(length=None)
        print(f"  ✅ Témoignages trouvés: {len(testimonials)}")
        for testimonial in testimonials:
            print(f"    • {testimonial.get('author', 'Unknown')}: {testimonial.get('rating', 0)}⭐")
        
        # Simulation endpoint /api/stats/public
        print("\n📋 Test: /api/stats/public")
        stats = await db.stats_public.find({}, {"_id": 0}).to_list(length=None)
        print(f"  ✅ Stats trouvées: {len(stats)}")
        for stat in stats:
            print(f"    • {stat.get('key', 'unknown')}: {stat.get('value', 'N/A')}")
        
        # Simulation endpoint /api/languages
        print("\n📋 Test: /api/languages")
        languages = await db.languages.find({"active": True}, {"_id": 0}).to_list(length=None)
        print(f"  ✅ Langues trouvées: {len(languages)}")
        for lang in languages:
            default_flag = " (DEFAULT)" if lang.get("default", False) else ""
            print(f"    • {lang.get('code', 'unknown')}: {lang.get('name', 'Unknown')}{default_flag}")
        
        # Test utilisateurs admin
        print("\n📋 Test: Utilisateurs admin")
        admin_users = await db.users.find({"is_admin": True}, {"email": 1, "name": 1}).to_list(length=None)
        print(f"  ✅ Admins trouvés: {len(admin_users)}")
        for admin in admin_users:
            print(f"    • {admin.get('email', 'unknown')} - {admin.get('name', 'Unknown')}")
        
        client.close()
        
        print(f"\n🎉 Tous les endpoints production sont prêts !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur test endpoints production: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_production_endpoints())
    if success:
        print("\n✅ Base production prête pour la bascule emergent.sh")
    else:
        print("\n❌ Problème détecté avec la base production")
        exit(1)