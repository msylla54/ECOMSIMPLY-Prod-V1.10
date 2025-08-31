# Tests automatiques pour Amazon Integration Phase 1
import pytest
import asyncio
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Tests pour le module d'authentification
class TestAmazonOAuthService:
    """Tests pour le service OAuth Amazon"""
    
    @pytest.fixture
    def oauth_service(self):
        """Fixture pour le service OAuth"""
        with patch.dict(os.environ, {
            'AMAZON_LWA_CLIENT_ID': 'test_client_id',
            'AMAZON_LWA_CLIENT_SECRET': 'test_client_secret',
            'AMAZON_REFRESH_TOKEN_ENCRYPTION_KEY': 'test_encryption_key_32_chars_long'
        }):
            from integrations.amazon.auth import AmazonOAuthService
            return AmazonOAuthService()
    
    def test_oauth_service_initialization(self, oauth_service):
        """Test de l'initialisation du service OAuth"""
        assert oauth_service.client_id == 'test_client_id'
        assert oauth_service.client_secret == 'test_client_secret'
        assert 'eu' in oauth_service.oauth_endpoints
        assert 'na' in oauth_service.oauth_endpoints
        assert 'fe' in oauth_service.oauth_endpoints
    
    def test_generate_oauth_url(self, oauth_service):
        """Test de génération d'URL OAuth"""
        result = oauth_service.generate_oauth_url(
            marketplace_id='A13V1IB3VIYZZH',
            region='eu'
        )
        
        assert 'authorization_url' in result
        assert 'state' in result
        assert 'expires_at' in result
        assert 'sellercentral-europe.amazon.com' in result['authorization_url']
        assert result['marketplace_id'] == 'A13V1IB3VIYZZH'
        assert result['region'] == 'eu'
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_success(self, oauth_service):
        """Test d'échange de code OAuth réussi"""
        
        # Mock de la réponse Amazon
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'token_type': 'bearer',
            'expires_in': 3600
        })
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            # Générer un state valide
            state = oauth_service._generate_secure_state()
            
            result = await oauth_service.exchange_code_for_tokens(
                code='test_code',
                state=state,
                region='eu'
            )
            
            assert result['access_token'] == 'test_access_token'
            assert result['refresh_token'] == 'test_refresh_token'
            assert 'retrieved_at' in result
    
    def test_encrypt_decrypt_refresh_token(self, oauth_service):
        """Test du chiffrement/déchiffrement des tokens"""
        test_token = 'test_refresh_token_value'
        user_id = 'test_user_123'
        
        # Chiffrer
        encrypted_data = oauth_service.encrypt_refresh_token(test_token, user_id)
        
        assert 'encrypted_token' in encrypted_data
        assert 'nonce' in encrypted_data
        assert encrypted_data['encryption_method'] == 'AES-GCM'
        
        # Déchiffrer
        decrypted_token = oauth_service.decrypt_refresh_token(encrypted_data, user_id)
        assert decrypted_token == test_token
    
    def test_state_generation_and_verification(self, oauth_service):
        """Test de génération et vérification du state OAuth"""
        
        # Générer un state
        state = oauth_service._generate_secure_state()
        assert isinstance(state, str)
        assert len(state) > 20
        
        # Vérifier le state (doit être valide)
        assert oauth_service._verify_state(state) is True
        
        # Tester avec un state invalide
        assert oauth_service._verify_state('invalid_state') is False

# Tests pour le client SP-API
class TestAmazonSPAPIClient:
    """Tests pour le client SP-API Amazon"""
    
    @pytest.fixture
    def spapi_client(self):
        """Fixture pour le client SP-API"""
        from integrations.amazon.client import AmazonSPAPIClient
        return AmazonSPAPIClient(region='eu')
    
    def test_client_initialization(self, spapi_client):
        """Test de l'initialisation du client"""
        assert spapi_client.region == 'eu'
        assert spapi_client.base_url == 'https://sellingpartnerapi-eu.amazon.com'
        assert spapi_client.max_retries == 3
    
    @pytest.mark.asyncio
    async def test_make_authenticated_request_success(self, spapi_client):
        """Test de requête authentifiée réussie"""
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'success': True, 'data': 'test'})
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.request.return_value.__aenter__.return_value = mock_response
            
            result = await spapi_client.make_authenticated_request(
                method='GET',
                path='/test',
                access_token='test_token',
                seller_id='test_seller',
                marketplace_id='A13V1IB3VIYZZH'
            )
            
            assert result['success'] is True
            assert result['data'] == 'test'
    
    @pytest.mark.asyncio
    async def test_health_check(self, spapi_client):
        """Test du health check"""
        
        mock_response = AsyncMock()
        mock_response.status = 401  # Attendu pour endpoint sans auth
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            result = await spapi_client.health_check()
            
            assert 'overall_status' in result
            assert 'regions' in result
            assert 'timestamp' in result

# Tests pour les modèles
class TestAmazonModels:
    """Tests pour les modèles Amazon"""
    
    def test_amazon_connection_model(self):
        """Test du modèle AmazonConnection"""
        from integrations.amazon.models import AmazonConnection, AmazonRegion
        
        connection = AmazonConnection(
            user_id='test_user',
            marketplace_id='A13V1IB3VIYZZH',
            region=AmazonRegion.EU
        )
        
        assert connection.user_id == 'test_user'
        assert connection.marketplace_id == 'A13V1IB3VIYZZH'
        assert connection.region == AmazonRegion.EU
        assert connection.status == 'pending'
        assert connection.id is not None
    
    def test_marketplace_validation(self):
        """Test de validation des marketplace IDs"""
        from integrations.amazon.models import AmazonConnection, AmazonRegion
        from pydantic import ValidationError
        
        # Marketplace valide
        connection = AmazonConnection(
            user_id='test_user',
            marketplace_id='A13V1IB3VIYZZH',  # France
            region=AmazonRegion.EU
        )
        assert connection.marketplace_id == 'A13V1IB3VIYZZH'
        
        # Marketplace invalide
        with pytest.raises(ValidationError):
            AmazonConnection(
                user_id='test_user',
                marketplace_id='INVALID_MARKETPLACE',
                region=AmazonRegion.EU
            )
    
    def test_supported_marketplaces(self):
        """Test de la liste des marketplaces supportés"""
        from integrations.amazon.models import SUPPORTED_MARKETPLACES
        
        assert len(SUPPORTED_MARKETPLACES) >= 6
        
        # Vérifier que la France est présente
        france_marketplace = next(
            (mp for mp in SUPPORTED_MARKETPLACES if mp.country_code == 'FR'), 
            None
        )
        assert france_marketplace is not None
        assert france_marketplace.marketplace_id == 'A13V1IB3VIYZZH'
        assert france_marketplace.name == 'Amazon.fr'

# Tests pour les routes
class TestAmazonIntegrationRoutes:
    """Tests pour les routes d'intégration Amazon"""
    
    @pytest.fixture
    def client(self):
        """Fixture pour le client de test FastAPI"""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        
        # Créer une app de test
        app = FastAPI()
        
        # Mock des dépendances
        def mock_get_database():
            return AsyncMock()
        
        def mock_get_current_user():
            return 'test_user_123'
        
        # Importer et configurer les routes
        from routes.amazon_integration_routes import amazon_integration_router
        
        # Override des dépendances
        amazon_integration_router.dependency_overrides[mock_get_database] = mock_get_database
        amazon_integration_router.dependency_overrides[mock_get_current_user] = mock_get_current_user
        
        app.include_router(amazon_integration_router)
        
        return TestClient(app)
    
    def test_get_marketplaces_endpoint(self, client):
        """Test de l'endpoint des marketplaces"""
        response = client.get('/api/amazon/marketplaces')
        
        assert response.status_code == 200
        data = response.json()
        assert 'marketplaces' in data
        assert 'total_count' in data
        assert data['total_count'] >= 6

# Tests d'intégration complets
class TestAmazonIntegrationE2E:
    """Tests d'intégration end-to-end"""
    
    @pytest.mark.asyncio
    async def test_complete_oauth_flow(self):
        """Test du flux OAuth complet"""
        
        # Ce test simule un flux OAuth complet sans appels réseau réels
        with patch.dict(os.environ, {
            'AMAZON_LWA_CLIENT_ID': 'test_client_id',
            'AMAZON_LWA_CLIENT_SECRET': 'test_client_secret',
            'AMAZON_REFRESH_TOKEN_ENCRYPTION_KEY': 'test_encryption_key_32_chars_long'
        }):
            from integrations.amazon.auth import AmazonOAuthService
            
            oauth_service = AmazonOAuthService()
            
            # 1. Générer URL OAuth
            oauth_data = oauth_service.generate_oauth_url(
                marketplace_id='A13V1IB3VIYZZH',
                region='eu'
            )
            
            assert 'authorization_url' in oauth_data
            assert 'state' in oauth_data
            
            # 2. Simuler échange de code (mock)
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                'access_token': 'test_access_token',
                'refresh_token': 'test_refresh_token',
                'token_type': 'bearer',
                'expires_in': 3600
            })
            
            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
                
                tokens = await oauth_service.exchange_code_for_tokens(
                    code='test_code',
                    state=oauth_data['state'],
                    region='eu'
                )
            
            # 3. Chiffrer le refresh token
            encrypted_data = oauth_service.encrypt_refresh_token(
                refresh_token=tokens['refresh_token'],
                user_id='test_user'
            )
            
            # 4. Vérifier que tout fonctionne
            assert tokens['access_token'] == 'test_access_token'
            assert 'encrypted_token' in encrypted_data
            
            # 5. Déchiffrer pour vérifier
            decrypted = oauth_service.decrypt_refresh_token(
                encrypted_data, 'test_user'
            )
            assert decrypted == 'test_refresh_token'
    
    def test_security_measures(self):
        """Test des mesures de sécurité"""
        
        with patch.dict(os.environ, {
            'AMAZON_LWA_CLIENT_ID': 'test_client_id',
            'AMAZON_LWA_CLIENT_SECRET': 'test_client_secret',
            'AMAZON_REFRESH_TOKEN_ENCRYPTION_KEY': 'test_encryption_key_32_chars_long'
        }):
            from integrations.amazon.auth import AmazonOAuthService
            
            oauth_service = AmazonOAuthService()
            
            # 1. Test CSRF protection
            state1 = oauth_service._generate_secure_state()
            state2 = oauth_service._generate_secure_state()
            
            # Les states doivent être différents
            assert state1 != state2
            
            # Chaque state doit être valide
            assert oauth_service._verify_state(state1) is True
            assert oauth_service._verify_state(state2) is True
            
            # 2. Test chiffrement multi-utilisateur
            token = 'same_token_value'
            user1_encrypted = oauth_service.encrypt_refresh_token(token, 'user1')
            user2_encrypted = oauth_service.encrypt_refresh_token(token, 'user2')
            
            # Les données chiffrées doivent être différentes
            assert user1_encrypted['encrypted_token'] != user2_encrypted['encrypted_token']
            
            # Chaque utilisateur ne peut déchiffrer que son token
            assert oauth_service.decrypt_refresh_token(user1_encrypted, 'user1') == token
            assert oauth_service.decrypt_refresh_token(user2_encrypted, 'user2') == token
            
            # Cross-user decryption should fail
            with pytest.raises(Exception):
                oauth_service.decrypt_refresh_token(user1_encrypted, 'user2')

if __name__ == '__main__':
    pytest.main([__file__, '-v'])