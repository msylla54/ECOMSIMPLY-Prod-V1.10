# 🔍 AUDIT DES SOURCES DE DONNÉES - ECOMSIMPLY

## 📋 RÉSUMÉ EXÉCUTIF

**Date :** 23 août 2025  
**Projet :** Migration complète vers MongoDB Atlas  
**Scope :** Toutes les données applicatives (testimonials, messages, IA, historiques, stats, utilisateurs)  
**Source Database :** Données codées en dur + quelques collections MongoDB existantes  
**Target Database :** MongoDB Atlas `ecomsimply_production`

---

## 🎯 PÉRIMÈTRE DE MIGRATION IDENTIFIÉ

### ✅ **Données à Migrer**

| Entité | Source Actuelle | Volume Estimé | Status |
|--------|----------------|---------------|--------|
| **Users** | MongoDB Existant | ~10-50 users | ✅ Déjà en DB |
| **Testimonials** | Codé en dur (server.py) | 3 testimonials | 🔄 À migrer |
| **Plans-Pricing** | Codé en dur (server.py) | 3 plans | 🔄 À migrer |
| **Languages** | Codé en dur (server.py) | 4 langues | 🔄 À migrer |
| **Stats Public** | Codé en dur (server.py) | 5 métriques | 🔄 À migrer |
| **Messages/Contact** | Non implémenté | 0 | 🆕 À créer |
| **AI Sessions** | Non persisté | 0 | 🆕 À créer |
| **Product Generations** | Non persisté | 0 | 🆕 À créer |
| **Affiliate Config** | Codé en dur (server.py) | 1 config | 🔄 À migrer |

---

## 📊 ANALYSE DÉTAILLÉE PAR ENTITÉ

### 1. **👤 USERS (Déjà en MongoDB)**
- **Source :** MongoDB Collection `users`
- **Schema Actuel :**
  ```json
  {
    "_id": ObjectId,
    "email": String (unique),
    "name": String,
    "passwordHash": String,
    "is_admin": Boolean,
    "isActive": Boolean,
    "created_at": DateTime
  }
  ```
- **Volume :** ~10-50 utilisateurs estimés
- **Index :** `{ email: 1 }` unique ✅
- **Action :** Ajouter `last_login_at` field + compléter index

### 2. **💬 TESTIMONIALS (Codé en dur)**
- **Source :** `/backend/server.py` lines 441-470
- **Données Actuelles :**
  ```python
  testimonials = [
    {
      "id": 1,
      "name": "Marie Dubois",
      "company": "Boutique Mode Paris", 
      "avatar": "/assets/testimonials/marie.jpg",
      "rating": 5,
      "text": "ECOMSIMPLY a révolutionné notre processus..."
    },
    {
      "id": 2,
      "name": "Thomas Martin",
      "company": "TechStore Online",
      "avatar": "/assets/testimonials/thomas.jpg",
      "rating": 5,
      "text": "L'IA d'ECOMSIMPLY génère des descriptions..."
    },
    {
      "id": 3,
      "name": "Sophie Laurent", 
      "company": "Cosmétiques Bio",
      "avatar": "/assets/testimonials/sophie.jpg",
      "rating": 5,
      "text": "Interface intuitive et résultats impressionnants..."
    }
  ]
  ```
- **Volume :** 3 témoignages
- **Migration :** Seed script + API switch to MongoDB

### 3. **💰 PLANS-PRICING (Codé en dur)**
- **Source :** `/backend/server.py` lines 384-434
- **Schema Actuel :**
  ```python
  plans = [
    {
      "id": "starter",
      "name": "Starter", 
      "price": 29,
      "currency": "EUR",
      "period": "month",
      "features": ["50 produits/mois", "IA basique", ...]
    },
    # Pro: 79€, Enterprise: 199€
  ]
  ```
- **Volume :** 3 plans tarifaires
- **Migration :** Collection `subscription_plans`

### 4. **📊 STATS PUBLIC (Codé en dur)**
- **Source :** `/backend/server.py` lines 475-485
- **Données :**
  ```python
  stats = {
    "products_generated": 125000,
    "active_users": 2500, 
    "time_saved_hours": 50000,
    "conversion_improvement": "45%",
    "seo_score_average": 92
  }
  ```
- **Volume :** 5 métriques clés
- **Migration :** Collection `stats_public` avec key-value

### 5. **🌐 LANGUAGES (Codé en dur)**
- **Source :** `/backend/server.py` lines 487-520
- **Schema :**
  ```python
  languages = [
    {"code": "fr", "name": "Français", "flag": "🇫🇷", "default": True},
    {"code": "en", "name": "English", "flag": "🇺🇸", "default": False},
    {"code": "es", "name": "Español", "flag": "🇪🇸", "default": False},
    {"code": "de", "name": "Deutsch", "flag": "🇩🇪", "default": False}
  ]
  ```
- **Volume :** 4 langues supportées
- **Migration :** Collection `languages`

### 6. **📧 MESSAGES/CONTACT (Non implémenté)**
- **Source :** Aucune (à créer)
- **Usage Frontend :** 168 références trouvées (components messages)
- **Schema Proposé :**
  ```json
  {
    "_id": ObjectId,
    "userId": ObjectId? (optional for anonymous),
    "email": String,
    "subject": String,
    "body": String,
    "source": "contact" | "chat" | "support",
    "status": "new" | "read" | "replied" | "closed",
    "created_at": DateTime,
    "updated_at": DateTime
  }
  ```
- **Volume :** 0 (nouveau)
- **API à créer :** POST /api/messages, GET /api/admin/messages

### 7. **🤖 AI SESSIONS & EVENTS (Non persisté)**
- **Source :** Logique métier dans components mais pas de persistance
- **Usage Frontend :** Intégrations IA dispersées dans components
- **Schema Proposé :**
  ```json
  // ai_sessions
  {
    "_id": ObjectId,
    "userId": ObjectId?,
    "sessionType": "product_generation" | "seo_optimization" | "chat",
    "model": String,
    "params": Object,
    "created_at": DateTime,
    "closed_at": DateTime?
  }
  
  // ai_events  
  {
    "_id": ObjectId,
    "sessionId": ObjectId,
    "role": "user" | "assistant" | "tool",
    "content": String,
    "tokens": Number?,
    "latencyMs": Number?,
    "created_at": DateTime
  }
  ```
- **Volume :** 0 (nouveau)
- **API à créer :** POST /api/ai/sessions, GET /api/ai/sessions/:id/events

### 8. **📦 PRODUCT GENERATIONS (Non persisté)**
- **Source :** Logique dans components mais historique non sauvé
- **Schema Proposé :**
  ```json
  {
    "_id": ObjectId,
    "userId": ObjectId,
    "input": {
      "productData": Object,
      "marketplace": String,
      "language": String,
      "options": Object
    },
    "result": {
      "title": String,
      "description": String,
      "keywords": Array,
      "images": Array?
    },
    "status": "pending" | "completed" | "failed",
    "cost": Number?,
    "created_at": DateTime,
    "finished_at": DateTime?
  }
  ```
- **Volume :** 0 (nouveau) 
- **API à créer :** POST /api/products/generations, GET /api/products/generations

---

## 🔍 SOURCES DE DONNÉES SUPPLÉMENTAIRES

### ✅ **Fichiers JSON Trouvés**
```bash
/app/ecomsimply-deploy/baseline.json - Tests/metrics (non migrable)
/app/ecomsimply-deploy/market_settings_test_results.json - Tests (non migrable)
/app/ecomsimply-deploy/iphone_15_pro_validation_results.json - Tests (non migrable)
/app/ecomsimply-deploy/artifacts/*.json - Build artifacts (non migrable)
```
**Verdict :** Aucun fichier JSON contenant des données business à migrer

### ✅ **Recherche SQLite/Databases**
```bash
# Aucune base SQLite trouvée
find /app/ecomsimply-deploy -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3"
# (empty result)
```
**Verdict :** Pas de bases de données locales

### ✅ **Données dans Models Python**
```bash
grep -r "testimonials\|messages\|stats" /app/ecomsimply-deploy/backend --include="*.py"
```
**Trouvé :** Principalement des références dans models/amazon et server.py
**Verdict :** Data hardcodée dans server.py uniquement

---

## 🎯 CONTRAINTES & DÉFIS IDENTIFIÉS

### 1. **Incohérences de Format**
- **IDs :** Mix de `id: 1` (int) et ObjectId MongoDB
- **Dates :** Pas de timestamps sur données hardcodées
- **Validation :** Aucune validation Pydantic sur données actuelles

### 2. **Volume de Données**
- **Très faible :** 3 testimonials, 3 plans, 5 stats
- **Pas d'historique :** AI sessions et product generations à 0
- **Avantage :** Migration rapide et simple

### 3. **Dépendances Frontend**
- **168 références** aux messages dans frontend
- **Endpoints hardcodés** dans components
- **Error handling** à vérifier lors du switch

### 4. **Index Performance**
- **Critiques :** users.email (unique), messages.userId, ai_sessions.userId
- **Search :** testimonials.published, stats_public.key
- **TTL :** ai_sessions optionnel pour cleanup automatique

---

## 📋 CHECKLIST VALIDATION

### ✅ **Complété**
- [x] Audit complet des sources de données
- [x] Identification volume et schema par entité  
- [x] Mappage source → target collections
- [x] Identification contraintes et défis
- [x] Plan collections + indexes

### 🔄 **Next Steps (Migration Scripts)**
- [ ] Créer Pydantic models pour toutes collections
- [ ] Script 0001: Seed testimonials depuis server.py
- [ ] Script 0002: Seed plans-pricing depuis server.py
- [ ] Script 0003: Seed languages depuis server.py  
- [ ] Script 0004: Seed stats_public depuis server.py
- [ ] Script 0005: Créer collections vides (messages, ai_sessions, etc.)
- [ ] Script 0006: Update users schema (last_login_at)

---

## 💾 RÉSUMÉ MIGRATION

**Total Collections :** 8 collections  
**Total Documents :** ~15-20 documents (seed data) + utilisateurs existants  
**Migration Complexity :** **FAIBLE** (principalement seed data)  
**Risk Level :** **BAS** (pas de données critiques en volume)  
**Rollback :** **SIMPLE** (backup MongoDB + restore hardcoded data)

**🎯 Ready for Migration Scripts Creation**