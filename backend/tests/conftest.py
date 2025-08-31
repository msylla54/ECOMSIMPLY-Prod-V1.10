"""
Configuration des tests pour le backend ECOMSIMPLY
"""
import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from faker import Faker

# Import des modules du projet
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from server import app

# Configuration Faker
fake = Faker('fr_FR')

# Configuration de l'event loop pour les tests asyncio
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Créer un event loop pour les tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Client de test synchrone
@pytest.fixture
def client() -> TestClient:
    """Client de test FastAPI synchrone."""
    return TestClient(app)

# Client de test asynchrone
@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Client de test FastAPI asynchrone."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# Base de données de test
@pytest_asyncio.fixture
async def test_db():
    """Base de données MongoDB de test."""
    # Utiliser une DB de test
    test_db_name = f"ecomsimply_test_{fake.uuid4()[:8]}"
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client[test_db_name]
    
    yield db
    
    # Nettoyage après les tests
    await client.drop_database(test_db_name)
    client.close()

# Fixtures pour les données de test
@pytest.fixture
def sample_user_data():
    """Données utilisateur de test."""
    return {
        "email": fake.email(),
        "password": fake.password(length=12),
        "name": fake.name(),
        "is_admin": False,
        "subscription_plan": "gratuit",
        "subscription_status": "active"
    }

@pytest.fixture
def sample_product_data():
    """Données produit de test."""
    return {
        "name": fake.catch_phrase(),
        "description": fake.text(max_nb_chars=200),
        "price": fake.pyfloat(positive=True, max_value=1000, right_digits=2),
        "category": fake.word(),
        "brand": fake.company(),
        "sku": fake.bothify(text='SKU-########'),
        "weight": fake.pyfloat(positive=True, max_value=10, right_digits=2),
        "dimensions": {
            "length": fake.pyfloat(positive=True, max_value=100, right_digits=1),
            "width": fake.pyfloat(positive=True, max_value=100, right_digits=1),
            "height": fake.pyfloat(positive=True, max_value=100, right_digits=1)
        }
    }

@pytest.fixture
def sample_subscription_data():
    """Données d'abonnement de test."""
    return {
        "user_id": fake.uuid4(),
        "plan": fake.random_element(["gratuit", "pro", "premium"]),
        "status": "active",
        "stripe_subscription_id": fake.bothify(text='sub_########'),
        "current_period_start": fake.date_time_this_month(),
        "current_period_end": fake.date_time_this_month(),
        "trial_used": fake.boolean()
    }

# Mocks pour les services externes
@pytest.fixture
def mock_stripe_client():
    """Mock du client Stripe."""
    class MockStripeClient:
        def __init__(self):
            self.subscriptions = MockSubscriptions()
            self.customers = MockCustomers()
            self.checkout = MockCheckout()
    
    class MockSubscriptions:
        def create(self, **kwargs):
            return {"id": fake.bothify(text='sub_########'), **kwargs}
        
        def retrieve(self, subscription_id):
            return {"id": subscription_id, "status": "active"}
    
    class MockCustomers:
        def create(self, **kwargs):
            return {"id": fake.bothify(text='cus_########'), **kwargs}
    
    class MockCheckout:
        def __init__(self):
            self.sessions = MockCheckoutSessions()
    
    class MockCheckoutSessions:
        def create(self, **kwargs):
            return {
                "id": fake.bothify(text='cs_########'),
                "url": fake.url(),
                **kwargs
            }
    
    return MockStripeClient()

@pytest.fixture
def mock_openai_client():
    """Mock du client OpenAI."""
    class MockOpenAIClient:
        def chat_completions_create(self, **kwargs):
            return {
                "choices": [
                    {
                        "message": {
                            "content": fake.text(max_nb_chars=500)
                        }
                    }
                ]
            }
    
    return MockOpenAIClient()

# Variables d'environnement pour les tests
@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Configuration des variables d'environnement pour les tests."""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("MONGO_URL", "mongodb://localhost:27017")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-openai-key-for-testing")

# Fixtures pour les headers d'authentification
@pytest.fixture
def auth_headers(sample_user_data):
    """Headers d'authentification pour les tests."""
    # Créer un token JWT fictif pour les tests
    token = "fake-jwt-token-for-testing"
    return {"Authorization": f"Bearer {token}"}

# Fixture pour nettoyer les effets de bord
@pytest.fixture
def cleanup_after_test():
    """Nettoyage automatique après chaque test."""
    yield
    # Ici on peut ajouter du nettoyage si nécessaire
    pass

# Configuration des markers pytest
def pytest_configure(config):
    """Configuration des markers personnalisés."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )