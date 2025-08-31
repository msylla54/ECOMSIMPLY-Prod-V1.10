#!/usr/bin/env python3
"""
Validation finale de la configuration Vercel pour ECOMSIMPLY
Vérifie que tous les éléments sont prêts pour le déploiement
"""

import os
import json
import sys
import requests
from pathlib import Path

def validate_vercel_config():
    """Valide la configuration Vercel complète"""
    print("🚀 VALIDATION CONFIGURATION VERCEL - ECOMSIMPLY")
    print("=" * 60)
    
    checks = []
    
    # 1. Vérifier vercel.json
    try:
        with open('/app/vercel.json', 'r') as f:
            vercel_config = json.load(f)
        
        required_keys = ['version', 'functions', 'rewrites']
        has_all_keys = all(key in vercel_config for key in required_keys)
        
        checks.append(("vercel.json structure", has_all_keys))
        
        # Vérifier les routes
        rewrites = vercel_config.get('rewrites', [])
        has_api_route = any('/api/' in route.get('source', '') for route in rewrites)
        has_frontend_route = any('/$1' in route.get('destination', '') for route in rewrites)
        
        checks.append(("vercel.json API route", has_api_route))
        checks.append(("vercel.json Frontend route", has_frontend_route))
        
    except Exception as e:
        checks.append(("vercel.json", False))
        print(f"❌ Erreur vercel.json: {e}")
    
    # 2. Vérifier point d'entrée ASGI
    try:
        sys.path.append('/app/backend')
        from api.index import handler
        checks.append(("Point d'entrée ASGI", True))
    except Exception as e:
        checks.append(("Point d'entrée ASGI", False))
        print(f"❌ Erreur ASGI: {e}")
    
    # 3. Vérifier build frontend
    build_path = Path('/app/frontend/build')
    index_exists = (build_path / 'index.html').exists()
    static_exists = (build_path / 'static').exists()
    
    checks.append(("Frontend build/index.html", index_exists))
    checks.append(("Frontend build/static", static_exists))
    
    # 4. Vérifier .env sécurisé
    env_removed = not os.path.exists('/app/backend/.env') or os.path.islink('/app/backend/.env')
    env_example = os.path.exists('/app/.env.example')
    gitignore_env = False
    
    try:
        with open('/app/.gitignore', 'r') as f:
            gitignore_content = f.read()
        gitignore_env = '.env' in gitignore_content
    except:
        pass
    
    checks.append(("Secrets sécurisés (.env removed)", env_removed))
    checks.append((".env.example exists", env_example))
    checks.append((".gitignore protects .env", gitignore_env))
    
    # 5. Vérifier API locale
    try:
        response = requests.get('http://localhost:8001/api/health', timeout=5)
        api_works = response.status_code == 200
        checks.append(("API locale /health", api_works))
    except:
        checks.append(("API locale /health", False))
    
    # Résultats
    print("\n📋 RÉSULTATS VALIDATION:")
    print("-" * 40)
    
    passed = 0
    total = len(checks)
    
    for check_name, status in checks:
        icon = "✅" if status else "❌"
        print(f"{icon} {check_name}")
        if status:
            passed += 1
    
    success_rate = (passed / total) * 100
    print(f"\n📊 SCORE: {passed}/{total} ({success_rate:.1f}%)")
    
    if success_rate >= 90:
        print("🎉 CONFIGURATION VERCEL PRÊTE !")
        print("✅ Vous pouvez déployer sur Vercel")
        return True
    else:
        print("⚠️ Configuration incomplète")
        print("❌ Corrigez les erreurs avant déploiement")
        return False

def show_deployment_instructions():
    """Affiche les instructions de déploiement"""
    print(f"\n🚀 INSTRUCTIONS DÉPLOIEMENT VERCEL:")
    print("=" * 50)
    print("1. Installer Vercel CLI:")
    print("   npm i -g vercel")
    print()
    print("2. Connecter à votre compte:")
    print("   vercel login")
    print()
    print("3. Déployer depuis /app:")
    print("   cd /app && vercel --prod")
    print()
    print("4. Configurer variables environnement:")
    print("   - Vercel Dashboard → Project → Settings → Environment Variables")
    print("   - Ajouter toutes les variables de .env.example")
    print("   - Mettre APP_BASE_URL avec votre URL Vercel")
    print()
    print("5. Tester après déploiement:")
    print("   - https://votre-app.vercel.app/api/health")
    print("   - https://votre-app.vercel.app (login admin)")
    print()
    print("🔐 CREDENTIALS ADMIN:")
    print("   Email: msylla54@gmail.com")
    print("   Password: SecureAdmin2025!")

if __name__ == "__main__":
    success = validate_vercel_config()
    if success:
        show_deployment_instructions()