# 🔑 GUIDE COMPLET D'OBTENTION DES CLÉS API DE PRODUCTION

## ✅ SECRETS GÉNÉRÉS (Déjà fait)
```bash
JWT_SECRET="Agm4i6GT7Y9zBTu6mjxuRHWdPCp_E_uhRGeObTNf5lI"
ENCRYPTION_KEY="7uWSQqDAewH34UjRHVSgeJawQnDa-ukRe0WERClY694="
MONGO_ROOT_PASSWORD="r@p12B73yh6nQ&m3"
REDIS_PASSWORD="2guckvxHggNdA8Wx"
GRAFANA_PASSWORD="RBQWJogvKIig"
```

## 🚀 ÉTAPES À SUIVRE MAINTENANT

### **1. OpenAI API - ÉTAPES DÉTAILLÉES** 🤖

#### **A. Créer le compte et obtenir la clé**
1. **Aller sur** : https://platform.openai.com/
2. **Se connecter** ou créer un compte OpenAI
3. **Naviguer vers** : Settings > API Keys (https://platform.openai.com/api-keys)
4. **Cliquer** : "Create new secret key"
5. **Nommer** : "ECOMSIMPLY-Production"
6. **Copier la clé** (commence par `sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...` ou `sk-...`)

#### **B. Configurer la facturation (OBLIGATOIRE)**
1. **Aller sur** : https://platform.openai.com/account/billing
2. **Ajouter une méthode de paiement** (carte bancaire)
3. **Définir un budget** : 100-200€/mois pour commencer
4. **Activer les alertes** à 50€, 80€, 100€

#### **C. Tester la clé**
```bash
curl -H "Authorization: Bearer YOUR_OPENAI_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 5}' \
     https://api.openai.com/v1/chat/completions
```

---

### **2. Stripe API - ÉTAPES DÉTAILLÉES** 💳

#### **A. Créer et vérifier le compte Stripe**
1. **Aller sur** : https://dashboard.stripe.com/
2. **Créer un compte Stripe** (business account)
3. **Compléter la vérification** (identité, banque, documents)
   - **IMPORTANT** : Sans vérification = pas de mode LIVE !

#### **B. Obtenir les clés API**
1. **Activer le mode LIVE** (toggle en haut à droite du dashboard)
2. **Aller sur** : Developers > API Keys (https://dashboard.stripe.com/apikeys)
3. **Copier** : "Secret key" (commence par `sk_live_...`)
4. **NE PAS** utiliser les clés de test (`sk_test_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...`)

#### **C. Créer les produits de subscription**
1. **Aller sur** : Products > Add product
2. **Créer "Plan Pro"** :
   - Name: "ECOMSIMPLY Pro"
   - Price: 29€/mois récurrent
   - Copier le `price_id` (commence par `price_...`)
3. **Créer "Plan Premium"** :
   - Name: "ECOMSIMPLY Premium"  
   - Price: 99€/mois récurrent
   - Copier le `price_id`

#### **D. Configurer les webhooks**
1. **Aller sur** : Developers > Webhooks
2. **Add endpoint** : `https://ecomsimply.com/api/stripe/webhook`
3. **Sélectionner les événements** :
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. **Copier le signing secret** (commence par `whsec_...`)

---

### **3. Fal.ai API - ÉTAPES DÉTAILLÉES** 🎨

#### **A. Créer le compte**
1. **Aller sur** : https://fal.ai/
2. **Sign up** avec email/GitHub
3. **Vérifier l'email**

#### **B. Obtenir la clé API**
1. **Aller sur** : Dashboard > API Keys (https://fal.ai/dashboard/keys)
2. **Create API Key**
3. **Nommer** : "ECOMSIMPLY-Production"
4. **Copier la clé** (format : `key-...`)

#### **C. Ajouter des crédits**
1. **Aller sur** : https://fal.ai/dashboard/billing
2. **Add credits** : 50-100$ pour commencer
3. **Configurer auto-reload** (optionnel)

#### **D. Tester la clé**
```bash
curl -X POST "https://fal.run/fal-ai/flux-pro" \
     -H "Authorization: Key YOUR_FAL_KEY" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "test image", "image_size": "square"}'
```

---

## 📝 CONFIGURATION FINALE

### **Créer votre fichier .env de production**
```bash
# Copier le template
cp /app/.env.production.keys /app/.env

# Éditer avec vos vraies clés
nano /app/.env
```

### **Fichier .env final à compléter**
```bash
# ========== REMPLACEZ CES VALEURS ==========
OPENAI_API_KEY="sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
STRIPE_API_KEY="sk_live_VOTRE_CLE_ICI"  
FAL_KEY="key-VOTRE_CLE_ICI"

# Produits Stripe (à créer)
STRIPE_PRICE_ID_PRO="price_VOTRE_ID_PRO"
STRIPE_PRICE_ID_PREMIUM="price_VOTRE_ID_PREMIUM"
STRIPE_WEBHOOK_SECRET="whsec_VOTRE_SECRET"

# ========== SECRETS DÉJÀ GÉNÉRÉS ==========
JWT_SECRET="Agm4i6GT7Y9zBTu6mjxuRHWdPCp_E_uhRGeObTNf5lI"
ENCRYPTION_KEY="7uWSQqDAewH34UjRHVSgeJawQnDa-ukRe0WERClY694="
MONGO_ROOT_PASSWORD="r@p12B73yh6nQ&m3"
REDIS_PASSWORD="2guckvxHggNdA8Wx"
GRAFANA_PASSWORD="RBQWJogvKIig"

# ========== DOMAINE (À CONFIGURER) ==========
REACT_APP_BACKEND_URL="https://votre-domaine.com"
```

---

## 💰 BUDGET PRÉVISIONNEL

| Service | Coût mensuel estimé | Usage |
|---------|-------------------|-------|
| **OpenAI** | 50-200€ | 1000-5000 générations IA |
| **Stripe** | 1.4% + 0.25€/transaction | Ex: 100 abonnements = ~50€ |
| **Fal.ai** | 20-50$ | 500-2000 images générées |
| **Serveur** | 20-100€ | VPS/Cloud selon specs |
| **Domaine** | 10-50€/an | Selon extension |
| **SSL** | Gratuit | Let's Encrypt |

**Total estimé** : **100-400€/mois** selon l'activité

---

## ✅ PROCHAINES ÉTAPES

**Une fois les clés obtenues** :
1. ✅ Secrets générés automatiquement 
2. ⏳ **VOUS** : Obtenir les clés API (OpenAI, Stripe, Fal.ai)
3. ⏳ **NOUS** : Configurer le domaine et SSL
4. ⏳ **NOUS** : Déployer en production
5. ⏳ **NOUS** : Tests finaux et lancement

**Quelle clé voulez-vous obtenir en premier ?** 🚀

---

**📞 BESOIN D'AIDE ?**
- OpenAI Support : help.openai.com
- Stripe Support : support.stripe.com  
- Fal.ai Support : support@fal.ai