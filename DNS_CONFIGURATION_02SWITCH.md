# 🌐 GUIDE CONFIGURATION DNS - www.ecomsimply.com

## 📋 INFORMATIONS IMPORTANTES
- **Domaine** : www.ecomsimply.com
- **Hébergeur DNS** : 02switch
- **IP Serveur ECOMSIMPLY** : 34.121.6.206
- **SSL** : Let's Encrypt (gratuit, automatique)

## 🔧 ÉTAPES À SUIVRE CHEZ 02SWITCH

### **1. Connexion au panel 02switch**
1. Allez sur : https://www.02switch.com/espace-client/
2. Connectez-vous avec vos identifiants
3. Accédez à la gestion de votre domaine ecomsimply.com

### **2. Configuration DNS (CRITIQUE)**
Dans la section **"Gestion DNS"** ou **"Zone DNS"**, configurez :

#### **A. Enregistrement A principal**
```
Type: A
Nom: @  (ou laisser vide)
Valeur: 34.121.6.206
TTL: 3600 (ou Auto)
```

#### **B. Enregistrement CNAME pour www**
```
Type: CNAME
Nom: www
Valeur: ecomsimply.com
TTL: 3600 (ou Auto)
```

#### **C. Configuration complète recommandée**
```
# Domaine principal
@    A    34.121.6.206

# Sous-domaine www
www  CNAME ecomsimply.com

# Optionnel : sous-domaine API
api  CNAME ecomsimply.com
```

### **3. Suppression anciens enregistrements**
⚠️ **IMPORTANT** : Supprimez ou modifiez les anciens enregistrements A qui pointaient vers votre plateforme de test

### **4. Propagation DNS**
- **Délai** : 5-30 minutes (parfois jusqu'à 24h)
- **Vérification** : `nslookup ecomsimply.com`

## 🚨 POINTS D'ATTENTION 02SWITCH

### **Interface 02switch typique :**
1. **Panel cPanel** : Cherchez "Zone Editor" ou "DNS Zone Editor"
2. **Panel 02switch custom** : Cherchez "Gestion DNS" ou "DNS"
3. **Aide** : Support 02switch très réactif si besoin

### **Formats possibles chez 02switch :**
- Certains panels demandent le nom complet : `ecomsimply.com.` (avec point final)
- D'autres acceptent juste `@` pour le domaine principal

## ✅ VALIDATION DE LA CONFIGURATION

### **Commandes de test (après modification DNS)**
```bash
# Test résolution DNS
nslookup ecomsimply.com
nslookup www.ecomsimply.com

# Test réponse serveur
curl -I http://34.121.6.206
ping ecomsimply.com
```

### **Vérification en ligne**
- https://www.whatsmydns.net/ (propagation mondiale)
- https://dnschecker.org/ (vérification DNS)

## 🔄 APRÈS MODIFICATION DNS

Une fois les enregistrements DNS modifiés chez 02switch :

1. ✅ **Attendre 5-10 minutes** pour la propagation
2. ✅ **Je configure SSL automatiquement** avec Let's Encrypt
3. ✅ **Je mets à jour ECOMSIMPLY** pour le domaine
4. ✅ **Tests complets** de la plateforme

## 📞 AIDE 02SWITCH

**Si vous ne trouvez pas la gestion DNS :**
- Support 02switch : https://www.02switch.com/support/
- Téléphone : 04 44 44 60 00
- Demandez : "Comment modifier les enregistrements DNS pour mon domaine ?"

---

**🎯 PROCHAINE ÉTAPE :** 
Modifiez les DNS chez 02switch, puis dites-moi "DNS modifié" pour que je configure le SSL et finalise le déploiement !