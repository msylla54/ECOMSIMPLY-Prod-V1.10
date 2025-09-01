# 🔄 MIGRATION BASE DE DONNÉES - ecomsimply_production → ecomsimply_production

## 📋 Résumé Exécutif

**Date** : 31 Août 2025  
**Opération** : Migration configuration base de données  
**Type** : Correction de pointeur ENV (pas de migration de données)  
**Durée estimée** : < 5 minutes  
**Risque** : FAIBLE (changement de configuration uniquement)

### **🎯 Situation Découverte**

- ❌ **Backend actuel** : Pointe vers `ecomsimply_production` (base VIDE - 0 documents)
- ✅ **Base production** : `ecomsimply_production` existe et contient 19 documents réels
- 🔄 **Action requise** : Corriger le pointeur ENV pour utiliser la vraie base

## 📊 Inventaire Pré-Migration

### **Base Source : ecomsimply_production**
- **Collections** : 0
- **Documents** : 0  
- **Status** : Complètement vide

### **Base Cible : ecomsimply_production**
- **Collections** : 11 (`users`, `testimonials`, `subscription_plans`, etc.)
- **Documents** : 19 (dont 3 utilisateurs)
- **Index** : Email unique validé et fonctionnel
- **Status** : ✅ Opérationnelle et prête

## 🔧 Configuration Technique

### **Variables d'Environnement emergent.sh**

**AVANT (Configuration incorrecte) :**
```bash
DB_NAME=ecomsimply_production
MONGO_URL=mongodb+srv://ecomsimply-app:***@ecomsimply.xagju9s.mongodb.net/ecomsimply_production
```

**APRÈS (Configuration correcte) :**
```bash
DB_NAME=ecomsimply_production  
MONGO_URL=mongodb+srv://ecomsimply-app:xIP7EfOXhODZdp0k@ecomsimply.xagju9s.mongodb.net/ecomsimply_production?retryWrites=true&w=majority&appName=EcomSimply
```

### **Variables de Contrôle (Temporaires)**
```bash
# Pendant migration uniquement
READ_ONLY_MODE=true   # Activer avant bascule
READ_ONLY_MODE=false  # Désactiver après validation
```

## 🚀 Procédure de Migration

### **PHASE 1 : Préparation**
1. ✅ Inventaire bases de données effectué
2. ✅ Validation index et contraintes production
3. ✅ Scripts de bascule et rollback préparés
4. ✅ Tests smoke automatisés créés

### **PHASE 2 : Mode Maintenance (< 2 minutes)**
1. **Activer lecture seule** : `READ_ONLY_MODE=true` dans emergent.sh
2. **Valider mode** : Vérifier que POST retourne 503
3. **Bascule ENV** : Configurer `DB_NAME=ecomsimply_production`
4. **Redéployer** l'application backend

### **PHASE 3 : Validation**
1. **Health check** : `/api/health` doit retourner `database: ecomsimply_production`
2. **Tests smoke** : Exécuter `scripts/smoke_db_switch.sh`
3. **Désactiver maintenance** : `READ_ONLY_MODE=false`
4. **Test écriture** : Valider création utilisateur

## 🧪 Commandes de Validation

### **Santé API**
```bash
curl https://ecomsimply-deploy.preview.emergentagent.com/api/health
# Attendu: {"database": "ecomsimply_production", "mongo": "ok"}
```

### **Tests Smoke Complets**
```bash
cd /app/ECOMSIMPLY-Prod-V1.6
./scripts/smoke_db_switch.sh
```

### **Test Contrainte Unique**
```bash
# Doit retourner 409 si email existe déjà
curl -X POST https://ecomsimply-deploy.preview.emergentagent.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"msylla54@gmail.com","password":"test123"}'
```

## 🔄 Plan de Rollback

### **Rollback Immédiat (< 5 minutes)**
En cas de problème détecté :

1. **Configurer emergent.sh** :
   ```bash
   DB_NAME=ecomsimply_production
   MONGO_URL=mongodb+srv://ecomsimply-app:***@ecomsimply.xagju9s.mongodb.net/ecomsimply_production
   READ_ONLY_MODE=false
   ```

2. **Redéployer** l'application

3. **Vérifier** :
   ```bash
   curl https://ecomsimply-deploy.preview.emergentagent.com/api/health
   # Attendu: {"database": "ecomsimply_production"}
   ```

### **Rollback Complet (Si corruption base)**
1. Utiliser snapshot Atlas pour restaurer `ecomsimply_production`
2. Appliquer rollback immédiat ci-dessus
3. Investigation des causes racines

## 📁 Artefacts Créés

### **Scripts d'Automation**
- `scripts/db_inventory.py` - Inventaire automatisé des bases
- `scripts/test_prod_db.py` - Test connexion et état production  
- `scripts/db_switch.sh` - Script de migration interactif
- `scripts/smoke_db_switch.sh` - Tests de non-régression
- `scripts/check_prod_indexes.py` - Validation index et contraintes

### **Documentation**
- `diag/db_inventory.md` - Rapport inventaire détaillé
- `scripts/backup_plan.md` - Plan de sauvegarde et rollback
- `DEPLOY_DB_SWITCH.md` - Ce document (guide complet)

### **Logs de Migration**
- `artifacts/db_switch_YYYYMMDD_HHMMSS.log` - Log détaillé migration
- `artifacts/smoke_test_YYYYMMDD_HHMMSS.log` - Résultats tests smoke

## ⚠️ Points d'Attention

### **Sécurité**
- ✅ Credentials MongoDB non exposés dans les logs
- ✅ Mode lecture seule pendant transition
- ✅ Validation contraintes unique email
- ✅ Tests de non-régression automatisés

### **Performance**
- ✅ Index email unique présent et testé
- ✅ Index performance `isActive_1_created_at_-1` présent
- ✅ Temps de réponse `/api/health` < 2s validé

### **Monitoring Post-Migration**
1. **Surveiller logs** application pour erreurs MongoDB
2. **Vérifier métriques** temps de réponse API
3. **Tester fonctionnalités** critiques (auth, CRUD)
4. **Valider données** cohérence et intégrité

## ✅ Checklist Validation

- [ ] `/api/health` retourne `database: ecomsimply_production`
- [ ] Tests smoke : 100% réussis
- [ ] Authentification : Login/Register fonctionnels
- [ ] Contraintes : Email unique validée
- [ ] Endpoints publics : Plans, testimonials OK
- [ ] Admin bootstrap : Fonctionnel avec token
- [ ] Mode lecture seule : Désactivé
- [ ] Logs : Aucune erreur MongoDB
- [ ] Performance : Temps réponse < 2s

## 📞 Support & Rollback d'Urgence

### **En cas d'urgence :**
1. **ROLLBACK IMMÉDIAT** : Configurer `DB_NAME=ecomsimply_production` dans emergent.sh
2. **Contact** : Ingénieur SRE/DevOps disponible
3. **Logs** : Consulter `artifacts/db_switch_*.log` pour diagnostic

### **Validation de Succès :**
✅ **Migration réussie si** :
- Health endpoint retourne `ecomsimply_production`  
- Tests smoke passent à 100%
- Utilisateurs peuvent se connecter/s'inscrire
- Aucune erreur dans les logs MongoDB

---

**📅 Document généré le 31/08/2025 22:30 UTC**  
**🔄 Status : PRÊT POUR EXÉCUTION**