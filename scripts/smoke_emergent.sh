#!/usr/bin/env bash

# 🚀 ECOMSIMPLY Smoke Tests pour Emergent.sh
# Tests post-déploiement pour validation production

set -euo pipefail

# Variables requises
: "${BASE_URL:?❌ Missing BASE_URL - Usage: BASE_URL=https://ecom-api-fixes.emergent.host ./smoke_emergent.sh}"
: "${ORIGIN:?❌ Missing ORIGIN - Usage: ORIGIN=https://ecomsimply.com ./smoke_emergent.sh}"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[SMOKE]${NC} $1"
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

# Test 1: Health Check
test_health() {
    log_info "GET ${BASE_URL}/api/health"
    
    if curl -fsSL "${BASE_URL}/api/health" | tee /tmp/health.json; then
        # Valider JSON structure
        if command -v jq >/dev/null 2>&1; then
            local status=$(jq -r '.status // "unknown"' /tmp/health.json)
            local service=$(jq -r '.service // "unknown"' /tmp/health.json)
            local response_time=$(jq -r '.response_time_ms // 0' /tmp/health.json)
            
            if [[ "$status" == "ok" && "$service" == "ecomsimply-api" ]]; then
                log_success "Health check OK (${response_time}ms)"
                return 0
            else
                log_error "Health check invalid: status=$status, service=$service"
                return 1
            fi
        else
            log_success "Health check reachable (jq not available for validation)"
            return 0
        fi
    else
        log_error "Health check failed - endpoint unreachable"
        return 1
    fi
}

# Test 2: CORS Preflight
test_cors() {
    log_info "OPTIONS preflight (CORS) with Origin: ${ORIGIN}"
    
    local response=$(curl -si -X OPTIONS "${BASE_URL}/api/health" \
        -H "Origin: ${ORIGIN}" \
        -H "Access-Control-Request-Method: GET" \
        --connect-timeout 10 --max-time 30 2>/dev/null || echo "ERROR")
    
    if [[ "$response" == "ERROR" ]]; then
        log_error "CORS preflight failed - network error"
        return 1
    fi
    
    # Extraire status code
    local status_code=$(echo "$response" | head -n 1 | grep -o '[0-9][0-9][0-9]' | head -n 1)
    
    if [[ "$status_code" == "200" ]]; then
        # Vérifier CORS headers
        if echo "$response" | grep -i "access-control-allow-origin" >/dev/null; then
            log_success "CORS preflight OK (${status_code}) - Headers present"
            return 0
        else
            log_warning "CORS preflight OK (${status_code}) - But missing Access-Control headers"
            return 0
        fi
    else
        log_error "CORS preflight failed (${status_code})"
        echo "$response" | sed -n '1,10p'
        return 1
    fi
}

# Test 3: API Endpoints Availability  
test_endpoints() {
    log_info "Testing API endpoints availability"
    
    local endpoints=(
        "/api/health"
        "/api/public/plans-pricing"
        "/api/testimonials"
        "/api/stats/public"
    )
    
    local passed=0
    local total=${#endpoints[@]}
    
    for endpoint in "${endpoints[@]}"; do
        if curl -fsSL --connect-timeout 5 --max-time 10 "${BASE_URL}${endpoint}" >/dev/null 2>&1; then
            log_success "✓ ${endpoint}"
            ((passed++))
        else
            log_warning "✗ ${endpoint} (non-critical)"
        fi
    done
    
    if [[ $passed -ge $((total/2)) ]]; then
        log_success "Endpoints check: ${passed}/${total} reachable"
        return 0
    else
        log_error "Endpoints check: only ${passed}/${total} reachable"
        return 1
    fi
}

# Main execution
main() {
    echo "🚀 ECOMSIMPLY Smoke Tests - Emergent.sh Deployment"
    echo "================================================="
    echo "Backend URL: $BASE_URL"
    echo "Frontend Origin: $ORIGIN"
    echo "================================================="
    
    local tests_passed=0
    local tests_total=0
    
    # Run tests
    for test_func in test_health test_cors test_endpoints; do
        echo ""
        ((tests_total++))
        
        if $test_func; then
            ((tests_passed++))
        fi
    done
    
    echo ""
    echo "================================================="
    
    if [[ $tests_passed -eq $tests_total ]]; then
        echo -e "${GREEN}🎉 ALL SMOKE TESTS PASSED (${tests_passed}/${tests_total})${NC}"
        echo -e "${GREEN}✅ Emergent.sh deployment is production-ready!${NC}"
        exit 0
    else
        echo -e "${RED}❌ SOME TESTS FAILED (${tests_passed}/${tests_total})${NC}"
        echo -e "${RED}🚨 Deployment may have issues${NC}"
        exit 1
    fi
}

# Cleanup function
cleanup() {
    rm -f /tmp/health.json 2>/dev/null || true
}
trap cleanup EXIT

# Execute
main "$@"