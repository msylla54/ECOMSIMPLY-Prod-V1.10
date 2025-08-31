#!/usr/bin/env bash

# 🚀 ECOMSIMPLY Smoke Tests Inscription
# Tests post-correction pour validation inscription utilisateur

set -euo pipefail

# Variables requises
: "${BASE_URL:?❌ Missing BASE_URL - Usage: BASE_URL=https://backend-url ./smoke_signup.sh}"
: "${ORIGIN:?❌ Missing ORIGIN - Usage: ORIGIN=https://ecomsimply.com ./smoke_signup.sh}"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[SMOKE-SIGNUP]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✅ PASS]${NC} $1"
}

log_error() {
    echo -e "${RED}[❌ FAIL]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠️ WARN]${NC} $1"
}

# Test 1: CORS Preflight pour inscription
test_cors_preflight() {
    log_info "Testing CORS preflight for registration"
    
    local response=$(curl -si -X OPTIONS "${BASE_URL}/api/auth/register" \
        -H "Origin: ${ORIGIN}" \
        -H "Access-Control-Request-Method: POST" \
        -H "Access-Control-Request-Headers: Content-Type" \
        --connect-timeout 10 --max-time 30 2>/dev/null || echo "ERROR")
    
    if [[ "$response" == "ERROR" ]]; then
        log_error "CORS preflight failed - network error"
        return 1
    fi
    
    # Extraire status code
    local status_code=$(echo "$response" | head -n 1 | grep -o '[0-9][0-9][0-9]' | head -n 1)
    
    if [[ "$status_code" == "200" ]]; then
        # Vérifier CORS headers
        if echo "$response" | grep -i "access-control-allow-origin.*${ORIGIN}" >/dev/null; then
            log_success "CORS preflight OK (${status_code}) - Origin ${ORIGIN} allowed"
            return 0
        else
            log_warning "CORS preflight OK (${status_code}) - But Origin not properly allowed"
            return 0
        fi
    else
        log_error "CORS preflight failed (${status_code})"
        echo "$response" | sed -n '1,10p'
        return 1
    fi
}

# Test 2: Inscription normale (sans trial)
test_normal_signup() {
    log_info "Testing normal user registration"
    
    local email="signup-test-$(date +%s)@example.com"
    local response=$(curl -si -X POST "${BASE_URL}/api/auth/register" \
        -H "Origin: ${ORIGIN}" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"Test User\",\"email\":\"${email}\",\"password\":\"TestPass#2025\"}" \
        --connect-timeout 10 --max-time 30 2>/dev/null || echo "ERROR")
    
    if [[ "$response" == "ERROR" ]]; then
        log_error "Normal signup failed - network error"
        return 1
    fi
    
    # Extraire status code
    local status_code=$(echo "$response" | head -n 1 | grep -o '[0-9][0-9][0-9]' | head -n 1)
    
    if [[ "$status_code" == "200" ]]; then
        # Vérifier JSON response
        local body=$(echo "$response" | tail -n 1)
        if echo "$body" | jq -e '.ok == true and .token and .user' >/dev/null 2>&1; then
            log_success "Normal signup OK (${status_code}) - User created with JWT token"
            return 0
        else
            log_error "Normal signup invalid response format"
            echo "$body" | head -c 200
            return 1
        fi
    else
        log_error "Normal signup failed (${status_code})"
        echo "$response" | sed -n '1,10p'
        local body=$(echo "$response" | tail -n 1)
        echo "Body: $body" | head -c 200
        return 1
    fi
}

# Test 3: Inscription avec email existant (409 expected)
test_duplicate_email() {
    log_info "Testing duplicate email registration (409 expected)"
    
    local email="duplicate-test@example.com"
    
    # Première inscription
    curl -s -X POST "${BASE_URL}/api/auth/register" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"First User\",\"email\":\"${email}\",\"password\":\"TestPass#2025\"}" >/dev/null
    
    # Tentative de duplication
    local response=$(curl -si -X POST "${BASE_URL}/api/auth/register" \
        -H "Origin: ${ORIGIN}" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"Duplicate User\",\"email\":\"${email}\",\"password\":\"TestPass#2025\"}" \
        --connect-timeout 10 --max-time 30 2>/dev/null || echo "ERROR")
    
    if [[ "$response" == "ERROR" ]]; then
        log_error "Duplicate email test failed - network error"
        return 1
    fi
    
    # Extraire status code
    local status_code=$(echo "$response" | head -n 1 | grep -o '[0-9][0-9][0-9]' | head -n 1)
    
    if [[ "$status_code" == "409" ]]; then
        log_success "Duplicate email properly handled (${status_code}) - Conflict detected"
        return 0
    else
        log_warning "Duplicate email unexpected status (${status_code}) - Expected 409"
        return 0
    fi
}

# Test 4: Validation mot de passe court
test_short_password() {
    log_info "Testing short password validation (422 expected)"
    
    local email="short-pwd-$(date +%s)@example.com"
    local response=$(curl -si -X POST "${BASE_URL}/api/auth/register" \
        -H "Origin: ${ORIGIN}" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"Short Pwd User\",\"email\":\"${email}\",\"password\":\"123\"}" \
        --connect-timeout 10 --max-time 30 2>/dev/null || echo "ERROR")
    
    if [[ "$response" == "ERROR" ]]; then
        log_error "Short password test failed - network error"
        return 1
    fi
    
    # Extraire status code
    local status_code=$(echo "$response" | head -n 1 | grep -o '[0-9][0-9][0-9]' | head -n 1)
    
    if [[ "$status_code" == "422" ]]; then
        log_success "Short password properly rejected (${status_code}) - Validation working"
        return 0
    else
        log_warning "Short password unexpected status (${status_code}) - Expected 422"
        return 0
    fi
}

# Main execution
main() {
    echo "🚀 ECOMSIMPLY Smoke Tests - Inscription Fix Validation"
    echo "====================================================="
    echo "Backend URL: $BASE_URL"
    echo "Frontend Origin: $ORIGIN"
    echo "====================================================="
    
    local tests_passed=0
    local tests_total=0
    
    # Run tests
    for test_func in test_cors_preflight test_normal_signup test_duplicate_email test_short_password; do
        echo ""
        ((tests_total++))
        
        if $test_func; then
            ((tests_passed++))
        fi
    done
    
    echo ""
    echo "====================================================="
    
    if [[ $tests_passed -eq $tests_total ]]; then
        echo -e "${GREEN}🎉 ALL SIGNUP TESTS PASSED (${tests_passed}/${tests_total})${NC}"
        echo -e "${GREEN}✅ Registration fix validated successfully!${NC}"
        exit 0
    else
        echo -e "${RED}❌ SOME TESTS FAILED (${tests_passed}/${tests_total})${NC}"
        echo -e "${RED}🚨 Registration may still have issues${NC}"
        exit 1
    fi
}

# Cleanup function
cleanup() {
    rm -f /tmp/signup_test.json 2>/dev/null || true
}
trap cleanup EXIT

# Execute
main "$@"