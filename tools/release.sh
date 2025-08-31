#!/bin/bash

# =================================================================
# ECOMSIMPLY RELEASE AUTOMATION SCRIPT
# Automatise la release complète vers GitHub
# =================================================================

set -e

# Configuration par défaut
BACKEND_URL=${BACKEND_URL:-"https://api.ecomsimply.com"}
APP_BASE_URL=${APP_BASE_URL:-"https://www.ecomsimply.com"}
GITHUB_OWNER=${GITHUB_OWNER:-"msylla54"}
GITHUB_REPO_NAME=${GITHUB_REPO_NAME:-"ECOMSIMPLY-Prod-V1.10"}
USE_GH_CLI=${USE_GH_CLI:-"false"}
BRANCH=${BRANCH:-"main"}

echo "🚀 === ECOMSIMPLY RELEASE AUTOMATION ==="
echo "Backend URL: $BACKEND_URL"
echo "App Base URL: $APP_BASE_URL"
echo "GitHub Owner: $GITHUB_OWNER"
echo "GitHub Repo: $GITHUB_REPO_NAME"
echo "Auth Method: $([ "$USE_GH_CLI" = "true" ] && echo "GitHub CLI" || echo "Personal Access Token")"
echo "Branch: $BRANCH"
echo ""

# =================================================================
# PHASE 1: SMOKE TESTS
# =================================================================
echo "📋 PHASE 1: SMOKE TESTS"
echo "========================================"

if [ -f "./tools/smoke.sh" ]; then
    echo "Exécution des smoke tests..."
    chmod +x ./tools/smoke.sh
    BACKEND_URL="$BACKEND_URL" APP_BASE_URL="$APP_BASE_URL" ./tools/smoke.sh
    echo "✅ Smoke tests réussis"
else
    echo "⚠️  Script smoke.sh non trouvé, continuons..."
fi

echo ""

# =================================================================
# PHASE 2: DÉTECTION REBUILD VERCEL
# =================================================================
echo "📋 PHASE 2: DÉTECTION REBUILD VERCEL"
echo "========================================"

# Vérifier si REACT_APP_BACKEND_URL dans .env frontend
CURRENT_REACT_URL=""
if [ -f "./frontend/.env" ]; then
    CURRENT_REACT_URL=$(grep "REACT_APP_BACKEND_URL" ./frontend/.env | cut -d'=' -f2 || echo "")
fi

echo "REACT_APP_BACKEND_URL actuel: $CURRENT_REACT_URL"
echo "BACKEND_URL cible: $BACKEND_URL"

if [ "$CURRENT_REACT_URL" != "$BACKEND_URL" ]; then
    echo "⚠️  REBUILD VERCEL NÉCESSAIRE:"
    echo "   - Configurer REACT_APP_BACKEND_URL=$BACKEND_URL dans Vercel"
    echo "   - Redéployer le frontend après push GitHub"
    VERCEL_REBUILD="true"
else
    echo "✅ Configuration frontend alignée"
    VERCEL_REBUILD="false"
fi

echo ""

# =================================================================
# PHASE 3: INITIALISATION GIT
# =================================================================
echo "📋 PHASE 3: INITIALISATION GIT"
echo "========================================"

# Créer .gitignore si absent
if [ ! -f ".gitignore" ]; then
    echo "Création du .gitignore..."
    cat > .gitignore << 'EOF'
# Dependencies
node_modules/
__pycache__/
*.pyc
.Python

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Build outputs
build/
dist/
*.log

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.temp
*.bak

# Logs
logs/
*.log

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/

# nyc test coverage
.nyc_output

# Dependency directories
jspm_packages/

# Optional npm cache directory
.npm

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# dotenv environment variables file
.env

# parcel-bundler cache (https://parceljs.org/)
.cache
.parcel-cache

# next.js build output
.next

# nuxt.js build output
.nuxt

# vuepress build output
.vuepress/dist

# Serverless directories
.serverless

# FuseBox cache
.fusebox/

# DynamoDB Local files
.dynamodb/

# TernJS port file
.tern-port

# Testing
/coverage

# Production
/build

# Misc
.DS_Store
.env.local
.env.development.local
.env.test.local
.env.production.local

npm-debug.log*
yarn-debug.log*
yarn-error.log*
EOF
    echo "✅ .gitignore créé"
fi

# Initialiser Git si nécessaire
if [ ! -d ".git" ]; then
    echo "Initialisation du repository Git..."
    git init
    git config user.name "ECOMSIMPLY Release Bot"
    git config user.email "release@ecomsimply.com"
    echo "✅ Git initialisé"
else
    echo "✅ Repository Git existant"
fi

echo ""

# =================================================================
# PHASE 4: DÉTERMINATION VERSION
# =================================================================
echo "📋 PHASE 4: DÉTERMINATION VERSION"
echo "========================================"

# Essayer d'extraire la version de l'API health
VERSION="unknown"
if curl -s --max-time 5 "$BACKEND_URL/api/health" > /tmp/health.json 2>/dev/null; then
    VERSION=$(grep -o '"version":"[^"]*"' /tmp/health.json | cut -d'"' -f4 2>/dev/null || echo "unknown")
    rm -f /tmp/health.json
fi

# Si pas de version dans l'API, utiliser timestamp
if [ "$VERSION" = "unknown" ] || [ -z "$VERSION" ]; then
    VERSION="v1.10.$(date +%Y%m%d%H%M)"
    echo "Version générée: $VERSION"
else
    VERSION="v$VERSION"
    echo "Version API détectée: $VERSION"
fi

echo ""

# =================================================================
# PHASE 5: COMMIT & TAG
# =================================================================
echo "📋 PHASE 5: COMMIT & TAG"
echo "========================================"

# Ajouter tous les fichiers
git add .

# Vérifier s'il y a des changements à commiter
if git diff --cached --quiet; then
    echo "Aucun changement à commiter"
else
    echo "Création du commit de release..."
    git commit -m "chore(release): prepare $VERSION

- Automated release preparation
- Backend: $BACKEND_URL
- Frontend: $APP_BASE_URL
- Vercel rebuild required: $VERCEL_REBUILD"
    echo "✅ Commit créé: $VERSION"
fi

echo ""

# =================================================================
# PHASE 6: CRÉATION REPOSITORY GITHUB
# =================================================================
echo "📋 PHASE 6: CRÉATION REPOSITORY GITHUB"
echo "========================================"

if [ "$USE_GH_CLI" = "false" ] && [ -n "$GITHUB_TOKEN" ]; then
    REPO_URL="https://$GITHUB_TOKEN@github.com/$GITHUB_OWNER/$GITHUB_REPO_NAME.git"
else
    REPO_URL="https://github.com/$GITHUB_OWNER/$GITHUB_REPO_NAME.git"
fi

if [ "$USE_GH_CLI" = "true" ]; then
    echo "Utilisation de GitHub CLI..."
    
    # Vérifier si gh est installé
    if command -v gh >/dev/null 2>&1; then
        echo "Création du repository via gh CLI..."
        gh repo create "$GITHUB_OWNER/$GITHUB_REPO_NAME" --public --description "ECOMSIMPLY Production Release $VERSION" || echo "Repository peut déjà exister"
        echo "✅ Repository GitHub créé/vérifié via CLI"
    else
        echo "❌ GitHub CLI non installé, passage au mode PAT"
        USE_GH_CLI="false"
    fi
fi

if [ "$USE_GH_CLI" = "false" ]; then
    echo "Utilisation du Personal Access Token..."
    
    if [ -z "$GITHUB_TOKEN" ]; then
        echo "❌ ERREUR: Variable GITHUB_TOKEN manquante"
        echo "Configurez votre Personal Access Token dans GITHUB_TOKEN"
        exit 1
    fi
    
    # Créer le repository via API GitHub
    echo "Création du repository via API GitHub..."
    curl -s -H "Authorization: token $GITHUB_TOKEN" \
         -H "Content-Type: application/json" \
         -d "{\"name\":\"$GITHUB_REPO_NAME\",\"description\":\"ECOMSIMPLY Production Release $VERSION\",\"private\":false}" \
         "https://api.github.com/user/repos" > /tmp/github_response.json
    
    if grep -q "already exists" /tmp/github_response.json; then
        echo "✅ Repository existe déjà"
    elif grep -q "\"id\":" /tmp/github_response.json; then
        echo "✅ Repository GitHub créé via API"
    else
        echo "⚠️  Réponse API GitHub:"
        cat /tmp/github_response.json
    fi
    
    rm -f /tmp/github_response.json
fi

echo ""

# =================================================================
# PHASE 7: PUSH & TAG
# =================================================================
echo "📋 PHASE 7: PUSH & TAG"
echo "========================================"

# Ajouter le remote GitHub
echo "Configuration du remote GitHub..."
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL"

# Push de la branche principale
echo "Push de la branche $BRANCH..."
git branch -M $BRANCH
git push -u origin $BRANCH --force

echo "✅ Code pushé vers GitHub"

# Création et push du tag
echo "Création du tag $VERSION..."
git tag -a "$VERSION" -m "Release $VERSION - $(date)" || echo "Tag peut déjà exister"
git push origin "$VERSION" --force

echo "✅ Tag $VERSION pushé"

echo ""

# =================================================================
# PHASE 8: INSTRUCTIONS FINALES
# =================================================================
echo "🎉 === RELEASE COMPLETED ==="
echo "================================"
echo ""
echo "✅ Repository GitHub: $REPO_URL"
echo "✅ Version: $VERSION"
echo "✅ Branch: $BRANCH"
echo ""
echo "📋 PROCHAINES ÉTAPES:"
echo "1. 🔗 Connecter Vercel au nouveau repository GitHub"
echo "2. ⚙️  Configurer les variables d'environnement Vercel:"
echo "   - REACT_APP_BACKEND_URL=$BACKEND_URL"
if [ "$VERCEL_REBUILD" = "true" ]; then
echo "3. 🔄 REBUILD VERCEL NÉCESSAIRE (config mise à jour)"
fi
echo ""
echo "🔍 Vérifier le repository:"
echo "   👉 $REPO_URL"
echo ""
echo "🚀 Release automation terminée!"

exit 0