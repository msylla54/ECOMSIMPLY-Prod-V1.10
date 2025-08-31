# 🔄 Plan de Rollback - ECOMSIMPLY

## Procédure de Rollback Rapide

### 1. Backup Vérification
- ✅ **MongoDB** : Base de données `ecomsimply_production` - Backup automatique via supervisor  
- ✅ **Code Source** : Version contrôlée avec git (pas de .git dans cet environnement)
- ✅ **Configuration** : Files .env sauvegardés en variables Kubernetes

### 2. Rollback Étapes (Temps estimé : 3-5 minutes)

```bash
# Étape 1 : Arrêt services (30s)
sudo supervisorctl stop all

# Étape 2 : Rollback code (1 min)
# [Action manuelle] : Restaurer version N-1 depuis Kubernetes/Ingress

# Étape 3 : Validation configuration (30s)
# Vérifier .env files intacts

# Étape 4 : Redémarrage services (2 mins)
sudo supervisorctl start all
sudo supervisorctl status

# Étape 5 : Vérification santé (1 min)
curl -s https://ecomsimply.com/api/health
```

### 3. Points de Vérification Post-Rollback
- [ ] API Health : `/api/health` retourne `status: "healthy"`  
- [ ] Frontend accessible : Homepage charge correctement
- [ ] Base de données : MongoDB opérationnelle
- [ ] Logs : Pas d'erreurs critiques dans supervisor logs

### 4. Responsables & Escalation
- **Release Manager** : Décision rollback
- **DevOps** : Exécution technique  
- **Escalation** : Si rollback échoue en > 10 minutes

**Temps de retour estimé :** 3-5 minutes maximum