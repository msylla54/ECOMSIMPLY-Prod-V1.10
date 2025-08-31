#!/usr/bin/env python3
"""
Script global pour refactoriser tous les composants avec des appels API
"""

import os
import re
import glob

# Dossier des composants
components_dir = '/app/ecomsimply-deploy/frontend/src/components'

# Patterns de remplacement
patterns = [
    # Import axios -> Import apiClient
    (r'^import axios from [\'"]axios[\'"];$', "// ✅ Import du client API centralisé\nimport apiClient from '../lib/apiClient';"),
    
    # Variables hardcodées
    (r'const\s+BACKEND_URL\s*=\s*process\.env\.REACT_APP_BACKEND_URL.*?;', ''),
    (r'const\s+backendUrl\s*=\s*process\.env\.REACT_APP_BACKEND_URL.*?;', ''),
    (r'const\s+API_BASE_URL\s*=.*?;', ''),
    
    # Appels fetch avec URL complète -> apiClient
    (r'fetch\(`\$\{backendUrl\}(/api/[^`]+)`', r"apiClient.get('\1')"),
    (r'fetch\(`\$\{BACKEND_URL\}(/api/[^`]+)`', r"apiClient.get('\1')"),
    
    # Options fetch -> paramètres apiClient
    (r'fetch\(`\$\{backendUrl\}(/api/[^`]+)`, \{\s*method: [\'"]GET[\'"],?\s*headers: [^}]+\}\)', r"apiClient.get('\1')"),
    (r'fetch\(`\$\{backendUrl\}(/api/[^`]+)`, \{\s*method: [\'"]POST[\'"],?\s*headers: [^}]+,?\s*body: JSON\.stringify\(([^)]+)\)\s*\}\)', r"apiClient.post('\1', \2)"),
]

def refactor_file(filepath):
    """Refactorise un fichier"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Appliquer les patterns
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        # Appliquer des remplacements spécifiques pour les patterns plus complexes
        
        # Remplacer les constructions d'options fetch complexes
        complex_fetch_pattern = r'const options = \{\s*method: [\'"]([A-Z]+)[\'"],?\s*headers: \{\s*[\'"]Content-Type[\'"]:\s*[\'"]application/json[\'"],?\s*[\'"]Authorization[\'"]:\s*`Bearer \$\{token\}`[^}]*\}[^}]*\};?\s*const response = await fetch\(`\$\{backendUrl\}(/api/[^`]+)`, options\);'
        
        def replace_complex_fetch(match):
            method = match.group(1).lower()
            endpoint = match.group(2)
            return f'const response = await apiClient.{method}(\'{endpoint}\');'
        
        content = re.sub(complex_fetch_pattern, replace_complex_fetch, content, flags=re.DOTALL)
        
        # Si le contenu a changé, sauvegarder
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement de {filepath}: {e}")
        return False

def main():
    """Fonction principale"""
    # Trouver tous les fichiers JS dans les composants
    js_files = glob.glob(os.path.join(components_dir, '**/*.js'), recursive=True)
    
    print(f"🔍 Traitement de {len(js_files)} fichiers...")
    
    modified_count = 0
    
    for js_file in js_files:
        # Ignorer certains fichiers déjà traités
        if 'apiClient.js' in js_file:
            continue
            
        if refactor_file(js_file):
            modified_count += 1
            print(f"✅ {os.path.basename(js_file)}")
        else:
            print(f"⏭️ {os.path.basename(js_file)} (pas de changement)")
    
    print(f"\n🎉 Refactoring terminé: {modified_count}/{len(js_files)} fichiers modifiés")

if __name__ == "__main__":
    main()