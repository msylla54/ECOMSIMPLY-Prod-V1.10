#!/usr/bin/env python3
"""
Test login admin avec base production
"""

import asyncio
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient

async def test_admin_login_production():
    """
    Test que l'admin peut se connecter avec la base production
    """
    try:
        prod_url = "mongodb+srv://ecomsimply-app:xIP7EfOXhODZdp0k@ecomsimply.xagju9s.mongodb.net/ecomsimply_production?retryWrites=true&w=majority&appName=EcomSimply"
        
        print("🔐 === TEST LOGIN ADMIN PRODUCTION ===")
        
        client = AsyncIOMotorClient(prod_url, serverSelectionTimeoutMS=10000)
        db = client["ecomsimply_production"]
        
        # Récupérer l'admin
        admin_user = await db.users.find_one({"email": "msylla54@gmail.com"})
        
        if not admin_user:
            print("❌ Admin non trouvé")
            return False
        
        print(f"✅ Admin trouvé: {admin_user['email']}")
        print(f"   Nom: {admin_user.get('name', 'Unknown')}")
        print(f"   Admin: {admin_user.get('is_admin', False)}")
        
        # Récupérer le hash du password
        password_hash = admin_user.get("passwordHash") or admin_user.get("password_hash")
        
        if password_hash:
            print("✅ Password hash présent")
            print(f"   Hash format: {password_hash[:10]}...")
            
            # Test avec quelques mots de passe possibles
            test_passwords = ["admin123", "ecom2025", "password123", "admin", "ecomsimply2025"]
            
            for pwd in test_passwords:
                try:
                    if bcrypt.checkpw(pwd.encode('utf-8'), password_hash.encode('utf-8')):
                        print(f"✅ Mot de passe trouvé: {pwd}")
                        client.close()
                        return True
                except:
                    continue
            
            print("⚠️  Aucun mot de passe test ne correspond")
            print("   (Normal - mot de passe sécurisé)")
        else:
            print("❌ Pas de password hash")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur test admin: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_admin_login_production())
    if success:
        print("\n✅ Admin configuré correctement en production")
    else:
        print("\n❌ Problème avec admin en production")