#!/usr/bin/env python3
"""
Validation des correctifs de sécurité ECOMSIMPLY-Prod-V1.1
Vérifie CORS, secrets, et conformité sécuritaire
"""

import os
import re
import json
import requests
import subprocess
from pathlib import Path

def validate_cors_config():
    """Valide la configuration CORS sécurisée"""
    print("🔒 VALIDATION CORS SÉCURISÉ")
    print("-" * 40)
    
    checks = []
    
    # Lire le fichier server.py
    try:
        with open('/app/backend/server.py', 'r') as f:
            server_content = f.read()
        
        # Vérifier absence de wildcards '*'
        cors_section = re.search(r'app\.add_middleware\(\s*CORSMiddleware,.*?\)', server_content, re.DOTALL)
        if cors_section:
            cors_config = cors_section.group(0)
            
            # Vérifier qu'il n'y a pas de "*" dans la config CORS
            has_wildcard = '"*"' in cors_config or "'*'" in cors_config
            checks.append(("CORS sans wildcard '*'", not has_wildcard))
            
            # Vérifier présence des variables d'environnement
            has_env_vars = 'APP_BASE_URL' in cors_config and 'APP_BASE_URL_PREVIEW' in cors_config
            checks.append(("CORS utilise variables environnement", has_env_vars))
            
            # Vérifier listes explicites
            has_explicit_methods = 'allowed_methods' in server_content
            has_explicit_headers = 'allowed_headers' in server_content
            checks.append(("Méthodes HTTP explicites", has_explicit_methods))
            checks.append(("Headers HTTP explicites", has_explicit_headers))
            
        else:
            checks.append(("Configuration CORS trouvée", False))
    
    except Exception as e:
        print(f"❌ Erreur lecture server.py: {e}")
        checks.append(("Lecture server.py", False))
    
    return checks

def validate_secrets_cleanup():
    """Valide la suppression des secrets"""
    print("\n🔐 VALIDATION SUPPRESSION SECRETS")
    print("-" * 40)
    
    checks = []
    
    # Vérifier suppression des .env
    env_files = []
    for root, dirs, files in os.walk('/app'):
        # Exclure .git
        dirs[:] = [d for d in dirs if d != '.git']
        for file in files:
            if file == '.env' or (file.startswith('.env.') and file != '.env.example'):
                env_files.append(os.path.join(root, file))
    
    checks.append(("Fichiers .env supprimés", len(env_files) == 0))
    if env_files:
        print(f"⚠️ Fichiers .env trouvés: {env_files}")
    
    # Vérifier .env.example existe
    checks.append((".env.example présent", os.path.exists('/app/.env.example')))
    
    # Vérifier .gitignore
    try:
        with open('/app/.gitignore', 'r') as f:
            gitignore = f.read()
        
        protects_env = '.env' in gitignore and '!.env.example' in gitignore
        checks.append((".gitignore protège .env", protects_env))
    except:
        checks.append((".gitignore accessible", False))
    
    # Scan rapide pour secrets hardcodés dans le code
    secret_patterns = [
        r'sk-[a-zA-Z0-9]{32,}',  # OpenAI keys
        r'pk_live_[a-zA-Z0-9]{24,}',  # Stripe
        r'sk_live_[a-zA-Z0-9]{24,}',  # Stripe
        r'mongodb://.*:.*@',  # MongoDB avec credentials
        r'AKIA[0-9A-Z]{16}',  # AWS Access Key
    ]
    
    hardcoded_secrets = []
    for root, dirs, files in os.walk('/app'):
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules']]
        for file in files:
            if file.endswith(('.py', '.js', '.json', '.md')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    for pattern in secret_patterns:
                        matches = re.findall(pattern, content)
                        if matches:
                            hardcoded_secrets.extend([(file_path, match) for match in matches])
                except:
                    continue
    
    checks.append(("Aucun secret hardcodé détecté", len(hardcoded_secrets) == 0))
    if hardcoded_secrets:
        print(f"⚠️ Secrets potentiels: {hardcoded_secrets[:3]}...")  # Show first 3
    
    return checks

def validate_api_health():
    """Valide l'API health check"""
    print("\n🏥 VALIDATION API HEALTH")
    print("-" * 40)
    
    checks = []
    
    # Test local si possible
    try:
        response = requests.get('http://localhost:8001/api/health', timeout=5)
        checks.append(("API /health locale répond", response.status_code == 200))
        
        if response.status_code == 200:
            data = response.json()
            checks.append(("API health format JSON", 'status' in data))
            
            # Vérifier headers CORS (ne doit pas contenir '*')
            cors_header = response.headers.get('Access-Control-Allow-Origin', '')
            no_wildcard_cors = cors_header != '*'
            checks.append(("Headers CORS sans '*'", no_wildcard_cors))
            
            if cors_header:
                print(f"📋 CORS Origin header: {cors_header}")
        
    except Exception as e:
        checks.append(("API /health accessible", False))
        print(f"⚠️ API locale non accessible: {e}")
    
    return checks

def validate_vercel_readiness():
    """Valide la préparation Vercel"""
    print("\n🚀 VALIDATION VERCEL READINESS")
    print("-" * 40)
    
    checks = []
    
    # Vérifier vercel.json
    checks.append(("vercel.json existe", os.path.exists('/app/vercel.json')))
    
    # Vérifier api/index.py
    checks.append(("api/index.py existe", os.path.exists('/app/api/index.py')))
    
    # Vérifier build frontend
    build_path = Path('/app/frontend/build')
    checks.append(("Frontend build présent", build_path.exists()))
    
    if build_path.exists():
        checks.append(("Frontend index.html", (build_path / 'index.html').exists()))
        checks.append(("Frontend static/", (build_path / 'static').exists()))
    
    return checks

def main():
    """Validation complète des correctifs sécurité"""
    print("🔐 VALIDATION CORRECTIFS SÉCURITÉ - ECOMSIMPLY-PROD-V1.1")
    print("=" * 65)
    
    all_checks = []
    
    # Exécuter toutes les validations
    all_checks.extend(validate_cors_config())
    all_checks.extend(validate_secrets_cleanup())
    all_checks.extend(validate_api_health())
    all_checks.extend(validate_vercel_readiness())
    
    # Résultats
    print(f"\n📊 RÉSULTATS GLOBAUX")
    print("=" * 40)
    
    passed = 0
    total = len(all_checks)
    
    for check_name, status in all_checks:
        icon = "✅" if status else "❌"
        print(f"{icon} {check_name}")
        if status:
            passed += 1
    
    success_rate = (passed / total) * 100
    print(f"\n🎯 SCORE SÉCURITÉ: {passed}/{total} ({success_rate:.1f}%)")
    
    if success_rate >= 95:
        print("🎉 CORRECTIFS SÉCURITÉ VALIDÉS !")
        print("✅ ECOMSIMPLY-Prod-V1.1 prêt pour déploiement sécurisé")
        
        print(f"\n🚀 PROCHAINES ÉTAPES:")
        print("1. Déployer sur Vercel avec nouvelles variables")
        print("2. Effectuer rotation des clés compromises")
        print("3. Purger historique Git (voir SECURITY_GIT_CLEANUP.md)")
        print("4. Tester connexion admin en production")
        
        return True
    else:
        print("⚠️ CORRECTIFS INCOMPLETS")
        print("❌ Corriger les problèmes avant déploiement")
        return False

if __name__ == "__main__":
    main()