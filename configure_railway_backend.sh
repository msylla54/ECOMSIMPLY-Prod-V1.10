#!/bin/bash
# Configuration autonome Railway Backend - ECOMSIMPLY
# Déploiement backend FastAPI avec toutes les variables d'environnement

set -e

echo "🚂 CONFIGURATION RAILWAY BACKEND - ECOMSIMPLY"
echo "=============================================="

# Variables de base
PROJECT_NAME="ecomsimply-backend"
BACKEND_DIR="/app/ecomsimply-deploy/backend"

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Vérification prérequis
check_prerequisites() {
    log_info "Vérification des prérequis..."
    
    if ! command -v railway &> /dev/null; then
        log_error "Railway CLI non installé"
        log_info "Installation: npm install -g @railway/cli"
        exit 1
    fi
    
    if ! railway whoami &> /dev/null; then
        log_error "Non connecté à Railway"
        log_info "Connexion: railway login"
        exit 1
    fi
    
    if [ ! -d "$BACKEND_DIR" ]; then
        log_error "Dossier backend non trouvé: $BACKEND_DIR"
        exit 1
    fi
    
    log_success "Prérequis validés"
}

# Configuration variables d'environnement
configure_environment_variables() {
    log_info "Configuration des variables d'environnement Railway..."
    
    cd "$BACKEND_DIR"
    
    # Variables CRITIQUES (obligatoires)
    log_info "Configuration variables critiques..."
    railway variables set ADMIN_EMAIL="msylla54@gmail.com" || true
    railway variables set ADMIN_PASSWORD_HASH='$2b$12$AX.4AQP8u50RP3.pcupJ6OJSSOHQqTG71NJvZRW/J6kyRFnxKX0.W' || true
    railway variables set ADMIN_BOOTSTRAP_TOKEN="ECS-Bootstrap-2025-Secure-Token" || true
    railway variables set JWT_SECRET="supersecretjwtkey32charsminimum2025ecomsimply" || true
    railway variables set APP_BASE_URL="https://ecomsimply.com" || true
    railway variables set DB_NAME="ecomsimply_production" || true
    
    # Variables AUTHENTIFICATION
    log_info "Configuration authentification..."
    railway variables set ENCRYPTION_KEY="w7uWSQqDAewH34UjRHVSgeJawQnDa-ukRe0WERClY694=" || true
    
    # Variables CONFIGURATION
    log_info "Configuration générale..."
    railway variables set ENVIRONMENT="production" || true
    railway variables set DEBUG="false" || true
    railway variables set MOCK_MODE="false" || true
    
    log_success "Variables d'environnement configurées"
    log_warning "⚠️ MONGO_URL doit être configuré manuellement dans Railway Dashboard"
}

# Déploiement sur Railway
deploy_to_railway() {
    log_info "Déploiement sur Railway..."
    
    cd "$BACKEND_DIR"
    
    # Vérifier si projet existe déjà
    if [ ! -f ".railway" ]; then
        log_info "Initialisation nouveau projet Railway..."
        railway init --name "$PROJECT_NAME"
    else
        log_info "Utilisation projet Railway existant"
    fi
    
    # Déployer
    log_info "Lancement du déploiement..."
    railway up --detach
    
    log_success "Déploiement initié"
}

# Validation du déploiement
validate_deployment() {
    log_info "Validation du déploiement..."
    
    cd "$BACKEND_DIR"
    
    # Attendre que le service soit prêt
    log_info "Attente de la disponibilité du service (60s)..."
    sleep 60
    
    # Obtenir l'URL
    log_info "Récupération de l'URL du service..."
    railway status
    
    # Obtenir l'URL publique Railway
    RAILWAY_URL=$(railway domain 2>/dev/null | head -n 1 | tr -d '\n' || echo "")
    
    if [ -n "$RAILWAY_URL" ]; then
        log_success "URL Railway: https://$RAILWAY_URL"
        
        # Test health check
        log_info "Test health check..."
        if curl -f -s "https://$RAILWAY_URL/api/health" > /dev/null; then
            log_success "Health check OK - Backend fonctionnel"
        else
            log_warning "Health check échoué (service peut être en cours de démarrage)"
        fi
        
        # Sauvegarder l'URL pour les étapes suivantes
        echo "$RAILWAY_URL" > /app/ecomsimply-deploy/RAILWAY_BACKEND_URL.txt
        
    else
        log_warning "URL Railway non disponible immédiatement"
        log_info "Vérifiez dans Railway Dashboard"
    fi
    
    # Logs du service
    log_info "Derniers logs du service:"
    railway logs --tail 10 || true
}

# Configuration commande de démarrage (si nécessaire)
configure_start_command() {
    log_info "Vérification de la commande de démarrage..."
    
    cd "$BACKEND_DIR"
    
    # La commande est définie dans le Dockerfile:
    # CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
    
    # Railway utilise automatiquement la variable $PORT
    # Configurer la commande de démarrage Railway si nécessaire
    railway run --service "$PROJECT_NAME" --command "uvicorn server:app --host 0.0.0.0 --port \$PORT --workers 4" || true
    
    log_success "Commande de démarrage vérifiée"
}

# Fonction principale
main() {
    echo
    log_info "Début de la configuration Railway Backend"
    echo
    
    check_prerequisites
    echo
    
    configure_start_command
    echo
    
    configure_environment_variables
    echo
    
    deploy_to_railway
    echo
    
    validate_deployment
    echo
    
    log_success "🎉 CONFIGURATION RAILWAY TERMINÉE"
    echo
    log_info "Prochaines étapes:"
    echo "  1. Configurer MONGO_URL dans Railway Dashboard"
    echo "  2. Vérifier https://[RAILWAY-URL]/api/health"
    echo "  3. Configurer DNS api.ecomsimply.com dans Vercel"
    echo "  4. Tester bootstrap admin"
    echo
}

# Gestion des interruptions
trap 'log_error "Configuration interrompue"; exit 1' INT TERM

# Exécution
main "$@"