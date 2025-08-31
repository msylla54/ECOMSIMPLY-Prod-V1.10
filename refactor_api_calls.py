#!/usr/bin/env python3
"""
Script de refactoring pour remplacer tous les appels API dans App.js
"""

import re

# Lire le fichier App.js
with open('/app/ecomsimply-deploy/frontend/src/App.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Remplacements des appels API avec le client centralisé
replacements = [
    # Remplacer ${API} par les appels apiClient appropriés
    (r'await axios\.get\(`\$\{API\}/([^`]+)`\)', r'await apiClient.get(\'/\1\')'),
    (r'await axios\.post\(`\$\{API\}/([^`]+)`, ([^)]+)\)', r'await apiClient.post(\'/\1\', \2)'),
    (r'await axios\.put\(`\$\{API\}/([^`]+)`, ([^)]+)\)', r'await apiClient.put(\'/\1\', \2)'),
    (r'await axios\.delete\(`\$\{API\}/([^`]+)`\)', r'await apiClient.delete(\'/\1\')'),
    
    # Remplacer les constructions d'URL restantes
    (r'`\$\{API\}/([^`]+)`', r"buildApiUrl('/\\1')"),
    
    # Remplacer axios.get/post direct avec URL complète
    (r'axios\.get\(`\$\{API\}/([^`]+)`', r'apiClient.get(\'/\1\''),
    (r'axios\.post\(`\$\{API\}/([^`]+)`, ([^)]+)', r'apiClient.post(\'/\1\', \2'),
    (r'axios\.put\(`\$\{API\}/([^`]+)`, ([^)]+)', r'apiClient.put(\'/\1\', \2'),
    (r'axios\.delete\(`\$\{API\}/([^`]+)`', r'apiClient.delete(\'/\1\''),
]

# Appliquer les remplacements
for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

# Sauvegarder le fichier modifié
with open('/app/ecomsimply-deploy/frontend/src/App.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Refactoring terminé - tous les appels API ont été mis à jour")