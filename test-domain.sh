#!/bin/bash

# Script de test d'accès à www.ecomsimply.com
# Usage: ./test-domain.sh

DOMAIN="www.ecomsimply.com"
SERVER_IP="34.121.6.206"

echo "🔍 Test d'accès à ECOMSIMPLY.COM..."
echo "=================================="

# Test 1: Résolution DNS  
echo "1. 🌐 Test résolution DNS:"
RESOLVED_IP=$(nslookup $DOMAIN 8.8.8.8 2>/dev/null | grep "Address:" | tail -1 | awk '{print $2}')
if [ "$RESOLVED_IP" = "$SERVER_IP" ]; then
    echo "   ✅ DNS résolu: $DOMAIN -> $RESOLVED_IP"
    DNS_OK=true
else
    echo "   ⏳ DNS en propagation: $DOMAIN -> $RESOLVED_IP (attendu: $SERVER_IP)"
    DNS_OK=false
fi

# Test 2: Accès HTTP (devrait rediriger vers HTTPS)
echo "2. 🌍 Test accès HTTP:"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "301" ] || [ "$HTTP_STATUS" = "302" ]; then
    echo "   ✅ HTTP redirige vers HTTPS (Status: $HTTP_STATUS)"
elif [ "$HTTP_STATUS" = "000" ]; then
    echo "   ⏳ Domaine pas encore accessible (DNS en propagation)"
else
    echo "   ⚠️  HTTP Status inattendu: $HTTP_STATUS"
fi

# Test 3: Accès HTTPS
echo "3. 🔒 Test accès HTTPS:"
if $DNS_OK; then
    HTTPS_STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" https://$DOMAIN 2>/dev/null || echo "000")
    if [ "$HTTPS_STATUS" = "200" ]; then
        echo "   ✅ HTTPS accessible (Status: $HTTPS_STATUS)"
        HTTPS_OK=true
    else
        echo "   ⚠️  HTTPS Status: $HTTPS_STATUS"
        HTTPS_OK=false
    fi
else
    echo "   ⏳ Skip HTTPS (DNS pas encore propagé)"
    HTTPS_OK=false
fi

# Test 4: API Backend
echo "4. 🔧 Test API Backend:"
if $HTTPS_OK; then
    API_RESPONSE=$(curl -k -s https://$DOMAIN/api/health 2>/dev/null || echo "ERROR")
    if echo "$API_RESPONSE" | grep -q '"status":"healthy"'; then
        echo "   ✅ API Backend fonctionnelle"
        API_OK=true
    else
        echo "   ⚠️  API Response: $API_RESPONSE"
        API_OK=false
    fi
else
    echo "   ⏳ Skip API (HTTPS pas accessible)"
    API_OK=false
fi

# Résumé final
echo ""
echo "📊 RÉSUMÉ FINAL:"
echo "==============="
if $DNS_OK && $HTTPS_OK && $API_OK; then
    echo "🎉 ECOMSIMPLY.COM EST ENTIÈREMENT OPÉRATIONNEL !"
    echo ""
    echo "🌐 Accès public:"
    echo "   Frontend: https://www.ecomsimply.com"
    echo "   API:      https://www.ecomsimply.com/api/health"
    echo ""
    echo "✅ Prêt pour les utilisateurs !"
elif $DNS_OK; then
    echo "⏳ DNS propagé, services en cours de finalisation..."
    echo "   Réessayer dans 5-10 minutes"
else
    echo "⏳ En attente de propagation DNS..."
    echo "   Cela peut prendre 5-30 minutes après modification DNS"
    echo "   Réessayer périodiquement avec: ./test-domain.sh"
fi

echo ""
echo "🔄 Pour relancer ce test: ./test-domain.sh"