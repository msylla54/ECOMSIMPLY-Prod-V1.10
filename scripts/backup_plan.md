# 🔒 PLAN DE SAUVEGARDE & ROLLBACK - Migration DB

## 📊 Situation Actuelle (31/08/2025 22:18 UTC)

- **Backend actuel** : `DB_NAME=ecomsimply_production` (vide, 0 documents)
- **Base production** : `ecomsimply_production` (11 collections, 19 documents)
- **Opération requise** : Correction variable ENV pour pointer vers la vraie base

## 🔒 Stratégie de Sauvegarde

### Option A : Snapshot Atlas (Recommandé)
- Atlas propose des snapshots automatiques
- Backup de `ecomsimply_production` avant bascule
- Restauration possible en 1-click depuis Atlas Console

### Option B : Export Manuel
```bash
# Backup production avant bascule
mongodump --uri="mongodb+srv://ecomsimply-app:xIP7EfOXhODZdp0k@ecomsimply.xagju9s.mongodb.net/ecomsimply_production" --out artifacts/backup_prod_$(date +%Y%m%d_%H%M%S)
```

## 🔄 Plan de Rollback

### Rollback Immédiat (si problème détecté)
1. **Variable ENV emergent.sh** :
   ```bash
   DB_NAME=ecomsimply_production  # Retour à l'ancienne valeur
   ```
   
2. **Redéploiement** :
   - Redéployer le backend emergent.sh
   - Vérifier `/api/health` → `database: ecomsimply_production`

3. **Temps de rollback estimé** : < 5 minutes

### Rollback Complet (si corruption)
1. Utiliser snapshot Atlas pour restaurer `ecomsimply_production`
2. Retour à `DB_NAME=ecomsimply_production`
3. Investigation des causes racines

## ⚠️ Risques Identifiés

1. **Risque FAIBLE** : Changement de pointeur ENV uniquement
2. **Risque de régression** : Minimal (les données sont déjà en prod)
3. **Fenêtre de risque** : 2-3 minutes (temps de redéploiement)

## ✅ Validation Pré-Migration

- ✅ Connexion Atlas production testée
- ✅ Base `ecomsimply_production` contient les données
- ✅ Backend fonctionne (pointe actuellement vers base vide)
- ✅ Credentials production configurés dans emergent.sh

---
*Document généré le 2025-08-31T22:18:00Z*