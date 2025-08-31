#!/bin/bash

# ================================================================================
# ECOMSIMPLY - SCRIPT DE VÉRIFICATION EXTRACTION PAGE D'ACCUEIL
# ================================================================================

set -e  # Exit on error

echo "🔍 VÉRIFICATION DE L'EXTRACTION PAGE D'ACCUEIL ECOMSIMPLY"
echo "========================================================"

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
README_FILE="/app/EXTRACTION_HOME_README.md"
ARCHIVE_FILE="/app/EXTRACTION_HOME_CODE.tar.gz"
EXTRACT_DIR="/tmp/home_extract"
TESTS_PASSED=0
TESTS_TOTAL=5

echo -e "${BLUE}📋 Tests de vérification de l'extraction${NC}"
echo

# ================================================================================
# TEST 1: Vérifier l'existence du README
# ================================================================================

echo -n "Test 1/5: Vérification existence README... "
if [ -f "$README_FILE" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ FAIL - README manquant${NC}"
fi

# ================================================================================
# TEST 2: Vérifier l'existence de l'archive
# ================================================================================

echo -n "Test 2/5: Vérification existence archive... "
if [ -f "$ARCHIVE_FILE" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    
    # Vérifier l'intégrité de l'archive
    echo -n "         Vérification intégrité archive... "
    if tar -tzf "$ARCHIVE_FILE" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
    else
        echo -e "${RED}❌ FAIL - Archive corrompue${NC}"
    fi
else
    echo -e "${RED}❌ FAIL - Archive manquante${NC}"
fi

# ================================================================================
# TEST 3: Vérifier le contenu du README
# ================================================================================

echo -n "Test 3/5: Vérification contenu README... "
if grep -q "LandingPage" "$README_FILE" && grep -q "App.js" "$README_FILE"; then
    echo -e "${GREEN}✅ PASS${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ FAIL - Contenu README incomplet${NC}"
fi

# ================================================================================
# TEST 4: Vérifier les fichiers extraits
# ================================================================================

echo -n "Test 4/5: Vérification fichiers extraits... "
if [ -d "$EXTRACT_DIR" ]; then
    FILE_COUNT=$(find "$EXTRACT_DIR" -name "*.js" -o -name "*.css" | wc -l)
    if [ "$FILE_COUNT" -ge 10 ]; then
        echo -e "${GREEN}✅ PASS ($FILE_COUNT fichiers)${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL - Pas assez de fichiers ($FILE_COUNT/10+)${NC}"
    fi
else
    echo -e "${RED}❌ FAIL - Répertoire d'extraction manquant${NC}"
fi

# ================================================================================
# TEST 5: Vérifier la présence des composants essentiels
# ================================================================================

echo -n "Test 5/5: Vérification composants essentiels... "
REQUIRED_FILES=(
    "frontend/src/index.js"
    "frontend/src/App.js"
    "frontend/src/App.css"
    "frontend/src/components/SubscriptionManager.js"
)

ALL_FOUND=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$EXTRACT_DIR/$file" ]; then
        ALL_FOUND=false
        echo -e "\n${RED}   ❌ Fichier manquant: $file${NC}"
    fi
done

if $ALL_FOUND; then
    echo -e "${GREEN}✅ PASS${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ FAIL - Fichiers essentiels manquants${NC}"
fi

# ================================================================================
# RÉSUMÉ FINAL
# ================================================================================

echo
echo -e "${BLUE}📊 RÉSUMÉ DE LA VÉRIFICATION${NC}"
echo "================================="

if [ -f "$README_FILE" ]; then
    README_SIZE=$(du -h "$README_FILE" | cut -f1)
    echo -e "📄 README: ${GREEN}$README_SIZE${NC}"
fi

if [ -f "$ARCHIVE_FILE" ]; then
    ARCHIVE_SIZE=$(du -h "$ARCHIVE_FILE" | cut -f1)
    echo -e "📦 Archive: ${GREEN}$ARCHIVE_SIZE${NC}"
fi

if [ -d "$EXTRACT_DIR" ]; then
    FILE_COUNT=$(find "$EXTRACT_DIR" -type f | wc -l)
    echo -e "📁 Fichiers extraits: ${GREEN}$FILE_COUNT${NC}"
fi

echo -e "✅ Tests réussis: ${GREEN}$TESTS_PASSED/$TESTS_TOTAL${NC}"

# ================================================================================
# RÉSULTAT FINAL
# ================================================================================

echo
if [ "$TESTS_PASSED" -eq "$TESTS_TOTAL" ]; then
    echo -e "${GREEN}🎉 EXTRACTION VALIDÉE AVEC SUCCÈS !${NC}"
    echo -e "${GREEN}Tous les tests sont passés. L'extraction est complète et prête à utiliser.${NC}"
    exit 0
else
    echo -e "${RED}❌ EXTRACTION INCOMPLÈTE${NC}"
    echo -e "${RED}$((TESTS_TOTAL - TESTS_PASSED)) test(s) ont échoué. Veuillez corriger les problèmes.${NC}"
    exit 1
fi