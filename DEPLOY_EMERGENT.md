# 🚀 ECOMSIMPLY - Guide de Déploiement Emergent.sh

Guide complet pour déployer ECOMSIMPLY sur la plateforme emergent.sh avec architecture hybride :
- **Backend** : FastAPI sur emergent.sh (Docker)
- **Frontend** : React sur Vercel
- **Base de données** : MongoDB Atlas

## 📋 Prérequis

### Services Externes Requis
- [MongoDB Atlas](https://www.mongodb.com/atlas) - Base de données cloud
- [Vercel](https://vercel.com) - Hébergement frontend
- [Stripe](https://stripe.com) - Paiements (optionnel)
- [Amazon SP-API](https://developer.amazonservices.com) - Intégration Amazon (optionnel)

### Outils de Développement
- Docker (pour tests locaux)
- Node.js 18+ et Yarn
- Python 3.11+

## 🛠️ Configuration des Variables d'Environnement

### Backend (Emergent.sh Dashboard)

Configurer ces variables dans le tableau de bord emergent :

#### 🔒 Variables Obligatoires (Emergent.sh Dashboard)
```bash
# Application Core
APP_BASE_URL=https://your-frontend.vercel.app
NODE_ENV=production
ENABLE_SCHEDULER=false
LOG_LEVEL=info
WORKERS=2

# Sécurité (UTILISEZ VOS VALEURS GÉNÉRÉES)
JWT_SECRET=f2YawofXeyl1qmIu5yYmX14FfQ5qe7cL4MFJmHmmFbgmQy40HN3PwczyYkTYDeN4
ENCRYPTION_KEY=Z3xuHvLANzqg75mmnj6sUnnQYDkBdrNK
ADMIN_BOOTSTRAP_TOKEN=ECS-Bootstrap-2025-BSEU_5vV79JR-ODJhvGZOw

# Base de données
MONGO_URL=mongodb+srv://USERNAME:PASSWORD@ecomsimply.xagju9s.mongodb.net/ecomsimply_production?retryWrites=true&w=majority&appName=EcomSimply
DB_NAME=ecomsimply_production

# Admin par défaut
ADMIN_EMAIL=msylla54@gmail.com
ADMIN_PASSWORD_HASH=$2b$12$9DyZFnXGz.TYhdp8QTN2fu0x4WEEn8nmCYIaiJUTayiYaEIF8bviW
```

#### 🌐 Configuration CORS
```bash
# Origins autorisées (en plus de APP_BASE_URL)
ADDITIONAL_ALLOWED_ORIGINS=https://preview-branch.vercel.app,https://staging.domain.com
```

#### 🔌 Intégrations Optionnelles
```bash
# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Amazon SP-API
AMAZON_LWA_CLIENT_ID=amzn1.application-oa2-client.XXXXXXXXXXXXXXXX..
AMAZON_LWA_CLIENT_SECRET=...
AWS_ROLE_ARN=arn:aws:iam::123456789012:role/YourRole
AWS_REGION=us-east-1

# IA
OPENAI_API_KEY=sk-...
FAL_KEY=...
```

### Frontend (Vercel Dashboard)

Configurer dans Vercel → Project → Settings → Environment Variables :

```bash
# Production
REACT_APP_BACKEND_URL=https://your-backend.up.railway.app
REACT_APP_STRIPE_PUBLISHABLE_KEY=pk_live_...

# Preview (optionnel)
REACT_APP_BACKEND_URL=https://staging-backend.up.railway.app
```

## 🚀 Étapes de Déploiement

### 1. Préparer MongoDB Atlas

1. Créer un cluster MongoDB Atlas
2. Configurer les autorisations réseau (0.0.0.0/0 pour emergent.sh)
3. Créer un utilisateur de base de données
4. Récupérer la connection string

### 2. Déployer le Backend sur Emergent.sh

1. **Push du code vers le repository**
   ```bash
   git add .
   git commit -m "Production ready deployment"
   git push origin main
   ```

2. **Configuration emergent.sh**
   - Connecter le repository GitHub
   - Le `Dockerfile` sera automatiquement détecté
   - Configurer toutes les variables d'environnement listées ci-dessus

3. **Lancer le déploiement**
   - Cliquer sur "Start Deployment"
   - Surveiller les logs de build
   - Vérifier que le healthcheck `/api/health` répond

### 3. Déployer le Frontend sur Vercel

1. **Connecter le repository à Vercel**
   
2. **Configuration de build**
   ```json
   {
     "buildCommand": "cd frontend && yarn build",
     "outputDirectory": "frontend/build",
     "installCommand": "cd frontend && yarn install"
   }
   ```

3. **Variables d'environnement Vercel**
   - Configurer `REACT_APP_BACKEND_URL` avec l'URL emergent
   - Ajouter les autres variables REACT_APP_* si nécessaire

4. **Déployer**
   - Vercel déploiera automatiquement sur push

### 4. Tests de Validation

Exécuter le script de smoke tests :

```bash
# Une fois les deux services déployés
chmod +x scripts/smoke_emergent.sh
BASE_URL=https://your-backend-emergent-domain ./scripts/smoke_emergent.sh
```

## 🔧 Tests Locaux avec Docker

Pour tester la configuration Docker avant déploiement :

```bash
# Build local
docker build -t ecomsimply-backend .

# Test avec variables d'env
docker run -p 8001:8001 \
  -e MONGO_URL=your-mongo-url \
  -e JWT_SECRET=test-secret \
  ecomsimply-backend

# Vérifier healthcheck
curl http://localhost:8001/api/health
```

## 📊 Monitoring et Logs

### Healthcheck
- **URL** : `https://your-backend-domain/api/health`
- **Réponse attendue** : `{"status":"ok","service":"ecomsimply-api",...}`
- **Timeout** : <200ms

### Logs Importantes
```
✅ FastAPI startup - MongoDB will connect lazily
✅ CORS configured for origins: [...]
✅ Database indexes created successfully
ℹ️ Scheduler disabled (prod default)
```

### CORS Debug
```
✅ CORS configured for origins: ['https://your-frontend.vercel.app']
⚠️ APP_BASE_URL not configured - using development CORS origins
```

## 🚨 Résolution de Problèmes

### Backend ne démarre pas
1. Vérifier les logs emergent.sh
2. Valider MONGO_URL dans les variables d'env
3. Tester la connection MongoDB depuis un outil externe

### Erreurs CORS
1. Vérifier que `APP_BASE_URL` correspond exactement au domaine Vercel
2. Ajouter les domaines preview dans `ADDITIONAL_ALLOWED_ORIGINS`
3. Redémarrer le backend après changement de CORS

### Frontend ne peut pas contacter le backend
1. Vérifier `REACT_APP_BACKEND_URL` dans Vercel
2. Tester l'URL backend manuellement : `curl https://backend-url/api/health`
3. Vérifier les logs réseau dans les DevTools du navigateur

### Scheduler activé involontairement
1. S'assurer que `ENABLE_SCHEDULER=false` (ou absent)
2. Logs attendus : `"Scheduler disabled (prod default)"`

## 🔐 Sécurité Production

### Variables Sensibles
- ❌ Jamais commiter de secrets dans le code
- ✅ Utiliser uniquement les dashboards emergent.sh et Vercel
- ✅ Rotation régulière des clés JWT et ENCRYPTION_KEY

### CORS Strict
- ✅ Autoriser uniquement les domaines nécessaires
- ❌ Éviter `allow_origins=["*"]` en production

### Healthcheck Sécurisé
- ✅ L'endpoint `/api/health` ne révèle pas d'informations sensibles
- ✅ Timeout rapide pour éviter les dénis de service

## 📱 Support et Maintenance

### Backup GitHub
Le repository reste synchronisé sur GitHub comme backup :
```bash
git remote add backup https://github.com/username/ecomsimply-backup.git
git push backup main
```

### Monitoring
- Healthcheck automatique via emergent.sh
- Logs centralisés dans les dashboards
- Métriques de performance via les outils intégrés

---

**Note** : Ce guide assume une architecture où emergent.sh gère le backend et Vercel le frontend. Pour une architecture entièrement sur emergent.sh, adapter les sections Vercel en conséquence.