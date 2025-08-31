# Amazon Pricing Rules - Phase 4 📍💰

## Vue d'ensemble

La Phase 4 "Prix & Règles Amazon" implémente un moteur de prix intelligents avec Buy Box awareness et publication temps réel via Amazon SP-API.

## Fonctionnalités Principales

### 🎯 Moteur de Prix Intelligents
- **Buy Box Awareness** : Analyse en temps réel des concurrents et détection de l'état Buy Box
- **Stratégies configurables** :
  - `buybox_match` : Matcher le prix Buy Box avec léger avantage
  - `margin_target` : Maintenir une marge cible définie
  - `floor_ceiling` : Rester dans les limites min/max avec variance

### ⚙️ Règles Configurables par SKU
- Prix minimum et maximum
- Variance percentage autorisée
- Prix MAP (Minimum Advertised Price)
- Mise à jour automatique avec fréquence configurable
- Contraintes de sécurité appliquées

### 🚀 Publication Temps Réel
- **Listings Items API** (méthode prioritaire)
- **Feeds API** (POST_PRODUCT_PRICING_DATA) en fallback
- Validation complète avant publication
- Retry automatique et gestion d'erreurs

### 📊 Historique et Monitoring
- Historisation complète de toutes les décisions
- Dashboard avec statistiques et alertes Buy Box
- Traitement par lot pour optimisation massive
- Métriques de performance détaillées

## Architecture Technique

### Backend

```
backend/
├── models/amazon_pricing.py          # Modèles Pydantic
├── amazon/pricing_engine.py          # Moteur de prix principal
├── services/amazon_pricing_rules_service.py  # Service MongoDB
├── routes/amazon_pricing_routes.py   # API REST endpoints
└── scripts/init_pricing_indexes.py   # Initialisation DB
```

### Frontend

```
frontend/src/
├── components/AmazonPricingRulesManager.js  # Interface principale
└── pages/AmazonIntegrationPage.js           # Intégration onglet
```

### API Endpoints

- `POST /api/amazon/pricing/rules` - Créer une règle
- `GET /api/amazon/pricing/rules` - Lister les règles
- `PUT /api/amazon/pricing/rules/{id}` - Modifier une règle
- `POST /api/amazon/pricing/calculate` - Calculer prix optimal
- `POST /api/amazon/pricing/publish` - Publier un prix
- `POST /api/amazon/pricing/batch` - Traitement par lot
- `GET /api/amazon/pricing/history` - Historique
- `GET /api/amazon/pricing/dashboard` - Données dashboard

## Configuration SP-API

### Variables d'environnement requises

```env
# Amazon SP-API Credentials (déjà configurées sur Vercel)
AMAZON_LWA_CLIENT_ID=amzn1.application-oa2-client.XXXXXXXXXXXXXXXX
AMAZON_LWA_CLIENT_SECRET=xxx
AMAZON_LWA_REFRESH_TOKEN=Atzr|xxx
AMAZON_SP_API_ROLE_ARN=arn:aws:iam::xxx:role/xxx

# Base de données
MONGO_URL=mongodb://localhost:27017/ecomsimply
```

## Installation et Démarrage

### 1. Initialiser les index MongoDB

```bash
cd /app/backend
python scripts/init_pricing_indexes.py
```

### 2. Démarrer les services

```bash
# Backend (FastAPI)
cd /app/backend
uvicorn server:app --host 0.0.0.0 --port 8001

# Frontend (React)
cd /app/frontend
npm start
```

### 3. Accéder à l'interface

- Frontend : `http://localhost:3000`
- Naviguer vers : `Amazon` → `Prix & Règles`

## Utilisation

### 1. Créer une règle de prix

```javascript
// Via interface ou API
const rule = {
  sku: "B08N5WRWNW",
  marketplace_id: "A13V1IB3VIYZZH", // Amazon FR
  min_price: 50.00,
  max_price: 150.00,
  variance_pct: 5.0,
  strategy: "buybox_match",
  auto_update: true
};
```

### 2. Publication manuelle

```javascript
// Calculer le prix optimal
const calculation = await fetch('/api/amazon/pricing/calculate', {
  method: 'POST',
  body: JSON.stringify({ sku: "B08N5WRWNW" })
});

// Publier si acceptable
const result = await fetch('/api/amazon/pricing/publish', {
  method: 'POST', 
  body: JSON.stringify({ 
    sku: "B08N5WRWNW",
    method: "listings_items"
  })
});
```

### 3. Traitement par lot

```javascript
const batch = await fetch('/api/amazon/pricing/batch', {
  method: 'POST',
  body: JSON.stringify({
    skus: ["B08N5WRWNW", "B08N5WRWNY"],
    marketplace_id: "A13V1IB3VIYZZH",
    force_update: false
  })
});
```

## Modèles de Données

### PricingRule

```python
{
  "id": "uuid",
  "user_id": "user-123", 
  "sku": "B08N5WRWNW",
  "marketplace_id": "A13V1IB3VIYZZH",
  "min_price": 50.00,
  "max_price": 150.00,
  "variance_pct": 5.0,
  "strategy": "buybox_match",
  "margin_target": 25.0,  # Si strategy = margin_target
  "auto_update": true,
  "status": "active",
  "created_at": "2025-01-20T10:00:00Z"
}
```

### PricingHistory

```python
{
  "id": "uuid",
  "sku": "B08N5WRWNW", 
  "old_price": 79.99,
  "new_price": 77.50,
  "price_change": -2.49,
  "buybox_price": 77.99,
  "buybox_status_before": "risk",
  "publication_success": true,
  "reasoning": "Alignement Buy Box avec avantage concurrentiel",
  "confidence": 85.5,
  "created_at": "2025-01-20T10:30:00Z"
}
```

## Monitoring et Alertes

### Dashboard Indicateurs

- **Règles actives** : Nombre de règles opérationnelles
- **Buy Box gagnées** : SKUs avec Buy Box
- **À risque** : SKUs risquant de perdre la Buy Box  
- **Mises à jour 24h** : Réussis/Échecs

### Alertes Buy Box

```javascript
{
  "sku": "B08N5WRWNW",
  "message": "Risque de perte Buy Box - concurrent à 0.50€ de moins", 
  "severity": "warning",
  "created_at": "2025-01-20T10:45:00Z"
}
```

## Tests Automatiques

### Backend

```bash
cd /app/backend
python -m pytest tests/test_amazon_pricing.py -v
```

### Frontend  

```bash
cd /app/frontend
npm test -- --testPathPattern=AmazonPricingRules
```

### Tests E2E

```bash
# Test complet : Calcul → Publication → Vérification SP-API
python tests/e2e/test_pricing_workflow.py
```

## Performance et Limites

### Contraintes SP-API

- **Product Pricing API** : 0.5 req/sec
- **Listings Items API** : 5 req/sec  
- **Feeds API** : Pas de limite stricte

### Optimisations

- Cache des données concurrentielles (5 min)
- Batch processing avec délais
- Retry exponential backoff
- Circuit breaker sur échecs répétés

## Sécurité

### Validation des Prix

- Contraintes min/max strictes
- Variance percentage limitée
- Validation MAP price
- Approbation manuelle pour changements >20%

### Authentification

- JWT tokens requis sur tous endpoints
- Isolation multi-tenant complète
- Audit trail complet des actions

## Troubleshooting

### Erreurs Communes

#### SP-API 403 Forbidden
```
Cause: Tokens expirés ou autorisations manquantes
Solution: Vérifier les credentials et refresh tokens
```

#### Prix hors contraintes
```
Cause: Calcul dépasse min/max ou variance
Solution: Ajuster les règles ou forcer avec force_update=true
```

#### Buy Box non détectée
```
Cause: Product Pricing API ne retourne pas de données
Solution: Vérifier ASIN et marketplace_id
```

## Support

### Logs

```bash
# Backend logs
tail -f /var/log/supervisor/backend.*.log | grep pricing

# Frontend console
F12 → Console → Filtrer "pricing"
```

### Debug Mode

```env
# Activer les logs détaillés
PRICING_DEBUG=true
LOG_LEVEL=DEBUG
```

---

**Phase 4 - Prix & Règles Amazon** développée pour ECOMSIMPLY  
Publication réelle via SP-API - Pas de mock ni sandbox  
Architecture production-ready pour Vercel