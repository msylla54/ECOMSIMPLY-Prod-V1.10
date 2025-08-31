# 🔧 CONFIGURATION VARIABLES VERCEL - ECOMSIMPLY

**Date** : $(date)  
**Objectif** : Configurer les variables d'environnement Vercel pour pointer vers le backend conteneurisé

---

## 🎯 **VARIABLES CRITIQUES À CONFIGURER**

### **Frontend (Vercel)**
```bash
# Variables d'environnement Vercel à configurer dans Dashboard
REACT_APP_BACKEND_URL=/api

# ⚠️ IMPORTANT : Utiliser /api (pas l'URL complète)
# Le rewrite vercel.json se charge de rediriger vers api.ecomsimply.com
```

### **Production Environment**
```
Environment: Production
REACT_APP_BACKEND_URL = /api
```

### **Preview Environment**  
```
Environment: Preview
REACT_APP_BACKEND_URL = /api
```

---

## 📋 **ÉTAPES DE CONFIGURATION**

### **Étape 1 : Accéder au Dashboard Vercel**
1. Ouvrir [vercel.com](https://vercel.com)
2. Sélectionner le projet ECOMSIMPLY
3. Aller dans **Settings** → **Environment Variables**

### **Étape 2 : Configurer REACT_APP_BACKEND_URL**

**Pour Production :**
```
Key: REACT_APP_BACKEND_URL
Value: /api
Environment: Production
```

**Pour Preview :**
```
Key: REACT_APP_BACKEND_URL  
Value: /api
Environment: Preview
```

**Pour Development (optionnel) :**
```
Key: REACT_APP_BACKEND_URL
Value: http://localhost:8001
Environment: Development
```

### **Étape 3 : Variables optionnelles (si nécessaires)**

Si d'autres variables sont utilisées côté frontend :
```bash
# Variables publiques frontend (préfixe REACT_APP_ obligatoire)
REACT_APP_API_VERSION=v1
REACT_APP_ENVIRONMENT=production
```

---

## 🔄 **WORKFLOW VERCEL APRÈS CONFIGURATION**

### **Flux de requête avec nouveau setup :**
```
1. Frontend Vercel : /api/health
2. Rewrite Vercel : https://api.ecomsimply.com/api/health  
3. Backend Container : Réponse 200 OK
```

### **Test après déploiement :**
```bash
# Depuis le navigateur sur https://ecomsimply.com
fetch('/api/health')
  .then(r => r.json())
  .then(console.log)

# Doit retourner : {"status": "healthy", ...}
```

---

## ⚠️ **MIGRATION DE L'ANCIEN SETUP**

### **Avant (ancien proxy Python) :**
```
REACT_APP_BACKEND_URL = https://ecomsimply.com  
Routes: /api/* → api/index.py → backend
```

### **Après (backend conteneur) :**
```
REACT_APP_BACKEND_URL = /api
Rewrites: /api/* → https://api.ecomsimply.com/api/*
```

### **Changements dans le code frontend :**
✅ **Aucun changement nécessaire** - Le code utilise déjà `process.env.REACT_APP_BACKEND_URL`

---

## 🧪 **TESTS DE VALIDATION**

### **Test 1 : Variables chargées**
```javascript
// Dans la console browser sur ecomsimply.com
console.log(process.env.REACT_APP_BACKEND_URL)
// Doit afficher : "/api"
```

### **Test 2 : API accessible**
```bash
curl -I https://ecomsimply.com/api/health
# Doit retourner 200 OK
```

### **Test 3 : Pas d'erreurs CORS**
```javascript
// Dans la console browser
fetch('/api/stats/public')
  .then(r => r.json())
  .then(console.log)
// Doit fonctionner sans erreur CORS
```

---

## 📝 **CHECKLIST POST-CONFIGURATION**

- [ ] Variable `REACT_APP_BACKEND_URL=/api` configurée Production
- [ ] Variable `REACT_APP_BACKEND_URL=/api` configurée Preview  
- [ ] Redéploiement Vercel déclenché
- [ ] Test : `console.log(process.env.REACT_APP_BACKEND_URL)` → `/api`
- [ ] Test : `curl https://ecomsimply.com/api/health` → 200 OK
- [ ] Test : Pas d'erreurs CORS dans la console
- [ ] Test : Login admin fonctionne
- [ ] Test : Navigation Amazon accessible

---

## 🚨 **SUPPRESSION ANCIEN PROXY**

Après validation complète, supprimer :
- [ ] Dossier `/api/` (ancien proxy Python)
- [ ] Build Python dans vercel.json (déjà fait)
- [ ] Variables inutiles côté backend

---

**✅ CONFIGURATION PRÊTE - Variables pointent vers backend conteneurisé**