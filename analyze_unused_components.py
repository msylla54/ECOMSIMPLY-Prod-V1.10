#!/usr/bin/env python3
"""
Analyser les composants non utilisés dans App.js
"""

import re
import os

# Lire App.js
with open('/app/ecomsimply-deploy/frontend/src/App.js', 'r', encoding='utf-8') as f:
    app_content = f.read()

# Extraire les imports de composants
import_pattern = r'^import\s+(?:\{([^}]+)\}|([^,\s]+))\s+from\s+[\'"]\./(components|pages)/([^\'\"]+)[\'"];?'
imports = {}
unused_imports = []

for match in re.finditer(import_pattern, app_content, re.MULTILINE):
    if match.group(1):  # Named imports like { Component1, Component2 }
        named_imports = [name.strip() for name in match.group(1).split(',')]
        for comp in named_imports:
            imports[comp] = match.group(4)
    elif match.group(2):  # Default import like Component
        imports[match.group(2)] = match.group(4)

print("📋 Composants importés:")
for comp, path in imports.items():
    print(f"  - {comp} from {path}")

print("\n🔍 Vérification d'utilisation:")

# Vérifier si chaque composant est utilisé dans le code
for component, path in imports.items():
    # Chercher les utilisations (en excluant les imports)
    usage_pattern = f'<{component}|{component}\\('
    
    # Retirer la ligne d'import pour éviter les faux positifs
    content_without_imports = re.sub(r'^import.*' + re.escape(component) + '.*$', '', app_content, flags=re.MULTILINE)
    
    if re.search(usage_pattern, content_without_imports):
        print(f"  ✅ {component} - UTILISÉ")
    else:
        print(f"  ❌ {component} - NON UTILISÉ")
        unused_imports.append((component, path))

print(f"\n📊 Résultats:")
print(f"  - Total imports: {len(imports)}")
print(f"  - Non utilisés: {len(unused_imports)}")

if unused_imports:
    print(f"\n🗑️ Composants à potentiellement supprimer:")
    for comp, path in unused_imports:
        print(f"  - {comp} ({path})")
        
        # Vérifier si le fichier existe
        file_path = f'/app/ecomsimply-deploy/frontend/src/{path.replace("/", "/")}' 
        if path.startswith('components'):
            file_path = f'/app/ecomsimply-deploy/frontend/src/{path}.js'
        elif path.startswith('pages'):
            file_path = f'/app/ecomsimply-deploy/frontend/src/{path}.js'
        
        if os.path.exists(file_path):
            print(f"    📁 Fichier existe: {file_path}")
        else:
            print(f"    ❓ Fichier non trouvé: {file_path}")