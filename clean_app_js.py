#!/usr/bin/env python3
"""
Nettoie complètement App.js des erreurs de regex et de syntaxe
"""

import re

# Lire le fichier
with open('/app/ecomsimply-deploy/frontend/src/App.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Corrections spécifiques
corrections = [
    # Corriger les buildApiUrl mal formés
    (r"buildApiUrl\('/\\1'\)", "buildApiUrl('/stats')"),
    (r"buildApiUrl\('/\\([^']+)'\)", lambda m: f"'/api/{m.group(1)}'"),
    
    # Corriger les échappements incorrects dans les regex
    (r"\\'/", "'/"),
    (r"\\\\/", "/"),
    
    # Corriger les appels API mal formés
    (r"await axios\.get\(buildApiUrl\('/([^']+)'\)", r"await apiClient.get('/\1')"),
    (r"axios\.get\(buildApiUrl\('/([^']+)'\)", r"apiClient.get('/\1')"),
    
    # Corriger les groupes de capture mal échappés
    (r"\\1", "stats"),
    (r"\\2", ""),
]

for pattern, replacement in corrections:
    if callable(replacement):
        content = re.sub(pattern, replacement, content)
    else:
        content = re.sub(pattern, replacement, content)

# Corrections manuelles pour les cas problématiques
problematic_patterns = [
    # Ligne qui cause l'erreur
    (r"const response = await axios\.get\(buildApiUrl\('/stats'\), \{", "const response = await apiClient.get('/stats');"),
    (r"buildApiUrl\('/([^']+)'\)", r"'/\1'"),
]

for pattern, replacement in problematic_patterns:
    content = re.sub(pattern, replacement, content)

# Sauvegarder
with open('/app/ecomsimply-deploy/frontend/src/App.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ App.js nettoyé")
