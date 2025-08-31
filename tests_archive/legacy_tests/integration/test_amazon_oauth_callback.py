"""
Tests d'intégration pour Amazon OAuth Callback
Simulation de callback EU avec mock LWA et cas d'erreurs
"""

import pytest
import asyncio
import sys
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
import os
import jwt
from datetime import datetime, timedelta

# Add backend path for imports
sys.path.append('/app/backend')

# Import du router Amazon
from routes.amazon_routes import amazon_router
from services.amazon_connection_service import AmazonConnectionService
from fastapi import FastAPI

# Configuration de test
TEST_JWT_SECRET = "test_jwt_secret_key_for_testing_only"
TEST_USER_ID = "test_user_12345"
TEST_DB_NAME = "test_ecomsimply"


@pytest.fixture
def test_app():
    """Créer une app FastAPI de test"""
    app = FastAPI()
    app.include_router(amazon_router)
    return app


@pytest.fixture
def test_client(test_app):
    """Client de test FastAPI"""
    return TestClient(test_app)


@pytest.fixture
def auth_token():
    """Token JWT de test valide"""
    payload = {
        'user_id': TEST_USER_ID,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm='HS256')


@pytest.fixture
async def test_db():
    """Base de données de test MongoDB"""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client[TEST_DB_NAME]
    yield db
    # Cleanup
    await client.drop_database(TEST_DB_NAME)
    client.close()


class TestAmazonOAuthCallbackSuccess:
    """Tests de callback OAuth réussis avec génération refresh token"""
    
    @patch.dict(os.environ, {
        'JWT_SECRET': TEST_JWT_SECRET,
        'MONGO_URL': 'mongodb://localhost:27017',
        'DB_NAME': TEST_DB_NAME,
        'AMAZON_LWA_CLIENT_ID': 'test_client_id',
        'AMAZON_LWA_CLIENT_SECRET': 'test_client_secret',
        'APP_BASE_URL': 'https://app.test.com',
        'AMAZON_REDIRECT_URI': 'https://api.test.com/api/amazon/callback'
    })
    @patch('backend.services.amazon_connection_service.AmazonConnectionService.handle_oauth_callback')
    async def test_callback_eu_success_with_refresh_token(self, mock_handle_callback, test_client):
        """Test callback EU avec mock LWA retournant refresh_token"""
        
        # Mock du service de connexion retournant succès
        mock_handle_callback.return_value = True
        
        # Paramètres de callback simulant Amazon EU
        callback_params = {
            'state': 'test_oauth_state_12345',
            'selling_partner_id': 'A2VIGQ35RCS4UG',  # Seller ID EU typique
            'spapi_oauth_code': 'ANcdefghijklmnop1234567890',
            'popup': 'true'
        }
        
        # Appel du callback
        response = test_client.get('/api/amazon/callback', params=callback_params)
        
        # Vérifications
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']
        
        # Vérifier le contenu HTML de succès
        html_content = response.text
        assert 'Amazon Connecté avec Succès!' in html_content
        assert 'tokens ont été générés automatiquement' in html_content
        assert 'AMAZON_CONNECTED' in html_content
        
        # Vérifier que le service a été appelé avec les bons paramètres
        mock_handle_callback.assert_called_once_with(
            state='test_oauth_state_12345',
            authorization_code='ANcdefghijklmnop1234567890',
            selling_partner_id='A2VIGQ35RCS4UG'
        )
    
    @patch.dict(os.environ, {
        'JWT_SECRET': TEST_JWT_SECRET,
        'MONGO_URL': 'mongodb://localhost:27017',
        'DB_NAME': TEST_DB_NAME,
        'AMAZON_LWA_CLIENT_ID': 'test_client_id',
        'AMAZON_LWA_CLIENT_SECRET': 'test_client_secret',
        'APP_BASE_URL': 'https://app.test.com'
    })
    @patch('backend.services.amazon_connection_service.AmazonConnectionService.handle_oauth_callback')
    async def test_callback_redirect_mode_success(self, mock_handle_callback, test_client):
        """Test callback en mode redirect (non-popup)"""
        
        # Mock du service de connexion retournant succès
        mock_handle_callback.return_value = True
        
        # Paramètres de callback sans popup
        callback_params = {
            'state': 'test_oauth_state_67890',
            'selling_partner_id': 'A2VIGQ35RCS4UG',
            'spapi_oauth_code': 'ANzyxwvutsrqponm0987654321'
        }
        
        # Appel du callback
        response = test_client.get('/api/amazon/callback', params=callback_params)
        
        # Vérifications - doit être une redirection 302
        assert response.status_code == 302
        assert 'location' in response.headers
        assert 'amazon=connected' in response.headers['location']
        
        # Vérifier que le service a été appelé
        mock_handle_callback.assert_called_once()


class TestAmazonOAuthCallbackErrors:
    """Tests de gestion d'erreurs du callback OAuth"""
    
    @patch.dict(os.environ, {
        'JWT_SECRET': TEST_JWT_SECRET,
        'MONGO_URL': 'mongodb://localhost:27017',
        'DB_NAME': TEST_DB_NAME,
        'AMAZON_LWA_CLIENT_ID': 'test_client_id',
        'AMAZON_LWA_CLIENT_SECRET': 'test_client_secret',
        'APP_BASE_URL': 'https://app.test.com'
    })
    def test_callback_missing_parameters(self, test_client):
        """Test callback avec paramètres manquants"""
        
        # Paramètres incomplets
        callback_params = {
            'state': 'test_state',
            # 'selling_partner_id': manquant
            'spapi_oauth_code': 'test_code'
        }
        
        # Appel du callback
        response = test_client.get('/api/amazon/callback', params=callback_params)
        
        # Vérifications
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']
        
        # Vérifier le contenu HTML d'erreur
        html_content = response.text
        assert 'Erreur de Connexion Amazon' in html_content
        assert 'Paramètres OAuth manquants' in html_content
        assert 'AMAZON_CONNECTION_ERROR' in html_content
    
    @patch.dict(os.environ, {
        'JWT_SECRET': TEST_JWT_SECRET,
        'MONGO_URL': 'mongodb://localhost:27017',
        'DB_NAME': TEST_DB_NAME,
        'AMAZON_LWA_CLIENT_ID': 'test_client_id',
        'AMAZON_LWA_CLIENT_SECRET': 'test_client_secret',
        'APP_BASE_URL': 'https://app.test.com',
        'AMAZON_REDIRECT_URI': 'https://api.test.com/api/amazon/callback'
    })
    @patch('backend.services.amazon_connection_service.AmazonConnectionService.handle_oauth_callback')
    async def test_callback_redirect_uri_mismatch_error(self, mock_handle_callback, test_client):
        """Test cas d'erreur: mismatch redirect_uri → mock LWA sans refresh_token"""
        
        # Mock du service simulant une erreur LWA (mismatch redirect_uri)
        mock_handle_callback.side_effect = ValueError("Token exchange failed: Invalid redirect_uri")
        
        # Paramètres de callback
        callback_params = {
            'state': 'test_oauth_state_error',
            'selling_partner_id': 'A2VIGQ35RCS4UG',
            'spapi_oauth_code': 'ANerrorcode12345',
            'popup': 'true'
        }
        
        # Appel du callback
        response = test_client.get('/api/amazon/callback', params=callback_params)
        
        # Vérifications
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']
        
        # Vérifier le contenu HTML d'erreur
        html_content = response.text
        assert 'Erreur de Connexion Amazon' in html_content
        assert 'Erreur de validation OAuth' in html_content
        assert 'AMAZON_CONNECTION_ERROR' in html_content
    
    @patch.dict(os.environ, {
        'JWT_SECRET': TEST_JWT_SECRET,
        'MONGO_URL': 'mongodb://localhost:27017',
        'DB_NAME': TEST_DB_NAME,
        'AMAZON_LWA_CLIENT_ID': 'test_client_id',
        'AMAZON_LWA_CLIENT_SECRET': 'test_client_secret',
        'APP_BASE_URL': 'https://app.test.com'
    })
    @patch('backend.services.amazon_connection_service.AmazonConnectionService.handle_oauth_callback')
    async def test_callback_service_failure(self, mock_handle_callback, test_client):
        """Test échec du service de connexion"""
        
        # Mock du service retournant échec
        mock_handle_callback.return_value = False
        
        # Paramètres de callback
        callback_params = {
            'state': 'test_oauth_state_fail',
            'selling_partner_id': 'A2VIGQ35RCS4UG',
            'spapi_oauth_code': 'ANfailcode12345'
        }
        
        # Appel du callback
        response = test_client.get('/api/amazon/callback', params=callback_params)
        
        # Vérifications
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']
        
        # Vérifier le contenu HTML d'erreur
        html_content = response.text
        assert 'Erreur de Connexion Amazon' in html_content
        assert 'Échec du traitement OAuth' in html_content


class TestAmazonConnectionStatus:
    """Tests du statut de connexion après callback"""
    
    @patch.dict(os.environ, {
        'JWT_SECRET': TEST_JWT_SECRET,
        'MONGO_URL': 'mongodb://localhost:27017',
        'DB_NAME': TEST_DB_NAME
    })
    @patch('backend.services.amazon_connection_service.AmazonConnectionService.get_user_connections')
    async def test_status_connected_after_successful_callback(self, mock_get_connections, test_client, auth_token):
        """Test statut 'connected' après callback réussi"""
        
        # Mock de connexions actives
        mock_connection_status = MagicMock()
        mock_connection_status.status = 'active'
        mock_connection_status.connection_id = 'conn_12345'
        mock_connection_status.marketplace_id = 'A13V1IB3VIYZZH'
        mock_connection_status.seller_id = 'A2VIGQ35RCS4UG'
        mock_connection_status.region = 'eu'
        mock_connection_status.connected_at = datetime.utcnow()
        
        mock_get_connections.return_value = [mock_connection_status]
        
        # Appel du statut avec token d'auth
        response = test_client.get(
            '/api/amazon/status',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        # Vérifications
        assert response.status_code == 200
        
        status_data = response.json()
        assert status_data['status'] == 'connected'
        assert status_data['message'] == 'Connexion Amazon active'
        assert status_data['connections_count'] == 1
        assert 'active_connection' in status_data
        assert status_data['active_connection']['connection_id'] == 'conn_12345'
        assert status_data['active_connection']['seller_id'] == 'A2VIGQ35RCS4UG'
    
    @patch.dict(os.environ, {
        'JWT_SECRET': TEST_JWT_SECRET,
        'MONGO_URL': 'mongodb://localhost:27017',
        'DB_NAME': TEST_DB_NAME
    })
    @patch('backend.services.amazon_connection_service.AmazonConnectionService.get_user_connections')
    async def test_status_revoked_after_error(self, mock_get_connections, test_client, auth_token):
        """Test statut 'revoked' après erreur de callback"""
        
        # Mock de connexions révoquées/erreur
        mock_connection_status = MagicMock()
        mock_connection_status.status = 'error'
        mock_connection_status.connection_id = 'conn_error_67890'
        
        mock_get_connections.return_value = [mock_connection_status]
        
        # Appel du statut
        response = test_client.get(
            '/api/amazon/status',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        # Vérifications
        assert response.status_code == 200
        
        status_data = response.json()
        assert status_data['status'] == 'revoked'
        assert status_data['message'] == 'Connexions Amazon expirées ou révoquées'
        assert status_data['connections_count'] == 1


class TestCallbackLogValidation:
    """Tests de validation des logs utiles sans secrets"""
    
    @patch.dict(os.environ, {
        'JWT_SECRET': TEST_JWT_SECRET,
        'MONGO_URL': 'mongodb://localhost:27017',
        'DB_NAME': TEST_DB_NAME,
        'AMAZON_LWA_CLIENT_ID': 'test_client_id',
        'AMAZON_LWA_CLIENT_SECRET': 'test_client_secret',
        'APP_BASE_URL': 'https://app.test.com'
    })
    @patch('backend.routes.amazon_routes.logger')
    @patch('backend.services.amazon_connection_service.AmazonConnectionService.handle_oauth_callback')
    async def test_callback_logs_without_sensitive_data(self, mock_handle_callback, mock_logger, test_client):
        """Test que les logs de callback ne contiennent pas de données sensibles"""
        
        # Mock du service retournant succès
        mock_handle_callback.return_value = True
        
        # Paramètres de callback avec codes sensibles
        callback_params = {
            'state': 'sensitive_state_abcd1234',
            'selling_partner_id': 'A2VIGQ35RCS4UG',
            'spapi_oauth_code': 'ANsensitivecode567890',
            'popup': 'true'
        }
        
        # Appel du callback
        response = test_client.get('/api/amazon/callback', params=callback_params)
        
        # Vérifications des logs
        assert response.status_code == 200
        
        # Vérifier que les logs info sont appelés
        mock_logger.info.assert_called()
        
        # Vérifier que les données sensibles ne sont pas loggées en clair
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        for log_message in log_calls:
            # Ne doit pas contenir le code OAuth complet
            assert 'ANsensitivecode567890' not in log_message
            # Ne doit pas contenir le state complet
            assert 'sensitive_state_abcd1234' not in log_message
            
            # Mais peut contenir des versions tronquées pour debug
            if 'state' in log_message:
                # Vérifier que seuls les premiers caractères sont loggés
                assert 'sensitive_state_abcd1234'[:20] in log_message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])