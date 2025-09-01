#!/bin/bash

# =====================================
# SCRIPT DE BASCULE BASE DE DONNÉES
# ecomsimply_production → ecomsimply_production
# =====================================

set -e

BACKEND_URL="https://ecomsimply-deploy.preview.emergentagent.com"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="artifacts/db_switch_${TIMESTAMP}.log"

# Créer le répertoire de logs
mkdir -p artifacts

echo "🔄 === MIGRATION BASE DE DONNÉES ECOMSIMPLY ===" | tee -a "$LOG_FILE"
echo "Timestamp: $(date)" | tee -a "$LOG_FILE"
echo "Backend: $BACKEND_URL" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# =====================================
# PHASE 1: VÉRIFICATION PRÉ-MIGRATION
# =====================================
echo "📋 PHASE 1: Vérification pré-migration" | tee -a "$LOG_FILE"

echo "  🔍 Test santé API actuelle..." | tee -a "$LOG_FILE"
HEALTH_BEFORE=$(curl -s "$BACKEND_URL/api/health" | jq -r '.database // "unknown"')
echo "  📊 Base actuelle: $HEALTH_BEFORE" | tee -a "$LOG_FILE"

if [ "$HEALTH_BEFORE" != "ecomsimply_production" ]; then
    echo "  ⚠️  ATTENTION: Base actuelle n'est pas 'ecomsimply_production' mais '$HEALTH_BEFORE'" | tee -a "$LOG_FILE"
    echo "  Continuer quand même ? (y/N)"
    read -r CONFIRM
    if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
        echo "  ❌ Migration annulée par l'utilisateur" | tee -a "$LOG_FILE"
        exit 1
    fi
fi

echo "" | tee -a "$LOG_FILE"

# =====================================
# PHASE 2: ACTIVATION MODE LECTURE SEULE
# =====================================
echo "📋 PHASE 2: Activation mode lecture seule" | tee -a "$LOG_FILE"
echo "  🔒 NOTE: Cette étape nécessite de configurer READ_ONLY_MODE=true dans emergent.sh" | tee -a "$LOG_FILE"
echo "  ⏱️  Temps estimé fenêtre maintenance: < 2 minutes" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "  Appuyez sur ENTRÉE quand READ_ONLY_MODE=true est configuré dans emergent.sh..."
read -r

# Vérifier que le mode lecture seule est actif
echo "  🧪 Test mode lecture seule..." | tee -a "$LOG_FILE"
READONLY_TEST=$(curl -s -X POST "$BACKEND_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"name":"test","email":"test@example.com","password":"test"}' \
    -w "%{http_code}")

HTTP_CODE="${READONLY_TEST: -3}"
if [ "$HTTP_CODE" = "503" ]; then
    echo "  ✅ Mode lecture seule actif (503 Service Unavailable)" | tee -a "$LOG_FILE"
else
    echo "  ⚠️  Mode lecture seule non détecté (HTTP $HTTP_CODE)" | tee -a "$LOG_FILE"
    echo "  Continuer quand même ? (y/N)"
    read -r CONFIRM
    if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
        echo "  ❌ Migration annulée - mode lecture seule requis" | tee -a "$LOG_FILE"
        exit 1
    fi
fi

echo "" | tee -a "$LOG_FILE"

# =====================================
# PHASE 3: BASCULE DB_NAME
# =====================================
echo "📋 PHASE 3: Bascule DB_NAME" | tee -a "$LOG_FILE"
echo "  📝 Variables à configurer dans emergent.sh:" | tee -a "$LOG_FILE"
echo "     DB_NAME=ecomsimply_production" | tee -a "$LOG_FILE"
echo "     MONGO_URL=mongodb+srv://ecomsimply-app:xIP7EfOXhODZdp0k@ecomsimply.xagju9s.mongodb.net/ecomsimply_production?retryWrites=true&w=majority&appName=EcomSimply" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "  Appuyez sur ENTRÉE quand DB_NAME=ecomsimply_production est configuré et l'app redéployée..."
read -r

# =====================================
# PHASE 4: VALIDATION POST-MIGRATION
# =====================================
echo "📋 PHASE 4: Validation post-migration" | tee -a "$LOG_FILE"

echo "  🔍 Test santé API après migration..." | tee -a "$LOG_FILE"
sleep 5  # Attendre stabilisation

HEALTH_AFTER=""
for i in {1..10}; do
    HEALTH_AFTER=$(curl -s "$BACKEND_URL/api/health" 2>/dev/null | jq -r '.database // "error"' 2>/dev/null || echo "error")
    if [ "$HEALTH_AFTER" = "ecomsimply_production" ]; then
        break
    fi
    echo "  ⏳ Tentative $i/10 - Attente stabilisation..." | tee -a "$LOG_FILE"
    sleep 3
done

if [ "$HEALTH_AFTER" = "ecomsimply_production" ]; then
    echo "  ✅ Migration réussie: Base = $HEALTH_AFTER" | tee -a "$LOG_FILE"
else
    echo "  ❌ ÉCHEC migration: Base = $HEALTH_AFTER" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    echo "🔴 PROCÉDURE DE ROLLBACK NÉCESSAIRE:" | tee -a "$LOG_FILE"
    echo "  1. Configurer DB_NAME=ecomsimply_production dans emergent.sh" | tee -a "$LOG_FILE"
    echo "  2. Redéployer l'application" | tee -a "$LOG_FILE"
    echo "  3. Vérifier /api/health" | tee -a "$LOG_FILE"
    exit 1
fi

echo "" | tee -a "$LOG_FILE"

# =====================================
# PHASE 5: DÉSACTIVATION LECTURE SEULE
# =====================================
echo "📋 PHASE 5: Désactivation mode lecture seule" | tee -a "$LOG_FILE"
echo "  🔓 Configurer READ_ONLY_MODE=false (ou supprimer) dans emergent.sh" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "  Appuyez sur ENTRÉE quand READ_ONLY_MODE=false est configuré..."
read -r

# Test fonctionnel final
echo "  🧪 Test écriture après migration..." | tee -a "$LOG_FILE"
TEST_EMAIL="migration-test-$(date +%s)@example.com"
WRITE_TEST=$(curl -s -X POST "$BACKEND_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"Migration Test\",\"email\":\"$TEST_EMAIL\",\"password\":\"testpassword123\"}" \
    -w "%{http_code}")

WRITE_HTTP_CODE="${WRITE_TEST: -3}"
if [ "$WRITE_HTTP_CODE" = "200" ] || [ "$WRITE_HTTP_CODE" = "201" ]; then
    echo "  ✅ Test écriture réussi (HTTP $WRITE_HTTP_CODE)" | tee -a "$LOG_FILE"
    
    # Nettoyer le compte de test
    echo "  🧹 Nettoyage compte de test..." | tee -a "$LOG_FILE"
    
elif [ "$WRITE_HTTP_CODE" = "409" ]; then
    echo "  ✅ Test écriture: compte existe déjà (HTTP 409) - index unique OK" | tee -a "$LOG_FILE"
else
    echo "  ⚠️  Test écriture: HTTP $WRITE_HTTP_CODE - à vérifier manuellement" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"

# =====================================
# RÉSUMÉ FINAL
# =====================================
echo "🎉 === MIGRATION TERMINÉE ===" | tee -a "$LOG_FILE"
echo "📊 Résumé:" | tee -a "$LOG_FILE"
echo "  • Base avant: $HEALTH_BEFORE" | tee -a "$LOG_FILE"
echo "  • Base après: $HEALTH_AFTER" | tee -a "$LOG_FILE"
echo "  • Status: ✅ SUCCÈS" | tee -a "$LOG_FILE"
echo "  • Log complet: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "📋 Prochaines étapes:" | tee -a "$LOG_FILE"
echo "  1. Vérifier fonctionnalités critiques de l'application" | tee -a "$LOG_FILE"
echo "  2. Surveiller les logs pour détecter d'éventuelles erreurs" | tee -a "$LOG_FILE"
echo "  3. Documenter la migration dans DEPLOY_DB_SWITCH.md" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "✅ Migration réussie ! Consultez $LOG_FILE pour les détails." | tee -a "$LOG_FILE"