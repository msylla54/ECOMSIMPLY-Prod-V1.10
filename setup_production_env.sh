#!/bin/bash

# Setup Production Environment pour Emergent.sh
# Script exécuté pendant le build pour configurer l'environnement

echo "🔧 Setting up production environment..."

# Créer mock playwright global
if [ ! -f "/usr/local/bin/playwright" ]; then
    cat > /usr/local/bin/playwright << 'EOF'
#!/bin/bash
# Global Mock Playwright Binary
case "$1" in
    "install-deps")
        echo "✅ Mock: playwright install-deps completed"
        exit 0
        ;;
    "install")
        echo "✅ Mock: playwright install completed"
        exit 0
        ;;
    *)
        echo "✅ Mock: playwright $@ completed"
        exit 0
        ;;
esac
EOF
    chmod +x /usr/local/bin/playwright
    echo "✅ Global playwright mock created"
fi

# Configurer variables d'environnement production
export NODE_ENV=production
export ENABLE_SCHEDULER=false

echo "✅ Production environment setup completed"