# Guide de Configuration Stripe pour ECOMSIMPLY
## Système d'Essai Gratuit 7 Jours

Ce guide vous explique comment configurer Stripe pour implémenter un système d'essai gratuit de 7 jours avec les plans Pro (29€/mois) et Premium (99€/mois).

---

## 🎯 Objectif
Remplacer le système actuel "setup mode" par la fonctionnalité native `trial_period_days` de Stripe pour une gestion plus simple et robuste des essais gratuits.

---

## 📋 Étape 1: Créer les Produits et Prix dans Stripe

### 1.1 Accéder au Dashboard Stripe
1. Connectez-vous à votre [Dashboard Stripe](https://dashboard.stripe.com)
2. Assurez-vous d'être en mode **Test** pour les tests initiaux

### 1.2 Créer le Produit "ECOMSIMPLY Pro"
1. Allez dans **Produits** → **Catalogue de produits**
2. Cliquez sur **+ Ajouter un produit**
3. Remplissez les informations :
   - **Nom** : `ECOMSIMPLY Pro`
   - **Description** : `Plan Pro avec génération IA de fiches produits`
   - **Image** : (optionnel) ajoutez le logo ECOMSIMPLY

### 1.3 Créer le Prix Pro avec Essai Gratuit
1. Dans la section **Informations de tarification** :
   - **Modèle de tarification** : `Tarification standard`
   - **Prix** : `29.00` EUR
   - **Facturation** : `Récurrente`
   - **Période de facturation** : `Mensuel`

2. **IMPORTANT** - Activer l'essai gratuit :
   - Cochez **Essai gratuit**
   - **Durée de l'essai** : `7` jours
   - Cliquez sur **Enregistrer le produit**

3. **Copier l'ID du prix** : Après création, copiez l'ID qui commence par `price_` (ex: `price_1234567890abcdef`)

### 1.4 Créer le Produit "ECOMSIMPLY Premium"
1. Répétez les étapes 1.2 et 1.3 avec :
   - **Nom** : `ECOMSIMPLY Premium`
   - **Description** : `Plan Premium avec fonctionnalités avancées`
   - **Prix** : `99.00` EUR
   - **Essai gratuit** : `7` jours

2. **Copier l'ID du prix Premium**

---

## 📋 Étape 2: Configuration des Webhooks

### 2.1 Créer un Endpoint Webhook
1. Allez dans **Développeurs** → **Webhooks**
2. Cliquez sur **+ Ajouter un endpoint**
3. **URL de l'endpoint** : `https://ecomsimply.com/api/stripe/webhook`
   - Remplacez `votre-domaine.com` par votre domaine réel
4. **Description** : `ECOMSIMPLY Trial Management`

### 2.2 Sélectionner les Événements
Cochez les événements suivants :

#### Événements Essentiels :
- ✅ `customer.subscription.created`
- ✅ `customer.subscription.updated` 
- ✅ `customer.subscription.deleted`
- ✅ `customer.subscription.trial_will_end`
- ✅ `invoice.payment_succeeded`
- ✅ `invoice.payment_failed`
- ✅ `checkout.session.completed`

#### Événements Optionnels (recommandés) :
- ✅ `customer.created`
- ✅ `customer.updated`
- ✅ `invoice.created`

### 2.3 Finaliser le Webhook
1. Cliquez sur **Ajouter un endpoint**
2. **Copier la clé de signature** (`whsec_...`) - vous en aurez besoin pour le code

---

## 📋 Étape 3: Récupérer les Clés API

### 3.1 Clés API
1. Allez dans **Développeurs** → **Clés API**
2. Copiez :
   - **Clé publique** (commence par `pk_test_` ou `pk_live_`)
   - **Clé secrète** (commence par `sk_test_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX` ou `sk_live_`)

---

## 📋 Étape 4: Variables d'Environnement

Ajoutez ces variables dans votre fichier `/app/backend/.env` :

```env
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_votre_cle_publique
STRIPE_SECRET_KEY=sk_test_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
STRIPE_WEBHOOK_SECRET=whsec_votre_signature_webhook

# Prix IDs (remplacez par vos vrais IDs)
STRIPE_PRO_PRICE_ID=price_1234567890abcdef_pro
STRIPE_PREMIUM_PRICE_ID=price_1234567890abcdef_premium
```

---

## 📋 Étape 5: Test de Configuration

### 5.1 Cartes de Test Stripe
Utilisez ces cartes pour tester :

#### Succès :
- **Visa** : `4242424242424242`
- **Mastercard** : `5555555555554444`

#### Échecs :
- **Carte déclinée** : `4000000000000002`
- **Fonds insuffisants** : `4000000000009995`

### 5.2 Informations de Test
- **Date d'expiration** : N'importe quelle date future (ex: 12/25)
- **CVC** : N'importe quel code à 3 chiffres (ex: 123)
- **Code postal** : N'importe lequel (ex: 12345)

---

## 🔄 Étape 6: Migration vers Production

### 6.1 Quand vous êtes prêt pour la production :
1. Basculez en mode **Live** dans Stripe
2. Recréez les produits et prix en mode Live
3. Reconfigurez les webhooks avec l'URL de production
4. Mettez à jour les clés API avec les clés Live (`pk_live_` et `sk_live_`)

---

## ✅ Checklist de Vérification

Avant de passer au code, vérifiez que vous avez :

- [ ] Créé le produit ECOMSIMPLY Pro avec prix 29€/mois et essai 7 jours
- [ ] Créé le produit ECOMSIMPLY Premium avec prix 99€/mois et essai 7 jours  
- [ ] Copié les deux Price IDs (Pro et Premium)
- [ ] Configuré le webhook avec tous les événements nécessaires
- [ ] Copié la clé de signature webhook (whsec_...)
- [ ] Copié les clés API (publique et secrète)
- [ ] Ajouté toutes les variables dans le fichier .env

---

## 🆘 Support

Si vous rencontrez des problèmes :
1. Vérifiez les logs Stripe dans **Développeurs** → **Logs**
2. Testez les webhooks avec l'outil de test intégré de Stripe
3. Consultez la [documentation officielle Stripe](https://stripe.com/docs/billing/subscriptions/trials)

---

**Une fois cette configuration terminée, nous pourrons procéder à la refactorisation du code backend pour utiliser le nouveau système !**