#!/usr/bin/env python3
"""
Script pour refactoriser AmazonIntegration.js
"""

import re

# Lire le fichier
with open('/app/ecomsimply-deploy/frontend/src/components/AmazonIntegration.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Supprimer les fonctions getApiBaseUrl et getAuthHeaders qui ne sont plus nécessaires
content = re.sub(
    r'  // Get API base URL\n  const getApiBaseUrl = \(\) => \{\n    return process\.env\.REACT_APP_BACKEND_URL \|\| \'http://localhost:8001\';\n  \};\n\n  // Get authentication headers\n  const getAuthHeaders = \(\) => \{\n    const token = localStorage\.getItem\(\'token\'\);\n    return token \? \{ Authorization: `Bearer \$\{token\}` \} : \{\};\n  \};\n\n',
    '',
    content
)

# Remplacer les appels axios par apiClient
replacements = [
    (r'await axios\.get\(\n        `\$\{getApiBaseUrl\(\)\}/api/amazon/connections`,\n        \{ headers: getAuthHeaders\(\) \}\n      \)', 'await apiClient.get(\'/amazon/connections\')'),
    (r'await axios\.post\(\n        `\$\{getApiBaseUrl\(\)\}/api/amazon/connect`,\n        \{\n          marketplace_id: selectedMarketplace,\n          region: marketplace\.region\n        \},\n        \{ headers: getAuthHeaders\(\) \}\n      \)', 'await apiClient.post(\'/amazon/connect\', {\n        marketplace_id: selectedMarketplace,\n        region: marketplace.region\n      })'),
    (r'await axios\.delete\(\n        `\$\{getApiBaseUrl\(\)\}/api/amazon/connections/\$\{connectionId\}`,\n        \{ headers: getAuthHeaders\(\) \}\n      \)', 'await apiClient.delete(`/amazon/connections/${connectionId}`)'),
]

for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

# Sauvegarder
with open('/app/ecomsimply-deploy/frontend/src/components/AmazonIntegration.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ AmazonIntegration.js refactorisé avec succès")