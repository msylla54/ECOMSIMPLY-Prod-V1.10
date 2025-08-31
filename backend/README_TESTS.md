# 🧪 Guide Tests & Qualité - ECOMSIMPLY Backend

## 📋 Vue d'ensemble

Ce guide présente l'environnement de tests et de qualité mis en place pour le backend ECOMSIMPLY.

## 🛠️ Outils installés

### Tests
- **pytest** - Framework de test principal
- **pytest-asyncio** - Support tests asynchrones
- **pytest-cov** - Coverage des tests
- **freezegun** - Mock des dates/heures
- **respx** - Mock des requêtes HTTP
- **faker** - Génération de données de test

### Qualité de code
- **ruff** - Linter et formateur moderne (remplace flake8, black, isort)
- **mypy** - Vérification des types Python
- **coverage** - Mesure de couverture de code
- **pre-commit** - Hooks de pre-commit

## 📁 Structure des tests

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Configuration globale des tests
│   ├── test_basic.py        # Tests de base
│   └── test_health.py       # Tests d'API de santé
├── pytest.ini              # Configuration pytest
├── ruff.toml               # Configuration ruff
├── mypy.ini                # Configuration mypy
├── .coveragerc             # Configuration coverage
├── Makefile                # Commandes make
└── scripts/ci.sh           # Script CI local
```

## 🚀 Commandes disponibles

### Via Makefile

```bash
# Tests
make test                    # Exécuter les tests
make test-verbose           # Tests en mode verbeux
make test-coverage          # Tests avec coverage
make test-html              # Générer rapport HTML

# Qualité
make lint                   # Vérifier le code avec ruff
make lint-fix              # Corriger automatiquement
make format                # Formater le code
make typecheck             # Vérifier les types avec mypy

# Pipeline complet
make ci                    # Pipeline CI complète
make ci-fast              # Pipeline CI rapide

# Utilitaires
make help                 # Afficher l'aide
make clean               # Nettoyer les fichiers temporaires
```

### Via script CI

```bash
# Modes d'exécution
./scripts/ci.sh              # Pipeline complète
./scripts/ci.sh fast         # Pipeline rapide
./scripts/ci.sh lint-only    # Lint seulement
./scripts/ci.sh test-only    # Tests seulement
```

### Commandes directes

```bash
# Tests
pytest tests/test_basic.py tests/test_health.py -q
pytest --cov=. --cov-report=html

# Qualité
ruff check .
ruff format .
mypy .
```

## 📊 Configuration pytest

### Fichier pytest.ini
- Coverage minimum : 80% 
- Mode asyncio strict
- Rapports HTML et XML automatiques
- Markers personnalisés : `unit`, `integration`, `api`, `slow`

### Marqueurs de tests

```python
@pytest.mark.unit           # Test unitaire
@pytest.mark.integration    # Test d'intégration  
@pytest.mark.api           # Test d'API
@pytest.mark.slow          # Test lent
```

### Exécution par type

```bash
pytest -m "unit"           # Seulement les tests unitaires
pytest -m "integration"    # Seulement les tests d'intégration
pytest -m "not slow"       # Exclure les tests lents
```

## 🎯 Fixtures disponibles

### Dans conftest.py

```python
# Clients de test
client                 # Client FastAPI synchrone
async_client          # Client FastAPI asynchrone

# Base de données
test_db               # Base MongoDB de test

# Données de test
sample_user_data      # Données utilisateur
sample_product_data   # Données produit
sample_subscription_data  # Données abonnement

# Mocks
mock_stripe_client    # Mock Stripe
mock_openai_client    # Mock OpenAI

# Auth
auth_headers          # Headers d'authentification
```

## 📈 Coverage

### Rapports générés
- **Terminal** : Résumé avec lignes manquantes
- **HTML** : `htmlcov/index.html` - Rapport détaillé
- **XML** : `coverage.xml` - Compatible CI/CD

### Configuration
- Exclusions : tests, __pycache__, venv
- Seuil minimum : 80%
- Branches incluses

## ⚙️ Configuration Ruff

### Règles activées
- **E, W** : pycodestyle errors/warnings
- **F** : pyflakes  
- **I** : isort (imports)
- **B** : flake8-bugbear
- **C4** : flake8-comprehensions
- **UP** : pyupgrade
- **S** : flake8-bandit (sécurité)
- **PT** : flake8-pytest-style

### Configuration spéciale
- Tests : `assert` autorisé
- Line length : 88 caractères
- Quote style : double quotes

## 🔍 Configuration MyPy

### Mode strict raisonnable
- Types obligatoires sur les fonctions
- Vérification des imports
- Warnings sur unused/redundant
- Configuration par module pour les tests

### Modules tiers ignorés
- pymongo, motor, emergentintegrations
- fal_client, woocommerce, selenium
- Autres dépendances sans stubs

## 🔄 Pipeline CI

### Étapes du pipeline complet
1. **Installation** des dépendances
2. **Format check** avec ruff
3. **Lint** avec ruff
4. **Type check** avec mypy
5. **Tests** avec pytest + coverage

### Pipeline rapide
- Format + Lint + Types + Tests (sans coverage)

## 📝 Exemple de test

```python
# test_example.py
import pytest
from fastapi.testclient import TestClient

@pytest.mark.api
def test_health_endpoint(client: TestClient):
    """Test l'endpoint de santé."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

@pytest.mark.asyncio
async def test_async_function():
    """Test asynchrone."""
    result = await some_async_function()
    assert result == "expected"

@pytest.mark.unit  
def test_unit_example(sample_user_data):
    """Test unitaire avec fixture."""
    user = create_user(sample_user_data)
    assert user.email == sample_user_data["email"]
```

## 🚦 Status actuel

### ✅ Tests qui passent
- `test_basic.py` : 7 tests de base
- `test_health.py` : 2 tests d'API

### 📊 Coverage
- **Total** : 23% (sera amélioré avec plus de tests)
- **Services testés** : health, logging (partiellement)

### 🎯 Prochaines étapes
1. Ajouter tests pour les endpoints principaux
2. Tests d'intégration avec MongoDB
3. Tests des services métier
4. Mocks plus complets pour Stripe/OpenAI
5. Tests de performance

## 🔧 Développement

### Pre-commit hooks (optionnel)
```bash
pip install pre-commit
pre-commit install
```

### Workflow recommandé
1. Écrire les tests en premier (TDD)
2. Implémenter le code
3. Vérifier avec `make ci-fast`
4. Commit + push

### Debugging tests
```bash
pytest -v -s tests/test_basic.py::test_specific  # Test spécifique
pytest --pdb                                     # Debugger intégré
pytest --lf                                      # Seulement les tests qui ont échoué
```

---

**🎉 Environnement de tests et qualité opérationnel !**

L'infrastructure est en place pour un développement robuste avec des tests automatisés et une qualité de code élevée.