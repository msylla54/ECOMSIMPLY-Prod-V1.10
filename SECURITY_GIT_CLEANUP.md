# 🔐 NETTOYAGE SÉCURITÉ GIT - ECOMSIMPLY-PROD-V1.1

**Date:** 21 Août 2025  
**Action:** Purge des secrets de l'historique Git + Rotation des clés

---

## ⚠️ PROBLÈME IDENTIFIÉ

Des fichiers `.env` contenant des secrets en clair ont été commitées dans l'historique Git :
- Mots de passe admin
- Clés API (Amazon, Shopify, Stripe, OpenAI)
- Secrets JWT et clés de chiffrement
- Strings de connexion MongoDB

**RISQUE:** Compromission des credentials même après suppression des fichiers.

---

## 🧹 ACTIONS DE NETTOYAGE RECOMMANDÉES

### 1. Purge de l'historique Git (OBLIGATOIRE)

```bash
# Sauvegarder le repo actuel
git clone --mirror https://github.com/votre-repo/ecomsimply.git backup-repo.git

# Purger les fichiers .env de l'historique
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env .env.* backend/.env* frontend/.env*' \
  --prune-empty --tag-name-filter cat -- --all

# Alternative plus moderne avec git-filter-repo
pip install git-filter-repo
git filter-repo --path .env --path .env.production --path backend/.env --invert-paths

# Forcer la mise à jour du remote
git push origin --force --all
git push origin --force --tags
```

### 2. Rotation OBLIGATOIRE des clés compromises

**🔐 ADMIN CREDENTIALS**
```bash
# FAIT ✅ - Nouveau mot de passe sécurisé généré
Email: msylla54@gmail.com
Nouveau password: SecureAdmin2025!
Hash: $2b$12$54mp5rKMn7RBleHBIZB2DO.kLSoKKFegF8uunFzMr3E9RJv6S47EG
```

**🔑 JWT & ENCRYPTION (À RENOUVELER)**
```bash
# Générer de nouvelles clés
JWT_SECRET: [NOUVELLE CLÉ 32+ chars]
ENCRYPTION_KEY: [NOUVELLE CLÉ 32 chars base64]
```

**🛍️ SHOPIFY (À RENOUVELER)**
```bash
# Dans Shopify Partner Dashboard
SHOPIFY_CLIENT_SECRET: [REGÉNÉRER dans Partner Dashboard]
SHOPIFY_ACCESS_TOKEN_ENCRYPTION_KEY: [NOUVELLE CLÉ 32 chars]
```

**🛒 AMAZON SP-API (À RENOUVELER)**
```bash
# Dans Amazon Developer Console
AMAZON_LWA_CLIENT_SECRET: [REGÉNÉRER dans Dev Console]
AMAZON_REFRESH_TOKEN_ENCRYPTION_KEY: [NOUVELLE CLÉ 32 chars]
```

**💳 STRIPE (À RENOUVELER)**
```bash
# Dans Stripe Dashboard → API Keys
STRIPE_SECRET_KEY: [REGÉNÉRER nouvelle clé]
STRIPE_WEBHOOK_SECRET: [REGÉNÉRER endpoint webhook]
```

**🤖 AI SERVICES (À RENOUVELER)**
```bash
# OpenAI Platform
OPENAI_API_KEY: [REGÉNÉRER nouvelle clé]

# FAL.ai Dashboard  
FAL_KEY: [REGÉNÉRER nouvelle clé]
```

**🗄️ MONGODB (À RENOUVELER)**
```bash
# MongoDB Atlas → Database Access
MONGO_URL: [REGÉNÉRER password utilisateur]
```

---

## 🛡️ MESURES PRÉVENTIVES APPLIQUÉES

### Configuration Git sécurisée
```bash
# .gitignore renforcé
.env
.env.*
!.env.example
!.env.template
*token.json*
*credentials.json*
```

### Politique de gestion des secrets
1. **Jamais de secrets en clair dans le code**
2. **Variables d'environnement uniquement**
3. **Rotation régulière (90 jours)**
4. **Accès minimal aux credentials**

### Validation automatique
```bash
# Hook pre-commit pour détecter secrets
git secrets --install
git secrets --register-aws
git secrets --scan
```

---

## 📋 CHECKLIST POST-NETTOYAGE

- [ ] **Git filter-branch** exécuté et historique purgé
- [ ] **Force push** effectué sur le remote
- [ ] **JWT_SECRET** régénéré et configuré dans Vercel
- [ ] **ENCRYPTION_KEY** régénérée et configurée
- [ ] **Shopify secrets** régénérés dans Partner Dashboard
- [ ] **Amazon secrets** régénérés dans Developer Console  
- [ ] **Stripe secrets** régénérés dans Dashboard
- [ ] **OpenAI/FAL keys** régénérées
- [ ] **MongoDB password** régénéré dans Atlas
- [ ] **Tests déploiement** avec nouvelles clés
- [ ] **Validation connexion admin** avec nouveau password

---

## 🚨 URGENCE DE MISE EN ŒUVRE

**PRIORITÉ CRITIQUE:** Effectuer la rotation des clés dans les 24h suivant ce commit.

**RISQUE:** Tant que les anciennes clés ne sont pas révoquées, elles restent utilisables par des tiers ayant accès à l'historique Git.

---

## 📞 SUPPORT

En cas de problème lors de la rotation :
1. Vérifier la documentation des services (Shopify Partner, Amazon Dev, etc.)
2. Tester chaque nouvelle clé individuellement
3. Utiliser les environnements de test avant production
4. Conserver temporairement les anciennes clés jusqu'à validation

---

*Document généré automatiquement - ECOMSIMPLY Security Team*