# 🧪 TESTS E2E MANUELS - BACKEND CONTENEURISÉ

**Date** : $(date)  
**Objectif** : Valider le fonctionnement après migration vers backend conteneur

---

## 🎯 **TESTS CRITIQUES À EFFECTUER**

### **PHASE 1 : Tests Backend (API directe)**

#### **Test 1.1 : Health Check**
```bash
curl -I https://api.ecomsimply.com/api/health
# Attendu : 200 OK

curl https://api.ecomsimply.com/api/health
# Attendu : {"status": "healthy", "database": "connected", ...}
```

#### **Test 1.2 : Bootstrap Admin**
```bash
curl -X POST https://api.ecomsimply.com/api/admin/bootstrap \
  -H "x-bootstrap-token: ECS-Bootstrap-2025-Secure-Token"
# Attendu : {"ok": true, "bootstrap": "exists|done", ...}
```

#### **Test 1.3 : Login Admin**
```bash
curl -X POST https://api.ecomsimply.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "msylla54@gmail.com", "password": "ECS-Temp#2025-08-22!"}'
# Attendu : {"access_token": "...", "token_type": "bearer", ...}
```

#### **Test 1.4 : Endpoints Publics**
```bash
# Stats publiques
curl https://api.ecomsimply.com/api/stats/public
# Attendu : {"satisfied_clients": 1, "average_rating": 4.8, ...}

# Marketplaces Amazon
curl https://api.ecomsimply.com/api/amazon/marketplaces  
# Attendu : Liste de 6 marketplaces
```

---

### **PHASE 2 : Tests Frontend via Vercel Proxy**

#### **Test 2.1 : Variables d'environnement**
```javascript
// Console browser sur https://ecomsimply.com
console.log(process.env.REACT_APP_BACKEND_URL)
// Attendu : "/api"
```

#### **Test 2.2 : API via Proxy Vercel**
```javascript
// Console browser sur https://ecomsimply.com
fetch('/api/health')
  .then(r => r.json())
  .then(console.log)
// Attendu : {"status": "healthy", ...}
```

#### **Test 2.3 : Login Frontend**
```javascript
// Console browser sur https://ecomsimply.com
fetch('/api/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    email: 'msylla54@gmail.com', 
    password: 'ECS-Temp#2025-08-22!'
  })
})
.then(r => r.json())
.then(console.log)
// Attendu : Token JWT + infos user
```

---

### **PHASE 3 : Tests UI Complets**

#### **Test 3.1 : Navigation Homepage**
- [ ] Ouvrir https://ecomsimply.com
- [ ] Page se charge sans erreur
- [ ] Logo ECOMSIMPLY visible
- [ ] Boutons navigation fonctionnels
- [ ] Pas d'erreurs console

#### **Test 3.2 : Workflow Authentification**
- [ ] Cliquer sur "Connexion"
- [ ] Modal login s'ouvre
- [ ] Saisir : msylla54@gmail.com / ECS-Temp#2025-08-22!
- [ ] Cliquer "Se connecter"
- [ ] ✅ Connexion réussie → Redirection dashboard
- [ ] ✅ JWT stocké dans localStorage

#### **Test 3.3 : Navigation Dashboard**
- [ ] Dashboard s'affiche après login
- [ ] Menu Amazon visible
- [ ] Cliquer sur section Amazon
- [ ] Page Amazon SP-API accessible
- [ ] Composant AmazonConnectionManager visible

#### **Test 3.4 : Amazon SP-API Frontend**
- [ ] Section "Connexions" visible
- [ ] 6 marketplaces disponibles
- [ ] Bouton "Connecter mon compte Amazon"
- [ ] États UI cohérents (loading, success, error)

---

### **PHASE 4 : Tests MongoDB Atlas**

#### **Test 4.1 : Données persistées**
```bash
# Via MongoDB Compass ou CLI
# Vérifier collections :
- users (admin existe)
- testimonials (données présentes)  
- subscription_plans (plans configurés)
- affiliate_config (config présente)
```

#### **Test 4.2 : Écriture MongoDB**
```javascript
// Test création utilisateur (optionnel)
fetch('/api/auth/register', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    email: 'test@example.com',
    password: 'Test123!'
  })
})
// Vérifier : utilisateur créé dans MongoDB
```

---

## 📊 **GRILLE DE VALIDATION**

### **Backend Direct (API)**
- [ ] Health check : 200 OK
- [ ] Bootstrap admin : Idempotent  
- [ ] Login admin : JWT généré
- [ ] Stats publiques : Données correctes
- [ ] Amazon marketplaces : 6 résultats

### **Frontend Proxy (Vercel)**
- [ ] Variable REACT_APP_BACKEND_URL : `/api`
- [ ] Health via proxy : 200 OK
- [ ] Login via proxy : JWT reçu
- [ ] Pas d'erreurs CORS
- [ ] localStorage JWT persisté

### **UI Workflow**
- [ ] Homepage sans erreur
- [ ] Login modal fonctionnel
- [ ] Dashboard accessible après auth
- [ ] Amazon section visible
- [ ] États UI cohérents

### **MongoDB Atlas**
- [ ] Collections présentes
- [ ] Admin user existe
- [ ] Données de base configurées
- [ ] Écritures fonctionnelles

---

## 🚨 **POINTS D'ATTENTION**

### **Erreurs possibles :**
- **404 sur /api/*** → DNS api.ecomsimply.com pas propagé
- **CORS errors** → Headers manquants dans vercel.json
- **401 Unauthorized** → JWT non transmis correctement
- **500 Internal** → Backend conteneur non démarré

### **Debugging :**
```bash
# Vérifier DNS
nslookup api.ecomsimply.com

# Tester direct backend
curl -I https://api.ecomsimply.com/api/health

# Vérifier logs Vercel
vercel logs --follow

# Logs backend container (Railway/Fly.io)
# Selon la plateforme choisie
```

---

## ✅ **VALIDATION FINALE**

**Critères de succès (tous obligatoires) :**
- [ ] https://ecomsimply.com s'ouvre sans erreur
- [ ] Login admin fonctionne avec JWT persisté
- [ ] /api/* via Vercel → 200 (proxy backend)
- [ ] Amazon SP-API endpoints → 200
- [ ] MongoDB Atlas → lectures/écritures OK
- [ ] Aucune erreur console critique
- [ ] Workflow E2E complet fonctionnel

**Si tous ✅ → Migration backend conteneur RÉUSSIE ✅**