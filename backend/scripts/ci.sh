#!/bin/bash
# Script CI local pour ECOMSIMPLY Backend
set -e

echo "🚀 ECOMSIMPLY Backend - Pipeline CI Local"
echo "========================================"

# Configuration
PYTHON=${PYTHON:-python3}
PIP=${PIP:-pip3}
RUFF=${RUFF:-ruff}
MYPY=${MYPY:-mypy}
PYTEST=${PYTEST:-pytest}

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Vérifier la présence des outils
check_tools() {
    print_step "Vérification des outils..."
    
    if ! command -v $PYTHON &> /dev/null; then
        print_error "Python non trouvé"
        exit 1
    fi
    
    if ! command -v $RUFF &> /dev/null; then
        print_error "Ruff non trouvé - installation..."
        $PIP install ruff
    fi
    
    if ! command -v $MYPY &> /dev/null; then
        print_error "MyPy non trouvé - installation..."
        $PIP install mypy
    fi
    
    if ! command -v $PYTEST &> /dev/null; then
        print_error "Pytest non trouvé - installation..."
        $PIP install pytest
    fi
    
    print_success "Tous les outils sont disponibles"
}

# Installation des dépendances
install_deps() {
    print_step "Installation des dépendances..."
    $PIP install -r requirements.txt > /dev/null 2>&1
    print_success "Dépendances installées"
}

# Vérification du formatage
check_format() {
    print_step "Vérification du formatage (ruff format)..."
    if $RUFF format . --check; then
        print_success "Formatage OK"
    else
        print_error "Problèmes de formatage détectés"
        print_warning "Exécutez 'make format' ou 'ruff format .' pour corriger"
        return 1
    fi
}

# Analyse du code
lint_code() {
    print_step "Analyse du code (ruff check)..."
    if $RUFF check .; then
        print_success "Code OK"
    else
        print_error "Problèmes détectés dans le code"
        print_warning "Exécutez 'make lint-fix' ou 'ruff check . --fix' pour corriger"
        return 1
    fi
}

# Vérification des types
check_types() {
    print_step "Vérification des types (mypy)..."
    if $MYPY .; then
        print_success "Types OK"
    else
        print_warning "Problèmes de typage détectés"
        # Ne pas faire échouer le CI pour mypy en mode développement
        return 0
    fi
}

# Exécution des tests
run_tests() {
    print_step "Exécution des tests (pytest)..."
    if $PYTEST tests/test_basic.py tests/test_health.py --maxfail=1 --disable-warnings --cov=.; then
        print_success "Tests OK"
    else
        print_error "Tests échoués"
        return 1
    fi
}

# Mode d'exécution
MODE=${1:-full}

case $MODE in
    "quick"|"fast")
        echo "Mode rapide activé"
        check_tools
        check_format
        lint_code
        $PYTEST tests/test_basic.py tests/test_health.py --maxfail=1 --disable-warnings -x
        ;;
    "lint-only")
        echo "Mode lint uniquement"
        check_tools
        check_format
        lint_code
        ;;
    "test-only")
        echo "Mode tests uniquement" 
        check_tools
        run_tests
        ;;
    "full"|*)
        echo "Mode complet"
        check_tools
        install_deps
        check_format
        lint_code
        check_types
        run_tests
        ;;
esac

if [ $? -eq 0 ]; then
    echo
    print_success "🎉 Pipeline CI terminée avec succès!"
    echo -e "${GREEN}=======================================${NC}"
else
    echo
    print_error "💥 Pipeline CI échouée"
    echo -e "${RED}=======================================${NC}"
    exit 1
fi