# 🧪 TESTS VALIDATION PRODUCTION - ENV-FIRST (STAFF LEVEL)

## 🎯 TESTS POST-REDÉPLOIEMENT

### **1. HEALTH CHECK COMPLET**
```bash
curl -s "https://ecom-api-fixes.emergent.host/api/health" | jq '.'
```

**Attendu:**
```json
{
  "status": "ok",
  "service": "ECOMSIMPLY API",
  "database": "ecomsimply_production",
  "stripe_enabled": true,
  "config_valid": true,
  "version": "1.6.0"
}
```

### **2. CONFIGURATION BILLING**
```bash
curl -s "https://ecom-api-fixes.emergent.host/api/billing/config" | jq '.'
```

**Attendu:**
```json
{
  "success": true,
  "stripe_enabled": true,
  "stripe_price_id": "price_1RrxgjGK8qzu5V5WvOSb4uPd",
  "plan": {
    "name": "Premium",
    "trial_days": 3,
    "price": 99
  },
  "trial_text_fr": "3 jours d'essai gratuit"
}
```

### **3. PLANS PRICING**
```bash
curl -s "https://ecom-api-fixes.emergent.host/api/public/plans-pricing" | jq '.'
```

**Attendu:**
```json
{
  "ok": true,
  "plans": [{
    "plan_name": "premium",
    "stripe_price_id": "price_1RrxgjGK8qzu5V5WvOSb4uPd",
    "trial_days": 3,
    "price": 99.0
  }],
  "trial_text_fr": "3 jours d'essai gratuit"
}
```

## 🔐 TESTS STRIPE CHECKOUT

### **4. AUTHENTIFICATION TEST**
```bash
# Login admin
curl -X POST "https://ecom-api-fixes.emergent.host/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ecomsimply.com","password":"admin_password"}'
```

### **5. CRÉATION SESSION CHECKOUT**
```bash
# Avec token JWT obtenu
export JWT_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

curl -X POST "https://ecom-api-fixes.emergent.host/api/billing/checkout" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -v
```

**Attendu:**
```json
{
  "success": true,
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_...",
  "session_id": "cs_...",
  "plan_type": "premium",
  "trial_days": 3,
  "message": "Session de paiement créée avec succès"
}
```

## 🔍 VALIDATION CONFIGURATION

### **6. VÉRIFICATION ENV VARIABLES**
```bash
# Depuis le container (si accès)
echo $STRIPE_PRICE_PREMIUM
echo $STRIPE_SECRET_KEY | head -c 10
echo $MONGO_URL | cut -d'@' -f2
```

### **7. VALIDATION LOGS DÉMARRAGE**
```bash
# Chercher dans les logs
grep "Configuration loaded" /var/log/app.log
grep "Stripe enabled: true" /var/log/app.log
grep "Database: ecomsimply_production" /var/log/app.log
```

## 🚨 TESTS DE SÉCURITÉ

### **8. AUCUN SECRET HARDCODÉ**
```bash
# Scan du code déployé (si accès)
git grep -n "sk_live" .
git grep -n "whsec_" .
git grep -n "price_1RrxgjGK8qzu5V5WvOSb4uPd" .
```

**Attendu:** Aucun résultat (secrets supprimés du code)

### **9. HEADERS SÉCURITÉ**
```bash
curl -I "https://ecom-api-fixes.emergent.host/api/health"
```

Vérifier présence headers sécurité.

## 🎯 TESTS FONCTIONNELS

### **10. WORKFLOW COMPLET USER**
1. **Inscription** nouveau user
2. **Login** et récupération JWT
3. **Checkout** création session Stripe
4. **Webhook** simulation événement (si possible)

### **11. ERROR HANDLING**
```bash
# Test sans auth
curl -X POST "https://ecom-api-fixes.emergent.host/api/billing/checkout"

# Test avec token invalide
curl -X POST "https://ecom-api-fixes.emergent.host/api/billing/checkout" \
  -H "Authorization: Bearer invalid_token"
```

## 📊 MÉTRIQUES VALIDATION

### **Critères de Succès**
- [ ] `/api/health` retourne 200 avec config valide
- [ ] `/api/billing/config` montre Price ID depuis ENV
- [ ] `/api/billing/checkout` crée session Stripe valide
- [ ] Logs montrent `stripe_enabled: true`
- [ ] Aucun secret hardcodé dans git grep
- [ ] Frontend affiche 1 plan Premium + "3 jours essai"

### **Critères d'Échec**
- ❌ Price ID hardcodé dans réponses API
- ❌ Erreur 500 sur endpoints billing
- ❌ Config Stripe non chargée depuis ENV
- ❌ Secrets visibles dans git grep
- ❌ Variables ENV manquantes causent crash

## 🔧 COMMANDES UTILES DIAGNOSTIC

### **Debug Configuration**
```bash
# Test rapide santé
curl -s https://ecom-api-fixes.emergent.host/api/health | jq '.database, .stripe_enabled'

# Validation Price ID
curl -s https://ecom-api-fixes.emergent.host/api/billing/config | jq '.stripe_price_id'

# Check CORS
curl -H "Origin: https://ecomsimply.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization" \
  -X OPTIONS \
  https://ecom-api-fixes.emergent.host/api/billing/checkout
```

## 📋 CHECKLIST FINALE

### **Pre-Deploy**
- [ ] STRIPE_PRICE_PREMIUM ajouté dans emergent.sh ENV
- [ ] Tous secrets supprimés du code (git grep négatif)
- [ ] Configuration centralisée dans core/config.py
- [ ] .env.example mis à jour

### **Post-Deploy** 
- [ ] Health check 200 + config valide
- [ ] Billing endpoints fonctionnels
- [ ] Stripe checkout créé avec ENV Price ID
- [ ] Frontend montre offre unique Premium
- [ ] Logs propres sans erreurs config