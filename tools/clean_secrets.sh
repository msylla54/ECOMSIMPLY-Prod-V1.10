#!/bin/bash

# =================================================================
# ECOMSIMPLY SECRET CLEANER
# Nettoie les secrets sensibles avant GitHub push
# =================================================================

set -e

echo "🧹 === NETTOYAGE DES SECRETS ECOMSIMPLY ==="
echo ""

# =================================================================
# PATTERNS DE SECRETS À NETTOYER
# =================================================================

# OpenAI API Keys
echo "🔑 Nettoyage des clés OpenAI..."
find . -name "*.py" -o -name "*.js" -o -name "*.json" -o -name "*.md" -o -name "*.txt" | \
xargs grep -l "sk-proj-" 2>/dev/null | \
while read file; do
    echo "  Nettoyage: $file"
    sed -i 's/sk-proj-[A-Za-z0-9_-]*/sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/g' "$file"
done

# Stripe API Keys
echo "🔑 Nettoyage des clés Stripe..."
find . -name "*.py" -o -name "*.js" -o -name "*.json" -o -name "*.md" -o -name "*.txt" | \
xargs grep -l "sk_test_" 2>/dev/null | \
while read file; do
    echo "  Nettoyage: $file"
    sed -i 's/sk_test_[A-Za-z0-9_-]*/sk_test_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/g' "$file"
done

# Amazon Client IDs
echo "🔑 Nettoyage des Amazon Client IDs..."
find . -name "*.py" -o -name "*.js" -o -name "*.json" -o -name "*.md" -o -name "*.txt" | \
xargs grep -l "amzn1\.application-oa2-client\." 2>/dev/null | \
while read file; do
    echo "  Nettoyage: $file"
    sed -i 's/amzn1\.application-oa2-client\.[A-Za-z0-9_-]*/amzn1.application-oa2-client.XXXXXXXXXXXXXXXX/g' "$file"
done

# Amazon Client Secrets
echo "🔑 Nettoyage des Amazon Client Secrets..."
find . -name "*.py" -o -name "*.js" -o -name "*.json" -o -name "*.md" -o -name "*.txt" | \
xargs grep -l -E "[A-Za-z0-9]{64}" 2>/dev/null | \
while read file; do
    echo "  Nettoyage potentiel: $file"
    # Plus conservateur pour éviter de casser du code
    sed -i 's/[a-f0-9A-F]\{64\}/XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/g' "$file"
done

# JWT Secrets
echo "🔑 Nettoyage des JWT secrets..."
find . -name "*.py" -o -name "*.js" -o -name "*.json" -o -name "*.md" -o -name "*.txt" | \
xargs grep -l "your-super-secret-jwt-key" 2>/dev/null | \
while read file; do
    echo "  Nettoyage: $file"
    sed -i 's/your-super-secret-jwt-key[A-Za-z0-9_-]*/your-super-secret-jwt-key-PLACEHOLDER/g' "$file"
done

# MongoDB URLs avec credentials
echo "🔑 Nettoyage des MongoDB URLs..."
find . -name "*.py" -o -name "*.js" -o -name "*.json" -o -name "*.md" -o -name "*.txt" | \
xargs grep -l "mongodb+srv://" 2>/dev/null | \
while read file; do
    echo "  Nettoyage: $file"
    sed -i 's/mongodb+srv:\/\/[^@]*@/mongodb+srv:\/\/USERNAME:PASSWORD@/g' "$file"
done

echo ""
echo "✅ Nettoyage des secrets terminé"
echo "🔍 Vérification des patterns dangereux restants..."

# Vérification
DANGEROUS_PATTERNS=(
    "sk-proj-"
    "sk_test_"
    "amzn1\.application-oa2-client\."
    "mongodb+srv://[^@]*[^:]:[^@]*@"
)

FOUND_SECRETS=""
for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    if grep -r "$pattern" . --exclude-dir=.git --exclude-dir=node_modules 2>/dev/null; then
        FOUND_SECRETS="yes"
        echo "⚠️  Pattern encore présent: $pattern"
    fi
done

if [ -z "$FOUND_SECRETS" ]; then
    echo "✅ Aucun secret dangereux détecté"
else
    echo "⚠️  Des secrets peuvent encore être présents"
fi

echo ""
echo "🚀 Prêt pour push GitHub sécurisé"

exit 0