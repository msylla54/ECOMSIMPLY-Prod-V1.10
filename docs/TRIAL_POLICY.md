# TRIAL POLICY - RÈGLE "UN SEUL ESSAI GRATUIT PAR CLIENT"

## 🎯 Vue d'ensemble

Cette documentation détaille l'implémentation de la règle business critique : **"Un seul essai gratuit de 7 jours par client"** dans le système ECOMSIMPLY. Cette règle empêche l'abus des essais gratuits tout en maintenant une expérience utilisateur fluide.

## 🏗️ Architecture de l'éligibilité

### Composants clés

1. **TrialEligibilityService** : Service métier pour vérification d'éligibilité
2. **Endpoint `/subscription/trial-eligibility`** : API de vérification côté serveur
3. **Frontend adaptatif** : Interface qui s'adapte selon l'éligibilité
4. **Stockage multi-critères** : Plusieurs mécanismes de détection

## 🔍 Critères d'éligibilité

### 1. Flag utilisateur (Primaire)
```python
# Dans User model
has_used_trial: bool = False
trial_used_at: Optional[datetime] = None
```

**Logique** :
- Si `has_used_trial = True` → **Non éligible**
- Si `trial_used_at` existe ET < 365 jours → **Non éligible**
- Sinon → **Éligible** (pour ce critère)

### 2. Fingerprint de paiement (Secondaire)
```python
# Collection MongoDB : trial_fingerprints
{
  "fingerprint_hash": "sha256_hash",
  "trial_used": true,
  "used_at": "2024-01-15T10:30:00Z",
  "user_id_hash": "sha256_hash",
  "plan_type": "pro"
}
```

**Logique** :
- Hash sécurisé du `payment_method.fingerprint` Stripe
- Si hash trouvé avec `trial_used: true` → **Non éligible**
- Empêche l'utilisation de la même carte sur différents comptes

### 3. Email normalisé (Détection multi-comptes)
```python
def _hash_email(self, email: str) -> str:
    normalized_email = email.lower().strip()
    return hashlib.sha256(f"email:{normalized_email}".encode()).hexdigest()
```

**Logique** :
- Hash SHA256 de l'email normalisé (minuscules + trim)
- Si hash trouvé avec essai utilisé → **Non éligible**
- Détecte les comptes multiples avec même email

### 4. Limite par IP (Optionnel)
```python
# Collection MongoDB : trial_ip_usage
{
  "ip_hash": "sha256_hash",
  "trial_started_at": "2024-01-15T10:30:00Z",
  "user_id_hash": "sha256_hash",
  "plan_type": "pro"
}
```

**Logique** :
- Maximum 3 essais par IP sur 365 jours (configurable)
- Protection contre les fermes de création de comptes
- Peut être désactivée en définissant `MAX_IP_TRIALS=999`

## ⚙️ Configuration

### Variables d'environnement
```bash
MAX_IP_TRIALS=3                    # Max essais par IP (défaut: 3)
TRIAL_COOLDOWN_DAYS=365           # Cooldown entre essais (défaut: 365)
```

### Collections MongoDB requises
```javascript
// Index pour performance et unicité
db.trial_fingerprints.createIndex({"fingerprint_hash": 1})
db.trial_ip_usage.createIndex({"ip_hash": 1})
db.users.createIndex({"email_hash": 1})
db.users.createIndex({"trial_used_at": 1})
```

## 🔄 Flux d'implémentation

### 1. Vérification d'éligibilité (Frontend)
```javascript
const checkTrialEligibility = async (planType) => {
  const response = await axios.get(`/api/subscription/trial-eligibility`, {
    params: { plan: planType },
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data; // { eligible: boolean, reason: string, message: string }
};
```

### 2. Interface adaptative
```javascript
// Si éligible
<button onClick={() => createSubscription('pro', true)}>
  🎁 Essai gratuit 7 jours
</button>

// Si non éligible
<>
  <p>Essai gratuit déjà utilisé</p>
  <button onClick={() => createSubscription('pro', false)}>
    💳 Souscrire maintenant (29€/mois)
  </button>
</>
```

### 3. Validation serveur (Critical)
```python
async def create_subscription_checkout(user, request, client_ip, db):
    # TOUJOURS vérifier côté serveur (ne jamais faire confiance au frontend)
    trial_check = await trial_eligibility_service.check_trial_eligibility(
        user=user, plan_type=request.plan_type, client_ip=client_ip, db=db
    )
    
    # Forcer la règle business
    actual_with_trial = request.with_trial and trial_check["eligible"]
    
    # Si essai demandé mais non éligible → Log + Forcer abonnement payant
    if request.with_trial and not trial_check["eligible"]:
        logger.warning(f"Trial requested but not eligible: {trial_check['reason']}")
        actual_with_trial = False
    
    # Créer session Stripe SANS trial_period_days si non éligible
```

### 4. Enregistrement utilisation
```python
async def handle_checkout_session_completed(event_data, db):
    # Après succès paiement avec essai
    if subscription.trial_end:
        # Enregistrer l'utilisation
        await trial_eligibility_service.record_trial_usage(
            user=user,
            payment_fingerprint=payment_fingerprint,
            client_ip=client_ip,  # Si disponible
            plan_type=plan_type,
            db=db
        )
        
        # Marquer utilisateur
        user.trial_used_at = datetime.utcnow()
        user.has_used_trial = True
```

## 🧪 Tests et validation

### Tests unitaires
```python
async def test_trial_eligibility_false_by_user_flag():
    user.has_used_trial = True
    result = await trial_eligibility_service.check_trial_eligibility(user, PlanType.PRO, db=mock_db)
    assert result["eligible"] == False
    assert result["reason"] == "trial_already_used_legacy"

async def test_trial_eligibility_false_by_fingerprint():
    # Mock fingerprint existant
    mock_db.trial_fingerprints.find_one.return_value = {"fingerprint_hash": "hash123", "trial_used": True}
    result = await trial_eligibility_service.check_trial_eligibility(user, PlanType.PRO, payment_fingerprint="test", db=mock_db)
    assert result["eligible"] == False
```

### Tests E2E
```python
async def test_user_non_eligible_is_routed_to_paid_checkout():
    # Mock API pour utilisateur non éligible
    await page.route("**/trial-eligibility*", lambda route: route.fulfill(
        json={"eligible": False, "reason": "trial_already_used"}
    ))
    
    # Vérifier que le bouton "Essai gratuit" n'est PAS visible
    trial_button = page.locator('button:has-text("Essai gratuit")')
    await pytest.raises(TimeoutError, lambda: trial_button.wait_for(timeout=3000))
    
    # Vérifier que "Souscrire maintenant" EST visible
    subscribe_button = page.locator('button:has-text("Souscrire maintenant")')
    await subscribe_button.wait_for(state="visible")
```

## 🔐 Sécurité et anti-contournement

### 1. Hashage sécurisé
```python
def _hash_email(self, email: str) -> str:
    # Normalisation pour éviter contournement avec espaces/casse
    normalized = email.lower().strip()
    return hashlib.sha256(f"email:{normalized}".encode()).hexdigest()

def _hash_fingerprint(self, fingerprint: str) -> str:
    return hashlib.sha256(f"fingerprint:{fingerprint}".encode()).hexdigest()
```

### 2. Protection données sensibles
- ❌ Jamais d'emails en clair dans les logs
- ❌ Jamais d'IPs complètes stockées
- ❌ Jamais d'IDs utilisateur en clair dans les métriques
- ✅ Hashes tronqués pour corrélation (`hash[:8]...`)

### 3. Validation double (Frontend + Backend)
```python
# Frontend : UX fluide
if (!eligibilityCheck.eligible) {
  showPaidSubscriptionOptions();
}

# Backend : Sécurité absolue (TOUJOURS)
actual_with_trial = request.with_trial and trial_check["eligible"]
```

## 📊 Monitoring et métriques

### Métriques business
```python
# Dans les logs structurés (sans PII)
"trial_eligibility_check": {
    "eligible": false,
    "reason": "trial_already_used",
    "plan_type": "pro",
    "checks_performed": 4
}

"trial_blocked": {
    "reason": "payment_fingerprint_already_used",
    "plan_type": "premium",
    "user_hash": "a1b2c3d4..."
}
```

### Statistiques d'usage
```python
async def get_trial_statistics(db):
    return {
        "recent_trials_30d": 150,        # Nouveaux essais
        "blocked_fingerprints": 45,      # Tentatives par fingerprint
        "limited_ips": 12,              # IPs ayant atteint limite
        "blocked_attempts_30d": 89      # Tentatives bloquées
    }
```

## 🛠️ Cas d'usage et gestion des exceptions

### Cas 1: Utilisateur légitime, nouvelle carte
- **Situation** : Client change de carte bancaire
- **Comportement** : Nouveau fingerprint → Éligible si pas d'autre critère bloquant
- **Action** : Autoriser essai

### Cas 2: Famille avec IP partagée
- **Situation** : Plusieurs membres famille sur même IP
- **Comportement** : Limite IP peut bloquer après 3 essais
- **Action** : Support client peut augmenter `MAX_IP_TRIALS` temporairement

### Cas 3: Utilisateur crée nouveau compte (même email)
- **Situation** : Tentative contournement avec même email
- **Comportement** : Hash email détecte → Non éligible
- **Action** : Proposer abonnement direct

### Cas 4: Erreur technique pendant vérification
- **Situation** : DB inaccessible, service en panne
- **Comportement** : Fail-safe → Considérer non éligible
- **Action** : Proposer abonnement direct + Log erreur

## 🔄 Migration et déploiement

### Phase 1: Déploiement avec flag de fonctionnalité
```python
TRIAL_POLICY_ENABLED = os.getenv("TRIAL_POLICY_ENABLED", "false").lower() == "true"

if TRIAL_POLICY_ENABLED:
    # Nouvelle logique strict
else:
    # Ancienne logique (transition)
```

### Phase 2: Migration des données existantes
```python
# Migrer users existants avec essai utilisé
await db.users.update_many(
    {"has_used_trial": True, "trial_used_at": {"$exists": False}},
    {"$set": {"trial_used_at": datetime.utcnow()}}
)

# Créer hashs emails pour users existants
users_to_migrate = await db.users.find({"email_hash": {"$exists": False}})
for user in users_to_migrate:
    email_hash = hash_email(user["email"])
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"email_hash": email_hash}}
    )
```

### Phase 3: Activation complète
```bash
# Variables d'environnement production
TRIAL_POLICY_ENABLED=true
MAX_IP_TRIALS=3
TRIAL_COOLDOWN_DAYS=365
```

## 🎯 Mesures de succès

### KPIs à suivre
1. **Taux de conversion essai → payant** : >25%
2. **Réduction des créations comptes multiples** : -80%
3. **Taux d'abus détectés** : <2%
4. **Satisfaction client** : Maintenir >4.5/5

### Alertes business
```python
# Si trop d'essais bloqués (possible problème)
if blocked_trials_rate > 30%:
    alert("High trial blocking rate - investigate")

# Si pas assez d'essais bloqués (possible contournement)  
if blocked_trials_rate < 5%:
    alert("Low trial blocking rate - verify policy")
```

---

## ✅ Résumé

La règle "Un seul essai gratuit par client" est implémentée avec :

- 🔒 **4 critères de vérification** (utilisateur, fingerprint, email, IP)
- 🛡️ **Validation serveur obligatoire** (pas de confiance frontend)
- 🔐 **Hashage sécurisé** de toutes les données sensibles
- 🎯 **UX adaptive** selon l'éligibilité
- 📊 **Monitoring complet** sans PII
- 🧪 **Tests exhaustifs** (unit, integration, E2E)

**Cette implémentation empêche efficacement l'abus des essais gratuits tout en maintenant une expérience utilisateur de qualité.**