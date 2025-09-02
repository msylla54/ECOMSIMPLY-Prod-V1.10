# DIAGNOSTIC DNS/CONTROL-PLANE + CORRECTIFS PREVIEW/API

## 📅 Date: 2025-09-02

## A) Control-plane emergent.sh - DNS Status

### Test DNS résolution
```bash
$ getent hosts api.emergent.sh
34.144.197.47   api.emergent.sh
```

✅ **RÉSULTAT**: DNS résout correctement vers `34.144.197.47`
- Pas d'erreur ERR_NAME_NOT_RESOLVED détectée côté environnement
- api.emergent.sh accessible pour les redéploiements

## B) Preview/API - Correctifs 404 + WebSocket

### Routes legacy corrigées (404 → 200):
1. ✅ `/api/public/plans-pricing-nocache` → Alias vers `/api/public/plans-pricing`
2. ✅ `/api/plans-pricing-alt` → Alias vers `/api/public/plans-pricing`  
3. ✅ `/api/public/affiliate-config` → Nouvelle route publique
4. ✅ `/healthz` → Nouveau endpoint pour ingress health check

### Tests validation:
- `/healthz` → 200 {"status":"ok"}
- `/api/public/affiliate-config` → 200 + config JSON
- `/api/public/plans-pricing-nocache` → 200 + plan Premium
- `/api/plans-pricing-alt` → 200 + plan Premium

## C) Configuration ENV mise à jour

### Stripe Configuration:
- Variables placeholders remplacées par `<REAL_*_NEEDED>` pour déploiement
- URLs billing configurées pour le domaine preview
- Architecture ENV-first maintenue

## D) Status final
- ✅ DNS api.emergent.sh fonctionnel 
- ✅ Routes legacy/404 corrigées
- ✅ /healthz endpoint ajouté
- ✅ Configuration Stripe prête pour clés réelles
- 🔄 Frontend cleanup en cours (prochaine étape)

## E) Prochaines actions
1. Nettoyer les appels frontend legacy
2. Corriger WebSocket URLs (si présentes)
3. Commit + force rebuild sur emergent.sh
4. Valider endpoints en production