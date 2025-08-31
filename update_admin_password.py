#!/usr/bin/env python3
"""
Script pour générer le hash du nouveau mot de passe admin
"""
import bcrypt

def main():
    print("🔐 MISE À JOUR HASH MOT DE PASSE ADMIN")
    print("=" * 50)
    
    # Nouveau mot de passe
    new_password = "ECS-Permanent#2025!"
    
    # Générer le hash
    new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    new_hash_str = new_hash.decode('utf-8')
    
    print(f"Nouveau mot de passe: {new_password}")
    print(f"Nouveau hash: {new_hash_str}")
    
    # Test de validation
    test_valid = bcrypt.checkpw(new_password.encode('utf-8'), new_hash)
    print(f"Validation hash: {'✅ VALIDE' if test_valid else '❌ INVALIDE'}")
    
    print("\n" + "=" * 50)
    print("📋 MISE À JOUR VERCEL REQUISE:")
    print("1. Aller sur vercel.com → Projet ecomsimply")
    print("2. Project Settings → Environment Variables")
    print("3. Modifier la variable ADMIN_PASSWORD_HASH:")
    print(f"   Nouvelle valeur: {new_hash_str}")
    print("4. Redéployer (Use existing Build Cache: No)")
    print("5. Attendre déploiement complet (2-3 minutes)")
    
    print("\n💡 ALTERNATIVE RAPIDE:")
    print("Ou utiliser l'ancien mot de passe temporairement:")
    print("ECS-Temp#2025-08-22! (hash déjà configuré)")
    
    return new_hash_str

if __name__ == "__main__":
    hash_value = main()