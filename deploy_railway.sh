#!/bin/bash

# 🚂 SCRIPT DÉPLOIEMENT RAILWAY - ECOMSIMPLY BACKEND
# Automatise le déploiement du backend FastAPI sur Railway

set -e  # Exit on error

echo "🚂 DÉPLOIEMENT ECOMSIMPLY BACKEND SUR RAILWAY"
echo "=============================================="

# Variables
BACKEND_DIR="/app/ecomsimply-deploy/backend"
PROJECT_NAME="ecomsimply-backend"

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Fonction de vérification des prérequis
check_prerequisites() {
    log_info "Vérification des prérequis..."
    
    # Vérifier Railway CLI
    if ! command -v railway &> /dev/null; then
        log_error "Railway CLI non installé"
        log_info "Installation: npm install -g @railway/cli"
        exit 1
    fi
    
    # Vérifier connexion Railway
    if ! railway whoami &> /dev/null; then
        log_error "Non connecté à Railway"
        log_info "Connexion: railway login"
        exit 1
    fi
    
    # Vérifier dossier backend
    if [ ! -d "$BACKEND_DIR" ]; then
        log_error "Dossier backend non trouvé: $BACKEND_DIR"
        exit 1
    fi
    
    # Vérifier Dockerfile
    if [ ! -f "$BACKEND_DIR/Dockerfile" ]; then
        log_error "Dockerfile non trouvé dans $BACKEND_DIR"
        exit 1
    fi
    
    log_success "Prérequis validés"
}

# Fonction de configuration des variables d'environnement
configure_environment() {
    log_info "Configuration des variables d'environnement..."
    
    cd "$BACKEND_DIR"
    
    # Variables critiques (valeurs par défaut sécurisées)
    log_info "Configuration variables critiques..."
    
    # Admin & Sécurité
    railway variables set ADMIN_EMAIL="msylla54@gmail.com" || true
    railway variables set ADMIN_PASSWORD_HASH='$2b$12$AX.4AQP8u50RP3.pcupJ6OJSSOHQqTG71NJvZRW/J6kyRFnxKX0.W' || true
    railway variables set ADMIN_BOOTSTRAP_TOKEN="ECS-Bootstrap-2025-Secure-Token" || true
    railway variables set JWT_SECRET="supersecretjwtkey32charsminimum2025ecomsimply" || true
    railway variables set ENCRYPTION_KEY="w7uWSQqDAewH34UjRHVSgeJawQnDa-ukRe0WERClY694=" || true
    
    # URLs
    railway variables set APP_BASE_URL="https://ecomsimply.com" || true
    
    # Environment
    railway variables set MOCK_MODE="false" || true
    railway variables set DEBUG="false" || true
    railway variables set NODE_ENV="production" || true
    railway variables set ENVIRONMENT="production" || true
    
    log_success "Variables d'environnement configurées"
    log_warning "⚠️ IMPORTANT: Configurer MONGO_URL manuellement dans Railway Dashboard"
}

# Fonction de déploiement
deploy_backend() {
    log_info "Déploiement sur Railway..."
    
    cd "$BACKEND_DIR"
    
    # Initialiser projet si nécessaire
    if [ ! -f ".railway" ]; then
        log_info "Initialisation nouveau projet Railway..."
        railway init --name "$PROJECT_NAME"
    fi
    
    # Déployer
    log_info "Lancement du déploiement..."
    railway up --detach
    
    log_success "Déploiement initié"
}

# Fonction de validation
validate_deployment() {
    log_info "Validation du déploiement..."
    
    cd "$BACKEND_DIR"
    
    # Attendre que le déploiement soit prêt
    log_info "Attente de la disponibilité du service..."
    sleep 30
    
    # Obtenir l'URL
    log_info "Récupération de l'URL du service..."
    railway status
    
    # Tenter d'obtenir l'URL publique
    if command -v railway domain &> /dev/null; then
        RAILWAY_URL=$(railway domain 2>/dev/null | head -n 1)
        if [ -n "$RAILWAY_URL" ]; then
            log_info "URL Railway: https://$RAILWAY_URL"
            
            # Test health check
            log_info "Test health check..."
            if curl -f -s "https://$RAILWAY_URL/api/health" > /dev/null; then
                log_success "Health check OK"
            else
                log_warning "Health check échoué (service peut être en cours de démarrage)"
            fi
        else
            log_warning "URL Railway non disponible immédiatement"
        fi
    fi
    
    log_info "Vérification des logs..."
    railway logs --tail 20
}

# Fonction principale
main() {
    echo
    log_info "Début du déploiement ECOMSIMPLY Backend sur Railway"
    echo
    
    # Étapes de déploiement
    check_prerequisites
    echo
    
    configure_environment
    echo
    
    deploy_backend
    echo
    
    validate_deployment
    echo
    
    log_success "🎉 DÉPLOIEMENT RAILWAY COMPLÉTÉ"
    echo
    log_info "Prochaines étapes:"
    echo "  1. Configurer MONGO_URL dans Railway Dashboard"
    echo "  2. Vérifier https://[YOUR-RAILWAY-URL]/api/health"
    echo "  3. Configurer DNS api.ecomsimply.com dans Vercel"
    echo "  4. Tester bootstrap admin"
    echo
}

# Gestion des interruptions
trap 'log_error "Déploiement interrompu"; exit 1' INT TERM

# Exécution
main "$@"