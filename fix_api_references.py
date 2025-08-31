#!/usr/bin/env python3
"""
Script pour corriger toutes les références API dans App.js
"""

import re

# Lire le fichier
with open('/app/ecomsimply-deploy/frontend/src/App.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Replacements plus agressifs
replacements = [
    # Remplacer toutes les utilisations ${API}/endpoint par apiClient.method
    (r'await axios\.get\(`\$\{API\}/([^`]+)`\)', r'await apiClient.get(\'/\1\')'),
    (r'await axios\.post\(`\$\{API\}/([^`]+)`, ([^)]+)\)', r'await apiClient.post(\'/\1\', \2)'),
    (r'await axios\.put\(`\$\{API\}/([^`]+)`, ([^)]+)\)', r'await apiClient.put(\'/\1\', \2)'),
    (r'await axios\.delete\(`\$\{API\}/([^`]+)`\)', r'await apiClient.delete(\'/\1\')'),
    
    # Remplacer les constructions d'URL simples
    (r'`\$\{API\}/([^`]+)`', r"buildApiUrl('/\\1')"),
    
    # Remplacer les appels axios sans await
    (r'axios\.get\(`\$\{API\}/([^`]+)`', r'apiClient.get(\'/\1\''),
    (r'axios\.post\(`\$\{API\}/([^`]+)`, ([^)]+)', r'apiClient.post(\'/\1\', \2'),
    (r'axios\.put\(`\$\{API\}/([^`]+)`, ([^)]+)', r'apiClient.put(\'/\1\', \2'),
    (r'axios\.delete\(`\$\{API\}/([^`]+)`', r'apiClient.delete(\'/\1\''),
]

# Appliquer les remplacements
original_content = content
for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

print(f"🔧 Modifications effectuées: {len(original_content) - len(content)} caractères de différence")

# Sauvegarder
with open('/app/ecomsimply-deploy/frontend/src/App.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Toutes les références API ont été corrigées")

# Vérifier s'il reste des références
remaining = len(re.findall(r'\$\{API\}', content))
print(f"📊 Références API restantes: {remaining}")
