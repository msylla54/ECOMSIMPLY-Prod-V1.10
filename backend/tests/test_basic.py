"""
Tests de base pour vérifier la configuration
"""

import pytest
from fastapi.testclient import TestClient


def test_configuration():
    """Test que la configuration est correcte."""
    assert True


def test_basic_math():
    """Test mathématique simple."""
    assert 2 + 2 == 4


@pytest.mark.asyncio
async def test_async_basic():
    """Test asynchrone basique."""
    result = await async_function()
    assert result == "test"


async def async_function():
    """Fonction async de test."""
    return "test"


def test_client_creation(client: TestClient):
    """Test la création du client de test."""
    assert client is not None


@pytest.mark.unit
def test_unit_example():
    """Exemple de test unitaire."""
    assert len("hello") == 5


@pytest.mark.integration
def test_integration_example():
    """Exemple de test d'intégration."""
    assert True


@pytest.mark.api
def test_api_example():
    """Exemple de test d'API."""
    assert True
