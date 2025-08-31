# ECOMSIMPLY - Guide de Déploiement Production

## 🚀 Déploiement Rapide

### Prérequis
- Docker et Docker Compose installés
- 4GB RAM minimum
- 20GB d'espace disque
- Ports 80, 443, 3000, 8001, 9090, 3001 disponibles

### 1. Configuration Initiale

```bash
# Cloner/copier les fichiers
git clone <votre-repo> ecomsimply
cd ecomsimply

# Copier et configurer les variables d'environnement
cp .env.template .env
nano .env  # Remplir toutes les valeurs nécessaires
```

### 2. Variables d'Environnement Critiques

⚠️ **OBLIGATOIRE** - Ces valeurs doivent être modifiées :

```bash
# Sécurité (CRITIQUE)
JWT_SECRET="your_64_char_secure_jwt_secret_here"
MONGO_ROOT_PASSWORD="your_secure_mongodb_password"
REDIS_PASSWORD="your_secure_redis_password"

# API Keys
OPENAI_API_KEY="your_production_openai_key"
STRIPE_API_KEY="your_production_stripe_key"
FAL_KEY="your_production_fal_key"

# URLs
REACT_APP_BACKEND_URL="https://api.yourdomain.com"
```

### 3. Génération des Secrets Sécurisés

```python
# Générer JWT_SECRET
import secrets
print("JWT_SECRET=" + secrets.token_urlsafe(32))

# Générer ENCRYPTION_KEY
from cryptography.fernet import Fernet
print("ENCRYPTION_KEY=" + Fernet.generate_key().decode())
```

### 4. Déploiement

```bash
# Lancer le déploiement
./scripts/deploy.sh production

# Vérifier le statut
docker-compose ps
curl http://localhost:8001/api/health
```

## 🔧 Configuration SSL (Production)

### 1. Certificats SSL

```bash
# Créer le dossier SSL
mkdir -p ssl

# Copier vos certificats
cp your-cert.pem ssl/cert.pem
cp your-key.pem ssl/key.pem

# Ou générer des certificats auto-signés (développement uniquement)
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes
```

### 2. Configuration DNS

Configurez votre DNS pour pointer vers votre serveur :
- `yourdomain.com` → IP de votre serveur
- `api.yourdomain.com` → IP de votre serveur (optionnel)

## 📊 Monitoring et Maintenance

### Endpoints de Monitoring

- **Health Check**: `GET /api/health`
- **Readiness**: `GET /api/health/ready`
- **Liveness**: `GET /api/health/live`
- **Metrics**: `GET /api/metrics`

### Services de Monitoring

- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090

### Logs

```bash
# Logs des conteneurs
docker-compose logs -f backend
docker-compose logs -f frontend

# Logs dans les fichiers
tail -f logs/ecomsimply_*.log
```

### Backup

```bash
# Backup manuel
./scripts/backup.sh

# Configurer un cron job pour backup automatique
0 2 * * * /path/to/ecomsimply/scripts/backup.sh
```

## 🔒 Sécurité

### 1. Configuration du Firewall

```bash
# UFW (Ubuntu)
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw enable

# Bloquer les ports internes
ufw deny 8001   # Backend direct
ufw deny 27017  # MongoDB
ufw deny 6379   # Redis
```

### 2. Configuration Nginx (Recommandée)

Utilisez Nginx comme reverse proxy pour :
- Terminaison SSL
- Rate limiting
- Load balancing
- Compression

### 3. Authentification Renforcée

- Changez tous les mots de passe par défaut
- Activez l'authentification 2FA où possible
- Utilisez des clés SSH pour l'accès serveur

## 🚨 Dépannage

### Problèmes Courants

1. **Service ne démarre pas**
```bash
docker-compose logs <service>
sudo supervisorctl status
```

2. **Problèmes de base de données**
```bash
docker exec -it ecomsimply_mongodb mongosh
```

3. **Problèmes de certificats SSL**
```bash
openssl x509 -in ssl/cert.pem -text -noout
```

4. **Vérification des endpoints**
```bash
curl -f http://localhost:8001/api/health || echo "Backend issue"
curl -f http://localhost:3000/health || echo "Frontend issue"
```

### Contacts de Support

- Logs d'erreur : `/var/log/ecomsimply_*.log`
- Monitoring : Grafana dashboard
- Health checks : Vérifier `/api/health` régulièrement

## 🎯 Performance

### Optimisations Recommandées

1. **Base de données**
   - Indexes MongoDB appropriés
   - Connection pooling configuré
   - Backup réguliers

2. **Cache**
   - Redis configuré et fonctionnel
   - TTL appropriés pour les données

3. **Frontend**
   - Compression gzip activée
   - Cache des assets statiques
   - CDN pour les ressources (optionnel)

4. **Monitoring**
   - Alertes configurées dans Grafana
   - Logs structurés et analysés
   - Métriques système surveillées

## ✅ Checklist de Production

- [ ] Toutes les variables d'environnement configurées
- [ ] Secrets sécurisés générés et appliqués
- [ ] SSL/TLS configuré et testé
- [ ] DNS configuré correctement
- [ ] Firewall configuré
- [ ] Backup automatique configuré
- [ ] Monitoring actif (Grafana/Prometheus)
- [ ] Health checks fonctionnels
- [ ] Tests de charge effectués
- [ ] Documentation mise à jour
- [ ] Équipe formée sur l'exploitation

---

**⚠️ Important**: Ce guide assume une installation sur un serveur dédié. Pour un déploiement cloud (AWS, GCP, Azure), des configurations supplémentaires peuvent être nécessaires.