# 🚀 GUIDE REDÉPLOIEMENT EMERGENT.SH - OFFRE UNIQUE PREMIUM

## ❌ PROBLÈME IDENTIFIÉ

Le redéploiement emergent.sh ne fonctionne pas car :
1. **Variables Stripe manquantes** dans emergent.config.json 
2. **Frontend Vercel** déploie depuis une version obsolète
3. **Cache CDN** empêche la mise à jour de l'interface

## ✅ SOLUTION COMPLÈTE

### 🔧 **1. BACKEND EMERGENT.SH - Variables Manquantes**

**PROBLÈME** : `STRIPE_PRICE_PREMIUM` et variables billing absentes de la config

**SOLUTION** : Ajouter dans emergent.sh les variables :
```bash
STRIPE_PRICE_PREMIUM=price_1RrxgjGK8qzu5V5WvOSb4uPd
BILLING_SUCCESS_URL=https://app.ecomsimply.com/billing/success?session_id={CHECKOUT_SESSION_ID}
BILLING_CANCEL_URL=https://app.ecomsimply.com/billing/cancel
```

### 🎯 **2. FRONTEND VERCEL - Version Obsolète**

**PROBLÈME** : Vercel déploie depuis une version qui contient encore :
- 3 plans (Gratuit/Pro/Premium)
- "7 jours d'essai gratuit"
- Appels à endpoints inexistants (`/api/plans-pricing-alt`, `/api/public/plans-pricing-nocache`)

**SOLUTION** : Vérifier la configuration Vercel :
1. **Repository** : Doit pointer vers `msylla54/ECOMSIMPLY-Prod-V1.10`
2. **Branche** : Doit déployer depuis `master` (commit `b820988`)
3. **Build** : Doit utiliser les sources de `/frontend`

### 🔄 **3. ÉTAPES DE REDÉPLOIEMENT**

#### **A. EMERGENT.SH (Backend)**
1. Ajouter variables manquantes :
   - `STRIPE_PRICE_PREMIUM=price_1RrxgjGK8qzu5V5WvOSb4uPd`
   - `BILLING_SUCCESS_URL=https://app.ecomsimply.com/billing/success?session_id={CHECKOUT_SESSION_ID}`
   - `BILLING_CANCEL_URL=https://app.ecomsimply.com/billing/cancel`
2. **Redéployer** avec force rebuild (clear cache)
3. **Vérifier** `/api/health` et `/api/billing/config` répondent

#### **B. VERCEL (Frontend)**
1. **Vérifier** la configuration :
   - Repository : `ECOMSIMPLY-Prod-V1.10`
   - Branch : `master`
   - Root Directory : `frontend`
2. **Force redeploy** avec clear cache
3. **Vérifier** que l'interface montre 1 seul plan Premium

### 📊 **4. VALIDATION POST-DÉPLOIEMENT**

#### **Backend Tests**
```bash
# Health check
curl https://ecom-api-fixes.emergent.host/api/health

# Plans pricing (doit retourner 1 plan Premium)
curl https://ecom-api-fixes.emergent.host/api/public/plans-pricing

# Billing config (doit avoir STRIPE_PRICE_PREMIUM)
curl https://ecom-api-fixes.emergent.host/api/billing/config
```

#### **Frontend Tests**
```bash
# Navigation privée sur : https://ecomsimply.com
# Doit afficher :
# ✅ 1 seule carte Premium
# ✅ "Essai Gratuit 3 jours"
# ✅ CTA direct "Commencer essai 3 jours"
```

## 🎯 **VALIDATION FINALE**

L'interface doit montrer :
- ✅ **1 seul plan** Premium (pas 3)
- ✅ **"3 jours d'essai gratuit"** (pas 7)
- ✅ **CTA direct** vers Stripe Checkout (pas de popup)
- ✅ **Backend** répond avec 1 plan Premium + trial_days=3

## 🚨 **CAUSES PRINCIPALES DU PROBLÈME**

1. **Variables Stripe** manquantes dans emergent.sh config
2. **Frontend Vercel** déploie depuis mauvaise source/branche
3. **Cache CDN** empêche mise à jour interface
4. **Repository sync** entre local et Vercel non aligné

## 📋 **CHECKLIST FINAL**

- [ ] Variables Stripe ajoutées dans emergent.sh
- [ ] Backend redéployé avec force rebuild  
- [ ] Frontend Vercel pointe vers bon repository/branche
- [ ] Frontend redéployé avec clear cache
- [ ] Interface montre 1 plan Premium + 3 jours essai
- [ ] CTA direct fonctionne (pas de popup)
- [ ] API retourne bonnes données Premium

---

**🎯 APRÈS CES ÉTAPES** : L'offre unique Premium avec essai 3 jours sera visible sur l'interface déployée.