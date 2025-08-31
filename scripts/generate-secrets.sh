#!/bin/bash

# GÉNÉRATEUR DE SECRETS SÉCURISÉS POUR ECOMSIMPLY
# Usage: ./scripts/generate-secrets.sh

echo "🔐 Génération des secrets sécurisés pour ECOMSIMPLY..."
echo ""

# JWT Secret
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "✅ JWT_SECRET généré:"
echo "JWT_SECRET=\"$JWT_SECRET\""
echo ""

# Encryption Key
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
echo "✅ ENCRYPTION_KEY généré:"
echo "ENCRYPTION_KEY=\"$ENCRYPTION_KEY\""
echo ""

# MongoDB Password
MONGO_PASSWORD=$(python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%^&*') for _ in range(16)))")
echo "✅ MONGO_ROOT_PASSWORD généré:"
echo "MONGO_ROOT_PASSWORD=\"$MONGO_PASSWORD\""
echo ""

# Redis Password
REDIS_PASSWORD=$(python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16)))")
echo "✅ REDIS_PASSWORD généré:"
echo "REDIS_PASSWORD=\"$REDIS_PASSWORD\""
echo ""

# Grafana Password
GRAFANA_PASSWORD=$(python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12)))")
echo "✅ GRAFANA_PASSWORD généré:"
echo "GRAFANA_PASSWORD=\"$GRAFANA_PASSWORD\""
echo ""

echo "🎯 COPIER CES VALEURS DANS VOTRE FICHIER .env"
echo "=========================================="
echo ""
echo "# SECRETS GÉNÉRÉS AUTOMATIQUEMENT"
echo "JWT_SECRET=\"$JWT_SECRET\""
echo "ENCRYPTION_KEY=\"$ENCRYPTION_KEY\""
echo "MONGO_ROOT_PASSWORD=\"$MONGO_PASSWORD\""
echo "REDIS_PASSWORD=\"$REDIS_PASSWORD\""
echo "GRAFANA_PASSWORD=\"$GRAFANA_PASSWORD\""
echo ""
echo "⚠️  IMPORTANT: Sauvegardez ces valeurs en lieu sûr !"
echo "⚠️  Ne partagez jamais ces secrets !"

# Optionellement, sauvegarder dans un fichier temporaire
echo "💾 Sauvegarde dans /tmp/ecomsimply-secrets.txt..."
cat > /tmp/ecomsimply-secrets.txt << EOF
# ECOMSIMPLY PRODUCTION SECRETS - $(date)
# ATTENTION: Fichier sensible - à supprimer après utilisation

JWT_SECRET="$JWT_SECRET"
ENCRYPTION_KEY="$ENCRYPTION_KEY"
MONGO_ROOT_PASSWORD="$MONGO_PASSWORD"
REDIS_PASSWORD="$REDIS_PASSWORD"
GRAFANA_PASSWORD="$GRAFANA_PASSWORD"
EOF

echo "✅ Secrets sauvegardés temporairement dans /tmp/ecomsimply-secrets.txt"
echo "🗑️  N'oubliez pas de supprimer ce fichier après utilisation !"