"""
Tests unitaires pour Amazon OAuth Service
Validation des endpoints EU/NA/FE et priorité AMAZON_REDIRECT_URI
"""

import pytest
import os
import sys
from unittest.mock import patch, AsyncMock

# Add backend path for imports
sys.path.append('/app/backend')

from services.amazon_oauth_service import AmazonOAuthService
from models.amazon_spapi import SPAPIRegion


@pytest.fixture
def oauth_service():
    """Fixture pour créer un service OAuth avec configuration test"""
    with patch.dict(os.environ, {
        'AMAZON_LWA_CLIENT_ID': 'test_client_id',
        'AMAZON_LWA_CLIENT_SECRET': 'test_client_secret',
        'AMAZON_APP_ID': 'amzn1.sellerapps.app.test-app-id',
        'APP_BASE_URL': 'https://app.test.com',
        'AMAZON_REDIRECT_URI': 'https://custom.test.com/api/amazon/callback'
    }):
        return AmazonOAuthService()


class TestAmazonOAuthEndpoints:
    """Test de conformité des endpoints OAuth par région"""
    
    def test_amazon_app_id_usage_in_authorization_url(self, oauth_service):
        """Test que AMAZON_APP_ID est utilisé pour application_id (pas client_id)"""
        state = oauth_service.generate_oauth_state("user123", "conn456")
        
        # Test avec AMAZON_APP_ID
        auth_url = oauth_service.build_authorization_url(
            state=state,
            marketplace_id="A13V1IB3VIYZZH",
            region=SPAPIRegion.EU
        )
        
        # Vérifier que l'URL contient l'app_id (pas client_id)
        assert 'application_id=amzn1.sellerapps.app.test-app-id' in auth_url
        assert 'application_id=test_client_id' not in auth_url
    
    def test_oauth_endpoints_mapping_conforme(self, oauth_service):
        """Test que les endpoints OAuth sont conformes à la spécification"""
        endpoints = oauth_service._oauth_endpoints
        
        # Validation NA (Amérique du Nord)
        assert endpoints[SPAPIRegion.NA]['auth'] == 'https://sellercentral.amazon.com/apps/authorize/consent'
        assert endpoints[SPAPIRegion.NA]['token'] == 'https://api.amazon.com/auth/o2/token'
        assert endpoints[SPAPIRegion.NA]['spapi'] == 'https://sellingpartnerapi-na.amazon.com'
        
        # Validation EU (Europe) - CORRECTION CRITIQUE
        assert endpoints[SPAPIRegion.EU]['auth'] == 'https://sellercentral-europe.amazon.com/apps/authorize/consent'
        assert endpoints[SPAPIRegion.EU]['token'] == 'https://api.amazon.com/auth/o2/token'  # <-- DOIT ÊTRE CORRIGÉ
        assert endpoints[SPAPIRegion.EU]['spapi'] == 'https://sellingpartnerapi-eu.amazon.com'
        
        # Validation FE (Extrême-Orient)
        assert endpoints[SPAPIRegion.FE]['auth'] == 'https://sellercentral-japan.amazon.com/apps/authorize/consent'
        assert endpoints[SPAPIRegion.FE]['token'] == 'https://api.amazon.co.jp/auth/o2/token'
        assert endpoints[SPAPIRegion.FE]['spapi'] == 'https://sellingpartnerapi-fe.amazon.com'
    
    def test_endpoint_eu_token_correction(self, oauth_service):
        """Test spécifique de la correction EU token endpoint"""
        eu_token_endpoint = oauth_service._oauth_endpoints[SPAPIRegion.EU]['token']
        
        # Vérifier que l'ancien endpoint incorrect n'est plus utilisé
        assert eu_token_endpoint != 'https://api.amazon.co.uk/auth/o2/token'
        
        # Vérifier que le bon endpoint est utilisé
        assert eu_token_endpoint == 'https://api.amazon.com/auth/o2/token'


class TestRedirectUriPriority:
    """Test de la priorité AMAZON_REDIRECT_URI > APP_BASE_URL"""
    
    def test_amazon_redirect_uri_priority_build_authorization_url(self, oauth_service):
        """Test que AMAZON_REDIRECT_URI a priorité dans build_authorization_url"""
        state = oauth_service.generate_oauth_state("user123", "conn456")
        
        # Test avec AMAZON_REDIRECT_URI définie
        auth_url = oauth_service.build_authorization_url(
            state=state,
            marketplace_id="A13V1IB3VIYZZH",
            region=SPAPIRegion.EU
        )
        
        # Vérifier que l'URL contient la redirect_uri prioritaire
        assert 'redirect_uri=https%3A//custom.test.com/api/amazon/callback' in auth_url
        assert 'redirect_uri=https%3A//app.test.com/api/amazon/callback' not in auth_url
    
    @patch.dict(os.environ, {'AMAZON_REDIRECT_URI': ''}, clear=False)
    def test_app_base_url_fallback_build_authorization_url(self, oauth_service):
        """Test que APP_BASE_URL est utilisée comme fallback"""
        state = oauth_service.generate_oauth_state("user123", "conn456")
        
        # Test sans AMAZON_REDIRECT_URI
        auth_url = oauth_service.build_authorization_url(
            state=state,
            marketplace_id="A13V1IB3VIYZZH",
            region=SPAPIRegion.EU
        )
        
        # Vérifier que l'URL contient la fallback
        assert 'redirect_uri=https%3A//app.test.com/api/amazon/callback' in auth_url
    
    @patch('httpx.AsyncClient.post')
    async def test_amazon_redirect_uri_priority_exchange_code(self, mock_post, oauth_service):
        """Test que AMAZON_REDIRECT_URI a priorité dans exchange_code_for_tokens"""
        # Mock de la réponse LWA
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'scope': 'sellingpartnerapi::notifications'
        }
        mock_response.raise_for_status = AsyncMock()
        mock_post.return_value = mock_response
        
        # Appel du service
        token_data = await oauth_service.exchange_code_for_tokens(
            authorization_code="test_code",
            region=SPAPIRegion.EU
        )
        
        # Vérifier que l'appel POST utilise la bonne redirect_uri
        call_args = mock_post.call_args
        post_data = call_args[1]['data']
        
        assert post_data['redirect_uri'] == 'https://custom.test.com/api/amazon/callback'
        assert token_data.access_token == 'test_access_token'
        assert token_data.refresh_token == 'test_refresh_token'
    
    @patch.dict(os.environ, {'AMAZON_REDIRECT_URI': ''}, clear=False)
    @patch('httpx.AsyncClient.post')
    async def test_app_base_url_fallback_exchange_code(self, mock_post, oauth_service):
        """Test que APP_BASE_URL est utilisée comme fallback dans exchange_code_for_tokens"""
        # Mock de la réponse LWA
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'scope': 'sellingpartnerapi::notifications'
        }
        mock_response.raise_for_status = AsyncMock()
        mock_post.return_value = mock_response
        
        # Appel du service
        token_data = await oauth_service.exchange_code_for_tokens(
            authorization_code="test_code",
            region=SPAPIRegion.EU
        )
        
        # Vérifier que l'appel POST utilise la fallback redirect_uri
        call_args = mock_post.call_args
        post_data = call_args[1]['data']
        
        assert post_data['redirect_uri'] == 'https://app.test.com/api/amazon/callback'
        assert token_data.access_token == 'test_access_token'


class TestErrorLoggingWithoutSecrets:
    """Test que les logs d'erreur n'exposent pas les secrets"""
    
    @patch('httpx.AsyncClient.post')
    async def test_error_logging_without_client_secret(self, mock_post, oauth_service):
        """Test que client_secret n'est jamais loggé"""
        from httpx import HTTPStatusError, Response, Request
        
        # Mock d'une erreur HTTP
        mock_request = Request("POST", "https://api.amazon.com/auth/o2/token")
        mock_response = Response(400, json={'error': 'invalid_grant'}, request=mock_request)
        mock_response._content = b'{"error": "invalid_grant"}'
        mock_post.side_effect = HTTPStatusError("Bad Request", request=mock_request, response=mock_response)
        
        # Capture des logs
        with patch('services.amazon_oauth_service.logger') as mock_logger:
            with pytest.raises(RuntimeError):
                await oauth_service.exchange_code_for_tokens(
                    authorization_code="invalid_code",
                    region=SPAPIRegion.EU
                )
            
            # Vérifier que les logs ne contiennent pas de secrets
            log_calls = [call[0][0] for call in mock_logger.error.call_args_list]
            for log_message in log_calls:
                assert 'test_client_secret' not in log_message
                assert 'client_secret' not in log_message
                assert 'authorization_code' not in log_message
    
    @patch('httpx.AsyncClient.post')
    async def test_error_logging_includes_debug_info(self, mock_post, oauth_service):
        """Test que les logs d'erreur incluent les informations de debug utiles"""
        from httpx import HTTPStatusError, Response, Request
        
        # Mock d'une erreur HTTP avec body de réponse
        mock_request = Request("POST", "https://api.amazon.com/auth/o2/token")
        mock_response = Response(400, json={'error': 'invalid_grant', 'error_description': 'The provided authorization grant is invalid'}, request=mock_request)
        mock_response._content = b'{"error": "invalid_grant", "error_description": "The provided authorization grant is invalid"}'
        mock_post.side_effect = HTTPStatusError("Bad Request", request=mock_request, response=mock_response)
        
        # Capture des logs
        with patch('services.amazon_oauth_service.logger') as mock_logger:
            with pytest.raises(RuntimeError):
                await oauth_service.exchange_code_for_tokens(
                    authorization_code="invalid_code",
                    region=SPAPIRegion.EU
                )
            
            # Vérifier que les logs incluent les informations utiles
            log_calls = [call[0][0] for call in mock_logger.error.call_args_list]
            
            # Doit contenir le status code
            assert any('400' in log for log in log_calls)
            
            # Doit contenir la redirect_uri utilisée
            assert any('custom.test.com' in log for log in log_calls)
            
            # Doit contenir la région
            assert any('EU' in log for log in log_calls)
    
    @patch('httpx.AsyncClient.post')
    async def test_missing_refresh_token_logging(self, mock_post, oauth_service):
        """Test logging spécifique quand refresh_token est absent"""
        # Mock d'une réponse sans refresh_token
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            # 'refresh_token': manquant !
            'token_type': 'Bearer',
            'expires_in': 3600
        }
        mock_response.raise_for_status = AsyncMock()
        mock_post.return_value = mock_response
        
        # Capture des logs
        with patch('services.amazon_oauth_service.logger') as mock_logger:
            with pytest.raises(ValueError, match="Missing refresh_token"):
                await oauth_service.exchange_code_for_tokens(
                    authorization_code="test_code",
                    region=SPAPIRegion.EU
                )
            
            # Vérifier les logs spécifiques
            log_calls = [call[0][0] for call in mock_logger.error.call_args_list]
            
            # Doit contenir le message d'erreur spécifique
            assert any('No refresh_token in response' in log for log in log_calls)
            
            # Doit contenir la redirect_uri et région pour debug
            assert any('custom.test.com' in log for log in log_calls)
            assert any('EU' in log for log in log_calls)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])