#!/usr/bin/env python3
"""
Script pour tester et générer le hash du mot de passe admin
"""
import bcrypt
import os

# Mot de passe admin prévu
admin_password = "ECS-Temp#2025-08-22!"

# Hash actuel dans l'env
current_hash = "$2b$12$yQhOn3ydalPB3RuDZNsD8uUbfuc.MVG3Pf30xrUougEsibvP4Ukty"

print("🔍 TEST PASSWORD HASH ADMIN")
print("=" * 50)

# Test du hash actuel
print(f"Mot de passe: {admin_password}")
print(f"Hash actuel: {current_hash}")

# Vérifier si le hash actuel correspond
try:
    is_valid = bcrypt.checkpw(admin_password.encode('utf-8'), current_hash.encode('utf-8'))
    print(f"✅ Hash actuel valide: {is_valid}")
except Exception as e:
    print(f"❌ Erreur validation hash: {e}")

# Générer un nouveau hash si nécessaire
if not is_valid:
    print("\n🔧 Génération nouveau hash:")
    new_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
    print(f"Nouveau hash: {new_hash.decode('utf-8')}")
    
    # Test du nouveau hash
    test_new = bcrypt.checkpw(admin_password.encode('utf-8'), new_hash)
    print(f"✅ Nouveau hash valide: {test_new}")
else:
    print("✅ Hash actuel est correct, pas besoin de régénération")

print("\n" + "=" * 50)