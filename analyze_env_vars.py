#!/usr/bin/env python3
"""
Analyse les variables d'environnement requises par le backend ECOMSIMPLY
"""

import os
import re
import json
from pathlib import Path
from typing import Set, Dict, List

def extract_env_vars_from_file(file_path: Path) -> Set[str]:
    """Extrait les variables d'environnement d'un fichier Python"""
    env_vars = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Patterns pour os.getenv, os.environ.get, os.environ[]
        patterns = [
            r'os\.getenv\(["\']([^"\']+)["\']',
            r'os\.environ\.get\(["\']([^"\']+)["\']',
            r'os\.environ\[["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            env_vars.update(matches)
            
    except Exception as e:
        print(f"Erreur lecture {file_path}: {e}")
    
    return env_vars

def analyze_backend_env_vars():
    """Analyse toutes les variables d'environnement du backend"""
    backend_path = Path("/app/ecomsimply-deploy/backend")
    all_env_vars = set()
    
    # Parcourir tous les fichiers Python
    python_files = list(backend_path.rglob("*.py"))
    
    for py_file in python_files:
        if "__pycache__" in str(py_file):
            continue
            
        env_vars = extract_env_vars_from_file(py_file)
        if env_vars:
            print(f"📁 {py_file.relative_to(backend_path)}: {len(env_vars)} variables")
            for var in sorted(env_vars):
                print(f"   {var}")
            print()
        
        all_env_vars.update(env_vars)
    
    return all_env_vars

def categorize_env_vars(env_vars: Set[str]) -> Dict[str, List[str]]:
    """Catégorise les variables d'environnement"""
    categories = {
        "critical": [],      # Variables essentielles
        "amazon": [],        # Amazon SP-API
        "database": [],      # Base de données
        "auth": [],          # Authentification
        "integrations": [],  # Intégrations tierces
        "config": [],        # Configuration générale
        "optional": []       # Variables optionnelles
    }
    
    for var in sorted(env_vars):
        var_lower = var.lower()
        
        # Catégorisation par préfixe/contenu
        if any(x in var_lower for x in ['mongo', 'db_']):
            categories["database"].append(var)
        elif any(x in var_lower for x in ['amazon', 'amz_', 'spapi', 'lwa']):
            categories["amazon"].append(var)
        elif any(x in var_lower for x in ['jwt', 'admin_', 'bootstrap', 'encryption']):
            categories["auth"].append(var)
        elif any(x in var_lower for x in ['openai', 'fal', 'stripe', 'smtp']):
            categories["integrations"].append(var)
        elif any(x in var_lower for x in ['app_base', 'environment', 'debug', 'mock']):
            categories["config"].append(var)
        else:
            categories["optional"].append(var)
    
    # Variables critiques essentielles
    critical_vars = [
        'MONGO_URL', 'DB_NAME', 'JWT_SECRET', 'ADMIN_EMAIL', 
        'ADMIN_PASSWORD_HASH', 'ADMIN_BOOTSTRAP_TOKEN', 'APP_BASE_URL'
    ]
    
    for var in critical_vars:
        if var in env_vars:
            categories["critical"].append(var)
            # Retirer des autres catégories
            for cat in ["database", "auth", "config"]:
                if var in categories[cat]:
                    categories[cat].remove(var)
    
    return categories

def generate_railway_env_script(categorized_vars: Dict[str, List[str]]):
    """Génère un script pour configurer les variables Railway"""
    print("🚂 SCRIPT CONFIGURATION RAILWAY")
    print("=" * 50)
    print("#!/bin/bash")
    print("# Configuration automatique variables d'environnement Railway")
    print("# Généré automatiquement - ECOMSIMPLY Backend")
    print()
    
    # Variables critiques
    print("# === VARIABLES CRITIQUES (OBLIGATOIRES) ===")
    for var in categorized_vars["critical"]:
        if var == 'MONGO_URL':
            print(f'railway variables set {var}="mongodb+srv://USERNAME:PASSWORD@cluster.mongodb.net/ecomsimply_production?retryWrites=true&w=majority"')
        elif var == 'DB_NAME':
            print(f'railway variables set {var}="ecomsimply_production"')
        elif var == 'JWT_SECRET':
            print(f'railway variables set {var}="supersecretjwtkey32charsminimum2025ecomsimply"')
        elif var == 'ADMIN_EMAIL':
            print(f'railway variables set {var}="msylla54@gmail.com"')
        elif var == 'ADMIN_PASSWORD_HASH':
            print(f'railway variables set {var}="$2b$12$AX.4AQP8u50RP3.pcupJ6OJSSOHQqTG71NJvZRW/J6kyRFnxKX0.W"')
        elif var == 'ADMIN_BOOTSTRAP_TOKEN':
            print(f'railway variables set {var}="ECS-Bootstrap-2025-Secure-Token"')
        elif var == 'APP_BASE_URL':
            print(f'railway variables set {var}="https://ecomsimply.com"')
        else:
            print(f'railway variables set {var}="VALUE_TO_SET"')
    print()
    
    # Variables Database (si pas dans critical)
    remaining_db = [v for v in categorized_vars["database"] if v not in categorized_vars["critical"]]
    if remaining_db:
        print("# === BASE DE DONNÉES ===")
        for var in remaining_db:
            print(f'railway variables set {var}="VALUE_TO_SET"')
        print()
    
    # Variables Auth (si pas dans critical)
    remaining_auth = [v for v in categorized_vars["auth"] if v not in categorized_vars["critical"]]
    if remaining_auth:
        print("# === AUTHENTIFICATION ===")
        for var in remaining_auth:
            if 'ENCRYPTION' in var:
                print(f'railway variables set {var}="w7uWSQqDAewH34UjRHVSgeJawQnDa-ukRe0WERClY694="')
            else:
                print(f'railway variables set {var}="VALUE_TO_SET"')
        print()
    
    # Variables Amazon
    if categorized_vars["amazon"]:
        print("# === AMAZON SP-API (Optionnel) ===")
        for var in categorized_vars["amazon"]:
            print(f'# railway variables set {var}="YOUR_AMAZON_VALUE"')
        print()
    
    # Variables Integrations
    if categorized_vars["integrations"]:
        print("# === INTÉGRATIONS TIERCES (Optionnel) ===")
        for var in categorized_vars["integrations"]:
            print(f'# railway variables set {var}="YOUR_API_KEY"')
        print()
    
    # Variables Configuration
    remaining_config = [v for v in categorized_vars["config"] if v not in categorized_vars["critical"]]
    if remaining_config:
        print("# === CONFIGURATION ===")
        for var in remaining_config:
            if var == 'ENVIRONMENT':
                print(f'railway variables set {var}="production"')
            elif var == 'DEBUG':
                print(f'railway variables set {var}="false"')
            elif var == 'MOCK_MODE':
                print(f'railway variables set {var}="false"')
            else:
                print(f'railway variables set {var}="VALUE_TO_SET"')
        print()
    
    print("echo 'Configuration Railway terminée!'")

def main():
    print("🔍 ANALYSE VARIABLES D'ENVIRONNEMENT ECOMSIMPLY BACKEND")
    print("=" * 60)
    
    # Analyser les variables
    env_vars = analyze_backend_env_vars()
    
    print(f"\n📊 RÉSUMÉ: {len(env_vars)} variables d'environnement trouvées")
    print("-" * 60)
    
    # Catégoriser
    categorized = categorize_env_vars(env_vars)
    
    for category, vars_list in categorized.items():
        if vars_list:
            print(f"\n🏷️  {category.upper()} ({len(vars_list)} variables):")
            for var in vars_list:
                print(f"   • {var}")
    
    print("\n" + "=" * 60)
    
    # Générer script Railway
    generate_railway_env_script(categorized)
    
    # Sauvegarder analyse
    analysis = {
        "total_vars": len(env_vars),
        "categorized": categorized,
        "all_vars": sorted(list(env_vars))
    }
    
    with open("/app/ecomsimply-deploy/env_vars_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n📋 Analyse sauvegardée: env_vars_analysis.json")

if __name__ == "__main__":
    main()