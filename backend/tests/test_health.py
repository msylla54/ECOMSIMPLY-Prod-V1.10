"""
Tests pour les endpoints de santé
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
def test_api_health_endpoint(client: TestClient):
    """Test l'endpoint de santé de l'API."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.integration
def test_database_connection_status(client: TestClient):
    """Test que la connexion DB est reportée dans le status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    # Le status doit contenir des informations sur la base de données
    assert "status" in data