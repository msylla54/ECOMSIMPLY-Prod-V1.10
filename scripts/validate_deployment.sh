#!/bin/bash

# 🔍 ECOMSIMPLY - Validation Pré-Déploiement Emergent.sh
# Script de validation complète avant déclenchement du déploiement

set -e

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
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

# Test 1: Structure du projet après nettoyage
test_project_structure() {
    log_info "Validating cleaned project structure..."
    
    local errors=0
    
    # Vérifier que les doublons ont été supprimés
    if [ -f "backend/server_backup.py" ]; then
        log_error "Code mort détecté: backend/server_backup.py (devrait être supprimé)"
        ((errors++))
    else
        log_success "Code mort supprimé: backend/server_backup.py"
    fi
    
    if [ -f "backend/Dockerfile" ]; then
        log_error "Doublon détecté: backend/Dockerfile (devrait être supprimé)"
        ((errors++))
    else
        log_success "Doublon supprimé: backend/Dockerfile"
    fi
    
    if [ -f "frontend/Dockerfile" ]; then
        log_error "Legacy détecté: frontend/Dockerfile (devrait être supprimé)"
        ((errors++))
    else
        log_success "Legacy supprimé: frontend/Dockerfile"
    fi
    
    # Vérifier la structure cible
    if [ -f "backend/server.py" ] && [ -f "Dockerfile" ]; then
        log_success "Structure cible valide: backend/server.py + Dockerfile racine"
    else
        log_error "Structure cible invalide"
        ((errors++))
    fi
    
    return $errors
}

# Test 2: Configuration des variables d'environnement
test_env_config() {
    log_info "Validating environment variables configuration..."
    
    local errors=0
    
    # Variables obligatoires dans .env.example
    local required_vars=(
        "APP_BASE_URL"
        "JWT_SECRET" 
        "ENCRYPTION_KEY"
        "ADMIN_BOOTSTRAP_TOKEN"
        "MONGO_URL"
        "ENABLE_SCHEDULER"
        "LOG_LEVEL"
        "WORKERS"
    )
    
    for var in "${required_vars[@]}"; do
        if grep -q "^$var=" .env.example; then
            log_success "Variable obligatoire présente: $var"
        else
            log_error "Variable obligatoire manquante: $var"
            ((errors++))
        fi
    done
    
    # Vérifier que ENABLE_SCHEDULER=false par défaut
    if grep -q "ENABLE_SCHEDULER=false" .env.example; then
        log_success "Scheduler désactivé par défaut (ENABLE_SCHEDULER=false)"
    else
        log_warning "ENABLE_SCHEDULER devrait être false par défaut"
    fi
    
    return $errors
}

# Test 3: Dockerfile optimisé
test_dockerfile() {
    log_info "Validating Dockerfile configuration..."
    
    local errors=0
    
    # Port dynamique
    if grep -q '${PORT:-8001}' Dockerfile; then
        log_success "Port dynamique configuré: \${PORT:-8001}"
    else
        log_error "Port dynamique manquant dans Dockerfile"
        ((errors++))
    fi
    
    # HEALTHCHECK
    if grep -q "HEALTHCHECK" Dockerfile; then
        log_success "HEALTHCHECK présent dans Dockerfile"
    else
        log_error "HEALTHCHECK manquant dans Dockerfile"
        ((errors++))
    fi
    
    # Workers
    if grep -q "WORKERS" Dockerfile; then
        log_success "Configuration WORKERS présente"
    else
        log_warning "Configuration WORKERS recommandée"
    fi
    
    return $errors
}

# Test 4: Backend server configuration
test_backend_config() {
    log_info "Validating backend server configuration..."
    
    local errors=0
    
    cd backend || return 1
    
    # Test import du serveur
    if python3 -c "from server import app, _is_true, get_allowed_origins; print('✅ Import OK')" 2>/dev/null; then
        log_success "Backend server importable sans erreur"
    else
        log_error "Erreur d'import du backend server"
        ((errors++))
    fi
    
    # Vérifier les fonctions critiques
    if python3 -c "from server import _is_true; assert _is_true('true') == True; assert _is_true('false') == False; print('✅ _is_true OK')" 2>/dev/null; then
        log_success "Fonction _is_true fonctionnelle"
    else
        log_error "Fonction _is_true défaillante"
        ((errors++))
    fi
    
    cd ..
    return $errors
}

# Test 5: CORS configuration
test_cors_config() {
    log_info "Validating CORS configuration..."
    
    local errors=0
    
    # Vérifier qu'il n'y a pas de wildcard
    if grep -q 'allow_origins=\["*"\]' backend/server.py; then
        log_error "CORS wildcard détecté - sécurité compromise"
        ((errors++))
    else
        log_success "Pas de CORS wildcard - configuration sécurisée"
    fi
    
    # Vérifier la fonction get_allowed_origins
    if grep -q "get_allowed_origins" backend/server.py; then
        log_success "Fonction CORS dynamique présente"
    else
        log_error "Fonction CORS dynamique manquante"
        ((errors++))
    fi
    
    return $errors
}

# Test 6: Documentation
test_documentation() {
    log_info "Validating deployment documentation..."
    
    local errors=0
    
    # Fichiers essentiels
    local required_docs=(
        "DEPLOY_EMERGENT.md"
        ".env.example"
        "scripts/smoke_emergent.sh"
    )
    
    for doc in "${required_docs[@]}"; do
        if [ -f "$doc" ]; then
            log_success "Documentation présente: $doc"
        else
            log_error "Documentation manquante: $doc"
            ((errors++))
        fi
    done
    
    # Vérifier que smoke_emergent.sh est exécutable
    if [ -x "scripts/smoke_emergent.sh" ]; then
        log_success "Script smoke tests exécutable"
    else
        log_warning "Script smoke tests non exécutable (chmod +x requis)"
    fi
    
    return $errors
}

# Test 7: Archives de nettoyage
test_cleanup_archives() {
    log_info "Validating cleanup archives..."
    
    local test_count=$(ls tests_archive/ 2>/dev/null | wc -l)
    local docs_count=$(ls docs_archive/ 2>/dev/null | wc -l)
    
    if [ $test_count -gt 0 ]; then
        log_success "Tests legacy archivés: $test_count fichiers"
    else
        log_warning "Aucun test archivé trouvé"
    fi
    
    if [ $docs_count -gt 0 ]; then
        log_success "Docs legacy archivés: $docs_count fichiers"
    else
        log_warning "Aucun doc archivé trouvé"
    fi
    
    return 0
}

# Fonction principale
main() {
    echo -e "${BLUE}🔍 ECOMSIMPLY Validation Pré-Déploiement Emergent.sh${NC}"
    echo "=========================================================="
    echo "Validation de la configuration avant déploiement manuel"
    echo "=========================================================="
    
    local total_tests=0
    local passed_tests=0
    local total_errors=0
    
    # Exécuter tous les tests
    local tests=(
        "test_project_structure"
        "test_env_config"
        "test_dockerfile"
        "test_backend_config"
        "test_cors_config"
        "test_documentation"
        "test_cleanup_archives"
    )
    
    for test_func in "${tests[@]}"; do
        echo ""
        ((total_tests++))
        
        if $test_func; then
            ((passed_tests++))
        else
            local errors=$?
            ((total_errors += errors))
        fi
    done
    
    echo ""
    echo "=========================================================="
    
    if [ $passed_tests -eq $total_tests ] && [ $total_errors -eq 0 ]; then
        echo -e "${GREEN}🎉 VALIDATION COMPLÈTE RÉUSSIE ($passed_tests/$total_tests)${NC}"
        echo -e "${GREEN}✅ Projet prêt pour déploiement emergent.sh !${NC}"
        echo ""
        echo -e "${BLUE}📋 Prochaines étapes:${NC}"
        echo "1. Configurer les variables d'environnement dans emergent.sh"
        echo "2. Lancer 'Start Deployment' dans le dashboard emergent.sh"
        echo "3. Tester avec: BASE_URL=https://your-domain ./scripts/smoke_emergent.sh"
        exit 0
    else
        echo -e "${RED}❌ VALIDATION ÉCHOUÉE ($passed_tests/$total_tests tests réussis, $total_errors erreurs)${NC}"
        echo -e "${RED}🚨 Corriger les erreurs avant déploiement${NC}"
        exit 1
    fi
}

# Validation des prérequis
if [ ! -f "backend/server.py" ]; then
    log_error "Répertoire incorrect - Exécuter depuis /app/ECOMSIMPLY-Prod-V1.6/"
    exit 1
fi

# Exécuter la validation
main "$@"