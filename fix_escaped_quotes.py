#!/usr/bin/env python3
import re

# Lire le fichier
with open('/app/ecomsimply-deploy/frontend/src/App.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Corriger les échappements incorrects
content = re.sub(r"\\'/", "'/", content)
content = re.sub(r"\\'", "'", content) 

# Sauvegarder
with open('/app/ecomsimply-deploy/frontend/src/App.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Échappements corrigés")
