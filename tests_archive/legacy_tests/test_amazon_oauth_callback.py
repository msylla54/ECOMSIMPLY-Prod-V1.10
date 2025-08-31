#!/usr/bin/env python3
"""
Tests pour la gestion du callback OAuth Amazon avec génération automatique du refresh token

Tests Unitaires:
- Validation code → refresh_token
- Chiffrement/déchiffrement des tokens en base
- Vérification CSRF avec OAuth state
- Gestion des erreurs et exceptions

Tests d'Intégration:
- /connect → callback → status retourne connected
- Flow complet OAuth avec mock Amazon LWA
- Persistance et récupération des tokens chiffrés
"""

import pytest
import asyncio
import os
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient

# Import du système à tester
import sys
sys.path.append('/app/backend')

from services.amazon_connection_service import AmazonConnectionService
from services.amazon_oauth_service import AmazonOAuthService
from services.amazon_encryption_service import AmazonTokenEncryptionService
from models.amazon_spapi import (
    AmazonConnection, ConnectionStatus, SPAPITokenData, SPAPIRegion
)
from routes.amazon_routes import amazon_router
from server import app


class TestAmazonOAuthCallback:
    """Tests complets pour le callback OAuth Amazon"""
    
    @pytest.fixture
    async def db_client(self):
        """Client MongoDB de test"""
        client = AsyncIOMotorClient("mongodb://localhost:27017")
        db = client.test_ecomsimply_oauth
        
        # Nettoyer avant les tests
        await db.amazon_connections.delete_many({})
        
        yield db
        
        # Nettoyer après les tests
        await db.amazon_connections.delete_many({})
        await client.close()
    
    @pytest.fixture
    def mock_oauth_service(self):
        """Service OAuth mocké"""
        service = Mock(spec=AmazonOAuthService)
        
        # Mock token data successful
        mock_token_data = SPAPITokenData(
            access_token="sp_access_token_123",
            refresh_token="sp_refresh_token_456",
            token_type="bearer",
            expires_in=3600,
            expires_at=datetime.utcnow() + timedelta(hours=1),
            scope="sellingpartnerapi::migration"
        )
        
        service.verify_oauth_state.return_value = True
        service.exchange_code_for_tokens.return_value = mock_token_data
        service.refresh_access_token.return_value = mock_token_data
        
        return service
    
    @pytest.fixture
    def mock_encryption_service(self):
        """Service de chiffrement mocké"""
        service = Mock(spec=AmazonTokenEncryptionService)
        service.kms_key_id = "test-kms-key-id"
        service.encrypt_token_data.return_value = ("encrypted_data_base64", "nonce_base64")
        service.decrypt_token_data.return_value = {
            "access_token": "sp_access_token_123",
            "refresh_token": "sp_refresh_token_456",
            "token_type": "bearer",
            "expires_in": 3600,
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "scope": "sellingpartnerapi::migration"
        }
        return service
    
    @pytest.fixture
    async def connection_service(self, db_client, mock_oauth_service, mock_encryption_service):
        """Service de connexion avec mocks"""
        service = AmazonConnectionService(db_client)
        service.oauth_service = mock_oauth_service
        service.encryption_service = mock_encryption_service
        return service
    
    # Tests Unitaires
    
    @pytest.mark.asyncio
    async def test_oauth_state_verification_success(self, connection_service):
        """Test: Vérification OAuth state réussie (protection CSRF)"""
        
        # Créer une connexion en attente
        connection_id = "test-connection-123"
        user_id = "test-user-456"
        oauth_state = "test-oauth-state-789"
        
        connection_doc = {
            "id": connection_id,
            "user_id": user_id,
            "marketplace_id": "A13V1IB3VIYZZH",
            "region": SPAPIRegion.EU,
            "status": ConnectionStatus.PENDING,
            "oauth_state": oauth_state,
            "oauth_state_expires": datetime.utcnow() + timedelta(minutes=30),
            "created_at": datetime.utcnow()
        }
        
        await connection_service.db.amazon_connections.insert_one(connection_doc)
        
        # Test du callback
        result = await connection_service.handle_oauth_callback(
            state=oauth_state,
            authorization_code="test-auth-code",
            selling_partner_id="AXXXXXXXXXXXX"
        )
        
        assert result is True
        connection_service.oauth_service.verify_oauth_state.assert_called_once_with(
            oauth_state, user_id, connection_id
        )
    
    @pytest.mark.asyncio
    async def test_oauth_state_verification_failure(self, connection_service):
        """Test: Échec de vérification OAuth state (protection CSRF)"""
        
        # Mock échec de vérification
        connection_service.oauth_service.verify_oauth_state.return_value = False
        
        # Créer une connexion en attente
        connection_doc = {
            "id": "test-connection-123",
            "user_id": "test-user-456",
            "marketplace_id": "A13V1IB3VIYZZH",
            "region": SPAPIRegion.EU,
            "status": ConnectionStatus.PENDING,
            "oauth_state": "test-oauth-state-789",
            "oauth_state_expires": datetime.utcnow() + timedelta(minutes=30),
            "created_at": datetime.utcnow()
        }
        
        await connection_service.db.amazon_connections.insert_one(connection_doc)
        
        # Test du callback
        result = await connection_service.handle_oauth_callback(
            state="test-oauth-state-789",
            authorization_code="test-auth-code",
            selling_partner_id="AXXXXXXXXXXXX"
        )
        
        assert result is False
        
        # Vérifier que la connexion est marquée en erreur
        connection = await connection_service.db.amazon_connections.find_one(
            {"id": "test-connection-123"}
        )
        assert connection["status"] == ConnectionStatus.ERROR
        assert "CSRF validation failed" in connection["error_message"]
    
    @pytest.mark.asyncio
    async def test_token_exchange_and_encryption(self, connection_service):
        """Test: Échange code → refresh_token et chiffrement"""
        
        # Créer une connexion en attente
        connection_doc = {
            "id": "test-connection-123",
            "user_id": "test-user-456",
            "marketplace_id": "A13V1IB3VIYZZH",
            "region": SPAPIRegion.EU,
            "status": ConnectionStatus.PENDING,
            "oauth_state": "test-oauth-state-789",
            "oauth_state_expires": datetime.utcnow() + timedelta(minutes=30),
            "created_at": datetime.utcnow()
        }
        
        await connection_service.db.amazon_connections.insert_one(connection_doc)
        
        # Test du callback
        result = await connection_service.handle_oauth_callback(
            state="test-oauth-state-789",
            authorization_code="test-auth-code",
            selling_partner_id="AXXXXXXXXXXXX"
        )
        
        assert result is True
        
        # Vérifier l'échange de tokens
        connection_service.oauth_service.exchange_code_for_tokens.assert_called_once_with(
            authorization_code="test-auth-code",
            region=SPAPIRegion.EU
        )
        
        # Vérifier le chiffrement
        connection_service.encryption_service.encrypt_token_data.assert_called_once()
        
        # Vérifier la mise à jour en base
        connection = await connection_service.db.amazon_connections.find_one(
            {"id": "test-connection-123"}
        )
        
        assert connection["status"] == ConnectionStatus.ACTIVE
        assert connection["seller_id"] == "AXXXXXXXXXXXX"
        assert connection["encrypted_refresh_token"] == "encrypted_data_base64"
        assert connection["token_encryption_nonce"] == "nonce_base64"
        assert connection["oauth_state"] is None  # Effacé après usage
    
    @pytest.mark.asyncio
    async def test_missing_refresh_token_error(self, connection_service):
        """Test: Erreur si refresh_token manquant dans la réponse LWA"""
        
        # Mock token data sans refresh_token
        mock_token_data = SPAPITokenData(
            access_token="sp_access_token_123",
            refresh_token="",  # Refresh token manquant
            token_type="bearer",
            expires_in=3600,
            expires_at=datetime.utcnow() + timedelta(hours=1),
            scope="sellingpartnerapi::migration"
        )
        
        connection_service.oauth_service.exchange_code_for_tokens.return_value = mock_token_data
        
        # Créer une connexion en attente
        connection_doc = {
            "id": "test-connection-123",
            "user_id": "test-user-456",
            "marketplace_id": "A13V1IB3VIYZZH",
            "region": SPAPIRegion.EU,
            "status": ConnectionStatus.PENDING,
            "oauth_state": "test-oauth-state-789",
            "oauth_state_expires": datetime.utcnow() + timedelta(minutes=30),
            "created_at": datetime.utcnow()
        }
        
        await connection_service.db.amazon_connections.insert_one(connection_doc)
        
        # Test du callback
        result = await connection_service.handle_oauth_callback(
            state="test-oauth-state-789",
            authorization_code="test-auth-code",
            selling_partner_id="AXXXXXXXXXXXX"
        )
        
        assert result is False
        
        # Vérifier que la connexion est marquée en erreur
        connection = await connection_service.db.amazon_connections.find_one(
            {"id": "test-connection-123"}
        )
        assert connection["status"] == ConnectionStatus.ERROR
        assert "Missing refresh token" in connection["error_message"]
    
    @pytest.mark.asyncio
    async def test_automatic_refresh_token_usage(self, connection_service):
        """Test: Utilisation automatique du refresh token pour renouveler l'access token"""
        
        # Créer une connexion active avec token expiré
        expired_time = datetime.utcnow() - timedelta(minutes=30)
        connection_doc = {
            "id": "test-connection-123",
            "user_id": "test-user-456",
            "marketplace_id": "A13V1IB3VIYZZH",
            "region": SPAPIRegion.EU,
            "status": ConnectionStatus.ACTIVE,
            "seller_id": "AXXXXXXXXXXXX",
            "encrypted_refresh_token": "encrypted_data_base64",
            "token_encryption_nonce": "nonce_base64",
            "encryption_key_id": "test-kms-key-id",
            "created_at": datetime.utcnow(),
            "connected_at": datetime.utcnow()
        }
        
        await connection_service.db.amazon_connections.insert_one(connection_doc)
        
        connection = AmazonConnection(**connection_doc)
        
        # Mock token data expiré
        expired_token_data = {
            "access_token": "expired_token",
            "refresh_token": "sp_refresh_token_456",
            "token_type": "bearer",
            "expires_in": 3600,
            "expires_at": expired_time,  # Token expiré
            "scope": "sellingpartnerapi::migration"
        }
        
        connection_service.encryption_service.decrypt_token_data.return_value = expired_token_data
        
        # Test de récupération d'un token valide
        access_token = await connection_service.get_valid_access_token(connection)
        
        assert access_token == "sp_access_token_123"
        
        # Vérifier que le refresh a été appelé
        connection_service.oauth_service.refresh_access_token.assert_called_once_with(
            refresh_token="sp_refresh_token_456",
            region=SPAPIRegion.EU
        )
        
        # Vérifier que les nouveaux tokens sont re-chiffrés et stockés
        connection_service.encryption_service.encrypt_token_data.assert_called()
    
    # Tests d'Intégration
    
    @pytest.mark.asyncio
    async def test_full_oauth_flow_integration(self, connection_service):
        """Test d'intégration: /connect → callback → status retourne connected"""
        
        user_id = "test-user-integration"
        
        # 1. Créer une connexion (simuler /connect)
        connection_result = await connection_service.create_connection(
            user_id=user_id,
            marketplace_id="A13V1IB3VIYZZH",
            region=SPAPIRegion.EU
        )
        
        connection_id = connection_result["connection_id"]
        oauth_state = connection_result["state"]
        
        # 2. Traiter le callback OAuth
        callback_success = await connection_service.handle_oauth_callback(
            state=oauth_state,
            authorization_code="integration-auth-code",
            selling_partner_id="INTEGRATION-SELLER"
        )
        
        assert callback_success is True
        
        # 3. Vérifier le status de connexion
        connections = await connection_service.get_user_connections(user_id)
        
        assert len(connections) == 1
        assert connections[0].status == ConnectionStatus.ACTIVE
        assert connections[0].seller_id == "INTEGRATION-SELLER"
        assert connections[0].connection_id == connection_id
    
    def test_callback_endpoint_popup_mode(self):
        """Test d'intégration: endpoint /api/amazon/callback en mode popup"""
        
        client = TestClient(app)
        
        # Simuler un callback réussi en mode popup
        response = client.get("/api/amazon/callback", params={
            "state": "test-state-popup",
            "selling_partner_id": "TEST-SELLER",
            "spapi_oauth_code": "test-oauth-code",
            "popup": "true"
        })
        
        # Vérifier la réponse HTML
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        
        # Vérifier le contenu HTML
        html_content = response.text
        assert "Amazon Connecté avec Succès!" in html_content
        assert "postMessage" in html_content
        assert "AMAZON_CONNECTED" in html_content
        assert "window.opener" in html_content
    
    def test_callback_endpoint_redirect_mode(self):
        """Test d'intégration: endpoint /api/amazon/callback en mode redirect"""
        
        client = TestClient(app)
        
        # Simuler un callback réussi en mode redirect
        response = client.get("/api/amazon/callback", params={
            "state": "test-state-redirect",
            "selling_partner_id": "TEST-SELLER",
            "spapi_oauth_code": "test-oauth-code"
            # Pas de paramètre popup = mode redirect
        }, follow_redirects=False)
        
        # Vérifier la redirection 302
        assert response.status_code == 302
        assert "Location" in response.headers
        assert "/dashboard?amazon=connected" in response.headers["Location"]
    
    def test_callback_endpoint_missing_parameters(self):
        """Test d'intégration: endpoint /api/amazon/callback avec paramètres manquants"""
        
        client = TestClient(app)
        
        # Simuler un callback avec paramètres manquants
        response = client.get("/api/amazon/callback", params={
            "state": "test-state",
            # selling_partner_id et spapi_oauth_code manquants
        })
        
        # Vérifier la gestion d'erreur
        assert response.status_code == 200
        if "text/html" in response.headers.get("content-type", ""):
            # Mode popup avec erreur
            assert "Erreur de Connexion Amazon" in response.text
            assert "AMAZON_CONNECTION_ERROR" in response.text
        else:
            # Mode redirect avec erreur
            assert response.status_code == 302
            assert "amazon_error" in response.headers["Location"]


# Configuration pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])