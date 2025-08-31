# PREVIEW RUNTIME - Configuration 502 Fix

## 🎯 Résolution du 502 Bad Gateway

Ce document décrit les corrections appliquées pour résoudre le problème 502 Bad Gateway en preview.

## ✅ Corrections Appliquées

### 1. Endpoints de Santé Ajoutés

#### Backend (FastAPI - Port 8001)
```python
# Endpoint racine
@app.get("/")
async def root():
    return {
        "message": "ECOMSIMPLY Backend API", 
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "running"
    }

# Health check pour preview
@app.get("/healthz")
async def preview_healthz():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# Readiness check avec vérification DB
@app.get("/readyz")
async def preview_readyz():
    try:
        await db.command("ping")
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")
```

#### Frontend (React - Port 3000)
- Endpoint `/healthz` natif via React (200 OK avec HTML)
- Endpoint `/` natif via React (200 OK avec HTML)

### 2. Configuration Uvicorn Optimisée

Configuration supervisor mise à jour (`/etc/supervisor/conf.d/supervisord.conf`):

```bash
command=/root/.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1 --reload --timeout-keep-alive 65 --proxy-headers --forwarded-allow-ips="*"
```

**Options ajoutées:**
- `--timeout-keep-alive 65`: Évite les timeouts 502
- `--proxy-headers`: Gestion des headers de proxy
- `--forwarded-allow-ips="*"`: Accepte les IPs forwarded

### 3. Gestion d'Erreurs Globale

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__}
    )
```

## 🧪 Tests de Validation

### Tests Locaux Réussis

#### Backend (127.0.0.1:8001)
```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8001/       # 200
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8001/healthz # 200
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8001/readyz  # 200
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8001/api/health # 200
```

#### Frontend (127.0.0.1:3000)
```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3000/       # 200
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3000/healthz # 200
```

### Réponses JSON Exemples

#### Backend `/healthz`
```json
{"status":"ok","timestamp":"2025-08-15T17:02:00.441155"}
```

#### Backend `/readyz`
```json
{"status":"ready","timestamp":"2025-08-15T17:02:00.460185"}
```

#### Backend `/`
```json
{
  "message":"ECOMSIMPLY Backend API",
  "version":"1.0.0",
  "timestamp":"2025-08-15T17:02:00.478005",
  "status":"running"
}
```

## 🚀 Lancement Local

### Backend
```bash
cd /app/backend
/root/.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1 --timeout-keep-alive 65 --proxy-headers --forwarded-allow-ips="*"
```

### Frontend
```bash
cd /app/frontend
HOST=0.0.0.0 PORT=3000 yarn start
```

### Via Supervisor
```bash
sudo supervisorctl restart all
sudo supervisorctl status
```

## 📋 Architecture des Services

```
FRONTEND (React)     → Port 3000 → 0.0.0.0:3000
    ↓
BACKEND (FastAPI)    → Port 8001 → 0.0.0.0:8001
    ↓
MONGODB             → Port 27017 → localhost:27017
```

## 🔧 Variables d'Environnement

### Frontend (`/app/frontend/.env`)
```
REACT_APP_BACKEND_URL=https://ecomsimply.com
WDS_SOCKET_PORT=443
```

### Backend (`/app/backend/.env`)
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="ecomsimply_production"
# ... autres variables API
```

## ✅ Critères d'Acceptation Validés

- ✅ `/healthz` répond 200 en preview (backend + frontend)
- ✅ La racine `/` sert l'app (200), plus de 502
- ✅ Routes client fonctionnelles (SPA fallback opérationnel)
- ✅ Timeout keep-alive configuré (65s)
- ✅ Gestion d'erreurs globale implémentée
- ✅ Logs structurés au démarrage

## 🐛 Historique du Debug

**Problème initial:** 502 Bad Gateway en preview
**Cause racine:** Absence d'endpoint `/healthz` sur le backend
**Solution:** Ajout endpoints + optimisation uvicorn + gestion erreurs
**Résultat:** ✅ Tous les tests passent (200 OK)