# 🚂 GUIDE DÉPLOIEMENT RAILWAY - ECOMSIMPLY BACKEND

**Date** : $(date)  
**Objectif** : Déployer le backend FastAPI conteneurisé sur Railway avec variables production

---

## 📋 **PRÉREQUIS**

1. **Compte Railway** : [railway.app](https://railway.app)
2. **Railway CLI** installé : `npm install -g @railway/cli`
3. **Docker** pour build local (optionnel)
4. **Variables production** : Récupérées de Vercel

---

## 🚀 **ÉTAPES DE DÉPLOIEMENT**

### **Étape 1 : Initialisation Railway**

```bash
# Se connecter à Railway
railway login

# Dans le dossier backend
cd /app/ecomsimply-deploy/backend

# Créer nouveau projet Railway
railway init

# Ou lier à projet existant si déjà créé
railway link
```

### **Étape 2 : Configuration Variables d'Environnement**

```bash
# Variables critiques Backend (à configurer dans Railway Dashboard)
railway variables set MONGO_URL="mongodb+srv://USERNAME:PASSWORD@cluster.mongodb.net/ecomsimply_production?retryWrites=true&w=majority"
railway variables set DB_NAME="ecomsimply_production"

# Admin & Sécurité
railway variables set ADMIN_EMAIL="msylla54@gmail.com"
railway variables set ADMIN_PASSWORD_HASH="$2b$12$AX.4AQP8u50RP3.pcupJ6OJSSOHQqTG71NJvZRW/J6kyRFnxKX0.W"
railway variables set ADMIN_BOOTSTRAP_TOKEN="ECS-Bootstrap-2025-Secure-Token"
railway variables set JWT_SECRET="supersecretjwtkey32charsminimum2025ecomsimply"
railway variables set ENCRYPTION_KEY="w7uWSQqDAewH34UjRHVSgeJawQnDa-ukRe0WERClY694="

# URLs Application
railway variables set APP_BASE_URL="https://ecomsimply.com"

# Environment flags
railway variables set MOCK_MODE="false"
railway variables set DEBUG="false"
railway variables set NODE_ENV="production"
railway variables set ENVIRONMENT="production"

# Optionnel : SMTP (si configuré)
# railway variables set SMTP_HOST="smtp.sendgrid.net"
# railway variables set SMTP_PORT="587"
# railway variables set SMTP_USER="apikey"
# railway variables set SMTP_PASSWORD="YOUR_SENDGRID_KEY"
# railway variables set SMTP_FROM="admin@ecomsimply.com"

# Optionnel : Intégrations IA (si configurées)
# railway variables set OPENAI_API_KEY="YOUR_OPENAI_KEY"
# railway variables set FAL_KEY="YOUR_FAL_KEY"
# railway variables set EMERGENT_LLM_KEY="YOUR_EMERGENT_KEY"

# Optionnel : Amazon SP-API (si configurées)
# railway variables set AMAZON_LWA_CLIENT_ID="YOUR_AMAZON_CLIENT_ID"
# railway variables set AMAZON_LWA_CLIENT_SECRET="YOUR_AMAZON_SECRET"
# railway variables set AMAZON_REFRESH_TOKEN_ENCRYPTION_KEY="YOUR_ENCRYPTION_KEY"
```

### **Étape 3 : Déploiement**

```bash
# Déployer depuis le dossier backend
cd /app/ecomsimply-deploy/backend
railway up

# Ou déploiement avec build spécifique
railway up --detach
```

### **Étape 4 : Configuration Port & Domaine**

```bash
# Railway assignera automatiquement un port et URL publique
# Format : https://ecomsimply-backend-production-xxxx.up.railway.app

# Vérifier le déploiement
railway status
railway logs

# Obtenir l'URL publique
railway domain
```

---

## 🔧 **CONFIGURATION DOCKERFILE**

Le Dockerfile existant est déjà optimisé pour Railway :

```dockerfile
# backend/Dockerfile (existant - ne pas modifier)
FROM python:3.11-slim
WORKDIR /app
# ... configuration sécurisée existante
EXPOSE 8001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
```

**⚠️ Important** : Railway utilise la variable `$PORT` automatiquement. Si nécessaire, adapter :

```dockerfile
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "$PORT", "--workers", "4"]
```

---

## 🌐 **DOMAINE PERSONNALISÉ (Optionnel)**

```bash
# Ajouter domaine personnalisé sur Railway
railway domain add api.ecomsimply.com

# Ou utiliser l'URL Railway par défaut pour les tests
```

---

## ✅ **VALIDATION DÉPLOIEMENT**

### **Tests de base :**

```bash
# Récupérer l'URL Railway
RAILWAY_URL=$(railway domain --json | jq -r '.[0].domain')
echo "Backend URL: https://$RAILWAY_URL"

# Test health check
curl -I https://$RAILWAY_URL/api/health

# Test endpoints publics
curl https://$RAILWAY_URL/api/stats/public
curl https://$RAILWAY_URL/api/amazon/marketplaces
```

### **Test bootstrap admin :**

```bash
curl -X POST https://$RAILWAY_URL/api/admin/bootstrap \
  -H "x-bootstrap-token: ECS-Bootstrap-2025-Secure-Token"
```

### **Test login admin :**

```bash
curl -X POST https://$RAILWAY_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "msylla54@gmail.com", "password": "ECS-Temp#2025-08-22!"}'
```

---

## 📊 **MONITORING & LOGS**

```bash
# Suivre les logs en temps réel
railway logs --follow

# Status du service
railway status

# Métriques (si disponibles)
railway metrics
```

---

## 🔄 **REDÉPLOIEMENT**

```bash
# Redéploiement après modifications
railway up

# Redéploiement forcé
railway up --force

# Rollback si problème
railway rollback
```

---

## 🚨 **TROUBLESHOOTING**

### **Problème : Port binding**
```bash
# Vérifier que Railway assigne bien le port
railway logs | grep "port"
```

### **Problème : Variables ENV**
```bash
# Lister toutes les variables
railway variables

# Tester une variable spécifique
railway run echo \$MONGO_URL
```

### **Problème : Build Docker**
```bash
# Build local pour debug
docker build -t ecomsimply-backend .
docker run -p 8001:8001 ecomsimply-backend
```

---

## 📋 **CHECKLIST DÉPLOIEMENT**

- [ ] Railway CLI installé et connecté
- [ ] Projet Railway créé/lié
- [ ] Variables ENV critiques configurées
- [ ] Dockerfile vérifié (port, commande)
- [ ] Déploiement réussi (`railway up`)
- [ ] URL publique obtenue
- [ ] Health check : 200 OK
- [ ] Bootstrap admin : 200 OK
- [ ] Login admin : JWT token reçu
- [ ] Logs propres (pas d'erreurs critiques)

---

**✅ BACKEND PRÊT POUR CONFIGURATION DNS VERCEL**