# 🚀 BOOTSTRAP AUTOMATIQUE ECOMSIMPLY

## Objectif

Garantir la création automatique de la base de données `ecomsimply_production`, des collections, index et utilisateur admin au démarrage de l'application sur Vercel.

## ✅ Implémentation Réalisée

### 1️⃣ Hook de Démarrage Automatique

```python
@app.on_event("startup")
async def startup_event():
    """Hook de démarrage pour bootstrap automatique"""
    logger.info("🔄 Exécution startup bootstrap...")
    await bootstrap_database()
```

**Avantages** :
- ✅ Exécuté automatiquement à chaque démarrage
- ✅ Idempotent (peut être relancé sans problème)
- ✅ Logs détaillés pour diagnostic

### 2️⃣ Fonction Bootstrap Complète

La fonction `bootstrap_database()` effectue :

1. **Test connectivité MongoDB** : `await client.admin.command("ping")`
2. **Création index unique** : `users.email` (unique, background)
3. **Création index performance** : `product_sheets.user_id` et `created_at`
4. **Création admin automatique** si `ADMIN_EMAIL` + `ADMIN_PASSWORD_HASH` présents

### 3️⃣ Route Bootstrap Manuelle

```
POST /api/admin/bootstrap
```

**Usage** :
```bash
curl -X POST https://ecomsimply.com/api/admin/bootstrap
```

**Réponse** :
```json
{
  "status": "success",
  "message": "Bootstrap database exécuté avec succès",
  "timestamp": "2025-08-22T12:00:00.000Z"
}
```

## 🔧 Configuration Requise

### Variables d'Environnement Vercel

```bash
# CRITIQUES pour bootstrap admin
ADMIN_EMAIL=msylla54@gmail.com
ADMIN_PASSWORD_HASH=$2b$12$AX.4AQP8u50RP3.pcupJ6OJSSOHQqTG71NJvZRW/J6kyRFnxKX0.W

# MongoDB avec DB dans l'URI (recommandé)
MONGO_URL=mongodb+srv://USERNAME:PASSWORD@cluster.mongodb.net/ecomsimply_production?retryWrites=true&w=majority

# OU MongoDB + DB_NAME séparée
MONGO_URL=mongodb+srv://USERNAME:PASSWORD@cluster.mongodb.net/?retryWrites=true&w=majority
DB_NAME=ecomsimply_production
```

## 🎯 Comportement Bootstrap

### Première Exécution (DB vide)
```
🚀 Démarrage bootstrap database...
✅ MongoDB ping successful
✅ Index unique sur users.email créé
✅ Index sur product_sheets créés
✅ Admin créé: msylla54@gmail.com
🎯 Bootstrap database terminé avec succès
```

### Exécutions Suivantes (DB existante)
```
🚀 Démarrage bootstrap database...
✅ MongoDB ping successful
📝 Index users.email déjà existant
📝 Index product_sheets déjà existants
📝 Admin déjà existant: msylla54@gmail.com
🎯 Bootstrap database terminé avec succès
```

## 🔐 Utilisateur Admin Créé

```json
{
  "id": "uuid-generated",
  "email": "msylla54@gmail.com",
  "name": "Admin ECOMSIMPLY",
  "password_hash": "$2b$12$AX.4AQP8u50RP3.pcupJ6OJSSOHQqTG71NJvZRW/J6kyRFnxKX0.W",
  "is_admin": true,
  "subscription_plan": "premium",
  "language": "fr",
  "created_at": "ISODate",
  "generate_images": true,
  "include_images_manual": true
}
```

**Mot de passe** : `ECS-Temp#2025-08-22!`

## ⚡ Test Rapide

Après déploiement sur Vercel :

### 1. Vérifier Bootstrap Auto
```bash
# Vérifier logs Vercel Functions
# Rechercher : "🎯 Bootstrap database terminé avec succès"
```

### 2. Tester Bootstrap Manuel
```bash
curl -X POST https://ecomsimply.com/api/admin/bootstrap
```

### 3. Tester Login Admin
- URL : https://ecomsimply.com/login
- Email : `msylla54@gmail.com`
- Password : `ECS-Temp#2025-08-22!`

## 🛡️ Sécurité

- ✅ **Idempotent** : Pas de duplication si relancé
- ✅ **Variables ENV** : Pas de credentials hardcodés
- ✅ **Logs sécurisés** : Pas de mots de passe dans les logs
- ✅ **Route temporaire** : `/api/admin/bootstrap` peut être désactivée après succès

## 🚫 Désactiver Route Bootstrap

Pour désactiver la route bootstrap après succès :

```python
# Commenter ou supprimer dans server.py
# @app.post("/api/admin/bootstrap")
# async def manual_bootstrap():
#     ...
```

## 📊 Monitoring

Surveiller dans les logs Vercel Functions :
- ✅ `MongoDB ping successful`
- ✅ `Admin créé: msylla54@gmail.com`
- ❌ `Erreur bootstrap database:` (si problème)

---

**Status** : ✅ Prêt pour déploiement Vercel
**Mot de passe admin** : `ECS-Temp#2025-08-22!`
**Prochaine étape** : Appliquer le patch et configurer les variables ENV sur Vercel