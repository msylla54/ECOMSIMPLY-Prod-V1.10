# 🚂 GUIDE SETUP RAILWAY - ECOMSIMPLY BACKEND

**Date de création** : $(date)  
**Objectif** : Déployer le backend ECOMSIMPLY sur Railway avec configuration automatisée

---

## 📋 **PRÉREQUIS CONFIGURÉS**

✅ **Fichiers Railway créés** :
- `railway.json` - Configuration Nixpacks avec Python 3.11
- `Procfile` - Commande de démarrage standardisée
- `scripts/railway_autodeploy.sh` - Script d'orchestration
- `scripts/railway_deploy_api.py` - Déploiement via API

✅ **Configuration Railway** :
```json
{
  "build": {
    "builder": "nixpacks",
    "buildCommand": "pip install -r backend/requirements.txt"
  },
  "deploy": {
    "startCommand": "python -m uvicorn backend.server:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/api/health"
  }
}
```

✅ **Structure Backend validée** :
- `backend/server.py` avec objet FastAPI `app` ✅
- `backend/requirements.txt` avec uvicorn, fastapi, etc. ✅
- Variables d'environnement préparées ✅

---

## 🚀 **ÉTAPES DÉPLOIEMENT RAILWAY**

### **1. Connexion Railway avec Token**
```bash
# Utiliser le token fourni
export RAILWAY_TOKEN="59a33ff7-ff58-43ca-ac8c-f88abdfa280d"

# Si Railway CLI disponible
railway login --token $RAILWAY_TOKEN
railway link 947cd7da-e31f-45a3-b967-49317532d948
```

### **2. Configuration Projet**
```bash
# Sélectionner environnement production
railway environment use production

# Vérifier la configuration
railway status
railway variables
```

### **3. Variables d'Environnement Critiques**
```bash
# Variables à configurer dans Railway Dashboard
railway variables set MONGO_URL="mongodb+srv://[YOUR_MONGODB_CONNECTION]"
railway variables set DB_NAME="ecomsimply_production"
railway variables set JWT_SECRET="supersecretjwtkey32charsminimum2025ecomsimply"
railway variables set ADMIN_EMAIL="msylla54@gmail.com"
railway variables set ADMIN_PASSWORD_HASH="$2b$12$AX.4AQP8u50RP3.pcupJ6OJSSOHQqTG71NJvZRW/J6kyRFnxKX0.W"
railway variables set ADMIN_BOOTSTRAP_TOKEN="ECS-Bootstrap-2025-Secure-Token"
railway variables set APP_BASE_URL="https://ecomsimply.com"
railway variables set ENCRYPTION_KEY="w7uWSQqDAewH34UjRHVSgeJawQnDa-ukRe0WERClY694="
railway variables set ENVIRONMENT="production"
railway variables set DEBUG="false"
railway variables set MOCK_MODE="false"
```

### **4. Déploiement**
```bash
# Déployer depuis la racine du projet
railway up

# Ou forcer redéploiement
railway redeploy
```

### **5. Vérification Service**
```bash
# Obtenir l'URL du service
railway domain

# Test health check
curl https://[RAILWAY_DOMAIN]/api/health
```

---

## 🔧 **CONFIGURATION ALTERNATIVE (Manual)**

### **Si token ne fonctionne pas** :

1. **Créer nouveau projet Railway** :
   - Aller sur [railway.app](https://railway.app)
   - Créer nouveau projet depuis GitHub
   - Connecter le repo `msylla54/ECOMSIMPLY-Prod-V1.6`
   - Sélectionner branch `main`

2. **Configuration automatique** :
   - Railway détectera `railway.json` et `Procfile`
   - Build utilisera Nixpacks avec Python 3.11
   - Start command : `python -m uvicorn backend.server:app --host 0.0.0.0 --port $PORT`

3. **Variables d'environnement** :
   - Aller dans Settings → Variables
   - Ajouter toutes les variables listées ci-dessus
   - **Important** : Configurer `MONGO_URL` avec la vraie connection string

4. **Redéployer** :
   - Push sur `main` déclenchera auto-deploy
   - Ou redéployer manuellement dans Railway Dashboard

---

## 📊 **HEALTHCHECK & VALIDATION**

### **Endpoints à tester après déploiement** :
```bash
# Health check
curl https://[RAILWAY_URL]/api/health
# Attendu: {"status": "healthy", "database": "connected"}

# Bootstrap admin
curl -X POST https://[RAILWAY_URL]/api/admin/bootstrap \
  -H "x-bootstrap-token: ECS-Bootstrap-2025-Secure-Token"
# Attendu: {"ok": true, "bootstrap": "done" ou "exists"}

# Login admin  
curl -X POST https://[RAILWAY_URL]/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "msylla54@gmail.com", "password": "ECS-Temp#2025-08-22!"}'
# Attendu: {"access_token": "...", "user": {...}}

# Endpoints publics
curl https://[RAILWAY_URL]/api/stats/public
curl https://[RAILWAY_URL]/api/amazon/marketplaces
```

### **Logs Railway** :
```bash
# Suivre les logs en temps réel
railway logs

# Logs spécifiques
railway logs --tail 100
```

---

## 🌐 **CONFIGURATION DNS (Après déploiement)**

### **Option 1 : Domaine personnalisé Railway**
```bash
# Ajouter domaine personnalisé
railway domain add api.ecomsimply.com

# Configurer DNS chez Vercel
# Type: CNAME
# Name: api  
# Value: [RAILWAY_CUSTOM_DOMAIN]
```

### **Option 2 : Vercel Proxy (Recommandé)**
```json
// vercel.json - Rewrites vers Railway
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://[RAILWAY_DOMAIN]/api/$1"
    }
  ]
}
```

---

## 🧪 **TESTS E2E POST-DÉPLOIEMENT**

```bash
# Script de test automatisé (à créer)
cd /app/ecomsimply-deploy
python3 scripts/test_railway_deployment.py --url https://[RAILWAY_URL]

# Tests manuels
curl -I https://ecomsimply.com/api/health  # Via proxy Vercel
curl -I https://[RAILWAY_URL]/api/health   # Direct Railway
```

---

## 📋 **CHECKLIST DÉPLOIEMENT**

### **Avant déploiement** :
- [ ] Token Railway validé
- [ ] Projet Railway lié (ID: 947cd7da-e31f-45a3-b967-49317532d948)
- [ ] Environment = production
- [ ] Fichiers `railway.json`, `Procfile` présents
- [ ] `backend/server.py` et `requirements.txt` vérifiés

### **Pendant déploiement** :
- [ ] Variables d'environnement configurées
- [ ] `MONGO_URL` avec vraie connection string
- [ ] Build Nixpacks Python 3.11 réussi
- [ ] Start command uvicorn exécuté
- [ ] Port $PORT correctement bindé

### **Après déploiement** :
- [ ] Health check : 200 OK
- [ ] Bootstrap admin : fonctionnel
- [ ] Login admin : JWT généré
- [ ] Endpoints publics : accessibles
- [ ] Amazon SP-API : 6 marketplaces
- [ ] Database : MongoDB connecté

### **DNS & Proxy** :
- [ ] URL Railway obtenue
- [ ] DNS api.ecomsimply.com configuré OU
- [ ] Vercel rewrites configurés
- [ ] Proxy `/api/*` fonctionnel
- [ ] Frontend → Backend communication OK

---

## 🏆 **RÉSULTAT ATTENDU**

**Backend Railway déployé et opérationnel** :
- URL : `https://[RAILWAY_DOMAIN]` ou `https://api.ecomsimply.com`
- Health : `https://api.ecomsimply.com/api/health` → 200 OK
- Admin : `msylla54@gmail.com` login fonctionnel
- Proxy : `https://ecomsimply.com/api/*` → Railway backend

**Architecture finale** :
```
Frontend (Vercel) → /api/* proxy → Railway Backend → MongoDB Atlas
```

---

*Guide généré automatiquement - Suivre étapes dans l'ordre pour déploiement réussi*