# Tests for Amazon SP-API Integration - Bloc 1
import pytest
import os
import json
import base64
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from motor.motor_asyncio import AsyncIOMotorDatabase
import httpx

from models.amazon_spapi import (
    AmazonConnection, ConnectionStatus, SPAPIRegion, 
    SPAPITokenData, SPAPIConnectionRequest
)
from services.amazon_encryption_service import AmazonTokenEncryptionService
from services.amazon_oauth_service import AmazonOAuthService
from services.amazon_connection_service import AmazonConnectionService

class TestAmazonEncryptionService:
    """Test suite for Amazon token encryption service"""
    
    @pytest.fixture
    def encryption_service(self):
        """Create encryption service with test environment"""
        with patch.dict(os.environ, {
            'AWS_KMS_KEY_ID': 'test-key-id',
            'AWS_REGION': 'eu-west-1',
            'AMAZON_LWA_CLIENT_ID': 'test-client-id',
            'AMAZON_LWA_CLIENT_SECRET': 'test-secret',
            'AWS_ROLE_ARN': 'test-role-arn'
        }):
            service = AmazonTokenEncryptionService()
            service.kms_client = Mock()
            return service
    
    @pytest.mark.asyncio
    async def test_encrypt_token_data_success(self, encryption_service):
        """Test successful token encryption"""
        # Mock KMS response
        mock_dek_response = {
            'Plaintext': b'test-key-32-bytes-long-for-aes256',
            'CiphertextBlob': b'encrypted-key-data'
        }
        encryption_service.kms_client.generate_data_key.return_value = mock_dek_response
        
        # Test data
        token_data = {
            'access_token': 'test-access-token',
            'refresh_token': 'test-refresh-token',
            'token_type': 'bearer',
            'expires_in': 3600
        }
        
        # Encrypt token
        encrypted_data, nonce = await encryption_service.encrypt_token_data(
            token_data=token_data,
            user_id='test-user-123',
            connection_id='test-conn-456'
        )
        
        # Verify encryption call
        encryption_service.kms_client.generate_data_key.assert_called_once()
        assert isinstance(encrypted_data, str)
        assert isinstance(nonce, str)
        assert ':' in encrypted_data  # Should contain encrypted key and ciphertext
    
    @pytest.mark.asyncio
    async def test_decrypt_token_data_success(self, encryption_service):
        """Test successful token decryption"""
        # Mock KMS responses
        mock_dek_response = {
            'Plaintext': b'test-key-32-bytes-long-for-aes256',
            'CiphertextBlob': b'encrypted-key-data'
        }
        encryption_service.kms_client.generate_data_key.return_value = mock_dek_response
        encryption_service.kms_client.decrypt.return_value = {
            'Plaintext': b'test-key-32-bytes-long-for-aes256'
        }
        
        # First encrypt some data
        token_data = {
            'access_token': 'test-access-token',
            'refresh_token': 'test-refresh-token',
            'token_type': 'bearer',
            'expires_in': 3600
        }
        
        encrypted_data, nonce = await encryption_service.encrypt_token_data(
            token_data=token_data,
            user_id='test-user-123',
            connection_id='test-conn-456'
        )
        
        # Then decrypt it
        decrypted_data = await encryption_service.decrypt_token_data(
            encrypted_data=encrypted_data,
            nonce_b64=nonce,
            user_id='test-user-123',
            connection_id='test-conn-456'
        )
        
        # Verify decryption
        assert decrypted_data['access_token'] == token_data['access_token']
        assert decrypted_data['refresh_token'] == token_data['refresh_token']
        assert decrypted_data['token_type'] == token_data['token_type']
    
    def test_kms_access_test_success(self, encryption_service):
        """Test KMS access validation"""
        # Mock successful KMS response
        encryption_service.kms_client.describe_key.return_value = {
            'KeyMetadata': {'KeyState': 'Enabled'}
        }
        
        result = encryption_service.test_kms_access()
        assert result is True
    
    def test_kms_access_test_failure(self, encryption_service):
        """Test KMS access validation failure"""
        # Mock KMS error
        encryption_service.kms_client.describe_key.side_effect = Exception("KMS Error")
        
        result = encryption_service.test_kms_access()
        assert result is False
    
    def test_mask_sensitive_data(self, encryption_service):
        """Test sensitive data masking"""
        sensitive_data = {
            'access_token': 'very-long-access-token-here',
            'refresh_token': 'refresh-token-data',
            'client_secret': 'secret-key',
            'normal_field': 'normal-value'
        }
        
        masked_data = encryption_service.mask_sensitive_data(sensitive_data)
        
        assert masked_data['access_token'] == 'very***MASKED***'
        assert masked_data['refresh_token'] == 'refr***MASKED***'
        assert masked_data['client_secret'] == '***MASKED***'
        assert masked_data['normal_field'] == 'normal-value'

class TestAmazonOAuthService:
    """Test suite for Amazon OAuth service"""
    
    @pytest.fixture
    def oauth_service(self):
        """Create OAuth service with test environment"""
        with patch.dict(os.environ, {
            'AMAZON_LWA_CLIENT_ID': 'test-client-id',
            'AMAZON_LWA_CLIENT_SECRET': 'test-secret'
        }):
            service = AmazonOAuthService()
            service.http_client = AsyncMock()
            return service
    
    def test_generate_oauth_state(self, oauth_service):
        """Test OAuth state generation"""
        state = oauth_service.generate_oauth_state(
            user_id='test-user-123',
            connection_id='test-conn-456'
        )
        
        assert isinstance(state, str)
        assert len(state) > 50  # Should be reasonably long
        
        # Should be base64 encoded
        try:
            decoded = base64.urlsafe_b64decode(state.encode()).decode()
            assert 'test-user-123' in decoded
            assert 'test-conn-456' in decoded
        except Exception:
            pytest.fail("State should be valid base64")
    
    def test_verify_oauth_state_valid(self, oauth_service):
        """Test OAuth state verification with valid state"""
        # Generate a state
        state = oauth_service.generate_oauth_state(
            user_id='test-user-123',
            connection_id='test-conn-456'
        )
        
        # Verify it immediately (should be valid)
        is_valid = oauth_service.verify_oauth_state(
            state=state,
            expected_user_id='test-user-123',
            expected_connection_id='test-conn-456',
            max_age_minutes=60
        )
        
        assert is_valid is True
    
    def test_verify_oauth_state_invalid_user(self, oauth_service):
        """Test OAuth state verification with wrong user"""
        state = oauth_service.generate_oauth_state(
            user_id='test-user-123',
            connection_id='test-conn-456'
        )
        
        # Verify with wrong user
        is_valid = oauth_service.verify_oauth_state(
            state=state,
            expected_user_id='wrong-user',
            expected_connection_id='test-conn-456'
        )
        
        assert is_valid is False
    
    def test_build_authorization_url(self, oauth_service):
        """Test authorization URL building"""
        auth_url = oauth_service.build_authorization_url(
            state='test-state',
            marketplace_id='A13V1IB3VIYZZH',
            region=SPAPIRegion.EU
        )
        
        assert 'sellercentral-europe.amazon.com' in auth_url
        assert 'test-client-id' in auth_url
        assert 'test-state' in auth_url
        assert 'A13V1IB3VIYZZH' in auth_url
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_success(self, oauth_service):
        """Test successful token exchange"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            'access_token': 'test-access-token',
            'refresh_token': 'test-refresh-token',
            'token_type': 'bearer',
            'expires_in': 3600,
            'scope': 'test-scope'
        }
        
        oauth_service.http_client.post.return_value = mock_response
        
        # Exchange code
        token_data = await oauth_service.exchange_code_for_tokens(
            authorization_code='test-auth-code',
            region=SPAPIRegion.EU
        )
        
        assert isinstance(token_data, SPAPITokenData)
        assert token_data.access_token == 'test-access-token'
        assert token_data.refresh_token == 'test-refresh-token'
        assert token_data.token_type == 'bearer'
        assert token_data.expires_in == 3600
    
    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, oauth_service):
        """Test successful token refresh"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            'access_token': 'new-access-token',
            'token_type': 'bearer',
            'expires_in': 3600
        }
        
        oauth_service.http_client.post.return_value = mock_response
        
        # Refresh token
        token_data = await oauth_service.refresh_access_token(
            refresh_token='test-refresh-token',
            region=SPAPIRegion.EU
        )
        
        assert isinstance(token_data, SPAPITokenData)
        assert token_data.access_token == 'new-access-token'
        assert token_data.refresh_token == 'test-refresh-token'  # Should reuse existing

class TestAmazonConnectionService:
    """Test suite for Amazon connection service"""
    
    @pytest.fixture
    def mock_database(self):
        """Create mock database"""
        db = Mock(spec=AsyncIOMotorDatabase)
        db.amazon_connections = AsyncMock()
        return db
    
    @pytest.fixture
    def connection_service(self, mock_database):
        """Create connection service with mocked dependencies"""
        service = AmazonConnectionService(mock_database)
        service.encryption_service = Mock(spec=AmazonTokenEncryptionService)
        service.oauth_service = Mock(spec=AmazonOAuthService)
        return service
    
    @pytest.mark.asyncio
    async def test_create_connection_success(self, connection_service):
        """Test successful connection creation"""
        # Mock OAuth service
        connection_service.oauth_service.generate_oauth_state.return_value = 'test-state'
        connection_service.oauth_service.build_authorization_url.return_value = 'https://test-auth-url.com'
        
        # Mock database insert
        connection_service.connections_collection.insert_one = AsyncMock()
        
        # Create connection
        result = await connection_service.create_connection(
            user_id='test-user-123',
            marketplace_id='A13V1IB3VIYZZH',
            region=SPAPIRegion.EU
        )
        
        # Verify result
        assert 'connection_id' in result
        assert 'authorization_url' in result
        assert 'state' in result
        assert 'expires_at' in result
        assert result['authorization_url'] == 'https://test-auth-url.com'
        
        # Verify database call
        connection_service.connections_collection.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_oauth_callback_success(self, connection_service):
        """Test successful OAuth callback handling"""
        # Mock database query
        mock_connection_doc = {
            'id': 'test-conn-123',
            'user_id': 'test-user-123',
            'region': 'eu',
            'marketplace_id': 'A13V1IB3VIYZZH',
            'status': 'pending'
        }
        connection_service.connections_collection.find_one = AsyncMock(return_value=mock_connection_doc)
        connection_service.connections_collection.update_one = AsyncMock()
        
        # Mock OAuth service
        connection_service.oauth_service.verify_oauth_state.return_value = True
        mock_token_data = SPAPITokenData(
            access_token='test-access',
            refresh_token='test-refresh',
            token_type='bearer',
            expires_in=3600,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        connection_service.oauth_service.exchange_code_for_tokens = AsyncMock(return_value=mock_token_data)
        
        # Mock encryption service
        connection_service.encryption_service.encrypt_token_data = AsyncMock(
            return_value=('encrypted-data', 'nonce')
        )
        connection_service.encryption_service.kms_key_id = 'test-key-id'
        
        # Handle callback
        result = await connection_service.handle_oauth_callback(
            state='test-state',
            authorization_code='test-code',
            selling_partner_id='test-seller-123'
        )
        
        # Verify success
        assert result is True
        connection_service.connections_collection.update_one.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_user_connections(self, connection_service):
        """Test getting user connections"""
        # Mock database query
        mock_connections = [
            {
                'id': 'conn-1',
                'user_id': 'test-user',
                'status': 'active',
                'marketplace_id': 'A13V1IB3VIYZZH',
                'seller_id': 'seller-1',
                'region': 'eu',
                'created_at': datetime.utcnow(),
                'last_used_at': None,
                'error_message': None
            }
        ]
        
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=mock_connections)
        connection_service.connections_collection.find.return_value = mock_cursor
        
        # Get connections
        connections = await connection_service.get_user_connections('test-user')
        
        assert len(connections) == 1
        assert connections[0].connection_id == 'conn-1'
        assert connections[0].status == ConnectionStatus.ACTIVE
        assert connections[0].marketplace_id == 'A13V1IB3VIYZZH'
    
    @pytest.mark.asyncio
    async def test_disconnect_connection_success(self, connection_service):
        """Test successful connection disconnection"""
        # Mock database update
        mock_result = Mock()
        mock_result.modified_count = 1
        connection_service.connections_collection.update_one = AsyncMock(return_value=mock_result)
        
        # Disconnect
        result = await connection_service.disconnect_connection(
            connection_id='test-conn-123',
            user_id='test-user-123'
        )
        
        assert result is True
        connection_service.connections_collection.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_states(self, connection_service):
        """Test cleanup of expired OAuth states"""
        # Mock database update
        mock_result = Mock()
        mock_result.modified_count = 3
        connection_service.connections_collection.update_many = AsyncMock(return_value=mock_result)
        
        # Cleanup
        count = await connection_service.cleanup_expired_states()
        
        assert count == 3
        connection_service.connections_collection.update_many.assert_called_once()

class TestAmazonModels:
    """Test suite for Amazon SP-API models"""
    
    def test_amazon_connection_model_validation(self):
        """Test AmazonConnection model validation"""
        # Valid connection
        connection = AmazonConnection(
            user_id='test-user-123',
            marketplace_id='A13V1IB3VIYZZH',
            seller_id='test-seller',
            encrypted_refresh_token='encrypted-token',
            token_encryption_nonce='nonce',
            encryption_key_id='key-id'
        )
        
        assert connection.user_id == 'test-user-123'
        assert connection.region == SPAPIRegion.EU  # Default
        assert connection.status == ConnectionStatus.PENDING  # Default
        assert isinstance(connection.created_at, datetime)
    
    def test_invalid_marketplace_id(self):
        """Test validation of invalid marketplace ID"""
        with pytest.raises(ValueError, match="Invalid marketplace ID"):
            AmazonConnection(
                user_id='test-user',
                marketplace_id='INVALID_ID',
                seller_id='test-seller',
                encrypted_refresh_token='token',
                token_encryption_nonce='nonce',
                encryption_key_id='key-id'
            )
    
    def test_spapi_connection_request_validation(self):
        """Test SPAPIConnectionRequest validation"""
        # Valid request
        request = SPAPIConnectionRequest(
            marketplace_id='A13V1IB3VIYZZH',
            region=SPAPIRegion.EU
        )
        
        assert request.marketplace_id == 'A13V1IB3VIYZZH'
        assert request.region == SPAPIRegion.EU
    
    def test_spapi_token_data_immutable(self):
        """Test that SPAPITokenData is immutable (security feature)"""
        token_data = SPAPITokenData(
            access_token='test-token',
            refresh_token='refresh-token',
            token_type='bearer',
            expires_in=3600,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        # Should not allow mutation (security feature)
        with pytest.raises(Exception):
            token_data.access_token = 'new-token'

class TestEnvironmentValidation:
    """Test environment variable validation"""
    
    def test_missing_required_env_vars(self):
        """Test that missing environment variables raise appropriate errors"""
        # Test encryption service
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Missing required environment variables"):
                AmazonTokenEncryptionService()
        
        # Test OAuth service
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Missing OAuth configuration"):
                AmazonOAuthService()
    
    def test_required_env_vars_present(self):
        """Test that services initialize successfully with required vars"""
        required_env = {
            'AWS_KMS_KEY_ID': 'test-key',
            'AWS_REGION': 'eu-west-1',
            'AMAZON_LWA_CLIENT_ID': 'test-client',
            'AMAZON_LWA_CLIENT_SECRET': 'test-secret',
            'AWS_ROLE_ARN': 'test-role'
        }
        
        with patch.dict(os.environ, required_env):
            # Should not raise any exceptions
            encryption_service = AmazonTokenEncryptionService()
            oauth_service = AmazonOAuthService()
            
            assert encryption_service.kms_key_id == 'test-key'
            assert oauth_service.client_id == 'test-client'

# Integration Tests
class TestIntegrationFlow:
    """Integration tests for complete OAuth flow"""
    
    @pytest.mark.asyncio
    async def test_complete_oauth_flow_simulation(self):
        """Test complete OAuth flow from connection creation to callback"""
        # This would be an integration test that:
        # 1. Creates a connection
        # 2. Simulates OAuth redirect
        # 3. Handles callback
        # 4. Verifies encrypted token storage
        # 5. Tests token refresh
        
        # For now, this is a placeholder for future integration testing
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])