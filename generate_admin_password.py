#!/usr/bin/env python3
"""
Script pour générer un nouveau hash de mot de passe administrateur sécurisé
Usage: python generate_admin_password.py [nouveau_mot_de_passe]
"""

import sys
import secrets
import string
import bcrypt

def generate_secure_password(length=16):
    """Génère un mot de passe sécurisé"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def main():
    print("🔐 GÉNÉRATEUR DE MOT DE PASSE ADMINISTRATEUR SÉCURISÉ")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        # Utiliser le mot de passe fourni
        new_password = sys.argv[1]
        print(f"📝 Utilisation du mot de passe fourni")
    else:
        # Générer un nouveau mot de passe sécurisé
        new_password = generate_secure_password()
        print(f"🎲 Nouveau mot de passe généré automatiquement")
    
    # Hasher le mot de passe
    password_hash = hash_password(new_password)
    
    print(f"\n✅ RÉSULTATS:")
    print(f"Email admin: msylla54@gmail.com")
    print(f"Nouveau mot de passe: {new_password}")
    print(f"Hash du mot de passe: {password_hash}")
    
    print(f"\n📋 ACTIONS À EFFECTUER:")
    print(f"1. Mettre à jour ADMIN_PASSWORD_HASH dans /app/backend/.env:")
    print(f'   ADMIN_PASSWORD_HASH="{password_hash}"')
    print(f"2. Sauvegarder le mot de passe: {new_password}")
    print(f"3. Redémarrer le backend: sudo supervisorctl restart backend")
    
    print(f"\n⚠️ SÉCURITÉ:")
    print(f"- Ne jamais stocker le mot de passe en clair dans le code")
    print(f"- Partager le mot de passe de manière sécurisée")
    print(f"- Le hash sera automatiquement utilisé au démarrage")

if __name__ == "__main__":
    main()