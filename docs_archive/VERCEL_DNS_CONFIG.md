# 🌐 CONFIGURATION DNS VERCEL - api.ecomsimply.com

**Date** : $(date)  
**Objectif** : Configurer le sous-domaine api.ecomsimply.com dans Vercel pour pointer vers Railway

---

## 🎯 **CONTEXTE**

- **Nameservers** : Gérés par Vercel (zone DNS centralisée)
- **Domaine principal** : ecomsimply.com (déjà sur Vercel)
- **Sous-domaine à créer** : api.ecomsimply.com
- **Destination** : Railway backend URL

---

## 📋 **ÉTAPES CONFIGURATION VERCEL DNS**

### **Étape 1 : Accéder au Dashboard Vercel**

1. Ouvrir [vercel.com/dashboard](https://vercel.com/dashboard)
2. Sélectionner le projet **ECOMSIMPLY**
3. Aller dans **Settings** → **Domains**

### **Étape 2 : Ajouter le sous-domaine**

#### **Option A : Via Vercel Dashboard (Recommandé)**

1. Dans **Settings** → **Domains**
2. Cliquer **Add Domain**
3. Saisir : `api.ecomsimply.com`
4. Sélectionner **Add as subdomain**
5. Vercel configure automatiquement les enregistrements DNS

#### **Option B : Configuration DNS manuelle**

Si l'option A ne fonctionne pas, aller dans **DNS Records** :

```
Type: CNAME
Name: api
Value: [RAILWAY_BACKEND_URL]
TTL: Auto (300s)

Exemple:
Name: api
Value: ecomsimply-backend-production-xxxx.up.railway.app
```

### **Étape 3 : Validation Propagation**

```bash
# Test résolution DNS
nslookup api.ecomsimply.com

# Test avec dig
dig api.ecomsimply.com

# Test HTTPS (après propagation)
curl -I https://api.ecomsimply.com/api/health
```

---

## 🔧 **CONFIGURATION DÉTAILLÉE**

### **Cas 1 : Railway fournit une URL stable**

```
CNAME Record:
- Name: api
- Value: ecomsimply-backend-production-xxxx.up.railway.app
- TTL: 300
```

### **Cas 2 : Railway fournit une IP dédiée**

```
A Record:
- Name: api  
- Value: [IP_RAILWAY]
- TTL: 300
```

### **Cas 3 : Configuration avec sous-chemin**

Si Railway utilise des sous-chemins :

```
CNAME Record:
- Name: api
- Value: [RAILWAY_DOMAIN]
- Redirect: /api/* → /*
```

---

## ⚙️ **INTÉGRATION AVEC VERCEL REWRITES**

Une fois le DNS configuré, mettre à jour `vercel.json` :

```json
{
  "version": 2,
  "builds": [...],
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://api.ecomsimply.com/api/$1"
    }
  ],
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "*" },
        { "key": "Access-Control-Allow-Methods", "value": "GET,POST,PUT,DELETE,OPTIONS" },
        { "key": "Access-Control-Allow-Headers", "value": "Content-Type,Authorization" }
      ]
    }
  ]
}
```

---

## 🧪 **TESTS DE VALIDATION**

### **Test 1 : Résolution DNS**

```bash
# DNS propagé ?
nslookup api.ecomsimply.com
# Doit retourner l'IP ou CNAME vers Railway

# Depuis différents serveurs DNS
nslookup api.ecomsimply.com 8.8.8.8
nslookup api.ecomsimply.com 1.1.1.1
```

### **Test 2 : SSL/HTTPS**

```bash
# SSL certificate valide ?
curl -I https://api.ecomsimply.com/api/health
# Doit retourner 200 OK avec certificat valide

# Vérification certificat
openssl s_client -connect api.ecomsimply.com:443 -servername api.ecomsimply.com
```

### **Test 3 : Endpoints Backend**

```bash
# Health check
curl https://api.ecomsimply.com/api/health
# {"status": "healthy", ...}

# Stats publiques
curl https://api.ecomsimply.com/api/stats/public
# {"satisfied_clients": 1, ...}

# Marketplaces Amazon
curl https://api.ecomsimply.com/api/amazon/marketplaces
# [{"name": "France", ...}, ...]
```

### **Test 4 : Proxy Vercel**

```bash
# Via le frontend (proxy)
curl https://ecomsimply.com/api/health
# Doit rediriger vers api.ecomsimply.com et retourner 200 OK

# Headers CORS
curl -H "Origin: https://ecomsimply.com" https://ecomsimply.com/api/stats/public
# Pas d'erreur CORS
```

---

## 🕒 **TEMPS DE PROPAGATION**

- **DNS Vercel** : 1-5 minutes (généralement rapide)
- **SSL Certificate** : 5-15 minutes (automatique via Vercel/Railway)
- **Global Propagation** : 15-30 minutes maximum

---

## 🚨 **TROUBLESHOOTING**

### **Problème : DNS non résolu**

```bash
# Vérifier configuration Vercel
# Dashboard → Settings → Domains → Vérifier api.ecomsimply.com

# Flush DNS local
sudo dscacheutil -flushcache  # macOS
ipconfig /flushdns             # Windows
sudo systemctl restart systemd-resolved  # Linux
```

### **Problème : SSL/HTTPS**

```bash
# Vérifier Railway SSL
curl -I https://[RAILWAY_URL]/api/health

# Forcer SSL Vercel
# Dashboard → Settings → Domains → Force HTTPS
```

### **Problème : 502/503 Errors**

```bash
# Vérifier backend Railway actif
railway status
railway logs

# Tester direct Railway
curl -I https://[RAILWAY_URL]/api/health
```

---

## 📋 **CHECKLIST DNS VERCEL**

- [ ] Domaine ecomsimply.com configuré sur Vercel
- [ ] Sous-domaine api.ecomsimply.com ajouté
- [ ] Enregistrement CNAME → Railway URL
- [ ] DNS propagé (nslookup OK)
- [ ] HTTPS/SSL actif
- [ ] Health check : 200 OK
- [ ] Endpoints publics accessibles
- [ ] Proxy Vercel fonctionne (/api/*)
- [ ] Pas d'erreurs CORS

---

## 🔗 **URLS FINALES**

Après configuration complète :

- **Frontend** : https://ecomsimply.com
- **Backend Direct** : https://api.ecomsimply.com/api/health
- **Backend via Proxy** : https://ecomsimply.com/api/health

---

**✅ DNS CONFIGURÉ - PRÊT POUR TESTS E2E**