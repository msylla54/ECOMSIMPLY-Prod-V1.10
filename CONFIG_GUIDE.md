# 🔧 ECOMSIMPLY - GUIDE CONFIGURATION ENV-FIRST (STAFF LEVEL)

## 🎯 PRINCIPE ENV-FIRST

**AUCUNE valeur sensible hardcodée dans le code. Toute configuration vient exclusivement de l'environnement.**

## 📋 RESPONSABILITÉS

### **Backend FastAPI**
- Configuration centralisée dans `backend/core/config.py`
- Validation automatique des variables ENV au démarrage
- Guards et erreurs explicites si configuration manquante

### **Frontend React/Vercel** 
- Variables publiques via `VITE_*` ou `NEXT_PUBLIC_*`
- **AUCUNE clé secrète côté client**
- Build-time injection des variables

## 🔐 VARIABLES OBLIGATOIRES

### **1. DATABASE**
```bash
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/ecomsimply_production
# DB_NAME optionnel - extrait automatiquement de l'URL
```

### **2. SECURITY**
```bash
JWT_SECRET=your-32char-minimum-secret-here
ENCRYPTION_KEY=your-32char-minimum-encryption-key
ADMIN_EMAIL=admin@ecomsimply.com
ADMIN_PASSWORD_HASH=$2b$12$hashed_password_here
ADMIN_BOOTSTRAP_TOKEN=secure-bootstrap-token
```

### **3. STRIPE BILLING**
```bash
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
STRIPE_PRICE_PREMIUM=price_1RrxgjGK8qzu5V5WvOSb4uPd
BILLING_SUCCESS_URL=https://app.ecomsimply.com/billing/success?session_id={CHECKOUT_SESSION_ID}
BILLING_CANCEL_URL=https://app.ecomsimply.com/billing/cancel
```

### **4. CORS & NETWORKING**
```bash
APP_BASE_URL=https://ecomsimply.com
ADDITIONAL_ALLOWED_ORIGINS=https://additional-domain.com,https://another.com
```

## 🔧 CONFIGURATION EMERGENT.SH

### **Variables à ajouter dans Env Variables (Production scope):**

1. **Ajouter** `STRIPE_PRICE_PREMIUM=price_1RrxgjGK8qzu5V5WvOSb4uPd`
2. **Vérifier** toutes les autres variables sont présentes
3. **Pas de doublons** entre scopes

### **emergent.config.json mis à jour:**
```json
{
  "optional_variables": [
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "STRIPE_PRICE_PREMIUM",
    "BILLING_SUCCESS_URL", 
    "BILLING_CANCEL_URL"
  ]
}
```

## 🚨 VALIDATION DÉMARRAGE

Le backend effectue ces vérifications au démarrage :

### **Validation Automatique**
- **MONGO_URL** : Format valid, connexion possible
- **JWT_SECRET** : Minimum 32 caractères
- **STRIPE_PRICE_PREMIUM** : Commence par 'price_'
- **APP_BASE_URL** : HTTPS obligatoire en production

### **Erreurs si Config Manquante**
```python
# Exemple d'erreur au boot
ValueError: STRIPE_PRICE_PREMIUM is required but not set
RuntimeError: Failed to load configuration: MONGO_URL is required for production
```

## 📊 ENDPOINT DE STATUT

### **GET /api/billing/config**
Retourne la configuration (masquée) :
```json
{
  "success": true,
  "stripe_enabled": true,
  "stripe_price_id": "price_1RrxgjGK8qzu5V5WvOSb4uPd",
  "plan": {
    "name": "Premium",
    "trial_days": 3
  }
}
```

### **GET /api/health**
Inclut validation config :
```json
{
  "status": "ok",
  "stripe_enabled": true,
  "database": "ecomsimply_production",
  "config_valid": true
}
```

## 🔍 DIAGNOSTIC CONFIG

### **Tests Configuration**
```bash
# Vérifier Stripe config
curl https://api.emergent.host/api/billing/config

# Vérifier health général
curl https://api.emergent.host/api/health

# Test création checkout (avec auth)
curl -X POST https://api.emergent.host/api/billing/checkout \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### **Logs Utiles**
```
✅ Configuration loaded: ECOMSIMPLY API v1.6.0
📊 Database: ecomsimply_production  
🔐 Stripe enabled: true
🌐 CORS origins: 3
```

## ⚠️ SÉCURITÉ

### **Ne JAMAIS faire**
- Committer des secrets dans le code
- Hardcoder des URLs/clés en développement
- Utiliser des fallbacks non-sécurisés en production

### **Bonnes Pratiques**
- Variables ENV pour TOUT (URLs, clés, configs)
- Validation stricte au démarrage
- Logs sans secrets (masquage automatique)
- Principe fail-fast si config manquante

## 🚀 DÉPLOIEMENT

### **Checklist Pre-Deploy**
- [ ] Toutes variables ENV configurées dans emergent.sh
- [ ] `STRIPE_PRICE_PREMIUM` ajouté et visible
- [ ] Pas de secrets hardcodés dans le code (`git grep "sk_live"` = vide)
- [ ] `.env.example` à jour sans valeurs réelles

### **Validation Post-Deploy**
- [ ] `/api/health` retourne `"stripe_enabled": true`
- [ ] `/api/billing/config` retourne Price ID correct
- [ ] `/api/billing/checkout` fonctionne avec auth
- [ ] Logs montrent configuration complète au démarrage