# Makefile pour le backend ECOMSIMPLY
.PHONY: help install test lint format typecheck cov clean ci dev

# Configuration
PYTHON := python3
PIP := pip3
RUFF := ruff
MYPY := mypy
PYTEST := pytest

help: ## Afficher l'aide
	@echo "Commandes disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Installer les dépendances
	$(PIP) install -r requirements.txt

test: ## Exécuter les tests
	$(PYTEST) tests/test_basic.py tests/test_health.py -q

test-verbose: ## Exécuter les tests en mode verbeux
	$(PYTEST) tests/test_basic.py tests/test_health.py -v

test-coverage: ## Exécuter les tests avec coverage
	$(PYTEST) tests/test_basic.py tests/test_health.py --cov=. --cov-report=term-missing

test-html: ## Générer le rapport de coverage HTML
	$(PYTEST) tests/test_basic.py tests/test_health.py --cov=. --cov-report=html
	@echo "Rapport disponible dans htmlcov/index.html"

lint: ## Vérifier le code avec ruff
	$(RUFF) check .

lint-fix: ## Corriger automatiquement les erreurs ruff
	$(RUFF) check . --fix

format: ## Formater le code avec ruff
	$(RUFF) format .

format-check: ## Vérifier le formatage sans modifier
	$(RUFF) format . --check

typecheck: ## Vérifier les types avec mypy
	$(MYPY) .

quality: lint typecheck ## Vérifier la qualité du code (lint + types)

ci: ## Pipeline CI complète
	@echo "🚀 Démarrage du pipeline CI..."
	@echo "📦 Installation des dépendances..."
	$(MAKE) install
	@echo "🎨 Vérification du formatage..."
	$(RUFF) format . --check
	@echo "🔍 Analyse du code..."
	$(RUFF) check .
	@echo "🔎 Vérification des types..."
	$(MYPY) .
	@echo "🧪 Exécution des tests..."
	$(PYTEST) tests/test_basic.py tests/test_health.py --maxfail=1 --disable-warnings --cov=.
	@echo "✅ Pipeline CI terminée avec succès!"

ci-fast: ## Pipeline CI rapide (sans coverage)
	@echo "🚀 Pipeline CI rapide..."
	$(RUFF) format . --check
	$(RUFF) check .
	$(MYPY) .
	$(PYTEST) tests/test_basic.py tests/test_health.py --maxfail=1 --disable-warnings -x
	@echo "✅ Pipeline CI rapide terminée!"

cov: ## Afficher le coverage actuel
	$(PYTEST) tests/test_basic.py tests/test_health.py --cov=. --cov-report=term-missing:skip-covered

clean: ## Nettoyer les fichiers temporaires
	@echo "🧹 Nettoyage..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	@echo "✅ Nettoyage terminé!"

dev: ## Lancer le serveur de développement
	uvicorn server:app --reload --host 0.0.0.0 --port 8001

dev-debug: ## Lancer le serveur avec debug
	uvicorn server:app --reload --host 0.0.0.0 --port 8001 --log-level debug

# Tests par catégorie
test-unit: ## Exécuter seulement les tests unitaires
	$(PYTEST) -m "unit" -q

test-integration: ## Exécuter seulement les tests d'intégration
	$(PYTEST) -m "integration" -q

test-api: ## Exécuter seulement les tests d'API
	$(PYTEST) -m "api" -q

# Développement
watch-test: ## Surveiller les fichiers et relancer les tests
	$(PYTEST) --looponfail

fix: ## Corriger automatiquement le code (format + lint)
	$(RUFF) format .
	$(RUFF) check . --fix

check: ## Vérification complète sans modification
	$(RUFF) format . --check
	$(RUFF) check .
	$(MYPY) .

# Rapports
report: ## Générer tous les rapports
	$(PYTEST) tests/test_basic.py tests/test_health.py --cov=. --cov-report=html --cov-report=xml
	@echo "📊 Rapports générés:"
	@echo "  - Coverage HTML: htmlcov/index.html"
	@echo "  - Coverage XML: coverage.xml"