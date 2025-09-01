#!/bin/bash

# =====================================
# SMOKE TESTS - POST DB SWITCH
# Validation non-régression après migration
# =====================================

set -e

BACKEND_URL="https://ecomsimply-deploy.preview.emergentagent.com"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="artifacts/smoke_test_${TIMESTAMP}.log"

echo "🧪 === SMOKE TESTS POST-MIGRATION ===" | tee "$LOG_FILE"
echo "Backend: $BACKEND_URL" | tee -a "$LOG_FILE"
echo "Timestamp: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

TESTS_PASSED=0
TESTS_TOTAL=0

# Helper function pour tests
run_test() {
    local test_name="$1"
    local expected_code="$2"
    local curl_cmd="$3"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    echo "  🔍 Test: $test_name" | tee -a "$LOG_FILE"
    
    response=$(eval "$curl_cmd" 2>/dev/null)
    actual_code="${response: -3}"
    
    if [ "$actual_code" = "$expected_code" ]; then
        echo "    ✅ PASS - HTTP $actual_code" | tee -a "$LOG_FILE"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo "    ❌ FAIL - Expected $expected_code, got $actual_code" | tee -a "$LOG_FILE"
        return 1
    fi
}

# =====================================
# TEST 1: HEALTH CHECK
# =====================================
echo "📋 TEST SUITE 1: Health & Configuration" | tee -a "$LOG_FILE"

echo "  🔍 Test: Health endpoint" | tee -a "$LOG_FILE"
HEALTH_RESPONSE=$(curl -s "$BACKEND_URL/api/health" 2>/dev/null || echo '{"error":"connection_failed"}')
HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.status // "error"' 2>/dev/null || echo "error")
DB_NAME=$(echo "$HEALTH_RESPONSE" | jq -r '.database // "unknown"' 2>/dev/null || echo "unknown")
MONGO_STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.mongo // "error"' 2>/dev/null || echo "error")

TESTS_TOTAL=$((TESTS_TOTAL + 1))
if [ "$HEALTH_STATUS" = "ok" ] && [ "$DB_NAME" = "ecomsimply_production" ] && [ "$MONGO_STATUS" = "ok" ]; then
    echo "    ✅ PASS - Health OK, DB=$DB_NAME, Mongo=$MONGO_STATUS" | tee -a "$LOG_FILE"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo "    ❌ FAIL - Status=$HEALTH_STATUS, DB=$DB_NAME, Mongo=$MONGO_STATUS" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"

# =====================================
# TEST 2: AUTHENTIFICATION
# =====================================
echo "📋 TEST SUITE 2: Authentication Endpoints" | tee -a "$LOG_FILE"

# Test login sans données (401 attendu)
run_test "Login sans données" "401" \
    'curl -s -X POST "$BACKEND_URL/api/auth/login" -H "Content-Type: application/json" -d "{\"email\":\"\",\"password\":\"\"}" -w "%{http_code}"'

# Test auth/me sans token (401 attendu)  
run_test "Auth/me sans token" "401" \
    'curl -s "$BACKEND_URL/api/auth/me" -w "%{http_code}"'

# Test register avec données invalides (422 attendu)
run_test "Register données invalides" "422" \
    'curl -s -X POST "$BACKEND_URL/api/auth/register" -H "Content-Type: application/json" -d "{\"name\":\"\",\"email\":\"invalid\",\"password\":\"123\"}" -w "%{http_code}"'

echo "" | tee -a "$LOG_FILE"

# =====================================
# TEST 3: ENDPOINTS PUBLICS
# =====================================
echo "📋 TEST SUITE 3: Public Endpoints" | tee -a "$LOG_FILE"

run_test "Plans pricing" "200" \
    'curl -s "$BACKEND_URL/api/public/plans-pricing" -w "%{http_code}"'

run_test "Testimonials" "200" \
    'curl -s "$BACKEND_URL/api/testimonials" -w "%{http_code}"'

run_test "Public stats" "200" \
    'curl -s "$BACKEND_URL/api/stats/public" -w "%{http_code}"'

run_test "Languages" "200" \
    'curl -s "$BACKEND_URL/api/languages" -w "%{http_code}"'

echo "" | tee -a "$LOG_FILE"

# =====================================
# TEST 4: ADMIN BOOTSTRAP
# =====================================
echo "📋 TEST SUITE 4: Admin Bootstrap" | tee -a "$LOG_FILE"

run_test "Bootstrap sans token" "403" \
    'curl -s -X POST "$BACKEND_URL/api/admin/bootstrap" -w "%{http_code}"'

run_test "Bootstrap avec token" "200" \
    'curl -s -X POST "$BACKEND_URL/api/admin/bootstrap" -H "x-bootstrap-token: ECS-Bootstrap-2025-Secure-Token" -w "%{http_code}"'

echo "" | tee -a "$LOG_FILE"

# =====================================
# TEST 5: FONCTIONNALITÉ ÉCRITURE
# =====================================
echo "📋 TEST SUITE 5: Write Operations" | tee -a "$LOG_FILE"

# Test création utilisateur complet
TEST_EMAIL="smoke-test-$(date +%s)@example.com"
echo "  🔍 Test: Création utilisateur complet" | tee -a "$LOG_FILE"
CREATE_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"Smoke Test User\",\"email\":\"$TEST_EMAIL\",\"password\":\"smoketest123\"}" \
    -w "%{http_code}")

CREATE_CODE="${CREATE_RESPONSE: -3}"
TESTS_TOTAL=$((TESTS_TOTAL + 1))

if [ "$CREATE_CODE" = "200" ] || [ "$CREATE_CODE" = "201" ]; then
    echo "    ✅ PASS - Utilisateur créé (HTTP $CREATE_CODE)" | tee -a "$LOG_FILE"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    
    # Tenter de créer le même utilisateur (409 attendu pour contrainte unique)
    echo "  🔍 Test: Contrainte unique email" | tee -a "$LOG_FILE"
    DUPLICATE_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/auth/register" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"Duplicate Test\",\"email\":\"$TEST_EMAIL\",\"password\":\"duplicate123\"}" \
        -w "%{http_code}")
    
    DUPLICATE_CODE="${DUPLICATE_RESPONSE: -3}"
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    if [ "$DUPLICATE_CODE" = "409" ]; then
        echo "    ✅ PASS - Contrainte unique email (HTTP $DUPLICATE_CODE)" | tee -a "$LOG_FILE"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "    ❌ FAIL - Expected 409, got $DUPLICATE_CODE" | tee -a "$LOG_FILE"
    fi
    
else
    echo "    ❌ FAIL - Expected 200/201, got $CREATE_CODE" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"

# =====================================
# RÉSUMÉ FINAL
# =====================================
echo "📊 === RÉSULTATS SMOKE TESTS ===" | tee -a "$LOG_FILE"
echo "Tests passés: $TESTS_PASSED/$TESTS_TOTAL" | tee -a "$LOG_FILE"

if [ $TESTS_PASSED -eq $TESTS_TOTAL ]; then
    echo "Status: ✅ TOUS LES TESTS RÉUSSIS" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    echo "🎉 Migration validée - Application opérationnelle sur ecomsimply_production" | tee -a "$LOG_FILE"
    exit 0
else
    FAILED=$((TESTS_TOTAL - TESTS_PASSED))
    echo "Status: ⚠️  $FAILED TESTS ÉCHOUÉS" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    echo "🔴 Vérification manuelle requise - Consultez les logs ci-dessus" | tee -a "$LOG_FILE"
    exit 1
fi