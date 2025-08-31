#!/bin/bash

# SCRIPT DE CONFIGURATION SSL POUR ECOMSIMPLY.COM
# Usage: ./scripts/setup-ssl.sh

DOMAIN="www.ecomsimply.com"
DOMAIN_ALT="ecomsimply.com"

echo "🔒 Configuration SSL pour $DOMAIN..."

# Vérifier si le domaine pointe vers ce serveur
echo "🔍 Vérification DNS..."
RESOLVED_IP=$(nslookup $DOMAIN | grep -A1 "Name:" | tail -1 | awk '{print $2}' | head -1)
SERVER_IP=$(curl -s ifconfig.me)

if [ "$RESOLVED_IP" != "$SERVER_IP" ]; then
    echo "⚠️  DNS pas encore propagé:"
    echo "   Domaine $DOMAIN pointe vers: $RESOLVED_IP"
    echo "   Serveur IP: $SERVER_IP"
    echo "   Attendre la propagation DNS avant de continuer..."
    exit 1
fi

echo "✅ DNS correctement propagé !"

# Installer certbot si pas déjà installé
if ! command -v certbot &> /dev/null; then
    echo "📦 Installation de certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi

# Arrêter temporairement nginx pour libérer le port 80
echo "🛑 Arrêt temporaire des services..."
systemctl stop nginx 2>/dev/null || true
docker-compose -f /app/docker-compose.yml down 2>/dev/null || true

# Générer les certificats SSL
echo "🔐 Génération certificats SSL..."
certbot certonly --standalone \
    -d $DOMAIN \
    -d $DOMAIN_ALT \
    --email admin@ecomsimply.com \
    --agree-tos \
    --non-interactive

if [ $? -eq 0 ]; then
    echo "✅ Certificats SSL générés avec succès !"
    
    # Copier les certificats
    cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /app/ssl/cert.pem
    cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /app/ssl/key.pem
    
    # Configurer les permissions
    chmod 644 /app/ssl/cert.pem
    chmod 600 /app/ssl/key.pem
    
    echo "✅ Certificats copiés dans /app/ssl/"
else
    echo "❌ Erreur lors de la génération des certificats SSL"
    echo "🔧 Génération certificats auto-signés temporaires..."
    
    openssl req -x509 -newkey rsa:4096 -keyout /app/ssl/key.pem -out /app/ssl/cert.pem -days 365 -nodes \
        -subj "/C=FR/ST=France/L=Paris/O=ECOMSIMPLY/CN=www.ecomsimply.com"
    
    echo "⚠️  Certificats auto-signés créés (à remplacer plus tard)"
fi

# Redémarrer les services
echo "🚀 Redémarrage des services..."
cd /app
docker-compose up -d

echo "🎉 Configuration SSL terminée !"
echo ""
echo "🌐 Votre site sera accessible sur :"
echo "   https://www.ecomsimply.com"
echo "   https://ecomsimply.com"