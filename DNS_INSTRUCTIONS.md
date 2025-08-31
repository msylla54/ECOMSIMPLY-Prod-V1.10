# 🌐 INSTRUCTIONS DNS - api.ecomsimply.com

**Date** : $(date)  
**Objectif** : Configurer le domaine api.ecomsimply.com pour pointer vers le backend conteneurisé

---

## 📋 **ENREGISTREMENTS DNS À CRÉER**

### **Étape 1 : Obtenir l'URL du service backend**

Après déploiement sur Railway/Fly.io, vous obtiendrez une URL du type :
```
Railway : https://ecomsimply-backend-production-xxxx.up.railway.app
Fly.io  : https://ecomsimply-backend.fly.dev
```

### **Étape 2 : Configuration DNS**

**Domaine** : `ecomsimply.com`  
**Sous-domaine à créer** : `api.ecomsimply.com`

#### **Option A : CNAME (Recommandé)**
```
Type : CNAME
Nom : api
Valeur : [URL_DU_SERVICE_SANS_HTTPS]
TTL : 300 (5 minutes)

Exemple Railway:
  Nom: api
  Valeur: ecomsimply-backend-production-xxxx.up.railway.app

Exemple Fly.io:
  Nom: api  
  Valeur: ecomsimply-backend.fly.dev
```

#### **Option B : A Record (Si CNAME indisponible)**
```
Type : A
Nom : api
Valeur : [IP_DU_SERVICE]
TTL : 300

⚠️ Nécessite de récupérer l'IP du service (variable)
```

### **Étape 3 : Validation SSL**

Les plateformes Railway/Fly.io gèrent automatiquement le SSL.  
Après propagation DNS (5-30 minutes), vérifier :

```bash
curl -I https://api.ecomsimply.com/api/health
# Doit retourner 200 OK
```

---

## 🔧 **COMMANDES DE VÉRIFICATION**

### **Test de propagation DNS**
```bash
# Vérifier la résolution DNS
nslookup api.ecomsimply.com
dig api.ecomsimply.com

# Test de connectivité
curl -v https://api.ecomsimply.com/api/health
```

### **Test des endpoints critiques**
```bash
# Health check
curl https://api.ecomsimply.com/api/health

# Marketplaces Amazon  
curl https://api.ecomsimply.com/api/amazon/marketplaces

# Stats publiques
curl https://api.ecomsimply.com/api/stats/public
```

---

## 📝 **CHECKLIST POST-DNS**

- [ ] DNS propagé (nslookup fonctionne)
- [ ] SSL actif (https:// accessible)
- [ ] `/api/health` retourne 200 OK
- [ ] Endpoints publics accessibles
- [ ] Pas d'erreurs CORS
- [ ] Logs backend propres

---

## ⚠️ **NOTES IMPORTANTES**

1. **Propagation** : Peut prendre 5-30 minutes
2. **SSL** : Automatique sur Railway/Fly.io après DNS OK
3. **Sous-domaines** : Créer uniquement `api`, pas `www.api`
4. **TTL** : 300s pour changements rapides, puis augmenter à 3600s
5. **Backup** : Garder trace de l'ancien DNS avant modification

---

**📧 CONTACT** : Une fois le service déployé, communiquer l'URL finale pour mise à jour DNS